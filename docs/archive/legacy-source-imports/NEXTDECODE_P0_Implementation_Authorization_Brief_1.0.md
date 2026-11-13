# NEXTDECODE Content OS — P0 Implementation Authorization Brief 1.0

**Document status:** Prepared for owner authorization — NOT AUTHORIZED  
**Version:** 1.0  
**Date:** 31 October 2026  
**Purpose:** Define the exact scope, permissions, safeguards and evidence required before P0 foundation implementation may begin.

Related documents:
- `NEXTDECODE_Architecture_Decision_Register_1.0.md`
- `NEXTDECODE_Architecture_Decision_Records_Pack_1.0.md`
- `NEXTDECODE_P0_Foundation_Implementation_Specification_1.0.md`
- `NEXTDECODE_P0_Owner_Decision_Review_Sheet_1.0.md`
- `NEXTDECODE_Canonical_Contracts_Pack_1.0.md`

---

## 1. Executive position

The architecture and P0 implementation scope have been documented. The next operational step is not to start coding immediately. It is to confirm the decisions, inspect the current system only under explicit permission, and then authorize a tightly bounded implementation increment.

This brief defines a proposed authorization boundary. It does not itself grant permission.

**Current authorization state:**
- Architecture decisions: pending explicit owner decisions.
- Repository inspection: not authorized.
- Git operations: not authorized.
- Source-code changes: not authorized.
- Dependency/environment changes: not authorized.
- Cloud account creation or paid service activation: not authorized.
- Deployment, production generation, upload or publishing: not authorized.

---

## 2. Proposed first implementation increment

### Increment name

**P0-A — Durable Content Workflow Foundation**

### Objective

Demonstrate that NEXTDECODE Content OS can create and persist a content workflow, dispatch a durable job, execute it through a registered worker, register an immutable artifact, recover safely from interruption, and enforce a deny-by-default protected-action boundary.

### Included capabilities

1. Minimal canonical domain model and IDs.
2. Persistence/migration foundation.
3. Workflow, task and job state transitions.
4. Durable job dispatch, leases and bounded retry.
5. Worker registration, authentication and capability checks.
6. Versioned control-plane/worker contracts.
7. Artifact metadata, checksum and controlled transfer interface.
8. Audit/correlation records.
9. Minimal quality/rights policy result interfaces.
10. Central authorization boundary with protected actions disabled by default.
11. Deterministic vertical-slice integration tests.
12. Recovery and security-negative tests.

### Explicitly excluded

- Full Content OS dashboard or polished user interface.
- Full research, strategy or brand-intelligence modules.
- Full multiformat creation.
- Broad agent autonomy or agent swarm.
- Automatic public publishing.
- Live platform uploads.
- Production cloud deployment.
- Replacing Shorts Studio.
- Rewriting existing rendering logic.
- Multi-user teams, tenancy, billing or SaaS.
- Advanced analytics, recommendation or vector search.

---

## 3. Mandatory prerequisites

No implementation should begin until all required prerequisites are satisfied.

| ID | Prerequisite | Evidence required | Current status |
|---|---|---|---|
| PRE-01 | Owner decisions recorded for foundational ADRs | Updated decision log | PENDING |
| PRE-02 | P0 scope accepted | Owner approval | PENDING |
| PRE-03 | Current repository state inspected under permission | Inspection report; no Git operations unless separately permitted | NOT AUTHORIZED |
| PRE-04 | Existing WIP and protected files identified | Preservation map | PENDING |
| PRE-05 | Current tests and baseline behavior understood | Approved test baseline report | PENDING |
| PRE-06 | File-level ownership agreed | Ownership map for Qoder/OpenCode | PENDING |
| PRE-07 | Kilo QA boundary confirmed | Read-only QA plan | PENDING |
| PRE-08 | Environment/dependency policy confirmed | Explicit permissions | PENDING |
| PRE-09 | No production side effects in test plan | Test isolation plan | PENDING |
| PRE-10 | Rollback/recovery approach defined | Preservation-safe recovery plan | PENDING |

A prerequisite may be deferred only if the owner explicitly accepts the resulting risk and the affected workstream does not depend on it.

---

## 4. Proposed work packages

The packages below are a sequencing proposal. They do not assign new agent ownership or authorize work.

### WP-0 — Baseline and preservation assessment

**Purpose:** Understand the current implementation without disturbing it.

Activities, only after repository inspection is authorized:
- Inspect relevant source, tests, configuration and project documentation.
- Identify existing uncommitted/WIP areas without using Git unless separately authorized.
- Map existing pipeline entry points and direct publishing paths.
- Map existing database, queue, API, worker and artifact prototypes.
- Record verified behavior separately from assumptions.
- Establish approved test commands and baseline results.

Deliverable: `P0_Current_System_Baseline_Report`.

Exit criteria:
- No files modified.
- Existing WIP and protected areas documented.
- Unknowns and conflicts listed.
- Test baseline reproducible.

### WP-1 — Domain and persistence foundation

Activities:
- Implement approved canonical entity schema.
- Add versioned migrations.
- Add repository/service boundaries.
- Add explicit entity relationships and constraints.
- Implement validated state transition functions.
- Preserve compatibility adapters where needed; do not rewrite Shorts Studio.

Deliverable: domain/persistence implementation with schema and tests.

Exit criteria:
- Entity/relationship tests pass.
- Invalid transitions are rejected.
- Migrations are repeatable in the approved test environment.
- No duplicate source of truth is introduced.

### WP-2 — Durable execution foundation

Activities:
- Implement durable job records and dispatch.
- Add lease claim, heartbeat, expiry and recovery.
- Add bounded retry and structured failure categories.
- Add transactional outbox/inbox or approved equivalent.
- Add idempotency enforcement.

Deliverable: durable job execution layer.

Exit criteria:
- Restart and worker-interruption tests pass.
- Duplicate event tests pass.
- Stale lease holder cannot overwrite current result.
- Retry behavior is bounded and auditable.

### WP-3 — Worker and contract boundary

Activities:
- Implement worker registry.
- Implement unique worker identity and approved credential lifecycle.
- Enforce capability-aware claims.
- Implement versioned API/event validation.
- Add worker heartbeat and revocation.

Deliverable: authenticated worker boundary.

Exit criteria:
- Unauthorized, revoked and unsupported workers are denied.
- Contract validation rejects malformed messages.
- Correlation IDs survive the complete path.
- Secrets are redacted.

### WP-4 — Artifact boundary

Activities:
- Implement artifact metadata and immutable versions.
- Implement storage abstraction using the provider approved by the owner.
- Add scoped transfer authorization.
- Add checksum verification and safe retry.

Deliverable: artifact registration and transfer boundary.

Exit criteria:
- Checksum mismatch blocks downstream use.
- Unauthorized cross-job access is denied.
- New versions do not mutate old versions.
- Interrupted transfers recover safely.

### WP-5 — Governance foundation

Activities:
- Implement policy evaluation interface.
- Implement review/approval/authorization separation.
- Implement central protected-action check.
- Implement emergency pause.
- Ensure all publishing paths are deny-by-default until explicitly authorized.

Deliverable: centralized governance enforcement.

Exit criteria:
- Missing, expired, revoked or mismatched authorization is denied.
- Hard-block quality/rights states cannot be bypassed by ordinary approval.
- Every decision is auditable.
- No live publishing is performed during WP-5 tests.

### WP-6 — Vertical-slice validation

Activities:
- Run one deterministic test workflow end to end.
- Inject worker, process, event and transfer failures.
- Verify recovery and audit trail.
- Produce test evidence and known-limitations report.

Deliverable: `P0_Acceptance_Evidence_Report`.

Exit criteria:
- Approved P0 acceptance matrix passes.
- Failure scenarios have evidence.
- No production side effects occurred.
- Independent read-only QA is completed by Kilo under its existing ownership.

---

## 5. Agent and ownership protocol

Existing ownership is preserved:

| Agent | Existing ownership | Permitted role in this proposed increment |
|---|---|---|
| Qoder | Phase 11 engineering owner | Engineering work only within an explicitly assigned, non-overlapping scope |
| OpenCode | Phase 10 engineering/closure owner | Engineering work only within an explicitly assigned, non-overlapping scope |
| Kilo | Independent read-only QA | Inspect/review/test evidence only; no source, test, config or Git modifications |

No agent receives a new task from this document.

Before execution:
- Name exact files/directories owned by each engineering agent.
- Identify shared interfaces and designate one owner for each.
- Do not allow concurrent edits to the same files.
- Kilo receives a frozen review target or explicitly defined read-only window.
- Any scope change requires owner approval.
- Each agent reports exact files changed, commands run, test outcomes, limitations and risks.

---

## 6. Permission matrix

This is the most important control in the brief. Each permission must be explicitly granted; one permission does not imply another.

| Action | Current permission | Separate owner authorization required? |
|---|---|---|
| Read architecture documents already provided | Allowed | No |
| Discuss implementation plan | Allowed | No |
| Inspect repository files | Not authorized | Yes |
| Run tests or commands against repository | Not authorized | Yes |
| Read Git status/log/diff | Not authorized | Yes |
| Any Git write operation | Not authorized | Yes |
| Modify source code | Not authorized | Yes |
| Modify tests/configuration | Not authorized | Yes |
| Install/update dependencies | Not authorized | Yes |
| Change Python/Node/system environment | Not authorized | Yes |
| Create cloud account/resources | Not authorized | Yes |
| Activate paid services | Not authorized | Yes |
| Deploy services | Not authorized | Yes |
| Generate production content | Not authorized | Yes |
| Upload to a platform | Not authorized | Yes |
| Publish publicly | Not authorized | Yes |

---

## 7. Preservation and change-control requirements

If implementation is later authorized:

1. No reset, clean, revert, force operation or destructive cleanup.
2. No broad staging such as `git add .`.
3. No overwriting unrelated or unowned files.
4. No changing agent ownership.
5. No dependency/environment change without separate permission.
6. No refactor outside the approved work package.
7. Preserve existing outputs and evidence unless a specific retention/migration plan is approved.
8. Make changes small and reviewable.
9. Record exact file-level changes.
10. Stop and ask if unexpected WIP, conflicting edits, secrets, destructive migrations or unclear ownership are discovered.

---

## 8. Test and evidence requirements

Each work package must provide:

- Scope and exact files changed.
- Test command(s) executed.
- Test count and pass/fail/skip summary.
- Relevant logs or sanitized output.
- Failure-injection results.
- Security-negative test results.
- Known gaps and unverified behavior.
- Confirmation that no unauthorized side effects occurred.

P0 acceptance requires:
- unit tests;
- integration tests;
- persistence/restart tests;
- worker lease/recovery tests;
- event deduplication tests;
- artifact integrity/access tests;
- governance negative tests;
- independent read-only QA.

A passing test suite does not establish production readiness.

---

## 9. Stop conditions

Stop implementation and report to the owner if any of the following occurs:

- An unapproved Git operation appears necessary.
- A destructive migration or data rewrite appears necessary.
- Existing WIP ownership is unclear or conflicting.
- A dependency or environment change is required but not authorized.
- A secret or credential is exposed.
- A direct publishing path cannot be safely contained.
- A hard rights/safety/integrity gate is ambiguous.
- A provider cost or cloud resource would exceed the approved envelope.
- A test risks real external side effects.
- The approved scope cannot be met without broad refactoring.

Do not improvise around a stop condition.

---

## 10. Authorization form

**This form is intentionally blank.** It must be completed explicitly by the owner before implementation begins.

### A. Decision baseline

- Approved ADR pack version: ____________________
- Approved ADR IDs: ____________________
- Deferred ADRs and accepted risks: ____________________
- Approved P0 specification version: ____________________

### B. Scope

- Authorized work packages: ____________________
- Explicitly excluded work: ____________________
- Authorized repository/project location: ____________________
- Authorized environment: ____________________

### C. Permissions

Mark each separately:

- [ ] Repository file inspection
- [ ] Running approved read-only inspection commands
- [ ] Running approved tests
- [ ] Source-code modification
- [ ] Test modification
- [ ] Configuration modification
- [ ] Git read operations
- [ ] Git write operations (specify exact operations): ____________________
- [ ] Dependency installation/update
- [ ] Environment changes
- [ ] Cloud resource creation
- [ ] Deployment
- [ ] Production generation
- [ ] Platform upload
- [ ] Public publishing

Unchecked permissions remain unauthorized.

### D. Ownership and safeguards

- Qoder scope/files: ____________________
- OpenCode scope/files: ____________________
- Kilo read-only QA scope: ____________________
- Protected files/WIP: ____________________
- Approved test commands: ____________________
- Stop/escalation contact or procedure: ____________________

### E. Owner authorization

- Decision: NOT AUTHORIZED / AUTHORIZED WITH SCOPE
- Conditions: ____________________
- Owner confirmation: ____________________
- Date: ____________________

---

## 11. Recommended next action

Do not execute this brief yet.

First, complete the P0 Owner Decision Review Sheet. The foundational decisions (ADR-001, ADR-002 and ADR-003) should be resolved before implementation details are finalized. Then authorize a read-only current-system baseline assessment as a separate, narrow permission. Only after that assessment should file ownership and code-change scope be assigned.

---

## 12. Current status

- Implementation increment defined: **PROPOSED**
- Work packages defined: **PROPOSED**
- Ownership protocol: **PRESERVED**
- Permission matrix: **DEFINED**
- Owner authorization: **NOT GRANTED**
- Repository inspection: **NOT AUTHORIZED**
- Git operations: **NOT AUTHORIZED**
- Code changes: **NOT AUTHORIZED**
- Deployment / production actions: **NOT AUTHORIZED**

## 13. Change log

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-10-31 | Initial P0 implementation authorization brief |
