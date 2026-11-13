# NEXTDECODE Content OS — P1 Governance & Autonomy Specification

**Document ID:** ND-P1-GOV-001 | **Version:** 0.1.0-draft | **Date:** 2026-11-04  
**Status:** DRAFT — reconcile all detailed rules with accepted P0 governance/authorization contracts.

## 1. Purpose

Define how P1 learning, policy, agent autonomy, notifications, approval and production changes remain human-governed, evidence-backed and reversible.

## 2. Governance invariants (Accepted direction)

- Human approval and execution authorization are distinct.
- Content approval does not authorize all future policy changes.
- Agents cannot approve their own restricted actions or grant themselves permissions.
- Rights, safety, integrity and hard policy blockers cannot be overridden by ordinary editorial approval.
- Automatic public publishing remains disabled pending a separate policy approval.
- Every consequential action must be attributable and auditable.
- Revocation overrides cached validity.
- Missing, stale, ambiguous or invalid authorization must not grant protected capability.

Authority: P0 Accepted Architecture Decision Baseline 1.0; P0 WP-0 Final Reconciliation Closure Record 1.0.

## 3. Learning lifecycle

**Accepted planning direction from current conversation:**
1. Collect creator feedback and system-generated signals.
2. Detect a possible issue or improvement opportunity.
3. Produce an evidence-backed proposal: problem, evidence, affected workflow/policy, expected impact, risk, dependencies and rollback plan.
4. Creator authorizes staging.
5. Candidate version is tested in isolated staging.
6. Compare candidate and current versions using equivalent evaluation data and tests.
7. Produce an evaluation report, including safety results and limitations.
8. Production activation requires a separate creator decision.
9. Progressive activation occurs only within a creator-approved plan.
10. Monitor after activation; roll back or restrict when criteria trigger.

Approval to stage is not approval to activate production.

## 4. Learning release and batch governance

**Accepted planning direction:**
- Normal releases may be prepared as batches under dynamic event-driven thresholds.
- Priority items can bypass normal batching thresholds, but not safety, rights or authorization gates.
- Critical incidents use a separate incident/review pathway, not automatic production policy mutation.
- AI evidence detection and creator manual marking both identify priority.
- Creator override wins over AI priority assessment; preserve both original assessment and override history.
- Threshold recalibration is event-driven; AI recommends and creator approves.
- Adaptive sensitivity is the selected planning direction; exact thresholds remain open.
- Batch review allows individual decisions per item.
- Batch membership is immutable after approval; changes create a new release version.
- Each change retains an independent approval record.
- Dependency-aware activation prohibits incompatible combinations.
- Failed mandatory tests make a release ineligible for activation.

## 5. Policy registry and enforcement

**Accepted planning direction from current conversation:**
- Hybrid central authority with module-scoped policies.
- Protected invariants cannot be overridden by module policy.
- Precedence: protected core invariants → security/authorization restrictions → central global policies → module-scoped policies → workflow configuration.
- Central authority publishes and governs policy versions.
- Modules enforce approved, integrity-protected snapshots for ordinary decisions.
- High-risk operations require fresh central authorization.
- Standard decision record should include allow/deny/require-authorization, policy version, reason, risk class, evidence reference and authorization reference.
- Policy change workflow: proposal → dependency/conflict analysis → staging → tests → explicit authorization → versioned release → monitoring/rollback.

### 5.1 Outage and snapshot handling

- Central outage uses risk-based continuity, not global fail-open or global fail-closed.
- Continue only safe low-risk operations under valid approved snapshots and explicitly approved offline rules.
- High-risk actions requiring current authorization are blocked.
- Snapshot validity is risk-based; revocation takes precedence over expiry.
- Expired snapshot blocks dependent operations; independent safe operations may continue only when separately authorized.
- No silent snapshot extension.
- Recovery revalidates blocked operations against current policy before resumption.

The last recovery-resumption step is a recommended default (AI/system may revalidate and resume eligible low-risk work); validate it against P0 recovery/job contracts before activation.

## 6. Identity, permission and delegation

**Recommended default, not owner-approved contract:**
- Central identity registry; module-local enforcement of approved permission snapshots.
- Combine role-based access, attribute/context checks and operation-scoped capabilities.
- Separate creator, collaborator, AI-agent, service and external-integration identities.
- A child agent never receives more authority than its delegator.
- Delegation includes task, resource, capability, expiry and parent actor.
- Revocation propagates through delegated grants and worker/agent sessions.
- High-risk actions require fresh central authorization.
- No agent can modify its own role, permissions, policy or qualification.

Existing P0 worker identity/capability contracts and P0 authorization service remain authoritative; this is not a competing IAM model.

## 7. Quality, rights and approval boundaries

- Quality outcomes use P0 accepted vocabulary; do not invent a second competing enum.
- Rights use the accepted CF-20 vocabulary from WP-0 closure: UNKNOWN, PENDING_REVIEW, CLEARED, RESTRICTED, EXPIRED, REVOKED, DENIED.
- Approval uses accepted CF-21 vocabulary: APPROVED, REJECTED, CHANGES_REQUESTED, EXPIRED, REVOKED.
- Approval is bound to the exact item/artifact versions reviewed.
- Authorization is separate, scoped to action/resource/destination and checked at execution boundary.
- A quality PASS alone does not imply rights clearance, approval or distribution authorization.
- Export-only distribution remains the planning baseline; no live publishing is authorized here.

## 8. Adaptive notifications

**Accepted planning direction:**
- AI adjusts routine digest timing only within creator-approved boundaries.
- Significant policy changes require creator approval.
- Critical alerts are immediate and protected from ordinary quiet-hour suppression.
- Notification grouping is intelligent: critical immediate, related important events grouped, routine events digested.
- Deduplicate repeated notifications but preserve underlying events.
- Acknowledging one notification does not resolve unrelated events.
- Digest cadence is adaptive to volume, urgency, relevance, actionability and creator history/preferences.
- Creator preferences inherit global → category → individual; temporary overrides expire.
- AI cannot silently change preference policy or boundaries.
- Rejected recommendations are reconsidered only with materially new evidence/conditions; do not repeat low-value requests.
- Material-change detection combines deterministic mandatory criteria and contextual AI assessment.
- Thresholds are evaluated with historical replay, controlled simulation and comparative metrics; avoid look-ahead leakage.
- Staging sends no real external notifications.
- Progressive production rollout follows creator-approved boundaries.

Exact channels, min/max intervals, quiet hours, volume thresholds and numeric rollout settings remain open.

## 9. Incident and autonomy recovery governance

**Accepted planning direction:**
- Risk-based incident severity uses deterministic safety triggers plus contextual AI assessment.
- AI may escalate severity but cannot downgrade a mandatory critical condition.
- Minor recovery may occur inside pre-authorized limits.
- Serious safety incidents require successful staging/recovery validation and explicit creator approval.
- Post-incident monitoring intensity/duration depends on severity, scope, recurrence risk, recovery confidence and data quality.
- Serious incidents require creator authorization to return to normal monitoring; AI cannot downgrade severity to enable automatic transition.
- Adaptive recurrence governance is a recommended default: repeated similar incidents can increase monitoring, restrict or suspend the affected capability; this still requires owner review before becoming a production policy.

## 10. Audit and change history

Every proposal, decision and consequential transition should record:
- unique ID and version;
- initiating actor and delegation chain;
- evidence and policy versions;
- affected resources/capabilities;
- decision and rationale;
- approval/authorization reference;
- evaluation report and test evidence;
- activation/rollback timestamps;
- monitoring outcome.

Never overwrite the historical decision; corrections are new linked records.

## 11. Acceptance criteria

- Stage approval and production activation are separate.
- Batch item decisions are independently attributable.
- Creator override is preserved and cannot bypass safety.
- Policy precedence is deterministic and testable.
- Revocation overrides cached snapshots.
- Expired snapshots cannot authorize dependent operations.
- High-risk outage behavior is deny/hold without current authorization.
- Agent delegation cannot increase authority.
- Critical notifications cannot be silently suppressed.
- Rejected proposals are not repeatedly resurfaced without material new evidence.
- Serious incident recovery and return-to-normal controls require creator approval.
- All consequential governance events are auditable.
- No publishing or external side effects are enabled by this document.

