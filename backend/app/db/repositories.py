"""Typed queries against the datastore.

All functions are async wrappers. Two backends are supported and selected by
`DATA_BACKEND` (default `auto`):

* `supabase` - the real deployment (Postgres + service role key, RLS on);
* `local`    - a single-file SQLite store so the demo runs with no cloud account.

Column names and SQL live here so routes and services stay storage-agnostic.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any, Literal

from app.config import get_settings
from app.db.client import get_supabase_client
from app.db.local_store import get_local_store
from app.schemas.common import ActivityEntry, Evidence, GuidanceRef, Indicator
from app.schemas.incidents import (
    CreateIncidentRequest,
    IncidentCreatedResponse,
    IncidentDetail,
    IncidentSummary,
)
from app.schemas.investigate import AssessmentResponse
from app.schemas.tools import CheckDomainReputationOutput

ActivityKind = Literal["tool_call", "tool_result", "error", "approval", "save"]


def _use_supabase() -> bool:
    """True when the configured backend is Supabase."""
    return get_settings().resolved_data_backend == "supabase"


def _supabase() -> Any:
    """Return the cached Supabase client."""
    return get_supabase_client()


# ---------------------------------------------------------------------------
# Guidance
# ---------------------------------------------------------------------------
async def get_guidance_by_ids(ids: Sequence[str]) -> list[GuidanceRef]:
    """Fetch guidance rows by exact IDs (used to verify citations)."""
    if not ids:
        return []

    if _use_supabase():
        response = (
            _supabase().table("guidance").select("id,title,body,tags").in_("id", list(ids)).execute()
        )
        rows = response.data or []
    else:
        rows = get_local_store().get_guidance_by_ids(list(ids))

    return [GuidanceRef.model_validate(row) for row in rows]


async def search_guidance(query: str, limit: int = 3) -> list[GuidanceRef]:
    """Search guidance by keyword/tag overlap, returning at most `limit` rows.

    The `guidance` table is small (tens of rows), so both backends fetch the
    rows and rank them in Python. TODO: move to a Postgres full-text or pgvector
    index once the corpus grows.
    """
    if _use_supabase():
        response = _supabase().table("guidance").select("id,title,body,tags").limit(200).execute()
        rows = response.data or []
        rows = _rank_guidance(rows, query, limit)
    else:
        rows = get_local_store().search_guidance(query, limit)

    return [GuidanceRef.model_validate(row) for row in rows]


def _rank_guidance(rows: list[dict[str, Any]], query: str, limit: int) -> list[dict[str, Any]]:
    """Score guidance rows by keyword/tag overlap (Supabase path)."""
    terms = [token for token in _tokenize(query) if len(token) > 2]
    scored: list[tuple[float, dict[str, Any]]] = []
    for row in rows:
        tags = " ".join(row.get("tags") or []).lower()
        text = f"{row.get('title', '')} {row.get('body', '')}".lower()
        score = 0.0
        for term in terms:
            if term in tags:
                score += 2.0
            elif term in text:
                score += 1.0
        if score > 0:
            scored.append((score, row))
    scored.sort(key=lambda pair: (-pair[0], pair[1].get("id", "")))
    return [row for _, row in scored[:limit]]


def _tokenize(text: str) -> list[str]:
    """Lower-case word tokens, for keyword scoring."""
    cleaned = "".join(char if char.isalnum() else " " for char in text.lower())
    return [token for token in cleaned.split() if token]


# ---------------------------------------------------------------------------
# Domains
# ---------------------------------------------------------------------------
async def get_domain_reputation(domain: str) -> CheckDomainReputationOutput | None:
    """Return reputation + trusted-list status, or None when the domain is unknown."""
    key = domain.strip().lower()

    if _use_supabase():
        reputation = (
            _supabase()
            .table("domain_reputation")
            .select("domain,status,source,note")
            .eq("domain", key)
            .limit(1)
            .execute()
            .data
            or []
        )
        trusted_rows = (
            _supabase().table("trusted_domains").select("domain").eq("domain", key).limit(1).execute().data
            or []
        )
        if not reputation and not trusted_rows:
            return None
        row = reputation[0] if reputation else {}
        return CheckDomainReputationOutput(
            domain=key,
            status=row.get("status", "unknown"),
            trusted=bool(trusted_rows),
            source=row.get("source") or ("allow-list" if trusted_rows else None),
            note=row.get("note") or ("Listed on the trusted-domain allow-list." if trusted_rows else None),
        )

    row = get_local_store().get_domain_reputation(key)
    if row is None:
        return None
    return CheckDomainReputationOutput.model_validate(row)


async def list_trusted_domains() -> list[str]:
    """Return all trusted domains (for prompt context and tests)."""
    if _use_supabase():
        rows = _supabase().table("trusted_domains").select("domain").order("domain").execute().data or []
        return [row["domain"] for row in rows]
    return get_local_store().list_trusted_domains()


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------
async def insert_incident(request: CreateIncidentRequest) -> IncidentCreatedResponse:
    """Insert an approved incident and return its generated ID and status.

    Only called after the route's approval gate has verified `approved is True`.
    """
    payload = request.payload
    fields: dict[str, Any] = {
        "message": request.message,
        "urls": [finding.model_dump() for finding in payload.urls],
        "indicators": [indicator.model_dump(mode="json") for indicator in payload.indicators],
        "evidence": [span.model_dump() for span in payload.evidence],
        "attack_sequence": [step.model_dump(mode="json") for step in payload.attack_sequence],
        "guidance_refs": [ref.id for ref in payload.guidance],
        "risk_score": payload.risk.score,
        "risk_band": payload.risk.band.value,
        "assessment": payload.assessment,
        "next_steps": list(payload.next_steps),
        "draft": request.draft if request.draft is not None else payload.draft,
        "draft_edited": request.draft_edited,
        "reviewed_by": request.reviewed_by,
        "status": "Pending review",
    }

    if _use_supabase():
        client = _supabase()
        allocated = client.rpc("next_incident_id").execute().data
        incident_id = str(allocated)
        client.table("incidents").insert(
            {
                "id": incident_id,
                **fields,
                "approved_at": "now()",
                "draft_edited": bool(fields["draft_edited"]),
            }
        ).execute()
        return IncidentCreatedResponse(id=incident_id, status=fields["status"])

    created = get_local_store().insert_incident(fields)
    return IncidentCreatedResponse.model_validate(created)


async def get_incident(incident_id: str) -> IncidentDetail | None:
    """Return one incident with its full assessment, or None when missing.

    `risk.breakdown` and `validation` are not stored as columns; both are
    deterministic functions of the stored indicators, so they are recomputed.
    """
    if _use_supabase():
        rows = (
            _supabase().table("incidents").select("*").eq("id", incident_id).limit(1).execute().data
            or []
        )
        row = rows[0] if rows else None
    else:
        row = get_local_store().get_incident(incident_id)

    if row is None:
        return None
    return await _row_to_incident_detail(row)


async def list_incidents(limit: int = 50) -> list[IncidentSummary]:
    """Return recent incidents, newest first, capped at `limit`."""
    if _use_supabase():
        rows = (
            _supabase()
            .table("incidents")
            .select("id,created_at,risk_band,risk_score,status,message")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
            .data
            or []
        )
    else:
        rows = get_local_store().list_incidents(limit)

    return [
        IncidentSummary(
            id=row["id"],
            created_at=str(row["created_at"]),
            risk_band=row["risk_band"],
            risk_score=int(row["risk_score"]),
            status=row["status"],
            message_preview=_preview(row.get("message", "")),
        )
        for row in rows
    ]


def _preview(message: str, limit: int = 120) -> str:
    """Plain-text preview of the message for the list view."""
    collapsed = " ".join(message.split())
    return collapsed if len(collapsed) <= limit else f"{collapsed[:limit]}..."


async def _row_to_incident_detail(row: dict[str, Any]) -> IncidentDetail:
    """Rebuild an IncidentDetail (with a full assessment) from a stored row."""
    # Imported here to avoid a circular import at module load.
    from app.schemas.common import ValidationResult
    from app.services.assess_risk import assess_risk
    from app.services.validate_evidence import validate_assessment

    message = row.get("message", "")
    indicators = [Indicator.model_validate(item) for item in _as_list(row.get("indicators"))]
    guidance = await get_guidance_by_ids([str(item) for item in _as_list(row.get("guidance_refs"))])
    known_ids = set(await list_guidance_ids())

    # Validation is not stored as a column; it is deterministic, so recompute it.
    # The placeholder below is immediately replaced once the object exists.
    assessment = AssessmentResponse(
        investigation_id=str(row["id"]),
        urls=_as_list(row.get("urls")),
        indicators=indicators,
        evidence=[Evidence.model_validate(item) for item in _as_list(row.get("evidence"))],
        attack_sequence=_as_list(row.get("attack_sequence")),
        guidance=guidance,
        risk=assess_risk(indicators),
        assessment=row.get("assessment", ""),
        next_steps=[str(item) for item in _as_list(row.get("next_steps"))],
        draft=row.get("draft", ""),
        validation=ValidationResult(passed=True, issues=[]),
        activity=await list_activity(incident_id=str(row["id"])),
    )
    assessment = assessment.model_copy(
        update={"validation": validate_assessment(message, assessment, known_ids)}
    )

    return IncidentDetail(
        id=str(row["id"]),
        created_at=str(row["created_at"]),
        approved_at=str(row["approved_at"]) if row.get("approved_at") else None,
        reviewed_by=row.get("reviewed_by"),
        status=row.get("status", "Pending review"),
        message=message,
        assessment=assessment,
    )


async def list_guidance_ids() -> list[str]:
    """Return every guidance ID (used to verify stored citations)."""
    if _use_supabase():
        rows = _supabase().table("guidance").select("id").execute().data or []
        return [row["id"] for row in rows]
    return get_local_store().list_guidance_ids()


def _as_list(value: Any) -> list[Any]:
    """Normalise a JSON column (str, list, or None) into a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []


# ---------------------------------------------------------------------------
# Activity log
# ---------------------------------------------------------------------------
async def insert_activity(
    *,
    investigation_id: str,
    kind: ActivityKind,
    tool_name: str | None = None,
    incident_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    """Append one activity_log row."""
    if _use_supabase():
        _supabase().table("activity_log").insert(
            {
                "investigation_id": investigation_id,
                "incident_id": incident_id,
                "kind": kind,
                "tool_name": tool_name,
                "payload": payload or {},
            }
        ).execute()
        return

    get_local_store().insert_activity(
        investigation_id=investigation_id,
        kind=kind,
        tool_name=tool_name,
        incident_id=incident_id,
        payload=payload,
    )


async def list_activity(
    *,
    investigation_id: str | None = None,
    incident_id: str | None = None,
) -> list[ActivityEntry]:
    """Return activity rows for an investigation or incident, oldest first."""
    if not investigation_id and not incident_id:
        raise ValueError("list_activity needs an investigation_id or an incident_id.")

    if _use_supabase():
        query = _supabase().table("activity_log").select("*")
        if incident_id:
            query = query.eq("incident_id", incident_id)
        else:
            query = query.eq("investigation_id", investigation_id)
        rows = query.order("id").execute().data or []
    else:
        rows = get_local_store().list_activity(
            investigation_id=investigation_id, incident_id=incident_id
        )

    return [
        ActivityEntry(
            id=row.get("id"),
            investigation_id=row.get("investigation_id"),
            incident_id=row.get("incident_id"),
            created_at=str(row["created_at"]) if row.get("created_at") else None,
            kind=row["kind"],
            tool_name=row.get("tool_name"),
            payload=_as_dict(row.get("payload")),
        )
        for row in rows
    ]


def _as_dict(value: Any) -> dict[str, Any]:
    """Normalise a JSON column into a dict."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}
