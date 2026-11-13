# NEXTDECODE Artifact 08 --- Implementation Reference: Accepted Contract Decisions

**Document ID:**
`NEXTDECODE_Artifact_08_Implementation_Reference_Accepted_Contract_Decisions_1.0.md`\
**Version:** 1.0\
**Date:** 31 October 2026\
**Purpose:** Preserve Artifact 08 owner decisions for use during future
implementation and agent handoff.

------------------------------------------------------------------------

## 1. Status and authority

This is an implementation reference and decision-reconciliation aid. It
is **not an implementation authorization**. It does not authorize
repository changes, Git operations, agent execution, code/configuration
changes, dependency installation, infrastructure provisioning,
deployment, paid-service activation, production generation, uploads or
publishing.

The detailed Artifact 08 contract freeze remains subject to formal
consolidation and owner review. Artifact 09 handoff preconditions
continue to apply.

Decision record: - **CF-01--CF-15:** Explicitly accepted by the owner. -
**CF-16--CF-21:** Accepted under the owner's standing delegation for
routine recommendations. - **CF-22:** Explicit owner decision --- Option
A, centralized authorization. - **CF-23:** Accepted under standing
delegation. - **CF-24:** No-paid-services constraint explicitly
accepted; operational parameters and provider selections remain
deferred.

Acceptance records agreed contract direction. It does not prove
implementation, testing or independent verification.

## 2. Project-wide invariants

1.  Preserve existing NEXTDECODE Content OS architecture, naming,
    artifact sequence and terminology.
2.  Preserve accepted P0 ADR-001 through ADR-010.
3.  Cloud control plane remains the intended future authority for shared
    workflow state; local workers handle local-only and heavy production
    workloads.
4.  Existing Shorts Studio remains a specialized Python/FFmpeg engine
    behind a bounded adapter. Do not wholesale replace it.
5.  Domain ownership does not require separate microservices. A modular
    application remains acceptable.
6.  Existing agent ownership remains: **Qoder --- Phase 11 engineering;
    OpenCode --- Phase 10 engineering/closure; Kilo --- independent
    read-only QA.**
7.  Human approval remains required before publishing. Automatic
    publishing remains disabled pending separate owner-approved policy.
8.  Unknown or uncertain security, rights, authorization and integrity
    states fail closed for protected actions.
9.  Preserve local work in progress. No destructive cleanup, reset,
    revert, stash, broad staging, overwrite, commit or push without
    explicit authorization.
10. Routine decisions may follow accepted recommendations and
    conservative defaults. Ask the owner only for genuinely critical
    decisions.

## 3. Accepted contract decisions

### CF-01 --- Canonical Entity Glossary

-   `ContentItem` is the shared editorial identity, independent of
    output format.
-   `ContentVariant` is a format/platform/language/treatment derivative.
-   Broader OS entities remain owned by their respective domain
    contracts.
-   This resolves the conflict between the Canonical Data Dictionary and
    Canonical Contracts Pack. Do not reopen without a superseding owner
    decision.

### CF-02 --- Entity Relationships and Ownership

-   One authoritative owner per canonical entity.
-   Typed canonical IDs for cross-domain references.
-   No competing canonical identities.
-   Relationships do not imply access, permission, approval or
    authorization.
-   Retain the existing 12-contract ownership structure; no new service
    boundaries are implied.

### CF-03 --- Required Fields and Nullability

-   Immutable UUIDv7 canonical IDs.
-   Shared record envelope includes schema version, creation metadata
    and applicable workspace scope.
-   Mutable records use update metadata and record versioning.
-   Entity owners define required/optional fields.
-   Null, empty and unknown are distinct; missing business-critical
    values are not inferred.
-   Unknown rights, approval or authorization never means permission.
-   Incomplete drafts cannot pass downstream gates until required
    information exists.

### CF-04 --- ID and Versioning Rules

-   UUIDv7 is canonical.
-   Entity identity, entity version, schema version, artifact version
    and execution attempt are distinct.
-   Mutable records use concurrency-safe versioning; stale updates are
    rejected or reconciled.
-   Artifact versions are immutable; changed bytes create a new version
    or identity.
-   Reviews and approvals bind to exact versions.
-   Idempotency keys and event/message IDs have separate identities and
    scopes.

### CF-05 --- Lifecycle and State Ownership

-   Each entity lifecycle has one authoritative owner.
-   Content, workflow, job execution, review, approval, authorization
    and distribution lifecycles remain separate.
-   Transitions are explicit, validated, attributable and auditable.
-   Invalid or unauthorized transitions are rejected.
-   Read models are not authoritative.
-   Quality, review, approval, authorization, execution and distribution
    are not interchangeable.

### CF-06 --- Relationship Integrity and Deletion Rules

-   Typed canonical references and workspace boundaries are enforced.
-   Cross-workspace relationships require explicit authorization.
-   Archival, logical deletion and physical deletion are distinct.
-   Deletion is dependency-aware and policy-controlled.
-   Historical lineage, approval evidence and required audit records are
    preserved.
-   Local deletion does not imply external-platform deletion.

### CF-07 --- Audit, Provenance and Traceability

-   Governed actions produce attributable audit records.
-   Provenance is preserved across domains.
-   Exact-version lineage is maintained from research through
    publication.
-   Forward and backward traceability are supported.
-   Ordinary operations do not silently rewrite audit history.
-   Sensitive credentials and unnecessary personal data are excluded
    from logs.
-   Retention follows central governance policy.

### CF-08 --- Job and Workflow Contract Boundaries

-   Workflow Definition, Workflow Run, Workflow Task, Job, Job Attempt,
    Queue Message and Event are distinct.
-   Each has clear ownership and canonical identity.
-   Running workflows remain bound to the workflow version they started
    with.
-   Standalone jobs require explicit operational purpose and owner.
-   At-least-once delivery is assumed; idempotency and deduplication
    protect logical effects.
-   Workers execute assigned jobs; they do not become global
    orchestrators.

### CF-09 --- Job State Transitions and Completion

-   Job states and transitions are explicit and validated.
-   Terminal outcomes preserve attempt history.
-   Success requires accepted, attributable completion evidence.
-   Failure classes determine retry eligibility.
-   Cancellation and recovery preserve actual external side-effect
    outcomes.
-   Duplicate/conflicting completion messages are handled safely.
-   Workflow completion is distinct from job completion.

### CF-10 --- Lease, Retry and Idempotency

-   Bounded leases use fencing protection; one authoritative active
    lease per job.
-   Each retry creates a new attempt identity; ordinary retries retain
    the logical job ID.
-   Idempotency records are durable and scoped.
-   Reusing a key with a different payload is a conflict.
-   Ambiguous external side effects are reconciled before retry.
-   Stale workers cannot commit after lease supersession.
-   Numerical lease/retry values remain deferred to CF-24.

### CF-11 --- Event, Outbox and Inbox

-   Domain Events, Commands, Outbox Messages and Inbox Receipts are
    distinct.
-   Domain changes and corresponding outbox records commit
    transactionally.
-   Consumers use durable deduplication.
-   Ordering is scoped, not assumed globally.
-   Event schema validation and compatibility are enforced.
-   Delivery failure and reconciliation are recoverable.
-   Events do not grant authorization or replace domain ownership.

### CF-12 --- Workflow Dependencies, Scheduling and Orchestration

-   Orchestration, scheduling, queue delivery, worker execution and
    domain ownership remain separate.
-   Task dependencies are explicit and validated.
-   Cyclic dependencies are rejected under the initial contract unless a
    future contract supports bounded loops.
-   Only eligible jobs are scheduled.
-   Local-only jobs wait safely when the required local worker is
    unavailable.
-   Failure propagation, cancellation and compensation are explicit.
-   Scheduling never grants authorization.

### CF-13 --- Worker Identity, Registration and Trust

-   Canonical worker identity is independent of hostname or machine
    name.
-   Registration and trust have explicit lifecycles.
-   Declared, verified, available and authorized capabilities are
    distinct.
-   Credentials are unique, scoped, short-lived and revocable.
-   Assignment and completion validate identity and authorization.
-   Local and remote workers follow the same trust boundary.
-   Worker trust changes are auditable.

### CF-14 --- Worker Capabilities, Isolation and Resources

-   Capabilities are versioned and independently verified.
-   Capability declarations do not grant permissions.
-   Jobs execute within controlled isolation boundaries.
-   Filesystem, network, credentials and artifact access are scoped.
-   Resource requirements/limits are defined by job class.
-   Local and remote workers share execution governance.
-   Administrative, production, QA and publishing permissions remain
    separated.
-   Numerical resource limits remain deferred.

### CF-15 --- Artifact Registration, Storage and Transfer

-   Artifacts have canonical identity and immutable versions.
-   Relational metadata is authoritative; binary storage is behind an
    abstraction.
-   Asset and Artifact are distinct.
-   Checksums verify integrity.
-   Transfers are controlled, attributable and verifiable.
-   Centralized access and rights enforcement apply.
-   Historical artifact bytes are not overwritten in place.
-   Provider-specific storage choices remain deferred.

### CF-16 --- Artifact Manifest, Provenance and Lineage

-   Manifests have canonical identity and immutable versions.
-   Components reference exact canonical artifact versions.
-   Composition and dependencies are explicit.
-   Integrity checks and production provenance are recorded.
-   Changed inputs/outputs create traceable new lineage.
-   Review, approval and distribution bind to exact manifest/artifact
    versions.
-   Manifest completeness is distinct from quality, rights and approval.

### CF-17 --- Artifact Access, Retention and Lifecycle

-   Artifact authorization is centralized and scope-aware.
-   Read, write, transfer, export, share and delete are distinct
    permissions.
-   Rights restrictions apply even when an artifact is accessible.
-   Artifact lifecycle and retention ownership are explicit.
-   Deletion is dependency-aware; recovery is controlled.
-   Local/cloud access boundaries are preserved.
-   Required audit and production lineage are retained.
-   Exact retention durations remain deferred.

### CF-18 --- Artifact Integrity, Validation and Quarantine

-   Validation is type-aware and versioned.
-   Checksums and structural checks are recorded.
-   Validation and availability are separate states.
-   Quarantine blocks normal downstream use.
-   Revalidation preserves historical results.
-   Repairs create new artifact versions.
-   Publishing rejects artifacts without required verified status.
-   Technical validation does not establish factual accuracy, rights or
    approval.

### CF-19 --- Quality Assessment and QA Results

-   One shared QA result contract across studios.
-   QA runs are immutable and bound to exact target versions.
-   Canonical outcomes: `PASS`, `PASS_WITH_WARNINGS`, `NEEDS_REVIEW`,
    `BLOCKED`.
-   Individual checks are evidence-backed.
-   Hard blockers are centrally enforced and cannot be bypassed by
    ordinary approval.
-   Studio-specific checks map to the shared contract.
-   Scores are supplementary and cannot override blockers.
-   QA remains separate from rights, approval and authorization.
-   Acceptance does not claim Phase 11 blockers are fixed or
    independently verified.

### CF-20 --- Rights Assessment and Usage Permission

-   Contract 07 owns the canonical rights assessment framework.
-   Rights decisions are evidence-backed and use-specific.
-   Rights states: `UNKNOWN`, `PENDING_REVIEW`, `CLEARED`, `RESTRICTED`,
    `EXPIRED`, `REVOKED`, `DENIED`.
-   Permission is evaluated against asset, intended use, platform,
    geography, time, commercial context and modification/attribution
    conditions.
-   Unknown rights fail closed for protected uses.
-   Rights restrictions propagate through artifact lineage.
-   Studios and distribution adapters cannot override restrictions.
-   Ambiguous/high-risk cases may require human legal review.
-   This is not blanket rights clearance or legal advice.

### CF-21 --- Approval and Human Decision

-   Central Governance / Contract 07 owns the approval framework.
-   Review packages are immutable snapshots.
-   Human decisions are attributable and bound to exact versions and
    scope.
-   Decisions: `APPROVED`, `REJECTED`, `CHANGES_REQUESTED`, `EXPIRED`,
    `REVOKED`.
-   QA blockers cannot be bypassed by ordinary approval.
-   Changed content, rights or destination may require re-review.
-   Approval is distinct from authorization and execution.
-   Human approval before publishing remains required; automatic
    publishing remains disabled.

### CF-22 --- Authorization and Policy Enforcement

**Explicit owner decision: Option A --- Centralized authorization.** -
One central governance authority makes authorization decisions. - APIs,
studios, workers and distribution adapters enforce those decisions. -
Default-deny and fail-closed behavior apply. - Least privilege, exact
action/resource/version/destination binding, expiry and revocation are
required. - Approval and authorization remain separate. - Agent
delegation cannot expand authority. - No domain-local competing
authorization authority.

### CF-23 --- Error Contracts, Failure Handling and Recovery

-   Shared structured error contract and stable taxonomy.
-   Severity and retryability are independent.
-   Retryability is explicit and governed by operation contract.
-   Failure and attempt history are durable.
-   Ambiguous external actions require reconciliation.
-   Recovery has a defined domain owner.
-   Dependency isolation and bounded retries are supported.
-   Policy and authorization denials cannot be bypassed through retry.
-   Diagnostic details are access-controlled.

### CF-24 --- Operational Selections and Constraints

**Explicit owner constraint: No paid services are authorized.** -
Development remains local-first and free-first. - Architecture remains
hybrid-ready; this does not authorize cloud deployment. - No paid
subscriptions, usage-based API spending, paid AI/model providers, paid
storage/databases, paid automation services or charge-generating
infrastructure without separate explicit owner approval. - No automatic
upgrades, paid trials that can convert to billing, or silent billing
exposure. - Prefer existing local resources and free tools. - Do not use
a free tier if it can silently generate charges. - Provider selection
and production infrastructure remain deferred.

## 4. Accepted P0 architecture baseline

  -----------------------------------------------------------------------
  ADR                                 Accepted direction
  ----------------------------------- -----------------------------------
  ADR-001                             UUIDv7 canonical IDs

  ADR-002                             PostgreSQL-compatible relational DB
                                      as authoritative shared-state store

  ADR-003                             DB-backed durable queue with
                                      transactional outbox/inbox
                                      initially

  ADR-004                             Versioned HTTP/JSON contracts with
                                      schema validation

  ADR-005                             Unique worker identity, scoped
                                      short-lived credentials and
                                      capability authorization

  ADR-006                             Relational artifact metadata;
                                      binaries behind object-storage
                                      abstraction

  ADR-007                             Centralized authorization;
                                      publishing adapters cannot bypass;
                                      automatic publishing disabled
                                      pending separate policy

  ADR-008                             QA outcomes PASS,
                                      PASS_WITH_WARNINGS, NEEDS_REVIEW,
                                      BLOCKED; ordinary approval cannot
                                      bypass hard blockers

  ADR-009                             Evidence-backed rights states and
                                      use-specific enforcement

  ADR-010                             Separate lifecycle state machines
                                      for content, workflow, execution,
                                      review, approval, authorization and
                                      distribution
  -----------------------------------------------------------------------

These are accepted architecture directions, not proof of implementation
or provider selection.

## 5. Deferred selections --- do not guess or prematurely freeze

-   Cloud provider and region.
-   Production database provider/deployment.
-   Queue implementation/provider beyond the accepted initial DB-backed
    direction.
-   Object-storage provider, region, replication and encryption
    configuration.
-   Token issuer, token format and production credential configuration.
-   Lease duration, renewal interval, retry count, backoff, jitter and
    dead-letter parameters.
-   Resource quotas, concurrency limits, scheduling weights and fairness
    algorithm.
-   Retention durations and legal-hold implementation.
-   Monitoring, tracing, logging and alerting provider.
-   Backup schedule, recovery testing, RPO and RTO.
-   Production workload placement and capacity.
-   Any budget or spending authority.

A recommended default is not approval for a paid provider or deployment.

## 6. Implementation-time execution boundaries

Before implementation or agent execution, verify: 1. Explicit owner
authorization for the specific work package. 2. Exact repository
identity and current baseline. 3. Current local and remote Git state,
preserving all local work in progress. 4. Contract decisions reconciled
into the detailed contract freeze. 5. Bounded scope, dependencies, file
ownership and acceptance criteria. 6. Environment, secrets, data safety
and security boundaries. 7. Explicit permissions for Git, code, tests,
dependencies, environment, cloud or external side effects. 8. Review and
evidence plan.

Existing agent ownership: - **Qoder:** Phase 11 engineering owner. -
**OpenCode:** Phase 10 engineering/closure owner. - **Kilo:**
independent read-only QA.

No agent may self-expand scope, self-approve work or perform an external
side effect without authorization.

Prohibited without separate explicit authorization: - Git reset, clean,
revert, stash, broad staging, commit or push. - Code, configuration,
test or dependency changes. - Environment or credential changes. - Cloud
resource provisioning or deployment. - Paid service activation or
spending. - Production generation, upload or publishing. - Destructive
deletion or migration.

## 7. Existing P0 execution scope

The accepted P0-A direction remains **Durable Content Workflow
Foundation**:

-   WP-0 --- Current system baseline and preservation assessment.
-   WP-1 --- Canonical domain and persistence foundation.
-   WP-2 --- Durable job and workflow execution.
-   WP-3 --- Worker registry and contract boundary.
-   WP-4 --- Artifact registration and transfer.
-   WP-5 --- Governance, quality and rights foundation.
-   WP-6 --- Vertical-slice integration and recovery validation.

P0-A exclusions remain: full dashboard, full research/trend
radar/strategy, complete brand intelligence, production-grade autonomous
fleet, automatic public publishing, live platform uploads, production
cloud deployment, wholesale Shorts Studio replacement, cloud rendering
of every workload, teams/billing/SaaS, advanced analytics, vector DB,
and paid services without separate approval.

## 8. Evidence and status discipline

Use these labels accurately: - **DOCUMENT-DEFINED:** Specified in a
document. - **OWNER-ACCEPTED:** Explicitly accepted by the owner or
under standing delegation. - **REPORT-BACKED:** Supported by an existing
report. - **VERIFIED:** Independently confirmed through current evidence
or tests. - **RECOMMENDATION:** Suggested but not accepted. -
**DEFERRED:** Intentionally left open. - **NOT VERIFIED:** Evidence is
absent or insufficient.

A contract acceptance is not an implementation result. Historical test
reports do not prove the current repository passes. Do not add
historical test counts unless overlap is understood.

## 9. Relationship to existing project artifacts

This reference supplements and does not replace: - Artifact 06 --- P0
Implementation Readiness & Risk Register. - Artifact 07 --- P0
Foundation Execution Plan & Acceptance Framework. - Artifact 08 --- P0
Detailed Contract Freeze & Open Decisions Closure. - Artifact 09 --- P0
Coding Agent Handoff Specification. - Canonical Data Dictionary & Entity
Ownership Registry. - Canonical Contracts Pack 1.0. - Accepted P0
Architecture Decision Baseline.

If a conflict is found, do not silently overwrite an existing artifact.
Identify the conflict and reconcile through the existing project
sequence.

## 10. Implementation reminder

Use this file as the accepted decision reference when preparing
implementation tasks, reviewing agent output and checking acceptance
evidence.

It is not a substitute for detailed contracts, repository baseline,
implementation authorization or Artifact 09 handoff gates.

**No paid services. No surprise billing. No unauthorized repository or
production side effects. Preserve the existing project path and local
work in progress.**
