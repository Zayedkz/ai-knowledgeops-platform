from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.ingestion.service import DocumentIngestionService, IngestDocumentCommand

router = APIRouter(prefix="/documents", tags=["documents"])
DbSession = Depends(get_db_session)


class IngestDocumentRequest(BaseModel):
    source: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=500)
    text: str = Field(min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)


class IngestDocumentResponse(BaseModel):
    document_id: str
    created: bool
    chunk_count: int
    embedding_job_count: int


@router.post("", response_model=IngestDocumentResponse, status_code=status.HTTP_201_CREATED)
def ingest_document(
    request: IngestDocumentRequest,
    session: Session = DbSession,
) -> IngestDocumentResponse:
    result = DocumentIngestionService().ingest(
        session,
        IngestDocumentCommand(
            source=request.source,
            title=request.title,
            text=request.text,
            metadata=request.metadata,
        ),
    )
    return IngestDocumentResponse(
        document_id=result.document.id,
        created=result.created,
        chunk_count=len(result.document.chunks),
        embedding_job_count=len(result.document.embedding_jobs),
    )
