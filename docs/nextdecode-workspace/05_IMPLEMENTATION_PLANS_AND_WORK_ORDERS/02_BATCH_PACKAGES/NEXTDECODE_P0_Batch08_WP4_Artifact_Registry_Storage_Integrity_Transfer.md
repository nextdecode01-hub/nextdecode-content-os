NEXTDECODE CONTENT OS

# P0 Batch 08
WP-4 Artifact Registry, Storage, Integrity & Transfer

Design working pack • 01 November 2026

Purpose: define a reviewable candidate contract for registering, versioning, storing, transferring, validating and retrieving NEXTDECODE artifacts. The design separates relational artifact metadata from binary storage and keeps provider selection deferred. This is not a frozen contract and does not authorize repository edits, storage provisioning, data migration, provider activation, uploads or publishing.

## 1. Status and use

| Label | Meaning |
| --- | --- |
| ACCEPTED DIRECTION | Recorded owner-accepted architecture rule or decision. |
| DESIGN CANDIDATE | Proposed artifact model requiring source reconciliation. |
| SOURCE REQUIRED | Exact fields, retention rules, lifecycle values or transfer semantics are not verified. |
| OWNER DECISION | A genuinely owner-reserved choice; no inferred approval. |
| NOT AUTHORIZED | No implementation, storage provisioning, migration, transfer or external side effect. |

Accepted direction: artifact metadata is stored relationally; binary content is managed behind a storage abstraction. Artifact identity/version, integrity and access are explicit. A storage provider is not selected by this pack. Existing Shorts Studio remains a bounded specialist producer/consumer of artifacts, not the authority for shared artifact governance.

## 2. WP-4 mission and boundaries

| WP-4 owns | WP-4 does not own |
| --- | --- |
| Canonical artifact registration and metadata contract | Core content/workflow persistence foundation (WP-1) |
| Artifact versioning, integrity metadata and lifecycle | Job orchestration and retry policy (WP-2) |
| Transfer protocol and scoped artifact access integration | Worker identity/trust lifecycle and credential issuance (WP-3) |
| Storage abstraction and provider-neutral operations | Central rights, approval, retention and authorization policy definition (WP-5) |
| Artifact validation, quarantine and repair semantics | Integrated P0 end-to-end acceptance (WP-6) |
| Traceability between artifact, source job, content version and evidence | Automatic public distribution or external publishing |

WP-4 consumes worker/job authorization boundaries and WP-5 governance policy. It must not implement a parallel permission model or treat possession of a storage URL as authorization.

## 3. Governing invariants

- Artifact metadata is relational; binary bytes sit behind a provider-neutral storage abstraction.

- Artifact identity is canonical and immutable; each new or repaired content version receives a distinct version identity.

- Integrity is verified using content hashes and recorded metadata; mismatch never silently passes.

- Artifact provenance links to its producing job/attempt, source inputs, content/variant version and relevant evidence where applicable.

- Access is scoped to the exact artifact/version and authorized principal/job; opaque identifiers or URLs are not permissions.

- Workers receive bounded artifact handles, not unrestricted bucket or filesystem credentials.

- At-least-once transfer and retry behavior must be idempotent and traceable.

- Quarantined or invalid artifacts cannot be consumed by protected downstream steps.

- Repair creates a new immutable version or explicit derivative; it does not overwrite history.

- Retention, deletion, legal hold and privacy behavior are governed by authoritative policy and must not be invented here.

- No storage provider, paid service, public bucket or cloud deployment is selected or authorized.

## 4. Candidate artifact domain model

| Concept | Candidate responsibility | Boundary / notes | Source status |
| --- | --- | --- | --- |
| Artifact | Logical registered output/input object | Stable identity across versions where appropriate | SOURCE REQUIRED |
| ArtifactVersion | Immutable bytes plus version-specific metadata | New content hash or repair creates a new version | ACCEPTED DIRECTION; details SOURCE REQUIRED |
| ArtifactDerivative | Transformed representation derived from another version | Explicit parent/version lineage and transformation metadata | DESIGN CANDIDATE |
| ArtifactReference | Typed reference used by jobs, content, reviews or distribution | Reference does not imply access permission | SOURCE REQUIRED |
| StorageObject | Provider-specific location behind an adapter | Never expose provider internals as canonical identity | ACCEPTED DIRECTION |
| TransferSession | Bounded transfer attempt with resumable/checksum state | Separate from artifact identity and job attempt | DESIGN CANDIDATE |
| IntegrityCheck | Hash/size/type/scan validation result | Bound to exact artifact version and checker version | DESIGN CANDIDATE |
| QuarantineRecord | Reason and evidence for withholding an artifact | Release requires authorized disposition | DESIGN CANDIDATE |
| RetentionDisposition | Retention/hold/deletion state under policy | Exact rules and durations SOURCE REQUIRED | SOURCE REQUIRED |

## 5. Candidate artifact lifecycle

The following state names are illustrative. Exact enum values and transitions must be imported from the governing artifact lifecycle contract.

| Candidate state | Meaning | Possible transitions | Guard |
| --- | --- | --- | --- |
| REGISTERED | Metadata exists; bytes may not yet be complete | INGESTING, EXTERNAL_REFERENCE_PENDING | Registration is attributable and scoped. |
| INGESTING | Bytes are being received or generated | STAGED, FAILED, QUARANTINED | Transfer/session identity and expected metadata recorded. |
| STAGED | Bytes are present in a temporary/staging location | VALIDATING, FAILED | Not yet trusted for downstream use. |
| VALIDATING | Integrity/type/security checks are running | AVAILABLE, QUARANTINED, FAILED | Checks apply to exact version. |
| AVAILABLE | Artifact version passed required checks and is accessible under policy | SUPERSEDED, QUARANTINED, RETENTION_HOLD | Availability does not grant access. |
| QUARANTINED | Artifact is withheld due to mismatch, unsafe content or policy concern | VALIDATING, RETIRED | Release requires authorized review and fresh validation. |
| SUPERSEDED | A newer version is preferred; old version remains traceable | RETENTION_HOLD, RETIRED | Never overwrite old version. |
| RETENTION_HOLD | Deletion/expiry is blocked by legal or policy hold | AVAILABLE, SUPERSEDED, RETIRED | Only authorized hold release permits next step. |
| RETIRED | No longer eligible for ordinary use | (terminal or policy-controlled restore) | Retention/deletion policy governs bytes and metadata. |
| FAILED | Ingestion/validation failed | INGESTING, RETIRED | Retry creates traceable attempt; no false availability. |

## 6. Metadata contract: candidate fields

| Field group | Candidate fields / meaning | Validation questions |
| --- | --- | --- |
| Identity | artifact_id, artifact_version_id, version_number or revision | Are canonical ID and version identity separate? What is the immutable key? |
| Classification | artifact_type, media_type/MIME, format, purpose, sensitivity label | Which controlled vocabularies are authoritative? |
| Content properties | byte_size, checksum_algorithm, checksum_value, dimensions/duration where relevant | Which fields are required by media type? |
| Provenance | producer_job_id, execution_attempt_id, source_artifact_version_ids, content_item/variant/version refs | Can every derivative be traced to its inputs and producer? |
| Storage reference | storage_backend_key, opaque object locator, storage class metadata | Are provider-specific values isolated behind adapter? |
| Lifecycle | state, created_at, validated_at, superseded_by, retention/hold references | Which state transitions and timestamps are legal? |
| Integrity | verification result, checker/version, check timestamp, failure reason | Can old validation be invalidated when bytes or policy changes? |
| Access | workspace/owner scope and policy references | Are access decisions always centralized and exact-version scoped? |
| Transfer | transfer_session_id, expected size/hash, received bytes, resume offset/chunk refs | How are partial transfers safely resumed? |
| Audit | actor, source, correlation ID, event/version references | Can registration, access, transfer, repair and deletion be reconstructed? |

Do not finalize field names, nullability, enum values, indexes or table decomposition until the authoritative data dictionary and CF source pack are verified.

## 7. Storage abstraction contract

| Operation | Provider-neutral behavior | Required safeguards |
| --- | --- | --- |
| put / begin upload | Create bounded upload session for a new artifact version | No public access; expected size/type and scope recorded. |
| complete upload | Finalize object and associate immutable storage reference | Verify bytes, size and checksum before AVAILABLE. |
| get / read | Return authorized stream or short-lived scoped handle | Authorize exact artifact version and purpose. |
| head / inspect | Return metadata needed for validation and transfer resume | Do not expose provider credentials or unrestricted object paths. |
| copy / promote | Move/copy staged object to approved storage tier | Verify checksum before and after; record lineage. |
| delete / expire | Apply authorized retention/deletion disposition | Respect legal hold, audit and retention policy. |
| repair / rehydrate | Restore or recreate bytes from trusted source | New version or explicit repair lineage; never silent overwrite. |
| list by reference | Resolve known authorized artifact references | No unrestricted bucket listing for workers. |

Adapter contract must support local filesystem storage initially if appropriate, while preserving a provider-neutral interface. This is a design option, not a commitment to a specific implementation until source and repository constraints are checked.

## 8. Integrity, validation and trust

| Check | Candidate rule | Failure behavior |
| --- | --- | --- |
| Checksum | Use a declared algorithm and checksum over exact bytes | Mismatch => QUARANTINED/FAILED; no downstream use. |
| Byte size | Compare received bytes with expected/declared size | Mismatch => fail validation; retain diagnostic evidence. |
| Media type | Validate detected content against declared type and allowed use | Mismatch => quarantine or reject; do not trust filename extension. |
| Format/container | Parse/validate supported format and structural integrity | Malformed or unsupported => quarantine/fail. |
| Malware/safety scan | Apply policy-defined scanning where required | Unknown or failed scan cannot be treated as clean. |
| Provenance | Check source/producer and lineage references | Missing required provenance blocks governed downstream use. |
| Rights/license | Resolve rights evidence and use-specific permission through WP-5 | Unknown/missing/ambiguous rights fail closed for protected use. |
| Version binding | Bind every validation to artifact_version_id and checksum | Changed bytes invalidate previous validation. |

Exact scan tools, algorithms, allowed formats and policy thresholds remain SOURCE REQUIRED or deferred. Do not claim that a checksum alone proves safety, authenticity or rights.

## 9. Transfer protocol candidate

1. Create a transfer session bound to artifact version, expected size/hash, source job/attempt and authorized destination.

1. Obtain a short-lived credential or opaque handle scoped to this transfer and exact object/version.

1. Transfer bytes in bounded chunks or a supported streaming mode; record progress and chunk/checksum metadata as required.

1. Support retry/resume without changing artifact identity or accepting conflicting bytes.

1. Finalize transfer only after the receiver validates expected size and checksum.

1. Run required media/security/provenance checks before marking the artifact AVAILABLE.

1. Persist transfer completion, integrity result and correlation references; revoke or expire temporary access.

1. If outcome is uncertain, reconcile object existence and checksum before replaying transfer completion.

| Concern | Candidate behavior | Open detail |
| --- | --- | --- |
| Partial upload | Remain STAGED/INGESTING; not consumable | Chunk size and multipart semantics SOURCE REQUIRED |
| Resume | Resume only against same immutable transfer/session expectations | Resume token format and expiry deferred |
| Duplicate transfer | Idempotent session/finalization handling | Deduplication key and retention SOURCE REQUIRED |
| Interrupted download | Retry using exact version and verified range/checksum | Range support and provider behavior deferred |
| Cross-worker transfer | Scoped source/destination handles; no shared bucket credentials | Exact credential broker interface SOURCE REQUIRED |
| Large media | Streaming/chunked transfer without loading whole file into memory | Thresholds and performance profile deferred |
| Local-only artifacts | Remain local if policy/job requires local-only handling | No unapproved remote upload or cloud fallback |

## 10. Access control and worker integration

| Action | Required control | Negative test |
| --- | --- | --- |
| Register artifact | Authenticated producer/job and authorized workspace scope | Untrusted producer cannot register into another workspace. |
| Read artifact | Central authorization for exact version and purpose | Opaque ID/URL alone cannot read. |
| Write new version | Authorized producer and new immutable version identity | Existing version bytes cannot be overwritten. |
| Transfer | Short-lived scoped credential/handle tied to job/attempt | Credential cannot access unrelated artifact. |
| Promote to AVAILABLE | Integrity and required policy checks pass | Incomplete or invalid artifact cannot be promoted. |
| Quarantine release | Authorized review and fresh checks | Worker cannot self-release quarantined artifact. |
| Delete/expire | Retention policy, legal hold and central authorization | Held artifact cannot be deleted by ordinary worker. |
| Export/share | Explicit destination/purpose authorization and applicable rights | No public URL or external share by default. |

## 11. Derivatives, repair and lineage

| Scenario | Required model | Invariant |
| --- | --- | --- |
| Thumbnail/proxy generation | New derivative version linked to exact source version and transformation | Source remains immutable; derivative provenance is explicit. |
| Transcode/re-encode | New artifact version with toolchain/parameters metadata | A transform is not an in-place update. |
| Subtitle/caption file | Separate typed artifact linked to media/content version | Language, timing and source lineage remain explicit. |
| Repair after corruption | New restored version or explicit repair event with source evidence | Do not overwrite corrupt history or erase incident evidence. |
| Revalidation | New check record bound to same immutable bytes/version | Old check history remains queryable. |
| Supersession | New version becomes preferred; prior version retained per policy | References and approvals remain bound to their original version. |

## 12. Retention, deletion and legal hold

Retention and deletion rules are policy-sensitive and cannot be inferred from this design pack. The physical model must support policy-controlled outcomes without silently deleting evidence.

- Distinguish logical retirement, access revocation, metadata tombstoning and physical byte deletion.

- Legal hold must prevent prohibited deletion/expiry and be attributable to an authorized authority.

- Deletion requests must be evaluated against retention, legal hold, rights, audit and dependency requirements.

- Preserve minimal audit evidence where policy requires it; do not retain unnecessary personal data by default.

- Define behavior for derivatives, replicas, caches, temporary transfer chunks and backups.

- Record deletion request, decision, execution evidence and any residual copies/backup expiry.

- Exact retention periods, legal bases, privacy requirements and deletion SLAs are SOURCE REQUIRED.

## 13. Observability and audit requirements

- Correlate artifact, version, transfer session, producer job/attempt, worker, validation check and downstream consumer.

- Record registration, version creation, access grant/deny, transfer start/completion/failure, integrity check, quarantine, release, supersession and deletion disposition.

- Do not log raw credentials, signed URLs, sensitive media contents or unnecessary personal data.

- Metrics should include ingestion/transfer duration, throughput, retry count, checksum mismatch, quarantine count, validation latency, storage usage and reconciliation backlog.

- Operational thresholds and retention windows require measured evidence and policy approval.

## 14. Failure scenarios and acceptance oracle

| Test ID | Scenario | Expected result | Evidence |
| --- | --- | --- | --- |
| WP4-ID-01 | Create a new artifact version | New immutable version identity; prior version unchanged | DB record and version comparison |
| WP4-HASH-01 | Received bytes have wrong checksum | Artifact quarantined/failed; never AVAILABLE | Checksum record and state transition |
| WP4-SIZE-01 | Transfer ends before expected size | Session remains incomplete or fails safely | Transfer state and byte count |
| WP4-RES-01 | Transfer interrupted and resumed | Resume completes same expected content or rejects mismatch | Session history and final hash |
| WP4-DUP-01 | Completion event delivered twice | No duplicate logical artifact version or unsafe side effect | Idempotency/inbox evidence |
| WP4-ACCESS-01 | Worker guesses artifact ID or storage locator | Read denied without central authorization | Negative access test |
| WP4-SCOPE-01 | Credential for artifact A used on artifact B | Access denied | Scope/audience test |
| WP4-TYPE-01 | Filename says MP4 but bytes are invalid/other type | Validation rejects or quarantines | Detected MIME/format report |
| WP4-QUAR-01 | Worker attempts to release quarantine | Denied; authorized review required | Policy denial and audit event |
| WP4-LINEAGE-01 | Derivative generated from source version | Lineage points to exact immutable source version | Lineage graph inspection |
| WP4-REPAIR-01 | Corrupt artifact repaired | New version/repair lineage; old evidence retained | Version and repair event records |
| WP4-HOLD-01 | Deletion attempted under legal hold | Deletion blocked | Hold record and denial audit |
| WP4-LOCAL-01 | Local-only artifact has no authorized transfer route | Remains local; no implicit cloud upload | No remote transfer evidence |
| WP4-PROV-01 | Artifact lacks required producer/source provenance | Protected downstream use blocked | Provenance validation result |

## 15. WP-4 acceptance gates

| Gate | Exit condition | Current status |
| --- | --- | --- |
| G1 — Metadata model | Canonical artifact/version and provenance contract maps to source | DESIGN CANDIDATE / SOURCE REQUIRED |
| G2 — Storage abstraction | Provider-neutral operations and access boundary are specified | DESIGN CANDIDATE |
| G3 — Integrity | Hash, size, type and required checks bind to exact version | ACCEPTED DIRECTION; implementation NOT VERIFIED |
| G4 — Transfer | Partial, retry, resume, duplicate and uncertain outcomes are safe | DESIGN CANDIDATE |
| G5 — Access governance | Central authorization and worker-scoped handles enforced | ACCEPTED DIRECTION; detailed contract SOURCE REQUIRED |
| G6 — Lifecycle | Quarantine, supersession, retention, legal hold and deletion semantics trace to policy | NOT VERIFIED |
| G7 — Integration | WP-1 metadata, WP-2 jobs, WP-3 credentials and WP-5 governance align | NOT VERIFIED |
| G8 — Owner approval | Exact WP-4 contract candidate approved | NOT REQUESTED |

## 16. Open and deferred decisions

| Item | Disposition | Closure trigger |
| --- | --- | --- |
| Exact artifact types and required metadata | SOURCE REQUIRED | Import approved data dictionary and CF source rows. |
| Checksum algorithms and validation profiles | CANDIDATE / SOURCE REQUIRED | Security/integrity policy and format requirements. |
| Storage provider and hosting | NOT SELECTED | Separate owner decision; cost/security review; no paid activation. |
| Local storage layout and path strategy | DEFERRED | Repository integration review under explicit implementation authorization. |
| Transfer chunk sizes and resume protocol | DEFERRED | Measured file sizes, reliability and performance tests. |
| Malware/content scanning tooling | DEFERRED | Threat model, policy and free-first feasibility review. |
| Retention durations and deletion SLAs | SOURCE REQUIRED | Authoritative retention/privacy/legal policy. |
| Legal hold authority and release workflow | SOURCE REQUIRED | Governing policy and owner/legal review. |
| External sharing/export policy | SOURCE REQUIRED | Distribution and rights governance contract. |
| Replica/cache/backup deletion behavior | SOURCE REQUIRED | Storage architecture and retention policy. |

## 17. Draft WP-4 work order — not active

| Field | Draft definition |
| --- | --- |
| Objective | Implement provider-neutral artifact metadata, immutable versioning, integrity validation, scoped transfer and lifecycle controls. |
| Preconditions | Authoritative artifact/data dictionary/retention sources verified; contract freeze approved; WP-1 schema, WP-2 job and WP-3 credential contracts approved; separate implementation authorization. |
| Allowed after authorization | Implement approved artifact registry, storage adapter interface, transfer sessions, checksum validation, quarantine, lineage and tests within file allowlist. |
| Forbidden without separate approval | Provider activation, public buckets, paid storage, bulk migration, destructive deletion, broad filesystem access, cloud deployment, publishing or broad Git operations. |
| Required outputs | Artifact metadata implementation, adapter contract, transfer and integrity tests, lineage evidence, retention/deletion behavior and traceability report. |
| Exit criteria | Mandatory WP-4 tests pass; cross-scope access and integrity failure paths proven; independent read-only QA disposition recorded. |
| Rollback boundary | New writes can be paused and staged objects reconciled; metadata and byte restoration plan tested before live migration. |

## 18. Readiness decision

| Question | Current answer |
| --- | --- |
| Is relational metadata plus storage abstraction accepted? | Yes — at architecture direction level. |
| Is a provider selected? | No. |
| Is this the final artifact schema/lifecycle contract? | No — candidate only; source and policy verification remain required. |
| Are storage provisioning, migration or transfer authorized? | No. |
| Can this be used for design review? | Yes — reconcile exact fields and lifecycle rules against authoritative sources before freeze. |

Recommended next step: reconcile this candidate with the original artifact/data dictionary, lifecycle, retention and API/event sources. Then continue with WP-5 Governance, Quality, Rights, Approval & Central Authorization design.

END OF BATCH 08


## Source document metadata (preserved from DOCX)

- **Footer:** NEXTDECODE • P0 design candidate • Not frozen • Not implementation authorization

