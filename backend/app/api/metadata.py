from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.services.metadata_indexer import MetadataIndexer
from app.services.metadata_retriever import MetadataRetriever

router = APIRouter(prefix="/metadata", tags=["metadata"])


class RebuildIndexResponse(BaseModel):
    indexed: int


class MetadataSearchItem(BaseModel):
    id: int
    object_type: str
    object_name: str
    parent_name: str | None = None
    business_name: str
    description: str
    synonyms: str = ""
    example_values: str = ""
    rank_score: float
    sources: list[str] = Field(default_factory=list)


class MetadataSearchResponse(BaseModel):
    query: str
    results: list[MetadataSearchItem]


@router.post("/index", response_model=RebuildIndexResponse)
def rebuild_metadata_index() -> dict[str, int]:
    return MetadataIndexer().rebuild()


@router.get("/search", response_model=MetadataSearchResponse)
def search_metadata(
    q: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=20),
) -> dict[str, object]:
    results = MetadataRetriever().search(q, limit=limit)
    return {"query": q, "results": results}

