# NEXTDECODE — Unified Lifecycle & State Transition Standard
**Version:** 1.0  
**Status:** Architecture specification — documentation only  
**Scope:** Shared Intelligence Core, specialized studios, orchestration, governance, distribution and publishing  
**Companion:** Canonical Data Dictionary & Entity Ownership Registry 1.0

---

## 1. Purpose

This standard defines how lifecycle state is represented, changed, audited and coordinated across NEXTDECODE.

It resolves a recurring architecture risk: separate domains need their own state machines, but the platform also needs a consistent way to record and communicate transitions between them.

The standard therefore establishes:

1. Domain-owned state machines, not one universal status enum.
2. A common lifecycle event envelope.
3. Explicit ownership of each state machine.
4. Transition guards, concurrency and idempotency rules.
5. Cross-domain orchestration without taking state ownership away from domain services.
6. Safe handling of approvals, retries, cancellation, expiry and uncertain external side effects.
7. Durable audit history and recoverable execution.

This is a specification, not implementation authorization. It does not authorize repository access, code changes, provider connections, infrastructure provisioning, spending, uploads or publishing.

## 2. Normative language

The terms **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT** and **MAY** are used as requirements:

- **MUST / MUST NOT:** mandatory for a conforming implementation.
- **SHOULD / SHOULD NOT:** expected default; deviations require a documented rationale.
- **MAY:** optional behavior.

## 3. Core design principles

### 3.1 Separate state machines by domain

NEXTDECODE MUST NOT introduce a single universal lifecycle enum for all entities.

A research run, content item, approval request, rendering job, asset, distribution package and external publishing operation have different meanings and valid transitions. Their state machines remain separate and are owned by their respective domains.

A shared event envelope makes transitions interoperable; it does not make their states interchangeable.

### 3.2 State ownership is explicit

Only the authoritative owner of a state machine may commit transitions to it.

Other services may:
- request a transition;
- observe and project a state;
- coordinate dependent work;
- record their own state;
- raise a policy or validation finding.

They MUST NOT directly mutate another domain's authoritative state.

### 3.3 A transition is an auditable fact

Every committed transition MUST create an immutable audit/event record containing the actor, reason, time, prior state, new state and relevant correlation context.

A mutable current-state projection MAY be maintained for efficient reads, but it MUST be reconstructible or reconcilable from authoritative transition history.

### 3.4 Authorization and execution are different

A workflow being ready, a task completing, quality passing, or a human approving a review item does not independently authorize a public external action.

Governance authorization is a distinct decision, scoped to the exact action, target, content/artifact version and applicable policy version.

### 3.5 Unknown is not success or failure

When an external side effect may have happened but its result cannot be confirmed, the operation MUST enter an explicit uncertain state and be reconciled. The system MUST NOT blindly retry an operation that could create a duplicate or irreversible effect.

---

## 4. Common lifecycle envelope

Every domain transition event MUST use a common envelope. Domain-specific payloads may add fields, but MUST NOT redefine the meaning of common fields.

### 4.1 Required envelope fields

| Field | Meaning |
|---|---|
| `event_id` | Unique immutable identifier for this event; UUIDv7 recommended |
| `entity_id` | Canonical UUIDv7 identity of the entity whose state changed |
| `entity_type` | Stable canonical entity type |
| `domain` | Owning domain that emitted the transition |
| `state_machine` | Stable identifier and version of the state machine |
| `state_version` | Monotonically increasing version for this entity's state machine |
| `previous_state` | State before the transition; null only for initial creation |
| `new_state` | State after the transition |
| `occurred_at` | Time the domain says the transition occurred |
| `recorded_at` | Time the authoritative store recorded the event |
| `actor_ref` | Canonical actor identity or service identity |
| `actor_type` | Human, agent, service, worker or external system |
| `reason_code` | Machine-readable reason from a controlled vocabulary |
| `reason_summary` | Short human-readable explanation |
| `correlation_id` | Identifier joining a business request or end-to-end operation |
| `causation_id` | Event/command that directly caused this transition, if applicable |
| `policy_version` | Policy version evaluated for the transition; nullable only when no policy applies |
| `evidence_refs` | References to evidence supporting the transition |
| `result_refs` | References to outputs/results produced by the transition |
| `schema_version` | Version of the event envelope schema |

### 4.2 Recommended additional fields

- `workspace_id`, `brand_id`, `studio_id` where applicable.
- `request_id` and `idempotency_key`.
- `transition_command_id`.
- `trace_id` and `span_id` for observability.
- `source_system` and `source_version`.
- `effective_at` for decisions whose effect begins at a future time.
- `supersedes_event_id` for an explicitly superseding record; never use it to erase history.
- `metadata` for bounded, non-sensitive domain context.

### 4.3 Time semantics

- `occurred_at` is the domain event time.
- `recorded_at` is the authoritative persistence time.
- Both MUST be stored in UTC with sufficient precision.
- User-facing interfaces MAY render local time.
- Clock skew MUST NOT be used to bypass state-version ordering. `state_version` is the ordering authority for one entity/state machine.

### 4.4 Event immutability

Once committed, an event MUST NOT be edited or deleted as an ordinary correction mechanism.

Corrections MUST be represented by a new compensating, superseding or annotation event with a reason and reference to the original event. Legal deletion obligations are handled through the platform's retention and privacy lifecycle, not by silently rewriting operational history.

---

## 5. State concepts that MUST remain distinct

These concepts are related but are not synonyms and MUST NOT be collapsed into one field.

| Concept | What it answers | Example values |
|---|---|---|
| **Lifecycle state** | Where is this entity in its domain process? | `DRAFT`, `ACTIVE`, `ARCHIVED` |
| **Execution outcome** | What happened when a task/job ran? | `SUCCEEDED`, `FAILED`, `CANCELLED`, `UNKNOWN_OUTCOME` |
| **Quality outcome** | Did the evaluated content/process meet its quality requirements? | `PASS`, `PASS_WITH_WARNINGS`, `NEEDS_REVIEW`, `BLOCKED` |
| **Governance disposition** | What did policy evaluation decide? | `ALLOW`, `ALLOW_WITH_CONDITIONS`, `PENDING`, `DENY` |
| **Human approval state** | Has the required human decision been made? | `NOT_REQUIRED`, `PENDING`, `APPROVED`, `REJECTED`, `EXPIRED`, `REVOKED` |
| **External operation status** | What is known about an operation at a platform/provider? | `NOT_SUBMITTED`, `SUBMITTED`, `CONFIRMED`, `REJECTED`, `UNKNOWN_OUTCOME` |
| **Epistemic status** | How should a knowledge assertion be interpreted? | `FACT`, `ESTIMATE`, `OPINION`, `HYPOTHESIS`, `DISPUTED` |
| **Provenance type** | Where did a record or assertion originate? | `OBSERVED`, `PLATFORM_REPORTED`, `HUMAN_ENTERED`, `MODEL_INFERRED`, `EXTERNAL_SOURCE` |

A domain may define additional values. It MUST document the semantic category and owner of each value.

A successful render does not mean quality passed. Quality passing does not mean rights are cleared. A human approval does not mean governance authorized a public action. A submitted publish request does not mean publication was confirmed.

---

## 6. State-machine ownership registry

The following ownership map is canonical at the architecture level. Detailed transition tables for each entity remain domain-specific and are maintained with the relevant contract.

| State machine / entity family | Authoritative owner | Coordination or consumer role |
|---|---|---|
| Workspace, actor and identity lifecycle | Workspace/identity foundation | All domains consume identity and scope |
| Audience, persona, segment, insight | Contract 01 — Audience & Identity | Contract 08 consumes and enriches performance context through owned records |
| Opportunity, evidence source/item, claim and claim-evidence link | Contract 02 — Opportunity & Evidence | Contract 05 operates research workflows and references evidence |
| Brand and studio identity | Contract 03 — Brand & Editorial Intelligence | Studios consume immutable identity versions |
| Knowledge and learning records | Contract 04 — Shared Knowledge & Learning | Other domains submit candidate knowledge/learning records |
| Research request/run and research execution | Contract 05 — Research Intelligence | Orchestrator schedules; Contract 02 owns canonical evidence/claim identities |
| Strategy, portfolio and planning records | Contract 06 — Strategy & Portfolio | Orchestrator coordinates approved plans |
| Quality assessment, rights, governance, approvals and authorization decisions | Contract 07 — Quality, Rights & Governance | All execution and distribution domains must consult the applicable decisions |
| Metric definitions, performance snapshots, experiments and attribution | Contract 08 — Audience & Performance | Studios and analytics producers supply observations |
| Financial records and commercial pipeline | Contract 09 — Business & Monetization | AI may recommend/prepare; financial authority remains owner-controlled |
| Agent, provider/model, resource, task and worker contracts | Contract 10 plus Parts 4, 5 and 8 | Orchestrator coordinates; domain services own their business entities |
| Creation project and studio production | Contract 11 — Multiformat Creation | Specialized studio engines execute production |
| Distribution package, schedule proposal and external operation records | Contract 12 — Distribution & Publishing | Contract 07 authorizes; platform adapters execute only permitted operations |
| Durable job queue, scheduler and worker leases | Part 4 — Queue/Scheduler/Worker | Orchestrator owns workflow/job progression |
| Artifact/asset integration and immutable artifact versions | Part 7, with Contract 07 rights/provenance governance | Studios create artifacts; shared services register and resolve them |
| Cross-domain workflow instance | Orchestration layer | Coordinates commands/events; does not own domain entity state |

If implementation discovers a conflict between a contract and this registry, it MUST be recorded as an architecture decision and resolved before implementation. It MUST NOT be silently resolved by allowing two domains to write the same state.

---

## 7. Transition command and commit protocol

### 7.1 Command lifecycle

A requested transition SHOULD follow this sequence:

1. Authenticate the actor or service identity.
2. Verify workspace/brand/studio scope.
3. Verify the actor has the capability required for this transition.
4. Load the authoritative entity and current state version.
5. Validate the requested transition against the state machine.
6. Evaluate transition guards, required evidence and applicable policy.
7. Compare the caller's expected state version with the current version.
8. Commit the state update and immutable event atomically.
9. Write any outbound event to a transactional outbox in the same transaction.
10. Return the committed state version and event reference.

A rejected command MUST return a structured reason. It MUST NOT create a misleading successful transition event.

### 7.2 Optimistic concurrency

Every state-changing command MUST include an expected state version, or an equivalent conditional update token.

If the expected version is stale:
- reject with a conflict result;
- return or reference the current version;
- do not silently overwrite the newer state;
- let the caller reload and decide whether to retry.

A transition MUST increment `state_version` exactly once.

### 7.3 Idempotency

Commands that may be retried MUST carry an idempotency key scoped to the operation and target entity.

- Repeating the same key and same request MUST return the original committed result.
- Reusing a key with a different request body MUST be rejected.
- Event consumers MUST record processed event IDs or equivalent deduplication keys.
- Idempotency retention MUST cover the realistic retry and recovery horizon; exact duration is an implementation decision.

### 7.4 Atomicity and event delivery

The state change and its outbox record MUST be committed atomically.

Outbox delivery is at-least-once. Consumers MUST be idempotent. The architecture MUST NOT claim exactly-once delivery across independent services.

Consumers SHOULD use an inbox/deduplication record and maintain their own processing checkpoint.

### 7.5 Side effects

External or expensive side effects SHOULD be initiated after the authoritative transition is committed, through durable jobs or commands.

The system MUST record:
- the intent to perform the side effect;
- the authorization decision, if required;
- the idempotency or provider reference;
- submission attempt and response;
- reconciliation result.

A failed event delivery MUST NOT roll back an already committed domain transition. It MUST be retried or moved to a dead-letter/reconciliation process.

---

## 8. Transition guards and invariants

Every state machine MUST publish a transition table containing:

- source state;
- requested transition/command;
- destination state;
- required actor capability;
- required evidence;
- policy guard;
- side effects;
- emitted events;
- retry and compensation behavior.

### 8.1 Universal guards

All state machines MUST enforce, where applicable:

1. Valid source-to-destination transition.
2. Correct entity scope and ownership.
3. Actor authentication and authorization.
4. Expected state version.
5. Required fields and evidence.
6. Applicable retention, privacy and security restrictions.
7. Idempotency.
8. Audit-event creation.
9. No unauthorized cross-domain state mutation.

### 8.2 Hard blockers

A hard blocker MUST prevent the protected action.

Ordinary human approval MUST NOT override:
- prohibited rights or unresolved mandatory rights checks;
- security isolation or revoked credentials;
- privacy/legal restrictions;
- invalid or missing required authorization;
- policy-defined non-overridable safety or compliance conditions.

A blocker may be cleared only through its defined owner-controlled remediation path and a fresh evaluation. An override, where the policy explicitly permits one, must be a separately authorized, scoped, reasoned and audited governance action. The architecture must not assume that every blocker is overrideable.

### 8.3 Quality and governance chain

The quality outcome vocabulary is:

- `PASS`
- `PASS_WITH_WARNINGS`
- `NEEDS_REVIEW`
- `BLOCKED`

Quality assessment and governance disposition remain separate.

A policy may permit a `PASS_WITH_WARNINGS` artifact to proceed to a specified next step, but the policy must identify which warnings are acceptable. `NEEDS_REVIEW` requires the designated review path. `BLOCKED` prevents the protected downstream action until remediation and re-evaluation.

No generic “approved” flag may replace the underlying quality findings, rights decision and governance decision.

---

## 9. Cross-domain lifecycle orchestration

The orchestrator owns workflow progression and durable job execution. It does not become the owner of opportunity, research, content, quality, approval, asset or publication state.

### 9.1 Reference end-to-end flow

| Stage | Domain-owned record/state | Orchestrator responsibility | Required handoff condition |
|---|---|---|---|
| 1. Discover | Opportunity candidate | Schedule discovery and persist workflow checkpoint | Candidate stored with provenance |
| 2. Evaluate | Opportunity assessment | Coordinate eligibility and scoring | Eligibility result and rationale recorded |
| 3. Research | Research request/run; evidence and claims | Launch bounded research jobs and track completion | Research result available; claims retain evidence links |
| 4. Plan | Strategy/portfolio/creative brief | Coordinate approved planning steps | Plan version and scope recorded |
| 5. Create | Creation project, studio production, artifacts | Route to the correct studio and workers | Required artifacts registered with immutable versions |
| 6. Validate | Quality assessments and rights records | Invoke independent checks and collect results | Quality and rights conditions satisfied for next step |
| 7. Review | Human approval request/decision | Present the exact review package and wait | Required approval is valid for the exact version/action |
| 8. Prepare distribution | Distribution package and schedule proposal | Coordinate channel adaptation and scheduling proposal | Package version and destination are explicit |
| 9. Authorize action | Governance authorization decision | Request policy decision; do not self-authorize | Exact action, target and artifact version are authorized |
| 10. Execute | External operation record | Dispatch a durable operation job | Provider response captured |
| 11. Reconcile | External operation status | Verify uncertain outcomes and update projections | Confirmed result or explicit unresolved exception |
| 12. Learn | Performance snapshot, experiment and learning record | Schedule measurement and learning workflow | Provenance and attribution quality recorded |

### 9.2 Handoff state is not publishing authorization

`APPROVED_FOR_HANDOFF` means only that a specified artifact/package may be handed to the next defined internal or operational stage.

It MUST NOT be interpreted as:
- approval to publish publicly;
- authorization to spend;
- authorization to sign or accept a commercial agreement;
- authorization to change a policy;
- authorization to bypass a hard blocker.

### 9.3 Publishing policy baseline

Autonomous public publishing remains **disabled** pending explicit owner approval of a separate publishing policy.

Until that policy is approved:
- the system may research, prepare, render, validate and stage eligible content within existing permissions;
- the system may prepare schedule proposals;
- the system MUST NOT infer publishing permission from a successful workflow, a human review, a schedule proposal or owner silence;
- a public publishing operation MUST remain blocked unless a valid explicit authorization exists.

This standard does not grant such authorization.

---

## 10. Human approval lifecycle

Human approval is a first-class governed record, not a boolean property on a content item.

### 10.1 Approval request scope

An approval request MUST bind to:
- the exact entity and immutable version being reviewed;
- the action being requested;
- the destination/target, where applicable;
- the relevant policy version;
- the required approver role/identity;
- the request creation and expiry times;
- the evidence/review package shown to the approver.

A material change to the artifact, destination, action or relevant policy invalidates the prior approval unless the approval policy explicitly defines a narrower unaffected scope.

### 10.2 Approval states

A recommended approval state machine:

`NOT_REQUIRED → PENDING → APPROVED | REJECTED | EXPIRED | REVOKED`

Additional implementation states MAY distinguish `WITHDRAWN` or `SUPERSEDED`, provided their semantics are explicit.

Rules:
- `PENDING` is not approval.
- Expiry is not approval.
- Silence is not approval.
- A missed notification is not approval.
- A workflow timeout is not approval.
- An approval for one version/action/target cannot be reused for another.
- Revocation MUST prevent future execution if the operation has not crossed an irreversible external boundary.
- If an operation is already in progress, the system must use the operation's cancellation/reconciliation semantics; it cannot pretend the external effect was undone.

### 10.3 Approval expiry

When an approval expires:
1. Mark it `EXPIRED` through the governance owner.
2. Emit an immutable transition event.
3. Prevent dependent actions from treating it as valid.
4. Preserve the review package and history.
5. Request renewed approval only when the workflow and policy permit it.

---

## 11. Durable jobs, workers and workflow progression

This section aligns with Part 4 (Persistent Job Queue, Scheduler & Worker Architecture) and Part 5 (Agent Contracts & Orchestration).

### 11.1 Distinguish the records

- **Workflow:** durable business process definition/instance and its dependencies.
- **Job:** durable unit of executable work with inputs, policy context and result.
- **Task:** scoped assignment/capability request, potentially routed to an agent or service.
- **Worker:** execution identity that leases and performs jobs.
- **Domain entity:** the business object being acted upon; its state remains domain-owned.

A workflow is not a job. A job is not a content item. A worker lease is not a business approval.

### 11.2 Job execution outcome

A recommended execution outcome vocabulary:

- `QUEUED`
- `LEASED`
- `RUNNING`
- `RETRY_WAIT`
- `SUCCEEDED`
- `FAILED`
- `CANCEL_REQUESTED`
- `CANCELLED`
- `TIMED_OUT`
- `UNKNOWN_OUTCOME`
- `DEAD_LETTERED`

Implementations may separate queue state from execution outcome where this improves clarity. They MUST document the distinction.

### 11.3 Lease semantics

A worker MUST acquire a time-bounded lease before executing a job.

The lease record SHOULD include:
- job ID;
- worker ID and worker identity version;
- lease token/fencing token;
- lease start and expiry;
- heartbeat/renewal time;
- attempt number;
- checkpoint reference.

Rules:
- Only the current lease holder may commit the protected job result.
- A monotonically increasing fencing token SHOULD prevent a stale worker from committing after a newer lease has been granted.
- A lease expiry makes the job eligible for recovery; it does not prove the old worker stopped.
- A recovered job MUST check for prior committed outputs and side effects before repeating work.
- Lease duration, heartbeat interval and retry schedule are configuration decisions, not hard-coded architecture facts.

### 11.4 Checkpoints and resumability

Long-running work SHOULD checkpoint at safe boundaries.

A checkpoint MUST identify:
- workflow/job version;
- completed steps;
- input and configuration versions;
- output/artifact references;
- external operation references;
- next safe resume point;
- relevant policy and permission context.

Resume MUST revalidate time-sensitive permissions and policy. A checkpoint is not a permanent authorization token.

### 11.5 Retry policy

Retries MUST be classified by operation type:

- **Pure/idempotent computation:** retry may be safe.
- **Idempotent external operation:** retry only with the same provider-supported idempotency key or verified equivalent.
- **Non-idempotent external operation:** reconcile before retry.
- **Irreversible or uncertain operation:** require explicit reconciliation/owner policy; never blindly repeat.

Retry policy MUST define maximum attempts, backoff, retryable errors, terminal errors, and dead-letter handling. Exact numerical values remain implementation decisions.

### 11.6 Cancellation and pause

Cancellation is a request, not proof that execution stopped.

- Queued jobs may be cancelled before lease acquisition.
- Running jobs should stop at a safe checkpoint where possible.
- Workers MUST check cancellation/pause signals at defined safe points.
- External operations already submitted require reconciliation and possibly provider-specific cancellation.
- The system MUST record whether cancellation was requested, acknowledged, completed or impossible.

A pause MUST prevent new eligible work from starting within its scope. It MUST NOT silently erase active jobs or audit history.

---

## 12. External side effects and unknown outcomes

This is a critical safety rule for publishing, uploads, payments, scheduling and any provider action that may not be safely repeated.

### 12.1 External operation state

A recommended external operation state machine:

`PREPARED → AUTHORIZED → SUBMITTED → CONFIRMED`

Alternative terminal or exception paths:

- `REJECTED`
- `FAILED_BEFORE_SUBMISSION`
- `UNKNOWN_OUTCOME`
- `CANCEL_REQUESTED`
- `CANCELLED`
- `RECONCILIATION_REQUIRED`

The precise state graph is provider-specific and must be documented by the adapter.

### 12.2 Unknown outcome protocol

If a timeout, connection loss or process crash occurs after submission may have reached the provider:

1. Record `UNKNOWN_OUTCOME`.
2. Preserve request payload hash, provider idempotency key, attempt ID and any response metadata.
3. Do not issue a fresh non-idempotent request.
4. Query provider status or use a provider webhook/reconciliation API where available.
5. Match provider-side records to the local operation using stable identifiers.
6. Resolve to `CONFIRMED`, `REJECTED`, `FAILED` or a documented unresolved exception.
7. Record the reconciliation evidence and actor.
8. Only retry after the adapter's safety rules prove it will not duplicate the side effect.

If the provider offers no reliable query or idempotency facility, the operation MUST remain in a controlled reconciliation path rather than being automatically retried.

### 12.3 Publishing adapter requirements

A publishing adapter MUST:
- accept only a scoped, current authorization decision;
- verify artifact and destination match the authorization;
- enforce the platform/account scope;
- use idempotency where supported;
- persist provider request/response references;
- distinguish submission from confirmed publication;
- expose reconciliation capability or explicitly document its absence;
- reject attempts when the emergency publishing pause is active;
- never create its own authorization based solely on a workflow state.

---

## 13. Pause, emergency stop and revocation

Emergency controls are layered and scoped. A control may apply globally or to a workspace, brand, studio, agent, integration, publishing path or financial action.

A pause/stop record SHOULD include:
- scope and target;
- initiating actor;
- reason and severity;
- effective time;
- affected operation classes;
- whether in-flight work is allowed to reach a safe checkpoint;
- release authority;
- release time and reason.

Requirements:
- A pause blocks new work in its scope.
- Security isolation or credential revocation takes precedence over normal recovery.
- A pause MUST NOT be interpreted as cancellation of an already-submitted external action.
- Releasing a pause does not automatically authorize previously blocked actions; guards and authorization must be re-evaluated.
- Agents and workers MUST NOT modify, release or widen their own emergency-control authority.

---

## 14. Stale, failed and recovery states

### 14.1 Stale projections

A read model may lag behind the authoritative state.

Interfaces and services SHOULD expose projection freshness or last-applied event version where operationally important. A stale projection MUST NOT be used as the final authorization source.

### 14.2 Recovery after crash

On restart, the system SHOULD:
1. load durable workflow/job state;
2. identify expired leases;
3. inspect checkpoints and committed outputs;
4. inspect pending outbox/inbox records;
5. identify external operations in uncertain states;
6. revalidate policy and credentials;
7. resume only safe work;
8. route uncertain/non-idempotent work to reconciliation;
9. emit recovery events and preserve the prior attempt history.

### 14.3 Dead-letter handling

Dead-lettering is an operational disposition, not deletion.

A dead-letter record MUST preserve:
- original job/event reference;
- failure class and sanitized diagnostic;
- attempt history;
- relevant correlation IDs;
- last checkpoint;
- remediation/replay eligibility;
- replay actor and reason, if replayed.

Replay MUST use current policy and authorization checks. It MUST NOT blindly reuse expired permissions.

---

## 15. Observability and audit

The platform MUST make it possible to trace a business request across workflow, job, task, worker, domain transitions, artifacts and external operations.

Minimum observability dimensions:
- workspace/brand/studio scope;
- correlation and causation IDs;
- workflow, job, task and worker IDs;
- entity type/ID and state version;
- transition reason code;
- actor and permission context;
- policy version;
- attempt and lease information;
- artifact/version references;
- external operation/provider reference;
- quality, rights and governance decisions.

Logs and traces MUST be sanitized. Secrets, access tokens and unnecessary personal data MUST NOT be written into ordinary logs or event payloads.

Audit history SHOULD support:
- who/what changed state;
- what changed and why;
- what evidence was considered;
- which policy version applied;
- what downstream action was triggered;
- whether it completed or required reconciliation.

Audit visibility MUST respect workspace isolation, data classification and role-based access.

---

## 16. Versioning and compatibility

### 16.1 State-machine versioning

Each state machine MUST have an explicit version.

A state-machine change that adds/removes states, changes transition legality, changes terminal-state meaning or changes authorization semantics is a compatibility-sensitive change.

Such a change requires:
- an architecture decision record;
- migration and compatibility plan;
- event/schema compatibility assessment;
- replay/recovery impact analysis;
- test cases for old and new records;
- owner approval where policy, security or foundational contracts are affected.

### 16.2 Event schema evolution

- Additive optional fields SHOULD be preferred.
- Consumers MUST tolerate unknown optional fields.
- Breaking changes require a new schema version and a controlled migration.
- Event meaning MUST NOT be changed while retaining the same schema/state-machine version.
- Historical events MUST remain interpretable under their recorded versions.

### 16.3 Policy versioning

Every governance decision MUST reference the policy version used.

Policy changes MUST NOT silently rewrite past decisions. For a pending or future action, the system must determine whether the prior decision remains valid under the policy's explicit applicability rules. If not, it must re-evaluate before execution.

---

## 17. Security, privacy and data handling

Lifecycle events are operational records and may contain sensitive context.

Requirements:
- Apply workspace/brand/studio isolation.
- Store only the minimum data needed in event payloads; prefer references to governed records.
- Apply Public/Internal/Confidential/Restricted classification.
- Enforce purpose limitation, consent and retention/deletion policies.
- Avoid embedding raw research notes, personal data, credentials or full provider payloads in broadly replicated events.
- Use scoped references and authorized retrieval for sensitive evidence.
- Ensure deletion/legal-hold workflows are compatible with audit and regulatory requirements.
- External AI/provider processing must satisfy the approved data-protection restrictions; if protections cannot be verified, block the transfer.

---

## 18. Recommended reason-code families

Reason codes SHOULD be stable, machine-readable and documented. Suggested families:

| Prefix | Meaning | Example |
|---|---|---|
| `USER_` | Explicit human request | `USER_SUBMITTED_FOR_REVIEW` |
| `AGENT_` | Authorized agent action | `AGENT_PREPARED_DRAFT` |
| `POLICY_` | Policy evaluation | `POLICY_HARD_BLOCKER` |
| `QUALITY_` | Quality evaluation | `QUALITY_NEEDS_REVIEW` |
| `RIGHTS_` | Rights evaluation | `RIGHTS_PENDING_VERIFICATION` |
| `SYSTEM_` | System lifecycle event | `SYSTEM_LEASE_EXPIRED` |
| `WORKER_` | Worker execution event | `WORKER_CHECKPOINT_SAVED` |
| `PROVIDER_` | External provider response | `PROVIDER_TIMEOUT_AFTER_SUBMISSION` |
| `RECON_` | Reconciliation action | `RECON_PROVIDER_STATUS_CONFIRMED` |
| `RECOVERY_` | Recovery process | `RECOVERY_RESUMED_FROM_CHECKPOINT` |
| `ADMIN_` | Authorized administrative action | `ADMIN_PAUSE_RELEASED` |

The list is illustrative. Each domain owns its detailed reason-code registry. Codes MUST NOT be reused with different meanings.

---

## 19. Acceptance criteria

An implementation conforms to this standard only when all applicable criteria are met.

### 19.1 State ownership and correctness
- [ ] Every state machine has one authoritative owner.
- [ ] Domain-specific state machines remain separate.
- [ ] Every transition validates source state, guards and expected version.
- [ ] Illegal transitions are rejected with structured reasons.
- [ ] State version increments exactly once per committed transition.
- [ ] Current-state projections can be reconciled with immutable history.

### 19.2 Event integrity
- [ ] All transition events use the common envelope.
- [ ] Event and state update are committed atomically through an outbox.
- [ ] Consumers are idempotent and deduplicate repeated delivery.
- [ ] Correlation and causation can trace cross-domain operations.
- [ ] Event schema and state-machine versions are recorded.

### 19.3 Governance and approval
- [ ] Quality, rights, governance disposition and human approval are separate.
- [ ] Approval binds to exact artifact/version/action/target/policy scope.
- [ ] Expiry, silence and notification failure never imply approval.
- [ ] Hard blockers cannot be bypassed by ordinary approval.
- [ ] `APPROVED_FOR_HANDOFF` cannot authorize public publishing.
- [ ] Autonomous public publishing remains disabled until explicit owner policy approval.

### 19.4 Jobs and recovery
- [ ] Workflow, job, task, worker and domain entity are distinct records.
- [ ] Jobs use durable leases and stale-worker protection.
- [ ] Long-running work can checkpoint and resume safely.
- [ ] Retries are operation-aware and idempotency-protected.
- [ ] Cancellation and pause outcomes are explicit.
- [ ] Dead-letter records preserve history and replay safeguards.

### 19.5 External operations
- [ ] Submission and confirmation are distinct.
- [ ] Unknown outcomes are recorded and reconciled.
- [ ] Non-idempotent uncertain operations are never blindly retried.
- [ ] Provider references and reconciliation evidence are retained.
- [ ] Adapters cannot self-authorize protected actions.

### 19.6 Security and operations
- [ ] Policy versions and actor identity are auditable.
- [ ] Sensitive payloads are minimized and sanitized.
- [ ] Emergency pause and credential revocation are enforced.
- [ ] Recovery revalidates permissions and policy.
- [ ] Observability supports end-to-end traceability without leaking secrets.

---

## 20. Required test scenarios

At minimum, automated tests SHOULD cover:

1. Valid transition commits one event and increments version once.
2. Illegal transition is rejected without mutation.
3. Stale expected version is rejected.
4. Duplicate command returns the original result.
5. Same idempotency key with different payload is rejected.
6. Outbox event is persisted atomically with state change.
7. Duplicate event delivery does not duplicate consumer effects.
8. Event ordering uses state version, not wall-clock timestamps.
9. Approval expires and dependent action remains blocked.
10. Silence or missed notification does not approve.
11. Artifact version change invalidates a scoped approval.
12. Hard rights/security blocker cannot be bypassed by ordinary approval.
13. `APPROVED_FOR_HANDOFF` does not authorize public publishing.
14. Publishing adapter rejects missing, stale or mismatched authorization.
15. Worker lease expiry prevents stale worker commit.
16. Recovery resumes from a valid checkpoint without duplicating committed outputs.
17. Cancellation request is distinguished from completed cancellation.
18. Provider timeout after possible submission creates `UNKNOWN_OUTCOME`.
19. Unknown non-idempotent operation is reconciled before retry.
20. Emergency pause blocks new scoped work.
21. Pause release triggers fresh policy/authorization evaluation.
22. Policy version change is reflected in future authorization checks.
23. Cross-workspace event/reference access is denied.
24. Dead-letter replay preserves attempt history and revalidates policy.

---

## 21. Open implementation decisions

This standard intentionally does not invent implementation-specific values. The following remain to be selected during implementation planning:

- Exact state graph and terminal states for every domain entity.
- Database schema, event-store/outbox layout and partitioning.
- Event transport and delivery topology.
- State-version storage and concurrency implementation.
- Idempotency-key scope and retention duration.
- Lease duration, heartbeat interval and fencing-token implementation.
- Retry limits, backoff schedules and dead-letter thresholds.
- Checkpoint frequency and storage format.
- Provider-specific reconciliation methods and retention.
- Exact reason-code catalogue.
- Event schema registry and compatibility tooling.
- Audit retention, legal-hold and deletion implementation.
- Projection freshness objectives and operational SLOs.
- Notification channels and escalation rules.
- Primary cloud provider, region and deployment topology.

These decisions MUST be made with the relevant contracts and approved deployment/security constraints in view. They are not authorization to provision infrastructure or incur expenditure.

---

## 22. Explicit non-goals and authority boundaries

This document does not:
- approve implementation readiness;
- authorize repository, GitHub or code access;
- authorize code changes or agent reassignment;
- select or connect external providers;
- select a cloud provider or region;
- provision infrastructure or create subscriptions;
- authorize spending or financial commitments;
- approve autonomous public publishing;
- authorize uploads, external distribution or public release;
- grant agents or workers new permissions;
- change owner-approved mission, policy or architecture.

Any such action requires its own explicit authorization.

## 23. Architecture decision summary

| Decision | Standard |
|---|---|
| Universal lifecycle enum | Rejected |
| Domain-specific state machines | Required |
| Common transition envelope | Required |
| Single authoritative state owner | Required |
| Immutable transition history | Required |
| State version + optimistic concurrency | Required |
| Transactional outbox/inbox and idempotent consumers | Required |
| Workflow/job/task/worker distinction | Required |
| Durable leases and checkpoint recovery | Required |
| Separate quality, rights, approval and authorization | Required |
| Silence/expiry as approval | Prohibited |
| Hard-blocker bypass by ordinary approval | Prohibited |
| `APPROVED_FOR_HANDOFF` as public publish approval | Prohibited |
| Blind retry after uncertain external side effect | Prohibited |
| Autonomous public publishing | Disabled pending explicit owner policy approval |

---

**End of Artifact 02 — Unified Lifecycle & State Transition Standard 1.0**

**Next recommended artifact:** Artifact 03 — API & Event Contract Standard 1.0.
