# Shorts Studio — Phase 10.4 Task 2: Final Design Refinement

**Status:** DESIGN ONLY. No source changes. No Task 2 implementation started. Owner approval required before integration.
**Prepared by:** OpenCode (primary implementation owner, Phase 10) · 2026-10-30
**Based on:** inspected working-tree state — Qoder's Strict Fail-Closed is live (`pipelines/short.py` `M`, `api/main.py` `M`; strict fail-closed tests exist but do not complete within polling window), Run Tracker core hardened (`run_tracker.py` + `tests/test_run_tracker.py`, 27/27 + 6/6 green).

---

## 1. Updated lifecycle diagram

```
                          generate_run_id → outputs/runs/<run_id>/
                              │ run_tracker.start_run()       [manifest: in_progress]
                              ▼
                        pipelines/short.py main()
                          quality gate (strong-only)
                              │ fail → SystemExit 2, last_failure.json,
                              │ NO run dir created — go to END (quality_gate)
                              ▼
                      run_strong_pipeline(topic, work_dir=run_dir)
                          strong_pipeline.run(work_dir=run_dir)   ← all artifacts land here
                              │ stage exception (Ordinary / SystemExit /
                              │ KeyboardInterrupt / power-loss)
                              ▼
   success                run_tracker.tracker.mark_ok()
                              │
                              ▼              pre-promotion validation (video / metadata / hashes)
                              ▼
                    atomic promote (metadata tmp+replace, video copy2 tmp+replace)
                              │
                              ▼              failure at any promotion sub-step
                         legacy slots refreshed
                              │
                              ▼              legacy output pair now references this run only
                    review_bundle.py → package run_id + run_manifest_path (+manifest sha256)
                              │
                              ▼              human approval (unchanged hash + checklist)
                         publish (20:00 IST window, approval_integrity)

   failure                run_tracker.tracker.mark_failed(stage, exc)
                              │
                              ▼              manifest: failed  failure.json (type/category only)
                              ▼              last_failure.json (Qoder: sanitized message)
                              ▼              re-raise → main() SystemExit(1)
                              ▼              legacy slots & review packages preserved
END
```

**Key invariant:** legacy slots (`data/metadata.json`, `outputs/output_short.mp4`) are touched **only** by a validated successful promotion. Every other path (refusal, strong failure, SystemExit, KeyboardInterrupt, power loss) leaves them exactly as they were.

---

## 2. Exact functions and file changes

### New file: `run_tracker.py` additions (Task 1 already landed)

Add one helper to the existing module:

```python
def promote(run_dir: Path | str,
            legacy_metadata: Path | str,
            legacy_video: Path | str,
            manifest: dict | None = None) -> dict:
    """
    Atomically promote validated artifacts from a successful run into the
    legacy output slots.  Metadata is replaced via same-dir os.replace();
    video is staged via copy2 into the slot directory then os.replace().
    Returns promotion record.  Raises RuntimeError on validation failure
    BEFORE any legacy file is touched.
    """
```

The `promote()` function performs:
1. Load run manifest from `run_dir/manifest.json` (raises if `status != "ok"`).
2. Validate required artifacts exist: `metadata.json`, `output_short.mp4` (non-empty).
3. Re-verify recorded SHA-256 against actual files on disk.
4. Stage `metadata.json` → `legacy_metadata.tmp` → `os.replace()`.
5. Stage `output_short.mp4` → `legacy_video.tmp` → `os.replace()`.
6. Return `{run_id, promoted_at, metadata_sha256, video_sha256}`.

No file is deleted, renamed, or moved outside this helper; old run dirs remain.

### Modified file: `pipelines/short.py` (Qoder-owned; edit scope discussed below)

Only `main()` strong branch, minimally:

```python
if args.quality == "strong":
    track = run_tracker.start_run(args.topic)   # injectable runs_root/index_path
    try:
        data = run_strong_pipeline(args.topic, track.run_dir, track.manifest_path)
        track.mark_ok()
        validation...
        promotion = run_tracker.promote(track.run_dir, metadata_file, output_mp4)
        data["run_id"] = track.run_id
        data["run_manifest_path"] = str(...)
        data["run_manifest_sha256"] = ...
        ... success payload unchanged ...
        return
    except BaseException as exc:
        track.mark_failed(stage=<derived>, exc=exc)
        Qoder's existing except behavior: _record_failure + sanitized print + SystemExit(1)
```

- `work_dir=track.run_dir` already flows into every strong artifact (verified: `app/script/pipeline.py:262`, `shots.py:60`, `storyboard.py:312`, `chain.py` intermediates).
- `run_strong_pipeline` (`:275`) currently writes metadata to `metadata_file` (legacy slot) — change to write into `run_dir` instead; legacy slot receives only via `promote()`.
- Exception derivation: ordinary exception → its type; `SystemExit` → `SystemExit` (code preserved by Qoder's handler); `KeyboardInterrupt` → re-raised without marking failed (no failure record for operator abort); power loss → nothing (no process survives; `in_progress` manifest + optional `failure.json` are the post-mortem record).

### Modified file: `review_bundle.py` (additive only)

Read `run_id`, `run_manifest_path`, `run_manifest_sha256` from metadata and copy them into the review package. Existing dual-hash verification (`video_sha256`/`metadata_sha256` against legacy slots) remains exactly as-is. Package continues to reference legacy slots **plus** exact run identity — so even after a later run becomes latest, this package stays valid because its files are immutable (run dirs are never overwritten).

---

## 3. Failure-state matrix

| Event | Manifest state | `failure.json` | Legacy slots | Review package | Exit code |
|---|---|---|---|---|---|
| Quality-gate refusal | never created | absent | unchanged | untouched | 2 |
| Strong stage exception | `failed` | present (type+category) | unchanged | untouched | 1 |
| Promotion validation fails | `ok` (pre-promotion) | absent | unchanged | untouched | 1 (non-zero) |
| Metadata promoted, video promotion fails | `ok` | absent | **metadata new, video old** → see B.4 | stale | 1 |
| Process stops during promotion | `ok` | absent | possibly mixed pair | stale | — (crash) |
| KeyboardInterrupt | `in_progress` | absent | unchanged | untouched | 130 |
| Power loss | `in_progress` | maybe (if crash mid-mark_failed) | unchanged | untouched | — |

Invariant never violated: **no failed process converts to success; original failure is never replaced.**

---

## 4. Promotion consistency (failure-safe strategy)

Individually atomic metadata/video replacement is **not jointly transactional**. Smallest reliable fix: a **promotion journal** written before any legacy file is touched:

```
data/promotions/YYYYMMDD-HHMMSS-<run_id>.json
{
  "run_id": "...",
  "stage": "promoting" | "completed" | "rolled_back",
  "metadata_sha256": "...",
  "video_sha256": "...",
  "started_at": "...",
  "finished_at": null
}
```

Sequence:
1. Write journal `{status: "promoting"}` (atomic write).
2. Stage metadata tmp → replace; stage video tmp → replace.
3. If both succeed: write journal `{status: "completed", finished_at}`.
4. If step 2 fails mid-way: roll back by restoring from the **previous run dir** (still intact — old run dirs are never deleted) or leave mixed pair and let `approve_review.py`'s existing hash check reject the package at approval time. The journal marks `{status: "rolled_back", finished_at}`.
5. Startup recovery (manual operator tool, out of Phase 10.4 implementation): scan `data/promotions/*.json` for `promoting` without `completed` → flag as "promotion interrupted; inspect legacy slots manually."

This keeps every existing consumer unchanged: `review_bundle.py`, `approve_review.py`, `api/main.py` all read legacy slots exactly as today.

---

## 5. Artifact validation (pre-promotion)

Before `os.replace()` on either legacy slot:

| Check | Implementation | Failure action |
|---|---|---|
| Run manifest `status == "ok"` | load manifest | RuntimeError before touching anything |
| `output_short.mp4` exists, non-empty | `path.is_file() and stat().st_size > 0` | RuntimeError |
| `metadata.json` exists, parses | `json.loads` | RuntimeError |
| Recorded artifact SHA-256 matches actual | `_sha256_file()` vs manifest entry | RuntimeError |
| Metadata corresponds to this run | `metadata["run_id"] == run_id` | RuntimeError |

Hash verification is the integrity gate; size>0 guards zero-byte renders. Any failure aborts promotion with legacy slots untouched and exit code 1.

---

## 6. Review package consistency

- Package records `run_id`, `run_manifest_path`, `run_manifest_sha256` in addition to existing dual-hash checks.
- Run dirs are **never overwritten or deleted**, so the manifest a package points at stays byte-identical forever.
- If another run becomes the latest output, the older package remains valid because approval hashes (`approve_review.py:27-34`) still verify against the legacy slots at approval time — and `approve_review.py` already fails loudly when files changed (`Review package does not match...`). Adding run identity simply lets an auditor trace *which run* the approved slots came from.
- No change to approval window, digest semantics, or publishing safeguards.

---

## 7. Failure recovery (clarified, no automatic recovery)

| If | Result |
|---|---|
| Pipeline succeeds but promotion fails | Manifest says `ok`, journal says `promoting`, legacy slots hold previous run. Operator manually inspects journal + slots; re-run promotion manually or treat latest run as failed. |
| Metadata promoted, video fails | Mixed pair possible; journal `promoting` without `completed`. `approve_review.py` hash check will reject stale pair at approval. Manual repair: restore metadata from previous run dir or re-promote. |
| Process stops during promotion | Same as above — journal is the post-mortem. |
| Review package already exists for previous run | Unchanged — new run creates a new dated package in `data/review_queue/`; old package remains valid (immutable run artifacts). |

No automatic recovery, deletion, or rollback is implemented. Recovery tooling is a future owner decision.

---

## 8. Exception & interruption lifecycle (specified)

| Type | Handling | Why |
|---|---|---|
| Ordinary `Exception` | `mark_failed(stage=<derived>, exc=exc)` → manifest `failed` + `failure.json` (type+category only) + index line → re-raise → Qoder's handler writes `last_failure.json` + sanitized print + `SystemExit(1)` | Failure recorded once, never replaced |
| `SystemExit` | Not marked as failed (no `failure.json`); re-raised untouched | Quality-gate refusal (`SystemExit 2`) is a policy refusal, not a pipeline failure; `--strict`/argparse exits unchanged |
| `KeyboardInterrupt` | Re-raised without marking failed | Operator abort is not a failure to record |
| Process termination / power loss | Nothing to record post-mortem; on next startup, any `in_progress` manifest without `failure.json` = interrupted/unknown; with `failure.json` = finalization incomplete | Identifiable via read-only scan of `outputs/runs/*` + `data/runs/index.jsonl` |

Failure recording must never convert failure into success: `mark_ok()` and `mark_failed()` both enforce terminal-state immutability (verified Task 1).

---

## 9. Minimum deterministic integration tests (specs only)

| # | Test | Asserts |
|---|---|---|
| I-1 | Successful strong run in sandboxed `SCRIPT_DIR` | run dir created, manifest `ok`, index line appended, legacy slots byte-equal to run artifacts |
| I-2 | Strong stage failure | manifest `failed`, `failure.json` present, legacy slots byte-unchanged, `last_failure.json` written by Qoder's path, exit 1 |
| I-3 | Quality-gate refusal (`--quality standard`) | no run dir created, `last_failure.json` present, exit 2 |
| I-4 | Promotion validation rejects missing/zero-size video | RuntimeError before any legacy slot touched |
| I-5 | Promotion validation rejects hash mismatch | RuntimeError before any legacy slot touched |
| I-6 | `--allow-standard` legacy path | not instrumented by tracker (owner decision: tracked with `quality:"standard"` but not promoted), legacy output unchanged |
| I-7 | Review package links run identity | package contains `run_id` + `run_manifest_path` + manifest sha256; `approve_review.py` hash checks pass |
| I-8 | Repeated failure then success | new run dir each time, previous manifest untouched, only latest success occupies legacy slots |

All hermetic: tmp `SCRIPT_DIR`, mocked research/LLM/voice/silent provider, real hashlib + ffmpeg-free artifact checks (write dummy files with known hashes).

---

## 9. Ownership and conflict map (current working-tree state)

| File | Owner | Task 2 claim | Conflict status |
|---|---|---|---|
| `pipelines/short.py` | Qoder (active strict fail-closed diff `+193` lines) | `main()` strong branch: start_run/mark_ok/mark_failed/promote | ⚠️ ACTIVE — edit is adjacent-but-disjoint to Qoder's strict block; coordination required before any source change |
| `api/main.py` | Qoder (already integrates strict semantics) | none needed | none |
| `review_bundle.py` | clean | additive run identity fields | clear |
| `run_tracker.py` | OpenCode (Task 1 complete) | `promote()` helper | clear |
| `tests/test_strict_fail_closed.py` | Qoder (in-flight; test run did not complete in polling window) | read-only integration tests reference behavior | none — new test files only |
| Shell scripts, n8n_runner, approval/publishing | clean | none | none |

Integration implementation is **deferred** until Qoder's strict-fail-closed diff is accepted by the owner and these files are released. Design is complete today.

---

## 10. Explicit unresolved decisions

1. Whether `--allow-standard` legacy runs are recorded in `data/runs/index.jsonl` at all (recommended: tracked separately with `quality:"standard"`, **not** promoted — promotion is for validated strong runs only).
2. Whether `review_bundle.py` should read `metadata.json` from the run dir instead of legacy slots (recommended: keep legacy-slot read for now; additive run identity is sufficient).
3. Promotion-journal location and rollback tooling (recommended: `data/promotions/` + manual operator scan only; automatic rollback is out of scope).
4. Retention policy for `outputs/runs/` (never auto-delete; future manual housekeeping tool).
5. `record_stage` free-string status vs closed enum (accepted as-is; low risk).

---

**Design complete. No source files were modified. Only `run_tracker.py`, `tests/test_run_tracker.py`, and this report exist as this agent's artifacts. Awaiting explicit owner approval before any Task 2 source integration.**
