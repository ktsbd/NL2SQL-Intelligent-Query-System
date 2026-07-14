from __future__ import annotations

import json
import time
from contextlib import contextmanager
from uuid import uuid4

from app.db.models import AgentTrace, AgentTraceEvent
from app.db.session import SessionLocal


class TraceLogger:
    def __init__(self, question: str, session_id: str | None = None) -> None:
        self.trace_id = uuid4().hex
        self.started_at = time.perf_counter()
        with SessionLocal() as session:
            session.add(AgentTrace(trace_id=self.trace_id, session_id=session_id, question=question))
            session.commit()

    def finish(
        self,
        *,
        status: str,
        route: str = "",
        rewritten_question: str = "",
        steps: list[str] | None = None,
        sql: str = "",
        context: list[dict[str, object]] | None = None,
        tool_results: list[dict[str, object]] | None = None,
        error_message: str = "",
    ) -> None:
        duration_ms = int((time.perf_counter() - self.started_at) * 1000)
        with SessionLocal() as session:
            trace = session.query(AgentTrace).filter(AgentTrace.trace_id == self.trace_id).one_or_none()
            if trace is None:
                return
            trace.status = status
            trace.route = route
            trace.rewritten_question = rewritten_question
            trace.steps_json = self._json(steps or [])
            trace.sql_text = sql
            trace.context_json = self._json(context or [])
            trace.tool_results_json = self._json(tool_results or [])
            trace.error_message = error_message
            trace.duration_ms = duration_ms
            session.commit()

    def event(
        self,
        *,
        node_name: str,
        status: str = "success",
        input_data: object | None = None,
        output_data: object | None = None,
        error_message: str = "",
        duration_ms: int = 0,
        model_name: str = "",
    ) -> None:
        input_json = self._json(input_data or {})
        output_json = self._json(output_data or {})
        with SessionLocal() as session:
            session.add(
                AgentTraceEvent(
                    trace_id=self.trace_id,
                    node_name=node_name,
                    status=status,
                    input_json=input_json,
                    output_json=output_json,
                    error_message=error_message,
                    duration_ms=duration_ms,
                    model_name=model_name,
                    estimated_input_chars=len(input_json),
                    estimated_output_chars=len(output_json),
                )
            )
            session.commit()

    @contextmanager
    def span(self, node_name: str, input_data: object | None = None, model_name: str = ""):
        started_at = time.perf_counter()
        try:
            yield
        except Exception as exc:
            self.event(
                node_name=node_name,
                status="error",
                input_data=input_data,
                error_message=str(exc),
                duration_ms=int((time.perf_counter() - started_at) * 1000),
                model_name=model_name,
            )
            raise
        else:
            self.event(
                node_name=node_name,
                input_data=input_data,
                duration_ms=int((time.perf_counter() - started_at) * 1000),
                model_name=model_name,
            )

    def _json(self, value: object) -> str:
        return json.dumps(value, ensure_ascii=False, default=str)
