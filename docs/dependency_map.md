# Dependency Map — shorts_studio

Snapshot: `main` @ `6ec4ccf` (Phase 0), 2026-10-26. Generated from source with AST import
scanning, shell/`subprocess` call scanning, the n8n workflow JSON, and the Compose file.
No secret values were read or recorded.

Legend: **imports** = local Python modules imported by the file. **imported by** = local
modules that import it (tests are listed separately). **trigger** = how the module actually
gets executed.

---

## 0. TL;DR

- n8n has exactly **two** operations: `POST /run/generate` and `POST /run/publish` on
  `http://studio-runner:8080` (`n8n_runner.py`). It never calls `server_3000.py`,
  `server_5678.py`, or `auth_server.py`.
- `server_5678.py` is an 11-line stub: it starts no server and only prints
  `YOUTUBE_CLIENT_ID`. The real n8n UI is the Docker `n8n` service on host port 5678.
- `server_3000.py` and `auth_server.py` are duplicate YouTube OAuth callback servers on
  ports 3000 and 5000. Neither is referenced by n8n, shell scripts, or the README.
- Generation is review-only: the runner forces `PUBLISH_MODE=review`. Publishing is a
  separate 20:00 IST gate (`scheduled_publish.py`).
- All pipeline entrypoints currently live in the repo root; tests import them as
  top-level modules. Moving files requires updating imports or adding shims.
- `logging_config.py`, `resilience.py`, `ollama_chat.py`, `publish_social.py`,
  `publish_review_safe.py`, and `review_ledger.py` have **no inbound import and no
  pipeline/shell/n8n invocation**. They are Phase 3 candidates, not deletion candidates.

---

## 1. Runtime topology

```text
n8n container (Docker, host 127.0.0.1:5678)
  schedule 12:00 IST ──POST http://studio-runner:8080/run/generate──┐
  schedule 20:00 IST ──POST http://studio-runner:8080/run/publish───┤
                                                                    v
                                                      n8n_runner.py (:8080, internal)
                                                        GET  /healthz
                                                        POST /run/generate -> run_scheduled_generation.sh
                                                        POST /run/publish  -> scheduled_publish.py
```

`compose.yaml` publishes only n8n (`127.0.0.1:5678`). The runner is internal on 8080;
ports 3000 and 5000 are not published by Compose.

---

## 2. n8n endpoint contract (must not change)

Workflow: `workflow_n8n_approved_schedule.json`
Name: `NEXTDECODE - Full Content Flow (Research to Approved Publish)`
State: `active: false` (currently disabled; contract still matters).

| n8n node | Schedule | Method + URL | Auth | Body | Timeout |
|---|---|---|---|---|---|
| Run Secure Generation Pipeline (Review Only) | `0 12 * * *` | `POST http://studio-runner:8080/run/generate` | `Authorization: Bearer $env.N8N_RUNNER_API_KEY` | empty | 14400 s |
| Run Approval-Gated Publisher | `0 20 * * *` | `POST http://studio-runner:8080/run/publish` | `Authorization: Bearer $env.N8N_RUNNER_API_KEY` | empty | 14400 s |

Runner details (`n8n_runner.py`):

- Rejects a non-empty request body (`request_body_not_supported`) and non-Bearer auth.
- Requires `N8N_RUNNER_API_KEY` to be at least 64 characters.
- `/run/generate` runs `/bin/bash run_scheduled_generation.sh` with
  `PUBLISH_MODE=review`, so generation never uploads.
- `/run/publish` runs `scheduled_publish.py`; exit code `2` (outside the 20:00 IST hour)
  is returned to n8n as HTTP 200 with `exit_code: 2`.
- One execution at a time (`EXECUTION_LOCK`); concurrent calls get HTTP 409.

**Phase 9 rule:** keep `studio-runner:8080/run/generate`, `/run/publish`, and `/healthz`
exactly as they are. The runner route paths are the n8n contract, not `api/main.py`'s choice.

---

## 3. Server route inventory (Phase 9 input)

| File | Listener | Routes | Auth | Called by | Status |
|---|---|---|---|---|---|
| `n8n_runner.py` | `ThreadingHTTPServer 0.0.0.0:8080` | `GET /healthz`; `POST /run/generate`; `POST /run/publish` | Bearer key on POSTs | n8n + Compose healthcheck | **Active** |
| `server_3000.py` | `socketserver.TCPServer :3000` | `GET <any path containing ?code=>` | none | manual Google OAuth redirect (`http://localhost:3000`) | No references; manual/legacy |
| `auth_server.py` | `socketserver.TCPServer :5000` | `GET /callback?code=...` (no `code` -> 404) | none | manual Google OAuth redirect (`http://localhost:5000/callback`) | No references; duplicate of `server_3000.py` |
| `server_5678.py` | none | none | n/a | none | **Dead stub**; prints `YOUTUBE_CLIENT_ID` and exits |
| `instagram_reels_upload.py` | temporary `ThreadingHTTPServer 127.0.0.1:<random>` | `GET/HEAD /reel/<random>.mp4` | random URL token | internal during Instagram upload via cloudflared | Ephemeral helper, not a service |

Notes:

- `server_3000.py` and `auth_server.py` both exchange the OAuth code and write
  `youtube_token.json`, then `os._exit(0)`. They differ only in port/path and messages.
- `server_5678.py` is not the n8n server. The n8n service in `compose.yaml` owns 5678.
- `GET /healthz` reports ffmpeg/ffprobe/edge-tts/Python modules, `model_health.json`,
  unhealthy providers, and free disk space.

---

## 4. Execution chains

### 4.1 Generation (n8n, review-only)

```text
POST /run/generate
  -> run_scheduled_generation.sh (flock on .scheduled_generation.lock)
     -> run_pipeline.sh (PUBLISH_MODE=review)
        -> create_short.py
        -> review_bundle.py
        -> notify_review.py short   [review mode exits here]
     -> Wed/Sat only: run_longform_pipeline.sh
        -> create_longform.py
        -> review_longform.py
        -> notify_review.py longform
```

`run_pipeline.sh` continues to `publish_all.py` only when `PUBLISH_MODE=publish`.

### 4.2 Publishing (n8n, approval-gated)

```text
POST /run/publish
  -> scheduled_publish.py
     -> checks IST 20:00 window (approval_integrity.upload_window_open)
     -> publish_all.py --scheduled-approved
        -> youtube_upload.py
        -> facebook_reels_upload.py
        -> instagram_reels_upload.py
     -> Wed/Sat only: youtube_longform_upload.py --scheduled-approved
```

Exit code 2 means "skipped cleanly" (outside window / review block) and is passed to n8n
as HTTP 200.

### 4.3 Manual/CLI flows

- `run_pipeline.sh` with `PUBLISH_MODE=publish` -> `create_short.py` ->
  `review_bundle.py` -> `publish_all.py`.
- `run_gen.sh` -> `strong_pipeline.py --topic ... --out metadata_strong.json`.
- `approve_review.py`, `approve_longform.py`, `setup_check.py`, `meta_preflight.py`,
  `model_health.py`, `monetization_tracker.py`, `workspace_sync.py` are manual tools.
- OAuth one-offs: `server_3000.py`, `auth_server.py`, `exchange_token.py`,
  `manual_auth.py`, `get_code.py`.

---

## 5. Python dependency graph

### 5.1 Core / AI / config

| Module | Imports | Imported by | Trigger | Target |
|---|---|---|---|---|
| `multi_model_ai.py` | `model_health`, `omniroute_client` | `app.research.selector`, `app.research.trends`, `app.script.longform`, `app.script.studio`, `create_short`, `model_health`, `visual_assets` | CLI + imports | `app/core/ai.py` |
| `model_health.py` | `multi_model_ai`, `omniroute_client` | `multi_model_ai` | CLI probe; reads `model_health.json` | `app/core/model_health.py` |
| `omniroute_client.py` | — | `model_health`, `multi_model_ai` | import only | `app/core/ai.py` |
| `ollama_chat.py` | — | — | CLI only (`multi_model_ai` talks to Ollama over HTTP itself) | archived in `archive/optional-cli/` |
| `logging_config.py` | stdlib only | — | none found | archived in `archive/unused-infra/` |
| `resilience.py` | stdlib only | — | none found | archived in `archive/unused-infra/` |

### 5.2 Research

| Module | Imports | Imported by | Trigger | Target |
|---|---|---|---|---|
| `app/research/topics.py` (was `topic_research.py`) | — | `create_longform`, `create_short`, `app.research.desk`, `strong_pipeline`, `app.research.selector` | imports | moved in Phase 4 |
| `app/research/trends.py` (was `trend_research.py`) | `multi_model_ai` (dynamic) | `app.research.selector` | imports | moved in Phase 4 |
| `app/research/selector.py` (was `topic_selector.py`) | `analytics_collect`, `multi_model_ai`, `app.research.topics`, `app.research.trends`, `visual_assets` | `strong_pipeline` | import | moved in Phase 4 |
| `app/research/desk.py` (was `research_desk.py`) | `app.research.topics` | `strong_pipeline` | import | moved in Phase 4 |
| `analytics_collect.py` | — | `app.research.selector` | CLI + import | `app/analytics/collect.py` |

`app.research.topics` and `app.research.trends` are sources; `app.research.selector` composes
them and `app.research.desk` reads the chosen sources. The package keeps the original
logic; only import paths and project-root lookups changed.

### 5.3 Script / voice

| Module | Imports | Imported by | Trigger | Target |
|---|---|---|---|---|
| `app/script/studio.py` (was `script_studio.py`) | `multi_model_ai`, `app.script.voice_guide` | `strong_pipeline` | CLI + import | moved in Phase 5 |
| `app/script/voice_guide.py` (was `voice_guide.py`) | — | `app.script.studio` | CLI + import | moved in Phase 5 |
| `app/script/longform.py` (extracted from `create_longform.py`) | `multi_model_ai`, `app.research.topics` | `create_longform` | import | moved in Phase 5 |
| `app/voice/provider.py` (was `voice_provider.py`) | — | `strong_pipeline` | CLI + import | moved in Phase 6 |
| `strong_pipeline.py` | `app.research.desk`, `app.research.selector`, `app.research.topics`, `app.script.studio`, `app.voice.provider`, `motion_director`, `motion_render` | `create_short` | `run_gen.sh`; imported by `create_short` | `app/script/pipeline.py` |

`app.script.voice_guide` is editorial prompt/copy guidance, not TTS. `app.voice.provider` is TTS.
Phase 6 merges the package only; the two modules stay separate. `create_longform.py` keeps only visual/render
helpers after Phase 5; script research and generation live in `app.script.longform`.

### 5.4 Visuals / render

| Module | Imports | Imported by | Trigger | Target |
|---|---|---|---|---|
| `stock_fetcher.py` | — | `motion_render`, `visual_assets` | CLI + import | `app/visuals/stock.py` |
| `visual_assets.py` | `multi_model_ai`, `stock_fetcher` | `create_short`, `motion_render`, `publish_social`, `topic_selector` | CLI + import | `app/visuals/assets.py` |
| `visual_quality.py` | — | `approve_longform`, `approve_review`, `publish_all`, `review_bundle`, `review_longform`, `youtube_longform_upload` | import only | `app/visuals/quality.py` |
| `motion_director.py` | — | `motion_render`, `strong_pipeline` | CLI + import | `app/visuals/motion.py` |
| `motion_render.py` | `motion_director`, `stock_fetcher`, `visual_assets` | `strong_pipeline` | CLI + import | `app/render/motion.py` |
| `video_archive.py` | — | `create_longform`, `create_short` | import only | `app/core/video_archive.py` |

### 5.5 Approval / review / notifications

| Module | Imports | Imported by | Trigger | Target |
|---|---|---|---|---|
| `approval_integrity.py` | — | `approve_longform`, `approve_review`, `publish_all`, `publish_social`, `review_bundle`, `review_longform`, `scheduled_publish`, `youtube_longform_upload` | import only | `app/approval/integrity.py` |
| `review_bundle.py` | `approval_integrity`, `visual_quality` | — | `run_pipeline.sh` | `app/approval/review_bundle.py` |
| `review_longform.py` | `approval_integrity`, `visual_quality` | — | `run_longform_pipeline.sh` | `app/approval/review_longform.py` |
| `approve_review.py` | `approval_integrity`, `visual_quality` | — | manual / Telegram instruction | `app/approval/approve.py` |
| `approve_longform.py` | `approval_integrity`, `visual_quality` | — | manual / Telegram instruction | `app/approval/approve.py` |
| `review_ledger.py` | — | — | CLI only | `app/analytics/ledger.py` or archive |
| `notify_review.py` | `notify_status` | — | both pipeline shell scripts | `app/approval/notify.py` |
| `notify_status.py` | — | `notify_review`, `publish_all`, `scheduled_publish`, `youtube_longform_upload` | shell + imports | `app/core/notify.py` |

### 5.6 Publishing

| Module | Imports | Imported by | Trigger | Target |
|---|---|---|---|---|
| `publish_all.py` | `approval_integrity`, `instagram_reels_upload`, `notify_status`, `visual_quality` | `publish_review_safe`, `publish_social` | `run_pipeline.sh` (publish mode), `scheduled_publish.py` | `app/publish/orchestrator.py` |
| `youtube_upload.py` | — | `youtube_longform_upload` | subprocess from `publish_all` | `app/publish/youtube.py` (short) |
| `youtube_longform_upload.py` | `approval_integrity`, `notify_status`, `visual_quality`, `youtube_upload` | — | subprocess from `scheduled_publish` | `app/publish/youtube.py` (long) |
| `facebook_reels_upload.py` | — | — | subprocess from `publish_all` | `app/publish/facebook.py` |
| `instagram_reels_upload.py` | stdlib only | `publish_all` | import (`public_video_url`) + subprocess | `app/publish/instagram.py` |
| `scheduled_publish.py` | `approval_integrity`, `notify_status` | — | subprocess from `n8n_runner` | `pipelines/publish_scheduled.py` |
| `publish_social.py` | `approval_integrity`, `publish_all`, `visual_assets` | — | CLI only | kept; decide in publish split phase |
| `publish_review_safe.py` | `publish_all` | — | CLI only | archived in `archive/optional-cli/` |

### 5.7 Orchestration / servers / one-off tools

| Module | Imports | Imported by | Trigger | Target |
|---|---|---|---|---|
| `create_short.py` | `multi_model_ai`, `strong_pipeline`, `topic_research`, `video_archive`, `visual_assets` | — | `run_pipeline.sh` | `pipelines/short.py` |
| `create_longform.py` | `multi_model_ai`, `topic_research`, `video_archive` | — | `run_longform_pipeline.sh` | `pipelines/longform.py` |
| `n8n_runner.py` | — | — | Docker CMD / Compose; n8n calls it | `api/main.py` (runner routes) |
| `server_3000.py` | — | — | manual OAuth | archived in `archive/legacy-oauth/` |
| `auth_server.py` | — | — | manual OAuth | archived in `archive/legacy-oauth/` |
| `server_5678.py` | — | — | manual, but dead | archived in `archive/legacy-oauth/` |
| `exchange_token.py` | — | — | CLI only | archived in `archive/legacy-oauth/` |
| `manual_auth.py` | — | — | CLI only | archived in `archive/legacy-oauth/` |
| `get_code.py` | — | — | CLI only | archived in `archive/legacy-oauth/` |
| `setup_check.py` | — | — | documented manual | `scripts/` |
| `meta_preflight.py` | — | — | documented manual | `scripts/` |
| `monetization_tracker.py` | — | — | documented manual | `app/analytics/` |
| `workspace_sync.py` | — (imports stdlib sqlite3) | — | documented manual | `app/core/db.py` |

---

## 6. Test dependencies

| Test | Local modules imported |
|---|---|
| `tests/test_approval_integrity.py` | `approval_integrity`, `publish_all`, `scheduled_publish` |
| `tests/test_longform_editorial.py` | `app.script.longform`, `create_longform` |
| `tests/test_longform_visuals.py` | `create_longform` |
| `tests/test_motion.py` | `motion_director`, `motion_render` |
| `tests/test_multi_model_ai.py` | `app.script.longform`, `create_short`, `multi_model_ai` |
| `tests/test_n8n_runner.py` | `n8n_runner` |
| `tests/test_n8n_workflow.py` | — (reads workflow JSON) |
| `tests/test_phase0_repo_hygiene.py` | — |
| `tests/test_research_desk.py` | `app.research.desk` |
| `tests/test_script_studio.py` | `app.script.studio`, `app.script.voice_guide` |
| `tests/test_setup_check.py` | — (copies `setup_check.py`) |
| `tests/test_strong_pipeline.py` | `app.script.studio`, `model_health`, `motion_director`, `stock_fetcher`, `strong_pipeline` |
| `tests/test_phase5_script_package.py` | `app.script.longform`, `app.script.studio`, `app.script.voice_guide`, `create_longform` |
| `tests/test_phase6_voice_package.py` | `app.voice.provider`, `strong_pipeline` |
| `tests/test_topic_research.py` | `app.research.topics` |
| `tests/test_visual_quality.py` | `approval_integrity`, `approve_longform`, `approve_review`, `visual_quality` |

All tests import modules from the repo root. Any Phase 4–7 move must either update these
imports or keep compatibility shims.

---

## 7. State and generated-file ownership

| File | Referenced by | Target |
|---|---|---|
| `metadata.json` | `create_short` writes; review/approve/publish/upload read | `data/` |
| `metadata_strong.json` | `strong_pipeline` / `run_gen.sh` | `data/` |
| `longform_metadata.json` | `create_longform` writes; review/approve/upload read | `data/` |
| `review_pending.json` | `review_bundle` writes; `approve_review`, `notify_review` read | `data/` |
| `review_queue/*.json` | `review_bundle` writes; `approve_review` reads | `data/review_queue/` |
| `review_approved.json` | `approve_review` writes; `publish_all`, `publish_social` read | `data/` |
| `longform_review_pending.json` | `review_longform` writes; `approve_longform`, `notify_review`, `youtube_longform_upload` read | `data/` |
| `longform_review_approved.json` | `approve_longform` writes; `youtube_longform_upload` reads | `data/` |
| `review_package.json` | no runtime references found; only docs/plans | legacy; inspect in Phase 8 |
| `uploaded_content.json` | `youtube_upload` | `data/` |
| `uploaded_longform_content.json` | `youtube_longform_upload` | `data/` |
| `social_upload_ledger.json` | `publish_social` | `data/` |
| `meta_uploads.json` | `facebook_reels_upload`, `instagram_reels_upload` | `data/` |
| `analytics_history.json`, `analytics_latest.json` | `analytics_collect`; `topic_selector` reads history | `data/` |
| `trend_cache.json`, `trend_history.json` | `trend_research` | `data/` |
| `model_health.json` | `model_health` writes; `multi_model_ai`, `n8n_runner`, `setup_check` read | `data/` |
| `monetization_progress.json` | `monetization_tracker` | `data/` |
| `feedback_ledger.csv` | `review_ledger`; `topic_selector` reads | `data/` |
| `used_topics.txt` | `topic_research`, `topic_selector`, `trend_research`, `create_short`, `create_longform` | `data/` |
| `recent_formats.txt` | `create_short` | `data/` |
| `workspace.db` | `workspace_sync.py` only (SQLite `content_records`) | `data/workspace.db` |
| `youtube_token.json` | OAuth helpers write; `youtube_upload`, `publish_all` read | secret, stay root/ignored |
| `output_short.mp4`, `output_longform.mp4` | render -> review -> publish | `outputs/` |
| `longform_voice.mp3`, `longform_subtitles.ass`, `longform_background.mp4` | `create_longform` | `outputs/` |
| `longform_script.txt` | `create_longform` | `data/` |
| `token_usage.json` | `multi_model_ai` | `data/` |
| `tts_output.mp3`, `voice.mp3`, `subtitles.ass`, `background.mp4` | `app.voice.provider`, `strong_pipeline`, `create_short` | `outputs/` |
| `shots/`, `media/`, `videos/`, `output/audio/` | generated assets | `outputs/` |
| archived videos | `video_archive` | `outputs/archive/` (or `VIDEO_ARCHIVE_DIR`) |
| `.scheduled_generation.lock` | `flock` in `run_scheduled_generation.sh` | replace with PID+timestamp lock |
| `.publish_all.lock` | `publish_all.py` PID-only lock | migrate to shared lock helper |
| `.env`, `.n8n-docker.env` | runtime secrets | never move into tracked data |

---

## 8. Archive decisions (Phase 3, 2026-10-26)

All archived files keep their history under `archive/` and are documented in
`archive/README.md`. No active module imports them and no shell script or n8n
workflow calls them.

1. **YouTube OAuth helpers — archived** to `archive/legacy-oauth/`:
   `server_3000.py` (port 3000), `auth_server.py` (port 5000),
   `exchange_token.py`, `manual_auth.py`, `get_code.py`, plus dead `server_5678.py`.
   The OAuth callback in use is n8n's port 5678; `youtube_token.json` already exists.
   The helpers keep absolute paths, so they still run directly from `archive/` if a
   manual re-auth is ever needed.
2. **Publish wrappers:** `publish_review_safe.py` archived to
   `archive/optional-cli/`. `publish_social.py` stays for now because it is documented
   in `docs/TOOLING_STACK.md` and checked by `setup_check.py`; decide in the publish
   split phase.
3. **Review tools:** `review_ledger.py` stays because `topic_selector` still reads
   `feedback_ledger.csv`; `review_package.json` is a generated artifact in `data/`.
4. **Unused infrastructure — archived:** `logging_config.py`, `resilience.py` to
   `archive/unused-infra/`; `ollama_chat.py` to `archive/optional-cli/`.
5. **Not duplicates — keep separate:** `youtube_upload.py` (short) vs
   `youtube_longform_upload.py` (long); `voice_guide.py` (copy guidance) vs
   `voice_provider.py` (TTS); `app.research.topics`/`app.research.trends` (sources) vs
   `app.research.selector` (composer).

---

## 9. Restructure risks

- **Hardcoded repo root** in the archived OAuth helpers under `archive/legacy-oauth/`,
  plus `notify_review.py`, `visual_assets.py`, `run_gen.sh`, `restore_n8n_workflow.sh`,
  and `compose.yaml`.
  Centralize behind `app/config.py` in the applicable phase; update Compose
  `STUDIO_ROOT`/bind mount together.
- **BOM at start of file:** archived `archive/unused-infra/logging_config.py` and
  `resilience.py` (`U+FEFF`). AST parsing failed until read with `utf-8-sig`; strip
  BOM if they are restored.
- **Move/import coupling:** tests and pipeline modules import top-level names. Do not move
  a module without updating every importer (tables above) or adding a temporary shim.
- **Runner paths:** `n8n_runner.py` checks for `run_scheduled_generation.sh` and
  `scheduled_publish.py` at `ROOT` and runs them with `cwd=ROOT`. Phase 9 must preserve
  those entrypoints or update the runner and Dockerfile atomically.
- **Docker:** `Dockerfile.runner` copies only `requirements.txt` and `n8n_runner.py`;
  `.dockerignore` allowlists the same. If the runner moves to `api/main.py`, update both.
- **Locks:** `.scheduled_generation.lock` is a 0-byte `flock` file;
  `.publish_all.lock` stores only a PID, no timestamp. Rule 12 (PID + timestamp + stale
  cleanup) is not implemented yet.
- **`server_5678.py`** prints `YOUTUBE_CLIENT_ID` (not a secret, but noisy) and does
  nothing else. Do not confuse it with the n8n container on 5678.
- **n8n workflow is inactive** (`active: false`). Keep the URL/auth contract intact when
  re-enabling; do not rename `/run/generate` or `/run/publish`.
- **Secrets:** `.env`, `.n8n-docker.env`, `youtube_token.json`, and `token_usage.json`
  are ignored. OAuth servers write `youtube_token.json`; never move that into `data/` if
  `data/` later becomes exportable.

---

## 10. Phase mapping

| Phase | Modules / files | Key constraint |
|---|---|---|
| 2 | generated MP4/MP3/ASS/JSON/assets; `metadata*`, `review_*`, `output_*`, `shots/`, `media/`, `output/` | update path constants; keep `review_*`/upload ledgers readable by existing tools |
| 3 | OAuth duplicate cluster, `publish_social`, `publish_review_safe`, `review_ledger`, `ollama_chat`, `server_5678` | confirm before archiving; no deletions |
| 4 | `topic_research`, `trend_research`, `topic_selector`, `research_desk`, `analytics_collect` | preserve public functions used by `strong_pipeline` |
| 5 | `create_short`, `create_longform`, `strong_pipeline`, `script_studio` | single entrypoints `pipelines/short.py`, `pipelines/longform.py`; preserve CLI args |
| 6 | `voice_guide`, `voice_provider` | moved to `app/script/voice_guide.py` and `app/voice/provider.py`; guidance vs TTS stay separate |
| 7 | `publish_all`, `youtube_upload`, `youtube_longform_upload`, `facebook_reels_upload`, `instagram_reels_upload` | split `app/publish/youtube.py`, `facebook.py`, `instagram.py`; keep subprocess/exit-code contract |
| 8 | all JSON ledgers + `workspace_sync.workspace.db` | migration script; keep JSON files until verified |
| 9 | `n8n_runner`, `server_3000`, `auth_server` | preserve n8n `:8080/run/*`; decide OAuth callback ports |
| 10 | tests, `Dockerfile.runner`, `compose.yaml`, dry-run | `DRY_RUN=1`, no paid API calls; full smoke + end-to-end dry run |

---

## 11. How this map stays current

`tests/test_phase1_dependency_map.py` checks that this document still contains the two n8n
endpoint URLs, the health route, both legacy server names, and the main pipeline entrypoints.
If an endpoint moves, that test must fail until this document is updated.
