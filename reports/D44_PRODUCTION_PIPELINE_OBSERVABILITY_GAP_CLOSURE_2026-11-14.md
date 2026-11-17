# D44 — Production Pipeline Observability Gap Closure Assessment

**Date:** 2026-11-14  
**Status:** INVESTIGATION COMPLETE — IMPLEMENTATION BOUNDARY IDENTIFIED  
**Scope:** Read-only source and artifact lineage inspection. No production execution or pipeline mutation.

## 1. Executive finding

The dashboard is not missing a hidden analytics endpoint. The current producer path does not persist granular stage events into the RunTracker manifest.

The existing RunTracker already supports stage and artifact records, but the production orchestrator currently writes only:
- one aggregate `strong_pipeline` stage after the complete strong pipeline returns;
- one `metadata` artifact;
- one `video` artifact.

These records are written only after the strong pipeline succeeds and the metadata has been finalized. A failure inside the strong pipeline occurs before those records are written. Therefore a failed manifest can correctly show zero completed stages and zero artifacts even though console logs may contain partial progress.

## 2. Source-level trace

Inspected:
- `pipelines/short.py`
- `app/tracking/run_tracker.py`
- `app/script/pipeline.py`
- API production-run list/detail implementation in `api/main.py`

Observed producer sequence in `pipelines/short.py`:
1. `start_run(...)` creates the run manifest.
2. `run_strong_pipeline(...)` executes the research/script/voice/visual/render work.
3. Metadata is stamped with run identity and governance.
4. `record_artifact("metadata", ...)` records finalized metadata.
5. `record_artifact("video", ...)` records the rendered video.
6. `record_stage("strong_pipeline", ...)` records one aggregate stage.
7. Promotion validates and copies the recorded artifacts to legacy output slots.
8. `mark_ok()` finalizes the run.

On exceptions during the strong pipeline, the catch path calls `mark_failed(stage="strong_pipeline", ...)`. No stage-level progress events or intermediate artifacts are persisted before that failure boundary.

## 3. Evidence-to-stage mapping

| Pipeline activity | Existing evidence | Run manifest linkage |
|---|---|---|
| Research | Strong pipeline console output and returned metadata (when successful) | No dedicated research stage |
| Claims/evidence | Research result / evidence ledger fields in pipeline metadata | No dedicated persisted stage/artifact record |
| Script | Generated script fields in pipeline metadata | No dedicated script stage |
| Voice | Voice provider result and generated audio path during pipeline | No dedicated voice stage/artifact record |
| Visual planning | Shot plan / storyboard / visual decisions in pipeline metadata | No dedicated visual stage |
| Render | Render output and QA result in pipeline metadata/log | Only represented indirectly by final video artifact after success |
| QA | Strong pipeline QA result and render validation | No dedicated QA stage |
| Promotion | Promotion journal and manifest promotion field | Separately recorded; not a production-generation stage |

Important: the table describes available code/log evidence, not proof that each item was persisted for either November 7 manifest.

## 4. Observed run evidence

### Failed run
`20261107-035211-ai-agent-infrastructure-funding-surge-20`
- Manifest status: `failed`
- Failure stage: `strong_pipeline`
- Error type: `RuntimeError`
- Error category: `unknown`
- Stages: 0
- Artifacts: 0
- `failure.json` agrees with the manifest.

This is consistent with a failure before the success-only artifact/stage recording block. It is not evidence that no internal work happened; it is evidence that granular work was not persisted to the manifest.

### Interrupted run
`20261107-034705-ai-agent-infrastructure-funding-surge-20`
- Manifest status: `in_progress`
- Finished timestamp: null
- Stages: 0
- Artifacts: 0

No recovery or mutation was attempted.

### Separate execution logs
The repository also contains successful direct/benchmark logs under `outputs/strong_check/run.log` and `outputs/strong_check2/run.log`. They show useful activity such as:
- research verdict and claim count;
- script title and word count;
- voice provider and estimated duration;
- shot count and shot types;
- render duration and 1080x1920 output;
- final process exit status.

These logs are not stored inside either November 7 run directory and do not carry the corresponding RunTracker run IDs. They must not be joined to those manifests by topic or timestamp guesswork. The strong_check2 log also records visual-provider failures/rate limits followed by a completed render; this is useful diagnostic evidence for that log's own execution only.

## 5. What the dashboard can truthfully show now

- Run status, topic, quality, timestamps and sanitized failure category from manifests.
- The single aggregate stage and finalized metadata/video artifacts when a run reaches the existing recording block.
- Promotion status/timestamps where present.
- A clear distinction between manifest-backed records and any future separately sourced diagnostics.

It cannot truthfully show per-stage progress, per-stage duration, stage-specific artifact previews, current in-flight stage, or stage-specific failure history from the current manifest contract.

## 6. Safe implementation path after authorization

A future instrumentation increment should be designed around the existing RunTracker and producer flow, not by scraping unrelated output directories.

Proposed acceptance criteria:
1. Every stage event belongs to one immutable `run_id`.
2. Stage vocabulary is explicit and stable: research, evidence, script, voice, visuals, render, qa, promotion.
3. Stage records have start/end timestamps and terminal status; in-flight state is represented explicitly only if the accepted contract permits it.
4. Artifacts are recorded only after finalization, remain inside the run directory, and retain SHA-256/size verification.
5. Failures identify the last entered stage without storing raw exception messages or secrets.
6. The API exposes only bounded, sanitized manifest-backed evidence.
7. Dashboard labels distinguish `recorded`, `running`, `failed`, `not recorded`, and `not linked`; it never converts missing evidence into zero-percent or guessed progress.
8. Tests cover successful stage sequence, failure at every stage boundary, interrupted execution, artifact containment, redaction, API authentication and dashboard empty states.
9. Existing manifests remain immutable; no retroactive reconstruction from ambiguous logs.
10. No production run is required for the implementation test suite; use temporary test directories and deterministic fakes.

## 7. Governance boundary

This investigation is read-only. Adding granular instrumentation changes the production execution path and writes to the run manifest contract. It is not a dashboard-only change and must not be smuggled in as observability UI work.

D37 gates remain authoritative. This assessment does not authorize canonical Studio adapter/schema/API/migration/workflow/worker/artifact registry/approval/publishing changes, production generation, or recovery of existing runs.

## 8. Recommended next increment

Once the applicable owner contract/implementation gates are closed, implement producer-side stage instrumentation and tests first. Then extend the existing authenticated read-only API and Run Observatory/Home to consume those persisted records. Only after this sequence should the dashboard display a live stage timeline.

For now, keep Home honest: show aggregate run evidence and clearly state that detailed stage trace is not yet recorded for these runs.
