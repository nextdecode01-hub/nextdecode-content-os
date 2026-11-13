# NEXTDECODE Content OS
## Artifact 08 — P0 Detailed Contract Freeze & Open Decisions Closure 1.0

**Version:** 1.0  
**Date:** 31 October 2026  
**Status:** Consolidated contract-review baseline — owner review required  
**High-level ADR status:** ADR-001 through ADR-010 ACCEPTED  
**Detailed contract freeze:** NOT YET APPROVED  
**Implementation authorization:** NOT GRANTED  
**Repository inspection:** NOT AUTHORIZED  
**Git operations:** NOT AUTHORIZED  
**Production authorization:** NOT GRANTED  
**Authority:** Product Owner

**Related artifacts**
- Master Blueprint 2.0
- System Architecture & Pipeline Parts 1–8
- Shared Intelligence Core Contracts 01–12
- Canonical Contracts Pack 1.0
- Accepted P0 Architecture Decision Baseline 1.0
- P0 Detailed Contract Freeze Pack 1.0
- P0 Foundation Implementation Specification 1.0
- P0 Implementation Authorization Brief 1.0
- Artifact 06 — Implementation Readiness & Risk Register 1.0
- Artifact 07 — P0 Foundation Execution Plan & Acceptance Framework 1.0

---

# 1. Executive Summary

Artifact 08 consolidates the detailed P0 contract proposals into one review and closure framework for the next implementation-planning stage.

It makes an important distinction:

- **High-level architecture decisions:** ADR-001 through ADR-010 are already recorded as accepted.
- **Detailed contract definitions:** fields, relationships, state transitions, error semantics, authorization scope and operational values still require review.
- **Operational selections:** cloud provider, region, budget, monitoring, backup targets and workload placement remain open or deferred.
- **Implementation authorization:** remains NOT GRANTED.

This artifact is not a claim that every proposed contract is frozen. It identifies what can be treated as an accepted architectural direction, what is a proposed detailed baseline, what remains open, and what evidence is required to close each item.

## 1.1 Current verdict

**READY FOR DETAILED CONTRACT REVIEW — NOT FROZEN FOR IMPLEMENTATION.**

The next objective is to review the detailed contract groups in a controlled sequence, record explicit decisions, reconcile the Canonical Contracts Pack, and publish a versioned frozen baseline.

## 1.2 Status vocabulary

| Status | Meaning |
|---|---|
| ACCEPTED DECISION | High-level owner decision already recorded in the accepted ADR baseline |
| PROPOSED DETAIL | Concrete contract recommendation; not yet accepted as a final detailed contract |
| OPEN | Requires an explicit value, policy, owner decision or evidence |
| DEFERRED | Intentionally outside P0 or postponed |
| REPORT-BACKED | Derived from historical engineering/reconciliation reports, not a fresh inspection |
| NOT VERIFIED | No current direct evidence establishes the claim |
| FROZEN | Explicitly reviewed and approved as part of a versioned detailed contract baseline |

No item becomes FROZEN merely because it appears in this document.

---

# 2. Accepted High-Level Architecture Baseline

The following decisions are already recorded as accepted. This artifact does not reopen them unless the owner explicitly issues a superseding decision.

| ADR | Accepted direction | Current status |
|---|---|---|
| ADR-001 | UUIDv7 canonical identifiers; opaque, immutable IDs | ACCEPTED |
| ADR-002 | PostgreSQL-compatible relational database as authoritative shared-state store | ACCEPTED |
| ADR-003 | Database-backed durable queue with transactional outbox/inbox initially | ACCEPTED |
| ADR-004 | Versioned HTTP/JSON contracts with schema validation | ACCEPTED |
| ADR-005 | Unique worker identity, scoped short-lived credentials and capability authorization | ACCEPTED |
| ADR-006 | Relational artifact metadata; binaries behind object-storage abstraction | ACCEPTED |
| ADR-007 | Centralized authorization; no publishing-adapter bypass; automatic publishing disabled pending separate policy | ACCEPTED |
| ADR-008 | PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW, BLOCKED; hard blockers cannot be bypassed by ordinary approval | ACCEPTED |
| ADR-009 | Evidence-backed rights states and use-specific enforcement | ACCEPTED |
| ADR-010 | Separate lifecycle state machines for content, workflow, execution, review, approval, authorization and distribution | ACCEPTED |

## 2.1 Locked topology and operating constraints

- Hybrid deployment direction remains locked.
- Cloud control plane is intended to remain available independently of the user's PC.
- Cloud owns authoritative shared workflow and control state.
- Local worker executes local-only tasks, including existing Shorts Studio workloads, when the PC is available.
- Shorts Studio is integrated as a specialized engine, not replaced wholesale.
- Agents perform bounded work and cannot grant themselves permissions or approve their own work.
- Workers execute assigned jobs and do not own global workflow state.
- Human approval remains required for critical actions unless a separate policy is approved.
- No production generation, upload or publishing without explicit authorization.
- Existing agent ownership remains unchanged:
  - Qoder — Phase 11 engineering owner.
  - OpenCode — Phase 10 engineering/closure owner.
  - Kilo — independent read-only QA.

## 2.2 Accepted does not mean selected

The accepted PostgreSQL direction does not select a hosting provider, version, region or budget. The accepted object-storage abstraction does not select a vendor. The accepted worker credential model does not select an identity provider or token format.

Do not silently infer these choices.

---

# 3. Canonical Entity and Identity Contract

**High-level direction:** ACCEPTED  
**Detailed schema:** PROPOSED DETAIL — OWNER REVIEW REQUIRED

## 3.1 Identity rules

Accepted baseline:
- UUIDv7 for canonical IDs.
- IDs are globally unique, opaque, immutable and never reused.
- Business meaning, mutable status, platform or owner must not be encoded into IDs.
- Entity type and relationships remain explicit.
- Legacy Shorts Studio identifiers remain external/source references, not canonical global IDs.

Proposed contract rules:
1. Generate a canonical ID once at entity creation.
2. Validate UUID representation at service boundaries.
3. Do not change an entity's ID when its status or version changes.
4. Use separate version identifiers or version numbers for immutable revisions.
5. Preserve source-system IDs in explicit external-reference fields.
6. Do not use human-readable prefixes as uniqueness guarantees.

## 3.2 P0 entity inventory

| Entity | Purpose | Canonical ID field | Detailed status |
|---|---|---|---|
| Workspace | Initial owner-controlled operating boundary | workspace_id | PROPOSED |
| Brand | Brand identity and policy scope | brand_id | PROPOSED |
| ContentIdea | Uncommitted concept or opportunity | content_idea_id | PROPOSED |
| ContentItem | Canonical content identity | content_item_id | PROPOSED |
| ContentVariant | Platform/format/language or other content version | content_variant_id | PROPOSED |
| Workflow | Orchestrated business process | workflow_id | PROPOSED |
| WorkflowTask | A logical step within a workflow | task_id | PROPOSED |
| Job | Durable executable unit | job_id | PROPOSED |
| JobAttempt | One execution attempt for a job | job_attempt_id | PROPOSED |
| Worker | Registered execution identity | worker_id | PROPOSED |
| ProductionRun | One studio production execution | production_run_id | PROPOSED |
| Asset | Source or reusable media resource | asset_id | PROPOSED |
| Artifact | Immutable produced output | artifact_id | PROPOSED |
| ReviewPackage | Exact package presented for evaluation | review_package_id | PROPOSED |
| Approval | Editorial decision bound to exact reviewed versions | approval_id | PROPOSED |
| Authorization | Permission for a specific protected action | authorization_id | PROPOSED |
| DistributionRequest | Request to distribute content | distribution_request_id | PROPOSED |
| DistributionAttempt | One execution attempt for distribution | distribution_attempt_id | PROPOSED |
| Event | Durable domain/integration notification | event_id | PROPOSED |
| OutboxMessage | Event awaiting publication/dispatch | outbox_message_id | PROPOSED |
| InboxReceipt | Consumer deduplication receipt | inbox_receipt_id | PROPOSED |

## 3.3 Entity boundary rules

Proposed baseline:
- ContentIdea is not ContentItem.
- ContentItem is not ContentVariant.
- ContentVariant is not ProductionRun.
- WorkflowTask is not Job.
- Job is not JobAttempt.
- Asset is not Artifact.
- Review is not Approval.
- Approval is not Authorization.
- Authorization is not DistributionAttempt.
- Event is a notification/record, not the authoritative current state of an entity.

## 3.4 Relationship proposals requiring owner review

| Parent | Child / reference | Proposed relationship rule |
|---|---|---|
| Workspace | Brand | Workspace may contain one or more brands; initial deployment uses NEXTDECODE |
| Brand | ContentItem | Content item belongs to an explicit brand/workspace scope |
| ContentItem | ContentVariant | One item may have multiple variants |
| ContentVariant | ProductionRun | One variant may have multiple production runs |
| Workflow | WorkflowTask | Workflow contains ordered/dependent tasks |
| WorkflowTask | Job | Task may create one or more jobs, subject to contract |
| Job | JobAttempt | Job may have multiple attempts; attempt history is retained |
| Worker | JobAttempt | Attempt records the worker identity that executed it |
| ProductionRun | Artifact | Run may produce multiple immutable artifacts |
| Asset | RightsRecord | Rights evidence is scoped to asset and intended use |
| ReviewPackage | Approval | Approval binds to exact reviewed package/version references |
| Approval | Authorization | Approval may be a prerequisite, but does not itself grant authorization |
| Authorization | DistributionAttempt | Attempt must match the authorization's exact scope |
| Event | Entity reference | Event identifies the affected entity and version |

## 3.5 Required detailed schema decisions

Before freeze, review:
- required versus optional fields;
- nullability and default values;
- workspace and brand scoping;
- foreign-key and deletion behavior;
- soft deletion versus retention/deletion workflow;
- uniqueness constraints;
- external-reference shape;
- entity versioning strategy;
- timestamp and timezone conventions;
- ownership of mutable fields;
- migration and compatibility rules.

**Freeze condition:** Every P0 entity has a defined owner, identity field, required relationships, lifecycle owner and versioning rule. Unresolved fields are explicitly OPEN or DEFERRED.

---

# 4. Lifecycle and State-Transition Contract

**High-level direction:** ACCEPTED under ADR-010  
**Detailed state tables:** PROPOSED DETAIL — OWNER REVIEW REQUIRED

## 4.1 Separation requirement

Maintain distinct lifecycle state machines for:
1. Content.
2. Workflow.
3. Task.
4. Job.
5. JobAttempt / lease.
6. Worker.
7. ProductionRun.
8. Artifact.
9. Review.
10. Approval.
11. Authorization.
12. DistributionRequest / DistributionAttempt.

A single global status field must not represent all these concepts.

## 4.2 Proposed state vocabulary

The following are candidate state vocabularies for review, not a declaration that every enum has been approved.

| Domain | Candidate states | Notes |
|---|---|---|
| ContentItem | DRAFT, ACTIVE, ARCHIVED | Editorial lifecycle |
| ContentVariant | DRAFT, READY_FOR_REVIEW, APPROVED, BLOCKED, ARCHIVED | Approval is version-bound |
| Workflow | PENDING, RUNNING, WAITING, COMPLETED, FAILED, CANCELLED | Aggregate workflow lifecycle |
| WorkflowTask | BLOCKED, PENDING, READY, RUNNING, WAITING, COMPLETED, FAILED, CANCELLED | Dependency-aware |
| Job | PENDING, QUEUED, LEASED, RUNNING, RETRY_WAIT, SUCCEEDED, FAILED, CANCELLED, DEAD_LETTER | Durable execution |
| JobAttempt | CLAIMED, RUNNING, SUCCEEDED, FAILED, EXPIRED, ABANDONED | Attempt history |
| Worker | REGISTERED, ONLINE, DEGRADED, OFFLINE, REVOKED | Registry/health state |
| ProductionRun | CREATED, RUNNING, SUCCEEDED, FAILED, CANCELLED | Studio execution |
| Artifact | PENDING_TRANSFER, VERIFYING, AVAILABLE, REJECTED, EXPIRED, DELETED | Artifact availability |
| Review | PENDING, IN_PROGRESS, COMPLETED | Evaluation process |
| Approval | PENDING, APPROVED, REJECTED, REVOKED, EXPIRED | Editorial decision |
| Authorization | REQUESTED, GRANTED, DENIED, REVOKED, EXPIRED, CONSUMED | Protected-action permission |
| DistributionAttempt | PENDING, AUTHORIZED, EXECUTING, SUCCEEDED, FAILED, CANCELLED | External action attempt |

## 4.3 Transition invariants

Proposed mandatory invariants:
- Every transition is validated by the owning domain.
- Every transition records actor, timestamp, reason and correlation ID.
- Stale version updates are rejected or reconciled explicitly.
- Terminal states do not silently reopen.
- Reopening requires an explicit, audited transition rule.
- Cancellation does not erase completed artifacts or history.
- A workflow's aggregate status is derived from its tasks and policy holds.
- A job's current state does not erase prior JobAttempt records.
- Worker offline/revoked state does not imply deletion of jobs assigned previously.
- Approval applies only to the exact reviewed content/artifact versions.
- Authorization applies only to its exact action and destination scope.
- A new artifact version does not inherit approval automatically.
- Rights revocation triggers re-evaluation of future protected use.

## 4.4 Transition table format required for freeze

Each state machine must provide:

| Required field | Definition |
|---|---|
| Current state | State from which transition begins |
| Command/event | Explicit requested transition |
| Next state | Resulting state |
| Actor | User, service, worker or system process |
| Preconditions | Required entity/version/policy conditions |
| Authorization | Required permission, if any |
| Side effects | Durable records/events created |
| Failure behavior | Rejection, retry or remediation |
| Audit evidence | Required reason and correlation fields |
| Reopen policy | Whether and how terminal state may reopen |

**Freeze condition:** Full transition tables exist for all P0 state machines, including cancellation, retry, expiry, revocation, stale updates and terminal/reopen behavior.

---

# 5. Workflow, Job, Lease and Event Contract

**High-level direction:** ACCEPTED under ADR-003 and ADR-010  
**Detailed semantics:** PROPOSED DETAIL — OWNER REVIEW REQUIRED

## 5.1 Responsibility boundaries

| Component | Owns | Must not do |
|---|---|---|
| Orchestrator | Workflow/task dependencies and progression | Execute worker payloads directly |
| Scheduler | Time-based and eligibility decisions | Bypass workflow or governance |
| Durable queue | Persistent eligible work and dispatch state | Become the source of business truth |
| Worker | Execute assigned job under lease/capability | Mutate unrelated entities or self-authorize |
| Agent | Bounded reasoning/tool task | Become scheduler, queue or authorization authority |
| Control plane | Authoritative shared state and policy | Trust worker-supplied authority claims without validation |

## 5.2 Proposed minimum Job fields

- job_id
- job_type
- workflow_id
- task_id
- payload_schema_version
- payload_reference or validated payload
- required_capabilities
- priority
- eligible_at
- state
- attempt_count
- max_attempts / retry_policy_reference
- idempotency_key
- lease_owner_worker_id
- lease_expires_at
- heartbeat_at
- created_at / updated_at
- correlation_id / causation_id
- failure_code / sanitized_failure_details

Exact field names and normalization remain subject to detailed schema review.

## 5.3 Lease semantics

Proposed rules:
1. A worker claims a job through the control plane.
2. Claiming creates or advances a JobAttempt.
3. The lease is time-bounded.
4. Only the current valid lease holder may heartbeat or submit the attempt result.
5. Lease expiry makes the job eligible for controlled recovery, subject to attempt policy.
6. A stale worker cannot overwrite a newer attempt.
7. Worker revocation prevents new claims and protected artifact access.
8. Lease tokens or credentials are never logged or placed in ordinary event payloads.
9. Lease duration and heartbeat cadence are configurable by job class, but exact values remain OPEN.
10. Lease expiration is not proof that the original worker stopped; side effects must remain idempotent or reconcilable.

## 5.4 Retry semantics

Proposed rules:
- At-least-once delivery is accepted; exactly-once execution is not assumed.
- Retries are bounded.
- Retryability is determined by stable error category and operation safety.
- Validation, authentication, authorization, conflict and policy-block errors are not blindly retried.
- Transient and dependency-unavailable errors may use bounded retry with backoff.
- Integrity failures block downstream use and require investigation.
- Each retry creates or records a distinct attempt.
- Attempt history is retained.
- Terminal failure requires explicit remediation or requeue policy.
- Requeue must not erase prior failure evidence.

OPEN parameters:
- maximum attempts by job class;
- backoff algorithm and ceiling;
- jitter policy;
- dead-letter handling;
- manual requeue authority;
- lease duration and heartbeat cadence.

## 5.5 Idempotency

Proposed rules:
- State-changing commands carry an idempotency key.
- Same key and same canonical payload returns the original logical result.
- Same key with a different payload returns a conflict.
- Idempotency scope and retention period must be explicit.
- Idempotency keys are not substitutes for entity IDs or correlation IDs.
- External side effects require provider-side idempotency where supported, or a reconciliation strategy.

## 5.6 Transactional outbox/inbox

Accepted direction: use transactional outbox/inbox semantics initially.

Proposed rules:
- Business state and its outbox record commit atomically.
- A rolled-back transaction must not emit an orphan event.
- Outbox delivery may be repeated.
- Consumer inbox receipt/deduplication prevents duplicate logical processing.
- Consumers validate schema version and ownership before applying effects.
- Pending outbox work is recoverable after restart.
- Event payloads carry references and metadata, not large media binaries.
- Events notify; authoritative state remains in the owning domain.

OPEN parameters:
- outbox/inbox retention;
- replay and purge policy;
- delivery ordering guarantees;
- poison-message handling;
- database claim/locking strategy.

**Freeze condition:** Job/attempt lifecycle, lease ownership, retry policy, idempotency semantics, outbox/inbox behavior and recovery tests are accepted in writing.

---

# 6. Worker Identity and Capability Contract

**High-level direction:** ACCEPTED under ADR-005  
**Detailed security contract:** PROPOSED DETAIL — OWNER REVIEW REQUIRED

## 6.1 Accepted requirements

- Each worker has a unique machine identity.
- Human and machine identities remain separate.
- Credentials are scoped, short-lived/renewable and revocable.
- Job execution is capability-authorized.
- Worker credentials are not user login credentials.

## 6.2 Proposed Worker record

- worker_id
- machine_identity_reference
- status
- software_version
- contract_version
- declared_capabilities
- environment_label (local/remote and execution context)
- last_heartbeat_at
- registered_at
- revoked_at
- credential_status
- metadata subject to minimization

## 6.3 Capability contract

A capability is a typed permission to execute a job class, not an unrestricted role.

Illustrative capability names:
- `research.fetch`
- `script.generate`
- `visuals.prepare`
- `shorts.render.local`
- `artifact.upload`
- `artifact.download`
- `quality.validate`

Rules:
- A job declares required capabilities.
- Worker must possess every required capability.
- Capability claims are checked server-side.
- Sensitive capabilities require explicit server approval.
- Local-only capability is eligible only while the local worker is online and healthy.
- Cloud workflow remains durable while local-only capability is unavailable.
- Capability catalogue is versioned and aligned with approved adapter boundaries.

## 6.4 Credential contract

Proposed rules:
- Credential audience is the control plane or explicitly approved service.
- Credential scope is limited to required worker actions.
- Credential expiry is enforced.
- Revocation prevents new claims and new protected artifact access.
- Renewal/reissue requires proof of worker identity.
- Human session tokens are never reused as machine credentials.
- Credentials are excluded from job payloads, logs, traces and error messages.
- Local secret storage method must be selected and reviewed before implementation.

OPEN:
- credential issuer and protocol;
- token format;
- renewal cadence;
- revocation propagation target;
- local secret storage mechanism;
- worker enrollment and recovery procedure;
- machine identity attestation requirements, if any.

**Freeze condition:** Worker enrollment, authentication, capability checking, heartbeat, revocation and secret-handling rules are detailed and testable.

---

# 7. Asset, Artifact, Manifest and Transfer Contract

**High-level direction:** ACCEPTED under ADR-006  
**Detailed schema and storage policy:** PROPOSED DETAIL — OWNER REVIEW REQUIRED

## 7.1 Concept boundaries

- **Asset:** Source or reusable media/resource with provenance and rights context.
- **Artifact:** Produced output or durable file generated/processed by a workflow or studio.
- **Manifest:** Structured declaration of a production's inputs, outputs, versions, settings and lineage.
- **Storage object:** Physical binary location; not an authorization grant.

## 7.2 Proposed Artifact metadata

- artifact_id
- immutable version reference
- content_item_id / content_variant_id
- workflow_id / task_id / production_run_id
- artifact_type
- media_type
- byte_size
- checksum_algorithm
- checksum_value
- producer identity
- created_at
- storage_object_reference
- validation_state
- provenance references
- rights references
- retention_class

## 7.3 Immutability rules

- Registered artifact content is immutable.
- New output creates a new version.
- Corrections affecting meaning are audited and versioned.
- Approval binds to exact artifact ID/version/checksum.
- Replacing a file at the same path must not silently replace an approved artifact.
- Prior artifact versions remain traceable unless a separate retention/deletion policy applies.

## 7.4 Transfer lifecycle

Proposed upload sequence:
1. Request upload authorization.
2. Validate worker/job scope.
3. Transfer binary to storage.
4. Verify byte size and checksum.
5. Register artifact metadata.
6. Mark artifact available only after validation.

Proposed download sequence:
1. Request artifact access.
2. Validate worker/job scope and policy.
3. Issue short-lived scoped transfer authorization.
4. Download.
5. Verify checksum before use.

Rules:
- Storage locator is not authorization.
- Transfer grants are scoped and time-limited.
- Checksum mismatch blocks downstream use.
- Interrupted transfer can be retried safely.
- Temporary files are not durable registered artifacts.
- Large binaries do not travel in ordinary JSON messages.

OPEN:
- object-storage provider and region;
- upload/download protocol;
- maximum file sizes and multipart strategy;
- retention classes and lifecycle rules;
- encryption and key management details;
- deletion and legal-hold behavior;
- manifest schema and compatibility.

## 7.5 Manifest minimum contents

Proposed manifest should identify:
- manifest ID and schema version;
- content item and variant;
- workflow and production run;
- input asset/artifact references and versions;
- output artifact references and checksums;
- producer/tool version;
- relevant non-secret settings/configuration references;
- provenance and rights references;
- creation timestamp;
- validation status.

Secrets, credentials and signed transfer URLs must never be embedded in a manifest.

**Freeze condition:** Artifact immutability, version binding, transfer authorization, integrity verification and manifest lineage rules are accepted.

---

# 8. Quality and Rights Policy Interfaces

**High-level direction:** ACCEPTED under ADR-008 and ADR-009  
**Detailed catalogue and exception rules:** PROPOSED DETAIL / OPEN

## 8.1 Quality outcomes

Accepted outcomes:
- `PASS`
- `PASS_WITH_WARNINGS`
- `NEEDS_REVIEW`
- `BLOCKED`

Rules:
- Hard blockers are explicit.
- Ordinary editorial approval cannot override hard blockers.
- Numeric scores do not replace hard-gate outcomes.
- A result records policy version, checks, severity, evidence and remediation.
- Exact checks and thresholds remain open.

## 8.2 Rights states

Accepted states:
- `CLEARED`
- `RESTRICTED`
- `PENDING_VERIFICATION`
- `PROHIBITED`
- `UNKNOWN`

Rules:
- Rights are evaluated for intended use, not merely for an asset in isolation.
- UNKNOWN and PENDING_VERIFICATION block affected protected use under the accepted baseline.
- PROHIBITED blocks affected use.
- RESTRICTED requires all applicable conditions to be satisfied.
- Evidence should cover relevant platform, territory and commercial-use scope.
- Derived assets retain provenance links.
- Rights expiry or revocation triggers re-evaluation of future protected use.
- Ordinary editorial approval cannot override prohibited rights.

## 8.3 Proposed policy result fields

- result_id
- subject_type / subject_id
- artifact references and exact versions
- policy_version_id
- outcome
- check results
- severity
- evidence references
- remediation instructions
- evaluated_at
- evaluator identity
- correlation_id

## 8.4 Open policy details

- exact quality check catalogue;
- severity mapping and thresholds;
- rights evidence taxonomy;
- who is permitted to verify rights;
- exception workflow, if any;
- rights revocation propagation;
- retention of evidence;
- policy version activation and rollback;
- treatment of historical published outputs.

**Freeze condition:** The interfaces and hard-block semantics are accepted. Open catalogue details are either resolved or explicitly deferred with owner-accepted risk.

---

# 9. Review, Approval and Authorization Contract

**High-level direction:** ACCEPTED under ADR-007  
**Detailed request/decision semantics:** PROPOSED DETAIL — OWNER REVIEW REQUIRED

## 9.1 Separation of concepts

| Concept | Meaning |
|---|---|
| Review | Evaluation of content, quality, rights or policy |
| Approval | Editorial decision about an exact reviewed version |
| Authorization | Permission for a specific action, target and time window |
| Execution | Adapter/worker performs the authorized action |

Approval alone is not permission to publish.

## 9.2 Proposed authorization request

Required logical fields:
- action (e.g. `distribution.publish`);
- content_variant_id;
- exact artifact references and checksums;
- destination platform and account reference;
- requested time window;
- approval reference, where required;
- quality result reference;
- rights evaluation reference;
- policy version;
- requester identity;
- correlation_id.

## 9.3 Proposed authorization decision

Required logical fields:
- authorization_id, if granted;
- `GRANTED` or `DENIED`;
- reason codes;
- exact action and scope;
- content/variant/artifact version references;
- destination platform/account;
- not-before and expiry;
- policy version;
- decision timestamp;
- decision authority;
- correlation_id.

## 9.4 Enforcement rules

- Deny by default.
- Missing or mismatched references are denied.
- Expired or revoked authorization is denied.
- Authorization for a different artifact hash is denied.
- Authorization for a different destination or action is denied.
- Emergency pause denies new protected actions.
- Adapter cannot self-authorize.
- Ordinary editorial approval cannot override quality/rights hard blocks.
- Automatic publishing remains disabled until a separate owner-approved policy exists.
- Dry-run cannot silently become live execution.
- Every decision and denial is auditable.

## 9.5 Open authorization details

- authorization consumption semantics (single-use vs bounded/reusable);
- expiry defaults;
- policy version activation;
- emergency pause ownership and override process;
- platform/account reference model;
- platform-specific privacy defaults;
- long-form publishing privacy behavior;
- conditional automatic publishing eligibility, if ever considered.

The previously discussed 12-hour Shorts and 48-hour long-form approval windows are examples only, not approved policy.

**Freeze condition:** Authorization scope, exact-version binding, denial semantics, expiry/revocation, emergency pause and audit requirements are accepted. Live platform integration remains separately unauthorized.

---

# 10. Error, Audit and Correlation Contract

**Status:** PROPOSED DETAIL — OWNER REVIEW REQUIRED

## 10.1 Proposed error categories

| Category | Examples | Retry guidance |
|---|---|---|
| VALIDATION | Invalid schema, missing required field | No automatic retry |
| AUTHENTICATION | Invalid/expired worker credential | Re-authenticate; no blind retry |
| AUTHORIZATION | Capability or action denied | No automatic retry |
| CONFLICT | Stale version, idempotency payload mismatch | Reconcile; no blind retry |
| NOT_FOUND | Unknown entity/artifact | Usually no retry |
| RATE_LIMITED | Provider/API throttling | Retry per backoff/Retry-After |
| TRANSIENT | Temporary network/service failure | Bounded retry |
| DEPENDENCY_UNAVAILABLE | Database/storage/provider unavailable | Bounded retry and alert |
| INTEGRITY | Checksum mismatch, invalid manifest | Block; investigate |
| POLICY_BLOCKED | Rights/quality/safety hard gate | No automatic retry until remediation |
| INTERNAL | Unexpected failure | Bounded retry only when safe |

Proposed error response fields:
- stable code;
- safe message;
- category;
- retryable;
- correlation_id;
- optional sanitized details;
- optional retry_after.

## 10.2 Audit event fields

Critical actions should record:
- event ID;
- actor type and actor ID;
- action;
- subject entity type/ID;
- before/after state or decision;
- timestamp;
- correlation and causation IDs;
- policy version where relevant;
- reason code;
- source service/worker;
- sanitized metadata.

Critical governance and lifecycle audit records should be append-only.

## 10.3 Prohibited log content

Do not log:
- raw credentials;
- lease bearer tokens;
- signed storage URLs;
- private keys;
- unredacted secrets;
- unnecessary personal data.

## 10.4 Correlation conventions

A correlation ID follows one logical end-to-end request/workflow across:
- API request;
- workflow;
- task;
- job;
- worker attempt;
- artifact registration;
- review/approval;
- authorization;
- distribution attempt.

Causation ID identifies the immediate event/request that caused a subsequent event.

Correlation IDs do not replace entity IDs or idempotency keys.

OPEN:
- audit retention;
- audit export/access policy;
- tamper-evidence requirements;
- event ordering expectations;
- trace/log/metric provider and retention.

**Freeze condition:** Stable error codes, safe retry rules, required audit fields, secret redaction and correlation propagation are accepted.

---

# 11. Operational and Infrastructure Decisions — OPEN / DEFERRED

These items are not silently selected by the accepted ADRs.

| Area | Open decision | Status |
|---|---|---|
| Cloud | Provider and region | OPEN |
| Database hosting | PostgreSQL provider/version/region | OPEN |
| Migrations | Migration tool and rollout policy | OPEN |
| Queue | Dedicated broker adoption, if workload evidence later justifies it | DEFERRED |
| Storage | Object-storage provider and region | OPEN |
| Identity | Credential issuer and token format | OPEN |
| Monitoring | Metrics/logging/tracing provider | OPEN |
| Alerting | Routing and escalation policy | OPEN |
| Recovery | RPO/RTO targets and backup retention | OPEN |
| Workload placement | Exact local versus remote capability matrix | OPEN |
| Budget | Infrastructure and operating-cost ceiling | OPEN |
| Teams/SaaS | Multi-user tenancy and billing | DEFERRED |
| Vector search | Vector database and advanced semantic search | DEFERRED |
| Automatic publishing | Eligibility, frequency and conditional policy | DEFERRED pending separate approval |

Operational choices must be made from requirements, cost and risk evidence. Do not select vendors merely because they appear in examples or existing code.

---

# 12. Detailed Contract Review and Freeze Matrix

This matrix is the owner review checklist for the detailed baseline.

| ID | Contract group | Current status | Required owner action |
|---|---|---|---|
| CF-01 | Canonical entity glossary | PROPOSED | Review entity boundaries |
| CF-02 | Entity relationships and ownership | PROPOSED | Accept/amend relationships |
| CF-03 | Required fields and nullability | OPEN | Review schema details |
| CF-04 | ID and versioning rules | Direction accepted; detail proposed | Confirm version semantics |
| CF-05 | Lifecycle state vocabularies | PROPOSED | Review each state machine |
| CF-06 | Transition/precondition tables | OPEN | Approve transition behavior |
| CF-07 | Terminal, cancellation and reopen rules | OPEN | Decide edge cases |
| CF-08 | Job and JobAttempt contract | PROPOSED | Review lifecycle and fields |
| CF-09 | Lease and heartbeat semantics | PROPOSED | Accept rules; choose values |
| CF-10 | Retry and dead-letter behavior | OPEN | Decide policy parameters |
| CF-11 | Idempotency contract | PROPOSED | Accept scope and conflict behavior |
| CF-12 | Outbox/inbox semantics | PROPOSED | Accept retention/replay details |
| CF-13 | Worker identity and enrollment | PROPOSED | Review security detail |
| CF-14 | Capability catalogue | OPEN | Approve P0 capabilities |
| CF-15 | Credential issuer/token/secret storage | OPEN | Select after security review |
| CF-16 | Artifact metadata/versioning | PROPOSED | Review required fields |
| CF-17 | Transfer authorization | PROPOSED | Review protocol and scope |
| CF-18 | Manifest schema | OPEN | Approve lineage fields |
| CF-19 | Quality result interface | PROPOSED | Accept interface; define checks |
| CF-20 | Rights evidence and exception rules | OPEN | Define evidence/verification policy |
| CF-21 | Authorization request/decision | PROPOSED | Accept exact scope and denial rules |
| CF-22 | Error taxonomy | PROPOSED | Accept stable categories |
| CF-23 | Audit and correlation | PROPOSED | Accept fields and retention policy |
| CF-24 | Operational providers/budget | OPEN | Defer pending costed comparison |
| CF-25 | Contract reconciliation across artifacts | OPEN | Update canonical pack and architecture references |

## 12.1 Decision recording rule

For each CF item, record one of:
- ACCEPT;
- ACCEPT WITH AMENDMENT;
- REJECT;
- DEFER.

Record:
- decision ID;
- exact contract/version;
- outcome;
- amendment or condition;
- accepted risk if deferred;
- decision owner;
- decision date.

Do not backfill approval based on silence, prior discussion or inclusion in a draft.

---

# 13. Contract Freeze Criteria

The detailed contract baseline may be marked **FROZEN** only after all applicable criteria are met.

## Gate A — Domain and identity
- [ ] Entity glossary reviewed.
- [ ] Ownership and relationships reviewed.
- [ ] Required fields and nullability reviewed.
- [ ] Identity and versioning rules accepted.
- [ ] Legacy Shorts Studio reference treatment confirmed.

## Gate B — Lifecycle and execution
- [ ] All P0 state machines have transition tables.
- [ ] Preconditions and actor permissions are explicit.
- [ ] Cancellation, expiry and terminal behavior defined.
- [ ] Reopen behavior defined or explicitly prohibited.
- [ ] Job, attempt, lease and retry semantics accepted.
- [ ] Idempotency and event delivery semantics accepted.

## Gate C — Worker and artifact
- [ ] Worker enrollment and identity rules accepted.
- [ ] Capability contract accepted.
- [ ] Credential lifecycle and revocation requirements accepted.
- [ ] Artifact metadata and immutable versioning accepted.
- [ ] Transfer authorization and checksum requirements accepted.
- [ ] Manifest lineage requirements accepted.

## Gate D — Governance and observability
- [ ] Quality result interface accepted.
- [ ] Rights state and evidence rules accepted.
- [ ] Authorization request/decision contract accepted.
- [ ] Exact-version binding and deny-by-default behavior accepted.
- [ ] Error taxonomy and retry guidance accepted.
- [ ] Audit fields, redaction and correlation conventions accepted.

## Gate E — Reconciliation and publication
- [ ] Open details decided or explicitly deferred with accepted risk.
- [ ] Canonical Contracts Pack updated to match this baseline.
- [ ] P0 Foundation Implementation Specification reconciled.
- [ ] Architecture Parts 1–8 conflicts resolved or recorded.
- [ ] Artifact 06 and Artifact 07 status references remain consistent.
- [ ] Versioned contract-freeze decision recorded.

A frozen contract baseline does not authorize repository inspection, implementation, deployment or production actions.

---

# 14. Coding-Agent Handoff Requirements

This section is intended to make the eventual frozen contract useful to coding agents without granting them permission to act now.

When implementation is separately authorized, the coding-agent handoff must include:

1. The frozen contract baseline version and checksum/reference.
2. The accepted ADR baseline 1.0.
3. P0 scope and explicit exclusions.
4. Exact entity schemas and relationship rules.
5. State-transition tables and invalid-transition behavior.
6. API/event envelope schemas and compatibility rules.
7. Job, lease, retry, idempotency and outbox/inbox semantics.
8. Worker identity, capability and credential requirements.
9. Artifact, manifest and transfer contracts.
10. Quality, rights and authorization rules.
11. Error taxonomy, audit and correlation requirements.
12. Acceptance test IDs and expected outcomes.
13. Exact repository/file ownership boundaries.
14. Approved commands, environment and dependency permissions.
15. Preservation, rollback and stop conditions.
16. Explicitly authorized work packages and excluded work.

## 14.1 Coding-agent instruction boundary

A coding agent must:
- implement only the approved frozen contract version;
- report deviations rather than silently changing contracts;
- stop when a required field, state or policy is undefined;
- never infer authorization from an approval record;
- never enable automatic publishing;
- never alter agent ownership;
- never perform unapproved Git operations;
- never install dependencies or alter environments without permission;
- never deploy or spend money without separate authorization;
- provide exact files changed and reproducible test evidence.

**This handoff section is a future requirement, not an instruction to start coding now.**

---

# 15. Reconciliation Notes Against Earlier Artifacts

1. The Accepted P0 Architecture Decision Baseline records ADR-001 through ADR-010 as accepted. Any older draft that still labels those high-level choices pending is superseded by that explicit decision record.
2. The P0 Detailed Contract Freeze Pack remains a proposed detailed baseline. Its fields, transition tables and implementation parameters must not be treated as approved merely because the high-level ADRs are accepted.
3. Artifact 06 remains the readiness/risk snapshot. Its overall implementation verdict remains unchanged.
4. Artifact 07 remains the execution plan and acceptance framework. Its tests are proposed acceptance criteria, not executed test evidence.
5. This Artifact 08 consolidates the contract-review and closure process. It does not claim that the detailed baseline is frozen.

---

# 16. Final Recommendation

Proceed in this order:

1. Review CF-01 through CF-07: entity, relationship, identity and lifecycle details.
2. Review CF-08 through CF-12: job, lease, retry, idempotency and event semantics.
3. Review CF-13 through CF-18: worker, capability, artifact and manifest contracts.
4. Review CF-19 through CF-23: quality, rights, authorization, error and audit contracts.
5. Decide or explicitly defer CF-24 operational selections.
6. Reconcile all accepted changes into a single versioned canonical contract baseline.
7. Prepare the coding-agent handoff only after the baseline is frozen.
8. Seek separate authorization for read-only repository baseline inspection.
9. Seek separate, bounded implementation authorization only after readiness gates are satisfied.

**Final decision: DETAILED CONTRACT REVIEW BASELINE CONSOLIDATED — CONTRACT FREEZE PENDING OWNER REVIEW — IMPLEMENTATION NOT AUTHORIZED.**

---

# 17. Source Register

1. NEXTDECODE Master Blueprint 2.0.
2. System Architecture & Pipeline Parts 1–8.
3. Shared Intelligence Core Contracts 01–12.
4. NEXTDECODE Canonical Contracts Pack 1.0.
5. NEXTDECODE Accepted P0 Architecture Decision Baseline 1.0.
6. NEXTDECODE P0 Detailed Contract Freeze Pack 1.0.
7. NEXTDECODE P0 Foundation Implementation Specification 1.0.
8. NEXTDECODE P0 Implementation Authorization Brief 1.0.
9. Artifact 06 — Implementation Readiness & Risk Register 1.0.
10. Artifact 07 — P0 Foundation Execution Plan & Acceptance Framework 1.0.

---

**END OF ARTIFACT 08**

**Document status:** Consolidated contract-review baseline — owner review required  
**ADR-001 through ADR-010:** ACCEPTED  
**Detailed contract freeze:** PENDING  
**Open operational decisions:** TRACKED  
**Repository inspection:** NOT AUTHORIZED  
**Git operations:** NOT AUTHORIZED  
**Code/configuration changes:** NOT AUTHORIZED  
**Implementation:** NOT AUTHORIZED  
**Deployment / production actions:** NOT AUTHORIZED
