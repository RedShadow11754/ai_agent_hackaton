"""Local SQLite store: the offline data path.

Why this exists: the demo must run end to end with no external services (no
Supabase project, no Gemini key). This store mirrors the table shapes in
`supabase/schema.sql` and the rows in `supabase/seed.sql`, so
`app.db.repositories` can switch between them without callers noticing.

Scope: single-process, single-file SQLite. It is NOT a production database -
no RLS, no migrations, no connection pool. Use Supabase for the real deployment.

Security note: SQLite has no Row Level Security. This file lives on the server
only (`.data/`, gitignored) and is never served to the browser.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import get_settings

# ---------------------------------------------------------------------------
# Schema - mirrors supabase/schema.sql (jsonb -> TEXT holding JSON, text[] -> JSON)
# ---------------------------------------------------------------------------
_SCHEMA = """
create table if not exists guidance (
    id    text primary key,
    title text not null,
    body  text not null,
    tags  text not null default '[]'
);

create table if not exists trusted_domains (
    domain text primary key,
    label  text not null
);

create table if not exists domain_reputation (
    domain text primary key,
    status text not null,
    source text not null default 'manual',
    note   text
);

create table if not exists incidents (
    id              text primary key,
    created_at      text not null,
    approved_at     text,
    reviewed_by     text,
    message         text not null default '',
    urls            text not null default '[]',
    indicators      text not null default '[]',
    evidence        text not null default '[]',
    attack_sequence text not null default '[]',
    guidance_refs   text not null default '[]',
    risk_score      integer not null default 0,
    risk_band       text not null default 'Low / Inconclusive',
    assessment      text not null default '',
    next_steps      text not null default '[]',
    draft           text not null default '',
    draft_edited    integer not null default 0,
    status          text not null default 'Pending review'
);

create table if not exists activity_log (
    id               integer primary key autoincrement,
    investigation_id text not null,
    incident_id      text,
    created_at       text not null,
    kind             text not null,
    tool_name        text,
    payload          text not null default '{}'
);
"""

# ---------------------------------------------------------------------------
# Seed data - mirrors supabase/seed.sql. FICTIONAL ONLY (hard rule 7):
# reserved domains (.test / .example) and documentation IPs (192.0.2.0/24).
# ---------------------------------------------------------------------------
_SEED_GUIDANCE: list[tuple[str, str, str, list[str]]] = [
    (
        "SEC-01",
        "Do not click links in unexpected messages",
        "If a message asks you to sign in, pay, or open an attachment and you were "
        "not expecting it, do not click. Open the site by typing the known address "
        "yourself, or verify with the sender through a channel you already trust.",
        ["links", "phishing", "general"],
    ),
    (
        "SEC-02",
        "Verify payment and bank-detail changes by phone",
        "Never act on new bank details sent by email or chat. Call the supplier or "
        "colleague on a number you already have on file before any payment details "
        "are changed.",
        ["payment", "fraud", "finance"],
    ),
    (
        "SEC-03",
        "Report suspected phishing to the service desk",
        "Forward the message as an attachment to the service desk, then delete it "
        "from your mailbox. Do not reply to the sender and do not open attachments.",
        ["reporting", "phishing", "process"],
    ),
    (
        "SEC-04",
        "Treat urgency and secrecy as warning signs",
        "Messages that demand immediate action, threaten consequences, or ask you to "
        "keep the request secret are common manipulation tactics. Slow down and "
        "verify before acting.",
        ["social-engineering", "urgency", "general"],
    ),
    (
        "SEC-05",
        "Multi-factor codes are never shared",
        "No legitimate helpdesk, bank, or supplier will ask you to read out a "
        "one-time code, approve a push prompt, or share a password. Refuse and "
        "report it.",
        ["credentials", "mfa", "general"],
    ),
]

_SEED_TRUSTED_DOMAINS: list[tuple[str, str]] = [
    ("intranet.example", "Internal intranet portal"),
    ("hr-portal.example", "Internal HR self-service"),
    ("helpdesk.example", "Internal IT service desk"),
]

_SEED_DOMAIN_REPUTATION: list[tuple[str, str, str, str]] = [
    ("intranet.example", "known_safe", "manual", "Internal allow-listed portal."),
    ("hr-portal.example", "known_safe", "manual", "Internal allow-listed portal."),
    ("example.test", "known_safe", "manual", "Reserved test domain used in training material."),
    (
        "secure-login.test",
        "known_suspicious",
        "manual",
        "Lookalike used in a past phishing simulation.",
    ),
    (
        "payroll-update.example",
        "known_suspicious",
        "manual",
        "Impersonates the payroll system in simulations.",
    ),
    (
        "192.0.2.45",
        "unknown",
        "manual",
        "Documentation IP literal (TEST-NET-1); no reputation data.",
    ),
]


def _now() -> str:
    """UTC timestamp in ISO-8601 form."""
    return datetime.now(timezone.utc).isoformat()


class LocalStore:
    """SQLite-backed implementation of every repository query.

    A single connection is cached per instance and guarded by a lock, because
    `:memory:` databases are per-connection and must be shared.
    """

    def __init__(self, path: str) -> None:
        """Record the database path. Nothing is opened until first use."""
        self._path = path
        self._lock = threading.Lock()
        self._connection: sqlite3.Connection | None = None

    # -- connection / bootstrap ------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        """Open (once) and initialise the database, seeding it if empty."""
        with self._lock:
            if self._connection is None:
                if self._path != ":memory:":
                    Path(self._path).parent.mkdir(parents=True, exist_ok=True)
                connection = sqlite3.connect(self._path, check_same_thread=False)
                connection.row_factory = sqlite3.Row
                connection.executescript(_SCHEMA)
                self._seed(connection)
                connection.commit()
                self._connection = connection
            return self._connection

    @staticmethod
    def _seed(connection: sqlite3.Connection) -> None:
        """Insert the demo rows when the tables are empty (idempotent)."""
        if connection.execute("select count(*) from guidance").fetchone()[0] == 0:
            connection.executemany(
                "insert into guidance (id, title, body, tags) values (?, ?, ?, ?)",
                [(gid, title, body, json.dumps(tags)) for gid, title, body, tags in _SEED_GUIDANCE],
            )
        if connection.execute("select count(*) from trusted_domains").fetchone()[0] == 0:
            connection.executemany(
                "insert into trusted_domains (domain, label) values (?, ?)",
                _SEED_TRUSTED_DOMAINS,
            )
        if connection.execute("select count(*) from domain_reputation").fetchone()[0] == 0:
            connection.executemany(
                "insert into domain_reputation (domain, status, source, note) values (?, ?, ?, ?)",
                _SEED_DOMAIN_REPUTATION,
            )

    # -- guidance --------------------------------------------------------
    def list_guidance_ids(self) -> list[str]:
        """Return every guidance ID (used to verify stored citations)."""
        connection = self._connect()
        rows = connection.execute("select id from guidance order by id").fetchall()
        return [row["id"] for row in rows]

    def get_guidance_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """Fetch guidance rows by exact ID."""
        if not ids:
            return []
        connection = self._connect()
        placeholders = ",".join("?" for _ in ids)
        rows = connection.execute(
            f"select id, title, body, tags from guidance where id in ({placeholders})",
            list(ids),
        ).fetchall()
        return [self._guidance_row(row) for row in rows]

    def search_guidance(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Rank guidance rows by keyword/tag overlap with `query`."""
        terms = [term for term in _tokenize(query) if len(term) > 2]
        connection = self._connect()
        rows = connection.execute("select id, title, body, tags from guidance").fetchall()

        scored: list[tuple[float, dict[str, Any]]] = []
        for row in rows:
            item = self._guidance_row(row)
            haystack_tags = " ".join(item["tags"]).lower()
            haystack_text = f"{item['title']} {item['body']}".lower()
            score = 0.0
            for term in terms:
                if term in haystack_tags:
                    score += 2.0  # tag hits are the strongest signal
                elif term in haystack_text:
                    score += 1.0
            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda pair: (-pair[0], pair[1]["id"]))
        return [item for _, item in scored[:limit]]

    @staticmethod
    def _guidance_row(row: sqlite3.Row) -> dict[str, Any]:
        """Convert a guidance row to a plain dict with parsed tags."""
        return {
            "id": row["id"],
            "title": row["title"],
            "body": row["body"],
            "tags": json.loads(row["tags"]),
        }

    # -- domains ---------------------------------------------------------
    def list_trusted_domains(self) -> list[str]:
        """Return every trusted domain, sorted."""
        connection = self._connect()
        rows = connection.execute("select domain from trusted_domains order by domain").fetchall()
        return [row["domain"] for row in rows]

    def get_domain_reputation(self, domain: str) -> dict[str, Any] | None:
        """Return reputation + trusted status for a domain, or None when unknown."""
        connection = self._connect()
        key = domain.strip().lower()
        row = connection.execute(
            "select domain, status, source, note from domain_reputation where domain = ?",
            (key,),
        ).fetchone()
        trusted = (
            connection.execute(
                "select 1 from trusted_domains where domain = ?", (key,)
            ).fetchone()
            is not None
        )
        if row is None and not trusted:
            return None
        return {
            "domain": key,
            "status": row["status"] if row else "unknown",
            "source": row["source"] if row else "allow-list",
            "note": row["note"] if row else "Listed on the trusted-domain allow-list.",
            "trusted": trusted,
        }

    # -- incidents -------------------------------------------------------
    def insert_incident(self, fields: dict[str, Any]) -> dict[str, str]:
        """Insert one approved incident, allocating the next INC-#### id."""
        connection = self._connect()
        with self._lock:
            next_number = connection.execute("select count(*) from incidents").fetchone()[0] + 1
            incident_id = f"INC-{next_number:04d}"
            connection.execute(
                """
                insert into incidents (
                    id, created_at, approved_at, reviewed_by, message, urls, indicators,
                    evidence, attack_sequence, guidance_refs, risk_score, risk_band,
                    assessment, next_steps, draft, draft_edited, status
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident_id,
                    _now(),
                    _now(),
                    fields.get("reviewed_by"),
                    fields.get("message", ""),
                    json.dumps(fields.get("urls", [])),
                    json.dumps(fields.get("indicators", [])),
                    json.dumps(fields.get("evidence", [])),
                    json.dumps(fields.get("attack_sequence", [])),
                    json.dumps(fields.get("guidance_refs", [])),
                    int(fields.get("risk_score", 0)),
                    fields.get("risk_band", "Low / Inconclusive"),
                    fields.get("assessment", ""),
                    json.dumps(fields.get("next_steps", [])),
                    fields.get("draft", ""),
                    1 if fields.get("draft_edited") else 0,
                    fields.get("status", "Pending review"),
                ),
            )
            connection.commit()
        return {"id": incident_id, "status": fields.get("status", "Pending review")}

    def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        """Return one stored incident row, or None when it does not exist."""
        connection = self._connect()
        row = connection.execute(
            "select * from incidents where id = ?", (incident_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_incidents(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return recent incidents, newest first."""
        connection = self._connect()
        rows = connection.execute(
            "select * from incidents order by created_at desc, id desc limit ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]

    # -- activity --------------------------------------------------------
    def insert_activity(
        self,
        *,
        investigation_id: str,
        kind: str,
        tool_name: str | None = None,
        incident_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Append one audit row."""
        connection = self._connect()
        with self._lock:
            connection.execute(
                """
                insert into activity_log
                    (investigation_id, incident_id, created_at, kind, tool_name, payload)
                values (?, ?, ?, ?, ?, ?)
                """,
                (
                    investigation_id,
                    incident_id,
                    _now(),
                    kind,
                    tool_name,
                    json.dumps(payload or {}),
                ),
            )
            connection.commit()

    def list_activity(
        self,
        *,
        investigation_id: str | None = None,
        incident_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return activity rows oldest-first for an investigation or incident."""
        connection = self._connect()
        clauses: list[str] = []
        params: list[Any] = []
        if investigation_id:
            clauses.append("investigation_id = ?")
            params.append(investigation_id)
        if incident_id:
            clauses.append("incident_id = ?")
            params.append(incident_id)
        where = f"where {' or '.join(clauses)}" if clauses else ""
        rows = connection.execute(
            f"select * from activity_log {where} order by id asc", params
        ).fetchall()
        return [dict(row) for row in rows]


def _tokenize(text: str) -> list[str]:
    """Lower-case word tokens, for keyword scoring."""
    cleaned = "".join(char if char.isalnum() else " " for char in text.lower())
    return [token for token in cleaned.split() if token]


@lru_cache(maxsize=4)
def get_local_store() -> LocalStore:
    """Return the process-wide local store for the configured path."""
    return LocalStore(get_settings().local_db_path)
