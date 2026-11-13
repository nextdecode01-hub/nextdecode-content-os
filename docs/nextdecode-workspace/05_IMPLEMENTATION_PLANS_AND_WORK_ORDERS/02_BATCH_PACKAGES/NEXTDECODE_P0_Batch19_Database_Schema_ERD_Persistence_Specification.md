# P0 Database Schema, ERD & Persistence Specification

NEXTDECODE Content OS | Batch 19 | Version 0.1 — Design Candidate

Status: Detailed schema and persistence candidate; formal owner freeze pending; implementation authorization not granted.

Purpose: translate the accepted domain ownership, lifecycle, API/event and governance direction into a coherent relational persistence design that can be reviewed and frozen before engineering changes begin.

Scope boundary: this document specifies logical entities, relationships, constraints, transaction boundaries, index candidates, migration controls and acceptance evidence. It does not inspect or modify the repository, execute SQL, select a hosting provider, activate paid services, or authorize production generation, upload or publishing.

## 1. Authority, evidence and design status

| Classification | Meaning in this document |
| --- | --- |
| Accepted baseline | A decision explicitly recorded in the accepted ADR/CF baseline or canonical standards. |
| Derived design candidate | A proposed schema structure that operationalizes accepted principles but still requires detailed owner review. |
| Open decision | A detail not settled by the source records; it must remain explicit and must not be silently treated as approved. |
| Illustrative example | A sample name, relationship, index or SQL fragment used to explain the design; not a frozen identifier or executable migration. |

- Canonical identity uses immutable UUIDv7 identifiers (accepted ADR-001).

- PostgreSQL-compatible relational persistence is the accepted authoritative shared-state direction (ADR-002); exact engine/version/hosting remain unselected.

- A DB-backed durable queue with transactional outbox/inbox is the accepted initial direction (ADR-003).

- Logical domains do not imply microservices. One canonical owner is responsible for each entity and its authoritative writes.

- The Shorts Studio Python/FFmpeg engine remains a specialist execution component behind a bounded adapter; this schema does not replace it.

- No automatic public publishing. Human approval and centralized authorization remain separate gates.

- This is a candidate model, not an approved migration plan. Every proposed table/column/index below requires review against authoritative source records and owner freeze.

## 2. Persistence design principles

| Principle | Persistence consequence |
| --- | --- |
| One canonical owner | Each authoritative entity has one owning domain; other domains store references or read projections, not competing truth. |
| Identity ≠ version | Stable entity ID identifies the logical object; immutable version rows identify a particular revision or snapshot. |
| Explicit scope | Workspace and applicable brand/studio/account scope are explicit; authorization is never inferred from a missing scope. |
| Append-oriented evidence | Approval, authorization, rights evidence, audit and external-operation outcomes are recorded as attributable records rather than overwritten flags. |
| No ambiguous status | Use purpose-specific fields such as lifecycle_status, epistemic_status, quality_outcome, governance_disposition, approval_outcome, execution_status and external_operation_status. |
| Optimistic concurrency | Mutable aggregates carry state_version or equivalent revision; commands may provide expected version. |
| At-least-once delivery | Inbox deduplication, idempotency and transactional outbox support safe retries. |
| Fail closed | Unknown rights, missing approval, absent authorization, integrity uncertainty or hard QA blockers do not grant permission. |
| Repair is a new version | Artifact repair/replacement creates a new immutable ArtifactVersion; it does not rewrite historical bytes or manifests. |
| No invented retention | Retention periods, deletion policy and legal-hold details remain open until approved. |

## 3. Logical data architecture and ERD

The diagram is a logical relationship map, not a physical deployment diagram. Cardinalities are indicative. Optionality and exact foreign keys must be confirmed during detailed schema review.

WORKSPACE 1 ──< BRAND
WORKSPACE 1 ──< STUDIO
WORKSPACE 1 ──< CONTENT_ITEM 1 ──< CONTENT_VARIANT 1 ──< CONTENT_VERSION
CONTENT_ITEM ──< RESEARCH_LINK >── RESEARCH_RECORD
CONTENT_ITEM ──< KNOWLEDGE_LINK >── KNOWLEDGE_RECORD
CONTENT_ITEM ──< STRATEGY_PLAN / CALENDAR_ENTRY
CONTENT_VERSION ──< QA_EVALUATION
CONTENT_VERSION ──< RIGHTS_DETERMINATION ──< RIGHTS_EVIDENCE
CONTENT_VERSION ──< REVIEW / APPROVAL_DECISION
APPROVAL_DECISION ──< AUTHORIZATION_DECISION
WORKFLOW_DEFINITION 1 ──< WORKFLOW_RUN 1 ──< TASK_INSTANCE
TASK_DEFINITION 1 ──< TASK_INSTANCE
TASK_INSTANCE ──< JOB 1 ──< JOB_ATTEMPT ──< LEASE
WORKER 1 ──< WORKER_CREDENTIAL / WORKER_CAPABILITY / JOB_ATTEMPT
ARTIFACT 1 ──< ARTIFACT_VERSION 1 ──< ARTIFACT_MANIFEST
ARTIFACT_VERSION ──< TRANSFER / VALIDATION / QUARANTINE_RECORD
CONTENT_VERSION / JOB_ATTEMPT / QA_EVALUATION ──< ARTIFACT_LINK
CONTENT_VERSION ──< DISTRIBUTION_PACKAGE ──< DISTRIBUTION_OPERATION
DISTRIBUTION_OPERATION ──< EXTERNAL_OPERATION_EVENT
ALL DOMAINS ──< AUDIT_EVENT / DOMAIN_EVENT
TRANSACTIONAL WRITE ──> OUTBOX_EVENT ──> INBOX_RECEIPT / PROJECTION
COMMAND ──> IDEMPOTENCY_RECORD

Interpretation: arrows indicate conceptual references only. Cross-domain references should normally point to immutable IDs and, where correctness depends on a revision, to the exact version ID as well.

## 4. Canonical identity, scope and common columns

| Field / concept | Candidate rule | Status |
| --- | --- | --- |
| id | UUIDv7 primary key; immutable after creation. | Accepted identity standard; exact physical type to confirm. |
| workspace_id | Required on workspace-scoped records; FK to Workspace. | Derived candidate from scope standard. |
| brand_id | Required where brand ownership or policy scope applies; FK to Brand. | Derived candidate; nullable only where domain allows. |
| studio_id | Required for studio execution/configuration records where applicable. | Derived candidate. |
| created_at / updated_at | UTC timestamps; updated_at only for mutable records. | Candidate; timestamp precision open. |
| created_by / actor_ref | Authenticated actor reference or system actor; never trust caller-supplied actor identity. | Accepted API/security direction. |
| schema_version | Version the serialized contract/payload where schema evolution requires it. | Accepted contract direction. |
| state_version | Monotonic aggregate revision for concurrency-sensitive state. | Derived candidate; increment semantics to freeze. |
| classification / purpose | Explicit data classification and purpose where required by policy. | Canonical data dictionary direction. |

Do not introduce a universal status column. The meaning of a state field must be explicit in its name and owned state machine. Avoid storing duplicated display labels as authoritative data.

## 5. Entity catalogue and ownership

| Entity | Logical owner | Core fields (illustrative) | Design note |
| --- | --- | --- | --- |
| Workspace | Workspace & Control Center | id, owner_actor_ref, lifecycle_status, state_version | One initial owner workspace is in initial scope; future multi-tenant expansion is not assumed. |
| Brand | Brand Intelligence | id, workspace_id, name, lifecycle_status, active_profile_version_id | Brand identity and brand-profile version must remain distinct. |
| Studio | Workspace & Control Center | id, workspace_id, studio_type, lifecycle_status | Logical execution/studio scope; not necessarily a separate service. |
| ContentItem | Content Graph | id, workspace_id, brand_id, content_type, lifecycle_status, state_version | Canonical editorial subject; not the same as a variant or rendered file. |
| ContentVariant | Content Graph | id, content_item_id, format, lifecycle_status | A derivative/format-specific expression of a ContentItem. |
| ContentVersion | Content Graph | id, content_variant_id, version_number, immutable_payload_ref, created_at | Immutable snapshot; exact payload storage model open. |
| KnowledgeRecord | Knowledge Management | id, workspace_id, source_ref, epistemic_status, classification | Knowledge source and confidence/provenance must not be conflated. |
| ResearchRecord | Research Intelligence | id, workspace_id, query_ref, evidence_set_ref, epistemic_status | Research evidence and synthesis lineage retained. |
| BrandProfileVersion | Brand Intelligence | id, brand_id, version_number, profile_payload_ref | Immutable profile snapshot; exact schema open. |
| StrategyPlan / CalendarEntry | Strategy & Planning | id, workspace_id, brand_id, plan_version_id, schedule fields | Separate plan definition/version from scheduled execution where needed. |
| QAEvaluation | Content Quality Intelligence | id, target_entity_id, target_version_id, quality_outcome, evidence_ref | Accepted outcomes: PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW, BLOCKED. |
| RightsEvidence | Governance | id, subject/version ref, evidence_type, source_ref, captured_at | Evidence is append-oriented; source and use scope required. |
| RightsDetermination | Governance | id, subject/version ref, rights_state, policy_version, evidence_set_ref | CF-20 vocabulary; determination is use-specific and evidence-backed. |
| Review | Governance | id, target_version_id, reviewer_ref, review_outcome, reason | Review record is distinct from formal approval and authorization. |
| ApprovalDecision | Governance | id, target_version_id, approval_outcome, approver_ref, decided_at | CF-21 vocabulary; exact-version bound. |
| AuthorizationDecision | Central Authorization | id, action, resource_ref, resource_version_id, destination_ref, policy_version, validity window, decision | Separate from approval; default deny and execution-time revalidation. |
| WorkflowDefinition | Automation & Agent Orchestration | id, workspace_id, definition_version, immutable_definition_ref | Definition is not a run. |
| WorkflowRun | Automation & Agent Orchestration | id, workflow_definition_version_id, execution_status, state_version | Run has its own lifecycle and execution facts. |
| TaskDefinition | Automation & Agent Orchestration | id, workflow_definition_version_id, task_key, definition_version | Definition-level task; no runtime lease here. |
| TaskInstance | Automation & Agent Orchestration | id, workflow_run_id, task_definition_version_id, execution_status | A runtime instance; cardinality to jobs requires owner freeze. |
| Job | Durable Execution | id, task_instance_id, execution_status, priority, available_at, state_version | Durable unit of work; not a worker identity. |
| JobAttempt | Durable Execution | id, job_id, attempt_number, execution_status, started_at, finished_at | Append-oriented attempt history; attempt limits/backoff values open. |
| Lease | Durable Execution | id, job_attempt_id, worker_id, lease_expires_at, lease_token_hash | Lease renewal, fencing and expiry semantics need detailed freeze. |
| Worker | Worker Registry | id, worker_identity, trust_state, capability_snapshot_ref | Unique identity; trust and capability authorization required. |
| WorkerCredential | Worker Registry | id, worker_id, credential_ref, issued_at, expires_at, revoked_at | Store secret references/hashes only; never plaintext credentials. |
| WorkerCapability | Worker Registry | id, worker_id, capability_key, constraints, effective window | Capability catalogue and exact policy model remain open. |
| Artifact | Asset Management | id, workspace_id, artifact_type, lifecycle_status | Logical artifact identity. |
| ArtifactVersion | Asset Management | id, artifact_id, version_number, checksum, byte_size, storage_ref | Immutable binary/version metadata; repair creates a new version. |
| ArtifactManifest | Asset Management | id, artifact_version_id, manifest_schema_version, manifest_ref, checksum | Manifest describes exact artifact version and lineage. |
| ArtifactLink | Asset Management | id, artifact_version_id, linked_entity_type, linked_entity_id, relation | Typed lineage/reference; avoid unconstrained polymorphic links unless validated. |
| Transfer | Asset Management | id, artifact_version_id, source_ref, destination_ref, execution_status | Transfer attempt/result tracked independently of artifact identity. |
| ValidationRecord | Asset Management | id, artifact_version_id, validation_type, outcome, evidence_ref | Integrity/format/security validation evidence. |
| QuarantineRecord | Asset Management | id, artifact_version_id, reason, disposition, opened_at, closed_at | Quarantine is explicit; no silent availability. |
| DistributionPackage | Distribution Studio | id, content_version_id, package_version_id, lifecycle_status | Exact content and asset versions included. |
| DistributionOperation | Distribution Studio | id, package_version_id, destination_id, external_operation_status | External side-effect record; unknown outcome must be reconciled. |
| Destination | Distribution Studio | id, workspace_id, platform_ref, account_ref, policy_ref | Credential/account binding and provider specifics open. |
| ExternalOperationEvent | Distribution Studio | id, distribution_operation_id, observed_status, provider_ref, observed_at | Append evidence for external result/reconciliation. |
| AuditEvent | Cross-cutting audit | id, actor_ref, action, resource_ref, reason, occurred_at, correlation_id | Append-only audit trail; access and retention policy open. |
| DomainEvent | Domain owner | id, aggregate_ref, event_type, schema_version, state_version, payload_ref | Committed fact, not an authorization grant. |
| OutboxEvent | Persistence infrastructure | id, domain_event_id, delivery_state, created_at, published_at | Written in same transaction as domain state change. |
| InboxReceipt | Persistence infrastructure | id, consumer_id, event_id, received_at, outcome | Deduplicates at-least-once deliveries. |
| IdempotencyRecord | Persistence infrastructure | id, scope_key, idempotency_key, request_hash, outcome_ref, expires_at | Uniqueness scope and retention period open. |
| Projection / ReadModel | Owning consumer | projection_key, source_version, rebuilt_at | Derived and rebuildable; never authoritative over source aggregate. |

## 6. Relationship and foreign-key rules

- Use real foreign keys for relationships within the same relational ownership boundary wherever practical; document intentional references across independently managed stores.

- Every workspace-scoped child must reference its workspace directly or prove scope through a constrained parent relationship. Direct scope columns may be duplicated for efficient authorization checks only if consistency is enforced.

- Use composite uniqueness or composite foreign keys where needed to prevent cross-workspace references (for example, a child workspace_id must match its parent workspace_id).

- Version-sensitive records must reference the exact immutable version ID, not merely the mutable parent entity ID.

- Do not use display names, slugs or external provider IDs as canonical primary keys. External IDs belong in scoped mapping tables with uniqueness constraints.

- Polymorphic references (entity_type + entity_id) are flexible but do not provide ordinary FK enforcement. Prefer typed link tables or explicit nullable FKs for high-integrity relationships.

- Delete cascades must not erase audit, approval, rights, authorization, attempt or external-operation evidence. Restrict or soft-delete according to an approved retention/legal-hold policy.

- Unique natural keys must include their true scope, such as workspace_id + external_source + external_id, where that mapping is required.

## 7. Versioning and immutability model

| Object | Mutable or immutable? | Candidate rule |
| --- | --- | --- |
| Canonical entity | Identity immutable; selected metadata mutable under owner rules. | Stable UUIDv7 id; state_version increments on accepted mutation. |
| Content/brand/workflow definition version | Immutable. | New version row for each approved revision; preserve author, time and source. |
| ArtifactVersion + manifest | Immutable. | Checksum, byte size, media/type metadata and manifest bind to exact bytes/version. |
| QA evaluation | Append-oriented. | Re-evaluation creates a new record; do not overwrite prior result. |
| Rights evidence/determination | Append-oriented. | New evidence/determination supersedes for current decision without deleting history. |
| Approval decision | Append-oriented. | New decision/revocation record; exact target version and approver recorded. |
| Authorization decision | Append-oriented and time-bound. | Re-evaluate at execution time; store action/resource/version/destination/policy binding. |
| JobAttempt / Transfer / DistributionOperation | Append-oriented execution facts. | Retries and reconciliation create traceable attempt/event records. |

Version numbering may be per parent aggregate and may be represented as an integer for human ordering, but the immutable UUIDv7 version ID remains the canonical reference. Whether version numbers are gapless is not assumed.

## 8. State fields and controlled vocabularies

| Field family | Accepted vocabulary / rule | Persistence guidance |
| --- | --- | --- |
| quality_outcome | PASS; PASS_WITH_WARNINGS; NEEDS_REVIEW; BLOCKED | Persist exact token; BLOCKED is a hard blocker under ordinary approval. |
| rights_state | UNKNOWN; PENDING_REVIEW; CLEARED; RESTRICTED; EXPIRED; REVOKED; DENIED | CF-20 canonical vocabulary; never map older tokens silently. |
| approval_outcome | APPROVED; REJECTED; CHANGES_REQUESTED; EXPIRED; REVOKED | CF-21 canonical vocabulary; exact version binding. |
| authorization | Centralized, default deny; separate from approval | Decision record includes exact action/resource/version/destination/policy and validity. |
| execution_status | Domain-specific lifecycle/attempt/run state | Candidate enum set not frozen; use state-machine ownership. |
| external_operation_status | Provider-observed or unknown outcome | Unknown external outcome must be reconciled, not blindly retried. |
| epistemic_status | Knowledge certainty/provenance dimension | Do not overload with lifecycle state. |
| lifecycle_status | Existence/availability lifecycle | Do not use as a substitute for execution or governance state. |

The exact full lifecycle enum sets for content, workflow, task, job, worker, artifact, transfer and distribution are not frozen by this schema document. Use the canonical lifecycle transition standard and Batch 17 catalogue for owner review.

## 9. Durable execution persistence

| Concern | Candidate persistence design | Open detail |
| --- | --- | --- |
| Queue claim | Claim eligible Job rows transactionally; prevent two workers claiming the same active lease. | Exact locking/claim algorithm and DB isolation level. |
| Attempt history | Create JobAttempt per execution attempt; never reuse an attempt row for a retry. | Attempt numbering and retry policy. |
| Lease | Persist worker, expiry, heartbeat/renewal facts and fencing token or equivalent. | Lease duration, renewal cadence and fencing implementation. |
| Worker authorization | Validate worker identity, trust, scoped credential and capability before assignment and execution. | Credential issuer, revocation propagation and capability catalogue. |
| Late result | Accept result only if attempt/lease/fencing context remains valid; record stale result for audit. | Exact stale-result disposition and operator workflow. |
| Unknown result | Reconcile side effects before retry when external operation may have succeeded. | Per-provider reconciliation mechanisms. |
| Retry | New JobAttempt with policy-driven available_at/backoff; preserve prior error/result. | Maximum attempts and backoff values intentionally open. |

Do not implement a queue by treating a process-local in-memory list as durable state. A durable job/attempt/lease record must survive process restart and support recovery evidence.

## 10. Outbox, inbox and idempotency

1. Within one database transaction, validate the aggregate transition, persist the authoritative state change, increment state_version, append the domain event and insert its outbox row.

1. A dispatcher publishes pending outbox records. Delivery is at least once; a successful publish marker is recorded only after the transport confirms acceptance.

1. Each consumer records an inbox receipt keyed by consumer identity and event ID in the same transaction as its local effect, so duplicate delivery does not repeat the effect.

1. Commands that can be retried use an idempotency key scoped to the authenticated actor/workspace/operation as appropriate, plus a canonical request hash.

1. If the same idempotency key is reused with a different request hash, reject it as a conflict; do not replay a prior result for a different payload.

1. Persist correlation_id and causation_id through command, event, job, attempt, artifact and external operation records.

Illustrative uniqueness candidates: (consumer_id, event_id) for inbox; (scope_key, idempotency_key) for command idempotency; unique event_id for outbox; aggregate_id + state_version for ordered aggregate history. Exact scope and retention need freeze.

## 11. Artifact registry, integrity and transfer

- Artifact is the logical identity; ArtifactVersion is the immutable content instance. Do not overwrite bytes under an existing version ID.

- Store a cryptographic checksum algorithm identifier and checksum value, byte size, media type, detected format, storage reference and creation provenance.

- Manifest records should bind the exact ArtifactVersion, input versions, transformation/tool versions, parameters, outputs and relevant evidence references. The manifest schema itself is versioned.

- ValidationRecord stores validator identity/version, validation type, outcome, timestamp and evidence. A successful upload/transfer does not itself prove content integrity.

- Transfer has its own execution state and attempts; partial, failed or unknown transfers must be distinguishable from a verified complete transfer.

- QuarantineRecord blocks ordinary use while a security, integrity, rights or policy concern is unresolved. Release requires an attributable disposition and any required revalidation.

- Repair or re-encoding creates a new ArtifactVersion with new checksum and lineage; preserve the prior version and its evidence.

- Storage provider, bucket/container layout, encryption implementation, retention period and backup topology remain open. Use an abstraction; do not bind the schema to an unapproved provider.

## 12. Rights, review, approval and authorization records

| Record | Must bind to | Must retain |
| --- | --- | --- |
| RightsEvidence | Subject + exact version where applicable + use/purpose + source | Evidence source, capture time, provenance, actor and integrity reference. |
| RightsDetermination | Subject/version + intended use + policy version | CF-20 state, evidence set, reason, reviewer/decision actor and time. |
| Review | Exact content/artifact version under review | Reviewer, outcome, findings, requested changes and evidence. |
| ApprovalDecision | Exact version + approver authority | CF-21 outcome, actor, time, reason, revocation/expiry linkage. |
| AuthorizationDecision | Action + exact resource/version + destination + policy version + validity | Allow/deny, evaluated facts, reason, actor/service, expiry and revocation context. |
| DistributionOperation | Exact package/version + destination + authorization decision | Attempt history, external references, observed outcomes and reconciliation evidence. |

An approval record is not an authorization grant. An authorization grant is not proof of execution. An API response indicating accepted/queued is not proof of external publication. These distinctions must survive in both schema and user-facing status.

## 13. Index and uniqueness candidates

| Area | Candidate index / constraint | Why |
| --- | --- | --- |
| Workspace scope | (workspace_id, created_at DESC) on frequently listed scoped entities | Scoped browsing and control-center views. |
| Content | (workspace_id, lifecycle_status, updated_at DESC) | Content lists and lifecycle filtering. |
| Immutable versions | UNIQUE(parent_entity_id, version_number); UNIQUE(id) | Resolve a version within its parent. |
| Workflow runs | (workspace_id, execution_status, created_at) | Run monitoring and recovery. |
| Queue claims | (execution_status, available_at, priority) with a partial predicate for claimable jobs | Efficient eligible-job selection; exact predicate open. |
| Lease expiry | (lease_expires_at) for active leases | Lease reaper and recovery. |
| Attempts | UNIQUE(job_id, attempt_number); (job_id, started_at DESC) | Attempt integrity and history. |
| Worker | UNIQUE(worker_identity); indexes on trust_state and capability lookup | Identity uniqueness and eligibility. |
| Artifacts | UNIQUE(artifact_id, version_number); (workspace_id, artifact_type, created_at DESC) | Version resolution and scoped browsing. |
| Checksum | (checksum_algorithm, checksum_value) where deduplication policy permits | Integrity lookup; global deduplication may leak cross-scope information and is not assumed. |
| Governance | (target_version_id, decided_at DESC); (resource_version_id, validity window) | Current decision lookup and audit. |
| Outbox | (delivery_state, created_at); unique domain_event_id | Dispatcher polling and deduplication. |
| Inbox | UNIQUE(consumer_id, event_id) | Consumer idempotency. |
| Idempotency | UNIQUE(scope_key, idempotency_key) | Command replay protection. |
| Audit/correlation | (correlation_id, occurred_at); (resource_ref, occurred_at) | End-to-end investigation. |

Index selection must be validated against real query patterns and data volumes. Avoid speculative indexes on every column; measure before adding expensive indexes.

## 14. Concurrency, transactions and consistency

- Use optimistic concurrency for aggregate updates: caller supplies expected state_version; update succeeds only when stored version matches.

- Increment state_version exactly once for each accepted aggregate transition. Rejected/conflicting commands must not mutate authoritative state.

- Use transactions for invariants that must be atomic within one relational database, including aggregate update + domain event + outbox insert.

- Do not claim distributed atomicity across the database, object storage, worker process and external platform. Model each boundary as an explicit operation with retries and reconciliation.

- External side effects require a durable operation record before execution, a centrally validated authorization binding, and an observed result record afterward.

- Read projections may be eventually consistent and rebuildable. Display their freshness or source version where stale data could mislead an operator.

- Use UTC instants for persisted event/decision timestamps. Local display timezone is a presentation concern; scheduling timezone and daylight-saving behavior need explicit policy.

## 15. Security, privacy and data minimization

- Never store plaintext passwords, API tokens, refresh tokens or worker secrets in ordinary entity columns. Persist secret-manager references or carefully protected credential metadata only.

- Derive actor identity from authenticated context; do not trust a requested_by value supplied by an untrusted client as proof of identity.

- Apply workspace and resource scope checks at the service boundary and enforce database constraints where practical; do not rely on UI filtering.

- Separate operational logs from audit evidence. Redact credentials, personal data and sensitive payloads from logs and event envelopes.

- Persist only the evidence needed for the declared purpose. Classification, purpose, access and retention policies must be explicit.

- Use restricted access for rights evidence, credentials, audit data and authorization evaluations.

- Do not assume row-level security is selected or configured; it is an open implementation/security decision requiring threat-model review.

## 16. Retention, deletion, legal hold and archival

These topics are intentionally unresolved. The source baseline establishes the need for governance and evidence but does not provide a complete approved retention schedule or legal-hold implementation.

| Topic | Candidate requirement | Decision status |
| --- | --- | --- |
| Retention schedule | Define per data class, purpose and jurisdiction; specify trigger and disposition. | OPEN — no periods invented. |
| Deletion | Define soft-delete/tombstone versus physical deletion; preserve required audit/evidence. | OPEN. |
| Legal hold | Hold must prevent covered deletion/expiry and be attributable and reviewable. | OPEN — exact workflow/schema open. |
| Artifact expiry | Do not delete binaries while referenced by active versions, approvals, operations or holds. | Candidate safeguard; dependency rules open. |
| Backups | Define backup retention, restore testing and deletion propagation. | OPEN. |
| Audit/event retention | Define immutable retention, access and archival policy. | OPEN. |
| Data subject/privacy requests | Define discovery, export, correction and deletion workflow where applicable. | OPEN — legal review required. |

## 17. Migration and schema rollout strategy

| Stage | Required activity | Exit evidence |
| --- | --- | --- |
| M0 — Source and baseline | Confirm authoritative source versions, current schema/repository baseline and preservation constraints. | Approved source inventory and non-destructive baseline record. |
| M1 — Contract-to-schema mapping | Map every accepted entity/field/relationship to owner, API, event and state machine; resolve contradictions. | Traceability matrix with no unexplained high-severity gaps. |
| M2 — Logical schema review | Review ERD, keys, constraints, immutability, scope and security. | Owner-reviewed schema candidate and recorded decisions. |
| M3 — Physical design | Select exact DB engine/version, types, indexes, constraints, isolation and migration tooling. | Approved physical design; not inferred from this document. |
| M4 — Migration plan | Design additive/expand-first migrations, backfill, validation, cutover and rollback/forward-fix. | Reviewed migration scripts and rehearsal evidence. |
| M5 — Test environment rehearsal | Apply migrations to disposable fixtures; test concurrency, restart, duplicate delivery and restore. | Repeatable logs, assertions and recovery evidence. |
| M6 — Production authorization | Separate explicit owner authorization for environment, timing, backup, change window and rollback. | Written authorization; absent today. |

- Prefer additive/expand-first migrations: add compatible structures, deploy compatible readers/writers, backfill, verify, then remove obsolete structures only under separate approval.

- Never use destructive reset/clean/drop/truncate or broad rewrite as a shortcut. Preserve all existing tracked and untracked user work.

- A migration must have an explicit owner, preconditions, expected row counts, validation queries, failure handling and recovery plan.

- Do not run migrations as part of this documentation batch.

## 18. Acceptance and failure-injection scenarios

| ID | Scenario | Acceptance oracle |
| --- | --- | --- |
| DB-01 | UUIDv7 identity | New canonical records receive unique immutable UUIDv7 IDs; IDs are not regenerated on retry. |
| DB-02 | Workspace isolation | A child cannot reference a parent from another workspace, including composite-FK and service validation paths. |
| DB-03 | Version integrity | An immutable version cannot be updated in place; a new revision creates a new version ID. |
| DB-04 | Optimistic concurrency | Two commands with the same expected state_version cannot both commit conflicting transitions. |
| DB-05 | Atomic outbox | A committed domain transition always has its corresponding outbox record; rollback leaves neither. |
| DB-06 | Duplicate inbox | Delivering the same event twice to one consumer causes one committed effect. |
| DB-07 | Idempotency mismatch | Reusing a key with a different request hash returns conflict and does not replay the old result. |
| DB-08 | Queue restart | Restarting the API/worker does not lose queued jobs, attempts or lease history. |
| DB-09 | Lease expiry | Expired lease is recoverable without allowing an obsolete worker to commit a current result. |
| DB-10 | Late result | A result from a stale attempt/lease is retained for audit but cannot overwrite current state. |
| DB-11 | Worker revocation | Revoked/expired credential or insufficient capability blocks new assignment/execution. |
| DB-12 | Artifact integrity | Checksum mismatch blocks ordinary use and creates a validation/quarantine record. |
| DB-13 | Artifact repair | Repair creates a new ArtifactVersion and preserves the old version and lineage. |
| DB-14 | Rights fail-closed | UNKNOWN, PENDING_REVIEW, RESTRICTED, EXPIRED, REVOKED or DENIED never silently permits protected use. |
| DB-15 | Approval binding | Approval for version N does not approve version N+1. |
| DB-16 | Authorization binding | Authorization for one action, version, destination or policy cannot be reused for another. |
| DB-17 | BLOCKED QA | BLOCKED cannot be bypassed by ordinary approval. |
| DB-18 | External unknown outcome | Unknown publish outcome is reconciled before retry; no duplicate blind side effect. |
| DB-19 | Audit continuity | Actor, reason, time, correlation and causation remain traceable across command, job, attempt and operation. |
| DB-20 | Retention/legal hold | When policy is approved, held records cannot be purged by ordinary retention jobs. |
| DB-21 | Projection rebuild | Read models can be rebuilt from authoritative records/events and do not become a competing source of truth. |
| DB-22 | Migration rehearsal | Migration can be repeated in a disposable environment with row-count and integrity checks; rollback/forward-fix is evidenced. |

## 19. Open decisions requiring owner or specialist review

| ID | Open decision |
| --- | --- |
| SC-01 | Exact physical DB engine/version, deployment topology and extension policy. |
| SC-02 | Physical table names, schemas/namespaces, column types, nullability and naming conventions. |
| SC-03 | Final entity cardinalities: task-to-job, workflow run scheduling, one-to-many attempts and multi-worker execution semantics. |
| SC-04 | Exact state enums and transition ownership for all aggregates; reconcile with Batch 17 and canonical lifecycle standard. |
| SC-05 | Version numbering, draft/published semantics and immutable payload storage format. |
| SC-06 | Typed FK strategy versus validated polymorphic references for artifact lineage and cross-domain links. |
| SC-07 | Worker credential issuance, secret storage, revocation propagation, capability catalogue and fencing mechanism. |
| SC-08 | Queue claim algorithm, isolation level, retry/backoff/attempt limits and dead-letter/manual recovery policy. |
| SC-09 | Outbox/inbox transport, payload storage, ordering guarantees, retention and replay controls. |
| SC-10 | Idempotency scope, request canonicalization, key expiry and response retention. |
| SC-11 | Artifact storage abstraction, checksum algorithm, manifest schema, deduplication scope and quarantine release authority. |
| SC-12 | Destination/account model, provider mapping and external operation reconciliation per platform. |
| SC-13 | Rights evidence taxonomy, use/purpose model and evidence sufficiency rules. |
| SC-14 | Authorization decision schema, revocation, emergency pause, policy versioning and execution-time enforcement. |
| SC-15 | Retention, deletion, legal hold, archival, backup and privacy-request policies. |
| SC-16 | Audit immutability/tamper evidence, access policy and retention. |
| SC-17 | Read projection strategy, rebuild cadence and acceptable staleness. |
| SC-18 | Migration tool, rollout orchestration, rollback/forward-fix and environment controls. |
| SC-19 | Performance targets, expected data volumes, index budgets and partitioning thresholds. |
| SC-20 | Whether and where row-level security is required, and how it is tested. |

## 20. Traceability to accepted architecture

| Accepted baseline | Schema implication |
| --- | --- |
| ADR-001 UUIDv7 | Canonical IDs are UUIDv7 and immutable. |
| ADR-002 relational authoritative store | Relational aggregates and constraints own shared state. |
| ADR-003 DB-backed durable queue + outbox/inbox | Jobs, attempts, leases, outbox, inbox and idempotency are durable records. |
| ADR-004 versioned HTTP/JSON | Schema version fields and compatible migration discipline. |
| ADR-005 worker identity and scoped credentials | Worker, credential and capability records; no plaintext secrets. |
| ADR-006 artifact metadata + storage abstraction | Artifact/ArtifactVersion/manifest metadata separate from binary storage. |
| ADR-007 centralized authorization | AuthorizationDecision separate from approval and distribution execution. |
| ADR-008 quality outcomes | Exact accepted quality vocabulary; BLOCKED is a hard blocker. |
| ADR-009 evidence-backed rights | RightsEvidence and RightsDetermination are attributable and use-specific. |
| ADR-010 separate state machines | State fields and owners remain distinct; no universal status column. |

Related documents: Batch 15 Source Reconciliation & Contract Closure Dossier; Batch 16 Domain & Interface Contract Closure Pack; Batch 17 State-Machine & Transition Catalogue; Batch 18 API, Event & Schema Specification Pack; canonical Data Dictionary; API/Event Contract Standard; Unified Lifecycle State/Transition Standard; Artifact 08 reconciliation and cross-document gap review.

## 21. Freeze checklist and implementation boundary

- Confirm this candidate against the authoritative source documents and the current module-to-contract traceability matrix.

- Resolve all HIGH cross-document gaps that affect schema ownership, authorization, worker trust, artifact versioning and recovery.

- Approve entity ownership and exact cardinalities; no two domains may claim the same authoritative write.

- Approve physical DB engine/version and physical schema separately from this logical design.

- Approve exact enums, constraints, indexes, retention/legal-hold and security policies.

- Approve migration and test strategy with preservation safeguards.

- Record explicit owner disposition for each open decision; silence or a request to continue documentation is not approval.

- Only after formal contract freeze may a separate implementation authorization be considered.

## 22. Final status

Batch 19 delivers a detailed relational schema and persistence candidate. It does not claim that the schema is frozen, that migrations exist or have run, that the repository has been inspected in this batch, or that implementation is authorized.

Current gate: detailed design candidate → owner review and source reconciliation → formal contract freeze → separate explicit implementation authorization.

Safety invariant: no paid services, cloud deployment, destructive repository operation, production generation, upload or public publishing is authorized by this document.


## Source document metadata (preserved from DOCX)

- **Header:** NEXTDECODE CONTENT OS  |  P0 ARCHITECTURE SERIES
- **Footer:** Batch 19 — Database Schema, ERD & Persistence Specification  |  Design candidate — not implementation authorization

