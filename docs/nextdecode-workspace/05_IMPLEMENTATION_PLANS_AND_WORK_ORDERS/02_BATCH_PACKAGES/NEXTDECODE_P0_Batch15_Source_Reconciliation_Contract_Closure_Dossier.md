NEXTDECODE

# P0 Source Reconciliation &
Contract Closure Dossier

BATCH 15  |  CONTROLLED DOCUMENTATION PACK

Version 1.0  •  1 November 2026  •  Design / governance pack

## Document control

| Field | Value |
| --- | --- |
| Document ID | ND-P0-B15 |
| Title | P0 Source Reconciliation & Contract Closure Dossier |
| Series position | Batch 15; follows Batches 02–14 |
| Primary purpose | Reconcile the working ODR-01–ODR-22 register against higher-authority owner decisions, accepted CF/ADR records and detailed contract reconciliation. |
| Status | Source-informed reconciliation dossier; proposed closure actions require the authority specified in each record. |
| Authority boundary | Does not approve new owner decisions, freeze detailed contracts, authorize implementation or replace source documents. |
| Primary baseline | NEXTDECODE_P0_Decision_Resolution_Register_0.1.md; Artifact 08 v1.0 decision records; Artifact 08 reconciliation/freeze candidate v1.1. |
| Implementation authorization | NOT GRANTED |
| Detailed contract freeze | PENDING consolidated owner confirmation |

## Executive summary

The complete working ODR-01–ODR-22 Decision Resolution Register has been located in the Library and read. It is a derived working register created to consolidate decision groups; it is not, by itself, proof that every ODR identifier existed as an original owner decision. The authoritative decision records are the accepted ADR/CF records and explicit owner-review records. The correct process is to preserve the working ODR IDs for traceability while mapping each row to its actual source authority and keeping proposed resolutions visibly proposed.

The source material confirms ADR-001–ADR-010 as accepted and records CF-01–CF-24 as owner-reviewed/accepted with different acceptance routes: CF-01–CF-15 explicitly accepted; CF-16–CF-21 and CF-23 accepted under standing delegation; CF-22 explicitly selected as Option A centralized authorization; CF-24 explicitly establishes the no-paid-services constraint while provider/operational choices remain deferred. Detailed contract freeze remains pending. Implementation authorization remains not granted.

Batch 15 turns that distinction into a usable reconciliation baseline: register integrity rules, all 22 ODR dispositions, RCN-01–RCN-11 findings, freeze gates FZ-01–FZ-21, the X-01–X-12 consistency backlog, source-authority rules, closure evidence requirements and owner-reserved decisions.

## 1. Scope and authority boundaries

### 1.1 What this dossier does

- Uses the working ODR-01–ODR-22 register as the index of decision-resolution topics.

- Maps decisions to accepted CF/ADR records, architecture constraints and detailed contract reconciliation findings where the source material supports the mapping.

- Separates accepted decisions, derived groupings, proposed resolutions, owner-reserved decisions and deferred operational choices.

- Defines what evidence is needed to close each remaining contract-freeze requirement.

- Creates a traceable closure plan for the detailed contract baseline.

### 1.2 What this dossier does not do

- It does not convert PROPOSED entries into OWNER-ACCEPTED decisions.

- It does not treat the derived ODR register as a higher authority than explicit owner decision records.

- It does not reopen accepted ADR/CF decisions or change their wording.

- It does not grant detailed contract freeze, implementation, repository, Git, test, agent, provider, spending, deployment, production-generation, upload or publishing permission.

- It does not invent numerical lease/retry/retention/capacity/RPO/RTO values or provider choices that the source documents explicitly defer.

## 1.3 Authority hierarchy

| Priority | Source class | How to use it |
| --- | --- | --- |
| 1 | Explicit owner decision records and accepted ADR/CF decisions | Controlling authority for accepted decisions; preserve exact IDs and wording. |
| 2 | Locked project constraints and architecture decision records | Source-backed operating/product constraints; do not recast as new ODR approvals. |
| 3 | Canonical data dictionary and API/event/lifecycle standards | Governing technical semantics; reconcile detailed contracts to them. |
| 4 | WP-1 through WP-6 specifications | Work-package design proposals; subordinate to accepted decisions and governing standards. |
| 5 | Derived decision-resolution / consolidation registers | Indexes and groups topics; cannot create owner authority. |
| 6 | Reconciliation documents and summaries | Identify conflicts and propose corrections; do not silently amend higher-authority sources. |

A document's date, completeness or filename does not automatically establish its authority. If two records conflict, preserve both references, identify the conflict and resolve it through the designated authority rather than silently choosing whichever wording is easier to implement.

## 2. Source inventory and provenance

| Source record | Role in reconciliation | Status / limitation |
| --- | --- | --- |
| NEXTDECODE_P0_Decision_Resolution_Register_0.1.md | Working ODR-01–ODR-22 index; 22 derived rows, proposals, owner-reserved decisions and deferrals. | Located and read in Library. Derived working register; not proof of 22 original accepted ODR records. |
| Artifact 08 Consolidated Owner Decision Record & Contract Freeze Closure 1.0 | Consolidated owner decision record for ADR-001–ADR-010 and CF-01–CF-24. | Located; final detailed freeze approval explicitly pending. |
| Artifact 08 Implementation Reference — Accepted Contract Decisions 1.0 | Reference for exact accepted CF decision content and implementation interpretation. | Located; implementation reference, not implementation authorization. |
| Artifact 08 Contract Reconciliation & Freeze Candidate 1.1 | RCN-01–RCN-11 findings and FZ-01–FZ-21 closure status. | Located; reconciliation candidate requiring owner confirmation for final freeze. |
| P0 Owner Review & Contract Freeze Decision Record 0.1 | Owner-facing sign-off record and freeze checklist. | Located; document itself labels owner decision draft / not yet approved. |
| ODR-22 Source Reconciliation & Decision-Register Integrity 0.1 | X-11 provenance clarification for ODR-22. | Located; ODR-22 remains provisional grouping; underlying constraints are source-supported. |
| Cross-Document Consistency Gap Review 0.1 | X-01–X-12 conflict/gap index. | Located; documentation-only review; no runtime/repository verification. |
| Canonical Data Dictionary 1.0 | Entity ownership, naming and canonical fields. | Located; reconcile WP schemas against it. |
| API & Event Contract Standard 1.0 | Command/query/event and interface envelope rules. | Located; documentation standard; detailed mappings remain to be completed. |
| Unified Lifecycle & State Transition Standard 1.0 | Domain-owned state machines and transition audit envelope. | Located; documentation standard; cross-WP lifecycle mapping remains open. |
| Module-to-Contract Traceability Matrix 1.0 | Maps modules to Parts/contracts/owners/dependencies. | Located; reconcile with final consolidated contract set. |

### 2.1 Important provenance correction

The working ODR register is available and complete as a 22-row working register. The earlier uncertainty was whether a separate original source register with independent owner-authored ODR-01–ODR-22 rows existed. The current evidence establishes the working register, not a distinct original master source with that exact row set. Therefore the correct description is: 'complete working ODR register located; original ODR row provenance is not independently established for every row.'

ODR-22 is a demonstrated example: the derived row combines single-owner Creator Mode constraints and agent responsibility assignments. The underlying constraints are supported by Architecture Register L-08/L-09/L-13 and Owner Decision Review Sheet C-01/C-02, but no separate accepted owner decision with the combined identifier and exact wording was verified. Keep ODR-22 as a provisional grouping note, not an accepted decision.

## 3. Accepted baseline — carry forward without reopening

| Decision family | Accepted status in source records | Treatment |
| --- | --- | --- |
| ADR-001–ADR-010 | Accepted / owner-accepted in Artifact 08 consolidated decision record and v1.1 reconciliation candidate. | Carry forward; do not reopen in this dossier. |
| CF-01–CF-15 | Explicitly accepted by owner. | Carry forward exact source wording. |
| CF-16–CF-21 | Accepted under standing delegation. | Carry forward with acceptance route preserved. |
| CF-22 | Explicit owner choice, Option A: centralized authorization. | Carry forward; detail enforcement/schema still needs reconciliation. |
| CF-23 | Accepted under standing delegation. | Carry forward. |
| CF-24 | Explicit no-paid-services constraint accepted; provider/operational choices deferred. | Carry forward constraint; do not infer a provider or budget. |

### 3.1 Accepted architectural directions

| ADR | Direction |
| --- | --- |
| ADR-001 | UUIDv7 canonical IDs; opaque and immutable. |
| ADR-002 | PostgreSQL-compatible relational database as authoritative shared-state store. |
| ADR-003 | Database-backed durable queue with transactional outbox/inbox initially. |
| ADR-004 | Versioned HTTP/JSON contracts with schema validation. |
| ADR-005 | Unique worker identity, scoped short-lived credentials and capability authorization. |
| ADR-006 | Relational artifact metadata; binaries behind an object-storage abstraction. |
| ADR-007 | Centralized authorization; publishing adapters cannot bypass it; automatic publishing disabled pending separate policy. |
| ADR-008 | QA outcomes PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW, BLOCKED; ordinary approval cannot bypass hard blockers. |
| ADR-009 | Evidence-backed rights states with use-specific enforcement. |
| ADR-010 | Separate lifecycle state machines for content, workflow, execution, review, approval, authorization and distribution. |

### 3.2 Accepted CF decision content — preserve by source ID

| CF range / ID | Accepted decision summary | Required reconciliation behavior |
| --- | --- | --- |
| CF-01 | ContentItem is shared editorial identity; ContentVariant is format/platform/language/treatment derivative. | Use consistently in entities, payloads, foreign keys and studio adapters. |
| CF-02 | One authoritative owner per entity; typed cross-domain refs; no competing canonical identities; relationships do not imply permission; retain 12-contract ownership structure. | No shadow canonical identity or implicit permission. |
| CF-03 | Immutable UUIDv7 identity; envelope/schema/workspace scope; mutable version metadata; null/empty/unknown distinct; no inference of missing critical values. | Preserve epistemic distinctions and explicit scope. |
| CF-04 | Entity identity/version/schema/artifact/execution attempt are distinct; concurrency-safe versioning; immutable artifact versions; review/approval exact-version; idempotency/event IDs distinct. | Pin all review/governance references to exact versions. |
| CF-05 | Separate lifecycle state owners for content, workflow, execution, review, approval, authorization and distribution. | No universal status field or cross-domain state ownership. |
| CF-06 | Typed refs and workspace boundary; archival/logical/physical deletion distinct; dependency-aware; audit preserved. | Deletion and retention remain governed. |
| CF-07 | Audit/provenance exact version lineage; avoid logging secrets/PII. | Retain attributable audit with privacy controls. |
| CF-08 | Workflow Definition, Run, Task, Job, Attempt, Queue Message and Event distinct; at-least-once; idempotency; workers not global orchestrators. | Explicit entity/cardinality/state mappings. |
| CF-09 | Explicit validated job states; durable attempt history; success requires attributable evidence; reconcile external side effects. | No false success or blind retry. |
| CF-10 | Leases with fencing; retries create new attempt IDs; durable idempotency; ambiguous external actions reconciled. | Numeric lease/retry parameters remain deferred. |
| CF-11 | Domain Events, Commands, Outbox, Inbox distinct; transactional outbox; durable dedup; scoped ordering; events do not grant authorization. | Complete envelope, dedup and replay contracts. |
| CF-12 | Separate orchestration/scheduling/queue/worker/domain ownership; explicit dependencies; reject cycles initially; local-only jobs wait if local worker unavailable. | No silent cloud substitution for local-only work. |
| CF-13 | Unique worker identity, trust lifecycle, declared/verified/available/authorized capabilities distinct; short-lived scoped revocable credentials. | Capability catalogue and credential protocol remain open. |
| CF-14 | Capability versioning/verification, isolation, scoped filesystem/network/credentials/artifacts, resource limits by job class; no cross-role privilege. | Minimum guarantees require detailed specification; numeric limits deferred. |
| CF-15 | Artifact identity/immutable versions; relational metadata, binary storage abstraction; Asset vs Artifact; checksums; controlled transfer; no overwrite. | Complete manifest, transfer and validation schemas. |
| CF-16–CF-21 | Accepted under standing delegation; include immutable manifests, exact version refs, access/rights separation, validation/quarantine, QA outcomes, rights lifecycle, review/approval binding. | Preserve standing-delegation route; align exact vocabulary and schemas. |
| CF-22 | Explicit Option A: centralized authorization. | Default deny, exact action/resource/version/destination/policy/time binding. |
| CF-23 | Accepted under standing delegation; structured error taxonomy and recovery semantics. | Separate severity from retryability; reconcile ambiguous effects. |
| CF-24 | No paid services; local-first/free-first; no silent billing exposure; provider/deployment deferred. | No provider, subscription or spending without separate approval. |

## 4. Working ODR-01–ODR-22 reconciliation register

The following table preserves the working register's topic and proposed resolution. It does not upgrade proposals to accepted decisions. 'Source mapping' identifies the strongest available source family; where exact source provenance is not established, the row remains derived/proposed.

| Working ID | Area | Working resolution (summary) | Current disposition | Source mapping / note |
| --- | --- | --- | --- | --- |
| ODR-01 | Entity schema | Keep canonical data dictionary authoritative; specify fields, nullability, constraints, references and transitions. | PROPOSED | Canonical Data Dictionary; WP-1 v0.3; CF-02/03/05. |
| ODR-02 | Content versioning | Keep entity identity, content version and variant identity distinct; content versions immutable. | PROPOSED | CF-01/03/04; WP-1 v0.3. |
| ODR-03 | Workflow model | Separate workflow definition, workflow run, task and dependency; pin each run to a definition version. | PROPOSED | CF-08/12; ADR-010; WP-2 v0.1. |
| ODR-04 | Job lifecycle | Separate logical job from attempts; specify terminal outcomes, cancellation and remediation. | PROPOSED | CF-08/09/10; WP-2 v0.1. |
| ODR-05 | Lease/fencing | One authoritative active lease per job; fencing prevents stale worker commit after takeover. | PROPOSED | CF-10; ADR-003; WP-2 v0.1. |
| ODR-06 | Retry/idempotency | Same key + same canonical payload returns original logical result; same key + different payload conflicts. | PROPOSED | CF-09/10/11; WP-2 v0.1. |
| ODR-07 | Outbox/inbox | Commit domain state and outbox atomically; deduplicate repeated delivery through inbox receipts. | PROPOSED | CF-11; ADR-003; WP-2 v0.1. |
| ODR-08 | Worker identity | Identity independent of hostname; explicit enrollment and trust lifecycle. | PROPOSED | CF-13; WP-3 v0.1. |
| ODR-09 | Worker capability | Declared, verified, available and authorized capabilities remain distinct. | PROPOSED | CF-13/14; WP-3 v0.1. |
| ODR-10 | Worker isolation | Least privilege and bounded filesystem, network, credential, artifact and resource access; minimum guarantees require owner/security review. | PROPOSED — MINIMUM GUARANTEES OWNER/SECURITY REVIEW | CF-14; WP-3 v0.1. |
| ODR-11 | Artifact model | Asset, Artifact and ArtifactVersion distinct; immutable versions and lineage. | PROPOSED | CF-15/16; ADR-006; WP-4 v0.1. |
| ODR-12 | Artifact transfer | Scoped, attributable, time-limited transfer with integrity verification; security details remain open. | PROPOSED — SECURITY DETAILS OPEN | CF-15/17/18; WP-4 v0.1. |
| ODR-13 | Artifact lifecycle | Define lifecycle ownership/enforcement now; defer provider-specific retention/backup values. | PROPOSED / PARTIALLY DEFERRED | CF-06/17/18; WP-4 v0.1. |
| ODR-14 | Governance schema | Separate QA results, rights evidence, review/approval snapshots and policy decisions. | PROPOSED | CF-19/20/21/22; ADR-008/009/010; WP-5. |
| ODR-15 | Authorization binding | Bind protected authorization to exact action, resource, version/hash, destination and policy context. | PROPOSED — EXACT POLICY SEMANTICS REQUIRE OWNER REVIEW | CF-22; ADR-007; WP-5. |
| ODR-16 | Emergency pause | Central pause authority and fail-closed protected-action behavior while paused. | OPEN — OWNER DECISION | WP-5 v0.1; owner-reserved in working register. |
| ODR-17 | Error and recovery | Separate severity from retryability; durable attempt history; reconcile ambiguous external effects before retry. | PROPOSED | CF-09/10/23; WP-2/WP-6. |
| ODR-18 | Shorts Studio integration | Retain Shorts Studio as bounded specialist engine; governed orchestration prevents direct bypass. | PROPOSED | CF-01/02/05/12/15/22; WP-5/WP-6; inherited D1/U1. |
| ODR-19 | Vertical-slice evidence | Synthetic deterministic non-production test path with failure injection. | PROPOSED | WP-6 v0.1; CF-19/21/22/23. |
| ODR-20 | Acceptance evidence | Tie evidence to requirement, source/build identity, environment, inputs, outputs and reviewer. | PROPOSED | WP-6 v0.1; Batch 14 acceptance framework. |
| ODR-21 | Provider and operations | Keep interfaces provider-neutral; defer vendor, region, sizing and production operations. | DEFERRED | ADR-002/006; CF-24. |
| ODR-22 | Scope and ownership | Carry forward single-owner Creator Mode and agent roles; no scope expansion. | PROVISIONAL GROUPING — SOURCE RECONCILIATION REQUIRED | Architecture Register L-08/L-09/L-13; Owner Decision Review Sheet C-01/C-02; Artifact 08. No distinct combined ODR-22 accepted source verified. |

### 4.1 ODR register integrity rules

1. Retain ODR-01–ODR-22 as working register IDs for historical traceability; do not present them as original source IDs unless source provenance is verified.

1. Every accepted decision must point to an authoritative source record and exact source identifier.

1. Where a working row groups independent constraints, retain each original source ID and label the group as derived.

1. PROPOSED means proposal only; CARRIED FORWARD means a prior decision/constraint is retained but does not prove exact wording; FROZEN requires formal inclusion in an approved detailed contract baseline; VERIFIED requires current implementation or independent evidence.

1. Do not renumber ODR or package-local O/J/W/A/G/F IDs to make the register appear cleaner.

1. Any source correction must append a traceable change; do not silently overwrite decision history.

1. Project constraints and agent role assignments do not independently grant agents implementation, legal, security, approval or external-action authority.

## 5. Artifact 08 reconciliation findings RCN-01–RCN-11

| Finding | Topic | Source-derived finding | Closure treatment |
| --- | --- | --- | --- |
| RCN-01 | Canonical content identity | CF-01: ContentItem is shared editorial identity; ContentVariant is a format/platform/language/treatment derivative. | Carry forward accepted decision; propagate consistently to dictionaries, entity tables, APIs, FKs and adapters. |
| RCN-02 | Entity identity vs version identity | Entity ID identifies enduring logical entity; version identity is separate; review/approval/QA/auth/distribution bind exact versions. | Direction accepted; exact representation/schema remains detailed-spec work. New correction/output creates new version, not overwrite. |
| RCN-03 | Rights-state vocabulary | CF-20 authoritative vocabulary: UNKNOWN, PENDING_REVIEW, CLEARED, RESTRICTED, EXPIRED, REVOKED, DENIED. Older detailed pack used PENDING_VERIFICATION and PROHIBITED. | Align documentation to CF-20. Suggested text compatibility mapping only: PENDING_VERIFICATION→PENDING_REVIEW; PROHIBITED→DENIED. No data migration or semantic equivalence assumed. |
| RCN-04 | Approval-decision vocabulary | CF-21: APPROVED, REJECTED, CHANGES_REQUESTED, EXPIRED, REVOKED. Older example only had APPROVED/REJECTED. | Align schema to full lifecycle. Bind immutable review package, exact versions/checksums, actor/time, decision/reason and policy/scope. No automatic inheritance. |
| RCN-05 | Authorization separate from approval | CF-22 Option A centralized authorization; default deny, exact action/resource/version/destination/policy/time binding. | Accepted decision; reconcile all protected action boundaries; enforce expiry/revocation at execution; no adapter bypass. |
| RCN-06 | QA outcomes and hard blockers | PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW, BLOCKED; immutable and exact-version/policy-bound; scores supplementary. | Accepted; check catalogue and thresholds remain open/deferred; BLOCKED cannot become PASS by ordinary approval. |
| RCN-07 | Job, attempt, lease and retry | Distinct workflow/task/job/attempt/worker identities; at-least-once; durable attempts; leases/fencing; idempotency; outbox/inbox. | Direction accepted. Numeric lease, heartbeat, retry, backoff, jitter, retention and scoped ordering deferred. |
| RCN-08 | Worker trust/capability | Identity independent of hostname; explicit registration/trust; declared/verified/available/authorized capabilities distinct; scoped short-lived revocable credentials; bounded isolation. | Catalogue, credential issuer/protocol, secret storage, numeric resource limits and quotas open. Any system inspection requires separate authorization. |
| RCN-09 | Artifact and manifest | Asset vs Artifact; immutable versions; relational metadata; binary storage abstraction; checksums; exact manifests; quarantine; repair creates new version. | Complete detailed schemas for manifests, transfer, validation, quarantine, lineage, retention and deletion. |
| RCN-10 | Error, recovery and audit | Structured error taxonomy; severity independent of retryability; operation-specific retry; durable failure history; ambiguous effects reconciled; domain-owned recovery; correlation/causation. | Complete schemas, audit-event catalogue, retention and operational monitoring thresholds; providers remain deferred. |
| RCN-11 | Operational constraints | CF-24: local-first/free-first; no paid services or silent billing; no provider/deployment implied by hybrid direction. | Accepted constraint. Provider, region, topology, capacity, budget and operational values remain deferred. |

## 6. Contract-freeze closure matrix FZ-01–FZ-21

| Gate | Requirement | Source status | Closure work |
| --- | --- | --- | --- |
| FZ-01 | ADR-001–ADR-010 recorded as accepted. | COMPLETE | Preserve source references. |
| FZ-02 | CF-01–CF-24 owner review and decisions recorded. | COMPLETE | Preserve exact acceptance route per CF. |
| FZ-03 | ContentItem / ContentVariant distinction. | DECIDED; PROPAGATION REQUIRED | Check all 12 contracts, schemas, APIs and adapters. |
| FZ-04 | Entity ownership and typed relationships consistent across 12 contracts. | NEEDS DOCUMENT RECONCILIATION | Map canonical owner and typed refs per entity. |
| FZ-05 | Required/optional fields, nullability and validation complete. | NEEDS DETAILED SCHEMA REVIEW | Complete field dictionaries, constraints, examples and validation rules. |
| FZ-06 | Entity versioning and exact-version references complete. | NEEDS DETAILED SCHEMA REVIEW | Define immutable version refs and exact binding in review/approval/auth/distribution. |
| FZ-07 | Full state-transition tables, terminal/reopen rules complete. | NEEDS CLOSURE | Reconcile lifecycle standard with WP1–WP6 state owners, transitions, cancellation, expiry, revocation, reopen. |
| FZ-08 | Job/attempt/lease/retry/idempotency semantics complete. | DIRECTION ACCEPTED; PARAMETERS DEFERRED | Specify semantics and owner/config ownership; do not invent numbers. |
| FZ-09 | Event envelope/outbox/inbox/dedup/recovery complete. | NEEDS DETAILED SCHEMA REVIEW | Complete command/event schemas, atomicity, dedup, ordering and replay. |
| FZ-10 | Worker identity/registration/trust/capability complete. | DIRECTION ACCEPTED; CATALOGUE/PROTOCOL OPEN | Complete capability catalogue, credential protocol, revoke/expiry and minimum isolation. |
| FZ-11 | Artifact/manifest/transfer/integrity complete. | NEEDS DETAILED SCHEMA REVIEW | Complete immutable manifest, transfer, checksum, quarantine, repair, retention/deletion. |
| FZ-12 | Rights vocabulary aligned to CF-20. | DOCUMENTATION CONFLICT IDENTIFIED | Update older candidate enums; preserve EXPIRED/REVOKED distinct from DENIED. |
| FZ-13 | Approval vocabulary aligned to CF-21. | DOCUMENTATION GAP IDENTIFIED | Support full decision lifecycle and exact-version package binding. |
| FZ-14 | Central authorization in every contract. | OWNER DECISION ACCEPTED; SCHEMA/BOUNDARIES NEED RECONCILIATION | Map every protected action to central authorization decision and adapter enforcement. |
| FZ-15 | QA outcomes and hard-blocker rules consistent. | OWNER-ACCEPTED; CHECK CATALOGUE OPEN | Define evidence-backed checks and hard-blocker catalogue; scores supplementary. |
| FZ-16 | Error taxonomy, audit and recovery complete. | NEEDS DETAILED SCHEMA REVIEW | Define structured errors, retry classification, audit events, correlation and reconciliation. |
| FZ-17 | Deferred operational values explicitly marked. | COMPLETE AS CONSTRAINT | Keep provider, sizing, retention durations, lease numbers, RPO/RTO and budget deferred. |
| FZ-18 | Cross-document contradiction register resolved. | IN PROGRESS | Close X-01–X-12 with evidence and owner disposition where required. |
| FZ-19 | Final consolidated version and checksum/reference prepared. | PENDING | Publish versioned candidate and integrity manifest after all document reconciliation. |
| FZ-20 | Owner confirms consolidated detailed contract freeze. | PENDING | Owner must explicitly ACCEPT/AMEND/REJECT/DEFER and record freeze. |
| FZ-21 | Separate implementation authorization. | NOT GRANTED; SEPARATE GATE | Requires separate bounded authorization after freeze. |

## 7. X-01–X-12 consistency backlog

| Finding | Severity | Gap | Required closure evidence |
| --- | --- | --- | --- |
| X-01 | HIGH | Workflow/task/job ownership, cardinality and state boundaries ambiguous. | Separate WorkflowDefinition vs WorkflowRun; task definition vs task instance; task/job cardinality; lifecycle vs execution status; authoritative state owner. |
| X-02 | HIGH | ArtifactVersion and manifest contract detail compressed/omitted. | Define immutable artifact version identity, manifest schema, component refs, checksums, lineage and exact approval/distribution binding. |
| X-03 | HIGH | Transfer/validation/quarantine records insufficiently defined. | Define transfer state, source/destination, authorization, integrity, validation evidence, quarantine entry/exit and repair-new-version. |
| X-04 | HIGH | Governance concept count/labels inconsistent. | One controlled glossary for QA outcome, rights state, review package, approval outcome, authorization decision, distribution state. |
| X-05 | HIGH | Authorization/emergency-pause contract incomplete. | Central policy request/decision schema; exact protected action/resource/version/destination/policy/time; pause authority/scope/override/recovery. |
| X-06 | HIGH | Worker trust/credential/revocation semantics insufficient. | Worker identity lifecycle, capability states, credential issue/expiry/revoke, active-job behavior and isolation guarantees. |
| X-07 | MEDIUM | Job/task/workflow mapping and state boundaries incomplete. | Explicit entity cardinality, task-to-job mapping, retries, terminal/cancel/remediation and ownership. |
| X-08 | MEDIUM | Command/event envelope compatibility and validation incomplete. | Align API/event standard with producer/consumer schema, version compatibility, outbox/inbox and idempotency. |
| X-09 | MEDIUM | Artifact lifecycle/deletion/legal hold/access semantics incomplete. | Separate archival, logical/physical deletion, legal hold, retention, access/transfer/export and audit preservation. |
| X-10 | MEDIUM | WP6 acceptance evidence/test oracle/environment controls incomplete. | Define E2E oracle, reproducible fixture, environment identity, correlation IDs, failure injection and evidence index. |
| X-11 | MEDIUM | ODR-22 not faithful transcription of confirmed source row. | Retain as provisional grouping; carry actual scope and agent constraints by source IDs L-08/L-09/L-13 and C-01/C-02. |
| X-12 | LOW | Status labels and document authority language vary. | Adopt multidimensional status model; do not conflate decision authority, design maturity, implementation state and evidence state. |

### 7.1 X-12 controlled status dimensions

| Dimension | Controlled values / guidance |
| --- | --- |
| Decision authority | OWNER-ACCEPTED, PROPOSED, OPEN, DEFERRED, REJECTED; preserve exact source vocabulary where governing. |
| Design maturity | DRAFT, RECONCILED, CANDIDATE, FROZEN. |
| Implementation state | NOT IMPLEMENTED, IMPLEMENTED, PARTIALLY IMPLEMENTED. |
| Evidence state | NOT VERIFIED, VERIFIED, FAILED, NOT RUN, NOT APPLICABLE. |
| Register disposition | CARRIED FORWARD, PROVISIONAL GROUPING, SUPERSEDED; never use as substitute for source authority. |

A row can legitimately be OWNER-ACCEPTED + CANDIDATE + NOT IMPLEMENTED + NOT VERIFIED. One status field must not imply the others.

## 8. Detailed contract closure workstreams

| Workstream | Linked gates/findings | Authority basis | Deliverables | Guardrail |
| --- | --- | --- | --- | --- |
| CW-01 — Domain ownership and schema | FZ-03/04/05/06; X-01/X-04/X-07/X-09 | Canonical Data Dictionary + CF-01–CF-06 | Entity catalogue; owner registry; fields/nullability; keys/FKs; workspace scope; version refs; deletion/retention fields; cross-contract examples. | Do not invent fields or nullability absent source/owner decision; unresolved choices remain OPEN. |
| CW-02 — Lifecycle and workflow | FZ-07/08; X-01/X-07 | Lifecycle Standard + CF-05/08/09/10/12; ADR-010 | State machines per domain; WorkflowDefinition/Run; Task definition/instance; Job/Attempt; transition guards; cancellation/expiry/reopen; state ownership. | Keep lifecycle state separate from execution outcome and external operation status. |
| CW-03 — Commands, events and durable delivery | FZ-08/09; X-08 | API/Event Standard + CF-08/09/11/12; ADR-003/004 | Command/query/event schemas; outbox/inbox; idempotency; delivery dedup; scoped ordering; compatibility; replay/recovery. | Event delivery is not business completion and never grants authorization. |
| CW-04 — Worker trust and isolation | FZ-10; X-06 | CF-13/14; ADR-005; WP-3 | Identity lifecycle; enrollment proof; trust state; capability catalogue/version; credentials; revoke/expiry; resource boundaries; active-job behavior. | Credential issuer/protocol and numeric limits may remain deferred; minimum guarantees need owner/security review. |
| CW-05 — Artifact and transfer | FZ-11; X-02/X-03/X-09 | CF-15/16/17/18; ADR-006; WP-4 | Asset/Artifact/ArtifactVersion; immutable manifest; checksums; validation; quarantine; transfer; lineage; retention/deletion/hold. | Storage provider, region, replication and numeric retention remain deferred. |
| CW-06 — Governance and authorization | FZ-12/13/14/15; X-04/X-05 | CF-19/20/21/22; ADR-007/008/009/010 | Canonical QA/rights/approval enums; exact-version review; policy decision schema; central auth; emergency pause; hard-blocker enforcement. | No ordinary waiver for rights/auth/security hard blockers; emergency pause authority remains owner-reserved. |
| CW-07 — Errors, audit and recovery | FZ-16; X-08/X-10 | CF-07/09/10/11/23; WP-2/WP-6 | Error envelope; severity/retryability; audit events; correlation/causation; failure owner; ambiguous outcome reconciliation; recovery runbooks. | Do not retry around policy denial or unresolved external side effect. |
| CW-08 — Shorts Studio adapter | FZ-14; X-05/X-10 | CF-01/02/05/12/15/22; inherited D1/U1; WP-5/WP-6 | Bounded input/output contract; artifact refs; execution assignment; callbacks/events; central auth enforcement; bypass tests. | No repo inspection or adapter modification authorized by this document. |
| CW-09 — Acceptance and consolidated freeze | FZ-15/18/19/20/21; X-10/X-12 | WP-6; Batch 14; owner freeze record | Traceability; acceptance criteria; evidence index; QA report; contradiction closure; version/checksum; owner freeze sign-off. | Freeze is not implementation authorization. |

## 9. Owner-reserved decisions and safe deferrals

### 9.1 Owner-reserved — do not resolve by routine delegation

| Area | Owner decision required | Why reserved |
| --- | --- | --- |
| Security | Minimum isolation guarantees; trust/revocation behavior; emergency override authority. | Material security and authority boundary. |
| Rights | Evidence requirements and use-specific enforcement where they materially affect permitted use. | Determines permitted use of content/assets. |
| Authorization | Protected-action scope and any override/exception authority. | Controls consequential actions. |
| Data lifecycle | Deletion, legal hold, backup and recovery obligations where irreversible or legally material. | Irreversible/legal consequences. |
| External effects | Any permission to upload, publish or perform real-world actions. | External/public side effects. |
| Commercial operations | Paid provider, subscription, usage charge, billing exposure or deployment. | Financial commitment and provider authority. |

### 9.2 Safe deferrals

| Deferred area | Must be specified now | May remain deferred |
| --- | --- | --- |
| Cloud topology | Provider-neutral boundary and security requirements. | Provider/account/region/deployment topology. |
| Database | PostgreSQL-compatible authoritative store contract. | Hosted provider, sizing and production topology. |
| Queue | DB-backed durable queue, outbox/inbox semantics. | Alternative broker selection. |
| Object storage | Binary storage abstraction, integrity/transfer contract. | Vendor, region, replication, encryption provider settings. |
| Credentials | Unique scoped short-lived revocable credential requirement. | Issuer, exact token format and production secret platform. |
| Execution timing | Lease/heartbeat/retry semantics and config ownership. | Numeric durations, counts, backoff and jitter. |
| Resource controls | Isolation/resource categories and enforcement ownership. | Numerical quotas/concurrency limits until evidence and owner approval. |
| Retention/backup | Lifecycle owner, deletion/hold semantics and enforcement hooks. | Exact durations, backup cadence, RPO/RTO. |
| Monitoring | Required signals and event/log categories. | Vendor and production thresholds. |
| Budget | No-paid-services constraint and explicit approval gate. | Budget/spend activation. |

## 10. Source reconciliation procedure and acceptance tests

1. Pin the exact source document version and record its authority, owner/provenance, date and locator.

1. Extract exact wording and source ID without paraphrasing away qualifiers, acceptance route or scope.

1. Map the source row to the working ODR ID only as an index; do not treat the ODR ID as original authority.

1. Compare against accepted CF/ADR records, canonical dictionary, API/event standard, lifecycle standard and WP contracts.

1. Record every contradiction as a finding with severity, affected requirements, source excerpts and proposed treatment.

1. Classify treatment as carry forward, propagate, align documentation, owner decision required, safe defer, or not verified.

1. Update subordinate detailed contracts; never silently edit the authoritative source decision.

1. Re-run document consistency checks and update the traceability matrix.

1. Obtain owner confirmation for owner-reserved matters and final consolidated freeze.

1. Record the final version/checksum and explicit exclusions; implementation remains a separate authorization.

### 10.1 Reconciliation quality checks

- Every accepted statement has an exact CF/ADR/owner source reference.

- Every ODR row has a source mapping or explicit NOT VERIFIED / PROVISIONAL disposition.

- Every vocabulary enum matches its accepted source or is explicitly marked as a superseded candidate.

- Every state transition has one authoritative owner and an auditable transition record.

- Every protected action is mapped to centralized authorization.

- Every exact-version approval/review/QA/distribution reference is immutable and verifiable.

- Every operational number/provider not approved is marked DEFERRED, not filled with a plausible guess.

- Every unresolved conflict has a finding ID, owner and closure condition.

## 11. Deliverables required before contract freeze

| Deliverable | Minimum contents | Acceptance condition |
| --- | --- | --- |
| D-01 Source/decision map | ODR-01–ODR-22 → exact CF/ADR/L/C source refs; acceptance route; source provenance. | No derived ODR row is misrepresented as owner-approved source. |
| D-02 Canonical domain appendix | 12-contract entity ownership, fields, nullability, refs, identity/version and scope. | No competing owners or unresolved critical schema ambiguity. |
| D-03 Lifecycle/state appendix | Domain-owned state machines and transitions, terminal/cancel/reopen/expiry/revoke behavior. | State ownership and transition guards are explicit. |
| D-04 Execution contract appendix | Workflow/task/job/attempt/lease/retry/idempotency/outbox/inbox. | Implementable without inventing core semantics; deferred numbers remain visible. |
| D-05 Worker contract appendix | Identity/trust/capability/credential/revocation/isolation. | Least-privilege boundaries and owner-reserved items resolved or explicitly deferred. |
| D-06 Artifact contract appendix | Asset/Artifact/ArtifactVersion/manifest/transfer/validation/quarantine/lineage/retention. | Immutable exact-version integrity and transfer enforcement defined. |
| D-07 Governance/auth appendix | QA/rights/review/approval/authorization/pause/distribution. | Accepted vocabularies aligned; protected action boundaries centralized. |
| D-08 Error/audit/recovery appendix | Errors, retries, correlation, audit, recovery ownership and external reconciliation. | No blind retry or untraceable protected action. |
| D-09 Cross-document consistency report | X-01–X-12 closure and evidence references. | All critical/high findings closed or explicitly owner-dispositioned where allowed. |
| D-10 Consolidated freeze candidate | Versioned package index, checksums, change log, open items and owner sign-off. | Owner explicitly freezes exact candidate; no implicit acceptance. |

## 12. Owner freeze record — template

| Field | Required entry |
| --- | --- |
| Freeze decision ID | [Unique ID] |
| Candidate package/version | [Exact consolidated contract version] |
| Package integrity | [Manifest/checksum] |
| Source set | [Artifact 08 v1.0/v1.1; dictionary; API/event; lifecycle; WP1–WP6; traceability] |
| Decision coverage | [CF-01–CF-24 and ADR-001–ADR-010 source status] |
| ODR mapping | [ODR-01–ODR-22; provisional/derived entries clearly marked] |
| Open findings | [X-01–X-12 and other findings with disposition] |
| Owner-reserved decisions | [ACCEPT / AMEND / REJECT / DEFER with exact wording] |
| Safe deferrals | [List and conditions] |
| Accepted exclusions | [Out-of-P0 scope and non-supported modes] |
| Freeze decision | [ACCEPT / ACCEPT WITH AMENDMENT / REJECT / DEFER] |
| Conditions / amendments | [Exact wording and affected documents] |
| Owner / date | [Attributable owner record] |
| Implementation authorization | NOT GRANTED unless separately issued. |

### 12.1 Separate implementation authorization template

| Field | Required entry |
| --- | --- |
| Authorization ID | [Unique ID] |
| Work package / scope | [Exact WP and deliverables] |
| Repository identity | [Exact repo and baseline] |
| Permitted inspection | [Paths and allowed read operations] |
| Permitted writes | [Exact file/path boundaries] |
| Tests | [Whether permitted; exact commands and scope] |
| Git operations | [Explicitly permitted actions; default none] |
| Agents | [Named agent, task, permissions and stop conditions] |
| Preservation rules | [All modified/untracked work protected] |
| Dependencies/environment/credentials | [Allowed or prohibited changes] |
| External effects | [Explicitly allowed or prohibited] |
| Budget/provider/deployment | [Explicit approval or prohibited] |
| Acceptance/QA | [Evidence and independent reviewer] |
| Stop-work conditions | [Triggers and reporting path] |
| Owner authorization | [Explicit attributable decision and date] |

## 13. Current status and next execution sequence

| Area | Current status | Next action |
| --- | --- | --- |
| Working ODR register | Located and read; complete working 22-row index. | Use as index; preserve derived/proposed status. |
| Original ODR row provenance | Not independently established for every ODR row; ODR-22 specifically provisional grouping. | Continue source mapping; do not claim original master provenance beyond evidence. |
| Accepted ADR/CF baseline | Source records located; acceptance routes recorded. | Carry forward unchanged. |
| RCN-01–RCN-11 | Reconciliation findings available. | Propagate accepted semantics into subordinate contract drafts. |
| FZ-01–FZ-21 | FZ-01/02 complete; remaining gates range from propagation/schema work to owner freeze. | Close in controlled order; keep deferrals explicit. |
| X-01–X-12 | Known cross-document backlog. | Resolve with source-backed contract appendices and owner disposition where required. |
| Detailed contract freeze | PENDING. | Requires consolidated package and explicit owner confirmation. |
| Implementation authorization | NOT GRANTED. | Separate later decision; not implied by freeze. |
| Independent QA / release | NOT YET DEMONSTRATED. | Use Batch 14 framework after authorized implementation and evidence creation. |

## 13.1 Recommended order

1. Finalize source/decision map and ODR provenance notes.

1. Close X-01/X-07 workflow-task-job ownership and cardinality.

1. Close X-02/X-03/X-09 artifact, manifest, transfer, integrity and lifecycle.

1. Close X-04/X-05 governance vocabulary, centralized authorization and emergency pause.

1. Close X-06 worker trust, credentials, revocation and isolation.

1. Close X-08 command/event envelope and compatibility.

1. Close X-10 E2E evidence and test oracle; carry X-11 provisional ODR-22 note; normalize X-12 statuses.

1. Update all WP contracts and module-to-contract traceability.

1. Prepare versioned consolidated freeze candidate and obtain explicit owner decision.

1. Only after freeze, request a separate bounded implementation authorization.

## 14. Final control statement

Batch 15 establishes the source-informed reconciliation baseline for NEXTDECODE P0. The working ODR-01–ODR-22 register is located and usable as a working index. Accepted ADR/CF decisions remain accepted under their recorded authority and acceptance routes. ODR-22 remains a provisional derived grouping because the inspected records do not verify a distinct accepted source decision with that combined ID and wording.

The detailed contract set is not frozen. The implementation gate remains separate and not granted. No repository, Git, test, agent, provider, spending, deployment, production generation, upload or publishing action is authorized by this dossier.

The next work is documentation-only closure of the identified source and contract gaps, with owner decisions requested only where the source register explicitly reserves authority or where a new material decision is genuinely required.


## Source document metadata (preserved from DOCX)

- **Header:** NEXTDECODE CONTENT OS  |  P0 CONTROLLED DELIVERY SERIES
- **Footer:** Batch 15 — Source Reconciliation & Contract Closure  •  Controlled design document

