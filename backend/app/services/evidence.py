"""Locate character offsets in the original message for evidence highlighting."""

from __future__ import annotations

from app.schemas.common import Evidence


def find_evidence(message: str, needle: str, *, start_at: int = 0) -> Evidence | None:
    """Return the first exact occurrence of `needle` at/after `start_at`.

    Matching is exact (`str.find`), never fuzzy: the UI highlights the literal
    substring `message[start:end]`, so the offsets must be exact.
    """
    if not needle:
        return None
    index = message.find(needle, start_at)
    if index < 0:
        return None
    return Evidence(start=index, end=index + len(needle), text=needle)


def find_all_evidence(message: str, needle: str) -> list[Evidence]:
    """Return every non-overlapping occurrence of `needle` as evidence spans.

    Returns an empty list when the text does not occur, so callers can never
    invent evidence: no match means no citation.
    """
    if not needle:
        return []

    spans: list[Evidence] = []
    start_at = 0
    while True:
        span = find_evidence(message, needle, start_at=start_at)
        if span is None:
            return spans
        spans.append(span)
        start_at = span.end


def first_evidence(message: str, needles: list[str], *, limit: int = 2) -> list[Evidence]:
    """Return up to `limit` spans for the first few needles that occur.

    Convenience for rule-based tools: pass the keyword list, get the quotes.
    """
    spans: list[Evidence] = []
    for needle in needles:
        for span in find_all_evidence(message, needle):
            if span not in spans:
                spans.append(span)
            if len(spans) >= limit:
                return spans
    return spans
