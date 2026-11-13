# NEXTDECODE Core Stack Evaluation — Agent Handoff Pack

**Document ID:** ND-INT-HANDOFF-001  
**Version:** 0.1.0-draft  
**Date:** 2026-11-13  
**Status:** PROPOSED TASK ASSIGNMENTS — owner dispatches agents manually; no agent dispatch or implementation authorization is implied  
**Parent:** ND-INT-EVAL-002 — Core Stack and Future-Extension Fit Scorecard

## 1. Purpose

Obtain independent, evidence-backed reviews of the proposed NEXTDECODE core stack and future-extension strategy. The objective is to validate the best fit for current requirements while keeping future options open without introducing unnecessary infrastructure.

Read the parent scorecard first. It is a preliminary recommendation, not a frozen architecture decision.

## 2. Shared context

- Existing repository: `/home/demon/shorts_studio`.
- Existing Shorts Studio remains the specialist production engine.
- Existing FastAPI API and Python packages are part of the current implementation.
- P0 accepted contracts and WP1–WP6 ownership remain authoritative.
- P1 is draft; broad Control Center implementation requires P0 closure/readiness and formal P1 authorization.
- Preferred frontend candidate for comparison: React + TypeScript + Vite modular SPA.
- Preferred UI candidate for comparison: Tailwind + shadcn/ui; Mantine is a strong alternative.
- Local autonomy runtime has its own PostgreSQL-backed store; its README explicitly says this is not the canonical P0 cloud control plane. SQLite remains a development/test adapter and preserved legacy source.
- Local-first, free-first, target spend ₹0. Human approval before protected actions; no public publishing by default.
- Current static UI concept is in `ui-prototype/`; it is sample-data-only and has no API integration.

## 3. Global rules for every assignment

1. Preserve existing architecture, P0/P1 decisions, canonical contracts and all current repository state.
2. Do not modify production source, canonical contracts, schema, migrations, API behavior or configuration.
3. Do not install/update dependencies, provision services, run live provider probes, access account dashboards or consume paid quotas.
4. Do not read secret values in `.env`, `youtube_token.json`, provider credentials or external account tokens. You may inspect variable names in `.env.example`.
5. Do not commit, push, reset, stash, clean, delete or overwrite existing work.
6. Do not dispatch additional agents or claim that another agent has completed work.
7. Kilo is excluded and must not be used.
8. No live upload, publishing, deployment, account change or external side effect.
9. Separate VERIFIED FACT, SOURCE-DOCUMENTED CLAIM, INFERENCE, RECOMMENDATION and UNKNOWN.
10. Cite exact repository paths/line ranges and official vendor documentation with date checked.
11. Any prototype code must be isolated under a new agent-specific directory inside `ui-prototype/variants/<agent-name>/`; do not change `ui-prototype/index.html` or project root.
12. Return unresolved owner decisions; do not choose or amend canonical decisions.

## 4. Assignment A — Architecture and P0 compatibility

**Lead:** OpenCode  
**Reviewers:** Hermes (cross-document reconciliation), DeepSeek (independent challenge), Copilot (testability/regression implications)  
**Mode:** READ-ONLY

### Prompt

Review the NEXTDECODE proposed core stack against the actual repository and accepted P0/P1 architecture.

Inspect:
- `docs/nextdecode-workspace/01_PRODUCT_AND_ARCHITECTURE/03_INTEGRATION_AND_RESEARCH/00_TECHNOLOGY_INTEGRATION_OPEN_SOURCE_PROGRAMME_INDEX.md`
- `docs/nextdecode-workspace/01_PRODUCT_AND_ARCHITECTURE/03_INTEGRATION_AND_RESEARCH/01_EXISTING_TECHNOLOGY_AND_INTEGRATION_BASELINE_0.1.md`
- `docs/nextdecode-workspace/08_P1_PRODUCT_EXPANSION/01_P1_PLANNING_PACKAGE/04_TECHNICAL_DESIGN/06_TECHNICAL_ARCHITECTURE.md`
- P0 accepted architecture decisions, canonical contract pack, WP1–WP6 specifications and current owner-decision matrix.
- Existing API, autonomy, provider and render package boundaries.

Evaluate the proposed modular React SPA + existing FastAPI + separate workers direction. Identify architecture conflicts, duplicated responsibilities, missing boundaries, premature complexity and future extension points.

Specifically answer:
1. Does this direction preserve the accepted modular architecture and domain ownership?
2. What belongs in the control plane, API process, worker runtime, specialist studio and provider adapter?
3. Which current components can be reused without redesign?
4. Which apparent technology choices are blocked by unresolved P0 decisions?
5. What should be core now, optional later or explicitly deferred?
6. What evidence would change the recommendation?

Deliver:
- one-page verdict;
- component/boundary diagram;
- requirement-to-component-to-contract traceability table;
- incompatibility and risk register;
- alternative architecture comparison using the shared scorecard;
- list of owner decisions that must remain open.

Do not edit any file or select a technology on behalf of the owner.

## 5. Assignment B — UI/UX and modular SPA prototype comparison

**Lead:** Antigravity  
**Implementation support:** Qoder  
**Reviewers:** Copilot (accessibility/regression), DeepSeek (product/UX critique)  
**Mode:** ISOLATED PROTOTYPE ONLY

### Prompt

Evaluate the Control Center visual direction and the preferred React + TypeScript + Vite modular SPA approach. Use the existing `ui-prototype/index.html` as a reference, not as a production baseline.

Design a second, clearly distinct prototype variant under:
`ui-prototype/variants/antigravity/` or `ui-prototype/variants/qoder/`.

Prototype scope:
- responsive application shell and navigation;
- Overview dashboard with sample-only metrics;
- Projects and Workflows;
- Research and Studio;
- Review & Approvals;
- Publishing (display-only; never execute);
- Analytics, Operations and Settings;
- realistic dense tables, status states, empty/loading/error states and clear blocked reasons;
- accessible keyboard navigation, visible focus, semantic controls and responsive behavior.

Constraints:
- Use sample data only.
- No backend/API connection, database, provider keys, real project data or external network calls.
- No generation, export, upload, publishing or authorization actions.
- Do not install dependencies or change project-root manifests.
- Keep all new files inside the agent-specific prototype directory.
- If React dependencies are unavailable, produce source-only prototype files and a precise run/build prerequisite note; do not install them.
- Do not overwrite the existing static prototype.

Compare Tailwind + shadcn/ui against Mantine. State which components are easiest to customize, which need accessibility work and whether either option creates avoidable complexity.

Deliver:
- isolated prototype source;
- screenshots or preview evidence if available;
- component inventory and route map;
- accessibility/responsive checklist;
- comparison scorecard;
- known limitations and exact commands required to preview (do not run package installs).

## 6. Assignment C — AI, API, database and secrets architecture

**Lead:** OpenCode  
**Implementation feasibility:** Qoder  
**Reviewers:** Copilot (test strategy), DeepSeek (security and data-boundary challenge)  
**Mode:** READ-ONLY

### Prompt

Inspect the current AI/provider, API, database and secrets architecture and compare it with the proposed core-stack direction.

Inspect:
- `api/main.py`;
- `app/providers/`;
- `app/autonomy/store.py` and `app/autonomy/postgres_store.py`;
- `app/autonomy/README.md`;
- `requirements.txt`, `.env.example` (names only), and relevant tests;
- P0 WP1/WP3/WP5 contracts and current P0 database/authorization decisions;
- existing AI provider/tool scorecard and live-provider evidence register.

Answer:
1. Which provider calls are direct and which pass through OmniRoute or another gateway?
2. What usage, token, cost, latency, failure and provider/model provenance is currently recorded?
3. What belongs in backend-only secrets handling versus browser-visible configuration?
4. How does the local PostgreSQL autonomy store differ from the canonical P0 shared control plane?
5. Which current API routes and auth controls exist, and what contract gaps remain?
6. When would LiteLLM, Redis, Langfuse, pgvector or a managed service be justified?
7. What tests would prove key isolation, budget enforcement, fail-closed behavior, idempotency and provider fallback safety?

Never inspect secret values or perform live provider calls. Do not modify code, schemas, environment files or dependencies.

Deliver:
- current-state component and data-flow diagram;
- provider/model inventory with confidence and verification gaps;
- token/cost/accounting gap table;
- database authority and persistence boundary analysis;
- secrets threat model;
- optional-extension trigger register;
- test and acceptance plan.

## 7. Assignment D — Workflow, workers and reliability

**Lead:** OpenCode  
**Implementation feasibility:** Qoder  
**Reviewers:** Copilot (recovery/idempotency test design), Hermes (contract traceability), DeepSeek (failure-mode challenge)  
**Mode:** READ-ONLY

### Prompt

Evaluate the existing local autonomy runtime and proposed P0 workflow/worker architecture without assuming they are the same system.

Inspect:
- `app/autonomy/README.md`;
- `app/autonomy/worker.py`, `tasks.py`, `store.py`, `postgres_store.py`, `worker_identity.py`, `worker_lifecycle.py`, `retry_policy.py`, `execution_policy.py`;
- tests for autonomy, PostgreSQL, idempotency, recovery and API lifecycle;
- P0 WP2 and WP3 specifications, canonical API/Event/Lifecycle contracts and open owner decisions.

Answer:
1. What is already implemented in the local autonomy runtime?
2. Which records and guarantees are local-runtime-only rather than canonical P0 entities?
3. What is implemented versus only specified for leases, fencing, retries, outbox/inbox, recovery and worker trust?
4. Where are the contract boundaries between local runtime, P0 control plane and Shorts Studio?
5. What gaps would make Temporal or another external orchestrator genuinely necessary?
6. What failure-injection and acceptance tests are still missing?
7. Which risks could allow duplicate execution, stale results, unknown side effects or authorization bypass?

Do not run migrations, database mutations, tests, service restarts or live jobs. Read source and existing test definitions only.

Deliver:
- current-state workflow diagram;
- implemented/specification-only/not-verified matrix;
- WP2/WP3 contract traceability;
- reliability and threat register;
- failure-injection test plan;
- recommendation on whether the existing WP2 direction is sufficient or what evidence would justify an extension.

## 8. Consolidation and decision process

Each reviewer returns its report independently. The owner/coordinator then:
1. reconciles conflicting findings against canonical source precedence;
2. verifies citations and repository evidence;
3. removes duplicate or unsupported claims;
4. updates the comparison scorecard with evidence and confidence;
5. records unresolved owner decisions separately;
6. recommends one core stack and a bounded future-extension register.

No technology becomes OWNER_APPROVED or ADOPTED from agent consensus alone. No implementation begins from this handoff pack.

## 9. Required report format

- Assignment ID and agent name.
- Date and exact commit/worktree context observed (read-only; do not change Git state).
- Scope completed / not completed.
- Executive verdict.
- Evidence table: claim, source, evidence class, confidence.
- Compatibility findings and conflicts.
- Security/governance findings.
- Cost and operational burden.
- Alternatives considered.
- Weighted score and rationale.
- Tests/acceptance evidence (distinguish proposed from executed).
- Open questions and owner decisions.
- Explicit statement of all files changed (expected: only isolated prototype files for Assignment B; none for A/C/D).

[executed on device: Anish (539ba48a-e995-44ed-96c9-ef6449713c5e)]
