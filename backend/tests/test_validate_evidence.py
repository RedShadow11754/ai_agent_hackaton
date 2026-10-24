"""TODO: real tests for evidence and guidance validation."""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="Scaffold stub: implement evidence validation tests.")
def test_validate_evidence_rejects_invented_spans() -> None:
    """Spans that do not match message[start:end] must fail validation."""
    assert True
