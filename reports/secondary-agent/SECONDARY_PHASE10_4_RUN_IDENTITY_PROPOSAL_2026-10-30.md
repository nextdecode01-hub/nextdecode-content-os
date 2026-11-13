# Shorts Studio — Phase 10.4 Architecture Research Proposal

**Run Identity, Artifact Isolation & Recovery**

**Role:** Independent architecture researcher (secondary agent, not the implementation agent)
**Date:** 2026-10-30 · **Mode:** STRICTLY READ-ONLY. No code changes, no git modifications, no Phase 9 audio work, no Phase 10.1.1 interference, no Strict Fail-Closed implementation changes.
**Basis:** Verified against the current working tree (file:line references included). Recommendations are clearly separated from verified facts.

**Constraints honored:** incremental only (not a rewrite); no concurrency support assumed unless evidence justifies it; preserve all existing outputs; keep existing `data/metadata.json` / `outputs/output_short.mp4` single-slot contract intact *alongside* (not instead of) the new run-level layout.

---

## 1. Executive summary

Shorts Studio generates one short per run, but every artifact is written to a **fixed-name, single-slot** location (`data/metadata.json`, `outputs/output_short.mp4`, `outputs/voice.mp3`, `outputs/shots/shot_000.mp4`…). There is **no run identity**, **no manifest**, and **no failure-run bookkeeping**. A repeated or concurrent run overwrites the previous run's artifacts; a halfway-failed run leaves partial files with no marker; and a previous successful run can only be preserved by the external `video_archive.py` copy (which runs only after success).

This proposal adds a lightweight **run-level layer** on top of the existing single-slot contract:

- A `run_id` (timestamp + short slug) assigned at pipeline start.
- Per-run directory `outputs/runs/<run_id>/` holding that run's manifest, metadata, voice, subtitles, shots, and render output.
- A `manifest.json` per run mapping every artifact to its SHA-256, stage, and status (ok / failed / partial).
- The legacy fixed slots (`data/metadata.json`, `outputs/output_short.mp4`) continue to point at the *latest successful* run so all existing callers (review_bundle, approve_review, API, n8n) keep working unchanged.
- A `data/runs/index.jsonl` append-only log of completed/failed runs for recovery and listing.
- On failure, a `failure.json` is written before re-raising; partial artifacts are tagged, not mistaken for success.

All existing files are preserved; nothing is deleted or moved. The change is additive.

---

## 2. Current architecture map (verified facts)

### 2.1 Fixed artifact slots (single-slot contract)

| Artifact | Current path | Owner (file:line) | Notes |
|---|---|---|---|
| Main metadata | `data/metadata.json` | `review_bundle.py:13` (METADATA); `pipelines/short.py:318` | Overwritten each run (`pipelines/short.py:364-365` legacy path; `run_strong_pipeline:222` strong path) |
| Main video | `outputs/output_short.mp4` | `review_bundle.py:14` (VIDEO); `pipelines/short.py:317` | Overwritten each run |
| Voice | `outputs/voice.mp3` | `pipelines/short.py:314`; `app/script/pipeline.py:323` | — |
| Subtitles | `outputs/subtitles.ass` | `pipelines/short.py:315`; `app/script/pipeline.py:329` | — |
| Background (legacy) | `outputs/background.mp4` | `pipelines/short.py:315` | — |
| Shots | `outputs/shots/shot_NNN.mp4` | `app/render/shots.py:60` | Regenerated unconditionally each run |
| Shot validity | size > 1000 bytes | `app/render/shots.py:47-48` | No structural check |
| Review pending | `data/review_pending.json` | `approve_review.py:19` | Single pending slot |
| Review approved | `data/review_approved.json` | `approve_review.py:61` | Single approved slot |
| Review queue | `data/review_queue/YYYYMMDD-HHMMSS-slug.json` | `review_bundle.py:30-31,62-63` | Timestamped packages — the only run-ish identification today |

### 2.2 How a run is identified today

**There is no formal run ID.** Identification is implicit:

- `review_bundle.py:24-31` derives a package filename from `metadata.created_at` timestamp + title slug.
- `approve_review.py:22-26` reads `review_pending.json` to find "the current" package, then verifies `video_sha256` / `metadata_sha256` against `data/metadata.json` and `outputs/output_short.mp4` (lines 27-34) — this catches slot overwrite at approval time but only *then*.
- Ad-hoc evidence of run-scattering: `data/metadata_chain_run*.json`, `data/metadata_phase5_benchmark*.json`, `data/metadata_strong.json`, `data/metadata_dry_run.json`, `data/metadata_phase7_benchmark*.json` — many differently-named metadata files already exist, showing developers have been inventing run-level names informally.

### 2.3 Stage associations today

- Research → claim ledger at `<work_dir>/research/claim_ledger.json` (`app/script/pipeline.py:297`), `work_dir` defaults to `ROOT/outputs` (`:262`).
- Script/voice/captions/shots/render all flow through `work_dir` fixed slots (`pipeline.py:323-348`).
- Storyboard `json_path` / `contact_sheet` recorded in metadata (`pipeline.py:388-390`).
- `review_bundle.py` binds `metadata.json` ↔ `output_short.mp4` via dual SHA-256 in the package (lines 36-37).
- `archive_video` (`video_archive.py:22-44`) copies video+metadata to a dated archive dir **only after a successful run** (`pipelines/short.py:345, 386`).

### 2.4 Concurrency safeguards today

- `run_scheduled_generation.sh:12-16`: `flock` on `.scheduled_generation.lock` — serializes scheduled invocations only.
- `n8n_runner.py:23`: `EXECUTION_LOCK` serializes the runner HTTP handler.
- `api/main.py:18`: `MAX_JOBS = 50` — the API accepts up to 50 concurrent jobs, all invoking `pipelines/short.py` writing the same fixed slots (`api/main.py:109-119`). **No per-run isolation.**

### 2.5 Halfway-failure behavior today

- Strong pipeline (`pipeline.run`, `:252-490`) writes `metadata.json` only at the very end (`run_strong_pipeline:222`). A failure mid-run leaves: partial `voice.mp3`, partial `shots/shot_NNN.mp4`, possibly partial `output_short.mp4`, and **no failure marker** and **no updated metadata**.
- Legacy path (`pipelines/short.py:362-398`) overwrites `data/metadata.json` at line 364-365 before later stages may fail — so a failed legacy run can leave a *stale/wrong* metadata file masquerading as the latest output.
- `render_shot` raises if `size <= 1000` (`assembly.py:205-206`); otherwise partial shots remain on disk.

### 2.6 Preservation / recovery today

- Successful runs only: `video_archive.py` copies to `outputs/archive/<media_type>/<YYYY>/<MM>/` or `D:/ShortsStudioVideos/...` with timestamp+slug filename (`:36-44`).
- No `failure.json`, no run index, no manifest, no way to list or recover a specific previous run except by hunting through `data/review_queue/` or ad-hoc `metadata_*.json` files.

---

## 3. Evidence-backed problem list

| # | Problem | Evidence (file:line) | Severity |
|---|---|---|---|
| P1 | No run identity — runs cannot be distinguished or referenced | No `run_id`/`manifest` anywhere (grep: 1 hit, unrelated comment in `desk.py:781`); fixed slots only | High |
| P2 | Fixed slots overwritten by repeated runs | `pipelines/short.py:318` metadata_file; `:364-365` legacy overwrite; `:222` strong write | High |
| P3 | Concurrent runs collide (API allows 50 jobs) | `api/main.py:18,109-119` — all jobs write same slots; no per-run lock | High (if API concurrency used) |
| P4 | No failure-run bookkeeping; halfway failures invisible | No `failure.json`; metadata written only at end (`run_strong_pipeline:222`); no failure marker | High |
| P5 | Partial outputs can be mistaken for success | `_valid_output` size-only (`shots.py:47-48`); `render_shot` size check (`assembly.py:205-206`); no manifest status | Medium |
| P6 | Review package references current slots, which may be overwritten before approval | `review_bundle.py:34-37` hashes current files; `approve_review.py:27-34` verifies at approval (catches, but late) | Medium |
| P7 | Recovery depends on external archive copy after success only | `video_archive.py:43-44` called only after render success (`pipelines/short.py:345, 386`) | Medium |
| P8 | Ad-hoc run-scattering already happening (metadata_strong, metadata_chain_run, phase benchmarks) | `data/` listing — many differently-named metadata files | Low (symptom of P1) |

Concurrency evidence: the scheduler uses `flock`, but the API does not. Since no evidence shows concurrent generation actually occurring in production today, **this proposal does not add concurrency primitives**; it adds per-run isolation so concurrency *could* be added later safely (P3 noted as a future consideration, not a requirement).

---

## 4. Proposed run identity & manifest design

### 4.1 Run ID format

```
<UTC timestamp YYYYMMDD-HHMMSS>-<slug of topic or "manual">
```

Example: `20261030-143022-ai-rmf-explained`

- Deterministic from topic+time, filesystem-safe, sortable.
- Collisions unlikely (sub-second not needed; if same topic same second, append `-2`, `-3`).
- No UUID (keeps IDs human-readable and traceable in logs/review_queue filenames).

### 4.2 Per-run directory

```
outputs/runs/<run_id>/
    manifest.json        # run-level manifest (see below)
    metadata.json        # this run's full pipeline metadata (copy of data/metadata.json)
    voice.mp3            # this run's voice
    subtitles.ass        # this run's captions
    output_short.mp4     # this run's render
    shots/
        shot_000.mp4 ... # this run's shots
    failure.json         # written ONLY if the run failed (before re-raise / before fallback)
```

### 4.3 Manifest schema (manifest.json)

```json
{
  "run_id": "20261030-143022-ai-rmf-explained",
  "status": "failed",                 // "in_progress" | "ok" | "failed"
  "started_at": "2026-10-30T14:30:22+05:30",
  "finished_at": null,
  "topic": "AI RMF Explained",
  "quality": "strong",
  "artifacts": {
    "metadata": {"path": "metadata.json", "sha256": "...", "bytes": 12345, "stage": "metadata", "status": "ok"},
    "video":    {"path": "output_short.mp4", "sha256": "...", "bytes": ..., "stage": "render", "status": "ok"},
    "voice":    {"path": "voice.mp3", "sha256": "...", "stage": "voice", "status": "ok"},
    "subtitles":{"path": "subtitles.ass", "sha256": "...", "stage": "captions", "status": "ok"},
    "shots":    [{"path": "shots/shot_000.mp4", "sha256": "...", "stage": "shots", "status": "ok"}, ...]
  },
  "stages": [
    {"name": "topic", "status": "ok", "started_at": "...", "finished_at": "..."},
    {"name": "research", "status": "ok", ...},
    {"name": "script", "status": "ok", ...},
    {"name": "voice", "status": "failed", "error": "VoiceGenerationError", "error_category": "voice", "started_at": "...", "finished_at": "..."}
  ],
  "failure": {"stage": "voice", "error": "VoiceGenerationError", "error_category": "voice", "written_at": "..."},
  "legacy_slots": {"metadata": "data/metadata.json", "video": "outputs/output_short.mp4"}
}
```

- `status` transitions: `in_progress` (at start) → `ok` (at end) or `failed` (on exception, before re-raise).
- SHA-256 computed after each artifact is finalized (reuse `approval_integrity.sha256_file`).
- Error category enum (not free text) — ties into Phase 10.3 observability recommendation: `{topic, research, evidence, script, voice, render, qa, io, unknown}`.
- No credentials/secrets in manifest (errors store type/category only, not exception text with tokens).

### 4.4 Legacy-slot contract (preserved)

- `data/metadata.json` and `outputs/output_short.mp4` continue to exist and point at the **latest successful run** (copied/symlinked from the run dir on success).
- All existing callers (`review_bundle.py`, `approve_review.py`, `api/main.py`, `n8n_runner.py`, `run_pipeline.sh`) require **zero changes** to keep working.
- On a failed run, legacy slots are **not** overwritten (preserves P1 "preserve existing valid outputs").

### 4.5 Run index

```
data/runs/index.jsonl
```

Append-only JSONL, one line per run (completed or failed):
`{"run_id":"...","status":"failed","stage":"voice","started_at":"...","finished_at":"...","topic":"..."}`

- Enables `ls`/listing of past runs, recovery selection, and "re-run this run_id" tooling later.
- Read-only for humans; no auto-trim (trim = destructive; left to a future manual housekeeping tool).

---

## 5. Suggested directory structure (additive)

```
shorts_studio/
├── data/
│   ├── metadata.json                 # UNCHANGED: latest successful run's metadata (legacy slot)
│   ├── review_pending.json           # UNCHANGED
│   ├── review_approved.json          # UNCHANGED
│   ├── review_queue/                 # UNCHANGED: dated packages
│   └── runs/
│       └── index.jsonl               # NEW: append-only run log
├── outputs/
│   ├── output_short.mp4              # UNCHANGED: latest successful run's video (legacy slot)
│   ├── voice.mp3                     # UNCHANGED (legacy slot)
│   ├── subtitles.ass                 # UNCHANGED (legacy slot)
│   ├── background.mp4                # UNCHANGED (legacy slot)
│   ├── shots/                        # UNCHANGED: latest run's shots (legacy slot)
│   └── runs/
│       └── <run_id>/
│           ├── manifest.json
│           ├── metadata.json
│           ├── voice.mp3
│           ├── subtitles.ass
│           ├── output_short.mp4
│           ├── shots/  (shot_NNN.mp4)
│           └── failure.json          # only on failure
└── outputs/archive/                  # UNCHANGED: post-success archive via video_archive.py
```

Nothing in the existing tree is deleted, renamed, or moved. `outputs/runs/` and `data/runs/` are new directories only.

---

## 6. Failure & recovery lifecycle

### 6.1 Successful run
1. Pipeline start: assign `run_id`, create `outputs/runs/<run_id>/`, write `manifest.json` with `status: "in_progress"`.
2. Each stage: on completion, write artifact into run dir, compute SHA-256, update manifest `artifacts[].status = "ok"` and `stages[]`.
3. On success: set manifest `status = "ok"`, `finished_at`. Copy `metadata.json` → `data/metadata.json` and `output_short.mp4` → `outputs/output_short.mp4` (legacy slots refreshed atomically: write temp + rename where supported). Append line to `data/runs/index.jsonl`. Continue to `review_bundle.py` / human approval as today.

### 6.2 Failed run (halfway)
1. Exception caught at pipeline top-level (or stage boundary): before re-raising / before any fallback, write `outputs/runs/<run_id>/failure.json` with stage, error category, error type (no secret text), partial artifact list.
2. Set manifest `status = "failed"`, record `stages[]` up to failure, `finished_at`.
3. Append failure line to `data/runs/index.jsonl`.
4. **Do not** touch `data/metadata.json` or `outputs/output_short.mp4` — the last successful run remains the legacy-slot target.
5. Propagate failure (exit non-zero / job status "failed") — no legacy fallback, no success JSON.

### 6.3 Recovery
- Operator lists runs via `data/runs/index.jsonl` (or `outputs/runs/*` dirs).
- To re-promote a past successful run into the legacy slots: copy its `metadata.json` and `output_short.mp4` back to `data/metadata.json` and `outputs/output_short.mp4`, then re-run `review_bundle.py`. Manual/operator action only (no auto-recover, to avoid silent state changes).
- To inspect a failed run: read `failure.json` + manifest `stages[]` — tells exactly which stage failed and which artifacts are partial.

### 6.4 How review packages reference a specific run safely
- `review_bundle.py` continues to package from the legacy slots, but the package can additionally record `run_id` and `run_manifest_path` (pointing into `outputs/runs/<run_id>/manifest.json`).
- `approve_review.py`'s existing hash check (`approve_review.py:27-34`) already guarantees the approved package matches the *current* slot files. With run identity, approval can also record which run_id was approved, making the approval-to-run link auditable.
- Because each run's artifacts live in their own dir with manifest hashes, a review package can never accidentally reference another run's partial output.

---

## 7. Migration strategy (preserves existing outputs)

1. **Add only.** Create `outputs/runs/` and `data/runs/` directories. No existing file touched.
2. **Instrument pipeline.** In `pipelines/short.py` `main()` and/or `app/script/pipeline.py` `run()`:
   - Generate `run_id` at start; create run dir; write in-progress manifest.
   - Wrap stages so each artifact write is followed by manifest SHA-256 update.
   - On success: refresh legacy slots from run dir; append to index.jsonl.
   - On failure: write failure.json before re-raise; do not touch legacy slots.
3. **Dual-write during transition.** Legacy slots remain the source of truth for `review_bundle`/`approve_review` until the owner decides to switch review_bundle to read from the run dir instead. Both can coexist.
4. **No data migration needed.** Existing `data/metadata_*.json`, `review_queue/*`, `outputs/archive/*` remain as-is (they are historical records, not part of the new run index).
5. **Rollback.** If the new code is reverted, `outputs/runs/` and `data/runs/index.jsonl` are inert new files; legacy slots and all existing behavior are unchanged.

---

## 8. Minimum tests needed (specifications only — do not create tests)

| # | Test | What it verifies |
|---|---|---|
| M1 | Run dir created with `run_id` from topic+timestamp; manifest.json exists with `status: "in_progress"` at start | Run identity + manifest creation |
| M2 | Successful run: `manifest.json` `status == "ok"`; all artifacts have SHA-256; legacy slots `data/metadata.json` and `outputs/output_short.mp4` match the run's artifacts | Success path + slot preservation |
| M3 | Failed run: `failure.json` written; manifest `status == "failed"`; `data/metadata.json` unchanged (hash compare before/after); exit non-zero; no success JSON | Failure bookkeeping + output protection |
| M4 | Halfway failure: partial `shots/shot_NNN.mp4` present but manifest marks that shot `status != "ok"` or missing; legacy slots not overwritten | Partial output not mistaken for success |
| M5 | `data/runs/index.jsonl` gains exactly one line per run (ok or failed); append-only, no existing lines modified | Run index integrity |
| M6 | Repeated runs: run 2 does not delete run 1's dir; both `outputs/runs/<run_id>/` coexist | Repeat isolation |
| M7 | Review package from a run includes `run_id` and `run_manifest_path`; `approve_review.py` hash check still passes against legacy slots | Review-package run linkage |

All hermetic: tmp work dirs, no network, no writes to real `data/` or `outputs/` except via temporary copies under test control. These tests pin current contracts (they pass on today's code where applicable) and guard the new run layer.

---

## 9. Risks, trade-offs & implementation sequence

### Risks / trade-offs

| Risk | Mitigation |
|---|---|
| Manifest SHA-256 adds ~14 ffprobe/hash calls per run | Only hash after artifact finalized; `sha256_file` streams in 1 MB chunks (already used in `approval_integrity.py`). Negligible vs FFmpeg render time. |
| Run dirs accumulate disk usage over time | No auto-deletion (destructive). Future manual housekeeping tool can list via `index.jsonl`. Disk space check already exists in `n8n_runner.py:75-80`. |
| Two code paths (legacy slots + run dir) during transition | Document clearly: legacy slots = latest successful run for compatibility; run dir = source of truth for history/recovery. Owner decides when to consolidate review_bundle to read run dir. |
| Forgetting to write failure.json on some exception path | Centralize failure handling at one top-level try/except in `pipelines/short.py` `main()` and `pipeline.run()`, not per-stage. |
| `run_id` collision if same topic same second | Append `-2`, `-3` if dir already exists. |

### Implementation sequence (recommended, owner decision)

1. Add `run_id` generation + run directory creation at pipeline start (in-progress manifest).
2. Per-artifact SHA-256 + manifest updates; legacy-slot refresh on success; index.jsonl append.
3. Failure path: `failure.json` before re-raise; legacy slots untouched; non-zero exit.
4. `review_bundle.py` optionally records `run_id`/`run_manifest_path` in package (additive, existing hash check unchanged).
5. Tests M1–M7; full suite green; then owner review.

---

## 10. Areas explicitly NOT changed by this proposal

- Phase 9 audio (`ffmpeg_tools.py` loudnorm targets, `app/voice/*`, `motion_render.py` audio mix).
- Approval/publishing safeguards (`approve_review.py`, `approve_longform.py`, `approval_integrity.py`, `publish_all.py`, `upload_window_open`, n8n workflow JSON).
- Phase 10.1 evidence ledger schema (`LEDGER_VERSION`, `ledger_sha256`, claim vocab).
- Phase 10.1.1 feed work (Qoder): `desk.py` stubs/dead block, `trends.py` XML guard, `topics.py` exceptions, Trends URL defect.
- Strict Fail-Closed implementation (the `pipelines/short.py` fallback/`--strict` behavior) — this proposal coexists with whatever strict-mode decision is made; failure bookkeeping (failure.json) complements it.
- Existing `data/metadata.json`, `outputs/output_short.mp4`, `outputs/voice.mp3`, `outputs/subtitles.ass`, `data/review_*.json`, `data/review_queue/` — preserved as legacy slots.
- `archive/superseded/` — not an active entrypoint; left as-is.

---

**Conclusion:** Phase 10.4 adds a small, additive run-level layer (run_id + per-run dir + manifest + failure.json + index.jsonl) that solves P1–P8 without touching any existing file, without concurrency assumptions, and without changing approval, publishing, audio, or Phase 10/10.1 behavior. Ready for owner review before implementation.

*Prepared by the independent secondary researcher. Nothing implemented. Awaiting owner review.*
