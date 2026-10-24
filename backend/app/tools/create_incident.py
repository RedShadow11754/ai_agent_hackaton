"""Approval-only incident persistence.

HARD RULE 2: this module is intentionally NOT imported by `app.agent.registry`.
The LLM must never see a `create_incident` tool. The only caller is
POST /api/incidents after it has verified `approved is True`.
"""

from __future__ import annotations

from app.db import repositories
from app.schemas.incidents import CreateIncidentRequest, IncidentCreatedResponse
from app.services.activity_log import record_activity


async def create_incident(
    payload: CreateIncidentRequest,
) -> IncidentCreatedResponse:
    """Insert an approved incident and its save/approval activity rows.

    Preconditions:
    - `payload.approved is True` (also enforced by the route);
    - the assessment passed evidence validation.

    Raises:
        PermissionError: when `approved` is not True. This is defence in depth:
            the route already rejects such requests with 403.
        ValueError: when the assessment failed validation.
    """
    if not payload.approved:
        raise PermissionError("Incident creation requires explicit approval (approved=true).")

    if not payload.payload.validation.passed:
        raise ValueError(
            "The assessment failed validation and cannot be saved: "
            + "; ".join(payload.payload.validation.issues)
        )

    investigation_id = payload.payload.investigation_id

    # Audit the approval before the write, so the trail exists even if the
    # insert then fails.
    await record_activity(
        investigation_id=investigation_id,
        kind="approval",
        payload={
            "approved": True,
            "reviewed_by": payload.reviewed_by,
            "draft_edited": payload.draft_edited,
        },
    )

    created = await repositories.insert_incident(payload)

    # Return the id/status only after the insert has committed.
    await record_activity(
        investigation_id=investigation_id,
        incident_id=created.id,
        kind="save",
        payload={"id": created.id, "status": created.status},
    )

    return created
