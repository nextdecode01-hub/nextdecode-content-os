# NEXTDECODE --- Project Handover

**Version:** 1.0 \| **As of:** 1 November 2026\
**Purpose:** Resume work in a future chat without repeating discovery or
decisions.

## 1. Project identity

**Brand:** NEXTDECODE\
**Tagline:** "Decode what comes next."\
**Positioning:** AI • Tech • Startups • Future\
**Product:** NEXTDECODE Content OS --- one shared intelligence system
with specialised studios and distribution channels.

## 2. Current status

-   Master Blueprint 2.0 and System Architecture Parts 1--8 exist as
    prior references.
-   Shared Intelligence Core Contracts 01--12 and Canonical Contracts
    Pack 1.0 exist.
-   ADR-001--010 and CF-01--24 are accepted as recorded.
-   Formal detailed contract freeze is pending final consolidated owner
    approval.
-   Artifact 06: Implementation Readiness & Risk Register; conditionally
    ready for final design review, not implementation approval.
-   Artifact 07: P0 Foundation Execution Plan & Acceptance Framework.
-   Artifact 08: consolidated owner decisions, contract freeze and
    implementation authorization materials.
-   WP-0: conditionally complete as a read-only baseline/preservation
    assessment.
-   WP-1--WP-6 remain planned foundation work packages.
-   Implementation authorization has not been granted.

## 3. Architecture

Twelve modules: 1. Workspace & Control Center 2. Content Graph 3.
Knowledge Management 4. Research Intelligence 5. Brand Intelligence 6.
Strategy & Planning 7. Content Quality Intelligence 8. Multiformat
Creation Engine 9. Asset Management 10. Automation & Agent Orchestration
11. Distribution Studio 12. Analytics & Learning

Lifecycle:
`Discover → Research → Verify → Strategize → Brief → Create → Review → Produce → Approve → Distribute → Analyze → Improve`

Shorts Studio pipeline:
`Topic / Brief → Research and Evidence → Claim Ledger → Script → Storyboard and Shot Planning → Visual Assets → Rendering → QA → Review Package → Approval → Publishing → Analytics and Learning`

The existing Shorts Studio remains a bounded Python/FFmpeg specialist
engine. Do not replace it wholesale.

## 4. Foundation work packages

  WP     Scope
  ------ -----------------------------------------------------
  WP-0   Current system baseline and preservation assessment
  WP-1   Canonical domain and persistence foundation
  WP-2   Durable job and workflow execution
  WP-3   Worker registry and contract boundary
  WP-4   Artifact registration and transfer
  WP-5   Governance, quality and rights foundation
  WP-6   Vertical-slice integration and recovery validation

P0-A vertical slice target: create a test content item and variant;
create workflow/task; dispatch durable job; claim with authenticated
worker; produce deterministic test output; register immutable artifact;
record transitions; inject failures and demonstrate recovery/audit
reconstruction. This is an acceptance target, not execution
authorization.

## 5. WP-0 result

**Recommended disposition: conditionally complete as assessment only.**

Evidence basis: user-provided local snapshot, prior remote source
inspection and historical Phase 10/11 handovers.

Not verified: current local runtime, fresh test suite, independent QA
acceptance, publishing safety or production readiness.

Do not repeat Git inventory solely to reconfirm the supplied snapshot.

## 6. Repository preservation state

Path: `/home/demon/shorts_studio`

Latest user-provided snapshot: - Branch `main`, reported tracking
`origin/main`. - Remote `main` SHA
`9d38f81ba4f8022d0e820b6a5e1fe2a0fc288c8c`. - 23 modified tracked
files. - 56 untracked paths reported. - No staged changes reported.

Preserve all local modifications and untracked WIP: Phase 10/11 docs,
tests, research/claim/lineage modules, storyboard/shotplan/render
modules, Run Tracker, scripts, fixtures and generated evidence.

No reset, revert, stash, delete, clean, overwrite, broad staging,
commit, push or rename without explicit approval. Do not ask for
repeated status snapshots.

## 7. Phase 10/11 ownership and status

**Phase 10 --- OpenCode** - Historical handover reported 535 passing
tests and focused checks. - Run Tracker, promotion journal and review
provenance integration were reported. - Live production run, runtime
recovery/storm behavior, some post-promotion failure edges and
independent Kilo QA remained open/unverified.

**Phase 11 --- Qoder** - Historical handovers reported ShotPlan
traceability implementation and focused tests. - G1 storyboard approval
gate remained a critical blocker. - Other reported gaps: rights
enforcement, unsupported claims, direct publisher/pipeline bypasses,
incomplete traceability and no approved non-public upload destination. -
Stage A/B was design proposal awaiting approval before Stage C, not
implementation authorization.

**Kilo** is independent read-only QA owner; independent acceptance
evidence remains pending/unavailable in supplied status. Historical test
counts are not fresh test results.

## 8. Known blockers

  ID   Summary
  ---- ---------------------------------------------------
  G1   Storyboard approval gate permissive by default
  G2   Rights not enforced end-to-end at publishing
  G3   Unsupported claims warning-only
  U1   Direct publishing adapters can bypass parent gate
  D1   Direct pipeline can bypass governed orchestration
  T1   Shot/beat/render traceability incomplete
  R1   Run Tracker runtime/recovery evidence missing

These are inherited report findings, not freshly retested results.

## 9. Ownership and operating rules

-   User: product owner/final authority.
-   Assistant: architecture coordinator, research/reconciliation and
    acceptance reviewer.
-   Qoder: Phase 11 engineering owner.
-   OpenCode: Phase 10 engineering/closure owner.
-   Kilo: independent read-only QA.

Ask only genuinely critical owner decisions. Routine decisions follow
standing delegation and conservative defaults.

## 10. Authorization boundaries

No implementation authorization is currently granted. Do not perform
code/repository changes, Git operations, tests, dependency installation,
environment/credential changes, provider activation, cloud deployment,
paid services, production generation, upload or publishing without
separate explicit authorization.

Automatic public publishing remains disabled pending separate policy.

## 11. Exact next step

**Artifact 08 --- Detailed Contract Freeze**, design/documentation
only: 1. Canonical entities and relationships. 2. Lifecycle/state
machines. 3. API and event contracts. 4. Worker identity, trust,
capabilities and leases. 5. Artifact registration, versioning and
transfer. 6. Centralized authorization, QA, rights, approval and
distribution enforcement. 7. Idempotency, retries, failure and recovery.
8. WP-1--WP-6 acceptance criteria.

After owner approval, implementation still requires separate explicit
authorization.

## 12. Continuity rule

**Decide → Document → Preserve → Continue**

Check existing documents before researching or recreating. Record
decisions, contracts, architecture, acceptance criteria and handovers in
versioned Markdown. Preserve originals. Distinguish accepted decisions,
proposals, historical evidence and unverified claims. Never claim a file
was saved unless it exists and its location is verified.
