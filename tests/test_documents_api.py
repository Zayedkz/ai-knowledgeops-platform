from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document
from app.main import app


def test_ingest_document_endpoint_persists_document(
    app_with_test_db: None,
    db_session: Session,
) -> None:
    response = TestClient(app).post(
        "/documents",
        json={
            "source": "sample/platform-overview.md",
            "title": "Platform Overview",
            "text": "AI KnowledgeOps indexes internal documents for retrieval.",
            "metadata": {"team": "ai-platform"},
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["created"] is True
    assert body["chunk_count"] == 1
    assert body["embedding_job_count"] == 1

    document = db_session.scalar(select(Document))
    assert document is not None
    assert document.id == body["document_id"]
    assert document.document_metadata == {"team": "ai-platform"}


def test_ingest_document_endpoint_returns_existing_document_for_duplicate(
    app_with_test_db: None,
) -> None:
    client = TestClient(app)
    payload = {
        "source": "sample/platform-overview.md",
        "title": "Platform Overview",
        "text": "Duplicate content is idempotent.",
        "metadata": {"team": "ai-platform"},
    }

    first = client.post("/documents", json=payload)
    second = client.post("/documents", json=payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["created"] is True
    assert second.json()["created"] is False
    assert first.json()["document_id"] == second.json()["document_id"]

