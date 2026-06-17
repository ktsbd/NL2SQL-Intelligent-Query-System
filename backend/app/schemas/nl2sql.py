from pydantic import BaseModel, Field


class NL2SQLRequest(BaseModel):
    question: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=50)


class RetrievedContext(BaseModel):
    object_name: str
    business_name: str
    description: str
    rank_score: float
    sources: list[str]


class NL2SQLResponse(BaseModel):
    question: str
    intent: str
    sql: str
    steps: list[str]
    context: list[RetrievedContext]
    columns: list[str]
    rows: list[dict[str, object]]
