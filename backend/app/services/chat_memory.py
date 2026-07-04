from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str
    created_at: str


class ShortTermChatMemory:
    def __init__(self, max_messages: int = 12) -> None:
        self.max_messages = max_messages
        self._sessions: dict[str, deque[ChatMessage]] = {}
        self._lock = RLock()

    def ensure_session(self, session_id: str | None = None) -> str:
        with self._lock:
            sid = session_id or uuid4().hex
            self._sessions.setdefault(sid, deque(maxlen=self.max_messages))
            return sid

    def add(self, session_id: str, role: str, content: str) -> None:
        message = ChatMessage(role=role, content=content, created_at=datetime.now(timezone.utc).isoformat())
        with self._lock:
            self._sessions.setdefault(session_id, deque(maxlen=self.max_messages)).append(message)

    def history(self, session_id: str, limit: int | None = None) -> list[dict[str, str]]:
        with self._lock:
            messages = list(self._sessions.get(session_id, []))
        if limit is not None:
            messages = messages[-limit:]
        return [
            {"role": item.role, "content": item.content, "created_at": item.created_at}
            for item in messages
        ]

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)


chat_memory = ShortTermChatMemory()
