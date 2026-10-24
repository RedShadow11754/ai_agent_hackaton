"""Transparent, reproducible risk scoring.

The score is a weighted sum of indicator contributions, clamped to 0-100, and
is always returned with a per-factor breakdown so analysts can audit it.

Hard rule 5: the lowest band is "Low / Inconclusive"; there is no "safe" band.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.schemas.common import (
    Indicator,
    IndicatorStatus,
    RiskAssessment,
    RiskBand,
    RiskBreakdownItem,
)

# Starting weights (TODO: tune with the security team).
INDICATOR_WEIGHTS: dict[str, float] = {
    "link_present": 10.0,
    "sender_domain_mismatch": 25.0,
    "urgency_language": 15.0,
    "credential_request": 30.0,
    "payment_change": 30.0,
    "attachment_present": 10.0,
    "ip_literal_host": 20.0,
    # The `urgency` tactic from detect_social_engineering is deliberately worth 0:
    # urgency is already scored by `urgency_language`, and scoring both would
    # double-count the same evidence.
    "urgency": 0.0,
    "secrecy": 15.0,
    "fear": 10.0,
    "authority_impersonation": 10.0,
    "reward": 15.0,
}

# Inclusive lower bounds for each band. The lowest band is never "safe".
BAND_THRESHOLDS: tuple[tuple[int, RiskBand], ...] = (
    (75, RiskBand.HIGH),
    (50, RiskBand.ELEVATED),
    (25, RiskBand.MODERATE),
    (0, RiskBand.LOW_INCONCLUSIVE),
)


def band_for_score(score: int) -> RiskBand:
    """Return the highest band whose threshold is <= `score`."""
    for threshold, band in BAND_THRESHOLDS:
        if score >= threshold:
            return band
    return RiskBand.LOW_INCONCLUSIVE


def assess_risk(indicators: Sequence[Indicator]) -> RiskAssessment:
    """Compute a 0-100 score, band, and itemised breakdown from indicators.

    Only `detected` indicators contribute points; `not_detected` and
    `not_assessable` stay visible in the breakdown with zero points, so an
    analyst can see exactly what was and was not assessed.
    """
    breakdown: list[RiskBreakdownItem] = []
    raw_score = 0.0

    for indicator in indicators:
        weight = indicator.weight if indicator.weight is not None else INDICATOR_WEIGHTS.get(indicator.id, 0.0)
        detected = indicator.status is IndicatorStatus.DETECTED
        points = weight if detected else 0.0
        raw_score += points

        if detected:
            reason = f"Detected, contributes {points:g} of {weight:g} possible points."
        elif indicator.status is IndicatorStatus.NOT_DETECTED:
            reason = "Not detected in the message text; contributes 0 points."
        else:
            reason = "Not assessable from the message text; contributes 0 points."

        breakdown.append(
            RiskBreakdownItem(
                indicator_id=indicator.id,
                label=indicator.label,
                status=indicator.status,
                weight=weight,
                points=points,
                reason=reason,
            )
        )

    score = int(min(100.0, raw_score))
    return RiskAssessment(score=score, band=band_for_score(score), breakdown=breakdown)
