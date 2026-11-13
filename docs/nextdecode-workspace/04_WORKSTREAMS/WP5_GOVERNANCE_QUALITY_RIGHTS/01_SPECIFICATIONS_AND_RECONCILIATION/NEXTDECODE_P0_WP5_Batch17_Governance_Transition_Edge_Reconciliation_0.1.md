# NEXTDECODE P0 — WP5 / Batch 17 Governance Transition-Edge Reconciliation

**Document ID:** NEXTDECODE-P0-WP5-B17-TRANSITIONS-0.1  
**Version:** 0.1  
**Date:** 2026-11-04  
**Status:** WORKING EVIDENCE CROSSWALK — OWNER REVIEW REQUIRED  
**Work package:** B-WP5-03  
**Implementation status:** NOT AUTHORIZED  
**Agent dispatch:** NOT AUTHORIZED  
**Batch 17 freeze:** NOT GRANTED

---

## 1. Purpose and scope

This package examines the actual Batch 17 SM-11 Rights Determination, SM-12 Review and Approval, SM-13 Central Authorization Decision and SM-14 Distribution/External Operation sections against accepted CF-20/CF-21/CF-22, Contract 07 v1.0, WP5 v0.1 and Data Dictionary v1.1.

The objective is to distinguish:
- accepted state vocabularies and invariants;
- candidate state labels and proposed transition edges;
- source-defined guards and enforcement requirements;
- missing transition edges and owner-reserved decisions.

This is documentation-only. It does not amend Batch 17 or any source contract, define new enums, freeze transitions, authorize schema changes or dispatch agents.

## 2. Dependency and authority check

| Source | Version/status | Relevant sections |
|---|---|---|
| Accepted Artifact 08 Implementation Reference / Contract Decisions | 1.0; accepted | CF-20, CF-21, CF-22 |
| Contract 07 — Content Quality, Rights & Governance Intelligence | 1.0; working architecture contract | §§7.2–7.4, 8–11, 14 |
| WP5 Governance, Quality, Rights & Authorization | 0.1; design candidate | §§3–4, 8–14, 17–19 |
| Data Dictionary & Entity Ownership Registry | 1.1; working standard | §§12.2–12.5, §§19.4–19.7 |
| Batch 17 State-Machine & Transition Catalogue | candidate; not frozen | §§13–20, 22–23; especially SM-11–SM-14 |
| B-WP5-01 Contract 07 / Batch 17 / Batch 19 Crosswalk | 0.1; working evidence | §§4–11 |
| B-WP5-02 Governance State & Decision Matrices | 0.1; working candidate | Matrices A–D |
| Contract 12 distribution/publishing reconciliation | 0.1; working candidate | C12-01..07; exact adapter details remain open |
| Agent Operating Protocol | 0.1.0-draft | Authorization and writer/reviewer boundaries |

Accepted baseline:
- CF-20 rights vocabulary: UNKNOWN, PENDING_REVIEW, CLEARED, RESTRICTED, EXPIRED, REVOKED, DENIED.
- CF-21 ApprovalDecision vocabulary: APPROVED, REJECTED, CHANGES_REQUESTED, EXPIRED, REVOKED.
- CF-22: centralized authorization Option A; default-deny, fail-closed, least privilege and exact action/resource/version/destination scope.
- ADR-010: separate lifecycle state machines.
- Human approval before publishing; automatic public publishing disabled.
- No implementation, agent execution, tests, repository/Git changes, deployment or publishing authorization.

## 3. Findings at a glance

| Batch 17 section | Current content | Reconciliation result |
|---|---|---|
| SM-11 Rights Determination | Canonical CF-20 state meanings and downstream effects | Vocabulary aligned; explicit from→to transition edges absent |
| SM-12 Review and Approval | CF-21 outcomes plus decision/event guard rows | Vocabulary aligned; rows are event/guard descriptions, not a complete transition matrix; ApprovalRequest lifecycle absent |
| SM-13 Central Authorization | Conceptual states and execution-time binding checks | Centralized authority aligned; state labels remain candidate; explicit from→to edges absent |
| SM-14 Distribution / External Operation | Proposed states and explicit from→to transition rows | Useful candidate edge catalogue; not frozen; must be checked against Contract 12 and adapter-specific behavior |

**Clarification on the previously reported contradiction:** the source evidence inspected here confirms a vocabulary conflict between Contract 07 §10.2 (WITHDRAWN) and accepted CF-21 (REVOKED). Batch 17 SM-12 uses the CF-21 vocabulary and a row labelled “Approval revoked.” However, SM-12 does not provide a contradictory explicit from-state → to-state edge. Therefore the currently evidenced conflict is a decision-token conflict plus missing transition specification, not a proven contradictory SM-12 edge. Any separate earlier finding must be tied to its exact row/source before it can be called an edge contradiction.

## 4. SM-11 — CF-20 RightsDetermination

### 4.1 State vocabulary and effect

| State | Batch 17 meaning/effect | Authority |
|---|---|---|
| UNKNOWN | Rights not established; fail closed | CF-20 accepted |
| PENDING_REVIEW | Evidence submitted but undecided; fail closed / hold | CF-20 accepted |
| CLEARED | Evidence supports specified use/context; rights prerequisite only | CF-20 accepted |
| RESTRICTED | Conditional use; conditions and separate authorization still apply | CF-20 accepted |
| EXPIRED | Validity ended; fail closed pending renewal/review | CF-20 accepted |
| REVOKED | Prior clearance withdrawn; fail closed; invalidate dependent assumptions | CF-20 accepted |
| DENIED | Intended use explicitly denied | CF-20 accepted |

Batch 17 explicitly says legacy PENDING_VERIFICATION and PROHIBITED are not silently aliased. This matches CF-20 propagation.

### 4.2 Transition-edge evidence

SM-11 contains a state meaning/effect table and scope/evaluation rules. It does not contain a complete explicit transition matrix of the form source state → target state, command/event, actor, guard, evidence and rejection behavior.

| Potential transition/event | What source establishes | What remains OPEN |
|---|---|---|
| Evidence received → assessment pending | PENDING_REVIEW is a canonical state; assessment is evidence-backed | Whether this is an initial state, event or separate record; actor and validation |
| PENDING_REVIEW → CLEARED | CLEARED meaning and exact-use prerequisite | Evidence threshold, decision actor/authority, command/event and transition guard |
| PENDING_REVIEW → RESTRICTED | RESTRICTED meaning and conditions | Restriction representation, approval authority and transition guard |
| PENDING_REVIEW → DENIED | DENIED means use explicitly denied | Decision authority, appeal/review and transition guard |
| CLEARED/RESTRICTED → EXPIRED | Expiry validity ends; checked at protected execution time | Expiry scheduler/clock, effective-time semantics, transition edge |
| CLEARED/RESTRICTED → REVOKED | Prior clearance withdrawn; checked at protected execution time | Revocation role, reason, effective time, notification and dependent-record invalidation |
| Any determination → reassessment | New evidence/determination history is retained | Whether a new record supersedes prior record or mutable aggregate state changes |
| Scope/evidence changes → invalidation/review | Rights are use-specific; prior clearance cannot be reused when material dimensions change | Exact invalidation event, downstream fan-out and approval re-review rule |

### 4.3 Disposition

The accepted CF-20 tokens and fail-closed effects are clear. Do not create transition edges or rights-state actors in Batch 17 until the owner/domain authority specifies them. Rights assessment remains separate from quality, approval and authorization.

## 5. SM-12 — CF-21 ApprovalDecision and ApprovalRequest

### 5.1 Accepted decision outcomes

| Outcome | Meaning/effect | Authority |
|---|---|---|
| APPROVED | Reviewer accepts exact reviewed scope/version; satisfies approval prerequisite only | CF-21 accepted |
| REJECTED | Exact scope/version rejected; no protected permission | CF-21 accepted |
| CHANGES_REQUESTED | Revision required; new version/review cycle as policy defines | CF-21 accepted |
| EXPIRED | Approval validity ended; no longer satisfies prerequisite | CF-21 accepted |
| REVOKED | Approval decision revoked; dependent action re-evaluated | CF-21 accepted |

Contract 07 v1.0 §10.2 instead lists WITHDRAWN as its fifth outcome. This is the confirmed source conflict. WITHDRAWN is not in accepted CF-21 and must not be silently aliased to REVOKED.

### 5.2 Event/guard evidence versus actual transitions

| Batch 17 SM-12 row | What it specifies | What it does not specify |
|---|---|---|
| Review opened | Reviewer role/access valid for exact version | Request state, request assignment workflow, transition edge |
| Decision recorded | Authenticated actor; reason/evidence/version recorded | Which request state permits which decision; source/target state edge |
| Approval expired | Validity window or policy condition reached | Expiry actor/system, exact transition from prior decision state, clock and precedence |
| Approval revoked | Authorized revocation role and reason | Revocation role matrix, source-state eligibility, effective-time and edge |
| New version created | Old approval remains bound to old version; new version requires review | Request lifecycle, event linkage, automatic invalidation details |

SM-12 provides decision/outcome vocabulary and guards. It does not provide a complete state transition graph.

### 5.3 ApprovalRequest is a separate unresolved lifecycle

- Data Dictionary v1.1 §12.4 defines ApprovalRequest fields including approval_request_id, subject/version, requested_action, destination_context, policy_version, expires_at and requested_by.
- Contract 07 §10.1 also describes assigned reviewer/role and decision/rationale history.
- Data Dictionary v1.1 separately defines ApprovalDecision and its approval_request_id link.
- Neither accepted CF-21 nor the inspected Data Dictionary section establishes a full ApprovalRequest lifecycle enum or complete transition graph.
- Contract 07 §10.2's WITHDRAWN token is in the approval-outcome list, but the source does not clearly distinguish request withdrawal from decision withdrawal.

**Disposition:** preserve ApprovalRequest as a separate record; do not add WITHDRAWN to ApprovalDecision; do not substitute REVOKED for request withdrawal. Request lifecycle, withdrawal/closure semantics, request expiry, resubmission and request-to-decision cardinality remain OPEN.

## 6. SM-13 — CF-22 Central Authorization

### 6.1 Authority and candidate states

CF-22 explicitly selects centralized authorization Option A. Batch 17 SM-13 lists conceptual states:

| Candidate state | Batch 17 meaning/effect | Status |
|---|---|---|
| NOT_EVALUATED | No decision; default deny | CANDIDATE |
| DENIED | Policy denied; protected action prohibited | CANDIDATE representation of accepted deny behavior |
| AUTHORIZED | Current decision permits exact bound action | CANDIDATE representation of scoped allow |
| EXPIRED | Validity ended; deny and re-evaluate | CANDIDATE |
| REVOKED | Decision withdrawn; deny and re-evaluate | CANDIDATE |
| INVALIDATED | Bound input changed; deny and obtain fresh decision | CANDIDATE |

These are not an owner-frozen authorization enum. The accepted contract is the centralized authority and its enforcement invariants.

### 6.2 Binding checks

| Binding | Batch 17 execution-time check | Reconciliation |
|---|---|---|
| Action | Requested operation matches exact action | Accepted CF-22 invariant |
| Resource/version | Target and immutable version match | Accepted CF-22 invariant |
| Destination | Exact platform/account/destination matches | Accepted CF-22 invariant |
| Policy version | Current policy still permits action | Accepted policy binding; exact update semantics OPEN |
| Time validity | Decision remains within validity window | Accepted expiry principle; duration OPEN |
| Approval | Required approval current and exact-version bound | Accepted CF-21 prerequisite; never authorization itself |
| Rights | Use-specific rights remain applicable | Accepted CF-20 prerequisite |
| Quality | BLOCKED or policy blocker prevents action | Accepted CF-19/ADR-008 invariant |
| Emergency pause | Current pause state permits execution | Accepted control principle; scope/in-flight detail OPEN |
| Actor/worker capability | Executing identity permitted for action | Accepted least-privilege principle; detailed capability model OPEN |

SM-13 does not define a full from→to state graph, authorization decision record cardinality, grant consumption or cache/revocation race behavior. Those details remain owner/schema/security decisions.

## 7. SM-14 — Distribution and external operation

SM-14 labels its state set as proposed and provides explicit candidate transition edges. It is the only governance-adjacent section in this reviewed range with a complete source/target transition table.

### 7.1 Proposed states

PREPARED, READY, AUTHORIZED, SUBMITTING, CONFIRMED, REJECTED, UNKNOWN_OUTCOME, CANCELLED and REVOKED_OR_BLOCKED.

These remain candidate distribution-operation states, not CF-22 authorization states.

### 7.2 Explicit candidate transition edges

| From → To | Batch 17 guard/evidence | Status |
|---|---|---|
| PREPARED → READY | Integrity, rights, QA, approval and destination checks pass | CANDIDATE; Contract 12 mapping required |
| READY → AUTHORIZED | Central allow for exact operation binding | CANDIDATE; central authority invariant accepted |
| AUTHORIZED → SUBMITTING | Recheck expiry/revocation, pause, exact version and destination | CANDIDATE; execution-time recheck principle accepted |
| SUBMITTING → CONFIRMED | Remote response/evidence confirms intended result | CANDIDATE; remote evidence requirement accepted |
| SUBMITTING → REJECTED | Remote platform definitively rejects | CANDIDATE; provider-specific evidence open |
| SUBMITTING → UNKNOWN_OUTCOME | Timeout/loss after possible side effect | CANDIDATE; unknown outcome must be reconciled |
| UNKNOWN_OUTCOME → CONFIRMED/REJECTED | Remote reconciliation establishes outcome | CANDIDATE; adapter lookup/evidence open |
| PREPARED/READY/AUTHORIZED → CANCELLED/BLOCKED | Authorized cancellation, policy change, revoked rights/approval or pause | CANDIDATE; cancellation authority and in-flight behavior open |

### 7.3 Cross-machine prerequisites and non-inheritance

Batch 17 §19 explicitly states:
- Quality pass does not inherit approval or rights clearance.
- Approval gate does not inherit central authorization.
- Rights gate for one use does not imply rights for another use/destination.
- Worker job claim does not imply permission to publish.
- Distribution execution requires exact package/version/destination, QA, rights, approval, central authorization and pause check.
- External success requires remote evidence; local process exit or command acceptance is insufficient.

Batch 17 §20 prohibits:
- BLOCKED QA bypassed by ordinary approval.
- UNKNOWN/PENDING_REVIEW rights treated as CLEARED.
- Approval treated as authorization.
- Expired/revoked authorization reused.
- Unknown external outcome blindly retried.
- Remote success inferred from local success.

These controls align with the accepted governance separation and should be retained in any later owner-frozen transition specification.

## 8. Acceptance-oracle traceability available in Batch 17

| Batch 17 test | Scenario | Expected result | Governance mapping |
|---|---|---|---|
| SMT-04 | Content version changes after approval | Old approval remains bound to old version | CF-21 |
| SMT-11 | QA BLOCKED with approval APPROVED | Protected action denied | CF-19 / CF-21 |
| SMT-12 | Rights PENDING_REVIEW | Protected use denied/held | CF-20 |
| SMT-13 | Approval expires before distribution | Authorization denied/re-evaluation required | CF-21 / CF-22 |
| SMT-14 | Authorization revoked before execution | Execution-time check denies | CF-22 |
| SMT-15 | Emergency pause before submit | Protected action denied per approved pause semantics | CF-22 / Contract 07 §14 |
| SMT-16 | Publish times out after possible success | UNKNOWN_OUTCOME; reconcile before retry | Contract 12 / distribution boundary |
| SMT-20 | Replay historical distribution event | Projection may rebuild; no side effect repeated | Lifecycle/event safety |

These are catalogue scenarios, not evidence that tests were implemented or executed. WP6/Artifact 07 exact test-level mapping remains open under GAP-026.

## 9. Owner decisions and unresolved details

| ID | Decision / evidence required | Owner boundary |
|---|---|---|
| B17-GOV-01 | RightsDetermination exact transition edges, actor roles and evidence thresholds | Contract 07 / governance owner |
| B17-GOV-02 | ApprovalRequest lifecycle, withdrawal/closure, expiry, resubmission and request-to-decision cardinality | Contract 07 / governance owner |
| B17-GOV-03 | ApprovalDecision source/target edges, reviewer/revocation roles, expiry and re-review | Contract 07 / governance owner |
| B17-GOV-04 | AuthorizationDecision vs PublishingAuthorization record model and state vocabulary | Central authorization / WP1 / Contract 07 |
| B17-GOV-05 | Authorization expiry/revocation propagation, idempotency/consumption and execution-time revalidation | Security / WP5 / WP1 |
| B17-GOV-06 | Emergency pause scope, authority, in-flight behavior and adapter-specific reconciliation | Product owner / WP5 / Contract 12 |
| B17-GOV-07 | Distribution operation states/edges and provider-specific remote evidence | Contract 12 / WP6 / adapter owner |
| B17-GOV-08 | Map SMT-04/11–16/20 to Artifact 07 IDs, exact clauses, fixtures and evidence outputs | WP6 / QA owner |

No owner-reserved value is filled by this reconciliation.

## 10. Agent coordination and implementation readiness

- Qoder remains the sole writer for the current governance-closure milestone.
- OpenCode is read-only for the assigned API/backend architecture review.
- Copilot is limited to focused regression-test review.
- Kilo performs independent read-only QA/security acceptance only after implementation/evidence is complete.
- Antigravity remains paused unless a separate targeted UI task is authorized.

The companion prompt pack B-WP5-02 is prepared but not dispatched. Current authorization still prohibits agent execution and implementation. No agent prompt can override that boundary.

Future engineering readiness requires:
1. owner-approved detailed contract freeze for the affected behavior;
2. explicit task-specific implementation authorization;
3. exact repository/branch/revision and path-level ownership;
4. permitted commands and test environment;
5. named reviewer and acceptance authority;
6. no overlapping writer; Qoder sole writer for governance closure;
7. protected-action, rights, approval and authorization negative-test oracles mapped to Artifact 07/WP6.

## 11. Next execution sequence

1. B-WP1-04 — Batch 19 field/entity mapping against the four governance matrices.
2. B-WP5/6-05 — protected-action and acceptance-oracle crosswalk to Contract 12 and Artifact 07/WP6.
3. B-GOV-06 — consolidated owner-review pack, with explicit options and consequences.
4. B-QA-07 — independent freeze-readiness review.

**Current disposition:** B-WP5-03 identifies which Batch 17 governance sections contain explicit edges and which only define states/guards. It clarifies the CF-21 WITHDRAWN/REVOKED conflict without claiming a non-existent contradictory from→to edge. Batch 17 remains a candidate; no freeze or implementation authorization is granted.

END OF DOCUMENT
