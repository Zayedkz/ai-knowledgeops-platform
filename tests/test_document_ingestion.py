from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk, EmbeddingJobRecord
from app.ingestion.service import DocumentIngestionService, IngestDocumentCommand


def test_ingestion_persists_document_chunks_and_embedding_jobs(db_session: Session) -> None:
    service = DocumentIngestionService()
    command = IngestDocumentCommand(
        source="sample/runbook.md",
        title="Runbook",
        text=" ".join(f"word{i}" for i in range(520)),
        metadata={"team": "platform"},
    )

    result = service.ingest(db_session, command)

    assert result.created is True
    assert result.document.source == "sample/runbook.md"
    assert result.document.document_metadata == {"team": "platform"}

    chunks = db_session.scalars(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == result.document.id)
        .order_by(DocumentChunk.chunk_index)
    ).all()
    jobs = db_session.scalars(select(EmbeddingJobRecord)).all()

    assert len(chunks) == 3
    assert len(jobs) == 3
    assert chunks[0].chunk_index == 0
    assert chunks[0].chunk_metadata["team"] == "platform"
    assert {job.status for job in jobs} == {"pending"}


def test_ingestion_is_idempotent_by_source_and_content_hash(db_session: Session) -> None:
    service = DocumentIngestionService()
    command = IngestDocumentCommand(
        source="sample/overview.md",
        title="Overview",
        text="This content should only be stored once.",
        metadata={"source_type": "markdown"},
    )

    first = service.ingest(db_session, command)
    second = service.ingest(db_session, command)

    documents = db_session.scalars(select(Document)).all()
    chunks = db_session.scalars(select(DocumentChunk)).all()
    jobs = db_session.scalars(select(EmbeddingJobRecord)).all()

    assert first.created is True
    assert second.created is False
    assert first.document.id == second.document.id
    assert len(documents) == 1
    assert len(chunks) == 1
    assert len(jobs) == 1

