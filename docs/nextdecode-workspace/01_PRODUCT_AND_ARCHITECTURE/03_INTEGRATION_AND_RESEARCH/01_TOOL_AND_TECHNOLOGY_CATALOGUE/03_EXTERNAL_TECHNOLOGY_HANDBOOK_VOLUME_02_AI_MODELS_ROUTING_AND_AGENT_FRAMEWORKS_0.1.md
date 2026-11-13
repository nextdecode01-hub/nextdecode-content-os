# External Technology Handbook — Volume 02
## AI Models, Routing and Agent Frameworks
**Document ID:** NDX-TECH-HB-V02  
**Version:** 0.1  
**Research date:** 2026-11-04  
**Status:** Research draft — decision support, not implementation authorization  
**Parent:** External Technology Handbook Master Map 0.1  
**Scope:** NEXTDECODE Content OS and the existing Shorts Studio specialist production engine

---

## 1. Executive decision

Keep the AI provider layer small, replaceable and task-specific.

1. Do not select one permanent model vendor. Use task-specific provider adapters and a versioned internal request/response contract.
2. Do not add a gateway merely because it supports many providers. Prove a need for provider switching, cost attribution, budgets, retries/fallbacks or shared access first.
3. Keep model routing separate from workflow orchestration. A router dispatches model calls; an agent framework coordinates model/tool steps and state.
4. Deterministic code remains in charge of rights, approvals, authorization and publishing. An LLM may recommend or prepare an action, but cannot grant permission or bypass the canonical workflow.
5. Free-first does not mean risk-free. Free API tiers can have lower quotas and different data-use terms. Local inference avoids per-token hosted charges but still consumes hardware, electricity, storage and engineering time.
6. No provider, router or framework is approved for installation or production by this handbook.

**Recommended direction:** preserve existing Shorts Studio provider integrations until code-level inventory and regression evidence justify change; maintain a provider-neutral adapter boundary; evaluate LiteLLM only if a measured central-routing need emerges; defer OmniRoute for production; evaluate PydanticAI for bounded typed agents; evaluate LangGraph only if durable graph state and resumable human checkpoints are truly required; treat Ollama as optional local inference, not a guaranteed zero-cost replacement.

---

## 2. Architecture: separate the layers

| Layer | Responsibility | Examples | Must not own |
|---|---|---|---|
| Model provider | Inference and model capabilities | OpenAI, Gemini, Groq, Anthropic | Content lifecycle or publishing authority |
| Local inference runtime | Runs model weights locally | Ollama | Canonical workflow state |
| Model gateway/router | Normalizes calls, routing, retries, budgets | LiteLLM, OmniRoute | Editorial policy or approval |
| Agent framework | Coordinates model/tool steps and state | PydanticAI, LangGraph | Canonical authorization decisions |
| Product workflow | Owns business process and deterministic transitions | Content OS services, Shorts Studio | Unreviewed model-directed side effects |

### Reference request path

1. Content OS service creates a typed task request with purpose, sensitivity, allowed tools, budget and deadline.
2. Policy layer selects an allowed provider/model profile.
3. Adapter or optional gateway translates the request into provider API format.
4. Provider returns output and usage metadata.
5. Application validates output against schema and quality rules.
6. Deterministic policy evaluates any proposed action and required human approval.
7. Workflow records result, provider/model/version, usage, timestamps and provenance.
8. Retries/fallbacks are bounded and idempotent; they must not duplicate side effects.

### Required invariants

- Provider keys remain in a secrets boundary, never in prompts or logs.
- Every call has a correlation ID and stable application task/run identity.
- Provider/model IDs and prompt/schema versions are recorded.
- Model output is untrusted until validated.
- Tool access is allowlisted per task and least-privilege.
- Timeout, quota error, malformed output or unavailable provider fails closed for privileged actions.
- Fallback must not silently weaken quality, safety or policy constraints.
- Gateway logs never become the business system of record.
- Authoritative shared state remains the P0-approved relational database; do not introduce SQLite as a competing authoritative store.

---

## 3. Provider comparison

### 3.1 OpenAI API

**What it is:** Hosted model inference and related API capabilities. The API is distinct from a ChatGPT subscription; ChatGPT plan access does not imply free API credits.

**Potential fit:** Structured extraction, script analysis, classification, research synthesis and selected high-quality reasoning tasks.

**Cost:** Usage-based and model/feature dependent. Input, output, cached tokens, tools, search, audio, image and hosted execution may have separate charges. The live official pricing page is the source of truth.

**Data handling:** OpenAI states API data is not used to train or improve models unless the customer opts in. Abuse-monitoring logs may contain customer content and are generally retained up to 30 days, subject to exceptions. Some API features store application state. This is not equivalent to “nothing is retained.”

**Controls:** Server-side keys, project budgets, usage alerts, feature-specific retention review and data minimization.

**Disposition:** Candidate provider; no default model selected.

### 3.2 Google Gemini Developer API

**What it is:** Hosted Gemini API with model-dependent multimodal, long-context, batch and grounding capabilities.

**Potential fit:** Long-context source analysis, multimodal document/video/image understanding, summarization and batchable research tasks.

**Cost and free-tier distinction:** Google documents free access for selected models and paid tiers with higher limits and different data-use terms. Current pricing documentation says free-tier content may be used to improve products, while paid-tier content is not used for that purpose. Model availability and prices change; verify the live pricing page before budgeting.

**Rate limits:** Depend on project usage tier and model. RPM/TPM and other caps may apply. A 429 can indicate a rate or quota limit, not a transient outage. Use bounded exponential backoff and honor reset information.

**Logging/data handling:** Logging defaults and controls are feature- and project-dependent. Documentation describes API logs, retention settings and optional contribution of datasets/feedback. Do not assume paid tier means all logs are disabled; configure and verify project settings.

**Disposition:** Strong evaluation candidate for multimodal and long-context tasks. Do not send sensitive or proprietary material through a free tier without explicit data-use review.

### 3.3 Groq

**What it is:** Hosted inference platform focused on fast inference for supported models. It is not a model family.

**Potential fit:** Latency-sensitive classification, extraction, draft transformations and other tasks where a supported model meets quality requirements.

**Cost:** Model-specific token or modality pricing. Groq publishes model prices and developer-plan limits; take a dated snapshot during evaluation.

**Rate limits:** Organization-level RPM, RPD, TPM, TPD and modality-specific limits. The first exhausted limit controls throughput. Build bounded queueing, backoff and usage telemetry.

**Risks:** Preview models are evaluation-only and may be discontinued. Do not use preview model IDs in production-critical contracts.

**Disposition:** Candidate for fast, bounded tasks; not a universal default.

### 3.4 Anthropic Claude API

**What it is:** Hosted Claude API with model-dependent reasoning, tool-use, long-context and batch capabilities.

**Potential fit:** Complex editorial analysis, long-form source synthesis, code/repository review and multi-step knowledge work where measured quality justifies cost.

**Cost:** Per-model input/output pricing with additional pricing for caching, batch, tools, fast mode and some data-residency choices. Quote exact model ID and date in every benchmark.

**Data handling:** Anthropic states retained data is not used for model training without express permission and documents feature-specific retention and zero-data-retention eligibility. ZDR is not universal across every feature/model; check the exact API feature and model.

**Risks:** Consumer subscription does not include API usage. API billing is separate; review prepaid credits, budget controls and feature retention.

**Disposition:** Candidate for high-value reasoning tasks; compare with other providers using identical prompts and blind scoring.

### 3.5 Ollama

**What it is:** Runtime and API for running supported open-weight models locally, with compatibility surfaces for common API clients. Ollama also documents hosted/cloud access; local and cloud modes must not be conflated.

**Potential fit:** Offline experimentation, local classification/extraction, privacy-sensitive prototyping and repeatable development fixtures—if quality and hardware capacity are sufficient.

**Cost:** Local inference may avoid a per-token hosted bill, but is not economically free. Hardware, RAM/VRAM, disk, electricity, cooling, downloads, setup and maintenance are real costs. Model weights have their own licenses and restrictions.

**Data handling:** A truly local request to a local server can remain on the machine/network boundary. Confirm endpoint and model mode; cloud access requires credentials and sends requests to the hosted service.

**Risks:** Quality, context limits, throughput, memory pressure and quantization artifacts vary. Pin model tags/digests, benchmark, isolate service and do not expose an unauthenticated local API to untrusted networks.

**Disposition:** Optional local runtime for experiments and specific tasks, not a blanket hosted-provider replacement.

### 3.6 OmniRoute

**What it is:** Open-source unified AI proxy/router. Its upstream repository describes a single endpoint with multi-provider routing and automatic fallback; its lineage includes 9router and CLIProxyAPI.

**Potential fit:** Local developer experimentation with multiple model/provider endpoints and compatibility layers.

**Important distinction:** A proxy/router is not an agent framework, workflow engine or security boundary by itself.

**Risks/controls:** Before production consideration, inspect pinned release, license, dependencies, authentication, admin surface, credential storage, log redaction, network exposure, update cadence, fallback semantics and usage accounting. Confirm requests do not route through an unintended third party. Require local-only binding or strong authentication and network controls.

**Disposition:** DEFER for production. Optional disposable non-sensitive sandbox only after security review. No installation or activation is authorized.

### 3.7 LiteLLM

**What it is:** Open-source Python SDK and optional self-hosted proxy/gateway normalizing provider APIs, with routing, retries/fallbacks, virtual keys, budgets and cost tracking. The project describes its open-source core as MIT-licensed; enterprise features/directories may have separate licensing.

**Potential fit:** Centralized provider access across Content OS services, consistent request interface, per-service credentials/budgets, provider failover and cost observability.

**Cost:** Self-hosted open-source components may avoid a software subscription, but infrastructure and operations still cost money. Provider inference remains separately billable. Enterprise features/support are paid.

**Risks/controls:** Gateway becomes sensitive central infrastructure that can see prompts, outputs and credentials. Restrict network access, protect admin UI, use virtual keys, enforce budgets, redact logs, pin versions and test provider mappings. Review license boundaries before packaging or redistribution.

**Disposition:** Best gateway candidate for controlled evaluation if centralization need emerges. Not required for the current narrow P0 slice.

---

## 4. Provider summary matrix

| Candidate | Main strength | Free/low-cost reality | Main risk | Disposition |
|---|---|---|---|---|
| OpenAI API | Broad hosted API/tool ecosystem | Pay-as-you-go; API separate from ChatGPT plan | Feature-specific cost/retention | Evaluate |
| Gemini API | Multimodal and long-context options | Selected free models; free-tier data terms differ | Data use and changing quotas | Evaluate |
| Groq | Fast hosted inference | Developer limits; model-specific pricing | Catalogue/preview lifecycle | Evaluate |
| Anthropic API | Reasoning and tool use | API separately billed | Premium cost and feature retention | Evaluate |
| Ollama | Local model runtime | No hosted token charge for local inference | Hardware and model-license costs | Optional local evaluation |
| OmniRoute | Multi-provider proxy | Open-source project; operations still cost | Security/maintenance boundary | Defer |
| LiteLLM | Provider abstraction/gateway | Self-hosted OSS; provider charges remain | Central gateway becomes critical | Evaluate if needed |

---

## 5. Routing strategy: choose by task

Create named task profiles rather than allowing arbitrary model selection.

| Task profile | Candidate capability | Required controls |
|---|---|---|
| Cheap classification | Small/fast model | Strict schema, confidence threshold, sample audit |
| Structured extraction | Reliable schema output | Validation, bounded retry, reject malformed result |
| Research synthesis | Strong reasoning and source context | Evidence references and claim/source checks |
| Script development | Editorial quality/style adherence | Rubric, source traceability, human review |
| Image/video understanding | Multimodal input | Rights review, supported formats, privacy controls |
| Code/repository analysis | Strong code reasoning | Read-only access by default, patch approval |
| Local/private prototype | Local model | Hardware benchmark and egress verification |
| Critical decision support | Strongest validated model | Independent verification; model never authorizes action |

### Routing policy requirements

- Allowlist task profile to provider/model mapping.
- Version mappings; do not silently follow moving “latest” aliases in production.
- Define primary and fallback only after equivalent-quality testing.
- Never fall back from a high-assurance model to a weaker one for privileged tasks.
- Enforce per-task token, time and monetary ceilings.
- Record provider, model ID, API version, prompt/schema version, usage, latency, error class and fallback reason.
- Retry only transient failures; do not retry policy denials or deterministic schema failures indefinitely.
- Use provider idempotency keys where supported and application-level deduplication for retries.
- Keep provider-specific details inside adapters, not domain entities.

---

## 6. Agent frameworks: PydanticAI vs LangGraph

### 6.1 PydanticAI

**What it is:** Python agent framework oriented around typed inputs/outputs, dependency injection, model abstraction and tool integration. It supports MCP client connections over local stdio and remote transports.

**Potential fit:** Bounded agents for evidence extraction, metadata normalization, editorial checklist generation, asset briefs and read-only research assistance.

**Strengths:** Python-native development, Pydantic schemas, explicit dependencies and a comparatively direct programming model.

**Limitations:** Does not automatically provide durable business workflow state, production authorization, safe tool permissions or auditable publishing. Those remain application responsibilities.

**Disposition:** ADOPT FOR EVALUATION as a lightweight agent candidate. No production adoption decision.

### 6.2 LangGraph

**What it is:** Graph-based orchestration runtime for stateful agent workflows, with graph execution, checkpointing and dynamic interrupts for human-in-the-loop patterns.

**Potential fit:** Long-running workflows with branching, resumability, explicit review checkpoints and recovery after interruption—if the project needs graph orchestration beyond its existing workflow engine and Content OS state machine.

**Strengths:** Explicit graph topology, checkpointed state, resumable execution and human interrupts. Documentation requires a persistent checkpointer and stable thread ID for durable pause/resume.

**Limitations:** Additional conceptual and operational complexity. Checkpoint state is not automatically canonical Content OS state. Graph thread IDs must link to, not replace, canonical workflow/execution IDs.

**Disposition:** ADOPT FOR EVALUATION as an alternative for complex stateful workflows. Do not adopt alongside PydanticAI by default.

### 6.3 Comparison

| Dimension | PydanticAI | LangGraph |
|---|---|---|
| Primary abstraction | Typed Python agent | Stateful graph workflow |
| Best fit | Bounded agent tasks | Branching, resumable flows |
| Typed outputs | Core strength via Pydantic | Application schemas |
| Human review | Application/tool pattern | First-class interrupt pattern |
| Durable state | Must be designed with app persistence | Checkpointer-based graph state |
| Complexity | Lower for simple agents | Higher; justified by graph needs |
| MCP | MCP client support | Depends on chosen integrations |
| Main risk | Tool boundary still needs policy | Graph state mistaken for business truth |

### Framework boundary rule

Neither framework may write directly to canonical tables outside approved service interfaces, mark rights cleared, create/alter approvals, grant publishing authorization, bypass deterministic quality gates, publish/distribute content or use broad filesystem/shell/browser/credential access by default.

---

## 7. Fit with NEXTDECODE and Shorts Studio

Shorts Studio already contains provider references and integration points across research, script, voice, visuals, rendering, review and publishing. References are not proof that every provider is active, configured, current or production-ready.

Relevant code areas from the existing baseline inventory:
- Research: app/research/desk.py, topics.py, trends.py, selector.py
- Script: app/script/short.py, studio.py, pipeline.py
- Voice: app/voice/provider.py, text_prep.py
- Visuals: app/visuals/motion_director.py, chain.py, storyboard.py
- Render/QA: app/render/assembly.py, subtitles.py, audio_diagnostics.py
- Review/approval: review_bundle.py, approve_review.py, approval_integrity.py
- Publishing: app/publish/ and root publishing scripts

### Proposed integration boundary (design only)

Content OS task service → model policy/profile → provider adapter → provider or optional gateway → schema validation → evidence/quality evaluation → canonical workflow service.

- Specialist pipeline remains responsible for production-specific behavior.
- Content OS owns shared task identity, authorization, durable workflow state and cross-module contracts.
- Model providers are replaceable infrastructure.
- Agent frameworks are optional execution helpers, not new systems of record.
- Human approval remains explicit and bound to the exact artifact/version/hash and applicable policy.
- Publishing remains blocked unless the existing approved authorization chain is satisfied.

### P0 compatibility

This volume does not expand P0-A. No Control Center build, broad agent platform, new gateway or provider migration is implied. P0-A remains the narrow vertical slice governed by accepted contracts and decisions. Any future integration requires a scoped work package, dependencies and acceptance criteria.

---

## 8. Security, privacy and reliability checklist

1. Data classification: public, internal, confidential, personal and rights-restricted.
2. Provider terms: processor/subprocessor, region, retention, training use, deletion path and feature-specific exceptions.
3. Secrets: outside source control; scoped, rotated and revoked; never logged.
4. Network: restrict gateway and Ollama interfaces; no unauthenticated public exposure.
5. Tool permissions: task-scoped allowlists and read-only defaults.
6. Prompt injection: treat retrieved pages, documents, source code and tool output as untrusted data.
7. Output validation: schemas, citations, URLs, asset references and policy-sensitive fields.
8. Budget controls: per-project/task/provider limits and alerts.
9. Reliability: timeouts, bounded retries, circuit breakers, backpressure and explicit degraded mode.
10. Observability: correlation IDs, model/version, latency, usage, errors, fallback and evaluation result.
11. Auditability: decision provenance in canonical application records, not only gateway logs.
12. Recovery: interrupted runs, duplicate messages, retries, provider outage and human rejection.
13. Supply chain: pinned versions, license review, dependency scan and update ownership.
14. Human control: no model/agent approves rights, authorizes distribution or publishes autonomously.

---

## 9. Free-first cost model

| Cost bucket | Example | Can it be zero? |
|---|---|---|
| Software license | OSS framework/gateway | Sometimes |
| Model inference | Hosted tokens/audio/image | Sometimes within limited tiers; usually not at scale |
| Infrastructure | VM, database, storage, GPU | Existing local hardware still has operating cost |
| Operations | Monitoring, backups, upgrades, security | Consumes time at minimum |
| Engineering | Integration, tests, incident response | No |

### Budget policy proposal

- Start with existing provider access and current code; add no subscriptions by default.
- Use free tiers only for non-sensitive evaluation after terms review.
- Set a hard spend ceiling before paid API tests.
- Record actual token usage and task success, not only price per million tokens.
- Compare cost per accepted output, including retries, failed generations and human correction.
- Batch asynchronous tasks when provider pricing supports discounts.
- Use local inference only when hardware and quality measurements justify it.
- Never treat free-tier quota as a production availability commitment.

---

## 10. Evaluation plan and acceptance gates

### Stage A — Baseline, no installation

Inventory actual provider calls, model IDs, environment-variable names only, and error/fallback handling. Do not read or print secret values. Identify duplicated clients and inconsistent configuration.

**Exit:** Current-state map reviewed; unknowns and contradictions listed.

### Stage B — Offline benchmark design

Use synthetic or approved non-sensitive samples:
- 20 research extraction cases;
- 20 script quality cases;
- 20 metadata/schema cases;
- 10 visual brief cases;
- 10 adversarial/prompt-injection cases.

Score correctness, evidence fidelity, schema validity, latency, cost and human correction time. Blind comparison where practical.

**Exit:** Reproducible benchmark, rubric, baseline and failure taxonomy.

### Stage C — Provider evaluation

Run identical workload samples through a small candidate set. Compare task success, schema failure rate, p50/p95 latency, cost per accepted result, retry/fallback rate, rate-limit behavior, data terms and operational burden.

**Exit:** Evidence-backed recommendation per task profile, not one global winner.

### Stage D — Gateway/framework evaluation (only if justified)

- LiteLLM: provider mapping, virtual keys, budget enforcement, redaction, failover and recovery.
- OmniRoute: security review before sandbox experiment; verify release/license and credential/log behavior.
- PydanticAI: prototype one typed, read-only task.
- LangGraph: prototype only a workflow requiring durable pause/resume and human interruption.

**Exit:** Measured benefit over current architecture and no policy/contract violations.

### Stage E — Approval before implementation

A work package must name exact components/versions, owner, permitted tools, contract changes, data classification, threat model, cost ceiling, tests, rollback, acceptance evidence and explicit approval required for installation/code changes/provider activation.

---

## 11. Open decisions

| ID | Decision | Recommendation | Status |
|---|---|---|---|
| AI-01 | Default provider | No global default; task-specific profiles | Proposed |
| AI-02 | Gemini free-tier use | Non-sensitive evaluation only after terms review | Proposed |
| AI-03 | Local inference | Optional Ollama evaluation; benchmark hardware first | Proposed |
| AI-04 | Gateway | LiteLLM only if central-routing need is demonstrated | Proposed |
| AI-05 | OmniRoute | Defer production; sandbox only after security review | Proposed |
| AI-06 | Agent framework | Prototype PydanticAI for one bounded task | Proposed |
| AI-07 | Graph orchestration | LangGraph only if resumability/branching need is evidenced | Proposed |
| AI-08 | Provider fallback | Explicit task-level policy; no silent quality downgrade | Proposed |
| AI-09 | Data retention | Provider/feature-specific review before real data | Required gate |
| AI-10 | Production enablement | Separate scoped owner approval | Not authorized |

No owner decision is implied by this research draft.

---

## 12. Hands-on learning sequence

Exercises should use synthetic/non-sensitive data unless separately approved.

1. Provider API basics: one authorized request; record model ID, latency and usage.
2. Structured output: request a small JSON object, validate with Pydantic, test malformed output.
3. Provider adapter: local throwaway interface with fake provider; add real provider only after approval; test timeout/error normalization.
4. Cost accounting: estimate cost from usage and compare with billing.
5. Ollama local benchmark: if runtime is already available and authorized, compare one small model with hosted inference.
6. PydanticAI prototype: read-only extraction agent with fixed tool allowlist and typed result.
7. LangGraph prototype: pause a toy graph for human input and resume from persistent checkpointer.
8. Gateway comparison: direct SDK calls vs LiteLLM only after a real multi-provider requirement exists.

Each exercise should produce an evidence note: environment/version, sample, expected/observed result, limitations and external cost.

---

## 13. Research evidence and source register

Official sources checked on 2026-11-04. Prices, model catalogues, limits and policies are volatile; re-check before procurement or implementation.

| Topic | Official source |
|---|---|
| OpenAI API pricing | https://developers.openai.com/api/docs/pricing |
| OpenAI API data controls | https://developers.openai.com/api/docs/guides/your-data |
| Gemini API pricing | https://ai.google.dev/gemini-api/docs/pricing |
| Gemini API rate limits | https://ai.google.dev/gemini-api/docs/rate-limits |
| Gemini API logging/data sharing | https://ai.google.dev/gemini-api/docs/logs-policy |
| Groq supported models/pricing/limits | https://console.groq.com/docs/models |
| Groq rate limits | https://console.groq.com/docs/rate-limits |
| Anthropic API pricing | https://platform.claude.com/docs/en/about-claude/pricing |
| Anthropic API data retention | https://platform.claude.com/docs/en/manage-claude/api-and-data-retention |
| Ollama API introduction | https://github.com/ollama/ollama/blob/main/docs/api/introduction.mdx |
| OmniRoute upstream repository | https://github.com/artzy/OmniRoute |
| LiteLLM documentation | https://docs.litellm.ai/docs/ |
| LiteLLM licensing/product boundaries | https://www.litellm.ai/about |
| PydanticAI MCP client | https://pydantic.dev/docs/ai/mcp/client/ |
| PydanticAI MCP overview | https://pydantic.dev/docs/ai/mcp/overview/ |
| LangGraph persistence | https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/persistence.mdx |
| LangGraph interrupts | https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/interrupts.mdx |

### Evidence limitations

- Documentation-based first-pass comparison, not a live performance benchmark.
- No API credentials used and no provider requests made.
- No provider account quotas or billing configuration inspected.
- No full license audit of transitive dependencies.
- No security audit, penetration test or local installation.
- Model quality must be validated against NEXTDECODE's own evaluation set.
- Later cost decisions must quote model ID, date, currency, region and modality.

---

## 14. Completion and status

| Work area | Status | Evidence / next action |
|---|---|---|
| Architecture separation | DOCUMENTED | Provider, gateway, agent and workflow responsibilities separated |
| Provider comparison | DOCUMENTED — first pass | Official documentation reviewed; re-check at procurement |
| Free/paid and data-use review | DOCUMENTED — first pass | Terms differ by provider, tier and feature |
| Routing policy | DOCUMENTED | Task profiles, bounded retries and fallback rules |
| Agent framework comparison | DOCUMENTED | PydanticAI vs LangGraph |
| NEXTDECODE integration fit | DOCUMENTED | Specialist engine preserved; P0 scope unchanged |
| Security/privacy checklist | DOCUMENTED | Implementation gates defined |
| Benchmark | NOT STARTED | Requires approved synthetic evaluation harness |
| Provider implementation | NOT AUTHORIZED | No code changes or provider activation |
| Gateway installation | NOT AUTHORIZED | No installation |
| Agent framework installation | NOT AUTHORIZED | No installation |
| Tests | NOT RUN | Documentation/research task only |
| Production verification | NOT PERFORMED | No live calls or deployment |

**Final status:** Volume 02 research draft documented. It is not an approved technology selection, implementation specification or production-readiness claim.
