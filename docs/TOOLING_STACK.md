# Tooling Stack

## AI / LLM
- Module: multi_model_ai.py / omniroute_client.py
- Keys: OMNIROUTE_API_KEY, GEMINI_API_KEY, GROQ_API_KEY, OLLAMA_BASE_URL
- Free tier: yes (Gemini, Groq, Ollama)

## Voice / TTS
- Module: voice_provider.py (edge_tts -> elevenlabs -> cartesia -> openai -> silent)
- Keys: TTS_PROVIDER, TTS_VOICE, ELEVENLABS_API_KEY, CARTESIA_API_KEY, OPENAI_API_KEY
- Free tier: yes (edge-tts)

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

## Scheduling / Orchestration
- n8n workflow K5Qcx4jH8xw4qc9F "Approved Shorts & Long-Form Studio" active; crons 0 12 * * * and 0 20 * * * Asia/Kolkata
- URL: http://localhost:5678/workflow/K5Qcx4jH8xw4qc9F
- Old id aibl9NX61mKH9z5m lost when n8n DB wiped; restore_n8n_workflow.sh re-imports idempotently.
- Limitation: n8n public API rejects settings.callerPolicy; restored workflow runs with timezone+executionOrder only.

## Free-tier recommended stack
Gemini + edge-tts + ffmpeg + YouTube Data API + Reddit + Cloudinary free tier + local sqlite.

## What is still missing
Meta creds, human approval, review_approved.json, pending review package.
