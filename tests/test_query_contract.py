from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import EmbeddingJobRecord
from app.embeddings import LocalHashEmbeddingProvider
from app.ingestion.service import DocumentIngestionService, IngestDocumentCommand
from app.jobs.embedding_processor import EmbeddingJobProcessor
from app.main import app


def test_query_endpoint_returns_empty_citations_when_no_embeddings(
    app_with_test_db: None,
) -> None:
    response = TestClient(app).post("/query", json={"question": "What is this platform?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "No embedded document chunks matched the query and metadata filter."
    assert body["citations"] == []


def test_query_endpoint_returns_retrieved_citations(
    app_with_test_db: None,
    db_session: Session,
) -> None:
    ingest_and_embed(
        db_session,
        source="sample/platform.md",
        title="Platform Overview",
        text="AI KnowledgeOps indexes internal documents for retrieval and citations.",
        metadata={"team": "ai-platform", "kind": "overview"},
    )

    response = TestClient(app).post(
        "/query",
        json={
            "question": "How does KnowledgeOps support retrieval?",
            "metadata_filter": {"team": "ai-platform"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "Retrieved relevant document chunks" in body["answer"]
    assert len(body["citations"]) == 1
    citation = body["citations"][0]
    assert citation["title"] == "Platform Overview"
    assert citation["source"] == "sample/platform.md"
    assert citation["metadata"]["team"] == "ai-platform"
    assert citation["metadata"]["kind"] == "overview"
    assert (
        citation["text"]
        == "AI KnowledgeOps indexes internal documents for retrieval and citations."
    )
    assert isinstance(citation["score"], float)


def test_query_endpoint_applies_metadata_filter(
    app_with_test_db: None,
    db_session: Session,
) -> None:
    ingest_and_embed(
        db_session,
        source="sample/platform.md",
        title="Platform Overview",
        text="Platform retrieval details.",
        metadata={"team": "ai-platform"},
    )

    response = TestClient(app).post(
        "/query",
        json={
            "question": "retrieval",
            "metadata_filter": {"team": "security"},
        },
    )

    assert response.status_code == 200
    assert response.json()["citations"] == []


def ingest_and_embed(
    session: Session,
    source: str,
    title: str,
    text: str,
    metadata: dict[str, str],
) -> None:
    result = DocumentIngestionService().ingest(
        session,
        IngestDocumentCommand(
            source=source,
            title=title,
            text=text,
            metadata=metadata,
        ),
    )
    job = session.scalar(
        select(EmbeddingJobRecord).where(EmbeddingJobRecord.document_id == result.document.id)
    )
    assert job is not None
    EmbeddingJobProcessor(provider=LocalHashEmbeddingProvider()).process_pending(session)
