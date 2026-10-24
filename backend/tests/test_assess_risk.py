"""TODO: real tests for transparent risk scoring."""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="Scaffold stub: implement risk scoring tests.")
def test_assess_risk_never_returns_safe_band() -> None:
    """The floor is 'Low / Inconclusive' even with zero detected indicators."""
    assert True
