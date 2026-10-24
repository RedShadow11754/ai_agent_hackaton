"""Shared Pydantic models: tri-state indicators, evidence, risk, activity.

HARD RULE 5: there is no "safe" state anywhere in these enums. The lowest risk
band is `Low / Inconclusive`, and every indicator is exactly one of
`detected | not_detected | not_assessable`.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class IndicatorStatus(str, Enum):
    """Tri-state indicator outcome. Deliberately has no "safe" member."""

    DETECTED = "detected"
    NOT_DETECTED = "not_detected"
    NOT_ASSESSABLE = "not_assessable"


class RiskBand(str, Enum):
    """Risk bands, highest first. `LOW_INCONCLUSIVE` is the floor."""

    HIGH = "High"
    ELEVATED = "Elevated"
    MODERATE = "Moderate"
    LOW_INCONCLUSIVE = "Low / Inconclusive"


class Evidence(BaseModel):
    """An exact character span in the original message, for UI highlighting.

    Invariant enforced by `validate_evidence`: `message[start:end] == text`.
    """

    start: int = Field(ge=0, description="Inclusive character offset into the message.")
    end: int = Field(ge=0, description="Exclusive character offset into the message.")
    text: str = Field(description="The exact substring message[start:end].")


class Indicator(BaseModel):
    """One assessed indicator with optional supporting evidence."""

    id: str = Field(description="Stable machine id, e.g. 'credential_request'.")
    label: str = Field(description="Short human-readable label for the UI.")
    status: IndicatorStatus
    detail: str = Field(default="", description="Plain-language explanation.")
    evidence: list[Evidence] = Field(default_factory=list)
    weight: float | None = Field(
        default=None, description="Scoring weight, when this indicator is scored."
    )


class RiskBreakdownItem(BaseModel):
    """One auditable row explaining part of the risk score."""

    indicator_id: str
    label: str
    status: IndicatorStatus
    weight: float = 0.0
    points: float = 0.0
    reason: str = ""


class RiskAssessment(BaseModel):
    """Transparent 0-100 score with band and itemised breakdown."""

    score: int = Field(ge=0, le=100)
    band: RiskBand
    breakdown: list[RiskBreakdownItem] = Field(default_factory=list)


class UrlFinding(BaseModel):
    """Structural facts about a URL. Never the result of visiting it."""

    url: str = Field(description="The raw string as pasted (shown defanged in the UI).")
    defanged: str = Field(description="Non-clickable display form, e.g. hxxps://host[.]tld.")
    host: str = ""
    observations: list[str] = Field(default_factory=list)


class AttackStep(BaseModel):
    """One inferred step in the likely attack sequence.

    `evidence` must cite at least one real span (validate_assessment checks it).
    """

    index: int = Field(ge=1, description="1-based order within the sequence.")
    description: str
    intent: str = Field(default="", description="Likely goal, stated as a possibility.")
    evidence: list[Evidence] = Field(default_factory=list)


class GuidanceRef(BaseModel):
    """An internal guidance passage, referenced by its real database ID."""

    id: str = Field(description="Real guidance ID from the `guidance` table, e.g. 'SEC-01'.")
    title: str
    body: str = ""
    tags: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Outcome of the post-model guardrail checks."""

    passed: bool
    issues: list[str] = Field(default_factory=list)


ActivityKind = Literal["tool_call", "tool_result", "error", "approval", "save"]


class ActivityEntry(BaseModel):
    """One audit-trail row: a tool call, result, error, approval, or save."""

    id: int | None = None
    investigation_id: str | None = None
    incident_id: str | None = None
    created_at: str | None = Field(default=None, description="ISO-8601 timestamp.")
    kind: ActivityKind
    tool_name: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
