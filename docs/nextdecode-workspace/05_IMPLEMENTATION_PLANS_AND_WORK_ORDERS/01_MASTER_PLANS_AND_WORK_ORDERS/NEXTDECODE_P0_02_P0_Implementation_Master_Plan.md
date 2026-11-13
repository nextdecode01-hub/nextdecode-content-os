# NEXTDECODE P0 — Implementation Master Plan

**Version:** 0.1  
**Status:** Planning candidate — owner review required  
**Purpose:** Convert WP-0 through WP-6 design work into a controlled engineering programme.

## 1. Executive direction

Implement the NEXTDECODE Content OS incrementally around the existing `shorts_studio` project. Preserve the current Python/FFmpeg specialist engine. Establish shared persistence, durable workflow execution, trusted workers, artifact provenance and centralized governance before expanding to more studios or distribution channels.

This plan is not an implementation authorization, formal contract freeze, deployment approval or spending approval.

## 2. Product and architecture boundaries

- Initial operating mode: single-owner Creator Mode, one NEXTDECODE brand.
- Initial spend target: ₹0; free-first.
- Existing Shorts Studio remains a bounded specialist engine integrated through an adapter.
- Long-term direction: cloud control plane for shared workflow/control state; local or remote workers for bounded execution.
- Provider, cloud, hosting and paid infrastructure choices remain deferred.
- Human approval remains required before critical publishing actions.
- Automatic public publishing remains disabled pending separate policy approval.
- Unknown/missing/ambiguous rights, approval or authorization fail closed for protected actions.
- Approval, authorization, execution and successful distribution are distinct facts.

## 3. Delivery phases and exit gates

| Phase | Work package | Primary outcome | Exit evidence |
|---|---|---|---|
| 0 | WP-0 | Baseline and preservation assessment | Inventory/provenance report; known limitations |
| 1 | WP-1 | Canonical domain and persistence | Migrations, constraints, repository tests, data ownership evidence |
| 2 | WP-2 | Durable workflow/job execution | Restart recovery, leases, retries, idempotency, outbox/inbox tests |
| 3 | WP-3 | Worker registry and trust boundary | Enrollment, identity, capability and authorization-negative tests |
| 4 | WP-4 | Artifact registration and transfer | Immutable version, manifest, checksum, quarantine and recovery tests |
| 5 | WP-5 | Governance, quality, rights and authorization | Central gate tests and bypass-negative tests |
| 6 | WP-6 | Integrated vertical slice | Deterministic end-to-end run, failure injection, audit reconstruction, independent QA |

WP-0 is conditionally complete as an assessment only. WP-1 through WP-6 are design/implementation packages, not completed engineering.

## 4. Recommended engineering order

1. Consolidate and owner-review the detailed contract baseline.
2. Authorize a narrowly scoped WP-1 implementation brief.
3. Implement and validate WP-1 before relying on its schema in WP-2.
4. Build WP-2 against the approved WP-1 contracts.
5. Build WP-3 worker boundary against WP-2 job/lease contracts.
6. Build WP-4 artifact boundary and connect it to execution outputs.
7. Build WP-5 centralized governance gates before any protected external action.
8. Complete WP-6 synthetic vertical slice and independent QA.
9. Only after P0 acceptance, plan wider studio integrations and user-facing control surfaces.

Parallel work is appropriate only for non-conflicting design/review tasks or isolated implementation packages with explicit file ownership and stable contracts. Do not parallelize schema/contract changes across agents without a designated owner and integration plan.

## 5. Engineering work package template

Every authorized work order must state:
- Work package ID and exact scope.
- Approved contract baseline and source versions.
- Allowed repository paths and prohibited paths.
- Existing modifications/untracked files that must be preserved.
- Inputs, outputs and API/event contracts.
- Migration and rollback/forward-recovery strategy.
- Security and governance invariants.
- Required tests and test data.
- Evidence to return: changed paths, diff summary, commands, test results, logs, limitations.
- Acceptance owner and independent QA boundary.
- Explicitly prohibited actions (commit/push/deploy/spend/external publish unless separately approved).

## 6. Repository and change safety

Project: `/home/demon/shorts_studio`.

Latest user-provided snapshot: local `main`, 23 tracked modified files, 56 untracked paths, no staged changes; remote SHA reported as `9d38f81ba4f8022d0e820b6a5e1fe2a0fc288c8c`. This is a historical snapshot, not a current inspection.

Mandatory preservation:
- Do not reset, revert, stash, clean, delete, overwrite, rename or broadly stage existing work.
- Do not commit, push, change branches/remotes or run destructive migrations without separate explicit authorization.
- New work must use isolated, clearly named files/paths and additive changes where possible.
- Before an authorized implementation starts, the engineer must inspect only the specific paths needed and record any overlap with existing user changes. Do not repeat broad inventory unless needed to resolve a concrete conflict.
- Prefer a separate worktree or isolated branch only after the owner explicitly approves the mechanism and confirms preservation.

## 7. Architecture-level acceptance invariants

1. One canonical owner per entity.
2. Immutable canonical identity and explicit versioning.
3. Unknown/missing/ambiguous rights, approval or authorization never grant permission.
4. Approval ≠ authorization ≠ execution ≠ successful publication.
5. Hard QA, rights and policy blockers are centrally enforced.
6. Workers execute bounded assignments.
7. At-least-once queue semantics with idempotency and traceable attempts.
8. Artifacts are versioned and integrity checked; repair creates a new version.
9. Review/approval is attributable and bound to exact version.
10. Automatic public publishing remains disabled.
11. Existing Shorts Studio remains a bounded specialist engine.
12. Local-only work waits safely if its local worker is unavailable.
13. Cloud control plane is a direction, not a selected provider/deployment.
14. Local-first/free-first.
15. No paid services without explicit approval.

## 8. Definition of done for P0

P0 is not done merely because code exists or unit tests pass. Evidence must show:
- Approved contract baseline and traceability.
- Deterministic synthetic content/variant creation.
- Workflow and dependent task creation.
- Durable job dispatch and authenticated worker claim.
- Deterministic output production.
- Immutable artifact registration and integrity verification.
- Correct state transitions and audit reconstruction.
- Restart/retry/lease-loss/failure recovery.
- Security-negative tests for unauthorized and out-of-scope operations.
- Central governance enforcement with bypass tests.
- Independent read-only QA report with findings and evidence.
- No unauthorized external side effects.

## 9. Decision and authorization gates

| Gate | Required authority | What it permits |
|---|---|---|
| G0: Design reconciliation complete | Architecture review | Submit candidate contracts for owner review |
| G1: Detailed contract freeze | Explicit owner approval | Treat identified baseline as frozen |
| G2: Engineering authorization | Explicit owner approval | Implement only the named package/scope |
| G3: Integration authorization | Explicit owner approval | Integrate named components within boundaries |
| G4: External operations authorization | Separate explicit owner approval | Specific provider, spend, deployment or publishing action |
| G5: Acceptance | Owner + independent QA evidence | Declare only the evidenced scope accepted |

## 10. Risks and controls

- Contract ambiguity → keep unresolved items explicit; no silent defaults.
- Existing user changes → preserve and isolate.
- Agent scope creep → narrow work orders and file ownership.
- Hidden adapter bypasses → centralized policy checks and negative tests.
- At-least-once duplicates → idempotency and inbox deduplication.
- Ambiguous external outcome → reconciliation; never blindly retry a non-idempotent side effect.
- Local worker unavailable → safe waiting state.
- Premature cloud choice → provider-neutral interfaces and deferred selection.
- False completion claims → evidence-bound status register.

## 11. Current status

- WP-0: conditionally complete as baseline/preservation assessment only.
- WP-1–WP-6: design packages exist; detailed contract freeze and implementation authorization remain pending.
- X-01–X-12: reconciliations produced; X-12 candidate is in this package.
- No repository changes, tests, agent runs, deployment, provider activation or spending are performed by this plan.
