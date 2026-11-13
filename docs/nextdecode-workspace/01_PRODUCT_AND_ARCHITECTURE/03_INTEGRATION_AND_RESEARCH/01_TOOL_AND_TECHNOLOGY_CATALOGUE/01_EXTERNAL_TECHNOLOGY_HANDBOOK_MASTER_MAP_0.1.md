# NEXTDECODE External Technology Handbook — Master Map

Version: 0.1.0-draft | Date: 2026-11-04
Status: Learning/evaluation guide; not implementation authorization.

## 1. Purpose

This handbook explains every external technology, tool and service proposed for NEXTDECODE: what it is, why it exists, how it works, where it fits, what it costs, what risks it adds, what alternatives exist and whether we should use it.

Every detailed chapter must cover:
1. Plain-language definition and technical purpose.
2. Problem solved and practical NEXTDECODE use case.
3. Architecture and data/request flow.
4. Integration method: API, SDK, CLI, MCP, webhook, database or file.
5. Data sent, retention, telemetry, privacy and residency.
6. Licence, free tier, paid usage, quotas, hidden infrastructure cost and commercial restrictions.
7. Security, reliability, lock-in and operational risks.
8. Alternatives and existing project capabilities.
9. Adoption decision, acceptance tests, rollback and maintenance.

Open-source, free local software and free hosted tiers are different things. A free tier is not necessarily unlimited, permanent, commercially unrestricted or zero-cost to operate. Pricing, licences and availability must be sourced and dated.

## 2. Proposed technology catalogue

### A. AI models and routing
- OpenAI API: hosted model inference.
- Google Gemini API: hosted model inference.
- Groq: hosted inference for supported models; model/organization rate limits apply.
- Anthropic API: hosted model inference.
- Ollama: local model runtime; hardware and model licence matter.
- OmniRoute: model/provider routing tool previously discussed; exact build and configuration require verification.
- LiteLLM: possible unified model gateway; evaluate only if routing, budgets or observability needs justify it.

Learn: tokens, context windows, input/output pricing, RPM/TPM, structured outputs, tool calling, latency, fallback, prompt injection, data retention and model licences.

### B. Speech and audio
- Edge TTS, gTTS, ElevenLabs, Cartesia: speech generation options with different service terms, quality, latency and pricing.
- faster-whisper: local speech-to-text.
- FFmpeg/ffprobe: local media processing and inspection.

Learn: TTS/STT, consent and voice rights, phoneme preparation, loudness, codecs, sample rate, captions and audio QA.

### C. Research and evidence
- Search/news providers and Exa: source discovery.
- Google Trends: trend-interest signal, not proof of market demand.
- Reddit: qualitative community signal, not a representative sample.
- Wikimedia, Pexels, Pixabay: media discovery; verify rights and attribution per asset.

Learn: provenance, evidence/claim links, freshness, source quality, bias, rights and attribution.

### D. Image, video and creative generation
- fal and Replicate: hosted model execution platforms; model-specific price and rights.
- Local image/video models: later option subject to hardware and licence.
- FFmpeg: compositing, transcoding, subtitles and assembly.
- B-roll and motion graphics: distinguish original, generated, licensed stock and public-domain assets.

Learn: async job lifecycle, reproducibility, frame rate, resolution, codecs, provenance and commercial rights.

### E. Databases and storage
- PostgreSQL-compatible database: accepted authoritative shared-state direction under P0 ADR-002.
- SQLite: bounded local/specialist-engine use only; not a replacement for accepted P0 authority.
- Cloudflare R2: object storage candidate behind the accepted abstraction.
- Supabase: managed PostgreSQL-related platform; evaluate against accepted DB/auth boundaries.
- Cloudinary: media management/transformation candidate; compare with direct object storage and FFmpeg.

Learn: relational records vs binary objects, immutable artifact versions, checksums, retention, backups, restore, access control and residency.

### F. Workflow, agents and MCP
- n8n: workflow automation; licence and use-case restrictions require review.
- PydanticAI: typed Python agent framework; evaluation candidate.
- LangGraph: stateful graph orchestration; alternative evaluation candidate.
- MCP: protocol exposing tools/resources/prompts; not a security boundary.
- GitHub MCP: repository context/actions; read-only evaluation first.
- Filesystem MCP: blocked pending OS/container isolation.
- Git MCP: deferred until mutation can be technically excluded.
- OpenTelemetry: vendor-neutral telemetry ecosystem.
- Langfuse/Phoenix: alternative LLM observability/evaluation platforms.

Learn: state machines, durable execution, retries, idempotency, queues, checkpoints, human review, capability security, annotations, sandboxing and audit logs.

### G. Notifications and distribution
- Telegram bot: notifications; protect tokens and chat authorization.
- YouTube Data API: OAuth, quota, upload processing and visibility controls.
- Instagram/Facebook APIs: platform permissions, app review and publishing eligibility.
- n8n notifications: alerting only; not an authorization bypass.

Learn: OAuth scopes, refresh tokens, quota, webhooks, idempotency, private/unlisted/public visibility and unknown outcomes.

### H. Developer productivity
- GitHub: source, issues, PRs, releases and security advisories.
- GitHub Awesome Copilot: skill discovery; audit against existing local skills.
- VS Code MCP: client configuration and trust boundaries.
- Docker/Compose: isolation and repeatable services; unavailable in inspected WSL baseline.
- SBOM/dependency scanners: future security evaluation.
- Notion: optional knowledge/task integration; must not become an ungoverned duplicate canonical source.

## 3. Learning sequence

| Module | Topic | Exit knowledge |
|---|---|---|
| 01 | API, SDK, CLI, MCP, webhook | Explain how tools connect |
| 02 | LLM providers, routing, tokens, limits | Compare cost, quality, latency and privacy |
| 03 | Agent frameworks and orchestration | Separate agent reasoning from durable business workflow |
| 04 | Database and object storage | Explain DB vs object store and immutable versions |
| 05 | TTS, STT, image/video and FFmpeg | Compare hosted and local media workflows |
| 06 | Research, evidence and rights | Trace claims/assets to evidence and rights |
| 07 | Notifications and platform APIs | Explain OAuth, quota and publishing visibility |
| 08 | Observability and evaluation | Diagnose failures without leaking data |
| 09 | MCP, GitHub and filesystem security | Apply least privilege and isolation |
| 10 | Licensing, cost and version governance | Make evidence-based dependency decisions |

## 4. Architecture guardrails

- Existing Shorts Studio remains the specialist production engine.
- Content OS integrates around it through bounded, versioned contracts.
- PostgreSQL-compatible persistence remains authoritative under accepted P0 ADR-002.
- Object storage remains behind the accepted storage abstraction.
- Centralized authorization governs side effects.
- Approval, authorization, execution and successful publication are distinct.
- Missing or ambiguous rights/authorization never grants permission.
- Human approval before publishing; public auto-publishing remains disabled absent separate authorization.
- No agent framework, MCP server or provider may create a parallel source of truth.

## 5. Free vs paid classification

For each service classify: open-source licence; free local software; hosted free tier; trial credit; paid usage API; paid managed service; or commercially restricted/source-available licence.

Record currency/tax, quotas, overages, payment-card requirement, data-use/training terms, commercial rights, rate limits, hardware/bandwidth, maintenance and exit cost.

## 6. Handbook volumes

1. Integration foundations, APIs, MCP, GitHub and filesystem.
2. LLM providers, routing, local models and agent frameworks.
3. Research, search, evidence and media rights.
4. TTS, STT, image/video generation and FFmpeg.
5. PostgreSQL, object storage, Supabase, R2 and media storage.
6. n8n, queues, notifications and platform distribution APIs.
7. OpenTelemetry, Langfuse, Phoenix, evaluation and QA.
8. Security, licensing, cost governance, upgrades and vendor exit.

Each volume will include plain-English teaching, technical architecture, NEXTDECODE examples, comparison tables, verified costs/licences, security checks and comprehension exercises.

## 7. Status

This is the master map and learning plan. It does not prove that listed tools are required, active, free, compatible or approved. Detailed volumes and provider-by-provider verification remain open.
