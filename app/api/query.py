from time import perf_counter

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import QueryEvent
from app.db.session import get_db_session
from app.embeddings import get_embedding_provider
from app.retrieval.models import Citation
from app.retrieval.service import EmbeddingRetriever

router = APIRouter(tags=["query"])
DbSession = Depends(get_db_session)


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    metadata_filter: dict[str, str] | None = None
    limit: int = Field(default=5, ge=1, le=20)


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]


@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest, session: Session = DbSession) -> QueryResponse:
    provider = get_embedding_provider(get_settings().embedding_provider)
    started_at = perf_counter()
    result = EmbeddingRetriever(provider=provider).retrieve(
        session=session,
        question=request.question,
        metadata_filter=request.metadata_filter,
        limit=request.limit,
    )
    latency_ms = max(0, round((perf_counter() - started_at) * 1000))

    session.add(
        QueryEvent(
            question=request.question,
            metadata_filter=request.metadata_filter,
            selected_chunk_ids=[citation.chunk_id for citation in result.citations],
            citation_scores=[
                {"chunk_id": citation.chunk_id, "score": citation.score}
                for citation in result.citations
            ],
            latency_ms=latency_ms,
        )
    )
    session.commit()

    if not result.citations:
        answer = "No embedded document chunks matched the query and metadata filter."
        return QueryResponse(answer=answer, citations=[])

    answer = (
        "Retrieved relevant document chunks. LLM answer generation is not connected yet, "
        "so use the returned citations as the grounded evidence."
    )
    return QueryResponse(answer=answer, citations=result.citations)
