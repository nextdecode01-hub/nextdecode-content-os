---
name: renderer-adapter-qualification
description: Evaluate or implement alternative NEXTDECODE video renderers without destabilizing FFmpeg production.
---

# Renderer Adapter Qualification

Inspect the current timeline schema, render interfaces, output profile and QA contracts before editing.

Classify candidates correctly: renderer/encoder, composition framework, timeline interchange, frame-analysis helper or nonlinear editor. Verify installation, OS/architecture, codecs, licensing and runtime requirements.

Implement behind an explicit opt-in adapter. FFmpeg remains the default until parity is demonstrated. Use the same deterministic timeline fixture and compare duration, frame count, FPS, 1080x1920 dimensions, audio, caption timing, black frames, silence, output integrity, CPU/RAM, runtime and size. Run the strict QA suite.

Never silently switch renderers or rewrite timeline semantics. No cloud renderer or metered API by default. No dependency installation without scoped approval. Record exact versions and licenses; Remotion has special commercial terms. A candidate that fails a required contract remains experimental.
