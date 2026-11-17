# NEXTDECODE — Actual Short Video Pipeline: Phase, API, Tool & Artifact Map
**Audit:** 16 November 2026  
**Scope:** Current strong Shorts path in `app/script/pipeline.py`, launched through the Shorts/orchestration layer. This is a code-path map, not a claim that every optional provider is active on every run.

## Executive view

The engine does **not** generate a complete video through one video-generation API. It builds a Short from a combination of:
- public research sources and article fetches;
- one or more text-model calls, or a deterministic source-grounded script template;
- a TTS provider;
- stock footage/photos and optional generated still images;
- original local motion graphics;
- FFmpeg/ffprobe editing, captions, audio mixing and QA.

The current render path has no integrated generative text-to-video model. Pixabay/Pexels/Coverr are stock-media search/download APIs, not text-to-video generation services. Kling credentials exist in `.env`, but the current pipeline has no Kling API client.

## 1. Run entry and orchestration

| Step | Code | Input | Tools / API | Output |
|---|---|---|---|---|
| Run entry | `pipelines/short.py` | topic, duration, run config | dotenv, RunTracker, existing orchestrator | run identity, work directory, stage hook |
| Strong pipeline | `app/script/pipeline.py::run` | topic or automatic discovery | local Python orchestration | staged pipeline result + metadata |
| Stage state | RunTracker / stage hook | stage start/success/failure | local manifest persistence | run manifest and per-stage status |

Important: direct `python -m app.script.pipeline` is draft-only by design; it stamps governance as non-publishable because it bypasses the approved orchestrator/review package.

## 2. Exact stage sequence during one video generation

### Phase A — Topic selection

**Code:** `app/script/pipeline.py::select_topic`, `app/research/topics.py::discover_topics`, `app/research/selector.py`

- If an operator supplies a topic, the engine records it as explicitly selected and skips autonomous multi-judge ranking.
- Otherwise, candidate discovery uses the topic adapters in `topics.py` (Hacker News Firebase API, arXiv Atom API, Reddit RSS and Google Trends feed logic where configured).
- Candidate scoring uses editorial criteria including audience relevance, freshness, evidence quality, originality and visual potential.
- The selector can make a bounded stock-footage feasibility probe using Pixabay/Pexels to estimate whether a topic has usable footage. This is a probe, not the final footage download.
- The selector can use configured LLM judges for channel-fit, visual-feasibility and angle/risk decisions. This path is separate from script drafting.

**Credential/API facts:** Hacker News, arXiv and RSS are public endpoints; Pixabay/Pexels need their respective keys. The precise active Google Trends adapter must be read from the current `topics.py` function before attributing a specific Google endpoint to a run.

**Artifact:** selected topic, scorecard, ranked/rejected candidates and selection method are carried into the run metadata.

### Phase B — Research and source extraction

**Code:** `app/script/pipeline.py::build_research`, `app/research/desk.py`, `app/research/claims.py`

1. The selected topic is converted into source URLs. For the MoE example, the pipeline explicitly adds primary references from Mistral, Hugging Face and arXiv.
2. Research desk makes direct HTTP requests to the source URLs; it does not require an LLM API key to fetch public web pages.
3. HTML text is extracted and bounded; blocked/unsupported content is not silently treated as evidence.
4. Research claims are tied to source URLs and exact source quotations.
5. The claims ledger classifies evidence, flags unsupported/unverified/conflicting/outdated claims and maps script sentences to source claims.

**APIs/tools:** public website HTTP, requests, HTML parser, arXiv API, RSS/feed adapters. This is source retrieval, not model inference.

**Artifacts:** research source bundle, source text, claim ledger JSON, claim IDs, source URLs, ledger/script hashes.

### Phase C — Script drafting

**Code:** `app/script/pipeline.py::_write_script_with_fallback`, `app/script/studio.py`, `app/providers/multi_model_ai.py`

- The pipeline first attempts a deterministic, source-grounded Mixtral explainer template for supported MoE topics. If it can build a valid script from primary-source evidence, it returns that script without a remote LLM call.
- Otherwise it calls Script Studio, which uses the shared provider layer.
- The provider layer routes through the currently configured hosted provider chain and model IDs.
- Script Studio applies the selected script profile, hook rules, word-count rules, rewrite/critic logic and structured metadata requirements.
- For the current 45–60-second production target, measured audio duration is authoritative; script word count alone is not accepted as duration proof.

**Current hosted provider adapters:** Gemini, Groq, Pollinations Text, NVIDIA NIM, Cloudflare Workers AI, OpenRouter, Mistral and Cerebras. Credentials/health are checked at runtime. A provider may be present in code but unavailable because the key, quota, model or service is unavailable.

**Retired from active routing:** OmniRoute and Ollama. The old environment entries may still exist, but the active routing order and provider inventory no longer include them. Autonomy/local-only mode fails closed rather than silently routing to hosted models when the retired local runtime is absent.

**Artifacts:** script JSON, title, hook, spoken text, tags, platform copy, source URLs, rewrite/critic information.

### Phase D — Evidence reconciliation

**Code:** `app/research/claims.py`, `app/script/pipeline.py::_build_evidence_checked_script`

- Every spoken factual sentence is checked against the research ledger.
- Blocking flags trigger a grounded rewrite; for supported MoE cases the deterministic primary-source template can be used.
- If the evidence gate still fails, the pipeline stops.
- If duration recovery changes the script, the ledger is rebuilt before captions/visual planning/rendering.

**Artifact:** `research/claim_ledger.json`, script SHA-256, ledger SHA-256, supported/qualified/unmapped claims and warnings.

### Phase E — Voice / narration

**Code:** `app/voice/provider.py`, called by `app/script/pipeline.py::generate_voice`

Provider order in the current module:
1. Edge TTS — Microsoft neural TTS service.
2. Kokoro local — local neural TTS.
3. ElevenLabs — optional API.
4. Cartesia — optional API.
5. OpenAI TTS — optional paid API.
6. Silent tone — diagnostic-only; invalid as production narration.

Credentials: `ELEVENLABS_API_KEY`, `CARTESIA_API_KEY` + `CARTESIA_VOICE_ID`, `OPENAI_API_KEY`; Edge/Kokoro do not require those hosted API keys.

- Voice result is written to local audio files.
- The pipeline measures actual audio duration with ffprobe.
- If too short, it regenerates a 45-second script and voice.
- If too long, it shortens at sentence boundaries and regenerates.
- The final narration must measure 45–60 seconds.

**Artifact:** `voice.mp3`, optional lossless master, measured duration, selected provider/voice metadata.

### Phase F — Captions and word timing

**Code:** `app/script/pipeline.py::build_captions`, `transcribe_words`, `app/render/subtitles.py`

- Local faster-whisper runs on CPU/int8 using `WHISPER_MODEL` (default `base`) for word-level timestamps.
- If transcription is unavailable, estimated proportional word timings are used; the timing source is recorded.
- ASS subtitle/caption file is created for kinetic/burned captions.

**External API:** none in the default Whisper path; it is local model inference.

**Artifact:** `subtitles.ass`, word-timing JSON and caption metadata.

### Phase G — Shot planning / visual intent

**Code:** `app/visuals/motion_director.py`, `app/visuals/shotplan.py`, `app/visuals/chain.py`

- Shot planning uses narration, measured audio duration, beat structure and claim ledger.
- Each beat gets a visual intent, query, shot type, expected duration, aspect ratio, on-screen text and motion metadata.
- The deterministic classifier chooses motion graphics for claims/numbers/lists/architecture and b-roll for ambient/context beats.
- For MoE mechanism scenes, the plan can prefer an original explanatory diagram rather than unrelated generic stock.

**Artifact:** `shot_plan.json`, per-shot intent/query/timing, scene briefs and editorial plan.

### Phase H — Visual asset resolution

**Code:** `app/render/assembly.py` calls `app/visuals/chain.py`; AI still generation is in `app/visuals/visual_assets.py`.

Current b-roll fallback (normal scene):
1. Pixabay video search/download (`PIXABAY_API_KEY`)
2. Pexels video search/download (`PEXELS_API_KEY`)
3. Wikimedia Commons still search/download (no API key)
4. AI-generated still image if a supported provider is configured
5. Gradient/caption or procedural fallback

For some technical MoE scenes, Wikimedia can be tried before stock video. Motion-graphic scenes use local FFmpeg cards/diagrams rather than an image API.

AI still-image provider chain in `visual_assets.py`:
- Pollinations (keyless supported; `POLLINATIONS_API_KEY` raises limits)
- Gemini image (`GEMINI_API_KEY`)
- Cloudflare image (`CF_ACCOUNT_ID` + `CF_API_TOKEN`; default model `@cf/black-forest-labs/flux-1-schnell`)
- fal (`FAL_KEY`)
- Replicate (`REPLICATE_API_TOKEN`)
- OpenAI image (`OPENAI_API_KEY`, paid)
- Wikimedia Commons
- local procedural fallback

**Important code/config gap:** the actual stock chain currently uses Pixabay, Pexels and Wikimedia. Coverr credentials exist in `.env`, but no Coverr client is wired into this path yet. Kling credentials exist, but Kling is not part of this visual chain. FAL/Replicate adapter code exists, but the environment audit did not confirm the exact expected keys.

**Asset metadata:** title, description, tags, dimensions, duration, source URL, author/license/attribution, relevance score and local cached/downloaded path are recorded where the provider exposes them. Stock footage is downloaded and prepared locally before rendering; no continuous live stock streaming is required during FFmpeg assembly.

### Phase I — Render / editing / audio mix

**Code:** `app/render/assembly.py`, `app/render/edit_director.py`, `app/render/shots.py`, `app/render/ffmpeg_tools.py`

- Automated Edit Director creates renderer-independent EDL decisions: source clip, in/out, framing, motion, transition and editorial rationale.
- FFmpeg makes the 1080×1920, 30fps vertical video; clips are normalized/cropped, animated and concatenated.
- Local voice audio is muxed/mixed with optional owner-provided licensed music and generated/configured SFX.
- Captions are burned into the render.
- Music bed is opt-in; `MUSIC_BED_FILE` selects a supplied licensed track, or `MUSIC_BED=on` requests the synthesized bed path.
- This is local compute. FFmpeg/ffprobe do not require a generative video API key.

**Artifacts:** EDL JSON, per-shot intermediates, output MP4, audio mix diagnostics, motion/contact sheets, storyboard and render QA evidence.

### Phase J — Final QA and metadata

**Code:** `app/script/pipeline.py::run_qa`, `app/render/ffmpeg_tools.py::qa_video`, `app/render/edit_director.py::validate_final_output`

- Check duration (45–60 seconds), stream presence, dimensions, frame rate, silence, black frames, clip continuity, visual assets and caption burn-in.
- Check narration/render sync.
- Persist provider counts, fallback scenes, source URLs, evidence ledger, voice provider, caption timing source and QA report in metadata.

**Artifact:** run metadata JSON + QA JSON + EDL/storyboard and contact sheets.

### Phase K — Human review and publishing

**Code:** `app/publish/orchestration.py`, platform uploaders, approval-integrity and authorization modules.

- Review package and approval binding must exist.
- Content quality/freshness and source URLs must pass.
- YouTube OAuth, Meta Facebook Page token and Instagram user token/tunnel requirements are checked.
- Protected authorization is checked before upload.
- Human approval remains mandatory. This audit did not call a real upload endpoint.

**Credentials:** YouTube OAuth client ID/secret and token file; Meta Graph API version, Facebook Page ID/access token, Instagram user ID/access token.

## 3. Current credential inventory — presence only, no secret values

The local `.env` presence check confirmed:
- Text/reasoning: NVIDIA primary + secondary, Gemini, Groq, Cloudflare account ID + API token, OpenRouter, Pollinations; Cerebras key absent; Mistral key absent.
- Stock: Pixabay and Pexels keys present.
- Media APIs not wired into current pipeline: Kling key, Coverr key, InferX key, InstaStudio key, Z API key.
- Image-generation adapters: Pollinations, Gemini, Cloudflare and OpenAI credentials present; expected `FAL_KEY` not present; expected `REPLICATE_API_TOKEN` not confirmed.
- TTS: ElevenLabs/Cartesia/OpenAI optional paths are code-supported; confirm actual presence from the current local `provider_status()` before a run.

Presence is not live authentication or proof of credits. This table deliberately avoids exposing key values.

## 4. Model qualification evidence from this audit

### Repeated exact-model benchmark

The three-task benchmark completed: 5 exact models × 3 tasks × 3 trials = 45 requests.

| Model | Script pass | Evidence pass | Visual-plan pass | Practical reading |
|---|---:|---:|---:|---|
| Groq Qwen 3.8 27B | 2/3 | 3/3 | 3/3 | Strong fast all-round candidate; script consistency not perfect |
| Groq GPT-OSS 20B | 1/3 | 3/3 | 3/3 | Extraction/planning; not primary script writer yet |
| Groq GPT-OSS 120B | 3/3 | 3/3 | 3/3 | Best Groq schema reliability in this run; inspect raw script quality before approval |
| NVIDIA Nemotron Bolt E4B | 0/3 | 3/3 | 0/3 | Fast extraction/evidence classification only |
| NVIDIA Nemotron Lightning 30B A3B | 3/3 | 3/3 | 0/3 | Strong script/evidence candidate but slow (script mean ~29.4s); visual output contract failed |

These are deterministic schema/contract passes, not human editorial quality scores. Raw outputs are under `data/model_benchmark_v1/`; aggregate results are in `data/model_benchmark_v1/latest.json`.

### NVIDIA Nemotron 3.5 Super VL 120B A12B

- Official model supports text, image and sampled-video-frame inputs; text output; up to 1M context in the API reference. NVIDIA's hosted API endpoint is OpenAI-compatible.
- Live text-only request succeeded (HTTP 200, ~2.7 seconds).
- Live image request succeeded (HTTP 200, ~4.3 seconds) and returned a grounded image description after using streaming output; sample described the visible stop sign.
- A previous non-streaming multimodal call hit output-length/reasoning budget behavior; streaming was the successful test method.
- This makes it a strong **visual QA / image understanding / sampled-video review candidate**, not a video generator. It does not generate MP4.
- Still needs repeated tests on NEXTDECODE's own storyboard/contact-sheet and rendered-video frames, and quota/latency checks. NVIDIA trial endpoint quota remains provider-account-specific/unknown.

## 5. Free-first APIs: what to add and what not to add

### Add / wire first — strong fit

| API | Best role | Free terms/limits found | Recommendation |
|---|---|---|---|
| Coverr | Stock video + stock music search | Free API key starts at 50 requests/hour; current `COVERR_API_KEY` already exists | **Highest-priority wiring task**. Adds a distinct stock source without paying for generative video |
| Cloudflare Workers AI image | AI stills / visual cutaways | 10,000 Neurons/day shared free allocation; some frontier models require paid billing | **Keep and use**. Real image-generation call passed (~4.1s, 641 KB) |
| NVIDIA Nemotron Super VL | Visual QA, contact-sheet and sampled-video analysis | NVIDIA prototype/trial endpoint; quota is account/model specific | **Add as visual-QA candidate**, not as a media generator |
| Z.AI GLM Flash | Fast chat/extraction; GLM-4.6V-Flash for vision candidate | Public free model pricing for GLM-4.7-Flash, GLM-4.5-Flash and GLM-4.6V-Flash; rate limits visible in account console | **Test the existing `Z_API_KEY`** and confirm which Z.AI platform/account it belongs to before integrating |

### Use existing APIs; do not add duplicates

- Pixabay: 100 requests per 60 seconds, requires 24-hour query caching, systematic mass downloads are prohibited. Existing key already present.
- Pexels: 200 requests/hour and 20,000/month by default; API is free. New key issuance is currently paused, but the existing key can be used. Attribution is expected and higher limits require approval.
- Wikimedia Commons: keyless image source; retain license/author/page attribution.
- Cloudflare: existing credentials and working image adapter; no new key to add.

### Optional / one-time credits, not ongoing free capacity

- Stability AI: 25 starter credits; image endpoints cost credits per image (e.g. Stable Image Core 3 credits, SD 3.5 Flash 2.5 credits). Good for limited A/B tests, not the primary free-first source.
- Hugging Face Inference Providers: current official docs show no included credits for Free users; do not treat it as an ongoing free API.
- fal and Replicate: pay-per-output APIs; no reliable ongoing free tier found in their official pricing. Do not add as free-first dependencies.

### Video generation APIs — important cost distinction

- Kling official API is available and the configured `KLING_API_KEY` appears to be the right key name. It supports text-to-video, image-to-video and reference-video workflows, including Kling 4.0/4.0 Flash. It is credit/resource-package billed; a trial resource package is offered for integration testing. Not an ongoing free API.
- InstaStudio API credentials exist locally, but its public docs show REST API access on Max/Team plans; free plan has 300 welcome credits for image/edit/audio tools, while video models and API access are plan/credit gated. This is not an ongoing free video API.
- Coverr is the free stock-video choice, not generative text-to-video.
- No major generative video API with reliable unlimited ongoing free usage was verified in this research. Do not build a production dependency on a temporary sign-up credit.

**Recommendation:** keep current stock + local FFmpeg as the zero-cost baseline; wire Coverr first; run a small Kling trial only if the owner wants generated moving shots and accepts credit consumption. Keep generated clips selective (hero shots/mechanism animation) rather than trying to generate the entire 45–60s video.

## 6. Current provider routing change

OmniRoute is removed from active provider routing and health inventory because its gateway is currently offline. Ollama is removed from active routing and health inventory because the owner already retired it. Old `.env` entries may remain but are ignored by the active provider order. No secrets were deleted.

The active hosted chain is owner-configured; invalid/retired names are ignored. Autonomy/local-only mode now fails closed instead of attempting a retired Ollama endpoint.

## 7. Next implementation order

1. Complete visual benchmark for Nemotron Super VL against real NEXTDECODE contact sheets and rendered frames.
2. Test Z.AI key with GLM-4.7-Flash (text) and GLM-4.6V-Flash (vision); read rate limits from its dashboard, not assumptions.
3. Wire Coverr stock-video and audio search into the existing visual asset resolver with attribution, cache, relevance and deduplication. Preserve Pixabay/Pexels/Wikimedia.
4. Implement Kling as an opt-in asynchronous video-generation provider with preflight credit estimate, task polling, download, media probe, rights/provenance and strict budget cap. No automatic use until approved.
5. Reconcile InstaStudio and InferX API credentials with their account-specific base URLs/model/plan; don't assume a global base URL from the key name.
6. Extend per-run provenance so every stage records the exact provider/model/API endpoint, source URL, credential slot, fallback reason, artifact path and hash.

---
## Official references used for free limits and model capabilities

- NVIDIA Nemotron 3.5 Super VL model/API: https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-3_5-super-vl-120b-a12b
- NVIDIA Nemotron hosted API example: https://build.nvidia.com/nvidia/nemotron-3.5-super-vl-120b-a12b
- Cloudflare Workers AI pricing: https://developers.cloudflare.com/workers-ai/platform/pricing/
- Pixabay API docs: https://pixabay.com/api/docs/
- Pexels API limits: https://help.pexels.com/hc/en-us/articles/47677890260761-Is-the-Pexels-API-free-to-use
- Coverr API and free limits: https://coverr.co/developers/
- Kling API quickstart and billing: https://kling.ai/document-api/guides/get-started/quick-start
- InstaStudio API and pricing: https://studio.instadatahelp.com/docs/api
- InferX API quickstart: https://www.inferx.net/docs/quickstart
- Z.AI API docs: https://docs.z.ai/guides/capabilities/mcp-call
- Stability AI pricing: https://docs.stability.ai/pricing
- Hugging Face Inference Providers pricing: https://huggingface.co/docs/inference-providers/pricing
- fal model API pricing: https://fal.ai/docs/documentation/model-apis/pricing


### Additional photo-source recommendation — Openverse

Openverse is the best next keyless photo-source candidate:
- API provides free anonymous access; a registered client ID/secret gives somewhat higher limits.
- It indexes openly licensed/public-domain media and exposes license/creator/source metadata.
- Rate limits apply; anonymous pagination is deliberately bounded.
- It supports images and videos, but every selected asset still needs license eligibility, attribution and provenance checks.
- Recommended role: additional still-image/diagram/photo discovery fallback after Wikimedia; not a substitute for generated cinematic visuals.

Unsplash is technically free with a 50 requests/hour demo limit, but its official API guidelines require hotlinking, download-event tracking and photographer/Unsplash attribution, and emphasize non-automated, authentic experiences. For this automated content pipeline, Openverse is a better fit than adding Unsplash as a dependency.


## 8. Live checks of other already-configured API credentials — 16 Nov 2026

These were safe, bounded requests only. No video/image generation jobs were started for paid services.

| API | Probe | Result | Decision |
|---|---|---|---|
| Coverr | Authenticated GET stock video search | HTTP 200; query `city` returned 3 hits (1,097 total matches) | **Verified working; wire into stock-video resolver first** |
| InstaStudio | GET `/account` and `/models` | Both HTTP 401, invalid/missing API key | The env key is present but not accepted by this API. Confirm which service issued `INSTUDIO_API_KEY`; no generation was attempted |
| Z.AI GLM-4.5-Flash | Text chat request | HTTP 200; answered MoE-router prompt | **Working free-chat candidate** |
| Z.AI GLM-4.7-Flash | Text chat request | HTTP 429, provider error 1305 (temporarily overloaded) | Retry later; do not mark the key invalid |
| Z.AI GLM-4.6V-Flash | Image-understanding request | HTTP 200; described visible objects/text in sample image | **Working vision candidate** |
| InferX | Not called | Key exists, but account-specific base URL and model ID are not in config | Need console endpoint/model before a valid request can be made |
| Kling | No generation call | Key exists; official docs confirm resource-package billing | Avoid accidental credit consumption; first inspect balance/resource package in Kling developer console |

The Coverr first query for a niche technology phrase returned zero hits but HTTP 200; a generic `city` query returned three. This was a query coverage issue, not an authentication failure.

Z.AI recommendations:
- `glm-4.5-flash`: candidate for fast, free text tasks.
- `glm-4.6v-flash`: candidate for visual QA / image understanding.
- `glm-4.7-flash`: do not rely on it as primary until provider overload stabilizes and account-console rate limits are checked.

The exact probe evidence is stored in `data/provider_probes/coverr_zai_followup.v1.json`.
