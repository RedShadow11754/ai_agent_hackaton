# Project 8: AI Suspicious Message Investigation Agent

Tech stack, tool architecture, and coding-agent scaffolding prompt.

## Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Frontend | **React + TypeScript + Vite + Tailwind CSS** | Matches the UI mockup. |
| Routing / data | **React Router + TanStack Query** | Loading, error, and retry states come almost free. |
| Backend | **FastAPI (Python 3.11+) + Pydantic v2 + Uvicorn** | Pydantic covers input validation and the approval payload. |
| Database | **Supabase Postgres (free plan)** via `supabase-py` | Used from the backend only. |
| LLM | **Gemini API free tier**, function calling, behind an adapter (`llm/base.py`) | Confirm your model's free access and tool support on your own account first. |
| Hosting | **Render free web service**, with the built React app served by FastAPI | One URL and no CORS. Vercel or Netlify for the frontend is the alternative. |
| Tests | **pytest** (backend), **Vitest** (optional) | Unit-test every rule-based tool. |

### Free-tier risks to handle

- Supabase free projects pause after about a week of inactivity, and Render free services sleep when idle. Wake both before judging, and state the initial-load delay in your submission.
- Keep `SUPABASE_SERVICE_KEY` and `GEMINI_API_KEY` in Render environment variables only, and commit `.env.example` with placeholders.
- Enable Row Level Security on every table with no public policies, so only your backend can read or write.
- Record each service and its limits in the service register.

## How the tools fit together

- **Model-chosen, read-only tools** (function calling): `inspect_indicators`, `analyze_url_structure`, `detect_social_engineering`, `check_domain_reputation`, `search_guidance`, `map_attack_sequence`.
- **Code-run guardrails** after the model finishes: `validate_evidence`, then `assess_risk_level`. They are not left to the model's choice.
- **Not in the model's tool list:** `create_incident`. Only the approval endpoint can call it.
- **Activity log:** every tool call, result, error, approval, and save outcome is written to a table.

## Prompt for your coding agent

```
You are scaffolding a hackathon project: "AI Suspicious Message Investigation Agent"
(IT helpdesk analyst role). Create the FULL FOLDER STRUCTURE with minimal, 
well-commented stub files only. Do NOT implement business logic yet: each stub 
should contain its signature, a docstring explaining its job, and a TODO. 
Everything must be runnable (backend starts, frontend builds) after scaffolding.

STACK
- Frontend: React + TypeScript + Vite + Tailwind CSS, React Router, TanStack Query
- Backend: FastAPI (Python 3.11), Pydantic v2, Uvicorn, supabase-py, httpx, pytest
- Database: Supabase Postgres (backend access only, service key in env)
- LLM: Gemini free tier via an adapter interface so providers can be swapped
- Deploy: single Render web service; FastAPI serves the built frontend from /web/dist

HARD RULES (encode them in code comments and README)
1. Text-only analysis. Never fetch, visit, or resolve any URL from a message.
2. create_incident is NOT exposed to the LLM as a tool. It is callable only by the
   POST /api/incidents endpoint, which rejects requests without approved=true.
3. Cap tool calls per investigation (config value, default 8), enforced in code.
4. No secrets in the repo or frontend. Provide .env.example with placeholders.
5. Never label a message "safe". Lowest risk band is "Low / Inconclusive".
   Indicator states are: detected | not_detected | not_assessable.
6. Render all message/model text as plain text in the UI; never use 
   dangerouslySetInnerHTML; show URLs defanged and non-clickable.
7. All demo data is fictitious; use reserved domains (.test / .example) and
   192.0.2.x for IPs.

REPO LAYOUT
/
├─ README.md                      (setup, env vars, run, deploy, free-service notes)
├─ .env.example
├─ .gitignore
├─ render.yaml                    (single web service: build frontend, run uvicorn)
├─ supabase/
│  ├─ schema.sql                  (tables below, RLS enabled, no public policies)
│  └─ seed.sql                    (5 messages are in the frontend sample file; seed:
│                                  3 trusted domains, ~6 domain_reputation rows,
│                                  3-6 guidance passages with IDs like SEC-01)
├─ backend/
│  ├─ requirements.txt
│  ├─ pytest.ini
│  ├─ app/
│  │  ├─ main.py                  (FastAPI app, CORS, router mounting, static serving)
│  │  ├─ config.py                (settings from env: keys, call cap, length cap)
│  │  ├─ api/
│  │  │  ├─ deps.py               (db client, rate limiter)
│  │  │  └─ routes/
│  │  │     ├─ health.py          GET  /api/health
│  │  │     ├─ investigate.py     POST /api/investigate  (runs agent, saves nothing)
│  │  │     └─ incidents.py       POST /api/incidents (approval gate)
│  │  │                           GET  /api/incidents, GET /api/incidents/{id}
│  │  │                           GET  /api/incidents/{id}/activity
│  │  ├─ agent/
│  │  │  ├─ loop.py               (bounded tool-calling loop, call cap, clarification)
│  │  │  ├─ prompts.py            (system prompt, uncertainty wording)
│  │  │  └─ registry.py           (tool declarations sent to the model)
│  │  ├─ llm/
│  │  │  ├─ base.py               (LLMClient interface: generate(messages, tools))
│  │  │  ├─ gemini.py             (Gemini implementation)
│  │  │  └─ fake.py               (test stub + forced-failure toggle)
│  │  ├─ tools/
│  │  │  ├─ inspect_indicators.py
│  │  │  ├─ analyze_url_structure.py
│  │  │  ├─ detect_social_engineering.py
│  │  │  ├─ check_domain_reputation.py   (reads domain_reputation table)
│  │  │  ├─ search_guidance.py           (reads guidance table, returns real IDs)
│  │  │  ├─ map_attack_sequence.py       (steps must cite evidence offsets)
│  │  │  └─ create_incident.py           (NOT in registry; approval endpoint only)
│  │  ├─ services/
│  │  │  ├─ validate_evidence.py  (evidence exists, guidance IDs exist, consistent)
│  │  │  ├─ assess_risk.py        (transparent weighted score + band + breakdown)
│  │  │  ├─ evidence.py           (character offsets for highlighting)
│  │  │  ├─ guidance_draft.py     (non-technical user guidance draft)
│  │  │  └─ activity_log.py       (write/read activity_log rows)
│  │  ├─ db/
│  │  │  ├─ client.py             (Supabase client, service key, backend only)
│  │  │  └─ repositories.py       (guidance, domains, incidents, activity queries)
│  │  └─ schemas/
│  │     ├─ common.py             (IndicatorStatus, RiskBand, Evidence{start,end,text})
│  │     ├─ investigate.py        (request/response incl. clarification variant)
│  │     ├─ tools.py              (input/output model per tool)
│  │     └─ incidents.py          (CreateIncidentRequest with approved: bool)
│  └─ tests/
│     ├─ test_inspect_indicators.py
│     ├─ test_analyze_url_structure.py
│     ├─ test_detect_social_engineering.py
│     ├─ test_validate_evidence.py
│     ├─ test_assess_risk.py
│     └─ test_approval_gate.py    (save without approval must fail)
├─ web/
│  ├─ package.json, vite.config.ts, tsconfig.json, tailwind.config.ts, index.html
│  └─ src/
│     ├─ main.tsx, App.tsx        (router + query provider + app shell)
│     ├─ api/                     client.ts (fetch wrapper, error shape), 
│     │                           investigate.ts, incidents.ts
│     ├─ types/                   api.ts (mirror backend schemas)
│     ├─ state/                   InvestigationContext.tsx (keeps data across pages)
│     ├─ data/                    sampleMessages.ts (5 fictitious samples)
│     ├─ pages/
│     │  ├─ InvestigatePage.tsx   (/)
│     │  ├─ ResultsPage.tsx       (/results)
│     │  ├─ ReviewPage.tsx        (/review)
│     │  ├─ IncidentsPage.tsx     (/incidents)
│     │  └─ IncidentDetailPage.tsx(/incidents/:id)
│     ├─ components/
│     │  ├─ layout/               AppShell, Stepper, NoticeBanner
│     │  ├─ RiskBadge.tsx, UncertaintyBanner.tsx, IndicatorCard.tsx
│     │  ├─ EvidenceHighlight.tsx, UrlList.tsx (defanged), GuidanceCard.tsx
│     │  ├─ AttackSequence.tsx, GuidanceDraftEditor.tsx
│     │  ├─ ApprovalPanel.tsx     (checkbox + Approve & Save + Discard)
│     │  ├─ ClarificationPrompt.tsx, ErrorBanner.tsx (with Retry)
│     │  └─ ActivityLog.tsx       (collapsible tool/approval/save log)
│     └─ styles/index.css

DATABASE TABLES (supabase/schema.sql)
- guidance(id text pk e.g. 'SEC-01', title, body, tags text[])
- trusted_domains(domain text pk, label)
- domain_reputation(domain text pk, status 'known_safe'|'known_suspicious'|'unknown',
  source text, note text)
- incidents(id text pk e.g. 'INC-0001', created_at, approved_at, reviewed_by text null,
  message text, urls jsonb, indicators jsonb, evidence jsonb, attack_sequence jsonb,
  guidance_refs text[], risk_score int, risk_band text, assessment text,
  next_steps jsonb, draft text, draft_edited bool, status text default 'Pending review')
- activity_log(id bigserial pk, investigation_id text, incident_id text null,
  created_at, kind 'tool_call'|'tool_result'|'error'|'approval'|'save',
  tool_name text null, payload jsonb)

API CONTRACT (define Pydantic models + mirrored TS types)
- POST /api/investigate -> either {type:"clarification", question}
  or {type:"assessment", investigation_id, urls, indicators[4 + extras], 
  evidence[], attack_sequence[], guidance[], risk{score,band,breakdown}, 
  assessment, next_steps[], draft, validation{passed, issues[]}, activity[]}
- POST /api/incidents body requires approved=true plus the full payload;
  returns {id, status} only after the DB insert succeeds.
- Error shape everywhere: {"error":{"code":"...","message":"..."}}

STUB QUALITY BAR
- Every Python file has type hints and a docstring; every TS file exports typed 
  placeholders. Routes return 501 with the error shape until implemented.
- Include one working smoke path: GET /api/health works; frontend pages render 
  their titles; `pytest` runs (test files can contain a single skipped test).
- README lists: install, run (backend + web), env vars, seeding Supabase,
  deploy to Render, and the free-tier caveats (Supabase pause, Render sleep).

After scaffolding, print the final tree and list every TODO stub so the team 
can assign them.
```

## Suggested team split

| Member | Owns |
|---|---|
| 1 | Rule-based tools: `inspect_indicators`, `analyze_url_structure`, `detect_social_engineering`, plus tests |
| 2 | Agent loop, Gemini adapter, prompts, `map_attack_sequence` |
| 3 | Supabase schema, seed data, repositories, `search_guidance`, `check_domain_reputation`, `create_incident`, activity log |
| 4 | `validate_evidence`, `assess_risk`, guidance draft, approval endpoint, backend tests |
| 5 | Frontend: all pages and components |

## Build order

You listed 11 items. Build the first six in your own order, then the guardrails and approval gate. The five-case test report and deployed demo matter more than any extra tool, so get the minimum flow working end to end on the live URL before adding more.
