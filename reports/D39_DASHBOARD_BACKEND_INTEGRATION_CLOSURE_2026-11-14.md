# D39 — Dashboard/backend integration closure
Date: 2026-11-14
Status: LOCAL DASHBOARD INTEGRATION VERIFIED · CANONICAL WP BRIDGE REMAINS BLOCKED

## Executive result
The existing NEXTDECODE Content OS dashboard now consumes the local autonomy runtime more completely. This increment adds a bounded global lifecycle feed, execution-heartbeat liveness diagnostics, correct server-side task-list limits, and advisory tool-catalog visibility. Existing pages now refresh their live records at defined intervals.

This is a local Content OS integration only. It does not implement or claim canonical WP2–WP6 integration.

## Backend changes
- `GET /tasks?limit=N`
  - Uses the store's existing bounded list API.
  - Enforces 1..500 and returns the applied limit.
  - Both SQLite and PostgreSQL stores already support bounded list retrieval.
- `GET /autonomy/events?after_event_id=N&limit=N`
  - Bearer-authenticated, read-only local task lifecycle feed.
  - Cursor zero returns the newest bounded event window in chronological order.
  - Nonzero cursor returns forward-only events after that event ID.
  - Returns a checkpoint value; this is not a canonical cross-service event bus.
- `GET /autonomy/stuck-tasks?stale_after_seconds=N&limit=N`
  - Bearer-authenticated, read-only running-task diagnostic based on execution heartbeat freshness.
  - Bounds threshold to 1..3600 seconds and page size to 1..500.
  - Does not recover tasks, renew leases or restart workers.
- Added `recent_event_feed()` to SQLite and PostgreSQL local autonomy stores. It returns the newest bounded window in chronological order and adds no schema change.

## Frontend integration
- Command Center:
  - Shows global lifecycle activity from the persisted local event feed.
  - Links each event to its task inspector.
  - Refreshes event feed every 5 seconds, tasks every 10 seconds, health every 15 seconds, capabilities every 30 seconds.
- Operations:
  - Shows stuck-task candidates and last execution heartbeat.
  - Keeps diagnostics read-only and clearly labels candidates as signals, not proof of hung workers.
- Task inspector:
  - Shows sanitized task input payload and output/evidence.
  - Preserves chronological event history, live refresh for active tasks, and explicit human-approval/publishing boundaries.
- Capability catalogue:
  - Connects the existing advisory tool-catalog endpoint and shows categories separately from registered task handlers.
  - Explicitly distinguishes metadata from installed/invocable tools and authorization.
- Existing Jobs, Dead Letters, Review Desk and Plans screens refresh their live API records at bounded intervals.

## Authentication and runtime verification
- Existing Vite proxy continues to inject the server-side Bearer key; no browser-side credential was added.
- Restarted the existing `nextdecode-autonomy-api.service` through its user systemd unit to load the new read-only routes. PostgreSQL and the worker service were not restarted.
- Authenticated live API probe results:
  - `/autonomy/health` — 200
  - `/tasks?limit=200` — 200; 23 task records returned
  - `/capabilities` — 200; 11 registered handlers
  - `/tool-catalog` — 200; 14 tool categories
  - `/autonomy/events?limit=12` — 200; 12 events
  - `/autonomy/stuck-tasks?stale_after_seconds=120&limit=100` — 200; 0 candidates
  - `/autonomy/dead-letters?limit=100` — 200; 6 records
  - `/review/pending` — 200; active package returned
  - `/jobs` — 200
- Unauthenticated request to the new event endpoint returned 401.
- Vite dev proxy requests to health, events and tasks all returned 200. This confirms proxy authentication injection and route forwarding against the running local API.

## Automated validation
- `tests/test_dashboard_api_observability.py`, `tests/test_api_auth.py`, `tests/test_api_lifecycle.py`: **20 passed**.
- Dashboard `npm run typecheck`: PASS.
- Dashboard `npm run build`: PASS; 1,745 modules transformed.
- `git diff --check`: PASS.

## Files changed in this increment
- `api/main.py`
- `app/autonomy/store.py`
- `app/autonomy/postgres_store.py`
- `dashboard/src/api.ts`
- `dashboard/src/pages/home.tsx`
- `dashboard/src/pages/operations.tsx`
- `dashboard/src/pages/task.tsx`
- `dashboard/src/pages/capabilities.tsx`
- `dashboard/src/pages/jobs.tsx`
- `dashboard/src/pages/dead-letters.tsx`
- `dashboard/src/pages/reviews.tsx`
- `dashboard/src/pages/plans.tsx`
- `tests/test_dashboard_api_observability.py`

## Runtime status
- `nextdecode-autonomy-api.service`: restarted successfully and active.
- `nextdecode-autonomy-worker.service`: left running; not restarted.
- Local dashboard Vite dev server: started at `http://127.0.0.1:5173/` for the current workspace session.
- No public network service or production deployment was created.

## Boundaries and remaining gaps
- The dashboard still shows local autonomy tasks/events, legacy in-memory jobs, local plans, local capability inventory, browser-local Studio drafts and the read-only review package. It does not relabel these as canonical WP2/WP3/WP4/WP5 records.
- Full LLM/tool-call spans, provider request/response traces, source-level research artifact browsing, and a canonical content graph are not exposed by the current backend contracts. This increment does not fabricate those records or add unsupported endpoints.
- Agent desktop readiness and connected agent sessions remain unverified through this API. Worker heartbeat ≠ agent identity/trust/assignment.
- D37-B/D37-C/D37-D contract and owner gates remain authoritative. Canonical Studio adapter, WP2–WP6 bridge, schema, migrations, approval mutations, provider activation, upload/publishing and deployment remain blocked pending the required owner/contract closure and separate authorization.

## Safety and repository preservation
- No database schema, DDL, migration or data mutation was introduced.
- No provider calls, media generation, upload, publishing or approval mutation was performed.
- No ECC repository changes.
- No agent dispatch.
- No Git commit, push, reset, clean or stash.
- Existing dirty and untracked project work was preserved.

## Disposition
**Local dashboard/backend integration increment: VERIFIED.**
**Canonical Content OS control-plane integration: NOT IMPLEMENTED — GOVERNANCE GATES OPEN.**

## D39 addendum — full advisory tool candidate detail
- Capability catalogue now loads each category's candidate records through the existing `/tool-catalog?capability=...` endpoint.
- Displays rank, deployment, license, cost model, status, strengths, limitations, replacement relationship and explicit approval requirement.
- Candidate records remain advisory only; the dashboard does not install, connect or invoke any candidate.
- Added responsive styling for category selection and candidate detail cards.
- Re-ran dashboard typecheck/build and the 20 focused backend/auth/lifecycle tests after this addition; all passed.
