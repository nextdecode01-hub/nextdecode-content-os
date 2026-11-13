# NEXTDECODE Content OS — Accepted P0 Architecture Decision Baseline 1.0

**Status:** Owner decisions recorded  
**Version:** 1.0  
**Date:** 31 October 2026  
**Purpose:** Consolidate the ten explicit owner decisions made during the P0 architecture review.

Related documents:
- `NEXTDECODE_Architecture_Decision_Register_1.0.md`
- `NEXTDECODE_Architecture_Decision_Records_Pack_1.0.md`
- `NEXTDECODE_P0_Foundation_Implementation_Specification_1.0.md`
- `NEXTDECODE_P0_Owner_Decision_Review_Sheet_1.0.md`
- `NEXTDECODE_P0_Implementation_Authorization_Brief_1.0.md`
- `NEXTDECODE_Canonical_Contracts_Pack_1.0.md`

---

## 1. Decision summary

The owner explicitly accepted all ten P0 architecture recommendations in the conversation.

| ADR | Decision | Accepted baseline |
|---|---|---|
| ADR-001 | Canonical identity | UUIDv7 for canonical IDs |
| ADR-002 | System of record | PostgreSQL-compatible relational database |
| ADR-003 | Durable queue and events | Database-backed durable queue, transactional outbox/inbox initially |
| ADR-004 | API and serialization | Versioned HTTP/JSON with schema validation |
| ADR-005 | Worker identity/security | Unique worker identity, scoped short-lived credentials, capability-based authorization |
| ADR-006 | Artifact storage | Metadata in PostgreSQL; binary files in object storage behind an abstraction |
| ADR-007 | Governance/publishing | Centralized authorization boundary; no adapter bypass; automatic publishing remains disabled pending separate policy approval |
| ADR-008 | Quality gates | PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW, BLOCKED; hard blockers cannot be bypassed by ordinary approval |
| ADR-009 | Rights and asset-use | Centralized evidence-backed rights states and use-specific enforcement |
| ADR-010 | Lifecycle state machines | Separate lifecycle state machines for content, workflow, execution, review, approval, authorization and distribution |

**Owner decision status: 10/10 accepted.**

This records architecture decisions only. It is not implementation authorization.

---

## 2. Detailed accepted decisions

### ADR-001 — Canonical identity and ID strategy

**Outcome:** ACCEPT

- UUIDv7 accepted as canonical ID format.
- IDs are opaque, globally unique and immutable.
- Entity type and relationships remain explicit.
- Legacy Shorts Studio identifiers remain external/source references.

### ADR-002 — Canonical database / system of record

**Outcome:** ACCEPT

- PostgreSQL-compatible relational database accepted as the authoritative shared control-plane store.
- Hosting provider, region and budget remain open.
- Local SQLite may be used for development or cache where appropriate, but not as a competing authority for shared state.

### ADR-003 — Durable queue and event delivery

**Outcome:** ACCEPT — Option A

- Start with a database-backed durable queue.
- Use transactional outbox/inbox semantics.
- Use leases, bounded retries, recovery and idempotency.
- A dedicated broker may be introduced later if workload evidence justifies it.

### ADR-004 — API and serialization contracts

**Outcome:** ACCEPT

- Versioned HTTP/JSON contracts.
- Schema validation at system boundaries.
- Large binaries transferred through artifact storage rather than ordinary JSON payloads.

### ADR-005 — Worker identity and authentication

**Outcome:** ACCEPT

- Each worker receives a unique machine identity.
- Use scoped, short-lived/renewable credentials.
- Enforce capability-based job authorization.
- Credentials can be revoked per worker.
- Human and machine identities remain separate.

### ADR-006 — Artifact and binary storage

**Outcome:** ACCEPT

- PostgreSQL stores artifact/asset metadata and references.
- Binary files live in object storage behind a provider-independent abstraction.
- Artifact versions are immutable.
- Transfers are scoped and time-limited, with checksum verification.
- Provider and retention policy remain open.

### ADR-007 — Centralized governance and publishing boundary

**Outcome:** ACCEPT

- All consequential distribution actions pass through centralized authorization.
- No publishing adapter may bypass the boundary.
- Review, approval, authorization and execution are separate.
- Emergency pause is required.
- Automatic publishing remains disabled until a separate policy is approved.
- Production publishing is not authorized by this decision.

### ADR-008 — Quality severity and hard-gate policy

**Outcome:** ACCEPT

Accepted outcomes:
- `PASS`
- `PASS_WITH_WARNINGS`
- `NEEDS_REVIEW`
- `BLOCKED`

- Hard blockers are required.
- Ordinary editorial approval cannot override hard blockers.
- Exact hard-gate catalogue, severity mapping and thresholds remain to be defined and approved.

### ADR-009 — Rights evidence and asset-use policy

**Outcome:** ACCEPT

Accepted rights states:
- `CLEARED`
- `RESTRICTED`
- `PENDING_VERIFICATION`
- `PROHIBITED`
- `UNKNOWN`

- Use-specific rights enforcement is required.
- Unknown or pending rights block the affected protected use under the accepted proposed baseline.
- Rights evidence must cover applicable platform, territory and commercial-use scope.
- Derived assets retain provenance.
- Ordinary editorial approval cannot override prohibited rights.
- Detailed evidence requirements and exception process remain to be defined.

### ADR-010 — Separate lifecycle state machines

**Outcome:** ACCEPT

- Content and variant lifecycles are distinct.
- Workflow, task, job and production-run lifecycles are distinct.
- Review and approval lifecycles are distinct.
- Authorization and distribution lifecycles are distinct.
- State transition tables and UI aggregation rules must be defined before implementation.

---

## 3. Architecture baseline now established

The accepted decisions establish the following conceptual foundation:

1. UUIDv7 identifies canonical entities.
2. PostgreSQL is the authoritative shared state store.
3. Durable job dispatch initially uses PostgreSQL-backed queue patterns.
4. HTTP/JSON contracts connect control plane and workers.
5. Workers authenticate independently and receive scoped permissions.
6. Artifact metadata is relational; large binaries are stored separately.
7. Governance is centralized and cannot be bypassed by adapters.
8. Quality and rights policy outcomes are explicit and enforceable.
9. Lifecycle state is separated by domain entity.
10. Hybrid topology remains the previously locked deployment direction.

This is a technology and contract baseline, not a deployment design. It does not select a cloud provider, storage provider, broker, region or budget.

---

## 4. Remaining details that are still open

Acceptance of an ADR's direction does not automatically decide every implementation parameter.

| Area | Still open |
|---|---|
| PostgreSQL | Provider, region, connection strategy, monthly budget |
| Queue | Exact schema, polling/claim strategy, lease duration, retry classes |
| Outbox/inbox | Retention, cleanup and replay policy |
| API | Schema tooling, compatibility window, exact endpoint catalogue |
| Worker security | Credential issuer, renewal cadence, local secret storage |
| Object storage | Provider, region, retention, lifecycle and egress controls |
| State machines | Full transition tables and invalid-transition handling |
| Governance | Exact authorization policy schema, roles and policy versioning |
| Quality | Check catalogue, severity per workflow stage and thresholds |
| Rights | Evidence types, verification authority, exception process and revocation propagation |
| Operations | RPO/RTO, backups, monitoring, alert routing and runbooks |
| Workload placement | Exact local versus remote worker capability matrix |

Do not silently infer these details from the accepted high-level decisions.

---

## 5. Decisions not included in the ten accepted ADRs

The following remain unapproved or deferred:

- Conditional automatic publishing policy, eligible formats and frequency limits.
- Approval expiry windows (previous 12h/48h examples remain examples only).
- Long-form publishing privacy behavior.
- Cloud provider and region.
- Infrastructure budget.
- Dedicated message broker adoption.
- Exact worker workload placement.
- Backup/recovery targets.
- Monitoring provider.
- Teams, tenancy, billing and SaaS.
- Vector database/search.
- Any change to existing agent ownership.

---

## 6. Authorization boundary

The owner acceptance of ADR-001 through ADR-010 does **not** grant any of the following permissions:

| Action | Status |
|---|---|
| Repository inspection | NOT AUTHORIZED |
| Running repository tests/commands | NOT AUTHORIZED |
| Git read operations | NOT AUTHORIZED |
| Git write operations | NOT AUTHORIZED |
| Source-code modification | NOT AUTHORIZED |
| Test/configuration modification | NOT AUTHORIZED |
| Dependency installation or environment changes | NOT AUTHORIZED |
| Cloud account/resource creation | NOT AUTHORIZED |
| Paid service activation | NOT AUTHORIZED |
| Deployment | NOT AUTHORIZED |
| Production generation | NOT AUTHORIZED |
| Platform upload or publishing | NOT AUTHORIZED |

Existing agent ownership remains unchanged:
- Qoder — Phase 11 engineering owner.
- OpenCode — Phase 10 engineering/closure owner.
- Kilo — independent read-only QA.

No agent task has been initiated by this decision record.

---

## 7. Next required work

The next architecture deliverable should be a **P0 Detailed Contract Freeze Pack** covering only the remaining implementation-critical details:

1. Canonical entity and relationship schema.
2. Full state-transition tables.
3. Job/lease/retry/outbox/inbox semantics.
4. Worker registration, credentials and capability model.
5. Artifact metadata, versioning and transfer contracts.
6. Quality and rights policy interfaces.
7. Authorization request/decision contract.
8. Error taxonomy, audit event and correlation conventions.

After that, a read-only current-system baseline assessment may be separately authorized. The assessment should identify reuse and integration boundaries before any code changes are planned.

---

## 8. Current status

- ADR-001 through ADR-010: **ACCEPTED**
- High-level P0 architecture baseline: **ESTABLISHED**
- Remaining detailed contracts: **NOT YET FROZEN**
- Provider and budget decisions: **OPEN**
- Implementation authorization: **NOT GRANTED**
- Repository inspection: **NOT AUTHORIZED**
- Git operations: **NOT AUTHORIZED**
- Code changes: **NOT AUTHORIZED**
- Deployment / production actions: **NOT AUTHORIZED**

---

## 9. Change log

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-10-31 | Recorded ten explicit owner-accepted P0 architecture decisions |
