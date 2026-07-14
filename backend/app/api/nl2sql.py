import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.nl2sql import NL2SQLRequest, NL2SQLResponse
from app.services.nl2sql_service import NL2SQLService
from app.services.sql_executor import SQLValidationError

router = APIRouter(prefix="/nl2sql", tags=["nl2sql"])


@router.post("/query", response_model=NL2SQLResponse)
def query(request: NL2SQLRequest) -> dict[str, object]:
    try:
        return NL2SQLService().query(request.question, limit=request.limit, confirmed=request.confirmed)
    except (SQLValidationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/stream")
def stream_query(request: NL2SQLRequest) -> StreamingResponse:
    def event_stream():
        service = NL2SQLService()
        try:
            yield _sse("step", {"name": "parse_intent", "message": "解析查询意图"})
            yield _sse("step", {"name": "retrieve_context", "message": "检索元数据上下文"})
            yield _sse("step", {"name": "generate_sql", "message": "生成并校验 SQL"})
            result = service.query(request.question, limit=request.limit, confirmed=request.confirmed)
            yield _sse("sql", {"sql": result["sql"], "intent": result["intent"]})
            yield _sse("context", {"items": result["context"]})
            yield _sse("result", result)
            yield _sse("done", {"ok": True})
        except Exception as exc:
            yield _sse("error", {"message": str(exc)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"
