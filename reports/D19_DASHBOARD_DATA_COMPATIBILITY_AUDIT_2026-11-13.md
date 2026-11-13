# D-19 — Dashboard Data Compatibility Audit

**Date:** 2026-11-13  
**Repository:** `/home/demon/shorts_studio`  
**Disposition:** PARTIAL PASS — local runtime data is queryable; canonical dashboard domain data is not yet available.  
**Inspection mode:** Read-only. No database rows, schemas, migrations, credentials, workers or API state were changed.

## 1. Executive result

The existing local PostgreSQL service is reachable through the project's private configuration and the existing authenticated FastAPI API is live on `127.0.0.1:8765`. The connected database is `nextdecode`, PostgreSQL 18.6. It contains six tables belonging exclusively to the local autonomy queue/runtime.

It does **not** contain the canonical WP1 domain model (Workspace, ContentItem, ContentVersion, ContentVariant, Relationship, Workflow, WorkflowTask, Artifact/ArtifactVersion, StudioProduction, or the corresponding canonical governance records). Therefore it is not safe to populate Projects, Content, Research, Studio, Reviews, Governance or Analytics with these local runtime records or fabricated data.

A useful first dashboard vertical slice can be connected today to local autonomy observability: queue health, local task records, local worker heartbeats, capabilities and task event history. That is what the initial React dashboard implements. It is explicitly not the canonical P0 control plane.

## 2. Evidence — live PostgreSQL

Connection was made using the existing external configuration at `~/.config/nextdecode/autonomy-db.env`; the DSN and password were not printed or copied into the repository.

- Database: `nextdecode`
- Database role: `nextdecode`
- Engine: PostgreSQL 18.6 (Alpine build)
- Runtime port: loopback `127.0.0.1:54329`
- Application API: `127.0.0.1:8765`
- Schema inspected: `public`
- User tables found: 6
- Schema migration/version table: none found

| Table | Rows | Ownership / interpretation |
|---|---:|---|
| `task_plans` | 3 | Local autonomy plans; not canonical WP2 Workflow |
| `tasks` | 12 | Local autonomy tasks; not canonical WP2 WorkflowTask/Job/JobAttempt |
| `task_dependencies` | 3 | Local DAG dependency edges |
| `task_events` | 36 | Local runtime task events; not canonical cross-domain event ledger |
| `plan_idempotency` | 0 | Local plan idempotency records |
| `worker_heartbeats` | 33 | Local process heartbeats; not canonical WP3 WorkerRegistry/Trust records |

The physical schema uses local runtime string IDs and JSON text payloads. It is not the UUIDv7 canonical domain schema described by the WP1 candidate.

## 3. Evidence — preserved SQLite database

`data/autonomy/tasks.sqlite3` was inspected using SQLite read-only mode.

| Table | Rows |
|---|---:|
| `task_plans` | 0 |
| `tasks` | 0 |
| `task_dependencies` | 0 |
| `task_events` | 0 |
| `plan_idempotency` | 0 |
| `worker_heartbeats` | 20 |

The legacy SQLite file is not the active queue source according to `app/autonomy/README.md`; it remains a preserved development/legacy source. It was not modified.

## 4. Existing API compatibility

The following existing authenticated read endpoints were successfully exercised through the local dashboard proxy (HTTP 200):

- `GET /autonomy/health`
- `GET /tasks?limit=200`
- `GET /tasks/{task_id}`
- `GET /capabilities`

The API's bearer key is stored outside the repository at `~/.config/nextdecode/api.env`. The dashboard development proxy loads that key in the Node/Vite server process and injects it server-side. The key is not included in browser source or browser storage.

## 5. Canonical compatibility findings

| Contract area | Existing local runtime | Dashboard compatibility |
|---|---|---|
| WP1 canonical entities | Not present in this DB | BLOCKED — no canonical project/content read model |
| WP2 workflow execution | Local autonomy queue only | PARTIAL — local queue visibility only; do not relabel as canonical WP2 |
| WP3 worker registry/trust | Local process heartbeats and runtime identity | BLOCKED for canonical agent trust/registration views |
| WP4 artifact registry | Local autonomy artifacts are separate | BLOCKED for canonical artifact lineage and immutable versions |
| WP5 approval/authorization | Local runtime does not implement canonical ApprovalRequest/ApprovalDecision | BLOCKED for review/approval/authorization dashboards |
| WP6 integration/acceptance | No canonical evidence projection found in this DB | BLOCKED for release acceptance dashboard |

This preserves the explicit boundary documented in `app/autonomy/README.md` and the WP1 schema candidate: local autonomy runtime IDs, tables and artifacts are not substitutes for canonical P0 entities/contracts.

## 6. D-19 disposition

**PASS:** Existing PostgreSQL autonomy runtime is queryable; authenticated API read endpoints return real data; existing task/worker/capability information can power a clearly labelled local operations view.

**GAP:** No canonical WP1 dashboard read projection, schema migration registry or canonical entity tables were found in the inspected database. The current DB cannot support the full NEXTDECODE Command Center data model.

**BLOCKER:** Do not create duplicate canonical tables or map local task/heartbeat records into WP2/WP3 entities to make the dashboard look complete. WP1 contract closure and WP2–WP6 ownership/API reconciliation must govern any canonical projection.

## 7. Next implementation gates

1. WP3-B: resolve the approved browser authentication/session boundary. The Vite proxy is development-only and loopback-only; it is not production authentication.
2. WP3-C: define query services over owner-approved canonical contracts; local autonomy reads remain a separate adapter.
3. WP3-D: publish versioned, read-only dashboard API projections with workspace scope, redaction, pagination and error semantics.
4. WP3-E: connect Projects, Content, Research, Studio, Reviews, Governance and Analytics only when their canonical read services exist.

## 8. Artifacts created in this increment

- `dashboard/` — React + TypeScript + Vite application connected to existing read-only local autonomy API routes.
- `reports/dashboard_data_compat_audit.py` — repeatable read-only SQLite and local listener inventory helper.
- `reports/inspect_local_postgres.py` — read-only PostgreSQL schema/count inspector (loads private DSN from the existing external config; does not print it).
- `reports/probe_dashboard_api.py` — read-only authenticated API endpoint probe (does not print the bearer key).

No production migration, database DDL, worker registration, task dispatch, approval, upload, publishing, deployment or Git operation was performed.
