from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import DocumentChunk, EmbeddingJobRecord
from app.embeddings import EmbeddingProvider

PENDING = "pending"
COMPLETED = "completed"
FAILED = "failed"


@dataclass(frozen=True)
class EmbeddingJobProcessorResult:
    processed: int = 0
    completed: int = 0
    failed: int = 0
    skipped: int = 0


class EmbeddingJobProcessor:
    def __init__(self, provider: EmbeddingProvider, max_attempts: int = 3) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")

        self.provider = provider
        self.max_attempts = max_attempts

    def process_pending(self, session: Session, limit: int = 10) -> EmbeddingJobProcessorResult:
        if limit < 1:
            raise ValueError("limit must be positive")

        jobs = session.scalars(
            select(EmbeddingJobRecord)
            .options(selectinload(EmbeddingJobRecord.chunk))
            .where(EmbeddingJobRecord.status == PENDING)
            .order_by(EmbeddingJobRecord.created_at, EmbeddingJobRecord.id)
            .limit(limit)
        ).all()

        result = EmbeddingJobProcessorResult()
        for job in jobs:
            result = self._process_job(session, job, result)

        return result

    def _process_job(
        self,
        session: Session,
        job: EmbeddingJobRecord,
        result: EmbeddingJobProcessorResult,
    ) -> EmbeddingJobProcessorResult:
        if job.chunk is None:
            job.status = FAILED
            job.attempts += 1
            job.last_error = "document chunk is missing"
            session.commit()
            return self._add(result, processed=1, failed=1)

        if job.chunk.embedding is not None:
            job.status = COMPLETED
            job.last_error = None
            session.commit()
            return self._add(result, processed=1, completed=1, skipped=1)

        try:
            job.chunk.embedding = self.provider.embed(job.chunk.text)
        except Exception as exc:
            job.attempts += 1
            job.last_error = str(exc)
            if job.attempts >= self.max_attempts:
                job.status = FAILED
            session.commit()
            return self._add(result, processed=1, failed=1)

        job.status = COMPLETED
        job.last_error = None
        session.commit()
        return self._add(result, processed=1, completed=1)

    @staticmethod
    def reset_failed_job(session: Session, job: EmbeddingJobRecord) -> None:
        if job.status != FAILED:
            return

        chunk = session.get(DocumentChunk, job.chunk_id)
        if chunk is not None and chunk.embedding is not None:
            job.status = COMPLETED
            job.last_error = None
        else:
            job.status = PENDING
            job.last_error = None
        session.commit()

    @staticmethod
    def _add(
        result: EmbeddingJobProcessorResult,
        *,
        processed: int = 0,
        completed: int = 0,
        failed: int = 0,
        skipped: int = 0,
    ) -> EmbeddingJobProcessorResult:
        return EmbeddingJobProcessorResult(
            processed=result.processed + processed,
            completed=result.completed + completed,
            failed=result.failed + failed,
            skipped=result.skipped + skipped,
        )
