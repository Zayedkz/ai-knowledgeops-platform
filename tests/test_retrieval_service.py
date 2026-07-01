from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk
from app.retrieval.service import EmbeddingRetriever, cosine_similarity


class StaticEmbeddingProvider:
    def embed(self, text: str) -> list[float]:
        match text:
            case "query":
                return [1.0, 0.0]
            case _:
                return [0.0, 1.0]


def test_cosine_similarity_scores_identical_vectors_highest() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine_similarity([1.0], [1.0, 0.0]) == 0.0


def test_retriever_orders_chunks_by_similarity(db_session: Session) -> None:
    matching = add_chunk(
        db_session,
        source="docs/matching.md",
        title="Matching",
        text="matching text",
        embedding=[1.0, 0.0],
        metadata={"team": "platform"},
    )
    add_chunk(
        db_session,
        source="docs/other.md",
        title="Other",
        text="other text",
        embedding=[0.0, 1.0],
        metadata={"team": "platform"},
    )

    result = EmbeddingRetriever(provider=StaticEmbeddingProvider()).retrieve(
        db_session,
        question="query",
        limit=2,
    )

    assert [citation.chunk_id for citation in result.citations] == [
        matching.id,
        db_session.query(DocumentChunk).filter_by(text="other text").one().id,
    ]
    assert result.citations[0].score == 1.0


def test_retriever_filters_by_chunk_metadata(db_session: Session) -> None:
    add_chunk(
        db_session,
        source="docs/platform.md",
        title="Platform",
        text="platform text",
        embedding=[1.0, 0.0],
        metadata={"team": "platform"},
    )
    security = add_chunk(
        db_session,
        source="docs/security.md",
        title="Security",
        text="security text",
        embedding=[1.0, 0.0],
        metadata={"team": "security"},
    )

    result = EmbeddingRetriever(provider=StaticEmbeddingProvider()).retrieve(
        db_session,
        question="query",
        metadata_filter={"team": "security"},
    )

    assert len(result.citations) == 1
    assert result.citations[0].chunk_id == security.id


def add_chunk(
    session: Session,
    source: str,
    title: str,
    text: str,
    embedding: list[float] | None,
    metadata: dict[str, str],
) -> DocumentChunk:
    document = Document(
        source=source,
        title=title,
        content_hash=source,
        document_metadata=metadata,
    )
    chunk = DocumentChunk(
        document=document,
        chunk_index=0,
        text=text,
        token_estimate=len(text.split()),
        chunk_metadata={"source": source, **metadata},
        embedding=embedding,
    )
    session.add(document)
    session.commit()
    session.refresh(chunk)
    return chunk
