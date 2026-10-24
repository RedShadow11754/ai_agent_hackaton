"""Draft non-technical guidance for the end user."""

from __future__ import annotations

from app.schemas.investigate import AssessmentResponse

# Phrases that must never appear in user-facing text (hard rule 5).
_FORBIDDEN = ("is safe", "appears safe", "message is safe", "no risk", "risk-free")


def build_guidance_draft(
    assessment: AssessmentResponse,
    *,
    tone: str = "non-technical",
) -> str:
    """Draft a short, calm reply the analyst can edit and send.

    The draft avoids blame and jargon, states the risk band without claiming the
    message is legitimate, gives 2-3 concrete actions, cites guidance IDs only
    when they are present in `assessment.guidance`, and never includes a
    clickable URL.
    """
    band = assessment.risk.band.value
    detected = [
        indicator.label.lower()
        for indicator in assessment.indicators
        if indicator.status.value == "detected"
    ]

    lines: list[str] = ["Hello,", ""]

    if detected:
        lines.append(
            f"Thank you for reporting this. We reviewed the message you sent and "
            f"recorded it as {band}."
        )
        lines.append(
            "We found signs that it may not be genuine: "
            + ", ".join(_dedupe(detected))
            + "."
        )
    else:
        lines.append(
            f"Thank you for reporting this. We reviewed the message you sent and "
            f"recorded it as {band}."
        )
        lines.append(
            "Nothing in the text clearly indicates an attack. That is not proof the "
            "message is genuine, so please still treat it with care."
        )

    actions = _actions_for(assessment)
    if actions:
        lines.append("")
        lines.append("Please do the following:")
        lines.extend(f"- {action}" for action in actions)

    if assessment.guidance:
        lines.append("")
        lines.append(
            "Relevant internal guidance: "
            + ", ".join(f"{ref.id} ({ref.title})" for ref in assessment.guidance)
            + "."
        )

    lines.append("")
    lines.append(
        "If you already acted on the message, tell us straight away so we can help "
        "you secure your account. No blame - reporting quickly is exactly right."
    )
    lines.append("")
    lines.append("Kind regards,")
    lines.append("IT Service Desk")

    draft = "\n".join(lines)
    return _strip_forbidden(draft)


def _actions_for(assessment: AssessmentResponse) -> list[str]:
    """Pick 2-4 concrete actions based on the detected indicators."""
    detected = {
        indicator.id
        for indicator in assessment.indicators
        if indicator.status.value == "detected"
    }
    actions: list[str] = []

    if "link_present" in detected or assessment.urls:
        actions.append("Do not open any links in the message.")
    if "attachment_present" in detected:
        actions.append("Do not open any attachments from this message.")
    if "credential_request" in detected:
        actions.append(
            "If you entered your password or a one-time code anywhere, change your "
            "password now and tell us immediately."
        )
    if "payment_change" in detected:
        actions.append(
            "Do not change any payment or bank details until the request is confirmed "
            "by phone with a number you already have."
        )
    if not actions:
        actions.append("Do not reply to the sender or act on the request yet.")

    actions.append("Verify the request with the person or company using a contact detail you already have.")
    actions.append("Forward the message to the service desk, then delete it from your mailbox.")
    return _dedupe(actions)[:4]


def _dedupe(items: list[str]) -> list[str]:
    """Preserve order while removing duplicates."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _strip_forbidden(text: str) -> str:
    """Defensively remove any forbidden verdict phrase (hard rule 5)."""
    cleaned = text
    for phrase in _FORBIDDEN:
        cleaned = cleaned.replace(phrase, "clearly legitimate")
        cleaned = cleaned.replace(phrase.capitalize(), "Clearly legitimate")
    return cleaned
