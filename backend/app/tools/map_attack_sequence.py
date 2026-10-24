"""Tool: map the likely attack sequence, citing evidence offsets."""

from __future__ import annotations

from app.schemas.common import AttackStep, Evidence, Indicator, IndicatorStatus
from app.schemas.tools import MapAttackSequenceInput, MapAttackSequenceOutput

# Candidate steps in a typical sequence, with the indicator ids that trigger them.
# Order matters: the filtered list is renumbered 1..n.
_STEP_LIBRARY: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (
        ("authority_impersonation", "sender_domain_mismatch"),
        "An attacker poses as a trusted person, team, or brand so the message looks routine.",
        "establish trust",
    ),
    (
        ("urgency", "urgency_language", "fear"),
        "The message applies time pressure or a threat so the reader acts before verifying.",
        "bypass verification",
    ),
    (
        ("secrecy",),
        "The reader is asked to keep the request quiet, which prevents a colleague from spotting it.",
        "isolate the target",
    ),
    (
        ("reward",),
        "A reward or refund is offered to make the reader respond without checking.",
        "bait the target",
    ),
    (
        ("link_present", "ip_literal_host"),
        "The reader is directed to a link that is not the site it claims to be.",
        "redirect to an attacker-controlled page",
    ),
    (
        ("attachment_present",),
        "The reader is invited to open an attachment that could carry malware.",
        "deliver a malicious file",
    ),
    (
        ("credential_request",),
        "The page or reply asks for a password, one-time code, or MFA approval to steal access.",
        "steal credentials",
    ),
    (
        ("payment_change",),
        "New bank details are introduced so a payment can be redirected.",
        "divert a payment",
    ),
)


async def map_attack_sequence(
    payload: MapAttackSequenceInput,
) -> MapAttackSequenceOutput:
    """Return ordered attack steps inferred from text and indicators.

    Every step cites at least one `Evidence` span from the original message, and
    steps with no supporting evidence are dropped rather than invented. Steps
    describe likely intent, not certainty, and never imply that a URL was
    visited.
    """
    detected = {
        indicator.id: indicator
        for indicator in payload.indicators
        if indicator.status is IndicatorStatus.DETECTED
    }

    steps: list[AttackStep] = []
    for trigger_ids, description, intent in _STEP_LIBRARY:
        if not any(trigger_id in detected for trigger_id in trigger_ids):
            continue

        evidence = _evidence_for(detected, trigger_ids)
        if not evidence:
            # No quote means no step: never assert something we cannot show.
            continue

        steps.append(
            AttackStep(
                index=len(steps) + 1,
                description=description,
                intent=intent,
                evidence=evidence,
            )
        )

    notes: list[str] = []
    if not steps:
        notes.append(
            "No attack sequence could be inferred from the text; this is not a "
            "statement that the message is legitimate."
        )

    return MapAttackSequenceOutput(steps=steps, notes=notes)


def _evidence_for(
    detected: dict[str, Indicator], trigger_ids: tuple[str, ...]
) -> list[Evidence]:
    """Collect up to two spans from the indicators that triggered this step."""
    spans: list[Evidence] = []
    for trigger_id in trigger_ids:
        indicator = detected.get(trigger_id)
        if indicator is None:
            continue
        for span in indicator.evidence:
            if span not in spans:
                spans.append(span)
            if len(spans) >= 2:
                return spans
    return spans
