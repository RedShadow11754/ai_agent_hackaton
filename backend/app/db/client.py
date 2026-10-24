"""Backend-only Supabase client.

Uses the service role key, which bypasses RLS. Never import this module from
frontend code and never return the client or its credentials to a caller.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.config import get_settings


@lru_cache(maxsize=1)
def get_supabase_client() -> Any:
    """Create and cache the Supabase client.

    Raises:
        RuntimeError: when `SUPABASE_URL` or `SUPABASE_SERVICE_KEY` is missing.

    The `supabase` import is lazy so `/api/health` and the test suite can run
    without database configuration.

    TODO: add explicit timeouts, retry policy, and structured error mapping.
    """
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set for database access."
        )

    from supabase import create_client  # local import keeps startup lightweight

    return create_client(settings.supabase_url, settings.supabase_service_key)
