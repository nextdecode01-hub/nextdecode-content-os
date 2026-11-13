# NEXTDECODE --- P0 Consolidated Contract Appendix

**Document ID:** `NEXTDECODE_P0_Consolidated_Contract_Appendix_0.1`\
**Version:** 0.1\
**Date:** 1 November 2026\
**Status:** CONSOLIDATED CONTRACT APPENDIX --- DESIGN CANDIDATE / OWNER
REVIEW REQUIRED\
**Scope:** WP-1 through WP-6 logical contracts and cross-package
interfaces\
**Detailed contract freeze:** NOT GRANTED\
**Implementation authorization:** NOT GRANTED

------------------------------------------------------------------------

## 1. Purpose and authority

This appendix consolidates the logical contract boundaries needed to
make the NEXTDECODE P0 foundation internally consistent.

It is based on the current P0 design candidates: - WP-1 --- Canonical
Domain and Persistence, v0.3. - WP-2 --- Durable Job and Workflow
Execution, v0.1. - WP-3 --- Worker Registry and Contract Boundary,
v0.1. - WP-4 --- Artifact Registration, Storage and Transfer, v0.1. -
WP-5 --- Governance, Quality, Rights and Authorization, v0.1. - WP-6 ---
Vertical-Slice Integration, Recovery and Validation, v0.1. - The
accepted ADR-001--ADR-010 and CF-01--CF-24 decisions. - The canonical
data dictionary, API/Event Contract Standard and Unified Lifecycle/State
Transition Standard.

This is a logical contract appendix, not SQL DDL, an OpenAPI
specification, executable schemas, a migration plan, a provider
selection, or implementation authorization.

### Status labels

-   **ACCEPTED BASELINE:** already accepted ADR/CF decision; carried
    forward.
-   **SOURCE-DEFINED:** required by an authoritative project source.
-   **PROPOSED:** conservative candidate detail; not formally accepted.
-   **OPEN:** requires further specification or owner decision.
-   **DEFERRED:** intentionally postponed where abstraction preserves
    safety.
-   **NOT VERIFIED:** no current implementation or independent test
    evidence is claimed.

Do not interpret a proposed state, field, envelope or example as frozen
merely because it appears in this appendix.

## 2. Cross-contract invariants

The following invariants apply across all P0 packages:

1.  Every canonical entity has one authoritative owning domain.
2.  Canonical IDs are immutable UUIDv7 values and are never reused.
3.  Entity identity, content/version identity and schema version are
    distinct.
4.  Typed references do not grant access, ownership, approval or
    authorization.
5.  Only the owning domain commits its authoritative state transitions.
6.  Queries are read-only; commands request changes; events report
    committed facts.
7.  Events and transition history are immutable; corrections create
    attributable new records.
8.  Workspace scope is explicit; cross-workspace access is rejected
    unless a separately approved mechanism permits it.
9.  QA, rights, review, approval, authorization, execution and
    distribution outcome are distinct.
10. Unknown, missing or ambiguous rights, approval or authorization
    never grant protected permission.
11. Hard QA and policy blockers cannot be bypassed by ordinary approval
    or retry.
12. Workers execute bounded assignments and cannot self-grant
    permissions.
13. Queue delivery is at-least-once; idempotency protects logical
    effects.
14. Artifact versions are immutable and integrity checked; repair
    creates a new version.
15. Review and approval are attributable and bound to exact versions and
    scope.
16. Automatic public publishing remains disabled.
17. Existing Shorts Studio remains a specialised engine behind a bounded
    adapter.
18. Local-only work waits safely when the required local worker is
    unavailable.
19. Hybrid control-plane direction remains architectural; no cloud
    provider or deployment is selected.
20. Development remains local-first/free-first; no paid services without
    explicit approval.

## 3. Canonical reference and identity contracts --- WP-1

### 3.1 Canonical reference envelope

**PROPOSED logical envelope:**

  -----------------------------------------------------------------------
  Field                   Meaning                 Requirement
  ----------------------- ----------------------- -----------------------
  `entity_type`           Canonical entity type   Required
                          discriminator           

  `entity_id`             Immutable canonical     Required
                          UUIDv7                  

  `workspace_id`          Workspace isolation     Required for
                          scope                   workspace-scoped
                                                  entities

  `entity_version_id`     Exact immutable         Required for
                          version, where          version-bound
                          applicable              operations

  `schema_version`        Version of the          Required
                          serialized contract     
  -----------------------------------------------------------------------

Rules: - A reference is not a permission. - The referenced owning domain
validates entity type, existence, workspace scope and version. -
Cross-workspace references fail closed unless a separately authorized
sharing contract applies. - Polymorphic references require owner-side
target validation.

### 3.2 Core logical entities

The following are the minimum logical records carried forward from WP-1.
They are not a final physical schema.

  ------------------------------------------------------------------------------------
  Entity                  Logical purpose                      Owning boundary
  ----------------------- ------------------------------------ -----------------------
  Workspace               Top-level isolation boundary         Workspace / shared data
                                                               model

  Brand reference         Typed link to brand-owned            Brand & Editorial
                          configuration                        Intelligence

  ContentItem             Shared editorial identity            Content / editorial
                                                               domain

  ContentVersion          Immutable version of editorial       Content / editorial
                          content                              domain

  ContentVariant          Format/platform/language/treatment   Content / editorial
                          derivative                           domain

  Relationship            Typed, versioned relationship        Relationship / shared
                          between entities                     data model

  Workflow                Orchestration definition/run         Orchestration
                          boundary as specified by WP-1/WP-2   

  WorkflowTask            A bounded unit in a workflow with    Orchestration
                          explicit dependencies                

  Artifact                Stable logical output record         Artifact & Asset
                                                               Management

  ArtifactVersion         Immutable exact bytes/content        Artifact & Asset
                          version                              Management

  StudioProduction        Production/run record referencing    Multiformat Creation
                          content, workflow and artifacts      

  ExternalReference       Namespaced reference to a legacy or  Owning domain /
                          external identifier                  integration boundary
  ------------------------------------------------------------------------------------

### 3.3 Content identity rules

**ACCEPTED BASELINE --- CF-01:** - `ContentItem` is the shared editorial
identity. - `ContentVariant` is a format/platform/language/treatment
derivative. - `ContentVersion` identity is distinct from entity identity
and schema version. - `ContentIdea` remains distinct from `ContentItem`;
origin linkage is explicit. - Existing Shorts Studio IDs remain
namespaced external/legacy references and do not become competing
canonical IDs.

**OPEN:** exact field nullability, uniqueness constraints, foreign keys,
deletion behavior, version sequencing and transition tables must be
completed in the canonical schema appendix before freeze.

### 3.4 Artifact identity rules

-   `Artifact` is the stable logical record.
-   `ArtifactVersion` identifies exact immutable bytes/content.
-   A material change creates a new `ArtifactVersion`; existing versions
    are never overwritten.
-   `Asset` and `Artifact` remain distinct concepts.
-   `StudioProduction` references exact artifacts; it does not become
    the artifact owner.

## 4. Workflow, job and execution contracts --- WP-2

### 4.1 Separate concepts

  -----------------------------------------------------------------------
  Concept                             Responsibility
  ----------------------------------- -----------------------------------
  Workflow definition                 Versioned description of a process

  Workflow run                        One execution of a pinned workflow
                                      definition

  Workflow task                       Dependency-aware unit within a
                                      workflow run

  Job                                 Durable logical unit eligible for
                                      worker execution

  Job attempt                         One attributable execution attempt
                                      for a job

  Lease                               Time-bounded authority for a worker
                                      to act on an assignment

  Queue message                       Delivery mechanism for eligible
                                      work

  Command                             Request for a state change

  Domain event                        Immutable fact that an owning
                                      domain committed a change

  Outbox record                       Durable event awaiting delivery

  Inbox receipt                       Durable record used to deduplicate
                                      consumed messages
  -----------------------------------------------------------------------

Orchestration coordinates dependencies; scheduling determines
eligibility; workers execute bounded assignments. These responsibilities
must not collapse into one component.

### 4.2 Candidate job/attempt model

**PROPOSED logical fields:**

  -----------------------------------------------------------------------
  Record                              Candidate fields
  ----------------------------------- -----------------------------------
  Job                                 `job_id`, `workspace_id`,
                                      `job_type`, `job_schema_version`,
                                      `subject_ref`, `workflow_run_ref`,
                                      `task_ref`, `input_refs`,
                                      `required_capabilities`,
                                      `job_state`, `priority_class`,
                                      `idempotency_scope_ref`,
                                      `created_at`, `updated_at`

  JobAttempt                          `attempt_id`, `job_id`,
                                      `attempt_number`, `worker_id`,
                                      `lease_generation`,
                                      `attempt_state`, `started_at`,
                                      `heartbeat_at`, `finished_at`,
                                      `outcome`, `error_ref`,
                                      `output_refs`, `correlation_id`

  Lease                               `lease_id`, `job_id`, `attempt_id`,
                                      `worker_id`, `fencing_generation`,
                                      `issued_at`, `expires_at`,
                                      `last_heartbeat_at`, `lease_state`
  -----------------------------------------------------------------------

These are conceptual fields. Exact names, constraints, indexes and
nullability remain OPEN.

### 4.3 Candidate state model

The following labels are a proposed vocabulary, not an accepted final
enum:

-   Job: `PENDING`, `ELIGIBLE`, `LEASED`, `RUNNING`, `SUCCEEDED`,
    `FAILED`, `CANCELLED`, `BLOCKED`.
-   Attempt: `CREATED`, `CLAIMED`, `RUNNING`, `SUCCEEDED`, `FAILED`,
    `LOST`, `CANCELLED`, `REJECTED_STALE`.
-   Lease: `ACTIVE`, `EXPIRED`, `RELEASED`, `REVOKED`.

Required semantics: - A retry creates a new attempt identity while
preserving the logical job identity. - One authoritative active lease
exists per job. - Lease ownership is checked against the authoritative
attempt and fencing generation. - A stale worker cannot commit after a
newer attempt has taken authority. - Lease expiry makes work eligible
for recovery only after approved expiry/reconciliation rules. - Workflow
completion is distinct from job completion. - Cancellation, terminal
outcomes, compensation and remediation need explicit transition
definitions before freeze.

### 4.4 Claim, heartbeat and completion

**PROPOSED claim sequence:** 1. Worker authenticates. 2. Control plane
verifies trust, credential, capability, availability and authorization.
3. Scheduler selects eligible work. 4. Claim is made atomically against
current job state. 5. A new attempt and lease/fencing generation are
recorded. 6. Assignment envelope is returned. 7. Worker heartbeats
against the current lease. 8. Completion is accepted only if worker,
attempt, lease and fencing generation remain current. 9. Outputs are
registered through the artifact contract; workflow progression is
committed by its owning domain.

### 4.5 Failure and retry semantics

Conceptual failure classes from WP-2: - `TRANSIENT` - `PERMANENT` -
`POLICY_DENIED` - `CAPABILITY_UNAVAILABLE` - `WORKER_LOST` -
`UNKNOWN_OUTCOME` - `CANCELLED`

Recommended handling: - Retry only explicitly classified transient
failures and approved worker-loss cases. - Policy denial is not
retryable to obtain a different authorization outcome. - Ambiguous
external effects require reconciliation before retry. - Every attempt
retains attributable outcome and structured failure evidence. - Numeric
attempt limits, backoff, jitter, dead-letter handling and manual requeue
authority remain OPEN.

### 4.6 Idempotency

Accepted direction: - Same idempotency key plus same canonical payload
returns the original logical result. - Same key plus different canonical
payload is a conflict. - Idempotency keys are not entity IDs, job IDs,
attempt IDs or correlation IDs. - Event consumers deduplicate repeated
delivery. - External effects use provider idempotency where supported;
otherwise reconciliation is required.

OPEN: key format, scope granularity, canonical payload comparison,
retention, expiry behavior and provider reconciliation contract.

### 4.7 Outbox/inbox

Accepted direction: - Domain state and corresponding outbox record
commit atomically. - A rolled-back transaction emits no event. -
Delivery may repeat. - Inbox deduplication prevents duplicate logical
processing. - Restart recovery and poison-message handling must be
specified. - Event references are not binary artifact payloads.

OPEN: ordering scope, retention, replay/purge authority, poison handling
and database claim strategy.

## 5. Worker registry and trust contracts --- WP-3

### 5.1 Responsibility boundary

**Control plane owns:** - Canonical worker identity and registration. -
Trust/enrollment decisions. - Capability verification and approval. -
Assignment eligibility and authorization. - Credential issuance policy
and revocation. - Assignment records, lifecycle and audit history.

**Worker owns:** - Local execution environment and reported health. -
Capability declarations and evidence. - Authentication to control
plane. - Execution of valid bounded assignments. - Heartbeats and lease
renewal. - Attributable completion/failure reports. - Secure handling of
temporary execution data.

A worker must not self-assign arbitrary jobs, self-grant capabilities,
alter global workflow state outside its authority, reuse human
credentials or access unrelated files/secrets/artifacts.

### 5.2 Candidate worker record

  -----------------------------------------------------------------------
  Field                               Meaning
  ----------------------------------- -----------------------------------
  `worker_id`                         Canonical immutable worker identity

  `machine_identity_reference`        Verified machine identity evidence
                                      reference

  `environment_type`                  Local or remote execution context

  `worker_status`                     Worker registration/trust lifecycle

  `software_version`                  Installed worker version

  `contract_version`                  Supported worker contract version

  `declared_capabilities`             Worker claims

  `verified_capabilities`             Independently verified capabilities

  `approved_capabilities`             Capabilities approved for
                                      eligibility

  `last_heartbeat_at`                 Last accepted heartbeat

  `credential_status`                 Credential lifecycle status

  `registered_at` / `revoked_at`      Lifecycle timestamps

  `metadata`                          Minimized non-sensitive operational
                                      metadata
  -----------------------------------------------------------------------

Hostname is an attribute/reference, never canonical worker identity.

### 5.3 Capability facts

These must remain separate: 1. **Declared:** what the worker claims. 2.
**Verified:** what evidence confirms it can do. 3. **Available:** what
it can do now, given health/load/resources. 4. **Authorized:** what it
may do for a particular assignment.

Capability declarations never grant permission. The capability catalogue
and verification protocol remain OPEN.

### 5.4 Enrollment, credentials and isolation

Accepted direction: - Credentials are unique, scoped,
short-lived/renewable and revocable. - Worker credentials are separate
from human login credentials. - Local and remote workers use the same
trust boundary. - Filesystem, network, credentials, artifacts and
resources are scoped. - Admin, production, QA and publishing permissions
remain separate.

OPEN: - Enrollment and machine identity proof. - Credential
issuer/protocol/token format/rotation. - Revocation propagation
target. - Local secret-storage mechanism. - Isolation technology and
threat model. - Numerical resource limits by job class. - Revocation
behavior for active jobs.

Local-only work waits safely if the required local worker is
unavailable. Reconnection requires re-authentication and refreshed
eligibility; it must not duplicate completed work.

## 6. Artifact registration, integrity and transfer --- WP-4

### 6.1 Logical records

  -----------------------------------------------------------------------
  Record                              Purpose
  ----------------------------------- -----------------------------------
  Asset                               Managed source/input media or
                                      resource; distinct from output
                                      Artifact

  Artifact                            Stable logical output record

  ArtifactVersion                     Immutable exact content/bytes

  ArtifactManifest                    Exact set of artifact/version
                                      references and provenance

  TransferRecord                      Attributable, scoped transfer
                                      lifecycle

  ValidationRecord                    Type, integrity and policy-relevant
                                      validation evidence

  QuarantineRecord                    Evidence and status for restricted
                                      downstream use
  -----------------------------------------------------------------------

### 6.2 Candidate ArtifactVersion fields

Carried forward from WP-1: - `artifact_version_id` - `artifact_id` -
`version_number` - `storage_ref` - `content_hash` - `media_type` -
`size_bytes` - `metadata` - `created_by` - `created_at` -
`parent_artifact_version_refs` - `schema_version`

Relational metadata is authoritative. Binary storage remains behind a
provider-neutral abstraction.

### 6.3 Manifest and provenance

A manifest should reference exact immutable artifact versions and
preserve: - artifact and version identity; - content hash, media type
and size; - source/input version references; - production/run and
attempt provenance; - creator/worker identity and timestamps; -
validation and quarantine references where applicable.

A storage locator alone never grants access.

### 6.4 Transfer and integrity

Required semantics: - Transfer authorization is scoped, attributable and
time-limited. - Transfer access is limited to exact authorized artifact
references. - Integrity is verified using recorded checksums/hashes and
expected size/type. - Interrupted transfers can be resumed or safely
restarted without accepting partial bytes as a completed artifact. -
Cross-job and cross-workspace access is denied unless separately
authorized. - Quarantined artifacts are blocked from ordinary downstream
use. - Repairs create a new immutable version.

OPEN: exact transfer protocol, signed access mechanism, checksum
algorithm policy, partial-transfer recovery, quarantine transitions,
retention, deletion, backup and provider-specific encryption. No
provider is selected.

## 7. Governance, QA, rights, approval and authorization --- WP-5

### 7.1 Keep five concepts separate

  -----------------------------------------------------------------------
  Concept                             Question it answers
  ----------------------------------- -----------------------------------
  QA                                  Does this exact version meet
                                      quality requirements?

  Rights                              Is this asset/content permitted for
                                      the intended use?

  Review                              What did a reviewer inspect and
                                      record?

  Approval                            Did an authorized human approve
                                      this exact scope/version?

  Authorization                       Is this actor permitted to perform
                                      this exact action now?
  -----------------------------------------------------------------------

Execution and confirmed external distribution outcome remain separate
additional facts.

### 7.2 Accepted vocabularies

**QA outcomes:** - `PASS` - `PASS_WITH_WARNINGS` - `NEEDS_REVIEW` -
`BLOCKED`

**Rights states:** - `UNKNOWN` - `PENDING_REVIEW` - `CLEARED` -
`RESTRICTED` - `EXPIRED` - `REVOKED` - `DENIED`

**Approval decisions:** - `APPROVED` - `REJECTED` -
`CHANGES_REQUESTED` - `EXPIRED` - `REVOKED`

These accepted vocabularies must not be conflated into one universal
status.

### 7.3 Candidate governance records

**QA result --- conceptual fields:** - `qa_run_id` - exact target
entity/version references - check-set and policy versions - outcome -
individual check results and evidence references - hard-blocker
indicators/reason codes - evaluator identity and timestamps

**Rights assessment --- conceptual fields:** - `rights_assessment_id` -
asset/content and exact version references - rights state - intended
use, platform, geography, time and commercial context -
modification/attribution conditions - evidence references -
reviewer/decision authority and timestamps - expiry/revocation
information

**Review/approval snapshot --- conceptual fields:** -
`review_snapshot_id` - exact target version references and hashes -
review package reference - reviewer identity - decision and scope -
timestamp - expiry/revocation references - policy/schema version

Exact schemas and validation rules remain OPEN.

### 7.4 Central authorization interface

**ACCEPTED BASELINE:** CF-22 / ADR-007 --- centralized authorization
authority, default-deny and fail-closed.

**Proposed policy evaluation request:** - request/correlation
identity; - actor or worker identity; - requested action; - target
entity and exact version/hash; - workspace; - destination and intended
use; - relevant QA, rights and approval references; - policy context and
schema version.

**Proposed policy decision:** - `ALLOW` or `DENY`; - reason codes; -
policy version; - evaluated context reference; - expiry; - revocation
reference; - decision/audit identity.

Authorization must be bound to exact action, resource, version/hash,
destination and policy context. APIs, studios, workers and distribution
adapters must enforce the central decision. Domain-local authorization
authorities are prohibited.

OPEN: exact request/decision JSON schema, reason-code catalogue,
policy-versioning, revocation propagation, emergency pause
authority/scope/override/recovery, and any exception process.

### 7.5 Distribution guard

-   Human approval before critical publishing actions remains required.
-   Automatic public publishing remains disabled.
-   No direct adapter or pipeline may bypass central authorization and
    governance.
-   Approval does not itself authorize execution.
-   Authorization does not prove execution occurred.
-   Execution does not prove the external platform accepted or published
    the content.
-   P0 acceptance tests must not perform live uploads or publishing.

## 8. Cross-package interface envelopes

The following are required interface categories. The tables are logical
shapes, not frozen JSON schemas.

### 8.1 Command envelope

  Field               Purpose
  ------------------- --------------------------------------
  `command_id`        Unique command identity
  `command_type`      Requested operation
  `schema_version`    Contract version
  `actor_ref`         Attributable caller
  `workspace_id`      Scope
  `target_ref`        Typed target reference
  `idempotency_key`   Duplicate logical request protection
  `correlation_id`    End-to-end trace
  `causation_ref`     Triggering command/event, if any
  `requested_at`      UTC request timestamp
  `payload`           Validated operation-specific data

### 8.2 Domain event envelope

  Field              Purpose
  ------------------ ----------------------------------
  `event_id`         Immutable event identity
  `event_type`       Committed fact type
  `event_version`    Event schema version
  `owner_domain`     Authoritative event owner
  `aggregate_ref`    Entity and version reference
  `workspace_id`     Scope
  `occurred_at`      Domain occurrence time
  `recorded_at`      Durable record time
  `correlation_id`   End-to-end trace
  `causation_ref`    Trigger reference
  `payload`          Bounded event data or references

Events report committed facts; they are not commands and do not grant
authority.

### 8.3 Job assignment envelope

  Field                     Purpose
  ------------------------- -----------------------------------
  `job_id`                  Logical job
  `attempt_id`              Current attempt
  `worker_id`               Assigned worker
  `lease_id`                Current lease
  `fencing_generation`      Stale-attempt protection
  `required_capabilities`   Assignment eligibility
  `input_refs`              Exact authorized input references
  `authorization_ref`       Central authorization context
  `expires_at`              Assignment/lease expiry
  `correlation_id`          Trace

### 8.4 Worker completion envelope

  Field                              Purpose
  ---------------------------------- ----------------------------------
  `job_id`, `attempt_id`             Logical and attempt identity
  `worker_id`                        Reporting worker
  `lease_id`, `fencing_generation`   Current authority proof
  `outcome`                          Structured completion outcome
  `error_ref`                        Structured error, if applicable
  `output_artifact_refs`             Exact registered output versions
  `evidence_refs`                    Attributable execution evidence
  `completed_at`                     UTC completion time
  `correlation_id`                   Trace

Completion is rejected if assignment identity, current lease, worker
trust or authorization no longer validates.

### 8.5 Artifact manifest

  Field                        Purpose
  ---------------------------- -----------------------------------
  `manifest_id`                Manifest identity
  `artifact_version_refs`      Exact immutable artifact versions
  `content_hashes`             Integrity evidence
  `media_types` and `sizes`    Type/size evidence
  `lineage_refs`               Input/source ancestry
  `production_ref`             StudioProduction/run reference
  `validation_refs`            Validation evidence
  `created_by`, `created_at`   Attribution

### 8.6 Acceptance evidence record

  Field                          Purpose
  ------------------------------ -------------------------------------------
  `evidence_id`                  Evidence identity
  `requirement_ref`              Requirement being tested
  `test_id`                      Test/scenario identity
  `source_build_ref`             Source/build identity
  `environment_ref`              Test environment
  `input_refs` / `output_refs`   Exact test inputs and outputs
  `result`                       PASS / warning / review / blocked outcome
  `log_refs`                     Supporting evidence
  `reviewer_ref`                 Attributable reviewer
  `recorded_at`                  Timestamp

## 9. Error, audit and correlation contract

Required cross-package properties: - Stable machine-readable error
code. - Human-readable safe summary. - Severity separate from
retryability. - Retryability and policy denial are explicit. -
Correlation and causation references are propagated. - Attempt and
transition history is durable and attributable. - Secrets, tokens and
sensitive provider payloads are excluded from logs and diagnostic
summaries. - Ambiguous external outcomes are represented as unknown
until reconciled. - Policy denials are not converted into transient
failures.

The final shared error taxonomy, severity mapping, retention and
redaction rules remain OPEN.

## 10. WP-6 vertical-slice acceptance contract

### 10.1 Intended non-production scenario

1.  Create one synthetic workspace-scoped ContentItem.
2.  Create an exact ContentVersion and ContentVariant.
3.  Create a version-pinned workflow and dependent task.
4.  Create a durable job.
5.  Authenticate an eligible worker.
6.  Claim work with a valid lease/fencing generation.
7.  Produce deterministic test output.
8.  Register an immutable ArtifactVersion and manifest.
9.  Validate hash, size, media type and provenance.
10. Record task/job/workflow outcomes through their owning domains.
11. Reconstruct the event, correlation and attempt history.
12. Inject failures and demonstrate safe recovery.
13. Exercise security-negative and governance-denial paths.
14. Confirm no unauthorized external side effects.
15. Submit evidence for independent read-only Kilo QA.
16. Record owner acceptance or rejection based on evidence and
    limitations.

### 10.2 Required failure-injection categories

-   Worker disconnect and lease expiry.
-   Stale completion callback after reassignment.
-   Duplicate command and duplicate event delivery.
-   Same idempotency key with conflicting payload.
-   Database/process restart around outbox delivery.
-   Interrupted artifact transfer and checksum mismatch.
-   Quarantined artifact access attempt.
-   Worker credential expiry and revocation.
-   Unverified or unavailable capability.
-   Cross-workspace reference attempt.
-   QA hard blocker and unresolved rights.
-   Missing/expired/revoked approval.
-   Authorization denial and emergency pause.
-   Direct adapter/pipeline bypass attempt.
-   Ambiguous external outcome and reconciliation path.
-   Local worker offline and reconnect behavior.

The exact test matrix and thresholds remain WP-6 acceptance work; this
appendix does not claim these tests have run.

### 10.3 Acceptance outcomes

Use the accepted QA outcome vocabulary: - `PASS` -
`PASS_WITH_WARNINGS` - `NEEDS_REVIEW` - `BLOCKED`

Hard blockers cannot be bypassed by ordinary approval. Independent QA
and owner acceptance are separate evidence/decision steps.

## 11. Open contract questions before freeze

These must be resolved in the detailed contract pack:

1.  Exact canonical entity field sets, nullability, uniqueness, FK
    behavior, deletion and transition tables.
2.  Exact content version sequencing and variant relationship
    constraints.
3.  Workflow definition/run/task state machines and dependency
    semantics.
4.  Job/attempt/lease state machines, cancellation, terminal and
    remediation behavior.
5.  Fencing generation and atomic claim/heartbeat/expiry semantics.
6.  Retry classes, limits, backoff, poison-message handling and manual
    requeue authority.
7.  Idempotency scope, retention and external reconciliation.
8.  Outbox/inbox ordering, replay, retention and purge authority.
9.  Worker enrollment, machine identity proof and trust transitions.
10. Credential issuer/protocol/rotation/revocation contract.
11. Capability catalogue, verification evidence and active-job
    revocation.
12. Minimum isolation technology/threat model and resource boundaries.
13. Artifact manifest schema, transfer protocol and partial-transfer
    recovery.
14. Artifact retention, deletion, legal hold, backup and restore
    obligations.
15. QA check/result schema and hard-blocker mapping.
16. Rights evidence schema and use-specific policy conditions.
17. Approval snapshot schema, expiry and re-review triggers.
18. Authorization request/decision schema and exact binding semantics.
19. Emergency pause authority, scope, override and recovery.
20. Shared error taxonomy, event compatibility and audit retention.
21. Shorts Studio adapter interface and all bypass-prevention points.
22. WP-6 evidence schema, acceptance thresholds and independent QA
    requirements.

Provider, region, production sizing and other operational selections may
be deferred only where the abstraction and enforcement contracts remain
complete.

## 12. Freeze and implementation gates

The appendix may become part of a frozen contract baseline only after: -
all freeze-critical questions have explicit contract answers; - proposed
details are accepted, amended, rejected or deferred by the owner; -
owner-reserved security, rights, authorization and material
data-lifecycle decisions are resolved; - all package documents are
reconciled to the same terms and schemas; - cross-contract consistency
is reviewed; - formal owner approval is recorded.

Implementation authorization remains separate and must specify exact
work packages, repository boundaries, permitted commands, test scope,
agent permissions, preservation rules and prohibited/allowed external
effects.

## 13. Current disposition

  -----------------------------------------------------------------------
  Area                                Status
  ----------------------------------- -----------------------------------
  ADR-001--ADR-010                    Accepted baseline

  CF-01--CF-24                        Carried forward as recorded

  WP-1--WP-6                          Design candidates

  Logical entities and envelopes in   Consolidated
  this appendix                       proposals/source-derived boundaries

  Exact physical schemas and          Not frozen
  executable API contracts            

  Owner-reserved decisions            Open

  Provider/operational choices        Deferred where safe

  Detailed contract freeze            NOT GRANTED

  Implementation authorization        NOT GRANTED

  Repository changes, tests, Git      Not authorized
  operations or agent execution       

  Paid services, deployment,          Not authorized
  production generation, upload or    
  publishing                          

  Independent implementation/QA       Not established by this document
  evidence                            
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## Plain-language explanation

This appendix puts the system's main building blocks and the ways they
communicate in one place. It explains what a content item, workflow,
job, worker, artifact and approval mean, and how they must interact
safely.

It is still a design candidate. Some exact fields, state transitions,
security protocols and policy decisions need to be completed before the
design can be frozen. Nothing has been implemented or tested by creating
this document.

**NEXTDECODE principle:** one shared source of truth, bounded workers,
immutable evidence, centralized governance, and explicit human
authority.
