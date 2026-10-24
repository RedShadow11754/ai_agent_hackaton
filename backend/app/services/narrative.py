"""Deterministic, template-based narrative for an assessment.

Why templates: the model's prose is optional refinement, never a requirement.
If the LLM is unavailable (offline demo, rate limit, invalid JSON), the
investigation must still produce a complete, valid assessment. Everything here
is a pure function of the tool outputs, so it is reproducible and testable.

Hard rule 5: this module never states or implies that a message is "safe".
"""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, Field

from app.schemas.common import Indicator, IndicatorStatus, RiskAssessment, UrlFinding

# Phrases that must never appear in generated narrative (hard rule 5).
_FORBIDDEN = ("is safe", "appears safe", "message is safe", "no risk", "risk-free")


class NarrativeDraft(BaseModel):
    """The three prose fields the model may supply; all optional in practice."""

    assessment: str = Field(default="")
    next_steps: list[str] = Field(default_factory=list)
    draft: str = Field(default="")


def build_assessment_summary(
    indicators: Sequence[Indicator],
    risk: RiskAssessment,
    urls: Sequence[UrlFinding] = (),
) -> str:
    """Summarise the findings in plain language, without claiming safety."""
    detected = [item for item in indicators if item.status is IndicatorStatus.DETECTED]
    not_assessable = [item for item in indicators if item.status is IndicatorStatus.NOT_ASSESSABLE]

    sentences: list[str] = []

    if detected:
        labels = ", ".join(item.label.lower() for item in detected)
        sentences.append(
            f"{risk.band.value} (score {risk.score}/100). The message shows signs of "
            f"manipulation or attack: {labels}."
        )
    else:
        sentences.append(
            f"{risk.band.value} (score {risk.score}/100). Nothing in the text clearly "
            "indicates an attack, but that is not proof the message is genuine."
        )

    if urls:
        flagged = sum(1 for finding in urls if finding.observations)
        if flagged:
            sentences.append(
                f"{len(urls)} link(s) were inspected structurally only and "
                f"{flagged} showed suspicious structure. No link was opened."
            )
        else:
            sentences.append(
                f"{len(urls)} link(s) were inspected structurally only. No link was opened."
            )

    if not_assessable:
        sentences.append(
            "Some checks could not be assessed from the text alone: "
            + ", ".join(item.label.lower() for item in not_assessable)
            + "."
        )

    if not detected:
        sentences.append(
            "Absence of detected indicators is not evidence that the message is genuine."
        )

    return _clean(" ".join(sentences))


def build_next_steps(
    indicators: Sequence[Indicator],
    risk: RiskAssessment,
    urls: Sequence[UrlFinding] = (),
) -> list[str]:
    """Return 3-5 concrete next steps for the analyst."""
    detected = {
        item.id for item in indicators if item.status is IndicatorStatus.DETECTED
    }
    steps: list[str] = []

    if "credential_request" in detected:
        steps.append(
            "Confirm with the user whether any password, one-time code, or MFA prompt "
            "was used, and reset credentials if so."
        )
    if "payment_change" in detected:
        steps.append(
            "Warn the finance team and block any payment change until it is verified by "
            "phone on a known number."
        )
    if "link_present" in detected or urls:
        steps.append("Do not open the links; keep them as text for the record.")
    if "attachment_present" in detected:
        steps.append("Quarantine the message and do not open its attachments.")
    if "sender_domain_mismatch" in detected:
        steps.append("Verify the sender's real address through a channel you already trust.")

    steps.append(
        "Verify the request with the person or company using a contact detail you "
        "already have, not by replying to the message."
    )
    steps.append("Log the outcome against this investigation and inform the user.")

    if risk.band.value == "Low / Inconclusive":
        steps.append(
            "If anything about the message still feels wrong, escalate it to the "
            "security team for a second opinion."
        )

    return _dedupe(steps)[:5]


def _clean(text: str) -> str:
    """Remove any forbidden verdict phrase as a last line of defence."""
    cleaned = text
    for phrase in _FORBIDDEN:
        cleaned = cleaned.replace(phrase, "clearly genuine")
        cleaned = cleaned.replace(phrase.capitalize(), "Clearly genuine")
    return " ".join(cleaned.split())


def _dedupe(items: list[str]) -> list[str]:
    """Preserve order while removing duplicates."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
