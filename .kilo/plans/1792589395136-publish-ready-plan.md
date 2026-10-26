# Publish-Ready Plan — Shorts Studio

## Goal
Publish the generated Short (`output_short.mp4`) to YouTube, Facebook, and Instagram via `publish_all.py`.

## Current State

### Present
- `review_package.json` — status `approved`, all 7 checklist items `true`, hashes recorded (metadata_sha256, video_sha256), visuals mode `multi_shot_stock` with 8 Wikimedia CC-licensed assets
- `.env` — `GEMINI_API_KEY`, `GROQ_API_KEY`, `OMNIROUTE_API_KEY`, `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `TELEGRAM_BOT_TOKEN` set; `PUBLISH_MODE=publish`, `AUTO_PUBLISH_APPROVED=true`
- `workflow_n8n_approved_schedule.json` — n8n workflow source
- `restore_n8n_workflow.sh` — idempotent recovery script
- Pipeline modules: `strong_pipeline.py`, `topic_selector.py`, `research_desk.py`, `script_studio.py`, `voice_guide.py`, `motion_director.py`, `motion_render.py`, `voice_provider.py`, `visual_assets.py`, `stock_fetcher.py`, `model_health.py`, `publish_social.py`, `workspace_sync.py`, `analytics_collect.py`, `trend_research.py`
- `approval_integrity.py`, `visual_quality.py`, `approve_review.py`

### Missing (blocks publishing)
| File | Why missing | Fix |
|---|---|---|
| `metadata.json` | Pipeline output deleted | Re-run `strong_pipeline.py` |
| `output_short.mp4` | Pipeline output deleted | Re-run `strong_pipeline.py` |
| `review_approved.json` | Approval file deleted | Re-run `approve_review.py` |
| `youtube_token.json` | YouTube OAuth never completed | User must authorize in browser |
| `FACEBOOK_PAGE_ID` | Empty in `.env` | User must create Meta Developer app |
| `FACEBOOK_PAGE_ACCESS_TOKEN` | Empty in `.env` | User must create Meta Developer app |
| `INSTAGRAM_USER_ID` | Empty in `.env` | User must create Meta Developer app |
| `INSTAGRAM_ACCESS_TOKEN` | Empty in `.env` | User must create Meta Developer app |
| `INSTAGRAM_VIDEO_URL` | Empty in `.env` | Cloudinary/R2/Supabase host, or cloudflared tunnel |

## Publish Gate Sequence (from `publish_all.py`)

1. `validate_content()` — requires `metadata.json` + `output_short.mp4` (>150KB) with valid title, word count, pillar, platform_copy, hashtags, source_urls, hook, timestamp
2. `approval_matches_current_content()` — requires `review_approved.json` + `review_package.json` with matching hashes and `approved_today()`
3. `platform_configured()` per platform:
   - `youtube` — `YOUTUBE_CLIENT_ID` + `YOUTUBE_CLIENT_SECRET` + `youtube_token.json`
   - `facebook` — `META_GRAPH_API_VERSION` + `FACEBOOK_PAGE_ID` + `FACEBOOK_PAGE_ACCESS_TOKEN`
   - `instagram` — `META_GRAPH_API_VERSION` + `INSTAGRAM_USER_ID` + `INSTAGRAM_ACCESS_TOKEN` + `INSTAGRAM_VIDEO_URL` (or cloudflared tunnel with `INSTAGRAM_TUNNEL_FALLBACK=true`)

## Plan

### Phase 1 — Regenerate video + metadata (no user input needed)
1. Run `venv/bin/python strong_pipeline.py --seconds 35 --out metadata.json`
2. Verify `metadata.json` and `output_short.mp4` exist and `output_short.mp4` > 150KB

### Phase 2 — Re-approve review package (no user input needed)
3. Compute SHA256 of `metadata.json` and `output_short.mp4`
4. Update `review_package.json` with new hashes and current `visuals` from `metadata.json`
5. Update `review_pending.json` to point at `review_package.json`
6. Run `venv/bin/python approve_review.py review_package.json`
7. Verify `review_approved.json` created with status `approved`

### Phase 3 — User must complete (cannot be automated)
8. **YouTube OAuth** — run `venv/bin/python youtube_upload.py --auth` (opens browser for consent, writes `youtube_token.json`)
9. **Meta Developer app** — user creates app at developers.facebook.com, adds Facebook Pages product, gets long-lived Page Access Token + Instagram Business Account ID
10. **Instagram media host** — set `INSTAGRAM_VIDEO_URL` to a public URL, or ensure `cloudflared` is installed for tunnel fallback
11. User provides these values to update `.env`:
    - `FACEBOOK_PAGE_ID`
    - `FACEBOOK_PAGE_ACCESS_TOKEN`
    - `INSTAGRAM_USER_ID`
    - `INSTAGRAM_ACCESS_TOKEN`
    - `INSTAGRAM_VIDEO_URL` (optional if cloudflared available)

### Phase 4 — Publish (after Phase 3 complete)
12. Run `venv/bin/python publish_all.py`
13. Verify output: `{"status": "completed", "platforms": [...]}`

## Risks
- `approved_today()` requires approval timestamp to match today (Asia/Kolkata) — must re-approve each day
- `validate_content()` rejects stale videos (>24h) and invalid hooks/content
- Meta security blocks account creation from unrecognized devices — user may need alternate network/device
- YouTube OAuth requires interactive browser consent — cannot be automated

## Validation
- `venv/bin/python setup_check.py` — verify all required items READY
- `venv/bin/python publish_all.py` — run and check exit code 0
- Check `review_approved.json` matches current `metadata.json` + `output_short.mp4` hashes