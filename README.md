# Nextdecode Shorts & Reels Studio (WSL)

Research-led vertical videos for Nextdecode. The full pipeline researches current AI/technology topics, creates an original short script, narration and captions, renders and checks a 1080×1920 MP4, then cross-posts to YouTube Shorts, Facebook Reels, and Instagram Reels when every destination is ready.

## Project files

- app/research/topics.py — topic discovery and repeat avoidance.
- app/research/trends.py — multi-source trending-topic discovery and heat ranking.
- create_short.py — script, voiceover, B-roll, subtitles, render, and quality checks.
- strong_pipeline.py — the strong editorial chain that `create_short.py --quality strong` runs.
- app/research/selector.py — scores candidate topics on seven editorial dimensions and picks the best one.
- app/research/desk.py — fetches and actually reads the sources, extracts verbatim claims, flags unsupported numbers and contradictions.
- app/script/studio.py — generates hook candidates, scores them, writes a beat sheet, and runs a critic loop that rewrites until the script passes.
- app/script/voice_guide.py — hook archetypes, channel voice, and the AI-slop ban list.
- app/script/longform.py — research-backed long-form topic selection, source validation, and script generation.
- app/voice/provider.py — pluggable TTS chain (Edge TTS → ElevenLabs → Cartesia → OpenAI → silent).
- motion_director.py — plans the edited shot list (cuts, zoom, SFX, safe zones).
- motion_render.py — renders the multi-shot video with Ken Burns motion, kinetic captions, music bed and SFX.
- stock_fetcher.py — key-free real-photo sourcing from Wikimedia Commons with licence attribution.
- model_health.py — probes every LLM provider, records the result, and prunes the fallback chain.
- run_pipeline.sh — runs create_short.py and queues a review package; it publishes only when explicitly configured.
- run_scheduled_generation.sh — generates a Short daily and long-form video on Wednesday/Saturday, in review-only mode.
- scheduled_publish.py — runs the 20:00 IST upload checks for today's exact owner-approved content.
- approval_integrity.py — binds approvals to rendered-video and metadata hashes and the current IST day.
- notify_review.py — sends a private Telegram review reminder with the local preview path and approval command.
- youtube_upload.py, facebook_reels_upload.py, instagram_reels_upload.py — platform publishers.
- publish_all.py — validates fresh metadata, video, credentials, and all three destinations before any upload. It refuses partial cross-posts when setup is incomplete.
- setup_check.py — safe setup report; never prints credential values or publishes, and distinguishes required setup blockers from optional integrations.
- notify_status.py — sends generic generation/publishing status alerts to the configured Telegram chat; it never includes credentials or OAuth codes.
- .env — private local credentials. Never paste keys into chat or commit this file.
- docs/META_REELS_SETUP.md and docs/REQUIRED_SETUP.md — platform and account setup steps.
- docs/ — planning, provider status, monetization, and setup notes (see also ROADMAP.md).

When TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are configured, generation failures, publishing blockers, and publish results are sent to that Telegram chat. Alerts are best-effort and do not change publishing outcomes.

The live npm workflow is n8n workflow `aibl9NX61mKH9z5m`, named **NEXTDECODE - Full Content Flow (Research to Approved Publish)**. Its canvas has sticky-note maps for the generation, review, integration, and approval-gated publishing stages; the two Execute Command nodes call the existing project scripts. The Docker-ready workflow definition in `workflow_n8n_approved_schedule.json` replaces those with authenticated HTTP calls to `studio-runner`; **do not import that definition into the npm instance before Docker cutover**, because its runner service is not running there. Both versions queue content daily at 12:00 IST, add long-form generation on Wednesday/Saturday, and check for uploads at 20:00 IST. Importing a workflow over this live ID deactivates it; back it up and explicitly reactivate it afterward. Older workflow snapshots (`workflow_n8n.json`, `workflow_n8n_safe.json`, and related variants) were archived to `/home/demon/shorts_studio_archive_pre_20261026/workflows/`; do not import them over the live workflow.

## The strong pipeline

`create_short.py --quality strong` (the default) runs the full editorial chain instead of the legacy single-pass path:

    topic_selector  ->  research_desk  ->  script_studio  ->  app.voice.provider
                   ->  motion_director  ->  motion_render  ->  QA

| Stage | What it does | Fails closed when |
|---|---|---|
| `topic_selector` | Scores candidate topics on demand, channel fit, visual feasibility, undersaturation, novelty, timing and risk, and applies the analytics feedback loop. | No candidate clears `min_topic_score` (default 55). |
| `research_desk` | Fetches the candidate sources, reads them, keeps only pages that are actually about the topic, and extracts claims with verbatim quotes. | The primary source cannot be fetched or no verifiable claim exists. |
| `script_studio` | Generates one hook per archetype, scores them, writes a timestamped beat sheet, then runs a critic loop that rewrites the script while it contains unsupported numbers, slop, a generic hook, or a wrong word count. | The script still fails the critic after the rewrite budget. |
| `app.voice.provider` | Speaks the script through the TTS chain. | No provider produced audio. |
| `motion_director` | Cuts the runtime into 8–14 shots (about 2.8 s each) with zoom, pan, SFX and safe zones. | — |
| `motion_render` | Renders every shot with Ken Burns motion, burns kinetic word-level captions, mixes a music bed under the voice, and adds SFX. | The render fails QA. |
| `qa_video` | Re-probes the finished file. | Wrong resolution, missing audio, or a duration that does not match the voice track. |

Visuals come from licensed stock when a Pexels or Pixabay key is present, otherwise from Wikimedia Commons (free, no key) with the licence, author and file page recorded in `metadata.json` under `visuals.assets`. AI images are used when an image provider is available and is quota permitting. Shots that find no real image fall back to a procedural gradient and the run is reported as `multi_shot_procedural`, which is not publishable without owner review.

Run it directly:

    cd ~/shorts_studio
    ./venv/bin/python strong_pipeline.py --topic "your topic" --out metadata_strong.json

Check the LLM provider chain and prune it:

    ./venv/bin/python model_health.py --probe --prune

`model_health.py` sends the real JSON workload to every configured provider, records latency and schema compliance in `model_health.json`, and skips providers that failed within the last six hours when `AI_HEALTH_GATE=true`. The verified model IDs on this project are `qwen/qwen3.8-27b` (Groq), `gemini-3.5-flash` (Gemini) and `groq/openai/gpt-oss-120b` (OmniRoute). `gemini-2.5-flash` and `qwen/qwen3-8b` are retired or never existed, and the OmniRoute `auto/*` routing models take about 40 seconds per call, so they are not used.

## Required setup

1. Both generators use the shared `multi_model_ai.py` provider layer: the order set in `AI_PROVIDER_CHAIN` (Groq, then OmniRoute, then Gemini, then local Ollama by default). Set `OMNIROUTE_BASE_URL=http://localhost:20128/v1`, `OMNIROUTE_API_KEY` from the OmniRoute dashboard, and optionally `OMNIROUTE_MODEL` (default `groq/openai/gpt-oss-120b`) in the private `.env`. Set `AI_GENERATION_PROVIDER=ollama` to force local-only inference for a run. Paid OpenAI and Anthropic providers are never automatic fallbacks. The verified model IDs are `GROQ_MODEL=qwen/qwen3.8-27b`, `GEMINI_MODEL=gemini-3.5-flash` and `OMNIROUTE_MODEL=groq/openai/gpt-oss-120b`; `gemini-2.5-flash` is retired for new users and `qwen/qwen3-8b` never existed. Each provider has a fallback model list, and `model_health.py` skips providers that recently failed when `AI_HEALTH_GATE=true`.
2. Free stock footage is optional and can use `PIXABAY_API_KEY` or an existing `PEXELS_API_KEY`. To get a Pixabay key, create/sign in to a Pixabay account and follow the official [Pixabay API documentation](https://pixabay.com/api/docs/); keep the key only in the private `.env`. Long-form searches for two distinct landscape clips per chapter, assembles them into a narrated 16:9 video, and adds creator/source credits to the description. Pixabay search responses are cached for 24 hours as required by its API guidance. **Pixabay says its API is for real-human requests and disallows lots of automated queries or systematic mass downloads.** This workflow makes a small number of targeted searches per video; review Pixabay's current API terms before enabling scheduled use, and do not use it for bulk scraping. At least eight distinct clips are required for a review-eligible stock cut. Pexels currently reports that new API key issuance is paused, so use an existing key if available. Without enough stock footage, long-form falls back to original procedural motion graphics; these are explainers, not footage, and remain draft-only. Owner-recorded footage can be supplied with `DEMO_VIDEO_PATH`. Long-form profiles range from 2 to 10 minutes, with 8 minutes as the default.
3. Complete Meta developer verification, connect an Instagram Business/Creator account to a Facebook Page, and configure the values listed in docs/META_REELS_SETUP.md.
4. Configure a stable public video URL/host for Instagram. Publishing stays blocked until YouTube, Facebook, and Instagram are all configured. As a fallback, `INSTAGRAM_TUNNEL_FALLBACK=true` in `.env` lets `publish_all.py` start a temporary Cloudflare Quick Tunnel for the run; `cloudflared` must be installed at `~/.local/bin/cloudflared`.
5. Keep WSL, n8n, and the machine available at 12:00 and 20:00 Asia/Kolkata. Generation is review-only; only a same-day approval for the exact rendered video and metadata can pass the upload check.

n8n currently runs as a systemd user service (`n8n.service`) so the daily schedule survives a WSL restart:

    systemctl --user status n8n.service
    systemctl --user restart n8n.service

## Prepared Docker Compose migration

`compose.yaml` pins n8n to the current `1.97.1` release and adds a separate Python runner with FFmpeg and the project dependencies. The runner exposes only two fixed, bearer-authenticated operations on the private Compose network; n8n has no access to the project `.env` or YouTube token. The maintained workflow source uses HTTP Request nodes for those operations. The project scripts keep using the existing WSL virtual environment unless `SHORTS_STUDIO_PYTHON` is explicitly set by the container.

**The migration is prepared but not active.** Docker Desktop is not installed yet; keep the npm service running until Docker Desktop's WSL integration is enabled, the Compose stack builds, and the imported workflow and schedules are verified. The n8n container mounts the existing data directory, while the runner mounts the project directory; the n8n image stays pinned to `1.97.1` for the first cutover. Do not run the npm and Docker instances' schedules at the same time.

Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) and enable the Ubuntu distro under [Docker Desktop's WSL 2 integration](https://docs.docker.com/desktop/features/wsl/).

After Docker Desktop is installed and running:

1. Create a private runner key in WSL: `cd ~/shorts_studio && (umask 077; python3 -c 'import secrets; print("N8N_RUNNER_API_KEY=" + secrets.token_hex(32))' > .n8n-docker.env && chmod 600 .n8n-docker.env)`.
2. Build and start only the runner first: `docker compose --env-file .n8n-docker.env build studio-runner && docker compose --env-file .n8n-docker.env up -d studio-runner`; confirm its health before switching n8n.
3. Take and verify a fresh n8n backup, confirm no execution is running, then stop `n8n.service`. Import the maintained workflow while the npm service is stopped: `docker compose --env-file .n8n-docker.env run --rm --no-deps n8n n8n import:workflow --input=/tmp/workflow_n8n_approved_schedule.json`.
4. Start the Compose stack. Check the imported workflow's two HTTP Request nodes and schedule settings, then activate workflow `aibl9NX61mKH9z5m` with `docker compose --env-file .n8n-docker.env exec n8n n8n update:workflow --id=aibl9NX61mKH9z5m --active=true` and apply the change with `docker compose --env-file .n8n-docker.env restart n8n`.
5. Verify owner login, active workflow, IST schedule, runner health, and the project integrations. Do not run publishing as a migration test; the scheduled publisher still requires same-day owner approval for the exact approved content.
6. If OmniRoute or Ollama is used, the runner defaults to `host.docker.internal` endpoints. Override `OMNIROUTE_BASE_URL_CONTAINER` or `OLLAMA_BASE_URL_CONTAINER` in `.n8n-docker.env` only if your host service uses a different address, then verify connectivity from the runner.

The checked migration archive is outside the repository at `/home/demon/.n8n/backups/n8n-pre-docker-migration-20261022T092254Z.tar.gz`. Keep it private and verify its SHA-256 before cutover. Do not upgrade n8n during this deployment migration.

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

## Daily review and upload schedule

At 12:00 IST, the workflow queues a Short for review; on Wednesday and Saturday it also queues a 2–10 minute long-form video (8 minutes by default). Telegram review messages include a Windows-accessible local preview and a PowerShell command that asks the owner to confirm the review checklist. Run the command only after watching the full video and checking the listed evidence, visuals, and publishing copy. A declined answer cancels approval.

At 20:00 IST, the workflow checks whether the exact current video and metadata were approved on the same IST day. Missing, expired, stale, or mismatched approval means no upload. Shorts still require YouTube, Facebook, and Instagram all to pass setup; long-form publishes only to YouTube on its scheduled days. Approvals are bound to SHA-256 hashes and expire at local midnight.

Example approval commands (also sent in the private review reminder):

    wsl.exe -d Ubuntu --exec /home/demon/shorts_studio/venv/bin/python /home/demon/shorts_studio/approve_review.py --interactive
    wsl.exe -d Ubuntu --exec /home/demon/shorts_studio/venv/bin/python /home/demon/shorts_studio/approve_longform.py --interactive

## Visual quality gate

Each generator records the visual source in its metadata. When stock or owner footage is unavailable, long-form uses animated chapter-specific diagrams and labels instead of a static grid; these explainers are not footage and remain draft-only. Short and long-form approval/upload paths reject procedural or unverified visuals even if a checklist was manually marked complete. Long-form Pexels or Pixabay scenes are selected per chapter, and creator/source links are recorded in metadata and the YouTube description. Long-form audio is normalized and exported as 48 kHz stereo AAC, then checked for an audio stream and non-silent output. Review footage relevance, rights, narration, and edit quality before approval; this gate is a safety check, not a guarantee of editorial quality.

## Long-form editorial and research gate

Long-form topic selection compares up to eight recent candidates using an AI editorial scorecard for viewer relevance, observed interest signals, evidence quality, originality, and visual potential. That score is an editorial estimate—not search volume, YouTube analytics, or a promise of virality. The selected primary source and an independently hosted, topic-matched secondary article must be retrievable before script generation; arXiv candidates try the free ar5iv full-text mirror first, and secondary coverage is searched through Google News RSS. The script must include exact, excerpt-checked evidence notes from both sources, an opening hook that exactly matches the first spoken line, an explicit evidence gap, and chapter-specific visual types. If sources cannot be retrieved or the script fails these checks, generation stops instead of rendering a weak draft. Editors still need to verify claims against the cited sources. Topic selection does not yet use channel analytics or YouTube search-volume data.

## Local video archive

After quality checks, both generators archive the finished MP4 and its JSON metadata. On this Windows/WSL setup the default archive is `D:\ShortsStudioVideos`, organized as `shorts\YYYY\MM` and `longform\YYYY\MM`. Rendering and publishing continue to use the existing project files, so this does not change the publishing workflow. If `D:` is unavailable, the archive defaults to the project `outputs/archive` folder. Set `VIDEO_ARCHIVE_DIR` in `.env` to choose another local path. The archive is local storage, not an online backup; monitor its remaining disk space.

Open output_short.mp4 from Windows File Explorer at:

    \\wsl.localhost\Ubuntu\home\demon\shorts_studio

API usage and free tiers depend on each provider; publishing access and monetization eligibility are controlled by each platform.
