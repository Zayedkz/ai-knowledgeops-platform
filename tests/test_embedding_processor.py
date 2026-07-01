from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DocumentChunk, EmbeddingJobRecord
from app.embeddings import LocalHashEmbeddingProvider
from app.ingestion.service import DocumentIngestionService, IngestDocumentCommand
from app.jobs.embedding_processor import (
    COMPLETED,
    FAILED,
    IN_PROGRESS,
    PENDING,
    EmbeddingJobProcessor,
)


class FailingEmbeddingProvider:
    def embed(self, text: str) -> list[float]:
        raise RuntimeError("provider unavailable")


def ingest_one_chunk(session: Session) -> EmbeddingJobRecord:
    result = DocumentIngestionService().ingest(
        session,
        IngestDocumentCommand(
            source="sample/embedding.md",
            title="Embedding Sample",
            text="A short document chunk for embedding.",
            metadata={"team": "ai-platform"},
        ),
    )
    return session.scalar(
        select(EmbeddingJobRecord).where(EmbeddingJobRecord.document_id == result.document.id)
    )


def test_processor_embeds_pending_job_and_marks_completed(db_session: Session) -> None:
    job = ingest_one_chunk(db_session)
    processor = EmbeddingJobProcessor(provider=LocalHashEmbeddingProvider(dimensions=4))

    result = processor.process_pending(db_session, limit=10)

    db_session.refresh(job)
    chunk = db_session.get(DocumentChunk, job.chunk_id)
    assert result.processed == 1
    assert result.completed == 1
    assert result.failed == 0
    assert job.status == COMPLETED
    assert job.attempts == 0
    assert job.last_error is None
    assert job.locked_at is None
    assert job.locked_by is None
    assert chunk is not None
    assert len(chunk.embedding) == 4


def test_processor_skips_completed_jobs_on_rerun(db_session: Session) -> None:
    job = ingest_one_chunk(db_session)
    processor = EmbeddingJobProcessor(provider=LocalHashEmbeddingProvider(dimensions=4))

    first = processor.process_pending(db_session, limit=10)
    second = processor.process_pending(db_session, limit=10)

    db_session.refresh(job)
    assert first.processed == 1
    assert second.processed == 0
    assert job.status == COMPLETED


def test_processor_marks_job_failed_after_max_attempts(db_session: Session) -> None:
    job = ingest_one_chunk(db_session)
    processor = EmbeddingJobProcessor(provider=FailingEmbeddingProvider(), max_attempts=2)

    first = processor.process_pending(db_session, limit=10)
    second = processor.process_pending(db_session, limit=10)

    db_session.refresh(job)
    assert first.processed == 1
    assert first.failed == 1
    assert second.processed == 1
    assert second.failed == 1
    assert job.status == FAILED
    assert job.attempts == 2
    assert job.last_error == "provider unavailable"
    assert job.locked_at is None
    assert job.locked_by is None


def test_reset_failed_job_allows_idempotent_retry(db_session: Session) -> None:
    job = ingest_one_chunk(db_session)
    failing_processor = EmbeddingJobProcessor(provider=FailingEmbeddingProvider(), max_attempts=1)
    success_processor = EmbeddingJobProcessor(provider=LocalHashEmbeddingProvider(dimensions=4))

    failing_processor.process_pending(db_session, limit=10)
    db_session.refresh(job)
    assert job.status == FAILED

    EmbeddingJobProcessor.reset_failed_job(db_session, job)
    retried = success_processor.process_pending(db_session, limit=10)

    db_session.refresh(job)
    assert retried.processed == 1
    assert retried.completed == 1
    assert job.status == COMPLETED
    assert job.attempts == 1
    assert job.last_error is None
    assert job.locked_at is None
    assert job.locked_by is None


def test_pending_job_with_existing_embedding_is_completed_without_reembedding(
    db_session: Session,
) -> None:
    job = ingest_one_chunk(db_session)
    chunk = db_session.get(DocumentChunk, job.chunk_id)
    assert chunk is not None
    chunk.embedding = [0.1, 0.2, 0.3, 0.4]
    job.status = PENDING
    db_session.commit()

    result = EmbeddingJobProcessor(provider=FailingEmbeddingProvider()).process_pending(
        db_session, limit=10
    )

    db_session.refresh(job)
    db_session.refresh(chunk)
    assert result.processed == 1
    assert result.completed == 1
    assert result.skipped == 1
    assert job.status == COMPLETED
    assert chunk.embedding == [0.1, 0.2, 0.3, 0.4]


def test_processor_claims_pending_jobs_with_worker_lease(db_session: Session) -> None:
    job = ingest_one_chunk(db_session)
    processor = EmbeddingJobProcessor(
        provider=LocalHashEmbeddingProvider(dimensions=4),
        worker_id="test-worker",
    )

    claimed = processor._claim_next_jobs(db_session, limit=10)

    db_session.refresh(job)
    assert claimed == [job]
    assert job.status == IN_PROGRESS
    assert job.locked_at is not None
    assert job.locked_by == "test-worker"


def test_processor_ignores_fresh_in_progress_jobs(db_session: Session) -> None:
    job = ingest_one_chunk(db_session)
    job.status = IN_PROGRESS
    job.locked_at = datetime.now(UTC)
    job.locked_by = "other-worker"
    db_session.commit()

    processor = EmbeddingJobProcessor(
        provider=LocalHashEmbeddingProvider(dimensions=4),
        lease_timeout=timedelta(minutes=5),
    )

    result = processor.process_pending(db_session, limit=10)

    db_session.refresh(job)
    assert result.processed == 0
    assert job.status == IN_PROGRESS
    assert job.locked_by == "other-worker"


def test_processor_recovers_stale_in_progress_jobs(db_session: Session) -> None:
    job = ingest_one_chunk(db_session)
    stale_lock_time = datetime.now(UTC) - timedelta(minutes=30)
    job.status = IN_PROGRESS
    job.locked_at = stale_lock_time
    job.locked_by = "stale-worker"
    db_session.commit()

    processor = EmbeddingJobProcessor(
        provider=LocalHashEmbeddingProvider(dimensions=4),
        lease_timeout=timedelta(minutes=5),
        worker_id="recovering-worker",
    )

    result = processor.process_pending(db_session, limit=10)

    db_session.refresh(job)
    chunk = db_session.get(DocumentChunk, job.chunk_id)
    assert result.processed == 1
    assert result.completed == 1
    assert job.status == COMPLETED
    assert job.locked_at is None
    assert job.locked_by is None
    assert chunk is not None
    assert chunk.embedding is not None
