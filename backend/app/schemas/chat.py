from pydantic import BaseModel, Field

from app.schemas.nl2sql import RetrievedContext


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


class ChatResponse(BaseModel):
    session_id: str
    route: str
    answer: str
    question: str
    intent: str | None = None
    sql: str | None = None
    steps: list[str] = Field(default_factory=list)
    context: list[RetrievedContext] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, object]] = Field(default_factory=list)
    matched_skills: list[dict[str, object]] = Field(default_factory=list)
    tool_results: list[dict[str, object]] = Field(default_factory=list)
    history: list[dict[str, str]] = Field(default_factory=list)
