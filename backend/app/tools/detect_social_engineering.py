"""Tool: detect social-engineering tactics in message text."""

from __future__ import annotations

from app.schemas.common import Indicator, IndicatorStatus
from app.schemas.tools import (
    DetectSocialEngineeringInput,
    DetectSocialEngineeringOutput,
)
from app.services.evidence import first_evidence
from app.tools.inspect_indicators import is_assessable_text

# Tactic id -> (label, keywords, detail when detected)
_TACTICS: tuple[tuple[str, str, list[str], str], ...] = (
    (
        "urgency",
        "Urgency pressure",
        [
            "immediately",
            "urgent",
            "urgently",
            "act now",
            "right away",
            "as soon as possible",
            "asap",
            "within 24 hours",
            "final notice",
            "last warning",
            "expires today",
            "deadline",
        ],
        "The message pushes the reader to act before they can check it.",
    ),
    (
        "authority_impersonation",
        "Authority or brand impersonation",
        [
            "it support",
            "helpdesk",
            "service desk",
            "your bank",
            "payroll",
            "hr team",
            "human resources",
            "administrator",
            "security team",
            "chief executive",
            "ceo",
            "director",
            "government",
            "police",
            "microsoft",
            "google",
            "accounts team",
        ],
        "The message borrows the name of a trusted team or brand.",
    ),
    (
        "secrecy",
        "Secrecy request",
        [
            "confidential",
            "do not tell",
            "do not discuss",
            "do not share",
            "between us",
            "keep this private",
            "keep it private",
            "don't tell anyone",
            "do not mention",
        ],
        "The message asks the reader to keep the request quiet, which blocks verification.",
    ),
    (
        "fear",
        "Fear or threat",
        [
            "lose access",
            "will be suspended",
            "suspended",
            "terminated",
            "account will be closed",
            "legal action",
            "penalty",
            "unauthorised access",
            "unauthorized access",
            "failure to",
            "consequences",
        ],
        "The message threatens a loss or penalty to force compliance.",
    ),
    (
        "reward",
        "Reward or bait",
        [
            "you have won",
            "winner",
            "prize",
            "bonus",
            "gift card",
            "refund",
            "free",
            "reward",
            "compensation",
        ],
        "The message offers a reward to make the reader act without thinking.",
    ),
)


async def detect_social_engineering(
    payload: DetectSocialEngineeringInput,
) -> DetectSocialEngineeringOutput:
    """Return tactics (urgency, authority, secrecy, fear, reward) with evidence.

    Each tactic is an `Indicator` whose status is detected / not_detected /
    not_assessable, never "safe". Evidence offsets always point into the
    original message text.
    """
    message = payload.message

    if not is_assessable_text(message):
        return DetectSocialEngineeringOutput(
            tactics=[
                Indicator(
                    id=tactic_id,
                    label=label,
                    status=IndicatorStatus.NOT_ASSESSABLE,
                    detail="Not assessable: the message is too short to analyse.",
                    evidence=[],
                )
                for tactic_id, label, _, _ in _TACTICS
            ],
            notes=["Message is too short for reliable tactic detection."],
        )

    tactics: list[Indicator] = []
    for tactic_id, label, keywords, detail in _TACTICS:
        evidence = first_evidence(message, keywords, limit=2)
        if evidence:
            tactics.append(
                Indicator(
                    id=tactic_id,
                    label=label,
                    status=IndicatorStatus.DETECTED,
                    detail=detail,
                    evidence=evidence,
                )
            )
        else:
            tactics.append(
                Indicator(
                    id=tactic_id,
                    label=label,
                    status=IndicatorStatus.NOT_DETECTED,
                    detail="No wording matching this tactic was found.",
                    evidence=[],
                )
            )

    return DetectSocialEngineeringOutput(tactics=tactics, notes=[])
