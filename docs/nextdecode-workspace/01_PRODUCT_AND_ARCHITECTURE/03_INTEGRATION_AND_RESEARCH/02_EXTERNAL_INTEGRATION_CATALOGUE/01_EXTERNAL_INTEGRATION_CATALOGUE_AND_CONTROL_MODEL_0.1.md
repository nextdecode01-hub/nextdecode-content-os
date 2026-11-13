# External Integration Catalogue — first-pass architecture and evidence register

**Document ID:** INT-CAT-001  
**Version:** 0.1 (working draft)  
**Date:** 2026-11-04  
**Status:** Research baseline; not an adoption, provider activation or implementation decision  
**Authority:** Subordinate to accepted P0 ADRs/CFs, canonical contracts and owner-approved policies.

## 1. Purpose and interpretation

This catalogue translates the existing Shorts Studio integration surface into a controlled Content OS integration inventory. It distinguishes source-code observations from dated documentation, live verification and future candidates. A key present in `.env.example`, a provider name in a fallback list, or an old successful test report does **not** prove that a provider is currently configured, reachable, paid, entitled or operational.

**Status vocabulary**
- **Observed in code:** adapter/client path exists in the inspected source.
- **Documented (historical):** named in a project document; freshness and runtime state unverified.
- **Live verified:** only allowed after an authorized, non-destructive health/contract check with recorded timestamp and evidence. None is claimed in this document.
- **Candidate:** evaluated for possible future use; not adopted.
- **Unknown:** current configuration, entitlement, account approval, availability or runtime state is not established.

## 2. Integration catalogue

| ID | Capability / provider family | Evidence observed in Shorts Studio | Status now | Content OS ownership / boundary | Priority |
|---|---|---|---|---|---|
| INT-LLM-01 | Groq | Historical provider report and env keys; source references in legacy tooling docs | Documented (historical); live state unknown | Model Gateway adapter; model selection/routing policy belongs to Content OS, not individual agents | P1 evaluation |
| INT-LLM-02 | Gemini Developer API | Direct image-generation HTTP client in `app/visuals/visual_assets.py`; historical text-provider report | Observed in code for image path; text runtime unknown | Model Gateway; task/model capability registry and data policy required | P1 evaluation |
| INT-LLM-03 | OmniRoute | Historical provider chain and env keys in project docs | Documented (historical); source/runtime reconciliation open | Model Gateway adapter only; intermediary routing must preserve provider/model attribution and cost | P1 evaluation |
| INT-LLM-04 | Ollama | Env key and historical local model reference | Documented (historical); local service state unknown | Optional local inference adapter; no silent substitution for cloud model semantics | Candidate |
| INT-LLM-05 | OpenAI API | TTS path and image-provider path exist in code; env keys | Observed in code for TTS/image; model gateway state unknown | Model Gateway / Speech adapter; explicit spend ceiling and data controls | Candidate/conditional |
| INT-LLM-06 | Cloudflare Workers AI, OpenRouter, Mistral, Cerebras, NVIDIA NIM, Pollinations text | Keys/model variables appear in `.env.example`; not proof of implemented clients | Unknown / candidate | Must not enter production routing until client, contract, cost and safety review exist | Discovery backlog |
| INT-TTS-01 | Edge TTS | `app/voice/provider.py` includes edge_tts first in provider list and local CLI lookup | Observed in code; external service availability/terms unknown | Speech adapter; preserve voice/model/version and generated-audio provenance | P0-compatible candidate |
| INT-TTS-02 | ElevenLabs | HTTP endpoint and adapter path in `app/voice/provider.py` | Observed in code; key/plan/rights unknown | Speech adapter; commercial-use rights and plan terms must be checked | Optional |
| INT-TTS-03 | Cartesia | HTTP endpoint, API version and adapter path in source | Observed in code; key/plan/rights unknown | Speech adapter; model/version and voice licensing metadata required | Optional |
| INT-TTS-04 | OpenAI TTS | Speech endpoint and model defaults in source | Observed in code; account/billing unknown | Speech adapter; explicit paid-provider opt-in | Optional |
| INT-IMG-01 | Pollinations | Image provider path in `app/visuals/visual_assets.py`; key optional | Observed in code; service terms/availability unknown | Image-generation adapter; do not treat free/keyless as SLA or commercial-rights guarantee | Conditional |
| INT-IMG-02 | Gemini image generation | Direct API path in source | Observed in code; current model/limits unknown | Image-generation adapter; record model, prompt, response and provider terms | Conditional |
| INT-IMG-03 | fal.ai / Replicate | Direct HTTP prediction paths in source | Observed in code; credentials/credits unknown | Image/video generation adapter; asynchronous job lifecycle and cost ceiling required | Optional |
| INT-IMG-04 | Cloudflare AI / local FFmpeg | Cloudflare provider listed; local FFmpeg fallback present | Partial code evidence; runtime unknown | Image/visual adapter; distinguish generated assets from deterministic local graphics | Candidate |
| INT-MEDIA-01 | Wikimedia Commons | `app/visuals/stock_fetcher.py` calls Commons API and extracts licence/author/page metadata | Observed in code | Media ingestion adapter; rights/attribution evidence mandatory per asset | Current code path |
| INT-MEDIA-02 | Pexels / Pixabay | Project docs and env template reference them; inspected stock fetcher is Wikimedia-based | Documented/candidate; current client not confirmed | Media-source adapter; store asset URL, creator, licence snapshot, retrieval time and attribution | Candidate |
| INT-RESEARCH-01 | Hacker News, arXiv, Reddit RSS, Google Trends RSS, Google News RSS, DuckDuckGo/Bing | `app/research/topics.py` contains fetchers for several feeds/search paths | Observed in code for inspected module; complete feed list needs audit | Research-source adapters; preserve source URL, publisher, timestamp, retrieval time and evidence excerpt | Current code path |
| INT-RESEARCH-02 | X, YouTube Data API, Reddit OAuth, Trends API | Env template / historical docs reference credentials | Documented/candidate; implementation and scopes require per-module audit | Research-source adapters; least-privilege access and platform terms | Candidate |
| INT-STORE-01 | SQLite | Local state references in repository docs/code | Observed/documented; not authoritative shared Content OS DB | Local cache/dev/test only where allowed; **must not override accepted PostgreSQL-authoritative ADR-002** | P0 boundary |
| INT-STORE-02 | PostgreSQL-compatible DB | Accepted P0 ADR-002 | Accepted architecture decision; deployment/runtime unknown | Authoritative shared state via canonical persistence boundary | P0 required |
| INT-STORE-03 | Cloudflare R2 / Cloudinary | Env template and historical workspace-sync docs | Documented/candidate; no live account proof | Binary object storage behind adapter; relational metadata and immutable ArtifactVersion records remain authoritative | P1 evaluation |
| INT-STORE-04 | Airtable / Notion / Supabase | Env template and historical workspace-sync docs | Documented/candidate; do not equate with canonical DB | Optional workspace/export integrations only; no competing system of record | Deferred |
| INT-ORCH-01 | n8n | Historical workflow ID and schedule in TOOLING_STACK.md; current deployment not verified | Documented (historical); live state unknown | External orchestration trigger/adapter; Content OS DB remains durable authority | P1 evaluation |
| INT-NOTIFY-01 | Telegram, Discord, WhatsApp, email-like relays | Env template / historical docs | Documented/candidate; current send paths and consent unknown | Notification adapter; messages contain minimal metadata, no secrets or unnecessary personal data | Optional |
| INT-PLAT-01 | YouTube Data API | Upload adapter exists; OAuth and upload ledger in source | Observed in code; authorization and live state unknown | Distribution adapter only; central authorization gate must precede side effect | Disabled unless explicitly authorized |
| INT-PLAT-02 | Instagram/Facebook Graph API, Threads, Bluesky, Mastodon, Pinterest, others | Several upload modules / env keys / historical docs | Mixed code/documentation; each platform requires separate audit | Separate platform adapters with per-platform scopes, policy, review and unknown-outcome reconciliation | Deferred |
| INT-AN-01 | YouTube Analytics, Meta Insights, GA4 | Historical docs and env template | Documented; YouTube Analytics scope gap reported historically | Read-only analytics ingestion; analytics cannot mutate editorial or approval state | Optional |
| INT-DEV-01 | GitHub API / GitHub MCP | GitHub connected tooling and prior MCP candidate screen | Candidate/connected tool availability is not repo authorization | Read-only repo intelligence first; write access separate explicit grant | High-priority evaluation |

## 3. Source-derived architecture observations

1. `app/voice/provider.py` defines a provider list containing Edge TTS, ElevenLabs, Cartesia, OpenAI and silent fallback. Its module comments describe fallback behavior, but that does not establish the current account entitlement or commercial-use rights.
2. `app/visuals/visual_assets.py` defines Pollinations, Gemini, Cloudflare, fal, Replicate, OpenAI, Wikimedia and local paths. The source includes direct HTTP calls and cooldown behavior. Provider ordering and model defaults are source-level behavior, not a Content OS-approved policy.
3. `app/visuals/stock_fetcher.py` queries Wikimedia Commons and returns licence, author, licence URL and page URL metadata. This is a useful provenance pattern, but metadata quality and the actual licence terms still require per-asset review.
4. `app/research/topics.py` includes Hacker News, arXiv, Reddit RSS, Google Trends RSS, Google News RSS, DuckDuckGo HTML and Bing News RSS fetch paths. These are best-effort discovery inputs, not authoritative evidence by themselves.
5. `docs/TOOLING_STACK.md` and `docs/AI_PROVIDER_STATUS.md` are dated project documents with conflicting provider/order claims. Treat SRC-INT-001..006 as open until reconciled.
6. `.env.example` lists many credentials and provider variables. It is a configuration schema hint only. No secret values were read for this catalogue.

## 4. Required Content OS integration pattern

Every external integration must sit behind a typed, versioned adapter contract. The adapter must not own business policy.

**Required logical envelope (field names are illustrative until mapped to the canonical API/Event standard):**
- `integration_id`, `provider_id`, `provider_account_ref` (opaque, non-secret)
- `operation`, `request_id`, `idempotency_key` where provider semantics support it
- `contract_version`, `provider_api_version`, `model_or_endpoint_version`
- `requested_at`, `started_at`, `completed_at`, `timeout_ms`
- `outcome`: succeeded / rejected / retryable_failure / permanent_failure / unknown
- `external_operation_ref`, `provider_request_ref` (redacted/safe)
- `usage`, `cost_estimate`, `currency`, `quota_snapshot` where available
- `data_classification`, `retention_class`, `rights_evidence_refs`
- `error_class`, `retry_after`, `correlation_id`

The exact envelope and event semantics must be reconciled with the canonical API/Event and Lifecycle standards before implementation. This document does not create a new canonical contract.

## 5. Cross-cutting controls

### 5.1 Credentials and authorization
- Keep secrets in a dedicated secret store or protected runtime environment; never in source, logs, prompts, artifacts, or agent-visible context.
- Use separate credentials per environment and provider account; least privilege; rotation and revocation procedures.
- Do not pass provider keys to workers/agents unless the adapter requires them. Prefer a server-side adapter with capability-scoped access.
- Treat OAuth consent, app review, token refresh, account ownership and provider-specific permissions as explicit operational dependencies.
- A credential's presence is not authorization to perform a business action.

### 5.2 Data and privacy
- Classify every request payload before sending it externally. Default to minimum necessary content.
- Never send private user data, credentials, approval records or internal governance documents to model/media providers unless an approved data-processing basis and purpose exist.
- Record provider retention/training terms and regional processing before adoption.
- Keep raw prompts and payloads out of logs by default; use redacted structured diagnostics.

### 5.3 Reliability and unknown outcomes
- Apply bounded timeouts, concurrency limits, exponential backoff with jitter and provider-specific Retry-After handling.
- Retry only operations known to be safe. A timeout after a remote side effect must become **unknown**, not automatic retry.
- For uploads/publication, reconcile remote state using external IDs/status before any retry. Never assume local timeout means remote failure.
- Store provider request IDs, external operation IDs and correlation IDs where available.
- A fallback provider can change quality, safety, licensing, latency, model behavior and cost. Record the actual provider/model used for each output.

### 5.4 Rights and licensing
- Every externally sourced or generated asset must carry provenance and rights evidence appropriate to its use.
- Stock media records should include creator, source page, licence identifier/URL, attribution text, retrieval time and any restrictions.
- Model-generated outputs need provider/model/terms snapshot and prompt lineage; do not infer exclusive ownership or unrestricted commercial rights.
- No asset enters a publishable package with missing or ambiguous rights.

### 5.5 Cost and quota
- Free tiers are conditional, model-specific, account-specific and changeable. Do not label a provider “free forever.”
- Track estimated and actual usage per task, provider, model and account. Enforce per-run and monthly budgets before invocation.
- Cache eligible read operations; deduplicate research; avoid retry storms; expose quota exhaustion as a controlled state.
- Paid services require explicit owner approval and a documented budget ceiling.

## 6. Initial provider decisions (recommendations, not approvals)

| Decision ID | Recommendation | Rationale | Required owner action |
|---|---|---|---|
| INT-DEC-01 | Keep PostgreSQL as the only authoritative shared-state target | Accepted ADR-002; SQLite/workspace tools must not create a competing source of truth | None; preserve accepted ADR |
| INT-DEC-02 | Treat existing provider chains as Shorts Studio internals, not Content OS policy | Existing source order may be stale and can change behavior/cost/rights | Approve future adapter inventory and policy boundary |
| INT-DEC-03 | Use Wikimedia Commons as an existing source-code pattern, not blanket licence clearance | Code records licence metadata; each asset still needs rights validation | Define minimum evidence and acceptance rule |
| INT-DEC-04 | Evaluate R2 for binary object storage only after canonical ArtifactVersion and storage contracts close | R2 has S3-compatible API and published free usage, but account/billing/retention controls remain | Owner approval after WP4 and cost/security review |
| INT-DEC-05 | Keep publishing adapters disabled by default | Accepted P0 authorization invariant and human approval policy | Separate explicit authorization required for any live publish |
| INT-DEC-06 | Build provider/model inventory and policy before selecting a “primary” model chain | Historical provider docs conflict; free-tier/limits/terms differ | Owner decision after capability benchmark and privacy review |

## 7. Minimum acceptance checklist for any future adapter

- [ ] Canonical contract owner and version identified; no duplicate system-of-record semantics.
- [ ] Provider API version, supported operations and official documentation recorded.
- [ ] Authentication scopes, secret storage, rotation and revocation tested without exposing credentials.
- [ ] Data classification, retention, training use and region reviewed.
- [ ] Pricing, quota, free-tier expiry/conditions and budget ceiling recorded.
- [ ] Timeouts, retry rules, idempotency and unknown-outcome reconciliation specified.
- [ ] Rights/licensing and attribution requirements represented in metadata.
- [ ] Contract tests cover success, malformed response, 401/403, 429, 5xx, timeout and partial/unknown outcomes.
- [ ] Observability includes provider/model/version, correlation IDs, usage, latency and redacted error class.
- [ ] Rollback/disable switch and fallback behavior reviewed.
- [ ] Security/owner approval recorded before activation.

## 8. Open dependencies

1. Complete source audit for every integration module, including publishing, analytics, storage/workspace sync, notifications and n8n. The current inspection is a targeted first pass.
2. Reconcile SRC-INT-001..006 and refresh the stale provider/workflow documents.
3. Map each integration to the exact canonical API/Event, Lifecycle, Artifact, Rights, Approval and Distribution contract sections.
4. Resolve provider account/credential ownership, scopes, commercial terms and current entitlements without reading or copying secret values.
5. Close WP4 artifact storage/version/retention decisions before selecting binary storage.
6. Close WP5 rights/approval/authorization semantics before enabling external side effects.
7. Close WP6 retry, idempotency, unknown-outcome and recovery acceptance before enabling publishing or other non-idempotent operations.

## 9. Official documentation and source references

Checked on 2026-11-04. Pricing and limits are snapshots; recheck before implementation.

- [Groq API reference](https://console.groq.com/docs/api-reference) and [rate limits](https://console.groq.com/docs/rate-limits).
- [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing) and [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits). The free tier has limited model access; Google states that free-tier content may be used to improve products, while paid-tier content is not. This is a material privacy decision, not just a price comparison.
- [ElevenLabs API pricing](https://elevenlabs.io/pricing/api) and [API cost explanation](https://elevenlabs.io/docs/help-center/technical/how-much-does-it-cost-to-use-the-api).
- [Cartesia pricing](https://www.cartesia.ai/pricing). Current public page shows a free plan with 20K monthly credits; commercial-use licensing is listed under Pro, so do not assume the free tier covers commercial NEXTDECODE publishing.
- [Pexels API documentation](https://www.pexels.com/api/documentation/) and [terms summary](https://help.pexels.com/hc/en-us/articles/900005880463-What-are-the-Terms-and-Conditions). The API has attribution/rate-limit requirements and restrictions on standalone redistribution and AI dataset/model use.
- [Pixabay API documentation](https://pixabay.com/api/docs/). Attribution is requested when API results are displayed; default documented rate limit is 100 requests per 60 seconds.
- [Cloudflare R2 pricing](https://developers.cloudflare.com/r2/pricing/) and [API options](https://developers.cloudflare.com/r2/api/). The published Standard tier includes 10 GB-month storage, 1M Class A and 10M Class B operations per month; account subscription and overage still require controls.
- [YouTube videos.insert](https://developers.google.com/youtube/v3/docs/videos/insert) and [Data API quota guide](https://developers.google.com/youtube/v3/determine_quota_cost). Use the exact current API quota table; the upload endpoint requires OAuth scope such as youtube.upload.
- [Google OAuth scopes](https://developers.google.com/identity/protocols/oauth2/scopes) includes the separate yt-analytics.readonly scope for analytics reads.
- [n8n queue mode documentation](https://docs.n8n.io/hosting/scaling/queue-mode/) (deployment/scaling reference; current local deployment still needs direct verification).
- [Wikimedia Commons API](https://www.mediawiki.org/wiki/API:Main_page) and [reuse guidance](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia).

## 10. Change log

- 0.1 — Initial integration inventory and control model based on targeted source inspection plus official documentation review. No provider health checks, credentials, API calls, installs, code changes or runtime configuration changes performed.
