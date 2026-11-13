# NEXTDECODE P0 — Fast Closure Master Plan

**Document ID:** ND-P0-CLOSE-001  
**Version:** 0.1  
**Date:** 3 November 2026  
**Status:** Proposed execution plan — owner review required  
**Phase:** P0 — Architecture, Contracts & Governance Closure  
**Part:** Cross-part / P0 programme control  
**Work package:** P0-CLOSE — Consolidated closure and acceptance  
**Layer:** Shared governance + backend-led contract work  
**Consumers:** Project owner, documentation agent, backend architect, frontend architect, QA/security reviewers  
**Authority:** Existing accepted decisions and source documents only  
**Implementation authorization:** NOT GRANTED  
**Storage:** `P0/00-governance-and-owner-decisions/closure`

## 1. Mission

Close P0 efficiently by consolidating evidence and completing only genuine gaps. Do not restart architecture, repeat accepted decisions, or create parallel specifications. Batch work across multiple related documents, but preserve separate approval and acceptance gates.

**P0 exit outcome:** a source-complete, internally consistent, owner-frozen architecture/contract baseline; a scoped engineering handoff; evidence-backed acceptance criteria; and an explicit, separate owner authorization decision for P1 implementation.

## 2. Current known position

### Verified from accessible project files
- Batch 02 consolidated implementation package exists. It defines separate decision, design, implementation and evidence statuses and records G0 in progress, G1 not ready, G2 WP-1 authorization not granted, G3 integration not authorized, G4 external operations not authorized, and G5 P0 acceptance pending.
- Batch 03 final contract consolidation/owner review package exists and explicitly describes itself as a candidate, not frozen and not implementation-authorized.
- A P0 document index exists and lists WP-1 through WP-6 designs, reconciliation packages and a seven-document implementation package.
- Batch 12 source verification/reconciliation contract exists.
- Batch 17 state-machine catalogue exists and is a detailed candidate, owner freeze pending.
- Batch 18 API/Event schema specification exists and is a detailed candidate, owner freeze pending.
- Batch 24 performance/scalability/capacity/cost-control specification exists and is a draft for owner review, not a contract freeze.
- Agent–Worker handoff ND-P0-AGW-001 exists; follow-on handoff ND-P0-B12-AGW-002 was created on 3 November 2026.

### Not yet established
- A complete, deduplicated inventory of every Batch 01–24 artifact and its current version/status.
- Full provenance/hash and supersession checks for all source and duplicate files.
- A single authoritative, source-complete master decision register with verified owner evidence.
- Formal closure of all detailed contracts and all owner-reserved decisions.
- Runtime implementation and independent verification for the P0 foundation.
- Formal P0 acceptance.

**No overall P0 completion percentage is asserted by this plan.** A percentage may be calculated only after the master register is complete and its weighted acceptance criteria are agreed.

## 3. Execution strategy: parallel documentation, serial gates

Run documentation work in parallel where ownership is independent. Do not parallelize decisions that require a single canonical owner or shared contract freeze.

### Wave A — Evidence and inventory (parallel)
| Track | Work | Owner role | Output |
|---|---|---|---|
| A1 | Inventory all Batch 01–24 files, versions, duplicates and locations | Documentation controller | Master file inventory |
| A2 | Reconcile ADR/CF/ODR owner decisions and source precedence | Governance/documentation agent | Decision provenance matrix |
| A3 | Reconcile Batch 12/17/18 and Agent–Worker source dependencies | API/contract agent | Contract traceability and conflict register |
| A4 | Reconcile Batch 24 performance/capacity/cost requirements with accepted constraints | Architecture/operations agent | Performance decision and evidence matrix |

**Wave A exit:** Every relied-upon source has a unique identity, version, status, authority level and known limitation. Conflicts are visible; none are silently resolved.

### Wave B — Contract closure (parallel by domain, shared interface review)
| Track | Work package | Output |
|---|---|---|
| B1 | WP-1 canonical domain and persistence | Owner-review schema and entity-ownership baseline |
| B2 | WP-2 workflow/job/attempt/lease | Durable execution contract and transition rules |
| B3 | WP-3 worker identity/trust/capability | Worker registration and assignment trust contract |
| B4 | WP-4 artifacts/manifests/transfer/integrity | Artifact lifecycle and storage contract |
| B5 | WP-5 quality/rights/approval/authorization | Governance and protected-action contract |
| B6 | WP-6 vertical slice/integration/recovery | Cross-domain acceptance and recovery contract |
| B7 | Shared API/Event + Part 5 Agent–Worker | Versioned schemas, commands/events and ownership matrix |
| B8 | Performance/capacity/cost | P0 workload profile, measurement plan and owner decisions |

**Wave B exit:** All field-level and state-level details are classified as accepted/source-defined, proposed, open, deferred or conflicted. No unresolved field is disguised as frozen.

### Wave C — Owner freeze (serial)
1. Present one consolidated owner-review pack, not repeated scattered questions.
2. Include only genuine owner-reserved decisions and source conflicts.
3. Record each disposition with exact wording, date, owner, source and supersession.
4. Freeze only contracts with complete source traceability and accepted owner disposition.
5. Keep deferred decisions explicitly deferred with safe interim behavior.

**Wave C exit:** Required contract baseline is explicitly frozen; deferred items have safe bounded behavior and do not block the P0 vertical slice.

### Wave D — Engineering readiness and authorization (serial)
1. Produce work orders with exact repository scope, files/modules, dependencies, tests, rollback/preservation constraints and acceptance oracles.
2. Map backend work and frontend consumers separately.
3. Review security, privacy, rights, approval and publishing boundaries.
4. Present a separate P1 implementation authorization request.
5. Do not begin implementation until that authorization is explicit and scoped.

### Wave E — P0 implementation/verification/acceptance
P0 is not complete merely when documents are frozen. Execute only the owner-authorized P0 foundation scope. Verify the bounded vertical slice with reproducible evidence, independent review and recovery/security tests. Then issue a formal P0 acceptance record or a gap-based rejection.

## 4. Work package exit criteria

### WP-1 — Canonical domain and persistence
- Canonical entities, IDs, versions, ownership and invariants trace to accepted sources.
- Entity relationships, uniqueness, referential integrity, lifecycle and transaction boundaries are specified.
- Logical data dictionary is not mistaken for a final migration until explicitly frozen.
- Migration, backup, restore and data-integrity acceptance evidence is defined.

### WP-2 — Durable workflow and job execution
- Workflow, task, job, attempt, lease and outbox/inbox responsibilities are unambiguous.
- State transitions, idempotency, fencing, retry/recovery and unknown outcomes are specified.
- Lease expiry is not treated as proof of job failure.
- Duplicate/stale submissions cannot overwrite canonical state.

### WP-3 — Worker registry and trust
- Worker identity, enrollment, trust, capabilities, credentials and revocation are owned and bounded.
- Assignment is bound to eligible worker, job/attempt, lease and expiry.
- Untrusted workers cannot self-grant capabilities or protected permissions.

### WP-4 — Artifact management
- Artifact identity/version, provenance, manifest, integrity, storage abstraction, transfer and validation are specified.
- Metadata and binary storage responsibilities are separate.
- Artifact rights and retention are not inferred from a local compatibility flag.
- Unknown/failed transfer outcomes are reconciled safely.

### WP-5 — Governance and authorization
- Quality, rights, review, approval and authorization remain separate.
- Protected actions are default-deny and bound to exact resource/version/action/destination/policy/time.
- Approval is not authorization.
- Public publishing remains disabled unless separately authorized.

### WP-6 — Vertical slice, integration and recovery
- One bounded synthetic vertical slice is selected and fully traceable.
- Failure injection, duplicate delivery, stale state, lease loss, worker failure, artifact corruption and recovery are tested.
- End-to-end evidence is reproducible and environment-labelled.
- Independent review and explicit acceptance are recorded.

### Cross-cutting Batch 24
- Workload and media profiles are defined.
- Latency, queue wait, throughput, resource, storage and cost metrics have owners and measurement methods.
- Numeric SLOs/quotas are not invented; owner decisions are recorded.
- Capacity and cost tests fit the local-first/free-first constraints and no paid provider is activated without separate approval.

## 5. Status model — never collapse dimensions

Every requirement/decision must carry four independent statuses:

1. **Decision:** OWNER_ACCEPTED / PROPOSED / OPEN / DEFERRED / CONFLICTED.
2. **Design:** DRAFT / RECONCILED / CANDIDATE / FROZEN.
3. **Implementation:** NOT_IMPLEMENTED / IN_PROGRESS / IMPLEMENTED / PARTIALLY_IMPLEMENTED / RETIRED.
4. **Evidence:** NOT_RUN / NOT_VERIFIED / VERIFIED / FAILED / INCONCLUSIVE / NOT_APPLICABLE.

QA outcomes remain PASS / PASS_WITH_WARNINGS / NEEDS_REVIEW / BLOCKED. Unknown external outcome remains a separate epistemic/operation state.

## 6. Fast execution cadence

Use work waves rather than a calendar promise:
- One source inventory pass.
- One consolidated reconciliation pass.
- One consolidated owner-review pass.
- One engineering readiness/authorization pass.
- One bounded implementation and evidence pass.

Create multiple related documents per wave, but do not create documents that merely restate existing source material. If an artifact already exists, update it through its own version/change-control process only when authorized; otherwise produce a clearly labelled change proposal.

## 7. Stop conditions

Pause the affected work if:
- an accepted owner decision conflicts with a derived document;
- canonical ownership is unclear;
- a protected-action policy or rights state is unresolved;
- a schema change would break another domain's contract;
- required source or provenance cannot be verified;
- a task requires repository access, Git, credentials, provider activation, paid services, deployment or external side effects not separately authorized.

## 8. P0 exit gate

P0 can be declared complete only when all applicable conditions pass:
- [ ] Complete source inventory and provenance register.
- [ ] Accepted ADR/CF/ODR decisions reconciled and source precedence documented.
- [ ] WP-1–WP-6 and shared API/Agent–Worker contracts owner-frozen or explicitly deferred with safe bounded posture.
- [ ] Batch 24 performance/capacity/cost controls have approved measurable targets or documented safe deferrals.
- [ ] Backend and frontend implementation boundaries and dependencies are documented.
- [ ] P1 work orders are actionable, scoped and traceable.
- [ ] P0 authorized implementation scope is complete.
- [ ] Required tests and independent reviews have reproducible evidence.
- [ ] Security, rights, approval, authorization, recovery and publishing safety gates pass.
- [ ] Formal owner P0 acceptance recorded.
- [ ] Separate P1 authorization recorded.

**P0 completion is a gate decision, not a document count.**
