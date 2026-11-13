# NEXTDECODE Content OS — P0 Owner Decision Review Sheet 1.0

**Document status:** For product-owner review  
**Version:** 1.0  
**Date:** 31 October 2026  
**Purpose:** Record explicit owner decisions before P0 implementation authorization.

Related:
- `NEXTDECODE_Architecture_Decision_Register_1.0.md`
- `NEXTDECODE_Architecture_Decision_Records_Pack_1.0.md`
- `NEXTDECODE_P0_Foundation_Implementation_Specification_1.0.md`
- `NEXTDECODE_Canonical_Contracts_Pack_1.0.md`

---

## 1. How to use this sheet

For each decision, choose one outcome:

- **ACCEPT** — accept the recommendation as written.
- **ACCEPT WITH AMENDMENT** — accept it with a clearly described change.
- **REJECT** — do not adopt the recommendation.
- **DEFER** — leave it open until specified evidence or a later milestone is available.

A decision is not accepted because it appears in a proposal, specification, checklist or chat recommendation. It becomes accepted only when the owner explicitly records the outcome.

### Important guardrails

This review sheet:
- does not authorize repository inspection or Git operations;
- does not authorize code changes or agent execution;
- does not authorize dependency installation or environment changes;
- does not authorize cloud account creation, paid services or deployment;
- does not authorize production generation, upload or publishing;
- does not change existing agent ownership.

---

## 2. Existing constraints — confirm unchanged

These are already established constraints, not new decisions in this sheet.

| ID | Constraint | Current status |
|---|---|---|
| C-01 | NEXTDECODE Content OS, single-owner Creator Mode first | LOCKED |
| C-02 | One initial brand: NEXTDECODE | LOCKED |
| C-03 | Hybrid deployment direction | LOCKED |
| C-04 | Always-on cloud control plane | LOCKED |
| C-05 | Cloud-authoritative shared workflow/control state | LOCKED |
| C-06 | Local worker executes Shorts Studio/heavy local rendering when PC is available | LOCKED |
| C-07 | Shorts Studio is integrated, not replaced wholesale | LOCKED |
| C-08 | Critical actions remain human-controlled unless a separate policy is approved | LOCKED |
| C-09 | No production generation, upload or publishing without explicit authorization | LOCKED |
| C-10 | Qoder, OpenCode and Kilo ownership remains unchanged | LOCKED |
| C-11 | Kilo remains independent read-only QA | LOCKED |
| C-12 | No Git operations of any kind until explicit superseding permission | LOCKED |
| C-13 | Preserve existing WIP; no destructive cleanup or broad overwrite | LOCKED |
| C-14 | Cloud/database/queue/storage provider and budget are not selected | OPEN |

If any locked constraint is to change, it requires a separate explicit superseding decision. Do not silently amend it through an ADR response.

---

## 3. P0 architecture decisions

### Decision 1 — Canonical identity and ID format

**ADR:** ADR-001  
**Recommendation:** Use opaque globally unique IDs; UUIDv7 is the candidate.

Why it matters:
- IDs connect content, variants, workflows, tasks, jobs, workers, runs and artifacts.
- Stable identity is required for event correlation and safe retries.
- Legacy Shorts Studio IDs remain external references, not global identity.

Alternatives:
- UUIDv7
- UUIDv4
- Database-generated numeric IDs
- Human-readable IDs

**Owner outcome:** PENDING

**Owner notes / amendment:**

____________________________________________________________

____________________________________________________________

### Decision 2 — Canonical database / system of record

**ADR:** ADR-002  
**Recommendation:** Use a PostgreSQL-compatible relational database as the canonical shared control-plane store. Provider and cost remain open.

Why it matters:
- Shared state must survive PC and process downtime.
- Workflow, jobs, approvals, policy and audit records need transactional consistency.
- Local SQLite may be useful for development/cache, but should not become a competing authority.

Alternatives:
- PostgreSQL-compatible relational database
- SQLite-only
- Document database
- Multiple databases from day one

**Owner outcome:** PENDING

**Provider / cost constraints / amendment:**

____________________________________________________________

____________________________________________________________

### Decision 3 — Durable queue and event delivery

**ADR:** ADR-003  
**Recommendation:** Start with a database-backed durable job model and transactional outbox/inbox; introduce a dedicated broker only if evidence requires it.

Why it matters:
- Work must survive restarts.
- Local-only work must wait safely while the PC is offline.
- At-least-once delivery, idempotency, leases and recovery must be explicit.

Alternatives:
- Database-backed queue
- Dedicated broker from the start
- In-memory queue
- Cron-only scheduling

**Owner outcome:** PENDING

**Owner notes / amendment:**

____________________________________________________________

____________________________________________________________

### Decision 4 — API and serialization contracts

**ADR:** ADR-004  
**Recommendation:** Versioned HTTP/JSON contracts with schema validation.

Why it matters:
- Cloud control plane and local/remote workers need a stable boundary.
- Components should not depend on undocumented database internals.
- Large media binaries should travel through controlled artifact transfer, not JSON payloads.

Alternatives:
- HTTP/JSON with schemas
- gRPC / Protocol Buffers
- Direct worker database access
- Unversioned ad hoc JSON

**Owner outcome:** PENDING

**Schema tooling / compatibility notes:**

____________________________________________________________

____________________________________________________________

### Decision 5 — Worker identity and authentication

**ADR:** ADR-005  
**Recommendation:** Unique machine identity for every worker, with scoped short-lived credentials and server-side capability authorization.

Why it matters:
- A worker must not be trusted only because it knows a job ID.
- Credentials need independent revocation and audit attribution.
- Human identity and machine identity must remain distinct.

Alternatives:
- Unique worker identities and scoped credentials
- One shared API key
- Reused user session credentials
- Unauthenticated local-network trust

**Owner outcome:** PENDING

**Security notes / amendment:**

____________________________________________________________

____________________________________________________________

### Decision 6 — Artifact and binary storage

**ADR:** ADR-006  
**Recommendation:** Store metadata in the canonical database and binaries behind an object-storage abstraction. Provider and retention remain open.

Why it matters:
- Media files are large and should not be stored as ordinary relational rows.
- Artifacts need immutable versions, checksums and controlled transfer.
- Approval must bind to an exact artifact version/hash.

Alternatives:
- Object storage abstraction
- Database BLOBs
- Local filesystem as global store
- Provider-specific URLs embedded throughout the product

**Owner outcome:** PENDING

**Provider / retention / cost notes:**

____________________________________________________________

____________________________________________________________

### Decision 7 — Separate lifecycle state machines

**ADR:** ADR-010  
**Recommendation:** Keep content, variant, workflow, task, job, production run, review, approval, authorization and distribution lifecycles separate.

Why it matters:
- A completed job does not mean content is approved or published.
- A render attempt is not the content identity.
- Parallel variants and retries need independent state.

**Owner outcome:** PENDING

**Required amendment or transition-table notes:**

____________________________________________________________

____________________________________________________________

### Decision 8 — Centralized governance and publishing boundary

**ADR:** ADR-007  
**Recommendation:** All consequential distribution actions pass through one centralized authorization boundary. Keep automatic publishing disabled until a separate policy is approved.

Why it matters:
- Direct adapters must not bypass approval/authorization.
- Approval is not the same as authorization.
- Emergency pause and audit must apply across all publish-capable paths.

**Owner outcome:** PENDING

**Governance notes / amendment:**

____________________________________________________________

____________________________________________________________

### Decision 9 — Quality severity and hard gates

**ADR:** ADR-008  
**Recommendation:** Use four explicit outcomes: PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW and BLOCKED. Define hard blockers by content type and workflow stage.

Why it matters:
- A single quality score cannot express release eligibility.
- Rights, safety and integrity blockers must not be bypassed by ordinary approval.
- Warnings and remediation need to remain visible.

**Owner outcome:** PENDING

**Initial hard-gate decisions / amendment:**

____________________________________________________________

____________________________________________________________

### Decision 10 — Rights evidence and asset-use policy

**ADR:** ADR-009  
**Recommendation:** Use a centralized rights record with explicit states: CLEARED, RESTRICTED, PENDING_VERIFICATION, PROHIBITED and UNKNOWN.

Why it matters:
- Unknown rights cannot silently mean permitted use.
- Rights must apply to the intended platform, territory and commercial context.
- Derived assets need provenance links.

**Owner outcome:** PENDING

**Evidence / exception policy notes:**

____________________________________________________________

____________________________________________________________

---

## 4. Operational decisions — keep separate from architecture approval

These are important but should not be forced into a premature provider or budget choice.

| ID | Decision | Current position | Owner outcome |
|---|---|---|---|
| O-01 | Cloud provider and region | Not selected | PENDING |
| O-02 | Monthly infrastructure budget | Not specified | PENDING |
| O-03 | Database provider | Not selected | PENDING |
| O-04 | Object-storage provider | Not selected | PENDING |
| O-05 | Dedicated broker | Defer until workload evidence | PENDING |
| O-06 | Backup retention | Not specified | PENDING |
| O-07 | Recovery point objective (RPO) | Not specified | PENDING |
| O-08 | Recovery time objective (RTO) | Not specified | PENDING |
| O-09 | Monitoring/alert provider | Not selected | PENDING |
| O-10 | Local/remote worker capability matrix | Not finalized | PENDING |
| O-11 | Conditional automatic publishing | Not approved; disabled baseline | PENDING |
| O-12 | Publishing frequency limits | Not specified | PENDING |
| O-13 | Approval expiry windows | 12h/48h were examples only | PENDING |
| O-14 | Long-form publishing privacy behavior | Must be independently reviewed | PENDING |

Notes:

____________________________________________________________

____________________________________________________________

---

## 5. P0 scope confirmation

**Recommendation:** Approve the narrow foundation scope, not the full Content OS.

P0 includes:
- canonical identity and minimum domain model;
- durable shared persistence;
- workflow/task/job state;
- durable dispatch, leases and recovery;
- worker registry, authentication and capabilities;
- versioned API/event contracts;
- artifact metadata and controlled transfer;
- separate lifecycle state machines;
- centralized authorization boundary;
- quality/rights policy interfaces;
- audit and observability;
- one controlled vertical-slice demonstration.

P0 excludes:
- full research and strategy intelligence;
- complete multiformat creation;
- broad autonomous agent orchestration;
- automatic public publishing;
- full analytics and optimization;
- teams, tenancy, SaaS billing;
- vector infrastructure;
- wholesale Shorts Studio rewrite.

**P0 scope outcome:** PENDING

**Scope amendment:**

____________________________________________________________

____________________________________________________________

---

## 6. Readiness and authorization are separate

Even if all architecture recommendations are accepted, implementation does not automatically begin.

### Gate A — Architecture baseline

- [ ] ADR decisions recorded.
- [ ] Canonical contracts reconciled.
- [ ] P0 domain model and state transitions frozen.
- [ ] Open questions have owners or explicit deferral.

### Gate B — Implementation authorization

- [ ] Exact repository inspection permission granted, if needed.
- [ ] Exact implementation scope authorized.
- [ ] Existing work-in-progress preservation plan agreed.
- [ ] File ownership and agent responsibilities confirmed without changing current ownership.
- [ ] Test commands and environment constraints agreed.
- [ ] Git permissions remain separately controlled.
- [ ] Dependency installation/environment changes remain separately controlled.

### Gate C — P0 acceptance

- [ ] Acceptance matrix passes.
- [ ] Failure recovery demonstrated.
- [ ] Worker security tests pass.
- [ ] Artifact integrity/access tests pass.
- [ ] Governance negative tests pass.
- [ ] Audit trail demonstrated.

### Gate D — Hybrid operational readiness

- [ ] Cloud services selected and authorized.
- [ ] Budget approved.
- [ ] Backup/restore tested.
- [ ] Monitoring and alerting operational.
- [ ] Worker reconnect/revocation tested.
- [ ] Runbooks reviewed.

### Gate E — Production distribution readiness

- [ ] Every publishing path passes centralized authorization.
- [ ] Rights and quality gates verified.
- [ ] Platform-specific privacy defaults independently checked.
- [ ] Emergency pause tested.
- [ ] Production action explicitly authorized.

---

## 7. Decision log

Complete this table as decisions are made. Do not backfill approvals based on assumptions.

| ADR | Outcome | Amendment / conditions | Decision date |
|---|---|---|---|
| ADR-001 | PENDING | — | — |
| ADR-002 | PENDING | — | — |
| ADR-003 | PENDING | — | — |
| ADR-004 | PENDING | — | — |
| ADR-005 | PENDING | — | — |
| ADR-006 | PENDING | — | — |
| ADR-010 | PENDING | — | — |
| ADR-007 | PENDING | — | — |
| ADR-008 | PENDING | — | — |
| ADR-009 | PENDING | — | — |

**Owner approval record**

- Owner decision: PENDING
- Approved ADR pack version: —
- Approved P0 specification version: —
- Conditions: —
- Explicit implementation authorization: NO
- Explicit repository inspection authorization: NO
- Explicit Git authorization: NO
- Explicit production action authorization: NO

---

## 8. Recommended decision sequence

To minimize rework, review in this order:

1. ADR-001 — identity.
2. ADR-002 — database.
3. ADR-003 — durable queue.
4. ADR-004 — API contracts.
5. ADR-005 — worker security.
6. ADR-006 — artifact storage.
7. ADR-010 — state machines.
8. ADR-007 — governance boundary.
9. ADR-008 — quality hard gates.
10. ADR-009 — rights policy.
11. Confirm P0 scope.
12. Decide operational provider/budget questions only when requirements and cost comparisons are ready.

If a decision depends on evidence not yet available, DEFER it instead of guessing.

---

## 9. Current status

- Owner decision review sheet: **CREATED**
- Architecture decisions: **PENDING OWNER REVIEW**
- P0 scope: **PROPOSED**
- Implementation authorization: **NOT GRANTED**
- Repository inspection: **NOT AUTHORIZED**
- Git operations: **NOT AUTHORIZED**
- Production deployment/publishing: **NOT AUTHORIZED**

**Recommended next step:** Review and explicitly decide the first three foundational choices (ADR-001, ADR-002 and ADR-003). The remaining decisions can then be considered against those foundations.

---

## 10. Change log

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-10-31 | Initial P0 owner decision review sheet |
