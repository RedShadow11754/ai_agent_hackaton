"""Incident routes.

HARD RULE 2: `POST /api/incidents` is the ONLY caller of `create_incident`, and
it rejects any request that does not carry `approved: true`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import enforce_rate_limit
from app.db import repositories
from app.schemas.common import ActivityEntry
from app.schemas.incidents import (
    CreateIncidentRequest,
    IncidentCreatedResponse,
    IncidentDetail,
    IncidentSummary,
)
from app.services.activity_log import read_activity
from app.tools.create_incident import create_incident

router = APIRouter(tags=["incidents"])


@router.post(
    "/incidents",
    response_model=IncidentCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_rate_limit)],
)
async def create_incident_route(
    request: CreateIncidentRequest,
) -> IncidentCreatedResponse:
    """Save a reviewed incident - but only after explicit human approval.

    Raises:
        HTTPException: 403 APPROVAL_REQUIRED when `approved` is not True;
            422 VALIDATION_FAILED when the assessment failed validation.
    """
    # The approval gate. This check runs before anything else touches the DB.
    if not request.approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "APPROVAL_REQUIRED",
                "message": (
                    "Saving an incident requires explicit human approval: "
                    "send approved=true after reviewing the assessment."
                ),
            },
        )

    if not request.payload.validation.passed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "VALIDATION_FAILED",
                "message": (
                    "This assessment did not pass validation and cannot be saved: "
                    + "; ".join(request.payload.validation.issues)
                ),
            },
        )

    try:
        return await create_incident(request)
    except PermissionError as exc:  # defence in depth; the gate above already ran
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "APPROVAL_REQUIRED", "message": str(exc)},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_FAILED", "message": str(exc)},
        ) from exc


@router.get("/incidents", response_model=list[IncidentSummary])
async def list_incidents(
    limit: int = Query(default=50, ge=1, le=200),
) -> list[IncidentSummary]:
    """List recent incidents, newest first."""
    return await repositories.list_incidents(limit)


@router.get("/incidents/{incident_id}", response_model=IncidentDetail)
async def get_incident(incident_id: str) -> IncidentDetail:
    """Return one stored incident with its full assessment.

    Raises:
        HTTPException: 404 NOT_FOUND when no incident has that id.
    """
    incident = await repositories.get_incident(incident_id)
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": f"No incident with id {incident_id!r}."},
        )
    return incident


@router.get("/incidents/{incident_id}/activity", response_model=list[ActivityEntry])
async def get_incident_activity(incident_id: str) -> list[ActivityEntry]:
    """Return the audit trail for one incident (tool calls, approval, save)."""
    incident = await repositories.get_incident(incident_id)
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": f"No incident with id {incident_id!r}."},
        )
    return await read_activity(incident_id=incident_id)
