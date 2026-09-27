from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import ScorePoint, User


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def recalculate_overall_score(db: Session, user_id: int) -> float:
    avg = db.scalar(
        select(func.avg(ScorePoint.score)).where(
            ScorePoint.user_id == user_id,
            ScorePoint.is_active.is_(True),
        )
    )
    user = db.get(User, user_id)
    if not user:
        return 0.0
    user.overall_score = float(avg or 0.0)
    db.add(user)
    return user.overall_score


def apply_negotiation_score(db: Session, user_id: int, negotiation_id: int, score: int) -> None:
    # деактивируем предыдущие баллы по этому чату
    existing = db.scalars(
        select(ScorePoint).where(
            ScorePoint.user_id == user_id,
            ScorePoint.negotiation_id == negotiation_id,
            ScorePoint.is_active.is_(True),
        )
    ).all()
    for point in existing:
        point.is_active = False
        db.add(point)

    db.add(
        ScorePoint(
            user_id=user_id,
            negotiation_id=negotiation_id,
            score=score,
            is_active=True,
        )
    )
    db.flush()
    recalculate_overall_score(db, user_id)


def week_score_series(db: Session, user_id: int) -> list[dict]:
    since = utcnow() - timedelta(days=7)
    points = db.scalars(
        select(ScorePoint)
        .where(
            ScorePoint.user_id == user_id,
            ScorePoint.is_active.is_(True),
            ScorePoint.created_at >= since,
        )
        .order_by(ScorePoint.created_at.asc())
    ).all()
    return [{"score": p.score, "created_at": p.created_at} for p in points]


def difficulty_prompt(difficulty: str) -> str:
    mapping = {
        "easy": (
            "Сложность ЛЁГКАЯ: отвечай вяло, мягко, используй общие фразы, мифы и "
            "расхожие мнения без жёстких фактов. Легко иди на уступки, слабо аргументируй."
        ),
        "medium": (
            "Сложность СРЕДНЯЯ: балансируй между гибкостью и давлением. Приводи рабочие "
            "аргументы, иногда уступай, но требуй встречные условия."
        ),
        "hard": (
            "Сложность СЛОЖНАЯ: будь более агрессивным оппонентом. Используй весомые "
            "аргументы, цифры, риски, контраргументы. Жёстко парируй слабые формулировки."
        ),
    }
    return mapping.get(difficulty, mapping["medium"])


def local_ai_reply(scenario: dict, difficulty: str, history: list[dict], user_text: str) -> str:
    """Локальный бесплатный ответчик на случай недоступности внешнего LLM."""
    role = scenario.get("opponent_role", "Оппонент")
    goals = "; ".join(scenario.get("goals_opponent", []))
    soft = [
        "Ну… в целом звучит знакомо, многие так говорят.",
        "Давайте не усложнять — обычно в таких случаях договариваются на словах.",
        "Я слышал, что на рынке сейчас спокойнее, чем кажется.",
        "Может, обойдёмся без жёстких цифр и просто найдём компромисс?",
    ]
    mid = [
        "Понимаю ваш интерес, но мне тоже нужно закрыть свои цели.",
        "Готов обсуждать, если вы предложите встречный шаг.",
        "Давайте отделим желаемое от реалистичного в рамках нашего сценария.",
        "Могу сдвинуться, но не в одностороннем порядке.",
    ]
    hard = [
        "Это слабый аргумент без опоры на измеримый результат.",
        "По данным нашей практики такие уступки бьют по марже и срокам.",
        "Если настаивать в этой формулировке — я фиксирую отказ по этому пункту.",
        "Контраргумент: без компенсации рисков сделка для меня неприемлема.",
    ]
    pool = {"easy": soft, "medium": mid, "hard": hard}.get(difficulty, mid)
    opener = random.choice(pool)
    focus = random.choice(
        [
            f"Как {role.lower()}, для меня важно: {goals or 'удержать позицию'}.",
            f"В рамках сценария «{scenario.get('name')}» я не могу игнорировать свои ограничения.",
            "Ответьте конкретнее: что именно вы готовы дать взамен?",
        ]
    )
    echo = user_text.strip()
    if len(echo) > 120:
        echo = echo[:117] + "…"
    return f"{opener} Вы сказали: «{echo}». {focus}"
