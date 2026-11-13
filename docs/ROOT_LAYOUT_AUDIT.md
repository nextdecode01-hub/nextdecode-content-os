# Root layout audit — 2026-11-07

## Decision

The repository root is reserved for real execution entrypoints, project configuration and required runtime/service files. Application implementations belong in their canonical domain packages. Root-level forwarding/compatibility Python wrappers are retired and prohibited.

## Allowed root Python entrypoints

| File | Purpose |
|---|---|
| `setup_check.py` | Standalone environment/setup diagnostic. |

All other application modules live under `app/` or `tools/`. The retired wrappers and their hashes are preserved outside the repository for recovery only. The former automation bridge and all dedicated integration files/services were removed after the local task API and worker cutover.

## Canonical package layout

- `app/research/`, `app/script/`, `app/voice/`: research, editorial scripting and voice.
- `app/visuals/`, `app/render/`: shot planning, asset selection, rights metadata, storyboard, rendering and QA.
- `app/providers/`: LLM providers, health and OmniRoute.
- `app/operations/`, `app/tracking/`: operations, analytics, archive, workspace and run state.
- `app/notifications/`: outbound notifications only.
- `app/review/`, `app/security/`: human review, approvals and integrity.
- `app/publish/`: publishing adapters, orchestration, scheduler and authorization.
- `tools/maintenance/`: explicit maintenance commands.

## Runtime entrypoints

- `run_pipeline.sh`, `run_scheduled_generation.sh`, and `run_longform_pipeline.sh` invoke package modules with `python -m`.
- `api/main.py` exposes authenticated task and plan routes; the dedicated autonomy worker runs from `app.autonomy.cli`.
- Publishing orchestration invokes platform adapters by canonical package module, not root script paths.
- Approval commands use `python -m app.review.approve_review` and `python -m app.review.approve_longform`.

## Local-only and runtime paths

- `.env`, `youtube_token.json`, `venv/`, `.venv/`, `outputs/`, `data/`, runtime locks, caches and local tunnel tooling are ignored or local runtime state.
- The dated `.env` backup is stored outside the repository under `/home/demon/.local/share/nextdecode/shorts-studio-local/`.
- `_holding/` contains quarantined recovery utilities, not active runtime code.
- `archive/` and `reports/` preserve historical records.
- `.agents/`, `.kilo/` and `.vscode/` contain active development configuration.

## Root cleanup acceptance

- Exactly one Python file is allowed at root: `setup_check.py`.
- Root wrapper absence is enforced by `tests/test_root_compatibility_facades.py`.
- Canonical package paths and module CLI entrypoints are covered by package-layout tests.
- No credentials, runtime data, media, virtual environments or local cache should be committed.
