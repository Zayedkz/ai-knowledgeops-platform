from dataclasses import dataclass
from math import sqrt

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import DocumentChunk
from app.embeddings import EmbeddingProvider
from app.retrieval.models import Citation


@dataclass(frozen=True)
class RetrievalResult:
    citations: list[Citation]


class EmbeddingRetriever:
    def __init__(self, provider: EmbeddingProvider) -> None:
        self.provider = provider

    def retrieve(
        self,
        session: Session,
        question: str,
        metadata_filter: dict[str, str] | None = None,
        limit: int = 5,
    ) -> RetrievalResult:
        query_embedding = self.provider.embed(question)
        chunks = session.scalars(
            select(DocumentChunk)
            .options(selectinload(DocumentChunk.document))
            .where(DocumentChunk.embedding.is_not(None))
            .order_by(DocumentChunk.created_at, DocumentChunk.id)
        ).all()

        scored: list[tuple[float, DocumentChunk]] = []
        for chunk in chunks:
            if not self._metadata_matches(chunk.chunk_metadata, metadata_filter):
                continue

            score = cosine_similarity(query_embedding, chunk.embedding or [])
            scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)

        citations = [
            Citation(
                document_id=chunk.document_id,
                chunk_id=chunk.id,
                title=chunk.document.title,
                source=chunk.document.source,
                score=round(score, 6),
                text=chunk.text,
                metadata=chunk.chunk_metadata,
            )
            for score, chunk in scored[:limit]
        ]
        return RetrievalResult(citations=citations)

    @staticmethod
    def _metadata_matches(
        chunk_metadata: dict[str, str],
        metadata_filter: dict[str, str] | None,
    ) -> bool:
        if not metadata_filter:
            return True

        return all(chunk_metadata.get(key) == value for key, value in metadata_filter.items())


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0

    dot_product = sum(
        left_value * right_value for left_value, right_value in zip(left, right, strict=True)
    )
    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return dot_product / (left_norm * right_norm)
