"""Read/write activity_log rows (tool calls, results, errors, approvals, saves)."""

from __future__ import annotations

import logging
from typing import Any, Literal

from app.db import repositories
from app.schemas.common import ActivityEntry

ActivityKind = Literal["tool_call", "tool_result", "error", "approval", "save"]

logger = logging.getLogger(__name__)


async def record_activity(
    *,
    investigation_id: str,
    kind: ActivityKind,
    tool_name: str | None = None,
    incident_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    """Append one activity row for auditability.

    Logging must never break an investigation, so datastore errors are caught
    and logged here instead of being raised. The in-response activity list is
    built separately by the agent loop, so a failed write loses only the
    persisted copy, not the investigation.
    """
    try:
        await repositories.insert_activity(
            investigation_id=investigation_id,
            kind=kind,
            tool_name=tool_name,
            incident_id=incident_id,
            payload=payload,
        )
    except Exception:  # noqa: BLE001 - audit logging must never raise
        logger.warning(
            "Could not persist activity row (kind=%s, tool=%s, investigation=%s).",
            kind,
            tool_name,
            investigation_id,
            exc_info=True,
        )


async def read_activity(
    *,
    investigation_id: str | None = None,
    incident_id: str | None = None,
) -> list[ActivityEntry]:
    """Return activity rows for an investigation or incident, oldest first.

    Raises:
        ValueError: when neither `investigation_id` nor `incident_id` is given.
    """
    if not investigation_id and not incident_id:
        raise ValueError("read_activity needs an investigation_id or an incident_id.")
    return await repositories.list_activity(
        investigation_id=investigation_id, incident_id=incident_id
    )
