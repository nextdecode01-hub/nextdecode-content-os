# NEXTDECODE P0 — Exit Gates & Parallel Agent Work Orders

**Document ID:** ND-P0-GATE-001  
**Version:** 0.1  
**Date:** 3 November 2026  
**Status:** Proposed work-order and acceptance framework — owner review required  
**Phase:** P0  
**Part:** Programme-wide, WP-1–WP-6  
**Work package:** P0-CLOSE / gate readiness  
**Layer:** Shared contracts; backend-led implementation readiness with frontend consumer mapping  
**Implementation authorization:** NOT GRANTED  
**Storage:** `P0/08-quality-security-and-testing/exit-gates`

## 1. How to work quickly without losing control

Use parallel work for independent source reviews and domain specifications. Use one canonical editor for shared contract documents. Do not let multiple agents edit the same canonical file concurrently.

### Role boundaries
- **Documentation controller:** owns inventory, version map, source citations, change log and duplicate reconciliation.
- **Contract/API architect:** owns Batch 18 consolidation and shared schemas, coordinating domain owners.
- **WP-1/WP-2 backend architect:** owns canonical persistence and durable execution design.
- **WP-3 worker/security architect:** owns worker identity/trust/capability contract.
- **WP-4 artifact architect:** owns artifact metadata, integrity and transfer contract.
- **WP-5 governance/security architect:** owns quality, rights, approval and authorization semantics.
- **WP-6 QA architect:** owns vertical-slice acceptance oracles, failure/recovery tests and evidence plan.
- **Performance/operations reviewer:** owns Batch 24 workload, measurement, capacity and cost-control review.
- **Frontend architect:** maps UI consumers and user-facing flows to frozen backend contracts; must not define backend state transitions or permissions.
- **Independent reviewer:** checks source traceability, security, compatibility and evidence independently from the author.

Agent names/assignments are not presumed. The project owner controls actual delegation.

## 2. Parallel work orders — documentation closure

### WO-00 — Source inventory and provenance
**Classification:** P0 / programme control / shared / documentation.

Tasks:
1. Enumerate all files for Batch 01–24 and all constituent artifacts.
2. Reconcile against `NEXTDECODE_P0_07_Master_Register_Change_Log_and_Document_Index.md`.
3. Record exact file identity, version, dates, status, owner evidence, hash where available and supersession.
4. Find duplicates and source-of-truth evidence; do not delete duplicates.
5. Verify original ADR/CF/ODR owner decision records, including rejected/deferred/superseded entries.
6. Record Notion connector limitation and alternate evidence sources.

Acceptance:
- Every batch and constituent artifact accounted for or explicitly unresolved.
- No file is declared missing based solely on a failed search.
- Duplicate and provenance conflicts are visible.
- No derived document is promoted to authority by recency alone.

### WO-01 — WP-1 canonical domain and persistence
**Classification:** P0 / WP-1 / backend / data model.

Tasks:
1. Reconcile Data Dictionary, entity ownership, accepted ADRs and WP-1 candidates.
2. Produce canonical entity/relationship/version/ownership matrix.
3. Define identifier strategy, uniqueness, FK behavior, optimistic concurrency and audit fields.
4. Define transaction boundaries and outbox/inbox ownership with WP-2.
5. Separate logical model from physical schema/migration decisions.
6. Define migration, backup, restore and integrity acceptance evidence.

Acceptance:
- Every canonical entity has one owner.
- Cross-domain write paths use owner commands.
- Identity/version semantics are unambiguous.
- Open physical DB choices are explicitly owner-approved or deferred.
- No schema is called final until owner freeze.

### WO-02 — WP-2 durable workflow and job execution
**Classification:** P0 / WP-2 / backend / orchestration.

Tasks:
1. Reconcile Workflow, WorkflowTask, Job, JobAttempt, Lease and event ownership.
2. Define assignment, acknowledgement, heartbeat/renewal, fencing, expiry and reassignment semantics.
3. Define idempotency scope, duplicate delivery and stale submission handling.
4. Define retry classification, cancellation, recovery and unknown outcome behavior.
5. Define outbox/inbox atomicity, ordering, retention and replay.
6. Map workflow state separately from execution, worker and external-operation state.

Acceptance:
- Attempt identity and lease generation prevent stale worker writes.
- Lease expiry does not automatically mean job failure.
- Retries/reassignments create correctly versioned attempts.
- Unknown side effects are reconciled before retry.
- State changes and outbox intent are atomic where specified.

### WO-03 — WP-3 worker registry and trust
**Classification:** P0 / WP-3 / backend + worker runtime / security-sensitive.

Tasks:
1. Define worker identity, enrollment, attestation/trust, eligibility and revocation.
2. Define capability catalogue, versioning and verification.
3. Define credential issuer, scope, expiry, rotation and revocation dependencies.
4. Bind assignment and result to worker, job, attempt, lease/fencing and capability.
5. Define worker isolation and untrusted-result handling.

Acceptance:
- Worker cannot self-assert trusted capabilities.
- Expired/revoked worker cannot acknowledge or execute protected assignments.
- Credential lifecycle and service authentication have explicit owners.
- Worker trust is not conflated with agent identity or user authorization.

### WO-04 — WP-4 artifact lifecycle
**Classification:** P0 / WP-4 / backend + storage adapter.

Tasks:
1. Define artifact identity/version, metadata, provenance, manifests and integrity.
2. Define binary storage abstraction and metadata authority.
3. Define upload/transfer completion, checksum, validation, quarantine and retry behavior.
4. Define references from job results and content versions.
5. Reconcile retention, legal hold, deletion, backup propagation and restore.
6. Ensure local compatibility flags do not become canonical rights grants.

Acceptance:
- Every artifact reference resolves to an immutable, verifiable version.
- Transfer state and external operation outcome are distinct.
- Integrity failures block downstream use.
- Retention/legal-hold rules have owner authority and no invented duration.

### WO-05 — WP-5 governance, quality, rights and authorization
**Classification:** P0 / WP-5 / backend policy / governance.

Tasks:
1. Separate quality outcome, rights assessment, review, approval and authorization.
2. Reconcile rights vocabulary conflict between ADR-009 and CF-20/Batch 17.
3. Define evidence binding to exact artifact/content version and intended use.
4. Define central default-deny authorization for protected actions.
5. Define approval expiry/revocation and authorization re-evaluation.
6. Preserve human approval and disabled automatic public publishing.

Acceptance:
- Approval is not authorization.
- Rights are use-specific and evidence-backed.
- Unknown/missing/revoked/expired rights do not grant permission.
- Protected actions bind exact resource/version/action/destination/policy/time.
- No adapter bypasses central authorization.

### WO-06 — WP-6 vertical slice, integration and recovery
**Classification:** P0 / WP-6 / shared / backend-led verification.

Tasks:
1. Select one narrow synthetic end-to-end vertical slice.
2. Map each step to canonical owner, command, event, state and artifact.
3. Define happy-path, duplicate, stale-version, timeout, worker-loss and recovery scenarios.
4. Define failure injection and evidence capture.
5. Define compatibility and replay tests.
6. Prepare independent review checklist.

Acceptance:
- A complete bounded slice can be reproduced in a documented environment.
- Failure/recovery evidence is current and traceable.
- No external publishing or paid provider is required for acceptance.
- Independent reviewer signs off on the defined scope.

### WO-07 — Batch 18 shared API/Event and Agent–Worker
**Classification:** P0 / Part 5 + WP-2/WP-3/WP-4/WP-5 / shared contract, backend-led.

Tasks:
1. Reconcile query, command, event, callback, worker assignment and result interfaces.
2. Close assignment issuance, acknowledgement/rejection, result acceptance and failure/recovery families.
3. Reconcile lease/fencing and agent Actor linkage.
4. Mark each field SOURCE-DEFINED / PROPOSED / OPEN / DEFERRED / CONFLICTED.
5. Create JSON Schema only for owner-frozen structures; examples remain illustrative.
6. Map frontend consumer needs without creating duplicate domain logic.

Acceptance:
- Each field has owner/source/status.
- Events are committed facts, not permission.
- Command ACCEPTED is not completion.
- Stale and duplicate messages are safe.
- Routes, enums and field constraints are frozen only with evidence.

### WO-08 — Batch 24 performance, scalability, capacity and cost
**Classification:** P0 / cross-cutting operations / shared, backend-led.

Tasks:
1. Define initial single-owner Creator Mode workload profile and media assumptions.
2. Identify latency, queue wait, throughput, render, storage, memory, disk and network measurements.
3. Define measurement method, environment and percentile/reporting rules.
4. Identify owner-reserved numeric decisions (SLOs, quotas, concurrency, limits, retention and capacity).
5. Define scale triggers and safe degradation behavior.
6. Reconcile with local-first/free-first and no-paid-service constraints.

Acceptance:
- Metrics have precise definitions and measurement owners.
- Numeric targets are owner-approved or explicitly deferred with safe interim limits.
- Cost estimates state assumptions and do not imply provider approval.
- No provider, spend or infrastructure activation is performed by this work order.

## 3. Frontend workstream — bounded until contracts freeze

Frontend architect may prepare:
- screen/flow inventory for creator, reviewer, administrator and operator roles;
- read-model and query needs;
- state presentation mapping to backend-owned states;
- error, retry, unknown-outcome and permission-denied UX;
- accessibility and human approval interaction requirements.

Frontend must not:
- create a second source of truth;
- mutate canonical domain state directly;
- treat UI visibility as authorization;
- infer approval or rights from a status label;
- invent backend enums or state transitions.

Deliverable: frontend consumer map linked to exact API/Event contract IDs. Actual UI implementation requires separate authorization.

## 4. Consolidated owner-review pack

The documentation controller assembles one pack containing:
1. Complete source/provenance matrix.
2. Accepted ADR/CF/ODR decision ledger and supersession.
3. Open/conflicted/deferred decision list.
4. WP-1–WP-6 contract closure matrix.
5. Batch 17 state transition matrix.
6. Batch 18 schema and Agent–Worker interface matrix.
7. Batch 24 performance/capacity/cost decision matrix.
8. Security/privacy/rights/approval/authorization review.
9. P0 acceptance oracle and evidence plan.
10. Explicit list of items requiring owner decision.

Do not send separate owner questions for issues already resolved by accepted decisions.

## 5. P0 exit gates

| Gate | Required evidence | Pass condition |
|---|---|---|
| G0 — Source completeness | Batch inventory, hashes/identity, provenance, supersession | No untracked authoritative dependency |
| G1 — Contract freeze | Owner-reviewed WP-1–WP-6 + shared API/Event baseline | All critical interfaces frozen or safely deferred |
| G2 — Implementation authorization | Explicit scoped owner decision | Exact WP, repository scope, agent roles and boundaries approved |
| G3 — P0 implementation | Versioned code/change record and build/test evidence | Authorized bounded slice implemented |
| G4 — Verification | Reproducible tests, security/recovery evidence, independent review | Acceptance oracle passes; no critical blocker |
| G5 — P0 acceptance | Consolidated evidence dossier and owner acceptance | Owner formally accepts P0 scope |
| G6 — P1 authorization | Separate explicit authorization | P1 work may begin within approved scope |

Provider activation, paid services, deployment, external upload and public publishing remain separate protected actions and are not implied by G2–G6.

## 6. Evidence quality requirements

For each test or acceptance claim record:
- test/evidence ID and requirement IDs;
- code/document version and commit or immutable source identity where authorized;
- environment and dependency versions;
- exact command or procedure;
- inputs/fixtures and expected outcome;
- actual result, logs and artifact references;
- reviewer and date;
- limitations, flakiness and untested branches.

Historical green tests are historical evidence, not proof of the current baseline.

## 7. Required agent completion report

Each agent returns:
- exact source files and versions read;
- files created/changed and exact paths;
- requirements/contracts addressed;
- field and decision classifications;
- tests proposed vs actually run;
- evidence references;
- unresolved decisions and correct owner;
- deviations and rationale;
- explicit confirmation that no unauthorized action occurred;
- next dependency and recommendation.

## 8. Global no-go conditions

Do not proceed to implementation or integration if source authority is unresolved, critical ownership is ambiguous, protected-action policy is incomplete, contracts conflict, acceptance oracles are missing, or explicit owner authorization is absent.
