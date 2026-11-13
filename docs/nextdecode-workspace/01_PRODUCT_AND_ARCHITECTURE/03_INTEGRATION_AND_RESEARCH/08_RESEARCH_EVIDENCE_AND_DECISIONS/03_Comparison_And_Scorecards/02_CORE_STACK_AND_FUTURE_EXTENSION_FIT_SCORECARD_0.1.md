# NEXTDECODE Core Stack and Future-Extension Fit Scorecard

**Document ID:** ND-INT-EVAL-002  
**Version:** 0.1.0-draft  
**Date:** 2026-11-13  
**Status:** PRELIMINARY RESEARCH / RECOMMENDATION — not an owner-approved technology decision or implementation authorization  
**Parent:** ND-INT-INDEX-001 — Technology, Tools, Integrations & Open-Source Programme  
**Scope:** NEXTDECODE Content OS and its existing Shorts Studio specialist engine

## 1. Decision principle

**Fit now. Extend later. Never over-engineer.**

Select the smallest dependable foundation that meets current requirements. Preserve explicit interfaces at points likely to change. Do not install, provision or operate optional infrastructure merely because it may be useful in a future phase.

This scorecard is subordinate to accepted P0 ADRs, canonical contracts, WP1–WP6 decisions and owner authorization. It does not amend them.

## 2. Requirements and non-negotiable boundaries

- Preserve the existing Shorts Studio as the specialist production engine; integrate it through explicit adapters.
- Keep the Content OS a modular domain architecture. Do not split into microservices without demonstrated independent scaling, ownership or isolation needs.
- Preserve P0 contracts and domain ownership. No competing schema, second IAM system or parallel workflow authority.
- PostgreSQL-compatible authoritative shared-state direction is already accepted in P0. This is not permission to provision, migrate or change schemas.
- Preserve human approval and central authorization for protected actions. Public publishing remains disabled by default.
- Local-first and free-first; target spend ₹0 unless separately approved.
- Keep provider credentials server-side. Never expose API keys, secrets or privileged capabilities to the browser.
- Keep optional providers replaceable and record provider/model/usage provenance.
- P1 broad Control Center implementation remains subject to P0 closure/readiness and formal P1 authorization.

## 3. Evaluation method

Scores below are **preliminary fit estimates**, not measured benchmarks, vendor rankings or agent performance results. Scale: 1 (poor) to 5 (strong). Scores are based on current project context and initial desk research; they require repository evidence, official-source checks and independent agent challenge.

| Criterion | Weight | Evaluation question |
|---|---:|---|
| Current requirement fit | 25% | Does it solve the actual near-term product and engineering need? |
| Existing architecture / P0 compatibility | 20% | Does it preserve accepted contracts, current modules and ownership? |
| Security and governance | 15% | Can identity, secrets, approval, audit and fail-closed controls remain authoritative? |
| Future extensibility | 15% | Can likely changes be added behind stable interfaces without redesign? |
| Maintainability | 10% | Is the stack understandable, testable and maintainable by a small team? |
| Local-first / free-first | 10% | Can the initial path run locally with controllable or zero spend? |
| Integration simplicity | 5% | Does it avoid unnecessary infrastructure and migration? |

**Hard gates override averages:** any conflict with P0 authority, unsafe protected-action boundary, exposed credentials, unbounded spend, unverified rights or unsafe retry/unknown-outcome behavior blocks adoption.

## 4. Leading core-stack direction

| Layer | Leading direction to validate | Why it fits now | What remains open |
|---|---|---|---|
| Frontend | React + TypeScript + Vite, modular SPA | One app, modular domain surfaces, straightforward local development and component reuse | Validate against actual frontend requirements and current repository state |
| UI system | Tailwind CSS + shadcn/ui | Customizable components and strong control over NEXTDECODE visual identity | Accessibility, keyboard behavior, table density and design consistency must be tested |
| Routing / server state | TanStack Router + TanStack Query | Explicit routes, URL state, caching and mutation lifecycle | Confirm fit with API contracts and error/retry semantics |
| Backend | Existing FastAPI application, modular domain boundaries | Reuses the current Python API and specialist-engine ecosystem | Reconcile API contracts and P0 control-plane ownership before integration |
| Execution | Existing P0 WP2 durable workflow/job direction; separate worker runtime where required | Keeps execution durable without placing long-running work inside request handlers | Validate current implementation against WP2/WP3 contracts; no replacement runtime selected |
| Database | P0-approved PostgreSQL-compatible system-of-record direction | Transactions and shared authoritative state align with accepted P0 direction | WP1 schema/contract closure, migrations and runtime readiness remain separate gates |
| Local runtime persistence | Existing autonomy runtime selects local PostgreSQL when DATABASE_URL is configured; SQLite remains an explicit development/test adapter and preserved legacy source | Reuses the existing PostgreSQL-backed local worker runtime | This local runtime is not the canonical P0 shared control plane or proof of WP1–WP3 acceptance; preserve that distinction and reconcile interfaces/contracts before integration |
| Artifacts | Local filesystem adapter first, behind WP4 artifact contracts | Avoids premature object-storage operations and cost | Retention, immutable versions, access and restore must follow WP4; vendor remains open |
| AI providers | Direct provider adapters behind a common internal interface | Lowest initial complexity; supports provider choice without a mandatory gateway | Provider terms, account entitlements, model IDs, budgets and data classification require verification |
| Secrets | Server-side environment for local development; approved OS/vault mechanism when needed | Keeps credentials out of frontend and source control | Select a production secret store only when deployment scope is authorized |
| Testing | pytest; Vitest + React Testing Library; Playwright | Covers backend contracts, frontend behavior and end-to-end user journeys | Define CI/runtime versions and acceptance thresholds |
| Observability | Structured, redacted logs and metrics; OpenTelemetry instrumentation candidate | Vendor-neutral telemetry without selecting a hosted platform | Align event/audit records with P0; telemetry is not the canonical audit ledger |

**Direction, not a freeze:** React + TypeScript + Vite is the preferred frontend candidate for prototype comparison. The existing FastAPI backend and P0 contracts remain authoritative. This scorecard does not authorize production frontend implementation or API/schema changes.

## 5. Preliminary option comparison

### 5.1 Application architecture

| Option | Indicative fit / 5 | Disposition | Reason |
|---|---:|---|---|
| React SPA + FastAPI modular backend + separate workers | 4.8 | LEADING CANDIDATE | Fits a modular Control Center and preserves backend/worker separation |
| React SPA + FastAPI with long jobs executed inside API requests | 3.5 | NOT PREFERRED | Couples request availability to long-running execution and weakens recovery |
| Next.js full-stack as a replacement for current backend boundaries | 3.7 | DEFER | Adds a second server-side application model without a demonstrated need |
| Microservices from the beginning | 3.0 | REJECT FOR CURRENT STAGE | Operational and contract overhead exceeds demonstrated benefit |

### 5.2 UI component approach

| Option | Indicative fit / 5 | Disposition | Reason |
|---|---:|---|---|
| Tailwind + shadcn/ui | 4.7 | LEADING CANDIDATE | Customizable, composable and suited to a distinct product identity |
| Mantine | 4.5 | STRONG ALTERNATIVE | Integrated component set may accelerate accessible product surfaces |
| Ant Design | 4.2 | ALTERNATIVE | Strong dense admin patterns; visual customization and bundle fit need validation |
| MUI | 4.0 | ALTERNATIVE | Mature ecosystem; design-system fit should be tested |

### 5.3 Workflow and persistence

| Option | Indicative fit / 5 | Disposition | Reason |
|---|---:|---|---|
| Existing P0 WP2 workflow/job foundation | 4.9 | PREFERRED BASELINE | Canonical project direction; avoid creating competing execution authority |
| Temporal as an external durable orchestrator | 4.2 | FUTURE EVALUATION ONLY | Powerful recovery/human workflows, but introduces operational and integration cost |
| Prefect / Celery / Dramatiq as a new primary workflow system | 3.5 | DEFER | No demonstrated gap that justifies replacing or duplicating WP2 |

### 5.4 AI routing and observability

| Option | Indicative fit / 5 | Disposition | Reason |
|---|---:|---|---|
| Direct provider adapters with common internal interface | 4.7 | PREFERRED INITIAL PATH | Minimal infrastructure; provider choice and provenance remain explicit |
| LiteLLM gateway | 4.3 | OPTIONAL EXTENSION | Add only when shared routing, virtual keys, budgets or multi-provider operations justify it |
| Portkey or other hosted gateway | 3.8 | DEFER | Hosted dependency and possible spend do not match the initial local-first target |
| OpenTelemetry instrumentation | 4.6 | PREFERRED TELEMETRY DIRECTION | Vendor-neutral traces/metrics/log context |
| Langfuse | 4.0 | OPTIONAL EXTENSION | Useful AI-specific tracing and usage views, but adds an operational service |

### 5.5 Artifact storage

| Option | Indicative fit / 5 | Disposition | Reason |
|---|---:|---|---|
| Local filesystem behind WP4 abstraction | 4.8 | PREFERRED INITIAL PATH | Local-first and low operational cost |
| S3-compatible object storage / Cloudflare R2 | 4.2 | FUTURE CANDIDATE | Useful when remote access, scale or transfer needs justify it |
| MinIO self-hosted | 3.8 | DEFER | Adds service operations and backup burden |
| Database BLOB storage for large media | 2.8 | NOT PREFERRED | Couples large binary lifecycle to relational database operations |

Scores are directional and must not be treated as benchmark results. Actual adoption depends on compatibility, licence, security, cost and owner review.

## 6. Future-extension register

Keep these options visible, but do not build them into the initial foundation without a demonstrated requirement.

| Extension | Trigger for reconsideration | Preserve now |
|---|---|---|
| LiteLLM or equivalent AI gateway | Multiple providers, centralized budgets, routing policies or key delegation become operationally necessary | Provider-neutral adapter and normalized usage/error records |
| Redis | Measured need for cross-process cache, rate coordination or ephemeral coordination that PostgreSQL/WP2 cannot meet | Clear cache/queue boundaries; no second source of truth |
| Temporal | WP2 cannot meet evidenced durability, orchestration or recovery requirements | Versioned workflow contracts and worker boundaries |
| S3-compatible storage / R2 | Remote artifact access, capacity, delivery or backup requirements exceed local storage | WP4 artifact abstraction, immutable IDs, checksums and metadata |
| Langfuse | AI trace review and token/cost analysis exceed current telemetry | Stable run/model/provider IDs and usage events |
| pgvector / vector database | A validated semantic-retrieval use case requires indexed embeddings at meaningful scale | Keep canonical source/evidence records independent of retrieval index |
| Multi-workspace / organization tenancy | Product requirements establish multiple independent customer workspaces | Workspace ownership and authorization boundaries in canonical contracts |
| Plugin ecosystem | Third-party extension demand and permission model are explicit | Capability registry, versioned interfaces and least-privilege tool contracts |
| Distributed workers / separate services | Independent scaling, isolation or availability is measured and justified | Worker identity, capabilities, idempotency and durable job contracts |
| Cloud / multi-region deployment | Availability, geography, compliance or collaboration requirements justify it | Environment-independent configuration, backup/restore and portable interfaces |

## 7. Architecture guardrails

1. Browser code contains no provider secrets, privileged credentials, database access or authorization authority.
2. Frontend modules call versioned backend APIs; they do not mutate another domain's records.
3. FastAPI request handlers do not perform unbounded media generation or long-running workflows synchronously.
4. Agents are bounded reasoning/tool users, not schedulers, workers or policy authorities.
5. Provider adapters normalize request, response, usage, error, timeout and provider identifiers.
6. Unknown provider outcome is reconciled before retry; do not repeat paid or external side effects blindly.
7. Usage accounting records provider, model, run, input/output usage where available, estimated/actual cost, latency and outcome. Unknown cost is not zero.
8. All protected publishing/export actions remain behind canonical authorization and human approval.
9. Telemetry, domain events and audit records remain distinct.
10. Optional infrastructure is added only after a written trigger, compatibility review, cost estimate, security review and owner authorization.

## 8. Agent review workstreams

These are **proposed role assignments and effort allocations**, not measured agent performance scores. The owner manually dispatches each prompt. No agent has been dispatched by this document.

| Workstream | Lead / reviewers | Effort allocation | Deliverable |
|---|---|---:|---|
| Architecture and P0 compatibility | OpenCode 35%; Hermes 25%; DeepSeek 25%; Copilot 15% | 100% | Contract-compatible architecture critique, dependency map, blockers and alternatives |
| UI/UX prototype comparison | Antigravity 40%; Qoder 25%; Copilot 20%; DeepSeek 15% | 100% | Competing modular SPA prototypes or prototype review, usability/accessibility scorecard |
| AI, API, database and secrets | OpenCode 35%; Qoder 25%; Copilot 20%; DeepSeek 20% | 100% | Provider/API/data boundary review, cost controls, security risks and test plan |
| Workflow, workers and reliability | OpenCode 35%; Qoder 25%; Copilot 20%; Hermes 10%; DeepSeek 10% | 100% | WP2/WP3 fit review, recovery/idempotency tests and future orchestration triggers |

### Shared agent rules

- Read-only research and isolated prototype work only unless a separate work package authorizes implementation.
- Preserve all existing source files, dirty worktree state, architecture decisions and canonical P0/P1 docs.
- No package installation, schema changes, migrations, live provider probes, credential/account changes, deployment, upload or publishing.
- Do not use Kilo; it is excluded from this programme.
- Do not claim an account entitlement, benchmark, licence clearance or test result without evidence.
- Cite official docs, exact repository paths and versions checked. Distinguish verified facts, inference and recommendation.
- Return unresolved questions; do not silently decide owner-controlled matters.

### Shared scoring rubric

| Criterion | Weight |
|---|---:|
| Correctness and evidence quality | 25% |
| Compatibility with existing architecture and P0 contracts | 20% |
| Security and governance | 20% |
| Maintainability and code quality | 15% |
| UX / operational usability | 10% |
| Cost and operational simplicity | 10% |

UI-specific scorecard: visual quality 25%; navigation/workflow usability 25%; responsive behavior 15%; accessibility 15%; component quality 10%; performance 10%.

## 9. Open questions and prerequisites

- Confirm the exact current P0/WP1–WP6 acceptance state before turning any P1 direction into implementation.
- Reconcile the existing local PostgreSQL-backed autonomy runtime and its SQLite development/test adapter with the accepted P0 PostgreSQL-compatible shared-state direction and WP1–WP3 ownership. The local autonomy package explicitly states that its PostgreSQL store is not the P0 cloud control plane; preserve this separation and verify the integration contract before any convergence.
- Verify the actual frontend baseline and whether any UI work already exists outside the isolated prototype.
- Validate the preferred UI system using working prototypes, keyboard/accessibility checks and realistic dense tables—not screenshots alone.
- Verify current official pricing, licences, model availability, account entitlements and data terms before recommending a provider for live use.
- Confirm the future storage and deployment requirements before choosing a vendor or paid service.
- Obtain explicit owner disposition before changing canonical decisions, contracts, schemas or implementation scope.

## 10. Current recommendation and status

**Preliminary recommendation:** validate a modular React + TypeScript + Vite SPA, using Tailwind + shadcn/ui as the leading UI candidate, integrated with the existing FastAPI backend and P0 workflow/persistence contracts. Keep workers separate from HTTP request handling. Retain provider-neutral adapters and local artifact storage behind canonical interfaces. Defer LiteLLM, Redis, Temporal, hosted observability, object-storage vendors and vector databases until concrete triggers are met.

**Status:** RECOMMENDED FOR COMPARATIVE VALIDATION — NOT OWNER-APPROVED, NOT ADOPTED, NOT IMPLEMENTATION-AUTHORIZED.

The next evidence step is parallel independent review and prototype comparison. Any resulting owner decision must be recorded separately in the programme's owner-decision area and reconciled with canonical P0/P1 authority.

## 11. Change log

- 0.1.0-draft — Initial core-stack fit assessment, extension register and agent review workstreams. No implementation or adoption authorized.
