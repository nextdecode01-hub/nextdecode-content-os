---
name: tts-provider-qualification
description: Qualify alternate narration engines and voice models for NEXTDECODE, including local/offline TTS.
---

# TTS Provider Qualification

Inspect app/voice/provider.py and its normalized provider output contract. A provider must create readable audio with measurable duration, expected sample rate/channels and non-silent content.

Provider failure, missing/truncated output or degraded/silent fallback must continue to the next configured provider or fail clearly. Preserve provider order unless the owner explicitly changes it.

Benchmark English pronunciation, pacing, naturalness, punctuation, acronyms, numerals and long-run stability. Record engine version, model/voice ID, model digest, language, license and provenance. Verify both engine and voice/model training-data licenses. Piper engine is GPL-3.0-or-later; individual voices have separate model-card and training-chain terms.

No silent fallback as success. No model download or package installation without scoped approval. Never infer commercial rights from the engine license alone. Keep human review before publishing. Add tests for unavailable provider, degraded output, fallback, invalid audio and license metadata.
