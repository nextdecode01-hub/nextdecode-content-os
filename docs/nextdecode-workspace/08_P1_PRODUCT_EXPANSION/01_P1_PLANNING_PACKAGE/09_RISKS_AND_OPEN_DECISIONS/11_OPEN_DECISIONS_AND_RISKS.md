# NEXTDECODE Content OS — Open Decisions, Risks & Blockers

**Document ID:** ND-P1-RISK-001 | **Version:** 0.1.0-draft | **Date:** 2026-11-04  
**Status:** DRAFT — must be updated after full P0 source reconciliation.

## 1. Critical blockers

| ID | Blocker | Evidence/source | Impact | Required resolution |
|---|---|---|---|---|
| BLK-001 | P0 implementation authorization is not granted | P0 Implementation Authorization Brief 1.0 | No repository/code/test implementation | Owner completes separate authorization process |
| BLK-002 | P0 detailed contracts are not fully frozen | WP-0 closure record and Canonical Contracts Pack | P1 cannot safely finalize schemas | Complete existing detailed contract closure; avoid duplicate documents |
| BLK-003 | P0 current runtime/independent QA evidence remains incomplete | WP-0 closure record | Readiness cannot be claimed | Follow separately authorized baseline/QA gates |
| BLK-004 | P1 scope and work packages require formal owner authorization | Current P1 package draft | No implementation work can begin | Owner review and explicit P1 authorization |
| BLK-005 | Existing P0 source reconciliation is incomplete in this documentation pass | Partial source extraction | Unseen clauses may conflict with P1 drafts | Review full Master Blueprint, contract pack remainder, all Parts 1–8, Shared Core contracts, traceability matrix and fast closure plan |

## 2. Architectural and governance risks

| ID | Risk | Severity | Mitigation |
|---|---|---|---|
| RSK-001 | P1 drafts may duplicate existing P0/P1 artifacts | High | Use existing P0 sources as authority; WP-0 no-duplication rule |
| RSK-002 | Current conversation choices may conflict with accepted P0 CF/ADR contracts | High | Reconcile each choice; P0 wins until formal superseding decision |
| RSK-003 | P1 module breadth may exceed approved scope and budget | High | Prioritize vertical slices; explicit scope and cost gate |
| RSK-004 | Full autonomous learning may alter policies without sufficient governance | Critical | Staged apply and separate production approval |
| RSK-005 | Local policy snapshots may become stale or revoked | High | Risk-based expiry, revocation precedence, operation-specific restrictions |
| RSK-006 | Cross-module state duplication creates inconsistent truth | Critical | Domain ownership, shared contracts, no hidden dual-write |
| RSK-007 | Research outputs overstate evidence or source independence | High | Claim-level evidence, source-family deduplication and uncertainty |
| RSK-008 | Agent delegation expands effective authority | Critical | Scope-limited delegation, parent ceiling, revocation and audit |
| RSK-009 | Failure recovery replays external side effects | Critical | Reconcile uncertain outcomes before retry |
| RSK-010 | UI becomes a bypass around backend authorization | Critical | Backend-enforced policy and negative tests |
| RSK-011 | Notification adaptation creates overload or suppresses critical items | High | Creator boundaries, critical exceptions, event ledger and monitoring |
| RSK-012 | Progressive rollout expands without proper authorization | Critical | Exact pre-authorized transitions, creator approval for protected expansion |
| RSK-013 | Provider selection conflicts with free-first target | Medium/High | Cost model and separate approval before paid activation |
| RSK-014 | Audit retention conflicts with privacy/storage requirements | High | Reconcile lifecycle, legal-hold, privacy and retention contracts |

## 3. Open owner decisions

- Exact P1 feature ordering and first P1 vertical slice.
- Strategic Intelligence depth; recommendation discussed but not explicitly selected.
- Final policy snapshot validity parameters and recovery resumption rules.
- Notification channels, quiet hours, min/max digest cadence and thresholds.
- Numerical learning release thresholds, priority batch rules and rollout percentages/durations.
- Incident recurrence triggers and automatic restriction boundaries.
- P1 acceptance thresholds for research, content and quality.
- Data/audit/evidence retention and deletion semantics.
- Cloud provider, region, storage provider, model provider and budgets (remain open in P0).
- RPO/RTO and production support model.
- Agent runtime/tooling and any change in existing agent ownership.

## 4. Source inspection limitations

In this pass:
- Accepted P0 decision baseline, decision register, architecture reconciliation report, P0 implementation authorization brief, P0 foundation specification and WP-0 closure record were read.
- Canonical Contracts Pack was only partially retrieved (first 1,000 of 1,499 lines).
- Master Blueprint 2.0 DOCX was located but not extracted.
- Architecture Parts 1–8 were present and listed; bulk content returned but output truncation prevented full per-section review.
- Fast Closure Master Plan file appeared in directory listing, but attempted exact path read returned ENOENT; exact path needs correction.
- Shared Intelligence Core Contracts 01–12 and Module-to-Contract Traceability Matrix were located in the existing P0 source tree but were not fully reviewed.

Therefore this package is a **first-pass P1 planning draft**, not a complete validated handoff.

## 5. Risk acceptance

No critical/high risk is accepted by default. Each requires an owner decision with rationale, affected scope, expiry/review trigger and mitigation. The existence of a mitigation proposal does not constitute risk acceptance.

## 6. Change log

| Version | Date | Change |
|---|---|---|
| 0.1.0-draft | 2026-11-04 | Initial blockers and risk inventory |
