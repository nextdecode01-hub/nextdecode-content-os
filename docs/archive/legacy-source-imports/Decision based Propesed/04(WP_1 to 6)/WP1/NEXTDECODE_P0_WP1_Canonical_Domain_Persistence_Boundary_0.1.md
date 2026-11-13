# NEXTDECODE — P0 WP-1 Canonical Domain & Persistence Boundary

**Document ID:** `NEXTDECODE_P0_WP1_Canonical_Domain_Persistence_Boundary_0.1`  
**Version:** 0.1  
**Status:** **DESIGN CANDIDATE — OWNER REVIEW REQUIRED**  
**Date:** 1 November 2026  
**Work package:** WP-1 — Canonical Domain and Persistence Foundation  
**Scope:** Minimum canonical model and persistence boundary needed by the P0 vertical slice  
**Authority:** Derived from existing NEXTDECODE architecture and contract sources; this document does not approve a final SQL schema or authorize implementation.

**Existing source documents used**
- `NEXTDECODE_Canonical_Data_Dictionary_Entity_Ownership_Registry_1.0.md`
- `NEXTDECODE_P0_Detailed_Contract_Freeze_Pack_1.0.md`
- `NEXTDECODE_Artifact_08_Implementation_Reference_Accepted_Contract_Decisions_1.0.md`
- `NEXTDECODE_Module_to_Contract_Traceability_Matrix_1.0.md`
- `NEXTDECODE_P0_Foundation_Implementation_Specification_1.0.md`
- `NEXTDECODE_P0_WP0_Final_Reconciliation_Closure_Record_1.0.md`
- Artifact 07 — P0 Foundation Execution Plan & Acceptance Framework

---

# 1. Purpose and boundary

WP-1 establishes the minimum canonical domain and persistence foundation required for the P0 vertical slice.

It must answer:
1. Which canonical records are required to represent one content item and variant?
2. Which domain owns each record?
3. How are canonical identity, immutable version identity and schema version distinguished?
4. Which typed relationships must be persisted and validated?
5. What minimum relational constraints protect ownership, scope and version integrity?
6. How can the system preserve existing Shorts Studio identifiers without treating them as competing canonical IDs?

This is a **bounded design candidate**, not a new master architecture plan and not a replacement for the Canonical Data Dictionary, Canonical Contracts Pack, Artifact 07 or Artifact 08.

## 1.1 Included in WP-1

- Canonical entity ownership and typed references for the first P0 vertical slice.
- UUIDv7 identity conventions.
- Entity identity versus version identity versus schema version.
- Minimum entity definitions and relationship constraints.
- Workspace/brand/content scope.
- Content item and content variant references.
- Workflow/task/job identity references needed to link the vertical slice, without implementing the scheduler.
- Artifact identity/version references sufficient for immutable linkage, without implementing the full transfer system.
- Persistence integrity, uniqueness and concurrency requirements.
- Legacy/external identifier preservation boundaries.
- Synthetic-data acceptance criteria for WP-1.

## 1.2 Explicitly outside WP-1

- Durable queue, scheduler, leases, retry and recovery implementation — WP-2.
- Worker registry, enrollment, credentials and capability verification — WP-3.
- Full artifact storage provider, transfer and quarantine implementation — WP-4.
- Full QA, rights, review, approval and central authorization enforcement — WP-5.
- End-to-end vertical-slice failure injection and recovery acceptance — WP-6.
- Cloud provider selection, deployment, paid services, public publishing or production data migration.
- Replacing or rewriting Shorts Studio.
- Broad migration of all existing local records.

---

# 2. Authority and status rules

Use these labels:

| Label | Meaning |
|---|---|
| **ACCEPTED** | Owner-accepted high-level direction; do not reopen without superseding decision. |
| **SOURCE-DEFINED** | Field/entity/relationship stated in an existing architecture source, but not necessarily final SQL approval. |
| **PROPOSED DETAIL** | WP-1 design recommendation that requires owner review. |
| **OPEN** | Must be specified before the affected implementation is authorized. |
| **DEFERRED** | Not needed to complete the WP-1 boundary; handled by a later work package. |

The accepted CF-01–CF-24 and ADR-001–ADR-010 records remain authoritative. This document does not create new accepted decisions.

---

# 3. Canonical identity and version rules

## 3.1 Canonical IDs — ACCEPTED

- UUIDv7 is the canonical identifier.
- IDs are globally unique, opaque, immutable and never reused.
- IDs do not encode mutable business meaning, status, platform or owner.
- Human-readable prefixes may be display/reference aliases only; they are not database identity substitutes.
- External platform IDs, legacy run IDs, file paths and provider object keys remain namespaced external references.

## 3.2 Identity dimensions — ACCEPTED

Keep these concepts distinct:

| Dimension | Meaning |
|---|---|
| Entity ID | Stable identity of the logical object |
| Entity version ID | Immutable identity of a specific revision |
| Schema version | Version of the record/contract shape and meaning |
| Artifact version | Exact immutable output revision |
| Execution attempt ID | One attempt to execute a job |
| Event/message ID | Identity of a notification/message |
| Idempotency key | Deduplication key with its own scope and retention |

A new entity version does not change the entity ID. A changed immutable artifact must not overwrite its previous bytes/version. Stale mutable-record updates must be rejected or safely reconciled.

## 3.3 Shared field conventions — SOURCE-DEFINED

The Canonical Data Dictionary specifies these conventions:
- `{entity}_id`: UUIDv7 canonical identity.
- `{entity}_version_id`: UUIDv7 or immutable version key.
- `workspace_id`: workspace scope.
- `brand_id` and `studio_id`: applicable scope references.
- `*_ref` / `*_refs`: typed canonical references.
- `lifecycle_status`: domain-owned lifecycle enum.
- `schema_version`: versioned contract identifier.
- `created_at` / `updated_at`: UTC timestamps.
- `created_by` / `updated_by`: actor references.
- `correlation_id`: trace identifier.
- `causation_id`: immediate triggering event/command, where applicable.
- `content_hash`: algorithm plus digest for integrity.

Avoid an unqualified generic `status` field when it could conflate lifecycle, epistemic, QA, authorization or external-operation state. Null, empty and unknown are distinct; missing business-critical values must not be inferred.

---

# 4. Canonical ownership boundary

The Module-to-Contract Traceability Matrix and Canonical Data Dictionary define the following ownership boundaries relevant to WP-1:

| Entity/domain | Canonical owner | WP-1 treatment |
|---|---|---|
| Workspace | Shared Data Model / Workspace layer | Include minimum workspace identity and scope |
| Actor | Identity and Security layer | Reference actor identity; do not create a parallel actor system |
| Brand / BrandIdentityVersion | Contract 03 | Store canonical brand reference; do not duplicate brand identity |
| ContentItem | Shared Content Graph | Include as canonical editorial identity |
| ContentVariant | Shared Content Graph / accepted CF-01 derivative | Include as format/platform/language/treatment derivative |
| Relationship | Shared Content Graph | Include typed relationship capability only where required |
| Workflow / WorkflowTask / Job / JobAttempt | Contract 10 + Parts 4/5/8 | Include minimum references and records needed to express vertical-slice lineage; execution behavior belongs to WP-2 |
| Worker | Contract 10 + Parts 4/5/8 | Reference only; registry implementation belongs to WP-3 |
| Artifact / Asset | Part 7, with Contract 07 governance | Include immutable identity/version references; full transfer/storage belongs to WP-4 |
| Opportunity / Evidence / Claim | Contract 02 | Reference only where content origin/evidence is present; do not duplicate ownership |
| QA / Rights / Approval / Authorization | Contract 07 | Reference only; enforcement implementation belongs to WP-5 |
| ProductionRun / StudioProduction | Contract 11 + Part 7 | Keep distinct from ContentItem, ContentVariant, WorkflowTask and Job |

**Ownership invariant:** A module may present, cache or reference an entity owned by another domain. It does not thereby become the canonical owner or gain write/authorization rights.

---

# 5. Minimum WP-1 entity set

This is the minimum logical set for the vertical slice. The detailed field lists below are source-derived or proposed as explicitly labelled. They are not a final SQL migration.

## 5.1 Workspace

**Owner:** Shared Data Model / Workspace layer.

**Purpose:** Top-level isolation and ownership boundary.

**SOURCE-DEFINED fields from the Canonical Data Dictionary**
- `workspace_id`
- `name`
- `workspace_type`
- `lifecycle_status`
- `owner_actor_ref`
- `default_classification_policy_ref`
- `default_retention_policy_ref`
- `created_at`
- `updated_at`
- `schema_version`

**OPEN:** Exact required/optional/nullability rules and whether policy references are in the first WP-1 persistence slice or represented as deferred typed references.

## 5.2 Brand reference

**Owner:** Contract 03.

WP-1 must not create a second canonical brand identity.

**SOURCE-DEFINED reference**
- `brand_id`
- `workspace_id`

The detailed freeze pack's P0 minimum model also proposes a simple Brand record with `name`, `status`, optional `brand_profile_ref`, and timestamps. The Canonical Data Dictionary defines the richer brand identity and version model under Contract 03.

**WP-1 rule:** Treat Brand as a Contract 03-owned entity. WP-1 stores a typed `brand_id` reference and validates workspace consistency. It must not create a competing Brand schema or own brand lifecycle transitions.

**OPEN:** Which Contract 03 fields are needed for the first vertical slice versus reference-only access.

## 5.3 ContentItem

**Owner:** Shared Content Graph.

**ACCEPTED meaning (CF-01):** Shared editorial/content identity independent of output format.

**SOURCE-DEFINED fields from the Canonical Data Dictionary**
- `content_item_id`
- `workspace_id`
- `brand_id`
- `origin_opportunity_id` (nullable)
- `primary_audience_refs`
- `editorial_pillar_refs`
- `content_type`
- `lifecycle_status`
- `current_content_version_id`
- `created_by`
- `created_at`
- `updated_at`
- `schema_version`

The Detailed Contract Freeze Pack also includes a P0 illustrative `title`, `source_idea_id` (nullable), `editorial_status`, `created_at` and `updated_at`. Those details must be reconciled with the accepted shared data dictionary and the entity owner before final schema approval.

**WP-1 boundary:** `ContentItem` is not a `StudioProduction`, render, distribution package or publication. It is the durable editorial identity.

**OPEN:** Final content version schema; title and source-idea field placement; lifecycle enum; required fields; audience/pillar reference representation.

## 5.4 Content version

**Purpose:** Immutable revision of a ContentItem.

The Canonical Data Dictionary specifies a distinct immutable version identity concept. `current_content_version_id` is referenced by ContentItem.

**PROPOSED minimum design:** A version record must have:
- its own immutable version identity;
- a reference to `content_item_id`;
- the versioned content payload or typed content reference;
- `schema_version`;
- creation actor and timestamp;
- integrity/hash reference where the payload requires it.

**OPEN:** The source material does not yet provide one reconciled final ContentVersion field schema or whether version labels are stored alongside UUIDv7 version IDs. Do not silently invent this as frozen.

## 5.5 ContentVariant

**Owner:** Shared Content Graph under accepted CF-01.

**ACCEPTED meaning:** A format/platform/language/treatment derivative of a ContentItem, not a new ContentItem.

**SOURCE-DEFINED fields from the Detailed Contract Freeze Pack's P0 minimum model**
- `content_variant_id`
- `content_item_id`
- `format`
- `platform_target` (nullable)
- `variant_status` (field name requires reconciliation with explicit lifecycle naming)
- `current_artifact_id` (nullable)
- `created_at`
- `updated_at`

**OPEN:** Whether language/treatment are separate typed fields or represented in a versioned variant profile; exact lifecycle vocabulary; immutable variant version requirements; whether current artifact pointer belongs on the variant or a production/release record.

## 5.6 Workflow

**Owner:** Contract 10 / orchestration domain.

**SOURCE-DEFINED proposed fields**
- `workflow_id`
- `workspace_id`
- `content_item_id` (nullable for non-content workflows)
- `workflow_type`
- `workflow_status`
- `definition_version`
- `created_at`
- `updated_at`
- `completed_at` (nullable)

WP-1 may persist the workflow identity and parent references needed for the vertical slice. Workflow scheduling, transition execution and recovery belong to WP-2.

## 5.7 WorkflowTask

**Owner:** Contract 10 / orchestration domain.

**SOURCE-DEFINED proposed fields**
- `task_id`
- `workflow_id`
- `task_type`
- `task_status`
- `dependency_task_ids`
- `required_capabilities`
- `input_refs`
- `result_refs`
- `created_at`
- `updated_at`

Rules from the Detailed Contract Freeze Pack:
- Workflow owns orchestration context.
- Task represents a logical step and dependency.
- Task is not a worker attempt.
- A task may create one or more jobs over its lifecycle, subject to retry/re-execution semantics.
- Workflow completion is not inferred from one job's success.

WP-1 only establishes the canonical identity/reference boundary; dependency scheduling belongs to WP-2.

## 5.8 Job and JobAttempt references

**Owner:** Contract 10 / orchestration domain.

The Detailed Contract Freeze Pack proposes:
- Job: `job_id`, `task_id`, `job_type`, `job_status`, `payload_schema_version`, `payload_ref` or validated payload, `required_capabilities`, `priority`, `eligible_at`, `idempotency_key`, `max_attempts`, timestamps.
- JobAttempt: `job_attempt_id`, `job_id`, `attempt_number`, nullable `worker_id`, `lease_token_hash`, `lease_expires_at`, `heartbeat_at`, `attempt_status`, start/finish timestamps, safe failure fields.

**WP-1 boundary:** Preserve the identity distinction `WorkflowTask ≠ Job ≠ JobAttempt`. WP-1 may define foreign-key/reference shapes required by the vertical slice, but job dispatch, lease, retry and attempt processing are WP-2 responsibilities.

## 5.9 Artifact reference

**Owner:** Part 7 Artifact & Asset Management; rights/provenance governance by Contract 07.

The source documents distinguish:
- `Asset`: source or reusable media resource.
- `Artifact`: immutable produced output.
- `artifact_id`: canonical output identity.
- artifact version: immutable exact revision.
- `content_hash`: algorithm plus digest.

The Detailed Contract Freeze Pack states that a new artifact does not overwrite historical artifact versions.

**WP-1 boundary:** Define the typed reference and immutable version linkage needed by ContentVariant/production output. Full binary storage, transfer, checksum verification workflow and quarantine belong to WP-4.

**OPEN:** Exact ArtifactVersion schema and whether `current_artifact_id` is a direct pointer or a version-specific reference. This must be reconciled with the Part 7 artifact contract.

## 5.10 External identifier mapping

External platform IDs, legacy Shorts Studio run IDs, file paths and provider object keys must remain external references, with source system/provider, external identifier/locator, related canonical entity, observed timestamp and optional metadata.

**WP-1 requirement:** Preserve source identifiers as references. Never use a legacy run ID, filename, filesystem path or provider object key as the canonical ID.

---

# 6. Minimum relationship model

The following relationships are stated in the existing Detailed Contract Freeze Pack or Canonical Data Dictionary. The WP-1 design should enforce only the relationships required by its approved slice.

| Parent / source | Child / target | Relationship | Status |
|---|---|---|---|
| Workspace | Brand | One workspace may contain one or more brands | SOURCE-DEFINED |
| Workspace | ContentItem | Content item belongs to explicit workspace scope | SOURCE-DEFINED |
| Brand | ContentItem | Content item belongs to explicit brand/workspace scope | SOURCE-DEFINED |
| ContentItem | ContentVariant | One item may have multiple variants | ACCEPTED / SOURCE-DEFINED |
| ContentItem | ContentVersion | One logical item may have immutable versions | ACCEPTED principle; detailed schema OPEN |
| Workflow | WorkflowTask | Workflow contains logical tasks and dependencies | SOURCE-DEFINED |
| WorkflowTask | Job | Task may create one or more jobs | SOURCE-DEFINED; execution semantics WP-2 |
| Job | JobAttempt | Job may have multiple retained attempts | SOURCE-DEFINED; execution semantics WP-2 |
| Worker | JobAttempt | Attempt records executing worker identity | SOURCE-DEFINED; registry WP-3 |
| ProductionRun | Artifact | Production run may produce multiple immutable artifacts | SOURCE-DEFINED; full model WP-4/11 |
| ContentVariant | Artifact reference | Variant may point to current output artifact | PROPOSED in detailed pack; final ownership OPEN |
| Canonical entity | Relationship | Typed source/target relationship | SOURCE-DEFINED |

**Relationship invariants**
- Foreign references must resolve to the correct canonical entity type.
- Workspace-scoped relationships must not cross workspace boundaries implicitly.
- Invalid or unauthorized cross-workspace links are rejected.
- Relationships do not grant access, ownership, approval or authorization.
- Historical lineage and required audit evidence must be preserved.
- A read model or graph projection is not an alternate canonical owner.

---

# 7. Persistence boundary and integrity requirements

## 7.1 Accepted direction

- PostgreSQL-compatible relational database is the authoritative shared-state store (ADR-002).
- The logical application may remain modular; domain ownership does not require one microservice per entity.
- Canonical records and relationships must be persisted in the authoritative store.
- Read models/caches are not authoritative.
- Binary artifacts sit behind a storage abstraction; WP-1 does not select a provider.
- Schema and API contracts are versioned.

## 7.2 WP-1 proposed persistence requirements

The WP-1 design must specify and later test:
1. Primary-key uniqueness for canonical UUIDv7 IDs.
2. Foreign-key integrity for typed canonical references.
3. Workspace/brand scope consistency.
4. Unique constraints for any source-system external reference within its declared namespace.
5. Immutable identity fields.
6. Version records that cannot be silently overwritten.
7. Concurrency-safe updates for mutable records.
8. Rejection or reconciliation of stale entity-version updates.
9. Required-field and nullability validation at service boundary and persistence boundary where applicable.
10. UTC timestamp handling.
11. Explicit schema-version storage.
12. Referential integrity for content item/variant and workflow/task relationships.

**OPEN:** Exact table names, column types, indexes, uniqueness scopes, delete actions, partitioning, isolation levels and ORM conventions. These must be decided in the WP-1 detailed schema review; they are not frozen here.

## 7.3 Deletion and archival

Accepted CF-06 principles:
- Archival, logical deletion and physical deletion are distinct.
- Deletion is dependency-aware and policy-controlled.
- Historical lineage, approval evidence and required audit records are preserved.
- Local deletion does not imply external-platform deletion.

**WP-1 boundary:** Do not implement physical deletion or broad cleanup as part of initial schema creation. Define safe referential behavior and defer full retention/deletion execution to the relevant governance work.

---

# 8. Scope and compatibility with existing Shorts Studio

WP-1 must preserve the existing engine boundary.

- Existing Shorts Studio remains a specialized Python/FFmpeg engine behind a bounded adapter.
- Legacy run IDs, file paths and internal identifiers are external/source references.
- New canonical IDs must be mapped to existing source identifiers without rewriting or deleting legacy data.
- A production run is not a ContentItem or ContentVariant.
- An artifact is not an Asset.
- WorkflowTask is not Job; Job is not JobAttempt.
- WP-1 must not modify current Shorts Studio files or perform a data migration without separate authorization.

**OPEN:** Exact mapping table shape and source identifier namespace must be decided after the read-only baseline/adapter contract is separately authorized and verified. WP-1 design may define the requirement but cannot assume unverified repository fields.

---

# 9. WP-1 acceptance criteria

These are proposed acceptance criteria derived from the existing P0 vertical-slice and acceptance framework. They are not executed test evidence.

| ID | Acceptance check | Expected result |
|---|---|---|
| WP1-ID-01 | Create Workspace with canonical UUIDv7 | Valid immutable canonical ID |
| WP1-ID-02 | Create Brand reference under Workspace | Brand owner remains Contract 03; workspace scope validates |
| WP1-ID-03 | Create ContentItem | Required fields and owner/scope validate |
| WP1-ID-04 | Create two ContentVariants for one ContentItem | Both reference same item; variants remain distinct |
| WP1-ID-05 | Create ContentVersion | Version identity distinct from ContentItem ID; previous version immutable |
| WP1-ID-06 | Attempt duplicate canonical ID | Rejected |
| WP1-REL-01 | Create valid typed relationship | Accepted and traceable |
| WP1-REL-02 | Create wrong-type or missing target reference | Rejected |
| WP1-REL-03 | Create unauthorized cross-workspace link | Rejected |
| WP1-SCOPE-01 | Create ContentItem with mismatched Brand/Workspace | Rejected |
| WP1-VER-01 | Submit stale mutable-record version update | Rejected or safely reconciled |
| WP1-VER-02 | Update immutable version payload in place | Rejected |
| WP1-EXT-01 | Attach legacy/source ID as external reference | Preserved without replacing canonical ID |
| WP1-PER-01 | Restart the persistence process in controlled test | Canonical records and relationships persist |
| WP1-PER-02 | Reconstruct entity relationships from stored references | Same authoritative links returned |
| WP1-DEL-01 | Attempt unapproved physical deletion | Denied/not exposed in WP-1 scope |

**Acceptance evidence must include:** approved schema/contract version, test identifiers, execution environment, commands, sanitized output, pass/fail/not-run counts, limitations and reviewer disposition. Tests are not to be run until separately authorized.

---

# 10. Open decisions for owner review

The following are the minimum genuinely open WP-1 design questions. No question here reopens accepted CF/ADR decisions.

| ID | Open question | Recommended handling |
|---|---|---|
| WP1-O-01 | Which ContentItem fields from the Canonical Data Dictionary and Detailed Contract Freeze Pack are required in the first vertical slice? | Reconcile with Contract 02/03 references and owner entity definition; do not duplicate fields blindly |
| WP1-O-02 | What is the final ContentVersion schema and version-ID convention? | Specify immutable version identity separately from entity ID and schema version |
| WP1-O-03 | Are `title` and source-idea fields on ContentItem, ContentVersion, or a separate ContentIdea relation? | Resolve against canonical contracts; preserve ContentIdea ≠ ContentItem |
| WP1-O-04 | What is the final ContentVariant version/profile structure for format, platform, language and treatment? | Use typed fields/profile references; do not overload one string without contract support |
| WP1-O-05 | Where does the current artifact pointer belong: ContentVariant or a production/release record? | Reconcile Part 7 and Contract 11 ownership before final schema |
| WP1-O-06 | Which workflow/task/job references must be physically persisted in WP-1 versus only defined as typed contract references? | Keep WP-1 minimal; execution behavior remains WP-2 |
| WP1-O-07 | What is the approved external-ID mapping shape for legacy Shorts Studio identifiers? | Design requirement now; final mapping requires authorized baseline evidence |
| WP1-O-08 | What are the exact foreign-key delete/update actions and archival semantics for the first schema? | Preserve lineage; no physical deletion in initial WP-1 slice |
| WP1-O-09 | Which schema migration and rollback tooling is allowed in the eventual approved environment? | Defer until implementation authorization and environment constraints are known |

The owner may accept a conservative proposed resolution or explicitly defer any question that is not needed for the first vertical slice. Deferral must be recorded in the existing Artifact 10 decision process, not silently assumed.

---

# 11. Dependencies and exit gate

## Dependencies
- Accepted ADR-001 and ADR-002.
- Accepted CF-01 through CF-06 and the other relevant accepted invariants.
- Canonical Data Dictionary and Entity Ownership Registry.
- Canonical Contracts Pack and Shared Intelligence Core Contracts 01–12.
- Module-to-Contract Traceability Matrix.
- Artifact 07 P0 sequence and acceptance framework.
- Artifact 10 owner-review and authorization process.
- WP-0 preservation and gap register plus WP-0 closure addendum.

## WP-1 design exit gate

WP-1 design is ready for owner review when:
- canonical owners are confirmed against the source contracts;
- minimum entity and relationship scope is explicit;
- entity/version/schema identities are distinct;
- ContentItem and ContentVariant boundaries are unambiguous;
- workflow/task/job/artifact references are bounded to the vertical slice;
- persistence integrity and concurrency requirements are stated;
- legacy identifier preservation is explicit;
- open questions are resolved or recorded as deferred;
- acceptance criteria are traceable to Artifact 07.

Passing this design gate does not authorize implementation.

## Separate implementation authorization required

Before repository modifications, Git operations, tests, dependency installation, environment/credential changes or agent assignment, the owner must issue a separate bounded authorization through Artifact 10, specifying:
- exact scope and permitted actions;
- repository/path boundaries;
- responsible engineering owner;
- preservation constraints;
- environment and test restrictions;
- allowed commands and prohibited operations;
- evidence/reporting requirements;
- stop conditions.

No provider activation, paid services, deployment, production generation, upload or publishing is included.

---

# 12. Plain-language explanation

WP-1 is the foundation for remembering what each thing in NEXTDECODE actually is.

A **ContentItem** is the core editorial idea. A **ContentVariant** is one version of how that idea is adapted for a format, platform, language or treatment. A **ProductionRun** is one time the production engine works on it. An **Artifact** is an actual output file. These must not be confused or assigned duplicate identities.

The database becomes the authoritative place for shared records and their relationships. Existing Shorts Studio IDs and files are preserved and linked as external/source references; they are not wiped out or renamed.

We are defining the smallest reliable model needed for one controlled end-to-end test—not building all twelve modules or implementing the queue, workers, publishing and governance in one step.

---

**WP-1 status: DESIGN CANDIDATE — OWNER REVIEW REQUIRED**  
**WP-1 implementation: NOT AUTHORIZED**  
**Next gate: Resolve WP1-O-01 to WP1-O-09 or record safe deferrals in Artifact 10.**
