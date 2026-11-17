# D47 — Package A Production Pipeline Observability Implementation Entry Proposal

**Date:** 2026-11-14  
**Status:** PREPARED FOR PRODUCT OWNER / REVIEWER DISPOSITION — NOT CLEARED FOR CODE OR TEST EXECUTION  
**Package:** ND-PKG-A-OBS-01  
**Scope:** Local Shorts Studio RunTracker stage lifecycle, finalized run-contained artifact evidence, authenticated manifest-backed API trace and dashboard presentation.  
**Authority:** M6-P / REG-131; M6-AH / REG-149; D44, D45, D46; H8 / REG-154.  
**Purpose:** Turn the existing observability contract into an exact, reviewable package proposal. This is a request for bounded implementation and separate test authorization, not an authorization itself.

## 1. Product outcome

When a local Shorts Studio production run executes, the system should persist its real stage lifecycle as it happens. If a stage fails or the process stops, the run manifest should preserve the last truthful state. The API and dashboard should display only recorded evidence, including legacy/incomplete distinctions. No percentage is inferred from stage count.

This package is local producer observability only. It is not canonical WP2 WorkflowRun/Job/JobAttempt/Lease, WP3 worker identity, WP1 persistence, WP4 artifact registry, WP5 approval/authorization, or a publishing workflow.

## 2. Repository baseline inspected

- Workspace: `/home/demon/shorts_studio`
- Branch: `main`
- Base HEAD: `419801d` — `feat: consolidate content OS runtime and governance baseline`
- Worktree: DIRTY before this proposal.
- Existing modifications include `api/main.py`, autonomy runtime/store/registry/tasks files and tests.
- Existing untracked work includes the dashboard, additional autonomy modules/tests, D21–D46 reports, and other files.
- No pre-existing work is to be overwritten, cleaned, reset, stashed, staged, committed or pushed.
- This baseline is an inspection snapshot, not a claim that the branch remains unchanged at a later execution time. Re-inspect immediately before any authorized implementation.

## 3. Exact proposed writable allowlist

The following is the smallest practical cross-layer allowlist identified from the current source layout. Paths are repository-relative. This list is proposed for explicit approval; it does not grant write access.

| # | Exact path | Intended responsibility | Proposed status |
|---:|---|---|---|
| 1 | `app/tracking/run_tracker.py` | Add explicit stage begin/finish/fail persistence while preserving manifest atomic-write, run containment, hash and existing terminal lifecycle behavior | PROPOSED WRITE |
| 2 | `app/script/pipeline.py` | Emit stage lifecycle notifications at actual existing execution boundaries; no pipeline redesign | PROPOSED WRITE |
| 3 | `pipelines/short.py` | Bind the observer to the active RunTracker; record only finalized artifacts already contained in the run directory | PROPOSED WRITE |
| 4 | `api/main.py` | Serialize bounded, sanitized manifest-backed trace while preserving bearer authentication and read-only routes | PROPOSED WRITE |
| 5 | `tests/test_run_tracker.py` | Extend existing temporary-root tracker tests for lifecycle, interruption, idempotency/invalid transitions and compatibility | PROPOSED WRITE |
| 6 | `tests/test_production_run_observability.py` | Extend existing synthetic-manifest API tests for malformed/legacy/interrupted traces, bounds and auth | PROPOSED WRITE |
| 7 | `dashboard/src/api.ts` | Extend existing ProductionRun/ProductionRunDetail response types only | PROPOSED WRITE |
| 8 | `dashboard/src/pages/runs.tsx` | Render actual granular lifecycle and interruption/legacy states in existing run detail surface | PROPOSED WRITE |
| 9 | `dashboard/src/pages/home.tsx` | Show concise active production stage only when API evidence supports it; preserve current Home layout and published-analytics not-connected state | PROPOSED WRITE |
| 10 | `reports/D48_PACKAGE_A_IMPLEMENTATION_AND_VERIFICATION_RECORD_2026-11-14.md` | Record implementation decisions, tests and limitations after authorization | PROPOSED NEW FILE |

**Not included:** `dashboard/src/types.ts` (does not exist in inspected tree); a new production-runs page (existing page is `runs.tsx`); CSS unless a demonstrated UI requirement cannot be met by existing styles; `app/visuals/*`, providers, database, autonomy, publishing, credentials, deployment, canonical contracts, Data Dictionary, DDL/ORM/migrations or historical run manifests.

Any additional file discovered to be necessary is out of scope until separately added to the allowlist and approved. No wildcard path permissions.

## 4. Contract and behavior baseline

- D44 establishes that detailed pipeline steps are currently held in memory and can be lost on failure; the wrapper records an aggregate stage only after success.
- D45 defines candidate local stage vocabulary: topic_selection, research, script, evidence, voice, captions, shot_planning, render, qa, metadata and promotion.
- D45 requires in_progress plus terminal ok/failed/skipped semantics, timestamps, safe failure categories, interruption handling and finalized run-contained artifacts.
- Existing RunTracker artifact registration uses run-directory containment and SHA-256. Reuse it; do not bypass or weaken it.
- Existing API endpoints are authenticated and read-only. Preserve bearer authentication, bounded output, sanitized errors/paths and legacy manifest compatibility.
- Existing dashboard already distinguishes persisted manifest evidence from canonical WP2 workflow execution. Keep `canonical_workflow_linked=false` unless a separately accepted integration establishes otherwise.
- Historical aggregate-only manifests remain aggregate-only. Do not backfill from detached logs.
- Stage count is not percentage complete. QA is not approval, rights clearance, publishability or publication.

**Baseline classification:** D45 remains a candidate local contract, not a frozen canonical contract. Product Owner acceptance of this exact local package boundary and architecture/security concurrence are still required before activation.

## 5. Proposed implementation behavior

1. Add a safe stage lifecycle API to the existing RunTracker. Beginning a stage writes an in-progress record with a timestamp; terminal completion/failure writes its finish timestamp and bounded safe category.
2. Preserve stage order and reject invalid transitions or duplicate active stage names according to the approved D45 semantics.
3. On process interruption, leave the in-progress record intact. API/UI label a historical dangling stage Interrupted; never imply it is still running.
4. Ensure failure handling does not replace the original pipeline exception with an observability-write failure. Record telemetry failure safely and preserve fail-closed run status.
5. Instrument only real boundaries in `app/script/pipeline.py`; stage names must map to actual operations. Do not invent a stage that did not execute.
6. Bind the observer in `pipelines/short.py` to the current run. Record only finalized artifacts under the run root through the existing integrity method.
7. API detail/list returns only bounded manifest-backed stage records. Malformed entries are safely omitted or classified as incomplete without crashing list/detail. Existing auth remains unchanged.
8. Dashboard shows recorded stage state, timestamps and safe failure category; missing data remains “Not recorded”. No weighted progress percentage.
9. Existing legacy/aggregate-only records remain readable and are not rewritten.
10. No external provider, production generation, upload, publication, analytics, approval or database side effects.

## 6. Proposed test authorization — separate decision required

No test is authorized or executed by this proposal.

### Proposed deterministic commands

Backend focused tests:
```bash
.venv/bin/python -m pytest tests/test_run_tracker.py tests/test_production_run_observability.py
```

Dashboard static validation:
```bash
cd dashboard && npm run typecheck && npm run build
```

The commands must be revalidated against the actual environment before approval. These are not a request to run the full test suite.

### Proposed test scenarios

- Successful run: ordered stages persisted with timestamps and terminal status.
- Failure at each stage boundary: only entered stage fails; later stages absent.
- Process interruption: active stage remains in_progress and is labelled interrupted by read-only API/UI.
- Tracker write failure: no false run success and no masking of the original pipeline error.
- Artifact integrity: run-contained finalized artifact recorded; outside path, symlink escape, duplicate name and missing file rejected.
- API auth: unauthenticated requests remain denied; authenticated requests return bounded trace.
- API malformed/legacy compatibility: malformed stage entry does not crash; aggregate-only and not-recorded states remain explicit.
- UI: no inferred stage, no inferred percentage, no approval/publication implication.
- No real production generation, provider calls, network egress, upload, publish, credentials or external side effects.

### Environment / fixture boundary

- Temporary directories only for tracker/API tests.
- Synthetic manifest and synthetic files only.
- No test writes to real `outputs/runs` or `data/runs`.
- No live API server or external provider.
- No production generation.
- No database/DDL/ORM/migration.
- ENV-01..14 applicability and no-egress proof must be explicitly dispositioned by the authorized security/QA owner before tests run; local-only intent is not a substitute for that disposition.

## 7. Rollback proposal

- Capture pre-change hashes and exact diff for every approved file.
- Keep the existing dirty/untracked baseline intact; do not restore unrelated files.
- Revert only the exact package-owned diff using the approved rollback procedure.
- No historical manifest rewrite or deletion.
- No schema/data migration to roll back.
- Preserve test logs and evidence outside production run roots.
- If a stage schema compatibility issue appears, stop and preserve both old and new evidence; do not silently rewrite old manifests.

## 8. Required assignments and approvals

| Required gate | Proposed value / current state |
|---|---|
| Product Owner / scope authority | User approval requested for exact package boundary and allowlist |
| Writer | ChatGPT implementation coordinator proposed; must be explicitly accepted as the bounded writer assignment under Q099 |
| Independent reviewer | NOT ASSIGNED — named reviewer and role required |
| Integration owner | NOT ASSIGNED — named owner required |
| QA/acceptance owner | NOT ASSIGNED — named owner required |
| Architecture concurrence | NOT RECEIVED for D46-B01..B03 |
| Security/artifact-integrity concurrence | NOT RECEIVED for D46-B04/B05/B08 |
| Product/UI/WP5 boundary concurrence | NOT RECEIVED for D46-B06/B07 |
| Exact writable path grant | PROPOSED ABOVE; NOT GRANTED |
| Implementation authorization | REQUESTED; NOT GRANTED UNTIL EXPLICIT APPROVAL |
| Test authorization | SEPARATE REQUEST; NOT GRANTED |
| ENV-01..14 disposition | NOT RECORDED for this package |
| Integration/merge permission | NOT GRANTED |

A generic “go ahead” to prepare this record is not interpreted as approval of the proposed path list, implementation scope, test commands or environment.

## 9. Approval record to complete

**Implementation decision:** PENDING  
**Approved exact writable paths:** PENDING  
**Approved exclusions:** PENDING  
**Writer assignment:** PENDING  
**Independent reviewer:** PENDING  
**Integration owner:** PENDING  
**Architecture concurrence:** PENDING  
**Security concurrence:** PENDING  
**Implementation authorization date/scope:** PENDING  
**Separate test authorization date/commands/fixtures:** PENDING  
**ENV-01..14 disposition:** PENDING  
**Rollback acceptance:** PENDING

## 10. Final disposition

Package A is now converted from a broad observability proposal into an exact nine-source-file allowlist proposal plus one evidence-report destination. The implementation/test scope, deterministic commands, fixtures, rollback and required reviewer/owner decisions are explicit.

**No code changed. No tests ran. No source contract, schema, manifest, production run or provider state changed. No agent was dispatched.**

The next action is to record explicit approval of the exact path list and bounded implementation scope, plus the missing reviewer/integration/architecture/security assignments. Implementation authorization and test authorization must be granted separately. Once those are satisfied, implement this package directly and update the D48 evidence record alongside the code; do not return to another generic planning cycle.
