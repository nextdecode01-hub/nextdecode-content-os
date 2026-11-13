# Shorts Studio — Phase 10.4 Task 2: Final Design Refinement (Revised)

**Status:** DESIGN ONLY. No source changes. No Task 2 implementation started. Owner approval required before integration.
**Prepared by:** OpenCode (primary implementation owner, Phase 10) · 2026-10-30
**Supersedes:** `reports/opencode/SECONDARY_PHASE10_4_TASK2_FINAL_DESIGN_2026-10-30.md` (previous draft)
**Evidence base:** inspected working tree — Qoder's Strict Fail-Closed live (`pipelines/short.py` `M`, `api/main.py` `M`; Qoder's own strict-fail-closed test file: 13 passed, **2 failed** against Qoder's own implementation — acceptance criteria not yet satisfied), Run Tracker hardened (`run_tracker.py` + `tests/test_run_tracker.py`, 27/27 + `test_phase2_storage_layout.py` 6/6 green).

---

## 0. Governing constraints (from owner)

- Design only. No source or test changes.
- Do not edit `pipelines/short.py` or any Qoder-owned file.
- Do not start Task 2 implementation.
- Preserve all working-tree changes; no git staging/commit/push/branch switch.
- Task 1 code (`run_tracker.py`) is mine and may be extended additively, but its terminal-state immutability (`mark_ok`/`mark_failed`) must not be weakened or rewritten.
- No automatic recovery, deletion, or rollback; manual intervention only.
- Approval and publishing safeguards unchanged; external publishing disabled; no Phase 9 audio work.

---

## 1. Revised lifecycle diagram

```
generate_run_id → outputs/runs/<run_id>/
    run_tracker.start_run(topic)                              [manifest: status=in_progress,
                                                               promotion absent]
            │
            ▼
  pipelines/short.py main() — quality gate
    quality != strong without --allow-standard
    → SystemExit 2, _record_failure("quality_gate"), NO run dir created → END

            │ quality == strong
            ▼
  run_strong_pipeline(topic, work_dir=run_dir)
    strong_pipeline.run(...)  ← every artifact lands under run_dir

    ═════════════════════════════════════════════════════════════
    SUCCESS path                                                FAILURE path
    ═════════════════════════════════════════════════════════════
    validate artifacts (video, metadata, hashes)                exception:
    │                                                           │
    ▼                                                           ▼
promotion journal: {status: "promoting"}                        mark_failed(stage, exc)
(data/promotions/<run_id>.json)                                 → manifest: failed
    │                                                             → failure.json (type+category)
    ▼                                                             → index line
metadata tmp → os.replace(legacy metadata)                       → re-raise → Qoder's _record_failure
    │                                                             → sanitized print + SystemExit(1)
    ▼                                                             → legacy slots & review packages untouched
video tmp → os.replace(legacy video)
    │
    ├─ both succeed ────────────────▶ journal: {status:"completed"}
    │                                   manifest: mark_ok()  → status=ok (terminal)
    │                                   index line
    │                                   review_bundle: package ← run_id, run_manifest_path,
    │                                            run_manifest_sha256 (additive fields)
    │                                   human approval (unchanged dual-hash + checklist)
    │
    └─ any promotion sub-step fails ─▶ journal: {status:"promoting"}
                                         manifest: still in_progress (NEVER ok)
                                         slots: possibly mixed → DETECTABLE
                                         → re-raise → SystemExit(1)
                                         → never treated as success
```

Key invariant: **manifest is marked `ok` only after promotion completes successfully.** During promotion the manifest stays `in_progress` (non-terminal), so a crash mid-promotion leaves `in_progress` + journal `promoting` — detectable, never false-success.

---

## 2. Run-state transition table

| From → To | Trigger | Terminal? | Index line? | failure.json? | Notes |
|---|---|---|---|---|---|
| (none) → `in_progress` | `start_run()` | No | No | No | Run dir created; first durable record |
| `in_progress` → `ready_for_promotion` | promotion validation passed, journal `promoting` written | **No** | No | No | Proposed additive state via promotion sub-field, not via mark_ok/mark_failed |
| `in_progress` → `ok` | `mark_ok()` — ONLY after completed promotion | **Yes** | Yes | No | Existing Task 1 logic unchanged |
| `in_progress` → `failed` | `mark_failed()` — pipeline exception | **Yes** | Yes | Yes | Existing Task 1 logic unchanged |
| `ready_for_promotion` → `ok` | `mark_ok()` after journal `completed` | **Yes** | Yes | No | Reuses existing mark_ok; guard extended to accept this non-terminal state |
| `ready_for_promotion` → `failed` | promotion failure, journal stays `promoting` | **Yes** | Yes | Yes | mark_failed from promoting state |
| `in_progress` (orphan) | crash/power loss mid-run | Unknown | No | Maybe | Post-mortem: read-only scan; never auto-resolved |

Status vocabulary: `in_progress | ready_for_promotion | ok | failed`. `ok` and `failed` are terminal and immutable per Task 1. `ready_for_promotion` is a non-terminal intermediary used only inside the promotion window.

Manifest gains one additive field (does not alter existing fields): `promotion: {"status": "idle|promoting|completed|failed", "journal_path": "...", "started_at": "...", "finished_at": null}`.

---

## 3. Promotion consistency strategy & failure matrix

### Strategy: promotion journal + cross-hash verification at approval

Joint atomicity across two files is impossible on POSIX without a transaction manager, so the design uses **detect-and-reject** instead of true atomicity:

1. Before touching any legacy slot, write journal `{run_id, status:"promoting", metadata_sha256, video_sha256, started_at}` atomically (`data/promotions/<run_id>.json`).
2. Stage metadata tmp → `os.replace()`; stage video tmp → `os.replace()`.
3. Both succeed → journal `{status:"completed", finished_at}`; then `mark_ok()`.
4. Any failure → journal stays `{status:"promoting"}` (never `completed`); manifest stays `in_progress`; legacy slots may be mixed → **detectable at approval time**.

### How consumers detect & reject incomplete/mixed promotion

The review package (written by `review_bundle.py`) carries, additively:
- `run_id`
- `run_manifest_path` (path into immutable run dir)
- `run_manifest_sha256` (sha256 of the run's manifest.json)

`approve_review.py` (existing dual-hash gate, unchanged behavior) gains one additive verification **only** when these fields are present (backward compatible with legacy packages):
1. Load run manifest from `run_manifest_path`; fail if missing/corrupt or `run_manifest_sha256` mismatch → package does not reference a valid run.
2. Require `manifest.status == "ok"` and promotion journal `status == "completed"` for that run_id → an incomplete promotion cannot be approved.
3. Cross-check: `manifest.artifacts.metadata.sha256 == sha256(current data/metadata.json)` AND `manifest.artifacts.video.sha256 == sha256(current outputs/output_short.mp4)` → mixed pair (metadata from run B, video from run A) fails because run B's manifest records run B's video hash, which won't match slot A's video.
4. Existing package-level `video_sha256`/`metadata_sha256` vs current slots remains in place (defense in depth).

A mixed pair can never be approved: either the journal isn't `completed`, or the manifest→slot hash cross-check fails, or both.

### Failure matrix

| Promotion scenario | Journal | Manifest | Legacy slots | Approvable? | Recovery |
|---|---|---|---|---|---|
| Metadata replaced, video replacement fails | `promoting` | `in_progress` | metadata=new, video=old | **No** (journal incomplete; cross-hash fails) | Manual: restore metadata from previous run dir or re-run promotion |
| Crash between replacements | `promoting` | `in_progress` | possibly mixed | **No** | Same as above — journal is post-mortem |
| Rollback itself fails | `promoting` | `in_progress` | mixed | **No** | Manual intervention only — no auto-rollback ever |
| Both succeed | `completed` | `ok` (after mark_ok) | consistent pair | **Yes** | — |

### Exception classification & exit codes

| Scenario | Handling | Exit code | Failure record |
|---|---|---|---|
| Quality-gate refusal (before run creation) | Qoder's existing path: `_record_failure("quality_gate")`, SystemExit 2, no run dir | 2 | `data/last_failure.json` (sanitized) |
| Strong pipeline ordinary exception | `mark_failed(stage=<derived>, exc=exc)` → re-raise → Qoder handler `_record_failure` + sanitized print + SystemExit(1) | 1 | run `failure.json` + `last_failure.json` |
| `SystemExit` raised inside strong pipeline | Not caught by `except Exception` (it's `BaseException`); propagates untouched | preserved | None new (Qoder's path if it reaches main) |
| `KeyboardInterrupt` | Propagates untouched | 130 | None |
| Process termination / power loss | Nothing; `in_progress` manifest survives + optional `failure.json` | — | Post-mortem via read-only scan |
| Promotion failure (after pipeline success) | Promote() raises before `mark_ok()`; manifest stays `in_progress`; journal `promoting` | 1 (non-zero) | No false `ok` ever written |

**Failure recording never replaces the original failure and never converts failure into success:** `mark_ok()` is called only from the success path after completed promotion; terminal-state immutability prevents resurrection.

---

## 4. Exact file/function changes

| File | Change type | Scope |
|---|---|---|
| `run_tracker.py` | Additive | New method `mark_ready_for_promotion(journal_path)` — sets non-terminal `ready_for_promotion` state + index line (does not touch mark_ok/mark_failed guards); optional helper `promote(...)` containing validation + journal + replace logic. Existing `mark_ok` guard extended to accept `ready_for_promotion` → `ok` (sole Task 1 adjustment; terminal immutability preserved). |
| `pipelines/short.py` | Qoder-owned — **deferred** | `main()` strong branch: instantiate tracker with `work_dir=run_dir`, validation, `promote()`, inject `run_id`/`run_manifest_path`/`run_manifest_sha256` into metadata before write. Adjacent-but-disjoint from Qoder's strict-fail-closed block. No edit until owner release. |
| `review_bundle.py` | Additive | Package gains `run_id`, `run_manifest_path`, `run_manifest_sha256` fields; existing dual-hash logic unchanged. |
| `approve_review.py` | Additive (minimal) | When package carries run identity: verify run manifest exists + sha256 match, `status=="ok"`, promotion journal `completed`, and manifest→slot cross-hash for metadata + video. Legacy packages (no run identity) verified exactly as today. |

No changes to: `app/script/pipeline.py`, render/visuals/voice, shell scripts, `n8n_runner.py`, `api/main.py`, publishing, Phase 9 audio, Phase 10.1(.1) files.

---

## 5. Minimum deterministic integration tests (specs only — not executed)

| # | Test | Asserts |
|---|---|---|
| I-1 | Successful strong run in sandboxed `SCRIPT_DIR` | run dir created; manifest `ok` **only after** promotion; index line; legacy slots byte-equal to run artifacts |
| I-2 | Strong stage failure | manifest `failed`; `failure.json` present; legacy slots byte-unchanged; Qoder's `last_failure.json` written; exit 1 |
| I-3 | Quality-gate refusal (`--quality standard`) | no run dir; `last_failure.json` present; exit 2 |
| I-4 | Promotion validation rejects missing/zero-size video | RuntimeError before any legacy slot touched |
| I-5 | Promotion validation rejects SHA-256 mismatch | RuntimeError before any legacy slot touched |
| I-6 | Metadata promoted, video promotion fails (simulated) | journal `promoting`; manifest `in_progress` (not ok); slots mixed but **rejectable** via cross-hash; exit non-zero |
| I-7 | `--allow-standard` legacy path | not promoted; `quality:"standard"` tracked separately (owner decision); legacy output unchanged |
| I-8 | Review package links run identity | package has `run_id`/`run_manifest_path`/`run_manifest_sha256`; `approve_review.py` hash checks pass; mixed pair rejected |
| I-9 | Repeated failure then success | new run dir each time; previous manifest untouched; only latest success occupies legacy slots |
| I-10 | Crash mid-promotion leaves detectable state | `in_progress` + journal `promoting`; no `ok`; read-only scan identifies it |

All hermetic: tmp `SCRIPT_DIR`, mocked research/LLM/voice/silent provider, real hashlib + known-hash dummy artifacts.

---

## 6. Compatibility and ownership/conflict map (current working-tree state)

| File | Owner | Task 2 claim | Conflict status |
|---|---|---|---|
| `pipelines/short.py` | Qoder (active strict fail-closed diff `+193` lines) | `main()` strong branch edits | ⚠️ ACTIVE — Qoder's own strict tests: **2 failed** (`test_video_quality_env_cannot_bypass_strong_pipeline`, `test_default_start_uses_the_strong_pipeline`), 13 passed. Acceptance criteria **not yet satisfied**. Edit deferred until owner release. |
| `api/main.py` | Qoder (strict semantics integrated) | none needed | none |
| `review_bundle.py` | clean | additive fields | clear |
| `approve_review.py` | clean | additive provenance check | clear |
| `run_tracker.py` | OpenCode (Task 1 complete, accepted) | `mark_ready_for_promotion` + `promote` | clear |
| `tests/test_strict_fail_closed.py` | Qoder (in-flight) | read-only reference only | none — new test files only |
| Shell scripts / n8n_runner / publishing | clean | none | none |

**Integration-readiness verdict: BLOCKED by policy, not technology.** Qoder's strict-fail-closed acceptance criteria are not yet green (2 own-test failures). Per the coordination rule, no source change to `pipelines/short.py` until Qoder's implementation is complete, re-inspected, acceptance criteria pass, and the owner explicitly approves.

---

## 7. Explicit unresolved decisions

1. Whether `--allow-standard` legacy runs appear in `data/runs/index.jsonl` (recommended: tracked separately with `quality:"standard"`, **not** promoted — promotion is for validated strong runs only).
2. `approve_review.py` additive provenance check vs. keeping approve logic untouched and relying solely on dual-hash + manifest path (recommended: additive check, backward compatible).
3. Promotion journal location `data/promotions/` vs `outputs/runs/<run_id>/promotion.json` (recommended: central `data/promotions/` for operator scan).
4. Retention policy for `outputs/runs/` (never auto-delete; future manual housekeeping tool — out of Phase 10.4 scope).
5. `mark_ok` guard extension to accept `ready_for_promotion` → `ok` — minimal Task 1 touch, or keep status=`in_progress` during promotion with additive `promotion.status` sub-field only (zero Task 1 changes; recommended).

---

**Design complete and revised. No source or test files were modified. Only this report exists as an artifact. Awaiting explicit owner approval before any Task 2 source integration.**
