# Shorts Studio — Phase 10.4: Task 1.1 Completion Report + Task 2 Integration-Readiness Design

**Agent:** OpenCode (secondary) · **Date:** 2026-10-30
**Coordination rule honored:** Qoder holds the current (unstaged) Strict Fail-Closed implementation in `pipelines/short.py` (+193-line diff at inspection time) and `api/main.py`; its diff was inspected in full and its tests read (not executed — one timed out at 120 s, treated as Qoder's in-flight WIP). **No implementation of Task 2 was performed. Design report only.**

---

## PART A — Task 1.1 status (already implemented; fresh verification evidence this turn)

Task 1.1 was owner-approved and implemented in the previous cycle. This turn's fresh check:

- **Pre-modification git check:** both authorized files untracked, no concurrent modifications → no conflict → proceed (already done; idempotent).
- **Exact changed files (unchanged since hardening):**
  - `run_tracker.py` — stale comment fixed (`:286` "(suffix -1, -2, ...)"), `schema_version: 1` (`:303` + docstring `:25`), run-dir containment with symlink-escape rejection and relative-only storage (`:144-176`), duplicate-artifact rejection (`:154-157, :161`), recovery rule documented (`:16-25`).
  - `tests/test_run_tracker.py` — +7 deterministic tests (external rejection, symlink escape [OSError→skip guard], duplicate rejection, schema version, interrupted-run states, >2 MB SHA-256).
- **Test commands / actual results (re-run this turn):**
  ```
  ./venv/bin/python -m pytest tests/test_run_tracker.py tests/test_phase2_storage_layout.py -q
  33 passed in 0.15s        # 27 run-tracker incl. all 7 new + 6 storage-layout
  ```
  (Separately this cycle: `tests/test_run_tracker.py -v` → 27 passed in 0.09 s; `tests/test_phase2_storage_layout.py -q` → 6 passed in 0.10 s.)
- **Git before == after:** both files remain untracked (`?? run_tracker.py`, `?? tests/test_run_tracker.py`); all 82 pre-existing status entries preserved. Nothing staged/committed/pushed/reset/cleaned/stashed.
- **Unresolved (owner decisions carried from self-review):** artifact-path enforcement is now implemented per approval; remaining known-but-deferred item: torn JSONL line handling on power loss (Task 2 owner decision), and `record_stage` free-string status (accepted as-is).
- Hardening details: `reports/opencode/SECONDARY_RUN_TRACKER_HARDENING_REPORT_2026-10-30.md` (Downloads).

**Task 1.1 verdict: COMPLETE, no outstanding defects blocking Task 2 design.**

---

## PART B — Task 2: Integration-Readiness Design (design only; no code changed)

### B.1 Current actual call-flow (inspected this turn, file:line)

```
run_scheduled_generation.sh:18 ──▶ run_pipeline.sh:17 ──▶ pipelines/short.py main()
api/main.py run_job:111-131 ─────▶ subprocess -m pipelines.short --quality <q>
n8n_runner.py:97 ────────────────▶ run_scheduled_generation.sh  (EXECUTION_LOCK :23 serializes)
                                          │
             ┌────────────────────────────┘
             ▼  main() (pipelines/short.py:434-483)
 quality gate: non-strong without --allow-standard → _record_failure("quality_gate") → SystemExit 2  (:434-440)
   ✔ NEW: VIDEO_QUALITY / --quality can no longer silently select legacy
 strong branch (:442-476):
     try: run_strong_pipeline(topic, work_dir, metadata_file)   :444
         run_strong_pipeline :263-276
           └─ strong_pipeline.run(work_dir=work_dir)            :266-270   ← every artifact lands here
           └─ metadata_file.write_text(...)                     :275  ← direct legacy-slot write
     except Exception:                                           :445-451
         _record_failure("strong_pipeline", exc, "strong")        :448  → data/last_failure.json (sanitized, :65-85)
         print sanitized via _redact(exc)                         :449  ← secret leakage fixed
         raise SystemExit(1)                                      :451  ← NO legacy fallback
     success → record_topic, archive_video(output_mp4,...)        :452-456 (legacy slots)
 explicit legacy: --allow-standard only → run_standard_pipeline   :470-483  ("legacy": true never automatic)
```

Qoder's implemented Strict Fail-Closed state (verified): quality gate (strong-only), no automatic fallback, sanitized diagnostics (`_redact` env-regex `:48-62`), legacy opt-in flag, `"legacy": true` marker in standard output, API “done” requires quality match (`api/main.py:135-138`), API rejects non-strong production with HTTP 400 (`:181-185`), previous outputs preserved on failure (legacy `data/metadata.json` untouched — the old overwrite at former `:364-365` is gone).

### B.2 The 10 assignment questions → design answers

**1. How `pipelines/short.py` invokes Strong Pipeline.** `main()` → `run_strong_pipeline(topic, work_dir, metadata_file)` (`:444`) → `strong_pipeline.run(topic, seconds=..., work_dir=work_dir)` (`:266-270`).

**2. `work_dir` isolation.** Unchanged leverage point: every strong artifact derives from `work_dir` (verified: voice/substitutions/output/shots/ledger/storyboard under `app/script/pipeline.py:264,297,323,329,340`; `assembly.py:194-207`; `shots.py:60`; `storyboard.py:312`; asset intermediates `chain.py:624,657,702,1091-1170`). Design: `main()` strong branch passes `work_dir = run_dir` after `track = run_tracker.start_run(topic)`; `run_strong_pipeline` writes metadata into the run dir; **one assignment change + one wrapper** — `main()` post-success lines (`:452-468`) continue to operate on legacy slots unchanged.

**3. Strict Fail-Closed × run-lifecycle interaction.** Qoder owns the except-block (`:445-451`). Design keeps his code authoritative: `run_strong_pipeline` wraps its body:
```
track = run_tracker.start_run(topic, work_dir=RUNS_ROOT)     # in_progress manifest
try: ... run(work_dir=run_dir) ...
     track.mark_ok()                                          # manifest ok; index line
     promote(run_dir → legacy slots)                          # copy+os.replace, only from ok
     return data
except BaseException as exc:
    track.mark_failed(stage=<category>, exc=exc)              # failure.json + manifest failed + index
    raise                                                     # Qoder's handler still runs unchanged
```
Two saved diagnostic layers coexist: per-run `outputs/runs/<run_id>/failure.json` (run-scoped history) and Qoder's `data/last_failure.json` (operator "latest" pointer). **Precedence rule documented:** `last_failure.json` = latest event only; the run index is the source of truth for history. Strict semantics untouched — `_record_failure`, quality gate, SystemExit codes, `--allow-standard` all remain as Qoder shipped them.

**4. Success/failure recording.** Success: manifest `ok` + index `{"run_id","status":"ok",...}` + legacy-slot promotion. Failure: manifest `failed` + sanitized `failure.json` (tracker stores only type/category — complements Qoder's `_redact`-sanitized message in `last_failure.json`) + index line. Quality-gate refusals (`SystemExit 2` at `:436-440`) happen **before** `start_run()` — they never create a run dir (design decision: refusal ≠ run).

**5. Atomic promotion to legacy slots.** `promote()` in Task 2 code: write `data/metadata.json.tmp` then `os.replace()`; `shutil.copy2(run_dir/output_short.mp4 → outputs/output_short.mp4.tmp)` then `os.replace()` (copy for video, replace for metadata; both same-dir replace = atomic on POSIX). Promoted only when `manifest.status == "ok"` and `metadata.json` hash recorded in manifest — never from `failed`/`in_progress` runs. `archive_video` (`main:453`) then archives the promoted legacy file — unchanged behavior.

**6. Preserving previous successful outputs.** (a) fail-closed guarantees no overwrite on failure (Qoder ✅); (b) promotion writes legacy slots **only on success** with replace-atomicity; (c) per-run dirs keep every historical copy; (d) `review_queue/` + `review_pending.json` untouched by promotion (approval chain reads current slots only at approval time — `approve_review.py:19-34` unchanged).

**7. Review package ↔ manifest link.** `run_strong_pipeline` injects `data["run_id"]` and `data["run_manifest_path"]` before metadata write; `review_bundle.py` copies these (plus optional `run_manifest_sha256`) into the package — additive fields only; existing dual-hash verification (`review_bundle.py:34-37`, `approve_review.py:27-34`) untouched. Approval then reads manifest from the run dir (immortal files, never overwritten) instead of the volatile legacy metadata slot — closes the "slot overwritten between package and approval" tracking gap.

**8. Interrupted-run identification.** Documented tracker rule (Task 1 hardened): `in_progress` (no `failure.json`) = interrupted/unknown; `in_progress` + `failure.json` = finalization incomplete; `failed`/`ok` terminal. Identification = read-only scan of `outputs/runs/*/manifest.json` + `data/runs/index.jsonl`. **No automatic deletion, recovery, or promotion** — ever. Future manual housekeeping tool lists them; deletion remains a human action (out of Phase 10.4).

**9. Concurrency evidence.** ❌ Not possible today, and not required: `api/main.py:186-189` allows exactly one queued/running job; `n8n_runner.py:23` `EXECUTION_LOCK` serializes the runner; scheduler has `flock` (`run_scheduled_generation.sh:12-16`). No per-run allocator race exists. Run dirs made it *possible later*, but Task 2 adds no concurrent primitives (constraint honored — no evidence of concurrent production use).

**10. Minimum integration tests (specs only).** T-01 run dir + in-progress manifest created before `strong_pipeline.run` is called; T-02 success → manifest ok, index line, legacy slots byte-equal to run artifacts, `main` post-success lines unchanged behavior; T-03 strong failure → manifest failed + failure.json + index, `data/metadata.json`/`output_short.mp4` byte-unchanged, exit 1, **Qoder's `last_failure.json` still written**; T-04 review package contains run_id/manifest path; approve-review hash checks pass; T-05 quality-gate refusal → SystemExit 2, no run dir created, `last_failure.json` present; T-06 `--allow-standard` legacy run skipped by tracker or indexed with `quality:"standard"` (owner picks; default design: tracked separately, no promotion from unvalidated legacy); T-07 re-run after failure creates a *new* run dir, previous manifest untouched. All hermetic (mock research/LLM/silent voice — pattern `run_dry_run`).

### B.3 File-level implementation plan (when later authorized)

| File | Change | Est. |
|---|---|---|
| `pipelines/short.py` | `run_strong_pipeline`: start_run + work_dir=run_dir + mark_ok/mark_failed + inject run_id into metadata + `promote()` | ~50 lines net |
| `run_tracker.py` | add `promote(run_dir, legacy_metadata, legacy_video)` helper (already isolated; small) | ~25 lines |
| `review_bundle.py` | additive run_id/manifest fields | ~6 lines |
| tests (new) | T-01..T-07 matrix | new files |

Untouched: `app/script/pipeline.py`, render/visuals/voice layers, `api/main.py`, shell scripts, `n8n_runner.py`, approval/publishing, Phase 9 audio, Phase 10.1(.1) files.

### B.4 Ownership / conflict map (.inspect-time state)

| File | Owner now | Task 2 claim | Conflict status |
|---|---|---|---|
| `pipelines/short.py` | Qoder (strict fail-closed, active unstaged diff, in-flight tests `tests/test_strict_fail_closed.py`) | Task 2 edits `run_strong_pipeline` only (adjacent but disjoint block) | ⚠️ ACTIVE — integration deferred until owner says Qoder's diff is complete & accepted |
| `app/research/desk.py` | Qoder 10.1.1 | none | none |
| `api/main.py` | Qoder (already integrated strict semantics, verified) | **none needed** | none |
| `review_bundle.py` | uncommited-clean (`` not in modified set at inspection) | tiny additive | clear |
| `run_tracker.py` | this agent | extend `promote()` | clear |
| shell scripts / n8n | clean | none | none |

### B.5 Failure & recovery scenario matrix

| Scenario | Files after event | Review impact |
|---|---|---|
| Mid-run crash (video stage) | run dir manifest `failed`/`in_progress`+failure.json, index line, legacy slots untouched, `last_failure.json` updated | previous package still valid |
| Quality-gate refusal | no run dir; `last_failure.json` (stage quality_gate) | none |
| Success | new run dir ok + promoted slots + index | fresh package from promoted metadata |
| Re-promote old run (manual) | copy back ok-run artifacts → legacy slots, then re-run review_bundle | hash-consistent because artifacts are manifest-hashed |

### B.6 Implementation-readiness verdict

**DESIGN-READY — implementation blocked by policy, not by technology.** All ten answers are grounded in inspected current code; no conflicts are unavoidable: `run_strong_pipeline` (`:263-276`) is the only edit surface in Qoder-owned files and it is disjoint from his strict-fail-closed edits (gate `:434-440`, except-block `:445-451`). Per the explicit coordination rule: **do not modify `pipelines/short.py` (or any Qoder-owned file) until (a) Qoder's implementation is complete, (b) its diff re-inspected, (c) strict fail-closed acceptance criteria pass (its test file exists but was not executed by this agent — one run timed out, treated as WIP), and (d) the owner explicitly approves integration.** Strict Fail-Closed acceptance appears satisfied in code (quality gate, no automatic fallback, sanitized diagnostics, guarded API "done", previous-output preservation) — final confirmation belongs to the owner/primary agent.

---

**No Task 2 implementation performed. Nothing staged/committed/pushed/reset/cleaned/stashed. All WIP preserved.** Awaiting owner decision: schedule Task 2 after Qoder's strict-fail-closed diff is accepted.
