# NEXTDECODE System Architecture & Pipeline
## Part 4 — Persistent Job Queue, Scheduler & Worker Architecture 1.0

**Document status:** Architecture draft  
**Version:** 1.0  
**Purpose:** Define the proposed durable workflow execution model for NEXTDECODE Content OS across its hybrid cloud control plane and local/remote workers.  
**Companion documents:**
- `NEXTDECODE_Master_Blueprint_2.0` — product vision, scope and roadmap.
- `NEXTDECODE_System_Architecture_Pipeline_Part_1_System_Architecture_Master_Reference_1.0` — overall architecture.
- `NEXTDECODE_System_Architecture_Pipeline_Part_2_Shorts_Studio_Pipeline_Contract_1.0` — Shorts Studio pipeline.
- `NEXTDECODE_System_Architecture_Pipeline_Part_3_Shared_Data_Model_Content_Graph_1.0` — data model and Content Graph.

---

## 1. Purpose and core principle

The purpose of the automation engine is to make NEXTDECODE workflows durable, resumable, observable and safe across cloud and local execution environments.

**Core principle: The control plane owns workflow truth; workers execute assigned work; the queue preserves work until it is completed, cancelled or explicitly dead-lettered.**

The system must not lose a task merely because:
- the owner's PC shuts down;
- a local worker disconnects;
- a cloud worker crashes;
- a provider request times out;
- the network becomes unavailable;
- an agent returns malformed output;
- a task needs human review;
- the owner is unavailable for several days.

This is a proposed technical architecture, not evidence that a durable queue or worker fleet currently exists.

## 2. Architecture boundaries

### 2.1 Cloud control plane

The cloud control plane is always-on and authoritative for:
- workflow definitions and runs;
- job records and state transitions;
- schedules and due-time evaluation;
- worker registration and capability records;
- leases and assignment ownership;
- retry and recovery decisions;
- approval and policy state;
- audit events and operational status.

The control plane should continue coordinating supported workflows when the owner's PC is off.

### 2.2 Execution workers

Workers execute assigned tasks. They may run:
- in the cloud;
- on the owner's local PC;
- on future remote machines.

A worker only receives the inputs, credentials and permissions required for its assigned job.

Workers do not own authoritative workflow state and cannot independently authorize public publishing.

### 2.3 Queue and scheduler

The queue holds executable work durably. The scheduler creates or releases jobs when their conditions or due times are met.

The queue and scheduler are related but distinct:
- **Scheduler:** determines when work becomes eligible.
- **Queue:** stores eligible work and manages delivery to workers.
- **Worker:** performs the assigned operation.
- **Orchestrator:** coordinates multi-stage workflow progression and state transitions.

## 3. High-level execution architecture

```text
User / Calendar / Event / Workflow Trigger
                 |
                 v
          Cloud Control Plane
                 |
        Workflow Orchestrator
                 |
          Persistent Scheduler
                 |
          Durable Job Queue
                 |
        Worker Eligibility Check
             /       \
            /         \
     Local Worker   Cloud Worker
            \         /
             \       /
          Result / Artifact Intake
                 |
        Server-side Validation
                 |
         Workflow State Update
                 |
       Next Job / Review / Hold
                 |
        Audit + Monitoring
```

This is a conceptual target design, not a current deployment diagram.

## 4. Core entities and records

Part 3 defines the wider Content Graph. Part 4 adds execution-specific records.

| Entity | Responsibility |
|---|---|
| Workflow Definition | Versioned description of a workflow |
| Workflow Run | One execution instance of a workflow |
| Workflow Step | A named stage within a workflow |
| Job | Durable unit of work offered to a worker |
| Job Attempt | One specific execution attempt |
| Queue Entry | Scheduling and delivery metadata for a job |
| Worker | Registered execution process |
| Worker Capability | Task types and resource constraints a worker supports |
| Worker Heartbeat | Recent worker health and availability |
| Job Lease | Time-bounded assignment ownership |
| Schedule | Time-based or recurring trigger |
| Event | A recorded state change or trigger |
| Retry Record | Retry decision and history |
| Dead-letter Record | Work requiring diagnosis or explicit intervention |
| Execution Log | Sanitized operational diagnostics |
| Artifact Result | Output references returned by a worker |

These are logical entities. They do not imply one table per entity or a specific queue product.

## 5. Job contract

Every job should have a durable, versioned contract.

### 5.1 Proposed job fields

- `job_id`: globally unique identifier.
- `workflow_run_id`: parent workflow execution.
- `content_item_id`: related content item, when applicable.
- `step_key`: workflow stage.
- `job_type`: executable task category.
- `contract_version`: job payload contract version.
- `input_refs`: references to required inputs.
- `required_capabilities`: worker capabilities needed.
- `priority`: configured scheduling priority.
- `status`: authoritative job state.
- `scheduled_at`: earliest eligible time.
- `deadline_at`: optional deadline.
- `attempt_count`: number of attempts made.
- `max_attempts`: policy limit.
- `idempotency_key`: duplicate-submission protection.
- `policy_version`: relevant policy version, where applicable.
- `created_at`, `updated_at`: timestamps.
- `correlation_id`: trace across workflow events and logs.

### 5.2 Payload principles

- Pass references to large artifacts, not large binary files inside queue messages.
- Validate payloads against a versioned schema.
- Include only the minimum data needed by the worker.
- Never place API keys, access tokens or passwords in job payloads.
- Treat all worker output as untrusted until validated by the control plane.
- Keep secrets in a dedicated secret-management mechanism and grant scoped access.

## 6. Job state machine

Proposed job states:

```text
CREATED
   |
   v
QUEUED
   |
   v
LEASED
   |
   v
RUNNING
   |
   +------> SUCCEEDED
   |
   +------> RETRY_WAIT -----> QUEUED
   |
   +------> FAILED
   |
   +------> CANCELLED

Additional controlled states:
PAUSED
BLOCKED
DEAD_LETTER
```

### State meanings

| State | Meaning |
|---|---|
| CREATED | Job record created, not yet eligible for queue delivery |
| QUEUED | Eligible and waiting for a worker |
| LEASED | Temporarily assigned to a worker |
| RUNNING | Worker has acknowledged and started execution |
| RETRY_WAIT | Failed/transient attempt waiting for retry time |
| SUCCEEDED | Result accepted by server-side validation |
| FAILED | Terminal failure under current retry policy |
| CANCELLED | Explicitly cancelled |
| PAUSED | Intentionally paused by workflow control |
| BLOCKED | Cannot proceed until a dependency or policy condition is resolved |
| DEAD_LETTER | Requires diagnosis or owner/operator intervention |

A job must not be marked `SUCCEEDED` merely because a worker reports success. The control plane validates the result and performs the authoritative transition.

## 7. Workflow state versus job state

Workflow, content item, job and worker states must remain separate.

Example:
- Content Item: `IN_PRODUCTION`
- Workflow Run: `RUNNING`
- Current Job: `RETRY_WAIT`
- Worker: `OFFLINE`

These states describe different objects.

A job failure does not automatically mean the entire content item is permanently failed. The orchestrator determines whether to retry, route to another worker, pause, request review or terminate the workflow.

## 8. Worker registration and capability model

### 8.1 Worker registration

Each worker registers:
- worker ID;
- worker type: local or remote;
- software/agent version;
- supported job types;
- capabilities;
- operating environment;
- available resource information where relevant;
- authentication identity;
- status and last heartbeat.

Do not expose unnecessary machine-identifying details in general dashboards or logs.

### 8.2 Capability examples

| Capability | Example tasks |
|---|---|
| `research_light` | Research synthesis and structured extraction |
| `script_generation` | Script drafting and revision |
| `asset_processing` | Image/audio/video asset preparation |
| `short_video_render` | FFmpeg-based Shorts rendering |
| `long_video_render` | Long-form video rendering |
| `qa_validation` | Automated validation and QA |
| `platform_publish` | Authorized platform delivery |
| `analytics_fetch` | Metrics collection |

Capability names are illustrative. Final names and resource requirements should be standardized before implementation.

### 8.3 Worker selection

A worker is eligible only if:
- it is authenticated;
- its heartbeat is within the allowed freshness window;
- it supports the requested job type;
- it meets required resource constraints;
- it has permission to access the job's inputs;
- it is not paused or disabled;
- it can satisfy relevant policy and locality restrictions.

Worker selection should be deterministic and explainable where possible. The scheduler must not assign a render job to a worker that cannot render it.

## 9. Heartbeats and health

Workers periodically report:
- worker ID;
- heartbeat timestamp;
- current status;
- active job and attempt IDs;
- supported capability/version information;
- optional resource health.

If heartbeats stop:
1. Mark the worker as stale or offline after a configured threshold.
2. Do not immediately assume the active job failed.
3. Allow the job lease and execution timeout policy to determine recovery.
4. Reconcile any artifacts or completion messages received later.
5. Record the health transition.

Heartbeat interval and stale thresholds must be configurable and validated under realistic network conditions. Do not hardcode assumptions before testing.

## 10. Job leases and safe assignment

A job lease is a time-bounded claim that a specific worker/attempt owns execution.

### 10.1 Lease requirements

A lease should include:
- job ID;
- attempt ID;
- worker ID;
- lease token or unguessable lease identity;
- issued time;
- expiry time;
- renewal rules.

### 10.2 Lease behavior

- The control plane creates the lease transactionally.
- A worker must acknowledge assignment before execution.
- Long-running tasks renew leases using authenticated heartbeats or lease-renewal calls.
- The control plane validates lease ownership on progress and completion updates.
- An expired lease can be reclaimed according to recovery policy.
- A stale worker cannot update authoritative job state using an expired lease.
- Reassignment creates a new attempt identity; it must not pretend to be the original attempt.

A lease prevents stale ownership from being authoritative. It does not guarantee that two machines can never perform the same physical work if a network partition occurs. Therefore, side-effecting operations also require idempotency and fencing.

## 11. Retries, backoff and failure classification

### 11.1 Failure categories

| Category | Example | Proposed handling |
|---|---|---|
| Transient | Network timeout, temporary provider outage | Retry with backoff |
| Worker failure | Process crash, machine shutdown | Expire lease and reassign/retry |
| Input failure | Missing or invalid input artifact | Block or fail; do not blindly retry |
| Policy failure | Rights or approval gate not satisfied | Block pending resolution |
| Permanent provider error | Invalid request or unsupported operation | Terminal failure or owner intervention |
| Unknown failure | Unclassified exception | Bounded retry, then dead-letter |

### 11.2 Backoff

Use configurable exponential backoff with jitter for eligible transient failures.

The policy should define:
- maximum attempts;
- base delay;
- maximum delay;
- jitter;
- retryable error categories;
- task deadline;
- escalation behavior.

Exact values should be chosen after workload and provider testing. They are not locked in this document.

### 11.3 Dead-letter handling

A job should enter dead-letter handling when:
- retry limits are exhausted;
- repeated deterministic failures occur;
- the job contract is invalid;
- an operator intervention is required;
- automatic recovery is unsafe.

Dead-letter records must preserve the original job, attempts, diagnostics and correlation IDs. Replaying a dead-letter job should require an explicit, auditable action and should create a new attempt or replay record.

## 12. Idempotency and duplicate prevention

At-least-once delivery is a realistic queue model: a worker may receive a job more than once after crashes, timeouts or lost acknowledgements.

Therefore:
- job handlers should be idempotent where practical;
- each attempt has a unique attempt ID;
- job submission uses a stable idempotency key;
- result registration is deduplicated;
- artifact creation checks expected identity/version;
- external publishing uses a separate publication idempotency key;
- a retry must not create duplicate public posts.

Do not assume the queue provides exactly-once execution. Design for duplicate delivery and safe effects.

## 13. Scheduler architecture

The scheduler should support:
- one-time scheduled jobs;
- recurring schedules;
- event-triggered workflows;
- dependency-based release;
- timezone-aware scheduling;
- paused schedules;
- missed-run handling;
- concurrency limits;
- quiet periods where configured;
- schedule versioning and audit.

### 13.1 Scheduling rules

- Store timestamps in UTC.
- Store the intended timezone for user-facing schedules.
- Calculate due times using explicit timezone rules.
- Define what happens when a scheduled time is missed.
- Prevent duplicate creation when the scheduler restarts.
- Use idempotent schedule-run keys.
- Record why a scheduled run was created, skipped or delayed.

### 13.2 Missed schedule behavior

A missed schedule should not automatically publish late.

The system should evaluate:
- whether the content is still relevant;
- whether approvals and policy versions remain valid;
- whether the schedule has expired;
- whether a new time is permitted;
- whether owner notification is required.

Publishing remains subject to the central authorization policy.

## 14. Workflow orchestration

The orchestrator coordinates dependencies between jobs.

Example Shorts workflow:

```text
Research
  -> Claim/Evidence Validation
  -> Script
  -> Storyboard / Shot Plan
  -> Asset Preparation
  -> Render
  -> Technical QA
  -> Content / Rights Gates
  -> Review Package
  -> Approval Policy
  -> Publishing Authorization
  -> Publishing
  -> Analytics
```

Each step should define:
- input contract;
- output contract;
- dependency conditions;
- worker capability requirements;
- timeout and retry policy;
- success criteria;
- failure routing;
- whether human review is required.

A workflow should resume from the last valid persisted step rather than rerunning all previous work unnecessarily.

## 15. PC shutdown and offline recovery

This is a primary acceptance scenario for the hybrid architecture.

### Scenario A — PC is off before a job starts
- Cloud scheduler creates or releases the job.
- Job remains durable in the queue.
- A capable remote worker may execute it.
- If no eligible worker exists, the job remains queued and visible.

### Scenario B — PC shuts down during local rendering
- Worker stops sending heartbeats.
- Lease eventually expires according to policy.
- Control plane marks the attempt interrupted/expired.
- Job becomes eligible for recovery if retry policy permits.
- A compatible remote worker may retry if available; otherwise it waits for the local worker.
- Partial local files are not treated as completed artifacts.
- A later reconnect reconciles local state without allowing stale completion to overwrite current state.

### Scenario C — PC is offline for seven days
- Cloud schedules, research and other supported remote tasks continue.
- Local-only render jobs remain queued unless remote rendering capacity exists.
- Pending approvals remain on hold.
- Alerts and operational summaries are recorded.
- On reconnect, the local worker authenticates, reports health and receives eligible work.

### Scenario D — Network disconnects during a job
- Worker may continue safe local processing if inputs are available.
- It cannot authoritatively complete the job while disconnected.
- It stores results locally and synchronizes after reconnecting.
- Control plane validates attempt/lease state and artifact checksums.
- Stale or conflicting results are quarantined for reconciliation rather than silently accepted.

## 16. Human approval and policy holds

A job that requires human approval should not consume a worker slot while waiting.

Instead:
- workflow transitions to a review/approval wait state;
- approval request is persisted;
- scheduler/queue does not repeatedly dispatch the blocked step;
- approval or rejection emits an event;
- orchestrator resumes, cancels or routes the workflow based on the decision.

Hard rights, safety and validation blockers cannot be bypassed by ordinary approval.

Conditional auto-publishing remains subject to the separate owner-approved policy. This document does not authorize public publishing.

## 17. Observability and operational monitoring

The system should expose:
- queue depth and age;
- jobs by status and priority;
- scheduled jobs due/missed;
- worker availability and stale heartbeats;
- active leases;
- retry and failure rates;
- dead-letter count;
- workflow duration by stage;
- artifact registration failures;
- publishing attempts and outcomes;
- alert history.

Every log/event should carry appropriate correlation IDs:
- workflow run ID;
- job ID;
- attempt ID;
- worker ID;
- content item ID where relevant.

Logs must be sanitized. Never log secrets, access tokens or sensitive credentials.

## 18. Security requirements

- Authenticate every worker.
- Authorize each job assignment and result submission.
- Use short-lived or revocable worker credentials where practical.
- Restrict worker access to assigned inputs and outputs.
- Keep platform credentials outside queue payloads.
- Encrypt communication in transit.
- Audit worker registration, assignment, cancellation and privileged actions.
- Support worker revocation and emergency pause.
- Validate all payloads and artifact references server-side.
- Do not trust agent or worker claims of approval or policy eligibility.

## 19. Technology selection — intentionally open

This document defines capabilities, not a vendor choice.

Evaluate queue/scheduler options against:
- durable storage;
- delivery guarantees;
- delayed and recurring jobs;
- lease/visibility timeout support;
- retries and dead-letter queues;
- idempotency patterns;
- worker concurrency;
- monitoring and operational burden;
- local development support;
- hybrid connectivity;
- cost and free-tier constraints;
- portability and lock-in.

Do not select a queue technology solely because it is already familiar or bundled with a hosting provider. Compare it with the expected workload and operational model.

The database, queue, scheduler and worker runtime may be separate components, but the initial system should avoid unnecessary infrastructure sprawl.

## 20. Acceptance criteria — not yet executed

The architecture is ready for implementation planning when these scenarios have explicit tests:

- [ ] A job survives control-plane process restart.
- [ ] A job survives worker process crash.
- [ ] A local worker going offline does not lose the job.
- [ ] An expired lease cannot authorize a stale completion.
- [ ] A job can be safely reassigned to another eligible worker.
- [ ] Duplicate delivery does not create duplicate artifacts or external side effects.
- [ ] Retry limits and backoff are enforced.
- [ ] Permanent failures reach dead-letter handling with diagnostics.
- [ ] A scheduled job is not created twice after scheduler restart.
- [ ] Timezone and missed-schedule behavior are deterministic.
- [ ] A human approval hold does not cause repeated worker dispatch.
- [ ] A seven-day owner absence does not stop supported cloud workflows.
- [ ] Local-only tasks remain queued when no capable worker is available.
- [ ] Worker credentials can be revoked.
- [ ] Monitoring exposes queue, worker, retry and dead-letter health.

These are future engineering acceptance tests. They have not been executed.

## 21. Open decisions for later parts

| Decision | Status |
|---|---|
| Durable queue required | Architecture requirement |
| Always-on scheduler/control plane | Locked direction |
| Cloud-authoritative job state | Proposed baseline |
| Local and remote worker support | Locked direction |
| Lease-based assignment | Proposed baseline |
| At-least-once delivery + idempotent handlers | Proposed baseline |
| Retry/backoff numerical values | To be tested |
| Heartbeat and lease durations | To be tested |
| Queue technology | Part 8 / technology evaluation |
| Scheduler technology | Part 8 / technology evaluation |
| Remote rendering provider/capacity | Deferred |
| Monitoring/alerting provider | Part 8 |
| Exact job and workflow schemas | Finalize after Parts 5–7 |

## 22. Implementation and repository restrictions

This document does not authorize code changes or repository operations.

Unless the owner explicitly grants new permission:
- do not perform Git/GitHub operations, including read-only operations;
- do not inspect or modify the private repository;
- do not change source, tests, configuration or documentation;
- do not install dependencies or alter environments;
- do not change agent ownership;
- do not deploy or provision paid infrastructure;
- do not run production uploads or public publishing;
- preserve all existing work-in-progress.

When implementation is authorized, begin with a read-only verification and discrepancy report, then implement small isolated milestones with focused tests and independent review.

## 23. Next document — Part 5

**NEXTDECODE System Architecture & Pipeline — Part 5: Agent Contracts & Orchestration 1.0**

Planned topics:
1. Agent roles and boundaries.
2. Agent input/output contracts.
3. Tool permissions and least privilege.
4. Agent-to-agent handoffs.
5. Orchestrator versus agent responsibilities.
6. Human escalation and approval.
7. Context and memory management.
8. Evaluation, testing and audit.
9. Failure recovery and agent timeouts.
10. Existing Qoder, OpenCode and Kilo ownership boundaries.

Part 5 will build on the job and worker contracts defined here. It should not change existing agent ownership.

---

**End of Part 4 — Persistent Job Queue, Scheduler & Worker Architecture 1.0**
