from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import MatchTicket, Message, Negotiation
from .scenarios import get_scenario
from .scoring import utcnow


def matched_payload(neg: Negotiation, system_message: str | None = None) -> dict:
    return {
        "status": "matched",
        "type": "matched",
        "negotiation_id": neg.id,
        "scenario_id": neg.scenario_id,
        "scenario_title": neg.scenario_title,
        "difficulty": neg.difficulty,
        "participant1_id": neg.participant1_id,
        "participant2_id": neg.participant2_id,
        "current_turn_user_id": neg.current_turn_user_id,
        "turn_deadline": neg.turn_deadline.isoformat() if neg.turn_deadline else None,
        "system_message": system_message,
    }


def _opener_text(db: Session, negotiation_id: int) -> str | None:
    msg = db.scalar(
        select(Message)
        .where(Message.negotiation_id == negotiation_id, Message.sender_type == "system")
        .order_by(Message.id)
    )
    return msg.content if msg else None


def _create_pair(db: Session, first: MatchTicket, second: MatchTicket) -> Negotiation:
    scenario = get_scenario(first.scenario_id) or {}
    settings = get_settings()
    title = scenario.get("name") or first.scenario_id
    neg = Negotiation(
        mode="human",
        difficulty=first.difficulty,
        scenario_id=first.scenario_id,
        scenario_title=title,
        status="active",
        participant1_id=first.user_id,
        participant2_id=second.user_id,
        current_turn_user_id=first.user_id,
        turn_deadline=utcnow() + timedelta(seconds=settings.turn_seconds),
    )
    db.add(neg)
    db.flush()
    opener = Message(
        negotiation_id=neg.id,
        sender_id=None,
        sender_type="system",
        content=f"Оппонент найден. Сценарий: {title}. На ход — 2 минуты.",
    )
    db.add(opener)
    first.negotiation_id = neg.id
    second.negotiation_id = neg.id
    db.add(first)
    db.add(second)
    db.commit()
    db.refresh(neg)
    return neg


def _pair_waiting(db: Session) -> None:
    waiting = db.scalars(
        select(MatchTicket).where(MatchTicket.negotiation_id.is_(None)).order_by(MatchTicket.created_at)
    ).all()
    buckets: dict[tuple[str, str], list[MatchTicket]] = {}
    for ticket in waiting:
        buckets.setdefault((ticket.scenario_id, ticket.difficulty), []).append(ticket)
    for tickets in buckets.values():
        while len(tickets) >= 2:
            a = tickets.pop(0)
            b = tickets.pop(0)
            if a.user_id == b.user_id:
                tickets.insert(0, b)
                continue
            _create_pair(db, a, b)


def cancel_search(db: Session, user_id: int) -> bool:
    ticket = db.get(MatchTicket, user_id)
    if not ticket:
        return False
    if ticket.negotiation_id:
        return False
    db.delete(ticket)
    db.commit()
    return True


def search_or_match(db: Session, user_id: int, scenario_id: str, difficulty: str) -> dict:
    scenario = get_scenario(scenario_id)
    if not scenario:
        return {"status": "error", "detail": "Сценарий недоступен"}
    if difficulty not in {"easy", "medium", "hard"}:
        return {"status": "error", "detail": "Некорректная сложность"}

    existing = db.get(MatchTicket, user_id)
    if existing and not existing.negotiation_id:
        db.delete(existing)
        db.flush()
    elif existing and existing.negotiation_id:
        neg = db.get(Negotiation, existing.negotiation_id)
        if neg and neg.status == "active":
            return matched_payload(neg, _opener_text(db, neg.id))
        db.delete(existing)
        db.flush()

    opponent = db.scalar(
        select(MatchTicket)
        .where(
            MatchTicket.user_id != user_id,
            MatchTicket.scenario_id == scenario_id,
            MatchTicket.difficulty == difficulty,
            MatchTicket.negotiation_id.is_(None),
        )
        .order_by(MatchTicket.created_at)
    )
    mine = MatchTicket(
        user_id=user_id,
        scenario_id=scenario_id,
        difficulty=difficulty,
    )
    db.add(mine)
    db.flush()
    if opponent:
        neg = _create_pair(db, opponent, mine)
        return matched_payload(
            neg,
            _opener_text(db, neg.id)
            or f"Оппонент найден. Сценарий: {scenario['name']}. На ход — 2 минуты.",
        )

    db.commit()
    _pair_waiting(db)
    mine = db.get(MatchTicket, user_id)
    if mine and mine.negotiation_id:
        neg = db.get(Negotiation, mine.negotiation_id)
        if neg:
            return matched_payload(neg, _opener_text(db, neg.id))
    return {"status": "searching", "type": "searching", "scenario_id": scenario_id}


def search_status(db: Session, user_id: int) -> dict:
    _pair_waiting(db)
    ticket = db.get(MatchTicket, user_id)
    if not ticket:
        return {"status": "idle"}
    if ticket.negotiation_id:
        neg = db.get(Negotiation, ticket.negotiation_id)
        if not neg:
            db.delete(ticket)
            db.commit()
            return {"status": "idle"}
        if neg.status != "active":
            return {
                "status": "finished",
                "type": "finished",
                "negotiation_id": neg.id,
                "reason": "manual",
            }
        return matched_payload(neg, _opener_text(db, neg.id))
    return {"status": "searching", "type": "searching", "scenario_id": ticket.scenario_id}
