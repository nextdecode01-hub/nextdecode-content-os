# AGENT WORKSTREAM MATRIX

These are recommended responsibility boundaries derived from the existing project decisions. This matrix does not dispatch agents or grant write permissions.

| Workstream | Primary responsibility | Required inputs | Main output | Independence / boundary |
|---|---|---|---|---|
| Architecture & traceability | Reconcile source authority, contracts, domain ownership and dependencies | Accepted P0 baseline, ADR/CF, data dictionary, traceability matrix, Parts 1–8 | Source-of-truth map, conflict register, dependency map | Must not resolve owner-reserved decisions |
| WP1 — Domain & persistence | Canonical entities, ownership, identity/version, relational persistence boundary | WP1 0.1/0.2/0.3 candidates, data dictionary, ADR-001/002, canonical contracts | WP1 reconciled schema candidate and migration compatibility plan | Do not design queue/worker/artifact storage beyond WP1 boundary |
| WP2 — Workflow execution | Workflow/job/task/attempt semantics, durable execution design | WP2 candidate, workflow/job reconciliation, state transitions, API/event standards | Versioned workflow/job contract candidate | Blocked by unresolved X-01 where relevant |
| WP3 — Worker trust | Worker identity, capabilities, credential lifecycle, revocation | Worker trust reconciliation, WP3 boundary, Contract 10, security decisions | Worker trust contract and acceptance cases | No provider deployment or credential changes by default |
| WP4 — Artifact storage | Artifact/version/manifest identity, registration, transfer, lifecycle | Artifact reconciliation, WP4 boundary, data dictionary, legal hold/retention records | Artifact contract and provider-neutral boundary | Retention/purge owner-reserved; no physical deletion |
| WP5 — Governance & quality | QA, rights, review, approval, authorization and protected actions | ADR-007/008/009, Contract 07, policy matrix, governance reconciliation | Governance contract and fail-closed acceptance cases | Cannot authorize real publishing or external actions |
| WP6 — Integration & recovery | Vertical-slice integration, failure/recovery, evidence and release gates | WP1–WP5 accepted contracts, WP6 spec, acceptance framework | Integrated acceptance evidence and release recommendation | No release/deployment without separate authorization |
| P1 Product & frontend | P1 requirement refinement and contract-aligned UI scaffolding | P1 docs, P0-A boundary, versioned API/event contracts | Traceable UI requirements and integration plan | No broad Control Center expansion during P0-A |
| Independent QA/security | Read-only independent review after implementation | Frozen scope, code snapshot, tests, evidence and threat model | Independent findings and acceptance recommendation | Must not implement fixes in the reviewed change set |

## Existing named-agent continuity
- Qoder: Phase 11 engineering owner / sole writer for current governance-closure milestone.
- OpenCode: Phase 10 engineering/closure owner; read-only API/backend architecture review as previously scoped.
- Kilo: independent read-only QA/security acceptance after implementation.
- Copilot: focused regression-test review suggestion.
- Antigravity: targeted product/UI review suggestion.
Do not reassign or dispatch any agent without explicit authorization and a task-specific handoff.