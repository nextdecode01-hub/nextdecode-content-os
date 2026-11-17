# D40 — Local Production Execution Trace

**Date:** 2026-11-14  
**Status:** IMPLEMENTED — LOCAL READ-ONLY OBSERVABILITY  
**Scope:** Existing Shorts Studio RunTracker manifests only. No canonical WP2–WP6 bridge.

## 1. Objective

Expose actual persisted production-engine execution evidence in the existing Run Observatory. This increment does not synthesize missing pipeline activity and does not change generation, review, approval, publishing or recovery behavior.

## 2. Source of truth

- `outputs/runs/*/manifest.json` — local RunTracker manifests.
- `app/tracking/run_tracker.py` — existing run lifecycle, stage and artifact recording contract.
- `data/runs/index.jsonl` — append-only terminal-run index (not treated as the complete run source).

The API enumerates manifests because an `in_progress` run may not yet have an index row. Manifest reads are bounded by response limits and validated against the expected run directory. No manifest or artifact is modified.

## 3. Implemented

### API
- `GET /production-runs?limit=...` — authenticated, read-only local RunTracker manifest listing; limit bounded to 1–200.
- `GET /production-runs/{run_id}` — authenticated, read-only manifest detail.
- Exposes recorded stage timestamps/status, artifact metadata/digest/size/existence, sanitized failure metadata and promotion status/timestamps.
- Does not return absolute filesystem paths, promotion journal paths, exception messages, logs, credentials or arbitrary manifest fields.
- Validates run ID shape and resolved path containment.
- Explicitly reports `trace_completeness=manifest_only` and `canonical_workflow_linked=false`.

### Dashboard
- Existing Run Observatory now has a separate **Persisted production runs** panel alongside local autonomy task executions.
- Displays actual run status, quality, start time, recorded stage/artifact counts and manifest detail.
- Empty stage/artifact arrays are shown as missing persisted evidence, not guessed pipeline stages.
- Local production runs are clearly distinguished from autonomy tasks and canonical WP2 workflow runs.

### Tests
Added `tests/test_production_run_observability.py` for bounded listing, real manifest detail, path traversal rejection, and route authentication.

## 4. Evidence observed in current workspace

At implementation time, `outputs/runs/` contained two manifests for the same topic:

| Run | Status | Recorded stages | Artifacts |
|---|---|---:|---:|
| `20261107-035211-ai-agent-infrastructure-funding-surge-20` | failed | 0 | 0 |
| `20261107-034705-ai-agent-infrastructure-funding-surge-20` | in_progress | 0 | 0 |

The failed manifest records failure stage `strong_pipeline`, error type `RuntimeError`, category `unknown`. The other manifest remains `in_progress` with no stages, artifacts or terminal result. No recovery was attempted.

The observed manifests do not contain research source records, claim evidence, script versions, voice artifacts, visual decisions, render stages or QA evidence. This increment therefore does not claim those stages are visible.

## 5. Validation

- `venv/bin/python -m pytest tests/test_production_run_observability.py tests/test_dashboard_api_observability.py tests/test_api_auth.py -q` — **23 passed**.
- `npm --prefix dashboard run typecheck` — PASS.
- `npm --prefix dashboard run build` — PASS; 1745 modules transformed.
- `git diff --check` — PASS.

## 6. Governance and non-goals

- No schema, DDL, migration, ORM, canonical adapter or canonical event bus.
- No WP2/WP3/WP4/WP5/WP6 implementation or acceptance claim.
- No provider calls, paid services, production generation, rendering, upload, publishing, approval mutation or deployment.
- No automated recovery or mutation of stale/in-progress manifests.
- No Git commit, push, reset, clean or stash.
- Existing dirty and untracked user work was preserved.

## 7. Remaining engineering gap

A true research-to-QA debugger requires the production pipeline to persist attributable stage and artifact records for each stage. Existing RunTracker supports stage and artifact entries, but the two observed manifests have empty arrays. Source-level research lineage and claim evidence are not yet connected to these run manifests in the persisted records observed here.

Next safe work: map existing research/script/voice/visual/render/QA output files to the RunTracker lifecycle and identify which records can be correlated without changing the approved contracts. Any instrumentation or execution mutation should be separately scoped; canonical bridge work remains blocked by D37 gates.

## 8. Live local runtime verification

- Restarted the existing `nextdecode-autonomy-api.service` to load the new read-only routes; service reported active.
- Authenticated `GET /production-runs` returned HTTP 200, source `local_run_tracker`, 2 manifests.
- Authenticated `GET /production-runs/{run_id}` returned HTTP 200 for the failed run, with 0 stages, 0 artifacts and `manifest_only` completeness.
- Unauthenticated `GET /production-runs` returned HTTP 401.
- Existing dashboard route `/runs` returned HTTP 200.
- No production pipeline execution was started. The only runtime operation was restarting the existing local API service and read-only verification.
