# Phase 9 — Premium Audio Quality & Voice-First Mixing

Date: 2026-10-29
Voice approved by the owner after the Phase 8 listening test: `en-US-AndrewMultilingualNeural`

## 1. What the source actually is

| Stage | Format | Measured |
|---|---|---|
| Edge TTS output (provider ceiling) | mp3, 24 kHz, mono, 48 kbps CBR | `bit_rate=48000`, `sample_rate=24000` |
| Narration master (new) | pcm_s24le WAV, 44.1 kHz, mono | ~1058 kbps, decoded once |
| Narration deliverable (new) | mp3, 44.1 kHz, mono, 320 kbps CBR | `bit_rate=320000` confirmed by ffprobe |
| Video audio before Phase 9 | AAC mono, `-b:a 192k` | measured ~171 kb/s |
| Video audio after Phase 9 | AAC mono, `-b:a 320k` requested | measured ~148–166 kb/s |

Two honest limits:

1. **320 kbps cannot make a 24 kHz / 48 kbps source richer.** The model never rendered anything above its ~12 kHz Nyquist limit — measured voice energy above 12 kHz is −91 dB. Encoding at 320 kbps stops a *further* lossy generation from hiding what is there; it adds no bandwidth. Getting genuinely wider bandwidth means a different TTS provider (ElevenLabs and Cartesia return 44.1 kHz), which needs your approval and has a cost.
2. **A mono AAC stream cannot carry 320 kb/s in ffmpeg.** The native encoder clamps at 6144 bits per frame, so the request lands around 148 kb/s regardless. The requested value is recorded in metadata and the *measured* value is what QA reports. The standalone narration mp3 really is 320 kbps CBR; the video track is not, and saying otherwise would be false.

## 2. Bugs found by measurement

These were silent and are now fixed and regression-tested.

**a) The narration lost ~6 dB whenever music was present.**
The voice filter output `[vn]` was consumed twice — once by `sidechaincompress` as the ducking sidechain and once by `amix`. Measured: voice-only mix −16.2 LUFS, bed mix −22.4 LUFS. The fix is `asplit=2`, giving each branch its own copy: the bed mix now measures −16.27 LUFS, i.e. the narration keeps its level with or without music. Every short rendered before this (including the Phase 7 benchmark, which measured −19.98 LUFS) shipped roughly 4 dB quieter than intended.

**b) The limiter was raising the master into clipping.**
`alimiter` defaults to automatic level detection, which *increases* gain toward the ceiling. Measured on a voice+bed sum: without it −16.81 LUFS / −1.34 dBTP; with the default limiter −15.30 LUFS / **0.00 dBTP** (hard clipping territory); with `level=false` −16.81 LUFS / −1.51 dBTP. The chain now runs `alimiter=limit=0.84:level=false`, a pure ceiling.

**c) The "music bed" was pink noise, and it filled every pause.**
`synthesize_music_bed` mixed a 110 Hz sine with pink noise. The narration has nothing above 12 kHz; the bed had −56 dB of broadband energy up past 18 kHz. Frame-by-frame RMS showed the floor between sentences rising from −77 dB (clean voice) to −38 dB (with bed) — the pause was never silent, which is exactly the "external sound affecting the voice" you described. The bed is now opt-in (`MUSIC_BED=on`), contains no noise layer at all (measured −91 dB above 12 kHz), and a real licensed track can be supplied with `MUSIC_BED_FILE`.

**d) Ducking was extreme.** `sidechaincompress=threshold=0.04:ratio=12:attack=10:makeup=2` (a 12:1 ratio plus 2× makeup gain) pumps the bed audibly around the words. Now `threshold=0.06:ratio=3:attack=20:release=250:makeup=1`.

**e) The riser SFX never existed.** The `aevalsrc` expression was passed with literal quotes, which lavfi cannot parse, so `synthesize_sfx("riser")` always returned `None`. Fixed, and trimmed to 0.2 linear because the raw sweep was full-scale.

**f) The whoosh was white noise high-passed at 900 Hz** — energy concentrated exactly in the 2–8 kHz band where consonants live. It is now pink noise limited to 180–2400 Hz with fades, and the boundary detector confirms it no longer reads as a click at a cut.

## 3. What changed in the code

- `app/voice/provider.py` — default voice is now `en-US-AndrewMultilingualNeural`; added `probe_audio_format()`, `to_wav_master()` (single decode to 44.1 kHz 24-bit mono) and `export_master_mp3()` (320 kbps CBR); CLI gained `--master` and prints the source format.
- `app/render/ffmpeg_tools.py` — measured two-pass **linear** `loudnorm` instead of the dynamic gain-rider; `asplit` fix; `level=false` limiter at −1.5 dBFS; noise-free bed; band-limited SFX; `audio_bitrate()`, `music_bed_requested()`, `music_bed_source()`; QA now measures true peak, flags digital clipping as an error, warns above −1 dBTP, and records the delivered audio codec/bitrate.
- `app/render/assembly.py` — bed is off by default; honest `voice_only` mix label; `audio_settings` block in the render result.
- `app/script/pipeline.py` — narration is decoded once to a WAV master that captions and the mix both read; a 320 kbps narration mp3 is exported; voice identity, prosody, source format and mix settings are written into metadata.
- `pipelines/short.py` — the legacy/dry-run render uses the same measured normalization and `AUDIO_BITRATE`.
- `README.md`, `docs/TOOLING_STACK.md` — document the new keys.
- Tests: new `tests/test_audio_quality.py` (21 checks), `tests/test_audio_diagnostics.py` extended so the boundary detector is still proven against a known-bad transient *and* against the new softened SFX, `tests/test_render_qa.py` updated for the voice-first default plus a new opt-in bed test.

Phase 7's boundary diagnostics, scene-aware motion and duration checks are untouched and still pass; Phase 8's text preparation remains available behind `TTS_TEXT_PREP=on`.

**Test results.** Full suite: `294 passed, 1 warning, 11 subtests passed in 253.82s` via `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q`. The single warning is the pre-existing `google.generativeai` deprecation notice from `multi_model_ai.py`, unrelated to audio. Targeted run of `tests/test_audio_quality.py`, `tests/test_audio_diagnostics.py`, `tests/test_render_qa.py`, `tests/test_voice_naturalness.py` and `tests/test_phase6_voice_package.py`: 64 passed in 31.80s.

## 4. Measurements

Narration chain (14 s test line, Andrew Multilingual, −4 % rate):

| Configuration | Integrated | True peak | Sample peak | Floor between phrases |
|---|---|---|---|---|
| Voice only (production default) | −16.24 LUFS | −1.50 dBTP | −1.5 dBFS | −77 dB |
| Voice + bed | −16.27 LUFS | −1.51 dBTP | −1.5 dBFS | −39 dB |
| Voice + bed + SFX | −16.27 LUFS | −1.51 dBTP | −1.5 dBFS | −39 dB |

All three hold the same narration level and none clips; durations are identical, so caption timing is unaffected.

Full test Short (see §5): −16.19 LUFS, −1.48 dBTP, mean sample −16.1 dB, max −1.5 dB, 13 cuts with 0 audio-boundary flags, no silence gap ≥ 0.6 s, QA pass, 1080×1920 @ 30 fps. The standalone narration export from the same master measures −16.18 LUFS / −1.50 dBTP at a verified 320 kbps CBR, so the two agree.

## 5. Test Short render

Produced with the Phase 9 chain, voice-first (bed off), from the topic "AI code review".

| Property | Value |
|---|---|
| File | `outputs/phase9_short_test/output_short.mp4` |
| Title / duration | "Why AI Code Review Is Essential in 2026", 38.664 s |
| Video | 1080×1920, 30 fps, h264, 2.01 Mb/s |
| Audio | AAC mono 44.1 kHz, **measured 164 kb/s** against the requested 320k (the mono-AAC clamp from §1) |
| Loudness | −16.19 LUFS integrated, −1.48 dBTP true peak, −1.5 dBFS sample peak |
| Narration deliverable | `voice_320k.mp3` — mp3 44.1 kHz mono, **320000 bps CBR verified**, −16.18 LUFS / −1.50 dBTP (matches the video) |
| Master | `voice.wav` — pcm_s24le 44.1 kHz mono, decoded once from the 24 kHz provider mp3 |
| Audio-boundary flags | 0 of 13 cuts (Phase 7 diagnostics still passing) |
| Silence | no gap ≥ 0.6 s; QA `audio_level` and `true_peak` checks both pass |
| Captions | script-aligned, burned in, 76 words, render duration equals narration duration |
| QA | pass; only warning is the standing "7 asset(s) … need visual review" visual note |

## 6. Listening set

Same 14-second narration, same words, same loudness, so only the mixing differs:

- `mix 1 voice.mp3` — production default: narration alone at −16 LUFS
- `mix 2 voice+bed.mp3` — plus the placeholder tonal bed at −18 dB with 3:1 ducking
- `mix 3 voice+bed+sfx.mp3` — plus three band-limited effects on cuts
- `narration master.wav` — the lossless 44.1 kHz / 24-bit master, unnormalized

These are in `Downloads` along with `mix key.txt`. Automated numbers prove level, peak, floor and sync; **they cannot prove that anything sounds good — that is your call.**

## 7. Settings

```ini
# production defaults after Phase 9
TTS_VOICE=en-US-AndrewMultilingualNeural   # (unset also resolves to this)
TTS_RATE=+0%                                # demo 2 used -4%; set it if you prefer that
TTS_TEXT_PREP=off                           # on = speech-friendly normalization
MUSIC_BED=off                               # on = synthesized tonal pad
MUSIC_BED_FILE=                             # path to a licensed track; implies on
SHOT_SFX=off                                # per-cut effects, off since Phase 7
AUDIO_BITRATE=320k                          # requested; mono AAC clamps near 148k
```

## 8. Remaining limitations

- The narration bandwidth is capped by the free Edge TTS source (24 kHz / 48 kbps). Nothing in this phase changes that; only a provider change would.
- The video's mono AAC track cannot physically carry 320 kb/s in ffmpeg. If you want a genuinely high-bitrate video track, the options are stereo output (doubles the frame budget, adds no information) or a different codec; both are one-line changes and I have not made either without your say-so.
- The "music bed" is still a synthesized tone pair, not music. It is off by default; give me a licensed file for `MUSIC_BED_FILE` and the real ducking behaviour will apply to it.
- The SFX are ffmpeg-generated placeholders, licence-free by construction but not professional library material. Clean, scene-relevant effects need a licensed pack; they remain opt-in after Phase 7.
- Perceptual quality is unverified by me. The listening set above is the evidence for that decision.
