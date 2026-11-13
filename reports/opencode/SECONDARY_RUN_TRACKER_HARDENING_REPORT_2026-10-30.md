# Shorts Studio — Phase 10.4 Task 1: Owner-Approved Hardening Report

**Agent:** OpenCode (secondary implementation agent) · **Date:** 2026-10-30
**Scope:** Only the two owner-authorized files (`run_tracker.py`, `tests/test_run_tracker.py`). Task 2 NOT started. No integration, no promotion, no review/approval changes, no pipelines/short.py touch.
**Pre-check:** Both files confirmed untracked (`??`) with no concurrent modifications — zero conflict; proceed authorized.

---

## 1. Implemented changes (all 5 approved items)

| # | Approved change | Implementation | Evidence |
|---|---|---|---|
| 1 | Fix stale collision-suffix comment | `run_tracker.py:262-263` now reads "(suffix -1, -2, ...)" | matches actual behavior pinned by tests `tests/test_run_tracker.py:43,53` |
| 2 | `schema_version: 1` in new manifests | Added to `start_run` manifest dict (`run_tracker.py:279`); documented in module docstring | test `test_manifest_has_schema_version` |
| 3 | Run-directory containment in `record_artifact()` | Symlink-resolved path must resolve inside the run dir; otherwise `RuntimeError "… escapes the run directory: <path> (approved artifacts must live inside <run_root>)"`. Only relative paths are stored. No automatic recovery — the exception is deterministic and the manifest is left unchanged | tests: external rejection (+ manifest-unchanged assert), symlink-escape rejection, symlink-inside-allowed → stored relative `shots/shot_000.mp4` |
| 4 | Duplicate artifact names rejected | `RuntimeError "artifact '<name>' already recorded for run <id>; refusing to overwrite"` before hashing; original entry preserved | test `test_duplicate_artifact_name_rejected` |
| 5 | New deterministic tests | 7 tests added (26 new asserts total incl. pre-check) | 27/27 green |

**Failure-recovery rule — documented only, in the module docstring (`run_tracker.py:16-25`):**
- `in_progress` without `failure.json` → interrupted/unknown
- `in_progress` WITH `failure.json` → failure recorded, manifest finalization incomplete
- `failed` → terminal failure · `ok` → terminal success
No old manifests rewritten; no existing runs altered; no automatic recovery implemented.

## 2. Tests executed — exact commands and actual results

```
$ ./venv/bin/python -m pytest tests/test_run_tracker.py -v
27 passed in 0.09s
```
(20 pre-existing + 7 new: `test_manifest_has_schema_version`, `test_artifact_outside_run_dir_rejected`, `test_symlink_escape_rejected` [OSError→skip guard for environments without symlink support], `test_symlink_resolving_inside_run_dir_allowed_and_stored_relative`, `test_duplicate_artifact_name_rejected`, `test_interrupted_run_identification_states`, `test_sha256_consistency_file_larger_than_2mb` [1 MB chunk loop ×2 MB+odd-tail file vs `hashlib.sha256(full_bytes)`])

```
$ ./venv/bin/python -m pytest tests/test_phase2_storage_layout.py -q
6 passed in 0.10s
```

## 3. Git state and diff summary

- Pre-task check: both targets untracked, no conflicts.
- Post-task `git status --short`: **identical pre-existing WIP preserved** (8 staged renames, the same modified set, and all untracked files — including Qoder's items). The only two files changed are the authorized ones:
  ```
  +?? run_tracker.py          (modified by hardening, still untracked)
  +?? tests/test_run_tracker.py  (modified by hardening, still untracked)
  ```
- `git diff --stat` output contains only the pre-existing Qoder modifications (21 tracked files, unchanged count from before this task) — the two hardening files are untracked so they do not appear in tracked diffs, exactly as before.
- No destructive git operations; nothing staged, committed, pushed; no branch switch.
- Zero modifications outside the two authorized files: `pipelines/short.py`, API, scheduler, review bundle, storyboard, cutouts, approval, publishing — all untouched.

## 4. Design notes

- Containment uses `Path.resolve()` (follows symlinks) + `relative_to` `ValueError` → deterministic fail — consistent with the file's existing style; works regardless of symlink direction (escape rejected, in-dir symlink resolves to its real relative location).
- Duplicate-name rejection occurs **before** hashing, so a rejected duplicate never re-reads a large file.
- External-path rejection test also asserts the manifest is byte-equal before/after — failed records leave zero residue.
- Interruption states tested via `load_manifest` + `failure.json` presence per the documented rule — pure identification, no recovery action anywhere.
- Edge case kept out of scope (already documented in self-review M-3): torn JSONL lines on power loss — remains a Task 2 owner decision.

*Hardening complete. Task 2 (pipeline integration) remains blocked pending separate owner approval.*
