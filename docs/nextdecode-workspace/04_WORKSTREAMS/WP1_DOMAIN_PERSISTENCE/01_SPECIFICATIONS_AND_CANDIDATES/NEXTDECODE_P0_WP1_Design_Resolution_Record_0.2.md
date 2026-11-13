# NEXTDECODE — P0 WP-1 Design Resolution Record

**Document ID:** `NEXTDECODE_P0_WP1_Design_Resolution_Record_0.2`  
**Version:** 0.2  
**Date:** 1 November 2026  
**Status:** **RECOMMENDED DESIGN RESOLUTIONS — OWNER REVIEW REQUIRED**  
**Parent:** `NEXTDECODE_P0_WP1_Canonical_Domain_Persistence_Boundary_0.1.md`  
**Scope:** Resolve or safely defer WP1-O-01 through WP1-O-09 using existing architecture sources.

## 1. Purpose

This is a focused resolution addendum to WP-1 v0.1. It does not recreate the architecture or replace the existing Canonical Data Dictionary, Canonical Contracts Pack, API & Event Contract Standard, Part 7 artifact model, Contract 11 creation model, Artifact 07 or Artifact 08.

The source review confirms several previously open questions can now be narrowed using existing source definitions. Other details remain genuinely unspecified and must stay open rather than being invented.

### Status labels

- **Source-resolved:** the existing source documents already establish the principle or entity boundary.
- **Recommended:** a conservative design recommendation derived from the sources; owner review is still required.
- **Deferred:** deliberately outside WP-1 or not needed for its minimum exit.
- **Open:** source material does not settle the question; do not treat a recommendation as accepted.

## 2. Resolution matrix

| ID | Topic | Resolution | Status |
|---|---|---|---|
| WP1-O-01 | ContentItem fields | Canonical Data Dictionary is the ownership/field baseline. Keep ContentItem as editorial identity; use typed refs for opportunity, audience and editorial pillars. Reconcile `title` and source-idea details as below. | Recommended |
| WP1-O-02 | ContentVersion | Keep entity ID, immutable version ID and schema version distinct. The source establishes this separation but does not provide a complete ContentVersion schema. | Principle source-resolved; schema open |
| WP1-O-03 | Title and source idea | Preserve `ContentIdea ≠ ContentItem`. Do not merge them. Recommend title/content payload be versioned with the editorial revision; retain the source idea as a nullable typed origin reference. | Recommended |
| WP1-O-04 | ContentVariant profile/version | A variant is a format/platform/language/treatment derivative. Recommend explicit typed dimensions and immutable variant revision identity; exact profile contract remains open. | Meaning source-resolved; details recommended/open |
| WP1-O-05 | Artifact pointer | Part 7 defines Artifact and ArtifactVersion; Contract 11 StudioProduction carries `artifact_refs`. Recommend production/artifact lineage be authoritative and any variant “current output” pointer be a derived convenience reference only. | Ownership source-resolved; exact pointer open |
| WP1-O-06 | Workflow/task/job persistence | Keep Workflow and WorkflowTask as WP-1 logical records/references. Job and JobAttempt execution semantics belong to WP-2; WP-1 defines their identity boundary only. | Recommended |
| WP1-O-07 | Legacy external IDs | Store legacy run IDs, paths and provider IDs as namespaced external references, never canonical IDs. Recommend a generic external-reference relation with uniqueness scoped by source system/type. | Principle source-resolved; exact table open |
| WP1-O-08 | FK delete/archive behavior | Preserve lineage and audit. Recommend restrictive FK behavior for canonical/history records; no cascade deletion of workflows, runs, artifacts or approvals. Archival/logical deletion policy remains governed separately. | Principles source-resolved; exact SQL actions recommended |
| WP1-O-09 | Migration tooling | Not specified by current sources and not needed to finish WP-1 logical design. Defer tooling selection until implementation authorization and environment constraints are approved. | Deferred |

## 3. Detailed resolutions

### 3.1 WP1-O-01 — ContentItem minimum fields

**Source basis**
- The Canonical Data Dictionary defines `ContentItem` as owned by the Shared Content Graph.
- Its canonical fields include `content_item_id`, `workspace_id`, `brand_id`, nullable `origin_opportunity_id`, `primary_audience_refs`, `editorial_pillar_refs`, `content_type`, `lifecycle_status`, `current_content_version_id`, creator/timestamps and `schema_version`.
- The Detailed Contract Freeze Pack's illustrative P0 model additionally lists `title`, `source_idea_id` and `editorial_status`.
- Accepted CF-01 says ContentItem is the shared editorial identity, not a format-specific output.

**Recommended WP-1 treatment**
1. Use the Canonical Data Dictionary as the owner/field baseline.
2. Do not introduce a second editorial status field if it duplicates `lifecycle_status`.
3. Keep `origin_opportunity_id` as a typed reference to Contract 02.
4. Keep audience and editorial-pillar links as typed references; do not copy audience or brand records into ContentItem.
5. Keep title/content revision data versioned rather than silently overwriting an approved editorial revision.
6. Treat `source_idea_id` as a nullable origin reference only if the existing ContentIdea contract confirms that relationship.

**Still open:** final requiredness/nullability for each field; exact reference storage representation; whether a title is duplicated as a current-version projection for efficient listing.

### 3.2 WP1-O-02 — ContentVersion

**Source basis**
- Canonical Data Dictionary distinguishes stable entity identity from immutable version identity.
- ContentItem contains `current_content_version_id`.
- Accepted CF-04 separates entity ID, entity version, schema version, artifact version and execution attempt.
- The available source material does not define a complete, authoritative ContentVersion field list.

**Recommended minimum logical contract**
- `content_version_id` — immutable version identity.
- `content_item_id` — owning ContentItem.
- versioned content payload or typed payload reference.
- `schema_version`.
- `created_by`, `created_at`.
- optional integrity hash where exact content bytes/payload integrity needs verification.

Do not freeze a version-numbering scheme, payload format, JSON structure or title placement based on this recommendation alone.

**Disposition:** the identity principle is source-resolved; the detailed schema remains open for owner review.

### 3.3 WP1-O-03 — ContentIdea and title placement

**Source basis**
- The Detailed Contract Freeze Pack explicitly distinguishes ContentIdea from ContentItem.
- It states an idea may produce one or more ContentItems.
- ContentItem is the durable editorial identity; ContentVariant is a format/platform adaptation.

**Recommended treatment**
- Preserve `ContentIdea` as an optional upstream concept/origin entity.
- Do not require every ContentItem to originate from a ContentIdea.
- Use a typed nullable origin reference (`source_idea_id` only if confirmed by the canonical contract) rather than embedding the entire idea record.
- Treat title and editorial content as versioned editorial data. A current title may be exposed as a read projection, but the authoritative revision should remain tied to the ContentItem version.

**Still open:** exact ContentIdea owner/field schema and whether a title projection is stored or derived. This does not block defining the identity boundary.

### 3.4 WP1-O-04 — ContentVariant dimensions and versions

**Source basis**
- Accepted CF-01 defines ContentVariant as a format/platform/language/treatment derivative.
- The Detailed Contract Freeze Pack lists `content_variant_id`, `content_item_id`, `format`, nullable `platform_target`, `variant_status`, nullable `current_artifact_id` and timestamps.
- The Canonical Data Dictionary requires explicit lifecycle naming rather than ambiguous generic `status`.

**Recommended treatment**
- Preserve the canonical `content_variant_id`.
- Require a typed `content_item_id` parent reference.
- Model format, platform, language and treatment as distinct typed dimensions or a versioned profile reference; do not pack them into an unvalidated free-form string.
- Use a domain-owned lifecycle field such as `lifecycle_status`, not generic `status`/`variant_status`, subject to the variant owner confirming the vocabulary.
- Keep variant revision identity distinct from `content_variant_id` if variant configuration itself is versioned.

**Still open:** exact dimension vocabularies, profile ownership, version entity name and lifecycle enum. No lifecycle states are frozen here.

### 3.5 WP1-O-05 — Artifact linkage

**Source basis**
- Part 7 defines `Artifact` and immutable `ArtifactVersion`.
- ArtifactVersion includes `artifact_version_id`, `artifact_id`, `version_number`, `storage_ref`, `content_hash`, media type, size, metadata, creator/timestamp and parent version refs.
- Contract 11's `StudioProduction` includes `artifact_refs`.
- The Detailed Contract Freeze Pack's simple ContentVariant model includes nullable `current_artifact_id`.

**Recommended treatment**
1. Treat Part 7's Artifact/ArtifactVersion model as the canonical artifact owner.
2. Treat production-to-artifact lineage (`StudioProduction.artifact_refs`, or its approved equivalent) as the authoritative record of what a run produced.
3. Do not make ContentVariant the owner of artifact metadata or artifact lifecycle.
4. If a UI needs “current output for this variant”, represent it as a derived pointer/projection to an exact `artifact_version_id`, not as a competing artifact record.
5. Approval and QA must ultimately bind to exact artifact versions and hashes, consistent with accepted governance decisions.

**Still open:** whether the variant stores a denormalized current-output pointer at all, and the exact typed link between ContentVariant, StudioProduction and ArtifactVersion.

### 3.6 WP1-O-06 — Workflow, task and job boundary

**Source basis**
- The Detailed Contract Freeze Pack distinguishes Workflow, WorkflowTask, Job and JobAttempt.
- A task is a logical step, not an execution attempt.
- A task may create one or more jobs.
- A retry creates a new JobAttempt and does not erase history.
- Full durable job semantics belong to the WP-2 execution work package.

**Recommended WP-1 boundary**
- Define canonical IDs and typed parent references for Workflow and WorkflowTask.
- Define the future relationship `WorkflowTask → Job` in the contract model.
- Do not implement dispatch, leases, retries, worker claims, scheduler behavior or outbox/inbox in WP-1.
- Job/JobAttempt tables may be deferred to WP-2 if WP-1's approved vertical-slice persistence test does not require actual job dispatch.
- Do not collapse task, job and attempt into one table/entity for convenience.

**Decision needed only if the vertical-slice acceptance scope changes:** whether a minimal Job record must be physically persisted during WP-1. Default recommendation is to leave execution persistence to WP-2.

### 3.7 WP1-O-07 — Legacy/external identifier mapping

**Source basis**
- Canonical Data Dictionary says external platform IDs remain separate namespaced fields.
- Detailed Contract Freeze Pack says legacy run IDs, file paths and provider object keys must be stored as external references with source system/provider, external ID/locator, related canonical entity and observed timestamp.
- Canonical UUIDv7 remains the internal identity.

**Recommended logical relation**
- `external_reference_id` — canonical UUIDv7 for the mapping record.
- `workspace_id` — scope where applicable.
- `source_system` — controlled namespace/provider identifier.
- `external_entity_type` — source-side entity kind.
- `external_id_or_locator` — source identifier/path/object key.
- `target_entity_type`, `target_entity_id` — typed canonical target.
- `observed_at`, `created_at`, `created_by`.
- optional safe metadata.

Recommend uniqueness on the tuple `(source_system, external_entity_type, external_id_or_locator)` within the appropriate workspace/scope, subject to source-system semantics.

This is a proposed mapping shape, not an accepted final schema. Do not crawl or rewrite local files to populate it during WP-1 design.

### 3.8 WP1-O-08 — Referential integrity and deletion

**Source basis**
- Accepted CF-06 distinguishes archival, logical deletion and physical deletion.
- Deletion is dependency-aware and policy-controlled.
- Historical lineage, approval evidence and required audit records must be preserved.
- Local deletion does not imply external-platform deletion.
- Canonical relationships must respect workspace boundaries.

**Recommended persistence default**
- Do not use broad cascading physical deletion across canonical business records.
- Prefer restrictive foreign-key behavior for referenced records with historical lineage.
- Use explicit archival/logical-deletion workflows governed by the owning domain.
- Do not permit a parent delete to erase runs, attempts, artifacts, review packages, approvals or audit evidence.
- Exact SQL `ON DELETE` actions remain subject to final schema review.

This is a conservative recommendation consistent with CF-06; it is not a new deletion policy.

### 3.9 WP1-O-09 — Migration and rollback tooling

No reviewed source selects a migration framework, ORM, deployment migration runner, or rollback mechanism.

**Disposition: DEFER.**
- Do not select a tool during logical contract design.
- Do not install dependencies or create migrations.
- Revisit only after implementation authorization, environment constraints and the selected persistence implementation are approved.
- Any future migration plan must preserve the local Shorts Studio work and provide evidence-backed backup/restore and compatibility behavior.

## 4. What is now resolved versus still open

### Resolved at the logical-design level
- ContentIdea, ContentItem and ContentVariant remain separate concepts.
- ContentItem is the shared editorial identity.
- ContentVariant is the format/platform/language/treatment derivative.
- Canonical entity ID and immutable version identity are distinct.
- Artifact and ArtifactVersion are owned by Part 7; StudioProduction records output lineage under Contract 11.
- WorkflowTask, Job and JobAttempt are separate concepts.
- Legacy IDs/paths are external references, never canonical IDs.
- Historical lineage must not be cascade-deleted.
- Migration tooling is deferred.

### Still open before final detailed schema
1. Complete ContentVersion schema and payload representation.
2. Exact ContentItem requiredness/nullability and title projection.
3. ContentIdea source contract and precise origin relationship.
4. ContentVariant dimension vocabularies, profile and revision model.
5. Exact ContentVariant ↔ StudioProduction ↔ ArtifactVersion link.
6. Whether Job is physically persisted in WP-1 or begins in WP-2.
7. External-reference uniqueness scope and exact schema.
8. Exact FK actions and archival representation.
9. SQL types, indexes, schema migration tooling and environment-specific details.

These are detailed design items, not reasons to reopen accepted ADR/CF decisions.

## 5. WP-1 minimum vertical-slice recommendation

For the first WP-1 persistence slice, recommend limiting physical persistence to:
1. Workspace identity/scope.
2. Typed Brand reference (Contract 03 remains owner).
3. ContentItem and its immutable content version.
4. ContentVariant and its parent ContentItem reference.
5. Workflow and WorkflowTask identity/parent relationship.
6. A typed Artifact/ArtifactVersion reference boundary, using Part 7 ownership.
7. External-reference mapping only if the first slice needs to link an existing Shorts Studio identifier.

Do not implement the worker registry, durable queue, lease management, artifact binary transfer, full governance enforcement or distribution in this slice.

If the existing P0 acceptance definition requires a persisted Job before WP-2, add only the minimum Job identity/reference record by an explicit owner-approved scope adjustment. Do not implement queue behavior early.

## 6. WP-1 design exit checklist

- [x] Existing source artifacts located and used; no duplicate architecture plan created.
- [x] Accepted identity and ownership decisions preserved.
- [x] ContentItem / ContentVariant distinction preserved.
- [x] Artifact and StudioProduction ownership reconciled against Part 7 and Contract 11.
- [x] Workflow / task / job / attempt boundaries retained.
- [x] Legacy external-ID principle reconciled.
- [x] Deletion principles aligned with CF-06.
- [x] Migration tooling deferred.
- [ ] Owner reviews recommended detailed resolutions.
- [ ] Remaining schema details are resolved or explicitly deferred.
- [ ] Final WP-1 schema/contract candidate is approved.
- [ ] Separate bounded implementation authorization is issued.

## 7. Next step

The next step is **WP-1 owner review of the recommended resolutions**, not implementation.

Once the owner confirms or adjusts the remaining schema details, consolidate the accepted results into a final WP-1 contract candidate and update the existing Artifact 10 decision record. Only after that should a separate implementation authorization be considered.

**No repository access, Git operation, code change, test execution, agent assignment, migration, dependency installation, provider connection, spending, deployment, production generation, upload or publishing is authorized by this record.**

---

## Plain-language summary

We found answers to most of the nine questions in documents that already existed. A few details—especially the exact content-version structure and how a variant points to a produced file—are genuinely not fully specified in those sources.

So we have not invented final schemas. We have made conservative recommendations, preserved the accepted architecture, and separated what can move forward from what still needs a real decision.

**WP-1 design resolution: prepared for owner review.  
Implementation: not authorized.**
