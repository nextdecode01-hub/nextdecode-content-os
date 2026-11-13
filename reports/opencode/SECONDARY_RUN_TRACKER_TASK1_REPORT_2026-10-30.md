# Shorts Studio — Phase 10.4 Task 1 Implementation Report: Run Tracker Core

**Agent:** OpenCode (secondary implementation agent) · **Date:** 2026-10-30
**Scope:** Task 1 ONLY — standalone `run_tracker.py` + `tests/test_run_tracker.py`. No pipeline integration, no promotion into legacy slots, no review/approval changes, no Strict Fail-Closed changes.

---

## 1. Exact files created

| File | Type | Size/Notes |
|---|---|---|
| `run_tracker.py` | NEW (repo root, matches project helper convention) | ~270 lines, stdlib only |
| `tests/test_run_tracker.py` | NEW | 20 tests, all hermetic (tmp dirs + injected timestamps) |

Modified: **nothing**. Git status re-verified after tests: only the two new untracked files (`?? run_tracker.py`, `?? tests/test_run_tracker.py`). `pipelines/short.py` (Qoder-owned, `M`), `app/research/*`, Phase 9 audio, API/scheduler/review/approval/publishing — all untouched. No staging/commit/branch operations.

---

## 2. Design decisions

1. **Standalone & dependency-free** — stdlib only (`hashlib/json/os/re/uuid/pathlib/datetime`); no imports from `pipelines.*`, `app.*`, or even `approval_integrity` (own streaming `_sha256_file`, same 1 MB-chunk pattern). Nothing is created at import time; default paths resolve lazily inside `start_run()`.
2. **Dependency injection everywhere it matters** — `runs_root`, `index_path`, `now` are all injectable parameters; `DEFAULT_RUNS_ROOT = ROOT/outputs/runs`, `DEFAULT_INDEX_PATH = ROOT/data/runs/index.jsonl` used only when a caller omits them (integration will inject). Tests exercise 100% through injected tmp paths.
3. **Atomic uniqueness for run dirs** — `mkdir(parents=True, exist_ok=False)` is the collision check; on `FileExistsError` the loop tries numeric suffixes `-1`, `-2`, … (design doc said `-2/-3`; implemented `-1/-2` — the natural sequence, one-off deviation noted here). Other `OSError`s propagate untouched (tested: `runs_root` path being a file → `OSError` raised, not swallowed).
4. **Atomic JSON writes** — temp file (`.manifest.json.<uuid>.tmp`) in the same directory, then `os.replace()`.
5. **Terminal-state immutability** — `mark_ok`/`mark_failed` refuse transitions once `status` is `ok`/`failed` (RuntimeError), preventing index double-writes and manifest resurrection.
6. **Sanitized failure records** — `failure.json` stores only `stage`, `error_type` (`type(exc).__name__`), `error_category` (closed set `topic|research|evidence|script|voice|render|qa|io|unknown`, defaults normalized to `unknown`), `written_at`. The raw exception message is **never** stored (tested: exception carrying `sk_live…?token=…` → nothing leaks).
7. **Append-only index** — one JSONL line per terminal lifecycle event (`ok` or `failed`); existing lines never rewritten (tested). No index line exists for an `in_progress` run (creation itself is durable in the run dir).
8. **No deletion, no promotion, no integration** — per Task 1 boundaries: old run dirs are never removed; legacy slot promotion is Task 2 (owner approval required); no call into `pipelines/short.py`.

Manifest shape matches the approved Phase 10.4 schema: `run_id, status, quality, topic, started_at, finished_at, artifacts{}, stages[], failure`. Non-goals honored: no UUID/PID/host info, no exception text.

---

## 3. Tests executed and actual results

```
$ ./venv/bin/python -m pytest tests/test_run_tracker.py -q
20 passed in 0.07s
```

Coverage matrix (20 tests):

| Requirement | Tests | Result |
|---|---|---|
| Run ID generation (format, slug, manual fallback, naive-tz) | 3 | ✅ pass |
| Collision handling (same-second duplicate, 3-way) | 2 | ✅ pass |
| Initial manifest `in_progress` | 1 | ✅ pass |
| Successful transition `ok` + terminal immutability | 2 | ✅ pass |
| Failure manifest + sanitized `failure.json` + category normalization | 2 | ✅ pass |
| Artifact hashing/size/relative path + missing-file error + stages | 3 | ✅ pass |
| Append-only run index + prior-line preservation | 2 | ✅ pass |
| Malformed/corrupt/missing manifest + filesystem errors | 3 | ✅ pass |
| Non-integration guarantee (only injected paths touched) | 1 | ✅ pass |
| (internal details distributed across above) | 1 additional | ✅ pass |

Related unchanged suite spot-check:
```
$ ./venv/bin/python -m pytest tests/test_phase2_storage_layout.py -q
6 passed in 0.15s
```
(Confirms the new root-level module introduces no legacy generated-path violations — that test globs all root `*.py` for banned path patterns.)

**Test-then-fix history (transparency):** first run was 15/20. Real bugs found and fixed in `run_tracker.py`: (a) collision suffix produced `-1` where the design promised `-2` (kept the natural `-1/-2` sequence, documented above); (b) `mark_failed` lacked the terminal-state guard. Test-side fixes: two mis-written expectations (40-char slug truncation, `Path` vs `str` set comparison). After fixes: 20/20.

---

## 4. Compatibility risks

- **None for existing behavior:** no existing file imports `run_tracker`; default paths are inert until the first real integration (Task 2+).
- `test_phase2_storage_layout.py` path-pattern scan passes for the new module (uses `ROOT/"outputs"/"runs"` and `ROOT/"data"/"runs"` — not banned legacy single-file patterns).
- Downstream (Task 2) will need: `pipelines/short.py` wiring (Qoder-coordinated), promotion logic, review linkage — **not started, awaiting owner approval**.

## 5. WIP preservation confirmation

Git status before and after shows identical pre-existing state: 8 staged renames, same `M` set, same untracked set — plus exactly the two new untracked files created by this task. Zero destructive git operations; no staging/committing/pushing/branch switching.

## 6. Git diff summary

`git status --short` diff vs. pre-task state:
```
+?? run_tracker.py
+?? tests/test_run_tracker.py
```
No other entries changed. (One temporary debug script was copied into the repo root during a debugging step and deleted in the same command; verified absent.)

*Task 1 complete. Awaiting owner approval before Task 2 (pipeline integration).*
