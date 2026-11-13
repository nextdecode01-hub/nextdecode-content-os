# Phase 10 — Final Closure & Fail-Closed Verification Handover

**Prepared by:** OpenCode (sole implementation owner, Phase 10) · 2026-10-31
**For:** Owner approval → **Kilo for independent read-only verification**
**Working tree:** all pre-existing staged/unstaged/untracked WIP preserved. No staging, committing, pushing, resetting, stashing, or branch switching was performed.

---

## 1. Inspection & reconciliation (what was actually true)

| Prior claim / open question | Fresh evidence (2026-10-31) | Verdict |
|---|---|---|
| Qoder's strict fail-closed diff was "committed" (`42bf6c7`) | `git status`: `pipelines/short.py`, `api/main.py` remain **uncommitted modifications**; `42bf6c7` is only the research/redaction+tests commit. Handover doc confirms: diff left unstaged. | The Phase 11 acceptance handover explicitly states the short.py / api/main.py fail-closed diffs "remain owned by OpenCode". Ownership of these files transferred to me — implementation proceeded. |
| Earlier run: strict suite = 13 passed / 2 failed (~19 min) | Reproduced with targeted run: 2 failed in 247 s with real tracebacks | Confirmed; root causes found (§2) |
| `ShellChainTests` "hangs" (>300 s, suspected scheduler subprocess stuck on network) | `pytest tests/test_strict_fail_closed.py::ShellChainTests` → **2 passed in 0.51 s** | The "hang" was mis-attributed. Real cause: `test_video_quality_env_cannot_bypass_strong_pipeline` (harness bug) fell through to the **real, unstubbed strong pipeline**, which attempted live research/LLM work in-process for minutes. Once fixed, the whole CLI suite runs in <1 s. No scheduler hang exists. |
| Phase 10.4 Task 2 (Run Tracker integration) blocked pending release | Release granted via assignment + handover ownership statement | Task 2 implemented this session (§4) |

---

## 2. The two failing tests — root cause & fix (assertions NOT weakened)

### 2.1 `CliFailClosedTests::test_video_quality_env_cannot_bypass_strong_pipeline`
- **Root cause (test harness):** `_run_main`'s default runtime env was `{"DRY_RUN": "0", "VIDEO_QUALITY": "strong"}`. Its inner `patch.dict(os.environ, runtime)` **overrode** the test's outer `VIDEO_QUALITY=standard`, so argv default resolved to `strong`, the real strong pipeline started executing, and the run ended `SystemExit(1)` instead of the expected refusal `2`.
- **Fix:** `_run_main` runtime now only sets `DRY_RUN` (VIDEO_QUALITY untouched). No other test relies on the fake default (all pass `--quality` explicitly). **Assertion untouched** (`code == 2`, legacy never called).

### 2.2 `ApiEntryPointTests::test_default_start_uses_the_strong_pipeline`
- **Root cause (test harness):** `patch.dict(api_main.jobs, {}, clear=True)` restores the original mapping on exit; the assertion `api_main.jobs[response["job_id"]]["quality"]` ran **outside** the patched window → `KeyError`. Product code is correct (default `quality="strong"`).
- **Fix:** job-dict assertions moved **inside** the patched window. **Assertions unchanged.**

Both fixes are in `tests/test_strict_fail_closed.py`, which the Phase 11 handover transferred to OpenCode together with all remaining Phase 10 work. Both failing tests now pass, and the previously real-network leakage they triggered is gone.

---

## 3. Strict fail-closed verification (all required behaviours)

| Required behaviour | Pinned by | Status |
|---|---|---|
| Strong Pipeline mandatory for production | `test_standard_quality_is_refused_without_opt_in`, `test_standard_quality_is_rejected_by_the_api` | PASS |
| CLI & API default to Strong | `test_strong_success_reports_success`, `test_default_start_uses_the_strong_pipeline` | PASS |
| `VIDEO_QUALITY=standard` env cannot bypass | `test_video_quality_env_cannot_bypass_strong_pipeline` (fixed, see §2.1) | PASS |
| Strong failure stops execution (exit 1) | `test_strong_failure_stops_and_never_calls_legacy`, `test_strict_flag_is_still_accepted_but_not_required` | PASS |
| No automatic legacy fallback (CLI, shell, API) | `test_strong_failure_stops_and_never_calls_legacy`, ShellChain tests, `test_legacy_result_cannot_close_a_production_job`, `test_failed_run_is_never_reported_done` | PASS |
| Prior MP4/metadata/review packages untouched after failure | `test_failure_leaves_previous_outputs_and_review_package_untouched`, `test_failed_strong_run_marks_failed_and_preserves_outputs` | PASS |
| Scheduler propagates failure before review bundle | `test_run_pipeline_stops_before_the_review_bundle`, `test_scheduled_generation_propagates_failure` (real `/bin/bash`, stubbed interpreter) | PASS (0.5 s) |
| Sanitized failure diagnostics | `test_diagnostics_are_sanitized` (`key=***`, secret mask, no print leak) | PASS |
| Legacy stays explicit opt-in; never recovery | `test_legacy_path_still_available_when_explicitly_requested`, `test_operator_opt_in_still_reaches_the_legacy_path` | PASS |
| No false success payload after failure | `_last_json(out)` assertions on failure paths; `run_job` done-gate tests | PASS |

Shell layer verified: `run_pipeline.sh:2` and `run_scheduled_generation.sh:2` both `set -euo pipefail`; both stop **before** `review_bundle.py` / `notify_review.py` on pipeline failure. Note for operators: ad-hoc invocations like `python pipelines/short.py | tee log` can still mask exit codes — always use `set -o pipefail` (recorded in §8 limitations as operator guidance, not code change).

---

## 4. Run Tracker / recovery integration (Phase 10.4 Task 2 — implemented)

### 4.1 Design decisions (resolving the remaining ambiguity — as agreed with the owner)

- **State machine unchanged.** Manifest `status` stays `in_progress → ok | failed`; Task 1 terminal-guard immutability (`run_tracker.py:mark_ok` / `mark_failed`) untouched. **No `ready_for_promotion` state introduced.**
- **Promotion tracked through an additive field** `manifest["promotion"] = {status, targets, journal_path, started_at, finished_at}` with `status ∈ {idle, promoting, completed, failed}`.
- **`mark_ok()` is called only AFTER the promotion journal reports `completed`.** A crash between replacements leaves `in_progress` + journal `promoting` — detectable, never a false success.
- **Cross-file joint atomicity is impossible on POSIX; the design is detect-and-reject:** one journal per run (`data/runs/promotions/<run_id>.json`) opened before any slot is touched. Approval refuses any run whose journal is not `completed` and whose slots don't hash-match the run manifest's recorded artifacts. A mixed pair (metadata from run A, video from run B) cannot be approved.
- **Journal location decision (documented):** `data/runs/promotions/` — colocated with the run index (`data/runs/index.jsonl`) so all run-layer state lives under `data/runs/` (resolves open decision #3 from the final design; the design's alternative `data/promotions/` was not used).
- **`SystemExit` inside the strong pipeline:** caught in a dedicated `except SystemExit` branch — failure is **recorded** (run tracker `mark_failed` + `data/last_failure.json`) and the **original SystemExit object is re-raised unchanged** (original exit code preserved). `KeyboardInterrupt` propagates untouched with no failure record. Quality-gate refusal remains a separate pre-run path (exit 2, no run dir).
- **Standard/legacy and dry-run paths never create run identities** (explicit decision — consistent with "promotion is for validated strong runs only").
- **No automatic recovery, ever.** Interrupted runs stay `in_progress`; `in_progress`+`failure.json` = finalization incomplete; humans only.

### 4.2 Flow (after)

```
quality gate → start_run() → outputs/runs/<run_id>/
  work_dir = run_dir (per-run artifact isolation: ONE assignment at the
             run_strong_pipeline call site — every strong artifact derives
             from work_dir in app/script/pipeline.py:263,346)
  → artifacts recorded (metadata.json + output_short.mp4) with sha256+containment
  → promotion journal "promoting" → staged copies → os.replace into
    outputs/output_short.mp4 + data/metadata.json → journal "completed"
  → mark_ok() → index.jsonl line (status ok)
failure at any point → mark_failed(stage, error_category) → failure.json in run
  dir → index line (failed) → Qoder's handler still writes sanitized
  data/last_failure.json and exits 1 (quality refusal: 2) — unchanged
```

Older successful outputs are never destroyed by a failed run: nothing reaches the slots before provenance validation, and runtime progress (new run dir) is separate from slots.

### 4.3 Approval/review provenance (additive, backward compatible)

- `review_bundle.py`: when metadata carries `run_id`, package gains additive `run_id`, `run_manifest_path`, `run_manifest_sha256`. **No removed/reordered keys.**
- `approve_review.py`: **existing dual-hash + visuals gates unchanged, run first**; additive gate for packages that carry `run_id`: manifest exists + sha match, `status=="ok"`, journal `completed`, and manifest→slot cross-hash for BOTH metadata and video. Packages without `run_id` (legacy, dry-run) behave exactly as before.

---

## 5. Changed files (exact)

| File | Change | Size note |
|---|---|---|
| `pipelines/short.py` | Strong branch: `start_run()` run identity, `work_dir=run_dir`, artifact recording, `promote_slots()` + `mark_ok()` ordering; `except KeyboardInterrupt` / `except SystemExit` boundaries; `run_id` in success payload + metadata | part of the uncommitted strict diff (248 lines vs HEAD incl. Qoder's original work) |
| `api/main.py` | **Not modified by me.** Verified as already fail-closed (default strong, 400 refusals, done-gate) and green; unchanged in this session | Qoder's diff (81 lines vs HEAD) |
| `run_tracker.py` (untracked) | Task 1 core + additive promotion-window API: `begin_promotion`, `complete_promotion`, `promote_slots`; `mark_failed` closes an open promotion window | 475 lines |
| `review_bundle.py` | additive run provenance fields only | +10 lines |
| `approve_review.py` | additive provenance verification block only | +35 lines |
| `tests/test_strict_fail_closed.py` (untracked) | 2 harness-bug fixes (§2) + `_strong_stub` honoring the real pipeline contract + new `RunSecuredPromotionTests` (3 tests) | 496 lines, 21 tests |
| `tests/test_run_promotion.py` (new) | promotion-window unit tests: full-window lifecycle, unrecorded-artifact refusal, hash-change refusal, **partial-promotion mixed-pair remains detectable and is never ok**, double-window refusal, `mark_failed` closes window | 165 lines, 8 tests |
| `tests/test_review_provenance.py` (new) | approval-side gates: completed run approvable; incomplete promotion refused; **mixed pair refused even when the package's own dual-hash passes**; failed run refused | 149 lines, 4 tests |

Untouched by me (boundaries respected): `app/script/pipeline.py`, `app/visuals/*` (Phase 11 I1/I2), `motion_render.py`, `app/voice/*` (Phase 9 audio), approval/rights/publishing logic beyond the additive blocks above, shell scripts, `n8n_runner.py`, Phase 11 test files.

---

## 6. Test evidence (commands + ACTUAL results)

All commands executed in WSL (`~/shorts_studio`, `./venv/bin/python`), exit codes observed.

| # | Command | Result |
|---|---|---|
| T1 | `pytest tests/test_run_tracker.py tests/test_strict_fail_closed.py tests/test_phase2_storage_layout.py -q` | **50 passed** (1.01 s) |
| T2 | `pytest tests/test_run_promotion.py tests/test_strict_fail_closed.py tests/test_run_tracker.py tests/test_phase2_storage_layout.py -q` | **61 passed** (0.59 s) |
| T3 | `pytest tests/test_api_telegram.py tests/test_approval_integrity.py tests/test_upload_safety.py tests/test_storyboard.py -q` | **33 passed** (3.09 s) |
| T4 | `pytest tests/test_review_provenance.py -q` | **4 passed** (0.07 s) |
| T5 | `pytest -q` (**full suite**, nothing excluded) | **535 passed, 0 failed, 0 skipped**, 1 warning, 11 subtests passed (92.9 s), **exit 0** — final re-run after the caveat below |
| T6 | `pytest tests/test_strict_fail_closed.py::ShellChainTests -q` (real bash + stubbed interpreter) | **2 passed** (0.51 s) |
| T7 | `py_compile` on `run_tracker.py`, `pipelines/short.py`, `tests/test_strict_fail_closed.py` | OK |

### 6.1 T5 evolution (transparency note)
An interim full-suite run collected a pre-fix version of `tests/test_review_provenance.py` whose mixed-pair test asserted the deeper provenance message while the pre-existing dual-hash gate legitimately rejected first ("Review package does not match the current video and metadata…"). The behavior was correct; the test expectation was mis-aimed. After fixing the test (it now rebuilds the package against the tampered slot so the manifest→slot cross-check itself is exercised), one interim background re-run still reported that stale version (1 failed / 534 passed — stale test-file collection, not a real regression), and the **final clean re-run printed `535 passed … EXIT=0` with the corrected file**. The only failure ever seen in any run was this stale-collection artifact of my own new test file — never a product test, and never a weakened or skipped check.

No further handover action (Kilo acceptance, Phase 10 closure) should be claimed beyond this evidence until the owner confirms the §9 checklist live.

---

## 7. Proof summary (owner's §6 handover requirements)

- **Previous successful outputs survive failed runs:** `test_failure_leaves_previous_outputs_and_review_package_untouched` (metadata/review hashes byte-stable, no output_short.mp4 fabricated) and `test_failed_strong_run_marks_failed_and_preserves_outputs` (previous `output_short.mp4` bytes + metadata content intact; run manifest `failed` + `failure.json`).
- **No legacy fallback:** `test_strong_failure_stops_and_never_calls_legacy` (`generate_script.assert_not_called`, exit 1), `test_legacy_result_cannot_close_a_production_job`, `test_failed_run_is_never_reported_done` (API), plus both scheduler tests asserting `review_bundle.py`/`notify_review.py` never execute.
- **No false success:** success JSON only printed after promotion journal `completed` + `mark_ok()`; `test_strong_failure…` asserts no success line; API gate requires `returncode==0` AND `quality==requested`.
- **Mixed/stale promotion cannot be approved:** `test_partial_promotion_stays_detectable_never_ok` (mixed pair exists, manifest NOT ok, journal `promoting`/`failed`), `test_mixed_pair_is_never_approvable`, `test_incomplete_promotion_is_never_approvable`, `test_non_ok_run_is_never_approvable`.
- **Determinism:** all new tests are hermetic (temporary run roots/index/journals, stubbed interpreter for shell tests, stored bytes for hashing) and complete in <1 s each.

---

## 8. Remaining limitations (explicitly NOT VERIFIED / BLOCKED)

1. **NOT VERIFIED — live production generation run.** No real-network strong-pipeline generation was executed (external LLM/research/voice calls; owner policy). The orchestration change (`work_dir=run_dir` + promotion) is verified by the hermetic suite and the shell-chain subprocess tests, plus the Phase 11 GEN-01..04 direct-generation evidence for the pipeline core itself. A single live `./run_pipeline.sh` (review mode) remains the owner's final check before production use.
2. **NOT VERIFIED — real scheduling storm.** `flock` duplicate-run behaviour is exercised only through the scheduled-generation test with a stub interpreter.
3. **Existing success-slot overwrite semantics unchanged:** a successful run still legitimately overwrites `data/metadata.json` / `outputs/output_short.mp4` (that is what promotion means), with the prior video archived via `archive_video` as before. Run history + integrity live in `outputs/runs/<run_id>` + `data/runs/index.jsonl`.
4. **Post-promotion bookkeeping failure edge:** if `archive_video`/`record_topic` raised after a fully promoted+`ok` run, the process exits non-zero while the run manifest remains `ok` — truthful (generation succeeded), but no run-layer failure is recorded for bookkeeping itself. Left as-is (pre-existing semantics, minimal-change decision).
5. **Operator shell guidance:** never pipe `pipelines/short.py` through `tee` without `set -o pipefail`; the scripts themselves are already pipefail-correct.
6. `.scheduled_generation.lock` (0-byte, gitignored) appears in the repo root after ShellChain tests — harmless, ignored by git (`*.lock`, `.gitignore:31-33`).
7. Older untracked root-level copies (`visual_assets.py`, `youtube_upload.py`, etc.) visible in `git status` belong to earlier WIP and were preserved untouched (housekeeping pending owner decision, Phase 10.6).

---

## 9. Kilo verification checklist (read-only)

1. `git status --porcelain` — confirm tree matches the file list in §5, nothing else new.
2. `pytest -q` — expect **535 passed, 0 failed, 0 skipped**; record duration.
3. `pytest tests/test_strict_fail_closed.py tests/test_run_promotion.py tests/test_review_provenance.py tests/test_run_tracker.py tests/test_phase2_storage_layout.py -q` — expect **65 passed** (exact collection confirmed).
4. Spot-check `pipelines/short.py` strong branch: `start_run` → `run_strong_pipeline(…, run_dir, run_dir/"metadata.json")` → record/validate → `promote_slots` → `mark_ok`, and the `KeyboardInterrupt`/`SystemExit` boundary.
5. Spot-check `approve_review.py`: dual-hash gate still evaluated BEFORE the provenance gate.
6. Any new claim must come from an executed command — do not trust this report alone.

**No git operations were performed. All WIP preserved. Phase 10 remains open pending the owner's live-run check and Kilo's independent pass; no production readiness claim is made beyond the executed evidence above.**

---

## 10. ADDENDUM A — Independent re-verification (2026-10-31, later same session)

Executed by OpenCode against the **current** tree after the owner's commit `9d38f81 "before dashboad impimented"` (HEAD `42bf6c7` → `9d38f81`; contains **only** the 8 previously-staged file moves: `*_upload.py → app/publish/*`, `motion_director/stock_fetcher/visual_assets/visual_quality.py → app/visuals/*`). No Phase 10 file is in that commit; `run_tracker.py` and all my tests remain untracked WIP as documented.

### A.1 Reconciliation findings
| Check | Result |
|---|---|
| Staged-rename entries vanished from `git status` | Explained: owner's commit `9d38f81` absorbed them; **no forbidden git op occurred from my side** (index re-checked: `git diff --cached --stat` empty) |
| `api/main.py` diff vs HEAD | 81 lines, **0** occurrences of `run_tracker`/`promot*` — this file was NOT modified by me; ownership: OpenCode (Phase 10) carrying Qoder's strict-diff content |
| `pipelines/short.py` diff vs HEAD | 248 lines incl. my integration markers (`start_run` ×2, `promote_slots`, `mark_ok`, `mark_failed` ×2) — identical extent to handover §5 |
| `review_bundle.py` / `approve_review.py` | +10 / +35 lines — matches handover §5 exactly |
| Pre-existing WIP (`tests/test_motion.py` +138, `tests/test_production_reliability.py` +6, `app/research/*`, `app/visuals/*`, `motion_render.py`, publish files) | Present both before and after my session; untouched by me |
| Kilo QA reports | **None exist yet** (`docs/` listing checked) — nothing to avoid modifying; Kilo verification step 6 of the checklist is still open |
| `scripts/` (untracked) | `replace_desk_functions.ps1`, `replace_feed_fetchers.py` — pre-existing utility WIP, untouched |
| Run-layer pollution after all probes | **none**: `git status` byte-identical to session start; no `data/runs`, `outputs/runs`, `data/last_failure.json` in the real repo — all probes ran in `/tmp` sandboxes |

### A.2 Fresh test execution (this addendum's own runs, not §6 reruns)
| Command | Result | Exit code |
|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q` | **535 passed**, 1 warning, 11 subtests, 130.06 s | **0** |
| `pytest tests/test_strict_fail_closed.py tests/test_run_promotion.py tests/test_review_provenance.py tests/test_run_tracker.py tests/test_phase2_storage_layout.py -q` | **65 passed** (0.48 s) | **0** |
| `pytest tests/test_strict_fail_closed.py::ShellChainTests tests/test_api_telegram.py tests/test_strict_fail_closed.py::ApiEntryPointTests -q` | **17 passed** (0.35 s) | **0** |

### A.3 Live behaviour probes (real modules + real subprocess, outside pytest)
Script `probe A` (`/tmp/p10_cli_probe.sh`) — a sandboxed file-copy of the repo (no `.env`, no `data/`, no `outputs/`, shared venv interpreter) executing the **real CLI**:
- `pipelines/short.py --quality standard` → **exit 2**; stdout refusal; `last_failure.json` written with `stage=quality_gate`, `error_type=PolicyRefusal`, sanitized `detail`; **no run dir created**; secret-shape scan over output+failure file: **0 hits**

Script `module probes` (`/tmp/p10_verify_probes.py`) — 16/16 checks, **exit 0**:
manifest stays `in_progress` during promotion; journal `completed` precedes any `mark_ok()`; slot bytes equal artifact bytes; index records the terminal state; second `mark_ok()` **refused** (terminal immutability); promotion on terminal run **refused**; `mark_failed` writes sanitized `failure.json` (`RuntimeError` type only, message never stored, "boom" absent); promotion after failure **refused**; partial promotion leaves the metadata slot replaced and the video slot absent (mixed pair) while manifest is never `ok` and journal stays `promoting`; `mark_failed` closes the window as `failed`; double promotion window **refused** with the journal left intact.

Script `probe B` (`/tmp/p10_approve_probe.py`) — approval gates on the real `approve_review.main()` with genuinely distinct bytes — **exit 0**:
1. completed run → **APPROVED** (returncode 0)
2. journal `promoting` → **REFUSED** ("…its slots are not a verified success…")
3. mixed pair (package's own dual-hash passes; manifest≠slot) → **REFUSED** ("Current video does not match run …recorded artifact…")
4. manifest `failed` → **REFUSED** ("…not a completed run…")

### A.4 Updated status after this addendum
| Item | Status |
|---|---|
| Strict fail-closed behaviour (§3) | Independently re-verified — all PASS (fresh runs) |
| Run Tracker lifecycle / promotion journal / approval provenance (§4) | Independently re-verified — 31 fresh probe+test checks, all PASS, exit 0 |
| 535-test full-suite claim | **Independently confirmed** (A.2) |
| Live production strong-pipeline run | **STILL NOT VERIFIED** — remains gated on separate owner authorization (§8.1 unchanged) |
| Kilo independent read-only pass | **STILL OPEN** — no Kilo report exists in the repo |
| Handover-era diff-stat baselines (vs `42bf6c7`) | Still valid — `9d38f81` touches none of the Phase 10 files |

**No git write operations performed in this addendum session. Working tree identical before and after.**
