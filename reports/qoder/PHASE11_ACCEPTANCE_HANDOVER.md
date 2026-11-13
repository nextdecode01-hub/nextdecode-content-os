# Phase 11 — Acceptance Test Results and Engineering Handover

Date: 2026-10-30 · Branch: `main` · Ownership: Qoder (I1/I2 + validation only)

## 1. What was implemented

- **I1 Structured Shot Planning** — `app/visuals/beats.py`, `app/visuals/shotplan.py`
  (beat analysis, deterministic shot IDs, narration/evidence linkage, coverage and
  evidence flags). Timing delegates to `motion_director.plan_shots` (parity tested).
- **I2 Global Visual Query De-duplication** — `app/visuals/chain.py`
  (`_query_key`, `_dedupe_query`, `MAX_QUERY_REUSE = 2`, recorded `query_reuse`
  decisions, rotation to an unused variant, planner returns `query_use` /
  `query_switches`).
- **Upload-safety test suite** — `tests/test_upload_safety.py` (mocked YouTube +
  social gates).

Nothing outside I1/I2 was edited. `pipelines/short.py`, `api/main.py`,
`app/script/pipeline.py`, `app/research/*`, Phase 9 audio and OpenCode-owned
Phase 10 files were not modified in this session.

## 2. Changed files

| File | Purpose |
|---|---|
| `app/visuals/beats.py` (new) | Narration beat extraction: subject/action/context/emotion, evidence demand |
| `app/visuals/shotplan.py` (new) | ShotPlan v1: shot_id, narration_ref, subject, visual_objective, evidence refs, rationale, coverage/validity flags |
| `app/visuals/chain.py` (mod) | Global query normalisation, reuse cap, switch recording |
| `tests/test_shot_plan.py` (new) | 13 tests (I1-01..I1-05) |
| `tests/test_query_dedup.py` (new) | 6 tests (I2-01..I2-05) |
| `tests/test_upload_safety.py` (new) | 10 tests (UPL-01/02) |

## 3. Direct generation (GEN-01..04)

Entry point traced: `python -m app.script.pipeline --topic ... --seconds 45
--work-dir outputs/phase11_direct --out data/metadata_phase11_direct.json`
(this is what `pipelines/short.py::run_strong_pipeline` wraps; the short.py and
api/main.py fail-closed diffs remain owned by OpenCode and were **not executed**).

### GEN-01 — PASS

- Command: `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m app.script.pipeline --topic "NIST AI risk management framework adoption" --seconds 45 --work-dir outputs/phase11_direct --out data/metadata_phase11_direct.json` (with `set -o pipefail`), exit 0.
- MP4: `outputs/phase11_direct/output_short.mp4`, 19,634,520 bytes, 53.2 s,
  1080×1920, h264 30 fps, AAC 44.1 kHz mono; sha256
  `af1831c6949de97c409f230d97089eeb674e3603e55bdd0faa24a4f0a55c4b02`.
- QA: `status=pass`; 14 shots; 10 claims; 0 fallback scenes; stock cap 6/6.

### GEN-02 — PASS (with gap)

- `metadata.video_path` exists and is the file above; metadata
  `ledger_sha256` = `a93f0b8f…` equals the ledger file and the storyboard;
  `script_sha256` matches across all three; storyboard JSON and contact sheet
  exist; `scene_digest=d44c2da0…`.
- Review package: `review_status=needs_review`, `approved=false`, 13 reasons
  (lexical stock matches, weak/outdated claim `clm_a3c949097d`).
- Gap: there is no UUID `run_id`; identity is the work-dir + hashes.

### GEN-03 — PARTIAL

- Layer verified: strong pipeline raises and exits non-zero with no success JSON
  and no `--out` file (controlled dead-proxy run → `RuntimeError: No research
  candidates were discovered`, exit 1; and a genuine first attempt that failed
  the editorial critic after 3 rewrites, exit 1).
- Orchestration layer (`pipelines/short.py`) that converts this into exit 1 +
  sanitised `data/last_failure.json` is **unverified** (OpenCode-owned, not run).
- Shell risk observed: `python … | tee log` reported success for a failed run;
  exit propagation requires `pipefail`/`PIPESTATUS`.

### GEN-04 — PASS

`outputs/output_short.mp4`, `data/metadata.json`, `data/review_approved.json`
hashes unchanged after both the failed attempts and the successful run.

## 4. Gates

- Approval integrity + rights: `tests/test_approval_integrity.py`,
  `tests/test_cutout_rights.py`, `tests/test_storyboard.py` → **33 passed**
  (REG-01/02 PASS).
- Rendering proceeded while the storyboard was `needs_review`
  (`STORYBOARD_GATE` default `warn`). This is an **unresolved critical blocker**
  (G1): production rendering is not gated by human approval. Fix proposal and
  tests: `reports/qoder/PHASE11_SHOTPLAN_TRACEABILITY_HANDOVER.md` §4. Not implemented.

## 5. Upload validation

- UPL-01 **PASS** — request body, completion loop, response id, fingerprint and
  duplicate-ledger checks (mocked, no network).
- UPL-02 **PASS** — quota error propagates without success; missing token and
  invalid ledger refuse before network; missing/stale approval blocks before any
  adapter.
- UPL-03 **BLOCKED** — no approved non-public destination exists;
  `app/publish/youtube_upload.py` hardcodes `privacyStatus: "public"` and offers
  no dry-run. No upload was attempted.

## 6. Tests actually executed

| Command | Result |
|---|---|
| `pytest -q tests/test_shot_plan.py tests/test_query_dedup.py` | 19 passed |
| `pytest -q tests/test_visual_quality.py tests/test_upload_safety.py` (+I1/I2) | 35 passed |
| `pytest -q tests/test_approval_integrity.py tests/test_cutout_rights.py tests/test_storyboard.py` | 33 passed |
| full suite `--ignore=tests/test_strict_fail_closed.py` (earlier this session) | 483 passed |

## 7. Acceptance matrix

| ID | Result | Evidence |
|---|---|---|
| I1-01..I1-05 | PASS | `tests/test_shot_plan.py` |
| I2-01..I2-05 | PASS | `tests/test_query_dedup.py` |
| REG-01/REG-02 | PASS | approval/rights/storyboard suites |
| GEN-01 | PASS | 53.2 s MP4, QA pass |
| GEN-02 | PASS (no UUID run_id) | hash agreement, storyboard/contact sheet |
| GEN-03 | PARTIAL | layer verified; short.py orchestration unverified |
| GEN-04 | PASS | byte-identical prior artifacts |
| UPL-01 | PASS | mocked upload tests |
| UPL-02 | PASS | failure/approval tests |
| UPL-03 | BLOCKED | only public destination exists |

## 8. Safeguards

Strong Pipeline mandatory in production (behaviour exists; verification pending
OpenCode). No fallback occurred in either failed run. No publishing invoked;
external publishing remains disabled. Approval/rights gates unchanged. No
stage, commit, push, reset or stash was performed; all WIP preserved.

## 9. Known gaps / blockers

1. `STORYBOARD_GATE` renders on `needs_review` (G1, needs approval).
2. Fail-closed orchestration (`pipelines/short.py`, `api/main.py`) unrun.
3. No run UUID; provenance relies on hashes + work dir.
4. Shell pipelines without `pipefail` mask failures.
5. First generation attempt failed the editorial critic (band 96–118 words,
   hook position); retry passed at 114 words — critic flakiness is real.
6. Uploader has no non-public destination or dry-run mode.

## 10. Recommended next slice

**Wire ShotPlan into the render/review outputs for narration → shot → asset
traceability** (read-only consumption, no renderer rewrite). Files:
`app/script/pipeline.py` (write `shot_plan.json`, embed `shot_id` in metadata),
`app/render/assembly.py` (label contact-sheet tiles with `shot_id`),
`app/visuals/storyboard.py` (carry `shot_id`/`evidence.claim_ids` into scene
records). Acceptance: every metadata shot has a stable `shot_id` that resolves
to the plan and its evidence refs; review package labels match; deterministic
across runs; no gate/rights changes. Requires owner approval before start.
