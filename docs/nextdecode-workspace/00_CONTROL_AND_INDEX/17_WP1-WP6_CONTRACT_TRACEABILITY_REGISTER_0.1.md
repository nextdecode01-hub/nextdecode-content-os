# NEXTDECODE P0 — WP1–WP6 Contract Traceability Register

**Document ID:** NEXTDECODE-P0-WP1-WP6-TRACE-0.1  
**Version:** 0.1  
**Status:** WORKING RECONCILIATION — OWNER REVIEW REQUIRED  
**Updated:** 2026-11-04  
**Scope:** Documentation-only traceability; no contract freeze, implementation or test authorization.

## 1. Authority and reading rules

Accepted owner decisions and ADR-001–ADR-010 / CF-01–CF-24 take precedence. Governing Data Dictionary, API/Event Contract Standard and Unified Lifecycle/State Transition Standard follow. WP1–WP6 specifications are authoritative within their package scope. Reconciliation documents are subordinate clarifications. Batch and appendix material cannot override accepted decisions.

Labels in this register: **BASELINE** = accepted; **SOURCE** = explicit package requirement; **RECONCILED** = logical boundary clarified; **OPEN** = unresolved owner/security/policy decision; **NOT AUTHORIZED** = no implementation/test action.

## 2. Work-package traceability

| Package | Canonical responsibility | Governing sources | Cross-package dependency | Current finding / unresolved point |
|---|---|---|---|---|
| WP1 Domain & Persistence | Canonical domain identity, ownership, typed relationships, minimum persistence boundary | ADR-001/002; CF-01..06; Data Dictionary; WP1 v0.1/v0.2/v0.3 | WP2 consumes workflow/job persistence; WP3 worker registry; WP4 artifact metadata; WP5 governance records | WP1 v0.1 logical model includes Workflow/Task/Job/Attempt; later v0.2/v0.3 defer physical Job/Attempt ownership to WP2. Resolve logical entity visibility vs physical table ownership. Data Dictionary v1.1 is latest working CF-20/21 propagation, but formal supersedes authority remains open. |
| WP2 Workflow Execution | Durable workflow/task/job/attempt progression, scheduling eligibility, retry/idempotency, outbox/inbox, recovery | ADR-003/004; CF-07..12; Contract 10/X-01; API/Event and Lifecycle standards; WP2 candidates | WP1 persistence; WP3 worker identity/lease proof; WP4 artifacts; WP5 policy gates | WP2 owns authoritative durable execution and lease/attempt state. Vocabulary/cardinality, parent aggregation, pause/cancel, retry and state mapping remain open. |
| WP3 Worker Trust | Worker identity/registration/trust, capability verification, credentials, worker health evidence, assignment authentication and fencing evidence | ADR-005; CF-13/14; Contract 10; WP3 trust/credential reconciliation and registry boundary | WP2 owns durable job/attempt/lease progression; WP5 owns central authorization; WP4 scopes artifact access | Worker heartbeat/lease-renewal requests and trust/fencing evidence must not create a second lease authority. Exact division of lease state vs worker-side evidence, active-job revocation and isolation guarantees require owner/security review. |
| WP4 Artifact Storage | Artifact/ArtifactVersion identity and metadata, manifests, storage abstraction, integrity, transfer, quarantine and lifecycle | ADR-006; CF-15..18; Data Dictionary; Part 7; WP4 artifact and lifecycle reconciliations | WP1 typed ownership; WP2 execution provenance; WP3 worker-scoped transfer; WP5 rights/authorization; WP6 evidence | Asset ≠ Artifact ≠ ArtifactVersion. ArtifactVersion immutable; manifests pin exact versions; metadata authoritative, binary provider-neutral. Retention, legal hold, purge authority, backup deletion propagation and shared-resource disposition remain owner-reserved. |
| WP5 Governance & Rights | QA, rights assessment, review snapshot, approval decision, centralized authorization, protected-action enforcement and audit | ADR-007/008/009; CF-19..22; Contract 07; Policy Authorization Decision Matrix; WP5 reconciliations | All work packages; especially WP3 worker access, WP4 artifact use, WP6 denial tests | QA, rights, review, approval, authorization, execution and distribution outcome are distinct. Central authorization is sole authority and fail-closed. Protected-action catalogue, emergency-pause authority and in-flight external action policy remain open. |
| WP6 Integration & Acceptance | Narrow synthetic P0-A vertical slice, environment gates, failure injection, security-negative tests, evidence package and independent QA | Artifact 07 acceptance framework; API/Event and Lifecycle standards; WP6 plan and test-oracle reconciliation | Consumes accepted WP1–WP5 contracts; does not redesign them | ENV-01..14, VS-01..18 and F-01..18 are candidate traceability/test identifiers. Artifact 07 remains authoritative for acceptance IDs/criticality. Environment approval and test execution authorization are absent; all unrun tests remain NOT_RUN. |

## 3. Cross-package conflict register

| ID | Conflict / dependency | Safe reconciliation boundary | Decision owner / evidence needed |
|---|---|---|---|
| WPX-01 | WP1 logical Job/Attempt entities vs WP2 physical ownership | WP1 may reference logical relationships; WP2 owns execution state and physical job/attempt contract | WP1/WP2 owners; accepted entity map, persistence boundary and migration compatibility |
| WPX-02 | WP2 lease lifecycle vs WP3 heartbeat/fencing | WP2 authoritative lease/attempt state; WP3 authenticates worker and supplies trust/heartbeat/fencing evidence | WP2/WP3/security; transition matrix, revocation and stale-worker acceptance cases |
| WPX-03 | Data Dictionary v1.0 vs v1.1 | Preserve both; use v1.1 as latest working CF-20/21 propagation without assuming formal supersession or runtime migration | Contract owner; explicit version authority and compatibility/migration decision |
| WPX-04 | WP4 artifact identity/version vs storage locator and manifest references | Canonical relational metadata owns identity; storage locator is opaque and grants no access; manifest pins immutable versions | WP4/WP1; field-level contract, integrity and reference constraints |
| WPX-05 | WP4 deletion/retention vs cross-domain evidence | No cascade assumptions; dependency assessment and legal hold/purge authority remain owner-reserved | Owner/legal/security; retention policy, purge authority, backup propagation and evidence disposition |
| WPX-06 | WP5 authorization vs local adapter/worker execution | One central decision; exact actor/action/resource/version/destination; authorization checked at side-effect boundary | Governance/security owner; protected-action catalogue, pause authority and in-flight behavior |
| WPX-07 | WP6 test IDs/oracles vs Artifact 07 | Preserve WP6 IDs as traceability only; Artifact 07 governs authoritative acceptance IDs and criticality | Acceptance owner; completed crosswalk and approved test environment |
| WPX-08 | WP6 failure recovery vs open WP2 numeric policy | Use only explicitly approved isolated test parameters; do not infer production timeouts/retry values | WP2/acceptance owner; test-only parameter record and evidence |
| WPX-09 | WP3 trust revocation vs active job/output | Deny new protected access; no stale completion; reconcile active attempt through WP2 fencing; quarantine uncertain output | Security/governance owner; revocation timing, active work and output disposition decisions |

## 4. Acceptance and authorization status

- Phase 4 is active; this register is a working traceability baseline, not phase closure.
- No detailed contract is frozen by this register.
- No schema, enum, migration, timeout, retry, credential, provider or policy value is newly approved.
- No repository/code changes, tests, Git operations, agent dispatch, credentials, provider activation, spending, deployment or publishing are authorized.
- WP6 acceptance requires actual evidence; documentation of an oracle is not a test pass.
- Automatic public publishing remains disabled absent separate authorization.

## 5. Remaining work

1. Complete exact clause-level traceability for each WP against governing standards and Batch 17–26 sources.
2. Build the Artifact 07 ↔ WP6 test identifier and criticality crosswalk.
3. Record each open decision with alternatives, consequences, accountable owner and required evidence.
4. Produce the consolidated owner-review pack.
5. Run documentation link/path QA after all planned additions.

