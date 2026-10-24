"""Validate that an assessment is internally consistent before display/save."""

from __future__ import annotations

from collections.abc import Sequence

from app.schemas.common import Evidence, ValidationResult
from app.schemas.investigate import AssessmentResponse
from app.services.assess_risk import assess_risk

# Wording that must never appear as a verdict (hard rule 5).
_FORBIDDEN_VERDICTS = ("is safe", "appears safe", "message is safe", "no risk", "risk-free")


def validate_evidence(message: str, evidence: Sequence[Evidence]) -> list[str]:
    """Check that every evidence span really exists in the original message.

    Rules:
    - `0 <= start < end <= len(message)`;
    - `message[start:end] == evidence.text` (exact match, no normalisation).
    """
    issues: list[str] = []

    for span in evidence:
        label = f"[{span.start}:{span.end}]"
        if span.start < 0 or span.end <= span.start:
            issues.append(f"Evidence {label} has an invalid range (start must be < end).")
            continue
        if span.end > len(message):
            issues.append(
                f"Evidence {label} runs past the end of the message ({len(message)} characters)."
            )
            continue
        actual = message[span.start : span.end]
        if actual != span.text:
            issues.append(
                f"Evidence {label} does not match the message: "
                f"expected {span.text!r} but found {actual!r}."
            )

    return issues


def validate_assessment(
    message: str,
    assessment: AssessmentResponse,
    known_guidance_ids: set[str],
) -> ValidationResult:
    """Run all consistency checks for one assessment.

    Checks:
    - every evidence span in indicators, attack steps, and the top-level list
      really exists in the message;
    - every cited guidance ID exists in `known_guidance_ids` (no inventions);
    - the reported risk score matches a recomputation from the indicators;
    - no indicator or narrative claims the message is "safe";
    - attack steps are ordered and each cites at least one span.
    """
    issues: list[str] = []

    # 1. Evidence spans (top-level, indicators, attack steps).
    spans: list[Evidence] = list(assessment.evidence)
    for indicator in assessment.indicators:
        spans.extend(indicator.evidence)
    for step in assessment.attack_sequence:
        spans.extend(step.evidence)
    issues.extend(validate_evidence(message, spans))

    # 2. Guidance citations must be real.
    for ref in assessment.guidance:
        if ref.id not in known_guidance_ids:
            issues.append(f"Guidance ID {ref.id!r} does not exist in the guidance table.")

    # 3. Risk score must match a recomputation from the indicators.
    recomputed = assess_risk(assessment.indicators)
    if recomputed.score != assessment.risk.score:
        issues.append(
            f"Risk score {assessment.risk.score} does not match the recomputed score "
            f"{recomputed.score} for these indicators."
        )
    if recomputed.band is not assessment.risk.band:
        issues.append(
            f"Risk band {assessment.risk.band.value!r} does not match the recomputed band "
            f"{recomputed.band.value!r}."
        )

    # 4. Never claim the message is safe.
    narrative = " ".join(
        [assessment.assessment, *[indicator.detail for indicator in assessment.indicators]]
    ).lower()
    for phrase in _FORBIDDEN_VERDICTS:
        if phrase in narrative:
            issues.append(f"Narrative uses a forbidden verdict phrase: {phrase!r}.")

    # 5. Attack steps: ordered, non-empty, and each backed by at least one span.
    for position, step in enumerate(assessment.attack_sequence, start=1):
        if step.index != position:
            issues.append(
                f"Attack step at position {position} has index {step.index}; "
                "steps must be numbered 1..n in order."
            )
        if not step.evidence:
            issues.append(f"Attack step {step.index} cites no evidence offsets.")
        if not step.description.strip():
            issues.append(f"Attack step {step.index} has an empty description.")

    return ValidationResult(passed=not issues, issues=issues)
