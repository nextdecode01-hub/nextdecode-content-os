# Archive

Files moved here during the restructure. Nothing was deleted. Archived files are
not imported by active code, are not called by the n8n workflow, and are not run
by any shell pipeline.

Restore a file with `git mv archive/<group>/<file> <destination>`.

## legacy-oauth/

Moved in Phase 3 (2026-10-26). n8n owns the YouTube OAuth callback at
`http://localhost:5678/rest/oauth2-credential/callback`; these helpers duplicate
that flow and no active module imports them. `youtube_token.json` already exists
in the repo root, and the helpers keep their absolute paths so they still run
directly from this folder if a manual re-auth is ever needed.

| File | Why archived |
|---|---|
| `server_3000.py` | Duplicate OAuth callback server on port 3000; redirect URI in use is port 5678. |
| `auth_server.py` | Duplicate OAuth callback server on port 5000; same overlap with the n8n callback. |
| `server_5678.py` | Dead 11-line stub: starts no server and only prints `YOUTUBE_CLIENT_ID`. |
| `exchange_token.py` | CLI code-exchange helper; superseded by n8n's OAuth credential flow. |
| `manual_auth.py` | CLI helper that only prints an auth URL; superseded by n8n's OAuth flow. |
| `get_code.py` | CLI helper that exchanges an auth code; same overlap as `exchange_token.py`. |

## unused-infra/

Moved in Phase 3 (2026-10-26). No inbound imports, no shell or workflow references.

| File | Why archived |
|---|---|
| `logging_config.py` | Never imported. Its intended replacement is `app/core/logging.py` in a later phase. |
| `resilience.py` | Never imported. Its intended replacement is `app/core/resilience.py` if retries are wired later. |

Both files start with a UTF-8 BOM; keep that in mind if they are restored.

## optional-cli/

Moved in Phase 3 (2026-10-26). Standalone CLIs that no runtime path calls.

| File | Why archived |
|---|---|
| `ollama_chat.py` | CLI chat client; `multi_model_ai.py` already talks to Ollama over HTTP itself. |
| `publish_review_safe.py` | Thin wrapper around `publish_all.py`; not called by n8n or the shell pipeline. |

## superseded/

Moved in Phase 5 (2026-10-27). Replaced by the target-tree entrypoints; the logic now
lives in `app/script/` and `pipelines/`.

| File | Why archived |
|---|---|
| `create_short.py` | Split into `app/script/short.py` (script generation) and `pipelines/short.py` (voice, visuals, render, QA, CLI). Restore only if the new entrypoint misbehaves. |

## Deliberately kept in the repo root

These look optional but are still referenced, documented, or checked by
`setup_check.py`, so Phase 3 does not archive them:

- `publish_social.py` — documented multi-platform publisher and checked by `setup_check.py`; decide in the publish split phase.
- `review_ledger.py` — manual feedback-ledger CLI; `topic_selector` still reads the ledger CSV.
- `monetization_tracker.py`, `meta_preflight.py`, `workspace_sync.py`, `setup_check.py` — documented manual tools scheduled for `scripts/` or `app/analytics/` in later phases.
