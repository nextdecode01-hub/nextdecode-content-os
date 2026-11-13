# D-20 — Dashboard Increment 02

**Date:** 2026-11-13  
**Disposition:** PASS — additional read-only operational views implemented against existing API contracts.

## Delivered

1. **Global search:** `Ctrl+K` / `Cmd+K` opens a keyboard-accessible search overlay. It queries the existing task and capability read models, displays bounded results and navigates to the selected record. Enter opens the first result; Escape closes the overlay. It intentionally does not index task payloads or result bodies.
2. **Dead-letter queue:** Added a dedicated terminal-failure view using `GET /autonomy/dead-letters?limit=100`. It exposes task ID, capability, terminal state, attempts, error code and last update, with a link to the task evidence. It has no retry/requeue/delete controls.
3. **Workflow topology:** Added a local autonomy plan explorer. It derives plan IDs from existing plan-linked tasks and reads `GET /plans/{plan_id}`. It shows stored plan metadata, human approval/external action flags, ordered nodes, dependency references, task status, attempt count and task detail links.
4. **Navigation and layout:** Added Plan Topology and Dead Letters navigation; responsive plan explorer styling; existing dark NEXTDECODE visual system retained.

## Verification

- `npm run build`: PASS (TypeScript no-emit check and Vite production build).
- `GET /autonomy/dead-letters?limit=100` via authenticated Vite proxy: HTTP 200.
- `GET /plans/d7238b560ec44d2fa6cd905367153f57` via authenticated Vite proxy: HTTP 200.
- Chrome headless rendered the Plan Topology page with 3 persisted local plans and a two-node dependency chain.
- Earlier D-19 checks remain: health, task list, task detail and capabilities proxy HTTP 200; browser bundle secret scan PASS.

## Boundaries

These remain **local autonomy runtime** views, not canonical WP2 Workflow/Job views. The plan example visibly declares `human_approval_required=true` and `external_actions_allowed=false`; the dashboard does not interpret plan completion as approval or publishing authorization. No task state, plan state, database schema, credentials, worker state or publishing state was changed.

## Remaining blockers

- Production browser authentication/session and CSRF design (WP3-B) remains unimplemented; the local Vite proxy is development-only and loopback-only.
- Canonical WP1/WP2/WP3/WP4/WP5 read projections are not available in the inspected local autonomy database.
- Projects, Content, Studio, Reviews, Governance and Analytics remain intentionally unconnected, with explicit empty/pending states instead of fabricated records.
- No production deployment, Git commit or push was performed.
