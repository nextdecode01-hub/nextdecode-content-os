# Implementation Increment Report — Story-First Documentary Upgrade

**Date:** 2026-11-17  
**Branch / HEAD at inspection:** main / 419801d  
**Workspace:** /home/demon/shorts_studio  
**Commit/push:** None

## Work completed
- Added `app/research/topic_diversity.py` with a 12-category taxonomy, normalization, similarity scoring, category annotation and diversity-first candidate ordering.
- Updated `app/research/topics.py` to broaden discovery beyond AI/technology with world, science, business, history, nature, space, human stories, culture, sports and consumer categories. Existing technical sources remain.
- Updated `app/script/short.py` to remove the AI-only commissioning voice, require topic-specific editorial direction and request a fully timed production storyboard with visual/audio/rights/edit/fallback fields.
- Added `app/script/production_storyboard.py` to validate storyboard phase completeness, time coverage, supported visual types and exact narration excerpts. Rights status is explicitly review-required.
- Updated the short generator output contract to persist story format, category, editorial angle, viewer question, payoff and storyboard.
- Updated `app/script/longform.py` commissioning language to support the broader documentary category universe and real-source/voice/animation visual options.
- Added focused tests in `tests/test_topic_diversity_and_production_storyboard.py` and updated the shared-provider short-generator fixture to the new contract.
- Added the consolidated target architecture and long-form expansion document: `docs/production/NEXTDECODE_STORY_FIRST_DOCUMENTARY_PRODUCTION_UPGRADE_2026-11-17.md`.

## Verification
- Python compilation passed for all changed Python modules.
- Focused test command:
  `PYTHONPATH=. venv/bin/python -m pytest -q tests/test_topic_diversity_and_production_storyboard.py tests/test_research_feeds.py tests/test_multi_model_ai.py tests/test_script_studio.py tests/test_longform_editorial.py tests/test_visual_quality.py tests/test_render_qa.py --disable-warnings --maxfail=5`
- Result: **118 passed, 3 subtests passed**.
- Separate broader visual-chain test attempt: 5 failures observed in `tests/test_visual_chain.py`, where current resolver selected `motion_graphic` while older assertions expected `gradient` or `pixabay`. This is not marked fixed. Needs inspection against current creative-director and provider-fallback behavior.
- No full repository suite run or live production video run completed in this increment.

## Repository safety
- The working tree was already heavily modified/untracked before this increment. Existing user/agent work was preserved; no reset, clean, stash, broad revert, commit or push was performed.
- Existing publishing approval/security boundaries were not changed.

## Remaining implementation
1. Rights/permission ledger and fail-closed enforcement across every media provider and publish path.
2. Actual acquisition adapters/workflow for licensed news archive footage and interviews; no automatic permission assumptions.
3. Original speech and natural-sound segment extraction with source/timecode provenance.
4. GIF discovery/reuse with per-item rights verification.
5. Beat-level visual-type routing from the new storyboard contract into current Visual Director, asset resolution and EDL.
6. J-cut/L-cut, sound bridges, original speech and NAT-sound audio track planning/execution.
7. Long-form chapter-level shot lists, complete visual/audio plans and dedicated QA.
8. Resolve visual-chain test failures and run end-to-end production using a non-AI category.

**Status:** First integrated increment completed; the full documentary-production vision is not yet implemented or production-ready.
