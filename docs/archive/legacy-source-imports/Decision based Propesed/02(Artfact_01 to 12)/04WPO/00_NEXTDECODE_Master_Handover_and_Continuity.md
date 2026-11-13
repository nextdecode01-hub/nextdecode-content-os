# NEXTDECODE --- Master Handover & Continuity

**Version:** 1.0 \| **Date:** 1 November 2026\
**Purpose:** Single-entry reference for continuing NEXTDECODE across
chats.

## Current position

NEXTDECODE Content OS is a shared intelligence system with specialised
studios and distribution channels. Shorts Studio remains the bounded
Python/FFmpeg production engine.

Architecture direction and major contract decisions have been accepted,
but formal detailed contract freeze is pending. **Implementation
authorization has not been granted.**

## Existing project references

The user reports having four original Markdown files. Preserve those
originals; this pack is continuation documentation, not a replacement.

Prior references include Master Blueprint 2.0; System Architecture Parts
1--8; Shared Intelligence Core Contracts 01--12; Canonical Contracts
Pack 1.0; ADR-001--010 and CF-01--24 records; Artifacts 06, 07 and 08;
Phase 10/11 handovers and QA reports.

## Current status

-   WP-0: conditionally complete as a read-only baseline/preservation
    assessment.
-   Next: Artifact 08 detailed contract freeze, design/documentation
    only.
-   WP-1--WP-6: planned; implementation not authorized.
-   Phase 10 owner: OpenCode; historical test evidence exists, runtime
    and independent QA gaps remain.
-   Phase 11 owner: Qoder; inherited G1/G2/G3/U1/D1/T1 findings remain
    open in supplied handovers.
-   Kilo: independent read-only QA owner; acceptance remains
    pending/unavailable.

## Repository snapshot

`/home/demon/shorts_studio` - Branch `main`, reported tracking
`origin/main`. - Remote main SHA
`9d38f81ba4f8022d0e820b6a5e1fe2a0fc288c8c`. - 23 modified tracked files;
56 untracked paths; no staged changes reported.

Preserve all local modifications and untracked items. Do not repeat Git
inventory without a genuinely new reason. No destructive cleanup or Git
operations without explicit approval.

## Accepted architecture decisions

ADR-001--010: - UUIDv7 immutable canonical IDs. - PostgreSQL-compatible
authoritative shared-state database. - DB-backed durable queue with
transactional outbox/inbox. - Versioned HTTP/JSON contracts with schema
validation. - Unique worker identity and scoped short-lived
credentials. - Relational artifact metadata with object-storage
abstraction. - Centralized authorization; no publishing bypass. - QA
outcomes PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW, BLOCKED. -
Evidence-backed, use-specific rights. - Separate lifecycle state
machines for content, workflow, execution, review, approval,
authorization and distribution.

CF-01--15 explicitly accepted; CF-16--21 accepted under standing
delegation; CF-22 Option A centralized authorization; CF-23 accepted
under standing delegation; CF-24 no paid services.

Formal detailed contract freeze remains pending owner approval.

## Blockers

G1 storyboard approval gate; G2 rights enforcement; G3 unsupported
claims enforcement; U1 direct publisher bypass; D1 direct pipeline
bypass; T1 traceability completeness; R1 Run Tracker runtime/recovery
evidence. These are inherited report findings, not fresh tests.

## Next step

Complete Artifact 08 Detailed Contract Freeze as design/documentation
only: entity model, state machines, API/event contracts, worker
trust/leases, artifact versioning, centralized governance, recovery
semantics and WP acceptance criteria.

Do not implement until formal contract freeze is approved and separate
explicit implementation authorization is granted.

## Non-negotiable boundaries

-   No code/repository changes, Git operations, tests, dependency
    installs, environment or credential changes without explicit
    authorization.
-   No paid services, provider activation or cloud deployment without
    separate explicit approval.
-   No production generation, upload or publishing without explicit
    authorization.
-   Automatic public publishing disabled.
-   Preserve Shorts Studio; no wholesale replacement.
-   Human approval for critical actions.
-   Unknown rights, approval or authorization never grant permission.

## Documentation continuity rule

**Decide → Document → Preserve → Continue**

Check existing files before creating new ones. Update/version where
appropriate. Keep important decisions and handovers in Markdown.
Preserve originals. Distinguish facts, accepted decisions, proposals,
historical evidence and unverified status. Never claim a document was
saved unless its file exists and location is verified.
