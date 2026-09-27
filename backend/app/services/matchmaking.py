from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket


@dataclass
class QueueEntry:
    user_id: int
    scenario_id: str
    difficulty: str
    websocket: WebSocket


@dataclass
class RoomState:
    negotiation_id: int
    user_ids: set[int] = field(default_factory=set)
    sockets: dict[int, WebSocket] = field(default_factory=dict)


class MatchmakingHub:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._queue: list[QueueEntry] = []
        self._rooms: dict[int, RoomState] = {}
        self._user_socket: dict[int, WebSocket] = {}

    async def register_socket(self, user_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            self._user_socket[user_id] = websocket

    async def unregister_socket(self, user_id: int) -> None:
        async with self._lock:
            self._user_socket.pop(user_id, None)
            self._queue = [q for q in self._queue if q.user_id != user_id]
            for room in self._rooms.values():
                room.sockets.pop(user_id, None)

    async def enqueue(self, entry: QueueEntry) -> QueueEntry | None:
        """Добавляет в очередь. Если найден оппонент — возвращает его entry."""
        async with self._lock:
            # убрать предыдущие заявки того же пользователя
            self._queue = [q for q in self._queue if q.user_id != entry.user_id]
            for idx, other in enumerate(self._queue):
                if (
                    other.user_id != entry.user_id
                    and other.scenario_id == entry.scenario_id
                    and other.difficulty == entry.difficulty
                ):
                    matched = self._queue.pop(idx)
                    return matched
            self._queue.append(entry)
            return None

    async def cancel(self, user_id: int) -> bool:
        async with self._lock:
            before = len(self._queue)
            self._queue = [q for q in self._queue if q.user_id != user_id]
            return len(self._queue) < before

    async def bind_room(self, negotiation_id: int, user_ids: list[int]) -> None:
        async with self._lock:
            room = RoomState(negotiation_id=negotiation_id, user_ids=set(user_ids))
            for uid in user_ids:
                ws = self._user_socket.get(uid)
                if ws:
                    room.sockets[uid] = ws
            self._rooms[negotiation_id] = room

    async def attach_to_room(self, negotiation_id: int, user_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            room = self._rooms.get(negotiation_id)
            if not room:
                room = RoomState(negotiation_id=negotiation_id, user_ids={user_id})
                self._rooms[negotiation_id] = room
            room.user_ids.add(user_id)
            room.sockets[user_id] = websocket
            self._user_socket[user_id] = websocket

    async def broadcast(self, negotiation_id: int, payload: dict[str, Any], exclude: int | None = None) -> None:
        async with self._lock:
            room = self._rooms.get(negotiation_id)
            sockets = list(room.sockets.items()) if room else []
        dead: list[int] = []
        for uid, ws in sockets:
            if exclude is not None and uid == exclude:
                continue
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(uid)
        if dead:
            async with self._lock:
                room = self._rooms.get(negotiation_id)
                if room:
                    for uid in dead:
                        room.sockets.pop(uid, None)

    async def send_to_user(self, user_id: int, payload: dict[str, Any]) -> None:
        async with self._lock:
            ws = self._user_socket.get(user_id)
        if not ws:
            return
        try:
            await ws.send_json(payload)
        except Exception:
            pass


hub = MatchmakingHub()
