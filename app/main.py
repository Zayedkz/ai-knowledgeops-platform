from fastapi import FastAPI

from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.query import router as query_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="AI KnowledgeOps Platform",
        version="0.1.0",
        description="Production-style RAG platform for answers with citations.",
    )
    app.state.settings = settings
    app.include_router(documents_router)
    app.include_router(health_router)
    app.include_router(query_router)
    return app


app = create_app()
