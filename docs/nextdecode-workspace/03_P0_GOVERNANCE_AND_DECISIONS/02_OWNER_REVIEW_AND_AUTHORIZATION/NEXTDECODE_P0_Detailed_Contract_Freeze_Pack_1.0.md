# NEXTDECODE Content OS — P0 Detailed Contract Freeze Pack 1.0

**Document status:** Proposed detailed contract baseline — owner review required  
**Version:** 1.0  
**Date:** 31 October 2026  
**Scope:** P0 foundation contracts  
**Authority:** Product owner

Related documents:
- `NEXTDECODE_Accepted_P0_Architecture_Decision_Baseline_1.0.md`
- `NEXTDECODE_Canonical_Contracts_Pack_1.0.md`
- `NEXTDECODE_P0_Foundation_Implementation_Specification_1.0.md`
- `NEXTDECODE_Architecture_Decision_Records_Pack_1.0.md`
- Architecture Parts 1–8

---

## 1. Purpose and status

This pack translates the ten accepted high-level architecture decisions into detailed, reviewable contracts for the P0 foundation.

It defines:
1. Canonical entity boundaries and relationships.
2. Lifecycle state-transition rules.
3. Job, lease, retry and event-delivery semantics.
4. Worker registration, identity and capability contracts.
5. Artifact metadata, immutability and transfer contracts.
6. Quality and rights policy interfaces.
7. Authorization request and decision contracts.
8. Error taxonomy, audit events and correlation conventions.
9. Contract-level acceptance tests.

**Status discipline**
- **ACCEPTED DECISION** means the owner accepted the high-level direction.
- **PROPOSED DETAIL** means this pack recommends a concrete implementation contract that still requires review.
- **OPEN** means a value or policy must be selected before the affected feature is implemented.
- **DEFERRED** means intentionally outside P0.

The owner accepted ADR-001 through ADR-010. That does not mean every field, enum, threshold, endpoint or retention value below has already been approved.

**No repository inspection, code modification, Git operation, dependency installation, cloud provisioning, deployment, production generation, upload or publishing is authorized by this pack.**

---

## 2. Accepted architecture constraints

The following high-level decisions are treated as accepted:

| ADR | Accepted direction |
|---|---|
| ADR-001 | UUIDv7 canonical identifiers |
| ADR-002 | PostgreSQL-compatible authoritative shared database |
| ADR-003 | Database-backed durable queue with transactional outbox/inbox initially |
| ADR-004 | Versioned HTTP/JSON with schema validation |
| ADR-005 | Unique worker identity, scoped short-lived credentials and capability authorization |
| ADR-006 | Relational metadata plus object storage abstraction for binaries |
| ADR-007 | Centralized authorization boundary; no adapter bypass; automatic publishing disabled pending separate approval |
| ADR-008 | PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW, BLOCKED; hard blockers cannot be bypassed by ordinary approval |
| ADR-009 | Centralized evidence-backed rights states and use-specific enforcement |
| ADR-010 | Separate lifecycle state machines |

Hybrid topology remains locked: always-on cloud control plane, cloud-authoritative shared state, local worker for local-only execution such as existing Shorts Studio when the PC is available.

---

# Part A — Canonical domain contracts

## 3. Identity rules

### 3.1 Canonical ID format

**Accepted:** UUIDv7.

All canonical IDs:
- are generated once;
- are immutable;
- are never reused;
- are opaque to business logic;
- are validated as UUID values at boundaries;
- are stored in a consistent database representation.

Do not encode mutable business meaning, status, platform or owner into the ID.

### 3.2 ID-bearing entity types

| Entity | Canonical ID field | Notes |
|---|---|---|
| Workspace | `workspace_id` | Initial single-owner workspace |
| Brand | `brand_id` | NEXTDECODE initially |
| Content idea | `content_idea_id` | Candidate/editorial concept |
| Content item | `content_item_id` | Durable editorial identity |
| Content variant | `content_variant_id` | Format/platform adaptation |
| Workflow | `workflow_id` | Orchestration instance |
| Workflow task | `task_id` | Logical unit of work |
| Job | `job_id` | Durable dispatchable execution request |
| Job attempt | `job_attempt_id` | One attempt to execute a job |
| Worker | `worker_id` | Registered machine execution identity |
| Studio job | `studio_job_id` | Adapter-level studio request |
| Production run | `production_run_id` | One concrete engine run |
| Artifact | `artifact_id` | Immutable output identity/version |
| Asset | `asset_id` | Reusable/source media resource |
| Review package | `review_package_id` | Exact review snapshot |
| Approval | `approval_id` | Editorial decision record |
| Authorization | `authorization_id` | Permission for a scoped action |
| Distribution | `distribution_id` | Platform delivery record |
| Event | `event_id` | Unique event identity |
| Policy version | `policy_version_id` | Immutable policy version |

### 3.3 External identifiers

External platform IDs, legacy run IDs, file paths and provider object keys must be stored as external references with:
- source system/provider;
- external ID or locator;
- related canonical entity;
- observed timestamp;
- optional metadata.

They must not replace canonical IDs.

---

## 4. Entity contracts and relationships

This is the proposed P0 minimum model. It is not a claim about the current repository schema.

### 4.1 Workspace and Brand

**Workspace**
- `workspace_id`
- `name`
- `status`
- `created_at`
- `updated_at`

**Brand**
- `brand_id`
- `workspace_id`
- `name`
- `status`
- `brand_profile_ref` (optional reference to a versioned profile)
- `created_at`
- `updated_at`

Relationship: one workspace has one or more brands. P0 starts with one workspace and NEXTDECODE brand.

### 4.2 ContentIdea, ContentItem and ContentVariant

**ContentIdea**
- `content_idea_id`
- `workspace_id`
- `brand_id`
- `title`
- `summary`
- `origin`
- `status`
- `created_at`
- `updated_at`

**ContentItem**
- `content_item_id`
- `workspace_id`
- `brand_id`
- `source_idea_id` (nullable)
- `title`
- `editorial_status`
- `created_at`
- `updated_at`

**ContentVariant**
- `content_variant_id`
- `content_item_id`
- `format`
- `platform_target` (nullable)
- `variant_status`
- `current_artifact_id` (nullable)
- `created_at`
- `updated_at`

Rules:
- An idea may produce one or more content items.
- A content item may have multiple variants.
- A variant is a format/platform adaptation, not a new content item.
- A variant may have multiple production runs over time.
- A new artifact does not overwrite historical artifact versions.

### 4.3 Workflow and WorkflowTask

**Workflow**
- `workflow_id`
- `workspace_id`
- `content_item_id` (nullable for non-content workflows)
- `workflow_type`
- `workflow_status`
- `definition_version`
- `created_at`
- `updated_at`
- `completed_at` (nullable)

**WorkflowTask**
- `task_id`
- `workflow_id`
- `task_type`
- `task_status`
- `dependency_task_ids`
- `required_capabilities`
- `input_refs`
- `result_refs`
- `created_at`
- `updated_at`

Rules:
- Workflow owns the orchestration context.
- Task represents a logical step and dependency.
- Task is not a worker attempt.
- A task may create one or more jobs over its lifecycle if retry/re-execution semantics require it.
- Workflow completion is derived from task and policy outcomes, not inferred from one job's success.

### 4.4 Job and JobAttempt

**Job**
- `job_id`
- `task_id`
- `job_type`
- `job_status`
- `payload_schema_version`
- `payload_ref` or validated payload
- `required_capabilities`
- `priority`
- `eligible_at`
- `idempotency_key`
- `max_attempts`
- `created_at`
- `updated_at`

**JobAttempt**
- `job_attempt_id`
- `job_id`
- `attempt_number`
- `worker_id` (nullable until claimed)
- `lease_token_hash` (never store raw bearer token)
- `lease_expires_at`
- `heartbeat_at`
- `attempt_status`
- `started_at`
- `finished_at`
- `failure_code` (nullable)
- `failure_detail_safe` (nullable)

Rules:
- Job is the logical dispatch request.
- JobAttempt is one execution attempt.
- Retry creates a new attempt record; it does not erase previous attempts.
- A job may be retried only under its retry policy.
- A stale attempt cannot commit a result after its lease is no longer current.

### 4.5 Worker

**Worker**
- `worker_id`
- `machine_identity`
- `worker_status`
- `software_version`
- `contract_versions`
- `capabilities`
- `last_heartbeat_at`
- `registered_at`
- `revoked_at` (nullable)

Rules:
- Worker identity is unique and independently revocable.
- Capabilities are server-authorized; worker claims are not blindly trusted.
- Human account identity and worker machine identity remain separate.
- Worker status is not a substitute for job lease validity.

### 4.6 StudioJob and ProductionRun

**StudioJob**
- `studio_job_id`
- `job_id`
- `studio_type`
- `adapter_contract_version`
- `studio_request_ref`
- `studio_status`

**ProductionRun**
- `production_run_id`
- `studio_job_id`
- `engine_name`
- `engine_version`
- `run_status`
- `started_at`
- `finished_at`
- `output_artifact_ids`

Rules:
- A StudioJob adapts a platform job to a specific studio engine.
- A ProductionRun represents one actual engine execution.
- Existing Shorts Studio remains a specialized engine behind an adapter boundary.
- P0 must not assume the existing engine already supports every proposed contract.

### 4.7 Asset and Artifact

**Asset**
- `asset_id`
- `workspace_id`
- `asset_type`
- `source_ref`
- `provenance_ref`
- `rights_record_id`
- `asset_status`
- `created_at`

**Artifact**
- `artifact_id`
- `artifact_version`
- `content_item_id` (nullable)
- `content_variant_id` (nullable)
- `workflow_id` (nullable)
- `production_run_id` (nullable)
- `artifact_type`
- `media_type`
- `byte_size`
- `checksum_algorithm`
- `checksum_value`
- `storage_object_ref`
- `artifact_status`
- `created_at`

Rules:
- Artifact versions are immutable.
- New output creates a new version/record.
- Checksum is calculated over the exact binary content.
- Storage object reference is not itself permission to access the object.
- Approval references exact artifact IDs and checksums.

### 4.8 Review, Approval, Authorization and Distribution

**ReviewPackage**
- `review_package_id`
- `content_variant_id`
- `artifact_refs`
- `policy_versions`
- `quality_result`
- `rights_result`
- `created_at`

**Approval**
- `approval_id`
- `review_package_id`
- `decision`
- `decision_actor`
- `decision_at`
- `comment_ref` (optional)

**Authorization**
- `authorization_id`
- `action`
- `content_variant_id`
- `artifact_refs`
- `destination`
- `policy_version_id`
- `authorization_status`
- `not_before`
- `expires_at`
- `issued_at`
- `revoked_at`

**Distribution**
- `distribution_id`
- `authorization_id` (nullable for denied attempts)
- `content_variant_id`
- `artifact_refs`
- `platform`
- `destination_account_ref`
- `distribution_status`
- `external_post_id` (nullable)
- `created_at`
- `completed_at`

Rules:
- Review is an evaluation.
- Approval is an editorial decision.
- Authorization is permission for a specific action.
- Distribution is an execution record.
- Approval cannot substitute for authorization.
- P0 does not enable automatic public publishing.

---

# Part B — Lifecycle contracts

## 5. State-machine principles

- Each domain entity has its own lifecycle.
- State changes must use validated transition functions.
- Every transition records actor, timestamp, reason and correlation ID.
- State transition history is append-only for critical entities.
- Invalid transitions are rejected.
- State names are not reused to mean different things across entity types.
- UI summary status is derived from underlying domain states.

## 6. Proposed state machines

The following are **proposed detailed states** derived from the accepted separation decision. They require review before implementation.

### 6.1 Content item

```text
DRAFT -> ACTIVE -> ARCHIVED
   \       |
    \      v
     -> CANCELLED
```

Suggested meaning:
- `DRAFT`: editorial identity created, not yet active.
- `ACTIVE`: content item is being developed or maintained.
- `ARCHIVED`: no longer active; retained for history.
- `CANCELLED`: intentionally stopped.

Open detail: whether `ARCHIVED` can be reopened and whether `CANCELLED` is terminal.

### 6.2 Content variant

```text
PLANNED -> IN_PRODUCTION -> READY_FOR_REVIEW
   |              |                 |
   v              v                 v
CANCELLED      NEEDS_REWORK <---- APPROVED
                                  |
                                  v
                              RELEASED
```

Suggested meaning:
- `PLANNED`: variant defined.
- `IN_PRODUCTION`: creation underway.
- `READY_FOR_REVIEW`: candidate artifact available for review.
- `NEEDS_REWORK`: review requested changes.
- `APPROVED`: editorial approval recorded for exact version.
- `RELEASED`: at least one authorized distribution completed.

Open detail: whether `RELEASED` is a terminal state or a derived summary when multiple platforms exist. Recommended: derive release state per distribution, not as a permanent variant state.

### 6.3 Workflow

```text
CREATED -> READY -> RUNNING -> COMPLETED
             |        |
             v        v
           BLOCKED   FAILED
             |        |
             +-> READY (after remediation/retry)
CREATED/READY/RUNNING -> CANCELLED
```

Rules:
- `COMPLETED` requires all required tasks and policy gates to reach terminal success.
- `BLOCKED` means progression is prevented by a prerequisite or policy.
- `FAILED` means the workflow cannot continue under current retry policy.
- Recovery must be an explicit transition with reason.

### 6.4 Workflow task

```text
PENDING -> READY -> RUNNING -> SUCCEEDED
   |         |        |
   |         |        +-> RETRY_WAIT -> READY
   |         +-> BLOCKED
   +-> CANCELLED

RUNNING -> FAILED
```

Rules:
- Dependencies must be satisfied before `READY`.
- `SUCCEEDED` requires a validated result.
- `FAILED` may be retryable or terminal; retryability is represented separately.
- `BLOCKED` requires a reason and resolution condition.

### 6.5 Job

```text
QUEUED -> LEASED -> SUCCEEDED
   |        |
   |        +-> RETRY_WAIT -> QUEUED
   |        +-> FAILED
   |        +-> CANCELLED
   +-> CANCELLED
```

Rules:
- Job is dispatch state, not editorial state.
- `LEASED` is valid only while a current attempt lease is valid.
- Job success requires accepted result persistence.
- Retry creates a new JobAttempt.
- Job cancellation must not erase attempt history.

### 6.6 JobAttempt

```text
CREATED -> CLAIMED -> RUNNING -> SUCCEEDED
                       |  |
                       |  +-> FAILED
                       +----> LEASE_EXPIRED
```

A lease-expired attempt is terminal for that attempt. The logical job may create another attempt if retry policy permits.

### 6.7 Worker

```text
PENDING_REGISTRATION -> ACTIVE -> OFFLINE
                              \-> REVOKED
OFFLINE -> ACTIVE (after re-authentication)
```

Rules:
- `OFFLINE` is derived from heartbeat expiry; it does not delete the worker.
- `REVOKED` prevents new claims and new artifact access.
- Revocation does not automatically erase audit history.

### 6.8 Production run

```text
CREATED -> STARTED -> RENDERED -> VALIDATED
             |          |           |
             v          v           v
           FAILED     FAILED      FAILED
```

Suggested state meaning:
- `RENDERED` means output file was produced.
- `VALIDATED` means required technical/manifest checks passed.
- `VALIDATED` does not mean editorially approved or authorized for publishing.

### 6.9 Review package

```text
CREATED -> EVALUATED -> PENDING_HUMAN_REVIEW -> CLOSED
              |                  |
              v                  v
           BLOCKED             CLOSED
```

A review package is an immutable snapshot of the exact artifact and policy versions evaluated. Re-evaluation creates a new package or explicit revision.

### 6.10 Approval

```text
PENDING -> APPROVED
        -> REJECTED
        -> EXPIRED
        -> REVOKED
```

Approval must reference the exact review package and artifact versions. A new artifact version requires a new approval decision.

### 6.11 Authorization

```text
NOT_ISSUED -> ACTIVE -> CONSUMED
                   \-> EXPIRED
                   \-> REVOKED
```

Authorization is scoped to action, destination, artifact/version, policy version and time window. One-time versus reusable authorization is an open policy detail; default recommendation is one authorization per distribution attempt.

### 6.12 Distribution

```text
REQUESTED -> DENIED
          -> AUTHORIZED -> SUBMITTED -> CONFIRMED
                                      \-> FAILED
                                      \-> UNKNOWN_OUTCOME
```

`UNKNOWN_OUTCOME` is important when an external platform request times out after the platform may have accepted it. The system must reconcile before retrying to avoid duplicate posts.

---

# Part C — Durable execution and event contracts

## 7. Job dispatch semantics

### 7.1 Job creation

A job is created only after:
- its task is eligible;
- dependency conditions are satisfied;
- required input references exist;
- the job payload validates against its schema;
- capability requirements are known.

Job creation and the corresponding outbox event should be committed atomically.

### 7.2 Claim operation

A worker claim request must include:
- worker identity;
- supported contract versions;
- declared capabilities;
- requested job classes;
- request correlation ID.

The server must:
1. authenticate the worker;
2. verify worker status is active;
3. verify capability eligibility;
4. select an eligible job transactionally;
5. create a new attempt;
6. issue a lease;
7. return the job envelope and lease metadata.

The worker must not choose arbitrary job IDs and self-assign them.

### 7.3 Lease contract

A lease includes:
- `job_id`
- `job_attempt_id`
- `worker_id`
- `lease_expires_at`
- opaque lease token (returned only to the authorized worker)
- heartbeat interval hint
- allowed result callback scope

**Proposed defaults:** lease duration and heartbeat interval are OPEN. Do not hardcode values until workload and rendering duration classes are assessed.

Rules:
- Lease token is treated as a secret.
- Store only a verifier/hash where practical.
- Heartbeat must prove current lease ownership.
- Lease extension is permitted only while the attempt is valid.
- A stale lease cannot be revived after reassignment.
- A worker may not extend another worker's lease.

### 7.4 Retry contract

Retry policy must specify:
- retryable failure codes;
- maximum attempts;
- delay/backoff;
- optional jitter;
- terminal failure conditions;
- manual requeue permissions.

**Proposed baseline:** bounded exponential backoff with jitter for transient infrastructure failures. Deterministic validation, policy and authorization failures are not automatically retried.

Exact retry counts and delays remain OPEN.

### 7.5 Idempotency

Every side-effecting operation should carry an idempotency key scoped to the logical operation.

Examples:
- job creation;
- result acceptance;
- artifact registration;
- authorization consumption;
- distribution submission.

A repeated request with the same key and same semantic payload returns the original logical result. Reuse with a different payload must be rejected as an idempotency conflict.

---

## 8. Transactional outbox/inbox

### 8.1 Outbox

When a transaction changes authoritative state and requires event publication, it writes:
- state change;
- outbox event;
- correlation/causation metadata;

in the same database transaction.

Outbox dispatcher:
- reads pending records;
- publishes or makes them available to consumers;
- records dispatch state;
- retries transient failures;
- never assumes one-time delivery.

### 8.2 Inbox / deduplication

A consumer records the event ID or deduplication key before applying a logical effect, in a transaction with that effect where possible.

Rules:
- Duplicate event ID must not repeat the logical effect.
- Event ordering must not be assumed globally.
- Consumers validate aggregate version or expected state before applying updates.
- Poison events are quarantined with safe diagnostics and an operator-visible status.

### 8.3 Event envelope

Proposed common envelope:

```json
{
  "event_id": "UUIDv7",
  "event_type": "job.created",
  "schema_version": "1.0",
  "occurred_at": "ISO-8601 timestamp",
  "producer": {
    "service": "workflow-orchestrator",
    "version": "x.y.z"
  },
  "correlation_id": "UUIDv7",
  "causation_id": "UUIDv7",
  "aggregate": {
    "type": "job",
    "id": "UUIDv7",
    "version": 1
  },
  "payload": {}
}
```

The sample is illustrative. Exact schema tooling and timestamp precision remain open.

---

# Part D — Worker contracts

## 9. Worker registration

Registration request should include:
- machine identity proof;
- worker software version;
- supported contract versions;
- declared capabilities;
- environment type (`local` or `remote`);
- optional resource profile.

Server response should include:
- canonical worker ID;
- registration status;
- credential issuance instructions;
- heartbeat policy;
- approved capability set;
- contract compatibility result.

A worker's declared capabilities are claims. The server may approve a narrower set.

## 10. Worker authentication and permissions

Accepted direction:
- unique worker identity;
- scoped short-lived credentials;
- independent revocation.

Proposed rules:
- credential audience is the control plane;
- credential scope is limited to worker actions;
- credentials are not included in job payloads or logs;
- refresh/reissue requires valid worker identity;
- revocation takes effect for new claims and artifact access;
- human session credentials are never reused as machine credentials.

Exact issuer, protocol and local secret storage are OPEN.

## 11. Capability model

A capability is a typed permission to execute a job class, not an unrestricted role.

Examples (illustrative):
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
- Sensitive capabilities require explicit server approval.
- A local worker may advertise local rendering only while it is online and healthy.
- Cloud workflows remain durable while a local-only capability is unavailable.

The final capability catalogue is OPEN and should be aligned with actual studio adapter boundaries after authorized system inspection.

---

# Part E — Artifact and rights contracts

## 12. Artifact metadata and versioning

### 12.1 Artifact registration

Artifact registration request should include:
- artifact ID or idempotency key;
- owning content/variant/workflow/run IDs;
- artifact type;
- media type;
- byte size;
- checksum algorithm and value;
- storage object reference;
- producer identity;
- provenance/rights references;
- schema version.

Server validates:
- worker/job lease scope;
- object ownership;
- checksum and byte size;
- media type constraints;
- entity relationships;
- idempotency.

### 12.2 Immutability

- Artifact content is immutable after registration.
- Metadata corrections are audited and versioned where they affect meaning.
- New generated output creates a new artifact version.
- An approval refers to exact artifact ID/version/checksum.
- Replacing a file at the same path must not silently replace an approved artifact.

### 12.3 Transfer

Use short-lived scoped transfer authorization.

Upload lifecycle:
1. request upload authorization;
2. upload binary to storage;
3. verify checksum/size;
4. register artifact metadata;
5. mark artifact available.

Download lifecycle:
1. request artifact access;
2. validate worker/job scope;
3. issue short-lived transfer authorization;
4. download;
5. verify checksum before use.

Storage provider and exact transfer protocol remain OPEN.

---

## 13. Rights record

Proposed rights record fields:
- `rights_record_id`
- `asset_id`
- `rights_status`
- `source_type`
- `rights_holder` (if known)
- `license_or_permission_basis`
- `evidence_refs`
- `allowed_platforms`
- `allowed_territories`
- `commercial_use_allowed`
- `attribution_required`
- `valid_from`
- `expires_at`
- `revoked_at`
- `verified_by`
- `verified_at`
- `policy_version_id`

Accepted rights states:
- `CLEARED`
- `RESTRICTED`
- `PENDING_VERIFICATION`
- `PROHIBITED`
- `UNKNOWN`

Rules:
- Rights must be evaluated for the intended use, not just asset in isolation.
- `UNKNOWN`, `PENDING_VERIFICATION` and `PROHIBITED` block affected protected use under the accepted baseline.
- `RESTRICTED` requires every condition to be satisfied.
- Rights expiry/revocation invalidates future authorization and triggers re-evaluation of queued distributions.
- Derived assets retain provenance links.

Open: evidence taxonomy, who may verify, exception workflow and treatment of historical published outputs.

---

# Part F — Quality and governance contracts

## 14. Quality result contract

Proposed quality result:

```json
{
  "result_id": "UUIDv7",
  "subject_type": "content_variant",
  "subject_id": "UUIDv7",
  "artifact_refs": [],
  "policy_version_id": "UUIDv7",
  "outcome": "PASS_WITH_WARNINGS",
  "checks": [
    {
      "check_id": "technical.video_profile",
      "severity": "warning",
      "status": "passed",
      "evidence_refs": [],
      "message_code": "VIDEO_PROFILE_VALID"
    }
  ],
  "evaluated_at": "ISO-8601 timestamp"
}
```

Accepted outcomes:
- `PASS`
- `PASS_WITH_WARNINGS`
- `NEEDS_REVIEW`
- `BLOCKED`

Rules:
- Result is tied to exact subject/artifact versions and policy version.
- Each check has a stable check ID and severity.
- `BLOCKED` cannot be converted to pass by ordinary editorial approval.
- `NEEDS_REVIEW` requires the defined human review action.
- Warning acceptance, where allowed, is recorded with actor and reason.
- A new artifact version requires re-evaluation where relevant.

Exact check catalogue and severity thresholds remain OPEN.

## 15. Approval contract

Approval request must reference:
- review package ID;
- exact artifact IDs and checksums;
- decision (`APPROVED` or `REJECTED`);
- actor identity;
- timestamp;
- optional reason/comment.

Rules:
- Approval applies only to the exact reviewed version.
- New artifact version invalidates applicability unless re-reviewed.
- Approval does not grant distribution authorization.
- Approval history is append-only; changes create new decisions.

## 16. Authorization contract

Authorization request must include:
- action (e.g. `distribution.publish`);
- content variant ID;
- exact artifact references/checksums;
- destination platform and account reference;
- requested time window;
- approval reference, where required;
- quality result reference;
- rights evaluation reference;
- policy version.

Authorization decision must include:
- authorization ID if granted;
- `GRANTED` or `DENIED`;
- reason codes;
- exact scope;
- not-before and expiry;
- policy version;
- decision timestamp.

Rules:
- Deny by default.
- Missing or mismatched references are denied.
- Expired/revoked authorization is denied.
- Emergency pause denies new protected actions.
- Automatic publishing remains disabled until a separate owner-approved policy exists.
- This contract does not authorize live platform integration.

---

# Part G — Error, audit and observability contracts

## 17. Error taxonomy

Proposed stable error categories:

| Category | Examples | Retry guidance |
|---|---|---|
| `VALIDATION` | Invalid schema, missing required field | No automatic retry |
| `AUTHENTICATION` | Invalid/expired worker credential | Re-authenticate; no blind retry |
| `AUTHORIZATION` | Capability or action denied | No automatic retry |
| `CONFLICT` | Stale version, idempotency payload mismatch | Reconcile; no blind retry |
| `NOT_FOUND` | Unknown entity/artifact | Usually no retry |
| `RATE_LIMITED` | Provider/API throttling | Retry per backoff/Retry-After |
| `TRANSIENT` | Temporary network/service failure | Bounded retry |
| `DEPENDENCY_UNAVAILABLE` | Database/storage/provider unavailable | Bounded retry and alert |
| `INTEGRITY` | Checksum mismatch, invalid manifest | Block; investigate |
| `POLICY_BLOCKED` | Rights/quality/safety hard gate | No automatic retry until remediation |
| `INTERNAL` | Unexpected failure | Bounded retry only when safe |

Error response should contain:
- stable `code`;
- safe `message`;
- `category`;
- `retryable`;
- `correlation_id`;
- optional `details` that contain no secrets;
- optional `retry_after`.

## 18. Audit event contract

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

Audit records should be append-only for critical governance and lifecycle decisions.

Do not log:
- raw credentials;
- lease bearer tokens;
- signed storage URLs;
- private keys;
- unredacted secrets;
- unnecessary personal data.

## 19. Correlation conventions

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

---

# Part H — Contract acceptance tests

## 20. Required contract tests

| ID | Contract | Test | Expected |
|---|---|---|---|
| CT-001 | Identity | Invalid UUID representation | Rejected |
| CT-002 | Identity | Duplicate canonical ID | Rejected |
| CT-003 | Domain | Content item with multiple variants | Valid |
| CT-004 | Domain | Artifact linked to unrelated run | Rejected |
| CT-005 | State | Invalid transition | Rejected |
| CT-006 | State | Stale state version update | Rejected |
| CT-007 | Job | Two workers claim same job | One current lease |
| CT-008 | Job | Expired lease submits result | Rejected |
| CT-009 | Job | Retry creates new attempt | Prior attempt retained |
| CT-010 | Job | Duplicate idempotency key, same payload | Original result returned |
| CT-011 | Job | Same idempotency key, different payload | Conflict |
| CT-012 | Event | Duplicate event delivery | One logical effect |
| CT-013 | Event | Outbox transaction rolls back | No orphan event |
| CT-014 | Event | Consumer restart | Pending event recovered |
| CT-015 | Worker | Revoked worker claims job | Denied |
| CT-016 | Worker | Unsupported capability | Denied |
| CT-017 | Worker | Worker accesses unrelated job | Denied |
| CT-018 | Artifact | Checksum mismatch | Rejected |
| CT-019 | Artifact | New artifact version | Old version unchanged |
| CT-020 | Artifact | Expired transfer authorization | Denied |
| CT-021 | Rights | Unknown rights | Protected use blocked |
| CT-022 | Rights | Restricted platform mismatch | Blocked |
| CT-023 | Quality | BLOCKED + ordinary approval | Remains blocked |
| CT-024 | Approval | Approval for old artifact version | Not valid for new version |
| CT-025 | Authorization | Missing authorization | Distribution denied |
| CT-026 | Authorization | Wrong destination | Distribution denied |
| CT-027 | Authorization | Expired/revoked authorization | Distribution denied |
| CT-028 | Authorization | Emergency pause active | Protected action denied |
| CT-029 | Audit | End-to-end correlation | Trace is reconstructable |
| CT-030 | Security | Secret in exception path | Redacted |

These tests are proposed. They have not been executed.

---

## 21. Open implementation parameters

The accepted architecture is sufficiently clear to define contracts, but the following must be decided or validated before implementation of affected areas:

### Database and persistence
- PostgreSQL provider and version.
- Migration tool.
- Connection pooling and transaction isolation expectations.
- Backup retention and recovery targets.

### Queue and leases
- Job claim strategy and locking approach.
- Lease duration by job class.
- Heartbeat cadence.
- Retry counts and backoff ceilings.
- Outbox/inbox retention and replay rules.

### API and worker security
- Schema tooling and compatibility policy.
- Credential issuer and token format.
- Renewal cadence and revocation propagation.
- Local secret storage approach.

### Artifact storage
- Object storage provider and region.
- Upload/download protocol.
- Retention classes and lifecycle policy.
- Maximum file sizes and multipart behavior.

### Quality and rights
- Exact check catalogue and severity.
- Rights evidence taxonomy and verification roles.
- Exception process, if any.
- Rights revocation propagation.

### Governance
- Authorization scope and consumption semantics.
- Policy version management.
- Emergency pause ownership and audit.
- Platform-specific privacy defaults.

---

## 22. Freeze criteria

This pack may be marked **CONTRACT BASELINE FROZEN** only after:

1. Owner reviews proposed detailed entity fields and relationships.
2. Owner reviews proposed state machines and terminal/reopen semantics.
3. Lease/retry/outbox/inbox rules are accepted.
4. Worker identity and capability contracts are accepted.
5. Artifact transfer and immutability contracts are accepted.
6. Quality and rights interfaces are accepted.
7. Authorization scope and denial semantics are accepted.
8. Open values are either decided or explicitly deferred with accepted risk.
9. Canonical Contracts Pack is updated to match this pack.
10. Conflicts with Architecture Parts 1–8 are reconciled.

A frozen contract baseline still does not authorize repository inspection or implementation.

---

## 23. Current status

- High-level ADR-001 through ADR-010: **ACCEPTED**
- Detailed contract pack: **DRAFT CREATED**
- Entity/relationship details: **PROPOSED**
- State-transition tables: **PROPOSED**
- Queue/lease/event semantics: **PROPOSED**
- Worker security details: **PROPOSED**
- Artifact transfer details: **PROPOSED**
- Quality/rights interfaces: **PROPOSED**
- Authorization contract: **PROPOSED**
- Contract baseline freeze: **PENDING OWNER REVIEW**
- Repository inspection: **NOT AUTHORIZED**
- Git operations: **NOT AUTHORIZED**
- Code changes: **NOT AUTHORIZED**
- Deployment / production actions: **NOT AUTHORIZED**

---

## 24. Recommended review sequence

Review the detailed contracts in this order:

1. Entity and relationship model.
2. State machines and transition rules.
3. Job, lease, retry and event semantics.
4. Worker identity and capability contracts.
5. Artifact metadata and transfer.
6. Quality and rights policy interfaces.
7. Authorization contract.
8. Error, audit and correlation conventions.

If a detail needs actual repository evidence, mark it OPEN and wait for separate read-only inspection authorization. Do not infer current implementation behavior from this proposed contract.

---

## 25. Change log

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-10-31 | Initial P0 detailed contract freeze pack |
