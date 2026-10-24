"""GET /api/health - the working smoke path.

Deliberately dependency-free: it must answer even when Supabase or Gemini is
unconfigured, so Render's health check passes before secrets are set.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Liveness/configuration summary. Never includes secrets."""

    status: str = "ok"
    environment: str
    llm_provider: str
    data_backend: str
    database_configured: bool
    max_tool_calls: int


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Report that the API is up and whether optional services are configured."""
    settings = get_settings()
    return HealthResponse(
        environment=settings.environment,
        llm_provider=settings.resolved_llm_provider,
        data_backend=settings.resolved_data_backend,
        database_configured=settings.database_configured,
        max_tool_calls=settings.max_tool_calls,
    )
