# Phase 11 — ShotPlan Traceability: Implementation and Handover

Date: 2026-10-30 · Branch: `main` · Owner: Qoder · QA: Kilo (read-only)

## 1. Implemented

Read-only consumption of the approved ShotPlan; no renderer rewrite, no gate,
rights, approval or publishing changes.

1. **Plan artifact** — `app/script/pipeline.py` builds
   `shotplan.plan_shot_plan(script, ledger=ledger, audio_duration=duration)` from
   the same inputs used for rendering and writes `<work>/shot_plan.json`.
2. **Metadata IDs** — `shotplan.annotate_shots()` adds to every rendered shot:
   `shot_id` (`sNN`, unique + deterministic), `shot_plan_ref` (beat entry id),
   `narration_ref` (`{sentence_index, text, claim_ids}`), `subject`,
   `evidence_claim_ids`, `evidence_flags`. Metadata gains a `shot_plan` block
   (`path`, `version`, counts, coverage, evidence summary, flags).
3. **Contact-sheet tiles** — storyboard thumbnails are labelled with the shot id
   (`sNN`; the existing sanitizer renders it upper-case, `S00`…). Motion-sheet
   frames use the same id. No renderer/assembly code changed.
4. **Storyboard records** — each scene carries `shot_id` (also `scene_id`),
   `shot_plan_ref`, `subject`, `narration_ref`, `plan_claim_ids`,
   `plan_evidence_flags` alongside the existing `claim_ids`/`evidence` rows.
5. **Determinism** — annotation is pure (input list untouched), the plan is
   deterministic for equivalent input, and `scene_digest` is unchanged (plan
   fields are not part of the hash, so approvals are unaffected).

## 2. Changed files

| File | Purpose |
|---|---|
| `app/visuals/shotplan.py` | `annotate_shots()`, `plan_summary()` |
| `app/script/pipeline.py` | build/write plan, annotate shots, metadata `shot_plan` block, shots step fields |
| `app/visuals/storyboard.py` | shot ids in records, tile labels, motion-frame labels |
| `tests/test_shot_traceability.py` (new) | 10 tests |
| `reports/qoder/PHASE11_SHOTPLAN_TRACEABILITY_HANDOVER.md` (new) | this handover |

## 3. Verification evidence

Real run (same entrypoint as GEN-01, `set -o pipefail`):

```
PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m app.script.pipeline \
  --topic "NIST AI risk management framework adoption" --seconds 45 \
  --work-dir outputs/phase11_trace --out data/metadata_phase11_trace.json
```

- Exit 0; 49.7 s, 1080×1920, QA `pass`; 14 shots, 9 beats,
  `coverage.ratio = 1.0`, `uncovered = []`.
- `outputs/phase11_trace/shot_plan.json` exists; metadata `shot_plan.path`
  points to it; counts agree (14/9).
- Metadata shots: `s00…s13`, unique; every index maps to a plan ref; plan entry
  start/end equal render shot start/end (0 mismatches).
- Storyboard: 14/14 records carry `shot_id`/`shot_plan_ref`; ids equal
  `scene_id`; claim-bearing scenes: `s04 clm_e18e287f71`,
  `s06 clm_7b91655500`, `s07/s08 clm_16eeee2286, clm_1e873d5b4a`,
  `s09 clm_9b0ddeb5b6`.
- Contact sheet inspected: tiles labelled `S00…S13` (upper-case display of the
  `sNN` ids).
- Prior artifacts (`outputs/output_short.mp4`, `data/metadata.json`,
  `data/review_approved.json`) hash-identical before/after.

Tests actually run:

| Command | Result |
|---|---|
| `pytest -q tests/test_shot_traceability.py` | 10 passed |
| `pytest -q tests/test_shot_traceability.py tests/test_shot_plan.py tests/test_query_dedup.py tests/test_cutout_rights.py tests/test_storyboard.py` | 55 passed |
| `pytest -q --ignore=tests/test_strict_fail_closed.py` | 503 passed, 11 subtests |

## 4. G1 — UNRESOLVED CRITICAL BLOCKER (not production-safe)

The 20:22 and 20:35 runs rendered with `review_status=needs_review` and
`approved=false` because `STORYBOARD_GATE` defaults to `warn`
(`app/render/assembly.py` gate default; `enforce_review_gate` default `warn`).
Human approval is therefore not enforced before protected rendering.

Narrow fix proposal (needs owner approval; not implemented here):

| File | Change |
|---|---|
| `app/visuals/storyboard.py` | `enforce_review_gate` default `require`; `warn` only when explicitly requested |
| `app/render/assembly.py` | `STORYBOARD_GATE` default `require`; `off` only via explicit dev opt-in, never implicit |
| `pipelines/short.py`, `api/main.py` | do not set the env to `warn` (OpenCode-owned; coordinate) |
| `tests/test_storyboard.py` | default blocks `needs_review`/`blocked`; valid approval+hash passes; `warn`/`off` require explicit opt-in (replaces `test_warn_and_off_do_not_raise`) |
| `tests/test_render_qa.py` | gate block writes no MP4 and preserves the previous output file |

Prerequisite: confirm contact-sheet digest determinism and add approve-then-render
fixtures for the pipeline tests.

## 5. Editorial critic inconsistency (recorded, not redesigned)

Band for `--seconds 45` is 96–118 words.

| Attempt | Result |
|---|---|
| 20:13 | Failed after 3 rewrites: `word_count 120 outside band 96-118`, `hook is not the first sentence` — no output |
| 20:18 | Passed, 114 words, 0 rewrites |
| 20:31 | Passed, 103 words, 0 rewrites |

Same topic, same settings, LLM variance at the band edge. Not changed in this task.

## 6. Shell failure propagation (verified)

```
(./venv/bin/python -c "import sys; sys.exit(3)" | tee /dev/null); echo $?   # 0
set -o pipefail; (./venv/bin/python -c "import sys; sys.exit(3)" | tee /dev/null); echo $?   # 3
```

The 20:13 run failed but a `tee` pipeline reported exit 0. Schedulers must use
`set -o pipefail`/`PIPESTATUS` or redirect instead of piping to `tee`.

## 7. Kilo QA packet (read-only)

Review files: `app/visuals/shotplan.py` (`annotate_shots`, `plan_summary`),
`app/script/pipeline.py` (shots → plan → annotate → metadata),
`app/visuals/storyboard.py` (record fields, tile labels),
`tests/test_shot_traceability.py`.

Commands:

```
PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q tests/test_shot_traceability.py
PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q tests/test_storyboard.py tests/test_cutout_rights.py tests/test_approval_integrity.py
PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q --ignore=tests/test_strict_fail_closed.py
```

Artifacts to inspect: `outputs/phase11_trace/{shot_plan.json,output_short.mp4}`,
`outputs/phase11_trace/shots/storyboard/{storyboard.json,contact_sheet.jpg}`,
`data/metadata_phase11_trace.json`.

Constraints: no edits, no git stage/commit/reset/stash, do not execute
`pipelines/short.py` or `api/main.py` fail-closed diffs (OpenCode-owned), do not
publish. Report PASS/FAIL per test with exact output; file defects to Qoder.

## 8. Git

Branch `main`, no stage/commit/push/reset/stash performed; all pre-existing WIP
preserved. New untracked: `tests/test_shot_traceability.py`, `reports/qoder/PHASE11_SHOTPLAN_TRACEABILITY_HANDOVER.md`,
`outputs/phase11_trace/`, `data/metadata_phase11_trace.json`.
