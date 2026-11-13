# NEXTDECODE System Architecture & Pipeline
## Part 3 — Shared Data Model & Content Graph 1.0

**Document status:** Architecture draft  
**Version:** 1.0  
**Purpose:** Define the proposed shared data model and Content Graph for NEXTDECODE Content OS.  
**Companion documents:**
- `NEXTDECODE_Master_Blueprint_2.0` — product vision, scope, strategy and roadmap.
- `NEXTDECODE_System_Architecture_Pipeline_Part_1_System_Architecture_Master_Reference_1.0` — overall system architecture.
- `NEXTDECODE_System_Architecture_Pipeline_Part_2_Shorts_Studio_Pipeline_Contract_1.0` — Shorts Studio pipeline contract.

---

## 1. Core design principle

**One content identity, many connected artifacts, multiple studio outputs.**

A single topic or content idea may produce multiple formats, such as a YouTube Short, long-form video, LinkedIn post, carousel and blog article. These outputs should remain connected to their shared research, evidence, claims, brand context and strategy.

The Content Graph is intended to prevent isolated, disconnected content projects. It should make every important content decision and output traceable.

This document is a proposed architecture baseline, not a finalized database schema and not implementation authorization.

## 2. Design constraints

The design must support:
- One workspace and one brand initially.
- Single-owner Creator Mode.
- Hybrid deployment: cloud control plane with local and remote workers.
- Persistent shared state accessible to authorized services and workers.
- Local execution caches and temporary files.
- Future additional brands and users without implementing multi-tenancy now.
- Multiple content formats and specialized studios.
- Versioned artifacts, traceability and auditable approvals.
- A future migration path if the initial database choice changes.

The existing `workspace_sync.py` SQLite prototype must be compared with the target model; it must not dictate the architecture simply because it exists.

## 3. Seven logical data domains

These are logical domains, not necessarily separate databases or services. Initially, prefer a well-structured modular data layer over unnecessary microservices.

### 3.1 Workspace & Identity
- Workspace
- Brand
- User
- Role / Permission
- Brand Profile
- Brand Rule

Initial configuration: one workspace, one brand (NEXTDECODE), one owner. The schema should leave room for future expansion.

### 3.2 Content Intelligence
- Topic
- Content Idea
- Research Package
- Source
- Evidence Item
- Claim
- Claim Evidence Link
- Knowledge Item
- Research Version

Important distinction:
- A **Source** is where information came from.
- An **Evidence Item** is the relevant information obtained from that source.
- A **Claim** is what the content intends to assert.

These entities must not be treated as interchangeable.

### 3.3 Planning & Strategy
- Content Pillar
- Strategy
- Campaign
- Content Brief
- Content Plan
- Content Calendar Entry

### 3.4 Production
- Content Item
- Studio Job
- Script
- Storyboard
- Beat
- Shot
- Asset
- Asset Rights Record
- Render
- Artifact
- Artifact Version

A single Content Idea can have several Content Items. Each Content Item can have multiple versions and artifacts.

### 3.5 Quality & Governance
- QA Run
- QA Result
- Rights Assessment
- Review Package
- Approval Request
- Approval Decision
- Policy
- Policy Version
- Audit Event

### 3.6 Automation & Execution
- Workflow Definition
- Workflow Run
- Job
- Job Attempt
- Worker
- Worker Capability
- Schedule
- Event
- Retry Record
- Execution Log

### 3.7 Distribution & Learning
- Platform
- Platform Account
- Publishing Request
- Publication
- Publication Attempt
- Metric Snapshot
- Experiment
- Feedback
- Learning Insight

## 4. Core Content Graph relationships

Conceptual relationship flow:

```text
Workspace
  -> Brand
  -> Topic
  -> Content Idea
  -> Research Package
       -> Sources
       -> Evidence Items
       -> Claims
  -> Content Brief
  -> Content Items
       -> Studio Jobs
       -> Scripts / Storyboards / Shot Plans
       -> Assets / Rights Records
       -> Renders / Artifacts
       -> QA Results
       -> Review Package
       -> Approval Decisions
       -> Publications
       -> Metric Snapshots
       -> Learning Insights
```

The graph must support explicit many-to-many relationships where needed:
- One research package can support multiple content items.
- One source can support multiple evidence items.
- One claim can be supported by multiple evidence items.
- One asset can be reused across multiple content items, subject to rights restrictions.
- One content item can be distributed to multiple platforms.
- One publication can have many metric snapshots.

Relationships should be represented by explicit database relations or well-defined references, not inferred from filenames.

## 5. Identity and ID strategy — proposed

The reconciliation reports identified ID namespace collisions. The proposed approach is globally unique identifiers, preferably UUIDv7 where supported.

Human-readable prefixes may identify entity types:

| Entity | Example prefix |
|---|---|
| Workspace | `wsp_` |
| Brand | `brd_` |
| Topic | `top_` |
| Idea | `ide_` |
| Research | `res_` |
| Source | `src_` |
| Claim | `clm_` |
| Brief | `brf_` |
| Content Item | `cnt_` |
| Studio Job | `stj_` |
| Artifact | `art_` |
| Asset | `ast_` |
| Workflow Run | `wfr_` |
| Job | `job_` |
| Worker | `wrk_` |
| Approval | `apr_` |
| Publication | `pub_` |

Prefixes are human-readable type markers; they are not the uniqueness mechanism.

Proposed ID rules:
- Every entity has a unique ID.
- IDs are never reused after deletion.
- IDs are not generated solely from array positions, filenames or timestamps.
- IDs remain stable across local and cloud environments.

## 6. Versioning strategy — proposed

| Data | Versioning approach |
|---|---|
| Brand profile | Versioned |
| Brand rules | Versioned |
| Research package | Versioned snapshots |
| Claims and evidence | Versioned with provenance |
| Brief | Versioned |
| Script | Immutable versions |
| Storyboard | Immutable versions |
| Shot plan | Immutable versions |
| Asset | Stable identity plus metadata revisions |
| Render | Immutable output record |
| QA result | Append-only execution record |
| Policy | Immutable policy versions |
| Approval | Immutable decision history |
| Publication | Append-only delivery history |

An approval must reference the exact artifact versions and policy version that were reviewed. If a script or video changes materially after approval, the old approval cannot automatically authorize the new version.

## 7. Artifact and file storage model

Database records and media binaries should be stored separately.

Database metadata may include:
- Artifact ID.
- Storage provider and object key.
- MIME type and file size.
- SHA-256 checksum.
- Creation timestamp.
- Content/run relationship.
- Version and provenance.
- Retention status.

Artifact storage may contain:
- Original source assets.
- Rendered MP4 files.
- Audio.
- Thumbnails.
- Subtitle files.
- Storyboard exports.
- Other production artifacts.

Proposed direction:
- Cloud control plane stores metadata and durable references.
- Local workers may use local temporary storage for rendering.
- Completed artifacts are uploaded or synchronized and validated.
- Large video binaries should not be sent through database records or ordinary API payloads.

## 8. Hybrid synchronization model — proposed

The model must work across:
1. Cloud control plane.
2. Local rendering workers.
3. Future remote execution workers.

### 8.1 Authority model

Use a **cloud-authoritative control model with local execution state**.

Cloud is authoritative for:
- Content identity.
- Workflow state.
- Job ownership and leases.
- Policy versions.
- Approval decisions.
- Publishing authorization.

Workers maintain local execution state such as:
- Local cache.
- Temporary files.
- Render progress.
- Execution results awaiting synchronization.

### 8.2 Synchronization rules

1. Cloud assigns a job with a unique job ID and lease.
2. Worker receives only required inputs and permissions.
3. Worker reports progress through authenticated requests.
4. Worker uploads artifacts and returns references/checksums.
5. Cloud validates results before accepting completion.
6. If a worker disconnects, its lease expires and the job can be recovered.
7. Duplicate completion reports must be safe to process.
8. Local workers cannot overwrite authoritative approval or policy records.

Avoid unrestricted bidirectional database replication because it creates unnecessary conflict and security risks.

### 8.3 Offline behavior

A disconnected local worker may finish already assigned work if it has the required inputs. It should retain results locally and synchronize after reconnecting.

It must not independently publish externally or assume an old approval remains valid.

## 9. Data integrity and lifecycle invariants — proposed

1. Every Content Item belongs to a workspace and has a defined brand context.
2. Every production job references a Content Item or another explicitly permitted workflow object.
3. Every generated artifact has a stable ID and provenance.
4. Every factual claim links to evidence or is explicitly marked unsupported/unverified.
5. Every reused asset has traceable provenance and rights status.
6. Every approval references exact artifact version(s) reviewed.
7. Every publishing request references an approved or policy-eligible artifact.
8. Every external publication has an idempotency identity and delivery record.
9. Every metric snapshot references a known publication or explicitly identified source.
10. Every important state transition creates an auditable event.
11. Archiving must not break historical lineage of published content.
12. A failed worker cannot mark a job complete without server-side validation.

## 10. Content Item lifecycle — proposed

Normal lifecycle:

```text
IDEA
  -> PLANNED
  -> BRIEF_READY
  -> IN_PRODUCTION
  -> QA_PENDING
  -> REVIEW_PENDING
  -> APPROVED
  -> SCHEDULED
  -> PUBLISHED
  -> ANALYZING
  -> ARCHIVED
```

Exception states:
- `BLOCKED`
- `REJECTED`
- `CHANGES_REQUESTED`
- `CANCELLED`
- `FAILED`

Content lifecycle status must be separate from job execution status.

Example:
- Content status: `IN_PRODUCTION`
- Current job status: `RETRY_WAIT`
- Worker status: `OFFLINE`

These represent different entities and should not be collapsed into one status field.

## 11. Database architecture recommendation — proposed

A relational database is recommended for the authoritative system of record because:
- Entity relationships are important.
- Approval and publishing require transactional consistency.
- Workflow state needs reliable updates.
- Content lineage requires traceable relationships.
- Database constraints can prevent invalid relationships.

A graph database is not required simply because the product uses the term Content Graph. A relational database with explicit relationship tables can support the initial graph.

Proposed direction:

| Layer | Recommendation |
|---|---|
| Primary system of record | PostgreSQL-compatible relational database |
| Local cache | SQLite or local files where appropriate |
| Artifact storage | Object/file storage with metadata references |
| Search | Relational search initially; dedicated search later if justified |
| Vector search | Deferred until a demonstrated semantic retrieval need |
| Event history | Append-only event records |
| Queue | Separate durable queue; technology to be decided in Part 4 |

This is not a final provider or product selection. The existing `workspace_sync.py` SQLite prototype must be inspected and compared before deciding how it fits.

## 12. Transaction and concurrency requirements — proposed

Hybrid execution means multiple workers may operate concurrently. The design should support:
- Transactional state transitions.
- Optimistic concurrency or equivalent version checks.
- Unique constraints on important identifiers.
- Worker job leases.
- Lease expiry and safe reassignment.
- Idempotent event processing.
- Atomic approval and publishing authorization checks.
- Protection against stale worker updates.

Example failure case:

A local worker starts rendering. Its lease expires while disconnected. A remote worker receives a retry assignment. When the local worker reconnects, its old completion report must not overwrite the newer authoritative job state.

The system must validate the lease/token and attempt identity before accepting the result.

## 13. Security and data access — proposed

Use least-privilege access from the beginning.

| Actor | Example permissions |
|---|---|
| Owner | Full workspace control |
| Research agent | Research and source records |
| Script agent | Brief, claims and script artifacts |
| Rendering worker | Assigned inputs and output registration |
| QA agent | Read artifacts and submit QA results |
| Approval service | Read review package and record authorized decisions |
| Publishing worker | Approved requests and required credentials only |

Security requirements:
- Workers must not receive unrestricted database credentials.
- Publishing secrets must not be stored in ordinary content records.
- Credentials should use a dedicated secret-management mechanism.
- All worker requests must be authenticated.
- Authorization must be checked server-side.
- Sensitive actions must create audit records.

## 14. Existing Shorts Studio integration boundary

Do not rewrite the Shorts Studio internal data model immediately.

The future Content OS adapter should translate between:

**Content OS entities**
- Content Item
- Research Package
- Brief
- Brand Profile
- Studio Job

**Shorts Studio artifacts**
- Script
- Storyboard
- Shot Plan
- Asset Manifest
- Render
- QA output
- Diagnostics

The adapter registers returned artifacts in the Content Graph without making Shorts Studio the owner of the entire Content OS database.

This provides a reusable integration path for future studios.

## 15. Decisions register

| Decision | Status |
|---|---|
| One shared Content Graph | Proposed baseline |
| Seven logical data domains | Proposed baseline |
| Globally unique IDs | Proposed baseline |
| Immutable artifact versions | Proposed baseline |
| Approval bound to artifact hashes | Proposed baseline |
| Cloud-authoritative shared state | Proposed baseline |
| Local execution cache | Proposed baseline |
| PostgreSQL-compatible system of record | Needs validation |
| SQLite prototype retained for comparison | Agreed approach |
| Dedicated queue technology | Part 4 |
| Final storage provider | Part 8 |

These are design proposals and working baselines, not approved code changes.

## 16. Acceptance criteria — not yet executed

- [ ] One idea can produce multiple format-specific Content Items.
- [ ] Multiple Content Items can reuse one research package.
- [ ] Claims trace to evidence and original sources.
- [ ] Every asset has traceable provenance and rights information.
- [ ] Every rendered output has a version and checksum.
- [ ] Approval becomes invalid when an approved artifact changes.
- [ ] Two workers cannot silently overwrite authoritative state.
- [ ] A disconnected local worker can safely synchronize later.
- [ ] Duplicate events cannot create duplicate publications.
- [ ] Published content remains traceable after archival.

These are future engineering acceptance tests; they have not been executed.

## 17. Verification required before schema approval

A targeted comparison with the existing system is still required:
1. `workspace_sync.py` SQLite prototype.
2. Existing metadata structures.
3. Current run tracker and job identity.
4. Actual artifact formats and manifests.
5. Existing research, claims and lineage schemas.
6. Current approval and publishing ledgers.

Repository/Git inspection remains restricted unless explicitly authorized. Do not invent compatibility claims.

## 18. Next document — Part 4

**NEXTDECODE System Architecture & Pipeline — Part 4: Persistent Job Queue, Scheduler & Worker Architecture 1.0**

Planned topics:
- Job creation and assignment.
- Cloud/local worker communication.
- Job leases and heartbeats.
- PC shutdown during execution.
- Retry, timeout and dead-letter behavior.
- Scheduling while the owner is unavailable.
- Duplicate job and duplicate publishing prevention.
- Recovery after extended offline periods.

Part 4 will add requirements for job identity, transactions, leases and event records. Incorporate those before freezing the final database schema.

---

**End of Part 3 — Shared Data Model & Content Graph 1.0**
