"""Smoke test for hard rule 2: saving without approval must fail.

This test is intentionally runnable in the scaffold: the approval gate is
implemented even though persistence is still a 501 stub.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _assessment_payload() -> dict[str, Any]:
    """Minimal valid AssessmentResponse payload for the approval gate test."""
    return {
        "type": "assessment",
        "investigation_id": "INV-TEST-0001",
        "urls": [],
        "indicators": [],
        "evidence": [],
        "attack_sequence": [],
        "guidance": [],
        "risk": {"score": 10, "band": "Low / Inconclusive", "breakdown": []},
        "assessment": (
            "Low / Inconclusive: nothing in the text clearly indicates an attack, "
            "but this is not proof that the message is legitimate."
        ),
        "next_steps": ["Verify the request with the user through a known channel."],
        "draft": "Please do not click any links in that message until we verify it.",
        "validation": {"passed": True, "issues": []},
        "activity": [],
    }


def test_save_without_approval_is_rejected() -> None:
    """approved=false must return 403 APPROVAL_REQUIRED and save nothing."""
    response = client.post(
        "/api/incidents",
        json={"approved": False, "payload": _assessment_payload()},
    )

    assert response.status_code == 403
    body = response.json()
    assert body["error"]["code"] == "APPROVAL_REQUIRED"
    assert "approval" in body["error"]["message"].lower()


def test_approved_request_is_not_blocked_by_the_gate() -> None:
    """approved=true must pass the gate (persistence is still a stub -> 501)."""
    response = client.post(
        "/api/incidents",
        json={"approved": True, "payload": _assessment_payload()},
    )

    assert response.status_code != 403
