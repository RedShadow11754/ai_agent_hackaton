"""Tool: search internal guidance and return real database IDs."""

from __future__ import annotations

from app.db import repositories
from app.schemas.tools import SearchGuidanceInput, SearchGuidanceOutput


async def search_guidance(payload: SearchGuidanceInput) -> SearchGuidanceOutput:
    """Return matching guidance passages (IDs such as SEC-01).

    Only IDs that exist in the `guidance` table may be returned; the model must
    never invent citations. An empty result is valid and is surfaced as "no
    matching guidance", never as reassurance.
    """
    query = payload.query.strip()
    limit = payload.limit

    try:
        results = await repositories.search_guidance(query, limit) if query else []
        if not results:
            # Fall back to the general passages so the analyst still gets advice.
            results = await repositories.search_guidance("general", limit)
    except Exception:  # noqa: BLE001 - guidance is helpful, not essential
        results = []

    return SearchGuidanceOutput(query=query, results=results)
