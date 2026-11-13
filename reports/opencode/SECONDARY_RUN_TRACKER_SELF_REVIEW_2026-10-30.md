# Shorts Studio — Phase 10.4 Task 1: Self Code Review (READ-ONLY)

**Agent:** OpenCode (secondary implementation agent) · **Date:** 2026-10-30
**Scope:** `run_tracker.py`, `tests/test_run_tracker.py` — reviewed in full, line-referenced. **Zero modifications made to either file or any repo file.** Git untouched.
**Basis:** re-read both files post-completion (20/20 tests green state as reviewed ✓). Findings ranked; verified-current behavior vs. theoretical risk separated. No Task 2 work started.

---

## 1. Findings (ranked)

### Critical

**None found.** No correctness, data-loss, or security defect was confirmed in the two files.

### High

**H-1. Partial-failure window between `failure.json` (`:210-214`) and manifest write (`:215`) — ✅ behavior confirmed, theoretical exposure.**
`mark_failed()` writes `failure.json` *before* updating the manifest. A crash in between leaves a run directory with `status:"in_progress"` + a `failure.json` present. This does **not** corrupt successful runs (each run dir is isolated, and the terminal-guard at `:196-200` blocks resurrection within one process), but a later reconciler must define precedence. **Not a defect today** (single-process lifecycle), but Task 2's failure hook must call `mark_failed()` and trust it — so the precedence rule must be documented. *
Mitigation note:* the ordering is actually the right one (failure.json is the durable signal); manifest staying `in_progress` is recoverable. Missing deterministic test (see §3 T-M1).

### Medium

**M-1. Artifact paths stored outside the run dir become absolute (`run_tracker.py:144-148`).** ✅ confirmed: `record_artifact()` stores a run-relative path when the file is inside the run dir, but silently falls back to an **absolute machine-specific path** when not (symlink followed via `.resolve()` also escapes). No traversal *vulnerability* (read-only hashing), but it breaks the "artifacts remain relative to the run directory" guarantee the manifest schema promises, and ports badly across machines. **Recommendation before Task 2:** integration caller must only ever pass run-dir-resident files; enforcement (reject outside paths) is a Task 2 boundary decision — owner call. Missing deterministic test (§3 T-M2).

**M-2. No `schema_version` in the manifest (`start_run` `:278-288`).** ✅ confirmed absent. Future schema evolution (Task 2+ adds fields) cannot distinguish v1 manifests from later ones when `load_manifest()` runs against old run dirs. Additive, one-line fix, cheap now vs. migration pain later. Owner decision (touches the approved schema).

**M-3. Torn JSONL line on power loss (`append_index_line` `:104-109`).** ✅ pattern-level: single-line writes to `open("a")` are small but not fsynced; a crash mid-write could leave a truncated last line that breaks naive `json.loads` over the index. Theoretical (no evidence of harm today), but the index is the recovery backbone. Recommendation: ignore in Task 1; handle at Task 2 (robust line-reader or fsync) — flagged as owner decision.

### Low

**L-1. STALE DESIGN-DRIFT COMMENT — ✅ confirmed defect (doc-only).** `run_tracker.py:262-263` comment reads "suffixes -2, -3, ..." but the implementation produces `-1`, `-2`, … (verified by tests `tests/test_run_tracker.py:43,53`). The module docstring (`:10`) and report were corrected, this inline comment was not. One-line fix, comment-only. (Deviation from the design doc's `-2/-3` was already disclosed in the Task 1 report.)

**L-2. Duplicate naive-datetime normalization logic.** `_utcnow` handling duplicated in `generate_run_id` (`:61-63`) and `_iso` (`:237-240`); `start_run` also does `now or _utcnow()` (`:277`) then `_iso` re-normalizes (`:283`). Minor duplication; harmless. Simplification candidate: make `_iso` the single choke point. No safety reduction.

**L-3. `record_stage` accepts any `status` string (`:161-166`)** — not validated against a closed set (contract of `ok|failed` is implicit only). Also `mark_failed`'s `stage` parameter is a free string while `error_category` is normalized (`:201`). Asymmetric but safe (no index pollution since values are stored as-is). Low.

**L-4. Silent overwrite of duplicate artifact name (`:155`).** `artifacts.setdefault(...)[name] = entry` replaces a previously recorded entry without warning. Theoretical (integration should record each artifact once). Could assert-on-duplicate if owner prefers strictness.

**L-5. Hash/size TOCTOU (`:151-152`).** `sha256` is computed, then `stat().st_size` read separately; a file mutated in between yields an entry whose bytes and hash refer to *different contents*. Theoretical — Task 2 integration writes artifacts before recording, single-process. A deterministic >1 MB test also is missing (§3 T-M3), so the chunk loop (1 MB, `:68-74`) is correct-by-inspection but chunk-boundary behavior is untested.

**L-6. Orphan run dir if `start_run` dies between dir creation (`:269`) and first manifest write (`:290`).** Dir exists with no manifest; the next same-second start would suffix numbered past it; `load_manifest` raises clearly ("manifest not found"). Theoretical, self-limiting.

**L-7. `test_nothing_written_outside_injected_paths` (`tests/test_run_tracker.py:221-226`) — weak assertion mixing.** The test proves (a) injected-only writes and (b) absence of an index file pre-terminal, but the two `DEFAULT_*` assertions (`:224-225`) only check constants and add no runtime safety. Not a false pass — just an unfocused test. Low.

---

## 2. Objectives 1–4 / 7–8 — clean areas (verified, no findings)

- **Public API/lifecycle (`:55-65, 90-101, 112-234, 243-291`):** `generate_run_id` deterministic & injectable ✅; `load_manifest` converts corrupt JSON/missing/malformed into clear RuntimeErrors ✅ (tests `:190-216`); terminal-state immutability enforced on *both* transitions (`:172-176, 196-200`) ✅ (test `:80-87`).
- **Atomic writes (`:77-87`):** same-directory temp file + `os.replace()` ✅; finally-block cleanup is safe (`tmp` already consumed after replace). After-fix note: the Task-1 fix history is reflected — the two task report bugs (collision suffix, failed-guard) are confirmed fixed at `:264-273, :196-200`.
- **Manifest schema & JSONL consistency:** `run_id` stored is the *suffixed directory name* (`:279, :289-290`) — collision chain and manifest/index stay consistent ✅ (tests `:161-174`).

- **Interrupted-run identification (objective 8):** ✅ works as designed — an interrupted run keeps `status:"in_progress"` + epoch `started_at` + no terminal index line; failed-but-unmanifested runs additionally have `failure.json` present. Successful runs can never be confused with either (isolated dirs, terminal guard, one index line per terminal event ✅ test `:177-185`).

- **Failure sanitization (objective 7):** ✅ verified both at storage layer (only `type(exc).__name__`, `:204`) and by test (`:130-149`, exception message containing `sk_live…?token=…` never reaches `failure.json` or manifest). Index records necessarily derive only from sanitized manifest fields (`:224-234`).

- **Concurrent creation safety (objective 3, within claim of the design):** the `mkdir(exist_ok=False)` loop (`:266-273`) is an atomic existence check, so two processes racing would both recover via suffix retries; non-FileExistsError OSErrors propagate (`:274-275`, test `:206-211`). ⚠️ **Concurrency itself is out of scope by design** (constraint honored) — the loop is *race-tolerant*, not a tested multi-process guarantee; no concurrency test exists and none is required until evidence of concurrent generation exists (per Task 1 boundary).

---

## 3. Missing deterministic tests (specs only — not written; no code modified)

| ID | Test | Protects |
|---|---|---|
| T-M1 | Interrupted run: `start_run` then discard tracker → `load_manifest` shows `status == "in_progress"`, no terminal index line; marked reconciliation precedence for `failure.json` present | H-1 recovery rule |
| T-M2 | Artifact provided outside run dir → behavior pinned (absolute-path stored, or rejected if owner chooses enforcement) | M-1 |
| T-M3 | Hash determinism across the 1 MB chunk boundary: file ≥ 2 MB hashed equals `hashlib.sha256(full_bytes)` | L-5 chunk loop |
| T-M4 | Duplicate artifact name semantics (overwrite allowed vs. rejected — owner picks) | L-4 |

Existing 20 tests reviewed against their claimed guarantees: all 20 map to asserted behaviors and none pass vacuously; two are opportunistic (L-7 noted). No test mislabels its coverage.

---

## 4. Integration-readiness verdict for Task 2

**READY, one owner decision pending.** The core is sound: atomic writes, terminal immutability, sanitized failures, append-only index, injectable paths all verified with line-referenced evidence and genuine tests. No critical or confirmed high defect blocks integration.

Recommended **before** Task 2 lands (all owner-approval-gated; none urgent):
1. Fix the stale `-2, -3` comment (`run_tracker.py:262-263`) — trivial.
2. Decide artifact-path enforcement: run-dir-relative-only (recommended) vs. current silent-absolute fall-through (M-1).
3. Add `schema_version` to the manifest while Task 2 is still pre-release (M-2).
4. Optionally add the four test specs (T-M1..T-M4) in the same change window.

Nothing further blocks: `pipelines/short.py` wiring, promotion-into-legacy-slots logic, and review linkage remain Task 2 scope per the approved plan — **not started by this agent, awaiting owner approval.**

## 5. Restrictions honored

Read-only review: zero modifications to `run_tracker.py`, `tests/test_run_tracker.py`, or any repository file. No git staging/commit/branch operations; all Qoder-owned files untouched. Only file produced: this review (docs/ + Downloads, per standing rule).

*Awaiting owner decision on the four pre-integration items; Task 2 remains blocked pending approval.*
