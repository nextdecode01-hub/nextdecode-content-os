# Phase 6 — Visual Fixes Verification Report

**Date:** 2026-10-29  
**Project:** `/home/demon/shorts_studio`  
**Branch:** `main`  
**Git:** no stage, commit, push, or branch switch  
**Publishing:** not triggered

## 1. What changed

- **Duplicate-card guard:** `plan_scenes` now compares the on-screen card text. If a card repeats text already used, it is downgraded to b-roll instead of rendering the same claim again.
- **Dark/flat footage check:** prepared stock clips and stills get `signalstats` luma measurements. Very dark or flat assets are marked `visual_quality=low_light`, treated as low relevance, and skipped in favour of another query when possible.
- **Script-aligned captions:** ASR supplies word timings, but the authored script supplies the spelling. Names such as “GrayGaps” are no longer replaced by Whisper’s “GrigApps”.
- **Optional vision review:** added `app/visuals/vision_review.py`, disabled by default. It only runs with `VISION_REVIEW_PROVIDER=gemini` and a configured Gemini key, never logs the key/URL, and leaves the lexical gate active when unavailable.
- **QA reporting:** asset stats now include `low_light`, `semantic_review`, `low_confidence` and confidence counts. Warnings identify dark/flat assets and lexical-only matches.

## 2. Files changed and why

| File | Change |
|---|---|
| `app/visuals/chain.py` | Duplicate-card signature/downgrade; luma-based low-light flagging; AI vendor names such as `pollinations` now go through generated-image review; vision-review integration |
| `app/visuals/vision_review.py` | New opt-in Gemini vision reviewer with frame extraction, JSON parsing and safe failure paths |
| `app/render/ffmpeg_tools.py` | `video_luma_stats`; QA `low_light` counts and warnings |
| `app/render/subtitles.py` | `align_script_to_asr` with interpolation and monotonic timing repair |
| `app/script/pipeline.py` | Caption build now prefers script-aligned spelling over raw ASR text |
| `tests/test_visual_chain.py` | Duplicate-card, dark/flat, AI-provider and vision-review tests |
| `tests/test_render_qa.py` | Caption alignment and QA low-light/review tests |
| `README.md` | Documents duplicate guard, dark check, script-aligned captions and opt-in vision review |
| `outputs/phase6_fixes_benchmark/` | Verification render using the Phase 5 fresh voice/shots |
| `data/metadata_phase6_fixes_benchmark.json` | Verification metadata, plan, assets and QA |
| `outputs/benchmark_frames/phase6/` | Extracted verification frames |

## 3. Verification render

This render **reuses the Phase 5 fresh voice and shot timings** to isolate the four fixes. It is not a new research run and should not replace the Phase 5 benchmark as the fresh-content sample.

- Duration: **57.867s**
- Providers: 3 motion graphics, 6 Pixabay, 4 Wikimedia, 1 Pollinations image
- Scene types: 2 typography, 5 footage, 2 diagram, 4 UI demo, 1 chart
- Stock: 6/6 cap used
- Assets: 14 unique, 0 consecutive repeats
- QA: **pass**
- Black intervals: none
- Frozen intervals: none
- Audio: mixed; mean −19.4 dB, peak −0.5 dB
- Captions: 41 events, last end 57.0s
- QA warning: `11 asset(s) rely on lexical/provenance matching and need visual review`
- Low-light assets in final render: 0
- Verification render time: **155.7s** (re-downloaded stock/stills and resolved more fallbacks)

### Caption fix

- Alignment input: 120 ASR words → 117 script words.
- The burned ASS contains “GrayGaps” and no “GrigApps”.
- Caption timing still fits inside the 57.867s video.

### Duplicate-card result

The plan now renders **3 cards instead of 5**:

- `52%` card once
- `70%` card once
- `84%` card once

Shots 1, 3 and 11 were downgraded to b-roll because their card text duplicated an earlier card. No duplicate on-screen card text remains.

### Dark-footage result

The low-light check flagged the previously used dark coding clip during resolution and selected an alternative. The final QA reports `low_light: 0`. The check is based on average luma and flat-contrast thresholds, so it does not catch every visually dark-but-readable clip.

### Vision review

Vision review was **not enabled** for this render. The offline lexical validator remains the default. The opt-in path is covered by mocked tests only; no paid vision call was made.

## 4. Comparison: Phase 5 vs Phase 6 verification

| Metric | Phase 5 | Phase 6 fixes |
|---|---:|---:|
| Duration | 57.867s | 57.867s |
| Cards | 5 | 3 |
| Duplicate card text | 52% ×2, 84% ×2 | none |
| Pixabay clips | 6 | 6 |
| Wikimedia stills | 3 | 4 |
| AI images | 0 | 1 (Pollinations) |
| Unique assets | 14 | 14 |
| Consecutive asset repeats | 0 | 0 |
| QA warnings | 9 review assets | 11 review assets |
| Low-light final assets | not checked | 0 |
| Caption source | ASR text | script-aligned spelling |
| “GrayGaps” caption | misheard as “GrigApps” | correct |
| Audio | −19.4 dB mean, −0.5 peak | same |
| Captions | 43 events / 57.0s | 41 events / 57.0s |
| Render time | ~108.7s | 155.7s |

## 5. Actual visual relevance after the fixes

Manual frame inspection of the verification render:

**Strong**

- Three distinct stat cards (52%, 70%, 84%).
- Cursor AI coding-agent UI (35.2s).
- Terminal/coding screen (22.8s).
- Two developers working at a keyboard (31.0s).

**Partial**

- Two keyboard clips (6.2s, 14.5s).
- AI benchmark chart (39.3s): a real chart, but about AI benchmark performance rather than the accuracy/security sentence.

**Weak or ambiguous**

- Very dark code screen (18.6s).
- Handwriting on paper (26.9s) — selected as the replacement for the rejected dark clip, but not clearly about coding agents.
- Dated office cubicle (47.6s) — replacement for the duplicate 84% card.
- PiCSTART hardware programmer (51.8s).
- Generated empty corridor (56.0s) — atmospheric, but not clearly a production software environment.

The duplicate guard and dark check remove the targeted defects, but the replacement b-roll is not consistently better than the cards it replaced. In this sample, the net visual-relevance improvement is **not demonstrated**; the measurable gains are correct caption spelling, no duplicate card text, and explicit low-light/review diagnostics.

## 6. Tests

```bash
PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q tests/test_visual_chain.py tests/test_render_qa.py tests/test_motion.py
# 74 passed, 11 subtests passed in 35.82s

PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q
# 230 passed, 1 warning, 11 subtests passed in 56.32s
```

The warning is the pre-existing `google.generativeai` deprecation warning. Ten tests were added in this round.

## 7. Remaining risks

- Duplicate-card replacement can choose weak b-roll because the resolver still ranks stock lexically.
- The low-light check uses average luma/contrast and does not catch every dark-but-readable clip.
- Script-aligned captions fix spelling, but forced alignment can drift if the ASR stream differs heavily from the script.
- Vision review is opt-in and not exercised against the live provider in this run.
- The verification render reuses Phase 5 shots; it is not a new content benchmark.
- Research claims and source names remain unverified by this report.

## 8. Next step

1. Replace duplicate cards with a short narration-derived card variant, not arbitrary b-roll.
2. Run the optional vision reviewer on the 3–5 weakest scenes and compare its verdicts with human review.
3. Enable a stricter low-light threshold only for scenes where the subject must be readable (UI, code, charts).
4. Run a new fresh 45–60s pipeline sample to confirm the fixes generalize beyond this script.
