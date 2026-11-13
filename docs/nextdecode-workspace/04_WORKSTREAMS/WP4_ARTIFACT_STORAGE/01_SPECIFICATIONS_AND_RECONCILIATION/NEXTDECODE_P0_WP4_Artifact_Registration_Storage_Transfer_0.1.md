# NEXTDECODE — P0 WP-4
## Artifact Registration, Storage & Transfer Boundary

**Version:** 0.1  
**Status:** DESIGN CANDIDATE — OWNER REVIEW REQUIRED  
**Scope:** P0 foundation  
**Implementation status:** Not authorized

---

## 1. Purpose

Define how NEXTDECODE registers, versions, validates, stores, transfers and retrieves durable artifacts without losing provenance, integrity or access control.

The database is authoritative for artifact identity and metadata. Binary storage is behind an abstraction. The storage provider remains unselected.

This package covers durable outputs and controlled transfer. It does not define the complete asset library, retention schedule, publishing system or provider deployment.

## 2. Decision labels

- **ACCEPTED:** Established by accepted ADR/CF decisions.
- **SOURCE-DEFINED:** Required by the P0 specification or contract sources.
- **RECOMMENDED:** Proposed design detail for owner review.
- **OPEN:** Requires further decision or evidence.
- **DEFERRED:** Intentionally postponed.

This document is not a schema freeze or implementation authorization.

## 3. Accepted architecture baseline

Under accepted CF-15 through CF-18 and the P0 specification:

1. Artifacts have canonical identity and immutable versions.
2. Relational metadata is authoritative; binary storage is abstracted.
3. Asset and Artifact are distinct concepts.
4. Checksums verify integrity.
5. Transfers are controlled, attributable and verifiable.
6. Centralized access and rights enforcement apply.
7. Historical artifact bytes are not overwritten in place.
8. Manifests have canonical identity and immutable versions.
9. Manifest components reference exact artifact versions.
10. Composition, dependencies, integrity and production provenance are recorded.
11. Review, approval and distribution bind to exact manifest/artifact versions.
12. Artifact authorization is centralized and scope-aware.
13. Read, write, transfer, export, share and delete are distinct permissions.
14. Deletion is dependency-aware and recovery is controlled.
15. Validation is type-aware and versioned.
16. Validation and availability are separate states.
17. Quarantine blocks normal downstream use.
18. Revalidation preserves historical results.
19. Repairs create new artifact versions.
20. Technical validation does not establish factual accuracy, rights or approval.
21. Exact retention durations and storage provider remain deferred.

## 4. Domain boundary: Asset, Artifact and ArtifactVersion

### 4.1 Asset

An Asset is a managed reusable source or resource used in creation workflows. Examples may include licensed footage, music, logos, templates or reference media.

An Asset can be referenced by multiple content items and workflows, subject to its own rights and access constraints.

### 4.2 Artifact

An Artifact is a durable output or evidence-bearing file produced, transformed, imported or registered by a workflow.

Examples:
- research evidence export;
- script document;
- storyboard;
- generated visual;
- voiceover audio;
- rendered video;
- subtitle file;
- QA report;
- review package;
- final approved production output.

An Artifact is not interchangeable with an Asset.

### 4.3 ArtifactVersion

An ArtifactVersion identifies one immutable byte-level/content version of an Artifact.

A changed output creates a new version. Historical bytes, checksums and evidence are not silently overwritten.

## 5. Conceptual metadata model

**RECOMMENDED logical structure — exact schema and constraints remain open.**

### Artifact

| Field | Purpose |
|---|---|
| `artifact_id` | Canonical immutable artifact identity |
| `workspace_id` | Owning workspace reference |
| `artifact_type` | Typed artifact classification |
| `owner_entity_type` | Typed owning entity category |
| `owner_entity_id` | Canonical owning entity reference |
| `lifecycle_status` | Artifact lifecycle state |
| `current_version_id` | Optional current-version pointer |
| `created_by` | Attributable producer/actor |
| `created_at` | Creation timestamp |
| `schema_version` | Metadata contract version |

### ArtifactVersion

| Field | Purpose |
|---|---|
| `artifact_version_id` | Canonical immutable version identity |
| `artifact_id` | Parent artifact reference |
| `version_number` | Version sequence within artifact |
| `storage_ref` | Opaque storage abstraction reference |
| `content_hash` | Integrity digest |
| `checksum_algorithm` | Algorithm used for digest |
| `media_type` | Verified or declared media type |
| `size_bytes` | Byte size |
| `validation_status` | Technical validation state |
| `provenance_refs` | Typed producer/input references |
| `rights_refs` | Rights evidence/assessment references |
| `created_by` | Attributable producer/actor |
| `created_at` | Version creation timestamp |
| `parent_version_refs` | Explicit lineage references |
| `metadata` | Type-specific, schema-versioned metadata |
| `schema_version` | Metadata contract version |

The source documents define core Artifact and ArtifactVersion concepts, but the exact final field set, nullability, indexes and foreign-key actions remain open.

## 6. Registration boundary

### Registration request — proposed minimum

- Artifact identity or an idempotency reference.
- Owning workspace and typed owner reference.
- Artifact type.
- Intended version identity/sequence.
- Media type.
- Byte size.
- Checksum algorithm and value.
- Storage reference or controlled transfer session.
- Producer identity.
- Workflow/run/job/attempt references where applicable.
- Provenance and rights references.
- Schema version.

### Registration checks

The owning domain/service should validate:

1. The producer is authenticated and authorized.
2. The owning entity reference exists and is valid.
3. The artifact type and schema version are supported.
4. The version identity does not conflict.
5. The storage reference belongs to an approved storage boundary.
6. The declared byte size and checksum are structurally valid.
7. Provenance references are well-formed and attributable.
8. Required rights and policy evidence is attached or explicitly unresolved.
9. Registration is idempotent or returns a clear conflict.

A storage locator is not authorization.

## 7. Storage abstraction

**ACCEPTED:** Binary storage sits behind an abstraction; provider-specific choices remain deferred.

### Required logical operations

- Create an upload/transfer session.
- Write or transfer bytes under a scoped authorization.
- Verify transferred content.
- Finalize durable registration.
- Retrieve an exact artifact version under authorization.
- Check availability and integrity.
- Quarantine or restrict an artifact version.
- Record transfer and access evidence.

### Boundary rules

- Domain services use an abstract storage reference, not provider-specific paths as canonical identity.
- Storage credentials are not exposed to ordinary workers unless explicitly scoped and required.
- Temporary upload locations are not authoritative artifact records.
- Incomplete transfers are not presented as durable, available artifacts.
- Provider migration must not change canonical artifact identity.
- Storage locator secrecy must not be mistaken for access control.

**OPEN:** Provider, bucket/container structure, encryption configuration, regional placement, backup/replication, lifecycle policies and operational cost.

## 8. Transfer authorization

Read, write, transfer, export, share and delete are distinct actions.

**SOURCE-DEFINED P0 rules:**

- Upload/download access is scoped and time-limited.
- Centralized authorization applies.
- Revoked workers cannot fetch new protected artifacts.
- Cross-job artifact access is denied.
- Expired transfer authorization is denied.

**RECOMMENDED transfer grant binding:**

A transfer grant should bind to:
- actor/worker identity;
- action (`UPLOAD`, `DOWNLOAD`, or other explicitly modelled action);
- exact artifact/version or controlled registration session;
- owning workspace and relevant job/run;
- permitted storage boundary;
- expiry;
- policy/authorization decision reference;
- maximum permitted transfer scope where applicable.

A grant for one artifact or job does not imply access to another.

## 9. Transfer lifecycle and safe completion

**RECOMMENDED conceptual transfer lifecycle — exact enum values remain open:**

`REQUESTED → AUTHORIZED → TRANSFERRING → VERIFIED → REGISTERED`

Failure or interruption may lead to:
- `EXPIRED`
- `FAILED`
- `CANCELLED`
- `RECONCILIATION_REQUIRED`

These are candidate labels, not frozen enums.

### Safe transfer sequence

1. Request transfer for an exact intended artifact/version or registration session.
2. Authenticate actor and evaluate centralized authorization.
3. Issue narrowly scoped, time-limited transfer permission.
4. Transfer bytes to a temporary or controlled location.
5. Compute/verify checksum and byte size.
6. Validate expected media/structure as required.
7. Finalize immutable ArtifactVersion metadata.
8. Mark the artifact version available only after required checks pass.
9. Record attributable transfer and registration evidence.

If a transfer is interrupted, retry safely using an idempotent transfer/session identity or create a new controlled attempt. Do not register partial bytes as a complete durable artifact.

## 10. Integrity and validation

### Integrity

- Store checksum algorithm and digest with the version record.
- Verify bytes after transfer and before downstream use.
- A checksum mismatch blocks downstream use.
- Repeated verification preserves historical results.
- A repair creates a new ArtifactVersion.

### Validation

Validation is type-aware and versioned.

It may include:
- byte-size and checksum checks;
- media type and container inspection;
- structural checks for known file formats;
- required metadata checks;
- malware/security scanning where an approved capability exists;
- artifact-specific validation rules.

Technical validation is not the same as factual accuracy, rights clearance, editorial approval or authorization.

### State separation

Do not collapse:
- validation status;
- availability status;
- quarantine status;
- rights status;
- QA outcome;
- approval status;
- authorization status.

A technically valid file may still be restricted, unapproved or unauthorized for a particular use.

## 11. Quarantine and recovery

**ACCEPTED:** Quarantine blocks normal downstream use.

**RECOMMENDED behavior:**

- Quarantined versions cannot be used by normal downstream workflows.
- Quarantine reason and evidence are attributable.
- Revalidation creates a new validation result; it does not erase the old result.
- A repaired file creates a new immutable version.
- Releasing quarantine requires the appropriate authorized decision.
- Quarantine does not automatically clear rights, QA or approval blockers.

**OPEN:** Quarantine triggers, authority to release, malware/security integration, notification policy and recovery procedures.

## 12. Manifest, provenance and lineage

A manifest is a canonical, immutable record describing a composition or production package.

### Accepted principles

- Manifest identity and versions are canonical and immutable.
- Components reference exact artifact versions.
- Composition and dependencies are explicit.
- Integrity and production provenance are recorded.
- Changed inputs or outputs create traceable new lineage.
- Review, approval and distribution bind to exact manifest/artifact versions.
- Manifest completeness is distinct from quality, rights and approval.

### Recommended manifest contents

- Manifest ID and version.
- Owning content item, variant and workflow/run references.
- Exact artifact/version references.
- Component roles and ordering where relevant.
- Input and dependency references.
- Producer and creation evidence.
- Relevant checksums.
- Schema version.

A manifest is not a substitute for an artifact, QA result, rights assessment or approval record.

## 13. Access, rights and lifecycle

Centralized authorization is scope-aware.

The following actions must remain distinct:
- `READ`
- `WRITE`
- `TRANSFER`
- `EXPORT`
- `SHARE`
- `DELETE`

Access to bytes does not establish permission to use them.

Rights restrictions continue to apply even when an artifact is technically accessible. Rights are use-specific and propagate through artifact lineage according to the accepted rights contract.

Deletion must be dependency-aware. Do not cascade-delete historical production evidence, approvals, audit records or artifacts merely because an owning content item is retired.

**OPEN:** Retention classes, durations, legal holds, deletion approval, recovery windows and physical purge policy.

## 14. Shorts Studio integration

Shorts Studio remains a specialised production engine integrated through a bounded adapter.

Its outputs can be registered as artifacts with:
- producer/worker identity;
- workflow/run/job/attempt references;
- content item and variant references;
- exact artifact version;
- media type, size and checksum;
- provenance and relevant rights references;
- validation evidence.

Local render paths and temporary files are not canonical shared artifact identity. The adapter must not bypass centralized authorization or artifact registration.

## 15. Proposed acceptance criteria

These are design targets, not executed tests.

1. Uploaded artifact checksum matches the source checksum.
2. Checksum mismatch blocks downstream use.
3. Expired transfer authorization is denied.
4. Revoked worker cannot fetch new protected artifacts.
5. Cross-job artifact access is denied.
6. A new artifact version does not mutate an earlier version.
7. Interrupted transfer can be retried safely.
8. Partial transfer is not marked as a durable available artifact.
9. Storage locator alone does not grant access.
10. Quarantined artifact is rejected by normal downstream use.
11. Revalidation preserves prior validation evidence.
12. Repair creates a new immutable version.
13. Manifest references exact artifact versions.
14. Approval and distribution references remain bound to exact versions.
15. Provider-specific storage paths do not become canonical entity IDs.
16. Transfer and access actions are attributable and auditable.

## 16. Open decisions

| ID | Open item | Required before |
|---|---|---|
| A-01 | Exact Artifact/ArtifactVersion schema and constraints | Schema freeze |
| A-02 | Storage provider and deployment boundary | Provider activation |
| A-03 | Upload/download transfer protocol | Transfer implementation |
| A-04 | Checksum algorithms and verification policy | Contract freeze |
| A-05 | Resumable transfer and idempotency semantics | Transfer implementation |
| A-06 | Storage encryption and key management | Security implementation |
| A-07 | Artifact type catalogue and validation profiles | Adapter integration |
| A-08 | Manifest schema and component-role vocabulary | Manifest implementation |
| A-09 | Quarantine triggers and release authority | Governance implementation |
| A-10 | Retention classes and durations | Lifecycle implementation |
| A-11 | Legal hold, deletion and physical purge rules | Lifecycle implementation |
| A-12 | Backup, replication and disaster recovery targets | Operational readiness |
| A-13 | Transfer grant exact binding and expiry policy | Authorization integration |
| A-14 | Local cache and offline artifact behavior | Hybrid worker integration |

No provider, retention duration, numeric transfer limit or security product is selected by this document.

## 17. Dependencies and handoffs

- **WP-1:** Canonical identity, ownership, relationships and versioning.
- **WP-2:** Job/attempt identity, idempotency, recovery and event history.
- **WP-3:** Worker identity, trust, scoped credentials and capability boundary.
- **WP-5:** Central authorization, rights, QA and approval enforcement.
- **WP-6:** End-to-end artifact registration, transfer interruption and recovery validation.

## 18. Implementation safety boundary

This document does not authorize:

- Repository or code changes.
- Storage provider selection or activation.
- Cloud bucket/container creation.
- Credential issuance or secret changes.
- Paid storage, bandwidth or scanning services.
- Migration or movement of existing user files.
- Production uploads or publishing.
- Destructive deletion, overwrite or retention purge.

Any such action requires separate appropriate authorization.

## 19. Plain-language explanation

Think of an artifact as a specific, registered version of a file—not merely a filename sitting on a computer.

NEXTDECODE records what the file is, who produced it, which workflow created it, which exact version it is and whether its bytes pass integrity checks. The actual bytes may live in local or cloud storage, but the database remains the authority for identity and metadata.

If a video is edited, the new output becomes a new version. If an upload is interrupted, it is not treated as a finished artifact. If a checksum fails or the file is quarantined, downstream workflows cannot quietly use it.

For NEXTDECODE, this protects research evidence, scripts, visual assets, voiceovers, renders and final review packages—and ensures that approvals refer to the exact file version that was reviewed.

---

**WP-4 outcome:** Artifact identity, immutable versions, storage abstraction, controlled transfer, integrity, validation, quarantine and lineage are defined as a design boundary. Detailed schemas, providers, protocols and numeric policies remain open for owner review.
