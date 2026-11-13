# NEXTDECODE Content OS
## Part 7 — Studio Integration APIs & Artifact Management
**Version:** 1.0  
**Status:** Architecture proposal — not implementation approval  
**Date:** 31 October 2026

---

## 1. Purpose

This document defines how specialized content studios integrate with the shared NEXTDECODE Content OS while retaining their own production logic.

The central principle is:

> Studios own format-specific creation and production. The Content OS owns shared identity, workflow coordination, governance, artifact registration, and cross-studio intelligence.

The architecture must integrate the existing Shorts Studio as a specialized production engine rather than replacing it wholesale. Future studios—long-form video, carousels, newsletters, articles, podcasts, and other formats—should connect through consistent contracts.

This is a proposed architecture baseline. It does not describe completed integrations or authorize repository access, code changes, API deployment, or production execution.

### 1.1 Goals

- Define a stable boundary between the Content OS and each studio.
- Provide consistent APIs and event contracts.
- Standardize artifact registration, versioning, storage references, and provenance.
- Support local and remote workers under the hybrid architecture.
- Make studio workflows resumable and observable.
- Prevent studio-specific adapters from bypassing centralized governance.
- Allow studios to evolve independently without fragmenting shared content identity.

### 1.2 Non-goals

- Rewriting Shorts Studio to fit a new framework.
- Forcing all studios to use the same internal language, renderer, or database.
- Treating a local file path as a globally accessible artifact reference.
- Allowing a studio to publish directly without centralized authorization.
- Finalizing a specific API framework, object-storage vendor, or deployment topology.

---

## 2. Integration architecture

The Content OS exposes shared capabilities through stable service boundaries. Studios integrate through adapters rather than coupling their internal code directly to every central subsystem.

### 2.1 Logical architecture

```text
                 NEXTDECODE CONTENT OS
+------------------------------------------------------+
| Workspace / Content Graph / Brand / Knowledge       |
|                                                      |
| Workflow Orchestrator <-> Persistent Job Queue       |
|          |                                           |
|          +--> Governance / Approval / Authorization |
|          |                                           |
|          +--> Artifact Registry / Asset Registry     |
|          |                                           |
|          +--> Event & Integration API                |
+--------------------------+---------------------------+
                           |
                  Studio Integration Layer
                           |
          +----------------+----------------+
          |                |                |
     Shorts Adapter   Long-form Adapter  Other Adapters
          |                |                |
     Shorts Studio     Long-form Engine   Future Studios
          |                |                |
     Local Worker      Cloud/Local Worker  Worker Pool
```

This is a logical view. Services may be co-deployed initially while retaining the boundaries and contracts.

### 2.2 Ownership boundaries

| Capability | Content OS owns | Studio owns |
|---|---|---|
| Content identity | Canonical content IDs and relationships | Format-specific internal IDs |
| Workflow | Shared lifecycle, task state, dependencies | Internal production stages |
| Brief and brand context | Approved shared references and versions | Format-specific interpretation |
| Creation | Shared inputs and cross-format coordination | Format-specific creative and production logic |
| Artifacts | Registry, version identity, provenance, access policy | Artifact generation and local temporary files |
| Quality | Shared policy and centralized gate outcomes | Format-specific checks and diagnostic evidence |
| Rights | Shared asset/rights records and policy | Accurate asset manifest and source usage |
| Approval | Authoritative approval records | Review previews and feedback interfaces |
| Distribution | Authorization and workflow state | Adapter integration only if separately approved |
| Analytics | Canonical content and distribution linkage | Format-specific metrics and events |

### 2.3 Studio adapter

Each studio should expose a small integration adapter that translates between its internal concepts and shared Content OS contracts.

The adapter:
- receives a validated job envelope;
- resolves authorized input references;
- maps the job to studio-specific operations;
- reports progress and structured outcomes;
- registers output artifacts;
- emits relevant events;
- handles cancellation and recovery;
- does not grant itself publishing permissions.

The adapter should not expose the studio's entire internal implementation as a public API.

---

## 3. Canonical integration identity

### 3.1 Identity hierarchy

The shared platform should distinguish:

- `workspace_id` — owner or workspace boundary;
- `content_id` — canonical idea or content item across formats;
- `content_version` — version of shared content metadata and relationships;
- `studio_id` — specialized creation environment;
- `studio_job_id` — studio-local execution identity;
- `workflow_id` — cross-studio workflow;
- `task_id` — one orchestrated task;
- `artifact_id` — stable identity of an output or source artifact;
- `artifact_version` — immutable artifact revision;
- `asset_id` — reusable source asset identity;
- `distribution_id` — one destination-specific distribution record.

A studio-local ID must never be mistaken for a canonical Content OS ID.

### 3.2 Correlation and idempotency

Every integration request should carry:
- a stable request ID;
- workflow, task, content, and studio identifiers where applicable;
- an idempotency key for operations that may be retried;
- contract version;
- trace or correlation ID.

The Content OS should be able to trace a job from initial user request through studio execution, artifact registration, governance, and distribution outcome.

### 3.3 Tenant and workspace scope

The initial product is single-owner Creator Mode, but identifiers and APIs should include workspace scope from the start. This prevents later multi-workspace expansion from requiring every contract to be redesigned.

This does not mean implementing teams, multi-tenancy, or billing now.

---

## 4. Studio integration contract

Each studio adapter should implement a versioned capability contract.

### 4.1 Capability declaration

A studio registration should declare:

| Field | Meaning |
|---|---|
| `studio_id` | Stable studio identity |
| `studio_version` | Studio release or build identity |
| `supported_formats` | Formats it can create or process |
| `capabilities` | Supported operations, such as draft, render, inspect |
| `input_contracts` | Accepted job and artifact schemas |
| `output_contracts` | Produced artifact types and schemas |
| `execution_requirements` | CPU, memory, GPU, disk, network, or tool needs |
| `execution_locations` | Local, cloud, or both |
| `cancellation_support` | Supported cancellation behavior |
| `health_status` | Ready, busy, degraded, unavailable |
| `limits` | Concurrency and resource constraints |

Capabilities must be explicit. The orchestrator must not assume that a studio can perform an operation simply because it can process a related format.

### 4.2 Standard job envelope

Illustrative conceptual envelope:

```json
{
  "job_id": "job_<stable-id>",
  "workflow_id": "workflow_<stable-id>",
  "task_id": "task_<stable-id>",
  "workspace_id": "workspace_<stable-id>",
  "content_id": "content_<stable-id>",
  "studio_id": "shorts_studio",
  "operation": "produce",
  "contract_version": "1.0",
  "input_refs": [
    {
      "artifact_id": "artifact_<stable-id>",
      "version": 2,
      "role": "approved_script"
    }
  ],
  "constraints": {
    "format_profile": "vertical_short",
    "brand_profile_version": "brand_v1"
  },
  "output_requirements": {
    "artifact_types": ["video", "thumbnail", "production_manifest"]
  },
  "idempotency_key": "idem_<stable-id>",
  "deadline_at": "ISO-8601 timestamp"
}
```

The exact schema must be finalized alongside Part 3 and Part 4. Large binary files should be transferred through the artifact service, not embedded in job messages.

### 4.3 Standard job result

The adapter returns:
- job and correlation identifiers;
- studio and contract version;
- execution status;
- progress or stage information;
- artifact references;
- structured warnings and errors;
- manifest and provenance references;
- timestamps and execution metadata.

Possible outcomes:
- `accepted`;
- `running`;
- `completed`;
- `needs_input`;
- `needs_review`;
- `failed_retryable`;
- `failed_terminal`;
- `cancelled`.

The orchestrator validates the result and owns the authoritative workflow transition.

---

## 5. API surface

The following is a proposed logical API surface, not a finalized URL or implementation specification.

### 5.1 Content and context APIs

| Operation | Purpose |
|---|---|
| `GET content/{content_id}` | Retrieve authorized content metadata |
| `GET content/{content_id}/versions/{version}` | Retrieve a specific immutable version |
| `GET briefs/{brief_id}` | Retrieve approved brief and constraints |
| `GET brand-profiles/{profile_id}/versions/{version}` | Retrieve exact approved brand profile |
| `GET artifacts/{artifact_id}/versions/{version}` | Retrieve artifact metadata and authorized access reference |

### 5.2 Studio job APIs

| Operation | Purpose |
|---|---|
| `POST studio-jobs` | Submit a validated studio job |
| `GET studio-jobs/{job_id}` | Retrieve job status |
| `POST studio-jobs/{job_id}/events` | Submit progress or structured events |
| `POST studio-jobs/{job_id}/cancel` | Request cancellation |
| `POST studio-jobs/{job_id}/complete` | Submit final job result |

The completion endpoint must validate that all referenced artifacts are registered and accessible. A studio cannot mark a cross-platform workflow complete by writing an arbitrary status field.

### 5.3 Artifact APIs

| Operation | Purpose |
|---|---|
| `POST artifacts` | Register artifact metadata and initial version |
| `POST artifacts/{artifact_id}/versions` | Register a new immutable version |
| `GET artifacts/{artifact_id}` | Retrieve artifact metadata |
| `GET artifacts/{artifact_id}/versions/{version}` | Retrieve a specific version |
| `POST artifacts/{artifact_id}/access-grants` | Request scoped access to artifact bytes |
| `POST artifacts/{artifact_id}/validate` | Request integrity or schema validation |

### 5.4 Event APIs

Events may be delivered through a durable event mechanism or authenticated callback. Delivery semantics must be documented; consumers should assume duplicate delivery is possible and be idempotent.

Illustrative event types:
- `studio.job.accepted`;
- `studio.job.progressed`;
- `studio.job.completed`;
- `studio.job.failed`;
- `studio.job.cancelled`;
- `artifact.registered`;
- `artifact.version.created`;
- `artifact.validation.failed`;
- `studio.health.changed`.

Events are notifications, not the authoritative database. Consumers should resolve current state through the relevant service.

---

## 6. Artifact management

The artifact service provides a consistent way to register, version, locate, validate, and access generated files.

### 6.1 Artifact categories

Examples include:
- research briefs and evidence packages;
- scripts and narration text;
- storyboards and shot plans;
- raw footage, B-roll, images, audio, and music;
- voiceover and subtitle files;
- project files and intermediate renders;
- final videos, thumbnails, and cover images;
- carousels, articles, newsletters, and podcast audio;
- QA reports, manifests, and distribution packages.

Not every artifact is user-facing. Intermediate artifacts may have restricted access and retention.

### 6.2 Artifact metadata

Proposed fields:

| Field | Meaning |
|---|---|
| `artifact_id` | Stable identity |
| `workspace_id` | Workspace scope |
| `content_id` | Linked content item |
| `studio_id` | Producing studio, if applicable |
| `artifact_type` | Script, video, audio, image, report, manifest, etc. |
| `version` | Immutable version number |
| `storage_ref` | Opaque storage locator |
| `media_type` | MIME type |
| `file_size` | Byte size |
| `checksum` | Integrity hash |
| `created_at` | Creation timestamp |
| `created_by` | User, service, or agent identity |
| `source_refs` | Inputs used to produce this artifact |
| `manifest_ref` | Asset and production manifest |
| `rights_refs` | Relevant rights records |
| `quality_refs` | Evaluations associated with this version |
| `lifecycle_state` | Draft, active, superseded, archived, or quarantined |

The storage locator is not a public URL and should not be exposed as an unrestricted permanent download link.

### 6.3 Immutable versions

- Artifact identity may remain stable while its versions increase.
- Registered versions are immutable.
- Editing creates a new version.
- A version records its source inputs and production context.
- A version must not be silently replaced in place.
- Approval and quality records bind to the exact version and hash.
- Superseded versions remain traceable according to retention policy.

### 6.4 Artifact manifests

A production manifest should record:
- source inputs and versions;
- assets actually used;
- generated intermediate outputs;
- tool and renderer versions where relevant;
- output artifact references;
- checksums;
- relevant rights references;
- warnings and known limitations.

For video, the manifest should support shot-level or segment-level references where the studio can provide them. This supports traceability and later quality investigations.

### 6.5 Storage and access

The artifact service should abstract storage providers. A studio requests access through a scoped grant or signed transfer mechanism rather than assuming shared filesystem access.

Possible storage patterns:
- local worker cache for temporary processing;
- shared object storage for durable cross-worker artifacts;
- metadata and relationships in the canonical data store;
- controlled transfer for large files.

Local paths such as `/home/...` or `C:\...` are worker-local implementation details. They must not be stored as if they were globally accessible artifact locations.

### 6.6 Integrity and quarantine

On registration or transfer:
- verify file existence and expected size;
- calculate and record a checksum;
- validate declared media type against actual content where feasible;
- reject or quarantine malformed or suspicious files;
- ensure the registered manifest matches the produced outputs;
- avoid treating a filename extension as proof of file type.

If integrity validation fails, the artifact must not pass downstream gates.

---

## 7. Hybrid execution and worker integration

The locked deployment direction is hybrid: always-on cloud control plane with local and remote workers.

### 7.1 Control plane

The cloud control plane owns:
- canonical workflow and job state;
- job queue and scheduling;
- studio and worker registry;
- artifact metadata and durable references;
- governance and approval;
- event routing and audit history;
- dashboard and monitoring.

### 7.2 Execution plane

Workers execute tasks according to declared capability and resource requirements.

- Local worker: preferred for existing Shorts Studio and local FFmpeg-heavy rendering when the PC is available.
- Remote worker: suitable for cloud-supported research, lightweight tasks, coordination, and future remote rendering.
- Worker selection: based on capability, data access, availability, policy, and cost constraints.

### 7.3 PC offline behavior

When the local PC is offline:
- the cloud control plane continues to accept and manage supported jobs;
- remote-capable jobs may continue;
- local-only rendering jobs remain queued or move to an eligible remote worker if configured;
- the system must not claim local rendering completed while the PC was unavailable;
- when the local worker reconnects, it reconciles its state and resumes eligible work safely.

The control plane must not depend on the local PC to retain authoritative job state.

### 7.4 Worker-local cache

A local worker may cache artifacts for performance, but:
- the shared artifact registry remains authoritative;
- cache entries are disposable and re-downloadable where permitted;
- cache deletion must not delete durable artifacts;
- cache paths must never be exposed as universal references;
- workers must validate versions and hashes before use.

---

## 8. Shorts Studio integration boundary

The existing Shorts Studio is retained as a specialized production engine.

### 8.1 Report-backed current boundary

The existing report-based pipeline has been described as:

```text
pipelines/short.py
    -> app.script.pipeline.run()
        -> motion_render.render_video()
```

The current system uses file-based artifacts and legacy output locations. A run tracker is wired in `short.py`, but runtime integration was reported as unverified. A SQLite workspace-sync prototype was reported as not connected to the pipeline.

These are prior report findings, not a fresh repository inspection or current runtime verification.

### 8.2 Proposed adapter responsibilities

The future Shorts Studio adapter should:
1. Receive a Content OS studio-job envelope.
2. Resolve exact script, storyboard, shot-plan, brand, and asset references.
3. Map them to existing Shorts Studio inputs without changing internal production logic unnecessarily.
4. Invoke the approved production entry point.
5. Track execution and report structured progress.
6. Register output video, thumbnail, subtitles, QA report, and manifest as artifacts.
7. Return exact artifact versions and checksums.
8. Preserve local worker and renderer diagnostics.
9. Hand outputs to centralized governance.
10. Never publish directly.

### 8.3 Migration strategy

Prefer an adapter or wrapper boundary around the current engine.

Avoid:
- wholesale replacement of the production pipeline;
- moving every internal file into a new architecture at once;
- changing unrelated WIP;
- assuming the existing run tracker or database prototype is production-ready;
- coupling the engine to a cloud provider's SDK.

Migration should be incremental and validated against the current baseline after repository work is explicitly authorized.

### 8.4 Compatibility requirements

The adapter should tolerate:
- studio job retries;
- worker restarts;
- duplicate event delivery;
- missing or stale input references;
- artifact transfer interruption;
- cancellation requests;
- a workflow being paused while rendering continues.

A completed render must be registered once as an immutable artifact version even if completion notifications are delivered more than once.

---

## 9. Security and API governance

- Authenticate every studio and worker.
- Authorize every request against workspace, job, and artifact scope.
- Use short-lived credentials or grants for artifact transfers.
- Validate schemas and payload sizes.
- Rate-limit and bound job submission.
- Redact secrets from logs and diagnostics.
- Treat callbacks and events as untrusted until authenticated and validated.
- Enforce replay protection or idempotency for state-changing operations.
- Prevent studios from changing policy, approval, or authorization records.
- Keep distribution credentials inside the dedicated publishing boundary.
- Version APIs and define compatibility/deprecation rules.

---

## 10. Observability and operational diagnostics

For each studio job, capture:
- workflow, task, job, and correlation IDs;
- studio and adapter versions;
- worker identity and execution location;
- input artifact references and versions;
- stage transitions and progress;
- output artifact references and hashes;
- start, heartbeat, completion, and failure timestamps;
- resource use and cost where available;
- retries and cancellation outcomes;
- validation and governance handoff results.

Dashboards should distinguish:
- queued;
- waiting for a local worker;
- waiting for a remote worker;
- running;
- transferring artifacts;
- validating;
- awaiting review;
- completed;
- failed;
- cancelled.

A studio's “100% complete” progress report does not by itself mean the Content OS workflow is complete.

---

## 11. Technology choices and open decisions

No specific API framework, object-storage provider, message broker, or serialization format is selected here.

Decisions still required:
1. Synchronous API versus event-first integration for each operation.
2. REST, RPC, or a mixed interface.
3. Event transport and delivery guarantees.
4. Object-storage provider and local development equivalent.
5. Artifact transfer protocol for large files.
6. API authentication and worker identity mechanism.
7. Schema registry and compatibility strategy.
8. Artifact retention, archival, and deletion policy.
9. Whether the first Shorts adapter runs in-process or as a separate worker service.
10. How to reconcile current file-based outputs with canonical artifact registration.
11. Whether long-form production should reuse any Shorts components or remain a separate engine.
12. Which studio capabilities are eligible for remote execution.

Select technologies only after comparing operational complexity, local development fit, reliability, cost, security, and portability.

---

## 12. Implementation sequence

### Stage A — Contracts and registry
- Define canonical studio and artifact schemas.
- Define capability registration.
- Define job submission and result contracts.
- Define event and idempotency behavior.

### Stage B — Artifact foundation
- Implement immutable artifact versions.
- Add checksum and media validation.
- Add scoped access and transfer.
- Establish durable storage and metadata references.

### Stage C — First studio adapter
- Build a thin Shorts Studio adapter around the existing engine.
- Map inputs and outputs.
- Register artifacts and manifests.
- Validate local worker reconnect and retry behavior.
- Keep all publishing disabled during integration testing.

### Stage D — Additional studios
- Add long-form and other studios through the same contracts.
- Share content identity, brand context, assets, and governance.
- Keep format-specific production logic inside each studio.

### Stage E — Operational hardening
- Add monitoring, failure injection, security tests, and recovery.
- Test duplicate events, partial transfers, stale artifacts, and worker loss.
- Validate that all external distribution remains behind Part 6 authorization.

This sequence is a proposal, not an implementation authorization.

---

## 13. Acceptance criteria

Part 7 is ready to guide implementation when:

- [ ] Content OS and studio ownership boundaries are explicit.
- [ ] Every studio declares versioned capabilities and contracts.
- [ ] Jobs carry canonical IDs, correlation IDs, and idempotency keys.
- [ ] The orchestrator owns authoritative workflow state.
- [ ] Artifacts have immutable versions, hashes, and provenance.
- [ ] Large files use controlled artifact transfer rather than job payloads.
- [ ] Worker-local paths are not treated as global artifact references.
- [ ] Local and remote workers use the same job and artifact contracts.
- [ ] PC-offline behavior is explicit and truthful.
- [ ] Shorts Studio can be integrated through a thin adapter without wholesale replacement.
- [ ] Studio completion cannot bypass centralized quality, rights, and approval governance.
- [ ] No studio can publish without Part 6 authorization.
- [ ] Duplicate events and retries do not create duplicate artifacts or external side effects.
- [ ] Security, observability, and recovery tests are defined.
- [ ] No repository or production work is inferred from this document.

---

## 14. Relationship to the other architecture parts

| Part | Relationship |
|---|---|
| Part 1 — System Architecture Master Reference | Defines overall Content OS and specialized studio model |
| Part 2 — Shorts Studio Pipeline Contract | Defines the existing Shorts production pipeline and integration boundary |
| Part 3 — Shared Data Model & Content Graph | Defines canonical identities, versions, relationships, and artifact metadata |
| Part 4 — Persistent Job Queue, Scheduler & Worker Architecture | Executes and recovers studio jobs across local and remote workers |
| Part 5 — Agent Contracts & Orchestration | Defines bounded agent tasks that may request studio operations |
| Part 6 — Centralized Quality, Rights, Approval & Publishing Governance | Controls eligibility and authorization for external distribution |
| Part 7 — Studio Integration APIs & Artifact Management | Connects specialized studios to shared services and manages durable outputs |

**Next architecture document:** Part 8 — Hybrid Deployment, Security, Monitoring, Backup & Recovery.

---

**Document status:** Proposed architecture baseline. No implementation, repository access, code modification, deployment, account change, upload, or publishing authorization is granted by this document.
