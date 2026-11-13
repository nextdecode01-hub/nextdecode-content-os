# NEXTDECODE Content OS — P1 Architecture Decision Register

**Document ID:** ND-P1-ADR-001 | **Version:** 0.1.0-draft | **Date:** 2026-11-04  
**Status:** DRAFT — decisions below do not supersede P0 authority.

## 1. Status rules

- **Accepted:** Explicit owner decision, supported by the conversation or existing accepted P0 source.
- **Recommended default:** Assistant recommendation for planning, not yet a frozen owner-approved contract.
- **Open:** Needs review, evidence or owner decision.
- **Blocked:** Cannot proceed until a dependency or authorization is resolved.

## 2. Accepted P0 decisions (carried forward)

| ID | Decision | Status | Authority |
|---|---|---|---|
| P0-ADR-001 | UUIDv7 canonical IDs | Accepted | P0 Accepted Architecture Decision Baseline 1.0 |
| P0-ADR-002 | PostgreSQL-compatible relational authoritative shared-state store | Accepted direction; provider open | P0 Accepted Architecture Decision Baseline 1.0 |
| P0-ADR-003 | DB-backed durable queue with transactional outbox/inbox initially | Accepted | P0 Accepted Architecture Decision Baseline 1.0 |
| P0-ADR-004 | Versioned HTTP/JSON with schema validation | Accepted | P0 Accepted Architecture Decision Baseline 1.0 |
| P0-ADR-005 | Unique worker identity, scoped short-lived credentials, capability authorization | Accepted | P0 Accepted Architecture Decision Baseline 1.0 |
| P0-ADR-006 | Relational artifact metadata and provider-independent binary storage abstraction | Accepted direction; provider/retention open | P0 Accepted Architecture Decision Baseline 1.0 |
| P0-ADR-007 | Centralized authorization; no adapter bypass; auto-publishing disabled pending separate policy | Accepted | P0 Accepted Architecture Decision Baseline 1.0 |
| P0-ADR-008 | PASS / PASS_WITH_WARNINGS / NEEDS_REVIEW / BLOCKED; hard blockers not bypassed by ordinary approval | Accepted | P0 Accepted Architecture Decision Baseline 1.0 |
| P0-ADR-009 | Evidence-backed, use-specific rights enforcement | Accepted | P0 Accepted Architecture Decision Baseline 1.0 |
| P0-ADR-010 | Separate content/workflow/execution/review/approval/authorization/distribution state machines | Accepted | P0 Accepted Architecture Decision Baseline 1.0 |

## 3. P1 decisions explicitly selected in the current planning conversation

These are explicit owner selections in this planning conversation, but they still require reconciliation with existing P0 accepted CF/ADR contracts before they become implementation contracts.

| ID | Decision | Status | Notes |
|---|---|---|---|
| P1-DEC-001 | Human-controlled learning: creator reviews proposals; staging precedes production | Accepted planning decision | Align with P0 policy/approval/learning contracts |
| P1-DEC-002 | Staged Apply: approval to stage is separate from production activation | Accepted planning decision | Two distinct approvals |
| P1-DEC-003 | Batch production approval with individual decisions per item | Accepted planning decision | Batch immutable after review; each change retains its own approval |
| P1-DEC-004 | Hybrid learning release: normal, priority and critical pathways | Accepted planning decision | Numeric thresholds remain open |
| P1-DEC-005 | Priority detection by AI evidence and creator marking; creator override wins | Accepted planning decision | Override cannot bypass rights/security/authorization |
| P1-DEC-006 | Threshold recalibration is event-driven; AI recommends, creator approves | Accepted planning decision | Adaptive sensitivity selected |
| P1-DEC-007 | Learning release evaluation combines historical replay, simulation and comparison | Accepted planning decision | Avoid leakage/look-ahead |
| P1-DEC-008 | Safety gates are mandatory; performance trade-offs cannot compensate for safety failure | Accepted planning decision | Hybrid acceptance |
| P1-DEC-009 | Staging uses standard baseline tests plus risk-based and major-change end-to-end tests | Accepted planning decision | Isolate external side effects |
| P1-DEC-010 | Production activation uses controlled progressive rollout with creator-approved plan | Accepted planning decision | Percentages/durations open |
| P1-DEC-011 | Pre-authorized routine rollout steps may proceed automatically; protected expansions require creator approval | Accepted planning decision | Exact transitions must be declared in release plan |
| P1-DEC-012 | Uncertain rollout performance receives risk-based hold, pause or rollback | Accepted planning decision | Missing evidence never means safe |
| P1-DEC-013 | Uncertainty classification combines deterministic safety rules and AI contextual assessment | Accepted planning decision | AI can escalate, not downgrade mandatory critical conditions |
| P1-DEC-014 | Serious incident recovery requires validated recovery and explicit creator approval | Accepted planning decision | Minor recovery only within approved boundaries |
| P1-DEC-015 | Post-incident enhanced monitoring and return-to-normal authorization are risk-based | Accepted planning decision | AI cannot downgrade serious incident severity |
| P1-DEC-016 | Adaptive recurrence governance is the recommended planning direction | Recommended default | Assistant selected after user delegated routine decisions; not explicit owner approval |
| P1-DEC-017 | Policy Registry Authority is central authority with module-scoped policies | Accepted planning decision | Protected invariants remain central |
| P1-DEC-018 | Policy enforcement uses hybrid central governance + local approved snapshots | Accepted planning decision | High-risk action needs current central authorization |
| P1-DEC-019 | Central outage behavior is risk-based continuity | Accepted planning decision | Safe low-risk operations only |
| P1-DEC-020 | Policy snapshot validity uses risk-based expiry | Accepted planning decision | Revocation overrides expiry |
| P1-DEC-021 | Expired snapshot during outage causes operation-specific restrictions | Accepted planning decision | Independent safe operations may continue only with separate valid authorization |
| P1-DEC-022 | Adaptive notifications use hybrid control | Accepted planning decision | AI adjusts within creator-approved boundaries |
| P1-DEC-023 | Notification boundary overrun triggers recommendation, not silent expansion | Accepted planning decision | Creator keeps boundary control |
| P1-DEC-024 | Rejected recommendations are reconsidered only with materially new evidence/conditions | Accepted planning decision | Preserve rejection history |
| P1-DEC-025 | Material-change detection combines deterministic conditions and contextual AI assessment | Accepted planning decision | Mandatory criteria cannot be bypassed |
| P1-DEC-026 | Notification threshold changes require creator approval | Accepted planning decision | AI monitors and proposes |
| P1-DEC-027 | Notification threshold evaluation uses historical replay + simulation + comparative metrics | Accepted planning decision | Candidate/current comparison |
| P1-DEC-028 | Mixed evaluation acceptance: mandatory safety pass plus criteria and creator approval | Accepted planning decision | No score can offset safety failure |
| P1-DEC-029 | Staging validation is hybrid: baseline + risk-based + full E2E for major changes | Accepted planning decision | No real external notifications from staging |
| P1-DEC-030 | Notification production activation uses controlled progressive rollout | Accepted planning decision | Creator authorizes rollout plan |
| P1-DEC-031 | Rollout progression uses hybrid authorization | Accepted planning decision | Pre-authorized transitions vs creator-approved expansions |
| P1-DEC-032 | Uncertain rollout uses risk-based response | Accepted planning decision | Monitor, hold, pause or protective rollback |
| P1-DEC-033 | Uncertainty severity uses deterministic + AI contextual assessment | Accepted planning decision | Safety engine may not be downgraded by AI |
| P1-DEC-034 | Serious incident recovery uses risk-based authorization | Accepted planning decision | Serious case requires creator approval |
| P1-DEC-035 | Post-incident autonomy monitoring uses risk-based enhanced monitoring | Accepted planning decision | Monitor scope/recurrence/confidence |
| P1-DEC-036 | Return to normal monitoring uses risk-based transition authorization | Accepted planning decision | Serious case requires explicit approval |

## 4. Recommended defaults (not owner-approved)

| ID | Recommendation | Rationale | Approval dependency |
|---|---|---|---|
| P1-REC-001 | Central Identity + distributed enforcement | Central authority, local module checks, high-risk central authorization | Reconcile P0 IAM/worker contracts |
| P1-REC-002 | RBAC + ABAC + capability model | Roles, context and operation-scoped grants | Existing capability contract review |
| P1-REC-003 | Append-only/tamper-evident audit ledger | Forensic continuity | Compare accepted event/audit contracts |
| P1-REC-004 | Claim-level provenance graph | Trace claims through evidence, scripts and final artifacts | Canonical evidence contracts |
| P1-REC-005 | Central workflow orchestrator with specialist execution | Avoid monolithic studio logic; preserve queue/worker separation | P0 Parts 4/5/7 |
| P1-REC-006 | Persisted DAG and verified checkpoints | Safe resume and lineage | Job/artifact state contracts |
| P1-REC-007 | Failure-domain isolation | Failure in one module should not take down independent modules | Deployment and operational contracts |
| P1-REC-008 | Central policy lifecycle manager | Dependency graph, conflict detection, compatibility and release controls | Existing policy registry and contract freeze |
| P1-REC-009 | Domain-owned data with shared versioned contracts | Avoid direct cross-module storage coupling | P0 canonical contract pack |
| P1-REC-010 | Keep logical components modular; do not force microservices | Cost and operational simplicity | Technology and deployment review |
| P1-REC-011 | Risk-based recovery revalidation automatically resumes eligible low-risk queued work | Aligns with risk-based continuity decisions | Owner review; no automatic side effect |
| P1-REC-012 | Adaptive recurrence governance | Increase monitoring/restriction for repeated incidents | Owner confirmation |
| P1-REC-013 | Configurable notification channels and hierarchical preferences | Global → category → individual overrides | Privacy and delivery contract review |

## 5. Open decisions

| ID | Topic | Why open |
|---|---|---|
| P1-OPEN-001 | Exact P1 product scope and ordering | Reconcile with Blueprint and existing P0/P1 plan |
| P1-OPEN-002 | Strategy depth and strategic-intelligence boundaries | Earlier conversation proposed Strategic Intelligence; no explicit selection recorded |
| P1-OPEN-003 | Exact identity roles and permissions | Need P0 capability/identity contracts |
| P1-OPEN-004 | Data schemas for learning/notifications/incident lifecycle | Need canonical schema, version and retention decisions |
| P1-OPEN-005 | Numeric adaptive thresholds and rollout values | Require baselines and owner approval |
| P1-OPEN-006 | Policy compatibility and stale snapshot numeric validity | Risk policy requires measurable criteria |
| P1-OPEN-007 | Digest quiet hours, min/max intervals and delivery channels | Creator settings and operational needs |
| P1-OPEN-008 | Audit and evidence retention periods | Legal/privacy/cost and P0 retention contracts |
| P1-OPEN-009 | Model/provider selection and fallback policy | Free-first/cost/privacy/data handling |
| P1-OPEN-010 | Cloud provider/region and production deployment | Explicitly open in P0 |
| P1-OPEN-011 | RPO/RTO and backup objectives | Must be costed and tested |
| P1-OPEN-012 | Full P1 acceptance thresholds and quality targets | Require testable baselines |

## 6. Conflict rule

If any P1 planning decision conflicts with accepted P0 ADR/CF decisions, the P0 decision controls until the owner formally approves a superseding ADR or contract amendment. This register is not itself a contract-freeze record.

