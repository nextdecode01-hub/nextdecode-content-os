# Nextdecode Shorts & Reels Studio (WSL)

Research-led vertical videos for Nextdecode. The full pipeline researches current AI/technology topics, creates an original short script, narration and captions, renders and checks a 1080×1920 MP4, then cross-posts to YouTube Shorts, Facebook Reels, and Instagram Reels when every destination is ready.

## Project files

- app/research/topics.py — topic discovery and repeat avoidance.
- app/research/trends.py — multi-source trending-topic discovery and heat ranking.
- app/script/short.py — short-form script generation and script validation.
- app/script/pipeline.py — the strong editorial chain that `pipelines/short.py --quality strong` runs.
- pipelines/short.py — short-video entrypoint: script, voiceover, B-roll, subtitles, render, and quality checks.
- pipelines/longform.py — long-form entrypoint: chapter visuals, narration, render, and QA.
- app/research/selector.py — scores candidate topics on seven editorial dimensions and picks the best one.
- app/research/desk.py — fetches and actually reads the sources, extracts verbatim claims, flags unsupported numbers and contradictions.
- app/script/studio.py — generates hook candidates, scores them, writes a beat sheet, and runs a critic loop that rewrites until the script passes.
- app/script/voice_guide.py — hook archetypes, channel voice, and the AI-slop ban list.
- app/script/longform.py — research-backed long-form topic selection, source validation, and script generation.
- app/voice/provider.py — pluggable TTS chain (Edge TTS → ElevenLabs → Cartesia → OpenAI → silent). Production voice is `en-US-AndrewMultilingualNeural` (approved in Phase 9); `TTS_VOICE`, `TTS_RATE`, `TTS_PITCH` and `TTS_VOLUME` still override it, and prosody defaults stay neutral. Edge renders 24 kHz / 48 kbps mono, so the narration is decoded once into a 44.1 kHz 24-bit WAV master (`to_wav_master`) and the deliverable is written at 320 kbps CBR (`export_master_mp3`).
- app/voice/text_prep.py — speech-friendly normalization (abbreviations, `%`, `N+1`, acronyms, long-sentence splits). Used by the opt-in `TTS_TEXT_PREP=on` path and by the Phase 8 A/B test.
- app/research/lineage.py — canonical URLs, wire/press-release detection and shingle clustering. Republished copies are one voice; independence is counted per publisher, and a report that only repeats an announcement does not count as confirmation.
- app/research/claims.py — durable claim ledger: stable claim IDs, verbatim excerpt with offset, source metadata and dates, verification status, decision, script mapping and a digest that invalidates stale approvals. Missing fields stay empty and are flagged; nothing is invented.
- app/research/atomic.py — splits a compound claim into verbatim clauses so each fact is checked on its own; every piece must be a substring of its parent sentence.
- app/script/evidence.py — maps narration sentences to claim IDs and flags wording that outruns the evidence (causation, forecast-as-fact, numbers absent from the excerpt, unsupported factual sentences).
- app/visuals/cutouts.py — balanced source cutouts: rendered excerpt cards with publisher/date/URL for key claims, a reuse-rights gate that blocks unknown rights from publish-ready, and a budget that never places two cutouts back to back.
- app/visuals/motion_director.py — plans the edited shot list and assigns scene-aware motion after assets resolve: native crop for real video, eased Ken Burns for stills, low-amplitude pushes for UI/text/chart scenes, with cut-to-cut scale continuity. Per-cut transition SFX are opt-in via `SHOT_SFX=on` and off by default.
- app/visuals/chain.py — builds the structured scene brief for every shot and resolves it through the provider chain (stock video, Wikimedia stills, AI image, procedural card), recording lexical relevance confidence, semantic-review flags and fallback reasons. Duplicate figures become a narration-derived recap card instead of unrelated b-roll; dark/flat stock clips and stills whose titles share only generic terms are rejected. Tag overlap is never reported as semantic understanding.
- app/visuals/vision_review.py — optional, opt-in vision review of selected assets. Disabled unless `VISION_REVIEW_PROVIDER=gemini` and `GEMINI_API_KEY` are configured; the offline lexical validator remains the default.
- app/visuals/storyboard.py — pre-render storyboard: writes `storyboard.json` plus a 4-column contact sheet from the selected assets, records provenance and review reasons, and enforces an optional review gate before rendering. After rendering it also writes `storyboard/motion_sheet.jpg` with start/mid/end frames for every shot.
- app/render/assembly.py — assembles the multi-shot video: scene-aware motion, kinetic captions, music bed, optional SFX and the ffprobe/FFmpeg QA pass. Mixing is voice-first: the narration is normalized with a measured two-pass linear `loudnorm` (no dynamic gain-riding), the bed is off unless `MUSIC_BED=on` or `MUSIC_BED_FILE=<path>`, ducking is a gentle 3:1 sidechain with no makeup gain, and the master limiter runs with `level=false` so it can only ceiling, never auto-raise. Delivery bitrate comes from `AUDIO_BITRATE` (default 320k).
- app/render/audio_diagnostics.py — measures short windows around every cut and flags a sustained noise burst or an isolated sample jump, so a click/pop/whoosh regression is visible in metadata and QA.
- app/render/subtitles.py — kinetic ASS captions. Caption spelling is aligned to the authored script while word timings come from ASR, so names such as “GrayGaps” are not replaced by a mishearing.
- app/visuals/stock_fetcher.py — key-free real-photo sourcing from Wikimedia Commons with licence attribution.
- `app/visuals/motion_director.py`, `app/visuals/stock_fetcher.py`, `app/visuals/visual_assets.py`, `app/visuals/visual_quality.py` — canonical visual modules.
- `app/providers/model_health.py` — probes configured LLM providers and records provider health.
- `run_pipeline.sh` — runs `pipelines/short.py`, creates a review package and notifies the owner; publishing remains separately gated.
- `run_scheduled_generation.sh` — generates a Short daily and long-form video on Wednesday/Saturday in review-only mode.
- `app.publish.scheduler` — runs the 20:00 IST upload checks for today's exact owner-approved content.
- `app.security.approval_integrity` — binds approvals to rendered-video and metadata hashes and the current IST day.
- `app.notifications.notify_review` — sends a private Telegram review reminder with the local preview path and module-based approval command.
- `app.publish.youtube_upload`, `facebook_reels_upload`, `instagram_reels_upload` — canonical platform publishers.
- `app.publish.orchestration` — validates fresh metadata, video, credentials and all destinations before upload; refuses partial cross-posts when setup is incomplete.
- `setup_check.py` — safe setup report; never prints credential values or publishes, and distinguishes required setup blockers from optional integrations.
- `app.notifications.notify_status` — sends generic generation/publishing status alerts to the configured Telegram chat; it never includes credentials or OAuth codes.
- Root Python entrypoints are limited to `setup_check.py`; forwarding/compatibility wrappers have been retired.
- .env — private local credentials. Never paste keys into chat or commit this file.
- docs/META_REELS_SETUP.md and docs/REQUIRED_SETUP.md — platform and account setup steps.
- docs/ — planning, provider status, monetization, and setup notes (see also docs/ROADMAP.md).

When TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are configured, generation failures, publishing blockers, and publish results are sent to that Telegram chat. Alerts are best-effort and do not change publishing outcomes.

### Canonical package layout and entrypoints

Canonical code lives under `app/`:

| Area | Canonical module |
|---|---|
| Topic selection and research | `app/research/selector.py`, `app/research/desk.py` |
| Script generation | `app/script/studio.py`, `app/script/pipeline.py` |
| Shot planning | `app/visuals/motion_director.py` |
| Scene briefs and asset resolution | `app/visuals/chain.py` |
| Pre-render storyboard and review gate | `app/visuals/storyboard.py` |
| Rendering, audio and QA | `app/render/assembly.py`, `app/render/ffmpeg_tools.py`, `app/render/legacy_api.py` |
| Publishing | `app/publish/` — platform upload adapters and multi-platform social orchestrator |
| Operational utilities | `app/operations/` — analytics collection, Meta preflight, monetization tracking, feedback ledger, video archive and workspace sync |
| Notifications | `app/notifications/` — outbound Telegram status and manual review reminders; no inbound approval callbacks |
| LLM providers | `app/providers/` — shared generation client, model health and OmniRoute adapter |
| Run tracking | `app/tracking/` — run identity, manifest lifecycle, artifact hashes and promotion journal |

`app/render/legacy_api.py` contains the retained adapter for older render APIs; the root forwarding file has been retired. Visual and render implementations remain canonical under `app/visuals/` and `app/render/`. The other root-level forwarding/compatibility Python wrappers have been retired. Do not recreate them.

Operations, notifications, provider clients, tracking, publishing, approval and review implementations now live only in their canonical `app.*` packages (with maintenance commands under `tools/`). Shell scripts invoke canonical package modules with `python -m`; no root import aliases are required. Root Python entrypoints are limited to the standalone `setup_check.py`.


## The strong pipeline

`pipelines/short.py --quality strong` (the default) runs the full editorial chain instead of the legacy single-pass path:

    topic_selector  ->  research_desk  ->  script_studio  ->  app.voice.provider
                   ->  motion_director  ->  motion_render  ->  QA

| Stage | What it does | Fails closed when |
|---|---|---|
| `topic_selector` | Scores candidate topics on demand, channel fit, visual feasibility, undersaturation, novelty, timing and risk, and applies the analytics feedback loop. | No candidate clears `min_topic_score` (default 55). |
| `research_desk` | Fetches the candidate sources, reads them, keeps only pages that are actually about the topic, and extracts claims with verbatim quotes. | The primary source cannot be fetched or no verifiable claim exists. |
| `script_studio` | Generates one hook per archetype, scores them, writes a timestamped beat sheet, then runs a critic loop that rewrites the script while it contains unsupported numbers, slop, a generic hook, or a wrong word count. | The script still fails the critic after the rewrite budget. |
| `app.voice.provider` | Speaks the script through the TTS chain. | No provider produced audio. |
| `motion_director` | Cuts the runtime into 8–14 shots and assigns motion by scene type: real video keeps its native motion at a fixed crop, stills get an eased Ken Burns move, and UI/text/chart scenes get a small readable push. Cut-to-cut scale is continuous. Transition SFX are off unless `SHOT_SFX=on`. | — |
| `app/visuals/chain.py` | Builds a scene brief per shot (purpose, scene type, query variants, on-screen text, fallback chain) and resolves stock video, Wikimedia stills, AI images or a procedural card. Stock is capped below half of the shots and reused assets are skipped. Duplicate figures become a narration-derived recap card instead of unrelated b-roll; dark/flat clips and generic title-only still matches are rejected. Each selection gets a lexical relevance confidence (`high`/`medium`/`low`/`none`), matched terms and a `semantic_review` flag; stock and stills are explicitly marked as needing visual review rather than semantic verification. Every fallback records its reason. | — (falls back and reports the reason). |
| `storyboard` | After assets are resolved but before the full render, writes `storyboard/storyboard.json` and `storyboard/contact_sheet.jpg`, with scene ID, narration, provider, confidence, fallback and review reasons. `STORYBOARD_GATE=require` blocks `needs_review` or `blocked` plans; an explicit human approval file can unlock them. After rendering, `storyboard/motion_sheet.jpg` shows start/mid/end frames for every shot. | Strict gate is on and no valid approval exists. |
| `motion_render` | Renders every shot with scene-aware motion, burns kinetic word-level captions, mixes a music bed under the voice, and optionally adds SFX (`SHOT_SFX=on`). Caption spelling is aligned to the script; ASR supplies only word timing. | The render fails QA. |
| `qa_video` | Re-probes the finished file with ffprobe and FFmpeg: resolution, frame rate, duration, audio presence and loudness, black/frozen stretches, duplicate assets, caption timing and audio click/whoosh signatures at shot cuts. | Wrong resolution/fps, missing or silent audio, duration drift, or missing captions. |

Audio mix failures no longer pass silently: if the music/SFX mix cannot be produced, the render keeps the voice track, sets `voice.mix_mode=voice_only`, and records a warning in the metadata. Caption burn-in failures retry without captions and are reported the same way. A successful FFmpeg exit code is not treated as success by itself — the output must pass `qa_video`.

Visual QA now reports `semantic_review`, `low_confidence` and `low_light` counts. Stock and stills remain lexical/title matches and carry a review warning; the optional vision reviewer can be enabled with `VISION_REVIEW_PROVIDER=gemini` and a Gemini key. It never runs by default, never logs the request URL or key, and leaves the existing lexical gate in place when unavailable.

Audio QA now measures the first 50 ms and the following 650 ms of every cut. A sustained high-frequency burst (the old per-cut whoosh) or an isolated sample jump is reported per boundary. Per-cut transition SFX are disabled by default because they read as an extra sound; set `SHOT_SFX=on` to restore the old impact/whoosh design. Stock clip audio is never used: every shot is rendered with `-an`, so the only audio sources are narration, the music bed and optional SFX.

Motion QA writes `storyboard/motion_sheet.jpg` after rendering. Real video keeps its source motion at a fixed crop; stills use an eased Ken Burns move whose start scale equals the previous shot's end scale, so cuts do not snap. The earlier `zoompan d=<frames>` filter froze video on its first frame; the renderer now uses `d=1` for video and a separate scale/crop path for native footage.

Before a full render, the storyboard stage writes a contact sheet and an explicit review state. `STORYBOARD_GATE=require` (default) stops before rendering when the storyboard is not approved; `STORYBOARD_GATE=warn` is an explicit opt-out that reports `needs_review`/`blocked` plans and continues. After inspecting the contact sheet, approve it explicitly with:

```bash
./venv/bin/python -m app.visuals.storyboard outputs/<run>/storyboard/storyboard.json --reviewer "Anish" --note "reviewed contact sheet"
```

The approval is bound to the contact-sheet hash. A missing approval, a changed contact sheet, or a `blocked` plan does not count as approved.

Visuals come from licensed stock when a Pexels or Pixabay key is present, otherwise from Wikimedia Commons (free, no key) with the licence, author and file page recorded in `metadata.json` under `visuals.assets`. AI images are used when an image provider is available and is quota permitting. Shots that find no real image fall back to a procedural gradient and the run is reported as `multi_shot_procedural`, which is not publishable without owner review.

Run it directly:

    cd ~/shorts_studio
    ./venv/bin/python -m app.script.pipeline --topic "your topic" --out data/metadata_strong.json

Check the LLM provider chain and prune it:

    ./venv/bin/python -m app.providers.model_health --probe --prune

`app.providers.model_health` sends the real JSON workload to every configured provider, records latency and schema compliance in `model_health.json`, and skips providers that failed within the last six hours when `AI_HEALTH_GATE=true`. The verified model IDs on this project are `qwen/qwen3.8-27b` (Groq), `gemini-3.5-flash` (Gemini) and `groq/openai/gpt-oss-120b` (OmniRoute). `gemini-2.5-flash` and `qwen/qwen3-8b` are retired or never existed, and the OmniRoute `auto/*` routing models take about 40 seconds per call, so they are not used.

## Required setup

1. Both generators use the shared `app.providers.multi_model_ai` provider layer: the order set in `AI_PROVIDER_CHAIN` (Groq, then OmniRoute, then Gemini, then local Ollama by default). Set `OMNIROUTE_BASE_URL=http://localhost:20128/v1`, `OMNIROUTE_API_KEY` from the OmniRoute dashboard, and optionally `OMNIROUTE_MODEL` (default `groq/openai/gpt-oss-120b`) in the private `.env`. Set `AI_GENERATION_PROVIDER=ollama` to force local-only inference for a run. Paid OpenAI and Anthropic providers are never automatic fallbacks. The verified model IDs are `GROQ_MODEL=qwen/qwen3.8-27b`, `GEMINI_MODEL=gemini-3.5-flash` and `OMNIROUTE_MODEL=groq/openai/gpt-oss-120b`; `gemini-2.5-flash` is retired for new users and `qwen/qwen3-8b` never existed. Each provider has a fallback model list, and `app.providers.model_health` skips providers that recently failed when `AI_HEALTH_GATE=true`.
2. Free stock footage is optional and can use `PIXABAY_API_KEY` or an existing `PEXELS_API_KEY`. To get a Pixabay key, create/sign in to a Pixabay account and follow the official [Pixabay API documentation](https://pixabay.com/api/docs/); keep the key only in the private `.env`. Long-form searches for two distinct landscape clips per chapter, assembles them into a narrated 16:9 video, and adds creator/source credits to the description. Pixabay search responses are cached for 24 hours as required by its API guidance. **Pixabay says its API is for real-human requests and disallows lots of automated queries or systematic mass downloads.** This workflow makes a small number of targeted searches per video; review Pixabay's current API terms before enabling scheduled use, and do not use it for bulk scraping. At least eight distinct clips are required for a review-eligible stock cut. Pexels currently reports that new API key issuance is paused, so use an existing key if available. Without enough stock footage, long-form falls back to original procedural motion graphics; these are explainers, not footage, and remain draft-only. Owner-recorded footage can be supplied with `DEMO_VIDEO_PATH`. Long-form profiles range from 2 to 10 minutes, with 8 minutes as the default.
3. Complete Meta developer verification, connect an Instagram Business/Creator account to a Facebook Page, and configure the values listed in docs/META_REELS_SETUP.md.
4. Configure a stable public video URL/host for Instagram. Publishing stays blocked until YouTube, Facebook, and Instagram are all configured. As a fallback, `INSTAGRAM_TUNNEL_FALLBACK=true` in `.env` lets `app.publish.orchestration` start a temporary Cloudflare Quick Tunnel for the run; `cloudflared` must be installed at `~/.local/bin/cloudflared`.



## Check setup safely

    cd ~/shorts_studio
    ./venv/bin/python setup_check.py

This reports missing requirements without printing credentials or publishing. See docs/REQUIRED_SETUP.md for account-specific steps.

## OmniRoute and VS Code

Start the WSL-installed gateway in WSL with `export PATH="$HOME/.local/bin:$PATH"` followed by `omniroute`; open [http://localhost:20128/dashboard](http://localhost:20128/dashboard) to connect an eligible model provider. Change the dashboard's initial password before use. For project generation, set `OMNIROUTE_BASE_URL=http://localhost:20128/v1`, `OMNIROUTE_MODEL=groq/openai/gpt-oss-120b`, and the gateway API key from **Dashboard → Endpoints** as `OMNIROUTE_API_KEY` in the private `.env`. The installed OmniCopilot VS Code extension provides OmniRoute models in Copilot Chat's model picker. Never paste API keys into chat or commit `.env`.

## Run the full pipeline manually

    cd ~/shorts_studio
    ./run_pipeline.sh

The script generates a fresh video and then creates a review package. The scheduled path always sets `PUBLISH_MODE=review`; it never uploads during generation. The optional `--topic` argument can request a current AI/technology topic. Generation fails closed if it cannot find a fresh source or produce a valid 70–90 word script and a render that passes duration, portrait-resolution, and audio checks.

Verify the local render path without any paid API, LLM, research, stock-footage, archive, or upload call:

    DRY_RUN=1 ./venv/bin/python pipelines/short.py

This writes `outputs/dry_run/output_short.mp4` and `data/metadata_dry_run.json`. It uses a silent local voice track and a procedural background, then runs the normal caption and video QA checks. The output is marked `not_for_publish`; production `data/metadata.json` and review queues are not touched.

Storyboard review is mandatory by default: when `STORYBOARD_GATE` is unset it behaves as `require`, so a render whose storyboard is still `needs_review` stops before encoding. That also applies to local benchmarks, because a dry run uses procedural fallback visuals and is normally `needs_review`. To exercise only the render mechanics, set the gate explicitly for that one command — `STORYBOARD_GATE=warn DRY_RUN=1 ./venv/bin/python pipelines/short.py` — and leave the production default untouched. `off`/`skip` skip storyboard generation. Any other value fails closed instead of silently degrading to `warn`. Dry-run and standard-quality artifacts stay unpublished regardless of the gate: the shared publishing authorization only accepts strong-pipeline output, and the direct `python -m app.script.pipeline` entry point marks its artifacts `governance.publishable=false`.

## Daily review and upload schedule

At 12:00 IST, the workflow queues a Short for review; on Wednesday and Saturday it also queues a 2–10 minute long-form video (8 minutes by default). Telegram review messages include a Windows-accessible local preview and a PowerShell command that asks the owner to confirm the review checklist. Run the command only after watching the full video and checking the listed evidence, visuals, and publishing copy. A declined answer cancels approval.

At 20:00 IST, the workflow checks whether the exact current video and metadata were approved on the same IST day. Missing, expired, stale, or mismatched approval means no upload. Shorts still require YouTube, Facebook, and Instagram all to pass setup; long-form publishes only to YouTube on its scheduled days. Approvals are bound to SHA-256 hashes and expire at local midnight.

All destinations are authorized through one shared boundary, `app.publish.authorization`, so a direct publisher run is checked exactly like the scheduled one. YouTube destinations publish as `private` by default; `public` needs a separate owner public-release authorization in `data/public_release_approved.json` (owner identity, same IST day, matching video and metadata hashes) — an editorial approval alone never makes a video public.

Example approval commands (also sent in the private review reminder):

    wsl.exe -d Ubuntu --exec /home/demon/shorts_studio/venv/bin/python -m app.review.approve_review --interactive
    wsl.exe -d Ubuntu --exec /home/demon/shorts_studio/venv/bin/python -m app.review.approve_longform --interactive

## Visual quality gate

Each generator records the visual source in its metadata. When stock or owner footage is unavailable, long-form uses animated chapter-specific diagrams and labels instead of a static grid; these explainers are not footage and remain draft-only. Short and long-form approval/upload paths reject procedural or unverified visuals even if a checklist was manually marked complete. Long-form Pexels or Pixabay scenes are selected per chapter, and creator/source links are recorded in metadata and the YouTube description. Long-form audio is normalized and exported as 48 kHz stereo AAC, then checked for an audio stream and non-silent output. Review footage relevance, rights, narration, and edit quality before approval; this gate is a safety check, not a guarantee of editorial quality.

## Long-form editorial and research gate

Long-form topic selection compares up to eight recent candidates using an AI editorial scorecard for viewer relevance, observed interest signals, evidence quality, originality, and visual potential. That score is an editorial estimate—not search volume, YouTube analytics, or a promise of virality. The selected primary source and an independently hosted, topic-matched secondary article must be retrievable before script generation; arXiv candidates try the free ar5iv full-text mirror first, and secondary coverage is searched through Google News RSS. The script must include exact, excerpt-checked evidence notes from both sources, an opening hook that exactly matches the first spoken line, an explicit evidence gap, and chapter-specific visual types. If sources cannot be retrieved or the script fails these checks, generation stops instead of rendering a weak draft. Editors still need to verify claims against the cited sources. Topic selection does not yet use channel analytics or YouTube search-volume data.

## Local video archive

After quality checks, both generators archive the finished MP4 and its JSON metadata. On this Windows/WSL setup the default archive is `D:\ShortsStudioVideos`, organized as `shorts\YYYY\MM` and `longform\YYYY\MM`. Rendering and publishing continue to use the existing project files, so this does not change the publishing workflow. If `D:` is unavailable, the archive defaults to the project `outputs/archive` folder. Set `VIDEO_ARCHIVE_DIR` in `.env` to choose another local path. The archive is local storage, not an online backup; monitor its remaining disk space.

Open output_short.mp4 from Windows File Explorer at:

    \\wsl.localhost\Ubuntu\home\demon\shorts_studio

API usage and free tiers depend on each provider; publishing access and monetization eligibility are controlled by each platform.


## Documentation and reports

- Start with [docs/README.md](docs/README.md) for the documentation map, current governance boundaries and source-of-truth rules.
- The [NEXTDECODE workspace mirror](docs/nextdecode-workspace/00_CONTROL_AND_INDEX/00_MASTER_INDEX.md) is copied from the canonical D-drive workspace. The D-drive source remains authoritative; see its [SHA-256 mirror manifest](docs/nextdecode-workspace/MIRROR_MANIFEST.md).
- Reports and agent reviews are organized under [reports/](reports/README.md). See [the report migration manifest](reports/MIGRATION_MANIFEST.md) for provenance, original paths and hashes.
- The former imported P0 source folder is preserved under docs/archive/legacy-source-imports/; its original root path remains as a compatibility symlink for historical references.
- Cleanup evidence and path-preservation decisions are recorded in [docs/CLEANUP_MIGRATION_MANIFEST.md](docs/CLEANUP_MIGRATION_MANIFEST.md).
