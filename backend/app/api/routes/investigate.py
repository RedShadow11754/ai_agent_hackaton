"""POST /api/investigate - run the agent and return an assessment or a question.

This endpoint SAVES NOTHING. Persistence happens only through the approval-gated
POST /api/incidents.
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.agent.loop import run_investigation
from app.api.deps import enforce_rate_limit, get_llm_client
from app.config import get_settings
from app.llm.base import LLMClient, LLMError
from app.schemas.investigate import InvestigateRequest, InvestigateResponse

router = APIRouter(tags=["investigate"])


def _new_investigation_id() -> str:
    """Allocate a correlation id used in the activity log and the response."""
    return f"INV-{uuid4().hex[:10].upper()}"


@router.post(
    "/investigate",
    response_model=InvestigateResponse,
    dependencies=[Depends(enforce_rate_limit)],
)
async def investigate(
    request: InvestigateRequest,
    llm: LLMClient = Depends(get_llm_client),
) -> InvestigateResponse:
    """Investigate one pasted message (text only; no URL is ever fetched).

    Runs the agent loop and returns either a clarification question or a full
    assessment. Nothing is persisted except the activity log.
    """
    settings = get_settings()
    if len(request.message) > settings.max_message_chars:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "MESSAGE_TOO_LONG",
                "message": (
                    f"Message exceeds {settings.max_message_chars} characters. "
                    "Paste the relevant part only."
                ),
            },
        )

    try:
        return await run_investigation(
            request.message,
            llm=llm,
            max_tool_calls=settings.max_tool_calls,
            investigation_id=_new_investigation_id(),
            sender=request.sender,
        )
    except LLMError as exc:
        # Retryable provider failure: the UI shows this with a Retry button.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "LLM_ERROR", "message": str(exc)},
        ) from exc
