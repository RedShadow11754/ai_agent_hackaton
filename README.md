# AI Suspicious Message Investigation Agent

A text-only investigation assistant for an IT helpdesk analyst. The analyst pastes a
suspicious message; the agent explains the indicators in plain language, maps the likely
attack sequence, cites internal guidance, and drafts a reply. Nothing is saved until a
human explicitly approves it.

**Stack:** React + TypeScript + Vite + Tailwind (frontend) · FastAPI + Pydantic v2 (backend)
· Supabase Postgres · Gemini free tier behind a swappable adapter · single Render web service.

> Status: **scaffold**. Folder structure, API contract, and the approval gate are in place;
> tool/service logic is stubbed with `TODO`s. See [Assignable TODOs](#assignable-todos).

---

## Hard rules (encoded in code and comments)

1. **Text-only analysis.** Never fetch, visit, or resolve any URL from a message.
   (`app/tools/analyze_url_structure.py`, `app/agent/prompts.py`)
2. **`create_incident` is not an LLM tool.** It is callable only by `POST /api/incidents`,
   which rejects requests without `approved: true`.
   (`app/agent/registry.py`, `app/api/routes/incidents.py`)
3. **Tool calls are capped per investigation** (`MAX_TOOL_CALLS`, default 8), enforced in the loop.
4. **No secrets in the repo or the frontend.** `.env.example` holds placeholders only; real keys
   live in Render environment variables. The frontend never receives a secret.
5. **Never label a message "safe".** The lowest band is `Low / Inconclusive`; indicator states are
   `detected | not_detected | not_assessable`.
6. **All message/model text is plain text in the UI.** No `dangerouslySetInnerHTML`; URLs are shown
   defanged and non-clickable.
7. **All demo data is fictitious** — reserved domains (`.test` / `.example`) and `192.0.2.x` IPs only.

---

## Layout

```
/
├─ README.md  .env.example  .gitignore  render.yaml
├─ supabase/        schema.sql (RLS on, no policies), seed.sql
├─ backend/         requirements.txt, pytest.ini
│  ├─ app/          main.py, config.py
│  │  ├─ api/       deps.py, routes/{health,investigate,incidents}.py
│  │  ├─ agent/     loop.py, prompts.py, registry.py
│  │  ├─ llm/       base.py, gemini.py, fake.py
│  │  ├─ tools/     inspect_indicators, analyze_url_structure, detect_social_engineering,
│  │  │             check_domain_reputation, search_guidance, map_attack_sequence,
│  │  │             create_incident (approval-only)
│  │  ├─ services/  validate_evidence, assess_risk, evidence, guidance_draft, activity_log
│  │  ├─ db/        client.py, repositories.py
│  │  └─ schemas/   common.py, investigate.py, tools.py, incidents.py
│  └─ tests/        pytest suite (one runnable approval-gate test, rest skipped stubs)
└─ web/             Vite app; src/{api,types,state,data,pages,components,styles}
```

---

## Setup

### 1. Environment

```bash
cp .env.example .env      # then fill in the placeholders
```

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Gemini key (free tier). Confirm free access **and function calling** on your account. |
| `GEMINI_MODEL` | Model id, default `gemini-1.5-flash`. |
| `LLM_PROVIDER` | `gemini` for real calls, `fake` for the deterministic offline stub (no key needed). |
| `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | Backend-only database access. The service key bypasses RLS — never expose it. |
| `MAX_TOOL_CALLS` | Hard cap per investigation (default 8). |
| `MAX_MESSAGE_CHARS` | Rejects oversized pastes (default 8000). |
| `RATE_LIMIT_PER_MINUTE` | In-process rate limit per client IP. |
| `CORS_ORIGINS` | Local dev only; in production the frontend is served from the same origin. |

### 2. Backend

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r backend/requirements.txt
cd backend && uvicorn app.main:app --reload --port 8000
```

* Health check (works with no database and no API key): <http://127.0.0.1:8000/api/health>
* Interactive docs: <http://127.0.0.1:8000/docs>

### 3. Frontend

```bash
cd web
npm install
npm run dev        # http://localhost:5173, proxies /api to :8000
npm run build      # outputs web/dist, which FastAPI serves in production
```

### 4. Tests

```bash
cd backend && python -m pytest
```

The scaffold runs: `test_approval_gate.py` (two passing tests) plus skipped stub tests to be
filled in. `pytest.ini` sets `pythonpath = .`, so no install is needed.

### 5. Seeding Supabase

1. Create a free Supabase project.
2. In the SQL editor, run `supabase/schema.sql`, then `supabase/seed.sql`.
3. Both scripts enable Row Level Security with **no public policies**, so only the backend
   service key can read or write. Do not add a public policy.
4. Put the project URL and `service_role` key in `.env` (locally) and in Render (production).

Seed contents: 5 guidance passages (`SEC-01`…`SEC-05`), 3 trusted domains, 6 reputation rows.
The 5 sample messages live in `web/src/data/sampleMessages.ts`.

---

## Deploy to Render

`render.yaml` defines **one** free web service that builds the frontend and runs FastAPI, which
serves the built SPA from `web/dist` — one URL, no CORS.

1. Push the repo to GitHub and create a Blueprint/Web Service from `render.yaml`.
2. Set `GEMINI_API_KEY`, `SUPABASE_URL`, and `SUPABASE_SERVICE_KEY` in the Render dashboard
   (they are marked `sync: false`, so they are never committed).
3. Deploy. Render runs `pip install … && cd web && npm ci && npm run build`, then
   `uvicorn app.main:app`.

### Free-tier caveats (state these in the submission)

* **Render free services sleep when idle.** The first request after a pause takes ~30–60s.
  Wake the service before judging.
* **Supabase free projects pause after ~1 week of inactivity.** Open the dashboard to wake it,
  and confirm `/api/health` reports `database_configured: true`.
* Gemini free tier has rate limits; the agent caps tool calls and prompt size to stay inside them.

---

## API contract

All errors use one shape: `{"error": {"code": "...", "message": "..."}}`.

| Method | Path | Notes |
|---|---|---|
| `GET` | `/api/health` | Works with no configuration. |
| `POST` | `/api/investigate` | Returns `{type:"clarification", question}` or a full `{type:"assessment", …}`. Saves nothing. |
| `POST` | `/api/incidents` | Requires `approved: true` plus the payload; returns `{id, status}` only after the insert commits. |
| `GET` | `/api/incidents` | Recent incidents. |
| `GET` | `/api/incidents/{id}` | One incident with its full assessment. |
| `GET` | `/api/incidents/{id}/activity` | Audit trail for one incident. |

Guardrails run in code, not by model choice: `validate_evidence` then `assess_risk` run after the
model finishes. `create_incident` is deliberately absent from `app/agent/registry.py`, and the
module import fails loudly if it is ever added.

---

## Assignable TODOs

| Area | Stub | TODO |
|---|---|---|
| Rules | `tools/inspect_indicators.py` | Regex/heuristic extraction with exact offsets |
| Rules | `tools/analyze_url_structure.py` | `urlsplit` + heuristics, defanged output |
| Rules | `tools/detect_social_engineering.py` | Tactic patterns with phrase evidence |
| Agent | `agent/loop.py` | Bounded tool loop, cap enforcement, repair pass |
| Agent | `tools/map_attack_sequence.py` | Indicator→ordered-steps mapping |
| LLM | `llm/gemini.py` | `contents`/`functionCall` translation, 429 retry |
| Data | `db/repositories.py`, `db/client.py` | All Supabase queries, timeouts, error mapping |
| Data | `tools/search_guidance.py`, `tools/check_domain_reputation.py` | Wire to repositories |
| Data | `tools/create_incident.py`, `services/activity_log.py` | Atomic `INC-####`, audit rows |
| Guards | `services/validate_evidence.py` | Evidence/guidance/score consistency checks |
| Guards | `services/assess_risk.py` | Weighted score, band, itemised breakdown |
| Guards | `services/guidance_draft.py` | Template-based user guidance draft |
| API | `api/routes/incidents.py` | Implement the three GET routes |
| Frontend | `pages/*`, `components/*` | Fill in per the mockup; each file has a `TODO` |
| Tests | `backend/tests/*` | Replace skipped stubs with real assertions |

After implementing, replace each stub's `raise NotImplementedError(...)` and delete the
`TODO` comment it belongs to.
