# NEXTDECODE P0 — Batch 16: Domain & Interface Contract Closure Pack

**Source:** `NEXTDECODE_P0_Batch16_Domain_Interface_Contract_Closure_Pack.docx` (ChatGPT Library)
**Prepared:** 1 November 2026
**Source-declared status:** Detailed contract candidate; not formally frozen
**Owner status:** Final consolidated owner freeze confirmation pending
**Implementation status:** Not authorized
**Conversion note:** Text extracted from the 19-page DOCX. Page boundaries are retained; multi-column/table-like text is preserved in monospaced blocks. This Markdown is a working reading copy, not an owner-approved replacement for the original DOCX.

---


                                                   NEXTDECODE

                            P0 DOMAIN & INTERFACE
                        CONTRACT CLOSURE PACK
                                  Batch 16 | Detailed reconciliation candidate


```text
    Document control                                             Value
    Series                                                       NEXTDECODE Content OS — P0 documentation series
    Batch                                                        16 — Domain & Interface Contract Closure Pack
    Prepared                                                     1 November 2026
    Document status                                              Detailed contract candidate; not formally frozen
    Owner status                                                 Final consolidated owner freeze confirmation pending
    Implementation status                                        Not authorized
```
                                                                 Domain ownership, identity/versioning, lifecycle, commands,
    Scope                                                        queries, events, workers, artifacts, governance and cross-package
                                                                 interfaces
                                                                 Accepted ADR/CF decisions are carried forward; unresolved
    Authority rule
                                                                 detailed semantics remain open and are not silently decided


Purpose. Convert the accepted architectural direction and the discovered canonical standards into a single,
reviewable domain/interface contract candidate. This pack is intended to make the remaining contract decisions
explicit and testable before any implementation authorization.

Important limitation. This is a documentation-level reconciliation based on the project source summaries and named
standards already identified in the P0 source review. It does not claim that every field, enum, endpoint, payload,
timeout, retry count, retention period, provider, or operational threshold has been owner-approved.


1. Executive contract position
NEXTDECODE Content OS is a modular, single-owner Creator Mode system. The logical modules are product/domain
boundaries, not a mandate to deploy microservices. The shared control plane is intended to become the authoritative
home for shared workflow state. Existing Shorts Studio remains the specialist Python/FFmpeg production engine
behind a bounded adapter.

- Canonical identity is immutable and uses UUIDv7 as accepted in ADR-001. Entity identity and immutable version
       identity are separate concepts.
- A domain has one authoritative owner for its canonical state. Other modules interact through versioned contracts
       rather than writing another domain’s state.
- Commands express intent; queries read state; events record committed facts. An event is not itself permission to
       perform a protected action.
- Lifecycle, execution, quality, governance, approval, authorization and external-operation outcomes are distinct
       state dimensions.
- Approval is not authorization; authorization is not execution; execution is not proof of a successful external
       outcome.
- Unknown, missing, ambiguous, expired, revoked or unverified rights/approval/authorization must never grant
       permission.


---

- Public automatic publishing remains disabled pending a separate owner-approved policy. Human approval is
       required before critical publishing actions.
- The architecture remains local-first/free-first. No paid provider, hosted service or deployment is selected or
       activated by this pack.


### 1.1 Accepted decision baseline
    Decision                                 Accepted direction                              Contract implication
                                                                                             Use canonical IDs consistently; do not
    ADR-001                                  UUIDv7 canonical identifiers; immutable
                                                                                             recycle identity.
                                                                                             Domain records and transactionally
                                             PostgreSQL-compatible relational DB as
    ADR-002                                                                                  coupled state changes belong in the
                                             authoritative shared-state store
                                                                                             authoritative relational store.
                                             DB-backed durable queue with                    Do not treat in-memory queues or best-
    ADR-003
                                             transactional outbox/inbox initially            effort events as durable execution.
                                                                                             Every command/event/query schema must
                                             Versioned HTTP/JSON contracts with
    ADR-004                                                                                  have an explicit version and compatibility
                                             schema validation
                                                                                             policy.
                                                                                             Workers receive bounded assignments;
                                             Unique worker identity, scoped short-lived
    ADR-005                                                                                  identity and capability are verified at
                                             credentials and capability authorization
                                                                                             execution.
                                             Relational artifact metadata; binaries          Metadata and binary storage are separate;
    ADR-006
                                             behind object-storage abstraction               provider choice remains deferred.
                                                                                             Protected operations require central policy
                                             Centralized authorization; publishing
    ADR-007                                                                                  evaluation and execution-time
                                             adapters cannot bypass
                                                                                             enforcement.
                                             QA outcomes: PASS,
                                                                                             Hard blockers remain non-bypassable by
    ADR-008                                  PASS_WITH_WARNINGS, NEEDS_REVIEW,
                                                                                             ordinary approval.
                                             BLOCKED
                                             Evidence-backed rights states and use-          Rights decisions bind to evidence and
    ADR-009
```text
                                             specific enforcement                            intended use, not a generic cleared flag.
    ADR-010                                  Separate lifecycle state machines               No overloaded universal status field.
```


### 1.2 Accepted cross-cutting contract decisions
```text
    Contract family                                                  Accepted baseline
    CF-01–CF-15                                                      Explicitly accepted by owner; carry forward as baseline.
```
                                                                     Accepted under the standing delegation rule; canonical semantics
    CF-16–CF-21
                                                                     still require faithful detailed representation.
                                                                     UNKNOWN, PENDING_REVIEW, CLEARED, RESTRICTED, EXPIRED,
    CF-20 rights vocabulary
                                                                     REVOKED, DENIED.
                                                                     APPROVED, REJECTED, CHANGES_REQUESTED, EXPIRED,
    CF-21 approval vocabulary
                                                                     REVOKED.
```text
    CF-22                                                            Owner explicitly selected Option A: centralized authorization.
    CF-23                                                            Accepted under standing delegation.
    CF-24                                                            No paid services; provider and operational choices deferred.
```


2. Contract design principles and normative language
    Term                                                             Meaning in this pack
                                                                     Required to preserve an accepted invariant or prevent an
    MUST
                                                                     unsafe/ambiguous action.
    MUST NOT                                                         Prohibited by accepted direction or a fail-closed control.
                                                                     Strong design recommendation; deviation requires documented
    SHOULD
                                                                     rationale and review.


---

    MAY                                                                  Permitted option where the detailed choice is still open.
                                                                         Not resolved by the available accepted owner decisions; requires
    OPEN
                                                                         owner disposition or a later approved design decision.
                                                                         Example only; not a frozen endpoint, field, enum, or operational
    ILLUSTRATIVE
                                                                         value.


- No contract may infer authority from a UI state, local cache, agent output, event receipt, or an unverified external
          response.
- Every state-changing command must identify the target, caller context, expected version/state where relevant,
          idempotency key, correlation context and policy context.
- Every committed transition must be attributable, auditable and versioned.
- Unknown external side effects must be reconciled before retrying; blind retry can duplicate publication or
          another external action.
- Detailed values not found in accepted sources remain open. This includes numeric lease durations, retry limits,
          retention periods, size limits, endpoint paths and provider-specific protocols.


3. Canonical entity identity, versioning and ownership
The canonical data dictionary is the naming and ownership reference. Avoid generic status fields. Use explicit state
dimensions such as lifecycle_status, epistemic_status, quality_outcome, governance_disposition, approval_outcome,
execution_status and external_operation_status.
    Entity / record family           Identity and version rule           Canonical owner / boundary          Contract notes
                                                                                                             Initial scope is one owner and
                                     Immutable entity ID; version
                                                                                                             one workspace; do not design
    Workspace                        only where configuration is         Workspace & Control Center
                                                                                                             multi-tenant assumptions as an
                                     versioned
                                                                                                             initial requirement.
                                                                                                             Initial active brand is
                                     Immutable entity ID; brand
    Brand                                                                Brand Intelligence                  NEXTDECODE; scope must
                                     configuration may be versioned
                                                                                                             remain explicit.
                                                                                                             Represents the canonical
    ContentItem                      Stable editorial subject identity   Content Graph                       content subject, not each
                                                                                                             rendition or output file.
                                                                                                             A platform/format-specific
```text
                                     Distinct derivative/format          Content Graph / Creation
    ContentVariant                                                                                           rendition is not a new canonical
                                     identity linked to a ContentItem    boundary
```
                                                                                                             subject.
                                                                                                             Version identity is distinct from
```text
                                     Immutable snapshot/version of                                           entity identity; exact version
    ContentVersion                                                       Content Graph
                                     content state or content payload                                        must be referenced by review
```
                                                                                                             and downstream operations.
                                                                                                             Describes reusable workflow
```text
                                     Versioned                           Automation & Agent
    WorkflowDefinition                                                                                       structure; not a running
                                     definition/configuration            Orchestration
```
                                                                                                             execution.
                                                                                                             Owns run lifecycle and
                                     Unique execution instance           Automation & Agent                  orchestration correlation; not
    WorkflowRun
                                     linked to a definition version      Orchestration                       interchangeable with a
                                                                                                             definition.
                                     Reusable task                       Automation & Agent                  Defines work semantics and
    TaskDefinition
                                     specification/version               Orchestration                       required capability.
                                                                                                             Execution unit instance;
```text
                                     Unique scheduled/created task       Automation & Agent
    TaskInstance                                                                                             cardinality with jobs must be
                                     occurrence                          Orchestration
```
                                                                                                             explicitly specified.
                                     Durable unit of                     Automation & Agent                  Owns execution status and
    Job
                                     scheduled/dispatchable work         Orchestration                       idempotent dispatch semantics.
                                                                                                             Attempt history is append-
```text
                                     One bounded attempt to execute      Automation & Agent
    JobAttempt                                                                                               oriented; retry creates another
                                     a Job                               Orchestration
```
                                                                                                             attempt, not a rewritten history.


---

                                                                                                        Identity is distinct from a
                                  Stable worker identity with        Automation & Agent
 Worker                                                                                                 session/credential; capability is
                                  lifecycle and trust posture        Orchestration
                                                                                                        separately evaluated.
                                  Logical named output or asset                                         Stable identity; points to one or
 Artifact                                                            Asset Management
                                  identity                                                              more immutable versions.
                                                                                                        Repair or replacement creates a
                                  Immutable binary/manifest
 ArtifactVersion                                                     Asset Management                   new version; do not overwrite
                                  version with integrity metadata
                                                                                                        an existing immutable version.
                                  Result bound to exact
                                                                                                        Outcome is not the same as
 Review / QA result               subject/version and policy         Content Quality Intelligence
                                                                                                        approval or authorization.
                                  context
                                                                                                        Must express intended use and
                                  Evidence-backed, use-specific
 Rights record                                                       Governance boundary                evidence; generic rights
                                  rights determination
                                                                                                        clearance is insufficient.
                                                                                                        Approval may expire or be
                                  Attributable decision bound to
 Approval decision                                                   Governance boundary                revoked; never treat as
                                  exact version and context
                                                                                                        evergreen.
                                  Central policy decision bound to
                                                                                                        Default-deny; evaluated at
 Authorization decision           action/resource/version/destinat   Central authorization boundary
                                                                                                        execution time.
                                  ion/time
                                                                                                        External side effect state must
                                  External operation instance and
 Distribution operation                                              Distribution Studio                be reconciled; unknown is not
                                  outcome
                                                                                                        success.


### 3.1 Content identity rules
1.   Create one ContentItem for the canonical editorial subject.
2.   Create ContentVariant records for meaningful derivatives (for example, a short-form cut, a long-form edit, or a
     platform-specific rendition) while preserving the parent relationship.
3.   Create immutable ContentVersion snapshots whenever a versioned content state changes in a way that must be
     reviewable or reproducible.
4.   A review, approval, rights evaluation, authorization and distribution request must reference the exact relevant
     content/version/variant and destination context.
5.   A regenerated or repaired output must receive a new ArtifactVersion; it must not silently mutate a previously
     reviewed artifact.
Open cardinality decision: the exact mapping among ContentItem, ContentVariant, ContentVersion, WorkflowRun,
TaskInstance, Job and JobAttempt must be frozen in the detailed schema pack. This document records the separation
and ownership boundaries but does not invent one-to-one or one-to-many cardinalities where the accepted source
summaries do not specify them.


4. Domain ownership and write boundaries
 Logical module                              Owns canonical state for                       Must not become owner of
                                             Workspace configuration, owner-level
                                                                                            Content lifecycle, worker execution, artifact
 1. Workspace & Control Center               controls, operational overview and policy
                                                                                            binary truth or external publish outcome.
                                             configuration references
                                             ContentItem, ContentVariant,
                                                                                            QA decisions, rights decisions, worker
 2. Content Graph                            ContentVersion relationships and editorial
                                                                                            leases or distribution outcomes.
                                             lineage
                                             Knowledge sources, captured references,
 3. Knowledge Management                     provenance and managed knowledge               Content approval or authorization.
                                             records
                                             Research records, source evidence and          Canonical content version or rights
 4. Research Intelligence
                                             research outputs                               clearance.
                                             Brand profile, voice rules, identity and
 5. Brand Intelligence                                                                      Final QA/approval or publish authorization.
                                             brand configuration versions

---

                                                  Strategy, objectives, calendars, plans and
    6. Strategy & Planning                                                                         Execution truth for jobs or publication.
                                                  planning decisions
                                                  Quality evaluations, evidence, outcomes
    7. Content Quality Intelligence                                                                Approval or authorization state.
                                                  and policy-bound findings
                                                  Creation requests and orchestration
                                                                                                   Canonical content identity, central
    8. Multiformat Creation Engine                references; specialist engine adapter
                                                                                                   authorization or final distribution truth.
                                                  contract
                                                  Artifact metadata, versions, manifests,          Content editorial approval or publish
    9. Asset Management
                                                  integrity, storage/transfer and lineage          permission.
                                                  Workflow definitions/runs, tasks, jobs,
    10. Automation & Agent Orchestration                                                           Rights, approval or authorization decisions.
                                                  attempts, worker registry and dispatch state
                                                  Distribution package, destination mapping        Independent authorization policy or
    11. Distribution Studio
```text
                                                  and external operation records                   bypass-capable publish permission.
                                                  Metrics, observations, attribution and           Retroactive mutation of source-of-truth
```
    12. Analytics & Learning
                                                  learning records                                 lifecycle or approval state.


Write-boundary rule: only the authoritative domain owner may commit its canonical state transition. Other domains
request changes through commands or consume committed events. Cross-domain transactions must use an explicitly
designed orchestration/saga or durable message pattern; do not simulate atomicity with informal multi-table writes.


5. Lifecycle and state-dimension contract
The unified lifecycle standard requires separate domain-owned state machines and a common auditable transition
envelope. A universal status enum is prohibited because it collapses materially different facts.
    State dimension                   What it answers                     Example values / form                Authority
                                                                          Domain-specific states; exact
                                      Where is this entity in its own
    Lifecycle status                                                      vocabularies per state machine       Owning domain
                                      lifecycle?
                                                                          remain to be frozen
                                                                          Queued, running, succeeded,
                                      What happened to a
    Execution status                                                      failed, cancelled are illustrative   Execution owner
                                      run/job/attempt?
                                                                          pending exact frozen enum
```text
                                      Did the evaluated version meet      PASS, PASS_WITH_WARNINGS,
    Quality outcome                                                                                            Quality domain
                                      quality policy?                     NEEDS_REVIEW, BLOCKED
```
                                                                          UNKNOWN, PENDING_REVIEW,
                                      Is this use supported by the
    Rights status                                                         CLEARED, RESTRICTED,                 Rights/governance owner
                                      rights evidence?
                                                                          EXPIRED, REVOKED, DENIED
                                                                          APPROVED, REJECTED,
                                      What did the authorized
    Approval outcome                                                      CHANGES_REQUESTED,                   Approval owner
                                      reviewer decide?
                                                                          EXPIRED, REVOKED
                                                                          Allow/deny decision with policy
```text
                                      May this exact action be                                                 Central authorization
    Authorization decision                                                and binding context; exact
                                      executed now?                                                            service/policy boundary
```
                                                                          schema open
                                                                          Confirmed, rejected,
```text
                                      What is known about the             unknown/reconciliation-
    External operation status                                                                                  Distribution operation owner
                                      external side effect?               required are conceptual
```
                                                                          distinctions; exact enum open
                                                                          Explicit
                                      How certain/verified is this
    Epistemic status                                                      verified/unverified/unknown          Owning domain
                                      information?
                                                                          semantics; exact enum open
```text
                                      What governance handling is         Policy-specific disposition; exact
    Governance disposition                                                                                     Governance owner
                                      required?                           vocabulary open
```


### 5.1 Transition envelope
Every committed state transition SHOULD carry, at minimum, the fields identified by the lifecycle standard:

- event_id; entity_id; entity_type; owning_domain;


---

- state_machine_name and state_machine_version; state_version;
- prior_state and new_state; occurred_at and recorded_at (UTC);
- actor_id/reference and actor_type; reason;
- correlation_id and causation_id; policy_version where relevant;
- evidence/result references where relevant; schema_version.
The exact required/optional status of each field must be frozen in the schema. A transition must be attributable and
auditable; consumers must not infer a transition from an uncommitted command request.


### 5.2 Transition control rules
6.     Validate the transition against the owning state machine and current state version.
7.     Reject stale expected-version writes as conflicts rather than silently overwriting newer state.
8.     Record actor, reason, timestamps, prior/new state and correlation references.
9.     Commit the state change and durable outbox record atomically where the event represents the committed fact.
10. Consumers deduplicate event delivery and maintain their own projection/checkpoint without claiming ownership
       of source state.
11. If an external side effect may have occurred but confirmation is missing, set/retain a reconciliation-required
       condition; do not blindly replay the side effect.


6. Command, query and event interface standard
The API/Event Contract Standard establishes a versioned HTTP/JSON direction. The examples below describe contract
families and semantics, not frozen URL paths. Exact route names, request/response schemas, error codes and
pagination conventions remain subject to detailed freeze.
    Interface type                 Purpose                            Must include / guarantee            Must not imply
                                                                      Caller scope; filters;
```text
                                   Read authoritative or explicitly                                       Permission to mutate or
    Query                                                             pagination/consistency
                                   identified projection state                                            execute.
```
                                                                      semantics; schema version
                                                                      Command ID/type/version;
                                                                      target; workspace/scope;
                                                                      requested_by; requested_at;
                                                                                                          That the operation has
    Command                        Express a state-changing intent    expected state version;
                                                                                                          completed.
                                                                      idempotency key;
                                                                      correlation/causation; policy
                                                                      context; payload
                                                                      Event ID; entity/type/domain;
                                                                      state machine/version; state
                                                                      version; prior/new state;
                                                                                                          Authorization to trigger a
    Event                          Record a committed fact            timestamps; actor; reason;
                                                                                                          protected action.
                                                                      correlation/causation;
                                                                      policy/evidence refs; schema
                                                                      version


### 6.1 Command outcome semantics
    Outcome                                    Meaning                                        Consumer behavior
                                               Command durably accepted for
                                                                                              Track the referenced operation; do not
    ACCEPTED                                   asynchronous processing; a durable
                                                                                              report completion.
                                               reference is returned
                                               Command processing reached its defined         Read the resulting authoritative state and
    COMPLETED
```text
                                               completion point                               any external outcome record.
                                               Command is invalid, unauthorized, policy-      Surface the reason; do not retry unchanged
```
    REJECTED
                                               blocked or otherwise not admissible            input blindly.

---

                                                Expected state/version or idempotency         Refresh authoritative state and require a
 CONFLICT
                                                context conflicts with current truth          deliberate new command.


A synchronous command may return a terminal result only when the contract defines that processing is complete. An
asynchronous ACCEPTED response must include a durable operation/job reference. The exact response shape remains
open.


### 6.2 Command envelope — required design fields
 Field                                          Contract purpose                              Status
                                                Unique command identity for audit and         Required design element; exact
 command_id
                                                deduplication                                 type/schema to freeze
 command_type / command_schema_version          Selects semantics and parser version          Required design element
 target_type / target_id                        Identifies intended aggregate/entity          Required design element
                                                Constrains tenant/workspace and resource      Required where applicable; exact scope
 workspace_id / scope
                                                scope                                         object open
                                                                                              Required; actor identity must be derived
 requested_by / requested_at                    Attribution and request time                  from authenticated context, not trusted
                                                                                              from payload
 expected_state_version                         Optimistic concurrency guard                  Required for version-sensitive transitions
                                                                                              Required for retryable state-changing
 idempotency_key                                Prevents duplicate command effects
                                                                                              operations; scope/retention open
 correlation_id / causation_id                  Connects workflow and causal chain            Required design element
                                                Carries policy references/inputs for          Required where policy-controlled; exact
 policy_context
                                                evaluation                                    structure open
 payload                                        Command-specific validated data               Schema-versioned


### 6.3 Event envelope — required design fields
 Field                                          Contract purpose                              Status
 event_id                                       Unique event identity                         Required design element
                                                Identifies changed entity and owning
 entity_id / entity_type / domain                                                             Required design element
                                                domain
 state_machine / state_machine_version /
                                                Identifies committed transition and version   Required for state-transition events
 state_version
 prior_state / new_state                        Makes transition explicit                     Required for state-transition events
                                                Separates event time from
 occurred_at / recorded_at                                                                    UTC; exact precision/schema open
                                                persistence/recording time
 actor_ref / actor_type / reason                Audit attribution                             Required design element
                                                Traceability across commands, jobs and
 correlation_id / causation_id                                                                Required design element
                                                events
                                                Supports governance and evidence
 policy_version / evidence_refs / result_refs                                                 Required where relevant
                                                traceability
 schema_version                                 Consumer compatibility and evolution          Required design element


7. Durable messaging, outbox/inbox and idempotency
ADR-003 selects a DB-backed durable queue with transactional outbox/inbox as the initial direction. Delivery should
be designed for at-least-once behavior; correctness therefore depends on idempotency and deduplication rather than
an assumption of exactly-once delivery.
 Mechanism                                      Required behavior                             Open details


---

                                                  Commit source state change and event
                                                  intent in one database transaction; publish   Schema, polling/claim strategy, retention
    Transactional outbox
                                                  asynchronously from durable outbox            and operational thresholds.
                                                  records.
                                                  Persist message receipt/deduplication
                                                  identity before applying consumer effects;    Dedup key scope, retention and consumer
    Inbox / consumer receipt
                                                  repeated delivery must not duplicate          transaction pattern.
                                                  effects.
                                                  A repeated command with the same key
                                                                                                Key format, scope, expiry and behavior for
    Idempotency                                   and same semantic request must not create
                                                                                                same key/different payload.
                                                  duplicate protected effects.
                                                  Preserve or detect ordering where entity
                                                                                                Partitioning/ordering guarantee and gap-
    Ordering                                      transitions require it; reject stale state
                                                                                                recovery procedure.
                                                  versions.
                                                  Repeatedly failing messages become visible    Retry thresholds, backoff, operator
    Dead-letter / poison handling
                                                  and recoverable, not silently dropped.        workflow and retention.
                                                  Replay must preserve original event
                                                                                                Replay authorization, projection rebuild
    Replay                                        identity and be safe for consumers; side
                                                                                                and side-effect suppression rules.
                                                  effects require separate safeguards.


- A successful broker/queue publish is not proof that a consumer applied the event.
- A consumer acknowledgment is not proof that an external platform operation succeeded.
- Outbox/inbox records must be correlatable to the originating command, job, attempt and domain transition.
- Do not use an event replay to repeat an external publish unless a fresh authorization and explicit replay policy
          permit it.


8. Workflow, task, job and attempt boundaries
    Concept                          Definition                           State owner                      Boundary rule
                                     Reusable, versioned
```text
                                                                          Automation & Agent               Immutable/versioned definition
    WorkflowDefinition               graph/recipe describing
                                                                          Orchestration                    reference captured by each run.
```
                                     orchestration
                                     One execution instance of a
```text
                                                                          Automation & Agent               Own lifecycle and correlation;
    WorkflowRun                      selected WorkflowDefinition
                                                                          Orchestration                    not the definition itself.
```
                                     version
                                     Reusable specification for a unit    Automation & Agent               Describes input/output contract
    TaskDefinition
```text
                                     of work                              Orchestration                    and required capability.
                                     One concrete occurrence of a         Automation & Agent               Own identity and execution
```
    TaskInstance
                                     task in a run or schedule            Orchestration                    relationship.
                                                                                                           Owns queue/dispatch/execution
                                                                          Automation & Agent
    Job                              Durable dispatchable work unit                                        status and idempotent
                                                                          Orchestration
                                                                                                           scheduling.
                                                                                                           Append-oriented attempt
```text
                                     One bounded execution attempt        Automation & Agent
    JobAttempt                                                                                             history; never rewrite an earlier
                                     for a Job                            Orchestration
```
                                                                                                           attempt as a later retry.


Unresolved mapping: the exact cardinality between TaskInstance and Job (one-to-one, one-to-many, or other) is not
asserted here. A frozen schema must define how one task can produce multiple jobs, how fan-out/fan-in is
represented, and which aggregate owns completion.


### 8.1 Execution invariants
- Every Job is durably recorded before dispatch.
- Every attempt is attributable to a worker identity and bounded assignment.
- A retry creates a new JobAttempt and preserves the prior attempt outcome/evidence.
- A worker lease/claim must be validated against current job state and lease generation/version.


---

- Late results from an expired or superseded attempt must not overwrite a newer accepted result.
- Job success is not equivalent to content QA pass, approval, authorization or distribution success.
- A workflow run can complete only according to its frozen orchestration semantics; a task/job terminal state does
       not automatically define run completion.


9. Worker identity, trust and capability interface
ADR-005 and CF-18/related worker decisions establish unique worker identity, scoped short-lived credentials and
capability authorization. The exact credential protocol, capability catalogue, isolation model and numeric expiry/lease
values remain open.
```text
    Contract element                            Minimum requirement                             Still open
                                                Stable unique worker ID; lifecycle/trust        Registration ceremony, identity proof and
```
    Worker identity
                                                state; auditable registration and revocation.   exact schema.
                                                Short-lived, scoped, revocable credential;
                                                                                                Issuance protocol, TTL, refresh, rotation
    Credential                                  never embed long-lived secrets in job
                                                                                                and storage.
                                                payloads.
                                                Explicit declared capability checked against    Canonical capability taxonomy, versioning
    Capability
                                                assignment requirements and policy.             and evidence of capability.
                                                Bound to job/attempt, required capability,
                                                                                                Exact assignment envelope and lease
    Assignment                                  input references, output contract and
                                                                                                semantics.
                                                expiry/lease context.
                                                Limit worker access to only required inputs,    Sandbox/container/process model and
    Execution isolation
                                                tools, secrets and outputs.                     platform-specific hardening.
                                                Revoked/expired workers or credentials
                                                                                                Propagation SLA and in-flight
    Revocation                                  cannot claim new work or continue
                                                                                                cancellation/reconciliation.
                                                protected actions.
                                                Local-only work remains safely pending          Wake-up/heartbeat cadence and offline
    Local worker availability
                                                when the local worker is unavailable.           recovery policy.


### 9.1 Worker authorization sequence
12. Authenticate the worker using its registered identity and current credential.
13. Verify worker lifecycle/trust state and credential validity/revocation.
14. Check declared capability against the job requirement and current policy.
15. Claim/lease the job atomically; record worker, attempt and lease generation.
16. Issue only the minimum assignment inputs and permitted secret references.
17. Validate result schema, output ownership and artifact integrity before accepting the result.
18. Reject late, duplicate, stale or out-of-scope results; preserve diagnostic evidence.
19. Re-evaluate authorization for any protected downstream action rather than inheriting worker permission.


10. Artifact, version, manifest and transfer contract
ADR-006 separates relational artifact metadata from binary storage behind an abstraction. Artifact identity and
ArtifactVersion are distinct. Storage provider, retention, encryption/key management and exact manifest schema
remain deferred.
```text
    Record / concept                            Required responsibility                         Control
                                                Stable logical asset/output identity and        Canonical ID; owner; scope; purpose;
```
    Artifact
                                                classification/context                          provenance.
                                                                                                Version ID; checksum; byte size/media type
                                                Immutable version of bytes and associated
    ArtifactVersion                                                                             where applicable; created time; producer
                                                metadata
                                                                                                reference.


---

                                                                                              Versioned schema; deterministic
                                              Describes files/components, relationships
    Manifest                                                                                  references; integrity checks; no assumed
                                              and package composition
                                                                                              mutable overwrite.
                                                                                              Source/destination references; transfer
                                              Tracks movement between
    Transfer record                                                                           identity; timestamps; result; checksum
                                              worker/local/cloud/storage boundaries
                                                                                              verification.
                                              Records validation performed on a specific      Validator/version; checks; outcome;
    Validation record
                                              artifact version                                evidence; time; correlation.
                                                                                              Reason; source; evidence; disposition;
    Quarantine record                         Tracks withheld/untrusted/invalid artifacts
                                                                                              authorized release path.
                                              Connects inputs, transformations, outputs       Parent refs; transformation/engine version;
    Lineage edge
                                              and producer attempts                           job/attempt; reproducibility metadata.


### 10.1 Artifact safety rules
- Never overwrite an immutable ArtifactVersion. A correction, repair or regeneration creates a new version.
- A manifest must identify exact artifact versions; a floating 'latest' reference is not sufficient for approval or
       distribution.
- Checksum mismatch, incomplete transfer, malformed manifest or failed validation blocks downstream use until
       resolved.
- Quarantined artifacts are not eligible for normal creation, review or distribution flows.
- Storage location is not an authorization grant. Access is checked centrally and scoped to the requester/worker and
       purpose.
- Deletion, retention, legal hold, encryption, backup and provider-specific semantics remain open and require
       explicit policy contracts.


11. Governance, quality, rights, review, approval and authorization
Governance is a set of distinct controls, not one boolean gate. A decision must be tied to the subject/version, intended
use, destination, evidence and applicable policy version.
    Control                                   Canonical vocabulary / model                    Binding and enforcement
                                                                                              Exact version + QA policy + evidence.
                                              PASS; PASS_WITH_WARNINGS;
    Quality outcome                                                                           BLOCKED is a hard blocker and cannot be
                                              NEEDS_REVIEW; BLOCKED
                                                                                              bypassed by ordinary approval.
                                                                                              Evidence-backed and use-specific. A
                                              UNKNOWN; PENDING_REVIEW; CLEARED;
    Rights status                                                                             CLEARED status for one use does not imply
                                              RESTRICTED; EXPIRED; REVOKED; DENIED
                                                                                              clearance for another.
```text
                                              APPROVED; REJECTED;                             Attributable reviewer; exact content/artifact
    Approval outcome                          CHANGES_REQUESTED; EXPIRED;                     version; scope and context;
                                              REVOKED                                         expiry/revocation semantics.
```
                                              Central allow/deny decision with exact
                                                                                              Default-deny; evaluated at execution time;
    Authorization                             action/resource/version/destination/policy/ti
                                                                                              distinct from approval.
                                              me binding
```text
                                              External operation record with                  Destination-specific; authorization checked
    Distribution operation                    known/unknown/confirmed outcome                 immediately before side effect; uncertain
                                              semantics                                       outcome reconciled.
```


### 11.1 Central authorization boundary
- CF-22 Option A is accepted: authorization is centralized.
- The authorization decision must bind the exact action, resource, immutable version, destination, policy version
       and validity window.


---

- Authorization is default-deny when required context is absent, stale, ambiguous or unverifiable.
- Execution-time enforcement must check expiry, revocation, emergency pause and current policy.
- Publishing adapters and workers cannot self-authorize or bypass the central boundary.
- Approval is one input to authorization, not a substitute for it.
- A previously authorized request must not be assumed valid after material resource/version/destination/policy
      changes.


### 11.2 Emergency pause — owner decision still required
The reconciliation material identifies emergency-pause semantics as an incomplete detailed contract. The design must
specify who may activate/deactivate it, scope (global/workspace/brand/destination/action), propagation and cache
invalidation, behavior for in-flight work, audit evidence, break-glass handling and recovery. This pack does not invent
those powers or choose the propagation SLA.


### 11.3 Rights vocabulary reconciliation
The canonical CF-20 vocabulary is preserved exactly. An older detailed schema used PENDING_VERIFICATION and
PROHIBITED; the reconciliation notes a documentation-only mapping issue. This pack does not silently equate,
migrate or alias those values. The owner-approved canonical values above govern the candidate vocabulary;
migration/legacy interpretation remains a separate explicit task.


### 11.4 Approval vocabulary reconciliation
The canonical CF-21 vocabulary includes CHANGES_REQUESTED, EXPIRED and REVOKED in addition to APPROVED
and REJECTED. Any older schema that supports only APPROVED/REJECTED is incomplete relative to the accepted
vocabulary and must be reconciled before freeze.


12. Distribution and external side-effect contract
20. Create a distribution request/package referencing exact immutable content and artifact versions, destination and
      intended operation.
21. Validate package integrity, rights for the destination/use, QA outcome, approval outcome and policy prerequisites.
22. Request a central authorization decision bound to the exact action/resource/version/destination/policy/time.
23. Immediately before execution, re-check authorization validity, revocation and emergency pause.
24. Execute through a bounded distribution adapter that cannot bypass central authorization.
25. Persist the external operation request/attempt and provider correlation reference before or atomically with the
      side-effect workflow as the detailed adapter contract permits.
26. Record confirmed success only when the external platform response/evidence supports it. If outcome is
      ambiguous, mark reconciliation required and inspect remote state before retry.
27. Keep automatic public publishing disabled until a separate policy and explicit authorization permit it.
The source review identified historical direct-upload paths in the existing Shorts Studio as a bypass risk. The target
contract requires adapter-level central authorization. This is a design requirement, not a claim that the existing
repository has already been changed or that bypasses have been eliminated.


13. Errors, audit, correlation and recovery
    Concern                                 Contract requirement                  Unresolved detail


---

                                              Distinguish validation, authentication,
                                              authorization, policy, conflict, transient
                                                                                             Canonical code catalogue and response
    Error taxonomy                            dependency, permanent dependency,
                                                                                             schema.
                                              integrity, timeout and unknown-outcome
                                              failures.
                                              Retry only classified retryable failures;
    Retryability                                                                             Retry budgets, backoff and jitter.
                                              preserve attempt history and idempotency.
                                              Reconcile remote state before repeating side
    Unknown external outcome                                                                 Destination-specific reconciliation protocol.
                                              effect.
                                              Record actor, action, target, version,
                                                                                             Audit schema, retention, access and tamper-
    Audit                                     decision, policy/evidence refs, time and
                                                                                             evidence mechanism.
                                              correlation.
                                              Propagate correlation/causation across
                                                                                             Header/field names and propagation
    Correlation                               command, workflow, task, job, attempt,
                                                                                             adapters.
                                              event, artifact and distribution operation.
                                              Document recovery owner, trigger, safe         Runbooks, RTO/RPO and operational
    Recovery
                                              replay boundary and verification evidence.     thresholds.
                                              Make poison messages visible, diagnosable
    Dead-letter                                                                              Thresholds and operator authorization.
                                              and recoverable under controlled action.


No RTO, RPO, timeout, retry count, lease duration, heartbeat interval, retention period or numeric threshold is fixed
by this pack. Such values require workload assumptions, local/cloud topology and explicit owner review.


14. Cross-package interface map
    Work package                  Owns / delivers                     Consumes / depends on              Freeze-critical interfaces
                                                                                                         Current system boundary,
                                  Baseline and preservation
    WP-0                                                              Existing repo/system facts         adapter inventory, risk
                                  evidence
                                                                                                         evidence.
                                  Canonical entities, IDs,
```text
                                                                      Data dictionary,                   Entity schemas, constraints,
    WP-1                          ownership, persistence and
                                                                      module/contract matrix             migrations, ownership registry.
```
                                  schema
                                                                                                         Command envelopes,
```text
                                  Workflow/job/attempt                WP-1 records; API/event
    WP-2                                                                                                 outbox/inbox, idempotency,
                                  durability and messaging            standard
```
                                                                                                         leases, recovery.
                                  Worker registry, trust,             WP-1 identity/scope; WP-2          Worker identity, credential and
    WP-3
```text
                                  credentials and capabilities        assignments                        assignment contract.
                                                                      WP-1 persistence; WP-2             ArtifactVersion, manifest,
```
                                  Artifact metadata, versioning,
    WP-4                                                              execution lineage; WP-3 worker     transfer, validation and
                                  transfer and integrity
                                                                      outputs                            quarantine schemas.
                                                                                                         Canonical vocabularies, exact-
```text
                                  Quality, rights, approval and       WP-1 identities/versions; WP-4
    WP-5                                                                                                 version bindings, policy and
                                  central authorization               artifact refs; policy/evidence
```
                                                                                                         decision contracts.
                                                                                                         End-to-end evidence, failure
                                  Integrated vertical slice,
    WP-6                                                              All prior WPs                      injection, replay safety and
                                  failure/recovery and acceptance
                                                                                                         release gates.


### 14.1 Shorts Studio bounded adapter
- Treat Shorts Studio as an existing specialist engine, not as the canonical Content OS state owner.
- The adapter accepts a versioned creation request with exact input references, policy context and output contract.
- The adapter returns structured result metadata and immutable artifact references; it does not directly mutate
       canonical content/approval/authorization/distribution state.
- Local rendering may execute on a local worker. If the worker is unavailable, local-only work remains pending
       safely.
- No adapter may upload or publish publicly without the distribution workflow and central authorization.


---

- Engine/version/configuration provenance must be recorded sufficiently to support lineage and reproducibility.


15. Module-to-contract traceability
    Module                                      Primary contract families                     Key cross-domain interfaces
                                                                                              Workspace scope to all domains; emergency
    Workspace & Control Center                  Policy/scope; owner controls; audit
                                                                                              pause and authorization visibility.
                                                ContentItem/Variant/Version; lifecycle        Creation requests, QA, approval, artifact
    Content Graph
                                                events                                        lineage and distribution references.
                                                                                              Research evidence and content source
    Knowledge Management                        Knowledge source/provenance
                                                                                              references.
                                                                                              Knowledge and content graph; provenance
    Research Intelligence                       Research record/evidence
                                                                                              and rights evidence references.
    Brand Intelligence                          Brand profile/configuration version           Creation, QA and policy context.
                                                                                              Workflow trigger and content graph
    Strategy & Planning                         Plan/calendar/objective
                                                                                              references.
                                                                                              Exact content/artifact versions; governance
    Content Quality Intelligence                QA evaluation/result/evidence
                                                                                              and approval prerequisites.
                                                                                              Workflow/job assignment and artifact
    Multiformat Creation Engine                 Creation command/result; engine adapter
                                                                                              outputs.
                                                Artifact/ArtifactVersion/manifest/transfer/   Creation workers, QA, distribution package
    Asset Management
                                                validation                                    and lineage.
                                                                                              All modules via commands/events; no
    Automation & Agent Orchestration            Workflow/task/job/attempt/worker/event
                                                                                              ownership of governance decisions.
                                                                                              Artifact versions, rights, QA, approval and
    Distribution Studio                         Package/operation/destination
                                                                                              central authorization.
                                                                                              Read committed events and outcomes; no
    Analytics & Learning                        Metric/observation/attribution
                                                                                              retroactive source-state writes.


This mapping follows the module-to-contract traceability approach. Exact Contract 01–12 names and part-level
numbering must be copied verbatim from the authoritative traceability matrix during the final freeze review; this
pack deliberately avoids inventing a replacement numbering scheme.


16. Reconciliation to known findings
    Finding                                     Contract impact                               Disposition in this pack
                                                                                              Separated explicitly; exact entity/field
    RCN-01                                      ContentItem vs ContentVariant
                                                                                              schema still to freeze.
                                                                                              Stable entity IDs and immutable version IDs
    RCN-02                                      Entity identity vs version identity
                                                                                              separated.
                                                                                              Canonical CF-20 values retained; no silent
    RCN-03                                      Rights vocabulary conflict
                                                                                              alias/migration.
                                                                                              Canonical CF-21 values retained; older two-
    RCN-04                                      Approval vocabulary conflict
                                                                                              value model marked incomplete.
                                                                                              Central authorization and execution-time
    RCN-05                                      Approval vs authorization
                                                                                              binding made explicit.
                                                                                              Four accepted QA outcomes; BLOCKED non-
    RCN-06                                      QA outcome and hard blockers
                                                                                              bypassable.
                                                                                              Durable attempt boundaries recorded;
    RCN-07                                      Job/attempt/lease/retry
                                                                                              numeric values open.
                                                                                              Identity/credential/capability boundary
    RCN-08                                      Worker trust/capability
                                                                                              recorded; detailed protocol open.
                                                                                              Version, manifest, transfer, validation,
    RCN-09                                      Artifact/manifest details                     quarantine and lineage obligations
                                                                                              recorded.
                                                                                              Contract families identified;
    RCN-10                                      Error/recovery/audit
                                                                                              schemas/runbooks/thresholds open.


---

                                                                                          Local-first/free-first; no provider or paid
RCN-11                                  No-paid-services constraint
                                                                                          activation selected.
                                                                                          Carry forward as complete in reconciliation
FZ-01 / FZ-02                           Source authority and accepted decisions
                                                                                          baseline.
                                                                                          Candidate content supplied here; item-by-
FZ-03–FZ-19                             Detailed domain/schema/interface closure
                                                                                          item owner freeze still required.
FZ-20                                   Formal owner contract freeze                      OPEN — no freeze inferred.
FZ-21                                   Implementation authorization                      NOT GRANTED.
                                                                                          Definitions and unresolved cardinality
X-01                                    Workflow/task/job state boundaries
                                                                                          separated.
X-02                                    ArtifactVersion/manifest detail                   Expanded into artifact contract section.
X-03                                    Transfer/validation/quarantine                    Expanded into artifact safety and records.
                                                                                          Distinct vocabularies and state dimensions
X-04                                    Governance labels
                                                                                          preserved.
                                                                                          Central authorization defined; emergency
X-05                                    Authorization/emergency pause
                                                                                          pause remains owner decision.
X-06                                    Worker trust/credential                           Boundary defined; detailed protocol open.
X-07                                    Job/task/workflow mapping                         Definitions separated; cardinality open.
                                                                                          Envelope requirements recorded; exact
X-08                                    Command/event envelope
                                                                                          schemas open.
                                                                                          Deletion, retention and legal hold remain
X-09                                    Artifact lifecycle/deletion/legal hold
                                                                                          explicit open items.
                                                                                          Acceptance evidence requirements
X-10                                    WP6 acceptance evidence
                                                                                          expanded in Section 18.
                                                                                          ODR-22 remains provisional grouping, not
X-11                                    ODR-22 provenance                                 treated as an independently owner-
                                                                                          approved source row.
                                                                                          Controlled status labels and authority
X-12                                    Status/authority language
                                                                                          statement included.


17. Open contract decisions and deferred values
ID                          Open item                            Why it cannot be assumed             Closure evidence required
                                                                                                      Owner-reviewed schema
                                                                 The standards define direction
                            Final field-level schemas for all                                         catalogue with field definitions,
OPEN-01                                                          and boundaries, but not every
                            canonical entities                                                        nullability, indexes and
                                                                 final field/constraint.
                                                                                                      invariants.
                                                                 Conceptual separation is
                            ContentItem/Variant/Version                                               ERD plus examples and
OPEN-02                                                          established; exact relationship
                            cardinalities                                                             migration/validation rules.
                                                                 rules need final schema.
                                                                 Definitions and instances must
                            Workflow/task/job cardinalities      remain distinct; exact               Workflow execution model and
OPEN-03
                            and completion semantics             fan-out/fan-in rules are not fully   state ownership table.
                                                                 established.
                                                                 No universal status enum; exact      State-machine catalogue with
                            Complete per-domain lifecycle
OPEN-04                                                          domain-specific states need          allowed/forbidden transitions
                            enums and transition matrices
```text
                                                                 explicit definitions.                and actors.
                            Exact API routes and                 Published examples are               OpenAPI/schema bundle and
```
OPEN-05
                            request/response schemas             illustrative, not frozen routes.     compatibility policy.
                                                                 Error classes are known; exact
                                                                                                      Error registry and consumer
OPEN-06                     Canonical error code catalogue       codes and retry classification
                                                                                                      behavior matrix.
                                                                 remain open.
                                                                 Durable pattern accepted;
                            Outbox/inbox schema and                                                   Transaction examples, duplicate
OPEN-07                                                          operational semantics need
                            deduplication rules                                                       delivery tests and replay policy.
                                                                 detail.
                                                                 Accepted short-lived scoped
                            Worker credential                                                         Threat model, credential
OPEN-08                                                          credential direction does not
                            issuance/rotation/revocation                                              lifecycle and revocation tests.
                                                                 select a protocol.


---

                                                                 Capability checks accepted;
                              Capability taxonomy and                                                Versioned capability registry
 OPEN-09                                                         catalogue and proof model
                              evidence                                                               and authorization mapping.
                                                                 open.
                                                                                                     Measured assumptions, owner-
                              Lease, timeout, retry and          Workload/topology assumptions
 OPEN-10                                                                                             selected values and boundary
                              heartbeat numeric values           not frozen.
                                                                                                     tests.
                                                                 Responsibilities are known;
                              Artifact manifest schema and                                           Manifest schema, transfer state
 OPEN-11                                                         provider and binary details
                              transfer protocol                                                      machine and checksum tests.
                                                                 deferred.
                                                                 No approved
                              Retention, deletion, legal hold,                                       Data lifecycle/security policy
 OPEN-12                                                         provider/operations policy
                              encryption and backup                                                  and owner decision.
                                                                 established.
                                                                                                     Owner-approved
                                                                 High-impact control with
                              Emergency pause scope and                                              activation/deactivation, scope,
 OPEN-13                                                         unresolved authority and in-
                              propagation                                                            propagation and recovery
                                                                 flight semantics.
                                                                                                     policy.
                              Approval expiry/revocation and     Vocabulary accepted; detailed       Role matrix and exact decision
 OPEN-14
                              reviewer roles                     role and timing rules open.         schema.
                                                                 Use-specific enforcement
                              Rights evidence sufficiency and                                        Rights policy matrix with
 OPEN-15                                                         accepted; taxonomy/evidence
                              use taxonomy                                                           examples and negative cases.
                                                                 threshold open.
                                                                                                     Per-destination
                              Distribution reconciliation        Unknown external outcomes
 OPEN-16                                                                                             query/reconciliation and
                              protocol                           must not be blindly retried.
                                                                                                     duplicate-side-effect tests.
                              Audit retention/access/tamper      Audit requirement exists;           Audit data contract and security
 OPEN-17
```text
                              evidence                           operational controls not fixed.     review.
                                                                 Acceptance oracle and               Versioned fixture pack, test run
```
                              WP6 test environment and
 OPEN-18                                                         environment controls need           manifest and independent QA
                              evidence bundle
```text
                                                                 explicit reproducibility.           report.
                              Provider/deployment/local-         CF-24 defers paid                   Owner-approved costed options;
```
 OPEN-19
                              cloud topology                     services/provider choice.           no activation by this document.
                                                                                                     Original source row or explicit
                              Final ODR-22 source                Current integrity review marks
 OPEN-20                                                                                             owner confirmation of the
                              provenance                         it provisional grouping.
                                                                                                     grouped disposition.


18. Testability and acceptance requirements
A contract is not ready merely because prose exists. Each frozen contract must have positive, negative, concurrency,
replay and recovery examples. The following are minimum acceptance scenarios for the domain/interface layer.
 Test ID                                  Scenario                                       Expected result / evidence
                                          Duplicate command delivered with same          No duplicate protected effect; same durable
 CT-01                                    idempotency key and same semantic              outcome/reference or documented
```text
                                          payload                                        idempotent response.
                                          Same idempotency key reused with a             Rejected or conflict according to frozen
```
 CT-02
                                          different semantic payload                     policy; no ambiguous execution.
                                                                                         CONFLICT; authoritative state unchanged
 CT-03                                    Stale expected_state_version command
                                                                                         by stale write.
                                                                                         Consumer deduplicates; no duplicate state
 CT-04                                    Event delivered twice to a consumer
                                                                                         effect.
                                          Outbox commit succeeds but publisher           Event remains durably pending and is
 CT-05
```text
                                          process stops before send                      eventually published after recovery.
                                          Consumer processes event but                   Redelivery does not duplicate consumer
```
 CT-06
                                          acknowledgment is lost                         effect.
                                                                                         New claim/protected execution denied;
 CT-07                                    Worker credential expired or revoked
                                                                                         audit record emitted.
 CT-08                                    Worker lacks required capability               Assignment rejected; no job execution.
                                                                                         Result rejected or quarantined; newer
 CT-09                                    Late result from superseded attempt
                                                                                         accepted attempt remains authoritative.
                                                                                         Artifact version fails validation and is
 CT-10                                    Artifact checksum mismatch
                                                                                         quarantined/blocked.


---

                                                                                               New ArtifactVersion created; prior version
    CT-11                                     Repair/regeneration of artifact
                                                                                               remains immutable.
                                              Rights state UNKNOWN or
    CT-12                                                                                      Protected use denied or held for review.
                                              PENDING_REVIEW for intended use
                                              Approval APPROVED but authorization              Execution denied; approval does not bypass
    CT-13
```text
                                              absent/expired/revoked                           central authorization.
                                              QA outcome BLOCKED with ordinary                 Protected downstream action remains
```
    CT-14
```text
                                              approval present                                 blocked.
                                              Emergency pause activated before                 Protected action denied according to owner-
```
    CT-15
```text
                                              execution                                        frozen pause scope.
                                              External publish response times out after        Operation becomes reconciliation-required;
```
    CT-16
```text
                                              possible side effect                             no blind duplicate publish.
                                              Event schema version is unsupported by           Controlled rejection/quarantine/dead-letter;
```
    CT-17
                                              consumer                                         no silent misinterpretation.
                                                                                               Projection rebuild is deterministic; external
    CT-18                                     Replay of historical event stream                side effects are suppressed unless
                                                                                               separately authorized.
                                              Cross-domain consumer attempts to write          Write is rejected; owner command
    CT-19
                                              another domain's canonical state                 boundary enforced.
                                                                                               Work remains safely pending; no silent
    CT-20                                     Local worker unavailable for local-only task
                                                                                               cloud substitution.


Each test must retain: test ID, contract/schema version, environment, fixture IDs, command/event IDs, correlation ID,
expected result, actual result, timestamps, logs/evidence references, pass/fail and reviewer. Independent QA must be
able to reproduce the result without relying on the implementer's verbal assertion.


19. Security, privacy and operational constraints
- Do not place credentials, access tokens or long-lived secrets in commands, events, logs, artifacts or job payloads.
- Use authenticated actor context; do not trust a caller-supplied actor ID as proof of identity.
- Apply least privilege to domain APIs, workers, storage access and administrative controls.
- Keep sensitive data out of broad event payloads; publish references and minimum necessary fields.
- Enforce workspace/brand/resource scope on every query and command.
- Treat imported source material, generated content and worker output as untrusted until validated.
- Maintain auditability for governance decisions, privileged actions, credential lifecycle and distribution
       operations.
- No paid service, cloud deployment or provider activation is authorized by this contract pack.


20. Freeze readiness checklist
    Gate                                      Required closure evidence                        Current disposition
                                              Authoritative source set and precedence
    G-01 Source authority                                                                      Baseline reconciled; retain provenance.
                                              confirmed
                                              Accepted decisions transcribed without           Carried forward; detailed representation
    G-02 Accepted ADR/CF baseline
                                              semantic drift                                   still reviewed.
                                              All canonical entities, fields, owners,
    G-03 Entity catalogue                                                                      Candidate included; field-level closure open.
                                              identity/version rules
                                              Per-domain states, transitions, actors,          Framework included; complete matrices
    G-04 State machines
```text
                                              guards and events                                open.
                                              Versioned schemas, compatibility and             Envelope requirements included; final
```
    G-05 API/event schemas
```text
                                              examples                                         schemas open.
                                              Outbox/inbox, idempotency, ordering,             Direction included; detailed operational
```
    G-06 Messaging semantics
```text
                                              replay and dead-letter                           rules open.
                                              Identity, credentials, capabilities, isolation   Boundary included; protocol and taxonomy
```
    G-07 Worker trust
                                              and revocation                                   open.


---

                                                 Version, manifest, transfer, validation,        Responsibilities included; schemas/provider
    G-08 Artifact contract
```text
                                                 quarantine and lineage                          details open.
                                                 QA, rights, approval, authorization and         Canonical vocabularies included; detailed
```
    G-09 Governance
```text
                                                 emergency pause                                 policy open.
                                                 Exact package/version/destination               Flow defined; destination adapters and
```
    G-10 Distribution
```text
                                                 authorization and reconciliation                reconciliation open.
                                                 Codes, audit schema, retention, recovery        Requirements included; schemas/values
```
    G-11 Errors/audit/recovery
```text
                                                 and runbooks                                    open.
                                                 Fixtures, oracles, failure injection and        Minimum scenarios included; executable
```
    G-12 Testability
                                                 independent QA                                  evidence pending.
                                                                                                 ODR-22 provisional grouping remains a
    G-13 ODR integrity                           All owner decisions source-traceable
                                                                                                 provenance caveat.
                                                 Explicit owner disposition on all open items
    G-14 Formal owner freeze                                                                     OPEN — not frozen.
                                                 and pack version
                                                 Separate explicit scope, repo baseline, agent
    G-15 Implementation authorization                                                            NOT GRANTED.
                                                 permissions and stop conditions


21. Explicit non-authorizations
Nothing in this document authorizes any of the following:

- Repository edits, code generation into the project, schema migrations, database changes or test execution against
       the project.
- Running Qoder, OpenCode, Kilo or another coding/QA agent on the repository.
- Reset, revert, stash, clean, delete, overwrite, rename, broad stage, commit, push, branch or remote changes.
- Cloud deployment, paid service activation, provider account creation or spend.
- Production content generation, external upload, public publishing or automatic publishing.
- Treating a design candidate, checklist, accepted ADR or accepted CF as blanket implementation authorization.
Implementation may begin only after (1) the detailed contract is formally frozen by the owner, (2) remaining owner-
reserved decisions are explicitly dispositioned, and (3) a separate implementation authorization names the permitted
work packages, repository baseline, tools/agents, allowed commands, test boundaries, stop conditions and rollback
constraints.


22. Owner review and sign-off record
    Review item                                  Owner disposition                               Notes / evidence
                                                                                                 Confirm boundaries and canonical owner
    Domain/entity ownership catalogue            PENDING
                                                                                                 per entity.
                                                                                                 Confirm ContentItem, ContentVariant and
    Content identity/version/cardinality model   PENDING
                                                                                                 ContentVersion relationships.
                                                                                                 Confirm cardinalities, run completion and
    Workflow/task/job/attempt model              PENDING
                                                                                                 retry semantics.
                                                                                                 Confirm domain-specific states and
    Lifecycle/state machine catalogue            PENDING
                                                                                                 transition guards.
                                                                                                 Confirm required fields, schemas and
    Command/query/event envelope                 PENDING
                                                                                                 compatibility rules.
                                                                                                 Confirm delivery, deduplication and replay
    Outbox/inbox/idempotency/replay              PENDING
                                                                                                 behavior.
                                                                                                 Confirm protocol, taxonomy and
    Worker trust/capability/credential           PENDING
                                                                                                 revocation.
    Artifact/manifest/transfer/validation        PENDING                                         Confirm schemas and data lifecycle policy.
                                                                                                 Confirm vocabularies, evidence and exact
    Quality/rights/approval/authorization        PENDING
                                                                                                 binding rules.
                                                                                                 Explicitly decide scope, authority,
    Emergency pause                              PENDING
                                                                                                 propagation and in-flight behavior.


---

                                                                                         Confirm per-destination unknown-outcome
 Distribution reconciliation               PENDING
                                                                                         recovery.
                                                                                         Confirm codes, retention and operational
 Error/audit/recovery                      PENDING
                                                                                         thresholds.
                                                                                         Confirm source row or explicitly accept
 ODR-22 provenance                         PENDING
                                                                                         provisional grouping.
                                                                                         Requires explicit owner approval of a
 Formal contract freeze                    NOT GRANTED
                                                                                         specific version.
 Implementation authorization              NOT GRANTED                                   Separate authorization required.


Owner decision: ______________________________    Date: __________________

Frozen document/version (if approved): __________________________________________

Explicit exclusions / conditions: __________________________________________________


23. Recommended next sequence
28. Complete a source-to-field reconciliation pass against the full canonical data dictionary, API/Event standard,
    lifecycle standard and module-to-contract matrix; record exact source section references for each frozen field and
    rule.
29. Produce the field-level schema and ERD appendix, including cardinality diagrams and domain ownership registry.
30. Produce the complete state-machine catalogue with transition tables and event examples for each state-owning
    domain.
31. Produce the versioned API/event schema bundle and compatibility/error catalogue; keep illustrative paths clearly
    marked until approved.
32. Close worker, artifact, governance, emergency-pause and distribution-reconciliation details with explicit owner
    dispositions.
33. Run a formal owner freeze review. Only after that, prepare the separate implementation authorization package.


## Appendix A — Source basis and authority notes
This pack is based on the identified NEXTDECODE project source set and reconciliation findings, including: Artifact 08
Implementation Reference / Accepted Contract Decisions 1.0; Artifact 08 Consolidated Owner Decision Record /
Contract Freeze Closure 1.0; Artifact 08 Contract Reconciliation & Freeze Candidate 1.1; Canonical Data Dictionary &
Entity Ownership Registry 1.0; API & Event Contract Standard 1.0; Unified Lifecycle & State Transition Standard 1.0;
Module-to-Contract Traceability Matrix 1.0; ODR-22 Source Reconciliation / Decision Register Integrity 0.1; and Cross-
Document Consistency Gap Review 0.1.

Source authority note: the Artifact 08 v1.1 reconciliation candidate supplements, but does not supersede, the accepted
v1.0 owner decision/reference records. The owner decision record states that detailed contract freeze remains
pending and implementation authorization has not been granted.

ODR-22 note: the integrity review found no independently traceable accepted owner decision row with that exact ID
and wording in the inspected records. It remains a provisional grouping of supported constraints and must not be
represented as a verbatim owner-approved ODR entry.


## Appendix B — Glossary
 Term                                                          Meaning
                                                               The authoritative domain record representing a real product
 Canonical entity
                                                               concept.
 Entity identity                                               Stable identifier for the entity across its lifetime.


---

                                                             Immutable identifier for one version/snapshot of an entity or
Version identity
                                                             artifact.
                                                             Domain boundary authorized to commit the canonical state
Aggregate / state owner
                                                             transition.
Command                                                      A request to perform a state-changing action.
Query                                                        A read request that does not itself mutate canonical state.
Event                                                        A durable record of a fact that has already been committed.
                                                             Durable record of an event to publish, committed with the source
Outbox
                                                             state change.
Inbox                                                        Durable consumer receipt/deduplication record.
                                                             Property that repeated equivalent requests do not create duplicate
Idempotency
                                                             effects.
ArtifactVersion                                              Immutable version of a binary or generated asset.
                                                             Central decision permitting a precisely bound action under current
Authorization
                                                             policy.
                                                             Process of resolving uncertain state/outcome against authoritative
Reconciliation
                                                             evidence.
