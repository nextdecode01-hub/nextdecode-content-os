# NEXTDECODE Content OS

## Remaining Phases — Consolidated Master Plan

One master document covering Phases 1–6, consolidating the remaining platform design, implementation planning, integration, validation and release work.

Version 1.0  |  01 November 2026

Status: MASTER PLAN / DESIGN-TO-IMPLEMENTATION ROADMAP — NOT A CONTRACT FREEZE — NOT IMPLEMENTATION AUTHORIZATION

Purpose: replace fragmented follow-on batch documents with one coherent plan. This document is designed to guide the remaining work while preserving source gaps, owner decisions, safety boundaries and evidence requirements.

## Executive summary

The remaining NEXTDECODE Content OS work is organized into six major phases. Each phase contains workstreams, required outputs, dependencies, acceptance criteria, and explicit stop conditions. The phases are intended to be executed sequentially with controlled overlap only where interfaces are already stable.

The target is a modular, owner-operated Content OS for the NEXTDECODE brand. It uses a shared control plane, specialist creation engines, durable workflows, governed assets and human-controlled distribution. The existing Shorts Studio Python/FFmpeg pipeline remains a specialist engine and is integrated through a bounded adapter rather than replaced wholesale.

This is a plan, not proof of implementation. No repository changes, tests, migrations, agent runs, deployments, provider activations, paid spend, production generation, uploads or publishing are authorized by this document.

| Planning dimension | Current direction |
| --- | --- |
| Operating model | Single-owner Creator Mode; one brand, NEXTDECODE. |
| Cost model | Local-first and free-first; ₹0 initial spend target. Paid services require separate explicit approval. |
| Quality priority | Quality over speed; human review before critical publishing. |
| Architecture | Shared control plane plus bounded local/remote workers and specialist engines. |
| Publishing | Automatic public publishing disabled pending separate policy approval. |
| Implementation | Only after authoritative source reconciliation, owner contract freeze and separate implementation authorization. |
| Acceptance | Evidence-backed, end-to-end and independently reviewed; historical test reports are not current proof. |

## 1. Architecture baseline carried forward

### 1.1 Twelve logical modules

| # | Module | Responsibility |
| --- | --- | --- |
| 1 | Workspace & Control Center | Owner workspace, configuration, status, operational controls and approvals inbox. |
| 2 | Content Graph | Canonical content objects, relationships, versions, series and campaign structure. |
| 3 | Knowledge Management | Reusable knowledge, reference material, notes and governed retrieval. |
| 4 | Research Intelligence | Discovery, source collection, verification, evidence and claim support. |
| 5 | Brand Intelligence | Brand voice, audience, positioning, visual identity and constraints. |
| 6 | Strategy & Planning | Editorial strategy, priorities, briefs, schedule and objectives. |
| 7 | Content Quality Intelligence | Quality assessment, claim checks, rights signals and review outcomes. |
| 8 | Multiformat Creation Engine | Creation orchestration and format-specific adapters. |
| 9 | Asset Management | Asset metadata, immutable versions, storage abstraction, integrity and lineage. |
| 10 | Automation & Agent Orchestration | Durable workflows, jobs, workers, retries, assignments and audit. |
| 11 | Distribution Studio | Destination packaging and publishing adapters behind central governance. |
| 12 | Analytics & Learning | Performance data, measurement, insights and feedback into strategy. |

These are logical modules, not a requirement for twelve deployable services. Prefer a modular implementation with explicit boundaries over premature microservice decomposition.

### 1.2 Accepted architectural decisions

| Decision | Accepted outcome | Still requires detailed contract work |
| --- | --- | --- |
| ADR-001 | UUIDv7 canonical immutable IDs. | Exact field-level conventions and source wording. |
| ADR-002 | PostgreSQL-compatible relational database authoritative for shared state. | Schema, deployment and provider choice. |
| ADR-003 | DB-backed durable queue with transactional outbox/inbox initially. | Exact event schemas and operational semantics. |
| ADR-004 | Versioned HTTP/JSON contracts with schema validation. | Routes, payloads, errors and compatibility policy. |
| ADR-005 | Unique worker identity, scoped short-lived credentials and capability authorization. | Registration, trust and credential lifecycle details. |
| ADR-006 | Relational artifact metadata; binaries behind object-storage abstraction. | Provider selection and storage implementation. |
| ADR-007 | Centralized authorization; adapters cannot bypass; automatic publishing disabled pending policy. | Exact protected-action matrix. |
| ADR-008 | PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW, BLOCKED; hard blockers not bypassed by ordinary approval. | Rule catalogue and evidence schema. |
| ADR-009 | Evidence-backed rights states and use-specific enforcement. | Exact rights vocabulary and mapping. |
| ADR-010 | Separate lifecycle state machines for content, workflow, execution, review, approval, authorization and distribution. | Full transition tables. |

CF-01–CF-15 were explicitly accepted by the owner; CF-16–CF-21 accepted under standing delegation; CF-22 explicitly accepted as Option A (centralized authorization); CF-23 accepted under standing delegation; CF-24 explicitly accepted as no paid services, with provider/operational choices deferred. Do not reopen these outcomes casually. Exact original wording remains to be reconciled from the authoritative source records.

### 1.3 Cross-cutting invariants

- Every canonical entity has one authoritative owner.

- Canonical identifiers are immutable; revisions and outputs use explicit versions.

- Unknown, missing, stale, contradictory or ambiguous rights, approval or authorization never grant permission.

- Approval ≠ authorization ≠ execution ≠ confirmed external outcome.

- Hard quality, rights and policy blockers are centrally enforced.

- Workers execute bounded assignments and cannot self-expand scope or self-approve.

- Queue delivery is at-least-once; idempotency and attempt-level traceability are mandatory.

- Artifacts are integrity-checked and immutable by version; repairs create new versions.

- Review and approval are attributable and bound to an exact version and use.

- Automatic public publishing remains disabled pending separate policy approval.

- Existing Shorts Studio remains a bounded specialist Python/FFmpeg engine.

- Local-only work waits safely when the local worker is unavailable.

- No provider deployment, paid service or charge-generating workload without separate approval.

## 2. Phase map and completion sequence

| Phase | Name | Primary workstreams | Exit outcome |
| --- | --- | --- | --- |
| 1 | Core Platform | WP-1 domain, identity, persistence and canonical state. | Stable canonical domain and persistence contract with migration/recovery evidence. |
| 2 | Execution Infrastructure | WP-2 durable workflows/jobs; WP-3 worker registry and trust. | Safe, recoverable execution across eligible workers. |
| 3 | Content & Asset Infrastructure | WP-4 artifact registry, storage abstraction, transfer and lineage. | Versioned, verifiable and traceable content assets. |
| 4 | Intelligence & Governance | WP-5 quality, claims, rights, review, approval and central authorization. | Fail-closed governance for protected actions. |
| 5 | Integration & Validation | WP-6 vertical slice, compatibility, failure injection, recovery and independent QA. | Evidence-backed end-to-end acceptance to pre-distribution hold. |
| 6 | Implementation & Release | Controlled rollout, operational readiness, monitoring, rollback and release decision. | Owner-approved limited release only after all prior gates pass. |

Phases are sequential gates. Phase 6 is not a promise to deploy; deployment and external actions remain subject to explicit owner approval and provider/cost decisions.

## 3. Phase 1 — Core Platform

Objective: establish the canonical domain and persistence foundation used by every other module. This phase is WP-1 led.

### 3.1 Workstreams

- Canonical domain map: workspace, brand, content, content version, source, evidence, claim, workflow, job, attempt, worker, capability, artifact, artifact version, review, approval, authorization, distribution request and analytics observation.

- Entity ownership: identify one authoritative module for each entity and define which modules may read, reference or request changes.

- Identifier and version policy: UUIDv7 canonical IDs, immutable identity, explicit versioning and stable external correlation identifiers.

- Persistence design: PostgreSQL-compatible relational model for shared state; transactional integrity and constraints.

- State separation: distinct state machines for content, workflow, execution, review, approval, authorization and distribution.

- Migration safety: forward migration, backup/restore, rollback or compensating migration strategy, and preservation of existing data.

- Auditability: actor, timestamp, reason, correlation ID and before/after evidence for material state changes.

### 3.2 Required outputs

- Canonical entity catalogue and ownership matrix.

- Logical schema and reviewed physical schema proposal.

- Identifier, versioning and state-transition conventions.

- Data integrity constraints and index rationale.

- Migration and recovery plan with data-preservation checks.

- WP-1 contract tests and traceability to requirements.

### 3.3 Acceptance criteria

- Every canonical entity has one owner and a stable identifier strategy.

- Versioned records cannot be silently overwritten where history matters.

- Foreign-key, uniqueness, nullability and lifecycle constraints enforce core invariants.

- A failed transaction cannot leave partially committed shared state.

- Migration rehearsal preserves existing data and is repeatable in a controlled test environment.

- Backup restoration is demonstrated before any production data migration.

Stop conditions: unresolved entity ownership; destructive migration risk; missing backup/restore evidence; incompatible source contracts; or a proposal that requires paid infrastructure without approval.

## 4. Phase 2 — Execution Infrastructure

Objective: create durable, observable execution with trusted workers. This phase combines WP-2 and WP-3 because job orchestration and worker identity form one operational boundary.

### 4.1 WP-2 — Durable workflow and job execution

- Define workflow and job lifecycles, including queued, eligible, assigned, running, retry-wait, succeeded, failed, cancelled and terminal semantics as verified against authoritative sources.

- Use a DB-backed durable queue and transactional outbox/inbox initially.

- Assume at-least-once delivery; define idempotency keys and duplicate-delivery handling.

- Specify leases, heartbeats, timeouts, retry classification, backoff, cancellation and recovery.

- Persist attempt history, error classification, worker identity, timestamps and output references.

- Define scheduler fairness, priority and concurrency limits without creating uncontrolled cost.

### 4.2 WP-3 — Worker registry, identity and trust

- Give each worker a unique stable identity independent of host location.

- Separate declared, verified, available and authorized capabilities.

- Define registration, trust establishment, revocation, health and offline transitions.

- Use scoped short-lived credentials and least-privilege authorization.

- Define assignment handshake, worker acknowledgement, lease renewal and completion reporting.

- Support local worker availability and future remote workers without allowing workers to own shared state.

### 4.3 Required outputs

- Workflow/job state model and transition table.

- Queue, outbox/inbox and idempotency contract.

- Retry, lease, timeout, cancellation and crash-recovery policy.

- Worker identity/trust/capability model.

- Credential scope and revocation design.

- Assignment and completion envelope schemas.

- Operational metrics and trace correlation specification.

### 4.4 Acceptance criteria

- Duplicate message delivery does not duplicate protected side effects.

- Worker crash and lease expiry lead to deterministic recovery.

- Retryable and non-retryable failures are classified and handled distinctly.

- A revoked, untrusted, unavailable or under-capable worker cannot receive an assignment.

- A local-only task remains safely queued when the local worker is offline.

- Every job attempt is traceable from workflow to worker and outputs.

- No worker can independently approve itself or bypass central authorization.

Stop conditions: duplicate side effects; missing attempt history; unbounded retry loops; credential leakage; untrusted worker assignment; or silent fallback to an unauthorized worker.

## 5. Phase 3 — Content & Asset Infrastructure

Objective: make all production outputs and reusable assets identifiable, versioned, integrity-checked and traceable. This phase is WP-4 led.

### 5.1 Workstreams

- Separate artifact metadata in the relational store from binary storage behind a provider-neutral abstraction.

- Define artifact identity, immutable artifact versions, media type, size, checksum, provenance, owner, retention and lineage.

- Define storage interface operations: create, read, stream, verify, copy/transfer, quarantine and delete under policy.

- Support resumable transfer and integrity verification for large media assets.

- Treat regenerated or repaired files as new versions; never silently overwrite approved or historical artifacts.

- Connect specialist engines through input/output manifests and explicit artifact references.

- Define retention, deletion, legal hold and rights-related lifecycle controls.

### 5.2 Required outputs

- Artifact and artifact-version data model.

- Storage abstraction contract and provider-neutral adapter interface.

- Checksum and integrity-verification policy.

- Transfer/resume and quarantine workflows.

- Lineage/provenance and retention rules.

- Specialist engine input/output manifest contract.

### 5.3 Acceptance criteria

- Every registered artifact version has verifiable integrity metadata.

- A corrupted or incomplete transfer is detected and cannot be treated as valid.

- Resume/retry does not produce duplicate or ambiguous final artifacts.

- Version history and lineage remain intact after regeneration.

- Quarantined artifacts cannot enter an approved production/distribution path.

- Storage provider changes do not alter canonical artifact identity or metadata contracts.

Provider-neutral design does not authorize selection or activation of a paid storage provider. Start with local/free-compatible options only where separately approved.

## 6. Phase 4 — Intelligence & Governance

Objective: make content quality, evidence, rights and protected actions enforceable through one central policy boundary. This phase is WP-5 led.

### 6.1 Workstreams

- Define evidence-backed claim records and links between claims, sources, content versions and review findings.

- Define quality assessment rules and canonical outcomes: PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW and BLOCKED.

- Distinguish warnings from hard blockers; ordinary approval cannot override hard blockers.

- Define rights evidence and use-specific permission checks for each asset/content version, destination and intended use.

- Bind review and approval to an exact immutable version and a defined use.

- Keep approval separate from central authorization; re-evaluate authorization immediately before a protected action.

- Define protected-action matrix for upload, scheduling, publishing, deletion, account changes and other external side effects.

- Keep automatic public publishing disabled pending separate policy approval.

### 6.2 Required outputs

- Quality rule catalogue and evidence schema.

- Claims/evidence traceability model.

- Rights vocabulary, evidence requirements and use-specific decision table.

- Review and approval record schema with exact-version binding.

- Central authorization policy and protected-action matrix.

- Fail-closed test suite and audit-event specification.

### 6.3 Acceptance criteria

- Missing, unknown, stale, conflicting or ambiguous rights never grant permission.

- Unsupported claims are surfaced according to the approved policy and cannot be silently promoted.

- A hard blocker prevents protected action regardless of ordinary approval.

- Approval for one version or use does not authorize another version or use.

- Authorization is checked at the action boundary, not only when work is queued.

- Distribution adapters cannot bypass central authorization.

- A platform request is not reported as published until the external outcome is confirmed.

Stop conditions: any direct adapter/pipeline path bypasses governance; rights are warning-only where enforcement is required; approval is not version-bound; or an ambiguous policy state defaults to allow.

## 7. Phase 5 — Integration & Validation

Objective: prove the system works as one coherent whole under normal and failure conditions. This phase is WP-6 led and depends on frozen WP-1–WP-5 contracts.

### 7.1 Vertical slice

The first end-to-end slice should travel from a content request through research/evidence, strategy/brief, creation, review, rendering, artifact registration and a governed pre-distribution hold. It should demonstrate all shared control boundaries without requiring public publishing.

### 7.2 Integration scenarios

1. Happy path: request → research → brief → creation → review → render → artifact registration → human approval → pre-distribution hold.

1. Duplicate job delivery: same idempotency key is delivered more than once; only one intended side effect occurs.

1. Worker loss: worker disappears during execution; lease expiry and safe recovery are demonstrated.

1. Local worker unavailable: local-only assignment waits and resumes when the worker returns.

1. Artifact corruption: checksum mismatch quarantines the artifact and prevents downstream approval/use.

1. Rights unknown: asset with unknown rights is blocked from protected use.

1. Approval mismatch: approval for an earlier version cannot authorize a newer version.

1. Hard QA blocker: BLOCKED prevents protected action despite an approval record.

1. Authorization revocation: a previously eligible request is denied when authorization is revoked before action.

1. Distribution ambiguity: request accepted but external outcome unconfirmed; system reports pending/unknown, not published.

1. Crash recovery: process/database boundary failure does not lose durable job/attempt state.

1. Traceability: content, job, worker, artifact, review, approval and authorization are correlated end to end.

### 7.3 Required outputs

- Cross-package contract compatibility matrix.

- End-to-end test plan and executable test evidence.

- Failure-injection and recovery report.

- Traceability report linking requirements, contracts, tests and artifacts.

- Independent read-only QA report.

- Known-issues and residual-risk register.

### 7.4 Acceptance criteria

- The vertical slice reaches the pre-distribution hold with complete traceability.

- All hard governance gates are enforced across every reachable path.

- Failure injection proves recovery rather than relying only on happy-path tests.

- Independent QA can reproduce the evidence from a clean, documented test procedure.

- No unresolved critical/high-severity issue remains without explicit owner disposition.

- P0 is described as accepted only if all required gates and evidence are satisfied.

## 8. Phase 6 — Implementation & Release

Objective: move from validated implementation to a controlled, owner-approved release. This phase is conditional and must not begin simply because this plan exists.

### 8.1 Implementation authorization gate

Before coding begins, the owner must approve a separate implementation authorization specifying the exact work packages, repository path, branch and baseline, permitted files/operations, test commands, agent roles, budget boundary, external-action boundary and stop conditions.

### 8.2 Controlled implementation sequence

1. Confirm authoritative source set and freeze the detailed contracts.

1. Capture a non-destructive repository baseline and preservation map at the moment implementation is authorized.

1. Implement WP-1 foundation and validate schema/migration safety.

1. Implement WP-2 and WP-3 execution/worker boundaries.

1. Implement WP-4 artifact lifecycle and storage adapter.

1. Implement WP-5 governance and centralized authorization before enabling any protected external action.

1. Integrate the specialist Shorts Studio engine through the bounded adapter.

1. Run WP-6 vertical-slice, failure-injection and independent QA.

1. Prepare a release candidate with rollback, monitoring and owner review.

1. Release only the explicitly approved scope; keep public publishing disabled unless separately approved.

### 8.3 Release readiness

| Area | Minimum evidence before limited release |
| --- | --- |
| Contract | Frozen version, owner approval, source traceability and no unresolved critical ambiguity. |
| Data | Migration rehearsal, backup/restore, integrity checks and recovery procedure. |
| Security | Credential scope, revocation, worker trust, least privilege and protected-action tests. |
| Governance | Rights, quality, approval and authorization gates pass fail-closed tests. |
| Reliability | Retries, idempotency, worker loss, recovery and observability validated. |
| Operations | Runbooks, alerts, logs, cost limits, incident handling and rollback plan. |
| QA | Independent report, reproducible evidence and accepted residual-risk register. |
| Owner | Explicit release approval for the exact candidate and scope. |

A release can be limited to internal/local use or a pre-distribution workflow. Public publishing is a separate protected capability and remains disabled by default.

## 9. Cross-phase dependency map

| Dependency | Why it matters | Must be true before downstream work |
| --- | --- | --- |
| Source verification → all phases | Detailed design must match authoritative requirements and accepted decisions. | Original records and source gaps reconciled or owner-dispositioned. |
| Phase 1 → Phases 2–6 | All shared state depends on canonical entities, IDs and persistence. | WP-1 contract and migrations reviewed. |
| Phase 2 → Phases 3–5 | Jobs and workers execute asset and governance workflows. | Durable execution and worker trust boundaries stable. |
| Phase 3 → Phases 4–5 | Governance and production depend on trustworthy artifact versions and provenance. | Artifact identity, integrity and lineage stable. |
| Phase 4 → Phase 5 | Integration must prove centralized governance in every protected path. | Rights, quality, approval and authorization contract stable. |
| Phase 5 → Phase 6 | Release relies on reproducible integration and recovery evidence. | Independent QA and owner acceptance. |
| Owner freeze → implementation authorization | Design agreement and permission to modify the repository are separate decisions. | Explicit authorization recorded. |

Limited parallelism is acceptable for documentation, test design and interface review. Implementation should not race ahead of unresolved upstream contracts.

## 10. Source verification and unresolved gaps

| Gap | Current status | Required resolution |
| --- | --- | --- |
| Artifact 08 exact decision/contract wording | NOT VERIFIED in the available working set for all required wording. | Import original source; especially CF-03–CF-12, CF-15–CF-19 and CF-23. Do not reconstruct from summaries. |
| ODR master register | NOT VERIFIED as a complete authoritative register; ODR-22 grouping previously provisional. | Obtain full register and reconcile IDs, status, rationale, owner and dependencies. |
| Data dictionary | NOT VERIFIED as a complete authoritative source. | Reconcile entity/field definitions, constraints, indexes, ownership and versioning. |
| API/event/message contracts | NOT VERIFIED at field-level completeness. | Verify routes, schemas, event names, error semantics and compatibility rules. |
| Lifecycle specifications | NOT VERIFIED as complete. | Verify state names, transitions, guards, retries, cancellation and terminal semantics. |
| WP-1 to WP-6 work orders | Design candidates exist; detailed source-aligned freeze remains open. | Reconcile candidates with original requirements and owner decisions. |
| Independent QA | PENDING / UNAVAILABLE in the current record. | Obtain read-only independent QA after implementation is authorized and evidence exists. |
| Fresh runtime/repository proof | NOT ESTABLISHED by this document. | Collect only under a separately authorized, non-destructive workflow. |

A missing item in the current working set is not proof that the artifact does not exist elsewhere. Keep the status as NOT VERIFIED until located or formally dispositioned.

## 11. Repository and agent safety protocol

Historical user-provided snapshot (01 Nov 2026): project path /home/demon/shorts_studio; local main reported tracking origin/main; remote SHA 9d38f81ba4f8022d0e820b6a5e1fe2a0fc288c8c; 23 tracked modified files and 56 untracked paths; no staged changes. Captured diff-stat output was blank and is a capture limitation, not proof of no changes.

- Preserve all tracked modifications and untracked paths.

- No reset, revert, stash, clean, delete, overwrite, rename, broad-stage, commit, push, branch change or remote change without explicit approval.

- Do not repeat repository inventory checks just for reassurance; refresh only when an authorized task genuinely depends on current state.

- User/product owner is final authority for scope, freeze, implementation authorization and protected actions.

- Assistant coordinates architecture, source reconciliation, documentation and acceptance review; it cannot self-authorize implementation.

- Qoder and OpenCode operate only within explicitly assigned scopes and cannot self-expand scope or self-approve.

- Kilo is independent read-only QA and cannot modify the implementation it reviews.

Historical Phase 10 report claimed 535 passing tests; this is not fresh evidence. Historical Phase 11 reports identified unresolved storyboard gate, rights enforcement, unsupported-claim handling, direct adapter/pipeline bypass, traceability and runtime/recovery gaps. Treat these as historical findings pending current verification.

## 12. Master acceptance gates

| Gate | Required evidence | Decision |
| --- | --- | --- |
| G0 Preservation | Preservation map; no unapproved destructive changes. | May proceed to source review. |
| G1 Source integrity | Original source inventory, exact wording, provenance and conflict resolution. | May proceed to contract freeze review. |
| G2 Core platform | WP-1 ownership/schema/constraints/versioning and migration tests. | Phase 1 accepted. |
| G3 Execution | WP-2 idempotency/retry/recovery and WP-3 identity/trust/capability tests. | Phase 2 accepted. |
| G4 Assets | WP-4 immutable versions, integrity, transfer, quarantine and lineage tests. | Phase 3 accepted. |
| G5 Governance | WP-5 rights/claims/quality/approval/authorization fail-closed tests. | Phase 4 accepted. |
| G6 Integration | WP-6 end-to-end traceability, failure injection, recovery and independent QA. | Phase 5 accepted. |
| G7 Release | Operational readiness, rollback, monitoring, owner approval and exact scope. | Phase 6 limited release may be considered. |

A gate is passed only when its evidence is present, reviewable and attributable. A document describing a test is not evidence that the test passed.

## 13. Master status reporting model

Report five separate dimensions. Never collapse them into a single green status.

| Dimension | Example values / interpretation |
| --- | --- |
| Decision outcome | Accepted / Rejected / Deferred / Superseded; accepted ADR/CF outcomes remain accepted unless formally changed. |
| Design maturity | Candidate / In Review / Frozen / Superseded; current WP designs are candidates. |
| Implementation | Not Started / In Progress / Implemented / Blocked / Deferred. |
| Evidence | Missing / Historical / Partial / Current / Independently Verified. |
| QA outcome | PASS / PASS_WITH_WARNINGS / NEEDS_REVIEW / BLOCKED. |

Use exact X-12 labels from its authoritative source when that full vocabulary is available. This plan does not invent the unverified full X-12 wording.

## 14. Owner freeze and authorization checklists

### 14.1 Contract freeze checklist

- ☐ All authoritative source artifacts located, versioned and inventoried.

- ☐ Exact CF wording and ODR master register reconciled; no wording reconstructed from summaries.

- ☐ Material conflicts and omissions explicitly dispositioned by owner.

- ☐ WP-1–WP-6 boundaries and canonical state ownership consistent.

- ☐ Entity, identifier, version, persistence and lifecycle contracts complete.

- ☐ API, event, job, worker, artifact, rights, approval and authorization contracts complete.

- ☐ Error, retry, timeout, cancellation, idempotency and recovery semantics explicit.

- ☐ Security, credential, capability and protected-action boundaries explicit.

- ☐ Acceptance criteria trace to every P0 requirement.

- ☐ Repository preservation and agent boundaries acknowledged.

- ☐ Owner explicitly approves the exact consolidated contract version.

Current freeze recommendation: NOT READY until source verification and owner review are complete.

Owner approval / signature: ____________________________________    Date: __________________

Approved contract version and hash: _______________________________________________________

### 14.2 Separate implementation authorization — template only

| Field | Required owner authorization detail |
| --- | --- |
| Work packages | Exact WP IDs and deliverables permitted. |
| Repository baseline | Exact repository path, branch and commit; preservation constraints. |
| Allowed operations | Explicit file and operation allowlist; no implied destructive permission. |
| Tests/commands | Exact commands, environment, scope and resource limits. |
| Agent assignments | Named agent, task, tool access and read/write boundary. |
| Budget/provider | Default ₹0; any paid service or provider activation separately approved. |
| External actions | Production generation, upload, account actions and publishing separately authorized. |
| Stop conditions | Unexpected dirty state, source conflict, destructive risk, secret exposure, cost, policy bypass or failed tests. |
| Reporting | Diff, tests, evidence, risks, unresolved items and recovery plan. |
| Approval | Explicit owner approval, date and exact contract version. |

Implementation authorization status: NOT ACTIVE / NOT AUTHORIZED.

## 15. Final recommended execution plan

1. Complete one source-integrity pass using the original Artifact 08, ODR master register, data dictionary, API/event schemas and lifecycle specifications.

1. Reconcile and version the detailed contracts across WP-1–WP-6; maintain the accepted ADR/CF outcomes.

1. Obtain explicit owner approval to freeze the consolidated P0 contract.

1. Obtain separate implementation authorization with a bounded scope and repository preservation rules.

1. Execute Phases 1–5 in dependency order, with evidence and independent QA at each gate.

1. Consider Phase 6 only after end-to-end acceptance, operational readiness and explicit release approval.

Final disposition: REMAINING WORK CONSOLIDATED INTO ONE MASTER PLAN • DESIGN CANDIDATES NOT FROZEN • IMPLEMENTATION NOT AUTHORIZED • INDEPENDENT QA PENDING • PUBLIC PUBLISHING DISABLED BY DEFAULT

## Appendix A — prior batch material carried forward

| Earlier batch | Material retained in this master plan |
| --- | --- |
| 02 | Traceability, owner decisions, dependencies, agent protocol, risks and readiness. |
| 03 | Contract consolidation, architecture outline, source authority and owner review. |
| 04 | Source verification gaps, freeze preparation and provenance controls. |
| 05 | WP-1 domain and persistence candidate. |
| 06 | WP-2 durable workflow and job execution candidate. |
| 07 | WP-3 worker registry, identity, trust and capabilities candidate. |
| 08 | WP-4 artifact registry, storage, integrity and transfer candidate. |
| 09 | WP-5 governance, quality, rights, approval and authorization candidate. |
| 10 | WP-6 vertical-slice integration, recovery and acceptance candidate. |
| 11 | Master integration blueprint and owner freeze review. |

This document consolidates the remaining forward plan and carries the key architecture constraints forward. It does not replace original authoritative source artifacts or erase the historical batch documents.


## Source document metadata (preserved from DOCX)

- **Header:** NEXTDECODE CONTENT OS  |  REMAINING PHASES MASTER PLAN
- **Footer:** Consolidated planning document  •  Version 1.0  •  01 Nov 2026

