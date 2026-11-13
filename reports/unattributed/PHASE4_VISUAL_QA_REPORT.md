# Phase 4 — Visual Pipeline and Render QA Report

**Date:** 2026-10-29  
**Project:** `/home/demon/shorts_studio`  
**Branch:** `main` (no commit, stage, push, or branch switch performed)

## 1. Implemented

- Added structured scene briefs for every shot: narration, beat ID, purpose, scene type, asset query and variants, expected duration, 9:16 aspect, on-screen text, motion/transition, fallback chain, and validation flags.
- Added a controlled asset provider chain: local card → Pixabay/Pexels video → Wikimedia still → AI image → gradient caption → procedural.
- Limited stock video to fewer than half of the shots and prevented more than two consecutive full-screen graphics.
- Skipped already-used assets so adjacent scenes do not repeat the same clip.
- Added honest per-scene diagnostics: `asset_id`, `relevance`, `attempts`, `fallback_reason`, provider counts, and visual-plan usage.
- Fixed the audio mix for this FFmpeg build by removing unsupported `afifo`/`fifo` filters. Music/SFX mixing now works; if it fails, the render keeps the voice track, sets `audio_mix_mode=voice_only`, and records a warning.
- Made FFmpeg exit code 0 insufficient on its own: the output must pass `qa_video`.
- Fixed kinetic captions so words are spaced correctly, decimal values are not split across lines, and punctuation attaches properly.
- Fixed “point one percent” parsing so the card shows `0.1%` rather than `1%`.
- Fixed a black-scene bug: a single black frame at the start of a stock clip was frozen by Ken Burns. Stock clips now trim a 0.15s lead-in, and mostly-black prepared clips are rejected.
- Added automated QA for: file existence/size, resolution, fps, duration, audio stream, audio loudness, black intervals, frozen intervals, duplicate assets, and caption timing.

## 2. Files changed + reasons

| File | Reason |
|---|---|
| `app/visuals/chain.py` | Scene brief, classification, provider chain, stock cap/ranking/dedupe, fallbacks, diagnostics, decimal-percent parsing, clip lead-in handling |
| `app/render/ffmpeg_tools.py` | FFmpeg/ffprobe helpers, Ken Burns filter, audio mix fix, black/frozen/audio/caption QA |
| `app/render/assembly.py` | Multi-shot assembly, visible audio-mix fallback, render diagnostics |
| `app/render/shots.py` | Deterministic per-shot rendering and procedural fallback |
| `app/render/subtitles.py` | Kinetic ASS captions with spacing and decimal handling |
| `motion_render.py` | Compatibility entry point; legacy asset resolver delegates to `app.visuals.chain` |
| `app/visuals/motion_director.py`, `visual_assets.py`, `visual_quality.py`, `stock_fetcher.py`; `app/publish/*` | Canonical module locations after controlled moves |
| Root `motion_director.py`, `stock_fetcher.py`, `visual_assets.py`, `visual_quality.py`, upload scripts | Thin compatibility shims preserving old imports and CLI entry points |
| `tests/test_visual_chain.py` | Scene planning, variety, fallback trail, stock ranking, number parsing |
| `tests/test_render_qa.py` | Audio filters, caption spacing, clip lead-in trimming, QA, assembly fallbacks |
| `tests/test_motion.py` | Legacy asset resolver compatibility |
| `README.md` | Canonical layout, compatibility shims, QA/audio failure behavior |
| `pipelines/short.py`, `publish_all.py`, `publish_social.py`, `tests/test_phase2_storage_layout.py` | Import-path updates after moves |

Unrelated pre-existing working-tree edits under `api/main.py`, `app/research/`, `app/script/`, and `tests/test_api_telegram.py` were left intact and were not part of this visual/render work.

## 3. Structure changes

- Canonical code now lives under `app/`.
- Root-level visual and publishing scripts remain as thin compatibility shims.
- `motion_render.py` translates the legacy `source` hint but delegates ranking and downloads to `app.visuals.chain`.
- No root scripts, `archive/`, `data/`, or `outputs/` content was deleted.
- No git staging, commit, push, or branch switch was performed.

## 4. Tests

Commands run after the final edits:

```bash
PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q tests/test_render_qa.py tests/test_visual_chain.py tests/test_motion.py
# 55 passed, 6 subtests passed in 26.93s

PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q
# 211 passed, 1 warning, 6 subtests passed in 42.16s
```

The single warning is the pre-existing `google.generativeai` deprecation warning. The baseline before this work was 177 passed.

## 5. Visual QA

**Final video:** `outputs/chain_run4_benchmark/output_short.mp4`  
**Metadata:** `data/metadata_chain_run4_benchmark.json`

- Status: **pass**; no warnings.
- Duration: 39.667s.
- Resolution: 1080×1920.
- Frame rate: 30fps.
- Audio: present; mean volume −19.0 dB, max −0.5 dB.
- Audio mix mode: `mixed`.
- Black intervals: none.
- Frozen intervals: none.
- Assets: 14 unique, 0 consecutive repeats.
- Captions: 30 events, last end 38.6s, burned successfully.
- Providers: 7 local motion graphics, 6 Pixabay clips, 1 Wikimedia still.
- Visual plan: stock 6/6 cap; scene types = 6 typography, 7 footage, 1 chart.

Evidence frames:

- `outputs/benchmark_frames/final/final2_7.5s.png` — card and caption spacing.
- `outputs/benchmark_frames/final/final3_12.8s.png` — corrected `0.1%` card.
- `outputs/benchmark_frames/final/final2_23.5s.png` — no invented bar chart; card treatment only.
- `outputs/benchmark_frames/final/final3_35.0s.png` — formerly black scene 12, now visible.
- `outputs/benchmark_frames/final/final2_37.0s.png` — Wikimedia still with weak visual relevance.
- `outputs/chain_run4_benchmark/output_short_before_clipfix.mp4` — previous black-render evidence.

## 6. Risks / limitations

- The benchmark reused stored shots, voice, and ASS timings from `data/metadata_chain_run3.json`; research and script stages were not rerun.
- The input is 39.7s, below the requested 45–60s benchmark range.
- Stock relevance is tag-overlap only, not visual semantics. Pixabay clip 29461 is tagged with “electricity pole” but is visually dominated by a tree and distant pylon. The Wikimedia “Data Center 2 (UNC)” image is also visually ambiguous.
- Live Pixabay results can vary between runs; provider selection is not deterministic across network responses.
- Captions have natural pauses where speech pauses (for example around 25.0s and 35.0s), so some frames have no caption. TTS tokenization also renders “ChatGPT” as “chat GPT” in one caption.
- The 0.15s lead-in trim could discard meaningful content in clips where the first frame matters.
- QA validates technical properties and loudness, not content accuracy or viewer comprehension.
- No publishing or upload was triggered.

## 7. Next step

Run the full pipeline end-to-end on a fresh 45–60s AI/tech script and review the scene briefs before rendering. The highest-value follow-up is a semantic visual-relevance gate or human review step before publishing, plus a golden-render regression test for stock lead-in trimming and numeric card text.
