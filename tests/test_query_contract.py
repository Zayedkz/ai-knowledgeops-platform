from fastapi.testclient import TestClient

from app.main import app


def test_query_endpoint_returns_answer_contract() -> None:
    response = TestClient(app).post("/query", json={"question": "What is this platform?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"]
    assert body["citations"] == []

