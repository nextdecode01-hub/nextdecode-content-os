# NEXTDECODE Engine — Data Source, API & Model Routing Map
**Audit date:** 16 November 2026  
**Repository:** `/home/demon/shorts_studio`  
**Status:** Code-path inspection completed; live provider probe running / results to be appended.  
**Purpose:** Explain where each pipeline stage obtains information, which credentials/endpoints it uses, how data moves between stages, and what is actually verified.

## 1. How to read this map

These statuses are deliberately separate:

- **Configured:** required environment settings exist.
- **Code path present:** source code contains an integration.
- **Live API tested:** an actual request was made and returned a recorded result.
- **Task qualified:** the integration completed the real task shape and passed the relevant schema/quality checks.
- **Production approved:** owner explicitly approved its use for production.

A configured provider is not necessarily reachable. A successful HTTP response is not proof of useful content quality. A model passing a JSON smoke test is not proof that it can reliably produce a publishable NEXTDECODE Short.

Secrets are never included here. This document lists environment-variable *names* only.

## 2. End-to-end data flow

```text
Topic discovery
  ├─ Google Trends / RSS or public feed adapters (where implemented)
  ├─ Hacker News Firebase API
  ├─ arXiv Atom API
  └─ Reddit RSS
       ↓ topic candidates + source URLs
Research desk
  ├─ HTTP GET public article/source URLs
  ├─ HTML text extraction and cleanup
  └─ claim/evidence ledger with quote + source URL
       ↓ evidence-backed research bundle
LLM provider layer
  ├─ OmniRoute gateway
  ├─ Gemini / Groq
  ├─ Pollinations / NVIDIA NIM / Cloudflare / OpenRouter
  ├─ Mistral / Cerebras / local Ollama
  └─ direct-only OpenAI / Anthropic paths
       ↓ structured script, metadata, plans (depending on caller)
Voice generation
  ├─ Edge TTS
  ├─ local Kokoro
  ├─ optional ElevenLabs / Cartesia / OpenAI TTS
  └─ diagnostic-only silent tone
       ↓ narration audio
Visual planning and asset resolution
  ├─ narration beats / visual intent / storyboard
  ├─ stock provider search and licensed source cutouts
  └─ downloaded/cached media + attribution
       ↓ selected local assets
Render / edit
  ├─ local source media + generated graphics
  ├─ FFmpeg / ffprobe
  ├─ captions, voice, music and SFX
  └─ EDL + render QA
       ↓ output MP4 + metadata + review artifacts
Human review / approval
       ↓ protected publish authorization
YouTube / Instagram / Facebook APIs
```

The diagram is a logical flow, not a claim that every optional integration is active in every run.

## 3. Topic discovery — where candidate ideas come from

**Primary code:** `app/research/topics.py`, `app/research/desk.py`

Observed source adapters in `topics.py`:

| Source | Data obtained | Access method | Credential |
|---|---|---|---|
| Hacker News | Top-story IDs, title, URL, timestamp, score | `https://hacker-news.firebaseio.com/v0/topstories.json` and `/v0/item/{id}.json` | None |
| arXiv | Recent AI/ML/CL/CV paper titles, abstracts, links, dates | `https://export.arxiv.org/api/query` (Atom) | None |
| Reddit | Subreddit feed entries via RSS | `https://www.reddit.com/r/{subreddit}/.rss` | No API key in this RSS path |
| Google Trends | Feed adapter is referenced in topic-ranking logic; actual fetch implementation must be verified before claiming live data | Check current implementation/feature flag | Not established by this inspection |

Candidates are ranked using topical relevance, source weight, freshness and engagement signals. This is discovery/ranking, not factual verification.

**Important implementation note:** `app/research/desk.py` contains legacy placeholder feed functions that return empty lists for Google Trends, Hacker News, Reddit and arXiv. The active feed implementations are in `topics.py`; do not confuse those placeholders with the actual discovery adapters.

## 4. Research and source retrieval

**Primary code:** `app/research/desk.py`

- Research desk receives source URLs and fetches each URL directly using Python `requests.get`.
- It uses a project User-Agent, 25-second default timeout and bounded text extraction (12,000 chars by default).
- HTML is converted to text; page furniture/navigation is removed; article title and publisher host are retained.
- arXiv abstract pages have a dedicated extraction path.
- Claims are extracted from retrieved text and associated with verbatim quotes and the original source URL.
- HTTP 401/403/406 is retried with a different Accept header; persistent refusal becomes blocked/manual-review-required. It does not claim to bypass paywalls or access controls.
- PDF and unsupported content types are not silently treated as verified article text.

**Credential model:** Public web retrieval does not use an LLM API key. It is direct HTTP access to source websites/APIs.

**Data handoff:** source records and claim/evidence artifacts are persisted under the run's data/artifact paths; the script/evidence layer consumes this material. Exact runtime filenames are run-specific and should be read from the manifest for each run.

## 5. LLM model/provider layer

**Primary code:** `app/providers/multi_model_ai.py`, `app/providers/omniroute_client.py`, `app/providers/model_health.py`

### Automatic provider chain

The current adapter inventory is:

| Provider | Endpoint / route | Credential environment names | Notes |
|---|---|---|---|
| OmniRoute | Local OmniRoute gateway; configured base URL/model chain | OmniRoute settings in `.env` (inspect names in local config; do not publish values) | First in configured provider order |
| Gemini | Google Generative Language API through SDK/client | `GEMINI_API_KEY` | Model chain can contain fallback models |
| Groq | Groq OpenAI-compatible API | `GROQ_API_KEY` | Model chain can contain fallback models |
| Pollinations Text | `https://text.pollinations.ai/openai` by default | Keyless in current adapter | Best-effort fallback; addressability is not health |
| NVIDIA NIM | `https://integrate.api.nvidia.com/v1` / chat completions | `NVIDIA_API_KEY`, `NVIDIA_API_KEY_2` | Two configured keys are attempted sequentially |
| Cloudflare Workers AI | Account-specific Workers AI endpoint | `CF_ACCOUNT_ID`, `CF_API_TOKEN` | OpenAI-compatible adapter |
| OpenRouter | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` | Quota/account free-tier limits may block requests |
| Mistral | `https://api.mistral.ai/v1` | `MISTRAL_API_KEY` | OpenAI-compatible adapter |
| Cerebras | `https://api.cerebras.ai/v1` | `CEREBRAS_API_KEY` | OpenAI-compatible adapter |
| Ollama | Local configured base URL | `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | Local model; only considered configured when both are explicitly set |

The provider order is owner-configured through `AI_PROVIDER_CHAIN` (unknown/duplicate names are ignored); default chain is defined in `multi_model_ai.py`. `NEXTDECODE_AUTONOMY_MODE` forces Ollama-only routing for autonomous workers. Health/quota controls include `AI_HEALTH_GATE` and emergency `AI_IGNORE_HEALTH`.

### Direct-call integrations (not automatic free-first members)

- OpenAI direct path: `OPENAI_API_KEY`
- Anthropic direct path: `ANTHROPIC_API_KEY`

Their presence in the code does not make them eligible for automatic routing or authorize paid use.

### Model selection and health

- Model defaults and fallback model chains are resolved from environment variables and code defaults.
- `GET /providers/inventory` is a **read-only snapshot**. It does not contact providers.
- `GET /providers/portfolio` is a **read-only snapshot** joining model candidates, qualification, usage and quota data. It does not call providers during dashboard polling.
- `probe_all()` explicitly calls configured provider APIs and persists health results.
- `qualify_portfolio()` calls exact candidate models, rather than silently switching to another model in that provider's chain.
- Health is stale after 24 hours; recent failures have a six-hour cooldown.
- Automatic 90% quota suppression is only allowed when provider-published remaining and limit counters are both available. Missing counters mean **unknown**, not zero or unlimited.

### Candidate portfolio — current position

- Target final production roster: 10 models.
- Current candidate pool: 11 (NVIDIA has two provisional candidates).
- Automatic selection is disabled; owner approval is required.
- NVIDIA Bolt is a fast extraction/evidence-classification candidate, not approved as script writer.
- NVIDIA Lightning is a slower quality candidate; repeat trials and editorial scoring remain necessary.
- Groq had three successful first-pass schema probes, but those earlier outputs were shorter than the updated 92–118 word Shorts requirement; do not use the old pass as final qualification.
- Gemini, OpenRouter, Cloudflare and other failures must be re-tested only after checking SDK/model IDs/quota and the current probe evidence.
- Existing qualification records are snapshots, not guarantees of present-day availability.

## 6. Script, evidence, and metadata handoff

**Primary code:** `app/script/pipeline.py`, `app/script/studio.py`, `app/script/evidence.py`

- Script generation consumes the research/evidence context and calls the shared LLM provider layer.
- Evidence reconciliation checks script claims against the research ledger.
- The production output is structured metadata (title, hook, voice text, tags, platform copy, source URLs and related fields).
- Qualification now checks a 92–118-word voice-text target, exact hook/first-sentence match, title length and non-empty string tags. This is a model qualification gate, not a rewrite of the production script profile.
- Per-run artifact manifests are the evidence of what a particular run actually consumed and produced.

## 7. Voice generation

**Primary code:** `app/voice/provider.py`

Priority order documented in the provider:

1. Edge TTS — Microsoft Edge neural TTS service; no project API key in this path.
2. Kokoro local — local neural TTS; no API key.
3. ElevenLabs — optional hosted TTS; `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`.
4. Cartesia — optional hosted TTS; `CARTESIA_API_KEY`, `CARTESIA_VOICE_ID`.
5. OpenAI TTS — optional paid path; `OPENAI_API_KEY`.
6. Silent tone — diagnostic only; not acceptable production narration.

Default voice in code: `en-US-AndrewMultilingualNeural`, overridable by `TTS_VOICE`. TTS provider/model can be overridden with `TTS_PROVIDER` and `TTS_MODEL`; Edge prosody controls include `TTS_RATE`, `TTS_PITCH`, `TTS_VOLUME`.

Voice generation writes local audio artifacts; rendering consumes the selected narration audio file.

## 8. Visual assets and source material

**Observed code:** `app/visuals/stock_fetcher.py`, `app/visuals/chain.py`, `app/visuals/visual_assets.py`, `app/visuals/vision_review.py`

- Wikimedia Commons integration is directly visible in `stock_fetcher.py`: `https://commons.wikimedia.org/w/api.php`, no API key, 24-hour search cache, image dimensions, description, author, license and attribution metadata.
- Visual resolution is called from `app/render/assembly.py` through the visual chain. Narration/shot plans are resolved to local assets or procedural/generated visual paths.
- Evidence cutouts can use original source excerpts with claim IDs, rights evidence and attribution.
- Pixabay/Pexels integrations are part of the existing visual workstream and must be inventoried from the current parallel-owned implementation before this map is considered exhaustive. Do not assume a provider is active merely because an older plan mentions it.
- Vision review is a separate service path from stock search. Its exact provider/model and credentials must be taken from its current implementation/config; it is not the same as the text-generation provider chain.
- Downloaded assets are local files; rendering should consume those local paths, not re-fetch media during FFmpeg assembly.

## 9. Rendering, music and SFX

**Primary code:** `app/render/assembly.py`, `app/render/edit_director.py`, `app/render/ffmpeg_tools.py`, `app/render/subtitles.py`

- Rendering is primarily local processing with FFmpeg/ffprobe. It does not require an LLM API key for the actual encode/mux step.
- Inputs include local voice audio, local video/image assets, edit decisions/EDL, subtitle/caption files, and optional music/SFX assets.
- EDL carries clip/source timing and editorial decisions; final QA checks media streams, duration, dimensions, frame continuity and related render constraints.
- Music/SFX may use local synthesis or configured assets; provider/source specifics should be recorded in each run manifest and current audio subsystem implementation.
- Production render is blocked unless `STORYBOARD_GATE=require`; dry-run is distinct from production.
- The render output, QA evidence, EDL and manifest are the artifacts to inspect when diagnosing visual quality.

## 10. Publishing and platform APIs

**Primary code:** `app/publish/orchestration.py` and platform uploaders.

| Platform | API | Credential names / auth | Key safety |
|---|---|---|---|
| YouTube | YouTube Data API upload | `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, OAuth token file `youtube_token.json` | OAuth; uploader requires current approval/governance |
| Facebook Reels | Meta Graph API `/{page_id}/video_reels` | `META_GRAPH_API_VERSION`, `FACEBOOK_PAGE_ID`, `FACEBOOK_PAGE_ACCESS_TOKEN` | Protected authorization + digest-pinned upload snapshot |
| Instagram Reels | Meta Graph API | `META_GRAPH_API_VERSION`, `INSTAGRAM_USER_ID`, `INSTAGRAM_ACCESS_TOKEN` | Requires publisher-owned digest-pinned tunnel; unverified external video URL is rejected |

Publishing orchestration is review-only unless the owner explicitly enables the publish mode and approval requirements are satisfied. The current project operating policy remains human approval before publishing and public auto-publishing disabled. Do not run a real upload as part of API qualification.

## 11. What is known vs still to verify

### Established by code inspection
- Topic source adapters and direct public URL fetch architecture.
- Evidence extraction is separate from LLM inference.
- Automatic LLM provider adapter inventory and key variable names above.
- Voice provider order and optional credentials.
- Wikimedia Commons keyless source path.
- FFmpeg-based local rendering.
- YouTube/Meta publishing APIs and credentials.
- Provider inventory/portfolio endpoints are read-only and do not probe APIs.

### Not yet fully established
- Whether every provider listed in the chain is currently configured in this machine's `.env` (must read booleans only; never values).
- Whether every provider API currently responds successfully. Live probe results are appended in the qualification report when complete.
- Exact live Google Trends adapter status.
- Complete Pexels/Pixabay implementation and active key names (parallel visual workstream owns these files).
- Vision-review provider/model and quota details.
- Exact music/SFX provider path and current external API use.
- Context-window and max-output limits for each shortlisted model where providers do not expose them in model catalog metadata.
- Whether a given run actually used the configured first provider or fell back. Confirm through per-run logs/manifest, not configuration alone.

## 12. Operator rule: never infer the source

For every production run, record:
- process/stage name;
- provider and exact model actually called;
- endpoint/adapter identifier (no secret);
- credential slot name (never credential value);
- request/task ID and timestamp;
- response status and latency;
- input/output token usage when provider returns it;
- quota headers/counters when provider returns them;
- artifact path + SHA-256;
- fallback reason and next provider;
- schema/quality gate outcome.

If a provider does not return a field, record `unknown`. Do not derive remaining quota from local token usage, and do not label an API connected merely because a key exists.

---
**Owner decision required before:** changing provider order/defaults, replacing configured models, enabling paid providers, changing credentials, publishing, or promoting candidates into production.


## 13. Live provider API probe — 16 November 2026

A deliberate `probe_all(timeout=35)` run was executed against all ten automatic-chain adapters. Results were saved separately to `data/model_health.live_audit.json` (the normal health snapshot was not overwritten).

| Provider | Configured | Probe result | Latency | Interpretation |
|---|---:|---|---:|---|
| OmniRoute | Yes | `RuntimeError` | 2 ms | Adapter/configuration failed before a valid workload response; inspect local gateway/base URL/model. |
| Gemini | Yes | `ImportError` | 0 ms | Python SDK/import dependency issue; not a provider-side rejection. |
| Groq | Yes | JSON valid, schema mismatch | 1.33 s | API responded, but output did not satisfy the 92–118-word production Shorts contract. |
| Pollinations Text | Yes | `ReadTimeout` | 35.35 s | No usable response within bounded timeout. |
| NVIDIA NIM (configured Gemma model) | Yes | `RuntimeError` | 35.36 s | Configured Gemma model timed out/fell through both configured NVIDIA keys in this probe. This does not invalidate the separately tested Nemotron IDs. |
| Cloudflare Workers AI | Yes | JSON valid, schema mismatch | 4.17 s | API responded, but output did not satisfy required script schema/length. |
| OpenRouter | Yes | `RuntimeError` | 1 ms | Probe could not return a usable response; previous explicit account quota check showed free-model daily allowance exhausted. |
| Mistral | No | `not_configured` | — | No live request made. |
| Cerebras | No | `not_configured` | — | No live request made. |
| Ollama | No | `not_configured` | — | No live request made. |

**Interpretation:** 10 adapters enumerated; 7 configured; 3 not configured; none passed this particular shared script probe. Groq and Cloudflare did respond with JSON, but failed the workload contract. This is not a generic connectivity benchmark: it deliberately tests the current script-shaped JSON task. NVIDIA's separate Nemotron tests remain distinct evidence.

The probe script was bounded and wrote a separate evidence snapshot. It did not alter provider defaults, credentials, routing order, or production settings.

## 14. Repeated task benchmark (in progress)

A repeatable exact-model benchmark runner is now present at `qualify_models_benchmark.py`. It runs three identical task families for three trials each against five shortlisted exact model IDs (45 requests total):
- 92–118-word Short script generation;
- evidence discipline / supported-vs-unsupported claim classification;
- five-shot visual planning with distinct visual intents.

It saves each raw response under `data/model_benchmark_v1/`, records latency and deterministic schema/contract checks, and aggregates pass counts/scores. Provider usage metadata is recorded as unknown where the shared client does not expose it. This benchmark is qualification-only and does not change production routing or defaults. Final editorial quality still needs human review of saved raw outputs.


## Owner corrections and 16 Nov 2026 follow-up

The owner confirmed:
- Gemini free quota is exhausted quickly; do not treat it as high-volume primary.
- Grok free quota is also limited; treat as quota-constrained.
- OmniRoute gateway is currently offline and is retired from active routing.
- Ollama was already removed by the owner and is retired from active routing.
- NVIDIA Nemotron Super VL is a priority multimodal candidate.
- Cloudflare was added today by the owner and requires both `CF_ACCOUNT_ID` and `CF_API_TOKEN`.
- Cerebras API key is not configured.

**Runtime change made:** OmniRoute and Ollama were removed from the active `PROVIDER_ORDER`, model-health supported provider inventory and setup readiness check. The autonomy/local-only flag now fails closed rather than routing to retired Ollama. Existing secret entries in `.env` were not deleted; they are ignored by active routing. No paid-provider defaults were changed.

**Cloudflare re-test:**
- Both `CF_ACCOUNT_ID` and `CF_API_TOKEN` are present.
- Text: `@cf/meta/llama-3.3-70b-instruct-fp8-fast` returned valid JSON in ~3.4s but only 46 spoken words, so failed NEXTDECODE's 92–118-word script gate.
- Image: `@cf/black-forest-labs/flux-1-schnell` returned a valid image (~641 KB) in ~4.1s. Cloudflare image generation is working.
- Official free allocation: 10,000 Neurons/day shared across Workers AI; not a request count. Some models require paid billing.

**NVIDIA Nemotron Super VL:**
- Added as provisional visual-QA candidate; candidate pool is now 12, final target remains 10.
- Text-only request passed (HTTP 200, ~2.7s).
- Image request passed using streaming response (HTTP 200, ~4.3s), with grounded description of the visible stop sign.
- This is a vision-language model for visual QA, sampled-video-frame analysis, document/image understanding and reasoning; it is not a generative video endpoint.
- A non-streaming multimodal call exhausted its output budget in reasoning and returned no final content; streaming is the tested successful request pattern.

**Other existing API keys discovered in local environment (presence only):** `KLING_API_KEY`, `COVERR_API_KEY`, `INFERX_API_KEY`, `INSTUDIO_API_KEY`, and `Z_API_KEY` are present but are not referenced by the current active app/pipeline modules. Coverr is a free stock video/music API with 50 requests/hour; it is the strongest free video-source addition. Kling is a credit/resource-package billed generative video API with a trial package, not an ongoing free tier. InstaStudio's API is plan/credit gated. InferX requires account-specific base URL and model ID from its console. Z.AI free GLM Flash models merit a controlled test if the key belongs to Z.AI's international API.


## 16 Nov API credential follow-up

- Coverr: authenticated stock-video search passed (HTTP 200, 3 results for `city`). The API key is already configured; no need to request another one.
- Z.AI: `Z_API_KEY` successfully authenticated. GLM-4.5-Flash text chat passed; GLM-4.6V-Flash image understanding passed; GLM-4.7-Flash returned a temporary 429 overload.
- InstaStudio: `INSTUDIO_API_KEY` is present but official API `GET /account` and `GET /models` both returned 401. Do not claim it is connected; confirm key origin/account plan.
- InferX: `INFERX_API_KEY` is present, but its console-specific base URL and model ID are absent, so a valid endpoint cannot be guessed.
- Kling: `KLING_API_KEY` is present. No generation call was made because it may consume paid resource credits. Check resource balance in the official console before testing.

## 16 Nov 2026  visual source credential and adapter reconciliation

The local .env presence audit was performed without reading or printing secret values:
- Configured: Pixabay, Coverr, Gemini, Groq, OpenRouter, Cloudflare (account ID + token), Z.AI, Kling.
- Not configured: Pexels, OpenAI, Anthropic, ElevenLabs, Cartesia, Fal, Replicate, YouTube Data API and Trends API.
- InstaStudio credential is present but its saved account/models probes returned HTTP 401; it is not an active provider.
- InferX credential is present but its endpoint/base URL and model ID are missing; it is not wired.
- Kling credential is present, but generation remains disabled under the zero-budget policy.

Pexels was removed from the active runtime source chain and its empty .env entry removed. Coverr is now the second stock-video source after Pixabay, using the existing COVERR_API_KEY and app.providers.media_sources.search_coverr_videos() adapter. The saved credential probe recorded HTTP 200 and three results for a city search; this proves search reachability at probe time, not current quota or every-query availability.

Openverse is integrated as a keyless still-image fallback after Wikimedia. Only non-mature results marked for commercial use are considered; title, creator, source URL, licence, licence version, licence URL and attribution are retained. OPENVERSE_ENABLED=true explicitly enables the external search in this workspace. Openverse results still require visual review and licence/attribution review; metadata matching is not visual-semantic proof.

Z.AI (Z_API_KEY) has saved successful text and image-understanding probes, but it is not silently promoted into automatic production routes. Task-specific qualification and the existing human-review policy remain required. No Kling generation, paid job, publishing, upload, or provider-quota probe was performed in this reconciliation.
