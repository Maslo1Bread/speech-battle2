from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..deps import require_admin, user_to_public
from ..models import Message, Negotiation, User
from ..schemas import (
    AdminUserCreate,
    AdminUserUpdate,
    NegotiationListItem,
    NegotiationOut,
    ParticipantOut,
    ParticipantScoreIn,
    ScoreRequest,
)
from ..security import encrypt_text, hash_lookup, hash_password
from ..services.scoring import apply_negotiation_score, utcnow, week_score_series
from ..routers.negotiations import _build_participants, _serialize_negotiation

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/reviews", response_model=list[NegotiationListItem])
def pending_reviews(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Negotiation)
        .where(Negotiation.status.in_(["pending_review", "reviewed"]))
        .order_by(Negotiation.created_at.desc())
    ).all()
    result = []
    for neg in rows:
        count = db.scalar(select(func.count(Message.id)).where(Message.negotiation_id == neg.id))
        participants = _build_participants(db, neg)
        result.append(
            NegotiationListItem(
                id=neg.id,
                mode=neg.mode,
                difficulty=neg.difficulty,
                scenario_title=neg.scenario_title,
                status=neg.status,
                score=neg.score,
                created_at=neg.created_at,
                finished_at=neg.finished_at,
                message_count=int(count or 0),
                participant_scores=participants,
            )
        )
    return result


@router.get("/reviews/{negotiation_id}", response_model=NegotiationOut)
def review_detail(
    negotiation_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    neg = db.scalar(
        select(Negotiation)
        .options(selectinload(Negotiation.messages))
        .where(Negotiation.id == negotiation_id)
    )
    if not neg:
        raise HTTPException(status_code=404, detail="Не найдено")
    return _serialize_negotiation(neg, admin.id, db)


@router.post("/reviews/{negotiation_id}/score")
def score_negotiation(
    negotiation_id: int,
    payload: ScoreRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    neg = db.get(Negotiation, negotiation_id)
    if not neg:
        raise HTTPException(status_code=404, detail="Не найдено")

    participant_ids = [uid for uid in (neg.participant1_id, neg.participant2_id) if uid]
    if not participant_ids:
        raise HTTPException(status_code=400, detail="Нет участников для оценки")

    # Нормализуем вход: либо scores[], либо одна score на единственного участника
    items: list[ParticipantScoreIn] = []
    if payload.scores:
        items = payload.scores
    elif payload.score is not None:
        if len(participant_ids) > 1:
            raise HTTPException(
                status_code=400,
                detail="Для переговоров с двумя участниками укажите scores для каждого",
            )
        items = [ParticipantScoreIn(user_id=participant_ids[0], score=payload.score)]
    else:
        raise HTTPException(status_code=400, detail="Укажите score или scores")

    allowed = set(participant_ids)
    seen: set[int] = set()
    for item in items:
        if item.user_id not in allowed:
            raise HTTPException(status_code=400, detail=f"Пользователь {item.user_id} не участник чата")
        if item.user_id in seen:
            raise HTTPException(status_code=400, detail="Дублирующая оценка участника")
        seen.add(item.user_id)

    if seen != allowed:
        missing = allowed - seen
        raise HTTPException(
            status_code=400,
            detail=f"Нужна оценка для всех участников: {sorted(missing)}",
        )

    for item in items:
        apply_negotiation_score(db, item.user_id, neg.id, item.score)

    # В карточке чата храним среднее (для списков)
    avg = round(sum(i.score for i in items) / len(items))
    neg.score = avg
    neg.status = "reviewed"
    neg.reviewed_at = utcnow()
    db.add(neg)
    db.commit()

    return {
        "ok": True,
        "score": avg,
        "scores": [{"user_id": i.user_id, "score": i.score} for i in items],
    }


def _member_matches(user: User, public: dict, needle: str) -> bool:
    if not needle:
        return True
    hay = " ".join(
        [
            str(user.id),
            f"user#{user.id}",
            public.get("username") or "",
            public.get("email") or "",
            public.get("full_name") or "",
            user.role,
            user.status,
        ]
    ).lower()
    if needle in hay:
        return True
    try:
        needle_hash = hash_lookup(needle)
    except Exception:
        needle_hash = ""
    return needle_hash in {user.username_hash, user.email_hash}


def _list_members_payload(db: Session, q: str | None) -> list[dict]:
    users = db.scalars(select(User).order_by(User.id.asc())).all()
    needle = (q or "").strip().lower()
    result = []
    for user in users:
        public = user_to_public(user)
        if _member_matches(user, public, needle):
            result.append(public)
    return result


@router.post("/members")
@router.post("/users")
def create_user(
    payload: AdminUserCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    username_hash = hash_lookup(payload.username)
    email_hash = hash_lookup(payload.email)
    exists = db.scalar(
        select(User).where(or_(User.username_hash == username_hash, User.email_hash == email_hash))
    )
    if exists:
        raise HTTPException(status_code=400, detail="Логин или почта уже заняты")

    user = User(
        username_hash=username_hash,
        email_hash=email_hash,
        username_enc=encrypt_text(payload.username.strip()),
        email_enc=encrypt_text(payload.email.lower().strip()),
        full_name_enc=encrypt_text(payload.full_name.strip()),
        password_hash=hash_password(payload.password),
        age=payload.age,
        role="admin" if payload.is_admin else "user",
        status="active",
        overall_score=0.0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_to_public(user)


@router.get("/members")
@router.get("/users")
def list_users(
    q: str | None = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return _list_members_payload(db, q)


@router.get("/members/{user_id}")
@router.get("/users/{user_id}")
def user_detail(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    data = user_to_public(user)
    data["week_scores"] = week_score_series(db, user.id)

    rows = db.scalars(
        select(Negotiation)
        .where(
            or_(Negotiation.participant1_id == user.id, Negotiation.participant2_id == user.id),
            Negotiation.status != "searching",
        )
        .order_by(Negotiation.created_at.desc())
    ).all()
    history = []
    for neg in rows:
        count = db.scalar(select(func.count(Message.id)).where(Message.negotiation_id == neg.id))
        participants = _build_participants(db, neg)
        my_score = next((p.score for p in participants if p.id == user.id), neg.score)
        history.append(
            {
                "id": neg.id,
                "mode": neg.mode,
                "difficulty": neg.difficulty,
                "scenario_title": neg.scenario_title,
                "status": neg.status,
                "score": my_score,
                "created_at": neg.created_at,
                "finished_at": neg.finished_at,
                "message_count": int(count or 0),
                "participant_scores": [p.model_dump() for p in participants],
            }
        )
    data["negotiations"] = history
    return data


@router.patch("/members/{user_id}")
@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if payload.username:
        new_hash = hash_lookup(payload.username)
        clash = db.scalar(select(User).where(User.username_hash == new_hash, User.id != user.id))
        if clash:
            raise HTTPException(status_code=400, detail="Логин уже занят")
        user.username_hash = new_hash
        user.username_enc = encrypt_text(payload.username.strip())
    if payload.email:
        new_hash = hash_lookup(payload.email)
        clash = db.scalar(select(User).where(User.email_hash == new_hash, User.id != user.id))
        if clash:
            raise HTTPException(status_code=400, detail="Почта уже занята")
        user.email_hash = new_hash
        user.email_enc = encrypt_text(payload.email.lower().strip())
    if payload.full_name:
        user.full_name_enc = encrypt_text(payload.full_name.strip())
    if payload.age is not None:
        user.age = payload.age
    if payload.password:
        user.password_hash = hash_password(payload.password)
    if payload.status in {"active", "blocked"}:
        user.status = payload.status
    if payload.role in {"user", "admin"}:
        user.role = payload.role

    db.add(user)
    db.commit()
    db.refresh(user)
    data = user_to_public(user)
    data["week_scores"] = week_score_series(db, user.id)
    return data
