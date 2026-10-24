"""Shared FastAPI dependencies: database client, LLM client, rate limiting."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Any

from fastapi import HTTPException, Request, status

from app.config import Settings, get_settings
from app.db.client import get_supabase_client
from app.llm.base import LLMClient
from app.llm.fake import FakeLLMClient
from app.llm.gemini import GeminiClient


def get_db_client() -> Any:
    """Return the cached Supabase client (service role, backend only).

    Raises:
        RuntimeError: when Supabase env vars are missing. The health route does
            not depend on this, so the app still starts without a database.
    """
    return get_supabase_client()


def get_llm_client() -> LLMClient:
    """Return the configured LLM adapter.

    `LLM_PROVIDER=fake` (or `auto` with no key) selects the deterministic
    offline stub, which needs no API key and makes no network calls.
    """
    settings: Settings = get_settings()
    if settings.resolved_llm_provider == "fake":
        return FakeLLMClient()
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "LLM_NOT_CONFIGURED",
                "message": "GEMINI_API_KEY is not set. Configure it or use LLM_PROVIDER=fake.",
            },
        )
    return GeminiClient(settings.gemini_api_key, settings.gemini_model)


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
# Simple in-process sliding window, good enough for a single free-tier instance.
# TODO: move to a shared store (e.g. Upstash Redis) if the service is scaled out.
_WINDOW_SECONDS = 60.0
_HITS: dict[str, deque[float]] = defaultdict(deque)


async def enforce_rate_limit(request: Request) -> None:
    """Dependency that rejects callers exceeding RATE_LIMIT_PER_MINUTE.

    Raises:
        HTTPException: 429 with the shared error envelope when the limit is hit.
    """
    settings = get_settings()
    limit = settings.rate_limit_per_minute
    if limit <= 0:
        return

    client_key = request.client.host if request.client else "unknown"
    now = time.monotonic()
    hits = _HITS[client_key]

    while hits and now - hits[0] > _WINDOW_SECONDS:
        hits.popleft()

    if len(hits) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "RATE_LIMITED",
                "message": f"Too many requests. Limit is {limit} per minute.",
            },
        )

    hits.append(now)
