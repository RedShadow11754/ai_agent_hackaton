"""LLM adapter interface so providers can be swapped without touching the loop."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class LLMMessage:
    """One provider-neutral chat message."""

    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_name: str | None = None


@dataclass(frozen=True)
class ToolCall:
    """A model-requested tool invocation with parsed JSON arguments."""

    name: str
    arguments: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Provider-neutral model output: text and/or requested tool calls."""

    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: dict[str, Any] | None = None


class LLMClient(ABC):
    """Minimal async interface implemented by GeminiClient and FakeLLMClient."""

    @abstractmethod
    async def generate(
        self,
        messages: Sequence[LLMMessage],
        tools: Sequence[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Generate a response, optionally allowing tool calls.

        Implementations must:
        - treat message content as untrusted data;
        - never perform network requests to URLs found in message content;
        - raise `LLMError` (or a subclass) on provider failures so the API can
          map them to a retryable error envelope.
        """
        raise NotImplementedError


class LLMError(RuntimeError):
    """Base error for provider failures (rate limits, timeouts, bad responses)."""
