from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import SessionLocal
from ..models import Message, Negotiation, User
from ..security import decode_access_token
from ..services.matchmaking import QueueEntry, hub
from ..services.scenarios import get_scenario
from ..services.scoring import utcnow

router = APIRouter(tags=["ws"])


def _user_from_token(token: str, db: Session) -> User | None:
    try:
        payload = decode_access_token(token)
        user = db.get(User, int(payload["sub"]))
        if user and user.status == "active":
            return user
    except Exception:
        return None
    return None


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    db = SessionLocal()
    user: User | None = None
    try:
        auth = await websocket.receive_json()
        if auth.get("type") != "auth" or not auth.get("token"):
            await websocket.send_json({"type": "error", "detail": "Требуется auth"})
            await websocket.close()
            return

        user = _user_from_token(auth["token"], db)
        if not user:
            await websocket.send_json({"type": "error", "detail": "Недействительный токен"})
            await websocket.close()
            return
        if user.role == "admin":
            await websocket.send_json({"type": "error", "detail": "Админ не участвует в переговорах"})
            await websocket.close()
            return

        await hub.register_socket(user.id, websocket)
        await websocket.send_json({"type": "ready", "user_id": user.id})

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "search":
                scenario_id = data.get("scenario_id")
                difficulty = data.get("difficulty", "easy")
                scenario = get_scenario(scenario_id)
                if not scenario:
                    await websocket.send_json({"type": "error", "detail": "Сценарий недоступен"})
                    continue
                if difficulty not in {"easy", "medium", "hard"}:
                    await websocket.send_json({"type": "error", "detail": "Некорректная сложность"})
                    continue

                await websocket.send_json({"type": "searching", "scenario_id": scenario_id})
                matched = await hub.enqueue(
                    QueueEntry(
                        user_id=user.id,
                        scenario_id=scenario_id,
                        difficulty=difficulty,
                        websocket=websocket,
                    )
                )
                if not matched:
                    continue

                # создаём переговоры для пары
                settings = get_settings()
                neg = Negotiation(
                    mode="human",
                    difficulty=difficulty,
                    scenario_id=scenario["id"],
                    scenario_title=scenario["name"],
                    status="active",
                    participant1_id=matched.user_id,
                    participant2_id=user.id,
                    current_turn_user_id=matched.user_id,
                    turn_deadline=utcnow() + timedelta(seconds=settings.turn_seconds),
                )
                db.add(neg)
                db.commit()
                db.refresh(neg)

                opener = Message(
                    negotiation_id=neg.id,
                    sender_id=None,
                    sender_type="system",
                    content=f"Оппонент найден. Сценарий: {scenario['name']}. На ход — 2 минуты.",
                )
                db.add(opener)
                db.commit()

                await hub.bind_room(neg.id, [matched.user_id, user.id])
                payload = {
                    "type": "matched",
                    "negotiation_id": neg.id,
                    "scenario_id": scenario["id"],
                    "scenario_title": scenario["name"],
                    "difficulty": difficulty,
                    "participant1_id": neg.participant1_id,
                    "participant2_id": neg.participant2_id,
                    "current_turn_user_id": neg.current_turn_user_id,
                    "turn_deadline": neg.turn_deadline.isoformat() if neg.turn_deadline else None,
                    "system_message": opener.content,
                }
                await hub.send_to_user(matched.user_id, payload)
                await hub.send_to_user(user.id, payload)

            elif action == "cancel_search":
                cancelled = await hub.cancel(user.id)
                await websocket.send_json({"type": "search_cancelled", "ok": cancelled})

            elif action == "typing":
                negotiation_id = data.get("negotiation_id")
                if negotiation_id:
                    await hub.broadcast(
                        int(negotiation_id),
                        {
                            "type": "typing",
                            "negotiation_id": int(negotiation_id),
                            "user_id": user.id,
                            "is_typing": bool(data.get("is_typing", True)),
                        },
                        exclude=user.id,
                    )

            elif action == "join_room":
                negotiation_id = int(data.get("negotiation_id"))
                neg = db.get(Negotiation, negotiation_id)
                if not neg or user.id not in {neg.participant1_id, neg.participant2_id}:
                    await websocket.send_json({"type": "error", "detail": "Нет доступа к комнате"})
                    continue
                await hub.attach_to_room(negotiation_id, user.id, websocket)
                await websocket.send_json({"type": "joined", "negotiation_id": negotiation_id})

            else:
                await websocket.send_json({"type": "error", "detail": f"Неизвестное действие: {action}"})

    except WebSocketDisconnect:
        pass
    finally:
        if user:
            await hub.unregister_socket(user.id)
        db.close()
