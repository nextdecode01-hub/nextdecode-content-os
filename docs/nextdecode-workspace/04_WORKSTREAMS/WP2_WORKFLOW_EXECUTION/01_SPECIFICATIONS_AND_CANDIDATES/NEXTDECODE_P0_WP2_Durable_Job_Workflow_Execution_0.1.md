# NEXTDECODE — P0 WP-2 Durable Job & Workflow Execution Design Candidate

**Document ID:** `NEXTDECODE_P0_WP2_Durable_Job_Workflow_Execution_0.1`  
**Version:** 0.1  
**Date:** 1 November 2026  
**Work package:** WP-2 — Durable Job and Workflow Execution  
**Status:** **DESIGN CANDIDATE — OWNER REVIEW REQUIRED**  
**Implementation status:** Not authorized

## 1. Purpose

WP-2 defines the logical execution contract that allows NEXTDECODE work to survive process interruption, worker disconnection and recoverable failures. It connects the WP-1 canonical domain model to the worker boundary (WP-3), artifact boundary (WP-4) and governance boundary (WP-5).

The goal is not to design a general-purpose distributed workflow platform. The goal is to prove one bounded P0 vertical slice with durable, auditable and recoverable execution.

This document is derived from:
- Artifact 07 — P0 Foundation Execution Plan & Acceptance Framework 1.0.
- Accepted P0 Architecture Decision Baseline 1.0, especially ADR-003, ADR-004 and ADR-005.
- Artifact 08 detailed contract freeze and open-decision closure material.
- API & Event Contract Standard 1.0.
- Unified Lifecycle & State Transition Standard 1.0.
- WP-1 v0.1, v0.2 and consolidated schema contract candidate v0.3.

This is a logical design candidate, not an implementation specification, SQL schema, migration, provider selection or authorization to execute.

## 2. Status and authority labels

- **Accepted baseline** — explicitly accepted architecture decision.
- **Source-defined** — requirement or boundary defined in a governing source.
- **Recommended default** — conservative design recommendation for owner review; not a frozen owner decision.
- **Open** — requires a detailed decision before implementation.
- **Deferred** — outside WP-2 or intentionally postponed.

Do not treat recommended defaults as accepted decisions.

## 3. Accepted architecture baseline

The following directions are already accepted and are not reopened by this document:

1. Database-backed durable queue initially; a separate broker may be considered later only if workload evidence justifies it.
2. Transactional outbox/inbox semantics.
3. At-least-once delivery; do not claim exactly-once execution.
4. Leases, bounded retries, recovery and idempotency.
5. Versioned HTTP/JSON contracts with schema validation at boundaries.
6. Unique worker identity and scoped, short-lived/renewable credentials (detailed worker contract belongs to WP-3).
7. Cloud control plane owns authoritative shared workflow state; local worker availability does not determine whether shared state survives.
8. Orchestrator coordinates dependencies; scheduler determines eligibility; workers execute bounded assignments.
9. A worker may update only work for which it holds valid authority and a current lease.
10. Approval, authorization, execution and confirmed external outcome remain separate.
11. No production side effects during P0 acceptance testing.
12. Existing Shorts Studio remains integrated through a bounded adapter, not replaced wholesale.

## 4. Scope and boundaries

### Included in WP-2

- Durable Job and JobAttempt logical records.
- Job eligibility and dependency-aware dispatch.
- Atomic lease claim, ownership, heartbeat and expiry.
- Attempt history and stale-attempt protection.
- Bounded retries and structured failure classification.
- Idempotency for commands and event consumption.
- Transactional outbox and inbox processing semantics.
- Workflow/task progression coordination.
- Recovery and reconciliation behavior.
- Deterministic tests for restart, contention, duplicate delivery and stale callbacks.

### Explicitly outside WP-2

- Worker enrollment, machine identity attestation, credential issuer and capability verification — WP-3.
- Artifact binary storage, transfer authorization and quarantine — WP-4.
- Full QA, rights, approval and centralized authorization implementation — WP-5.
- Full end-to-end vertical-slice integration and recovery acceptance — WP-6.
- Provider, hosting region, deployment topology and paid infrastructure selection.
- A dedicated message broker at initial launch.
- Autonomous agent swarms, general-purpose workflow designer or polished Control Center UI.
- Production generation, upload, publishing or other real external side effects.

## 5. Core conceptual model

### 5.1 Workflow

**Owner:** Orchestration layer.  
**Status:** Source-defined in WP-1 and lifecycle standards.

A Workflow is the durable coordination instance for a bounded business process. It references a subject entity and a versioned workflow definition. It coordinates domain-owned work but does not take ownership of ContentItem, Artifact, QA, rights, approval or publication state.

### 5.2 WorkflowTask

**Owner:** Orchestration layer.  
**Status:** Source-defined in WP-1; detailed execution contract open.

A WorkflowTask is a logical unit in a workflow dependency graph. It expresses what work is required and what prerequisite tasks must be satisfied. A task is not itself a worker attempt.

Recommended conceptual fields:
- `workflow_task_id`
- `workflow_id`
- `task_type`
- `task_definition_version`
- `subject_entity_type`, `subject_entity_id`, where applicable
- `dependency_refs`
- `task_execution_status`
- `required_capabilities`
- `input_refs`
- `result_refs`
- audit fields and `schema_version`

### 5.3 Job

**Owner:** Orchestration / durable execution layer.  
**Status:** Required by Artifact 07; detailed schema open.

A Job is a durable, dispatchable execution request derived from a task or an explicitly authorized operational request. It contains bounded instructions and references, not unrestricted permissions.

Recommended conceptual fields:
- `job_id` — UUIDv7
- `workspace_id`
- `workflow_id`, nullable only for explicitly supported non-workflow jobs
- `workflow_task_id`, where applicable
- `job_type`
- `job_definition_version`
- `job_status` — job-owned execution state
- `priority` — bounded policy-controlled value
- `scheduled_at`
- `available_at`
- `required_capabilities`
- `input_refs`
- `idempotency_scope` and `idempotency_key`, where required
- `current_attempt_id`, nullable before first claim
- `created_at`, `updated_at`
- `schema_version`

Rules:
- A Job is not a ContentItem, WorkflowTask or Artifact.
- A job payload is not an authorization token.
- Job records must not contain credentials or unrestricted secret material.
- Large binaries travel through the artifact boundary, not ordinary job payloads.
- Job creation and dispatch intent must be durably recorded.

### 5.4 JobAttempt

**Owner:** Durable execution layer.  
**Status:** Recommended logical record required to preserve attempt history.

A JobAttempt represents one worker execution attempt for a Job. Each retry creates a new attempt record; it does not erase or reset prior attempt history.

Recommended conceptual fields:
- `job_attempt_id` — UUIDv7
- `job_id`
- `attempt_number`
- `worker_id`, nullable until claim
- `attempt_status`
- `lease_id` or equivalent lease identity
- `lease_expires_at`
- `heartbeat_at`
- `started_at`
- `finished_at`
- `failure_classification`, nullable
- `failure_code`, nullable
- `failure_summary`, bounded and redacted
- `result_refs`
- `created_at`
- `schema_version`

Rules:
- Attempt number is unique within one Job.
- A finished attempt is immutable except for separately recorded reconciliation/annotation events.
- A later attempt does not overwrite the result history of an earlier attempt.
- Only the current valid lease holder may submit a result for the active attempt.
- A stale attempt result is rejected, retained as diagnostic evidence if policy allows, and never becomes the authoritative Job result.

### 5.5 Lease

**Owner:** Durable execution layer.  
**Status:** Accepted concept; exact protocol and numeric parameters open.

A lease is a time-bounded claim granting one worker authority to execute one specific attempt. A lease is not a permanent job assignment and does not grant unrelated capabilities.

Recommended conceptual fields:
- unique lease identity or attempt-bound lease token reference
- `job_id`
- `job_attempt_id`
- `worker_id`
- `claimed_at`
- `expires_at`
- `last_heartbeat_at`
- `revoked_at`, where applicable
- monotonic lease generation or fencing value

Rules:
- Only one active lease may exist for a Job at a time.
- Claim must be atomic under concurrent workers.
- Heartbeat is accepted only from the authenticated current lease holder.
- Expired or revoked leases cannot submit authoritative results.
- Reclaiming a Job creates a new attempt and a newer fencing generation.
- Lease expiry makes work eligible for recovery; it does not prove that the old worker stopped executing.

## 6. Logical lifecycle model

The exact state vocabulary and transition tables are still open. The following is a **recommended conceptual lifecycle**, not an accepted enum freeze.

### 6.1 Job lifecycle candidate

`PENDING → ELIGIBLE → RUNNING → SUCCEEDED`

Recoverable paths:
- `RUNNING → RETRY_WAIT → ELIGIBLE`
- `RUNNING → FAILED_TERMINAL`
- `RUNNING → CANCELLED`
- `RUNNING → UNKNOWN_OUTCOME` when an external side effect may have occurred but cannot yet be confirmed
- `PENDING / ELIGIBLE → CANCELLED`

Important:
- Do not collapse `FAILED_TERMINAL` and `UNKNOWN_OUTCOME`.
- `UNKNOWN_OUTCOME` requires reconciliation before any retry that could duplicate an irreversible effect.
- A terminal failure requires an explicit remediation/requeue policy.
- Whether `ELIGIBLE` is a persisted state or a scheduler-derived condition remains open.

### 6.2 Attempt lifecycle candidate

`CREATED → CLAIMED → RUNNING → SUCCEEDED`

Other outcomes:
- `RUNNING → FAILED`
- `CLAIMED / RUNNING → LEASE_EXPIRED`
- `CLAIMED / RUNNING → CANCELLED`
- `RUNNING → UNKNOWN_OUTCOME`

A JobAttempt records what happened in one execution. The Job records the current aggregate execution status. Their meanings must not be conflated.

### 6.3 WorkflowTask progression

A task becomes dispatchable only when:
- all required predecessor tasks have reached their defined successful terminal condition;
- required inputs and exact-version references exist;
- its schedule/eligibility constraints are met;
- the workflow has not been cancelled, paused or blocked by a governing condition;
- the required execution capability can be satisfied by an eligible worker.

A task completing does not itself authorize a protected external action.

## 7. Dispatch and lease protocol

### 7.1 Eligibility

**Recommended default:**
A scheduler selects only jobs that:
- are in an eligible state;
- are due (`available_at` / `scheduled_at` satisfied);
- have all workflow dependencies satisfied;
- are not cancelled or blocked;
- have not exceeded their permitted attempt policy;
- declare a required capability set;
- are within the applicable workspace and policy scope.

The scheduler does not grant worker permissions. WP-3 verifies worker identity, capability and credential validity at claim time.

### 7.2 Atomic claim

Recommended claim sequence:

1. Worker authenticates using its WP-3 identity and credential.
2. Worker requests work for a declared capability set.
3. Control plane filters eligible jobs within authorized scope.
4. One job is selected and claimed atomically.
5. The claim creates a new JobAttempt and lease identity/generation.
6. Job and attempt state changes commit transactionally.
7. Worker receives a bounded job payload, attempt reference and lease details.
8. Worker begins work only after the claim is confirmed.

Concurrency requirement:
- Two workers racing for the same job must not both receive a valid active lease.
- Claim correctness must be enforced by the authoritative persistence transaction, not by a best-effort pre-check in application memory.

### 7.3 Heartbeat

A heartbeat:
- identifies the worker, job, attempt and lease generation;
- is authenticated and authorized;
- is accepted only for the current active lease;
- updates the lease heartbeat/expiry according to the approved lease policy;
- cannot revive an already superseded attempt;
- does not independently report task success.

Exact heartbeat cadence and expiry thresholds remain open.

### 7.4 Lease expiry and fencing

Lease expiry makes a job eligible for recovery after the approved expiry/reconciliation rules are satisfied.

A fencing value or equivalent monotonically increasing generation is recommended so that a stale worker cannot overwrite a newer attempt's result even if it continues running after losing its lease.

A stale result callback must be rejected based on authoritative attempt/lease identity, not merely on worker-reported timestamps.

Lease expiry does not guarantee the old process has stopped. Any external side effect must separately use idempotency or reconciliation.

## 8. Retry and failure policy

### 8.1 Failure classification

**Recommended conceptual classes:**
- `TRANSIENT` — potentially recoverable infrastructure/network failure.
- `PERMANENT` — invalid input, unsupported operation or deterministic failure requiring correction.
- `POLICY_DENIED` — authorization or policy denied; retry cannot bypass the denial.
- `CAPABILITY_UNAVAILABLE` — no currently eligible worker can perform the job.
- `WORKER_LOST` — worker disappeared or lease expired.
- `UNKNOWN_OUTCOME` — side effect may have occurred but outcome is uncertain.
- `CANCELLED` — work was explicitly cancelled.

The final controlled taxonomy and mappings remain open.

### 8.2 Bounded retry

Accepted baseline requires bounded retries. The following remain open and must not be invented as frozen values:
- maximum attempts by job class;
- backoff algorithm and ceiling;
- jitter policy;
- retryable versus non-retryable failure mapping;
- dead-letter handling;
- manual requeue authority;
- terminal failure remediation process.

**Recommended default:** retry only explicitly classified transient failures and worker-loss cases. Never retry a policy denial to seek a different outcome. Do not blindly retry an operation with an uncertain external side effect.

### 8.3 Attempt history

Every attempt must retain:
- attempt number;
- worker identity;
- claim/start/finish times;
- lease identity/generation;
- outcome;
- structured failure classification and reason;
- bounded diagnostic summary;
- result references;
- correlation and causation context.

Secrets, tokens and sensitive provider payloads must not enter logs or failure summaries.

## 9. Idempotency

**Accepted direction:** retriable commands use idempotency; repeated event delivery must not create duplicate logical effects.

Recommended rules:
1. Idempotency key is scoped to an operation and target resource.
2. Same key plus same canonical request returns the original logical result.
3. Same key plus different canonical request is rejected as a conflict.
4. Idempotency keys are distinct from entity IDs, job IDs, attempt IDs and correlation IDs.
5. Consumers persist event receipt/deduplication identity before applying a logical effect.
6. External operations use provider-side idempotency where supported; otherwise a reconciliation strategy is required.
7. Idempotency retention must cover the approved retry and recovery horizon.

Open parameters:
- key format;
- scope granularity;
- canonical payload comparison method;
- retention duration;
- behavior after retention expiry;
- external provider reconciliation policy.

## 10. Transactional outbox/inbox

### 10.1 Outbox

**Accepted direction:** business state and the corresponding outbox record commit atomically.

Recommended conceptual outbox fields:
- `outbox_event_id`
- `event_type`
- `event_version`
- `aggregate/entity type and ID`
- `workspace_id`
- `occurred_at`, `recorded_at`
- bounded event payload/reference
- delivery status/attempt metadata
- `next_delivery_at`
- correlation/causation references

Rules:
- A rolled-back transaction must not emit an orphan event.
- Pending outbox records survive process restart.
- Delivery may occur more than once.
- Event payloads carry references and metadata, not large media binaries or secrets.
- Outbox delivery does not change the authoritative meaning of the domain event.

### 10.2 Inbox

**Accepted direction:** consumers deduplicate repeated delivery using inbox or equivalent durable receipt semantics.

Recommended conceptual inbox fields:
- `consumer_id`
- `event_id`
- `event_version`
- `received_at`
- processing status
- result/reference to applied effect
- failure classification and retry metadata

Rules:
- Duplicate event receipt must not create a duplicate logical effect.
- Consumer validates schema version, ownership and authorization context before processing.
- A failed consumer transaction must not leave a false completed inbox record.
- Poison-message handling and replay policy are explicit, auditable operations.

### 10.3 Open delivery parameters

Not frozen:
- outbox/inbox retention;
- replay and purge policy;
- delivery ordering guarantees;
- poison-message/dead-letter handling;
- claim/locking strategy;
- maximum batch size and polling cadence.

## 11. Workflow dependency ordering

- Dependencies are explicit references, not inferred from task names or creation order.
- A task is not eligible until its required predecessor conditions are satisfied.
- Dependency evaluation is deterministic and auditable.
- Cycles are rejected at workflow-definition validation time.
- A failed predecessor blocks dependent tasks unless an owner-defined remediation or alternate path applies.
- Cancellation and pause behavior must propagate according to the workflow's defined policy.
- The orchestrator coordinates progression but cannot directly mutate another domain's authoritative business state.

Exact dependency expression language and branching semantics remain open.

## 12. Recovery and reconciliation

### 12.1 Control-plane restart

On restart, the control plane must be able to reconstruct:
- pending and eligible jobs;
- active and expired leases;
- attempt history;
- retry eligibility and next available time;
- undelivered outbox events;
- unprocessed inbox events;
- workflow/task dependency state.

Recovery must use durable records, not process-local memory as the source of truth.

### 12.2 Worker disconnect

If a worker disappears:
- heartbeat stops;
- lease expiry is detected according to the approved policy;
- old attempt is marked expired/lost through an auditable transition;
- job becomes recoverable only after the required safety checks;
- a later claim creates a new attempt and fencing generation;
- stale callbacks from the previous attempt are rejected.

### 12.3 Uncertain external side effects

If an external action may have happened but confirmation is missing:
- record `UNKNOWN_OUTCOME` or the equivalent explicit uncertain state;
- do not blindly retry;
- reconcile using provider reference, idempotency key or an approved read-back process;
- record the reconciliation result as a new attributable fact;
- only then determine whether another attempt is safe.

WP-2 defines this safety behavior but does not authorize live external operations.

## 13. Observability and audit

Every workflow/job/attempt/event path should preserve:
- `workspace_id` and applicable scope;
- `workflow_id`, `workflow_task_id`, `job_id`, `job_attempt_id`;
- `worker_id`, where applicable;
- `event_id`;
- `correlation_id`;
- `causation_id`;
- state version;
- timestamps;
- actor identity/type;
- reason/failure code;
- exact input/output references.

Logs and traces must be structured and redacted. Correlation IDs are for traceability, not authorization.

## 14. Failure-injection and acceptance criteria

The following criteria derive from Artifact 07. They are acceptance targets, not completed test evidence.

| Test | Required result |
|---|---|
| Control-plane restart with pending jobs | Pending work remains durable and recoverable |
| Two workers claim the same eligible job concurrently | At most one active lease is granted |
| Worker heartbeat with wrong lease/worker identity | Rejected |
| Lease expiry | Work becomes recoverable under approved policy |
| Old worker submits result after a newer attempt is active | Stale callback rejected |
| Duplicate event delivery | No duplicate logical side effect |
| Same idempotency key and same request | Original logical result returned |
| Same idempotency key with different request | Conflict rejected |
| Transient failure | Bounded retry policy applied and attempt retained |
| Policy denial | No retry path bypasses denial |
| Terminal failure | Explicit remediation/requeue policy required |
| Outbox transaction rollback | No orphan event is delivered |
| Pending outbox after restart | Delivery resumes safely |
| Duplicate inbox event | Already-applied effect is not repeated |
| Dependency predecessor incomplete | Dependent task is not dispatched |
| Uncertain external side effect | Reconciliation required before unsafe retry |
| Local-only capability unavailable | Work waits durably; no false claim that local execution occurred |

## 15. Open decisions — not frozen

| ID | Open item | Safe handling |
|---|---|---|
| J-01 | Exact Job and JobAttempt field schema | Use logical model above; finalize with WP-1 physical schema |
| J-02 | Job and attempt state vocabularies/transitions | Candidate only; owner/domain transition review required |
| J-03 | Lease duration, heartbeat cadence and expiry grace | Leave unset pending workload and failure analysis |
| J-04 | Retry limits by job class | Require bounded policy; exact numbers open |
| J-05 | Backoff, jitter and retry eligibility | Require explicit classification; exact algorithm open |
| J-06 | Dead-letter and terminal remediation/requeue authority | Require owner-controlled policy |
| J-07 | Fencing token representation and generation semantics | Recommend monotonic generation; physical representation open |
| J-08 | Idempotency key scope, canonicalization and retention | Preserve accepted semantics; detailed parameters open |
| J-09 | Outbox/inbox retention, ordering, replay and poison-message policy | Preserve at-least-once semantics; parameters open |
| J-10 | DB claim/locking and scheduler selection strategy | Provider-neutral design; implementation decision later |
| J-11 | Workflow dependency and branching expression | Explicit DAG baseline; richer branching deferred |
| J-12 | Cancellation/pause semantics across active attempts | Owner review required |
| J-13 | External side-effect reconciliation adapters | No live adapter/production operation in WP-2 |
| J-14 | Numeric resource limits and job-class quotas | Align with worker/job-class policy; values open |

## 16. Dependencies and handoffs

- **WP-1:** supplies approved canonical identities, Workflow and WorkflowTask persistence boundary.
- **WP-3:** supplies authenticated worker identity, credentials, capability checks and heartbeat identity.
- **WP-4:** supplies artifact registration and scoped transfer interfaces.
- **WP-5:** supplies central authorization and hard policy gates before protected actions.
- **WP-6:** validates the full vertical slice and recovery behavior across boundaries.

WP-2 must not invent worker trust, artifact storage, rights or publishing authorization mechanisms.

## 17. Explicit safety boundary

This document does not authorize:
- repository inspection or modification;
- SQL migrations, ORM models, code changes or tests;
- Git operations;
- dependency installation or environment/credential changes;
- running Qoder, OpenCode, Kilo or other agents;
- provider selection, connection, provisioning or paid usage;
- deployment;
- production generation, upload, publishing or other external side effects.

All such actions require their applicable separate authorization.

## 18. Plain-language explanation

Think of a Job as a durable work ticket, a JobAttempt as one specific try at completing it, and a Lease as a temporary claim held by one worker.

If the worker disappears, NEXTDECODE does not lose the ticket. The lease eventually expires, the system records what happened, and a safe retry can be assigned. If an old worker later returns with a result, the system checks whether it still owns the current attempt and rejects stale results.

The outbox/inbox pattern makes sure committed changes can be announced and processed even when components restart or receive duplicate messages.

The important distinction: **durable does not mean blindly repeat everything**. When an external action may already have happened, NEXTDECODE must reconcile before retrying.
