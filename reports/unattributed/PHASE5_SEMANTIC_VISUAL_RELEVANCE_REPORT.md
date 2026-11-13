# Phase 5 — Semantic Visual Relevance and Fresh Benchmark Report

**Date:** 2026-10-29  
**Project:** `/home/demon/shorts_studio`  
**Branch:** `main`  
**Git:** no stage, commit, push, or branch switch  
**Publishing:** not triggered

## 1. What changed

- Added lexical/provenance relevance validation for every resolved visual against its narration beat and scene purpose.
- Added explicit confidence labels: `high`, `medium`, `low`, `none`.
- Added `semantic_review`, `relevance_reason`, `matched_terms` and `review_reason` per asset.
- Stock and still matches are never labelled as semantic understanding. They remain `relevance: tag_overlap` or `title_query_match`, with `semantic_review: true`.
- Motion-graphic cards generated directly from narration text are `high` confidence and not sent to semantic review.
- Gradient/procedural fallbacks are `low` or `none` confidence and always flagged for review.
- When the first stock query returns low lexical relevance and another query exists, the resolver tries the alternative query before accepting the weak candidate.
- Added singular/plural term matching so `server` and `servers` can match without a full stemmer.
- QA now reports `semantic_review`, `low_confidence` and `confidence_counts` in asset statistics, and warns when assets rely only on lexical/provenance matching.
- Preserved the existing render/audio QA and all compatibility wrappers.

## 2. Files changed and why

| File | Change |
|---|---|
| `app/visuals/chain.py` | Added `validate_asset_relevance`, content-term matching, plural handling, low-confidence re-query, and confidence/review fields in resolved assets and planner diagnostics |
| `app/render/ffmpeg_tools.py` | QA asset statistics and warnings for lexical-only assets and low-confidence assets |
| `tests/test_visual_chain.py` | Added 8 tests for validation tiers, ambiguity, fallback behavior and re-query selection |
| `tests/test_render_qa.py` | Added QA test for low-confidence and semantic-review reporting |
| `README.md` | Documented confidence/review semantics and the “tag overlap is not semantic understanding” rule |
| `outputs/phase5_benchmark_final/` | Fresh final benchmark video, voice, captions, shot renders and assets |
| `data/metadata_phase5_benchmark.json` | Final benchmark metadata including per-asset confidence and QA |
| `outputs/benchmark_frames/phase5/` | Representative frames extracted from the final video |
| `reports/unattributed/PHASE5_SEMANTIC_VISUAL_RELEVANCE_REPORT.md` | This report |

The preliminary 43.5s run was preserved separately in `data/metadata_phase5_benchmark_43s.json` and `outputs/benchmark_frames/phase5_pipeline_43s.log`; it was below the requested 45–60s range, so the benchmark was rerun with a 58s target.

## 3. Pipeline trace

The fresh run used the real strong pipeline, not stored Phase 4 shots:

1. `app.script.pipeline.run` → explicit AI/technology topic.
2. `select_topic` → topic/angle/pillar.
3. `build_research` → research claims, sources, contradictions and limitations.
4. `script_studio.write_script` → hook, beat sheet, critic loop, final voice text.
5. `voice_provider.synthesize_with_fallback` → Edge TTS voice track.
6. Faster-Whisper → word timings, then `make_kinetic_ass`.
7. `motion_director.plan_shots` → 14 shots with claim/visual/query/motion metadata.
8. `motion_render.render_video` → scene planning, provider resolution, relevance validation, per-shot render, audio mix, caption burn-in.
9. `qa_video` → ffprobe, audio loudness, black/frozen detection, duplicate assets, caption timing and semantic-review counts.

## 4. Fresh benchmark

**Title:** AI Coding Agents: Productivity vs Accuracy  
**Topic:** Why AI coding agents are reshaping software development  
**Video:** `outputs/phase5_benchmark_final/output_short.mp4`  
**Metadata:** `data/metadata_phase5_benchmark.json`

- Duration: **57.867s** (inside the requested 45–60s range).
- Words: 117.
- Shots: 14 (average 4.14s).
- Research: sufficient, 14 claims, 5 sources, 0 contradictions, 3 limitations.
- Script: 1 rewrite, slop score 0.
- Voice: Edge TTS, 57.867s.
- Providers: 5 motion graphics, 6 Pixabay clips, 3 Wikimedia stills.
- Stock: 6/6 cap used; fallbacks 0.
- Scene types: 3 typography, 3 footage, 2 diagram, 4 UI demo, 2 chart.
- QA: **pass**.
- Black intervals: none.
- Frozen intervals: none.
- Assets: 14 unique, 0 consecutive repeats.
- Confidence: 5 high, 9 medium, 0 low/none.
- Semantic review: 9 assets.
- Audio: mixed; mean −19.4 dB, max −0.5 dB.
- Captions: 43 events, last end 57.0s, burned successfully.
- QA warning: `9 asset(s) rely on lexical/provenance matching and need visual review`.
- Total pipeline elapsed: **771.1s** (research, script, voice, transcription, visuals, render, QA).
- Render/asset assembly: approximately **108.7s**, derived from the first shot render timestamp (01:32:09.665) to final output (01:33:58.332).

## 5. Comparison with the Phase 4 benchmark

| Metric | Phase 4 benchmark | Phase 5 fresh benchmark |
|---|---|---|
| Input | Reused stored shots/voice/ASS | Fresh research + script + voice + shots |
| Duration | 39.667s | 57.867s |
| Cards | 7 | 5 |
| Pixabay clips | 6 | 6 |
| Wikimedia stills | 1 | 3 |
| Scene types | typography 6, footage 7, chart 1 | typography 3, footage 3, diagram 2, UI demo 4, chart 2 |
| Unique assets | 14/14 | 14/14 |
| Consecutive asset repeats | 0 | 0 |
| Relevance metadata | None | Confidence + matched terms + review flag |
| Semantic review | Not available | 9 assets flagged |
| QA warnings | 0 | 1 semantic-review warning |
| Audio | mean −19.0 dB, max −0.5 dB | mean −19.4 dB, max −0.5 dB |
| Captions | 30 events, last 38.6s | 43 events, last 57.0s |
| Render time | 76.5s render | ~108.7s render/asset stage |
| Total pipeline time | Not measured in Phase 4 | 771.1s |

Normalised render cost is similar: about **1.93s per output second** in Phase 4 and **1.88s per output second** in Phase 5 for the render/asset stage.

## 6. Actual visual relevance, repetition, audio and captions

### Manual frame inspection

This is a subjective review of extracted frames, not an automated semantic score.

**Strong matches**

- Shot 9 / 38.5s: Cursor AI coding-agent screen recording. Directly matches the coding-agent narration.
- Shot 4 / 18.5s: terminal with authorization/typing prompt. Strong coding-workflow match.
- Shot 2 / 10.0s: code-editor screen. Visually dark, but subject-matched.

**Partial / generic matches**

- Shot 5 / 22.0s: laptop keyboard. Relevant to development work but generic.
- Shot 7 / 30.5s: keyboard close-up. Generic.
- Shot 8 / 34.0s: laptop stand and keyboard. Generic.

**Weak or ambiguous matches**

- Shot 6 / 26.0s: Pixabay 1021 is a very dark coding screen; subject matches but the frame is hard to read.
- Shot 12 / 51.0s: Wikimedia “Picstart Development Programmer” is 1990s hardware-programmer equipment, not an AI coding agent. Title match only.
- Shot 13 / 55.0s: Wikimedia “A Programmer’s Workstation” is a dated office cubicle. Title match only.

The new validator flags all 9 stock/still assets for visual review. It does not claim to know that the PiCSTART device or cubicle are semantically weak; that is why the review flag exists. Manual inspection still found 3 weak/ambiguous stock/still scenes.

### Repetition

- No stock or still asset was reused: 14 unique assets, 0 consecutive asset repeats.
- Card text repetition remains: the `52%` card appears in shots 0 and 1 (0–8.29s), and the `84%` card appears in shots 10 and 11 (41.43–49.72s). Four of the five cards are duplicate pairs with different gradient backgrounds.
- Phase 4 was not instrumented for duplicate card text, so this is a newly measured issue rather than a proven regression.

### Audio

Phase 5 audio is mixed, with mean −19.4 dB and peak −0.5 dB. No silent or near-silent output. Audio QA and the voice-only fallback remain intact.

### Captions

43 caption events, last end 57.0s, inside the 57.867s video. Captions are legible on inspected frames. One ASR error is visible: the script says “GrayGaps report” while the burned caption says “GrigApps report”. Numbers such as 52%, 70% and 84% are rendered correctly.

### Render time

The render/asset stage took about 108.7s for 57.867s of output, versus 76.5s for 39.667s in Phase 4. Per output second the cost is roughly unchanged. The total fresh pipeline took 771.1s, dominated by research, script generation, TTS and Whisper transcription rather than FFmpeg.

## 7. Tests

```bash
PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q tests/test_visual_chain.py tests/test_render_qa.py tests/test_motion.py
# 64 passed, 6 subtests passed in 40.74s

PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q
# 220 passed, 1 warning, 6 subtests passed in 75.32s
```

The warning is the pre-existing `google.generativeai` deprecation warning. Before this milestone the full suite was 211 passed; 9 new relevance/QA tests were added.

## 8. Regressions and remaining risks

- Lexical validation is not semantic vision. It can mark a title-matching still as `medium` even when the image content is weak.
- The new QA warning is intentionally noisy for any lexical-only stock/still asset. That is honest, but it means a normal stock render will usually carry a warning.
- Two consecutive duplicate cards remain possible because the variety budget limits consecutive graphics to two but does not compare their text.
- Dark-but-not-black footage (for example the 26.0s coding screen) passes black/frozen checks while remaining visually weak.
- Captions are ASR-derived and can mis-transcribe names; “GrigApps” vs “GrayGaps” is one observed example.
- Research claims and source names were not independently re-verified for this report. The pipeline reports 14 claims and 5 sources, but editorial verification is still required before publishing.
- The final benchmark is one sample. It is not evidence of general visual-quality improvement; it is evidence that relevance is now inspectable and weak matches are flagged.
- No publishing or upload was triggered.

## 9. Next step

1. Add a duplicate-card guard that compares on-screen text, not just provider type, and downgrades the second card to b-roll.
2. Add a low-light/contrast check so dark stock clips are flagged even when they are not fully black.
3. Replace ASR-only caption text with script-aligned text where confidence is high, to preserve names and product terms.
4. Add an optional semantic vision-model review behind a configured provider; keep the current lexical gate as the offline default.
5. Run a second fresh 45–60s sample to measure whether the review flags correlate with human judgments across topics.
