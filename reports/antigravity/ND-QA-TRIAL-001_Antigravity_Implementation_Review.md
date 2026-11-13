# ND-QA-TRIAL-001 — Antigravity Implementation Review

## Recommendation: Revise before accepting

### Findings

| Severity | Status | Evidence / reproduction | Impact |
|---|---|---|---|
| Medium | Verified defect | `app/visuals/chain.py:230` checks `previous in "+#"`. At the beginning of a string, `previous == ""`, and Python considers the empty string contained in every string. Repro: `_first_number("42 workers") == ""`; `classify_scene({"caption": "42 workers"})` returns `broll` instead of a numeric graphic. | Leading bare counts without a recognized unit/percent are lost, including the first number on a scene card. The 12 new tests do not cover this case. |
| Medium | Verified false positives | `classify_scene` uses substring checks at `chain.py:350`. Repros: “The first responders entered” and “A first-rate server room” become motion graphics; “A chartreuse skyline” becomes a chart. The new test at `tests/test_visual_classification_regression.py:120` explicitly expects “flowchart” to promote to a motion graphic, baking in the same substring issue. | Ordinary descriptive text can be routed to full-screen cards/charts rather than footage or diagrams. |
| Low | Coverage weakness | `tests/test_visual_classification_regression.py:176` uses `caption=[]`, which is falsy and becomes an empty string; it does not exercise a truthy malformed value. Most motion-graphic hint/list cases assert only `visual_type`. | The tests overstate malformed-input and precise classification coverage; revise with boundary/negative cases and stronger expected `scene_type`/number assertions. |

## Test quality and contract assessment

- The new file has 12 distinct test methods; loops use subtests, and the focused run passed all 12 tests and 40 subtests.
- Useful added coverage: field precedence, empty/None values, claim/list triggers, and a short planner downgrade/fallback case.
- Significant overlap with `tests/test_visual_chain.py`: ambient/numeric classification, spelled quantities, model/year exclusions, brief contracts, and graphics budgeting already have tests there. The added suite is not wholly redundant, but does not test the leading-number defect or negative substring matches.
- The planner test checks the first downgrade and its fallback chain, but does not independently establish the full stock/graphic budgets or variety behavior; existing tests provide broader coverage.
- Malformed-input checks are only partly realistic: the `dict` contract makes empty/missing/None fields reasonable, but a list-valued caption is not a robust malformed-input probe, and `classify_scene(None)` is untested.

## Reproducibility

- Focused new suite: `12 passed, 40 subtests passed`.
- Combined new + existing visual-chain suite: `62 passed, 3 failed, 51 subtests passed`.
- All three failures are existing resolution/render tests expecting local-card or gradient output; they instead receive the procedural fallback. `ffmpeg` was not found on the active Windows PATH, so these failures do not establish a classification/budget regression. Re-run those tests in an environment with the expected FFmpeg runtime before accepting their render behavior.

## Git isolation

Verified: `app/visuals/chain.py`, `tests/test_visual_classification_regression.py`, and `tests/test_visual_chain.py` are untracked in the shared `main` checkout. `git worktree list` shows the shared checkout plus a separate detached worktree, but the trial files are in the shared checkout, not that separate worktree. This establishes that the deliverable is not isolated in the current Git state; it does not establish who created the files or whether the shared-tree change was intentional. The worktree was already broadly dirty; no files were changed by this review.

## Outcome

Revise the number-prefix check and make hint matching token-/context-aware (or explicitly test and document intended substring behavior). Replace tests that encode false promotions with negative cases, add the leading-number regression, and rerun render tests with FFmpeg available. No production code or tests were modified during this review.
