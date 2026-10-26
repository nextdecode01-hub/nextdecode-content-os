# End-to-End Content Pipeline Plan

## Goal
Produce and publish a verified short-form video (YouTube Shorts / IG Reels / FB Reels) through the strong editorial pipeline, with same-day owner approval gating, across all platforms, while failing closed on any weak stage.

## Stages (strong_pipeline.run)
1. **Topic selection** (`topic_selector.select_best` over `discover_topics`): 7-dim scorecard, min_score=55. Explicit topic still scored. Rejects below bar.
2. **Research** (`research_desk.research_topic`): fetch + read primary/secondary sources, extract verbatim claims, flag unsupported numbers + contradictions. Fails if primary unverifiable.
3. **Script** (`script_studio.write_script`, strict_research=True): hook candidates per archetype, beat sheet, critic loop (unsupported numbers, slop, generic hook, word count). Fails if critic doesn't pass.
4. **Voice** (`voice_provider.synthesize_with_fallback`, edge_tts preferred): TTS chain. Fails if no audio.
5. **Captions** (`faster_whisper` word timings, fallback estimated).
6. **Shot plan** (`motion_director.plan_shots`): 8-14 shots ~2.8s, zoom/pan/SFX/safe zones.
7. **Render** (`motion_render.render_video`): Ken Burns, kinetic captions, music bed, SFX.
8. **QA** (`motion_render.qa_video`): resolution 1080x1920, audio present, duration within 0.75-1.35x voice.

## Visual gate
- Providers classified: stock (pexels/pixabay/wikimedia), AI (ai_image/gemini/fal/replicate/openai), procedural (procedural/local), demo.
- Mode = multi_shot_stock | multi_shot_ai | multi_shot_mixed | multi_shot_procedural | owner_recorded.
- Procedural/unverified visuals block publishing even if checklist marked complete.

## Review & approval
- Generation is review-only (PUBLISH_MODE=review). run_pipeline.sh queues review package.
- notify_review.py sends Telegram with preview path + approval command.
- approve_review.py binds approval to SHA-256 of rendered video + metadata + IST day; expires midnight.
- scheduled_publish.py at 20:00 IST checks exact current video/metadata approved same day; missing/stale/mismatched → no upload.

## Publish gate (publish_all.py)
- Validates fresh metadata, video, credentials, all 3 destinations configured before any upload.
- Refuses partial cross-posts when setup incomplete.
- Instagram requires stable public video URL (or INSTAGRAM_TUNNEL_FALLBACK cloudflared).
- Long-form: YouTube only on Wed/Sat.

## Data flow
strong_pipeline.py → metadata_strong.json + output_short.mp4 → (copy to metadata.json + output_short.mp4) → approve_review.py → scheduled_publish.py → youtube_upload.py / facebook_reels_upload.py / instagram_reels_upload.py.

## Failure modes
- No candidate clears min_topic_score → RuntimeError, no render.
- Primary source unfetchable / no verifiable claim → no script.
- Critic fails after rewrite budget → no render.
- No TTS audio → no render.
- Render QA fail → no publish.
- Procedural visuals → draft-only, publish blocked.
- Approval mismatch/expired → no upload at 20:00.
- Missing credentials → publish_all refuses partial cross-post.

## Validation
- setup_check.py (safe, no creds printed, no publish).
- model_health.py --probe --prune (LLM chain health).
- qa_video resolution/audio/duration.
- Approval hash binding verification.

## n8n orchestration
- Live workflow aibl9NX61mKH9z5m queues daily 12:00 IST, long-form Wed/Sat, publish check 20:00 IST.
- Execute Command nodes call project scripts.
- Docker migration prepared but inactive (npm service running). Do not run both schedules simultaneously.

## Manual publish run (refinement)

### Exact sequence the user intends
1. `copy tmp/video/video.mp4 output_short.mp4` — replace working video with a pre-rendered candidate.
2. `copy metadata_strong.json metadata.json` — replace working metadata with the strong-pipeline metadata.
3. `wsl ./venv/bin/python youtube_upload.py` — upload to YouTube.

### Gaps / risks in this sequence
- **Hash binding**: approve_review.py binds approval to SHA-256 of `output_short.mp4` + `metadata.json` + IST day. If the copied files differ from what was approved, scheduled_publish.py must reject. Manual copies bypass the approval step entirely unless approve_review.py is run after copying.
- **Metadata/video mismatch**: metadata_strong.json references `video_path: output_short.mp4` and `duration_seconds` from the strong render. Copying a different video (tmp/video/video.mp4) makes metadata stale → publish gate should fail on duration/hash mismatch.
- **No approval recorded**: youtube_upload.py alone does not check approval_integrity; scheduled_publish.py does. Running youtube_upload.py directly skips the same-day approval gate.
- **Visual gate**: metadata_strong.json `visuals.mode` must be stock/ai/mixed/owner_recorded; procedural → blocked.
- **Credentials**: youtube_upload.py requires valid OAuth token (youtube_token.json). No preflight here.

### Required preflight before upload (recommended)
1. Verify `tmp/video/video.mp4` exists and probe duration/resolution with ffprobe.
2. Compare probed duration to `metadata_strong.json.duration_seconds` (must be within 0.75-1.35x).
3. Run `setup_check.py` (no creds printed).
4. Run `approve_review.py --interactive` AFTER the copies, so approval hash matches the actual files being published.
5. Only then run `scheduled_publish.py` (not youtube_upload.py directly) so the 20:00 IST gate + integrity check apply.

- Manual publish MUST run approve_review.py after the copies, so the approval hash binds to the actual files being published. Direct youtube_upload.py without approval is disallowed.

### Out of scope for this refinement
- Automated n8n path (separate refinement).
- Image generation re-addition.

## Open questions
- Whether to wire the zero-investment n8n workflow (workflow_n8n_zero_investment.json) into the live instance or keep it as a separate draft (it bypasses approval gate — should NOT be used for publishing).
- Whether image generation should be re-added with a supported provider, or keep text-only thumbnails.
