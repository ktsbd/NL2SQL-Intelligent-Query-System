import json

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.db.models import AgentTrace, AgentTraceEvent
from app.db.session import SessionLocal

router = APIRouter(prefix="/traces", tags=["traces"])


@router.get("")
def list_traces(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
    with SessionLocal() as session:
        rows = session.execute(
            select(AgentTrace).order_by(AgentTrace.id.desc()).limit(limit)
        ).scalars().all()
        trace_ids = [item.trace_id for item in rows]
        events = session.execute(
            select(AgentTraceEvent)
            .where(AgentTraceEvent.trace_id.in_(trace_ids))
            .order_by(AgentTraceEvent.id)
        ).scalars().all() if trace_ids else []
    events_by_trace: dict[str, list[AgentTraceEvent]] = {}
    for event in events:
        events_by_trace.setdefault(event.trace_id, []).append(event)
    return {
        "items": [
            {
                "trace_id": item.trace_id,
                "session_id": item.session_id,
                "question": item.question,
                "rewritten_question": item.rewritten_question,
                "route": item.route,
                "status": item.status,
                "steps": _loads(item.steps_json, []),
                "sql": item.sql_text,
                "duration_ms": item.duration_ms,
                "error_message": item.error_message,
                "events": [
                    {
                        "node_name": event.node_name,
                        "status": event.status,
                        "duration_ms": event.duration_ms,
                        "model_name": event.model_name,
                        "estimated_input_chars": event.estimated_input_chars,
                        "estimated_output_chars": event.estimated_output_chars,
                        "error_message": event.error_message,
                        "created_at": event.created_at.isoformat(),
                    }
                    for event in events_by_trace.get(item.trace_id, [])
                ],
                "created_at": item.created_at.isoformat(),
            }
            for item in rows
        ]
    }


def _loads(value: str, fallback):
    try:
        return json.loads(value)
    except Exception:
        return fallback
