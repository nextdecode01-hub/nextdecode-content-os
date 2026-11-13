# NEXTDECODE Contract 10 / X-01 — Workflow, Job, Worker & Resource Ownership Reconciliation
**Document ID:** NEXTDECODE-C10-X01-RECON-0.1  
**Version:** 0.1 | **Date:** 2026-11-04  
**Status:** Working source reconciliation — documentation only  
**Contract freeze:** NOT GRANTED | **Implementation authorization:** NOT GRANTED

## 1. Purpose and disposition
Resolve the conceptual ownership boundary among Contract 10 (Agent Intelligence, Resource Management & Orchestration), WP2 durable workflow/job execution, WP3 worker trust, WP1 canonical persistence, Contract 11 business creation/production lifecycle, and WP4 artifact ownership.

**Disposition:** Contract 10 is the orchestration and capability-coordination contract, not owner of every business-domain record. WP2 owns durable workflow/job progression and execution attempts. WP3 owns worker identity/trust, capability enforcement, scoped credentials, leases/fencing and worker revocation. Business-domain owners retain their own lifecycle state. Contract 10 coordinates commands/events without writing another domain's canonical state.

## 2. Source set reviewed
- Contract 10 v1.0, especially §§1–5, 8–15.
- Batch 16 Domain & Interface Contract Closure Pack Markdown reading copy, including canonical ownership table and ADR/CF baseline.
- Data Dictionary v1.0/v1.1 and Module-to-Contract Traceability Matrix.
- API/Event Contract Standard 1.0 and Unified Lifecycle & State Transition Standard 1.0.
- WP1–WP3 package readmes and WP2/WP3 reconciliation packages.
- Accepted ADR-001–ADR-005 and ADR-007–ADR-010; CF-01–CF-24.

## 3. Canonical entity and capability ownership

| Entity / capability | Canonical owner | Contract 10 responsibility | Boundary / open detail |
|---|---|---|---|
| WorkflowDefinition | Automation & Agent Orchestration / WP2 | Select and coordinate versioned definitions | Exact schema/approval in WP2 |
| WorkflowRun | Automation & Agent Orchestration / WP2 | Coordinate run; correlate tasks/outcomes | Owns run lifecycle, not business lifecycle |
| WorkflowTask / TaskInstance | WP2 | Plan/decompose and coordinate task occurrence | Canonical name/cardinality differs among sources; X-01 open |
| TaskDefinition / capability requirement | Contract 10 catalog with WP2 reference | Match work to required capability and I/O contract | Separate reusable capability from execution occurrence |
| Job | WP2 | Coordinate durable dispatchable execution unit | Not synonymous with Task or WorkflowRun |
| JobAttempt | WP2 | Coordinate bounded attempt and retry history | Append-oriented; exact relationship open |
| WorkerIdentity / Worker | WP3 | Select eligible worker; pass scoped assignment | Contract 10 must not own worker trust or issue credentials |
| WorkerSession / Lease / Heartbeat / Fencing | WP3 | Consume eligibility and assignment result | Protocol and expiry are WP3 decisions |
| AgentIdentity / AgentVersion / AgentCapability | Contract 10 | Own registry, versioned capability declaration and evaluation metadata | Does not prove quality or grant permissions |
| ProviderRecord / ModelRecord | Contract 10 registry, subject to owner/security approval | Track eligible providers/models and terms | Registry entry is not approval to send data |
| RoutingDecision / DelegationRecord | Contract 10 | Own rationale and scope | Delegation cannot exceed delegator authority |
| ResourceAccount / UsageRecord / Reservation | Contract 10 resource governance | Track approved quota/budget, reservations and usage | Cannot increase budget, buy credits or activate services |
| TaskCheckpoint / RecoveryRecord | WP2 orchestration, with WP3 worker provenance | Preserve safe resume/reconciliation state | Store and retention open |
| ContentItem / ContentVariant / CreationProject / StudioProduction | Content/creation domain, Contract 11 and WP1 registry | Submit and coordinate production tasks | Must not own editorial/studio lifecycle |
| Artifact / ArtifactVersion / Manifest | Part 7 / WP4 | Pass references and verify output handoff | Must not own binary storage or overwrite immutable versions |
| Quality / Rights / Approval / PublishingAuthorization | Contract 07 / WP5 | Consume gates and route review | Cannot approve or authorize own work |
| DistributionPackage / PublishOperation / Publication | Contract 12 | Coordinate eligible workflow only | Contract 07 authorizes; Contract 12 owns distribution state |

**Terminology note:** Contract 10 v1.0 uses Workflow, Task, TaskCheckpoint and WorkerIdentity; Batch 16 uses WorkflowDefinition, WorkflowRun, TaskDefinition, TaskInstance, Job, JobAttempt and Worker. Do not assume exact aliases. WP2/WP1 must ratify canonical entity set and relationship cardinalities.

## 4. Workflow lifecycle vs business lifecycle
These state dimensions are independent:
- Business/content lifecycle: Content Graph / Contract 11 or relevant domain.
- WorkflowRun lifecycle: WP2.
- Task/Job execution lifecycle: WP2.
- JobAttempt outcome/history: WP2.
- Worker trust/availability/lease: WP3.
- Artifact lifecycle/integrity: WP4.
- Quality/rights/governance/approval/authorization: Contract 07 / WP5.
- Distribution and external publication outcome: Contract 12.

A workflow event may report production task completion; it does not mark canonical content approved, rights-cleared, published or publicly visible. A worker heartbeat is not proof of task completion. A task result is not a committed business-domain transition until the owning domain accepts/commits it.

## 5. Durable execution and state authority
Carry forward accepted baseline:
- PostgreSQL-compatible relational DB is authoritative shared-state store (ADR-002).
- DB-backed durable queue with transactional outbox/inbox initially (ADR-003).
- Versioned HTTP/JSON contracts with schema validation (ADR-004).
- UUIDv7 canonical IDs, immutable identity (ADR-001).
- Unique worker identity, scoped short-lived credentials and capability authorization (ADR-005).
- Separate lifecycle state machines (ADR-010).
- At-least-once delivery, idempotent consumers; no global exactly-once promise.
- Local-only work remains queued/deferred while local worker unavailable; never simulate completion or silently send restricted data to an unapproved remote worker.

Contract 10 §9 lists workflow coordination requirements: dependencies, durable transitions, leases/heartbeats, checkpoints, bounded retry, dead-letter handling, cancellation, idempotent result recording and audit/resource accounting. These are capabilities, not permission for agents to mutate authoritative state arbitrarily. Transitions are enforced by owning WP2 service/domain boundary.

## 6. Worker trust and assignment boundary
WP3 owns worker identity/registration; authentication and credential issuance/rotation/revocation; capability/environment attestation; scoped assignment authorization; lease/heartbeat/fencing and stale-worker rejection; revocation propagation and in-flight assignment handling.

Contract 10 may route a task to an eligible worker but must receive an authoritative eligibility/assignment decision. Agent identity, model identity, worker identity and authenticated principal are distinct. A model/provider is not a worker; an agent is not a worker; a worker session is not canonical worker identity.

A worker cannot self-assert capability or expand scope. Fallback worker/provider must already be approved for the same task, data classification, operation and resource envelope.

## 7. Resource and provider authority
Contract 10 may forecast, reserve within, attribute and optimize resources inside already approved envelopes. It may not increase budgets/quotas; buy credits/subscriptions; authorize a new provider/service/contract; initiate payment; transfer restricted data to an ineligible provider; or treat pricing estimates as provider-reported charges.

Provider eligibility is a hard filter before quality/cost/latency optimization. ResourceAccount limits and hard-stop behavior remain authoritative. Exact accounting grain, reservation concurrency, reconciliation and reset semantics remain open.

## 8. Cross-contract interfaces
- WP1 exposes canonical IDs, typed references, versions and persistence ownership; WP2 consumes them.
- WP2 owns WorkflowDefinition/Run, Task/Job/Attempt progression and durable recovery; Contract 10 supplies routing/capability/resource decisions.
- WP3 authenticates and fences workers; WP2 rejects stale/revoked worker execution.
- WP4 registers immutable output artifacts; WP2 records references and cannot mutate artifact bytes.
- WP5 supplies governance/rights/approval/authorization outcomes; workflow execution cannot bypass hard blockers.
- Contract 11 submits production work and accepts domain outcomes; WP2 does not take over CreationProject/StudioProduction lifecycle.
- Contract 12 submits distribution work; authorization remains WP5 and external operation semantics must reconcile before retry.
- API/Event + Lifecycle standards provide common envelopes and transition protocol.

## 9. X-01 open issues and owner decisions

| ID | Issue | Why it matters | Owner / required action |
|---|---|---|---|
| X01-01 | Canonical workflow entity vocabulary | Workflow, WorkflowDefinition, WorkflowRun, Task, TaskDefinition, TaskInstance and WorkflowTask are inconsistent | WP1/WP2 propose canonical vocabulary and legacy mapping; owner ratification |
| X01-02 | Task-to-job cardinality | Sources do not settle whether one TaskInstance creates one Job, multiple Jobs or nested jobs | WP2 define cardinality and creation/retry semantics |
| X01-03 | JobAttempt vs TaskAttempt | Attempt terminology may duplicate execution concepts | WP2 define one attempt identity and relationship; avoid competing retry histories |
| X01-04 | WorkflowRun vs Task/Job state | Separate state machines required; parent aggregation rules unsettled | WP2 define derived vs authoritative parent status and event semantics |
| X01-05 | Worker lease/fencing semantics | Stale worker rejection required; exact lease duration, fencing token and reclaim protocol open | WP3 specify and owner-review; no invented durations |
| X01-06 | Cancellation/pause after side effect begins | Workflow cancellation cannot guarantee provider operation cancellation | WP2/WP3/WP6 distinguish cooperative cancel, stop-dispatch, revoke and external reconciliation |
| X01-07 | Checkpoint authority and retention | Checkpoint content described; store/retention/restore safety open | WP2/WP4/WP3 define boundaries; owner reserves retention |
| X01-08 | Resource reservation concurrency | Oversubscription and inaccurate usage reconciliation risk | Contract 10/WP2 define atomic reservation and reconciliation model |
| X01-09 | Provider/agent/worker identity relationships | Identity conflation creates permission and audit ambiguity | Contract 10/WP3 publish typed identity model |
| X01-10 | Business-domain commit after task success | Workflow success may be mistaken for accepted domain result | WP2 and domain owners define result-acceptance/commit handoff |
| X01-11 | Direct-entry and alternate execution paths | Entry points can bypass workflow and governance controls | WP2/WP5/WP6 inventory paths and require equivalent gates |
| X01-12 | Local worker offline and remote fallback | Shorts Studio local rendering must not be falsely completed or silently moved to unapproved provider | WP3/WP6 define queue/defer/fallback acceptance rules |

## 10. Closure acceptance criteria
- One canonical vocabulary and relationship diagram exists for workflow, run, task, job, attempt, worker and checkpoint.
- Each entity has one authoritative owner; no duplicate writable state.
- Workflow, task/job, worker, business, artifact, governance and distribution state machines remain distinct.
- Worker identity, credential, capability, lease and fencing checks are enforced by WP3.
- WP2 durable transitions use expected-version, idempotency and transactional outbox/inbox rules.
- Task execution success does not automatically commit business-domain state.
- Retry/recovery distinguishes transient, policy, authorization, quality and unknown external outcome failures.
- Local-only tasks safely wait while local worker unavailable; remote fallback is policy-authorized only.
- Resource optimization cannot expand budget or provider authority.
- Direct/alternate entry paths cannot bypass required authorization/quality/rights gates.
- WP6 acceptance cases cover worker loss, stale lease, duplicate delivery, retry, cancellation, unknown external side effect and domain-result rejection.

## 11. Disposition
**Contract 10 / X-01 reconciliation: PARTIALLY CLOSED at logical ownership level.** Exact workflow entity vocabulary, cardinalities, lease/fencing, checkpoint, cancellation, resource reservation and handoff semantics remain open. No schema freeze, owner decision, repository action, test execution, agent dispatch or implementation authorization is granted.
