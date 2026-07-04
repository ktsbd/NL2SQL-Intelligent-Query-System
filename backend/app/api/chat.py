import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_memory import chat_memory
from app.services.chat_service import ChatService
from app.services.sql_executor import SQLValidationError

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
def chat_message(request: ChatRequest) -> dict[str, object]:
    try:
        return ChatService().chat(request.message, session_id=request.session_id, limit=request.limit)
    except (SQLValidationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/stream")
def stream_chat(request: ChatRequest) -> StreamingResponse:
    def event_stream():
        try:
            yield _sse("step", {"name": "route_intent", "message": "识别聊天意图"})
            yield _sse("step", {"name": "memory", "message": "读取短期记忆"})
            result = ChatService().chat(request.message, session_id=request.session_id, limit=request.limit)
            if result.get("sql"):
                yield _sse("step", {"name": "nl2sql", "message": "生成并执行 SQL"})
                yield _sse("sql", {"sql": result["sql"], "intent": result.get("intent")})
            yield _sse("result", result)
            yield _sse("done", {"ok": True, "session_id": result["session_id"]})
        except Exception as exc:
            yield _sse("error", {"message": str(exc)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.delete("/sessions/{session_id}")
def clear_session(session_id: str) -> dict[str, bool]:
    chat_memory.clear(session_id)
    return {"ok": True}


def _sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"
