# NEXTDECODE Brain — Central Production Intelligence Foundation

**Status:** Implemented foundation v0 (deterministic, read-only)  
**Date:** 2026-11-15  
**Scope:** Pipeline-owned central context and decision surface; Dashboard remains independently owned.

## Purpose

NEXTDECODE needs one central system that understands project identity, production standards, current run evidence and the safest next recommended action. This is not a chatbot or autonomous agent framework. Conversational interfaces and specialist agents are future extensions, not current prerequisites.

## Architecture boundary

The brain is a control/intelligence layer around the existing Shorts Studio specialist engine. It must not duplicate research, script, visual selection, rendering, publishing or Dashboard implementations.

- **Project context:** versioned, reviewed project identity, format, production standards and guardrails in config/brain/project_context.v1.json.
- **Observed production state:** bounded read-only extraction from existing run manifests. Manifests remain owned by RunTracker; the brain does not rewrite them.
- **Decision logic:** deterministic, evidence-backed next-action recommendations. No model is called and no recommendation executes itself.
- **API contract:** authenticated read-only endpoints /brain/context, /brain/overview, /brain/decision. Dashboard may consume these contracts without owning the brain.
- **Existing autonomy runtime:** remains a local specialist task queue/planner with local PostgreSQL/SQLite adapters. Its own README explicitly says it is not the accepted P0 shared cloud control plane or canonical WP2/WP3/WP5 workflow. The brain does not relabel it as such.

## Current decision rules

| Latest observed run state | Recommendation | Authority |
|---|---|---|
| No manifests | Inspect/start first run | Recommendation only |
| failed | Diagnose failed run, cite stage/error evidence | Recommendation only |
| in_progress | Verify process liveness before recovery | Recommendation only |
| ok | Human review of completed video | Recommendation only |
| Unknown state | Inspect run state | Recommendation only |

The service exposes only allow-listed manifest fields, skips malformed/symlinked run records, bounds manifest size and run count, and never returns arbitrary manifest content or environment secrets.

## Non-negotiable constraints

1. Deterministic policy/state checks remain authoritative; AI suggestions can never override governance.
2. No public auto-publishing. Existing publishing authorization boundary remains authoritative.
3. No automatic mutation/recovery of historical or in-progress runs based only on a manifest.
4. Rights, provenance, editorial approval and technical render success remain separate facts.
5. Dashboard is a client of stable API contracts; do not edit its implementation in this workstream.
6. Reuse existing stores and workflow systems. Do not create a competing source of truth.

## Deliberate limitations of v0

- No persistent brain decision journal yet.
- No merge of local autonomy task queue, RunTracker and Dashboard state into one canonical cross-domain state model.
- No canonical P0 WP1–WP6 shared control-plane implementation claimed.
- No LLM, RAG/vector database, agent, chatbot or autonomous workflow execution.
- No creative video-quality model; current recommendation rules only inspect run lifecycle evidence.

These limitations are explicit. Durable decision history and cross-domain state integration must be designed against accepted P0 entity/event/lifecycle contracts, not added as a parallel ad-hoc database.

## Future evolution (not implemented)

1. Add a durable decision/evidence journal using the canonical database/event contracts when WP1/WP2 integration boundaries are cleared.
2. Add a unified read model that reconciles run manifests, jobs, worker heartbeats, artifacts, review and governance states without conflating their lifecycles.
3. Add measurable quality evaluation using real video evidence and owner-approved acceptance criteria.
4. Add AI-assisted analysis as a bounded advisor that returns typed proposals with citations/evidence and confidence; deterministic policy validates every proposal.
5. Consider chat or specialist agents only when they materially improve an established workflow.

## Verification

- tests/test_brain.py: context loading, manifest allow-listing, failed/in-progress/completed recommendations, malformed/symlink handling, authenticated API and read-only method boundary.
- tests/test_autonomy_api.py: existing autonomy API regression.
- No provider calls, service restarts, dependency installation, production render, upload, publishing, commit or push in this increment.


## v1 — unified local operations read model (15 Nov 2026)

The Brain v1 increment adds a bounded operational observer for the existing local autonomy queue and worker heartbeat tables.

### New read model

- `GET /brain/operations` exposes a versioned operations snapshot for Dashboard consumers.
- `GET /brain/overview` now combines production-run observations and local autonomy operations.
- `GET /brain/decision` includes the evidence-backed recommendation and the operations snapshot.
- The operations view reports queue counts, expired running leases, bounded recent failed-task metadata, and bounded worker heartbeat status.
- Sensitive task payloads/results, worker hostnames/PIDs, database paths, credentials and raw exception messages are not returned.
- SQLite is opened with `mode=ro` and `PRAGMA query_only=ON`. The observer never initializes a missing database or performs recovery.
- If `DATABASE_URL` is configured, the PostgreSQL adapter is intentionally reported as unavailable until a separately qualified read-only adapter exists. The current PostgreSQL TaskStore constructor performs schema initialization and must not be called from an observer.

### Authority and contract boundary

This is **local autonomy runtime telemetry**, not canonical WP1/WP2/WP3 state. The existing queue schema is not silently promoted into the accepted P0 control plane. The P0 baseline accepts PostgreSQL as the shared system of record, while WP1–WP5 detailed contracts and implementation specifications remain candidate/open. Brain v1 therefore labels this source `non_canonical_operational_observation` and documents the limitation in every overview response.

The Brain does not infer canonical Job, JobAttempt, Workflow, WorkerIdentity, QA, Rights, Approval or Authorization entities from local runtime tables. It does not merge the local worker heartbeat into a trusted/authorized worker identity. Heartbeat freshness is only an operational signal.

### Decision priority

1. Latest failed production run → diagnose that run.
2. Expired local task lease → inspect lease evidence; no automatic recovery.
3. Stale local worker heartbeat → inspect worker availability; no worker termination or reassignment.
4. Failed local autonomy task → review sanitized task failure metadata.
5. Queued/running work → monitor or verify progress.
6. Otherwise, retain the existing production-run review/liveness recommendations.

All outputs remain recommendation-only. No action is dispatched.

### API contract for Dashboard

`GET /brain/operations` returns:

- `schema`: `nextdecode.brain.operations.v1`
- `brain_version`
- `authority`: `non_canonical_operational_observation`
- `operations`: availability, backend, queue counts, worker heartbeat summary, expired leases and sanitized recent failures

All Brain routes inherit the existing API bearer-key dependency at router registration. They are read-only GET routes; unsupported mutation methods return 405.

### v1 limits / next integration gate

- PostgreSQL read-only observation is not yet implemented.
- Canonical P0 entities/events are not yet integrated.
- Canonical state transitions, worker trust/capability verification, artifact metadata, QA/rights/approval and authorization remain separate domains and cannot be inferred from local runtime telemetry.
- The next shared-control-plane integration requires the owner-reviewed/frozen WP1–WP5 contracts and a non-mutating adapter against the actual canonical schema. No new database, schema or source of truth is introduced here.
