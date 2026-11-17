# NEXTDECODE Render and Evidence Remediation — 2026-11-16

## Scope

Remediation was performed against the existing `/home/demon/shorts_studio` architecture. Existing working-tree changes, untracked files, historical run artifacts, provider architecture, rights gates, publishing governance, and the local-first/free-first operating model were preserved. No reset, stash, cleanup, commit, push, deploy, public publishing, paid provider call, or credential inspection was performed.

## Corrected findings from run `20261116-073137-can-ai-agents-conduct-open-ended-ai-rese`

- The manifest records the `render` stage as failed and the run-level failure as `RuntimeError` / `unknown`.
- Voice, captions, shot plan, and storyboard artifacts exist. The render stage was entered, but the pre-render storyboard gate runs before `execute_clip()` and FFmpeg clip rendering.
- `storyboard.json` had `review_status=needs_review`, 11 semantic-review flags, and the shot plan carried four `evidence_missing` beat flags plus one `uncovered_beat`.
- Therefore this run is not evidence that FFmpeg encoding began.
- The separate short-script run `20261115-142221...` remains a distinct run and is not conflated with this render failure.

## Implemented changes

1. **Shot-plan integrity is now enforced by the storyboard gate.**
   - Scene review reasons now include shot-plan evidence flags.
   - `evidence_missing`, `evidence_unsupported_status`, `evidence_reference_invalid`, and `uncovered_beat` make the storyboard `blocked`.
   - Blocked storyboards cannot be human-approved. This prevents visual approval from bypassing missing evidence or uncovered narration.

2. **Human visual approval now has a consistent final-QA meaning.**
   - When the exact storyboard approval validates against the contact sheet, script hash, ledger hash, and scene digest, resolved assets are marked `human_reviewed` for final QA.
   - The original `semantic_review` signal is retained for audit.
   - Strict visual QA no longer rejects an asset solely because its semantic-review flag remains set after valid human approval. Low confidence, low-light, duplicate, and other strict QA failures remain enforced.

3. **FFmpeg failure diagnostics are retained safely.**
   - `_run()` now raises a bounded error with executable, exit/timeout status, and a stderr/stdout excerpt; it does not include the full command or private input path.
   - `RunTracker.mark_failed()` accepts a bounded diagnostic only when supplied by a caller.
   - The strong-pipeline failure path passes `_redact(exc)` into the per-run manifest and `failure.json`. The stable error type/category remain present.

4. **Script punctuation corruption is repaired before voice and captions.**
   - `_normalize_script_punctuation()` restores common possessive/contraction forms such as `DeepMind?s` → `DeepMind's` and separates malformed question boundaries such as `research?or` → `research? or`.
   - Word count is recalculated from the normalized spoken text.
   - Both deterministic and model-writer outputs pass through the normalizer.

5. **Factual-sentence classification is more complete and aligned with shot planning.**
   - The evidence classifier recognizes capability/action phrasing such as `is designed`, `proposes`, `described`, `accelerates`, `generates`, and `refines`, including workflow/system/tool/agent subjects.
   - A publication attribution such as `Nature has described...` is recognized as factual.
   - An opening question is not automatically treated as an asserted factual claim by narration-beat planning.
   - Evidence thresholds were not lowered and missing factual support remains a blocking issue.

## Verification

- Focused regression command (using the isolated WSL test environment):
  `pytest tests/test_evidence_script.py tests/test_shot_plan.py tests/test_storyboard.py tests/test_render_qa.py tests/test_run_tracker.py tests/test_strong_pipeline.py tests/test_visual_chain.py tests/test_visual_asset_qa.py tests/test_multi_model_ai.py -q`
- Result: **245 passed, 1 skipped, 22 subtests passed**.
- Python compile checks passed for the modified production modules.
- `git diff --check` passed; Git emitted only a CRLF/LF working-copy warning for `tests/test_storyboard.py`.
- The repository's existing `.venv` is a Windows-style venv without a WSL `bin/python`. A separate environment was created outside the repository at `/home/demon/.venvs/shorts-studio` with system site packages, and the already-declared `google-genai` dependency was installed there. No repository dependency manifest was changed.

## Remaining blockers — do not mark release-ready

1. **Visual semantic QA is still not automatically qualified.** The `visual_qa` model route remains disabled because the configured vision model has not passed project contact-sheet and sampled-video-frame qualification. Do not enable it just to make the pipeline pass. External assets without a successful visual review still require human review.
2. **Human approval/resume workflow needs an end-to-end acceptance test.** The approval binding and QA semantics are corrected, but a safe operator workflow that pauses on a generated storyboard, accepts approval, and resumes the same run without repeating paid/provider work has not been demonstrated here.
3. **No new controlled full production E2E was run.** No live provider calls were made. The latest historical run remains failed and must not be relabelled as fixed. The new evidence checks are expected to stop unsupported factual beats earlier, which is intentional fail-closed behaviour.
4. **Visual relevance still needs a dedicated acceptance pass** using real contact sheets and sampled frames across representative topics/providers. Metadata overlap alone is not proof of semantic relevance.

## Governance

No publishing action was taken. Human approval before publishing remains required; automatic public publishing remains disabled. The project is **not release-ready** until the remaining blockers above are closed with evidence.
