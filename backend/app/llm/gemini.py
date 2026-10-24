"""Gemini implementation of the LLMClient interface (free tier)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.llm.base import LLMClient, LLMMessage, LLMResponse


class GeminiClient(LLMClient):
    """Gemini adapter using the REST API through httpx.

    Keep this the only module that knows Gemini's request/response shape.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        *,
        timeout_seconds: float = 30.0,
    ) -> None:
        """Store credentials and defaults. Never log the API key."""
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds

    @property
    def model(self) -> str:
        """Configured model identifier."""
        return self._model

    async def generate(
        self,
        messages: Sequence[LLMMessage],
        tools: Sequence[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Call Gemini and normalise the response into `LLMResponse`.

        TODO:
        - translate `messages` into Gemini `contents` (system -> systemInstruction);
        - map `tools` to function declarations and parse `functionCall` parts;
        - retry once on 429/5xx with backoff; raise LLMError on final failure;
        - keep prompts short to stay inside free-tier quotas;
        - never pass URLs to any fetch/grounding feature (hard rule 1).
        """
        raise NotImplementedError("GeminiClient.generate is a scaffold stub.")
