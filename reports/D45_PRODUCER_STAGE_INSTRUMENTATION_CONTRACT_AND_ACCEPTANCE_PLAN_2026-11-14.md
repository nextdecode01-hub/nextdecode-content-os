# D45 — Producer Stage Instrumentation Contract & Acceptance Plan

**Date:** 2026-11-14  
**Status:** CANDIDATE — IMPLEMENTATION AND TEST AUTHORITY NOT GRANTED  
**Depends on:** D44 Production Pipeline Observability Gap Closure Assessment; M6-P implementation entry gates  
**Purpose:** Prepare a bounded, source-grounded producer instrumentation package for owner/architecture/security review. This is not a canonical contract and does not authorize code or test changes.

## 1. Decision requested

Approve or reject a narrowly bounded producer-side observability increment for the existing local RunTracker path:
- instrument the current Strong Pipeline stages against the existing run_id;
- persist stage start and terminal outcomes incrementally;
- record only finalized, run-contained artifacts;
- expose those records through the existing authenticated read-only production-run API and dashboard.

This proposal does not introduce WP2 durable workflow execution, a canonical event bus, a worker registry, a new database model, an artifact registry, approval service or publishing integration.

## 2. Exact source-grounded current pipeline

The current app/script/pipeline.py run() performs:
1. Topic selection (select_topic).
2. Research (build_research).
3. Script generation (script_studio.write_script).
4. Claim ledger construction and write.
5. Voice synthesis/master conversion/export and duration probe.
6. Caption transcription/alignment and caption file creation.
7. Shot and shot-plan generation.
8. Visual asset/render assembly (render_video).
9. Render acceptance checks (qa_video).
10. Visual outcome summary derived from render results.
11. Final metadata assembly and return.

Important source findings:
- The steps list is assembled in memory and returned only if run() succeeds.
- pipelines/short.py records only one aggregate strong_pipeline stage after the call returns.
- RunTracker.record_stage() accepts a completed/failed stage with start and finish timestamps; it does not model an in-progress stage or stage identity/update.
- record_artifact() accepts only an existing file inside the run directory, resolves symlinks for containment, hashes it and rejects duplicate names.
- The API reads manifests only. It does not infer stages from console logs or detached output folders.

## 3. Proposed bounded stage vocabulary

| Stage ID | Meaning | Start boundary | Success boundary |
|---|---|---|---|
| topic_selection | Explicit topic validation or candidate discovery/scoring | Before select_topic | Topic accepted |
| research | Source research and research verdict | Before build_research | Research bundle accepted |
| script | Research-grounded script generation | Before write_script | Script returned |
| evidence | Claim ledger build, warnings and persisted ledger | Before build_ledger | Ledger written |
| voice | TTS synthesis, master conversion/export and duration probe | Before synthesis | Required voice asset and duration validated |
| captions | ASR/transcription, alignment and caption files | Before caption build | Caption outputs written |
| shot_planning | Shot list and shot plan creation | Before shot planning | Shot plan written |
| render | Visual asset/render assembly and final video output | Before render_video | Render output returned and required captions confirmed |
| qa | Strict rendered-video QA | Before qa_video | Existing QA gate accepts result |
| metadata | Final metadata assembly/write in orchestrator | Before metadata write | Metadata persisted with run identity/governance |
| promotion | Existing promotion journal / slot promotion | Existing promotion boundary | Existing promotion journal completed |

The current visuals summary is post-render and derived from render results, not an independent provider-execution boundary. Do not invent a separate running visuals stage unless source code is refactored to provide a real start/end boundary. The dashboard may display visual-provider outcomes as render metadata.

The aggregate strong_pipeline stage may remain for backwards compatibility during transition, but must not be double-counted as a granular production stage.

## 4. Proposed stage record lifecycle (candidate only)

A live timeline requires an explicit in-progress record. Proposed logical shape:

| Field | Required | Rule |
|---|---|---|
| stage_id | Yes | Stable vocabulary from §3 |
| started_at | Yes | UTC ISO-8601 at entry |
| finished_at | Nullable | Null only while in_progress |
| status | Yes | in_progress, ok, failed, skipped |
| attempt | Yes | Positive integer; initially 1 |
| failure_category | Nullable | Sanitized bounded category; no raw exception |
| metrics | Optional | Small allowlisted facts only; no secrets/unbounded payloads |

Lifecycle invariants:
1. Stage entry is persisted before the stage body begins.
2. Exactly one terminal update closes that stage record.
3. ok and failed require finished_at; in_progress requires null finished_at.
4. A run cannot be marked successful while a stage remains in_progress.
5. A failure closes the active stage as failed before the run is marked failed.
6. If interrupted, the last stage may remain in_progress; once the run is no longer active, API/UI labels it interrupted/unknown, not failed or successful.
7. Stage order follows actual execution; unentered stages are absent.
8. Retries must never overwrite prior stage history. This proposal does not add retry orchestration.

This requires an additive RunTracker lifecycle API or equivalent internal methods. Existing record_stage() alone cannot provide a live in-progress timeline. Exact method names and manifest schema version require review and approval.

## 5. Artifact recording proposal

Candidate finalized files, only when present inside the run directory:
- research/claim_ledger.json — evidence
- voice.mp3 and optional lossless voice master/export — voice
- captions.words.json and subtitles.ass — captions
- shot_plan.json — shot_planning
- output_short.mp4 — render
- metadata.json — metadata

Rules:
- Register after final/atomic write, never when a file is merely expected.
- Reuse existing path containment, symlink resolution and SHA-256/size recording.
- Do not register temp files, caches, external URLs, or files outside the run root.
- Artifact names are unique under the current tracker. Use stable distinct names for voice derivatives.
- Do not register raw logs, credentials, provider response bodies or sensitive source payloads by default.
- Missing optional derivatives are omitted.
- Never retroactively attach existing files to historical runs without proven lineage.

## 6. Failure and interruption behavior

- Mark the active stage failed with a safe category before propagating the exception to the existing fail-closed orchestrator.
- Preserve existing mark_failed() and sanitized failure.json semantics.
- Never store raw exception messages, prompts, provider response bodies, signed URLs or credentials in stage metrics.
- If stage-close persistence fails, preserve the original pipeline failure as primary; do not falsely mark the run successful.
- KeyboardInterrupt/operator abort remains distinct. Current behavior leaves a run in_progress; this proposal does not silently change that policy.
- A process crash may leave an in-progress stage. No automatic recovery/re-execution is proposed.

## 7. Read-only API and dashboard consumer requirements

Existing authenticated endpoints:
- GET /production-runs
- GET /production-runs/{run_id}

Candidate API extension:
- Return ordered stage records and bounded metrics from the manifest.
- Include trace completeness: granular, aggregate_only, interrupted_stage, or not_recorded.
- Keep canonical_workflow_linked=false unless a separately accepted integration establishes otherwise.
- Continue redacting absolute paths and raw errors.
- Bound stage count, metric keys, string lengths and artifact list size.
- Malformed stage entries must not crash the listing endpoint.
- Preserve API-key authentication and read-only semantics.

Dashboard behavior:
- in_progress: show current stage only while run itself is in progress.
- ok: show completed stage.
- failed: show failed stage and safe category.
- Missing stage: show Not recorded, not guessed progress.
- Historical run with dangling in_progress stage: show Interrupted / last recorded stage, not Running.
- Legacy aggregate-only runs remain visually distinct.
- Do not translate stage count into percent complete; stages have unequal duration and no calibrated weights.
- Render/QA completion must not imply approval or publishability.

## 8. Acceptance test plan (proposed IDs; not Artifact 07 IDs)

| ID | Scenario | Expected evidence |
|---|---|---|
| OBS-STG-01 | Full success with deterministic fakes | Ordered stages terminal ok; run success |
| OBS-STG-02 | Topic selection failure | Only entered stage failed; later stages absent |
| OBS-STG-03 | Research failure | Topic ok, research failed; later stages absent |
| OBS-STG-04 | Script failure | Earlier stages ok, script failed |
| OBS-STG-05 | Evidence write failure | Evidence failed; ledger artifact only if finalized and recorded |
| OBS-STG-06 | Voice failure | Voice failed; captions/render absent |
| OBS-STG-07 | Captions failure | Captions failed; shot/render absent |
| OBS-STG-08 | Shot planning failure | Shot planning failed; render absent |
| OBS-STG-09 | Render failure | Render failed; QA absent |
| OBS-STG-10 | QA rejection | Render ok, QA failed; run not successful |
| OBS-STG-11 | Metadata write failure | Metadata failed; no final success |
| OBS-STG-12 | Promotion failure | Promotion failed; existing promotion semantics preserved |
| OBS-STG-13 | Process interruption | In-progress stage preserved; API labels interrupted if run inactive |
| OBS-STG-14 | Tracker persistence failure | No false success; original failure preserved |
| OBS-ART-01 | Artifact inside run root | SHA-256/size/path recorded |
| OBS-ART-02 | Missing artifact | Not registered |
| OBS-ART-03 | Artifact outside run root | Rejected |
| OBS-ART-04 | Symlink escaping run root | Rejected |
| OBS-ART-05 | Duplicate artifact name | Rejected without replacement |
| OBS-API-01 | Authenticated list/detail | Bounded sanitized trace |
| OBS-API-02 | Unauthenticated list/detail | 401; no disclosure |
| OBS-API-03 | Malformed stage entry | Safe bounded response |
| OBS-API-04 | Legacy aggregate-only manifest | Backward compatibility; aggregate_only |
| OBS-API-05 | Historical manifest with no stages | not_recorded; no inferred history |
| OBS-UI-01 | Granular active run | Timeline shows recorded stage/status |
| OBS-UI-02 | Failed run | Failed stage/category; no fabricated percentage |
| OBS-UI-03 | Interrupted run | Last active stage labelled interrupted |
| OBS-UI-04 | Legacy run | Aggregate-only state |
| OBS-UI-05 | Missing stage | Not recorded |
| OBS-GOV-01 | Strong pipeline QA success | UI does not imply approval/publication |
| OBS-GOV-02 | Direct pipeline entry | Remains draft-only; not joined to orchestrated run |

Tests should use temporary run roots, deterministic fakes and synthetic files. No provider calls, real production generation, database mutation, upload, approval or publishing is needed.

## 9. Bounded implementation file candidates (allowlist proposal only)

Potential source files requiring a later explicit allowlist:
- app/tracking/run_tracker.py — stage lifecycle persistence.
- app/script/pipeline.py — optional stage observer/callback at real boundaries.
- pipelines/short.py — bind observer to active RunTracker and register finalized artifacts.
- api/main.py — bounded serialization of stage records.
- tests/test_run_tracker.py and focused new tests — tracker invariants.
- tests/test_production_run_observability.py — API compatibility/auth/legacy behavior.
- dashboard/src/types.ts, dashboard/src/api.ts, dashboard/src/pages/production-runs.tsx — verify exact current paths before any authorization.
- reports/ — implementation and verification evidence after authorization.

This is not an approved write allowlist. Exact branch/base state, file ownership, reviewer, integration owner, accepted contract versions, commands, rollback and separate test authorization are required before edits or tests.

## 10. Compatibility and migration

- Existing manifests remain readable without migration.
- No backfill from logs or detached output folders.
- No rewrite of historical manifests.
- New schema versioning must be additive and explicitly approved.
- API reports legacy trace completeness; it does not normalize old data into guessed granular stages.
- Do not change run_id format, directory naming, index semantics, promotion journal, upload authorization or publishability policy.

## 11. Non-goals

No canonical WP2 WorkflowRun/Job/JobAttempt implementation; database/DDL/ORM/migrations; event bus; worker changes; scheduler/retries/cancellation/recovery; provider health telemetry; analytics ingestion; approval/publishing changes; historical log scraping; broad dashboard redesign.

## 12. Gate and authorization checklist

- [ ] Confirm this is local RunTracker observability, not canonical WP2 workflow execution.
- [ ] Obtain architecture/security concurrence for manifest mutation and telemetry.
- [ ] Resolve conflicts with accepted API/Event, artifact and lifecycle contracts.
- [ ] Record exact branch, base commit and dirty state.
- [ ] Name writer, reviewer and integration owner.
- [ ] Approve exact writable file paths.
- [ ] Approve implementation scope separately from tests.
- [ ] Approve deterministic fixtures, commands and rollback.
- [ ] Confirm no provider egress, production generation or external side effects.
- [ ] Preserve D37/M6-P stop conditions and all existing dirty work.

**Current disposition:** READY FOR REVIEW AS A CANDIDATE ONLY. Implementation and test execution remain NOT CLEARED.
