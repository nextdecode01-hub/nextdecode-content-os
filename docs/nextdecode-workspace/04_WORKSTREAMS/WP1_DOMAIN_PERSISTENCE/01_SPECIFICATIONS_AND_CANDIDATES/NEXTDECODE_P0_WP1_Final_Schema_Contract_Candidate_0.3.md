# NEXTDECODE — P0 WP-1 Final Schema Contract Candidate

**Document ID:** `NEXTDECODE_P0_WP1_Final_Schema_Contract_Candidate_0.3`  
**Version:** 0.3  
**Date:** 1 November 2026  
**Work package:** WP-1 — Canonical Domain and Persistence Foundation  
**Status:** **CONSOLIDATED DESIGN CANDIDATE — OWNER REVIEW REQUIRED**  
**Implementation status:** Not authorized

## 1. Purpose

This document consolidates WP-1 v0.1 and the v0.2 Design Resolution Record into one reviewable logical schema contract candidate. It defines the minimum canonical records and persistence boundaries needed to support the P0 vertical slice without freezing unresolved physical-schema details.

It is subordinate to, and must remain consistent with:
- `NEXTDECODE_Canonical_Data_Dictionary_Entity_Ownership_Registry_1.0.md`
- `NEXTDECODE_API_Event_Contract_Standard_1.0.md`
- `NEXTDECODE_Unified_Lifecycle_State_Transition_Standard_1.0.md`
- `NEXTDECODE_P0_Foundation_Implementation_Specification_1.0.md`
- Artifact 08 accepted contract decisions and the WP-1 v0.1/v0.2 records.

This is a logical contract candidate, not SQL DDL, an ORM specification, migration plan, or implementation authorization.

## 2. Decision-status legend

- **Accepted baseline** — explicitly accepted architecture decision or established by an authoritative source document.
- **Source-defined** — defined in an existing architecture/contract source; preserve its semantics.
- **Recommended default** — conservative design recommendation for owner review; not yet an accepted owner decision.
- **Open** — requires a later contract decision or detailed design.
- **Deferred** — deliberately outside WP-1.

Do not interpret a recommended default as a frozen requirement.

## 3. Non-negotiable architecture constraints

1. Internal canonical entity IDs use immutable UUIDv7 values; IDs are never reused.
2. Entity identity, immutable content/version identity and schema version are distinct concepts.
3. Every canonical entity has one authoritative owning domain.
4. Typed references do not imply access, ownership, approval or authorization.
5. Domain state machines remain separate; do not create a universal status field.
6. Only the owning domain commits its authoritative state transitions.
7. Queries are read-only; commands request changes; events report committed facts.
8. Events and transition history are immutable; corrections create new attributable records.
9. Workspace scope is explicit and cross-workspace references are rejected unless separately authorized.
10. Shorts Studio remains a specialised engine behind a bounded adapter; WP-1 does not replace it.
11. No provider, deployment, paid infrastructure, production migration, generation, upload or publishing is authorized by this document.

## 4. Logical persistence model

### 4.1 Workspace

**Owner:** Workspace / Shared Data Model layer.  
**Status:** Source-defined.

Purpose: top-level isolation boundary.

Canonical logical fields:
- `workspace_id` — UUIDv7 primary identity
- `name`
- `workspace_type`
- `lifecycle_status` — workspace-owned vocabulary
- `owner_actor_ref` — typed actor reference
- `default_classification_policy_ref`
- `default_retention_policy_ref`
- `created_at`, `updated_at` — UTC timestamps
- `schema_version`

Rules:
- Every tenant-scoped record belongs to exactly one workspace.
- Membership and access are governed separately by identity/security policy.
- No implicit cross-workspace retrieval, linking or learning.

### 4.2 Brand reference

**Owner:** Contract 03 — Brand & Editorial Intelligence.  
**Status:** Source-defined.

WP-1 stores a canonical `brand_id` reference on applicable records. It does not create a competing brand identity table or duplicate the brand definition. Brand identity and studio identity versions remain owned by Contract 03.

### 4.3 ContentItem

**Owner:** Shared Content Graph.  
**Status:** Source-defined.

Purpose: canonical editorial/content concept, independent of format-specific production.

Canonical logical fields:
- `content_item_id` — UUIDv7
- `workspace_id`
- `brand_id`
- `origin_opportunity_id` — nullable typed reference
- `primary_audience_refs`
- `editorial_pillar_refs`
- `content_type`
- `lifecycle_status` — ContentItem lifecycle only
- `current_content_version_id` — nullable exact-version pointer
- `created_by`, `created_at`, `updated_at`
- `schema_version`

Rules:
- A ContentItem is not a ContentIdea, StudioProduction, render, distribution package or publication.
- It represents the shared editorial subject or initiative.
- Format derivatives reference the ContentItem and retain independent production and QA histories.
- Origin opportunity is optional; the source identity remains owned by Contract 02.

### 4.4 ContentVersion

**Owner:** Shared Content Graph.  
**Status:** Required logical concept; exact field schema is a recommended design pending owner review.

Purpose: immutable editorial revision belonging to one ContentItem.

Minimum logical fields recommended:
- `content_version_id` — immutable UUIDv7/version identity
- `content_item_id` — parent ContentItem
- `version_number` — monotonically increasing within the ContentItem
- `title` and/or versioned editorial payload reference
- `editorial_payload_ref` — optional reference if payload is stored separately
- `change_summary` — optional
- `created_by`, `created_at`
- `schema_version`

Rules:
- A ContentItem's stable identity does not change when its editorial content changes.
- A ContentVersion is immutable once committed.
- `current_content_version_id` is a convenience pointer to one exact version; it is not the version itself.
- Do not conflate content version identity with entity schema version.
- The exact content payload shape, title placement, and whether payload is inline or separately referenced remain open.

### 4.5 ContentVariant

**Owner:** Multiformat Creation / Contract 11 for format-native production identity; shared Content Graph owns the editorial relationship.  
**Status:** Accepted semantic baseline; exact schema open.

Purpose: a format/platform/language/treatment derivative of a ContentItem.

Minimum logical identity and references recommended:
- `content_variant_id` — UUIDv7
- `workspace_id`
- `content_item_id`
- `variant_definition_version_id` or explicit versioned profile reference
- format dimension
- platform dimension, where applicable
- language dimension
- treatment/creative-approach dimension
- `lifecycle_status` — variant-owned lifecycle
- audit fields and `schema_version`

Rules:
- ContentVariant is not a second ContentItem.
- Each variant may have independent production, QA and review history.
- Exact controlled vocabularies, nullability, uniqueness and profile-version model remain open.
- A variant's optional current-output pointer must refer to an exact ArtifactVersion and must not become a competing artifact owner.

### 4.6 Relationship

**Owner:** Shared Content Graph.  
**Status:** Source-defined.

Canonical logical fields:
- `relationship_id` — UUIDv7
- `workspace_id`
- `source_entity_type`, `source_entity_id`
- `relationship_type`
- `target_entity_type`, `target_entity_id`
- `valid_from`, `valid_to`
- `created_by`, `created_at`
- `schema_version`

Rules:
- Relationship types are controlled and versioned.
- Cross-workspace links are rejected unless a separately approved sharing mechanism applies.
- Relationships do not grant access or ownership.
- Polymorphic references require owner-side validation because a conventional single-column foreign key cannot validate every target type.

### 4.7 Workflow and WorkflowTask

**Owner:** Orchestration layer.  
**Status:** Required logical concepts for P0; detailed schema and state transitions open.

Workflow minimum logical fields:
- `workflow_id` — UUIDv7
- `workspace_id`
- `workflow_type` and `workflow_definition_version`
- `subject_entity_type`, `subject_entity_id`
- `lifecycle/execution state` as separately named domain-owned concepts
- `created_by`, `created_at`, `updated_at`
- `schema_version`

WorkflowTask minimum logical fields:
- `workflow_task_id` — UUIDv7
- `workflow_id`
- `task_type` and `task_definition_version`
- `subject_entity_type`, `subject_entity_id`, where applicable
- dependency references to other tasks
- task-owned execution state
- input/output references
- audit and schema-version fields

Rules:
- The orchestrator owns workflow progression, not the authoritative lifecycle of ContentItem, Artifact, QA, rights, approval or publication entities.
- Task dependencies must be explicit and validated.
- Detailed transitions, retry semantics, lease/attempt fields and scheduler behavior belong to WP-2.
- Whether a physical `Job`/`JobAttempt` record is required in the WP-1 vertical-slice schema is deferred to WP-2 boundary design.

### 4.8 Artifact and ArtifactVersion

**Owner:** Part 7 — Artifact & Asset Management, with Contract 07 rights/provenance governance.  
**Status:** Source-defined.

Artifact logical fields:
- `artifact_id` — UUIDv7
- `workspace_id`
- `artifact_type`
- `owner_entity_type`, `owner_entity_id`
- `current_artifact_version_id`
- `classification`
- `lifecycle_status`
- `created_by`, `created_at`
- `schema_version`

ArtifactVersion logical fields:
- `artifact_version_id` — immutable UUIDv7/version identity
- `artifact_id`
- `version_number`
- `storage_ref`
- `content_hash`
- `media_type`
- `size_bytes`
- `metadata`
- `created_by`, `created_at`
- `parent_artifact_version_refs`, where applicable
- `schema_version`

Rules:
- Artifact is the stable logical record; ArtifactVersion identifies exact immutable bytes/content.
- A material change creates a new ArtifactVersion; never overwrite an existing version in place.
- Relational metadata is authoritative; binary storage remains behind an abstraction.
- Asset and Artifact are distinct concepts. Do not merge their identities.
- Storage provider, retention periods, transfer protocol, quarantine implementation and binary lifecycle are WP-4 or later.
- A StudioProduction records artifact references; it does not become the artifact owner.

### 4.9 StudioProduction compatibility boundary

**Owner:** Contract 11 — Multiformat Creation.  
**Status:** Source-defined.

Contract 11's StudioProduction record includes references such as:
- `studio_production_id`
- `creation_project_id`
- `content_item_id`
- studio and profile version references
- `workflow_run_id`
- `artifact_refs`
- QA/rights references
- `lifecycle_status`

WP-1 must preserve this boundary:
- StudioProduction is a production record, not the canonical ContentItem.
- It references immutable brand/studio/profile versions and exact artifacts.
- Shorts Studio remains the specialised engine integrated through an adapter.
- Existing Shorts Studio IDs are retained as namespaced external/legacy references; they do not become competing canonical IDs.

### 4.10 External and legacy references

**Status:** Recommended default.

Use a namespaced reference mapping concept where needed:
- `external_ref_id` — internal UUIDv7 for the mapping record
- `workspace_id`
- `canonical_entity_type`, `canonical_entity_id`
- `external_system`
- `external_entity_type`
- `external_id`
- optional `external_uri`
- `observed_at`, `created_at`
- provenance/verification metadata

Rules:
- External identifiers are never substituted for canonical IDs.
- Namespaces prevent collisions between providers and local systems.
- Preserve legacy IDs and source paths for traceability.
- Whether the mapping is one-to-one, one-to-many or temporal must be defined by the specific integration contract.

## 5. Relationship overview

```text
Workspace
  ├── Brand reference (owned by Contract 03)
  ├── ContentItem
  │     ├── ContentVersion [immutable revisions]
  │     ├── ContentVariant [format/platform/language/treatment derivative]
  │     ├── Relationship [typed links to other canonical entities]
  │     └── StudioProduction [Contract 11 production record]
  │              └── Artifact references
  │                     └── Artifact
  │                            └── ArtifactVersion [immutable output]
  └── Workflow
         └── WorkflowTask [dependencies and execution references]
```

This is a logical relationship view, not a final physical table diagram. Cross-domain links are validated through the owning contract/API; the diagram does not authorize direct cross-domain writes.

## 6. Persistence and integrity requirements

### 6.1 Identity and version integrity

- Canonical IDs are UUIDv7 and immutable.
- Version IDs are distinct from parent entity IDs.
- Enforce uniqueness of `(parent_entity_id, version_number)` where a sequential version number is used.
- Exact-version references must resolve to an existing version owned by the referenced entity.
- Current-version pointers must reference a version belonging to the same parent entity.
- Schema version is metadata about record shape/meaning, not a content revision.

### 6.2 Scope integrity

- Every tenant-scoped row carries `workspace_id` or is unambiguously scoped through an immutable parent.
- Parent-child references must remain within the same workspace.
- Cross-workspace relationships fail closed absent a separately approved sharing model.
- Authorization is not inferred from database reachability or a relationship record.

### 6.3 Ownership integrity

- Each canonical entity has one authoritative owner.
- A consumer may hold a projection/cache but cannot write authoritative state directly.
- Query, command and event semantics remain distinct.
- The owning domain validates commands, commits transitions and publishes authoritative events.

### 6.4 Lifecycle and audit integrity

- Do not use a generic `status` column for unrelated meanings.
- Keep lifecycle, execution, quality, rights, approval, authorization and external-operation outcomes distinct.
- Every committed state transition creates an immutable audit/event record.
- A mutable current-state projection may exist but must be reconstructible or reconcilable from transition history.
- Optimistic concurrency uses an expected state version or equivalent conditional token.
- Idempotency is required for retriable commands.

### 6.5 Deletion and retention

**Recommended default — owner review required:**
- Avoid cascading deletion across canonical lineage.
- Prefer restrictive references or explicit archival/tombstone lifecycle handling.
- Never silently delete workflow history, production records, artifacts, artifact versions, approvals or governance evidence as a side effect of deleting a parent.
- Legal/privacy deletion and retention rules require a separately defined policy and controlled workflow.
- Exact FK `ON DELETE` actions are not frozen here.

### 6.6 Indexes and constraints

Recommended logical constraints for later physical design:
- unique primary key for every canonical ID;
- unique version number per parent where applicable;
- indexes on `workspace_id`, parent IDs, exact-version pointers and common lookup references;
- composite integrity checks to prevent cross-workspace parent-child links;
- unique namespaced external identity where provider semantics guarantee uniqueness;
- bounded and validated relationship types;
- explicit foreign-key strategy for typed/polymorphic references.

Exact index names, SQL types, partial indexes, nullability, partitioning and database-specific features remain open.

## 7. API and event boundary

The API/Event Contract Standard remains authoritative:
- Query API: read-only authorized view.
- Command API: requests a state change or work from its owner.
- Event: reports a committed fact.
- Each API/event has one owning domain.
- Consumers must not write directly into another domain's tables.
- Versioned HTTP/JSON with schema validation is the architecture baseline.
- Events use the common lifecycle envelope and are delivered at least once; consumers must be idempotent.
- State update and outbox record are committed atomically where the outbox pattern applies.

WP-1 defines logical records and ownership; endpoint inventory, exact event catalogue and payload schemas are separate contract work.

## 8. Open decisions — explicitly not frozen

| ID | Open item | Safe handling in this candidate |
|---|---|---|
| O-01 | Full ContentItem title/editorial payload placement | Preserve dictionary fields; treat title/payload as versioned editorial data pending owner resolution |
| O-02 | Complete ContentVersion schema | Keep immutable version identity distinct; defer exact payload schema |
| O-03 | ContentIdea to ContentItem conversion/lineage | Keep ContentIdea distinct; use nullable typed origin reference where applicable |
| O-04 | ContentVariant controlled dimensions and profile versioning | Preserve derivative semantics; defer exact vocabularies and constraints |
| O-05 | Variant-to-output ArtifactVersion relationship | Use exact-version reference if needed; defer canonical link ownership and cardinality |
| O-06 | WorkflowTask versus Job/JobAttempt physical boundary | Workflow/task in WP-1; scheduler, lease and attempt schema in WP-2 |
| O-07 | External-reference cardinality and verification lifecycle | Use namespaced mapping as a recommendation; defer exact schema |
| O-08 | Exact FK actions and archival/tombstone mechanics | Restrictive/no-cascade is recommended; no SQL action frozen |
| O-09 | Legacy data migration tooling and mapping | Deferred; preserve identifiers and lineage only |
| O-10 | Exact SQL types, nullability, uniqueness, indexes and constraints | Defer to physical schema review after owner approval |
| O-11 | Exact lifecycle vocabularies and transition tables for new WP-1 entities | Do not invent; use owning domain contract and later transition design |
| O-12 | Database engine/provider and deployment topology | Not selected; no provisioning authorized |

## 9. WP-1 acceptance criteria candidate

WP-1 may be considered ready for implementation review only when the owner approves the logical model and the implementation design demonstrates:

1. One Workspace-scoped ContentItem with a stable UUIDv7 identity.
2. At least one immutable ContentVersion linked to that ContentItem.
3. At least one ContentVariant referencing the same ContentItem without duplicating its identity.
4. Typed relationship validation that rejects invalid/cross-workspace links.
5. A Workflow and dependent WorkflowTask reference the canonical subject without owning its lifecycle.
6. Artifact and ArtifactVersion are represented separately; an exact immutable version can be referenced by a production record.
7. Version identity, entity identity and schema version are demonstrably distinct.
8. Authoritative ownership boundaries prevent direct cross-domain state writes.
9. State transition history is attributable and versioned where the relevant state machine is in scope.
10. Existing Shorts Studio identifiers can be mapped without replacing or deleting source records.

These are proposed acceptance criteria, not evidence that they have been implemented or tested.

## 10. Explicit exclusions and safety boundary

This candidate does not authorize:
- repository inspection or modification;
- SQL migrations, ORM models or schema deployment;
- Git operations;
- dependency installation or environment/credential changes;
- agent execution or delegation;
- provider selection, connection or provisioning;
- paid services or charge-generating infrastructure;
- production generation, uploads or publishing;
- data migration or destructive cleanup.

WP-2 owns durable jobs, leases, retries and recovery. WP-3 owns worker registration/trust/capabilities. WP-4 owns artifact transfer/storage implementation. WP-5 owns QA/rights/governance enforcement. WP-6 owns end-to-end integration and recovery validation.

## 11. Review and exit gate

**Current status:** Consolidated design candidate — owner review required.

WP-1 design may move to an owner-approved baseline only after:
- the owner reviews the recommended defaults and open-decision table;
- any rejected recommendation is recorded with its replacement;
- the logical model is reconciled against the canonical data dictionary and Contract 11;
- the physical schema design is separately prepared and reviewed;
- implementation authorization is explicitly granted as a separate decision.

Approval of this document alone must not be interpreted as authorization for code changes, migrations, deployment or production activity.

## 12. Plain-language explanation

Think of this as NEXTDECODE's record-keeping blueprint:

- **ContentItem** is the main idea/editorial subject.
- **ContentVersion** is a frozen revision of that subject's actual editorial material.
- **ContentVariant** is a specific adaptation, such as a Short in a particular language or platform format.
- **StudioProduction** records a production run; it does not replace the content identity.
- **Artifact** is the logical output record; **ArtifactVersion** identifies the exact immutable file/output.
- **Workflow** coordinates the process; it does not take ownership of every business record it touches.
- **Workspace** keeps records inside the correct isolation boundary.

The key benefit: one content identity can move through research, creation, review and distribution without every module inventing its own competing copy or status.
