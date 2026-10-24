"""Incident persistence models and the approval payload.

HARD RULE 2: `CreateIncidentRequest.approved` must be `True` before any write.
The route checks it and returns 403 APPROVAL_REQUIRED otherwise; the
`create_incident` tool is never exposed to the model.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.investigate import AssessmentResponse


class CreateIncidentRequest(BaseModel):
    """Body of POST /api/incidents: the reviewed assessment plus approval."""

    approved: bool = Field(
        default=False,
        description="Explicit human approval. Requests without it are rejected with 403.",
    )
    payload: AssessmentResponse = Field(description="The full assessment being saved.")
    message: str = Field(
        default="",
        description="The original message text, stored with the incident for the record.",
    )
    reviewed_by: str | None = Field(default=None, description="Analyst name/handle, if known.")
    draft_edited: bool = Field(default=False, description="True when the analyst changed the draft.")
    draft: str | None = Field(
        default=None, description="Analyst-edited draft; falls back to payload.draft when null."
    )


class IncidentCreatedResponse(BaseModel):
    """Returned only after the database insert commits."""

    id: str = Field(description="Generated incident id, e.g. 'INC-0001'.")
    status: str = Field(default="Pending review")


class IncidentSummary(BaseModel):
    """Row shape for GET /api/incidents (list view)."""

    id: str
    created_at: str
    risk_band: str
    risk_score: int
    status: str
    message_preview: str = Field(default="", description="First ~120 characters, plain text.")


class IncidentDetail(BaseModel):
    """Full stored incident for GET /api/incidents/{id}."""

    id: str
    created_at: str
    approved_at: str | None = None
    reviewed_by: str | None = None
    status: str
    message: str
    assessment: AssessmentResponse
