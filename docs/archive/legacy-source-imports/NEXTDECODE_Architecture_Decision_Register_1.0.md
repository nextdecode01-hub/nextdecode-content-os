# NEXTDECODE Content OS
## Architecture Decision Register 1.0

**Document status:** Proposed decision register — owner decisions pending  
**Version:** 1.0  
**Prepared:** 31 October 2026  
**Purpose:** Track architecture decisions that must be confirmed before implementation, preserve already-locked product constraints, and prevent proposals from being mistaken for approvals.

> This register is a governance artifact. It does not approve implementation, repository inspection, Git operations, infrastructure deployment, paid services, uploads, or publishing. A decision becomes **ACCEPTED** only after the owner explicitly confirms it and the decision is recorded with date, rationale, and scope.

---

# 0. Decision governance

## 0.1 Status definitions

| Status | Meaning |
|---|---|
| **LOCKED** | Explicitly selected by the owner in prior discussions. Do not reopen without a new explicit request. |
| **PROPOSED** | Recommended option for owner review. Not approved. |
| **OPEN** | No decision has been made. |
| **DEFERRED** | Intentionally postponed until a named dependency or stage. |
| **ACCEPTED** | Explicitly approved by the owner and recorded in this register. |
| **REJECTED** | Explicitly declined by the owner. Preserve the rationale. |
| **SUPERSEDED** | Replaced by a later decision; retain for history. |

## 0.2 Decision record requirements

Every decision record should contain:
- Decision ID and title.
- Status.
- Context/problem.
- Options considered.
- Recommended option (if any).
- Consequences and trade-offs.
- Dependencies.
- Owner decision and date.
- Scope and review trigger.

No decision may be inferred from silence, a draft document, an assistant recommendation, a successful test, or a technical agent's report.

## 0.3 Decision principles

1. Preserve locked decisions.
2. Prefer the simplest architecture that meets the actual reliability and product requirements.
3. Avoid choosing infrastructure before the workload, cost, and operational needs are understood.
4. Keep provider-specific implementation behind replaceable interfaces where practical.
5. Design for hybrid operation without prematurely building a complex multi-tenant SaaS platform.
6. Fail closed for rights, safety, integrity, authentication, and authorization.
7. Separate editorial approval from permission to execute external side effects.
8. Make every external side effect traceable and idempotent.
9. Do not let the local PC become the source of truth for cloud-coordinated work.
10. Do not treat architecture readiness as production readiness.

---

# 1. Locked decisions and constraints

These are carried forward from explicit prior owner choices. They are not new recommendations.

| ID | Decision / constraint | Status | Scope and interpretation |
|---|---|---|---|
| L-01 | NEXTDECODE is the product/brand identity | **LOCKED** | Tagline: “Decode what comes next.” |
| L-02 | Content OS direction | **LOCKED** | One shared intelligence system, multiple content studios, multiple distribution channels, one operating environment. |
| L-03 | Hybrid deployment topology | **LOCKED** | Always-on cloud control plane plus local and remote workers. |
| L-04 | Cloud-authoritative control state | **LOCKED** | Cloud owns shared identity, workflow, job, policy, approval, and distribution state. |
| L-05 | Local Shorts rendering role | **LOCKED** | Local worker is preferred for existing Shorts Studio/FFmpeg-heavy rendering when the PC is available. |
| L-06 | PC-offline behavior | **LOCKED** | Local compute does not run while the PC is off. Supported cloud work continues; local-only work waits unless an eligible remote worker exists. |
| L-07 | Shorts Studio preservation | **LOCKED** | Retain the existing Shorts Studio as a specialized engine; integrate through a boundary/adapter rather than wholesale replacement. |
| L-08 | Initial operating mode | **LOCKED** | Single-owner Creator Mode, one initial workspace and NEXTDECODE brand. |
| L-09 | Future expansion posture | **LOCKED** | Architecture should not block future studios, teams, or SaaS evolution, but those are not initial implementation scope. |
| L-10 | Human control of critical actions | **LOCKED** | Critical actions require explicit control/approval; no silent assumption of consent. |
| L-11 | No production side effects by implication | **LOCKED** | No real publishing, upload, deployment, or external side effect without explicit authorization. |
| L-12 | No Git/repository operations | **LOCKED** | No Git operations of any kind until explicit superseding permission. |
| L-13 | Existing agent ownership | **LOCKED** | Qoder: Phase 11 engineering owner; OpenCode: Phase 10 engineering/closure owner; Kilo: independent read-only QA. |
| L-14 | Preserve existing WIP | **LOCKED** | No reset, revert, overwrite, cleanup of unrelated changes, or broad staging. |
| L-15 | Free-first development preference | **LOCKED** | Prefer free/local-first development where practical; this is not a guarantee that hybrid cloud operation can cost ₹0. |

## 1.1 Important non-decisions

The following are **not** locked merely because they appeared in drafts or recommendations:
- Database vendor or product.
- Cloud provider, hosting provider, or deployment region.
- Queue/broker product.
- Event transport.
- API framework or protocol.
- Object-storage provider.
- Vector database.
- Worker authentication product.
- Numeric publishing limits.
- Conditional auto-publishing policy.
- Approval time windows.
- Long-form publishing privacy defaults.
- Any production deployment budget.

---

# 2. Priority decision register

## 2.1 P0 — Must resolve before the corresponding foundation is implemented

### ADR-001 — Canonical identity and ID strategy

**Status:** PROPOSED  
**Recommendation:** Globally unique IDs, with UUIDv7 as the preferred candidate if the selected stack supports it reliably. Human-readable prefixes may be used for diagnostics but must not provide uniqueness.

**Context:** Existing reconciliation identified identifier namespace collisions and ambiguity between workflow, task, job, studio job, production run, artifact, and publication identities.

**Options:**
1. UUIDv7 with optional readable type prefix.
2. UUIDv4 with optional readable type prefix.
3. Database-generated numeric IDs.
4. Custom time-sortable identifiers.

**Trade-offs:**
- UUIDv7 improves temporal ordering and distributed generation.
- UUIDv4 is broadly supported but not time-sortable.
- Numeric IDs are compact but can expose sequencing and complicate distributed generation.
- Custom IDs add maintenance burden.

**Dependencies:** Database choice, language/runtime support, migration compatibility.

**Owner decision:** Pending.

---

### ADR-002 — Authoritative system-of-record database

**Status:** OPEN  
**Recommendation:** Use a PostgreSQL-compatible relational system as the authoritative shared store, subject to cost, operations, security, backup, and local-development evaluation. Keep SQLite for local cache/prototype use where justified, not as an automatic source of cloud truth.

**Context:** Content Graph relationships, transactional state transitions, audit history, approvals, and publishing authorization require reliable relational constraints and concurrency control.

**Options:**
1. Managed PostgreSQL-compatible service.
2. Self-hosted PostgreSQL.
3. SQLite-first with a later migration.
4. Another database after evidence-based comparison.

**Trade-offs:**
- Managed service reduces operational burden but may introduce recurring cost and provider dependence.
- Self-hosting improves control but creates backup, patching, monitoring, and recovery responsibilities.
- SQLite is excellent for local prototypes and single-process workflows but is not automatically suitable as the shared multi-worker authoritative control plane.

**Dependencies:** Hybrid deployment budget, provider choice, backup/RPO/RTO expectations, authentication model.

**Owner decision:** Pending.

---

### ADR-003 — Durable job queue and event delivery

**Status:** OPEN  
**Recommendation:** Require durable job state and transactional outbox/inbox or equivalent idempotent delivery. Select the actual queue/event technology only after evaluating the chosen database, hosting model, throughput, operational complexity, and cost.

**Context:** Work must survive PC shutdown, worker crashes, provider timeouts, and owner unavailability. Duplicate delivery is expected.

**Options:**
1. Database-backed durable queue for the initial workload.
2. Dedicated managed queue/broker.
3. Self-hosted broker.
4. Hybrid: database as source of truth plus broker for dispatch.

**Trade-offs:**
- Database-backed queue can reduce initial infrastructure but needs careful locking, polling, and scaling design.
- Dedicated broker can improve decoupling and throughput but adds operational cost and another failure domain.
- Hybrid approach separates durable state from dispatch but requires robust reconciliation.

**Minimum required regardless of technology:**
- durable jobs;
- leases and heartbeat/recovery;
- attempt history;
- retry and dead-letter behavior;
- idempotent consumers;
- stale-worker protection;
- event replay/reconciliation;
- no loss on process restart.

**Owner decision:** Pending.

---

### ADR-004 — API and contract serialization

**Status:** OPEN  
**Recommendation:** Start with versioned, schema-validated HTTP APIs for service boundaries unless a measured requirement justifies RPC or another transport. Keep contract definitions independent of a specific framework.

**Options:**
1. REST/JSON.
2. RPC/protobuf.
3. Mixed: HTTP/JSON for control APIs and a separate event transport.
4. Another approach.

**Trade-offs:** REST/JSON is easy to inspect and integrate; RPC can provide stronger generated typing and compact payloads; mixed systems increase tooling and compatibility complexity.

**Dependencies:** Language/runtime choices, schema registry/tooling, event transport.

**Owner decision:** Pending.

---

### ADR-005 — Worker identity and authentication

**Status:** OPEN  
**Recommendation:** Every worker and studio adapter must authenticate as a distinct machine identity, receive scoped short-lived credentials, and be authorized server-side for each workspace/job/artifact operation. Do not distribute unrestricted database credentials.

**Options:**
1. Short-lived signed tokens issued by a control-plane identity service.
2. Mutual TLS with worker certificates.
3. Managed workload identity where supported.
4. A carefully designed combination.

**Minimum requirements:**
- worker identity and revocation;
- scoped authorization;
- credential rotation;
- replay protection;
- audit trail;
- no secrets in job payloads or logs;
- separate human and machine identities.

**Owner decision:** Pending.

---

### ADR-006 — Artifact storage and transfer

**Status:** OPEN  
**Recommendation:** Store artifact metadata and relationships in the canonical data store; store large binaries in an abstracted object/file storage layer. Use scoped, short-lived transfer access and checksum validation.

**Options:**
1. Managed object storage.
2. Self-hosted S3-compatible storage.
3. Local filesystem for development plus a replaceable production storage adapter.
4. Another provider after cost and reliability comparison.

**Minimum requirements:**
- immutable artifact versions;
- SHA-256 or equivalent integrity checks;
- resumable/retry-safe transfer;
- scoped access grants;
- no global use of worker-local paths;
- backup/retention strategy;
- quarantine on integrity failure.

**Owner decision:** Pending.

---

### ADR-007 — Central governance and fail-closed publishing boundary

**Status:** PROPOSED  
**Recommendation:** Adopt a single centralized governance and publishing boundary. All studios and agents submit outputs and publication requests through it. No direct studio-to-platform publishing path is permitted.

**Context:** Prior reconciliation identified direct adapters capable of bypassing intended quality, approval, and publishing controls.

**Required behavior:**
- QA, rights, safety, and integrity checks are centrally evaluated.
- Approval binds to exact review package/artifact versions.
- Authorization is separate from approval.
- Publishing service checks a scoped grant at execution time.
- Unknown rights and hard blockers prevent publication.
- Provider timeouts trigger reconciliation before retry.
- Emergency pause prevents new side effects.

**Owner decision:** Pending explicit confirmation of the proposed governance contract. Existing no-bypass restrictions remain in force as safety requirements during design.

---

### ADR-008 — QA severity and hard-gate policy

**Status:** OPEN  
**Recommendation:** Use versioned QA profiles with explicit severity mapping. Do not treat warning-only results as passes when the corresponding check is configured as a hard gate.

**Context:** Prior report findings identified storyboard and factual-claim checks operating as warnings in some paths, while publishing bypasses also existed.

**Required decision areas:**
- which checks are blocking;
- which checks are warnings;
- what constitutes evidence coverage;
- whether missing/unknown provenance blocks release;
- how manual exceptions are recorded;
- who can approve an exception;
- whether exceptions expire.

**Owner decision:** Pending.

---

### ADR-009 — Rights evidence and asset-use policy

**Status:** OPEN  
**Recommendation:** Unknown, expired, or insufficiently documented rights must not be treated as cleared. A versioned rights policy should evaluate intended use, destination, territory, commercial use, and relevant restrictions.

**Required decision areas:**
- acceptable evidence types;
- stock provider/license evidence;
- music, footage, image, font, and model releases;
- derivative/transformative use rules;
- territory and duration;
- expiry and revocation;
- escalation/review process.

**Owner decision:** Pending.

---

### ADR-010 — Content, workflow, job, and publication state separation

**Status:** PROPOSED  
**Recommendation:** Keep separate state machines for Content Item, Workflow Run, Task, Job, Job Attempt, Worker, Studio Job, QA, Rights, Approval, Authorization, Publication Request, Publication, and Publication Attempt.

**Context:** A single status field cannot accurately represent content lifecycle, execution health, review, and distribution state.

**Required invariant:** A content item may be `IN_PRODUCTION` while its current job is `RETRY_WAIT` and its local worker is `OFFLINE`; these are not contradictory.

**Owner decision:** Pending.

---

## 2.2 P1 — Resolve before production operations or broader studio expansion

### ADR-011 — Conditional automatic publishing policy

**Status:** OPEN — NOT LOCKED  
**Context:** The owner previously selected conditional automatic publishing as a preferred direction for discussion, but requested implications before locking the policy.

**Recommendation:** Keep automatic publishing disabled until an explicit policy is approved and tested. Design the policy engine to support three outcomes:
- `AUTO_ELIGIBLE`
- `PENDING_APPROVAL`
- `BLOCKED`

**Open policy dimensions:**
- eligible formats;
- eligible platforms/accounts;
- content categories and risk classes;
- required QA and rights evidence;
- maximum daily/weekly frequency;
- scheduling windows;
- destination-specific metadata requirements;
- whether long-form is always manual approval initially;
- policy expiry and review cadence;
- emergency pause and rollback.

**Non-negotiable:** Pending approval never becomes automatic approval because the owner is unavailable.

**Owner decision:** Pending.

---

### ADR-012 — Human approval windows and escalation

**Status:** OPEN  
**Recommendation:** Do not hard-code the previously discussed 12-hour Shorts or 48-hour long-form windows. Treat them as unapproved examples until the owner chooses explicit values.

**Options:**
1. No expiry; remain pending until a decision.
2. Configurable expiry that returns to a safe hold state.
3. Expiry plus owner notification/escalation.
4. Format- and risk-specific windows.

**Required:** No timeout may silently authorize publication.

**Owner decision:** Pending.

---

### ADR-013 — Local versus remote worker eligibility

**Status:** PARTIALLY LOCKED  
**Locked:** Hybrid topology; local worker preferred for existing Shorts Studio/FFmpeg-heavy rendering when available.

**Open:** Which jobs may run remotely, what data may leave the local machine, whether remote rendering is enabled, and the cost/resource limits.

**Recommendation:** Capability- and policy-based scheduling. Local-only tasks remain queued when local worker is offline. Remote execution requires explicit capability, security, cost, and data-handling approval.

**Owner decision:** Pending for detailed worker matrix.

---

### ADR-014 — Shorts Studio adapter process boundary

**Status:** OPEN  
**Recommendation:** Start with the thinnest safe adapter around the existing production entry point. Choose in-process wrapper versus separate worker service only after repository inspection is explicitly authorized and compatibility is demonstrated.

**Required validation:**
- run identity and attempt mapping;
- current file-based input/output formats;
- artifact registration;
- runtime behavior of run tracker;
- QA and approval handoff;
- no direct publishing;
- retry and cancellation safety;
- preserve existing WIP.

**Owner decision:** Pending.

---

### ADR-015 — Monitoring, backup, and recovery objectives

**Status:** OPEN  
**Recommendation:** Define service-level expectations before production deployment.

**Required values:**
- Recovery Point Objective (RPO).
- Recovery Time Objective (RTO).
- backup frequency and retention;
- restore-test cadence;
- artifact durability/retention;
- worker offline alert thresholds;
- queue age thresholds;
- provider failure alerts;
- emergency pause behavior;
- operational cost ceiling.

**Owner decision:** Pending.

---

### ADR-016 — Analytics and learning feedback

**Status:** DEFERRED to analytics stage  
**Recommendation:** Preserve canonical publication IDs and metric provenance now; defer advanced recommendation/experimentation logic until reliable publication and analytics linkage exists.

**Minimum foundation:** Every metric snapshot links to a known publication, destination, capture time, and source. Do not infer causality from raw metrics.

**Owner decision:** Deferred.

---

### ADR-017 — Multi-user, team, and SaaS tenancy

**Status:** DEFERRED  
**Recommendation:** Keep workspace and actor scope in contracts from the beginning, but do not implement team roles, billing, tenant isolation, or SaaS operations in the initial Creator Mode foundation.

**Owner decision:** Deferred.

---

### ADR-018 — Vector search and dedicated knowledge retrieval

**Status:** DEFERRED pending demonstrated need  
**Recommendation:** Start with structured research/source/evidence records and conventional search. Add embeddings/vector retrieval only when a measurable retrieval requirement justifies the added operational complexity.

**Owner decision:** Deferred.

---

# 3. Recommended decision order

Do not try to decide every detail at once. The following order minimizes rework.

| Order | Decisions | Why now |
|---|---|---|
| 1 | ADR-001 Identity, ADR-010 state separation | Defines stable nouns and lifecycle boundaries |
| 2 | ADR-002 database, ADR-003 queue/events | Defines authoritative persistence and execution foundation |
| 3 | ADR-004 APIs, ADR-005 worker identity | Defines safe service/worker communication |
| 4 | ADR-006 artifact storage | Required for cross-worker production and immutable outputs |
| 5 | ADR-007 governance, ADR-008 QA, ADR-009 rights | Required before any publishing path is enabled |
| 6 | ADR-014 Shorts adapter | Requires current-system compatibility discovery |
| 7 | ADR-011/012 autonomy and approval windows | Requires tested governance and explicit owner policy |
| 8 | ADR-015 recovery objectives | Must precede production deployment |
| 9 | ADR-016/017/018 | Later-stage capabilities; keep boundaries ready, defer implementation |

---

# 4. Proposed initial baseline

The following is the recommended coherent baseline to review. It is **not accepted** until explicitly confirmed.

| Area | Proposed baseline |
|---|---|
| Identity | Globally unique IDs; UUIDv7 candidate |
| Data store | PostgreSQL-compatible relational system of record |
| Local data | SQLite/files only for local cache or bounded prototypes |
| Queue | Start by evaluating database-backed durable queue; preserve option for broker later |
| Events | Versioned events; at-least-once delivery; idempotent consumers; transactional outbox/inbox pattern |
| APIs | Versioned schema-validated HTTP/JSON initially |
| Worker security | Distinct machine identity, short-lived scoped credentials, server-side authorization |
| Artifacts | Metadata in canonical store; binaries in abstracted object storage; immutable versions and checksums |
| Content Graph | Relational entities and explicit relationships; no graph database requirement by default |
| Workflow | Separate workflow/job/attempt/worker/studio/content state machines |
| Governance | Centralized quality, rights, approval, authorization, and publishing boundary |
| Publishing | Disabled until owner approves a separate conditional-publishing policy |
| Shorts integration | Thin adapter; existing engine retained; dry-run first |
| Deployment | Hybrid topology already locked; provider/service selection remains open |
| Operations | Backup, restore, monitoring, emergency pause, and cost controls before production |

---

# 5. Current-system evidence and limits

The architecture reconciliation reports describe the existing Shorts Studio as a file-based pipeline with reusable research, script, voice, visual, render/QA, review, and publishing components. They also identify gaps such as:
- no shared Content Graph;
- incomplete integration of run tracking;
- incomplete central artifact/rights registry;
- warning-only checks in some paths;
- direct publishing paths that may bypass centralized controls;
- incomplete linkage between analytics and production runs;
- unauthenticated API/in-memory job limitations in the reported baseline.

These are **report-backed historical findings**, not a fresh inspection of the current repository. They must be revalidated only after the owner explicitly permits repository inspection. No current code compatibility should be assumed from this register.

---

# 6. Decision approval log

No new decisions have been approved by creating this document.

| Decision ID | Owner decision | Date | Rationale / conditions |
|---|---|---|---|
| ADR-001 | Pending | — | — |
| ADR-002 | Pending | — | — |
| ADR-003 | Pending | — | — |
| ADR-004 | Pending | — | — |
| ADR-005 | Pending | — | — |
| ADR-006 | Pending | — | — |
| ADR-007 | Pending | — | — |
| ADR-008 | Pending | — | — |
| ADR-009 | Pending | — | — |
| ADR-010 | Pending | — | — |
| ADR-011 | Pending | — | — |
| ADR-012 | Pending | — | — |
| ADR-013 | Pending | — | — |
| ADR-014 | Pending | — | — |
| ADR-015 | Pending | — | — |
| ADR-016 | Deferred | — | Analytics stage |
| ADR-017 | Deferred | — | Multi-user/SaaS stage |
| ADR-018 | Deferred | — | Demonstrated retrieval need |

---

# 7. Readiness gates

## Gate A — Contract baseline accepted
- [ ] Canonical entity glossary accepted.
- [ ] ID strategy accepted or explicitly deferred.
- [ ] Separate state machines accepted.
- [ ] Task/job/studio/event envelopes accepted.
- [ ] Artifact/asset/manifest distinctions accepted.
- [ ] Approval versus authorization accepted.

## Gate B — Foundation technology decisions
- [ ] Database decision recorded.
- [ ] Queue/event delivery decision recorded.
- [ ] API/serialization decision recorded.
- [ ] Worker identity/security decision recorded.
- [ ] Artifact storage/transfer decision recorded.
- [ ] Backup and recovery objectives drafted.

## Gate C — Governance readiness
- [ ] Blocking QA checks defined.
- [ ] Rights evidence policy defined.
- [ ] Approval scope/version binding accepted.
- [ ] Authorization grant contract accepted.
- [ ] Direct publishing bypasses addressed.
- [ ] Emergency pause tested.
- [ ] Conditional publishing policy separately approved or explicitly disabled.

## Gate D — Existing system integration readiness
- [ ] Repository inspection explicitly authorized.
- [ ] Existing WIP preserved.
- [ ] Current data structures and runtime behavior inspected.
- [ ] Shorts adapter boundary validated.
- [ ] No unapproved dependency or environment changes.
- [ ] Dry-run integration tests pass.
- [ ] Independent QA evidence recorded.

## Gate E — Production readiness
- [ ] Security tests pass.
- [ ] Retry/idempotency and failure recovery tests pass.
- [ ] Backup restore verified.
- [ ] Monitoring and alerting operational.
- [ ] Cost limits configured.
- [ ] Owner explicitly authorizes production deployment and any external side effects.

**Current overall status:** Gate A is ready for owner review; Gates B–E are not approved or demonstrated by this document.

---

# 8. Recommended next step

Review the **proposed initial baseline** in Section 4 and the P0 decisions in Section 2.1. Once those are accepted or corrected, update this register with the owner's actual decisions and create a concise Architecture Decision Records (ADR) set for the accepted choices.

Do not start implementation merely because this register exists. Implementation requires a separate explicit go-ahead and, where compatibility work is needed, explicit permission for repository inspection. All current repository/Git restrictions and agent ownership remain unchanged.

---

**End of NEXTDECODE Architecture Decision Register 1.0**
