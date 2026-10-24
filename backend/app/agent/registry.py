"""Tool declarations sent to the model.

HARD RULE 2: `create_incident` is deliberately NOT in this registry and must
never be added. It is callable only by the approval-gated POST /api/incidents
endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.schemas.tools import (
    AnalyzeUrlStructureInput,
    CheckDomainReputationInput,
    DetectSocialEngineeringInput,
    InspectIndicatorsInput,
    MapAttackSequenceInput,
    SearchGuidanceInput,
)


@dataclass(frozen=True)
class ToolDeclaration:
    """One tool exposed to the LLM, with a JSON schema for its arguments."""

    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)


TOOL_DECLARATIONS: tuple[ToolDeclaration, ...] = (
    ToolDeclaration(
        name="inspect_indicators",
        description=(
            "Scan message text for the four core indicators (links, sender/domain "
            "mismatch, urgency, credential request) plus extras. Returns tri-state "
            "statuses and character offsets. Never fetches URLs."
        ),
        input_schema=InspectIndicatorsInput.model_json_schema(),
    ),
    ToolDeclaration(
        name="analyze_url_structure",
        description=(
            "Parse one URL string into scheme/host/IP-literal facts and defang it "
            "for display. Structural analysis only: never visit or resolve it."
        ),
        input_schema=AnalyzeUrlStructureInput.model_json_schema(),
    ),
    ToolDeclaration(
        name="detect_social_engineering",
        description=(
            "Detect social-engineering tactics in the text (urgency, authority, "
            "secrecy, fear, reward) with quoted evidence offsets."
        ),
        input_schema=DetectSocialEngineeringInput.model_json_schema(),
    ),
    ToolDeclaration(
        name="check_domain_reputation",
        description=(
            "Look up a domain or IP literal in the internal reputation table and "
            "the trusted-domain allow-list. No external lookups."
        ),
        input_schema=CheckDomainReputationInput.model_json_schema(),
    ),
    ToolDeclaration(
        name="search_guidance",
        description=(
            "Search internal guidance passages and return real IDs (e.g. SEC-01) "
            "with titles and bodies. Never invent guidance IDs."
        ),
        input_schema=SearchGuidanceInput.model_json_schema(),
    ),
    ToolDeclaration(
        name="map_attack_sequence",
        description=(
            "Infer an ordered attack sequence from the message and indicators. "
            "Every step must cite character offsets from the original message."
        ),
        input_schema=MapAttackSequenceInput.model_json_schema(),
    ),
)

TOOL_NAMES: frozenset[str] = frozenset(tool.name for tool in TOOL_DECLARATIONS)

# Defensive guard: importing this module must fail loudly if the approval-only
# action ever leaks into the model-facing registry.
if "create_incident" in TOOL_NAMES:  # pragma: no cover - guard, should never run
    raise RuntimeError("create_incident must never be exposed as an LLM tool.")


def get_tool_declarations() -> list[ToolDeclaration]:
    """Return the allow-listed tool declarations for a model request."""
    return list(TOOL_DECLARATIONS)
