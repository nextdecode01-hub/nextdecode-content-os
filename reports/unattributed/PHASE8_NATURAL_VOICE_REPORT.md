# Phase 8 — Natural Voice & Narration Quality

Date: 2026-10-29
Status: samples generated and measured; **production default deliberately unchanged pending owner listening**

## 1. What the pipeline actually uses (diagnosis, Phase 8A)

| Stage | Actual implementation | Evidence |
|---|---|---|
| Script | `app/script/studio.py` → `voice_text` | project pipeline |
| Text normalization | none before Phase 8 | `generate_voice()` sent `voice_text` verbatim |
| Chunking | one request per whole script (Edge TTS), 1800-char chunks only for long-form/hosted providers | `chunk_text()` in `app/voice/provider.py` |
| TTS provider | `edge_tts` (Microsoft Edge online neural TTS), local CLI | `PROVIDERS[0]`, `_synthesize_edge_tts()` |
| Voice | `TTS_VOICE` → default `en-US-ChristopherNeural` | `DEFAULT_VOICE` |
| Prosody before Phase 8 | none — CLI called with voice + text only | old `_synthesize_edge_tts()` |
| SSML | **not used.** edge-tts CLI wraps text in one `<prosody pitch/rate/volume>` element; no `<break>`, `<emphasis>`, or `<mstts:express-as>` styles | `edge-tts --help`, `text_prep.py` header |
| Post-processing | render mix: `aresample=44100`, `loudnorm=I=-16:TP=-1.5:LRA=11`; music bed at −18 dB-ish gain via linear volume | `app/render/ffmpeg_tools.py:351–354` |
| Reuse of voice file | new file per run; Phase 8 samples were generated fresh, not reused | `outputs/phase8_voice_ab/` |
| Silent fallbacks | chain can drop to ElevenLabs → Cartesia → OpenAI → silent tone; none configured, so Edge was used | `provider_status()` |

### Was the old “Anti Gravity” / Andrew configuration recoverable?

No. A repository-wide search found no `Andrew`, `Anti Gravity`, or multilingual voice configuration in code, docs, `.env*`, or metadata. Render metadata records only `provider: edge_tts`, not the voice id. The previous configuration is therefore **not recoverable from this repository**; the only concrete lead is the user's memory of `en-US-AndrewMultilingualNeural`.

### Root causes of “robotic”

1. Voice choice: Christopher is a neutral, news-reader-style voice; no style/expressiveness control exists in Edge TTS.
2. No prosody configuration — every render used Edge defaults.
3. Raw text sent as-is: `84%`, `N+1`, `&`, dashes, and long run-on sentences are read literally or rushed.
4. One flat request for the whole script; pauses depend entirely on punctuation.
5. `loudnorm` is applied once in the final mix and is not a naturalness problem; no pitch shift, time stretch, denoise, or compression is applied to the voice.

No evidence points to post-processing as the cause of robotic delivery.

## 2. Is Andrew available? (Phase 8B check)

Verified against the installed `edge-tts 7.3.1` voice list:

| Voice id | Available | Tags |
|---|---|---|
| `en-US-AndrewMultilingualNeural` | yes | Warm, Confident, Authentic, Honest |
| `en-US-AndrewNeural` | yes | same tags (standard, en-US only) |
| HD / DragonHD Andrew | **no** | not present in edge-tts 7.3.1 |
| `en-US-ChristopherNeural` | yes | current default |

Cost: **free** — Edge TTS has no key, quota, or per-character billing. No paid provider was configured or used. Licensing: Microsoft Edge online TTS; acceptable for the project's current usage, but it is a Microsoft service, not a self-hosted model.

## 3. Code changes made

- `app/voice/provider.py`
  - Added validated `rate`/`pitch`/`volume` support for the Edge CLI (`_edge_prosody`), read from explicit args then `TTS_RATE`/`TTS_PITCH`/`TTS_VOLUME`.
  - Defaults are neutral (`+0%`, `+0Hz`, `+0%`), so existing renders are byte-identical in behavior unless env vars are set.
  - `synthesize`, `synthesize_with_fallback`, `synthesize_long` and the CLI accept the new controls; paid-provider fallbacks intentionally never receive Edge voice/prosody.
- `app/voice/text_prep.py` (new)
  - `normalize_for_speech`: `%` → “percent”, `N+1` → “N plus one”, `&` → “and”, dashes/arrows → pauses, `e.g./i.e./vs./etc.` → words, `API/SQL/GPU/CPU/LLM` → spaced letters; markdown noise stripped.
  - `split_long_sentences`: splits >28-word sentences at existing clauses, no words added or removed.
  - `prepare_narration`: per-paragraph normalization, preserves paragraph breaks (the only pause control available).
  - `script_sha256`: manifest hash.
- `app/script/pipeline.py`
  - `generate_voice` passes `TTS_VOICE`; text preparation is **opt-in** via `TTS_TEXT_PREP=on`, default off so production output does not change silently.
- `README.md`, `docs/TOOLING_STACK.md`: document the new keys.
- `tests/test_voice_naturalness.py` (new): normalization, word-preserving splits, idempotence, hash, prosody validation, Edge command contents, fallback isolation, opt-in behavior.

No Phase 7 audio-boundary, motion, storyboard, or render code was modified.

## 4. Controlled A/B/C samples

One representative 58-word script (hook → explanation → question → technical term + number → conclusion), identical for A and current; B/C differ only in text preparation and rate. All samples were rendered mono, 44.1 kHz, MP3 192 kbps, then normalized with `loudnorm=I=-16:TP=-1.5:LRA=11,aresample=44100`.

| Sample | Voice | Text | Rate | Duration | Integrated | True peak |
|---|---|---|---|---|---|---|
| **current** | `en-US-ChristopherNeural` | raw | +0% | 30.168 s | −17.26 LUFS | −1.71 dBTP |
| **A** | `en-US-AndrewMultilingualNeural` | raw | +0% | 28.920 s | −17.24 LUFS | −1.76 dBTP |
| **B** | `en-US-AndrewMultilingualNeural` | prepared | −4% | 29.712 s | −17.24 LUFS | −1.75 dBTP |
| **C** | `en-US-AndrewNeural` (no HD) | prepared | −4% | 27.048 s | −16.79 LUFS | −1.75 dBTP |

Files (in `outputs/phase8_voice_ab/`):

- `a_andrew_multilingual_raw.mp3`
- `b_andrew_multilingual_prepared.mp3`
- `c_andrew_standard_prepared.mp3`
- `current_christopher_raw.mp3`
- `manifest.json`, `variants.json`, `asr_check.json`

Only differences between A and B: `84%` → “84 percent”, paragraph breaks added, three long sentences split at existing clauses, and a conservative −4% rate. C isolates the standard-vs-multilingual voice using B's exact text and settings.

An experimental paragraph-chunked render exists at `experimental/b_andrew_multilingual_chunked.mp3` (31.36 s), but it exceeded the 30 s target and was excluded from A/B/C.

## 5. Automated checks — and what they do **not** prove

- Pronunciation: faster-whisper ASR of all four samples recovered every content word. A heard “team” (singular) for “teams” and capitalized “Code Review” in B; no dropped words, no number errors. The `84%` → “84 percent” conversion was read correctly.
- Loudness/format: all four within 0.5 LU of each other, peaks below −1.7 dBTP, no clipping, consistent 44.1 kHz mono.
- Duration: all within the 20–30 s target.
- Tests: full suite **271 passed, 1 warning, 11 subtests passed in 92.98 s** (`PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q`). The warning is the pre-existing `google.generativeai` deprecation in `multi_model_ai.py`.
- Phase 7 boundary diagnostics were not rerun on a new full render, because Phase 8 changed no audio-mix or boundary code; the A/B files are standalone recordings, not mixed shorts.

These measurements confirm alignment, loudness, and intelligibility. **They cannot establish whether a voice sounds human or natural.**

## 6. Your decision

Listen to the four files in this order and pick one:

1. `voice current.mp3` — what production sounds like today
2. `voice A.mp3` — Andrew Multilingual, raw text
3. `voice B.mp3` — Andrew Multilingual, prepared text, 4% slower
4. `voice C.mp3` — standard Andrew, same prepared text/settings as B

Tell me which sounds most natural, and whether the text preparation in B is an improvement or over-corrects. Until then nothing in production changes: `TTS_VOICE` stays unset (Christopher), prosody stays neutral, and `TTS_TEXT_PREP` stays off.

## 7. Limitations

- No HD/DragonHD Andrew exists in this provider; C is the standard voice, not HD.
- Edge TTS offers no SSML styles, `<break>`, or emphasis, so rhythm improvements are limited to punctuation, paragraphing, and ±rate.
- The old Anti Gravity configuration is not in the repository and cannot be reconstructed.
- Multilingual Andrew may switch pronunciation based on context; ASR caught no errors here, but longer technical scripts should be spot-checked.
- If you want clearly more expressive delivery (emotion tags, style prompting, breath control), the options are paid providers (ElevenLabs/Cartesia/OpenAI) or a local model — a provider change that needs your approval and a cost review first. The current free chain already supports those APIs, so no new dependency would be required.
