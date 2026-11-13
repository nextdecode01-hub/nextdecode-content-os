# Shorts Studio — Phase 10.4 Technical Design (Refined, Implementation-Ready)

**Run Identity, Artifact Isolation & Failure Recovery**
**Agent:** OpenCode (secondary) · **Date:** 2026-10-30 · **Mode:** READ-ONLY. No code modified. No git operations. Refines `reports/secondary-agent/SECONDARY_PHASE10_4_RUN_IDENTITY_PROPOSAL_2026-10-30.md` after fresh evidence verification.
**Excluded:** Phase 9 audio, Phase 10.1.1 (Qoder's working files untouched), Strict Fail-Closed implementation, publishing safeguards, concurrency infrastructure (no evidence production concurrency exists; `flock` at `run_scheduled_generation.sh:12-16` covers scheduler, API single-job serialization exists at `api/main.py:161-164`).

**Legend:** ✅ verified current behavior (file:line) · 💡 recommendation · ⚠️ owner decision required.

---

## A. Revised architecture diagram

```
                        ┌────────────────────────────────────────────────┐
   Callers (UNCHANGED)  │  run_pipeline.sh / run_scheduled_generation.sh │
                        │  api/main.py · n8n_runner.py                   │
                        └───────────────┬────────────────────────────────┘
                                        │ exec / subprocess (identical contracts)
                                        ▼
                        ┌────────────────────────────────────────────────┐
  NEW: run_tracker.py   │  run_id create → run dir → manifest lifecycle  │
  (single new module)   └───────┬────────────────────────┬───────────────┘
                                        │                        │
                     work_dir = run_dir │                        │ on success / on failure
                                        ▼                        ▼
                        ┌──────────────────────────────┐   ┌──────────────────────────┐
  Strong pipeline ✅    │ pipelines/short.py           │   │ legacy slots refreshed    │
  (one-line change)     │  → app/script/pipeline.run() │   │ ONLY from status=="ok"    │
                        │  writes ALL artifacts into   │   │ runs: metadata.json +     │
                        │  outputs/runs/<run_id>/ ✅   │   │ output_short.mp4          │
                        └──────────────────────────────┘   └────────────┬─────────────┘
                                        │                               ▼
                                        ▼                   ┌──────────────────────────────┐
                        ┌─────────────────────────────┐     │ review_bundle.py ✅ additive │
                        │ manifest.json (per run)     │     │ run_id + run_manifest_path   │
                        │ failure.json (only on fail) │     │ → approve_review ✅ unchanged│
                        │ data/runs/index.jsonl (log) │     │ → publishing ✅ unchanged    │
                        └─────────────────────────────┘     └──────────────────────────────┘
```

**Key leverage point (verified):** every strong-pipeline artifact is derived from `work_dir` — voice (`app/script/pipeline.py:323`), subtitles (`:329`), render output (`:340`), shots (`:264`, `assembly.py:194-207`, `shots.py:60`), claim ledger (`:297`), storyboard (`storyboard.py:312`), asset intermediates (`chain.py:624,657,702,1098,1101,1167-1170`). `pipeline.run(work_dir=...)` already accepts the parameter (`:262`) and `pipelines/short.py:338` already passes it. **→ Artifact isolation = one assignment change; no render/render/visuals module modifications.**

---

## B. Proposed directory structure (additive only)

```
shorts_studio/
├── run_tracker.py                          # NEW module (project convention: root-level helper, like video_archive.py)
├── data/
│   ├── metadata.json          # ✅ UNCHANGED contract: mirrors latest successful run
│   ├── review_pending.json / review_approved.json / review_queue/  # ✅ UNCHANGED
│   └── runs/
│       └── index.jsonl                     # NEW: append-only, one line per run
├── outputs/
│   ├── output_short.mp4  / voice.mp3 / subtitles.ass  # ✅ UNCHANGED legacy slots
│   └── runs/
│       └── <run_id>/                       # NEW per-run isolated tree
│           ├── manifest.json               # in_progress → ok | failed
│           ├── metadata.json               # this run's copy
│           ├── voice.mp3 / subtitles.ass / output_short.mp4
│           ├── research/claim_ledger.json  # (from :297 — lands here automatically)
│           ├── storyboard.json             # (from :312 — lands here automatically)
│           ├── shots/shot_000.mp4 …        # (from :60 — lands here automatically)
│           └── failure.json                # written only on failure
└── outputs/archive/                        # ✅ UNCHANGED (video_archive.py, post-success)
```

No existing file is deleted, renamed, or moved. `outputs/runs/` and `data/runs/` are new only.

**Run ID:** `YYYYMMDD-HHMMSS-<slug(topic) ≤ 40 chars>` (UTC timestamp, slug reused from `review_bundle.py:17-18`). **Collision prevention:** create with `mkdir(exist_ok=False)`; on `FileExistsError`, append `-2`, `-3`, … until unique (deterministic, monotonic, no ledger read needed).

---

## C. Exact manifest schema + realistic example

Schema (JSON, document-anchored below):

```jsonc
{
  "run_id": "...",                 // required, matches directory name
  "status": "...",                 // required: "in_progress" | "ok" | "failed"
  "quality": "...",                // "strong" | "dry_run" (recorded, not asserted)
  "topic": "...",
  "started_at": "...",             // ISO-8601 with tz
  "finished_at": null,             // null until terminal state
  "artifacts": {                   // keyed by artifact name; sha256 after finalize
    "<name>": { "path": "<relative to run dir>", "sha256": "...", "bytes": 0, "stage": "..." }
  },
  "stages": [                      // only what exists today in metadata.steps ✅ (:269-276) + timing
    { "name": "...", "started_at": "...", "finished_at": "...", "status": "ok|failed" }
  ],
  "failure": null                  // object only on failure: {stage, error_type, error_category}
}
```

Realistic example (failed run, voice stage):

```json
{
  "run_id": "20261031-142233-nist-ai-rmf-enterprise",
  "status": "failed",
  "quality": "strong",
  "topic": "NIST AI RMF Explained: What Enterprises Need to Know",
  "started_at": "2026-10-31T14:22:33+00:00",
  "finished_at": "2026-10-31T14:25:47+00:00",
  "artifacts": {
    "script_metadata": { "path": "metadata.json", "stage": "metadata", "sha256": "9f2c…e1", "bytes": 41233 }
  },
  "stages": [
    { "name": "topic",    "started_at": "2026-10-31T14:22:34+00:00", "finished_at": "2026-10-31T14:22:41+00:00", "status": "ok" },
    { "name": "research", "started_at": "2026-10-31T14:22:41+00:00", "finished_at": "2026-10-31T14:24:02+00:00", "status": "ok" },
    { "name": "voice",    "started_at": "2026-10-31T14:24:05+00:00", "finished_at": "2026-10-31T14:25:47+00:00", "status": "failed" }
  ],
  "failure": { "stage": "voice", "error_type": "RuntimeError", "error_category": "voice" }
}
```

Deliberate omissions (avoid unnecessary metadata): no UUID, no process/PID, no host info, no frozen step payloads (those stay in `metadata.steps[]` ✅ `:486` where they already live), no free-text exception messages (type/category only — also avoids secret leakage risk flagged in `pipelines/short.py:342`), no fluid per-artifact status enum (an artifact recorded = finalized; status lives at run level).

Error categories (closed set, aligned with 10.3 observability): `topic | research | evidence | script | voice | render | qa | io | unknown`.

---

## D. Lifecycle — success / failure / recovery

**Success:** 1) `run_id` + run dir + `manifest{status:"in_progress"}` → 2) `pipeline.run(work_dir=run_dir)` ✅ unchanged internals → 3) `run_strong_pipeline` writes `metadata.json` into run dir → 4) tracker hashes artifacts into manifest, sets `status:"ok", finished_at`, appends index line → 5) **promote:** copy run-dir `metadata.json`→`data/metadata.json`, `output_short.mp4`→`outputs/output_short.mp4` (copy-with-temp+rename; ✅ `video_archive.py` then archives from legacy slot, unchanged) → 6) `review_bundle.py` → human approval — all existing steps untouched.

**Failure (strong stage fails mid-run):** 1) exception reaches the caller of `run_strong_pipeline` → 2) tracker writes `failure.json` + sets manifest `status:""failed"`, appends index line → 3) **legacy slots are never touched by a failed run** (preserves last good output; resolves the overwrite risk at `pipelines/short.py:364-365`) → 4) control flow returns exactly as today (current fallback semantics preserved — see ⚠️ D-1 below).

**Recovery (operator-initiated, never automatic):** list runs via `data/runs/index.jsonl` / `outputs/runs/*`; to re-promote a past run, copy its `metadata.json`+`output_short.mp4` into the legacy slots, then re-run `review_bundle.py`. Manual only — **incomplete/failed runs are never promoted automatically**, and `approve_review.py:27-34` hash verification continues to bind approval to the exact files.

**⚠️ D-1 (owner decision):** recording failure.json requires **one additive call inside the `except` block at `pipelines/short.py:339-343`** — before the existing `print`/fall-through. Control flow is unchanged (no strict-mode change), but that block is Strict Fail-Closed territory, so this line needs explicit owner sign-off. Alternative: skip D step-3 hook and record failure only via strong-path wrapper inside `run_strong_pipeline` (:210-223) — same region, same approval need.

---

## E. Existing files/modules that would need modification (complete list)

| File | Change | Size | Why |
|---|---|---|---|
| `run_tracker.py` (NEW) | run_id gen, dir create, manifest read/write, sha256 (reuse `approval_integrity.sha256_file` ✅ `:12-17`), index append, promote | ~150 lines | single owner of run-layer logic |
| `pipelines/short.py` | `run_strong_pipeline` (:210-223) + fallback `except` (:336-343): pass `work_dir=run_dir` instead of fixed `outputs/`, promote legacy slots on success, additive failure hook | ~25 lines net | leverage point; metadata_file path :318 stays as promote target |
| `review_bundle.py` | additive `run_id`/`run_manifest_path` fields read from metadata (:30-48) | ~6 lines | links review package ↔ run |
| `tests/test_run_tracker.py` (NEW) / `tests/test_run_isolation.py` (NEW) | acceptance tests F1–F7 | new files | — |

Not modified: `app/script/pipeline.py`, `app/render/*`, `app/visuals/*`, `app/voice/*`, `approve_review.py`, `api/main.py`, all shell scripts, `n8n_runner.py`, `video_archive.py`, `approval_integrity.py` — contracts already satisfied because artifacts land in the run dir via `work_dir` and legacy slots are refreshed post-success.

---

## F. Seven focused acceptance tests

1. **F1 Run creation:** invoking the strong path creates `outputs/runs/<run_id>/manifest.json` with `status:"in_progress"`; second identical-second invocation gets `-2` suffix (collision).
2. **F2 Isolation:** after a full synthetic run (mocked research/LLM/procedural voice), voice/subtitles/output/shots/ledger/storyboard all resolve inside the run dir; zero artifacts written to `outputs/` root until promotion.
3. **F3 Promotion:** on success, legacy `data/metadata.json` + `outputs/output_short.mp4` are byte-identical (hash) to the run dir copies; manifest `status=="ok"`.
4. **F4 Failure preservation:** strong stage raises at voice; `failure.json` exists, manifest `status=="failed"` with error category; **pre-existing** `data/metadata.json`/`output_short.mp4` hashes unchanged; exit/control-flow identical to today.
5. **F5 Index integrity:** `data/runs/index.jsonl` gains exactly one append-only line per run (ok and failed); prior lines byte-unchanged.
6. **F6 Review linkage:** review package contains `run_id`+`run_manifest_path`; `approve_review.py` hash checks (:27-34) pass unchanged against legacy slots; a package without run_id (old metadata) still packages without error (backward compat).
7. **F7 Repeat-run independence:** run 2 (different run_id) never modifies run 1's directory; run 1's manifest remains `ok`.

All hermetic: tmp dirs, mocked network/LLM, silent voice provider (pattern exists in `run_dry_run`, `pipelines/short.py:250-292`), never touching real `data/`/`outputs/`.

---

## G. Incremental implementation plan (small tasks, each independently landable)

| # | Task | Touches | Gate |
|---|---|---|---|
| 1 | `run_tracker.py` + unit tests (pure library; nothing calls it yet) | new files | unit tests green |
| 2 | Wire strong path: run_dir + `work_dir=run_dir` + success promotion + index line | `pipelines/short.py` | full pytest; dry-run path untouched |
| 3 | Failure hook (⚠️ owner sign-off first, D-1) | `pipelines/short.py` except block | F4 green; fallback behavior identical |
| 4 | Review linkage fields | `review_bundle.py` | F6 green; `test_phase2_storage_layout.py` path assertions (:101-108) unaffected |
| 5 | F2/F3/F5/F7 acceptance tests + full-suite gate + `docs/PHASE10_4_*` note | tests, docs | whole suite green; owner review |

Rollback: delete `run_tracker.py` calls (one import + call sites); `outputs/runs/`+`data/runs/` are inert data. Zero legacy contract at risk.

---

## H. Risks, dependencies, unresolved owner decisions

**Risks:** (1) Extra disk copies per run (~video duplicate in run dir + archive) — acceptable; retention/cleanup = future manual tool, never auto-delete. (2) Failure hook sits in strict-fallback block — mitigated by pure-additive call, owner sign-off (D-1). (3) Storyboard approval writes (`storyboard.py:511-512`) now land inside run dirs — approval artifacts become per-run; existing tests pin only the review statuses, not global paths ✅ verified; flag for owner awareness. (4) `archive_video` still archives from legacy slot post-success — unchanged behavior, but archives reference the slot copy not the run-dir original (identical bytes ✅ F3).

**Dependencies:** none on Phase 10.1.1 (different files/regions); none on Strict Fail-Closed outcome (tracker records whatever control flow produces); none on concurrency (single-job serialization already exists at both caller layers).

**⚠️ Unresolved owner decisions:** (a) D-1 failure-hook approval; (b) who lands this — secondary vs Qoder (avoiding a second `desk.py`-style dual-ownership contention; `pipelines/short.py` is currently Qoder-modified `M`, so **coordination required before Task 2 lands**); (c) retention policy for run dirs; (d) eventual upgrade of `review_bundle.py` to read run dir directly (deferred; legacy-slot read is sufficient now).

**Owner-decision items require human review before implementation. Nothing implemented by this reviewer.**
