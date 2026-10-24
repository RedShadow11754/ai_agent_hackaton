"""Deterministic fake LLM for tests and offline demos, with a failure toggle."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.llm.base import LLMClient, LLMMessage, LLMResponse


class FakeLLMClient(LLMClient):
    """Return a canned response without any network access.

    Set `forced_failure=True` to exercise error paths (429/timeout handling).
    """

    def __init__(
        self,
        forced_failure: bool = False,
        response: LLMResponse | None = None,
    ) -> None:
        """Configure the failure toggle and optional canned response."""
        self.forced_failure = forced_failure
        self._response = response or LLMResponse(
            text=(
                "Can you paste the full message, including the sender address "
                "and any links? The current text is too short to assess."
            )
        )

    async def generate(
        self,
        messages: Sequence[LLMMessage],
        tools: Sequence[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Return the canned response, or raise when failure mode is enabled."""
        if self.forced_failure:
            raise RuntimeError("Forced LLM failure (FakeLLMClient.forced_failure).")
        return self._response
