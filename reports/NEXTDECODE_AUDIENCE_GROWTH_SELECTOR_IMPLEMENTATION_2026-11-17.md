# Audience-Growth Selector Implementation Increment
**Date:** 2026-11-17  
**Workspace:** `/home/demon/shorts_studio`  
**Commit/push:** None

## Objective
Remove the legacy AI/technology-only editorial scoring bias so the expanded topic discovery system can fairly evaluate the broader NEXTDECODE documentary universe.

## Implemented
1. Reworked `app/research/selector.py::_score_channel_fit`:
   - Removed the positive/negative AI-term gate from the objective heuristic.
   - Added category-neutral signals: recognized story category, concrete subject, curiosity framing, jargon accessibility and actionable/insight language.
   - Updated editorial judge criteria to cover science, engineering, technology, business, history, geography, investigations, culture, sports, nature and human-interest.
   - Added broad editorial pillars while retaining legacy pillar names so historical feedback ledgers remain readable.
   - Marked judge-derived scores as estimates rather than measured outcomes.
2. Reworked `niche_relevance`:
   - Uses the shared 12-category taxonomy.
   - Accepts recognized non-technology documentary categories.
   - Unknown categories remain visible for editorial review with a score cap instead of disappearing silently.
3. Fixed `app/research/topic_diversity.py::classify_topic`:
   - Uses token-boundary matching, preventing the short marker `ai` from matching inside unrelated words such as `rainforest`.
   - Added rainforest/rainfall and geography markers, including canal/strait/shipping-route terms.
4. Added `tests/test_selector_growth_breadth.py` covering broad category acceptance, category-neutral scoring, review treatment for unknown categories and the short-token false-positive regression.

## Verification
- `py_compile` passed for `selector.py` and `topic_diversity.py`.
- Focused growth selector tests: **5 passed**.
- Combined regression group: **77 passed** across:
  - `test_selector_growth_breadth.py`
  - `test_topic_diversity_and_production_storyboard.py`
  - `test_research_quality.py`
  - `test_research_feeds.py`
  - `test_pipeline_topic_discovery.py`
- No full repository suite or live production video run completed in this increment.

## Important limitation
The selector's current score is still a research/editorial estimate, not a prediction of actual views, retention, CTR, subscriber conversion or revenue. Those outcomes require channel analytics after publishing. No competitor private metrics are inferred.

## Safety / repository state
- No reset, clean, stash, broad revert, commit or push.
- No publishing action.
- Existing approval and rights boundaries were not modified.
- Existing user changes and unrelated working-tree files were preserved.

## Next
1. Expand the auditable competitor benchmark dataset to 100-150 qualified channels and at least 1,000 video observations; record unavailable fields as null.
2. Add story/packaging/audience-continuity dimensions only after validating available inputs and current selector contracts.
3. Fix existing visual-chain regression failures and run a fresh, human-reviewed non-AI documentary production test.
