NEXTDECODE CONTENT OS

# P0 Batch 05
WP-1 Domain & Persistence Design Candidate

Design working pack • 01 November 2026

Purpose: provide a structured, reviewable WP-1 design candidate for the canonical domain and persistence foundation. This is not a frozen schema, migration script, implementation order or authorization to modify the repository.

## 1. How to use this pack

This pack turns the accepted architecture direction into a set of design questions, entity boundaries, persistence responsibilities and acceptance checks. It intentionally avoids pretending that missing source specifications have been verified.

| Label | Meaning | Permitted use |
| --- | --- | --- |
| ACCEPTED DIRECTION | Owner-accepted ADR/CF decision outcome already recorded | Treat as governing direction; do not reopen casually. |
| DESIGN CANDIDATE | A proposed structure consistent with known direction | Review and reconcile against authoritative source documents. |
| SOURCE REQUIRED | The governing detail is not present or verified in the current source set | Do not finalize field names, enums, constraints or behavior. |
| OWNER DECISION | A genuinely owner-reserved choice | Escalate only when the decision is necessary to proceed. |
| NOT AUTHORIZED | Execution or mutation not approved | Do not implement, migrate, deploy or run agents. |

Design principle: preserve the accepted intent while keeping unverified detail visibly provisional.

## 2. WP-1 scope and boundary

| In scope for WP-1 | Out of scope for WP-1 |
| --- | --- |
| Canonical domain entities and identity policy | Full workflow/job orchestration implementation (WP-2) |
| Relational persistence foundation and constraints | Worker registration and credential lifecycle implementation (WP-3) |
| Ownership and typed relationship model | Binary transfer/storage implementation (WP-4) |
| Versioning, audit references and idempotency foundations | Complete governance/policy engine implementation (WP-5) |
| Migration strategy, compatibility and recovery design | End-to-end integrated vertical slice (WP-6) |
| Data dictionary and schema acceptance criteria | Production deployment, paid provider activation or publishing |

WP-1 must provide stable foundations to WP-2 through WP-6 without absorbing their responsibilities.

## 3. Governing design constraints

- Canonical IDs are immutable UUIDv7; identity and version are separate concepts.

- Each canonical entity has one authoritative owner; cross-domain references are typed and do not imply ownership or permission.

- ContentItem is the shared editorial identity; ContentVariant represents a format/platform/language/treatment derivative.

- Content, workflow, execution, review, approval, authorization and distribution state machines remain separate.

- Centralized authorization is authoritative. Approval is not authorization, and authorization is not proof of execution success.

- Unknown, missing or ambiguous rights/approval/authorization never grant permission for protected actions.

- At-least-once job delivery requires idempotency and traceable attempts; WP-1 supplies persistence primitives, WP-2 enforces execution semantics.

- Artifact metadata is relational; binary storage is behind an abstraction and is not hardwired to a provider.

- Automatic public publishing remains disabled pending separate policy approval.

- Local-first/free-first remains the initial constraint; no paid service or provider is selected by this design.

## 4. Candidate domain map

The following is a conceptual map, not a final physical schema. Entity names and boundaries must be checked against the authoritative data dictionary and CF source pack.

| Domain concept | Candidate responsibility | Ownership / boundary note | Source status |
| --- | --- | --- | --- |
| Workspace | Top-level operating context and configuration | Owns workspace-scoped configuration, not every domain record | SOURCE REQUIRED |
| Brand | Brand identity, voice and governed brand settings | Separate from workspace and content identity | SOURCE REQUIRED |
| ContentItem | Canonical editorial idea/story identity | Shared identity across derivative variants | ACCEPTED DIRECTION; details SOURCE REQUIRED |
| ContentVariant | Format/platform/language/treatment-specific derivative | References ContentItem; does not replace it | ACCEPTED DIRECTION; details SOURCE REQUIRED |
| ResearchRecord | Research findings and supporting source references | Must preserve provenance and source attribution | SOURCE REQUIRED |
| Claim / Evidence | Claim-level support and evidence linkage | No unsupported claim is upgraded by a status label | SOURCE REQUIRED |
| Asset | Registered binary or external asset reference plus metadata | Binary bytes remain behind storage abstraction | ACCEPTED DIRECTION; details SOURCE REQUIRED |
| Review | Review findings tied to exact version | Review is not approval or authorization | SOURCE REQUIRED |
| Approval | Human approval tied to exact artifact/content version and purpose | Does not itself authorize external execution | ACCEPTED DIRECTION; details SOURCE REQUIRED |
| AuthorizationDecision | Central policy decision and scope | Single authoritative policy boundary | ACCEPTED DIRECTION; details SOURCE REQUIRED |
| Job / ExecutionAttempt | Durable work identity and attempt history | WP-2 owns execution behavior; WP-1 supplies persistence foundation | SOURCE REQUIRED |
| Worker | Registered execution principal and trust metadata | WP-3 owns lifecycle and credential behavior | SOURCE REQUIRED |
| DistributionRecord | External distribution intent and confirmed outcome | Publishing adapter cannot bypass central gates | SOURCE REQUIRED |

## 5. Candidate persistence principles

| Concern | Candidate rule | Review questions |
| --- | --- | --- |
| Primary key | UUIDv7 immutable canonical identifier | Are IDs generated once and preserved across retries/imports? |
| Versioning | Explicit version/revision separate from canonical ID | Which entities are versioned, and what creates a new version? |
| Ownership | Explicit owner type and owner ID or typed FK where appropriate | Can ownership be enforced without polymorphic ambiguity? |
| Relationships | Typed references with declared cardinality and deletion behavior | Does every relation state whether it is owning, referencing or evidentiary? |
| Timestamps | UTC instants plus actor/source metadata where required | Which timestamps are event time, ingestion time and update time? |
| Audit | Append-only or tamper-evident audit trail for material actions | What is retained, who can read it, and how is correlation preserved? |
| Idempotency | Scoped idempotency key with request/result association | What uniqueness scope and retention window are required? |
| Concurrency | Explicit optimistic concurrency/version check where concurrent edits occur | Which updates must reject stale versions? |
| Soft deletion / tombstone | Explicit lifecycle state; no implicit destructive cascade | How do legal hold and retention constraints interact? |
| Indexes | Indexes derived from query and uniqueness requirements | Which query patterns are actually required by the WPs? |
| Transactions | Atomic persistence for invariants within one DB transaction | Which cross-domain actions need outbox/event patterns? |
| Portability | PostgreSQL-compatible relational design; avoid provider lock-in | Are extensions or vendor-specific features avoidable at P0? |

## 6. Candidate logical table families

The names below are illustrative grouping labels, not approved table names. The authoritative data dictionary may require different names or a different decomposition.

| Family | Possible records | Design questions before physical schema |
| --- | --- | --- |
| Workspace & brand | workspace, brand, workspace_brand | Can a brand be shared across workspaces later without changing canonical identity? |
| Content | content_item, content_variant, content_version | Which fields belong to the stable item versus a versioned variant? |
| Research & evidence | research_record, source_reference, claim, evidence_link | How are source snapshots, URLs, retrieval dates and claim support represented? |
| Assets | asset_record, asset_version, asset_derivative | How are content hashes, MIME type, size, storage key and provenance captured? |
| Review & approval | review_record, review_finding, approval_record | How are exact version, reviewer, purpose, decision and expiry represented? |
| Authorization & audit | authorization_decision, audit_event | How are policy version, principal, scope, reason and correlation recorded? |
| Execution foundation | job_record, execution_attempt, idempotency_record | Which fields are WP-1 persistence primitives versus WP-2 orchestration behavior? |
| Worker registry | worker_record, worker_capability_snapshot | Keep detailed trust lifecycle and credentials in WP-3; avoid duplicating policy. |
| Distribution | distribution_intent, distribution_attempt, external_outcome | How are intent, attempt, external receipt and confirmed outcome distinguished? |

## 7. State separation: persistence model

Do not create one universal status column for a content object. The architecture requires independent state dimensions with explicit owners and transition rules.

| State machine | What it describes | Persistence design requirement | Owner WP |
| --- | --- | --- | --- |
| Content lifecycle | Editorial maturity of a content item/variant | Version-bound content state and transition audit | WP-1 + WP-5 |
| Workflow lifecycle | Progress through orchestration stages | Workflow instance/state history, not content status reuse | WP-2 |
| Execution lifecycle | Queued/running/retrying/finished/unknown execution | Attempt-level records and idempotency linkage | WP-2 |
| Review lifecycle | Review findings and QA disposition | Review record bound to exact version and evidence | WP-5 |
| Approval lifecycle | Human acceptance of exact version for purpose | Attributable approval record; stale version invalidation | WP-5 |
| Authorization lifecycle | Policy grant/deny for scoped action | Central decision record, scope and policy version | WP-5 |
| Distribution lifecycle | Intent, attempt and external outcome | Separate intent/attempt/confirmed outcome records | WP-5 + WP-6 |

The exact enum values and legal transitions are SOURCE REQUIRED until the governing lifecycle contract is inspected.

## 8. Integrity and safety constraints

| Constraint | Candidate enforcement location | Minimum negative test |
| --- | --- | --- |
| Canonical ID immutable | DB permissions/constraints + application domain layer | Attempt to mutate an existing canonical ID; operation rejected. |
| Single authoritative owner | Foreign keys / ownership constraints / service boundary | Create competing owner for same canonical entity; rejected. |
| Typed cross-domain references | Typed FK or validated reference table | Reference a nonexistent or wrong-type target; rejected. |
| Exact-version approval | Approval references immutable version ID/hash | Change content after approval; prior approval cannot authorize new version. |
| Fail-closed rights | Central policy gate and evidence validation | Rights unknown/missing/ambiguous; protected action denied. |
| Central authorization | Single policy decision interface | Call publishing path without valid authorization; denied. |
| Idempotent command | Unique scoped key and stored result | Replay same request; no duplicate canonical side effect. |
| At-least-once attempt traceability | Job and attempt records | Retry after worker interruption; attempts remain correlated. |
| Artifact integrity | Content hash and immutable version metadata | Hash mismatch; artifact marked invalid/quarantined, not silently accepted. |
| No implicit deletion | Explicit lifecycle and retention policy | Delete parent with protected child/held evidence; no destructive cascade. |

## 9. Migration and recovery design checklist

- Define schema version and migration ordering before authoring executable migrations.

- Prefer additive changes at P0; destructive or data-rewriting migrations require separate review and explicit approval.

- Document preconditions, postconditions, expected lock duration and compatibility impact.

- Define backup and restore procedure and verify it in an isolated environment before any production migration.

- Define how an interrupted migration is detected and safely resumed or recovered.

- Ensure application versions and workers tolerate the intended schema compatibility window.

- Never use a rollback script as a substitute for a tested restore strategy.

- Do not run migrations against the existing project or any live database under this design-only pack.

## 10. WP-1 acceptance test catalogue

| Test ID | Acceptance assertion | Evidence expected | Status |
| --- | --- | --- | --- |
| WP1-ID-01 | New canonical entity receives immutable UUIDv7 identity | Automated test + persisted record inspection | NOT RUN |
| WP1-ID-02 | Canonical identity remains stable across version creation | Automated test showing same entity ID and distinct version ID | NOT RUN |
| WP1-OWN-01 | Each canonical entity has one authoritative owner | Constraint/domain test and negative duplicate-owner case | NOT RUN |
| WP1-REL-01 | Typed references reject wrong-type or missing targets | Positive and negative relationship tests | NOT RUN |
| WP1-CNT-01 | ContentItem and ContentVariant remain distinct | Domain test covering multiple variants per item | NOT RUN |
| WP1-STA-01 | State dimensions persist independently | Test showing review/approval/distribution changes do not overwrite content lifecycle | NOT RUN |
| WP1-AUD-01 | Material state and decision changes are attributable | Audit record includes actor, time, action, target and correlation | NOT RUN |
| WP1-IDEMP-01 | Duplicate idempotency key does not duplicate side effect | Replay test and stored result inspection | NOT RUN |
| WP1-VER-01 | Stale version update is rejected or safely reconciled | Concurrent update test | NOT RUN |
| WP1-RGT-01 | Unknown rights cannot be treated as permission | Negative policy/persistence integration test | NOT RUN |
| WP1-MIG-01 | Migration can be applied and recovery plan validated in isolated environment | Migration log + restore/recovery evidence | NOT RUN |
| WP1-COMP-01 | Schema/API compatibility policy is testable | Compatibility matrix and automated contract test | NOT RUN |

## 11. Decisions deliberately deferred

| Decision area | Why deferred | Required trigger |
| --- | --- | --- |
| Exact physical table and column names | Authoritative data dictionary and exact CF wording are not fully verified | Source reconciliation complete |
| Exact enum values and transition graph | Must come from governing lifecycle/state contract | Source contract imported and reviewed |
| Numeric resource limits | Previously deferred; must be based on workload classes and capacity evidence | Before worker/job execution limits are implemented |
| Database vendor, hosting and provider | PostgreSQL-compatible direction accepted; provider choice not approved | Separate owner decision after cost/security review |
| Object storage provider | Only abstraction accepted; no provider selected | Separate owner decision; no paid activation without approval |
| Retention durations and legal-hold details | Must be grounded in governing policy/legal requirements | Authoritative policy and owner review |
| Operational indexes/partitioning | Need actual query patterns and scale evidence | After access-pattern review; before performance-critical rollout |

## 12. WP-1 implementation work order — draft only

This work order is intentionally NOT ACTIVE. It becomes executable only after contract freeze and a separate explicit owner authorization.

| Field | Draft definition |
| --- | --- |
| Work package | WP-1 — Canonical Domain & Persistence Foundation |
| Objective | Implement the approved canonical domain and persistence contract without disturbing existing Shorts Studio work. |
| Preconditions | Authoritative source pack reconciled; contract freeze approved; repository baseline refreshed under explicit authorization; scope and file allowlist approved. |
| Allowed work after authorization | Implement only approved domain models, persistence adapters, migrations, schema validation and WP-1 tests within the authorized file scope. |
| Forbidden without separate approval | Destructive migration; broad refactor; dependency/provider activation; secrets rotation; deployment; paid services; publishing; broad Git operations. |
| Required outputs | Schema/model implementation, migrations, data dictionary update, test evidence, migration/recovery notes, traceability report. |
| Exit criteria | WP-1 acceptance tests pass; migration/recovery evidence reviewed; no unresolved critical contract divergence; independent read-only QA disposition recorded. |
| Rollback boundary | Must be explicitly defined per migration and validated in isolated environment before any live application. |

## 13. Readiness decision

| Question | Current answer |
| --- | --- |
| Is the architecture direction accepted? | Yes — at decision level, per recorded ADR/CF outcomes. |
| Is this physical schema approved? | No — this is a design candidate. |
| Are exact original CF sources fully verified? | No — Batch 04 records outstanding source gaps. |
| Is the contract frozen? | No. |
| Is WP-1 implementation authorized? | No. |
| Can this pack be used for structured design review? | Yes — with every candidate reconciled against authoritative sources before freeze. |

Recommended next step: complete source intake and exact wording reconciliation, then review this WP-1 candidate against the authoritative data dictionary, lifecycle contract and approved WP-1 specification. Do not skip directly to migrations.

END OF BATCH 05


## Source document metadata (preserved from DOCX)

- **Footer:** NEXTDECODE • P0 design candidate • Not frozen • Not implementation authorization

