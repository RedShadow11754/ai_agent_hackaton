"""TODO: real tests for structural URL analysis (no network access)."""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="Scaffold stub: implement URL structure tests.")
def test_analyze_url_structure_defangs_without_fetching() -> None:
    """Analysis must parse only; the test must not resolve DNS or fetch."""
    assert True
