# NEXTDECODE — Component, Agent and Tool Responsibility Map

Document ID: ND-INT-MAP-001
Version: 0.1.0-draft
Date: 2026-11-04
Status: PROPOSED RESPONSIBILITY MAP — must be reconciled with P0 contracts and owner-approved agent policy

## 1. Purpose
This map answers three questions for every capability: which component owns the work, which human/agent/service may use the relevant tool, and what the tool is for. It distinguishes a product runtime integration from a developer/reviewer tool. It does not assign agents or grant permissions.

## 2. Product component to agent responsibility
| Component/capability | Primary human/agent role | Tool/provider class | Purpose | Non-delegable boundary |
|---|---|---|---|---|
| Topic discovery and research | Research agent; creator | Search/news APIs, source fetchers, source registry | Discover topics, retrieve primary sources, create evidence-backed research packages | Research agent cannot invent sources or self-certify unsupported claims |
| Claim verification | Fact-check agent; QA reviewer | Source retrieval, claim/evidence ledger, deterministic validators | Verify exact claim excerpts, source independence, contradiction and uncertainty | Cannot approve rights, editorial release or publication |
| Brand and strategy | Strategy agent; creator | Brand/strategy profiles, audience/market evidence, analytics read models | Recommend priorities and briefs aligned with brand/audience context | AI recommendation does not silently change strategy/policy |
| Script/editorial | Script and editorial agents; creator | LLM provider abstraction, structured output validation, script critic | Generate/revise scripts against brief, evidence, voice and format constraints | Creator override and provenance retained; no unsupported factual claims |
| Visual direction | Visual Director agent; human reviewer | Stock/media sources, image/video generation providers, storyboard/vision QA | Plan scenes, source visuals, record provenance and review needs | Unknown rights or needs_review cannot be treated as cleared |
| Production/render | Production worker / Shorts Studio | Python pipeline, FFmpeg/ffprobe, TTS, asset adapter | Produce audio/video artifacts and run deterministic media QA | Worker cannot approve itself or bypass governance |
| Quality and rights | Governance/QA service; human reviewer | Rules engine, rights metadata, quality evaluators, evidence store | Produce PASS/PASS_WITH_WARNINGS/NEEDS_REVIEW/BLOCKED and use-specific rights findings | Hard blockers remain centrally enforced |
| Review and approval | Creator / authorized reviewer | Review UI, immutable review package, approval ledger | Approve or request changes for exact content/artifact version | Approval is not authorization or execution |
| Workflow execution | Orchestrator / scheduler / worker | DB-backed queue, outbox/inbox, worker registry | Durable task progression, retry, lease, idempotency and recovery | Agent framework is not workflow/job source of truth |
| Export/distribution | Export service; creator | Platform adapters, export packaging, analytics APIs | Prepare private export bundles and later permitted platform operations | No public publishing without separate authorization and central decision |
| Analytics and learning | Analytics agent; creator | Platform analytics APIs, metric store, evaluation datasets | Collect authorized performance signals and propose learning changes | Correlation is not causation; learning changes require approval |

## 3. Developer and engineering tool assignment (proposed)
| Tool | Intended user | Purpose | Required restriction | Status |
|---|---|---|---|---|
| ChatGPT / Codex | Product owner, coordinator, scoped engineering/research agents | Planning, research, design, code review and work orchestration | Respect assigned scope; do not imply repo write permission | Existing work environment; per-task authorization applies |
| Qoder | Assigned implementation agent | Execute explicitly assigned work package | Sole writer only where existing governance specifically assigns it; branch/scope/test rules apply | Historical role; current assignment must be re-confirmed per work package |
| OpenCode | Architecture/API reviewer or assigned engineering agent | Read-only architecture review unless explicitly assigned implementation | Review role cannot edit; no inferred authority | Historical role; scope-specific |
| Kilo | Independent QA/security reviewer | Independent read-only acceptance after implementation | No implementation edits during independent acceptance | Historical role; dispatch not implied |
| Copilot | Focused regression/code review | Targeted independent test review | No broad refactor or authority expansion | Candidate role; task-specific |
| Antigravity | Product/UI review | Targeted UI/UX feedback | No unrelated product expansion | Candidate role; task-specific |
| GitHub MCP | Engineering coordinator/reviewers | Remote repo, PR, commit, security evidence | --read-only; repository-limited credential; minimum toolsets | Candidate; evaluate first |
| Filesystem MCP | Documentation intelligence/QA reviewers | Read source, docs, tests, manifests and evidence | Read-only mount; only /home/demon/shorts_studio | Candidate; evaluate first |
| Git MCP | Reviewer only if technically read-only | Status/diff/history | Mutating tools must be unavailable; --repository exact target | Deferred pending safe configuration |
| Awesome Copilot skills | Documentation and codebase-intelligence agents | Reusable task instructions and templates | Audit installed skills; skill instructions do not grant tool permissions | Existing documentation-writer reported installed; verify inventory |

## 4. External integration ownership matrix (initial inventory)
| Integration family | Current code/document references | Consuming capability | Proposed service owner | State requiring verification |
|---|---|---|---|---|
| LLM providers | multi_model_ai.py, omniroute_client.py, model_health.py | Research, fact-check, strategy, script, metadata | Model Gateway/Provider Adapter | Exact chain/model/quota/cost and current health |
| TTS providers | app/voice/provider.py | Voice generation | Voice Adapter / Production | Provider order, voice terms, fallback policy and spend |
| Image/visual generation | visual_assets.py and app/visuals/chain.py | Visual generation and asset resolution | Visual Provider Adapter | Enabled provider, output rights, model and cost |
| Stock/media search | stock_fetcher.py, Wikimedia, Pexels/Pixabay references | Visual assets and long-form chapter footage | Media Source Adapter | API terms, attribution, quotas and availability |
| Research sources | YouTube Data API, Reddit, X, Trends references | Topic discovery and evidence | Research Source Adapter | API scopes, terms, quota, reliability and source quality |
| n8n | workflow JSON, n8n_runner.py | Scheduled trigger and workflow invocation | Scheduler Adapter | Live workflow ID/state, endpoint, timezone and auth |
| Telegram | notify_review.py, notify_status.py | Private review/status notifications | Notification Adapter | Chat scope, message data minimization and credential state |
| YouTube/Facebook/Instagram | publisher scripts and analytics_collect.py | Export/publishing and analytics | Distribution/Analytics Adapters | Separate read/write scopes, review, authorization and platform policy |
| Cloudinary/R2/Supabase/Notion/Airtable | workspace_sync.py and tooling note | Storage/workspace integrations | Storage/Workspace Adapters | Whether used, what data is stored, cost and accepted P0 storage contract |

## 5. Core interaction and control flow
1. Creator requests a task in the Content OS workspace/control surface.
2. Control plane validates identity, task scope and applicable policy.
3. Orchestrator creates a durable workflow/task/job record through the accepted P0 execution contracts.
4. Scheduler/queue assigns a bounded task to an eligible worker; agent reasoning is one bounded task capability, not a replacement for the worker/job lifecycle.
5. Agent/tool calls use only the declared tool profile and scoped credentials. External content is untrusted input.
6. Outputs are registered as immutable artifact versions with provenance and checksums.
7. Quality, rights and evidence checks run against exact versions.
8. Human review/approval is recorded against exact immutable review package and artifact versions.
9. Central authorization independently decides whether a protected action is permitted.
10. Export/distribution adapter performs only the authorized action and records provider outcome; unknown external outcomes are reconciled before retry.
11. Analytics collects separately authorized read-only metrics; learning proposals require human-controlled activation.

## 6. Cross-cutting safeguards
- Tool availability is not permission. Agent role is not identity authority.
- No agent may grant itself capabilities, approve its own work or alter policy.
- Secrets are never included in prompts, repository documents or diagnostic logs.
- Every external call records provider, operation, model/version, request correlation, latency, outcome and cost where available, without logging secret values or unnecessary personal data.
- Provider fallbacks must be explicit, observable and policy-compatible; a fallback must not silently change quality, rights or data-residency guarantees.
- User-facing publishing remains disabled unless the existing owner-approved publishing policy explicitly authorizes the exact action.

## 7. Open dependencies
- Reconcile the role map with P0 ADR-005/ADR-007 and WP2/WP3/WP5 boundaries.
- Reconcile all integration families with canonical Contract 05/07/10/11/12 and Data Dictionary ownership.
- Confirm which agents exist in the actual local toolchain and which are only historical proposals.
- Confirm provider usage from current code/config without exposing secrets.
- Define exact tool permission profiles before any MCP configuration is changed.
