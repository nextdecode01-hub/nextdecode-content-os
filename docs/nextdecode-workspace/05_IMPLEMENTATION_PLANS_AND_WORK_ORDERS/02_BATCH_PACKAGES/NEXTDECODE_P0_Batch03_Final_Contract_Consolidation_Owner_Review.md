NEXTDECODE

P0 — FINAL CONTRACT CONSOLIDATION
& OWNER REVIEW PACKAGE

BATCH 03 • Version 0.1 • 1 November 2026

Consolidation candidate — not frozen, not implementation-authorized

## 1. Executive summary

This package brings the existing P0 architecture and reconciliation work into one owner-review path. It is intended to reduce document hopping and make the next decision clear: review the detailed contract baseline, resolve or explicitly defer owner-reserved items, and only then consider authorizing WP-1.

This is a candidate consolidation, not a claim that every source has been re-read or that every contract detail is settled. Exact original CF wording that was not present in the available working files is deliberately identified as a source-completion task rather than reconstructed.

| Area | Current posture |
| --- | --- |
| Architecture decisions ADR-001–ADR-010 | Recorded as accepted in the project decision history; implementation not implied. |
| Contract decisions CF-01–CF-24 | Recorded as accepted in the project decision history; some exact source wording still needs verbatim import. |
| X-01–X-12 reconciliations | Candidate clarifications; not automatically owner-approved or frozen. |
| WP-1–WP-6 | Design/work-order packages prepared; no engineering execution implied. |
| WP-0 | Conditionally complete as baseline/preservation assessment only. |
| Implementation authorization | Not granted. |
| External operations / spending / deployment / publishing | Not authorized. |

## 2. Consolidated P0 scope and architecture

P0 establishes the shared foundation for NEXTDECODE Content OS while preserving the existing Shorts Studio as a bounded specialist engine.

- Initial product mode: single-owner Creator Mode and one NEXTDECODE brand.

- Existing Python/FFmpeg Shorts Studio remains in place and is integrated through a bounded adapter; no wholesale rewrite.

- Long-term direction: cloud control plane for shared workflow/control state, with local or remote workers for bounded execution. No provider or deployment is selected.

- Initial spend target: ₹0; no paid service or infrastructure activation without separate approval.

- Human approval remains required before critical publishing actions; automatic public publishing remains disabled pending separate policy.

- Unknown, missing or ambiguous rights, approval or authorization never grants permission for a protected action.

- Approval, authorization, execution and successful distribution are distinct facts.

### 2.1 Logical system boundaries

| Boundary | Responsibility | Key constraint |
| --- | --- | --- |
| Workspace & control | Workspace context, owner controls, operational visibility | Single-owner initial scope. |
| Canonical domain & persistence | Stable IDs, entities, relationships, versions | One authoritative owner per canonical entity. |
| Workflow & execution | Workflow, tasks, jobs, attempts, leases, retries | Durable and auditable; at-least-once delivery. |
| Worker system | Identity, enrollment, trust, capability facts and scoped execution | Capability declaration is not permission. |
| Artifact system | Assets, immutable artifact versions, manifests, transfer and validation | Integrity and provenance required. |
| Governance | QA, rights, review, approval, authorization and audit | Central enforcement; fail closed. |
| Specialist studios & adapters | Research, script, visuals, rendering, distribution | Adapters cannot bypass central policy. |

## 3. Source authority and consolidation rules

1. Explicit owner decision records and accepted ADR/CF decisions govern their exact scope.

1. Governing standards, canonical data dictionary, API/event and lifecycle contracts apply within their approved scope and cannot override an explicit owner decision.

1. WP-1 through WP-6 specifications elaborate implementation requirements but do not silently change owner decisions.

1. Consolidated appendices and traceability matrices are derivative indexes.

1. Reconciliation documents remain proposals unless explicitly accepted.

1. Chat summaries and generated indexes do not override authoritative source records.

When sources conflict, preserve both statements, identify the exact clauses and scope, mark the issue open/needs review, and do not silently select one. Supersession requires explicit authority, scope, date/version and traceability.

### 3.1 Source-completion limitation

The working traceability register intentionally does not reconstruct the exact wording of CF-03–CF-12, CF-15–CF-19 and CF-23 from memory. Those rows must be copied verbatim from the authoritative Artifact 08 owner decision record and checked against its version. Until then, this package is not source-complete and cannot be treated as a frozen master contract.

The available working package names the relevant source documents, but their exact source file hashes and original row text were not all available in the current artifact set. No hashes, commit IDs or approval evidence have been invented.

## 4. Cross-cutting contract invariants

1. One canonical entity owner; cross-domain references do not imply permission.

1. Canonical identity is immutable; changes are versioned.

1. Unknown/missing/ambiguous rights, approval or authorization never grants protected permission.

1. Approval ≠ authorization ≠ execution ≠ successful publication.

1. Hard QA, rights and policy blockers are centrally enforced.

1. Workers execute bounded assignments and cannot expand their own authority.

1. Queue delivery is at-least-once; idempotency and durable attempt history prevent duplicate logical processing.

1. Artifacts are immutable/versioned and integrity checked; repair creates a new version.

1. Review and approval bind to the exact version and policy context.

1. Automatic public publishing remains disabled.

1. Existing Shorts Studio remains a bounded specialist engine.

1. Local-only work waits safely if its local worker is unavailable.

1. Cloud control plane is a direction, not a provider/deployment decision.

1. Local-first/free-first; no paid services without explicit approval.

## 5. Consolidated WP-1 to WP-6 contract outline

| WP | Contract responsibility | Must prove before exit |
| --- | --- | --- |
| WP-1 | Canonical domain, persistence, immutable IDs, ownership, migrations and repositories | Schema constraints, repository/transaction tests, migration safety and traceability. |
| WP-2 | Workflow/task/job/attempt/lease, durable queue, outbox/inbox, idempotency and recovery | Restart recovery, duplicate delivery, stale lease and idempotency behavior. |
| WP-3 | Worker identity, enrollment, trust, capability facts, credentials and bounded execution | Unknown/revoked worker denial, scope enforcement and audit. |
| WP-4 | Asset/artifact distinction, immutable versions, manifests, checksums, transfer, validation and quarantine | Integrity, incomplete transfer, quarantine and lifecycle tests. |
| WP-5 | QA, rights, review, approval, centralized authorization, emergency controls and audit | Hard-blocker enforcement and adapter/API/worker bypass-negative tests. |
| WP-6 | Synthetic end-to-end vertical slice, failure injection, recovery and independent QA | VS-01–VS-18, failure oracles, evidence bundle and Kilo read-only findings. |

## 6. Workflow, job and execution boundary

| Concept | Owns | Must not be confused with |
| --- | --- | --- |
| Workflow | Overall process coordination and lifecycle | A worker execution attempt. |
| WorkflowTask | Logical step, dependency and task outcome | A durable executable request. |
| Job | Durable executable request and scheduling state | The logical workflow step itself. |
| JobAttempt | One execution attempt and its outcome | The job's complete history. |
| Lease | Time-bounded worker claim/ownership | Worker identity or authorization. |
| Worker | Registered execution identity and trust/capability facts | A permission grant. |

A successful Job does not automatically complete its WorkflowTask or Workflow. Orchestration evaluates task-specific predicates and then updates workflow state. At-least-once delivery is expected; duplicate delivery must not create duplicate logical processing. A stale worker cannot overwrite a newer attempt.

Exact state vocabularies, transition guards, cardinality, cancellation/reopen semantics and numeric lease/retry timings remain subject to the approved detailed contracts.

## 7. Artifact and governance contract

### 7.1 Artifact lifecycle

- Asset and Artifact are distinct concepts; artifact versions are immutable.

- Relational metadata is authoritative; binary storage is behind an abstraction.

- Manifest references exact artifact versions and includes integrity metadata.

- Transfer, validation and quarantine are explicit records/states.

- A repair creates a new artifact version; it does not rewrite prior evidence.

- Retirement, deletion request, dependency assessment, logical deletion, legal hold, purge authorization, physical purge and restore are distinct operations.

- No cascade deletion of shared dependencies. Rights revocation does not automatically erase audit evidence.

### 7.2 Governance separation

| Concept | Meaning |
| --- | --- |
| QA result | Quality evaluation outcome; hard blockers cannot be bypassed by ordinary approval. |
| Rights assessment | Use-specific rights state and evidence. |
| Review snapshot | Exact version and context presented for human review. |
| Approval decision | Human decision: APPROVED, REJECTED, CHANGES_REQUESTED, EXPIRED or REVOKED. |
| Authorization decision | Central permission for exact action/resource/version/hash/destination/time. |
| Execution/distribution outcome | What actually happened, including ambiguous external outcome. |

Central authorization is the authority boundary. APIs, workers and publishing adapters must enforce it. A grant for one version or destination does not authorize another. Expiry/revocation must be enforced. Unknown rights or approval fail closed.

## 8. WP-1 schema and migration review package

This is a review checklist for the first implementation package, not a final DDL specification. Exact schema definitions must be reconciled against the authoritative canonical data dictionary and approved WP-1 schema candidate.

| Review area | Questions that must be answered | Evidence required |
| --- | --- | --- |
| Canonical identity | Are IDs immutable UUIDv7? Are entity ownership and uniqueness explicit? | DDL, constraints, repository tests. |
| Entity ownership | Is there one authoritative owner per canonical entity? Are cross-domain references typed? | Ownership matrix and FK/constraint tests. |
| Versioning | Which entities are versioned? What is immutable? How is optimistic concurrency enforced? | Version model and concurrent update tests. |
| Relationships | Are cardinalities, nullability, delete behavior and dependency rules explicit? | ERD/schema and referential-integrity tests. |
| Transactions | Which writes must be atomic? How are state change and outbox record committed together? | Rollback and transactional outbox tests. |
| Migrations | Are migrations additive and reversible or forward-recoverable? Is data backfill required? | Migration plan, preconditions and rollback/forward plan. |
| Audit | Which changes record actor, source, correlation and timestamp? | Audit schema and reconstruction test. |
| Synthetic data | Can the schema and repositories be tested without real user data? | Deterministic fixtures and cleanup strategy. |

### 8.1 WP-1 proposed exit criteria

- Approved schema baseline and migration strategy.

- No destructive migration of existing user data.

- Canonical identity, uniqueness, ownership and referential integrity enforced.

- Repository tests cover create/read/update/version and invalid relationships.

- Transaction rollback tests prove partial writes do not leak.

- Traceability links each schema object to an approved requirement/source clause.

- No unrelated existing project files are modified.

### 8.2 WP-1 unresolved choices

- Exact package/module placement in the existing repository.

- Migration framework and local database connection strategy.

- Exact table names, columns, nullability, indexes, FK constraints and delete behavior.

- Which entity records require optimistic version columns and which event/audit fields are mandatory.

- Exact outbox/inbox schema ownership and transaction boundary.

- Whether isolated worktree/branch is permitted for implementation.

## 9. Owner-reserved decisions and safe interim posture

| ID | Decision | Safe interim posture |
| --- | --- | --- |
| OR-01/02 | Legal-hold authority/release and irreversible purge authority | No physical purge. |
| OR-03 | Retention classes and durations | Do not invent durations; preserve records. |
| OR-04/05 | Audit purge and backup propagation | Preserve audit; do not claim complete deletion. |
| OR-06/07 | Emergency pause authority/scope and break-glass | Deny unapproved exceptions. |
| OR-08 | In-flight external actions during pause/revocation | Reconcile before retry. |
| OR-09/10 | Worker identity assurance and isolation threat model | Do not trust unverified identity; no privileged execution. |
| OR-11/12/13 | Lease revocation, quarantine/recovery and quarantined output treatment | Quarantine and require review. |
| OR-14/15 | Numeric lease/retry/heartbeat and idempotency retention/scope | Do not invent production values. |
| OR-16 | External provider idempotency/reconciliation | No blind retry of ambiguous non-idempotent action. |
| OR-17/18 | Local runtime/database and future cloud provider | Provider-neutral; no paid activation. |
| OR-19/20 | Publishing automation and production release authorization | Automatic public publishing disabled; synthetic P0 only. |

Only ask the owner about a reserved item when it becomes a genuine blocker to the next authorized package. Deferral is not permission to invent a default.

## 10. P0-A vertical slice and acceptance oracles

1. Create a synthetic ContentItem and ContentVariant.

1. Create a Workflow and dependent WorkflowTask.

1. Create a durable Job using the approved command contract.

1. Dispatch and claim the job with an authenticated worker.

1. Execute a deterministic synthetic operation.

1. Register an immutable ArtifactVersion and manifest.

1. Record task/job/attempt/workflow transitions and audit history.

1. Reconstruct the execution from durable records after restart.

1. Inject worker crash, lease expiry, duplicate delivery, checksum mismatch and authorization denial.

1. Demonstrate safe recovery and prove no unauthorized external side effect occurred.

WP-6 proposed tests VS-01–VS-18 and failure cases F-01–F-18 are design oracles. They are NOT_RUN until actually executed against a named build, environment and fixture. Historical Phase 10 report claims of 535 passing tests are historical only and do not prove current P0 acceptance.

## 11. First implementation authorization brief — WP-1 only

Recommended first engineering scope after formal contract freeze: WP-1 canonical domain and persistence foundation only. This is a proposed authorization brief, not an authorization.

| Field | Proposed value / requirement |
| --- | --- |
| Work package | WP-1 — Canonical domain and persistence foundation. |
| Precondition | Owner approves exact detailed contract baseline and WP-1 schema candidate. |
| Repository | /home/demon/shorts_studio (historical path; verify only when authorized). |
| Permitted scope | Only approved new domain/persistence modules, additive migrations and isolated tests. |
| Preservation | Preserve all tracked modifications and untracked files; no reset/revert/stash/clean/delete/overwrite/rename/broad stage. |
| Prohibited | No commit/push/branch/remote changes, destructive migration, paid service, provider activation, deployment, real-data migration or publishing. |
| Engineering owner | To be explicitly named in the actual work order; prior role assignments do not launch a task. |
| Required report | Changed paths, diff summary, migrations, commands/tests actually run, evidence, limitations and deviations. |
| Acceptance | Architecture review plus independent read-only QA where appropriate; owner accepts exact scope. |

### 11.1 Stop conditions

- Any collision with existing user modifications or untracked paths.

- Any unresolved canonical entity ownership or schema source conflict.

- Any migration requiring destructive data transformation.

- Any need to choose a paid provider or incur spend.

- Any request to expand beyond WP-1.

- Any ambiguity about authorization, rights or protected actions.

## 12. Owner review — decisions requested

This package is designed to ask for only the decisions genuinely needed now. Existing accepted ADR/CF decisions are carried forward and are not being re-requested.

| Review item | What the owner is being asked to do | Current status |
| --- | --- | --- |
| R-01 Source completeness | Allow source-completion pass to import exact CF wording and source versions before freeze. | Required before freeze. |
| R-02 Contract candidate | Review the consolidated P0 contract set and identify corrections or objections. | Not approved yet. |
| R-03 Owner-reserved blockers | Resolve only items that block the detailed contract or WP-1; explicitly defer others. | Open/reserved. |
| R-04 Contract freeze | Approve exact versioned baseline, scope and exclusions after source completion. | Not frozen. |
| R-05 WP-1 authorization | Separately authorize WP-1 with exact permitted paths and work order. | Not authorized. |
| R-06 External operations | Separate future approval for provider, spending, deployment, real data or publishing. | Not authorized. |

### 12.1 What is not being requested

- No re-approval of ADR-001–ADR-010 or CF-01–CF-24 where already accepted.

- No approval to implement WP-2 through WP-6.

- No approval to start Qoder, OpenCode or Kilo tasks.

- No approval for paid services, cloud provider, deployment or spending.

- No approval for public publishing or real external side effects.

- No approval to modify the repository.

## 13. Readiness conclusion and next action

| Gate | Status |
| --- | --- |
| G0 — Reconciliation | Candidate package assembled; source-completion remains. |
| G1 — Detailed contract freeze | NOT READY until exact source wording and owner review are complete. |
| G2 — WP-1 implementation authorization | NOT AUTHORIZED. |
| G3 — Integration authorization | NOT AUTHORIZED. |
| G4 — External operations | NOT AUTHORIZED. |
| G5 — P0 acceptance | NOT RUN. |

Recommended next action: complete a source-backed reconciliation pass against the original Artifact 08 decision record, detailed freeze pack, canonical data dictionary, API/event standard and WP-1 schema candidate. Import exact wording and source versions, update the master traceability register, then present the final contract freeze decision to the owner. Do not start implementation until the owner separately authorizes WP-1.

## Appendix A — Working artifacts available during consolidation

### Historical source snapshot (verbatim from the DOCX)

Prior working artifacts found in the current file workspace: 6 of 13 indexed files.

- NEXTDECODE_P0_Batch02_01_Master_Traceability_Register_0.1.md

- NEXTDECODE_P0_Batch02_02_Decision_and_Owner_Reserved_Register_0.1.md

- NEXTDECODE_P0_Batch02_03_Dependency_and_Sequencing_Map_0.1.md

- NEXTDECODE_P0_Batch02_04_Agent_Execution_and_Change_Control_Protocol_0.1.md

- NEXTDECODE_P0_Batch02_05_Risk_Register_and_Mitigation_Plan_0.1.md

- NEXTDECODE_P0_Batch02_06_Implementation_Readiness_Scorecard_0.1.md

Not present in the current working folder (this does not prove the source does not exist elsewhere):

- NEXTDECODE_P0_01_X12_Unified_Status_Vocabulary_Source_Precedence_Evidence_Classification_0.1.md

- NEXTDECODE_P0_02_P0_Implementation_Master_Plan_0.1.md

- NEXTDECODE_P0_03_Repository_Integration_and_Preservation_Map_0.1.md

- NEXTDECODE_P0_04_Engineering_Work_Orders_WP1_to_WP6_0.1.md

- NEXTDECODE_P0_05_P0_Acceptance_Evidence_and_Release_Gates_0.1.md

- NEXTDECODE_P0_06_Owner_Review_and_Implementation_Authorization_Checklist_0.1.md

- NEXTDECODE_P0_07_Master_Register_Change_Log_and_Document_Index_0.1.md

This list describes working artifacts only. It does not substitute for the original authoritative source documents or their exact versions/hashes.

### Current workspace verification — 2026-11-04

The six Batch 02 working artifacts above are now represented as six sections inside the consolidated `NEXTDECODE_P0_Batch02_Consolidated.docx` and Markdown counterpart; they are not six standalone files in the current workspace.

All seven separately indexed P0 control artifacts 01–07 have now been located in `05_IMPLEMENTATION_PLANS_AND_WORK_ORDERS/01_MASTER_PLANS_AND_WORK_ORDERS/`:

- `NEXTDECODE_P0_01_X12_Unified_Status_Vocabulary_Source_Precedence_Evidence_Classification.md` — reconciliation candidate; not owner-approved.
- `NEXTDECODE_P0_02_P0_Implementation_Master_Plan.md` — planning candidate; owner review required.
- `NEXTDECODE_P0_03_Repository_Integration_and_Preservation_Map.md` — planning map; logical paths are not verified repository paths.
- `NEXTDECODE_P0_04_Engineering_Work_Orders_WP1_to_WP6.md` — draft templates; not assignments or implementation authorization.
- `NEXTDECODE_P0_05_P0_Acceptance_Evidence_and_Release_Gates.md` — candidate acceptance framework; not executed.
- `NEXTDECODE_P0_06_Owner_Review_and_Implementation_Authorization_Checklist.md` — review aid; no approval recorded.
- `NEXTDECODE_P0_07_Master_Register_Change_Log_and_Document_Index.md` — coordination index; source hashes and authority links require verification.

Location is verified; authority, completeness and currency are not thereby accepted. Retain the status written in each source document.


## Source document metadata (preserved from DOCX)

- **Footer:** NEXTDECODE P0 • Batch 03 • Page

