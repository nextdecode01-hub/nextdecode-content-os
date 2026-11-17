# M1 Automated Edit Director — Implementation & Acceptance Report

**Date:** 2026-11-15  
**Workspace:** `/home/demon/shorts_studio`  
**Scope:** Existing FFmpeg renderer, EDL, timeline and local QA  
**Disposition:** M1.1–M1.6 implementation complete; real-footage creative acceptance remains blocked.

## 1. Owner intent and boundaries

The goal is a 45–60 second NEXTDECODE Short that feels editorially directed, not a collection of downloaded assets and generic cards. The implementation remains inside the existing pipeline and retains FFmpeg as the executor. This report does not authorize public publishing, deployment, paid services, or changes to publishing/security governance.

The current worktree contains extensive parallel and agent changes. Those changes were preserved. This pass did not edit dashboard, asset selection/provider integrations, audio/script/voice implementation, or publishing/security/governance.

## 2. Automated Edit Director delivered

### M1.1 — Renderer-independent EDL
- Added `app/render/edit_director.py` and `tests/test_edit_director.py`.
- Added versioned `nextdecode.edl.v1` with integer frame allocations, source ranges, framing, motion, transitions, narration cue and editorial rationale.
- EDL is authored before rendering and persisted atomically.

### M1.2 — EDL execution
- Supports hard cuts and planned opening/closing edge fades.
- Rejects unsupported interior fades/transitions rather than silently pretending to execute them.
- Trims source video to the selected EDL source range before the visual renderer.
- Executes fill/contain framing and fade edges through the existing render stack.
- Prevents visual-QA and EDL execution failures from being hidden by fallback rendering.

### M1.3 — Deterministic source segment choice
- Explicit shot-level source in/out overrides take priority.
- Optional supplied segment candidates are ranked deterministically using their provided score.
- Otherwise selects deterministic windows and avoids overlapping adjacent use of the same source when possible.
- Does not claim semantic relevance when no semantic score exists.

### M1.4 — Source-segment QA
- Samples start/middle/end frames with FFmpeg frame hashes.
- Records black and frozen intervals and maps them to the selected source segment.
- Rejects segments that are effectively unusable; retains warnings/evidence for non-fatal issues.

### M1.5 — Rendered-clip QA and EDL persistence
- Uses ffprobe to validate each rendered clip's stream, dimensions and duration against its EDL allocation.
- Persists per-clip execution QA back into the authoritative EDL after rendering.
- Carries source and execution QA evidence into the existing `nextdecode.timeline.v1` manifest.
- Keeps dry-run fixture exceptions explicit; production execution remains fail-closed.

### M1.6 — Final delivery QA
- Validates EDL/timeline clip counts, IDs, contiguous frame boundaries and total frames.
- Validates final MP4 video/audio stream presence, canvas dimensions, duration, frame rate, encoded frame count and audio duration.
- Rejects interior black intervals while allowing expected opening/closing fade-to-black.
- Reports freeze intervals only over source-video ranges; intentional still-image and generated-card intervals are excluded from the freeze gate.
- Stores `delivery_qa` in the timeline manifest and assembly result.
- Added a reproducible 45-second FFmpeg integration fixture with three picture segments, narration audio and actual encoded opening/closing fades.

## 3. Verification performed

Focused command:

```bash
python3 -m pytest -q \
  tests/test_edit_director.py \
  tests/test_editorial_timeline.py \
  tests/test_motion.py \
  tests/test_shot_plan.py \
  tests/test_render_qa.py
```

Final focused regression after the validator strengthening: **93 passed in 66.75s**.

Full repository suite using the project virtual environment (`venv/bin/python -m pytest -q`): **1,231 passed, 12 skipped, 71 subtests passed in 145.07s**. The initial system-interpreter attempt could not collect API/Postgres tests because system Python lacks FastAPI/psycopg; no packages were installed. The project venv run collected and completed the full suite successfully.

Python compilation and scoped `git diff --check` passed after the final validator changes.

## 4. Existing local footage and storyboard review

No new production render was initiated. Existing run artifacts were inspected offline.

### Run `20261115-153459-how-mixture-of-experts-models-route-toke`
- Runtime target: 49.425 seconds; 14 planned shots across 9 narration beats.
- Research, script, evidence, voice, captions and shot planning stages completed.
- Render stage failed; the retained manifest only records a generic `RuntimeError` at `strong_pipeline`, category `unknown`. The exact render exception is not retained in `failure.json`.
- No final video artifact was recorded.
- Storyboard status: `needs_review`; `approved=false`.
- Storyboard summary: 10 high relevance, 4 none; 4 fallback scenes; 14 scenes total.
- Visual contact sheet shows repeated MoE routing diagrams/cards and four gradient-caption fallback scenes. It is not a human-approved storyboard.

### Asset QA evidence for that run
- Four downloaded Pixabay videos were inspected offline.
- No missing assets and no duration shortfalls.
- Adjacent exact duplicate pairs: s02/s03 and s12/s13; both pairs had dHash distance 0.
- Provider title, description, tags, source URL, licence and credit metadata were absent from the persisted rejected-candidate records. Those assets cannot be considered publish-ready or provenance-complete on this evidence.
- The storyboard records Vision review HTTP 429 for several candidates; unavailability was not treated as approval.

### Existing completed video reviewed
- Existing file: `outputs/runs/20261115-043229-how-ai-models-activate-a-few-experts-to/output_short.mp4`.
- ffprobe: 1080×1920, 30 fps, 49.1 seconds, video and audio streams both 49.1 seconds.
- Contact sheet generated at `outputs/qa_review_20261115/existing_delivery_contact_sheet.jpg`.
- Visual review shows a technically coherent MoE diagram/card sequence, but repeated routing diagrams and gradient text-only slides dominate. It does not yet meet the intended cinematic/hybrid editorial bar.
- This is a historical completed delivery, not the failed 15:34 run and not proof that the latest asset-selection changes are working end-to-end.

## 5. Acceptance decision

**Technical EDL implementation:** implemented and focused tests passed at the prior M1.6 checkpoint; strengthened final validation now additionally checks frame rate/audio clock and records visual QA.

**Creative acceptance:** NOT ACCEPTED.

Reasons:
1. The latest reviewed run did not produce a final video.
2. The storyboard remains unapproved.
3. Four scenes fell back to gradient cards.
4. Repeated MoE diagrams remain visible.
5. Downloaded stock candidates include exact adjacent duplicates and incomplete retained provenance.
6. Vision review rate limiting prevented complete review for some candidates.
7. The existing completed video still reads as repeated diagrams and text cards rather than a cinematic hybrid edit.

A technically valid MP4 is not equivalent to a publish-ready NEXTDECODE Short.

## 6. Remaining blockers to close before production acceptance

1. Preserve and expose the exact render exception for each failed run (bounded, redacted diagnostics; no raw secrets/prompts).
2. Resolve why the latest render stage fails before treating a storyboard/voice-ready run as a delivery.
3. Ensure only candidates with complete rights/provenance metadata can progress to an approved storyboard.
4. Replace gradient placeholders for critical explanatory beats with purposeful local motion graphics or verified relevant footage; do not auto-approve fallback cards.
5. Reduce repeated composition across adjacent and distant scenes; visual variety must be intentional, not random.
6. Complete one owner-reviewed 45–60 second video and inspect the full playback, not only a contact sheet.
7. Run the complete regression suite after the current shared worktree settles.

## 7. Preservation and actions not taken

- No git reset, stash, clean, broad reformat or deletion.
- No provider search/download/API call in this pass.
- No dependency installation or service restart.
- No public production render or publishing/upload/deployment.
- No commit or push.
- Existing uncommitted changes across Parallel, OpenCode and other project workstreams were preserved.
