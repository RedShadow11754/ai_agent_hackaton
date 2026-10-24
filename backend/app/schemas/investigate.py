"""Pydantic models for the investigation API contract.

`POST /api/investigate` returns either a clarification question or a full
assessment; both share the `type` discriminator so the frontend can narrow
the union safely.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import (
    ActivityEntry,
    AttackStep,
    Evidence,
    GuidanceRef,
    Indicator,
    RiskAssessment,
    UrlFinding,
    ValidationResult,
)


class InvestigateRequest(BaseModel):
    """Body of POST /api/investigate. Text only: never a URL to fetch."""

    message: str = Field(min_length=1, description="The pasted message text.")
    sender: str | None = Field(default=None, description="Optional sender as shown to the user.")
    context: str | None = Field(default=None, description="Optional analyst note.")


class ClarificationResponse(BaseModel):
    """Returned when the message is too short/ambiguous to assess responsibly."""

    type: Literal["clarification"] = "clarification"
    investigation_id: str
    question: str


class AssessmentResponse(BaseModel):
    """Full investigation result. Produced only after the guardrail services run."""

    type: Literal["assessment"] = "assessment"
    investigation_id: str
    urls: list[UrlFinding] = Field(default_factory=list)
    indicators: list[Indicator] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    attack_sequence: list[AttackStep] = Field(default_factory=list)
    guidance: list[GuidanceRef] = Field(default_factory=list)
    risk: RiskAssessment
    assessment: str = Field(description="Plain-language summary. Never says 'safe'.")
    next_steps: list[str] = Field(default_factory=list)
    draft: str = Field(default="", description="Editable reply draft for the analyst.")
    validation: ValidationResult
    activity: list[ActivityEntry] = Field(default_factory=list)


# Discriminated union used as the route's return annotation.
InvestigateResponse = ClarificationResponse | AssessmentResponse
