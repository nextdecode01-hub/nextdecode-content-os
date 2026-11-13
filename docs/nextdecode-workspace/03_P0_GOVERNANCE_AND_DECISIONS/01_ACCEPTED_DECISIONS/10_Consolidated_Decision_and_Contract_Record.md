# NEXTDECODE --- Consolidated Decision & Contract Record

**Version:** 1.0 \| **Date:** 1 November 2026\
**Status:** Accepted decisions consolidated; formal detailed contract
freeze pending.

## 1. Authority

This is a consolidated summary of decisions recorded in the project
context, not a replacement for original decision records. Original
contract packs remain authoritative for exact full wording where not
reproduced here. Do not invent omitted rationale, text or sign-off
metadata.

An accepted design decision is not implementation authorization. Unknown
or ambiguous permission never grants permission.

## 2. ADR-001 to ADR-010

  -----------------------------------------------------------------------
  ADR                                 Accepted decision
  ----------------------------------- -----------------------------------
  ADR-001                             UUIDv7 canonical IDs; opaque and
                                      immutable

  ADR-002                             PostgreSQL-compatible relational DB
                                      as authoritative shared-state store

  ADR-003                             DB-backed durable queue with
                                      transactional outbox/inbox
                                      initially

  ADR-004                             Versioned HTTP/JSON contracts with
                                      schema validation

  ADR-005                             Unique worker identity, scoped
                                      short-lived credentials and
                                      capability authorization

  ADR-006                             Relational artifact metadata;
                                      binaries behind object-storage
                                      abstraction

  ADR-007                             Centralized authorization;
                                      publishing adapters cannot bypass;
                                      automatic publishing disabled
                                      pending separate policy

  ADR-008                             QA outcomes `PASS`,
                                      `PASS_WITH_WARNINGS`,
                                      `NEEDS_REVIEW`, `BLOCKED`; hard
                                      blockers cannot be bypassed by
                                      ordinary approval

  ADR-009                             Evidence-backed rights states with
                                      use-specific enforcement

  ADR-010                             Separate lifecycle state machines
                                      for content, workflow, execution,
                                      review, approval, authorization and
                                      distribution
  -----------------------------------------------------------------------

## 3. CF-01 to CF-24 status

Recorded status: - CF-01--CF-15 explicitly accepted by owner. -
CF-16--CF-21 accepted under standing delegation. - CF-22 explicitly
accepted, Option A: centralized authorization. - CF-23 accepted under
standing delegation. - CF-24 explicitly accepted: no paid services.

Exact full text of every CF item is not reproduced here; consult the
original Canonical Contracts Pack and decision records.

### Important recorded details

**CF-13 --- Worker identity and trust** - Identity independent of
hostname/machine. - Explicit registration and trust lifecycle. -
Declared, verified, available and authorized capabilities are
distinct. - Scoped, short-lived, revocable credentials. - Same trust
model for local and remote workers. - Auditable trust changes.

**CF-14 --- Worker capabilities, isolation and resources** - Capability
declarations are not permissions. - Bounded job isolation and scoped
filesystem, network, credential and artifact access. - Resource limits
by job class; numeric limits deferred. - Same governance for local and
remote workers. - Admin, production, QA and publishing permissions
separated.

**CF-22 --- Centralized authorization** - Central authorization is
authoritative. - Workers and publishing adapters cannot bypass it.

**CF-24 --- No paid services** - No paid services or charge-generating
infrastructure without separate explicit owner approval.

## 4. Cross-cutting invariants

1.  One canonical owner per entity.
2.  Immutable canonical identity; explicit versions for changes.
3.  Unknown/missing/ambiguous rights, approval or authorization never
    grant permission.
4.  Approval ≠ authorization ≠ execution ≠ successful publication.
5.  Hard QA, rights and policy blockers centrally enforced.
6.  Workers execute bounded assignments.
7.  At-least-once queue delivery; idempotency and traceable attempts
    required.
8.  Artifacts versioned and integrity-checked; repair creates a new
    version.
9.  Review/approval attributable and bound to exact versions.
10. Automatic public publishing disabled pending separate policy.
11. Existing Shorts Studio remains a bounded specialist engine; no
    wholesale replacement.
12. Local-only work waits safely when its required local worker is
    unavailable.
13. Long-term direction: cloud control plane as shared workflow
    authority plus local workers; no provider/deployment selected.
14. Early development local-first and free-first.
15. No paid services without explicit approval.

## 5. Product scope

NEXTDECODE Content OS is one shared intelligence system with specialised
studios and distribution channels.

Twelve product modules: 1. Workspace & Control Center 2. Content Graph
3. Knowledge Management 4. Research Intelligence 5. Brand Intelligence
6. Strategy & Planning 7. Content Quality Intelligence 8. Multiformat
Creation Engine 9. Asset Management 10. Automation & Agent Orchestration
11. Distribution Studio 12. Analytics & Learning

These modules do not imply twelve deployable services.

Lifecycle:
`Discover → Research → Verify → Strategize → Brief → Create → Review → Produce → Approve → Distribute → Analyze → Improve`

Shorts Studio pipeline:
`Topic / Brief → Research and Evidence → Claim Ledger → Script → Storyboard and Shot Planning → Visual Assets → Rendering → QA → Review Package → Approval → Publishing → Analytics and Learning`

## 6. Scope and deployment boundaries

-   Single-owner Creator Mode, one brand: NEXTDECODE.
-   Team, SaaS, billing, multi-brand and advanced cloud expansion
    deferred.
-   Long-term hybrid direction: cloud control plane owns authoritative
    shared workflow/control state; local worker handles local-only and
    heavy rendering when available; remote workers may be supported.
-   Hybrid is a direction, not a selected provider or deployment
    authorization.
-   Early development local-first and cost-minimal; ₹0 initial spending
    target.
-   No paid services, charge-generating infrastructure, provider
    activation or cloud deployment without separate explicit approval.
-   No production generation, upload or publishing without explicit
    authorization.
-   Automatic public publishing disabled pending separate policy.
-   Human approval for critical actions.

## 7. Ownership

  -----------------------------------------------------------------------
  Role                                Responsibility
  ----------------------------------- -----------------------------------
  User                                Product owner and final authority

  Assistant                           Architecture coordination,
                                      research/reconciliation and
                                      acceptance review

  Qoder                               Phase 11 engineering owner

  OpenCode                            Phase 10 engineering/closure owner

  Kilo                                Independent read-only QA
  -----------------------------------------------------------------------

Agents cannot self-expand scope or self-approve.

## 8. Formal status and authorization

**Accepted:** ADR-001--010 and CF-01--24 as summarized.\
**Pending:** Formal detailed contract freeze and final consolidated
owner approval.

**Not authorized:** repository modifications, code implementation, Git
operations, test execution, dependency installation,
environment/credential changes, deployment/provider activation, paid
services, production generation/upload/publishing.

Documentation approval does not grant implementation permission.

## 9. Next gate

Complete Artifact 08 detailed contract freeze as a design/documentation
package, then obtain owner approval. WP-1 implementation requires
separate explicit authorization.
