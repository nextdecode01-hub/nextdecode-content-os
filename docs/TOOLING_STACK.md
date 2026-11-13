# Tooling Stack

## AI / LLM
- Module: multi_model_ai.py / omniroute_client.py
- Keys: OMNIROUTE_API_KEY, GEMINI_API_KEY, GROQ_API_KEY, OLLAMA_BASE_URL
- Free tier: yes (Gemini, Groq, Ollama)

## Voice / TTS
- Module: app/voice/provider.py (edge_tts -> elevenlabs -> cartesia -> openai -> silent)
- Default voice: en-US-AndrewMultilingualNeural (Phase 9 approval); source is 24 kHz / 48 kbps mono mp3
- Keys: TTS_PROVIDER, TTS_VOICE, TTS_RATE, TTS_PITCH, TTS_VOLUME, TTS_TEXT_PREP, ELEVENLABS_API_KEY, CARTESIA_API_KEY, OPENAI_API_KEY
- Free tier: yes (edge-tts)

## Audio mix / delivery
- Module: app/render/ffmpeg_tools.py
- Keys: AUDIO_BITRATE (default 320k), MUSIC_BED (on/off, default off), MUSIC_BED_FILE (licensed track), SHOT_SFX (default off)
- Chain: 44.1 kHz mono 24-bit WAV master -> measured linear loudnorm (I=-16 TP=-1.5) -> optional 3:1 duck -> limiter (level=false, -1.5 dBFS)

## Visuals / Images
- Module: visual_assets.py (gemini -> fal -> replicate -> openai -> local ffmpeg)
- Keys: GEMINI_API_KEY, FAL_KEY, REPLICATE_API_TOKEN, OPENAI_API_KEY, IMAGE_PROVIDER, THUMBNAIL_PROVIDER
- Free tier: yes (Gemini)

## Video / Editing
- ffmpeg, ffprobe, edge-tts (venv/bin/edge-tts, not on PATH)

## Trending / Discovery
- Module: trend_research.py (10 sources)
- Keys: YOUTUBE_DATA_API_KEY, TRENDS_API_KEY, REDDIT_CLIENT_ID/SECRET, X_BEARER_TOKEN
- Free tier: yes
- Limitation: ads.tiktok.com unreachable from this WSL host

## Publishing
- Module: publish_social.py (bluesky, threads, mastodon, discord, reddit, pinterest, gbp, whatsapp, telegram, uploadpost, relayapi)
- Keys: see .env.example Publishing sections
- Meta: META_GRAPH_API_VERSION, FACEBOOK_PAGE_ID, FACEBOOK_PAGE_ACCESS_TOKEN, INSTAGRAM_USER_ID, INSTAGRAM_ACCESS_TOKEN

## Storage / Workspace
- Module: workspace_sync.py (sqlite, airtable, notion, supabase, cloudinary, r2)
- Keys: AIRTABLE_*, NOTION_*, SUPABASE_*, CLOUDINARY_*, R2_*
- Free tier: yes

## Analytics
- Module: analytics_collect.py (youtube_analytics, youtube_data, meta_insights, ga4, local)
- Keys: GA4_*, YT_ANALYTICS_ENABLED, META_INSIGHTS_ENABLED
- Limitation: YouTube Analytics needs yt-analytics.readonly OAuth scope (403 without it)

## Autonomous task execution — 2026-11-07

- Application-owned runtime: `app.autonomy` (versioned contracts, explicit capability registry, SQLite WAL queue, leases, retries, idempotency and append-only task events).
- No external workflow server is required for the core task lifecycle. Local worker command: `python -m app.autonomy.cli worker`.
- Capability execution is allow-listed; task payloads cannot supply shell commands. External publishing remains blocked by default.
- Additional browser, coding, research, document and media specialists will be added only after free/licence/resource/quality qualification.

## Free-tier recommended stack
Gemini + edge-tts + ffmpeg + YouTube Data API + Reddit + Cloudinary free tier + local sqlite.

## What is still missing
Meta creds, human approval, review_approved.json, pending review package.
