# NEXTDECODE Content OS — Architecture Decision Records Pack 1.0

**Document status:** Draft for owner review  
**Version:** 1.0  
**Prepared:** 31 October 2026  
**Decision authority:** Product owner  
**Relationship:** Companion to `NEXTDECODE_Architecture_Decision_Register_1.0.md` and `NEXTDECODE_Canonical_Contracts_Pack_1.0.md`

---

## 1. Purpose and decision status

This pack turns the highest-priority architecture questions into reviewable Architecture Decision Records (ADRs). It is intended to make the trade-offs, dependencies, consequences and verification requirements explicit before implementation begins.

**Important:** These are recommendations, not accepted decisions. Unless a record explicitly says otherwise, its status is **PROPOSED** or **OPEN**. Creating this pack does not authorize repository inspection, code changes, dependency installation, deployment, publishing, or any other operational side effect.

### Status vocabulary

- **LOCKED CONSTRAINT** — already established by an explicit owner decision; do not silently change it.
- **PROPOSED** — a recommended direction awaiting owner acceptance.
- **OPEN** — requires a decision or evidence before implementation.
- **DEFERRED** — intentionally outside the initial foundation scope.

### Existing locked constraints relevant to these ADRs

1. NEXTDECODE Content OS is a single-owner Creator Mode first, for one brand: NEXTDECODE.
2. The deployment direction is **Hybrid**: always-on cloud control plane, with local execution capacity for the existing Shorts Studio and heavy rendering.
3. Cloud-authoritative shared workflow/control state; local worker state is execution/cache state, not the global source of truth.
4. Shorts Studio is a specialized production engine to integrate, not replace wholesale.
5. Human approval is required for critical actions unless a separately approved conditional-publishing policy later permits a bounded exception.
6. No production generation, upload, or publishing without explicit authorization.
7. Existing agent ownership remains unchanged: Qoder (Phase 11 engineering owner), OpenCode (Phase 10 engineering/closure owner), Kilo (independent read-only QA).
8. No Git operations of any kind, including read-only Git inspection, until explicit superseding permission.
9. Preserve work in progress; no destructive cleanup, reset, revert, broad staging, or unrelated overwrite.
10. Cloud provider, database, queue, storage provider, budget and deployment target have not been selected or authorized.

---

## 2. Recommended review order

The records below are sequenced by dependency, not by implementation authorization.

| Order | ADR | Subject | Status | Why it comes here |
|---:|---|---|---|---|
| 1 | ADR-001 | Canonical identity and IDs | PROPOSED | Every durable record and event depends on stable identity |
| 2 | ADR-002 | System of record / database | OPEN | Establishes transactional ownership and persistence |
| 3 | ADR-003 | Durable queue and event delivery | OPEN | Depends on transaction and persistence decisions |
| 4 | ADR-004 | API and serialization contracts | PROPOSED | Defines safe boundaries between control plane and workers |
| 5 | ADR-005 | Worker identity and authentication | PROPOSED | Required before remote or local workers can be trusted |
| 6 | ADR-006 | Artifact and binary storage | PROPOSED | Defines durable media/artifact references and transfer |
| 7 | ADR-010 | Separate lifecycle state machines | PROPOSED | Prevents workflow, job, run and publishing state from collapsing |
| 8 | ADR-007 | Centralized governance and publishing boundary | PROPOSED | Makes approval and authorization enforceable across paths |
| 9 | ADR-008 | QA severity and hard-gate policy | OPEN | Determines what can progress or publish |
| 10 | ADR-009 | Rights evidence and asset-use policy | OPEN | Defines safe handling of licensed and unknown-rights assets |

ADR-010 is listed after the transport/storage records for readability, but it should be reviewed early alongside ADR-001 and ADR-002. ADR-007 through ADR-009 must be agreed before any production publishing path is enabled.

---

# ADR-001 — Canonical identity and ID strategy

**Status:** PROPOSED  
**Decision owner:** Product owner  
**Scope:** All durable Content OS entities, workflow objects, events and artifact references.

## Context

The platform needs to distinguish content ideas, content items, format-specific variants, workflows, tasks, jobs, studio executions, production runs, artifacts, assets, reviews, approvals and distribution attempts.

The existing Shorts Studio has file-oriented and legacy run conventions. The Content OS must integrate it without allowing legacy filenames or local folder paths to become global identity.

The architecture reconciliation identified a need for a canonical identity hierarchy and non-colliding ID namespaces.

## Decision

Adopt globally unique, opaque identifiers for durable entities. **UUIDv7 is the recommended candidate**, subject to compatibility review and owner acceptance.

Use explicit entity types and relationships rather than encoding business meaning into IDs. IDs must not be reused. Human-readable slugs may be added for display, but must not be treated as primary identity.

Recommended identity families include:

- `workspace_id`
- `brand_id`
- `content_idea_id`
- `content_item_id`
- `content_variant_id`
- `workflow_id`
- `task_id`
- `job_id`
- `worker_id`
- `studio_job_id`
- `production_run_id`
- `artifact_id`
- `asset_id`
- `review_id`
- `approval_id`
- `authorization_id`
- `distribution_id`
- `event_id`

A content item represents the durable editorial/content identity. A content variant represents a particular format or platform adaptation. A production run is one execution attempt, not the content itself.

## Alternatives considered

1. **UUIDv7** — time-ordered, globally unique, opaque; recommended candidate.
2. **UUIDv4** — widely supported and random, but less naturally time-ordered.
3. **Database-generated numeric IDs** — compact, but awkward across independently executing workers and imported legacy systems.
4. **Human-readable IDs** — convenient operationally, but risk collisions, leakage of internal meaning and brittle renaming.

## Consequences

**Benefits**
- Stable identity across cloud and local workers.
- Safer event correlation and idempotency.
- Supports multiple variants and repeated production attempts.
- Legacy Shorts Studio paths can be mapped to canonical records without becoming canonical IDs.

**Costs / risks**
- UUIDv7 library and database support must be checked for the selected stack.
- Human-facing interfaces need readable titles/slugs alongside opaque IDs.
- Migration/adaptation logic is required for legacy run identifiers.

## Required invariants

- Entity type is explicit; do not infer it from an ID prefix alone.
- IDs are immutable and never reused.
- Every event includes its own `event_id` and relevant aggregate/entity IDs.
- Every artifact version has a stable identity and immutable version reference.
- Legacy identifiers are stored as external/source identifiers, not silently promoted to canonical IDs.

## Verification before implementation

- Confirm selected language/runtime libraries can generate and validate UUIDv7.
- Define uniqueness constraints and indexes.
- Define mapping rules for existing Shorts Studio run IDs and file paths.
- Add contract tests for entity-type mismatch, duplicate IDs and stable references.

## Owner decision

**Pending.** Accept UUIDv7 as the default canonical ID format, or request an alternative.

---

# ADR-002 — Canonical system of record and database

**Status:** OPEN  
**Decision owner:** Product owner  
**Scope:** Durable shared control-plane state.

## Context

Hybrid operation requires the system to continue coordinating work while the user's PC is off. Workflow state, approvals, policies, jobs, worker registrations and distribution records cannot live only in local files or process memory.

The architecture requires one authoritative shared state model. The current project has a SQLite prototype (`workspace_sync.py`) that is not yet connected to the pipeline; it is not evidence of a production-ready shared database.

## Recommended direction

Use a **PostgreSQL-compatible relational database as the canonical system of record** for shared control-plane entities.

Keep relational constraints and transactions authoritative for:
- identity and entity relationships;
- workflow/job/task state;
- worker registrations and leases;
- policy versions;
- review and approval records;
- authorization decisions;
- distribution attempts and outcomes;
- event outbox/inbox metadata;
- artifact and asset metadata.

Do not store large media binaries directly in relational rows. Store metadata and durable object references.

SQLite may remain useful for local development, tests, caches or a single-machine mode, but should not silently become a second competing authority for shared cloud state.

## Alternatives considered

1. **PostgreSQL-compatible relational database** — recommended; transactions, constraints, indexing and broad ecosystem.
2. **SQLite as the only database** — excellent for local prototypes, but not the recommended shared multi-worker control-plane authority.
3. **Document database** — flexible schemas, but relational lifecycle and governance constraints are central to this product.
4. **Multiple databases from day one** — adds operational and consistency complexity before proven need.

## Consequences

**Benefits**
- Durable state independent of the user's PC.
- Transactional enforcement of relationships and state transitions.
- Supports transactional outbox/inbox patterns.
- Strong fit for auditability and governance.

**Costs / risks**
- Requires a hosted or otherwise continuously available database for always-on operation.
- Backups, migrations, access control, connection management and recovery become operational responsibilities.
- Provider and cost remain open.

## Required invariants

- One authoritative owner for each shared state field.
- No hidden dual-write between local SQLite and cloud database.
- Local worker cache must be rebuildable or reconcilable from authoritative state.
- Schema changes are versioned and migrated deliberately.
- Approval, policy and authorization history is durable and auditable.

## Open questions

- Which managed PostgreSQL provider and region?
- What is the acceptable monthly cost envelope?
- What backup retention and recovery objectives are required?
- Is a local development profile required to run without cloud credentials?

## Verification before implementation

- Compare candidate providers for region, pricing, backups, connection limits, security and portability.
- Define schema migration tooling and rollback/forward-fix policy.
- Test transaction boundaries for state change plus outbox event.
- Test restore from backup in a non-production environment.

## Owner decision

**Pending.** Select the database technology/provider and operational cost envelope before deployment planning.

---

# ADR-003 — Durable queue, scheduler and event delivery

**Status:** OPEN  
**Decision owner:** Product owner  
**Scope:** Asynchronous work dispatch, retries, scheduling and event propagation.

## Context

The system must continue supported cloud workflows when the user's PC is offline or the user is unavailable. A process-local queue or in-memory job list is insufficient. The architecture distinguishes scheduler, orchestrator, queue, worker and agent as separate responsibilities.

The current API reportedly keeps jobs in memory; this is not durable enough for the target architecture.

## Recommended direction

Use a **durable database-backed job model with transactional outbox/inbox semantics as the initial baseline**, then introduce a dedicated broker only if measured throughput, fan-out or latency requires it.

Core responsibilities:
- **Scheduler:** decides when work becomes eligible.
- **Orchestrator:** coordinates workflow steps and dependencies.
- **Queue:** durably records dispatchable work.
- **Worker:** claims and executes an assigned job.
- **Agent:** performs bounded reasoning or tool work under a contract; it is not the queue or worker.

A job claim should use a lease with expiry/heartbeat. Expired leases become eligible for controlled recovery. Retries must be bounded and classified. Jobs must be idempotent or protected by idempotency keys.

Use an outbox written in the same database transaction as the state change. Consumers record inbox/deduplication state so duplicate event delivery does not duplicate side effects.

## Alternatives considered

1. **Database-backed queue + outbox/inbox** — recommended starting point; fewer services and strong transaction alignment.
2. **Dedicated message broker from day one** — potentially better at high throughput, but adds infrastructure and consistency work.
3. **In-memory queue** — rejected for durable operation.
4. **Cron-only scheduling** — insufficient for dependencies, retries, leases and workflow-level visibility.

## Consequences

**Benefits**
- Work survives process restarts.
- Cloud coordination continues while the local PC is off.
- Duplicate delivery can be handled safely.
- A broker can be added later behind stable queue contracts.

**Costs / risks**
- Database-backed polling may need tuning at higher scale.
- Lease expiry and retry policies require careful design.
- Exactly-once execution cannot be assumed; design for at-least-once delivery plus idempotent effects.

## Required invariants

- A job is not considered complete merely because a worker process exits successfully; its result must be durably recorded.
- Every claim has a lease owner, expiry and heartbeat policy.
- A stale worker cannot overwrite a newer attempt's result.
- Retries are bounded, observable and classified.
- Events are notifications; authoritative state remains in the database.
- Publishing side effects require separate authorization and idempotency protection.

## Open questions

- Polling interval and expected job volume?
- Lease duration and heartbeat cadence by job class?
- Retry classes and dead-letter/manual-recovery workflow?
- Which scheduling needs require precise time-zone and recurrence semantics?

## Verification before implementation

- Kill a worker mid-job and verify lease recovery.
- Deliver the same event repeatedly and verify one logical effect.
- Simulate a stale worker returning after lease reassignment.
- Restart scheduler/orchestrator and verify pending work is recovered.
- Verify local-only rendering waits safely while the local worker is offline.

## Owner decision

**Pending.** Accept database-backed durable queue as the initial baseline, or select a dedicated broker now.

---

# ADR-004 — Versioned API and serialization contracts

**Status:** PROPOSED  
**Decision owner:** Product owner  
**Scope:** Control plane, local worker, remote worker and studio adapter communication.

## Context

The hybrid design crosses process and machine boundaries. Components must exchange validated, versioned messages rather than depend on shared filesystem assumptions or undocumented Python internals.

The Canonical Contracts Pack defines proposed envelopes for tasks, jobs, workers, studio APIs and events.

## Decision

Adopt **versioned HTTP/JSON contracts with schema validation** as the initial interoperability baseline.

Each request, response and event should declare a contract/schema version. Use explicit envelopes with:
- message or request ID;
- correlation and causation IDs where applicable;
- entity IDs;
- creation timestamp;
- producer identity;
- schema version;
- typed payload;
- structured error information.

Large binaries should not be embedded in ordinary JSON messages. Exchange controlled artifact references and short-lived transfer instructions instead.

Breaking changes require a new contract version or a documented compatibility window. Unknown fields may be tolerated only where the schema's compatibility policy permits; unknown critical enum values must fail safely.

## Alternatives considered

1. **HTTP/JSON + schema validation** — recommended for initial simplicity and debuggability.
2. **gRPC / Protocol Buffers** — efficient and strongly typed, but adds tooling and operational complexity.
3. **Direct shared database access from workers** — rejected as the default boundary because it couples workers to internal schema and weakens service ownership.
4. **Unversioned ad hoc JSON** — rejected due to drift and unsafe evolution.

## Consequences

**Benefits**
- Clear integration boundary for Shorts Studio.
- Easier local debugging and contract testing.
- Supports independent worker implementations later.

**Costs / risks**
- JSON payloads need disciplined validation.
- Contract versioning and compatibility tests become required.
- HTTP authentication and transport security must be designed with ADR-005.

## Required invariants

- Validate all inbound messages at the boundary.
- Never trust worker-supplied status without validating ownership, lease and allowed transition.
- Include correlation IDs in logs and traces.
- Do not send secrets or unrestricted credentials in job payloads.
- Do not transfer media binaries through ordinary control-plane API payloads.

## Verification before implementation

- Generate or maintain schemas from a single authoritative contract source.
- Add compatibility tests for supported contract versions.
- Test malformed payloads, unknown enum values and oversized requests.
- Test idempotency and correlation propagation end to end.

## Owner decision

**Pending.** Accept versioned HTTP/JSON as the initial contract transport.

---

# ADR-005 — Worker identity, authentication and authorization

**Status:** PROPOSED  
**Decision owner:** Product owner  
**Scope:** Local and remote worker trust, registration and access.

## Context

The local PC worker and any remote workers must connect to an always-on control plane. A worker must not be trusted merely because it knows a job ID or can reach an endpoint.

The system is single-owner initially, but hybrid execution creates a machine-to-machine security boundary. Future multi-user support must not be assumed to exist now.

## Decision

Give each registered worker a **unique machine identity** and scoped credentials. Prefer short-lived credentials or renewable tokens over long-lived shared secrets.

The control plane should:
- register and revoke workers;
- authenticate each worker;
- authorize capabilities and job classes;
- issue or validate time-bounded job leases;
- restrict artifact access to the specific job/run;
- record worker identity in audit events.

A worker must receive only the minimum permissions required for its declared capabilities. Local worker credentials must be revocable independently of user login credentials.

## Alternatives considered

1. **Unique worker identity + scoped short-lived credentials** — recommended.
2. **One shared API key across all workers** — rejected; weak revocation and attribution.
3. **User session cookie reused by workers** — rejected; conflates human and machine identity.
4. **Unauthenticated local-network trust** — rejected; network location is not identity.

## Consequences

**Benefits**
- Per-worker revocation and auditability.
- Capability-based job assignment.
- Reduced blast radius if a worker credential leaks.

**Costs / risks**
- Credential issuance, rotation and revocation need implementation.
- Clock skew and token expiry need handling.
- Secure local secret storage differs across operating systems.

## Required invariants

- Never place credentials in logs, artifacts, prompts or ordinary job payloads.
- Workers cannot self-assign arbitrary jobs.
- Worker capability claims are validated by the control plane.
- Revoked workers cannot claim new work or fetch new artifacts.
- A worker may update only jobs for which it holds a valid lease.
- Human approval identity and machine worker identity remain distinct.

## Verification before implementation

- Test token expiry, rotation and revocation.
- Test a worker attempting to claim a job outside its capabilities.
- Test cross-worker artifact access denial.
- Verify secrets are redacted from logs and diagnostics.
- Define secure credential storage for the user's Windows/WSL environment.

## Owner decision

**Pending.** Accept unique worker identities and scoped short-lived credentials as the baseline.

---

# ADR-006 — Artifact metadata, binary storage and transfer

**Status:** PROPOSED  
**Decision owner:** Product owner  
**Scope:** Generated media, source files, evidence, manifests, previews and other artifacts.

## Context

The system produces large media files and many smaller structured artifacts. The cloud control plane must remain available while the local PC may be offline. Large binaries should not be placed in the relational database or copied through ordinary API messages.

The architecture distinguishes:
- **Asset:** a reusable or sourced media/resource object, with rights and provenance.
- **Artifact:** an output produced by a workflow or production step.
- **Manifest:** a structured record describing a set of artifacts and their relationships.

## Decision

Store artifact/asset metadata and lifecycle references in the canonical database. Store binary content in an **abstracted object-storage layer**. The actual provider remains open.

Every artifact should have:
- immutable `artifact_id` and version;
- owning content/variant/run references;
- media type, size and checksum;
- creation time and producer;
- storage locator/reference;
- validation and retention metadata;
- provenance and rights references where applicable.

Transfer should use scoped, time-limited upload/download authorization. Workers should verify checksums after transfer. Temporary local files are caches, not authoritative shared artifacts.

## Alternatives considered

1. **Object storage behind an abstraction** — recommended.
2. **Database BLOB storage** — rejected for large media and operational separation.
3. **Local filesystem as global artifact store** — incompatible with PC-off continuity.
4. **Provider-specific URLs embedded throughout the product** — rejected; creates lock-in and complicates migration.

## Consequences

**Benefits**
- Handles large media efficiently.
- Keeps control-plane records compact and queryable.
- Allows provider changes behind a storage interface.
- Supports local rendering followed by controlled artifact upload.

**Costs / risks**
- Storage and egress costs must be monitored.
- Signed transfer links require strict scope and expiry.
- Retention, deletion and backup semantics must be explicit.

## Required invariants

- Artifact versions are immutable; a new output creates a new version.
- Approval binds to exact artifact/version hashes, not a mutable filename.
- Checksum mismatch blocks downstream use.
- Storage locators are not authorization by themselves.
- Temporary files are not treated as durable completed outputs.
- Rights/provenance metadata remains linked to the asset and its derived uses.

## Open questions

- Which provider and region?
- Which artifacts need long-term retention versus temporary retention?
- Are source media and generated outputs subject to different retention rules?
- What is the maximum acceptable transfer time/size for local workers?

## Verification before implementation

- Upload/download large files with checksum verification.
- Expire and revoke transfer authorization.
- Recover artifact metadata after worker interruption.
- Verify exact-version references remain stable after new output generation.
- Test retention and deletion policy in a non-production environment.

## Owner decision

**Pending.** Accept object storage behind an abstraction; provider and retention policy remain open.

---

# ADR-010 — Separate lifecycle state machines

**Status:** PROPOSED  
**Decision owner:** Product owner  
**Scope:** Content, workflow, task, job, production run, review and distribution lifecycle.

## Context

The platform contains multiple objects that progress independently. Treating all progress as one generic `status` creates ambiguous transitions and makes recovery, audit and user-facing status unreliable.

The architecture reconciliation identified a need to distinguish content identity, workflow execution, job attempts, studio runs, approvals and distribution.

## Decision

Maintain **separate state machines per domain entity**, with explicit relationships and documented transition rules.

Recommended conceptual separation:

- Content item: editorial lifecycle.
- Content variant: format/platform readiness lifecycle.
- Workflow: end-to-end orchestration lifecycle.
- Task: logical unit of work and dependency lifecycle.
- Job: dispatch/lease/attempt lifecycle.
- Studio job: adapter-level execution request lifecycle.
- Production run: concrete engine execution lifecycle.
- Review: review-package lifecycle.
- Approval: decision lifecycle bound to an exact version/hash.
- Authorization: permission to perform a specific consequential action.
- Distribution: platform-specific delivery lifecycle.

Do not use a job's `completed` status to imply that content is approved or published. Do not use approval to imply authorization. Do not use a successful local render to imply that the workflow is complete.

## Alternatives considered

1. **Separate domain state machines** — recommended.
2. **One global content status** — rejected; cannot represent parallel variants and attempts.
3. **One status shared by workflow/job/run** — rejected; conflates orchestration and execution.

## Consequences

**Benefits**
- Accurate progress reporting.
- Independent retries without corrupting content state.
- Clear audit trail.
- Better handling of parallel formats and multiple production attempts.

**Costs / risks**
- More explicit transition definitions and mappings.
- UI must aggregate states carefully.
- Cross-entity transitions need transactional rules and event contracts.

## Required invariants

- Every state transition has an allowed-from/allowed-to rule.
- Transition actor and timestamp are recorded.
- Failed attempts do not erase successful prior artifacts.
- New content versions do not mutate historical approvals.
- Distribution status is platform- and attempt-specific.
- State mapping for UI summaries is derived, not stored as an ambiguous universal status.

## Verification before implementation

- Create transition tables for each entity.
- Test invalid transitions are rejected.
- Test retry after failure preserves prior artifacts and history.
- Test parallel variants have independent lifecycles.
- Test UI summary derivation against mixed states.

## Owner decision

**Pending.** Accept separate state machines and require explicit transition tables before implementation.

---

# ADR-007 — Centralized governance and publishing boundary

**Status:** PROPOSED  
**Decision owner:** Product owner  
**Scope:** Review, approval, authorization and all consequential distribution actions.

## Context

The current Shorts Studio reports identify paths where direct adapters may publish publicly without passing through a centralized approval boundary. In particular, direct execution paths were reported as able to bypass intended controls. A successful review or an approval record alone is not sufficient proof that a particular action is authorized.

The product needs a consistent governance boundary across every studio and platform adapter.

## Decision

All consequential distribution actions must pass through one **centralized policy and authorization service**. No studio or platform adapter may independently decide that publishing is permitted.

Keep these concepts separate:
- **Review:** evaluation of a specific review package.
- **Approval:** an editorial decision bound to exact content/artifact versions.
- **Authorization:** a policy decision permitting a specific action, destination and time window.
- **Execution:** the adapter performs the authorized action and records the result.

The initial safe baseline is **publishing disabled unless explicitly authorized**. Conditional automatic publishing remains an open policy decision and must not be enabled by this ADR.

## Alternatives considered

1. **Centralized governance boundary** — recommended.
2. **Per-adapter approval checks** — rejected; inconsistent and bypass-prone.
3. **Approval flag stored on content only** — rejected; does not bind exact versions or action scope.
4. **Trust the UI to hide publish buttons** — rejected; backend enforcement is mandatory.

## Consequences

**Benefits**
- One enforceable policy boundary.
- Easier audit and emergency pause.
- Adapters become execution-only components.
- Supports future conditional automation without weakening the baseline.

**Costs / risks**
- Existing direct publishing paths require authorized inspection and later remediation.
- Central policy service becomes a critical component.
- Authorization decisions need clear scope, expiry and revocation semantics.

## Required invariants

- No adapter publishes without a valid authorization decision.
- Authorization binds to exact content/variant/artifact version, platform/account, action and policy version.
- Approval is not authorization.
- Hard rights, safety and integrity blockers cannot be overridden by ordinary editorial approval.
- Emergency pause blocks new consequential actions.
- All attempts, including denials and failures, are auditable.
- Test and dry-run modes cannot silently become live modes.

## Verification before implementation

- Inventory every publish-capable entry point only after repository inspection is explicitly authorized.
- Add negative tests proving direct adapter calls fail without authorization.
- Test expired, revoked, mismatched-version and wrong-destination authorization.
- Test emergency pause across all adapters.
- Verify private/draft defaults independently for each platform adapter; do not infer long-form policy from Shorts policy.

## Owner decision

**Pending.** Accept the centralized governance boundary and keep all automatic publishing disabled until a separate policy decision is approved.

---

# ADR-008 — Quality severity and hard-gate policy

**Status:** OPEN  
**Decision owner:** Product owner  
**Scope:** Content quality checks, traceability, factual claims, technical validation and release eligibility.

## Context

Current Shorts Studio reports indicate that some quality conditions are warnings rather than blockers. Examples include storyboard `warn` behavior, factual-claim warnings and incomplete evidence/traceability. A quality score alone cannot safely express whether an output is eligible for a consequential action.

The system needs deterministic outcomes and clear distinction between editorial concerns and non-overridable integrity/safety blockers.

## Recommended direction

Define a centrally versioned quality policy with at least four outcomes:

- **PASS:** all required checks pass.
- **PASS_WITH_WARNINGS:** no hard blocker; warnings are visible and recorded.
- **NEEDS_REVIEW:** a human decision is required before the next protected stage.
- **BLOCKED:** a hard gate failed; ordinary editorial approval cannot bypass it.

The exact checks and thresholds must be configured by content type and workflow stage. Do not invent one universal numeric quality threshold before evaluation evidence exists.

Candidate hard-gate categories for owner review:
- missing or invalid required artifact;
- checksum/integrity failure;
- unresolved rights restriction for an asset used in the output;
- prohibited/safety-critical content condition;
- invalid or missing required approval/authorization;
- invalid provenance where provenance is mandatory;
- malformed or incomplete release package;
- failed technical validation required by the target platform.

Factual claim evidence policy needs a separate explicit threshold: not every claim necessarily requires the same evidence depth, but unsupported high-impact factual claims should not be silently treated as safe.

## Alternatives considered

1. **Severity-based policy with hard blockers** — recommended.
2. **One numeric quality score** — rejected as sole release criterion.
3. **Warnings for all failures** — rejected; cannot protect critical boundaries.
4. **Human approval can override every check** — rejected for integrity, rights and safety hard blockers.

## Consequences

**Benefits**
- Predictable workflow decisions.
- Explainable reasons for holds and blocks.
- Policy can evolve by format and risk class.
- Tests can verify enforcement.

**Costs / risks**
- Requires a maintained check catalogue and policy versions.
- False positives can slow production; false negatives create risk.
- Human review workload depends on calibrated thresholds.

## Open questions

- Which checks are hard blockers for Shorts, long-form and social text?
- Which claim categories require citations/evidence?
- Which warnings can be accepted by an editor, and how is acceptance recorded?
- What evidence is required to change a gate from warning to blocker?

## Verification before implementation

- Build a check catalogue with severity, scope, evidence and remediation.
- Test each hard gate with positive and negative fixtures.
- Test policy version changes do not retroactively mutate old decisions.
- Test warnings remain visible in review packages.
- Test a blocked package cannot be released through an ordinary approval action.

## Owner decision

**Pending.** Approve the four-outcome model and decide the initial hard-gate catalogue before implementation.

---

# ADR-009 — Rights evidence and asset-use policy

**Status:** OPEN  
**Decision owner:** Product owner  
**Scope:** Third-party media, generated assets, music, footage, images, fonts, templates and derived outputs.

## Context

Current architecture evidence indicates rights data is partial and may be represented as strings or per-run metadata rather than a centralized rights registry. Unknown rights must not be assumed to mean permitted use.

An asset may be reused across multiple content items and platforms, so rights evidence must be linked to the asset and the intended use, not only to one output folder.

## Recommended direction

Create a centralized asset-rights record linked to each reusable asset and each relevant use. Rights status should be explicit and evidence-backed.

Suggested rights states:
- `CLEARED` — documented basis supports the intended use and scope.
- `RESTRICTED` — use is permitted only under recorded conditions.
- `PENDING_VERIFICATION` — evidence is incomplete or awaiting review.
- `PROHIBITED` — known restriction disallows the intended use.
- `UNKNOWN` — no reliable rights conclusion is available.

For release eligibility, `UNKNOWN`, `PENDING_VERIFICATION` and `PROHIBITED` must block the affected use unless a separately defined, documented exception process is approved. Ordinary editorial approval must not silently override a rights restriction.

Record at minimum:
- asset identity and source/provenance;
- creator/owner where known;
- license or permission basis;
- evidence reference and capture date;
- allowed media, territories, platforms and commercial use;
- attribution requirements;
- expiry/revocation conditions;
- reviewer and verification timestamp;
- derived assets and affected content uses.

Generated content is not automatically rights-cleared for every component used to create it; source assets, model/provider terms and music/voice rights may still matter.

## Alternatives considered

1. **Centralized rights registry with use-specific checks** — recommended.
2. **Free-text license field only** — insufficient for automated enforcement.
3. **Assume unknown means allowed** — rejected.
4. **Store rights only in output metadata** — insufficient for reusable assets and cross-format use.

## Consequences

**Benefits**
- Reusable, auditable rights evidence.
- Safer cross-platform adaptation.
- Clear remediation for blocked assets.

**Costs / risks**
- Evidence collection and review add workflow overhead.
- Licenses can be complex and change over time.
- Automated parsing cannot replace legal interpretation for ambiguous terms.

## Open questions

- What evidence types are accepted for each source category?
- Who may verify or approve rights records?
- What is the exception process, if any?
- How are expired or revoked permissions propagated to existing content?
- Which third-party providers and asset sources are in scope initially?

## Verification before implementation

- Test that unknown rights block a protected release path.
- Test restricted rights against platform, territory and commercial-use scope.
- Test expiry/revocation invalidates future use authorization.
- Test derivative assets preserve provenance links.
- Test that approval cannot override prohibited rights status.

## Owner decision

**Pending.** Approve the rights-state model and decide the initial evidence and exception policy.

---

## 3. Cross-ADR dependency map

| Decision | Depends on | Must be settled before |
|---|---|---|
| ADR-001 IDs | None | Durable schema and event contracts |
| ADR-002 database | ADR-001 entity model | Shared persistence implementation |
| ADR-003 queue/events | ADR-001, ADR-002 | Durable orchestration |
| ADR-004 API contracts | ADR-001, ADR-003, ADR-006 | Worker/studio integration |
| ADR-005 worker security | ADR-004 | Remote worker connectivity |
| ADR-006 artifact storage | ADR-001, ADR-002, ADR-004 | Artifact transfer and durable media workflows |
| ADR-010 state machines | ADR-001, ADR-002 | Workflow implementation and UI status |
| ADR-007 governance | ADR-001, ADR-006, ADR-010 | Any production publishing path |
| ADR-008 quality gates | ADR-006, ADR-007, ADR-010 | Protected release eligibility |
| ADR-009 rights policy | ADR-006, ADR-007 | Asset ingestion and publishing eligibility |

---

## 4. Decisions deliberately not made in this pack

The following remain open or deferred in the Architecture Decision Register:

- Conditional automatic publishing policy, eligible formats, frequency limits and approval windows.
- Exact cloud provider, region, database provider, object-storage provider and monthly budget.
- Exact broker choice if database-backed queue proves insufficient.
- Worker capability matrix and which workloads may run remotely.
- Backup retention, RPO/RTO and disaster-recovery objectives.
- Monitoring provider and alert-routing configuration.
- Long-term analytics and feedback architecture.
- Team/multi-tenant/SaaS architecture.
- Vector database/search technology.
- Any change to existing agent ownership.
- Any repository-level implementation plan that requires inspection not yet authorized.

The previously discussed 12-hour Shorts and 48-hour long-form approval windows are examples only; they are not approved policy.

---

## 5. Owner review checklist

For each ADR, the owner should record one of:
- **ACCEPT** — approve the recommendation as written.
- **ACCEPT WITH AMENDMENT** — approve with a documented change.
- **REJECT** — do not adopt the recommendation.
- **DEFER** — keep open pending evidence or a later milestone.

| ADR | Subject | Recommended review action | Owner status |
|---|---|---|---|
| ADR-001 | Canonical IDs | Review UUIDv7 candidate | PENDING |
| ADR-002 | Database | Choose database direction/provider and cost envelope | PENDING |
| ADR-003 | Queue/events | Review database-backed queue baseline | PENDING |
| ADR-004 | API contracts | Review versioned HTTP/JSON baseline | PENDING |
| ADR-005 | Worker security | Review unique worker identity and scoped credentials | PENDING |
| ADR-006 | Artifact storage | Review object-storage abstraction | PENDING |
| ADR-010 | State machines | Review separation and require transition tables | PENDING |
| ADR-007 | Governance | Review centralized boundary; keep auto-publish disabled | PENDING |
| ADR-008 | Quality gates | Decide initial hard-gate catalogue | PENDING |
| ADR-009 | Rights policy | Decide rights states, evidence and exception policy | PENDING |

No owner approvals have been recorded in this version.

---

## 6. Implementation-readiness gate

**This ADR pack does not approve implementation.**

Before foundation implementation can be authorized:

1. Owner reviews and records decisions for ADR-001 through ADR-006 and ADR-010.
2. The canonical contracts and ADRs are checked for consistency.
3. P0 data model and state-transition tables are frozen as a versioned baseline.
4. Security and governance decisions are sufficient to prevent unsafe worker access and publishing bypass.
5. A separately scoped implementation plan identifies file ownership, tests, preservation rules and explicit permissions.
6. Repository inspection is separately authorized if implementation planning requires it; this pack does not grant that authorization.

Before any production publishing is enabled:

1. ADR-007 is accepted and implemented across every publish-capable path.
2. ADR-008 and ADR-009 hard gates are accepted and tested.
3. Platform-specific authorization, privacy defaults and emergency pause are verified.
4. Real-world execution is separately authorized and tested in a controlled manner.

### Current readiness statement

- Architecture decision drafting: **COMPLETE — DRAFT PACK CREATED**
- Owner decision approval: **PENDING**
- Implementation authorization: **NOT GRANTED**
- Repository inspection / Git operations: **NOT AUTHORIZED**
- Production deployment / real publishing: **NOT AUTHORIZED**

---

## 7. Change log

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-10-31 | Initial proposed ADR pack for P0 architecture decisions |

