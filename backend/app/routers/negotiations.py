from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..config import get_settings
from ..database import get_db
from ..deps import get_current_user, user_to_public
from ..models import Message, Negotiation, ScorePoint, User
from ..schemas import (
    MessageOut,
    NegotiationListItem,
    NegotiationOut,
    ParticipantOut,
    SendMessageRequest,
    StartAiRequest,
)
from ..services.ai_opponent import generate_ai_reply
from ..services.matchmaking import hub
from ..services.scenarios import get_scenario, list_scenarios_for_ui
from ..services.scoring import as_utc, utcnow

router = APIRouter(prefix="/api/negotiations", tags=["negotiations"])


def _ensure_user(user: User) -> None:
    if user.role == "admin":
        raise HTTPException(status_code=403, detail="Администратор не участвует в переговорах")


def _participant_scores_map(db: Session, negotiation_id: int) -> dict[int, int]:
    points = db.scalars(
        select(ScorePoint).where(
            ScorePoint.negotiation_id == negotiation_id,
            ScorePoint.is_active.is_(True),
        )
    ).all()
    return {p.user_id: p.score for p in points}


def _build_participants(db: Session, neg: Negotiation) -> list[ParticipantOut]:
    score_map = _participant_scores_map(db, neg.id)
    result: list[ParticipantOut] = []
    for uid in (neg.participant1_id, neg.participant2_id):
        if not uid:
            continue
        user = db.get(User, uid)
        if not user:
            continue
        public = user_to_public(user)
        result.append(
            ParticipantOut(
                id=user.id,
                username=public["username"],
                full_name=public["full_name"],
                score=score_map.get(user.id),
            )
        )
    return result


def _sender_label(msg: Message, name_by_id: dict[int, str]) -> str:
    if msg.sender_type == "ai":
        return "Нейросеть"
    if msg.sender_type == "system":
        return "Система"
    if msg.sender_id and msg.sender_id in name_by_id:
        return name_by_id[msg.sender_id]
    return "Участник"


def _serialize_message(msg: Message, viewer_id: int, name_by_id: dict[int, str] | None = None) -> MessageOut:
    labels = name_by_id or {}
    return MessageOut(
        id=msg.id,
        sender_id=msg.sender_id,
        sender_type=msg.sender_type,
        content=msg.content,
        created_at=msg.created_at,
        is_mine=msg.sender_id == viewer_id and msg.sender_type == "user",
        sender_label=_sender_label(msg, labels),
    )


def _serialize_negotiation(neg: Negotiation, viewer_id: int, db: Session | None = None) -> NegotiationOut:
    participants: list[ParticipantOut] = []
    name_by_id: dict[int, str] = {}
    if db is not None:
        participants = _build_participants(db, neg)
        name_by_id = {p.id: p.username for p in participants}

    return NegotiationOut(
        id=neg.id,
        mode=neg.mode,
        difficulty=neg.difficulty,
        scenario_id=neg.scenario_id,
        scenario_title=neg.scenario_title,
        status=neg.status,
        score=neg.score,
        participant1_id=neg.participant1_id,
        participant2_id=neg.participant2_id,
        current_turn_user_id=neg.current_turn_user_id,
        turn_deadline=neg.turn_deadline,
        created_at=neg.created_at,
        finished_at=neg.finished_at,
        messages=[_serialize_message(m, viewer_id, name_by_id) for m in neg.messages],
        participants=participants,
    )


def _user_negotiations_filter(user_id: int):
    return or_(Negotiation.participant1_id == user_id, Negotiation.participant2_id == user_id)


@router.get("/scenarios")
def scenarios():
    return list_scenarios_for_ui()


@router.get("/history", response_model=list[NegotiationListItem])
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Negotiation)
        .where(_user_negotiations_filter(user.id), Negotiation.status != "searching")
        .order_by(Negotiation.created_at.desc())
    ).all()
    result = []
    for neg in rows:
        count = db.scalar(
            select(func.count(Message.id)).where(Message.negotiation_id == neg.id)
        )
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
            )
        )
    return result


@router.get("/{negotiation_id}", response_model=NegotiationOut)
def get_negotiation(
    negotiation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    neg = db.scalar(
        select(Negotiation)
        .options(selectinload(Negotiation.messages))
        .where(Negotiation.id == negotiation_id)
    )
    if not neg:
        raise HTTPException(status_code=404, detail="Переговоры не найдены")
    if user.role != "admin" and user.id not in {neg.participant1_id, neg.participant2_id}:
        raise HTTPException(status_code=403, detail="Нет доступа")
    return _serialize_negotiation(neg, user.id, db)


@router.post("/ai/start", response_model=NegotiationOut)
async def start_ai(
    payload: StartAiRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_user(user)
    scenario = get_scenario(payload.scenario_id)
    if not scenario:
        raise HTTPException(status_code=400, detail="Сценарий недоступен")
    if payload.difficulty not in {"easy", "medium", "hard"}:
        raise HTTPException(status_code=400, detail="Некорректная сложность")

    neg = Negotiation(
        mode="ai",
        difficulty=payload.difficulty,
        scenario_id=scenario["id"],
        scenario_title=scenario["name"],
        status="active",
        participant1_id=user.id,
        current_turn_user_id=None if payload.ai_starts else user.id,
    )
    db.add(neg)
    db.commit()
    db.refresh(neg)

    if payload.ai_starts:
        opening = scenario.get("opening_ai") or await generate_ai_reply(
            scenario, payload.difficulty, [], None
        )
        msg = Message(
            negotiation_id=neg.id,
            sender_id=None,
            sender_type="ai",
            content=opening,
        )
        db.add(msg)
        neg.current_turn_user_id = user.id
        db.add(neg)
        db.commit()

    neg = db.scalar(
        select(Negotiation)
        .options(selectinload(Negotiation.messages))
        .where(Negotiation.id == neg.id)
    )
    return _serialize_negotiation(neg, user.id, db)


@router.post("/{negotiation_id}/messages", response_model=NegotiationOut)
async def send_message(
    negotiation_id: int,
    payload: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_user(user)
    neg = db.scalar(
        select(Negotiation)
        .options(selectinload(Negotiation.messages))
        .where(Negotiation.id == negotiation_id)
    )
    if not neg:
        raise HTTPException(status_code=404, detail="Переговоры не найдены")
    if neg.status != "active":
        raise HTTPException(status_code=400, detail="Переговоры уже завершены")
    if user.id not in {neg.participant1_id, neg.participant2_id}:
        raise HTTPException(status_code=403, detail="Нет доступа")

    text = payload.content.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Пустое сообщение")

    # Проверка таймера хода для human
    if neg.mode == "human":
        if neg.current_turn_user_id and neg.current_turn_user_id != user.id:
            raise HTTPException(status_code=400, detail="Сейчас ход оппонента")
        if neg.turn_deadline and as_utc(utcnow()) > as_utc(neg.turn_deadline):
            await _finish_negotiation(db, neg, reason="timeout")
            raise HTTPException(status_code=400, detail="Время хода истекло, переговоры завершены")

    user_msg = Message(
        negotiation_id=neg.id,
        sender_id=user.id,
        sender_type="user",
        content=text,
    )
    db.add(user_msg)
    db.commit()

    if neg.mode == "ai":
        scenario = get_scenario(neg.scenario_id)
        history = [
            {"sender_type": m.sender_type, "content": m.content} for m in neg.messages
        ] + [{"sender_type": "user", "content": text}]
        reply = await generate_ai_reply(scenario, neg.difficulty, history[:-1], text)
        ai_msg = Message(
            negotiation_id=neg.id,
            sender_id=None,
            sender_type="ai",
            content=reply,
        )
        db.add(ai_msg)
        neg.current_turn_user_id = user.id
        db.add(neg)
        db.commit()
    else:
        # human: передаём ход оппоненту
        opponent_id = (
            neg.participant2_id if user.id == neg.participant1_id else neg.participant1_id
        )
        settings = get_settings()
        neg.current_turn_user_id = opponent_id
        neg.turn_deadline = utcnow() + timedelta(seconds=settings.turn_seconds)
        db.add(neg)
        db.commit()
        await hub.broadcast(
            neg.id,
            {
                "type": "message",
                "negotiation_id": neg.id,
                "message": {
                    "id": user_msg.id,
                    "sender_id": user.id,
                    "sender_type": "user",
                    "content": text,
                    "created_at": user_msg.created_at.isoformat() if user_msg.created_at else None,
                },
                "current_turn_user_id": neg.current_turn_user_id,
                "turn_deadline": neg.turn_deadline.isoformat() if neg.turn_deadline else None,
            },
            exclude=None,
        )

    neg = db.scalar(
        select(Negotiation)
        .options(selectinload(Negotiation.messages))
        .where(Negotiation.id == neg.id)
    )
    return _serialize_negotiation(neg, user.id, db)


@router.post("/{negotiation_id}/finish", response_model=NegotiationOut)
async def finish_negotiation(
    negotiation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_user(user)
    neg = db.scalar(
        select(Negotiation)
        .options(selectinload(Negotiation.messages))
        .where(Negotiation.id == negotiation_id)
    )
    if not neg:
        raise HTTPException(status_code=404, detail="Переговоры не найдены")
    if user.id not in {neg.participant1_id, neg.participant2_id}:
        raise HTTPException(status_code=403, detail="Нет доступа")
    if neg.status != "active":
        return _serialize_negotiation(neg, user.id, db)

    await _finish_negotiation(db, neg, reason="manual")
    neg = db.scalar(
        select(Negotiation)
        .options(selectinload(Negotiation.messages))
        .where(Negotiation.id == neg.id)
    )
    return _serialize_negotiation(neg, user.id, db)


@router.post("/{negotiation_id}/check-timeout", response_model=NegotiationOut)
async def check_timeout(
    negotiation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    neg = db.scalar(
        select(Negotiation)
        .options(selectinload(Negotiation.messages))
        .where(Negotiation.id == negotiation_id)
    )
    if not neg:
        raise HTTPException(status_code=404, detail="Переговоры не найдены")
    if user.id not in {neg.participant1_id, neg.participant2_id} and user.role != "admin":
        raise HTTPException(status_code=403, detail="Нет доступа")
    if (
        neg.mode == "human"
        and neg.status == "active"
        and neg.turn_deadline
        and as_utc(utcnow()) > as_utc(neg.turn_deadline)
    ):
        await _finish_negotiation(db, neg, reason="timeout")
        neg = db.scalar(
            select(Negotiation)
            .options(selectinload(Negotiation.messages))
            .where(Negotiation.id == neg.id)
        )
    return _serialize_negotiation(neg, user.id, db)


async def _finish_negotiation(db: Session, neg: Negotiation, reason: str) -> None:
    if neg.status != "active":
        return
    neg.status = "pending_review"
    neg.finished_at = utcnow()
    neg.turn_deadline = None
    system = Message(
        negotiation_id=neg.id,
        sender_id=None,
        sender_type="system",
        content=(
            "Время хода истекло. Переговоры отправлены на проверку администратору."
            if reason == "timeout"
            else "Переговоры завершены и отправлены на проверку администратору."
        ),
    )
    db.add(system)
    db.add(neg)
    db.commit()
    await hub.broadcast(
        neg.id,
        {
            "type": "finished",
            "negotiation_id": neg.id,
            "reason": reason,
            "status": neg.status,
        },
    )


@router.post("/human/match")
async def create_or_join_match(
    payload: StartAiRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """REST-заглушка: фактический матчмейкинг идёт через WebSocket."""
    _ensure_user(user)
    scenario = get_scenario(payload.scenario_id)
    if not scenario:
        raise HTTPException(status_code=400, detail="Сценарий недоступен")
    return {
        "ok": True,
        "scenario_id": scenario["id"],
        "difficulty": payload.difficulty,
        "hint": "Подключитесь к /ws и отправьте action=search",
    }
