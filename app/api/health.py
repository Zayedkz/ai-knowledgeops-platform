from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    environment: str


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    return HealthResponse(status="ok", environment=settings.app_env)

