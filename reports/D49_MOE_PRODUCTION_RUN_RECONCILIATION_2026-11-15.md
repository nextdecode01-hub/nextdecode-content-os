# D49 — MoE Production Run Reconciliation

**Date:** 2026-11-15  
**Workspace:** `/home/demon/shorts_studio`  
**Branch snapshot:** `main` tracking `origin/main`  
**Inspection type:** Read-only repository, manifest, source and process inspection  
**Disposition:** Findings recorded; no pipeline code, tests, services, manifests or historical runs modified.

## 1. Executive finding

The latest inspected MoE run did not fail in rendering, voice generation or asset selection. It failed before voice generation because the editorial script critic rejected an undersized script after three rewrite attempts.

The strongest available failure evidence is:

- Run: `20261115-142221-how-mixture-of-experts-models-route-toke`
- Manifest status: `failed`
- Entered stages: topic_selection, research, script, evidence, script_evidence_reconciliation
- The first four stages completed successfully.
- `script_evidence_reconciliation` failed.
- `data/last_failure.json` records: `Script did not pass the editorial critic after 3 rewrite(s): word_count: Word count 52 outside band 92-118`.
- No voice, captions, shot plan or rendered-video artifact was recorded for this run.

This is the immediate production blocker for this execution. Visual-quality remediation cannot help a run that never reaches voice or render.

## 2. Run evidence matrix

| Run ID | Manifest state | Last recorded stage | Artifact evidence | Finding |
|---|---|---|---|---|
| `20261115-142221-how-mixture-of-experts-models-route-toke` | failed | script_evidence_reconciliation — failed | research claim ledger only; no voice/video | Editorial critic rejected 52 words against 92–118 |
| `20261115-141617-how-mixture-of-experts-models-route-toke` | failed | render — failed | No finalized artifacts in manifest | Render boundary failed; exact exception not retained in per-run failure record |
| `20261115-141926-how-mixture-of-experts-ai-routes-tokens` | failed | research — ok | No finalized artifacts | Failed after research; exact cause not retained in per-run failure record |
| `20261115-141017-how-mixture-of-experts-models-route-toke` | in_progress | render — in_progress | No finalized artifacts | Stale/interrupted candidate; do not infer it is live or mutate/recover it |

The inspection found no matching active Shorts Studio pipeline/Kokoro process at the time of the process query. This is not permission to alter the in-progress manifest. Its state remains unchanged.

## 3. Source-level explanation of the latest failure

Relevant source files inspected:

- `app/script/pipeline.py`
- `app/script/studio.py`

The producer sequence in `app/script/pipeline.py` is:

1. Build the initial script.
2. Build and persist the claim ledger.
3. Detect blocking script/evidence issues.
4. If issues exist, enter `script_evidence_reconciliation`.
5. Call `_build_evidence_checked_script(...)`.
6. Only after that returns does the pipeline proceed to voice synthesis.

The reconciliation helper requests a grounded rewrite, rebuilds the claim ledger, and rejects the script if blocking evidence issues remain. The strict editorial writer can itself raise when its critic still fails after its configured rewrite count.

In `app/script/studio.py`, the 45-second profile is configured for 92–118 words. The critic rejects a script below that band. The latest retained failure confirms the final candidate contained 52 words after three rewrites.

**Confirmed:** the final candidate was too short for the selected 45-second profile and the strict critic stopped the run.

**Not yet confirmed:** why all rewrite attempts returned an undersized draft; whether the deterministic verified-MoE script path returned no usable candidate; whether the rewrite prompt/provider response handling contributed; and whether the duration/profile passed into this run was the intended product setting. These require a bounded source/test investigation, not assumptions.

## 4. Evidence quality observations

The latest run directory contains a research claim ledger. Its recorded content shows:

- Research verdict was `sufficient`.
- The captured research set included Mistral's Mixtral announcement and Hugging Face's Mixtral article.
- Some source material is dated 2023 and was marked stale for current-tense claims.
- A numeric performance claim stating 6x faster inference conflicted with a 4x figure in the Hugging Face source.
- The initial script mapping contained blocking flags for partially supported claims and at least one unmapped factual sentence.

This supports the need for evidence-bounded rewriting. It does not justify weakening the evidence gate or silently accepting unsupported narration.

## 5. Relationship to prior observability decisions

The following prior reports were read and reconciled:

- D44 — identified that earlier producer manifests lacked granular stage persistence.
- D45 — defined a candidate local producer-stage instrumentation contract; not implementation/test authority.
- D46 — explicitly left owner, architecture, security and QA dispositions outstanding; no implementation/test authority.
- D47 — proposed Package A with an exact candidate allowlist; explicitly not cleared for code or test execution.
- D48 — documented earlier research and duration failures; its earlier test results do not verify the November 15 runs.

The November 15 manifests now contain granular stages for these runs, so the D44-era statement about only aggregate stages is historical for the earlier observed manifests and must not be generalized to the current workspace. This does not establish canonical WP2 workflow execution.

The local RunTracker manifest remains distinct from canonical WP2/WP3/WP4/WP5 records. The dashboard must continue to display only persisted evidence and must not infer progress, approval, rights clearance or publishability.

## 6. Repository preservation snapshot

At inspection:

- Branch: `main...origin/main`.
- Git reported 135 changed/untracked paths.
- The existing production architecture document remained present at `docs/production/NEXTDECODE_SHORTS_STUDIO_PRODUCTION_ARCHITECTURE.md` (388 lines, 3,074 words).
- The worktree already contained extensive modified and untracked work across pipeline, autonomy, dashboard, tests, skills and reports.

No existing file was overwritten, reset, stashed, staged, cleaned or deleted. No commit or push was made.

## 7. Recommended next engineering increment

**Target:** deterministic script evidence-reconciliation failure closure.

Recommended order, after required package gates and separate test authorization:

1. Reproduce the 52-word / 92–118-word critic failure with a deterministic fixture based on the retained claim ledger.
2. Trace why the verified-MoE deterministic script candidate is not accepted, if that is indeed the fallback path taken.
3. Capture bounded rewrite-attempt diagnostics: attempt number, word count, critic issue kinds and final disposition. Do not persist raw prompts, provider responses, secrets or unrestricted exception text.
4. Ensure the rewrite prompt preserves the requested word-count band while resolving evidence flags; do not lower the critic threshold to force a pass.
5. Add deterministic regression tests for short drafts, three failed rewrites, evidence-clean recovery, and fail-closed behavior.
6. Run only the separately authorized focused tests, then proceed to a new human-reviewed production run.
7. Once a run reaches rendering, inspect the render failure from `20261115-141617` separately; do not mix it with the script failure.

Do not change visual providers, FFmpeg, Blender, Remotion, TTS providers, music/SFX, storyboard approval or publishing behavior as part of this script-gate fix.

## 8. Authorization and stop conditions

D46/D47 still record unresolved independent review and implementation/test authorization gates. This report is evidence documentation only. It does not grant:

- implementation authority for D47 Package A or any new path;
- test execution authority;
- authority to mutate/recover historical run manifests;
- production generation, provider calls, service restarts, uploads, publishing, deployment, spend, agent dispatch, commit or push.

Before code or tests, re-open the applicable M6-P/M6-AH records, confirm actual named roles and reviewer dispositions, re-inspect the dirty worktree, and record the exact approved paths and commands.

## 9. Verification statement

Read-only actions completed: report inspection, architecture document verification, manifest/failure/claim-ledger inspection, source inspection, process query and Git status snapshot.

Not performed: code edits, tests, render, production generation, API/service restart, manifest recovery, provider call, agent dispatch, publishing, commit or push.

**D49 status: RECONCILIATION COMPLETE — IMPLEMENTATION NOT CLEARED.**

## 10. Additional source trace — deterministic script fallback

A further read-only trace of `app/script/pipeline.py` and `app/script/studio.py` established:

- `_write_script_with_fallback()` attempts `build_verified_moe_script()` before invoking the general LLM script writer.
- The verified-MoE template is conditional: it requires eligible supported/qualified claims from approved source domains to contain the Mixtral entity, sparse architecture and router/two-expert mechanism, and it must pass the same editorial critic.
- The latest retained exception originated from the strict general writer's three-rewrite critic failure. Therefore the deterministic template did not produce an accepted script for this execution; control proceeded to the general writer.
- The exact template rejection condition has not yet been evaluated against the full claim ledger. It may be an evidence-eligibility or critic condition; do not assume which one.

This narrows the next investigation: explain why the evidence-bounded template is unavailable for this specific ledger, and why the general writer repeatedly returns a 52-word draft despite receiving the 92–118-word requirement. Preserve both the evidence gate and the word-count gate.
