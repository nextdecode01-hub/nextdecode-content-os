# NEXTDECODE — P0 Artifact Contract Reconciliation

**Document ID:** `NEXTDECODE_P0_Artifact_Contract_Reconciliation_0.1`  
**Version:** 0.1  
**Date:** 1 November 2026  
**Status:** DESIGN RECONCILIATION — OWNER REVIEW REQUIRED  
**Scope:** WP-4; cross-document findings X-02, X-03 and X-09  
**Detailed contract freeze:** NOT GRANTED  
**Implementation authorization:** NOT GRANTED

---

## 1. Purpose and disposition

This document restores the artifact details that were compressed in the Consolidated Contract Appendix and defines a more complete logical boundary for artifact versions, manifests, transfers, validation and quarantine.

It reconciles the existing WP-4 design candidate with the Consolidated Contract Appendix and the Cross-Document Consistency & Gap Review. It does not silently convert proposed details into accepted decisions.

**Disposition:** X-02 and X-03 are addressed at the logical-contract level by this reconciliation candidate. X-09 is only partially addressed: lifecycle safeguards are clarified, but owner-reserved deletion, legal-hold and purge authority remain open. This document is not a schema freeze, provider selection, implementation plan or authorization to change the repository.

### Decision labels

- **ACCEPTED BASELINE:** already established by accepted ADR/CF decisions.
- **SOURCE-DEFINED:** required by the existing WP-4 or governing project sources.
- **RECONCILED:** wording or boundary clarified to resolve a documented cross-document inconsistency, without changing accepted policy.
- **PROPOSED:** conservative candidate contract detail for owner review.
- **OPEN / OWNER-RESERVED:** requires further specification or explicit owner decision.
- **DEFERRED:** intentionally postponed because a provider-neutral boundary can be maintained.

## 2. Authority and source precedence

Apply this precedence when sources differ:

1. Accepted owner decision record and ADR-001–ADR-010 / CF-01–CF-24.
2. Governing canonical data dictionary, API/Event Contract Standard and Unified Lifecycle/State Transition Standard.
3. WP-1 through WP-6 package specifications.
4. Consolidated Contract Appendix as a derivative consolidation aid.
5. This reconciliation as a candidate clarification, subordinate to all higher-authority sources.

This document does not amend accepted ADR/CF decisions. Where it proposes fields, states or transitions, those remain proposed unless separately ratified.

## 3. Artifact domain: preserve the three-way distinction

### 3.1 Asset — ACCEPTED BASELINE

An **Asset** is a managed reusable source or resource used by creation workflows, such as licensed footage, music, logos, templates or reference media. An asset may be referenced by multiple content items or workflows subject to its own access and rights constraints.

### 3.2 Artifact — ACCEPTED BASELINE

An **Artifact** is a durable output or evidence-bearing file produced, transformed, imported or registered by a workflow. Examples include research evidence exports, scripts, storyboards, generated visuals, voiceovers, rendered videos, subtitles, QA reports, review packages and final production outputs.

An Artifact is not interchangeable with an Asset.

### 3.3 ArtifactVersion — ACCEPTED BASELINE

An **ArtifactVersion** identifies one immutable byte-level/content version of an Artifact. A changed output creates a new version. Historical bytes, checksums and evidence are not silently overwritten.

### 3.4 Ownership boundary — RECONCILED

- The Artifact domain owns canonical Artifact and ArtifactVersion identity and their authoritative metadata/lifecycle transitions.
- The binary storage system stores bytes behind a provider-neutral abstraction; it does not own canonical identity.
- The owning content/workflow domain supplies typed ownership and provenance references but does not gain authority to rewrite artifact history.
- A storage locator is not an identity, permission or authorization grant.

Exact service decomposition is not prescribed here.

## 4. Artifact and ArtifactVersion logical records

The following field set restores WP-4 detail. It is a **logical contract candidate**, not final DDL. Exact nullability, indexes, constraints, foreign keys and field types remain open.

### 4.1 Artifact

| Field | Meaning | Status |
|---|---|---|
| `artifact_id` | Canonical immutable Artifact identity (UUIDv7 baseline) | SOURCE-DEFINED |
| `workspace_id` | Owning workspace reference | SOURCE-DEFINED |
| `artifact_type` | Typed artifact classification | SOURCE-DEFINED |
| `owner_entity_type` | Typed owning entity category | SOURCE-DEFINED |
| `owner_entity_id` | Canonical owning entity reference | SOURCE-DEFINED |
| `lifecycle_status` | Logical artifact lifecycle status | SOURCE-DEFINED; enum OPEN |
| `current_version_id` | Optional pointer to current version | PROPOSED |
| `created_by` | Attributable producer/actor | SOURCE-DEFINED |
| `created_at` | Creation timestamp | SOURCE-DEFINED |
| `schema_version` | Metadata contract version | SOURCE-DEFINED |

### 4.2 ArtifactVersion

| Field | Meaning | Status |
|---|---|---|
| `artifact_version_id` | Canonical immutable version identity | SOURCE-DEFINED |
| `artifact_id` | Parent Artifact reference | SOURCE-DEFINED |
| `version_number` | Version sequence within Artifact | SOURCE-DEFINED |
| `storage_ref` | Opaque provider-neutral storage reference | SOURCE-DEFINED |
| `content_hash` | Integrity digest | SOURCE-DEFINED |
| `checksum_algorithm` | Algorithm used to compute digest | SOURCE-DEFINED |
| `media_type` | Declared/verified media type, with distinction retained | SOURCE-DEFINED |
| `size_bytes` | Byte size | SOURCE-DEFINED |
| `validation_status` | Technical validation status | SOURCE-DEFINED; enum OPEN |
| `provenance_refs` | Typed producer/input references | SOURCE-DEFINED |
| `rights_refs` | Rights evidence/assessment references | SOURCE-DEFINED |
| `created_by` | Attributable producer/actor | SOURCE-DEFINED |
| `created_at` | Version creation timestamp | SOURCE-DEFINED |
| `parent_version_refs` | Explicit lineage references | SOURCE-DEFINED |
| `metadata` | Type-specific, schema-versioned metadata | SOURCE-DEFINED |
| `schema_version` | Metadata contract version | SOURCE-DEFINED |

**Integrity rule:** an ArtifactVersion's content identity and historical evidence are immutable. Metadata correction must be attributable and versioned according to the eventual schema policy; it must not silently rewrite the evidence describing previously reviewed bytes.

**OPEN:** whether `current_version_id` is stored or derived; version-number allocation/concurrency; exact parent-reference cardinality; metadata mutability rules; uniqueness constraints; and whether validation status is a denormalized projection or read from ValidationRecord.

## 5. ArtifactManifest and exact-version composition

### 5.1 Purpose — ACCEPTED BASELINE

An **ArtifactManifest** is a canonical, immutable record describing a composition or production package. It records the exact components and dependencies that make up a deliverable or evidence package.

A manifest is not itself a substitute for the component artifacts, a QA result, rights assessment, human review, approval or authorization.

### 5.2 Logical records — PROPOSED

- `manifest_id`: canonical immutable manifest identity.
- `manifest_version_id`: immutable version identity.
- `manifest_version_number`: version sequence within the manifest.
- `workspace_id`: owning workspace.
- `owner_entity_type` / `owner_entity_id`: typed owner reference.
- `content_item_id`, `content_variant_id`: optional exact editorial references where applicable.
- `workflow_id`, `workflow_run_id`: optional production context.
- `schema_version`: manifest schema version.
- `created_by`, `created_at`: attributable producer and timestamp.
- `content_hash`: integrity digest for canonical manifest representation.
- `components[]`: ordered component entries.

Each component entry should carry:
- stable component identity or ordinal within the manifest version;
- component role (vocabulary OPEN);
- exact `artifact_id` and `artifact_version_id`;
- expected content hash, media type and size where required;
- explicit dependency/input references;
- ordering/relationship information where composition requires it.

### 5.3 Manifest invariants — ACCEPTED / RECONCILED

1. Components reference exact immutable ArtifactVersions, never only a mutable Artifact pointer.
2. The manifest version is immutable once finalized.
3. A changed component, dependency, ordering or composition creates a new manifest version.
4. A manifest's integrity evidence covers a canonical representation; canonical serialization rules remain OPEN.
5. Approval, review and distribution references bind to the exact manifest version and relevant artifact versions.
6. Manifest completeness is separate from technical validation, rights, QA, review, approval and authorization.
7. A manifest reference does not grant access to its component bytes.

**OPEN:** canonical serialization/hash rules, component-role catalogue, nested-manifest policy, optional/required component semantics, cycle prevention, and treatment of unavailable components.

## 6. TransferRecord contract

X-03 identified that TransferRecord was named but lacked minimum fields, ownership and lifecycle detail. The following is a **PROPOSED logical record**.

### 6.1 Identity and scope

A TransferRecord should include:
- `transfer_id`: canonical immutable transfer identity.
- `workspace_id`: explicit workspace scope.
- `actor_type` and `actor_id`: attributable user/service/worker identity.
- `action`: explicit operation such as upload or download.
- exact `artifact_id` and `artifact_version_id`, where already known; otherwise a controlled registration-session reference.
- related `workflow_id`, `workflow_run_id`, `job_id` and `job_attempt_id`, where applicable.
- `authorization_decision_id`: central policy decision reference.
- `storage_boundary_ref`: abstract storage boundary, not a provider path as identity.
- `expires_at`: transfer permission expiry.
- `created_at`, `updated_at`: timestamps.
- `idempotency_key` or controlled session identity, scoped according to the governing idempotency contract.

### 6.2 Progress and outcome evidence

Candidate evidence fields:
- transfer attempt number or child-attempt reference;
- declared and observed byte counts;
- resumable checkpoint/part references where supported;
- expected and observed checksum algorithm/digest;
- declared and detected media type;
- start, progress and completion timestamps;
- failure/reconciliation reason;
- final registration/version reference.

Do not expose credentials, signed secrets or sensitive storage tokens in ordinary event payloads or audit descriptions.

### 6.3 Transfer authority and lifecycle

**SOURCE-DEFINED:** transfer access is centralized, scoped and time-limited; expired authorization is denied; revoked workers cannot fetch new protected artifacts; cross-job access is denied unless separately authorized.

A transfer grant should be bound to actor/worker, action, exact artifact/version or controlled registration session, workspace/job scope, permitted storage boundary, expiry and authorization decision reference.

**PROPOSED conceptual lifecycle only:**

`REQUESTED → AUTHORIZED → TRANSFERRING → VERIFIED → REGISTERED`

Possible interruption/failure outcomes: `EXPIRED`, `FAILED`, `CANCELLED`, `RECONCILIATION_REQUIRED`.

These labels are not frozen enums. The governing lifecycle standard must be reconciled before final state names are accepted.

### 6.4 Safe transfer protocol

1. Create a transfer request for an exact version or controlled registration session.
2. Authenticate the actor and evaluate centralized authorization.
3. Issue narrowly scoped, time-limited permission.
4. Transfer to a temporary/controlled location.
5. Verify observed byte count, checksum and expected media/structure.
6. Run required type-aware validation.
7. Finalize immutable ArtifactVersion metadata.
8. Mark the version available only after required checks pass.
9. Persist attributable transfer, validation and registration evidence.

Interrupted transfer may resume only under an approved resumability protocol and still-valid authorization, or restart as a safely identified attempt. Partial bytes are never registered as a complete, available ArtifactVersion.

**OPEN:** protocol, chunking, checkpoint format, resume authorization refresh, maximum transfer sizes, parallelism, timeout values and idempotency retention.

## 7. ValidationRecord contract

A **ValidationRecord** is an immutable, attributable assessment of a specific artifact version. It does not represent general content quality or editorial approval.

### 7.1 Proposed minimum fields

- `validation_record_id`: canonical immutable identity.
- exact `artifact_id`, `artifact_version_id` and `content_hash` assessed.
- `validator_identity`: worker/service/person or approved capability identity.
- `validation_profile_id` and `validation_profile_version`.
- `validator_version` and relevant schema/rule-set version.
- `outcome`: candidate technical outcome vocabulary OPEN.
- `checks[]`: check identifier, result, evidence reference and relevant measured value.
- `started_at`, `completed_at`, `created_at`.
- `failure_reason` / structured diagnostic reference where applicable.
- `supersedes_validation_record_id` when a new validation supersedes an earlier assessment.

### 7.2 Validation boundaries

Validation may cover:
- byte-size and checksum;
- media type and container inspection;
- structural checks for known file formats;
- required metadata;
- malware/security scanning only where an approved capability exists;
- artifact-specific validation profiles.

A technical validation result does not establish factual accuracy, rights clearance, editorial QA, human approval or authorization.

A rerun creates a new ValidationRecord. Historical validation evidence is retained and not overwritten.

**OPEN:** exact outcomes, check catalogue, severity mapping, validator trust requirements, profile ownership and retention.

## 8. QuarantineRecord contract

Quarantine is a restriction on downstream use of an exact artifact version, not a substitute for rights, QA, approval or authorization state.

### 8.1 Proposed minimum fields

- `quarantine_record_id`: canonical immutable identity.
- exact `artifact_id`, `artifact_version_id` and content hash.
- `workspace_id`.
- `trigger_type` and `reason_code`.
- evidence references and detection source.
- actor/service that initiated the quarantine.
- `created_at` and relevant timestamps.
- current quarantine disposition/status (vocabulary OPEN).
- release/revalidation decision reference, if any.
- authorizing actor and authorization decision reference for release.
- audit/event references.

### 8.2 Required behavior

**ACCEPTED:** quarantine blocks normal downstream use.

**PROPOSED detail:**
- Quarantine applies to the exact version, not automatically every version of the Artifact; broader scope must be explicit.
- Quarantined versions are denied to ordinary downstream reads/production use, subject to separately authorized investigation/recovery actions.
- The reason and supporting evidence are attributable.
- Revalidation creates a new ValidationRecord and never erases prior evidence.
- Releasing quarantine requires the appropriate centrally authorized decision.
- Quarantine release does not automatically clear rights, QA, review, approval or other policy blockers.
- A repaired file is a new ArtifactVersion, not an in-place replacement.

**OPEN / OWNER-REVIEW:** trigger catalogue, who may initiate quarantine, release authority, appeal/review route, malware/security integration, notifications and emergency handling.

## 9. Availability and state separation

Do not collapse these independent facts:

| Dimension | What it answers |
|---|---|
| Transfer state | Have bytes been transferred and reconciled? |
| Registration state | Has the durable version record been finalized? |
| Availability | Can the authorized storage boundary currently serve the bytes? |
| Integrity | Do observed bytes match the registered digest/size? |
| Validation | Did a versioned technical profile pass? |
| Quarantine | Is ordinary downstream use restricted? |
| Rights | Is the intended use permitted? |
| QA | Does the exact version meet quality requirements? |
| Review | What did a reviewer inspect and record? |
| Approval | Did an authorized human approve the exact scope/version? |
| Authorization | May this actor perform this action now? |

A file may be registered but temporarily unavailable; available but quarantined; technically valid but rights-restricted; or technically valid and rights-cleared but not approved for publication.

No single `READY` flag may be used as a shortcut for these independent controls.

## 10. Storage abstraction and access evidence

**ACCEPTED BASELINE:**
- Relational metadata is authoritative.
- Binary storage is behind a provider-neutral abstraction.
- Provider-specific paths do not become canonical IDs.
- A storage locator alone is not authorization.
- Temporary upload locations are not authoritative artifact records.
- Incomplete transfers are not durable available artifacts.
- Provider migration must not change canonical Artifact identity.

Required logical operations:
1. create upload/transfer session;
2. write/transfer under scoped authorization;
3. verify transferred content;
4. finalize durable registration;
5. retrieve exact version under authorization;
6. check availability and integrity;
7. quarantine/restrict a version;
8. record transfer and access evidence.

Read, write, transfer, export, share and delete remain distinct permissions.

**DEFERRED:** provider, bucket/container structure, encryption configuration, regional placement, backup/replication, lifecycle policies and operational cost. No provider is selected.

## 11. Lifecycle, deletion and legal hold — X-09 partial resolution

### 11.1 Safe principles — SOURCE-DEFINED

- Deletion is dependency-aware.
- Recovery is controlled.
- `DELETE` is distinct from read, write, transfer, export and share.
- Do not cascade-delete historical production evidence, approvals, audit records or artifacts merely because an owning content item is retired.
- Retention durations remain deferred.
- Legal hold and irreversible purge authority remain owner-reserved.

### 11.2 Proposed lifecycle distinctions

These are separate operations, not interchangeable statuses:

1. **Retirement:** remove an entity/version from ordinary active use while retaining required history and evidence.
2. **Deletion request:** create an attributable request identifying exact targets and reason; no bytes are physically removed by the request itself.
3. **Dependency assessment:** discover manifests, variants, workflows, approvals, audit records, rights evidence, derived artifacts and external references.
4. **Legal hold:** apply a preservation restriction that blocks incompatible deletion/purge actions.
5. **Purge authorization:** separately authorize an irreversible operation after dependency, hold and retention checks.
6. **Physical purge:** remove eligible bytes/metadata according to approved policy, retaining required non-content audit evidence where applicable.
7. **Recovery/restore:** restore only through controlled, attributable procedure; restored bytes must be integrity-verified and must not silently rewrite historical identity.

### 11.3 Owner-reserved decisions

No default is selected here for:
- who may authorize irreversible purge;
- legal-hold authority and release;
- statutory/contractual retention obligations;
- recovery window and backup deletion propagation;
- whether/when audit metadata may itself be purged;
- treatment of shared assets and artifacts referenced by multiple owners.

**Freeze effect:** lifecycle interfaces and safeguards must be specified before detailed contract freeze. Exact durations and provider backup mechanics may remain deferred only if enforceable hooks and owner authority are explicit.

## 12. Shorts Studio adapter boundary

Shorts Studio remains a specialised production engine behind a bounded adapter.

Its outputs may be registered with:
- producer/worker identity;
- workflow/run/job/attempt references;
- ContentItem and ContentVariant references;
- exact ArtifactVersion identity;
- media type, size and checksum;
- provenance and relevant rights references;
- ValidationRecord evidence.

Local render paths and temporary files are not canonical shared artifact identity. The adapter must not bypass centralized authorization, artifact registration, quarantine or exact-version review/approval binding.

## 13. WP-6 acceptance matrix — proposed test oracles

These are design targets, not executed tests. All tests must use isolated synthetic fixtures and non-production storage; no real publishing or external side effects.

| Test ID | Scenario | Expected oracle |
|---|---|---|
| ART-01 | Register valid synthetic artifact | One durable Artifact and immutable ArtifactVersion; provenance attributable |
| ART-02 | Re-submit same idempotency key and same canonical payload | Original logical result returned; no duplicate version |
| ART-03 | Same key with different canonical payload | Explicit conflict; no silent overwrite |
| ART-04 | Checksum mismatch after transfer | Registration/availability blocked; evidence retained |
| ART-05 | Interrupted transfer | Partial bytes never appear as complete available version |
| ART-06 | Resume/retry transfer | Safe idempotent continuation or new attributable attempt; no duplicate logical registration |
| ART-07 | Expired transfer grant | Transfer denied |
| ART-08 | Revoked worker requests protected bytes | New protected access denied |
| ART-09 | Cross-job/workspace access | Denied absent separate explicit authorization |
| ART-10 | Storage locator presented without grant | Access denied |
| ART-11 | Manifest component changes | New immutable manifest version; old manifest unchanged |
| ART-12 | Manifest references mutable Artifact only | Rejected; exact ArtifactVersion required |
| ART-13 | Quarantined version used downstream | Normal downstream use blocked |
| ART-14 | Revalidation after quarantine | New ValidationRecord; historical result preserved |
| ART-15 | Repair after integrity failure | New ArtifactVersion; prior bytes/evidence unchanged |
| ART-16 | Retire owner ContentItem with historical evidence | No accidental cascade deletion of artifacts, approvals or audit evidence |
| ART-17 | Legal hold exists during purge request | Purge blocked pending authorized hold resolution |
| ART-18 | Approval references manifest/version A; version B is created | Approval does not silently transfer to B |
| ART-19 | Provider locator changes in test adapter | Canonical Artifact/ArtifactVersion identity remains unchanged |
| ART-20 | Transfer/validation/quarantine action occurs | Attributable audit evidence is reconstructable |

Test fixtures, exact event IDs, test environment controls, evidence retention, teardown rules and result mapping must be reconciled with WP-6's authoritative acceptance plan. No test execution is authorized by this document.

## 14. Open-decision register

| ID | Decision | Status / required before |
|---|---|---|
| A-01 | Exact Artifact/ArtifactVersion schema, constraints and mutability | OPEN — schema freeze |
| A-02 | Storage provider/deployment boundary | DEFERRED — provider activation |
| A-03 | Upload/download protocol | OPEN — transfer implementation |
| A-04 | Checksum algorithms and verification policy | OPEN — contract freeze |
| A-05 | Resumable transfer and idempotency details | OPEN — transfer implementation |
| A-06 | Encryption and key management | OPEN — security implementation |
| A-07 | Artifact type catalogue and validation profiles | OPEN — adapter integration |
| A-08 | Manifest schema, canonical serialization and component-role vocabulary | OPEN — manifest implementation |
| A-09 | Quarantine triggers, scope and release authority | OPEN — governance implementation |
| A-10 | Retention classes and durations | OWNER-REVIEW / DEFERRED — lifecycle implementation |
| A-11 | Legal hold, deletion and physical purge authority/rules | OWNER-RESERVED — lifecycle freeze |
| A-12 | Backup, replication and disaster recovery targets | DEFERRED — operational readiness |
| A-13 | Exact transfer-grant binding and expiry policy | OPEN — authorization integration |
| A-14 | Local cache and offline artifact behavior | OPEN — hybrid worker integration |
| ART-15 | Availability model and state ownership | OPEN — contract freeze |
| ART-16 | Validation outcome vocabulary and validator trust | OPEN — contract freeze |
| ART-17 | Quarantine state model, release/appeal path | OPEN — governance freeze |
| ART-18 | Manifest hashing/canonical serialization | OPEN — manifest implementation |
| ART-19 | Retirement/deletion/purge state model and audit preservation | OWNER-RESERVED — lifecycle freeze |

No provider, numeric retention period, transfer size limit, checksum algorithm, encryption product or legal policy is selected here.

## 15. Traceability to gap findings

- **X-02 — ArtifactVersion and manifest detail:** restored in Sections 4 and 5.
- **X-03 — Transfer, validation and quarantine records:** specified as logical candidate records in Sections 6–8; exact enums/protocols remain open.
- **X-09 — Artifact lifecycle/deletion/legal hold:** safeguards and operation distinctions clarified in Section 11; owner-reserved authority and policy remain open.

This reconciliation does not resolve X-05 authorization/emergency pause, X-06 worker trust, X-08 API/event conformance or X-10 full acceptance evidence.

## 16. Handoffs and dependencies

- **WP-1:** canonical identity, entity ownership, versioning and relational constraints.
- **WP-2:** job/attempt provenance, idempotency, recovery and event history.
- **WP-3:** worker identity, trust, scoped credentials and capability boundary.
- **WP-5:** centralized authorization, rights, QA and approval enforcement.
- **WP-6:** test fixture, expected outcome, evidence and independent QA traceability.
- **Lifecycle Standard:** reconcile candidate transfer/validation/quarantine and deletion states with governing status rules.
- **API/Event Standard:** reconcile commands, events, compatibility, ordering, replay and payload minimization.

## 17. Safety and authorization boundary

This document does not authorize:
- repository/code changes or migrations;
- tests or runtime execution;
- provider selection or activation;
- cloud bucket/container creation;
- credential issuance or secret changes;
- paid storage, bandwidth or scanning;
- movement of existing user files;
- destructive deletion, overwrite or retention purge;
- production generation, upload or publishing;
- agent execution.

Any such action requires separate appropriate authorization.

## 18. Plain-language explanation

Think of an Artifact as a registered file and an ArtifactVersion as one exact, unchangeable version of that file. A Manifest is the recipe that says exactly which versions were combined to make a production package. A TransferRecord tells us who moved which bytes, under what permission and whether the transfer completed. A ValidationRecord tells us which technical checks were run on those exact bytes. A QuarantineRecord explains why that version is blocked from normal use.

This matters to NEXTDECODE because a script, voiceover, visual, rendered short and final review package must remain traceable. If a video is edited, the new file becomes a new version. If an upload stops halfway, it is not treated as finished. If a file is repaired, the repaired file gets a new version. And if an approval was given to one exact version, it does not automatically approve a later edit.

**Reconciliation outcome:** X-02 and X-03 have a more complete logical contract candidate. X-09 has clearer lifecycle safeguards but remains open for owner decisions. The overall P0 package is still **NOT READY FOR DETAILED CONTRACT FREEZE**.

**Detailed contract freeze:** NOT GRANTED.  
**Implementation authorization:** NOT GRANTED.
