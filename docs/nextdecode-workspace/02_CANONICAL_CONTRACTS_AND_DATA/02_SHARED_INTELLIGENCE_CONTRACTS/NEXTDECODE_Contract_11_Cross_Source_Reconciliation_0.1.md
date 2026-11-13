# Contract 11 — Cross-Source Reconciliation

**Version:** 0.1  
**Date:** 2026-11-04  
**Status:** Working reconciliation analysis; not an owner decision, not a frozen contract  
**Scope:** Contract 11 v1.0 against Data Dictionary v1.1, Module-to-Contract Traceability Matrix 1.0, Batch 16 Domain & Interface Contract Closure Pack, and accepted CF-20/CF-21 decisions.

## 1. Source set

| Source | Status / authority role |
|---|---|
| Shared Intelligence Core Contract 11 — Multiformat Creation & Studio Intelligence Model 1.0 | Working architecture contract; documentation only; not frozen |
| Canonical Data Dictionary & Entity Ownership Registry 1.1 | Working architecture standard; latest working reference for CF-20/CF-21 vocabulary; detailed model not frozen |
| Module-to-Contract Traceability Matrix 1.0 | Ownership/contract mapping reference; complete source review still pending |
| P0 Batch 16 — Domain & Interface Contract Closure Pack | Detailed contract candidate; owner freeze pending; implementation not authorized |
| Artifact 08 owner decision record / implementation reference | Sources for accepted ADR-001–ADR-010 and CF-01–CF-24 decisions |

## 2. Consistent boundaries supported across the sources

1. Contract 11 owns the Multiformat Creation Engine domain: creation projects, studio productions and format-native creation lifecycle.
2. The module-to-contract matrix maps Module 8 — Multiformat Creation Engine — to Contract 11, with supporting Contracts 03, 04, 05, 06, 07, 10 and 12.
3. Contract 03 owns canonical Brand and StudioIdentity definitions/versions. Contract 11 consumes exact immutable studio identity versions; it must not become a competing StudioIdentity owner.
4. Contract 11 owns/defines FormatProfile and studio production behavior, while shared platform/format constraints remain versioned and explicit.
5. Contract 11 creates derivative production records; each derivative has independent QA, rights and approval evidence. Approval does not transfer between formats or channels.
6. Shorts Studio remains a specialized production engine behind a bounded adapter. Contract 11 integrates it; it does not replace it.
7. Part 7 owns shared artifact/asset integration. Contract 07 owns quality, rights, governance, approval and authorization decisions. Contract 12 owns distribution packages and external operation records.
8. Shared evidence and research may be reused, but each derivative must preserve lineage and independently validate new claims, rights and quality.

## 3. Confirmed conflict: rights vocabulary

Contract 11 v1.0 still lists the older rights states:
- `CLEARED`
- `RESTRICTED`
- `PENDING_VERIFICATION`
- `PROHIBITED`
- `UNKNOWN`

Accepted CF-20 and Data Dictionary v1.1 use:
- `UNKNOWN`
- `PENDING_REVIEW`
- `CLEARED`
- `RESTRICTED`
- `EXPIRED`
- `REVOKED`
- `DENIED`

Batch 16 explicitly says the CF-20 vocabulary is canonical and does not silently equate, migrate or alias the older values. Its compatibility notes are documentation-only.

**Disposition:** Contract 11 v1.0 is stale on this vocabulary and needs a controlled revision or explicit owner-approved compatibility note. Do not silently edit the source, map legacy values at runtime, backfill data or assume `PENDING_VERIFICATION` and `PENDING_REVIEW` or `PROHIBITED` and `DENIED` are perfectly equivalent.

## 4. Approval and quality boundary

- Accepted CF-21 approval vocabulary includes `APPROVED`, `REJECTED`, `CHANGES_REQUESTED`, `EXPIRED` and `REVOKED`.
- Data Dictionary v1.1 additionally requires approval binding to the immutable review package and exact content/artifact/manifest version plus checksum.
- Contract 11 requires derivative-specific QA and approval and states that approval of one source package or derivative does not automatically approve another.
- Batch 16 says any older schema limited to `APPROVED`/`REJECTED` is incomplete relative to accepted CF-21.

**Disposition:** Preserve the independent derivative approval rule. Ensure every Contract 11 approval reference resolves to Contract 07's canonical decision and exact reviewed version/checksum. The detailed field representation remains open until the schema owner approves it.

## 5. Entity and field completeness differences

### 5.1 CreationProject

Contract 11 v1.0 describes required information including:
- Project identity; workspace, brand and initiative references.
- Opportunity and research references.
- Audience context.
- Parent brand profile version.
- Strategy/portfolio reference.
- Objective and intended outcomes.
- Priority, target window and resource envelope.
- Project owner and accountable editor.
- Lifecycle state and timestamps.

Data Dictionary v1.1 lists a smaller canonical field set:
- `creation_project_id`
- `content_item_id`
- `workspace_id`, `brand_id`
- `objective_refs`, `audience_refs`
- `studio_production_refs`
- `lifecycle_status`
- `owner_ref`

The smaller dictionary may be a minimal canonical registry rather than a full payload. It is not safe to assume the omitted fields are intentionally removed.

**Open mapping:** decide which fields are canonical CreationProject attributes, which are references to Strategy/Research/Brand/Resource entities, and which belong in a versioned project specification or workflow payload.

### 5.2 StudioProduction

Contract 11 v1.0 includes production ID/project, studio and identity version, format profile/version, channel target, audience context, creative brief/concept versions, evidence/knowledge inputs, production engine contract, required agents/capabilities, resource estimate/reservation, state/blockers and timestamps.

Data Dictionary v1.1 lists:
- `studio_production_id`
- `creation_project_id`, `content_item_id`
- `studio_id`, `studio_identity_version_id`
- `format_profile_version_id`, `creative_direction_brief_version_id`
- `workflow_run_id`
- `artifact_refs`
- `quality_assessment_refs`, `rights_assessment_refs`
- `lifecycle_status`

**Open mapping:** identify the canonical owner and storage location for channel target, audience context, concept version, evidence/knowledge refs, engine contract/version, required capabilities, resource estimate/reservation, blockers and timestamps. Do not duplicate worker/job state owned by WP2/WP3.

### 5.3 StudioIdentity and FormatProfile

Data Dictionary v1.1 explicitly assigns StudioIdentity ownership to Contract 03 and requires Contract 11 to reference exact immutable identity/profile versions. Contract 11 v1.0 contains a StudioIdentity conceptual model as part of its creation domain description.

**Disposition:** Treat Contract 11's StudioIdentity description as a consumer-facing compatibility requirement, not a second canonical owner. Contract 03 remains the owner. Contract 11 owns/consumes versioned FormatProfile semantics subject to the canonical schema review.

### 5.4 Asset, Artifact and lineage

Contract 11 references asset requests, manifests and produced artifact references. Data Dictionary v1.1 separates Asset from Artifact/ArtifactVersion and assigns shared artifact integration to Part 7, with Contract 07 rights/provenance governance.

**Disposition:** Preserve Asset ≠ Artifact ≠ ArtifactVersion. Contract 11 production records reference exact immutable ArtifactVersions and rights evidence; they do not own the binary storage lifecycle or central rights decision.

## 6. Batch 16 alignment

The Batch 16 candidate supports these boundaries:
- Accepted CF-20/CF-21 vocabularies are carried forward.
- Legacy rights-token differences are documentation-only; no silent equivalence or migration.
- Contract 11 is a creation domain within the wider domain/interface model.
- Detailed field semantics and contract freeze remain open.
- Emergency-pause semantics remain an owner decision.
- Implementation is not authorized.

Batch 16 is a candidate, not a source that can unilaterally freeze Contract 11 fields.

## 7. Required closure work

| ID | Closure item | Evidence required |
|---|---|---|
| C11-01 | Rights vocabulary updated/reconciled to CF-20 | Exact owner-approved wording and compatibility treatment |
| C11-02 | Approval binding to CF-21 | Review package + exact version + checksum field mapping |
| C11-03 | CreationProject field ownership | Field-by-field mapping to Data Dictionary and owning contracts |
| C11-04 | StudioProduction field ownership | Field-by-field mapping to WP2/WP3/WP4/Contract 07/12 |
| C11-05 | StudioIdentity boundary | Contract 03 remains sole owner; Contract 11 references immutable versions |
| C11-06 | Asset/Artifact references | Exact ArtifactVersion, manifest, provenance and rights linkage |
| C11-07 | Contract 11 revision authority | Explicit owner confirmation of the version to freeze; no version inferred from filename |

## 8. Current disposition

- Contract 11 source location: **RESOLVED**.
- Contract 11 authority/reconciliation: **OPEN**.
- Rights vocabulary conflict: **CONFIRMED**.
- CreationProject/StudioProduction field completeness: **OPEN MAPPING**.
- StudioIdentity ownership: **Contract 03 is the canonical owner per Data Dictionary v1.1; Contract 11 is a consumer**.
- Detailed contract freeze: **PENDING OWNER CONFIRMATION**.
- Implementation authorization: **NOT GRANTED**.

This report does not amend Contract 11, create owner decisions, freeze a schema or authorize implementation.

## 9.1 Field ownership mapping — working classification

This mapping classifies fields from the Contract 11 and Data Dictionary v1.1 source descriptions. It is not a final schema or owner decision. “Candidate owner” means the source responsibility indicated by the current contract boundaries.

### CreationProject

| Field / concept in Contract 11 | Data Dictionary v1.1 representation | Candidate classification | Owner / action |
|---|---|---|---|
| Creation project identity | `creation_project_id` | Canonical identity | Contract 11 / WP1 |
| Shared editorial subject | `content_item_id` | Typed canonical reference | Content domain / WP1; Contract 11 references it |
| Workspace / brand | `workspace_id`, `brand_id` | Scope and canonical references | Workspace/Brand owners; validate scope |
| Objective and outcomes | `objective_refs` | Typed references, not duplicated strategy truth | Strategy/Planning owner; Contract 11 references |
| Audience context | `audience_refs` | Typed references | Contract 01 owns audience entities |
| Related productions | `studio_production_refs` | Typed relationship/reference | Contract 11 / WP1 |
| Lifecycle status | `lifecycle_status` | Domain lifecycle state | Contract 11 owns CreationProject lifecycle; do not reuse workflow/job state |
| Project owner/accountable editor | `owner_ref` | Actor/ownership reference | Identity/scope model; Contract 11 stores reference |
| Opportunity/research references | Not separately enumerated in the minimal dictionary field list | Typed references | Contracts 02/05 own opportunity/evidence/research records |
| Parent brand profile version | Not listed as a CreationProject field | Exact immutable version reference or resolved through studio/brief | Contract 03 owns brand/studio identity; owner must confirm whether direct project-level pinning is required |
| Strategy/portfolio reference | Not separately enumerated | Typed reference | Contract 06 owns strategy/portfolio records |
| Priority, target window, resource envelope | Not separately enumerated | Planning/operational attributes or references | Contract 06 for priority/target intent; Contract 10/WP2 for execution reservation; exact split open |
| Project owner/editor responsibility | `owner_ref` is present but accountable editor is not distinct | Actor reference(s) | Confirm whether one owner_ref is sufficient or whether accountable editor is a separate role reference |

### StudioProduction

| Field / concept in Contract 11 | Data Dictionary v1.1 representation | Candidate classification | Owner / action |
|---|---|---|---|
| Production identity | `studio_production_id` | Canonical identity | Contract 11 / WP1 |
| Parent creation project | `creation_project_id` | Typed canonical reference | Contract 11 |
| Shared editorial subject | `content_item_id` | Typed canonical reference | Content domain / WP1 |
| Studio | `studio_id` | Canonical reference | Studio registry/Contract 03 boundary; exact owner to confirm |
| Studio identity version | `studio_identity_version_id` | Immutable version reference | Contract 03 owns; Contract 11 consumes |
| Format profile version | `format_profile_version_id` | Immutable version reference | Contract 11 owns FormatProfile semantics; WP1 owns canonical persistence mechanics |
| Creative direction brief version | `creative_direction_brief_version_id` | Immutable version reference | Contract 11 |
| Workflow run | `workflow_run_id` | Operational execution reference | Contract 10 / WP2 owns WorkflowRun |
| Produced artifacts | `artifact_refs` | Typed exact Artifact/ArtifactVersion references | Part 7 / WP4 owns artifact registry and storage boundary |
| Quality assessments | `quality_assessment_refs` | Typed governance references | Contract 07 / WP5 |
| Rights assessments | `rights_assessment_refs` | Typed governance references | Contract 07 / WP5 |
| Lifecycle status | `lifecycle_status` | Domain lifecycle state | Contract 11 owns StudioProduction lifecycle; distinct from WorkflowRun/Job/Artifact/DistributionPackage state |
| Channel target | Not separately listed | Typed ChannelProfile/target reference or brief-level intent | Contract 12 owns channel/distribution records; confirm whether production target is a reference or only a creative brief constraint |
| Audience context | Not separately listed on StudioProduction | Reference through CreationProject/brief unless a production-specific snapshot is required | Contract 01 owns audience records; avoid copied mutable audience data |
| Concept version | Not separately listed | Immutable CreativeConcept version reference | Contract 11; add only after owner confirms canonical linkage |
| Evidence/knowledge inputs | Not enumerated on StudioProduction | Typed references to Claim/Evidence/Knowledge | Contracts 02/04; Contract 11 consumes |
| Engine contract/version | Not separately listed | Versioned engine capability/adapter contract reference | Contract 10 owns agent/worker capability; Shorts Studio adapter boundary requires explicit versioning |
| Required capabilities | Not separately listed | Capability requirement reference | Contract 10 / WP3; do not duplicate worker identity or grant authority |
| Resource estimate/reservation | Not separately listed | Estimate vs reservation must be distinct | Contract 10 owns resource/usage records; WP2 schedules execution; no budget authority implied |
| Blockers | Not separately listed | Derived references to quality/rights/governance/worker/workflow blockers | Each owning domain remains authoritative; StudioProduction may expose a projection, not duplicate decisions |
| Timestamps | Not fully enumerated in the dictionary's minimal field list | Audit/lifecycle metadata | Exact required timestamps and source-of-truth rules need WP1/WP2 contract review |

### Mapping rules

1. Do not add every field described in the broader Contract 11 narrative as a column on CreationProject or StudioProduction.
2. Prefer typed references to entities owned by Contracts 01–10 and 12.
3. Keep operational state in WP2/WP3, artifact lifecycle in WP4, and governance outcomes in WP5.
4. A StudioProduction read model may expose a consolidated status view, but must preserve the source owner and state/version for each component.
5. Where a production must be reproducible, pin exact immutable versions of the StudioIdentity, FormatProfile, CreativeDirectionBrief, CreativeConcept, input claims/evidence and output ArtifactVersions.
6. Do not infer that a missing field in Data Dictionary v1.1 has been intentionally removed from Contract 11. The v1.1 registry may be a minimal canonical record definition; field placement remains subject to owner review.

## 9.2 Contract 11 closure items — refined

| ID | Decision required | Proposed evidence/owner |
|---|---|---|
| C11-01 | Align rights vocabulary with CF-20 | Contract 07/WP5 owner-reviewed state definitions |
| C11-02 | Bind approval to exact immutable review package, versions and checksum | Contract 07/WP5 + Data Dictionary owner |
| C11-03 | Decide CreationProject field placement for strategy, opportunity, research, priority, target window and resource envelope | Contract 06 + Contract 11 + WP1/WP2 |
| C11-04 | Decide StudioProduction field placement for channel, audience, concept, evidence, engine version, capabilities, resources, blockers and timestamps | Contract 11 + Contract 10 + Contract 12 + WP1/WP2/WP3 |
| C11-05 | Confirm StudioIdentity ownership and immutable reference semantics | Contract 03 owner; no competing owner in Contract 11 |
| C11-06 | Confirm ArtifactVersion, manifest, lineage, rights and quality reference semantics | Part 7/WP4 + Contract 07/WP5 |
| C11-07 | Confirm Contract 11 revision and freeze authority | Explicit owner review of exact revised document/version |

