from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4

from sqlalchemy import delete, select

from app.db.models import ChatMessageRecord, ChatSession
from app.db.session import SessionLocal


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
        with SessionLocal() as session:
            existing = session.get(ChatSession, sid)
            if existing is None:
                session.add(ChatSession(id=sid))
                session.commit()
        return sid

    def add(self, session_id: str, role: str, content: str) -> None:
        message = ChatMessage(role=role, content=content, created_at=datetime.now(timezone.utc).isoformat())
        with self._lock:
            self._sessions.setdefault(session_id, deque(maxlen=self.max_messages)).append(message)
        with SessionLocal() as session:
            existing = session.get(ChatSession, session_id)
            if existing is None:
                existing = ChatSession(id=session_id)
                session.add(existing)
            existing.updated_at = datetime.utcnow()
            session.add(ChatMessageRecord(session_id=session_id, role=role, content=content))
            session.commit()

    def history(self, session_id: str, limit: int | None = None) -> list[dict[str, str]]:
        row_limit = limit or self.max_messages
        with SessionLocal() as session:
            rows = session.execute(
                select(ChatMessageRecord)
                .where(ChatMessageRecord.session_id == session_id)
                .order_by(ChatMessageRecord.id.desc())
                .limit(row_limit)
            ).scalars().all()
        if rows:
            return [
                {"role": item.role, "content": item.content, "created_at": item.created_at.replace(tzinfo=timezone.utc).isoformat()}
                for item in reversed(rows)
            ]

        with self._lock:
            messages = list(self._sessions.get(session_id, []))
        messages = messages[-row_limit:]
        return [{"role": item.role, "content": item.content, "created_at": item.created_at} for item in messages]

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
        with SessionLocal() as session:
            session.execute(delete(ChatMessageRecord).where(ChatMessageRecord.session_id == session_id))
            session.execute(delete(ChatSession).where(ChatSession.id == session_id))
            session.commit()


chat_memory = ShortTermChatMemory()
