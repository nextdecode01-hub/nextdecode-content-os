# NEXTDECODE Model Routing & Video Provider Integration

**Date:** 16 November 2026  
**Status:** Task-aware model routing implemented; video provider adapters implemented; live generation qualification pending.

## Model routing

The active task-routing contract is `config/brain/model_task_routing.v1.json`. It assigns exact provider/model pairs by workload, with ordered fallbacks restricted to that workload. The routing module is `app/providers/model_router.py`; script drafting and script review in `app/script/studio.py` now call this router through `generate_for_task_json()`.

Initial task roles:
- Research synthesis: Gemini Flash, then Qwen.
- Script drafting and review: GPT-OSS 120B, Qwen, Gemini.
- Evidence extraction: Nemotron Bolt, GPT-OSS 20B, Cloudflare.
- Visual planning: GPT-OSS 120B, Qwen, Gemini.
- Visual QA: Nemotron Super VL, Gemini.
- Fast classification: GPT-OSS 20B, Nemotron Bolt, Cloudflare.
- Metadata transformation: Gemini Flash Lite, GPT-OSS 20B, Pollinations.
- General fallback: OpenRouter free model, Pollinations, Cloudflare.

The role list is a working 10-model routing portfolio, not an assertion that every model has passed editorial qualification. Existing benchmark outcomes remain attached to the candidate portfolio; exact-model route traces record the chosen provider/model and any in-role failures.

Read-only APIs:
- `GET /providers/routing`: task assignment and local configuration readiness.
- `GET /providers/portfolio`: qualification, usage and quota observations.
- `GET /providers/inventory`: provider configuration and last-known health.

## Video adapters

`app/providers/video_generation.py` provides:
- Kling: official API text-to-video task creation, task lookup, normalized status and download.
- Runway: official API text-to-video task creation, task lookup, normalized status and download.
- Google Veo: Vertex AI SDK adapter with operation polling; it explicitly requires Vertex AI project/application credentials and does not assume a Gemini API key alone is sufficient.
- `app/providers/video_generation_workflow.py`: explicit provider submission, bounded polling with backoff, download, ffprobe metadata, SHA-256 and a per-asset provenance sidecar. It never switches provider automatically.

Every generation submission calls the existing authorization guard before network I/O. Provider status/download operations do not create new generation tasks. No generation was submitted as part of implementation or tests.

Read-only API:
- `GET /providers/video-capabilities`: credential/configuration readiness only, no live calls.

## Short-form production contract

For NEXTDECODE Shorts:
- Frame: 9:16 portrait.
- Master render: 1080x1920, 30 fps, H.264 MP4 with AAC audio.
- Generated clips: prefer 5–10 second shots; choose 720p/1080p when provider/model supports it; conform/crop/scale to 1080x1920 in FFmpeg.
- Clip role: b-roll or a planned visual beat, never replace narration/captions/EDL authority.
- Audio: generated-video audio disabled by default; narration remains the master audio track and licensed music/SFX are mixed by existing audio pipeline.
- Every clip must retain provider, model, task ID, prompt, source URL, local SHA-256, dimensions, duration, FPS and run ID in provenance.
- Validate download integrity, ffprobe metadata, usable duration, orientation, black/frozen frames, duplicate compositions and relevance before the clip enters the EDL.
- Failed or unsuitable generated clips must fail closed to the existing approved stock/local visual paths; no silent substitution with unverified media.
- Human review and existing publishing governance remain unchanged.

## Known qualification limits

- Kling and Runway adapters are implemented against their official task APIs, but no live generation task was submitted.
- Veo adapter requires Vertex AI configuration; current Gemini API-key configuration alone is not proof of Veo readiness.
- Provider credentials in `.env` are not proof of quota/entitlement or endpoint success.
- Production render integration still depends on the visual resolver/renderer boundary owned by the parallel visual workstream. This change does not overwrite `app/visuals/chain.py`, `app/visuals/stock_fetcher.py`, `app/render/assembly.py` or Dashboard.
