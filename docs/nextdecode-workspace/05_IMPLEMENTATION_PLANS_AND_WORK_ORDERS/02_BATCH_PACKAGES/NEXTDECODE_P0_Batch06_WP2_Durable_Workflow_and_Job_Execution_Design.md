NEXTDECODE CONTENT OS

# P0 Batch 06
WP-2 Durable Workflow & Job Execution Design

Design working pack • 01 November 2026

Purpose: define a reviewable candidate contract for durable workflow orchestration and job execution. It builds on the WP-1 domain/persistence candidate while keeping execution, authorization, worker trust, artifact handling and distribution responsibilities separate. This document is not frozen and does not authorize code changes, migrations, agent runs or production execution.

## 1. Status and use

| Label | Meaning |
| --- | --- |
| ACCEPTED DIRECTION | A recorded owner-accepted architecture decision or invariant. |
| DESIGN CANDIDATE | A proposed execution model that must be reconciled with authoritative source contracts. |
| SOURCE REQUIRED | Exact behavior, field names, enum values or thresholds are not verified in the current source set. |
| OWNER DECISION | A genuinely owner-reserved decision; do not infer approval. |
| NOT AUTHORIZED | No implementation, runtime execution, deployment or external action is permitted by this pack. |

This is the WP-2 design candidate. The exact original CF wording and full authoritative source inventory remain incomplete as recorded in Batch 04. Therefore, every candidate below must be checked against the original CF source pack, lifecycle/state contract, API/event contract and approved WP-2 specification before contract freeze.

## 2. WP-2 mission and boundaries

| WP-2 owns | WP-2 does not own |
| --- | --- |
| Durable job lifecycle and orchestration behavior | Canonical domain identity and core persistence schema (WP-1) |
| Workflow instance progression and stage coordination | Worker identity, trust lifecycle and credential issuance (WP-3) |
| Queue delivery, retry scheduling and execution-attempt coordination | Binary artifact transfer/storage implementation (WP-4) |
| Idempotent dispatch semantics and recovery behavior | Central policy definitions and full rights/approval governance (WP-5) |
| Cancellation, timeout, lease and dead-letter behavior | End-to-end integrated vertical-slice sign-off (WP-6) |
| Job event production and traceable execution history | Direct publishing or external side effects outside approved gates |

WP-2 consumes WP-1 persistence primitives and calls WP-3 worker assignment boundaries. It must not embed a parallel authorization authority or bypass WP-5 governance.

## 3. Governing invariants

- Queue delivery is at-least-once; the system must not assume exactly-once execution.

- Idempotency keys and durable attempt records prevent duplicate logical side effects and preserve retry traceability.

- Approval, authorization, execution and confirmed external outcome are distinct facts.

- Centralized authorization remains authoritative; queue possession or worker capability is not permission.

- Workers execute bounded assignments and cannot self-expand scope.

- Unknown or ambiguous rights, approval or authorization fail closed for protected operations.

- Every job and attempt is correlated to the relevant workflow, content/version, actor or service principal, and evidence.

- Artifacts are registered/versioned and integrity-checked through WP-4 contracts; WP-2 does not own binary storage.

- Local-only work must wait safely when the local worker is unavailable; no paid or cloud fallback is implied.

- Human approval is required before critical publishing actions; automatic public publishing remains disabled pending separate policy.

## 4. Candidate execution model

| Concept | Candidate meaning | Required separation |
| --- | --- | --- |
| Workflow definition | Versioned description of stages, dependencies and routing | Definition is not a running workflow instance. |
| Workflow instance | One execution of a workflow for a target and version | Owns orchestration progress, not content lifecycle. |
| Job | A durable unit of bounded work with inputs, constraints and expected outputs | Job identity is not an attempt identity. |
| Execution attempt | One worker's attempt to perform a job | Each retry creates a distinct attempt record. |
| Queue message | A delivery notification/reference to durable job state | Message is not the authoritative job record. |
| Lease | Time-bounded claim to work by a worker | Lease expiry permits recovery; it does not prove the prior worker stopped. |
| Job event | Append-only record of a material execution transition | Event history supplements authoritative current state. |
| Idempotency record | Scoped key and stored result/side-effect association | Deduplicates logical requests, not distinct legitimate jobs. |
| Outbox event | Transactionally persisted event awaiting publication | Prevents DB commit/event publication gap. |
| Inbox receipt | Deduplication record for consumed event/message | Prevents repeated message delivery from repeating processing. |

## 5. Candidate job lifecycle

The lifecycle below is a design proposal. Exact enum names, allowed transitions and terminal-state rules are SOURCE REQUIRED until verified against the governing lifecycle contract.

| Candidate state | Meaning | Allowed transition examples | Guard / note |
| --- | --- | --- | --- |
| CREATED | Job request persisted but not eligible for dispatch | READY, CANCELLED | Validate request, idempotency and dependencies. |
| READY | All prerequisites satisfied and job eligible | QUEUED, BLOCKED, CANCELLED | Authorization must be checked at the correct action boundary. |
| QUEUED | Durably available for worker claim | LEASED, CANCELLED | Queue message is a wake-up/reference, not source of truth. |
| LEASED | A worker has claimed the job for a bounded period | RUNNING, READY, UNKNOWN_OUTCOME, CANCELLED | Lease token/version prevents stale worker updates. |
| RUNNING | Attempt is actively executing | SUCCEEDED, FAILED, RETRY_WAIT, CANCEL_REQUESTED, UNKNOWN_OUTCOME | Heartbeat/progress is observational, not proof of success. |
| RETRY_WAIT | Retry scheduled for a future time | QUEUED, CANCELLED, DEAD_LETTERED | Retry policy is bounded and class-specific. |
| CANCEL_REQUESTED | Cancellation requested while work may still be running | CANCELLED, UNKNOWN_OUTCOME, SUCCEEDED | Cancellation is cooperative; do not assume side effect did not occur. |
| SUCCEEDED | Logical job completed with validated result | (terminal) | Requires output/evidence validation, not merely worker exit code. |
| FAILED | Job failed without further automatic retry | (terminal or explicit requeue policy) | Failure classification and operator disposition retained. |
| CANCELLED | Cancellation confirmed without unresolved external outcome | (terminal) | Do not use if side-effect outcome is uncertain. |
| DEAD_LETTERED | Retry/processing policy exhausted or job quarantined | (terminal pending explicit disposition) | Requires reason and traceable operator action. |
| UNKNOWN_OUTCOME | Execution may have produced an effect but confirmation is unavailable | RECONCILIATION_REQUIRED | Never blindly replay non-idempotent external side effects. |

## 6. Workflow lifecycle and orchestration

| Workflow stage | Candidate responsibility | Exit evidence |
| --- | --- | --- |
| Instantiate | Create workflow instance bound to definition version and target version | Stable workflow ID, definition version, target reference |
| Resolve dependencies | Determine prerequisites and dependency graph | Resolved dependency set and validation result |
| Authorize dispatch | Request centralized authorization for the intended action and scope | Policy decision reference; deny or defer if absent |
| Schedule | Create durable jobs and outbox records transactionally | Persisted job IDs and outbox event IDs |
| Dispatch | Deliver queue reference to eligible worker pool | Delivery/claim correlation; no assumption of execution |
| Execute | Track worker attempt, lease, heartbeat and result | Attempt record, logs/evidence and output references |
| Validate | Validate outputs and required evidence | Structured validation result |
| Advance | Mark stage complete and schedule next eligible stage | Transition event and next-stage job reference |
| Reconcile | Resolve uncertain outcomes, stale leases and partial failures | Explicit reconciliation record and disposition |
| Complete | Mark workflow terminal only when all required stages meet contract | Workflow completion evidence and final state |

A workflow stage may produce multiple jobs; one job may be retried through multiple attempts. These relationships must be explicit and traceable.

## 7. Queue and delivery contract

| Concern | Candidate rule | Questions requiring source/owner confirmation |
| --- | --- | --- |
| Delivery guarantee | At-least-once | Confirm no source contract assumes exactly-once delivery. |
| Durable source | Database-backed job state plus transactional outbox/inbox initially | Verify transaction boundary and event publication semantics. |
| Claim operation | Atomic claim with lease token, worker identity and lease expiry | Define isolation/locking strategy and stale claim handling. |
| Visibility timeout | Lease duration and heartbeat policy per job class | Numeric values deferred; derive from measured workload classes. |
| Ordering | No global FIFO assumption unless a workflow dependency requires it | Define per-key ordering requirements, if any. |
| Concurrency | Bounded by worker capability, job class and resource policy | Exact limits deferred; central policy must remain authoritative. |
| Backpressure | Stop or defer dispatch when eligible capacity is unavailable | Define queue age/pressure thresholds from operational evidence. |
| Poison messages | Quarantine with diagnostic reason and correlation | Define operator disposition and safe replay rules. |
| Duplicate delivery | Consumer idempotency and durable inbox receipt | Define message identity and deduplication retention. |
| Outbox relay | Retry publication until acknowledged; publish stable event IDs | Define ordering and poison-event handling. |
| Inbox processing | Record receipt and processing outcome atomically where possible | Define duplicate and partial-commit behavior. |

## 8. Retry, timeout and recovery policy

| Failure class | Candidate response | Replay safety |
| --- | --- | --- |
| Transient infrastructure failure before work starts | Release/requeue with bounded backoff | Usually safe if no side effect began; verify attempt state. |
| Worker disappears / lease expires | Mark attempt lease expired; reconcile before requeue | Prior worker may still be running; fencing/lease token required. |
| Deterministic input/validation failure | Fail or quarantine; do not retry unchanged input indefinitely | Replay only after input/version or contract changes. |
| Rate limit / temporary external unavailability | Retry only under bounded adapter policy | External request idempotency or reconciliation required. |
| External timeout after request submission | Set UNKNOWN_OUTCOME and reconcile external receipt/state | Do not blindly repeat non-idempotent action. |
| Artifact hash/validation mismatch | Quarantine result; retain evidence and attempt trace | Do not mark job successful or silently repair in place. |
| Authorization denied/revoked | Block dispatch or terminate protected step safely | No retry until a fresh valid authorization decision exists. |
| Cancellation during execution | Request cooperative cancellation; reconcile side effects | Do not claim cancelled until outcome is known. |
| Retry budget exhausted | Dead-letter/quarantine with actionable reason | Explicit human/operator disposition before replay. |

- Backoff strategy, maximum attempts, timeout values and lease durations are configuration decisions requiring workload evidence; do not invent numeric values here.

- Use jitter where synchronized retries could amplify load.

- Every retry must create a distinct attempt and preserve parent job/workflow correlation.

- Fencing tokens or monotonically increasing lease generations should prevent stale workers from committing state after reassignment.

- Recovery logic must distinguish safe-to-retry computation from uncertain external side effects.

## 9. Idempotency and side-effect safety

| Operation type | Idempotency strategy | Required behavior |
| --- | --- | --- |
| Create logical job | Scoped client/request idempotency key | Same key and same request returns existing logical job/result; conflicting payload is rejected. |
| Queue delivery | Stable message/event ID plus inbox receipt | Duplicate delivery does not create a second attempt unless policy explicitly creates a retry. |
| Worker completion | Attempt ID + lease/fencing token + compare-and-set transition | Stale or duplicate completion cannot overwrite newer state. |
| Artifact registration | Stable artifact/version identity and content hash | Repeated registration is deduplicated; mismatched content is not silently accepted. |
| External API side effect | Provider idempotency key where supported; otherwise pre/post reconciliation | Unknown outcome is reconciled before retry. |
| Publishing | Central authorization + exact-version approval + external receipt tracking | No automatic public publishing; no direct adapter bypass. |

Exactly-once effects cannot be assumed merely because the queue, database or worker uses an idempotency key. The design must state the boundary and residual uncertainty for each external side effect.

## 10. Authorization and governance integration

| Execution point | Required control | Failure behavior |
| --- | --- | --- |
| Workflow/job creation | Validate caller identity, scope and permitted operation | Reject or persist as blocked according to governing contract. |
| Before dispatch | Check central authorization for the action and target scope | Do not dispatch protected work without a valid decision. |
| Worker claim | Verify worker is trusted and authorized for declared capability | Deny claim; capability declaration alone grants no permission. |
| During long-running work | Handle revocation/expiry and re-check at defined checkpoints | Stop or quarantine safely; do not continue protected action on stale grant. |
| Artifact access | Enforce scoped access to exact required artifacts | Deny access outside job scope. |
| Approval-sensitive step | Require human approval bound to exact content/artifact version and purpose | Block if missing, stale, ambiguous or mismatched. |
| Publishing/external action | Central authorization plus applicable approval and rights gates | Fail closed; record denial and do not call external adapter. |

WP-2 must call the centralized authorization interface; it must not duplicate policy logic or treat worker identity, queue membership or prior approval as authorization.

## 11. Candidate persistence records consumed from WP-1

| Record family | Minimum conceptual data | WP-2 responsibility |
| --- | --- | --- |
| workflow_definition | Definition ID/version, stage graph, configuration reference, lifecycle | Bind each instance to immutable definition version. |
| workflow_instance | Instance ID, definition version, target reference/version, state, timestamps | Maintain orchestration state and transition history. |
| job_record | Job ID, workflow ID, type, payload reference, priority/class, state, idempotency scope | Maintain authoritative job state and constraints. |
| execution_attempt | Attempt ID, job ID, worker ID, lease generation, start/end, outcome | Preserve each execution attempt separately. |
| job_event | Event ID, job/attempt/workflow refs, event type, actor, timestamp, correlation | Append auditable transition facts. |
| outbox_event | Event ID, aggregate reference, payload/version, publish state | Publish only after transaction commit. |
| inbox_receipt | Consumer ID, message/event ID, processing state, received time | Deduplicate message consumption. |
| idempotency_record | Scope, key, request hash, logical result reference, expiry/retention | Reject key reuse with conflicting payload. |
| reconciliation_record | Uncertain operation, external reference, evidence, disposition | Track UNKNOWN_OUTCOME resolution. |

Exact physical tables, columns, indexes and enums remain SOURCE REQUIRED. Align with WP-1 after its source verification and schema review; do not create parallel overlapping records.

## 12. Observability and audit contract

- Every workflow, job, attempt, worker, event, artifact and external operation must have stable correlation references.

- Record state transition actor, timestamp, previous/new state, reason and policy decision reference where applicable.

- Separate business state from telemetry: heartbeat/log volume must not be treated as successful completion.

- Redact secrets and sensitive payloads from logs; store references to protected data rather than copying it into events.

- Metrics should cover queue age, claim latency, attempt duration, retry count, lease expiry, dead-letter count, unknown outcomes and reconciliation age.

- Operational thresholds and alert levels require measured baselines and are not fixed in this candidate.

- Audit records must be access-controlled and retained under the governing retention/legal-hold policy.

## 13. Failure scenarios and acceptance oracle

| Test ID | Scenario | Expected result | Evidence |
| --- | --- | --- | --- |
| WP2-DUR-01 | Process stops after job/outbox transaction commits but before publish | Outbox relay eventually publishes stable event; job remains discoverable | DB snapshot + relay log + event receipt |
| WP2-DUR-02 | Message delivered twice | Duplicate consumption does not create duplicate logical side effect | Inbox record + side-effect count |
| WP2-LEASE-01 | Worker dies after claim | Lease expires; attempt remains traceable; reassignment uses fencing | Attempt history + lease generation |
| WP2-LEASE-02 | Old worker reports completion after reassignment | Stale completion is rejected | Compare-and-set/fencing test |
| WP2-RETRY-01 | Transient failure occurs | Bounded retry policy schedules a distinct attempt | Attempt records and retry schedule |
| WP2-RETRY-02 | Retry budget exhausted | Job is quarantined/dead-lettered with reason | Terminal state and operator disposition |
| WP2-UNK-01 | External request times out after submission | Job enters UNKNOWN_OUTCOME and reconciliation; no blind replay | External lookup/evidence and reconciliation record |
| WP2-CAN-01 | Cancellation requested during execution | Cancellation is cooperative; uncertain effect is reconciled | Cancel event and final outcome evidence |
| WP2-AUTH-01 | Authorization denied before dispatch | Protected job is not dispatched | Policy decision + absence of worker claim |
| WP2-AUTH-02 | Authorization revoked during protected work | Protected step stops or is safely quarantined | Revocation event and execution trace |
| WP2-ART-01 | Worker returns artifact with invalid hash | Output is rejected/quarantined; job not marked successful | Hash validation and artifact status |
| WP2-REC-01 | Service restarts with queued, leased and uncertain jobs | Recovery reconciles each class without losing attempts | Before/after state report |
| WP2-LOCAL-01 | Local-only job has no available local worker | Job waits safely; no unapproved cloud/paid fallback | Queue state and no remote dispatch evidence |
| WP2-PUB-01 | Publishing requested without exact-version approval and authorization | Action is blocked; adapter is not called | Negative integration test and audit event |

## 14. WP-2 acceptance gates

| Gate | Exit condition | Current status |
| --- | --- | --- |
| G1 — Contract traceability | Every WP-2 requirement maps to governing source, entity/event and test | NOT VERIFIED |
| G2 — Durable persistence | Job/workflow/attempt/outbox/inbox semantics are transactionally specified | DESIGN CANDIDATE |
| G3 — Delivery and idempotency | At-least-once, duplicate delivery and side-effect boundaries are explicit | DESIGN CANDIDATE |
| G4 — Recovery | Lease expiry, stale worker fencing, retry and unknown outcomes are specified | DESIGN CANDIDATE |
| G5 — Governance | Central authorization and exact-version approval gates are enforced in contract | ACCEPTED DIRECTION; detailed contract SOURCE REQUIRED |
| G6 — Observability | Correlation, audit and operational metrics are specified | DESIGN CANDIDATE |
| G7 — Integration | WP-2 contract aligns with WP-1, WP-3, WP-4 and WP-5 | NOT VERIFIED |
| G8 — Owner approval | Exact WP-2 contract candidate reviewed and approved | NOT REQUESTED |

## 15. Open items and deferred decisions

| Item | Disposition | Closure trigger |
| --- | --- | --- |
| Exact job/workflow state enum names | SOURCE REQUIRED | Import governing lifecycle/state contract. |
| Retry counts, backoff, lease and timeout values | DEFERRED | Workload-class measurement and owner-approved operational policy. |
| Priority classes and fairness policy | CANDIDATE / SOURCE REQUIRED | Confirm workflow requirements and prevent starvation. |
| Queue partitioning and scaling topology | DEFERRED | Measured throughput, ordering and recovery needs. |
| External idempotency support matrix | SOURCE REQUIRED | Inventory each adapter/API and document provider semantics. |
| Unknown-outcome reconciliation procedure per integration | SOURCE REQUIRED | Define authoritative external lookup/evidence for each side effect. |
| Cancellation guarantees | SOURCE REQUIRED | Define per job class whether cancellation is best-effort or confirmable. |
| Operational alert thresholds | DEFERRED | Establish baseline from test and production-like telemetry after authorization. |
| Database and queue deployment provider | NOT SELECTED | Separate owner decision; no paid activation implied. |

## 16. Draft WP-2 work order — not active

| Field | Draft definition |
| --- | --- |
| Objective | Implement durable workflow/job orchestration with at-least-once delivery, idempotency, traceable attempts and safe recovery. |
| Preconditions | Authoritative CF/lifecycle/API sources verified; contract freeze approved; WP-1 persistence contract approved; separate implementation authorization issued. |
| Allowed after authorization | Implement approved workflow/job state transitions, queue/outbox/inbox, lease/attempt handling, retry/reconciliation and WP-2 tests within file allowlist. |
| Forbidden without separate approval | Destructive migrations, broad refactors, provider activation, paid services, cloud deployment, external publishing, broad Git operations or agent self-expansion. |
| Required outputs | Implementation, migrations if separately authorized, contract tests, recovery evidence, observability notes and traceability matrix. |
| Exit criteria | All mandatory WP-2 acceptance tests pass; recovery and negative governance paths demonstrated; independent QA disposition recorded. |
| Rollback boundary | Per-change recovery plan and validated database restore/compatibility procedure; no assumed safe rollback. |

## 17. Readiness decision

| Question | Current answer |
| --- | --- |
| Is WP-2 architecture direction consistent with accepted invariants? | Candidate appears consistent; authoritative source reconciliation is still required. |
| Is this the final job/workflow contract? | No — candidate only. |
| Are exact state values and retry/lease limits approved? | No — source verification and operational evidence required. |
| Is implementation authorized? | No. |
| Can this be used for design review? | Yes — reconcile each contract detail against authoritative sources before freeze. |

Recommended next step: use this candidate as the WP-2 review scaffold after the source intake work is completed. Then proceed to WP-3 worker registry and trust-boundary design without treating this candidate as frozen.

END OF BATCH 06


## Source document metadata (preserved from DOCX)

- **Footer:** NEXTDECODE • P0 design candidate • Not frozen • Not implementation authorization

