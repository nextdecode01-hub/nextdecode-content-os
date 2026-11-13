# NEXTDECODE Content OS — P1 System Architecture

**Document ID:** ND-P1-ARCH-001  
**Version:** 0.1.0-draft | **Date:** 2026-11-04  
**Status:** DRAFT — not an approved implementation specification

## 1. Purpose and scope

Define the P1 target architecture as an extension of the accepted P0 foundation and existing Content OS architecture. P1 must not restart the project, replace Shorts Studio, or duplicate contracts already defined in P0.

P1 product direction in this planning package covers multi-format content intelligence and production: Shorts, Long-form, Social, X, Blog, Newsletter and Podcast. Distribution remains export-oriented unless a separate publishing policy is approved. The workspace should be functional and quality-oriented; this does not authorize a full P0 Control Center expansion.

## 2. P0 architectural invariants (Accepted)

The following are carried forward from P0 and must not be re-decided casually:

- One shared intelligence system, multiple specialized content studios and distribution channels, one operating environment.
- Existing Shorts Studio remains a specialized Python/FFmpeg engine and is integrated through a bounded adapter, not wholesale replaced.
- Hybrid is the target deployment direction: cloud control plane with local and remote workers; local rendering remains preferred when local worker is available.
- Cloud-authoritative shared workflow/control state is the accepted target direction.
- UUIDv7 canonical identifiers are accepted in the P0 baseline.
- PostgreSQL-compatible relational database is accepted as the authoritative shared-state store direction; provider/region/budget remain open.
- Database-backed durable queue with transactional outbox/inbox initially is accepted.
- Versioned HTTP/JSON contracts with schema validation are accepted.
- Workers use unique identities, scoped short-lived credentials and capability-based authorization.
- Artifact metadata is relational; binary files sit behind an object-storage abstraction; exact provider/retention remains open.
- Centralized governance and publishing authorization; adapters cannot bypass central authorization.
- Automatic publishing remains disabled pending a separate approved policy.
- Quality outcomes include PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW and BLOCKED; hard blockers cannot be bypassed by ordinary approval.
- Rights enforcement is evidence-backed and use-specific.
- Content, workflow, execution, review, approval, authorization and distribution have separate lifecycle state machines.
- Human silence is never approval. Critical actions require explicit authorization.

Source: Accepted P0 Architecture Decision Baseline 1.0 and WP-0 Final Reconciliation Closure Record 1.0.

## 3. P1 capability architecture (Recommended default)

P1 should compose these domain capabilities around the P0 foundation:

1. Workspace & Creator Control.
2. Content Graph and portfolio.
3. Knowledge and shared memory.
4. Research Intelligence.
5. Brand Intelligence.
6. Strategy and Planning.
7. Content Quality Intelligence.
8. Multiformat Creation Studios.
9. Asset and Artifact Management.
10. Automation and Agent Orchestration.
11. Distribution Preparation / Export.
12. Analytics and Learning.

The exact delivery order and depth must follow P0 contracts and approved P1 requirements; capability names do not imply these modules already exist in the repository.

## 4. Logical architecture layers

### 4.1 Experience layer
Creator workspace, content portfolio, research review, planning, production review, export package review, learning and notification surfaces.

### 4.2 Orchestration layer
Workflow definitions, dependency resolution, scheduling, execution state, task routing, checkpoint/recovery and approval gates. Preserve P0 separation: orchestrator coordinates progression; scheduler controls eligibility; queue durably stores work; workers execute.

### 4.3 Intelligence layer
Research, evidence verification, strategy, brand context, content generation, evaluation, learning proposals and analytics.

### 4.4 Studio layer
Specialist studios for Shorts, Long, Social, X, Blog, Newsletter and Podcast. Shorts Studio remains the first established specialist engine.

### 4.5 Governance layer
Policy registry, policy decision/enforcement, rights checks, quality gates, review, human approval, authorization, emergency pause, audit and controlled learning release.

### 4.6 Data and evidence layer
Canonical relational records, Content Graph, source/evidence/claim registry, artifact/asset registry, provenance graph, audit ledger, immutable versions and object-storage abstraction.

### 4.7 Runtime and infrastructure layer
Cloud control plane, local and approved remote workers, provider adapters, model adapters, storage adapter, observability, backup and recovery. Vendor and deployment specifics remain open unless accepted in P0.

## 5. Evidence-driven research pipeline (Recommended default)

Topic discovery (manual + system suggestions) → research-depth selection → source discovery → evidence extraction → claim mapping → independent verification → synthesis → research package → creator review / brief.

Research depth modes from current planning:
- Standard: straightforward topics and sufficient evidence.
- Advanced: complex, conflicting or multi-domain evidence.
- Frontier: emerging, uncertain, future-facing or potentially transformative topics.
- Escalation: deeper analysis when uncertainty, risk, contradiction or evidence gaps warrant it.
- Creator manual override remains available; explicit requests for deep analysis must not be silently downgraded.

These modes are planning concepts, not frozen contract enums. P0 canonical evidence contracts take precedence.

## 6. Content production pipeline (Recommended default)

Content idea → format-specific content item → research/brief references → studio-specific workflow → versioned production artifacts → quality and rights evaluation → human review/approval where required → export package → optional separately authorized distribution.

Each format-specific item retains its own lifecycle and artifact lineage. Reusable research and assets use typed references with rights verification; references do not imply access or reuse rights.

## 7. Orchestration and execution

- Workflow execution graph is persisted.
- Task inputs/outputs use versioned contracts.
- Checkpoints reference verified artifacts, not merely files that happen to exist.
- Retry is bounded and error-classified.
- Uncertain external side effects require reconciliation before retry.
- Approval is a dedicated gate bound to exact artifact version/hash and applicable policy version.
- A failed or blocked task cannot produce a success-grade downstream artifact.
- Resume must be idempotent and preserve lineage.

Details must reconcile with Architecture Part 4/5 and Canonical Contracts Pack before freeze.

## 8. Governance and learning

P1 adds a controlled learning lifecycle: collect feedback → detect issue → propose improvement with evidence/impact/risk → creator approves staging → isolated validation → comparative report → separate creator production activation approval → monitor → scoped rollback/recovery.

A content approval does not automatically update global policies. AI may propose but cannot silently change policy, evaluation standards, autonomy or governance.

Current conversation selections for staged apply, batch production approval, creator override, adaptive notifications, policy authority and risk-based continuity must be reconciled against P0 accepted CF/ADR records before being promoted from recommendation to accepted P1 requirement.

## 9. Data consistency and contracts

- P0 canonical IDs, domain ownership, identity/version distinction and state-machine boundaries remain authoritative.
- P1 modules consume versioned shared contracts rather than reaching into another module's private storage.
- Contract changes require owner, compatibility assessment, migration, tests and versioned approval.
- No hidden dual-write or secondary source of truth.
- Artifacts are versioned and provenance-linked; mutations create new versions.
- Audit history is append-only/tamper-evident by design; exact implementation is open.

## 10. Cross-cutting reliability and security

Use risk-based continuity, not blanket fail-open or blanket fail-closed:
- continue only independently safe operations under valid approved policy snapshots and explicitly approved offline rules;
- block high-risk actions requiring fresh central authorization;
- expired policy snapshots cannot authorize dependent operations;
- revocation takes precedence over cached validity;
- recovery revalidates operations and does not replay uncertain external side effects without reconciliation.

Observability separates audit records, logs, metrics, traces and domain events. RPO/RTO, retention, alert thresholds and provider choices remain open.

## 11. Explicit non-goals / boundaries

- No wholesale rewrite of Shorts Studio.
- No automatic public publishing.
- No production deployment or paid service enablement.
- No broad Control Center build folded into P0-A.
- No unbounded agent autonomy or self-approval.
- No unapproved policy/contract migration.
- No claim that architectural descriptions prove implementation or runtime readiness.

## 12. Validation dependencies

This architecture cannot be called implementation-ready until:
1. P0 detailed contracts are reconciled and frozen through existing owner process.
2. Master Blueprint 2.0 and all Architecture Parts 1–8 are fully cross-checked.
3. Existing module/contract traceability and WP-0 no-duplication requirements are honored.
4. P1 requirements and scope are explicitly approved.
5. A bounded work package, tests and implementation authorization exist.

## 13. Change log

| Version | Date | Change |
|---|---|---|
| 0.1.0-draft | 2026-11-04 | Initial P1 system architecture draft |
