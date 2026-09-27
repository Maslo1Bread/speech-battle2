from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Negotiation, User
from ..security import decode_access_token
from ..services.human_match import cancel_search, search_or_match
from ..services.matchmaking import hub
from ..services.scenarios import get_scenario

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
                result = search_or_match(db, user.id, scenario_id, difficulty)
                if result.get("status") != "matched":
                    continue

                payload = {k: v for k, v in result.items() if k != "status"}
                payload["type"] = "matched"
                await hub.bind_room(result["negotiation_id"], [result["participant1_id"], result["participant2_id"]])
                await hub.send_to_user(result["participant1_id"], payload)
                await hub.send_to_user(result["participant2_id"], payload)

            elif action == "cancel_search":
                cancelled = cancel_search(db, user.id)
                await hub.cancel(user.id)
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
