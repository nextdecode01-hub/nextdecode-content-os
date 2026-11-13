# NEXTDECODE Content OS
## Canonical Contracts Pack 1.0

**Document status:** Proposed contract baseline — approval pending  
**Version:** 1.0  
**Prepared:** 31 October 2026  
**Scope:** Canonical identities, state machines, task/job/studio envelopes, events and idempotency, artifact/asset/manifest records, governance decisions and authorization, and acceptance tests.

> **Important:** This pack translates the existing NEXTDECODE Blueprint 2.0, Architecture Parts 1–8, and Architecture Reconciliation & Implementation Readiness Report into concrete contract proposals. It is not evidence of implementation, a finalized database schema, or permission to inspect or modify the repository, perform Git operations, deploy infrastructure, spend money, upload, or publish.

---

# 0. How to use this pack

## 0.1 Status vocabulary

| Label | Meaning |
|---|---|
| **LOCKED** | Explicitly selected by the product owner in prior decisions. |
| **PROPOSED BASELINE** | Recommended contract for review; not yet approved as a final implementation contract. |
| **OPEN** | Requires a product or technical decision. |
| **DEFERRED** | Intentionally postponed; do not implement in the initial foundation unless separately approved. |
| **REPORT-BACKED** | Describes existing-system findings from prior reconciliation reports, not a fresh repository inspection. |

## 0.2 Contract principles

1. The cloud control plane owns authoritative shared workflow, identity, policy, approval, and distribution state.
2. Workers execute assigned work; they do not own global workflow state.
3. Agents perform bounded tasks; they do not grant themselves permissions or approve their own work.
4. The orchestrator coordinates workflow progression. The scheduler determines when work becomes eligible. The queue durably stores eligible work. Workers execute it.
5. A content idea, content item, studio job, workflow job, artifact, asset, and publication are distinct entities.
6. IDs are stable and globally unique; human-readable prefixes are labels, not uniqueness guarantees.
7. Versions that have been registered are immutable. Changes create new versions.
8. Events are notifications, not the authoritative source of current state.
9. Duplicate delivery and retries are expected. State-changing consumers must be idempotent.
10. Approval is bound to the exact content/artifact versions and policy version reviewed.
11. Approval and authorization are separate: an approval decision does not itself grant a worker unrestricted permission to publish.
12. Large media binaries travel through controlled artifact transfer, not queue messages.
13. Hard rights, safety, integrity, or policy blockers cannot be overridden by ordinary editorial approval.
14. A user's unavailability is never interpreted as consent or approval.

## 0.3 Compatibility and authority

This pack proposes logical contracts, not specific vendors, database tables, endpoint URLs, queue products, serialization libraries, or cloud providers. Those remain open unless explicitly marked locked elsewhere.

If two documents appear to conflict:
- the later explicit owner decision takes precedence over earlier assumptions;
- the reconciliation report's proposed resolutions are recommendations, not automatic approvals;
- do not silently convert a proposal into a locked decision;
- record any accepted change in a versioned Architecture Decision Record (ADR).

---

# 1. Entity and ID glossary

## 1.1 Canonical entity glossary

| Entity | Canonical meaning | Must not be confused with |
|---|---|---|
| Workspace | Top-level owner-controlled operating boundary | Brand |
| Brand | Identity, voice, audience, rules, and positioning used by content | Workspace |
| Topic | Subject area or issue that may generate ideas | Content Idea |
| Content Idea | A candidate editorial concept, before format-specific production | Content Item |
| Research Package | Versioned research synthesis and its provenance | Source or Evidence Item |
| Source | Original origin of information (article, report, dataset, interview, etc.) | Evidence Item |
| Evidence Item | Extracted/located information relevant to a claim | Claim |
| Claim | A factual or interpretive assertion proposed for content | Evidence Item |
| Content Brief | Approved or draft instructions for a specific content item | Research Package |
| Content Item | A format-specific editorial product with its own lifecycle | File, artifact, or social post |
| Content Variant | A distinct version/derivative of a content item for a platform, audience, language, or treatment | A new idea by default |
| Workflow Definition | Versioned description of a process | Workflow Run |
| Workflow Run | One execution instance of a workflow definition | Job |
| Task | Logical bounded unit of work requested by a workflow/agent | Job Attempt |
| Job | Durable executable unit assigned to a worker | Workflow Run |
| Job Attempt | One execution attempt for a job | Job |
| Studio | Specialized format/production capability boundary | Worker |
| Studio Job | A studio-scoped production request, linked to a canonical job | Content Item |
| Worker | Authenticated execution process (local or remote) | Agent |
| Agent | Bounded reasoning/transformation capability | Orchestrator |
| Asset | Reusable source or licensed media element with provenance and rights | Artifact |
| Artifact | Registered output/input file or structured deliverable | Asset |
| Artifact Version | Immutable registered revision of an artifact | Mutable working file |
| Manifest | Structured record of inputs, assets, tools, outputs, and provenance for a production | Artifact binary |
| QA Run | One execution of a defined quality evaluation | Approval |
| QA Result | Findings produced by a QA run against exact targets | Approval Decision |
| Rights Assessment | Evaluation of permitted use for an asset/artifact and context | License text alone |
| Review Package | Exact set of versions and evidence presented for human/policy review | Approval |
| Approval Request | Request for a decision against a defined review package | Authorization grant |
| Approval Decision | Immutable allow/reject/changes-requested decision | Publishing credential |
| Authorization Grant | Scoped, time-bounded permission for a specific action | Editorial approval |
| Policy / Policy Version | Rules governing eligibility and allowed actions | Workflow state |
| Event | Immutable notification/fact that something happened | Current state record |
| Publication Request | Intent to distribute an approved version to a destination | Publication |
| Publication | External platform's resulting post/video/article identity and status | Publication Attempt |
| Publication Attempt | One delivery attempt, including provider response | Publication |
| Metric Snapshot | Time-bounded metrics captured for a publication | Learning Insight |
| Learning Insight | Interpreted finding derived from performance and context | Raw metric |

## 1.2 Identity hierarchy

**PROPOSED BASELINE**

```text
Workspace
└── Brand
    └── Topic
        └── Content Idea
            ├── Research Package (one or more versions)
            └── Content Item (one or more format-specific items)
                ├── Content Variant(s)
                ├── Brief / Script / Storyboard / Shot Plan versions
                ├── Studio Job(s)
                │   └── Job Attempt(s)
                ├── Asset references + Rights Assessments
                ├── Artifact(s)
                │   └── Artifact Version(s)
                ├── QA Run(s) + QA Results
                ├── Review Package(s)
                ├── Approval Request(s) + Decision(s)
                └── Publication Request(s)
                    └── Publication(s)
                        └── Publication Attempt(s) + Metric Snapshot(s)
```

A workflow can span multiple content items and jobs. A job can exist for non-content operational work, but must have an explicit parent or purpose. Do not infer parentage from filenames or directory layout.

## 1.3 ID convention

**PROPOSED BASELINE**

- Use globally unique identifiers. UUIDv7 is the preferred candidate where the selected stack supports it; final ID technology remains open.
- Optional type prefixes improve readability but are not the uniqueness mechanism.
- IDs are immutable and never reused, including after archival or deletion.
- Never derive identity solely from array position, filename, timestamp, title, or platform post ID.
- A platform's external ID is stored as an external identifier, not substituted for the internal canonical ID.
- IDs must remain stable across local and cloud workers.

| Entity | Suggested prefix |
|---|---|
| Workspace | `wsp_` |
| Brand | `brd_` |
| Topic | `top_` |
| Content Idea | `ide_` |
| Research Package | `res_` |
| Source | `src_` |
| Evidence Item | `evd_` |
| Claim | `clm_` |
| Brief | `brf_` |
| Content Item | `cnt_` |
| Content Variant | `var_` |
| Workflow Definition | `wfd_` |
| Workflow Run | `wfr_` |
| Task | `tsk_` |
| Job | `job_` |
| Job Attempt | `jat_` |
| Studio | `std_` |
| Studio Job | `stj_` |
| Worker | `wrk_` |
| Agent | `agt_` |
| Asset | `ast_` |
| Artifact | `art_` |
| Manifest | `man_` |
| QA Run | `qar_` |
| Review Package | `rvp_` |
| Approval Request | `apr_` |
| Approval Decision | `apd_` |
| Authorization Grant | `azg_` |
| Policy | `pol_` |
| Event | `evt_` |
| Publication Request | `pbr_` |
| Publication | `pub_` |
| Publication Attempt | `pat_` |

## 1.4 Common record envelope

**PROPOSED BASELINE**

Every durable record should include the fields applicable to its entity type:

```json
{
  "id": "cnt_<globally-unique-id>",
  "workspace_id": "wsp_<globally-unique-id>",
  "schema_version": "1.0",
  "record_version": 1,
  "created_at": "2026-10-31T12:00:00Z",
  "updated_at": "2026-10-31T12:00:00Z",
  "created_by": {
    "type": "user",
    "id": "owner"
  },
  "updated_by": {
    "type": "service",
    "id": "content-service"
  },
  "status": "draft",
  "provenance_refs": []
}
```

Rules:
- `schema_version` describes the shape/contract of the record.
- `record_version` is a concurrency/revision token for the mutable record.
- Immutable content versions use an explicit version number or immutable version ID.
- `created_by` and `updated_by` identify actors, not display names.
- `status` is entity-specific; do not use one universal enum for all records.
- Timestamps are UTC ISO 8601/RFC 3339 values. The exact timestamp precision is an implementation choice.

## 1.5 Content Item minimum contract

**PROPOSED BASELINE**

```json
{
  "id": "cnt_<id>",
  "workspace_id": "wsp_<id>",
  "brand_id": "brd_<id>",
  "content_idea_id": "ide_<id>",
  "format": "short_video",
  "studio_id": "shorts_studio",
  "channel_intents": ["youtube_shorts", "instagram_reels"],
  "brief_ref": {
    "artifact_id": "art_<id>",
    "version": 2
  },
  "research_package_refs": [
    {"research_package_id": "res_<id>", "version": 3}
  ],
  "brand_profile_ref": {
    "brand_id": "brd_<id>",
    "version": 4
  },
  "claim_refs": ["clm_<id>"],
  "workflow_run_refs": ["wfr_<id>"],
  "current_production_ref": "stj_<id>",
  "current_review_package_ref": null,
  "current_publication_refs": [],
  "lifecycle_status": "planned",
  "schema_version": "1.0",
  "record_version": 1
}
```

A Content Item is not a file, not a studio job, and not a platform publication. It is the format-specific editorial object that connects them.

---

# 2. Canonical state machines

## 2.1 State machine rules

**PROPOSED BASELINE**

- Each entity owns its own state machine.
- A transition must be validated by the authoritative service for that entity.
- Transitions record actor, timestamp, reason, correlation ID, and relevant version/policy references.
- Terminal states are terminal unless a documented recovery/new-instance path exists.
- Do not make state changes by editing arbitrary status fields from workers or agents.
- `record_version` or equivalent optimistic concurrency prevents stale updates.
- A failed gate must not be silently converted into a pass by an unrelated workflow transition.

## 2.2 Content Item lifecycle

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

Transition guidance:

| From | To | Minimum condition |
|---|---|---|
| IDEA | PLANNED | Editorial selection recorded |
| PLANNED | BRIEF_READY | Brief exists and required context is linked |
| BRIEF_READY | IN_PRODUCTION | Eligible studio/workflow accepted |
| IN_PRODUCTION | QA_PENDING | Required production outputs registered |
| QA_PENDING | REVIEW_PENDING | Required QA gates meet policy |
| QA_PENDING | BLOCKED | A blocking quality/rights/safety failure exists |
| REVIEW_PENDING | APPROVED | Required decision(s) recorded against exact versions |
| REVIEW_PENDING | CHANGES_REQUESTED | Reviewer requests a revision |
| REVIEW_PENDING | REJECTED | Reviewer rejects the reviewed package |
| APPROVED | SCHEDULED | Distribution policy and authorization permit scheduling |
| SCHEDULED | PUBLISHED | External publication is confirmed and recorded |
| PUBLISHED | ANALYZING | Measurement window or analytics workflow begins |
| ANALYZING | ARCHIVED | Retention/analysis completion conditions met |

Important:
- `APPROVED` is not the same as `AUTHORIZED_TO_PUBLISH`.
- A material change to an approved artifact requires a new review decision or an explicitly defined policy path.
- A new format-specific Content Item may be created from the same Content Idea.
- `BLOCKED` requires an explicit blocker record; ordinary editorial approval cannot clear hard rights/safety/integrity blockers.

## 2.3 Workflow Run state

**PROPOSED BASELINE**

```text
CREATED -> READY -> RUNNING -> SUCCEEDED
                    |   |
                    |   +-> WAITING
                    |   +-> PAUSED
                    |   +-> FAILED
                    |   +-> CANCEL_REQUESTED -> CANCELLED
                    +------> BLOCKED
```

Recommended enum:
`CREATED`, `READY`, `RUNNING`, `WAITING`, `PAUSED`, `BLOCKED`, `CANCEL_REQUESTED`, `CANCELLED`, `FAILED`, `SUCCEEDED`.

A workflow may be `WAITING` for a human decision, a schedule, a local worker, an external provider, or another dependency. The wait reason must be explicit.

## 2.4 Job state

**PROPOSED BASELINE**

```text
CREATED -> QUEUED -> LEASED -> RUNNING -> SUCCEEDED
                       |         |
                       |         +-> RETRY_WAIT -> QUEUED
                       |         +-> FAILED
                       |         +-> CANCEL_REQUESTED -> CANCELLED
                       +-> LEASE_EXPIRED -> QUEUED
```

Recommended enum:
`CREATED`, `QUEUED`, `LEASED`, `RUNNING`, `RETRY_WAIT`, `CANCEL_REQUESTED`, `CANCELLED`, `SUCCEEDED`, `FAILED`, `DEAD_LETTERED`.

Rules:
- A retry creates a new Job Attempt; it does not erase the previous attempt.
- Lease expiry permits reassignment only after authoritative validation.
- A stale worker cannot complete a job after its lease/attempt has been superseded.
- `DEAD_LETTERED` means automatic retries are exhausted or disallowed and explicit intervention is needed.
- Retryability is an error classification/policy decision, not a free-form worker preference.

## 2.5 Job Attempt state

`CREATED`, `STARTED`, `HEARTBEATING`, `SUCCEEDED`, `FAILED_RETRYABLE`, `FAILED_TERMINAL`, `LEASE_LOST`, `CANCELLED`, `ABANDONED`.

Attempt records are append-only execution history. Never reuse an attempt number for the same job.

## 2.6 Worker state

`REGISTERED`, `READY`, `BUSY`, `DEGRADED`, `OFFLINE`, `REVOKED`.

Worker status is operational health, not job state. A worker can go offline while a job remains queued or leased until lease expiry/reconciliation.

## 2.7 Studio Job state

`SUBMITTED`, `ACCEPTED`, `RUNNING`, `NEEDS_INPUT`, `NEEDS_REVIEW`, `COMPLETED`, `FAILED_RETRYABLE`, `FAILED_TERMINAL`, `CANCEL_REQUESTED`, `CANCELLED`.

The Studio Job state is scoped to the studio operation. It does not independently determine the parent Content Item, Workflow Run, QA, approval, or publication state.

## 2.8 Governance state distinctions

| Record | Example states |
|---|---|
| QA Run | `PENDING`, `RUNNING`, `PASS`, `PASS_WITH_WARNINGS`, `FAIL`, `ERROR` |
| Rights Assessment | `UNKNOWN`, `PENDING`, `CLEARED`, `RESTRICTED`, `BLOCKED`, `EXPIRED` |
| Review Package | `DRAFT`, `READY`, `SUPERSEDED`, `WITHDRAWN` |
| Approval Request | `PENDING`, `APPROVED`, `REJECTED`, `CHANGES_REQUESTED`, `EXPIRED`, `WITHDRAWN` |
| Authorization Grant | `ACTIVE`, `EXPIRED`, `REVOKED`, `CONSUMED` |
| Publication Request | `DRAFT`, `ELIGIBLE`, `PENDING_APPROVAL`, `AUTHORIZED`, `SCHEDULED`, `SUBMITTING`, `PUBLISHED`, `FAILED`, `CANCELLED`, `BLOCKED` |
| Publication Attempt | `CREATED`, `SUBMITTING`, `CONFIRMED`, `FAILED_RETRYABLE`, `FAILED_TERMINAL`, `UNKNOWN_OUTCOME` |

`UNKNOWN_OUTCOME` is important: a network timeout after a provider accepted a post must trigger reconciliation before retrying, or duplicate publication may occur.

## 2.9 State transition record

**PROPOSED BASELINE**

```json
{
  "transition_id": "evt_<id>",
  "entity_type": "job",
  "entity_id": "job_<id>",
  "from_state": "LEASED",
  "to_state": "RUNNING",
  "actor": {"type": "worker", "id": "wrk_<id>"},
  "reason_code": "worker_started",
  "reason": null,
  "occurred_at": "2026-10-31T12:01:00Z",
  "expected_record_version": 4,
  "resulting_record_version": 5,
  "correlation_id": "cor_<id>"
}
```

---

# 3. Task, job, and studio API envelopes

## 3.1 Responsibility boundaries

| Component | Owns | Must not own |
|---|---|---|
| Orchestrator | Workflow progression, dependencies, task creation, retry/timeout decisions | Unrestricted creative truth or permission escalation |
| Scheduler | Due-time and trigger eligibility | Full workflow progression |
| Queue | Durable eligible work and delivery metadata | Policy approval or business decisions |
| Worker | Execution of assigned job and reporting results | Authoritative global workflow state |
| Agent | Bounded reasoning/transformation output | Global workflow state, self-approval, permission escalation |
| Studio adapter | Translate canonical studio contract to/from studio-specific execution | Cross-platform workflow completion or publishing authorization |
| Policy/gate service | Deterministic policy evaluation | Creative generation |
| Approval service | Record authenticated decision against review package | Granting arbitrary worker permissions |
| Publishing service | Execute authorized external distribution | Deciding that an unapproved item is eligible |

## 3.2 Task envelope

A Task is a logical request for bounded work. It may be executed by an agent, deterministic service, or studio.

**PROPOSED BASELINE**

```json
{
  "task_id": "tsk_<id>",
  "workspace_id": "wsp_<id>",
  "workflow_run_id": "wfr_<id>",
  "parent_task_id": null,
  "content_item_id": "cnt_<id>",
  "task_type": "research.synthesize",
  "task_contract_version": "1.0",
  "objective": "Synthesize the approved research inputs into a structured brief.",
  "input_refs": [
    {"entity_type": "research_package", "id": "res_<id>", "version": 3}
  ],
  "required_capabilities": ["research_synthesis"],
  "constraints": {
    "allowed_sources": ["provided_research_refs"],
    "must_preserve_citations": true
  },
  "expected_output_schema": "research_synthesis_result.v1",
  "idempotency_key": "task:<workflow-run-id>:research.synthesize:v1",
  "correlation_id": "cor_<id>",
  "deadline_at": null,
  "created_at": "2026-10-31T12:00:00Z"
}
```

Task output must be structured and validated. Free-form agent text may be included as a field, but it is not a substitute for required typed outputs, references, or provenance.

## 3.3 Job envelope

A Job is the durable executable unit delivered to a worker.

**PROPOSED BASELINE**

```json
{
  "job_id": "job_<id>",
  "workspace_id": "wsp_<id>",
  "workflow_run_id": "wfr_<id>",
  "task_id": "tsk_<id>",
  "content_item_id": "cnt_<id>",
  "studio_job_id": "stj_<id>",
  "job_type": "studio.produce",
  "contract_version": "1.0",
  "input_refs": [
    {
      "entity_type": "artifact",
      "artifact_id": "art_<id>",
      "version": 2,
      "role": "approved_script"
    }
  ],
  "required_capabilities": ["short_video_render"],
  "execution_requirements": {
    "location": ["local"],
    "cpu": null,
    "memory_mb": null,
    "gpu": "optional",
    "disk_mb": null
  },
  "priority": "normal",
  "scheduled_at": "2026-10-31T12:00:00Z",
  "deadline_at": null,
  "attempt_count": 0,
  "max_attempts": 3,
  "idempotency_key": "studio.produce:<studio-job-id>:v1",
  "policy_version_refs": [],
  "correlation_id": "cor_<id>",
  "trace_id": "trc_<id>",
  "status": "QUEUED",
  "created_at": "2026-10-31T12:00:00Z"
}
```

Rules:
- `input_refs` identify exact versions, not “latest”.
- `execution_requirements.location` is a capability constraint, not a promise that a worker is currently available.
- Large binary payloads are never embedded in the job message.
- Credentials are never included in the job payload. Use scoped secret/transfer grants.
- `attempt_count` is derived/maintained by the authoritative job service and cannot be trusted from a worker's self-report.

## 3.4 Worker lease and assignment envelope

**PROPOSED BASELINE**

```json
{
  "job_id": "job_<id>",
  "job_attempt_id": "jat_<id>",
  "worker_id": "wrk_<id>",
  "lease_id": "lea_<id>",
  "lease_expires_at": "2026-10-31T12:10:00Z",
  "lease_generation": 2,
  "allowed_operations": ["read_assigned_inputs", "write_job_outputs", "report_progress"],
  "input_access_grants": ["grant_<short-lived-token-reference>"],
  "policy_snapshot_ref": "pol_<id>:version:5",
  "correlation_id": "cor_<id>"
}
```

- Lease tokens are opaque and short-lived.
- Lease renewal is validated server-side.
- A worker cannot renew a revoked or superseded lease.
- A result from an expired lease is quarantined for reconciliation; it must not overwrite authoritative state.
- Lease duration, heartbeat interval, and renewal policy remain open implementation decisions.

## 3.5 Standard job result envelope

**PROPOSED BASELINE**

```json
{
  "job_id": "job_<id>",
  "job_attempt_id": "jat_<id>",
  "worker_id": "wrk_<id>",
  "studio_id": "shorts_studio",
  "studio_version": "reported-build-id",
  "contract_version": "1.0",
  "outcome": "completed",
  "progress": {
    "stage": "artifact_registration",
    "percent": 100
  },
  "output_refs": [
    {"artifact_id": "art_<id>", "version": 1, "role": "final_video"},
    {"artifact_id": "art_<id>", "version": 1, "role": "production_manifest"}
  ],
  "warning_codes": [],
  "error": null,
  "started_at": "2026-10-31T12:01:00Z",
  "completed_at": "2026-10-31T12:08:00Z",
  "correlation_id": "cor_<id>"
}
```

Allowed outcome values:
- `accepted`
- `running`
- `completed`
- `needs_input`
- `needs_review`
- `failed_retryable`
- `failed_terminal`
- `cancelled`

The orchestrator validates the result, checks lease/attempt identity, verifies output references, and owns the authoritative transition.

## 3.6 Studio capability declaration

**PROPOSED BASELINE**

```json
{
  "studio_id": "shorts_studio",
  "studio_version": "adapter-contract-version",
  "supported_formats": ["short_video"],
  "capabilities": ["draft", "storyboard", "render", "inspect"],
  "input_contracts": ["shorts_production_input.v1"],
  "output_contracts": ["shorts_production_result.v1"],
  "execution_requirements": {
    "locations": ["local"],
    "ffmpeg": true,
    "gpu": "optional"
  },
  "cancellation_support": "best_effort",
  "health_status": "ready",
  "limits": {
    "max_concurrency": 1
  }
}
```

Capabilities must be explicit. The orchestrator must not infer a capability from a studio name or a related format.

## 3.7 Studio Job submission envelope

**PROPOSED BASELINE**

```json
{
  "studio_job_id": "stj_<id>",
  "job_id": "job_<id>",
  "workspace_id": "wsp_<id>",
  "content_item_id": "cnt_<id>",
  "studio_id": "shorts_studio",
  "operation": "produce",
  "contract_version": "1.0",
  "input_refs": [
    {"artifact_id": "art_<id>", "version": 2, "role": "script"},
    {"artifact_id": "art_<id>", "version": 1, "role": "storyboard"}
  ],
  "constraints": {
    "format_profile": "vertical_short",
    "brand_profile_ref": {"brand_id": "brd_<id>", "version": 4}
  },
  "output_requirements": {
    "artifact_types": ["video", "thumbnail", "subtitle", "production_manifest"]
  },
  "idempotency_key": "shorts:<content-item-id>:produce:<revision>",
  "correlation_id": "cor_<id>"
}
```

## 3.8 API surface — logical only

The following operations are proposed logical interfaces, not approved endpoint paths or an API framework selection.

| Operation | Purpose |
|---|---|
| Read content item/version | Retrieve authorized canonical metadata |
| Read brief/brand/research version | Resolve exact approved context |
| Submit studio job | Validate and enqueue a studio operation |
| Read studio job | Retrieve current studio job state |
| Report progress/event | Submit authenticated progress |
| Request cancellation | Request controlled cancellation |
| Submit completion | Submit result for server-side validation |
| Register artifact/version | Register metadata and immutable version |
| Request artifact access grant | Obtain scoped access to bytes |
| Validate artifact | Request integrity/schema/media checks |
| Request QA run | Evaluate exact target versions |
| Create review package | Freeze exact review inputs |
| Submit approval decision | Record authorized human/policy decision |
| Create publication request | Request distribution evaluation |
| Execute authorized publication | Perform provider side effect only after authorization |

## 3.9 Error envelope

**PROPOSED BASELINE**

```json
{
  "error": {
    "code": "INPUT_VERSION_NOT_FOUND",
    "message": "The requested immutable input version is unavailable.",
    "retryable": false,
    "details": {
      "entity_type": "artifact",
      "entity_id": "art_<id>",
      "requested_version": 3
    }
  },
  "correlation_id": "cor_<id>",
  "occurred_at": "2026-10-31T12:02:00Z"
}
```

Error messages and details must be sanitized. Never expose access tokens, provider secrets, environment variables, private keys, or raw credential-bearing URLs.

---

# 4. Event envelope and idempotency rules

## 4.1 Event envelope

**PROPOSED BASELINE**

```json
{
  "event_id": "evt_<globally-unique-id>",
  "event_type": "studio.job.completed",
  "event_schema_version": "1.0",
  "occurred_at": "2026-10-31T12:08:00Z",
  "recorded_at": "2026-10-31T12:08:01Z",
  "producer": {
    "type": "studio_adapter",
    "id": "shorts_studio"
  },
  "workspace_id": "wsp_<id>",
  "aggregate": {
    "type": "studio_job",
    "id": "stj_<id>",
    "version": 5
  },
  "workflow_run_id": "wfr_<id>",
  "job_id": "job_<id>",
  "job_attempt_id": "jat_<id>",
  "correlation_id": "cor_<id>",
  "causation_id": "evt_<parent-event-id>",
  "idempotency_key": "studio-job-completed:<studio-job-id>:<attempt-id>",
  "payload": {
    "outcome": "completed",
    "output_refs": [
      {"artifact_id": "art_<id>", "version": 1}
    ]
  }
}
```

## 4.2 Event rules

1. Every event has a unique `event_id`.
2. Every event has a versioned type/schema.
3. Events identify the aggregate/entity and its version.
4. Events include workspace and correlation context where applicable.
5. `occurred_at` is when the event happened; `recorded_at` is when the control plane persisted it.
6. Events are append-only. Corrections are new events, not silent edits.
7. Consumers assume at-least-once delivery and possible reordering.
8. Consumers deduplicate by event ID and apply aggregate-version checks.
9. Events notify consumers that something happened; consumers query the authoritative service for current state before consequential actions.
10. Event transport, ordering guarantees, retention, and replay mechanism remain open technology decisions.

## 4.3 Idempotency model

Idempotency must be applied at multiple layers:

| Layer | Key/guard | Purpose |
|---|---|---|
| API command | Client-supplied or server-issued idempotency key + operation scope | Prevent duplicate command creation |
| Job creation | Workflow/task/operation identity | Prevent duplicate logical jobs |
| Job execution | Job ID + attempt ID + lease generation | Prevent stale attempt completion |
| Event consumer | Event ID + consumer identity | Prevent duplicate event effects |
| Artifact registration | Producer operation + content hash + output role/version policy | Prevent duplicate registration |
| Publication | Publication request ID + destination + provider reconciliation identity | Prevent duplicate external posts |

Rules:
- Same idempotency key and same normalized request: return the prior result.
- Same key with materially different request body: reject with an idempotency conflict.
- Idempotency records must be retained at least as long as the associated operation can be retried or reconciled; exact retention is open.
- A network timeout is not proof that an external side effect failed.
- For provider `UNKNOWN_OUTCOME`, reconcile provider state before retrying.
- Never rely only on a client-side button lock to prevent duplicates.

## 4.4 Outbox/inbox recommendation

**PROPOSED BASELINE — implementation pattern open**

Use a transactional outbox or equivalent durable pattern so a state change and its event cannot silently diverge. Consumers should maintain an inbox/deduplication record or equivalent idempotent processing guard.

This is a reliability requirement, not a selection of a specific broker or database feature.

## 4.5 Event type naming

Suggested names:
- `workflow.run.created`
- `workflow.run.started`
- `workflow.run.paused`
- `workflow.run.completed`
- `job.queued`
- `job.leased`
- `job.started`
- `job.retry_scheduled`
- `job.lease_expired`
- `job.completed`
- `job.failed`
- `worker.status_changed`
- `studio.job.accepted`
- `studio.job.progressed`
- `studio.job.completed`
- `studio.job.failed`
- `artifact.registered`
- `artifact.version.created`
- `artifact.validation.failed`
- `qa.run.completed`
- `rights.assessment.changed`
- `approval.requested`
- `approval.decided`
- `authorization.granted`
- `authorization.revoked`
- `publication.requested`
- `publication.authorized`
- `publication.submitted`
- `publication.confirmed`
- `publication.outcome_unknown`
- `publication.failed`
- `analytics.snapshot.recorded`

---

# 5. Artifact, asset, and manifest schemas

## 5.1 Distinguish the three concepts

| Concept | Meaning | Example |
|---|---|---|
| Asset | Reusable media/source element with origin and rights context | Licensed stock footage, original logo, music track |
| Artifact | A registered file or structured output with immutable versions | Script PDF, rendered MP4, subtitle file, QA report |
| Manifest | Structured provenance record describing a production and its inputs/outputs | Which shots, footage, music, tools, and versions produced a video |

A raw asset can itself be stored as an artifact binary, but its semantic role and rights lifecycle remain an Asset record. Do not collapse the two entities.

## 5.2 Artifact record

**PROPOSED BASELINE**

```json
{
  "artifact_id": "art_<id>",
  "workspace_id": "wsp_<id>",
  "content_item_id": "cnt_<id>",
  "studio_id": "shorts_studio",
  "artifact_type": "final_video",
  "media_type": "video/mp4",
  "lifecycle_state": "active",
  "current_version": 1,
  "created_at": "2026-10-31T12:08:00Z",
  "created_by": {"type": "worker", "id": "wrk_<id>"},
  "source_refs": [
    {"entity_type": "artifact", "id": "art_<script-id>", "version": 2}
  ],
  "manifest_ref": {"manifest_id": "man_<id>", "version": 1},
  "rights_refs": [],
  "quality_refs": [],
  "approval_refs": [],
  "schema_version": "1.0"
}
```

## 5.3 Immutable artifact version

**PROPOSED BASELINE**

```json
{
  "artifact_id": "art_<id>",
  "version": 1,
  "artifact_version_id": "arv_<id>",
  "storage_ref": {
    "provider": "abstract-storage-provider",
    "object_key": "opaque/object/key",
    "region": null
  },
  "media_type": "video/mp4",
  "file_size_bytes": 48200123,
  "checksum": {
    "algorithm": "sha256",
    "value": "<64-character-hex-digest>"
  },
  "created_at": "2026-10-31T12:08:00Z",
  "producer": {
    "type": "studio_adapter",
    "id": "shorts_studio",
    "version": "reported-build-id"
  },
  "input_refs": [
    {"artifact_id": "art_<id>", "version": 2}
  ],
  "manifest_ref": {"manifest_id": "man_<id>", "version": 1},
  "validation_status": "pending",
  "lifecycle_state": "active"
}
```

Rules:
- The registered bytes for a version never change.
- Re-rendering or editing creates a new version or a new artifact, according to the semantic change.
- `storage_ref` is opaque and not a public permanent URL.
- Local filesystem paths are worker-local details and cannot be canonical storage references.
- Hashes are calculated from actual bytes by a trusted registration/validation boundary.
- A filename extension is not proof of media type.
- Failed integrity checks quarantine the version and prevent downstream use.
- Approval and QA bind to the exact artifact version and checksum.

## 5.4 Asset record

**PROPOSED BASELINE**

```json
{
  "asset_id": "ast_<id>",
  "workspace_id": "wsp_<id>",
  "asset_kind": "stock_video",
  "origin_type": "licensed_provider",
  "source_ref": {
    "provider": "provider-name",
    "external_asset_id": "provider-asset-id",
    "source_url": null
  },
  "artifact_ref": {"artifact_id": "art_<id>", "version": 1},
  "creator_or_rightsholder": "known-party-or-unknown",
  "acquired_at": "2026-10-31T12:00:00Z",
  "rights_assessment_refs": [],
  "usage_restrictions": [],
  "provenance_status": "documented",
  "lifecycle_state": "active"
}
```

Do not infer a license from the fact that a file is downloadable, publicly visible, or present in a local folder.

## 5.5 Rights assessment record

**PROPOSED BASELINE**

```json
{
  "rights_assessment_id": "rgt_<id>",
  "asset_id": "ast_<id>",
  "artifact_version_ref": null,
  "intended_use": {
    "brand_id": "brd_<id>",
    "channels": ["youtube", "instagram"],
    "territories": ["global"],
    "commercial_use": true,
    "duration": null
  },
  "evidence_refs": [],
  "status": "UNKNOWN",
  "restrictions": [],
  "assessed_by": {"type": "service", "id": "rights-service"},
  "policy_version_ref": {"policy_id": "pol_<id>", "version": 1},
  "assessed_at": "2026-10-31T12:00:00Z",
  "expires_at": null
}
```

Unknown or expired rights must not be treated as cleared. Exact evidence sufficiency rules and any exceptional rights workflow require explicit policy approval.

## 5.6 Production manifest

**PROPOSED BASELINE**

```json
{
  "manifest_id": "man_<id>",
  "version": 1,
  "workspace_id": "wsp_<id>",
  "content_item_id": "cnt_<id>",
  "studio_job_id": "stj_<id>",
  "production_run_id": "run_<id>",
  "studio": {
    "studio_id": "shorts_studio",
    "studio_version": "reported-build-id",
    "adapter_contract_version": "1.0"
  },
  "inputs": [
    {"artifact_id": "art_<id>", "version": 2, "role": "script"}
  ],
  "assets_used": [
    {
      "asset_id": "ast_<id>",
      "artifact_version_ref": {"artifact_id": "art_<id>", "version": 1},
      "usage": "shot_04_background",
      "rights_assessment_ref": "rgt_<id>"
    }
  ],
  "production_steps": [
    {
      "step_id": "render",
      "tool": "ffmpeg",
      "tool_version": "reported-version",
      "configuration_ref": null
    }
  ],
  "outputs": [
    {"artifact_id": "art_<id>", "version": 1, "role": "final_video"}
  ],
  "warnings": [],
  "created_at": "2026-10-31T12:08:00Z",
  "created_by": {"type": "worker", "id": "wrk_<id>"}
}
```

For video, the manifest should support shot/segment-level lineage when the studio can supply it:
- shot/beat ID;
- time range;
- source asset and version;
- rights reference;
- claim/evidence reference where relevant;
- rendered output segment reference;
- validation result.

Do not invent shot-level provenance where the current engine cannot produce it. Mark missing coverage explicitly.

## 5.7 Artifact lifecycle

Suggested lifecycle:
`DRAFT` → `ACTIVE` → `SUPERSEDED` → `ARCHIVED`

Additional quarantine state:
`QUARANTINED`

Lifecycle is separate from approval state. An artifact can be active but not approved; approved but later superseded; or quarantined due to integrity concerns.

## 5.8 Storage and transfer requirements

- Metadata and binaries are separate.
- Large files use controlled transfer/object storage.
- Database and queue records carry references, not binary payloads.
- Access grants are scoped, short-lived, and auditable.
- Cloud metadata and durable references are authoritative.
- Local worker caches are disposable and must verify version/checksum.
- Cache deletion must not delete durable artifacts.
- Artifact transfer interruption must be resumable or safely restartable.
- Provider selection and retention duration remain open.

---

# 6. Governance decision and authorization contracts

## 6.1 Governance pipeline

**PROPOSED BASELINE**

```text
Production Outputs Registered
          |
          v
Integrity + Schema Validation
          |
          v
Quality Evaluation
          |
          v
Rights Assessment
          |
          v
Safety / Policy Evaluation
          |
          v
Review Package Frozen
          |
          v
Approval Decision (where required)
          |
          v
Publication Eligibility Evaluation
          |
          v
Scoped Authorization Grant
          |
          v
Publishing Service Executes
          |
          v
Provider Reconciliation + Audit
```

The actual order may include parallel independent checks, but publication must not proceed until all required gates have authoritative results.

## 6.2 QA result contract

**PROPOSED BASELINE**

```json
{
  "qa_run_id": "qar_<id>",
  "target_refs": [
    {"artifact_id": "art_<id>", "version": 1}
  ],
  "target_checksums": ["sha256:<digest>"],
  "qa_profile": "short_video_release",
  "qa_profile_version": 1,
  "overall_result": "PASS_WITH_WARNINGS",
  "checks": [
    {
      "check_id": "render_integrity",
      "result": "PASS",
      "severity": "blocking",
      "finding_codes": []
    },
    {
      "check_id": "claim_evidence_coverage",
      "result": "WARN",
      "severity": "blocking",
      "finding_codes": ["EVIDENCE_COVERAGE_INCOMPLETE"]
    }
  ],
  "blocking_findings": [],
  "warnings": ["EVIDENCE_COVERAGE_INCOMPLETE"],
  "created_at": "2026-10-31T12:10:00Z"
}
```

A `WARN` from a check configured as blocking must not be interpreted as a pass. The policy engine maps check outcomes and severity to eligibility. This contract does not assume that every existing warning is already a blocker; policy profiles must explicitly define that mapping.

## 6.3 Review Package contract

**PROPOSED BASELINE**

```json
{
  "review_package_id": "rvp_<id>",
  "content_item_id": "cnt_<id>",
  "package_version": 1,
  "artifact_refs": [
    {
      "artifact_id": "art_<id>",
      "version": 1,
      "checksum": "sha256:<digest>",
      "role": "final_video"
    }
  ],
  "qa_run_refs": ["qar_<id>"],
  "rights_assessment_refs": ["rgt_<id>"],
  "research_package_refs": [
    {"research_package_id": "res_<id>", "version": 3}
  ],
  "claim_evidence_snapshot_ref": "snapshot_<id>",
  "brand_profile_ref": {"brand_id": "brd_<id>", "version": 4},
  "policy_version_refs": [
    {"policy_id": "pol_<id>", "version": 5}
  ],
  "created_at": "2026-10-31T12:11:00Z",
  "status": "READY"
}
```

A review package is a frozen review target. If any reviewed version changes, create a new package or explicitly invalidate the old one.

## 6.4 Approval Decision contract

**PROPOSED BASELINE**

```json
{
  "approval_decision_id": "apd_<id>",
  "approval_request_id": "apr_<id>",
  "review_package_ref": {"review_package_id": "rvp_<id>", "version": 1},
  "decision": "APPROVED",
  "decided_by": {
    "type": "user",
    "id": "owner"
  },
  "decided_at": "2026-10-31T12:12:00Z",
  "comment": null,
  "scope": {
    "action": "editorial_release",
    "destinations": ["youtube_shorts", "instagram_reels"]
  },
  "policy_version_refs": [
    {"policy_id": "pol_<id>", "version": 5}
  ],
  "decision_evidence": [],
  "supersedes_decision_id": null
}
```

Rules:
- Decisions are append-only and immutable.
- A later decision may supersede an earlier one, but must preserve history.
- The decision identifies who/what decided, what exact package was reviewed, and under which policy version.
- An agent cannot approve its own work.
- Approval scope is explicit. Editorial approval does not imply all destinations or all future versions are approved.
- Expiry and revocation semantics must be defined for the decision types that need them.

## 6.5 Approval versus authorization

This distinction is mandatory:

| Approval | Authorization |
|---|---|
| Records a decision that reviewed content is acceptable for a defined purpose | Grants a specific actor/service permission to perform a specific action |
| Bound to exact review package and policy | Bound to action, target, actor, scope, policy, and time |
| Usually a human/editorial or configured policy decision | Enforced by an authorization service at action time |
| Does not carry platform credentials | Does not itself establish editorial quality |

An approval record must never be treated as a reusable bearer token.

## 6.6 Authorization Grant contract

**PROPOSED BASELINE**

```json
{
  "authorization_grant_id": "azg_<id>",
  "grant_type": "publication.execute",
  "subject": {
    "type": "service",
    "id": "publishing-service"
  },
  "action": "publish",
  "resource": {
    "publication_request_id": "pbr_<id>",
    "content_item_id": "cnt_<id>",
    "artifact_ref": {"artifact_id": "art_<id>", "version": 1}
  },
  "destinations": ["youtube_shorts"],
  "conditions": {
    "approval_decision_ref": "apd_<id>",
    "policy_version_ref": {"policy_id": "pol_<id>", "version": 5},
    "rights_assessment_refs": ["rgt_<id>"],
    "qa_run_refs": ["qar_<id>"]
  },
  "issued_at": "2026-10-31T12:13:00Z",
  "expires_at": "2026-10-31T13:13:00Z",
  "max_uses": 1,
  "uses": 0,
  "status": "ACTIVE"
}
```

- Grant must be checked server-side immediately before the side effect.
- Grant is bound to a specific publication request and exact artifact version.
- Grant is scoped by destination, action, subject, and policy version.
- Revocation and expiry must be enforced.
- Credentials remain in a dedicated secret boundary, not in this record.
- Grant issuance and consumption create audit events.

## 6.7 Publication eligibility decision

**PROPOSED BASELINE**

The policy engine should return one of three outcomes:

| Outcome | Meaning |
|---|---|
| `AUTO_ELIGIBLE` | All hard gates pass and current policy permits execution without a new human decision |
| `PENDING_APPROVAL` | No hard blocker exists, but a required human approval is missing |
| `BLOCKED` | A hard rights, safety, integrity, validation, policy, or technical blocker exists |

These are proposed outcome names, not a locked autonomy policy. The owner's earlier preference for conditional automation was discussed but not finalized as a complete publishing policy. Numeric limits, eligible formats, time windows, and platform-specific conditions remain open.

**Important:** `PENDING_APPROVAL` is a hold, not a timeout-based auto-approval. User unavailability must not convert it to `AUTO_ELIGIBLE`.

## 6.8 Publication Request contract

**PROPOSED BASELINE**

```json
{
  "publication_request_id": "pbr_<id>",
  "content_item_id": "cnt_<id>",
  "artifact_ref": {
    "artifact_id": "art_<id>",
    "version": 1,
    "checksum": "sha256:<digest>"
  },
  "destination": {
    "platform": "youtube",
    "format": "shorts",
    "account_ref": "platform-account-ref"
  },
  "metadata_ref": {"artifact_id": "art_<metadata-id>", "version": 1},
  "approval_decision_refs": ["apd_<id>"],
  "qa_run_refs": ["qar_<id>"],
  "rights_assessment_refs": ["rgt_<id>"],
  "policy_version_ref": {"policy_id": "pol_<id>", "version": 5},
  "eligibility_outcome": "PENDING_APPROVAL",
  "idempotency_key": "publish:<content-item-id>:youtube:<artifact-version>",
  "scheduled_at": null,
  "created_at": "2026-10-31T12:13:00Z"
}
```

## 6.9 Publishing boundary

- Only the centralized publishing service may perform public external side effects.
- Studios, agents, and generic workers cannot bypass the publishing service.
- Publishing service must verify eligibility, approval requirements, authorization grant, exact artifact checksum/version, destination scope, and policy version at execution time.
- A direct provider adapter must not expose an alternate ungoverned publishing path.
- Provider responses must be reconciled before retries where outcome is uncertain.
- Private-by-default settings are a separate product/policy choice; the previously completed Shorts YouTube default change does not automatically authorize changes to the long-form uploader or other platforms.

## 6.10 Emergency controls

**PROPOSED BASELINE**

The control plane should support:
- global distribution pause;
- per-platform pause;
- per-account pause;
- per-content-item pause;
- credential revocation;
- authorization grant revocation;
- worker revocation;
- policy version rollback only through an audited owner-controlled process.

Emergency pause must stop new side effects and prevent queued work from silently resuming until policy says it may. Already-submitted provider requests require reconciliation.

---

# 7. Acceptance-test matrix

All tests below are **proposed acceptance criteria, not executed tests**. They should become automated tests and integration scenarios after contract approval and implementation authorization.

## 7.1 Identity and Content Graph

| ID | Scenario | Expected result | Priority |
|---|---|---|---|
| ID-01 | Create two records of same type | IDs are globally unique | P0 |
| ID-02 | Retry create command with same idempotency key/body | Existing logical result returned; no duplicate | P0 |
| ID-03 | Reuse same idempotency key with different body | Conflict rejected | P0 |
| ID-04 | Content Idea creates Short and long-form Content Items | Both link to same idea; separate item IDs/lifecycles | P0 |
| ID-05 | One research package supports multiple items | Explicit references preserve lineage | P0 |
| ID-06 | Source supports multiple evidence items | Source/evidence distinction preserved | P0 |
| ID-07 | Claim lacks evidence | Marked unsupported/unverified; never silently represented as sourced | P0 |
| ID-08 | Archive a content item | Historical lineage remains queryable | P1 |

## 7.2 State machines and concurrency

| ID | Scenario | Expected result | Priority |
|---|---|---|---|
| ST-01 | Invalid Content Item transition | Rejected by authoritative service | P0 |
| ST-02 | Worker tries to change workflow state directly | Denied | P0 |
| ST-03 | Stale record version updates | Conflict; caller must refresh | P0 |
| ST-04 | Job lease expires | Job can be safely requeued under policy | P0 |
| ST-05 | Old worker submits after lease reassignment | Result rejected/quarantined; cannot overwrite current attempt | P0 |
| ST-06 | Retry occurs | New Job Attempt recorded; history retained | P0 |
| ST-07 | User unavailable while approval pending | Workflow remains pending; no implied approval | P0 |
| ST-08 | Workflow waits for local-only render while PC is off | Remains queued/waiting or moves to eligible remote worker | P0 |

## 7.3 Task, job, studio, and agent contracts

| ID | Scenario | Expected result | Priority |
|---|---|---|---|
| API-01 | Submit valid job envelope | Schema validated and durable job created | P0 |
| API-02 | Submit unknown contract version | Rejected or routed through explicit compatibility handler | P0 |
| API-03 | Job references missing input version | Rejected before execution | P0 |
| API-04 | Worker lacks required capability | Not assigned | P0 |
| API-05 | Agent returns malformed output | Output rejected; workflow does not advance | P0 |
| API-06 | Agent requests unauthorized tool | Denied and audited | P0 |
| API-07 | Studio reports 100% progress but output missing | Studio job not accepted as completed | P0 |
| API-08 | Studio attempts to publish directly | Denied; publishing boundary enforced | P0 |
| API-09 | Duplicate studio completion callback | One logical completion and artifact registration | P0 |

## 7.4 Events and idempotency

| ID | Scenario | Expected result | Priority |
|---|---|---|---|
| EVT-01 | Same event delivered twice | Consumer applies effect once | P0 |
| EVT-02 | Events arrive out of order | Aggregate version check prevents stale overwrite | P0 |
| EVT-03 | State commit succeeds but event relay fails | Outbox/recovery eventually delivers event | P0 |
| EVT-04 | Consumer crashes after effect before acknowledgement | Redelivery does not duplicate effect | P0 |
| EVT-05 | Provider request times out after possible acceptance | State becomes `UNKNOWN_OUTCOME`; reconcile before retry | P0 |
| EVT-06 | Duplicate publication command | No duplicate external publication | P0 |

## 7.5 Artifacts, assets, and manifests

| ID | Scenario | Expected result | Priority |
|---|---|---|---|
| ART-01 | Register artifact with valid bytes | Version, size, media type, and checksum recorded | P0 |
| ART-02 | Same version bytes are overwritten | Prohibited; new version required | P0 |
| ART-03 | Checksum mismatch on transfer | Quarantine; downstream gates blocked | P0 |
| ART-04 | Local path is supplied as global storage reference | Rejected or normalized through storage service | P0 |
| ART-05 | Asset rights are unknown | Rights gate does not pass | P0 |
| ART-06 | Manifest references missing input | Validation fails | P0 |
| ART-07 | Shot-level provenance unavailable | Explicitly marked unavailable; not fabricated | P1 |
| ART-08 | Worker cache is deleted | Durable artifact remains available | P1 |

## 7.6 Governance and publishing

| ID | Scenario | Expected result | Priority |
|---|---|---|---|
| GOV-01 | Approval references exact artifact version/hash | Decision stores exact target | P0 |
| GOV-02 | Artifact changes after approval | Old approval does not authorize changed version | P0 |
| GOV-03 | QA blocking check fails | Publication blocked | P0 |
| GOV-04 | Rights status is unknown/restricted/expired | Publication blocked under hard-gate policy | P0 |
| GOV-05 | Editorial approval exists but authorization grant absent | Publishing denied | P0 |
| GOV-06 | Authorization grant is expired/revoked/consumed | Publishing denied | P0 |
| GOV-07 | Destination differs from approved scope | Publishing denied | P0 |
| GOV-08 | Emergency pause active | New publication side effects prevented | P0 |
| GOV-09 | User unavailable during pending approval | No automatic approval | P0 |
| GOV-10 | Direct adapter attempts public publishing | Denied and audited | P0 |
| GOV-11 | Provider result uncertain | Reconciliation required before retry | P0 |

## 7.7 Security, recovery, and operations

| ID | Scenario | Expected result | Priority |
|---|---|---|---|
| OPS-01 | Unauthenticated worker request | Denied | P0 |
| OPS-02 | Worker accesses another workspace's artifact | Denied | P0 |
| OPS-03 | Worker requests unassigned secret | Denied; no secret in logs | P0 |
| OPS-04 | Worker heartbeat stops | Health degrades/offline; lease recovery policy runs | P0 |
| OPS-05 | Cloud control plane remains up while local PC is off | Supported cloud workflows continue | P0 |
| OPS-06 | Local worker reconnects with stale cache | Versions/checksums revalidated | P0 |
| OPS-07 | Database/queue outage | No false completion; recovery preserves durable work | P1 |
| OPS-08 | Restore from backup | Record relationships, artifact hashes, and audit history verified | P1 |
| OPS-09 | Cost threshold reached | Configured pause/alert behavior occurs | P1 |
| OPS-10 | Secret appears in exception text | Redaction test fails build | P0 |

## 7.8 Release gate

A contract implementation is not accepted merely because unit tests pass. Before any production side effect:
- contract schema validation passes;
- integration tests pass across control plane, queue, worker, studio, artifact service, and governance;
- retry and duplicate-delivery tests pass;
- stale lease and concurrency tests pass;
- hard-gate bypass tests pass;
- security and secret-redaction tests pass;
- emergency pause is demonstrated;
- provider sandbox or dry-run behavior is verified;
- restore/recovery expectations are documented;
- owner explicitly authorizes any real external side effect.

---

# 8. Open decisions register

These are intentionally not guessed or silently locked.

| ID | Decision | Current status | Recommended next action |
|---|---|---|---|
| DEC-01 | Final ID implementation (UUIDv7 or equivalent) | OPEN | Validate stack support and migration implications |
| DEC-02 | Database/provider selection | OPEN | Compare requirements, cost, portability, operations |
| DEC-03 | Event transport and delivery guarantees | OPEN | Choose after outbox/inbox requirements are accepted |
| DEC-04 | API style and schema tooling | OPEN | Compare REST/RPC and schema compatibility |
| DEC-05 | Worker authentication/identity mechanism | OPEN | Define trust boundary and credential rotation |
| DEC-06 | Lease duration and heartbeat policy | OPEN | Derive from render/task durations and failure tests |
| DEC-07 | Artifact storage provider and retention | OPEN | Define cost, transfer, backup, and restore needs |
| DEC-08 | QA profile and blocking severity mapping | OPEN | Owner review of actual quality policy |
| DEC-09 | Rights evidence sufficiency and exception policy | OPEN | Define hard blockers; legal review where appropriate |
| DEC-10 | Conditional auto-publishing scope and numeric limits | OPEN | Owner decision; keep disabled until approved |
| DEC-11 | Eligible formats/platforms for auto-publishing | OPEN | Decide per format and destination |
| DEC-12 | Approval expiry and review windows | OPEN | Define only after autonomy policy |
| DEC-13 | Emergency pause semantics for in-flight provider requests | OPEN | Specify reconciliation behavior |
| DEC-14 | Initial Shorts adapter process boundary | OPEN | Validate integration design after repo inspection is authorized |
| DEC-15 | Existing SQLite prototype compatibility | OPEN | Requires explicit repository inspection permission |
| DEC-16 | Existing metadata, run tracker, manifests, and approval compatibility | OPEN | Requires explicit repository inspection permission |
| DEC-17 | Backup retention, RPO, RTO, and cost limits | OPEN | Set before production deployment |
| DEC-18 | Exact cloud/local/remote worker split | PARTIALLY LOCKED | Hybrid topology locked; specific services/providers remain open |

## 8.1 Locked architecture constraints carried forward

- Hybrid deployment: always-on cloud control plane plus local and remote workers.
- Cloud is authoritative for shared identity, workflow, job, policy, approval, and distribution state.
- Local worker is preferred for existing Shorts Studio/FFmpeg-heavy rendering when available.
- PC-offline behavior must be truthful; local compute does not run while the PC is off.
- Existing Shorts Studio is retained and integrated through an adapter; no wholesale replacement.
- Initial operating mode: single-owner Creator Mode and NEXTDECODE brand.
- Human-controlled critical decisions and explicit authorization for external side effects.
- No assumption that all cloud services are free; ₹0/free-first remains an economic target, not a guarantee.
- Existing agent ownership remains unchanged: Qoder Phase 11 engineering owner, OpenCode Phase 10 engineering/closure owner, Kilo independent read-only QA.
- No repository/Git operations until explicit superseding permission.
- No implementation, deployment, paid services, real uploads, or publishing authorization is granted by this pack.

---

# 9. Implementation sequencing after approval

This is a proposed sequence, not an authorization to begin.

1. **Contract review and approval:** decide which proposed schemas become canonical; close or explicitly defer open decisions.
2. **Compatibility discovery:** only after explicit permission, inspect current repository structures and compare `workspace_sync.py`, metadata, run tracker, manifests, approval ledgers, and publishing paths. Preserve all WIP.
3. **Foundation data layer:** implement canonical identity, Content Graph relationships, versioning, and audit primitives.
4. **Execution foundation:** implement durable workflow/job records, leases, worker registration, retries, and event idempotency.
5. **Governance foundation:** centralize QA/rights/approval/authorization checks and close direct publishing bypasses before enabling any external side effect.
6. **Artifact service:** immutable versions, checksum validation, manifests, scoped transfer, and lifecycle.
7. **Shorts Studio adapter:** thin adapter around existing engine; dry-run first; publishing disabled during integration validation.
8. **Hybrid operations:** monitoring, recovery, backup/restore, security, emergency pause, and cost controls.
9. **Controlled production readiness:** separate owner authorization after acceptance evidence; never inferred from test success.

---

# 10. Source basis and traceability

This pack is derived from the following existing NEXTDECODE project documents and prior report-backed findings:

1. `NEXTDECODE_Master_Blueprint_2.0.docx` — product vision, twelve modules, content lifecycle, human-control principle, initial Creator Mode and product scope.
2. `NEXTDECODE_System_Architecture_Pipeline_Part_1_System_Architecture_Master_Reference_1.0.md` — overall architecture.
3. `NEXTDECODE_System_Architecture_Pipeline_Part_2_Shorts_Studio_Pipeline_Contract_1.0.md` — Shorts Studio boundary and production lifecycle.
4. `NEXTDECODE_System_Architecture_Pipeline_Part_3_Shared_Data_Model_Content_Graph_1.0.md` — entity domains, graph relationships, identity, versioning, hybrid authority, and data integrity.
5. `NEXTDECODE_System_Architecture_Pipeline_Part_4_Persistent_Job_Queue_Scheduler_Worker_Architecture_1.0.md` — durable job model, scheduler/queue/worker/orchestrator boundaries, leases, retries, and recovery.
6. `NEXTDECODE_System_Architecture_Pipeline_Part_5_Agent_Contracts_Orchestration_1.0.md` — bounded agents, least privilege, deterministic services, task contracts, and human control.
7. `NEXTDECODE_System_Architecture_Pipeline_Part_6_Centralized_Quality_Rights_Approval_Publishing_Governance_1.0.md` — centralized gates, rights, approval, authorization, and publishing restrictions.
8. `NEXTDECODE_System_Architecture_Pipeline_Part_7_Studio_Integration_APIs_Artifact_Management_1.0.md` — studio capabilities, job envelopes, API surface, artifact versions, manifests, and integration boundaries.
9. `NEXTDECODE_System_Architecture_Pipeline_Part_8_Hybrid_Deployment_Security_Monitoring_Backup_Recovery_1.0.md` — hybrid topology, security, operations, monitoring, backup, and recovery.
10. `NEXTDECODE_Architecture_Reconciliation_Implementation_Readiness_Report_1.0.md` — canonical identity recommendations, state separation, job/task/artifact/event minimum contracts, current Shorts Studio report findings, major blockers, and implementation readiness status.

**Source limitations:** This pack does not claim that any schema, state machine, API, queue, event transport, database, authorization service, or test has been implemented or verified in the repository. Current-system compatibility remains unverified because repository inspection and Git operations remain restricted.

---

# 11. Approval checklist

The pack is ready for owner review when the owner can answer:

- [ ] Are the entity distinctions and identity hierarchy correct?
- [ ] Are the ID conventions acceptable, subject to final technology selection?
- [ ] Are the separate Content Item, Workflow Run, Job, Attempt, Worker, Studio Job, QA, Approval, Authorization, and Publication state machines acceptable?
- [ ] Are the task/job/studio envelopes sufficient for the first implementation?
- [ ] Are at-least-once event delivery and idempotent consumer requirements accepted?
- [ ] Are the artifact/asset/manifest distinctions and immutable version rules acceptable?
- [ ] Is the separation of approval from authorization accepted as mandatory?
- [ ] Are `AUTO_ELIGIBLE`, `PENDING_APPROVAL`, and `BLOCKED` acceptable as proposed eligibility outcomes, pending a separate autonomy policy?
- [ ] Are the acceptance tests complete enough to become the initial engineering gate?
- [ ] Are open decisions correctly marked open/deferred?

**Recommended disposition:** Review and approve the contract baseline before implementation planning is converted into executable engineering tasks. Do not treat silence or continued discussion as approval.

---

**End of NEXTDECODE Canonical Contracts Pack 1.0**
