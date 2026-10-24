"""Input/output models for every tool.

These models are the single source of truth for two things:
1. the JSON schema advertised to the model in `app.agent.registry`;
2. the validated payload each tool function receives and returns.

Tools are read-only and text-only: no field here should ever be a URL to fetch.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import AttackStep, GuidanceRef, Indicator


# ---------------------------------------------------------------------------
# inspect_indicators
# ---------------------------------------------------------------------------
class InspectIndicatorsInput(BaseModel):
    """Input for `inspect_indicators`."""

    message: str = Field(description="Raw message text to scan. Never fetched.")
    sender: str | None = Field(
        default=None,
        description="Sender line as shown to the user, used for the domain-mismatch check.",
    )


class InspectIndicatorsOutput(BaseModel):
    """Four core indicators plus any extra ones, each with offsets."""

    indicators: list[Indicator] = Field(default_factory=list)
    urls: list[str] = Field(
        default_factory=list,
        description="URL-like tokens found in the text, normalised for structural parsing only.",
    )
    notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# analyze_url_structure
# ---------------------------------------------------------------------------
class AnalyzeUrlStructureInput(BaseModel):
    """Input for `analyze_url_structure`."""

    url: str = Field(description="A single URL string to parse structurally.")
    visible_text: str | None = Field(
        default=None, description="Anchor text as shown to the user, to spot mismatches."
    )


class AnalyzeUrlStructureOutput(BaseModel):
    """Structural facts plus a defanged display form. Never a fetch result."""

    url: str
    defanged: str = Field(description="e.g. hxxps://host[.]tld/path - never clickable.")
    scheme: str = ""
    host: str = ""
    port: int | None = None
    path: str = ""
    is_ip_literal: bool = False
    observations: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# detect_social_engineering
# ---------------------------------------------------------------------------
class DetectSocialEngineeringInput(BaseModel):
    """Input for `detect_social_engineering`."""

    message: str = Field(description="Raw message text to scan for tactics.")


class DetectSocialEngineeringOutput(BaseModel):
    """Tactics such as urgency, authority, secrecy, fear, reward."""

    tactics: list[Indicator] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# check_domain_reputation
# ---------------------------------------------------------------------------
class CheckDomainReputationInput(BaseModel):
    """Input for `check_domain_reputation`."""

    domain: str = Field(description="Domain or IP literal, e.g. 'secure-login.test'.")


class CheckDomainReputationOutput(BaseModel):
    """Internal reputation lookup result. No external lookups, ever."""

    domain: str
    status: Literal["known_safe", "known_suspicious", "unknown"] = "unknown"
    trusted: bool = Field(default=False, description="True when on the trusted allow-list.")
    source: str | None = None
    note: str | None = None


# ---------------------------------------------------------------------------
# search_guidance
# ---------------------------------------------------------------------------
class SearchGuidanceInput(BaseModel):
    """Input for `search_guidance`."""

    query: str = Field(description="Keywords or tags describing the situation.")
    limit: int = Field(default=3, ge=1, le=10, description="Maximum passages to return.")


class SearchGuidanceOutput(BaseModel):
    """Matching guidance passages. IDs must exist in the `guidance` table."""

    query: str
    results: list[GuidanceRef] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# map_attack_sequence
# ---------------------------------------------------------------------------
class MapAttackSequenceInput(BaseModel):
    """Input for `map_attack_sequence`."""

    message: str = Field(description="Raw message text.")
    indicators: list[Indicator] = Field(
        default_factory=list, description="Indicators found so far, to ground the mapping."
    )


class MapAttackSequenceOutput(BaseModel):
    """Ordered, evidence-backed attack steps (see `common.AttackStep`)."""

    steps: list[AttackStep] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
