# Phase 7 — Audio Cut Noise, Motion Quality & Visual Relevance

**Date:** 2026-10-29  
**Project:** `/home/demon/shorts_studio`  
**Branch:** `main`  
**Git:** no stage, commit, push, reset, or branch switch  
**Publishing:** not triggered

## 1. Scope

This phase follows `shorts_studio_phase7_audio_motion_brief.md` and the earlier implementation brief and roadmap. It fixes the reported defects in this order:

1. Extra/click/whoosh sound at scene changes.
2. Unsmooth or frozen motion.
3. Weak visual relevance and duplicate-card replacement with unrelated b-roll.

The Phase 6 report was read first so completed fixes (duplicate guards, dark-footage checks, script-aligned captions, storyboard gate) were not repeated.

## 2. Audio diagnosis and fix

### 2.1 Root cause

The sound was not a codec click or a stock-clip audio leak. Every shot is rendered with `-an`, and the final concat has `a=0`, so source footage audio never reaches the mix.

The sound was a **deliberate transition SFX scheduled at every cut**. `motion_director._pick_sfx` assigned:

- `impact` to the hook and payoff;
- `whoosh` to every other shot after index 0.

`render_video` then called `synthesize_sfx(kind)` and `_mix_audio` placed it at `shot["start"]`. The Phase 6 render therefore contained **13 whooshes at 13 cuts**:

`4.143, 8.287, 12.430, 16.574, 20.717, 24.861, 29.004, 33.147, 37.291, 41.434, 45.578, 49.721, 53.865`

### 2.2 Measurements

`app/render/audio_diagnostics.py` decodes the final audio to mono 44.1 kHz and measures:

- pre-cut window: −0.40 to −0.10 s;
- post-cut window: +0.10 to +0.45 s;
- onset window: 0 to +0.05 s;
- control window: mid-shot;
- high-band energy via first difference (the whoosh is a 900 Hz high-passed noise burst);
- sustained high-band run and isolated sample-jump ratio.

Phase 6 result:

- **13/13 cuts flagged**;
- post-cut high-band energy consistently **−17.5 to −17.7 dB**, while control windows were roughly **−25 to −43 dB**;
- the whoosh lasts 0.7 s, so it is a sustained lift, not a single click.

The before/after spectrogram around the first cut is in:

- `outputs/phase7_audio_diagnostics/spectrum_before_cut.png` (broad noise band begins at the cut)
- `outputs/phase7_audio_diagnostics/spectrum_after_cut.png` (voice harmonics only)

### 2.3 Fix

- Transition SFX are **off by default**. `SHOT_SFX=on` restores the old impact/whoosh design for anyone who wants it.
- If opted in, `impact` now has a 20 ms fade-in so it cannot start with a hard sine edge.
- `_mix_audio` had a latent bug: with no music and no SFX it connected `[vn]` to two `anull` filters, which FFmpeg rejected. The duplicate branch was removed; voice-only mixing now works.
- Audio boundary diagnostics are attached to every render and to QA. A sustained whoosh or isolated sample jump becomes a QA warning instead of passing silently.
- Speech onsets after silence are not treated as clicks: the detector requires an isolated spike far above the local 95th-percentile slope, not just a large pre/post RMS difference.

### 2.4 Before/after

Same voice and music, same cuts, clean mix:

| Metric | Phase 6 | Clean remix |
|---|---:|---:|
| Cuts flagged | **13/13** | **0/13** |
| Post-cut high-band | −17.5 to −17.7 dB | −24.6 to −63.5 dB |
| SFX count | 13 | 0 |

A manual listening pass was not possible inside the agent environment. The conclusion is supported by waveform samples, per-boundary metrics, and the before/after spectrograms; human listening is still listed as an open verification item.

## 3. Motion diagnosis and fix

### 3.1 Root cause

`build_ken_burns_filter` used `zoompan ... d=<frames>`. With a video input, FFmpeg repeats the **first source frame** for the whole shot while the zoom changes. A synthetic 60-frame moving-box test showed:

- old filter centroid x: `10.5 → 10.5 → 7.0 → 4.5 → 4.5` (frozen; only the zoom moves it);
- new filter centroid x: `10.5 → 31.5 → 71.0 → 115.0 → 137.5` (native motion retained).

In addition, every shot zoomed **in** from 1.00–1.04 to 1.12–1.18, so every cut snapped back to a smaller scale. Motion was linear from the first frame and identical in character for cards, UI, stills, and video.

### 3.2 Fix

- `d=1` for Ken Burns; real video also gets a separate fixed scale/crop path with no artificial zoom.
- Motion is assigned after assets resolve, using scene type and asset kind:

| Scene type / asset | Motion |
|---|---|
| real video | fixed crop, source motion only |
| still photo | 8% eased Ken Burns, varied direction |
| UI/code demo | 5% slow push, minimal pan |
| typography / claim card | 4% push, no pan |
| chart | 3.5% push, very small pan |
| diagram | 6% push, small pan |
| map / product | 6–7% push |
| gradient caption | 4% text-card push, no pan |

- Zoom direction alternates. The first zoom of a shot equals the last zoom of the previous shot, so cuts do not jump in scale. Pan start also continues from the previous shot.
- Motion uses smoothstep easing (`3t² − 2t³`), so it starts and stops gently instead of a linear ramp.
- Zoom is bounded to 1.00–1.20 and pan to ±3% of width.
- A video shorter than its shot is looped with `-stream_loop -1` instead of silently truncating the segment. This fixed a real desync: the first final render was 54.07 s while the voice was 56.90 s.
- After rendering, `storyboard/motion_sheet.jpg` shows start/mid/end frames for every shot.

### 3.3 Motion evidence

- Synthetic test: `outputs/phase7_motion_diagnostics/summary.json`.
- Final start/mid/end sheet: `outputs/phase7_final_benchmark_v2/shots/storyboard/motion_sheet.jpg`.
- Reviewed shots: S00/S01 (UI video), S02 (text card), S03 (keyboard), S04/S05 (native lab footage), S06 (finger/laptop), S07 (diagram), S08 (still), S09/S10 (charts), S11 (conference), S12 (card), S13 (chart).
- No freeze, scale snap, or unreadable card was visible in the sheet. Native clips show real source motion.

## 4. Visual relevance

### 4.1 What changed

- **Duplicate figure → recap card, not b-roll.** A repeated number now produces a narration-derived recap card listing the real figures used so far. Recap cards still obey the graphic budget and the maximum consecutive-card rule, and two recaps cannot be adjacent.
- **Dates and code notation are not statistics.** `_first_number` now ignores bare years (`2010`, `2026`), `N+1`, and `N plus 1`. Phase 7's first fresh run generated meaningless `1` and `2026` cards; the final run does not.
- **Queries are beat-specific.** Shot queries now prefer beat-only visual concepts, then beat phrases, then topic phrases. Generic/verb/date phrases such as `june 2026`, `must check whether`, `often fails`, `bugs developers`, and `tools handle` are filtered out. Added concepts for bugs/testing, databases, and pull requests.
- **Weak stock is rejected.** Low-confidence lexical matches and dark/flat clips are skipped instead of used as a last resort; the scene falls through to Wikimedia, a generated image, or a gradient caption.
- **Generic Wikimedia titles are rejected.** A still whose title shares only broad terms (for example “Performance Measurement – Grassroots Development Programme” for “software development performance”) is refused rather than treated as a subject match.
- **Card text is narration-derived.** Claim cards show the real claim; numeric cards show the real number; recap cards show only numbers already spoken. No chart or figure is invented.

### 4.2 Manual judgement of the final 14 scenes

Rubric: **strong** = asset shows the subject/claim directly; **partial** = same domain but not the exact claim; **weak** = only generic/title overlap, near-duplicate framing, or unreadable at phone size.

| Verdict | Count | Examples |
|---|---:|---|
| Strong | 6 | claim card (S02), typing hands (S03), software-testing life-cycle diagram (S07), TestingCup event (S11), 30-minute card (S12), code-review survey chart (S13) |
| Partial | 6 | developer at laptop (S00/S01), lab scientists (S04), microscope (S05), finger on laptop (S06), programmer workstation cubicle (S08) |
| Weak | 2 | generic academic-works charts (S09/S10) do not show database queries, loops, or memory leaks |

Full per-scene reason: `outputs/phase7_final_benchmark_v2/scene_relevance.json`.

Phase 6 reported 3 strong, 2 partial, and 5 weak scenes. This run has 6 strong, 6 partial, and 2 weak, on a different fresh narration; the comparison is directional, not a controlled A/B.

## 5. Controlled benchmark

The fresh narration was generated in `outputs/phase7_benchmark_v2` with topic:

> “How AI code review catches bugs developers miss”

The script is “What AI Code Review Catches and Misses” (122 words). That run exposed the short-clip truncation bug (54.07 s video vs 56.90 s voice). After the loop and query fixes, the visual stage was regenerated from the same fresh beat sheet and voice to produce the final sample. No Phase 5/6 shots or timings were reused.

### Final sample

- Video: `outputs/phase7_final_benchmark_v2/output_short.mp4`
- Duration: **56.900 s**, 1080×1920, 30 fps
- Audio: mixed; SFX count **0**; audio-boundary flags **0/13**
- Captions: 42 events, last end **55.92 s** (inside the video)
- Black/frozen checks: pass
- Assets: 14 unique, 0 consecutive asset-ID repeats
- Providers: 6 Pixabay, 6 Wikimedia, 2 local cards
- Confidence: 2 high, 12 medium, 0 low/none; 0 low-light
- QA: **pass**
- Render time: **226.8 s**
- Storyboard: `needs_review` (12 lexical/title review reasons, no human approval recorded)
- Contact sheet: `outputs/phase7_final_benchmark_v2/shots/storyboard/contact_sheet.jpg`
- Motion sheet: `outputs/phase7_final_benchmark_v2/shots/storyboard/motion_sheet.jpg`
- Metadata: `outputs/phase7_final_benchmark_v2/verification.json`
- Audio report: `outputs/phase7_final_benchmark_v2/audio_boundary_report.json`

### Versus Phase 6

| Metric | Phase 6 | Phase 7 final |
|---|---:|---:|
| Tests | 230 | **259** |
| Duration | 57.867 s | 56.900 s |
| Audio cut flags | not measured (13 whooshes present) | **0/13** |
| Transition SFX | 13 | 0 |
| Cards | 3 | 2 |
| Near-duplicate/weak scenes | 5 | 2 weak + 1 near-duplicate pair |
| Native stock motion | frozen by `d=frames` | retained |
| Video/voice duration match | 57.867 / 57.867 | 56.900 / 56.904 |
| Storyboard/motion sheet | contact sheet only | contact sheet + start/mid/end sheet |

## 6. Files changed

| File | Reason |
|---|---|
| `app/render/audio_diagnostics.py` | New offline boundary analyser (pure stdlib + FFmpeg) |
| `app/render/ffmpeg_tools.py` | `d=1`/smoothstep filter, fixed-crop filter, SFX fade-in, voice-only mix fix, short-freeze filter, audio-boundary QA |
| `app/render/shots.py` | Loop short video sources so a shot cannot truncate |
| `app/render/assembly.py` | Assign scene-aware motion, write motion sheet, attach audio-boundary report |
| `app/visuals/motion_director.py` | Scene profiles, cut continuity, eased motion, SFX opt-in default off, preserve explicit captions |
| `app/visuals/chain.py` | Recap cards, budget/run limits, year/`N+1` rejection, generic Wikimedia rejection, low-confidence/low-light rejection |
| `app/visuals/storyboard.py` | Start/mid/end motion contact sheet |
| `app/script/studio.py` | Beat-specific query variants, query stopwords/dates, bug/database/pull-request concepts |
| `app/script/pipeline.py` | Audio-boundary and duration warnings; voice vs render duration |
| `tests/test_audio_diagnostics.py` | New boundary, whoosh, speech-onset tests |
| `tests/test_motion.py` | Motion profiles, continuity, native crop, SFX opt-in, `d=1` |
| `tests/test_visual_chain.py` | Recap, budget, year/`N+1`, generic-title, low-light rejection |
| `tests/test_render_qa.py` | Short-video loop test |
| `README.md` | Updated motion, audio, relevance, and motion-sheet behavior |
| `reports/unattributed/PHASE7_AUDIO_MOTION_RELEVANCE_REPORT.md` | This report |

## 7. Tests

```bash
PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q \
  tests/test_audio_diagnostics.py tests/test_motion.py tests/test_visual_chain.py \
  tests/test_render_qa.py tests/test_storyboard.py
# 103 passed, 11 subtests passed in 50.84s

PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q
# 259 passed, 1 warning, 11 subtests passed in 87.35s
```

The warning is the pre-existing `google.generativeai` deprecation warning. No test used the network, a credential, or a publishing path.

## 8. Remaining issues

- S00 and S01 are two Pixabay clips from the same shoot (IDs 215189/215188). Asset-ID dedupe does not catch “same person, same room”.
- S09/S10 are generic academic-works charts, not database/loop imagery.
- S13 is on-topic (code-review survey) but mostly blank at thumbnail size; it needs a full-frame check.
- Vision review remains disabled by default; no paid vision call was made. The 12 medium-confidence assets still need human visual review.
- Storyboard status is `needs_review`, and no human approval file was written. It is not publish-ready.
- Manual listening was not possible in the agent environment. The audio conclusion rests on waveform metrics and before/after spectrograms.
- Short stock clips are looped to fill a shot; a 0.4 s loop point may be visible in a few clips and was not individually inspected.
- The music bed is still synthesized, not licensed music.
- The first fresh run (`outputs/phase7_benchmark_v2`, 54.07 s) is kept as evidence of the truncation bug; the corrected final sample is `outputs/phase7_final_benchmark_v2` (56.90 s).

## 9. Next step

Enable the vision reviewer on the five weakest/ambiguous scenes (S00/S01, S09, S10, S13) with owner approval, and add same-shoot dedupe using Pixabay tags/author or perceptual hash. Then rerun with `STORYBOARD_GATE=require`, record explicit human approval, and compare the approved storyboard with this one.
