# P0 Master Integration Blueprint & Owner Freeze Review

## Batch 11 — Complete Cross-Package Architecture and Integration Specification

NEXTDECODE Content OS | Version 1.1 | 01 November 2026

Status: INTEGRATION DESIGN CANDIDATE — OWNER REVIEW REQUIRED — NOT FROZEN

Purpose: define how WP-1 through WP-6 fit together as one P0 system. This is the integration-level companion to the individual work-package design documents. It defines boundaries, ownership, lifecycle interactions, contract expectations, failure behavior, acceptance coverage and the owner freeze gate.

Authority note: accepted ADR/CF outcomes are carried forward as recorded in project history. Exact original wording and some detailed source specifications remain subject to the source-verification process in Batch 12. This document must not invent missing wire-level schemas or claim source verification that has not occurred.

Non-authorization: this document does not authorize repository edits, tests, migrations, agent execution, deployment, provider activation, paid spend, production generation, uploads, account actions or publishing.

## 1. Executive architecture decision

The P0 system is a modular Content OS with one shared control plane and a set of bounded specialist capabilities. Shared workflow/control state, canonical identities, governance decisions, artifact metadata and audit evidence have central authority. Workers and specialist engines execute bounded assignments; they do not become authorities for shared state or policy.

The initial operating mode is single-owner Creator Mode for the NEXTDECODE brand. The system is local-first and free-first, with a ₹0 initial spend target. Existing Shorts Studio remains a specialist Python/FFmpeg engine integrated through an adapter. The target architecture can support a shared cloud control plane and local/remote workers later, but no cloud provider, deployment topology or paid service is selected or approved.

| Architecture dimension | P0 direction | Constraint |
| --- | --- | --- |
| Product mode | Single owner, one brand: NEXTDECODE. | Do not design P0 around enterprise multi-tenant complexity. |
| System shape | Modular architecture with explicit contracts. | Twelve logical modules do not imply twelve microservices. |
| Shared state | PostgreSQL-compatible relational store is authoritative. | No split-brain shared-state authority. |
| Execution | Durable DB-backed workflow/job execution. | At-least-once delivery; idempotency required. |
| Workers | Unique identity, trust, capability and scoped credentials. | Workers execute bounded tasks only. |
| Assets | Relational metadata plus provider-neutral binary storage abstraction. | No storage vendor activation by implication. |
| Governance | Centralized quality, rights, approval and authorization controls. | Fail closed on unknown or ambiguous permission. |
| Distribution | Destination adapters behind central authorization. | Automatic public publishing disabled. |
| Cost | Local-first/free-first; ₹0 initial spend target. | Paid spend requires separate explicit approval. |

## 2. System context and trust boundaries

| System actor / boundary | Role | Trust and authority rule |
| --- | --- | --- |
| Owner / creator | Defines brand, content intent, approvals and protected-action permissions. | Final authority for scope, freeze, implementation and external actions. |
| Control plane | Owns shared canonical state, orchestration, policy decisions and audit trail. | Authoritative source for shared state and central authorization. |
| Specialist modules | Research, strategy, creation, quality, asset, distribution and analytics capabilities. | Operate through defined contracts; no duplicate ownership of shared entities. |
| Local worker | Executes local-only tasks and heavy rendering when PC is available. | Must authenticate, be trusted and match task capability requirements. |
| Remote worker | Executes eligible remote work when explicitly enabled. | Scoped identity/credentials; no authority to self-approve or bypass policy. |
| Shorts Studio engine | Existing Python/FFmpeg rendering and production capability. | Bounded specialist engine; preserve existing capability and repository work. |
| External platform | Receives authorized distribution actions and returns outcome evidence. | A request acknowledgement is not proof of publication. |

Trust boundary principle: an input from a source, agent, worker, plugin, external platform or generated artifact is data to validate, not an instruction that can override system policy or owner decisions.

## 3. Twelve logical modules and ownership boundaries

| # | Module | Owns / produces | Must not own or bypass |
| --- | --- | --- | --- |
| 1 | Workspace & Control Center | Owner-facing configuration, status, approvals inbox and operational controls. | Independent duplicate lifecycle or authorization state. |
| 2 | Content Graph | Canonical content objects, versions, series/campaign relationships and lineage links. | Job execution, worker trust or platform authorization. |
| 3 | Knowledge Management | Reusable knowledge records, reference material and governed retrieval. | Changing source evidence without provenance. |
| 4 | Research Intelligence | Research plans, source records, verification findings and claim evidence. | Silently upgrading uncertain claims to verified facts. |
| 5 | Brand Intelligence | Brand voice, audience, positioning, visual identity and constraints. | Overriding owner-approved brand policy. |
| 6 | Strategy & Planning | Priorities, objectives, editorial plans, briefs and schedules. | Approving rights or authorizing publishing. |
| 7 | Content Quality Intelligence | Quality assessments, claims checks, rights findings and review outcomes. | Self-authorizing protected external actions. |
| 8 | Multiformat Creation Engine | Format-specific creation orchestration and specialist adapters. | Directly owning shared workflow state or bypassing governance. |
| 9 | Asset Management | Artifact metadata, immutable versions, integrity, storage references and lineage. | Treating an unverified/corrupt asset as valid. |
| 10 | Automation & Agent Orchestration | Workflow/job state, assignment, retries, worker registry and execution trace. | Making owner decisions or bypassing policy gates. |
| 11 | Distribution Studio | Destination packaging, adapter requests and external outcome records. | Direct publish without central authorization. |
| 12 | Analytics & Learning | Observed performance, attribution context, insights and feedback. | Rewriting historical source facts or approval evidence. |

These are logical ownership boundaries. A module may initially be implemented as a package or bounded context within one deployable application. Physical service separation is a later architectural decision.

## 4. P0 work-package architecture

| WP | Primary responsibility | Authoritative outputs | Consumes |
| --- | --- | --- | --- |
| WP-0 | Current-system baseline and preservation assessment. | Baseline, preservation map, known risks and source inventory. | Existing repository and dated evidence. |
| WP-1 | Canonical domain and persistence foundation. | Entity ownership, IDs, versioning, schema, constraints and migrations. | Owner decisions and domain requirements. |
| WP-2 | Durable workflows and job execution. | Workflow/job state, queue, idempotency, attempts, retry and recovery contracts. | WP-1 persistence and policy boundaries. |
| WP-3 | Worker registry, identity, trust and capabilities. | Worker identity, trust lifecycle, capability model and assignment protocol. | WP-1 identity and WP-2 scheduling. |
| WP-4 | Artifact registry, storage, integrity and transfer. | Artifact metadata, immutable versions, storage interface, transfer and lineage. | WP-1 entities and WP-2 execution. |
| WP-5 | Governance, quality, rights, approval and authorization. | Quality outcomes, claims/evidence, rights policy, approval and central authorization. | WP-1 entities and all protected workflows. |
| WP-6 | Vertical-slice integration, recovery and acceptance. | Compatibility evidence, E2E tests, failure/recovery report and acceptance record. | Frozen WP-1–WP-5 contracts. |

WP-0 is an assessment/preservation workstream. WP-1–WP-6 are the six P0 design and implementation packages. No WP design candidate is frozen merely because it has a document.

## 5. Canonical data ownership and state model

### 5.1 Accepted data architecture

- UUIDv7 canonical identifiers are immutable.

- A PostgreSQL-compatible relational database is authoritative for shared state.

- A DB-backed durable queue with transactional outbox/inbox is the initial execution direction.

- Contracts use versioned HTTP/JSON with schema validation.

- Artifact metadata is relational; binary payloads sit behind an object-storage abstraction.

- Each canonical entity has one authoritative owner; other modules hold references or request state transitions.

### 5.2 State machines remain separate

| State machine | Owns | Must not be conflated with |
| --- | --- | --- |
| Content lifecycle | Editorial/content status and content version progression. | Job status or approval. |
| Workflow lifecycle | Business process progress and orchestration stage. | Worker execution attempt. |
| Execution lifecycle | Job/attempt state, leases, retries and completion. | Content approval. |
| Review lifecycle | Review request, findings and disposition. | Owner approval or authorization. |
| Approval lifecycle | Human approval for exact version and defined use. | Permission to execute an external action. |
| Authorization lifecycle | Central policy decision for a specific protected action. | Execution result. |
| Distribution lifecycle | Prepared, submitted, confirmed, failed or unknown external outcome. | A mere request acknowledgement. |

Exact state names and transition tables must be reconciled with authoritative specifications in Batch 12 before contract freeze.

## 6. Canonical end-to-end content lifecycle

| Stage | Primary operation | Required output / control |
| --- | --- | --- |
| Discover | Capture topic/opportunity and context. | Traceable candidate and source context. |
| Research | Collect sources, notes and evidence. | Source records and provenance. |
| Verify | Evaluate reliability and substantiate claims. | Claim/evidence status; uncertainty surfaced. |
| Strategize | Select audience, angle, objective and format. | Brand-aligned strategy decision. |
| Brief | Create production brief and acceptance criteria. | Versioned brief and inputs. |
| Create | Generate script, storyboard and creative components. | Versioned outputs and job trace. |
| Review | Assess quality, claims, rights and editorial readiness. | Canonical quality outcome and findings. |
| Produce | Render/export using eligible workers and specialist engine. | Immutable artifact version and integrity evidence. |
| Approve | Human approves exact version for defined use. | Attributable version-bound approval. |
| Distribute | Prepare destination package and request protected action. | Central authorization and confirmed external outcome; P0 default is hold. |
| Analyze | Collect performance and outcome data. | Time/context-bound analytics observations. |
| Improve | Feed learning into future strategy/research. | Versioned changes; historical evidence preserved. |

The default P0 vertical slice should terminate at a governed pre-distribution hold. It must prove that the content and artifact are ready for a later authorized action without requiring public publishing.

## 7. Cross-package interface contracts

This section defines the contract boundary and minimum semantics. It intentionally does not invent exact endpoint paths, event names or field schemas that remain unverified in authoritative source artifacts.

| Interface | Minimum contract content | Safety / compatibility rule |
| --- | --- | --- |
| WP-1 → all | Canonical IDs, entity references, versions, ownership and persistence semantics. | One owner per entity; no ambiguous identity or silent overwrite. |
| WP-2 ↔ WP-3 | Assignment, worker identity, capability requirements, lease/heartbeat and completion report. | Worker trusted, available, capable and authorized for that task. |
| WP-2 ↔ WP-4 | Job output references, artifact version and attempt lineage. | Every output linked to exact job/attempt; immutable artifact versions. |
| WP-2 ↔ WP-5 | Policy checkpoint, review/approval reference and protected-action authorization request. | Re-evaluate central policy at the action boundary. |
| WP-3 ↔ WP-5 | Worker trust, capability and credential scope. | Revoked, untrusted or under-scoped worker denied. |
| WP-4 ↔ WP-5 | Artifact version, provenance, rights and retention context. | Unknown rights or quarantined asset blocked. |
| WP-5 → WP-6 | Quality outcome, hard blockers, approval and authorization evidence. | No ordinary approval can bypass hard blockers. |
| WP-1–WP-5 → WP-6 | Versioned APIs/events, lifecycle transitions and trace identifiers. | Contract tests and end-to-end correlation required. |
| Specialist engine ↔ orchestration/assets | Input manifest, bounded invocation, status and output manifest. | Engine cannot own shared workflow or policy state. |
| Distribution adapter ↔ authorization | Protected action request, policy result and confirmed external outcome. | No direct adapter bypass; no false publication success. |

## 8. Shared execution and job protocol

### 8.1 Required job envelope semantics

| Concept | Required behavior |
| --- | --- |
| Identity | Stable job ID, workflow reference and idempotency key. |
| Origin | Requesting actor/module and trace/correlation context. |
| Task definition | Task type, versioned input reference, required capabilities and constraints. |
| Scheduling | Priority, eligibility, concurrency and deadline where applicable. |
| Assignment | Worker identity, assignment ID, lease and scoped credentials. |
| Attempt | Attempt number, timestamps, heartbeat/lease evidence and error classification. |
| Completion | Outcome, output artifact references and structured failure details. |
| Audit | Actor, timestamps, policy checks and state transition evidence. |

### 8.2 Delivery and recovery rules

- Assume at-least-once queue delivery; never assume exactly-once execution.

- Idempotency keys and deduplication protect side effects from duplicate delivery.

- A lease expiry makes an assignment eligible for controlled recovery; it does not prove the worker stopped.

- Retries must distinguish transient, permanent, policy-blocked and unknown failures.

- Retry limits, backoff and dead-letter/quarantine behavior must be explicit.

- Cancellation must define whether in-flight work can stop, complete or be compensated.

- Every attempt remains in history; retries do not erase failed attempts.

- A worker crash must not lose durable job state or leave a job permanently running.

- External side effects require a separate idempotency/reconciliation strategy; a database transaction alone cannot guarantee external exactly-once behavior.

## 9. Worker identity, trust and capability contract

| Capability state | Meaning | Permitted use |
| --- | --- | --- |
| Declared | Worker claims it supports a capability. | Discovery hint only. |
| Verified | Capability has passed an approved verification process. | May be considered for eligibility. |
| Available | Worker is currently reachable/ready for the task. | May be scheduled if other checks pass. |
| Authorized | Policy grants this worker permission for this task/resource. | Required before assignment/execution. |

- Worker identity must be unique and independent of host name or network address.

- Credentials must be scoped, short-lived where feasible, stored safely and revocable.

- Registration, trust, health, suspension and revocation must be auditable.

- Capability matching must include version/requirements where compatibility matters.

- A worker cannot alter its own trust status, grant itself capabilities or approve its own output.

- Local worker absence must produce a waiting/deferred state for local-only tasks, not fabricated completion.

- Remote execution must be explicitly eligible for the task and permitted by policy.

## 10. Artifact and storage interaction contract

| Artifact concern | Required integration behavior |
| --- | --- |
| Registration | Every output is registered with canonical artifact identity and provenance. |
| Versioning | Versions are immutable; regeneration or repair creates a new version. |
| Integrity | Checksum and size/type metadata validated on write/read/transfer as appropriate. |
| Storage | Binary storage provider hidden behind an abstraction; metadata remains authoritative in relational store. |
| Transfer | Resumable transfer verifies completeness and integrity before promotion. |
| Quarantine | Corrupt, incomplete, suspicious or policy-blocked assets cannot proceed to production/distribution. |
| Lineage | Artifact links to source content version, job, worker, attempt and transformation where applicable. |
| Retention | Deletion, retention and legal hold follow explicit policy and audit rules. |

Provider selection and activation are not part of this integration blueprint. No paid storage or hosting service is authorized.

## 11. Quality, rights, approval and central authorization

### 11.1 Canonical quality outcomes

| Outcome | Interpretation | Default downstream behavior |
| --- | --- | --- |
| PASS | Required checks satisfied. | May proceed to remaining gates; not automatically approved. |
| PASS_WITH_WARNINGS | Checks pass with recorded non-blocking warnings. | Proceed only where policy permits and warnings remain visible. |
| NEEDS_REVIEW | Human/specialist judgement is required. | Hold until review disposition. |
| BLOCKED | A hard blocker or prohibited condition exists. | Stop protected progression; ordinary approval cannot override. |

### 11.2 Separate governance records

| Record | Must bind to | What it does not grant |
| --- | --- | --- |
| Quality assessment | Exact content/artifact version and rule-set version. | Human approval or action authorization. |
| Rights evidence | Asset/content, destination, use and time/context. | Blanket rights for other uses. |
| Review | Exact version, findings and reviewer. | Approval or permission to publish. |
| Approval | Exact version, intended use, approver and decision time. | Authorization to execute an external action. |
| Authorization | Protected action, resource, actor/worker, policy version and current context. | Proof of execution or external success. |
| Execution result | Attempt, actor/adapter and action correlation. | Confirmed external publication unless destination evidence proves it. |
| External outcome | Destination receipt/status or other authoritative confirmation. | Permission for future unrelated actions. |

- Unknown, missing, stale, contradictory or ambiguous rights/approval/authorization must fail closed.

- Hard blockers cannot be overridden by ordinary approval.

- Authorization must be checked immediately before protected action, not only when the job is queued.

- Publishing adapters cannot bypass central authorization.

- Automatic public publishing remains disabled pending separate policy approval.

## 12. Distribution boundary and external side-effect handling

Distribution Studio prepares destination-specific packages and coordinates protected actions through centralized authorization. It does not own the policy decision.

| Step | Required behavior | Evidence |
| --- | --- | --- |
| Prepare | Build destination package from exact approved version. | Package manifest and source artifact versions. |
| Preflight | Validate destination requirements, rights, quality and account context. | Preflight report and findings. |
| Request authorization | Ask central policy for a current decision on this exact action. | Authorization decision ID and policy version. |
| Execute | Perform only the explicitly authorized action. | Attempt ID, adapter version and request correlation. |
| Reconcile | Query destination or inspect authoritative receipt/status. | External confirmation or explicit unknown/pending result. |
| Record | Persist distribution lifecycle and evidence. | Audit record linked to content, artifact, approval and authorization. |

If the platform times out after accepting a request, the system must not blindly repeat a potentially non-idempotent publish. It must reconcile the destination state or hold for review. 'Request accepted' and 'published' are distinct.

## 13. Observability, audit and operational diagnostics

| Signal | Minimum fields / evidence | Purpose |
| --- | --- | --- |
| Correlation | Workflow ID, job ID, attempt ID, worker ID, artifact ID/version, review/approval/authorization IDs. | Trace the complete lifecycle. |
| State transition | Entity, from/to, actor, timestamp, reason and policy reference. | Explain why state changed. |
| Execution telemetry | Queue age, lease age, retry count, duration, worker health and failure class. | Detect stuck or unhealthy execution. |
| Artifact telemetry | Size, checksum, transfer state, quarantine reason and lineage. | Detect integrity and transfer problems. |
| Governance telemetry | Quality outcome, rights result, approval state and authorization result. | Prove fail-closed controls. |
| External action telemetry | Destination, request/attempt IDs and confirmed outcome. | Avoid false success reporting. |

Logs must not expose secrets, access tokens or unnecessary personal data. Diagnostic detail must be sufficient for safe troubleshooting without leaking credentials.

## 14. Failure modes and required system behavior

| Failure scenario | Expected behavior | Acceptance evidence |
| --- | --- | --- |
| Duplicate job delivery | Idempotent handling; one intended side effect. | Duplicate-message test and state comparison. |
| Worker disappears | Lease expiry and controlled reassignment/recovery. | Worker-loss injection and attempt history. |
| Local worker offline | Local-only task waits safely. | Offline/online transition test. |
| Database unavailable | No false durable acknowledgement; recover after service returns. | Fault injection and consistency check. |
| Outbox publish failure | Outbox record remains pending and is retried safely. | Outbox recovery test. |
| Artifact checksum mismatch | Quarantine and block downstream use. | Corruption test and quarantine evidence. |
| Rights unknown | Protected use blocked. | Fail-closed rights test. |
| Approval stale/version mismatch | Approval rejected for new version/use. | Version-binding test. |
| Hard QA blocker | Protected progression blocked despite approval. | Hard-blocker test. |
| Authorization revoked | Action denied at execution boundary. | Revocation race test. |
| External platform timeout | Outcome remains unknown/pending until reconciled. | Timeout and destination reconciliation test. |
| Process restart | Durable state restored; no lost attempt or duplicate protected side effect. | Restart/recovery test. |

## 15. Vertical-slice integration blueprint

The first P0 vertical slice should prove the architecture with the smallest end-to-end workflow that exercises every critical boundary while stopping before public distribution.

| Sequence | Action | Package / module | Expected evidence |
| --- | --- | --- | --- |
| 1 | Create content request and canonical content record. | WP-1 / Content Graph | Content ID, version and owner. |
| 2 | Create research workflow and collect source evidence. | WP-2 / Research | Workflow/job IDs and source records. |
| 3 | Verify claims and prepare strategy/brief. | WP-5 / Research / Strategy | Evidence links, review findings and brief version. |
| 4 | Generate script/storyboard through bounded creation workflow. | WP-2 / WP-3 / Creation | Assignment, worker, attempt and output references. |
| 5 | Run quality/rights checks. | WP-5 | Quality outcome, claims and rights findings. |
| 6 | Render using existing Shorts Studio adapter. | WP-2 / WP-3 / specialist engine | Bounded invocation and execution trace. |
| 7 | Register rendered output as immutable artifact version. | WP-4 | Artifact ID/version, checksum and lineage. |
| 8 | Review and approve exact version for intended internal/pre-distribution use. | WP-5 | Attributable review and version-bound approval. |
| 9 | Evaluate distribution readiness but hold before external publish. | WP-5 / Distribution | Central decision and explicit pre-distribution hold. |
| 10 | Reconcile full trace. | WP-6 | One trace connecting request through artifact and governance records. |

The vertical slice is not accepted by a successful render alone. It must prove canonical identity, durable execution, worker trust, artifact integrity, rights/quality gates, exact-version approval and end-to-end traceability.

## 16. Integration acceptance test catalogue

| Test ID | Scenario | Expected result | Required proof |
| --- | --- | --- | --- |
| INT-01 | Happy-path vertical slice. | Reaches pre-distribution hold with full trace. | E2E run and trace report. |
| INT-02 | Duplicate delivery. | No duplicate protected side effect. | Idempotency evidence. |
| INT-03 | Worker crash during task. | Lease expiry and safe recovery. | Failure-injection report. |
| INT-04 | Local worker unavailable. | Task waits and resumes only when eligible. | Worker-state trace. |
| INT-05 | Corrupt artifact. | Checksum mismatch quarantines asset. | Integrity/quarantine report. |
| INT-06 | Unknown rights. | Protected use blocked. | Policy decision evidence. |
| INT-07 | Approval for old version. | New version remains unapproved. | Version-binding test. |
| INT-08 | Hard blocker with approval present. | Protected action blocked. | Policy enforcement trace. |
| INT-09 | Authorization revoked before action. | Action denied. | Revocation test. |
| INT-10 | Platform timeout after request. | Outcome remains unknown until reconciled. | Destination reconciliation record. |
| INT-11 | Process restart during execution. | Durable state recovers without lost history. | Restart test. |
| INT-12 | Cross-package schema mismatch. | Compatibility validation rejects incompatible contract. | Contract test report. |
| INT-13 | Direct adapter invocation attempt. | Central authorization cannot be bypassed. | Negative security test. |
| INT-14 | Full traceability audit. | All lifecycle records are correlated. | Trace completeness report. |

## 17. Release gates and acceptance ownership

| Gate | Required evidence | Approver / authority |
| --- | --- | --- |
| G0 Preservation | Repository preservation baseline and no unapproved destructive changes. | Owner. |
| G1 Source integrity | Authoritative source register, exact decision wording and conflict disposition. | Owner / document custodian. |
| G2 Domain/persistence | WP-1 schema, constraints, migration and recovery tests. | Engineering owner; owner accepts contract. |
| G3 Execution/workers | WP-2/WP-3 reliability, trust and recovery evidence. | Engineering owner; independent QA reviews. |
| G4 Assets | WP-4 integrity, transfer, lineage and retention evidence. | Engineering owner; independent QA reviews. |
| G5 Governance | WP-5 fail-closed rights, quality, approval and authorization tests. | Owner and independent QA. |
| G6 Vertical slice | WP-6 E2E, failure injection, recovery and traceability. | Independent QA; owner accepts. |
| G7 Release | Operational readiness, rollback, monitoring and exact release scope. | Owner explicitly approves. |

The assistant, engineering agent or package owner cannot self-approve its own work. A passing automated test suite is necessary evidence but is not a substitute for independent review and owner acceptance.

## 18. Cross-package risks and mitigations

| Risk | Impact | Mitigation / control |
| --- | --- | --- |
| Duplicate state ownership | Divergent lifecycle and inconsistent data. | Canonical owner matrix; contract review; no shadow authoritative stores. |
| In-memory job state | Lost jobs on process restart. | Durable DB queue/state and recovery tests. |
| Worker trust confusion | Untrusted execution or capability escalation. | Separate declared/verified/available/authorized states. |
| Artifact overwrite | Loss of history and approval mismatch. | Immutable artifact versions and checksums. |
| Rights warning-only behavior | Unauthorized content use. | Central fail-closed rights enforcement. |
| Adapter bypass | Unapproved public action. | Central authorization at action boundary and negative tests. |
| Stale approval | Wrong version distributed. | Exact-version and use-bound approval. |
| False publish success | Incorrect user-facing state and audit. | External reconciliation; unknown remains unknown. |
| Premature cloud/provider choice | Unapproved cost and lock-in. | Provider-neutral contracts and explicit owner approval. |
| Repository cleanup damage | Loss of existing user work. | Strict preservation protocol and bounded file allowlists. |

## 19. Repository preservation and implementation boundary

Historical user-provided repository snapshot (01 Nov 2026): /home/demon/shorts_studio; local main reported tracking origin/main; remote SHA 9d38f81ba4f8022d0e820b6a5e1fe2a0fc288c8c; 23 tracked modified files and 56 untracked paths; no staged changes. Captured diff-stat output was blank and is a capture limitation, not proof that there are no changes.

- Preserve all tracked modifications and untracked paths.

- No reset, revert, stash, clean, delete, overwrite, rename, broad-stage, commit, push, branch change or remote change without explicit owner authorization.

- Do not repeat repository inventory checks merely for reassurance; refresh only when an authorized task genuinely depends on current state.

- Existing Shorts Studio is a bounded specialist engine; do not replace it wholesale.

- No agent execution or implementation work starts from this design document alone.

| Role | Responsibility | Boundary |
| --- | --- | --- |
| Owner | Final scope, freeze, authorization and protected-action authority. | Silence is not approval. |
| Assistant | Architecture coordination, integration documentation and acceptance review. | Cannot self-authorize implementation. |
| Qoder | Phase 11 engineering owner when explicitly assigned. | No scope expansion or self-approval. |
| OpenCode | Phase 10 engineering/closure owner when explicitly assigned. | Historical report is not fresh proof. |
| Kilo | Independent read-only QA. | No implementation changes or self-approval. |

## 20. Accepted decision outcomes retained

| Decision | Recorded accepted outcome |
| --- | --- |
| ADR-001 | UUIDv7 canonical immutable IDs. |
| ADR-002 | PostgreSQL-compatible relational DB authoritative for shared state. |
| ADR-003 | DB-backed durable queue with transactional outbox/inbox initially. |
| ADR-004 | Versioned HTTP/JSON contracts with schema validation. |
| ADR-005 | Unique worker identity, scoped short-lived credentials and capability authorization. |
| ADR-006 | Relational artifact metadata; binaries behind object-storage abstraction. |
| ADR-007 | Centralized authorization; publishing adapters cannot bypass; automatic publishing disabled pending policy. |
| ADR-008 | PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW, BLOCKED; hard blockers cannot be bypassed by ordinary approval. |
| ADR-009 | Evidence-backed rights states and use-specific enforcement. |
| ADR-010 | Separate lifecycle state machines for content, workflow, execution, review, approval, authorization and distribution. |
| CF-01–CF-15 | Accepted by owner as recorded in project history. |
| CF-16–CF-21 | Accepted under standing delegation as recorded in project history. |
| CF-22 | Explicitly accepted: Option A, centralized authorization. |
| CF-23 | Accepted under standing delegation; exact original wording still requires source verification. |
| CF-24 | Explicitly accepted: no paid services; operational/provider choices deferred. |

This table preserves recorded outcomes. It is not the original decision register and does not replace source verification in Batch 12.

## 21. Owner freeze review checklist

- ☐ System context, logical module boundaries and WP responsibilities are correct.

- ☐ Every canonical entity and state machine has one authoritative owner.

- ☐ Cross-package interface responsibilities and failure semantics are complete.

- ☐ Central governance and protected-action boundaries are correctly represented.

- ☐ The vertical slice is correctly scoped to a governed pre-distribution hold.

- ☐ Local-first/free-first and ₹0 initial spend constraints are preserved.

- ☐ Existing Shorts Studio is preserved as a specialist engine.

- ☐ Source gaps and unverified exact wording remain visible.

- ☐ Acceptance gates and independent QA responsibilities are adequate.

- ☐ Repository preservation and agent boundaries are accepted.

- ☐ Owner approves the exact version of the detailed contract after Batch 12 source reconciliation.

Owner review outcome: NOT YET APPROVED / PENDING SOURCE RECONCILIATION

Owner signature: ____________________________________    Date: __________________

Reviewed version / hash: _______________________________________________________

Exceptions or required changes: __________________________________________________

## 22. Formal disposition and handoff

Batch 11 establishes the integrated P0 architecture and cross-package interaction model. It is a comprehensive design candidate for owner review. It does not declare the contract frozen because Batch 12 source verification is still required.

Recommended order: (1) use this blueprint as the integration target; (2) complete Batch 12 source verification and exact contract reconciliation; (3) prepare Batch 13 implementation-readiness and controlled-execution package; (4) obtain explicit owner contract freeze; (5) obtain separate implementation authorization; (6) only then begin Phase 1.

| Status dimension | Batch 11 disposition |
| --- | --- |
| Architecture integration | DOCUMENTED — OWNER REVIEW REQUIRED |
| Accepted decisions | CARRIED FORWARD — NOT REOPENED |
| Detailed source fidelity | PENDING BATCH 12 RECONCILIATION |
| Contract freeze | NOT FROZEN |
| Implementation | NOT AUTHORIZED |
| Independent QA | PENDING |
| Public publishing | DISABLED BY DEFAULT |

End of Batch 11.


## Source document metadata (preserved from DOCX)

- **Header:** NEXTDECODE CONTENT OS  |  P0 MASTER INTEGRATION
- **Footer:** Batch 11  •  Master integration blueprint  •  01 Nov 2026

