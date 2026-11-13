# NEXTDECODE — P0 Workflow & Job Contract Reconciliation

**Document ID:** `NEXTDECODE_P0_Workflow_Job_Contract_Reconciliation_0.1`  
**Version:** 0.1  
**Date:** 1 November 2026  
**Scope:** Reconciliation of WP-1, WP-2, the P0 Consolidated Contract Appendix, the Unified Lifecycle & State Transition Standard, and the API & Event Contract Standard  
**Status:** DESIGN RECONCILIATION — OWNER REVIEW REQUIRED  
**Detailed contract freeze:** NOT GRANTED  
**Implementation authorization:** NOT GRANTED

---

## 1. Purpose

This note resolves the first workflow/execution boundary questions identified in the P0 cross-document review:

- **X-01:** workflow lifecycle versus execution ownership ambiguity.
- **X-07:** WorkflowTask / Job / JobAttempt cardinality and state mapping.

It preserves accepted ADR-001–ADR-010 and CF-01–CF-24. It does not reopen accepted decisions, freeze physical schema, authorize implementation, or claim runtime/test evidence.

## 2. Sources and authority

The reconciliation uses these project sources:

1. `NEXTDECODE_P0_WP1_Final_Schema_Contract_Candidate_0.3.md`
2. `NEXTDECODE_P0_WP2_Durable_Job_Workflow_Execution_0.1.md`
3. `NEXTDECODE_P0_Consolidated_Contract_Appendix_0.1.md`
4. `NEXTDECODE_Unified_Lifecycle_State_Transition_Standard_1.0.md`
5. `NEXTDECODE_API_Event_Contract_Standard_1.0.md`
6. The accepted ADR/CF baseline and the canonical data dictionary / ownership registry.

Where a detailed candidate document is less specific than an accepted architecture standard, preserve the standard. Where the sources define a concept but leave exact vocabulary, schema, cardinality, or transition behavior open, this note labels the resolution as **PROPOSED**, not accepted.

## 3. Reconciled conceptual model

### 3.1 The four records answer different questions

| Record | Question it answers | Authority / responsibility |
|---|---|---|
| **Workflow** | What bounded business process is being coordinated, for which subject and workflow-definition version? | Orchestration layer owns workflow progression and coordination. |
| **WorkflowTask** | What logical step is required, what are its prerequisites, and has that step satisfied its completion conditions? | Orchestration layer owns task progression and dependency evaluation. |
| **Job** | What bounded, durable unit of executable work has been scheduled or requested? | Durable execution/orchestration boundary owns job scheduling and aggregate execution state. |
| **JobAttempt** | What happened during one worker's particular execution attempt? | Durable execution layer records attempt history and validates lease/fencing authority. |

A worker is an execution identity, not a workflow/task owner. A lease is time-bounded authority for one attempt, not a business approval. A domain entity (ContentItem, Artifact, QA assessment, rights record, approval, publication record, etc.) remains owned by its own domain.

### 3.2 Workflow progression is not a universal business lifecycle

**SOURCE-DEFINED:** The orchestrator owns workflow progression and durable job execution. It coordinates domain-owned work but does not take ownership of ContentItem, Artifact, QA, rights, approval, or publication state.

**PROPOSED resolution:** Treat `workflow_status` as the orchestration instance's own progression state. Do not use it as a mirror of the subject ContentItem lifecycle, a QA outcome, a human approval, an authorization decision, or a publication outcome.

If a separate operational execution projection is required, name it distinctly (for example, `workflow_execution_status`) and define its purpose. Do not add both fields merely to represent the same fact. The exact need for two persisted workflow state dimensions remains **OPEN** pending owner review.

Workflow progression may be based on task results and domain-owned handoff facts, but it must not mutate those domain records directly. It requests transitions from the relevant domain owner and observes the resulting committed events.

### 3.3 Task completion is an orchestration decision

A WorkflowTask is a logical step in a dependency graph, not a worker attempt. A task is dispatchable only when its dependencies, required inputs/exact versions, schedule constraints, workflow controls, policy conditions, and capability requirements are satisfied.

**PROPOSED resolution:** The orchestrator is the sole writer of task progression. Workers report attempt results against a valid JobAttempt/lease; they do not set a WorkflowTask to complete. The orchestrator evaluates the task's declared completion condition using validated job outcomes and any required domain-owned facts/events.

A successful Job is evidence about that Job. It does not automatically mean its parent task is complete, and it never independently means the entire Workflow is complete.

## 4. Relationship and cardinality proposal

The following is the recommended logical relationship model for owner review:

```text
Workflow (1)
  └── WorkflowTask (0..N)
        └── Job (0..N over the task lifecycle)
              └── JobAttempt (1..N once execution begins)
                    └── Lease (one active lease at most per Job;
                               lease is bound to one attempt)
```

Additional constraints:

- A WorkflowTask belongs to exactly one Workflow.
- A Job belongs to one WorkflowTask when task-derived; explicitly supported operational jobs may have no WorkflowTask and must be marked as such.
- A Job may be created later for a task after a prior Job reaches a retry/recovery/remediation outcome. This is distinct from retrying a Job.
- A Job has an ordered attempt history. Each retry/reclaim creates a new JobAttempt; it does not reset or overwrite the earlier attempt.
- At most one active lease may exist for a Job at a time.
- A lease is bound to one JobAttempt and one authenticated worker identity.
- A JobAttempt has one Job parent and a unique attempt number within that Job.
- WorkflowTask dependencies reference other tasks in the same Workflow and must be validated for valid references and cycles.
- A Job's `workflow_id` / `workflow_task_id` references are coordination links; they do not grant access to or ownership of the subject entity.

**Open cardinality detail:** Whether every task-derived Job must be a child row of a task in the physical schema, or whether the relationship is represented through typed references, remains a physical-schema decision. The logical semantics above should remain stable either way.

## 5. State ownership and mapping

### 5.1 State authority matrix

| State / fact | Authoritative writer | Inputs / consumers |
|---|---|---|
| Workflow progression | Orchestrator | Task outcomes, domain events, workflow controls |
| WorkflowTask progression | Orchestrator | Dependency evaluation, validated Job results, required domain handoff facts |
| Job scheduling and aggregate execution outcome | Durable execution/orchestration service | Scheduler, validated attempts, cancellation/pause policy, reconciliation |
| JobAttempt outcome | Durable execution service after validating worker report and current lease/fencing token | Authenticated worker report, lease state, attempt history |
| Lease claim/renewal/expiry/revocation | Durable execution service | WP-3 authenticated worker identity and current credential/capability validation |
| ContentItem lifecycle | Shared Content Graph owner | Orchestrator requests transitions; owner commits and emits event |
| Artifact / ArtifactVersion state | Artifact & Asset Management owner | Studio/worker submits through authorized artifact boundary |
| QA, rights, review, approval, authorization | Contract 07 governance owner | Orchestrator consumes decisions; does not self-authorize |
| Distribution / external operation outcome | Distribution adapter/domain owner, with governance authorization enforced centrally | Provider response and reconciliation evidence |

The worker may submit a result, heartbeat, checkpoint, or failure report. These are inputs to the authoritative execution service, not direct authority to rewrite workflow/task/job state.

### 5.2 Keep state dimensions separate

Do not use one generic `status` column or reuse one enum across these records.

| Record | State field concept | Meaning |
|---|---|---|
| Workflow | `workflow_status` (exact vocabulary open) | Orchestration instance progression |
| WorkflowTask | `task_execution_status` (exact vocabulary open) | Logical step progression |
| Job | `job_status` / execution outcome | Aggregate state of the durable executable request |
| JobAttempt | `attempt_status` | Outcome/progress of one specific execution attempt |
| Lease | lease validity / lifecycle fields | Whether one worker currently holds time-bounded authority |
| Domain entity | Domain-owned lifecycle/state | Business meaning owned outside orchestration |

The Lifecycle Standard provides a recommended job execution vocabulary: `QUEUED`, `LEASED`, `RUNNING`, `RETRY_WAIT`, `SUCCEEDED`, `FAILED`, `CANCEL_REQUESTED`, `CANCELLED`, `TIMED_OUT`, `UNKNOWN_OUTCOME`, and `DEAD_LETTERED`. WP-2 also contains a separate conceptual candidate using `PENDING`, `ELIGIBLE`, `RUNNING`, `RETRY_WAIT`, `SUCCEEDED`, `FAILED_TERMINAL`, `CANCELLED`, and `UNKNOWN_OUTCOME`.

**Reconciliation:** Do not combine these lists into a new frozen enum. Preserve the Lifecycle Standard's vocabulary as the governing reference for the next detailed state-table pass. Resolve WP-2 candidate differences explicitly:
- `PENDING` and `ELIGIBLE` may be queue/scheduler conditions rather than durable Job execution outcomes.
- `FAILED_TERMINAL` may be represented as `FAILED` plus a terminal/retryability disposition, or retained as a distinct state only if the owner chooses that model.
- `LEASED` is a Job/queue aggregate condition; `CLAIMED` is an Attempt progression concept. Avoid duplicating the same state under inconsistent names.
- `LEASE_EXPIRED` is an attempt/lease event or outcome; it should not erase the Job's recovery history.
- `UNKNOWN_OUTCOME` is not equivalent to `FAILED`; reconcile before unsafe retry.

Exact state graphs, transition guards, terminality, reopening, cancellation and pause semantics remain **OPEN** until the detailed transition matrix is reviewed.

## 6. Recommended execution and progression sequence

1. An authorized command requests a Workflow or a task-derived Job. The command response distinguishes acceptance from completion and uses idempotency.
2. The orchestrator creates/records the Workflow and its logical tasks, with explicit dependency references and definition versions.
3. The scheduler evaluates task readiness and Job eligibility. Eligibility does not grant worker permissions.
4. A worker authenticates through WP-3. The execution service checks identity, credential validity, capability, scope, policy and current eligibility.
5. An atomic claim creates a new JobAttempt and attempt-bound lease/fencing generation. The Job/Attempt/lease records commit consistently.
6. The worker executes only after the claim is confirmed, using bounded inputs and capabilities.
7. Heartbeats/checkpoints are accepted only from the current authenticated lease holder. A heartbeat does not mean task success.
8. The worker submits a result against the exact JobAttempt and lease generation.
9. The execution service rejects stale/superseded results, validates the report, records the attempt outcome, and updates the Job aggregate state.
10. The orchestrator evaluates whether the WorkflowTask's declared completion condition is satisfied. If not, it may schedule another Job or await required domain events, subject to policy and bounded retry rules.
11. The orchestrator advances the Workflow only when its own completion conditions are met. It does not infer completion from one successful Job.
12. Each authoritative transition emits an immutable event through the transactional outbox. Consumers process at least once and deduplicate idempotently.

For external operations, an uncertain result must be reconciled before a potentially duplicative retry. Workflow/task completion, human approval, governance authorization, execution, and confirmed provider outcome remain distinct.

## 7. Cancellation, pause, failure and recovery rules

Source-defined requirements to preserve:

- Cancellation is a request, not proof that execution stopped.
- Queued work may be cancelled before lease acquisition.
- Running work should stop at safe checkpoints where possible.
- Workers check pause/cancellation at defined safe points.
- The system records whether cancellation was requested, acknowledged, completed, or impossible.
- Lease expiry makes work eligible for recovery; it does not prove the old worker stopped.
- A newer fencing generation prevents stale workers from committing authoritative results.
- Recovery checks prior committed outputs and side effects before repeating work.
- Policy denial is not a retryable infrastructure failure.
- An uncertain external side effect is reconciled before unsafe retry.
- A terminal failure requires an explicit remediation/requeue policy.
- Pause prevents new eligible work within its scope and does not erase active jobs or audit history.

**Open parameters:** lease duration, heartbeat cadence, expiry grace/reconciliation, retry ceilings, backoff/jitter, dead-letter policy, manual requeue authority, checkpoint requirements, and task-specific completion conditions. No numeric values are proposed as frozen in this document.

## 8. API, command and event boundary

Preserve the API & Event Contract Standard:

- Query APIs are read-only.
- Commands request state changes or work from the owning domain.
- Events report committed facts; they are not commands or permissions.
- Each API/event has one authoritative owner.
- State-changing commands use expected-state-version or equivalent concurrency control.
- Retryable commands use scoped idempotency keys; same key/same request returns the original logical outcome, same key/different request conflicts.
- State transition and outbox record commit atomically where the outbox pattern applies.
- Event delivery is at least once; consumers are idempotent and tolerate delay/duplication/out-of-order delivery.
- A command accepted response is not proof the requested work completed.

### 8.1 Proposed event families (not a final event catalogue)

The following are illustrative event names for the next contract pass, not approved event identifiers:

- `workflow.created`, `workflow.progressed`, `workflow.paused`, `workflow.cancel_requested`
- `workflow_task.created`, `workflow_task.ready`, `workflow_task.completed`, `workflow_task.blocked`
- `job.created`, `job.eligible`, `job.claimed`, `job.started`, `job.retry_scheduled`, `job.completed`, `job.failed`, `job.cancel_requested`
- `job_attempt.created`, `job_attempt.started`, `job_attempt.finished`, `job_attempt.lease_expired`
- `lease.claimed`, `lease.renewed`, `lease.expired`, `lease.revoked`

Before freeze, each event needs an owning aggregate, exact schema, state-version behavior, causation/correlation rules, replay behavior, and compatibility policy. Do not emit an event until its underlying authoritative transition has committed.

## 9. Contract fields: minimum logical boundary

These are logical fields already supported or recommended by the source candidates; this is not a final nullability/DDL declaration.

### Workflow
- `workflow_id` (UUIDv7)
- `workspace_id`
- `workflow_type`
- `workflow_definition_version`
- `subject_entity_type`, `subject_entity_id`
- `workflow_status` (vocabulary open)
- audit timestamps/actor
- `schema_version`

### WorkflowTask
- `workflow_task_id` (UUIDv7)
- `workflow_id`
- `task_type`
- `task_definition_version`
- `subject_entity_type`, `subject_entity_id` where applicable
- dependency references
- `task_execution_status` (vocabulary open)
- `required_capabilities`
- `input_refs`, `result_refs`
- audit fields and `schema_version`

### Job
- `job_id` (UUIDv7)
- `workspace_id`
- `workflow_id` and `workflow_task_id` where applicable
- `job_type`, `job_definition_version`
- `job_status`
- bounded priority and scheduling/eligibility fields
- `required_capabilities`
- `input_refs`
- scoped idempotency fields
- `current_attempt_id` where used
- audit fields and `schema_version`

### JobAttempt
- `job_attempt_id` (UUIDv7)
- `job_id`
- `attempt_number`
- `worker_id` (nullable until claim)
- `attempt_status`
- lease identity / fencing generation reference
- heartbeat/start/finish timestamps
- safe failure classification/code/summary
- `result_refs`
- `schema_version`

### Lease
- lease identity
- `job_id`, `job_attempt_id`, `worker_id`
- claim/expiry/heartbeat/revocation timestamps
- monotonic fencing generation or equivalent

Credentials, access tokens, unrestricted secrets, and large binary payloads do not belong in Job payloads or event envelopes. Large artifacts use the WP-4 artifact boundary.

## 10. Acceptance implications for WP-6

The vertical slice should prove the following with synthetic, non-production data:

1. One Workflow can own multiple dependent WorkflowTasks.
2. A task can create one or more Jobs over its lifecycle without conflating retry and new task work.
3. A Job can have multiple immutable JobAttempts with unique attempt numbers.
4. Concurrent claim attempts cannot produce two valid active leases for one Job.
5. Lease renewal is accepted only for the current authenticated worker/attempt/generation.
6. An expired or superseded worker cannot commit an authoritative result.
7. A Job success does not automatically complete a WorkflowTask or Workflow.
8. The orchestrator alone commits Workflow and WorkflowTask progression.
9. A task's completion condition can include validated Job results and required domain-owned handoff events.
10. Duplicate commands/events do not create duplicate logical work or transitions.
11. State and outbox event are atomic; restart/replay does not lose committed work or repeat external side effects.
12. Cancellation, pause, worker loss, lease expiry, retry, terminal failure and unknown outcome are tested.
13. No workflow/job state implies approval, authorization, or permission to publish.
14. Every transition is attributable and reconstructible/reconcilable from history.

These are proposed acceptance criteria, not test evidence. WP-6 remains unexecuted and independent QA remains pending.

## 11. Open decisions to carry forward

| ID | Open question | Safe handling until resolved |
|---|---|---|
| WJ-01 | Does Workflow need one progression state or separate lifecycle and execution dimensions? | Keep one clearly defined `workflow_status` candidate; do not duplicate state without a distinct use case. |
| WJ-02 | Final Workflow, WorkflowTask, Job and JobAttempt state vocabularies and legal transitions? | Use Lifecycle Standard as governing reference; explicitly reconcile WP-2 candidate names before freeze. |
| WJ-03 | Exact task completion conditions by task type? | Require versioned task definition and explicit completion predicate; no implicit “job succeeded = task complete”. |
| WJ-04 | Physical cardinality/representation of task-to-job links? | Preserve logical 1:N over task lifecycle; defer physical mapping. |
| WJ-05 | Whether operational Jobs without WorkflowTask are in P0 scope? | Keep nullable task link only for explicitly supported, separately classified job types. |
| WJ-06 | Exact cancellation/pause/terminal/reopen semantics? | Preserve request-versus-confirmation distinction; defer exact graph. |
| WJ-07 | Lease, heartbeat, retry, retention and dead-letter numeric parameters? | Configuration decisions after workload/security review; no invented constants. |
| WJ-08 | Final event catalogue and payload schemas? | Treat names in this document as illustrative only. |
| WJ-09 | Exact task/job definition versioning and compatibility rules? | Require explicit versions; define compatibility/migration policy before freeze. |

## 12. Reconciliation outcome

### Resolved at the logical-design level

- Workflow, WorkflowTask, Job, JobAttempt and Lease have distinct responsibilities.
- Orchestration owns Workflow and WorkflowTask progression.
- Durable execution owns Job scheduling/aggregate outcome, attempts and leases within the accepted orchestration boundary.
- Workers report results but do not directly own authoritative workflow/task/job state.
- A task may create multiple Jobs over its lifecycle; a Job may have multiple immutable attempts.
- Job success is not equivalent to task completion or workflow completion.
- Domain-owned business states remain with their owning domains.
- State transitions are attributable, immutable and evented after commit.
- Lease fencing, idempotency, at-least-once delivery and uncertain-outcome reconciliation remain mandatory safeguards.

### Still unresolved

- Exact state enums and transition tables.
- Whether Workflow needs more than one persisted state dimension.
- Task-specific completion predicates.
- Exact physical schema/cardinality constraints.
- Cancellation, pause, terminality and requeue details.
- Numeric operational parameters and final event schemas.

**Conclusion:** X-01 and X-07 are partially resolved at the conceptual ownership and relationship level. They are not fully closed for detailed contract freeze. The next reconciliation should convert the state mapping above into a state-transition matrix, then validate the artifact and worker boundaries against it.

---

**Authority notice:** This document is a proposed reconciliation artifact. It does not grant owner acceptance, detailed contract freeze, implementation authorization, repository access, agent delegation, provider selection, spending, production generation, uploads, or publishing.
