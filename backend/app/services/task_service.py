from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable
from uuid import uuid4

from app.db.models import BackgroundTaskRecord
from app.db.session import SessionLocal


executor = ThreadPoolExecutor(max_workers=2)


class TaskService:
    def mark_interrupted_tasks(self) -> int:
        with SessionLocal() as session:
            tasks = session.query(BackgroundTaskRecord).filter(BackgroundTaskRecord.status.in_(["pending", "running"])).all()
            for task in tasks:
                task.status = "failed"
                task.progress = 100
                task.error_message = "Task was interrupted by service restart."
            session.commit()
            return len(tasks)

    def submit(self, task_type: str, payload: dict[str, Any], fn: Callable[[], dict[str, Any]]) -> dict[str, object]:
        task_id = uuid4().hex
        with SessionLocal() as session:
            session.add(
                BackgroundTaskRecord(
                    id=task_id,
                    task_type=task_type,
                    status="pending",
                    progress=0,
                    input_json=json.dumps(payload, ensure_ascii=False, default=str),
                )
            )
            session.commit()
        executor.submit(self._run, task_id, fn)
        return {"task_id": task_id, "status": "pending"}

    def get(self, task_id: str) -> dict[str, object] | None:
        with SessionLocal() as session:
            task = session.get(BackgroundTaskRecord, task_id)
            if task is None:
                return None
            return {
                "task_id": task.id,
                "task_type": task.task_type,
                "status": task.status,
                "progress": task.progress,
                "input": self._loads(task.input_json, {}),
                "result": self._loads(task.result_json, {}),
                "error_message": task.error_message,
                "duration_ms": task.duration_ms,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
            }

    def _run(self, task_id: str, fn: Callable[[], dict[str, Any]]) -> None:
        started = time.perf_counter()
        self._update(task_id, status="running", progress=10)
        try:
            result = fn()
            self._update(
                task_id,
                status="success",
                progress=100,
                result=result,
                duration_ms=int((time.perf_counter() - started) * 1000),
            )
        except Exception as exc:
            self._update(
                task_id,
                status="failed",
                progress=100,
                error_message=str(exc),
                duration_ms=int((time.perf_counter() - started) * 1000),
            )

    def _update(
        self,
        task_id: str,
        *,
        status: str,
        progress: int,
        result: dict[str, Any] | None = None,
        error_message: str = "",
        duration_ms: int = 0,
    ) -> None:
        with SessionLocal() as session:
            task = session.get(BackgroundTaskRecord, task_id)
            if task is None:
                return
            task.status = status
            task.progress = progress
            task.error_message = error_message
            task.duration_ms = duration_ms
            if result is not None:
                task.result_json = json.dumps(result, ensure_ascii=False, default=str)
            session.commit()

    def _loads(self, value: str, fallback):
        try:
            return json.loads(value)
        except Exception:
            return fallback
