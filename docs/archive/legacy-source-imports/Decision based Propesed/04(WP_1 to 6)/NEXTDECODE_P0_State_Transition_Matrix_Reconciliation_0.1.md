# NEXTDECODE — P0 State-Transition Matrix Reconciliation

**Document ID:** `NEXTDECODE_P0_State_Transition_Matrix_Reconciliation_0.1`  
**Version:** 0.1  
**Date:** 1 November 2026  
**Scope:** Workflow, WorkflowTask, Job, JobAttempt and Lease state ownership, transitions, guards, cancellation, pause, retry, expiry and recovery  
**Status:** DESIGN CANDIDATE — OWNER REVIEW REQUIRED  
**Detailed contract freeze:** NOT GRANTED  
**Implementation authorization:** NOT GRANTED

---

## 1. Purpose

This document advances the Workflow & Job Contract Reconciliation v0.1 by turning its ownership model into a reviewable transition matrix.

It is subordinate to:
- `NEXTDECODE_Unified_Lifecycle_State_Transition_Standard_1.0.md`
- `NEXTDECODE_API_Event_Contract_Standard_1.0.md`
- `NEXTDECODE_P0_WP1_Final_Schema_Contract_Candidate_0.3.md`
- `NEXTDECODE_P0_WP2_Durable_Job_Workflow_Execution_0.1.md`
- `NEXTDECODE_P0_Consolidated_Contract_Appendix_0.1.md`
- `NEXTDECODE_P0_Workflow_Job_Contract_Reconciliation_0.1.md`

This is a logical transition design, not an executable state-machine specification, SQL schema, API catalogue, migration plan, or implementation authorization.

## 2. Status labels and interpretation

- **SOURCE-DEFINED:** directly required by an existing governing project source.
- **ACCEPTED BASELINE:** carried forward from accepted ADR/CF decisions.
- **PROPOSED:** a conservative design candidate for owner review; not accepted merely by appearing here.
- **OPEN:** source material does not settle the point.
- **DEFERRED:** intentionally postponed to a later contract or implementation decision.

The Lifecycle Standard requires separate domain-owned state machines, a common event envelope, explicit transition guards, immutable history, expected-state-version concurrency, idempotency, and transactional outbox semantics. It does not supply final state graphs for Workflow or WorkflowTask. Therefore, Workflow and WorkflowTask states below are explicitly **PROPOSED**, not source-defined enums.

## 3. Universal transition protocol

Every state-changing command should follow this sequence:

1. Authenticate the actor/service/worker identity.
2. Validate workspace and entity scope.
3. Check the required capability and current authorization.
4. Load authoritative state and `state_version`.
5. Validate the source state and requested transition.
6. Evaluate required evidence and transition guards.
7. Check `expected_state_version`.
8. Commit the state change, immutable transition record and outbox record atomically.
9. Return the committed state/version and event reference.

Mandatory rules:
- A stale expected version returns a conflict; it never silently overwrites current state.
- A committed transition increments `state_version` exactly once.
- Same idempotency key + same canonical request returns the original logical result.
- Same idempotency key + different request is rejected.
- Rejected commands do not emit a successful transition event.
- Event delivery is at least once; consumers are idempotent.
- Events represent committed facts, not commands or permissions.
- Corrections append a compensating/superseding/annotation event; they do not rewrite history.
- Only the authoritative owner commits its state machine.
- A projection/cache is not an authorization source if stale.

## 4. Ownership matrix

| Entity / state machine | Authoritative owner | Who may request / provide input | Who commits state |
|---|---|---|---|
| Workflow | Orchestration layer | Authorized caller; task/job/domain events | Orchestrator |
| WorkflowTask | Orchestration layer | Scheduler, validated job results, domain handoff events | Orchestrator |
| Job | Durable execution / orchestration boundary | Orchestrator, scheduler, authorized operational command, worker reports | Durable execution service |
| JobAttempt | Durable execution layer | Authenticated worker reports, lease/recovery service | Durable execution service |
| Lease | Durable execution layer, with WP-3 identity verification | Authenticated worker claim/heartbeat; credential/trust revocation | Durable execution service |
| Domain business state | Its canonical domain owner | Orchestrator requests transition; domain events provide facts | That domain owner only |

Workers do not directly complete Workflow or WorkflowTask. Workers submit attempt-scoped results. The execution service validates and records the attempt/job result; the orchestrator evaluates task/workflow completion.

## 5. Proposed state vocabularies

### 5.1 Workflow — proposed, not frozen

Candidate progression states:

`DRAFT`, `ACTIVE`, `PAUSED`, `BLOCKED`, `COMPLETED`, `CANCELLED`

Interpretation:
- `DRAFT`: workflow instance exists but has not been started.
- `ACTIVE`: orchestration may progress eligible tasks.
- `PAUSED`: new work in scope must not start; active work follows safe pause/checkpoint rules.
- `BLOCKED`: a required dependency, domain condition, policy condition or owner-controlled intervention prevents progression.
- `COMPLETED`: all declared completion conditions have been satisfied.
- `CANCELLED`: cancellation has been confirmed for the workflow's orchestration scope; this does not claim that an already-submitted external operation was undone.

**OPEN:** Whether `BLOCKED` is a persisted workflow state or a derived hold reason; whether `DRAFT` is required for all workflows; whether a completed workflow can be reopened. Do not add `FAILED` as a generic workflow state until the owner decides whether failure is a terminal progression state or an aggregate of task/job outcomes.

### 5.2 WorkflowTask — proposed, not frozen

Candidate progression states:

`WAITING`, `READY`, `RUNNING`, `BLOCKED`, `SUCCEEDED`, `FAILED`, `CANCELLED`

Interpretation:
- `WAITING`: prerequisites are not yet satisfied.
- `READY`: prerequisites and dispatch conditions are satisfied.
- `RUNNING`: one or more associated Jobs are executing or task work is in progress.
- `BLOCKED`: required input, policy/domain handoff, capability or owner intervention prevents progression.
- `SUCCEEDED`: the task's versioned completion predicate has been satisfied.
- `FAILED`: the task has reached a terminal failure disposition under its definition/policy.
- `CANCELLED`: task cancellation has been confirmed.

**OPEN:** Task-specific completion predicates, whether `FAILED` is terminal or remediable, whether a task can return from `BLOCKED` to `READY`, and how multiple Jobs combine into one task outcome.

### 5.3 Job — governing reference and reconciliation

The Lifecycle Standard's recommended execution vocabulary is the governing reference for this pass:

`QUEUED`, `LEASED`, `RUNNING`, `RETRY_WAIT`, `SUCCEEDED`, `FAILED`, `CANCEL_REQUESTED`, `CANCELLED`, `TIMED_OUT`, `UNKNOWN_OUTCOME`, `DEAD_LETTERED`

The WP-2 candidate also uses `PENDING`, `ELIGIBLE`, and `FAILED_TERMINAL`. Reconciliation:
- `PENDING` and `ELIGIBLE` should initially be treated as scheduler/queue eligibility conditions, not automatically as separate persisted execution outcomes.
- `LEASED` is the Job-level aggregate indication that a current attempt has an active lease.
- `CLAIMED` belongs to the Attempt progression, not a duplicate Job state.
- `FAILED_TERMINAL` is not added to the governing list. Terminality/retryability should be represented by explicit failure disposition and policy unless the owner chooses a distinct state.
- `UNKNOWN_OUTCOME` remains distinct from `FAILED`.

### 5.4 JobAttempt — proposed vocabulary

Candidate attempt progression:

`CREATED`, `CLAIMED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `LOST`, `CANCELLED`, `REJECTED_STALE`

Semantics:
- Every execution attempt has a new immutable identity and unique attempt number within its Job.
- `LOST` means the attempt lost its valid execution authority or its worker disappeared; it does not prove the process stopped.
- `REJECTED_STALE` is preferably a result-submission disposition/event rather than a mutation of an already finished attempt. Exact representation remains open.
- `LEASE_EXPIRED` is primarily a lease transition/event; the attempt may be classified `LOST` after recovery rules determine its disposition.
- A finished attempt is immutable except for separately recorded reconciliation/annotation events.

### 5.5 Lease — proposed vocabulary

Candidate lease states:

`ACTIVE`, `EXPIRED`, `RELEASED`, `REVOKED`

A lease is bound to exactly one Job, JobAttempt and worker identity. At most one active lease may exist for a Job. Lease generation/fencing value must increase when a newer attempt takes authority.

## 6. Workflow transition matrix — proposed

| From | Command / trigger | To | Required guards | Owner / notes |
|---|---|---|---|---|
| DRAFT | Start workflow | ACTIVE | Definition/version valid; subject/scope valid; caller authorized; initial conditions satisfied | Orchestrator |
| ACTIVE | Pause workflow | PAUSED | Authorized pause request; scope explicit | Blocks new work; active work receives safe-point signal |
| PAUSED | Resume workflow | ACTIVE | Pause release authorized; current policy/credentials and task conditions re-evaluated | Resume does not restore expired authorization |
| ACTIVE | Blocked condition detected | BLOCKED | Specific blocker and reason recorded; owner/policy evidence referenced | Orchestrator records its own hold; does not mutate domain blocker |
| BLOCKED | Blocker cleared / condition revalidated | ACTIVE | Authoritative blocker owner confirms resolution; fresh policy/authorization evaluation where required | Orchestrator |
| ACTIVE | Completion conditions satisfied | COMPLETED | All required tasks/hand-offs satisfy versioned workflow definition; no unresolved required work | Orchestrator |
| DRAFT / ACTIVE / PAUSED / BLOCKED | Cancel workflow | CANCELLED | Authorized cancellation; cancellation semantics applied to child tasks/jobs; external operations reconciled separately | Request and confirmed outcome must be distinguishable |
| COMPLETED | Reopen / amend | OPEN | No source-defined reopening rule | Owner decision required; safer default is new workflow/version rather than silently reopening |

**Important:** Workflow completion is not inferred from one Job's success. A workflow does not become publish-authorized because it is `COMPLETED`.

## 7. WorkflowTask transition matrix — proposed

| From | Command / trigger | To | Required guards | Owner / notes |
|---|---|---|---|---|
| (created) | Evaluate dependencies | WAITING or READY | Workflow exists; task definition/version valid; dependencies validated and acyclic | Orchestrator |
| WAITING | All prerequisites satisfied | READY | Required predecessor completion conditions met; inputs/exact versions exist; workflow active; policy/eligibility conditions pass | Orchestrator |
| READY | Dispatch / work begins | RUNNING | Job created/associated or explicitly supported internal task execution begins; worker permissions validated at claim | Job acceptance is not task completion |
| RUNNING | All task completion predicates satisfied | SUCCEEDED | Validated results and required domain-owned handoff facts present; exact input/output versions resolved | Orchestrator |
| RUNNING | Recoverable failure / work needs retry | READY or BLOCKED | Job failure classified; retry/re-execution policy allows another Job; bounds not exceeded | New Job may be created; attempt retry is separate |
| READY / RUNNING | Blocking condition | BLOCKED | Reason, owner and evidence recorded; no implicit policy bypass | Orchestrator records coordination hold |
| BLOCKED | Required condition cleared | READY or WAITING | Blocker owner confirms resolution; dependencies re-evaluated | Recompute readiness |
| WAITING / READY / BLOCKED | Workflow/task cancellation confirmed | CANCELLED | Authorized cancellation; child work handled under cancellation rules | Running work may require checkpoint/acknowledgement |
| RUNNING | Terminal task failure | FAILED | Versioned task policy says no further permitted recovery; evidence and reason recorded | Remediation/reopen semantics open |
| FAILED | Remediate / retry task | OPEN | Source does not define whether same task reopens or a new task version/instance is created | Owner decision; preserve history |

**Task completion rule:** A Job success is an input to the task's completion predicate, not an unconditional transition to `SUCCEEDED`.

## 8. Job transition matrix — governing states, detailed guards proposed

| From | Trigger | To | Required guards / behavior |
|---|---|---|---|
| (created) | Durable submission | QUEUED | Job and dispatch intent persisted; schema and scope valid; idempotency applied |
| QUEUED | Atomic worker claim | LEASED | Worker authenticated/trusted; capability and authorization valid; job eligible; no active lease; new attempt and lease committed atomically |
| LEASED | Worker starts | RUNNING | Current lease/attempt/fencing generation valid; worker starts only after claim confirmation |
| LEASED / RUNNING | Retryable failure or worker loss | RETRY_WAIT | Failure class explicitly retryable; bounded retry policy permits; no unsafe unknown side effect |
| RETRY_WAIT | Backoff/eligibility condition met | QUEUED | Job re-enters dispatchable queue; fresh claim will create a new attempt |
| RUNNING | Valid result accepted | SUCCEEDED | Current worker/attempt/lease/fencing token valid; output refs validated; completion accepted by execution owner |
| QUEUED | Cancel before claim | CANCELLED | Authorized request; no active attempt; cancellation committed |
| LEASED / RUNNING | Cancel requested | CANCEL_REQUESTED | Authorized request; signal worker; record request separately from completion |
| CANCEL_REQUESTED | Worker acknowledges and stops safely | CANCELLED | Stop/checkpoint evidence recorded; no claim that external submitted action was undone |
| RUNNING | Execution deadline exceeded | TIMED_OUT or recovery disposition | Timeout policy and evidence applied; inspect side effects before retry |
| RUNNING / TIMED_OUT | Side effect may have happened, result unknown | UNKNOWN_OUTCOME | Reconciliation required; no blind retry for non-idempotent operation |
| UNKNOWN_OUTCOME | Reconciliation confirms success | SUCCEEDED | Authoritative evidence confirms the effect/result |
| UNKNOWN_OUTCOME | Reconciliation confirms no effect and retry is safe | RETRY_WAIT or QUEUED | Evidence and idempotency/retry policy support safe retry |
| UNKNOWN_OUTCOME | Still ambiguous | UNKNOWN_OUTCOME | Remain blocked from unsafe retry; route for reconciliation/owner decision |
| QUEUED / RETRY_WAIT / FAILED | Retry budget exhausted or terminal disposition | DEAD_LETTERED | Preserve full history; replay/remediation requires authorized process |
| DEAD_LETTERED | Authorized replay/remediation | QUEUED or new Job | Explicit replay actor/reason; fresh policy/credential checks; preserve previous attempts |

**Open:** Whether `TIMED_OUT` is a transient Job state, terminal state, or a failure classification. The governing vocabulary lists it; the exact transition and recovery semantics need an explicit decision.

## 9. JobAttempt transition matrix — proposed

| From | Trigger | To | Required guards / behavior |
|---|---|---|---|
| (created) | Atomic claim creates attempt | CLAIMED | Unique attempt number; Job claim committed; lease bound to attempt and worker |
| CLAIMED | Worker begins execution | RUNNING | Current lease and fencing generation valid |
| RUNNING | Valid worker result accepted | SUCCEEDED | Result submitted by current authenticated lease holder; execution service validates and commits |
| CLAIMED / RUNNING | Classified execution failure | FAILED | Failure classification and safe diagnostics recorded |
| CLAIMED / RUNNING | Lease expires / worker disappears | LOST | Expiry/recovery evidence recorded; expiry does not prove worker stopped |
| CLAIMED / RUNNING | Cancellation completed | CANCELLED | Stop acknowledgement/safe checkpoint or equivalent confirmed state |
| Any non-authoritative stale callback | Result submission arrives after supersession | REJECTED_STALE disposition/event | Reject as authoritative result; retain diagnostic evidence only if policy allows |
| Finished attempt | Correction/reconciliation annotation | Same terminal state + appended event | Do not mutate historical attempt result |

A retry of the same Job creates a new JobAttempt. Do not reset an old attempt from `FAILED` or `LOST` back to `RUNNING`.

## 10. Lease transition matrix — proposed

| From | Trigger | To | Required guards / behavior |
|---|---|---|---|
| (not created) | Successful atomic claim | ACTIVE | One active lease per Job; binds Job, Attempt, Worker and fencing generation |
| ACTIVE | Valid heartbeat/renewal | ACTIVE | Authenticated current holder; same attempt and generation; renewal policy allows it |
| ACTIVE | Expiry threshold reached | EXPIRED | Authoritative time/lease policy; mark expiry; do not infer worker process termination |
| ACTIVE | Explicit safe release | RELEASED | Current holder or authorized controller; execution stopped/checkpointed as required |
| ACTIVE | Credential revocation, trust loss or authorized control action | REVOKED | Security revocation takes precedence; stale worker cannot commit |
| EXPIRED / REVOKED | Old worker submits result | No transition to active | Reject stale result using attempt identity and fencing generation |
| EXPIRED / REVOKED / RELEASED | New worker claims Job | New Lease ACTIVE | New JobAttempt and strictly newer fencing generation |

**Open:** Lease expiry grace, renewal cadence, clock source/precision, release conditions, fencing representation and whether lease history is a separate canonical entity or an immutable attempt-bound record.

## 11. Cross-state invariants

1. A WorkflowTask belongs to one Workflow.
2. A task-derived Job references one WorkflowTask; explicitly supported operational jobs must be separately classified.
3. A Job retains one logical identity across its attempts.
4. Every JobAttempt has a unique attempt number within its Job.
5. Every lease binds to one JobAttempt and one worker identity.
6. At most one active lease exists per Job.
7. New authority uses a newer fencing generation.
8. A stale attempt cannot commit an authoritative Job result.
9. Job success does not imply task success.
10. Task success does not imply workflow completion unless the workflow definition's completion conditions are satisfied.
11. Workflow completion does not imply human approval, governance authorization or publication.
12. A policy denial is not retryable to obtain a different authorization result.
13. Unknown external outcomes are not treated as failure or success until reconciled.
14. Cancellation request, acknowledgement, completion and impossibility are distinguishable.
15. Pause blocks new scoped work; it does not erase or cancel existing work automatically.
16. Releasing a pause triggers fresh policy/authorization checks.
17. Event ordering is by entity `state_version`, not wall-clock timestamps.
18. Every committed transition has an immutable, attributable event/audit record.
19. At-least-once event delivery requires idempotent consumers.
20. Recovery preserves attempt history and checks prior committed outputs/side effects.

## 12. Required transition record and event envelope

For each committed transition, retain at minimum:
- event ID and event/schema version;
- entity type and ID;
- prior state and new state;
- `state_version`;
- actor/service/worker identity;
- workspace scope;
- reason code and bounded reason metadata;
- `occurred_at` and `recorded_at` in UTC;
- correlation ID and causation reference;
- trace/span references where available;
- workflow/job/task/attempt/lease references as relevant;
- policy/evidence references where the transition requires them.

The common lifecycle envelope remains authoritative. Do not invent a parallel event envelope for this package.

## 13. Required negative and recovery tests for WP-6

### Ownership and state integrity
- [ ] Worker cannot directly set Workflow or WorkflowTask state.
- [ ] Consumer cannot write another domain's authoritative state.
- [ ] Illegal source-to-destination transition is rejected.
- [ ] Stale expected state version returns conflict.
- [ ] State version increments exactly once on commit.
- [ ] Rejected transition emits no success event.

### Workflow and task
- [ ] Workflow cannot complete while a required task remains incomplete/blocked.
- [ ] Task cannot become READY while a required predecessor is incomplete.
- [ ] Job success alone cannot complete a task whose completion predicate is not met.
- [ ] Task completion alone cannot complete a workflow whose other conditions are unmet.
- [ ] Pause blocks new work within scope.
- [ ] Resume re-evaluates dependencies, credentials and policy.

### Job, attempt and lease
- [ ] Concurrent claims produce at most one valid active lease.
- [ ] Attempt number is unique within a Job.
- [ ] Retry creates a new attempt and preserves prior attempt history.
- [ ] Heartbeat from wrong worker/attempt/generation is rejected.
- [ ] Expired/revoked lease cannot commit an authoritative result.
- [ ] Old worker result after a newer fencing generation is rejected.
- [ ] Lease expiry does not assume the worker stopped.
- [ ] Recovery checks prior outputs/checkpoints before repeating work.

### Cancellation, failure and uncertain outcomes
- [ ] Cancellation request is distinguishable from completed cancellation.
- [ ] Running work stops at a safe checkpoint where possible.
- [ ] Policy denial does not enter automatic retry.
- [ ] Retry ceiling/dead-letter behavior preserves history.
- [ ] Unknown non-idempotent external outcome is reconciled before retry.
- [ ] Provider timeout after possible submission becomes `UNKNOWN_OUTCOME`.
- [ ] Pause release does not automatically authorize a previously blocked action.

### Events and durability
- [ ] State and outbox event commit atomically.
- [ ] Duplicate event delivery does not duplicate logical effects.
- [ ] Out-of-order events are handled by `state_version`.
- [ ] Restart recovers pending jobs/outbox/inbox and expired leases safely.
- [ ] Replay preserves original event identity and does not repeat external effects by default.

No tests are claimed as executed by this design document.

## 14. Open decisions

| ID | Decision still required | Why it matters | Safe default until decided |
|---|---|---|---|
| STM-01 | Ratify Workflow vocabulary and whether `BLOCKED` is persisted or derived | Defines orchestration lifecycle and reporting | Treat vocabulary as proposed only |
| STM-02 | Ratify WorkflowTask vocabulary and task completion predicates | Prevents premature completion | Require versioned explicit predicates |
| STM-03 | Final Job transition graph, especially `TIMED_OUT`, `FAILED`, `DEAD_LETTERED` | Retry and terminal semantics | Preserve Lifecycle Standard names; do not infer terminality |
| STM-04 | Final JobAttempt vocabulary and stale-result representation | Historical integrity and observability | Keep attempt immutable; stale callback is a rejected disposition/event |
| STM-05 | Lease expiry, fencing, release and renewal protocol | Prevents split-brain execution | Current-holder validation and monotonic fencing mandatory; numbers deferred |
| STM-06 | Cancellation semantics across active jobs and external operations | Avoids claiming effects were undone | Request/acknowledge/complete/impossible remain distinct |
| STM-07 | Workflow/task reopening and remediation semantics | Avoids rewriting terminal history | Prefer new workflow/task version or explicit remediation record |
| STM-08 | Failure taxonomy, retryability, max attempts, backoff and dead-letter policy | Operational safety/cost | Bounded retries; no numeric values frozen |
| STM-09 | Event catalogue and exact payload schemas | Interoperability and compatibility | Use common envelope; illustrative event names only |
| STM-10 | Exact task-to-job physical cardinality and operational job exceptions | Schema integrity | Logical 1:N over task lifecycle; exception types explicitly declared |

## 15. Reconciliation result

### Clarified in this candidate
- State ownership and command authority across all five records.
- Proposed Workflow and WorkflowTask progression states.
- Reconciliation of the Job vocabulary against the governing Lifecycle Standard.
- Separate Attempt and Lease progression.
- Guards for cancellation, pause, retry, lease expiry, stale results and unknown outcomes.
- Cross-state invariants and WP-6 negative/recovery test requirements.

### Not closed
- No final Workflow/WorkflowTask enums have been owner-ratified.
- Exact state graphs, terminality and reopening remain open.
- Numeric lease/retry parameters remain open.
- Event catalogue and physical schema remain open.
- No implementation, runtime, test or independent QA evidence is claimed.

**Conclusion:** The matrix is ready for owner review as a detailed design candidate. It is not ready to be called a frozen contract until the open decisions are resolved or explicitly deferred by the owner.

---

**Authority notice:** This document does not grant detailed contract freeze, implementation authorization, repository access, agent delegation, provider selection, spending, production generation, uploads, distribution or publishing.
