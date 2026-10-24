-- AI Suspicious Message Investigation Agent - database schema
-- ---------------------------------------------------------------------------
-- Run this in the Supabase SQL editor (or `supabase db push`) before seeding.
--
-- SECURITY: Row Level Security is ENABLED on every table with NO public
-- policies. That means the anon key (which the frontend would use) can read and
-- write nothing. Only the backend's service_role key, which bypasses RLS, has
-- access. See README "Seeding Supabase".

-- ===========================================================================
-- guidance: internal, curated advice passages cited by ID (e.g. SEC-01).
-- ===========================================================================
create table if not exists guidance (
    id     text primary key,              -- e.g. 'SEC-01'
    title  text not null,
    body   text not null,
    tags   text[] not null default '{}'
);

-- ===========================================================================
-- trusted_domains: allow-list of domains we consider internal/known-good.
-- A trusted domain is context, NOT a verdict about a whole message.
-- ===========================================================================
create table if not exists trusted_domains (
    domain text primary key,              -- lowercase, no scheme, e.g. 'intranet.example'
    label  text not null
);

-- ===========================================================================
-- domain_reputation: internal reputation rows for domains / IP literals.
-- Populated by hand for the demo; never filled from live DNS or WHOIS.
-- ===========================================================================
create table if not exists domain_reputation (
    domain text primary key,              -- domain or IP literal, lowercase
    status text not null
        check (status in ('known_safe', 'known_suspicious', 'unknown')),
    source text not null default 'manual',
    note   text
);

-- ===========================================================================
-- incidents: a saved investigation, created ONLY after human approval.
-- ===========================================================================
create table if not exists incidents (
    id              text primary key,     -- e.g. 'INC-0001'
    created_at      timestamptz not null default now(),
    approved_at     timestamptz,
    reviewed_by     text,                 -- null until a named analyst is recorded
    message         text not null,
    urls            jsonb not null default '[]'::jsonb,
    indicators      jsonb not null default '[]'::jsonb,
    evidence        jsonb not null default '[]'::jsonb,
    attack_sequence jsonb not null default '[]'::jsonb,
    guidance_refs   text[] not null default '{}',
    risk_score      int  not null default 0 check (risk_score between 0 and 100),
    risk_band       text not null default 'Low / Inconclusive',
    assessment      text not null default '',
    next_steps      jsonb not null default '[]'::jsonb,
    draft           text not null default '',
    draft_edited    boolean not null default false,
    status          text not null default 'Pending review'
);

create index if not exists incidents_created_at_idx on incidents (created_at desc);

-- ===========================================================================
-- activity_log: append-only audit trail of every tool call, result, error,
-- approval, and save. Never updated or deleted.
-- ===========================================================================
create table if not exists activity_log (
    id               bigserial primary key,
    investigation_id text not null,
    incident_id      text references incidents (id) on delete set null,
    created_at       timestamptz not null default now(),
    kind             text not null
        check (kind in ('tool_call', 'tool_result', 'error', 'approval', 'save')),
    tool_name        text,
    payload          jsonb not null default '{}'::jsonb
);

create index if not exists activity_log_investigation_idx
    on activity_log (investigation_id, created_at);
create index if not exists activity_log_incident_idx
    on activity_log (incident_id, created_at);

-- ===========================================================================
-- Atomic INC-#### allocation for create_incident (hard rule 2: the only caller
-- is the approval-gated POST /api/incidents endpoint).
-- ===========================================================================
create sequence if not exists incident_id_seq start 1;

create or replace function next_incident_id()
returns text
language sql
as $$
    select 'INC-' || lpad(nextval('incident_id_seq')::text, 4, '0');
$$;

-- ===========================================================================
-- Lock everything down: RLS on, no policies. The service_role key bypasses RLS.
-- ===========================================================================
alter table guidance          enable row level security;
alter table trusted_domains   enable row level security;
alter table domain_reputation enable row level security;
alter table incidents         enable row level security;
alter table activity_log      enable row level security;

-- Intentionally no `create policy` statements: no public access, ever.
-- TODO: if a read-only analyst dashboard is added later, add a policy that
-- grants SELECT to an authenticated role only.
