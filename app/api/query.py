from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.retrieval.models import Citation

router = APIRouter(tags=["query"])


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    metadata_filter: dict[str, str] | None = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]


@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    answer = (
        "Retrieval and generation providers are not connected yet. "
        "This scaffold returns the contract that future RAG responses will follow."
    )
    return QueryResponse(answer=answer, citations=[])

