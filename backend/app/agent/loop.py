"""Bounded tool-calling loop for one investigation.

Hard rule 3: the loop must never exceed `max_tool_calls` tool invocations.
Hard rule 5: the loop can return a clarification or an assessment, never a
"safe" verdict.

Design
------
Two phases, so the product works with or without a working LLM:

1. **Model-chosen tools.** The model is offered the read-only tools and may call
   them; every call is allow-listed, validated, logged, and counted.
2. **Deterministic baseline plan.** Whatever the model did not do, a rule-based
   planner finishes (inspect, detect tactics, analyse links, check reputation,
   search guidance, map the sequence), still inside the cap.

Then the guardrails run in code, not by model choice: `validate_evidence`, then
`assess_risk`, then the guidance draft. If validation fails, the narrative is
rebuilt from templates (which are valid by construction) and re-validated; if it
still fails, the API returns a clarification rather than unvalidated output.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ValidationError

from app.agent.prompts import (
    UNCERTAINTY_WORDING,
    build_finalize_prompt,
    build_planning_prompt,
    SYSTEM_PROMPT,
)
from app.agent.registry import TOOL_NAMES, get_tool_declarations
from app.config import get_settings
from app.db import repositories
from app.llm.base import LLMClient, LLMMessage
from app.schemas.common import (
    ActivityEntry,
    ActivityKind,
    AttackStep,
    Evidence,
    GuidanceRef,
    Indicator,
    UrlFinding,
    ValidationResult,
)
from app.schemas.investigate import AssessmentResponse, ClarificationResponse
from app.schemas.tools import (
    AnalyzeUrlStructureInput,
    AnalyzeUrlStructureOutput,
    CheckDomainReputationInput,
    CheckDomainReputationOutput,
    DetectSocialEngineeringInput,
    DetectSocialEngineeringOutput,
    InspectIndicatorsInput,
    InspectIndicatorsOutput,
    MapAttackSequenceInput,
    MapAttackSequenceOutput,
    SearchGuidanceInput,
    SearchGuidanceOutput,
)
from app.services.assess_risk import assess_risk
from app.services.guidance_draft import build_guidance_draft
from app.services.narrative import (
    NarrativeDraft,
    build_assessment_summary,
    build_next_steps,
)
from app.services.validate_evidence import validate_assessment
from app.tools.analyze_url_structure import analyze_url_structure
from app.tools.check_domain_reputation import check_domain_reputation
from app.tools.detect_social_engineering import detect_social_engineering
from app.tools.inspect_indicators import (
    inspect_indicators,
    is_assessable_text,
    registrable_domain,
)
from app.tools.map_attack_sequence import map_attack_sequence
from app.tools.search_guidance import search_guidance

_MAX_MODEL_ROUNDS = 3
_MAX_URLS_ANALYSED = 2
_MAX_DOMAINS_CHECKED = 2
_MAX_TOP_LEVEL_EVIDENCE = 8

# Tool name -> (input model, coroutine). `create_incident` is deliberately absent.
_TOOL_FUNCS: dict[str, Any] = {
    "inspect_indicators": inspect_indicators,
    "analyze_url_structure": analyze_url_structure,
    "detect_social_engineering": detect_social_engineering,
    "check_domain_reputation": check_domain_reputation,
    "search_guidance": search_guidance,
    "map_attack_sequence": map_attack_sequence,
}

_INPUT_MODELS: dict[str, type[BaseModel]] = {
    "inspect_indicators": InspectIndicatorsInput,
    "analyze_url_structure": AnalyzeUrlStructureInput,
    "detect_social_engineering": DetectSocialEngineeringInput,
    "check_domain_reputation": CheckDomainReputationInput,
    "search_guidance": SearchGuidanceInput,
    "map_attack_sequence": MapAttackSequenceInput,
}


class ToolCallCapExceeded(RuntimeError):
    """Raised if orchestration tries to exceed the configured tool budget."""


@dataclass
class InvestigationState:
    """Mutable state carried through one investigation."""

    investigation_id: str
    message: str
    sender: str | None = None
    tool_calls_used: int = 0
    activity: list[ActivityEntry] = field(default_factory=list)


@dataclass
class _Facts:
    """Everything the tools found, ready to be assembled into an assessment."""

    indicators: list[Indicator] = field(default_factory=list)
    tactics: list[Indicator] = field(default_factory=list)
    discovered_urls: list[str] = field(default_factory=list)
    url_findings: list[AnalyzeUrlStructureOutput] = field(default_factory=list)
    domain_checks: list[CheckDomainReputationOutput] = field(default_factory=list)
    guidance: list[GuidanceRef] = field(default_factory=list)
    steps: list[AttackStep] = field(default_factory=list)
    done: set[str] = field(default_factory=set)
    notes: list[str] = field(default_factory=list)

    @property
    def all_indicators(self) -> list[Indicator]:
        """Core indicators plus social-engineering tactics, de-duplicated by id."""
        merged: list[Indicator] = []
        seen: set[str] = set()
        for indicator in [*self.indicators, *self.tactics]:
            if indicator.id in seen:
                continue
            seen.add(indicator.id)
            merged.append(indicator)
        return merged


async def run_investigation(
    message: str,
    *,
    llm: LLMClient,
    max_tool_calls: int,
    investigation_id: str,
    sender: str | None = None,
) -> ClarificationResponse | AssessmentResponse:
    """Investigate one message and return a clarification or full assessment.

    The message is treated as untrusted data throughout: it is only ever
    analysed as text, never executed or fetched.
    """
    settings = get_settings()
    state = InvestigationState(
        investigation_id=investigation_id, message=message, sender=sender
    )

    # --- Guard: too little text to assess responsibly ----------------------
    if not is_assessable_text(message, min_chars=settings.min_assessable_chars):
        return ClarificationResponse(
            investigation_id=investigation_id,
            question=UNCERTAINTY_WORDING["clarification"],
        )

    facts = _Facts()

    # --- Phase 1: the model may choose tools ------------------------------
    await _model_tool_phase(state, llm, facts, max_tool_calls)

    # --- Phase 2: deterministic baseline fills the gaps -------------------
    await _baseline_plan(state, facts, max_tool_calls)

    # --- Assemble + guardrails -------------------------------------------
    assessment = await _assemble(state, facts)
    return await _guard_and_return(state, facts, assessment, llm)


# ---------------------------------------------------------------------------
# Phase 1: model-chosen tools
# ---------------------------------------------------------------------------
async def _model_tool_phase(
    state: InvestigationState, llm: LLMClient, facts: _Facts, cap: int
) -> None:
    """Offer the tools to the model and execute whatever it asks for (bounded)."""
    tools = [
        {
            "name": declaration.name,
            "description": declaration.description,
            "parameters": declaration.input_schema,
        }
        for declaration in get_tool_declarations()
    ]
    messages = [
        LLMMessage(role="system", content=SYSTEM_PROMPT),
        LLMMessage(
            role="user",
            content=build_planning_prompt(state.message, state.sender, cap),
        ),
    ]

    for _round in range(_MAX_MODEL_ROUNDS):
        if state.tool_calls_used >= cap:
            return

        try:
            response = await llm.generate(messages, tools=tools)
        except Exception as exc:  # noqa: BLE001 - degrade to the baseline plan
            await _log(
                state,
                "error",
                payload={"stage": "tool_selection", "message": str(exc)},
            )
            return

        if not response.tool_calls:
            return

        messages.append(LLMMessage(role="assistant", content=response.text or ""))
        executed_any = False

        for call in response.tool_calls:
            if state.tool_calls_used >= cap:
                await _log(
                    state,
                    "error",
                    tool_name=call.name,
                    payload={"reason": "tool_call_cap_reached", "cap": cap},
                )
                break
            output = await _execute(state, call.name, dict(call.arguments), facts, cap)
            if output is None:
                continue
            executed_any = True
            messages.append(
                LLMMessage(
                    role="tool",
                    tool_name=call.name,
                    content=json.dumps(output, default=str),
                )
            )

        if not executed_any:
            return


# ---------------------------------------------------------------------------
# Phase 2: deterministic baseline plan
# ---------------------------------------------------------------------------
async def _baseline_plan(state: InvestigationState, facts: _Facts, cap: int) -> None:
    """Run the required tools the model did not run, stopping at the cap."""
    if not _at_cap(state, cap) and "inspect_indicators" not in facts.done:
        await _execute(
            state,
            "inspect_indicators",
            {"message": state.message, "sender": state.sender},
            facts,
            cap,
        )

    if not _at_cap(state, cap) and "detect_social_engineering" not in facts.done:
        await _execute(
            state,
            "detect_social_engineering",
            {"message": state.message},
            facts,
            cap,
        )

    for url in facts.discovered_urls[:_MAX_URLS_ANALYSED]:
        if _at_cap(state, cap):
            break
        await _execute(state, "analyze_url_structure", {"url": url}, facts, cap)

    for host in _hosts_to_check(facts)[:_MAX_DOMAINS_CHECKED]:
        if _at_cap(state, cap):
            break
        await _execute(state, "check_domain_reputation", {"domain": host}, facts, cap)

    if not _at_cap(state, cap) and "search_guidance" not in facts.done:
        await _execute(
            state,
            "search_guidance",
            {"query": _guidance_query(facts), "limit": 3},
            facts,
            cap,
        )

    if not _at_cap(state, cap) and "map_attack_sequence" not in facts.done:
        await _execute(
            state,
            "map_attack_sequence",
            {
                "message": state.message,
                "indicators": [item.model_dump(mode="json") for item in facts.all_indicators],
            },
            facts,
            cap,
        )


def _hosts_to_check(facts: _Facts) -> list[str]:
    """Hosts worth a reputation lookup: the host itself plus its base domain."""
    hosts: list[str] = []
    for finding in facts.url_findings:
        if not finding.host:
            continue
        for candidate in (finding.host, registrable_domain(finding.host)):
            if candidate and candidate not in hosts:
                hosts.append(candidate)
    return hosts


def _guidance_query(facts: _Facts) -> str:
    """Build a guidance search query from the detected indicators."""
    detected = {
        indicator.id
        for indicator in facts.all_indicators
        if indicator.status.value == "detected"
    }
    terms: list[str] = []
    if "credential_request" in detected:
        terms.append("credentials mfa password")
    if "payment_change" in detected:
        terms.append("payment fraud bank")
    if "link_present" in detected or "ip_literal_host" in detected:
        terms.append("links phishing")
    if "urgency" in detected or "urgency_language" in detected:
        terms.append("urgency")
    if "secrecy" in detected:
        terms.append("social-engineering")
    if "attachment_present" in detected:
        terms.append("phishing attachments")
    if not terms:
        terms.append("general")
    return " ".join(terms)


# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------
def _at_cap(state: InvestigationState, cap: int) -> bool:
    """True when the tool budget is exhausted."""
    return state.tool_calls_used >= cap


async def _execute(
    state: InvestigationState,
    name: str,
    arguments: dict[str, Any],
    facts: _Facts,
    cap: int,
) -> dict[str, Any] | None:
    """Validate, run, and log one tool call. Returns the serialised output.

    Raises:
        ToolCallCapExceeded: if called when the budget is already spent.
    """
    if _at_cap(state, cap):
        raise ToolCallCapExceeded(
            f"Tool budget of {cap} calls is exhausted; '{name}' was not run."
        )

    # Hard rule 2: only allow-listed, read-only tools can ever run here.
    if name not in TOOL_NAMES or name not in _TOOL_FUNCS:
        await _log(
            state,
            "error",
            tool_name=name,
            payload={"reason": "tool_not_allow_listed"},
        )
        return None

    model = _INPUT_MODELS[name]
    try:
        parsed = model.model_validate(arguments)
    except ValidationError as exc:
        await _log(
            state,
            "error",
            tool_name=name,
            payload={"reason": "invalid_arguments", "issues": exc.errors()[:5]},
        )
        return None

    state.tool_calls_used += 1
    await _log(state, "tool_call", tool_name=name, payload=parsed.model_dump(mode="json"))

    try:
        output: BaseModel = await _TOOL_FUNCS[name](parsed)
    except Exception as exc:  # noqa: BLE001 - one failed tool must not sink the run
        await _log(state, "error", tool_name=name, payload={"message": str(exc)})
        return None

    _apply(facts, name, output)
    payload = output.model_dump(mode="json")
    await _log(state, "tool_result", tool_name=name, payload=payload)
    return payload


def _apply(facts: _Facts, name: str, output: BaseModel) -> None:
    """Store a tool output in the facts object."""
    if isinstance(output, InspectIndicatorsOutput):
        facts.indicators = output.indicators
        facts.discovered_urls = output.urls
        facts.notes.extend(output.notes)
    elif isinstance(output, DetectSocialEngineeringOutput):
        facts.tactics = output.tactics
        facts.notes.extend(output.notes)
    elif isinstance(output, AnalyzeUrlStructureOutput):
        facts.url_findings.append(output)
    elif isinstance(output, CheckDomainReputationOutput):
        facts.domain_checks.append(output)
    elif isinstance(output, SearchGuidanceOutput):
        facts.guidance = output.results
    elif isinstance(output, MapAttackSequenceOutput):
        facts.steps = output.steps
        facts.notes.extend(output.notes)
    facts.done.add(name)


async def _log(
    state: InvestigationState,
    kind: ActivityKind,
    *,
    tool_name: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    """Append an activity entry and best-effort persist it (never raises)."""
    from app.services.activity_log import record_activity

    state.activity.append(
        ActivityEntry(
            investigation_id=state.investigation_id,
            kind=kind,
            tool_name=tool_name,
            payload=payload or {},
        )
    )
    await record_activity(
        investigation_id=state.investigation_id,
        kind=kind,
        tool_name=tool_name,
        payload=payload,
    )


# ---------------------------------------------------------------------------
# Assembly + guardrails
# ---------------------------------------------------------------------------
async def _assemble(
    state: InvestigationState,
    facts: _Facts,
    *,
    narrative: NarrativeDraft | None = None,
) -> AssessmentResponse:
    """Build an assessment from the facts, optionally using model wording."""
    indicators = facts.all_indicators
    url_findings = [
        UrlFinding(
            url=finding.url,
            defanged=finding.defanged,
            host=finding.host,
            observations=finding.observations,
        )
        for finding in facts.url_findings
    ]
    risk = assess_risk(indicators)

    summary = build_assessment_summary(indicators, risk, url_findings)
    next_steps = build_next_steps(indicators, risk, url_findings)

    if narrative is not None:
        if narrative.assessment.strip():
            summary = narrative.assessment.strip()
        if narrative.next_steps:
            next_steps = narrative.next_steps

    assessment = AssessmentResponse(
        investigation_id=state.investigation_id,
        urls=url_findings,
        indicators=indicators,
        evidence=_top_level_evidence(indicators),
        attack_sequence=facts.steps,
        guidance=facts.guidance,
        risk=risk,
        assessment=summary,
        next_steps=next_steps,
        draft="",
        validation=_PENDING_VALIDATION,
        activity=state.activity,
    )

    draft = build_guidance_draft(assessment)
    if narrative is not None and narrative.draft.strip() and _draft_is_safe(narrative.draft):
        draft = narrative.draft.strip()

    return assessment.model_copy(update={"draft": draft})


_PENDING_VALIDATION = ValidationResult(
    passed=False, issues=["Validation has not run yet."]
)


def _top_level_evidence(indicators: list[Indicator]) -> list[Evidence]:
    """Union of indicator evidence spans, de-duplicated and capped."""
    spans: list[Evidence] = []
    for indicator in indicators:
        for span in indicator.evidence:
            if span not in spans:
                spans.append(span)
            if len(spans) >= _MAX_TOP_LEVEL_EVIDENCE:
                return spans
    return spans


def _draft_is_safe(text: str) -> bool:
    """Reject model drafts that claim the message is safe (hard rule 5)."""
    lowered = text.lower()
    return not any(
        phrase in lowered
        for phrase in ("is safe", "appears safe", "message is safe", "no risk", "risk-free")
    )


async def _guard_and_return(
    state: InvestigationState,
    facts: _Facts,
    assessment: AssessmentResponse,
    llm: LLMClient,
) -> AssessmentResponse | ClarificationResponse:
    """Run validation (with one repair pass) and return the final response.

    Repair pass: if the model-refined wording fails validation, the
    deterministic template narrative is used instead. Templates are valid by
    construction, so this repairs wording, never facts.
    """
    known_ids = await _known_guidance_ids()

    # 1. Optional model refinement of the template wording.
    refined = await _refine_with_model(state, llm, assessment)
    if refined is not None:
        candidate = await _assemble(state, facts, narrative=refined)
        result = validate_assessment(state.message, candidate, known_ids)
        if result.passed:
            return _with_activity(candidate, state, result)
        await _log(
            state,
            "error",
            payload={"reason": "model_narrative_failed_validation", "issues": result.issues},
        )

    # 2. Deterministic narrative: the repair pass, valid by construction.
    result = validate_assessment(state.message, assessment, known_ids)
    if result.passed:
        return _with_activity(assessment, state, result)

    # 3. Still invalid: return a clarification rather than unvalidated output.
    await _log(
        state,
        "error",
        payload={"reason": "assessment_failed_validation", "issues": result.issues},
    )
    return ClarificationResponse(
        investigation_id=state.investigation_id,
        question=(
            "The analysis could not be validated against the message text, so it has "
            "not been shown. " + UNCERTAINTY_WORDING["clarification"]
        ),
    )


def _with_activity(
    assessment: AssessmentResponse, state: InvestigationState, validation: ValidationResult
) -> AssessmentResponse:
    """Return the assessment with the final activity list and validation result.

    The activity list is re-read from the state so entries appended after the
    assessment was assembled (e.g. validation failures) are still included.
    """
    return assessment.model_copy(
        update={"activity": list(state.activity), "validation": validation}
    )


async def _refine_with_model(
    state: InvestigationState, llm: LLMClient, assessment: AssessmentResponse
) -> NarrativeDraft | None:
    """Ask the model to improve the wording. Returns None when unavailable."""
    prompt = build_finalize_prompt(
        summary=assessment.assessment,
        next_steps=assessment.next_steps,
        draft=assessment.draft,
    )
    try:
        response = await llm.generate(
            [
                LLMMessage(role="system", content=SYSTEM_PROMPT),
                LLMMessage(role="user", content=prompt),
            ],
            tools=None,
        )
    except Exception as exc:  # noqa: BLE001 - templates are the fallback
        await _log(state, "error", payload={"stage": "finalize", "message": str(exc)})
        return None

    return _parse_narrative(response.text)


def _parse_narrative(text: str) -> NarrativeDraft | None:
    """Parse the model's JSON narrative, tolerating code fences."""
    if not text or "{" not in text:
        return None
    candidate = text[text.find("{") : text.rfind("}") + 1]
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    try:
        draft = NarrativeDraft.model_validate(payload)
    except ValidationError:
        return None
    return draft if (draft.assessment or draft.next_steps or draft.draft) else None


async def _known_guidance_ids() -> set[str]:
    """Every guidance ID that exists, used to reject invented citations."""
    try:
        return set(await repositories.list_guidance_ids())
    except Exception:  # noqa: BLE001 - without a datastore we cannot verify
        return set()
