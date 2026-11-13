# NEXTDECODE P0 — WP5 Governance State & Decision Matrices

**Document ID:** NEXTDECODE-P0-WP5-GOV-MATRIX-0.1  
**Version:** 0.1  
**Date:** 2026-11-04  
**Status:** WORKING CANDIDATE — OWNER REVIEW REQUIRED  
**Work package:** B-WP5-02  
**Implementation status:** NOT AUTHORIZED  
**Agent dispatch status:** NOT AUTHORIZED  
**Contract freeze:** NOT GRANTED

---

## 1. Purpose and decision labels

This documentation-only package separates four governance concerns:

1. CF-20 RightsDetermination / AssetRightsRecord.
2. ApprovalRequest lifecycle.
3. CF-21 ApprovalDecision.
4. CF-22 AuthorizationDecision / PublishingAuthorization relationship.

Labels used below:
- ACCEPTED: explicit accepted ADR/CF or owner decision.
- SOURCE-DEFINED: required by a canonical source, but not necessarily a frozen implementation detail.
- CANDIDATE: present in a working document and not frozen.
- OPEN: unresolved or conflicting; requires evidence or owner/schema/security/legal disposition.
- NOT AUTHORIZED: no permission to implement, migrate, test live systems, dispatch agents or perform external actions.

Non-negotiable separations:
- QA result ≠ rights determination.
- Rights determination ≠ human approval.
- ApprovalRequest lifecycle ≠ ApprovalDecision outcome.
- Approval ≠ centralized authorization.
- Authorization ≠ execution.
- Local execution result ≠ confirmed external outcome.
- A candidate state token does not become accepted merely by repetition.

## 2. Authority and dependency review

| Source | Version/status | Use |
|---|---|---|
| Accepted P0 Architecture Decision Baseline | 1.0; accepted ADR-001..010 | Governing architecture, especially ADR-007/008/009/010 |
| Artifact 08 Implementation Reference / Accepted Contract Decisions | 1.0; accepted reference | CF-20, CF-21, CF-22 |
| Contract 07 | 1.0; working architecture contract | Governance-domain source requiring reconciliation |
| WP5 Governance, Quality, Rights & Authorization | 0.1; design candidate | Consolidated baseline and open details |
| Data Dictionary & Entity Ownership Registry | 1.1; working standard | Working canonical entity/field registry; not frozen |
| Batch 17 State-Machine & Transition Catalogue | candidate; not frozen | Candidate state, outcome and guard catalogue |
| Batch 19 Database Schema, ERD & Persistence Specification | candidate; not frozen | Candidate persistence model; no schema freeze |
| Contract 07 / Batch 17 / Batch 19 Crosswalk | 0.1; working evidence | Prior B-WP5-01 reconciliation |
| Agent Operating Protocol | 0.1.0-draft | Task boundaries and agent roles |
| Artifact 09 Coding-Agent Handoff Specification | 1.0; draft | Engineering handoff preconditions; not execution authorization |

Accepted baseline carried forward:
- CF-20 / ADR-009: Contract 07 owns canonical rights assessment; evidence-backed and use-specific; accepted states UNKNOWN, PENDING_REVIEW, CLEARED, RESTRICTED, EXPIRED, REVOKED, DENIED.
- CF-21: Contract 07 / Central Governance owns human approval; immutable review package; attributable decision bound to exact reviewed version and scope; accepted outcomes APPROVED, REJECTED, CHANGES_REQUESTED, EXPIRED, REVOKED.
- CF-22 / ADR-007: Option A, centralized authorization; default-deny, fail-closed, least privilege, exact action/resource/version/destination binding, expiry/revocation; no competing domain-local authority.
- ADR-010: separate lifecycle state machines.
- Human approval before publishing remains required; automatic public publishing remains disabled.
- No implementation, agent execution, repository changes, tests, dependency/environment changes, provider activation, deployment, production generation, upload or publishing without separate explicit authorization.

## 3. Matrix A — CF-20 RightsDetermination

### 3.1 Record and ownership

| Element | Source evidence | Disposition |
|---|---|---|
| Domain owner | Contract 07 owns canonical rights assessment | ACCEPTED |
| Working entities | Data Dictionary v1.1 §12.2 AssetRightsRecord; Batch 19 RightsEvidence / RightsDetermination | Entity mapping OPEN |
| Evidence | Source, licence/permission, rights holder, permitted/prohibited uses and evidence references | SOURCE-DEFINED |
| Subject | Asset or ArtifactVersion; exact version where relevant | SOURCE-DEFINED; relationship/cardinality OPEN |
| Scope | Intended use, platform/destination, territory, time, commercial context, modification/attribution | ACCEPTED principle; exact requiredness OPEN |
| Canonical field | Data Dictionary uses rights_status; Batch 19 uses rights_state | CONFLICT CONFIRMED |
| History | Append-oriented evidence/determinations; preserve history | SOURCE-DEFINED direction; supersession model OPEN |

### 3.2 Accepted vocabulary

| Token | Meaning / effect | Source |
|---|---|---|
| UNKNOWN | Rights not established; fail closed for protected use | CF-20; WP5 §3; Batch 17 SM-11 |
| PENDING_REVIEW | Evidence submitted but undecided; fail closed / hold | CF-20; WP5 §3; Batch 17 SM-11 |
| CLEARED | Evidence supports specified use/scope; prerequisite only for exact context | CF-20; WP5 §3; Batch 17 SM-11 |
| RESTRICTED | Use limited by conditions; restrictions and separate authorization still apply | CF-20; WP5 §3; Batch 17 SM-11 |
| EXPIRED | Clearance validity ended; fail closed pending renewal/review | CF-20; WP5 §3; Batch 17 SM-11 |
| REVOKED | Prior clearance withdrawn; fail closed and invalidate dependent assumptions | CF-20; WP5 §3; Batch 17 SM-11 |
| DENIED | Use explicitly denied; protected use denied | CF-20; WP5 §3; Batch 17 SM-11 |

Legacy Contract 07 tokens PENDING_VERIFICATION and PROHIBITED are not silently aliased. Historical interpretation, backfill or migration requires a separate explicit decision.

### 3.3 Transition and guard matrix

| Transition/event | Evidence currently available | Unresolved detail |
|---|---|---|
| Evidence received / assessment opened | Data Dictionary captures evidence refs; Batch 17 defines PENDING_REVIEW | Command/event, actor, validation and initial-state edge OPEN |
| Assessment to CLEARED | CF-20 defines outcome and exact-use effect | Evidence threshold, authority and edge OPEN |
| Assessment to RESTRICTED | CF-20 defines conditional use | Restriction schema, evaluation and edge OPEN |
| Assessment to DENIED | CF-20 defines explicit denial | Decision authority, appeal/review and edge OPEN |
| Active clearance to EXPIRED | Batch 17 SM-11 says validity ended and fail closed | Expiry trigger, clock, scheduler and edge OPEN |
| Active clearance to REVOKED | Batch 17 SM-11 says prior clearance withdrawn and fail closed | Revocation authority, reason, effective time and dependent-record handling OPEN |
| Reassessment | Evidence-backed reassessment; Batch 17 preserves determination history | New record vs state transition and trigger OPEN |
| Rights change after approval | WP5 §3 says changed rights may require re-review | Exact invalidation/reapproval behavior OPEN |

### 3.4 Owner/schema decisions

1. Confirm canonical field name: rights_status or rights_state.
2. Confirm whether AssetRightsRecord and RightsDetermination are the same aggregate, linked records or distinct record types.
3. Confirm relationships/cardinality among RightsEvidence, AssetRightsRecord and RightsDetermination.
4. Define who may issue, expire, revoke and deny determinations, including legal-review escalation.
5. Define validity/time semantics and how changed rights invalidate downstream approval/authorization.
6. Define legacy token treatment only if a separately authorized migration is planned.

No new rights enum, alias, transition edge or physical column is introduced here.

## 4. Matrix B — ApprovalRequest lifecycle

### 4.1 Critical distinction

CF-21 defines ApprovalDecision outcomes. It does not, in the accepted evidence inspected for this package, define a complete ApprovalRequest lifecycle enum. A request being closed, cancelled or withdrawn is not itself a reviewer decision and must not be stored as a CF-21 ApprovalDecision outcome.

### 4.2 Record fields and evidence

| Element | Source evidence | Disposition |
|---|---|---|
| Entity | Data Dictionary v1.1 §12.4 defines ApprovalRequest separately from ApprovalDecision | SOURCE-DEFINED |
| Identity | approval_request_id | SOURCE-DEFINED |
| Subject | subject_entity_type, subject_entity_id, subject_version_id | SOURCE-DEFINED |
| Action | requested_action | SOURCE-DEFINED |
| Destination | destination_context | SOURCE-DEFINED |
| Policy | policy_version | SOURCE-DEFINED |
| Expiry | expires_at | SOURCE-DEFINED field; lifecycle behavior OPEN |
| Requester | requested_by | SOURCE-DEFINED |
| Request state / enum | Not defined in inspected Data Dictionary §12.4 | OPEN |
| Reviewer assignment/queue | Contract 07 §10.1 describes assigned reviewer/role; detailed assignment/queue lifecycle is not fully defined | SOURCE-DEFINED concept; workflow details OPEN |
| Withdrawal | Contract 07 v1.0 uses WITHDRAWN among approval outcomes; CF-21 does not | CONFLICT; request semantics OPEN |
| Decision link | ApprovalDecision includes approval_request_id | SOURCE-DEFINED; cardinality/history OPEN |

### 4.3 Lifecycle facts versus lifecycle states

| Fact/event | Evidence | Safe statement |
|---|---|---|
| Request created/submitted | ApprovalRequest has requested_by and subject/action | Request record exists; no canonical state token established |
| Review opened | Batch 17 SM-12 requires reviewer role/access for exact version | Candidate event/guard; request-state mapping OPEN |
| Decision recorded | Batch 17 SM-12 requires authenticated actor, reason/evidence/version | Creates separate ApprovalDecision; request transition OPEN |
| Request expires | ApprovalRequest has expires_at | Field exists; distinct from ApprovalDecision EXPIRED? OPEN |
| Request withdrawn/closed | Legacy Contract 07 WITHDRAWN conflicts with CF-21 | No accepted request state or withdrawal behavior may be inferred |
| Request resubmitted | Not defined in inspected accepted sources | OPEN; new request vs reopen undecided |
| New subject version | CF-21 exact-version binding; Batch 17 says new version requires review | Old decision does not carry forward; request treatment OPEN |

### 4.4 Prohibited assumptions

- Do not add WITHDRAWN to ApprovalDecision.
- Do not automatically substitute REVOKED for request withdrawal.
- Do not assume request withdrawal revokes an already-recorded decision.
- Do not assume request expiry and decision expiry are the same fact.
- Do not invent a request enum such as DRAFT/SUBMITTED/IN_REVIEW/CLOSED.
- Do not infer one-to-one or one-to-many request/decision cardinality.

### 4.5 Owner decisions required

1. Is request withdrawal/closure supported?
2. Which actor may withdraw/close a request, when and with what reason/evidence?
3. What happens if a decision already exists?
4. Is request expiry separate from decision expiry?
5. Can one request receive multiple decisions/reviews, or must each review cycle create a new request?
6. What happens after CHANGES_REQUESTED or a new subject version?
7. What lifecycle facts and history must persist?

Keep request lifecycle OPEN and ApprovalRequest / ApprovalDecision separate until decided.

## 5. Matrix C — CF-21 ApprovalDecision

### 5.1 Record and binding

| Element | Source evidence | Disposition |
|---|---|---|
| Domain owner | Central Governance / Contract 07 | ACCEPTED |
| Entity | ApprovalDecision, separate from ApprovalRequest | SOURCE-DEFINED |
| Identity | approval_decision_id | SOURCE-DEFINED |
| Request link | approval_request_id | SOURCE-DEFINED; cardinality OPEN |
| Subject/version | subject_version_id and exact reviewed scope | ACCEPTED invariant |
| Immutable review package | CF-21 requires immutable snapshot | ACCEPTED invariant |
| Content/artifact/manifest versions | Exact version references required | ACCEPTED invariant |
| Checksum | Exact checksum binding required | ACCEPTED invariant |
| Persisted package/version/checksum fields | Not fully defined in Data Dictionary v1.1 §12.4 | OPEN; do not invent fields |
| Actor/time/reason | decided_by, decided_at, reason | SOURCE-DEFINED |
| Attestation | signature_or_attestation_ref where supported | SOURCE-DEFINED optionality; proof mechanism OPEN |

### 5.2 Accepted outcomes

| Token | Meaning/effect | Source |
|---|---|---|
| APPROVED | Human accepts exact reviewed scope/version; prerequisite only within scope/validity | CF-21; WP5 §3; Batch 17 SM-12 |
| REJECTED | Human rejects exact scope/version; no protected permission | CF-21; WP5 §3; Batch 17 SM-12 |
| CHANGES_REQUESTED | Revision required; new version/review cycle as policy defines | CF-21; WP5 §3; Batch 17 SM-12 |
| EXPIRED | Approval validity ended; no longer satisfies prerequisite | CF-21; WP5 §3; Batch 17 SM-12 |
| REVOKED | Approval decision withdrawn/revoked; dependent action re-evaluated | CF-21; WP5 §3; Batch 17 SM-12 |

WITHDRAWN is not an accepted CF-21 ApprovalDecision outcome.

### 5.3 Decision/event/guard matrix

| Decision/event | Supported guard/rule | Unresolved detail |
|---|---|---|
| Review opened | Reviewer role/access valid for exact version | Reviewer role matrix, assignment, delegation and request linkage OPEN |
| Decision recorded | Actor authenticated; reason/evidence/version recorded | Permitted transitions and cardinality OPEN |
| APPROVED | Exact immutable reviewed scope/version; hard QA blockers cannot be bypassed | Validity duration, conditions and destination-change re-review OPEN |
| REJECTED | Exact scope/version rejected | Appeal/re-review and request closure OPEN |
| CHANGES_REQUESTED | Revision required; new version/review cycle as policy defines | Same request vs new request; transition guards OPEN |
| Approval expired | Validity window or policy condition reached | Clock, scheduler, exact edge and precedence OPEN |
| Approval revoked | Authorized revocation role and reason | Role matrix, effective time and downstream invalidation OPEN |
| New version created | Old approval remains bound to old version; new version requires review | Automated invalidation/event linkage OPEN |

### 5.4 Invariants and owner/schema decisions

- Approval is attributable to a human decision-maker and exact immutable review scope.
- Changed versions do not inherit approval automatically.
- Approval cannot override a hard QA blocker.
- Approval is not centralized authorization and cannot directly trigger external execution.
- Changed rights, destination or policy may require re-review; exact triggers remain OPEN.
- Historical decisions remain auditable; no destructive overwrite is implied.

Owner/schema decisions:
1. Review-package identity/version representation.
2. Exact links to content, artifact and manifest version IDs.
3. Checksum algorithm/value/reference and verification timing.
4. Request-to-decision cardinality, uniqueness and multi-review history.
5. Reviewer roles, delegation, expiry, revocation and appeal/re-review authority.
6. Changed rights/destination/policy invalidation triggers.
7. Attestation/signature requirements by decision class.

## 6. Matrix D — CF-22 AuthorizationDecision

### 6.1 Authority and record-model conflict

| Element | Source evidence | Disposition |
|---|---|---|
| Authority | CF-22 explicitly accepted Option A: centralized authorization | ACCEPTED |
| Enforcement | APIs, studios, workers and adapters enforce central decision; default deny/fail closed | ACCEPTED |
| Scope | Exact actor/action/resource/version/destination/policy/time context | ACCEPTED invariant |
| Entity | Data Dictionary v1.1 §5 and Batch 19 list AuthorizationDecision | SOURCE-DEFINED working entity |
| PublishingAuthorization | Data Dictionary v1.1 §12.5 separately defines PublishingAuthorization | SOURCE-DEFINED working entity |
| Relationship | Batch 19 does not establish whether evaluation/decision and issued grant are one or linked records | OPEN |
| Canonical identity | No accepted decision resolves one-record vs linked-record model | OPEN |
| Execution relation | Contract 07/12 require adapter enforcement before external side effects | ACCEPTED boundary; persistence details OPEN |

### 6.2 Candidate conceptual states — NOT FROZEN

Batch 17 SM-13 lists these conceptual states. CF-22 accepts centralized authorization and its invariants; it does not freeze this entire enum set.

| Candidate token | Batch 17 meaning/enforcement | Status |
|---|---|---|
| NOT_EVALUATED | No decision exists; default deny | CANDIDATE |
| DENIED | Policy evaluation denied; protected action prohibited | CANDIDATE representation of accepted deny behavior |
| AUTHORIZED | Current decision permits exact bound action; proceed only while bindings valid | CANDIDATE representation of scoped authorization |
| EXPIRED | Validity ended; deny and re-evaluate | CANDIDATE |
| REVOKED | Decision withdrawn; deny and re-evaluate | CANDIDATE |
| INVALIDATED | Bound input changed; deny and obtain fresh decision | CANDIDATE |

Do not present these labels as an owner-frozen canonical authorization enum.

### 6.3 Authorization binding and enforcement

| Binding/guard | Accepted requirement | Execution-time implication |
|---|---|---|
| Actor identity/trust | Actor identified and trusted for action | Validate current identity and authority |
| Action | Exact requested operation | No broad wildcard grant inferred |
| Resource/version | Exact target and immutable version | Mismatch denies/re-evaluation required |
| Destination/account | Exact platform/account/destination where relevant | Destination change invalidates prior scope |
| Policy version | Policy context bound | Re-evaluate if applicable policy changes |
| Time validity | Expiry enforced | Expired authorization denies |
| Approval | Required human approval current and exact-version bound | Approval remains prerequisite, not grant |
| Rights | Use-specific rights remain applicable | Unknown/pending/expired/revoked/denied rights fail closed for protected use as applicable |
| Quality | BLOCKED and hard blockers prevent protected action | Ordinary approval cannot bypass |
| Emergency pause | Current pause state permits execution | Pause denies new protected action; in-flight semantics adapter-specific |
| Worker/adapter capability | Executing identity has permitted capability | Agent delegation cannot expand authority |
| Revocation | Revocation enforced centrally | Propagation, cache and race semantics OPEN |

### 6.4 Owner/schema decisions required

1. Is AuthorizationDecision the policy evaluation result, issued grant, or linked to a separate PublishingAuthorization?
2. If two records exist, which is authoritative, how linked, and which is presented to adapters?
3. How does PublishingAuthorization bind ApprovalDecision, exact subject version, distribution package version and channel account?
4. Is a grant consumed once or reusable during validity? Idempotency/consumption rules OPEN.
5. What are expiry/revocation propagation and execution-time revalidation requirements?
6. How are emergency pause and in-flight operations reconciled by adapter?
7. Which protected-action catalogue and reason-code vocabulary are in P0?

No competing authorization authority or grant model is selected here.

## 7. Cross-matrix invariant checks

| ID | Required invariant | Coverage |
|---|---|---|
| GOV-01 | Rights do not imply approval | A, C |
| GOV-02 | Request lifecycle is not decision outcome | B, C |
| GOV-03 | WITHDRAWN is not silently treated as REVOKED | B, C |
| GOV-04 | Exact immutable review-package/version/checksum binding | C |
| GOV-05 | Approval does not grant authorization | C, D |
| GOV-06 | Authorization does not prove execution/external success | D |
| GOV-07 | Missing/ambiguous governance facts fail closed for protected actions | A, B, C, D |
| GOV-08 | Hard QA blockers cannot be bypassed by ordinary approval | C, D |
| GOV-09 | No universal in-flight cancellation guarantee is inferred | D |
| GOV-10 | Candidate enum/schema detail is not promoted to accepted/frozen | A, B, C, D |

## 8. Agent coordination and handoff readiness

Current Agent Operating Protocol 0.1.0-draft and Agent Workstream Matrix preserve:
- Qoder: Phase 11 engineering owner / sole writer for the current governance-closure milestone.
- OpenCode: Phase 10 engineering/closure owner; read-only API/backend architecture review where assigned.
- Kilo: independent read-only QA/security acceptance after implementation is complete.
- Copilot: focused regression-test review suggestion only.
- Antigravity: targeted product/UI review suggestion only; remain paused unless separately assigned.

These are role boundaries, not new task assignments. Current owner-review record and Artifact 09 state that implementation and agent execution are NOT AUTHORIZED. This package prepares handoff readiness only; no agent is dispatched.

Companion copy-paste prompts, exact inputs, outputs, permissions, stop conditions and sequencing:
06_AGENT_HANDOFFS/NEXTDECODE_P0_WP5_Governance_Matrix_Agent_Handoff_Prompts_0.1.md

## 9. Acceptance criteria for B-WP5-02

- Four concerns are separately modelled: rights, ApprovalRequest lifecycle, ApprovalDecision and authorization.
- Accepted tokens are sourced to CF-20/CF-21/CF-22 and canonical documents.
- Batch 17 authorization labels are marked candidate/not frozen.
- ApprovalRequest lifecycle remains OPEN; no new request enum is invented.
- WITHDRAWN is not added to CF-21 outcomes or silently replaced.
- Immutable review-package/content/artifact/manifest/checksum binding is stated as accepted; field representation remains OPEN.
- AuthorizationDecision / PublishingAuthorization relationship remains OPEN.
- Supported guards are distinguished from missing transition edges.
- Owner decisions, dependencies and implementation prerequisites are explicit.
- Agent roles and authorization restrictions are preserved.
- No source contract, accepted decision, Batch 17 or Batch 19 candidate is modified.
- No implementation, agent dispatch, tests, migration, release or production evidence is claimed.

## 10. Open dependencies

- GAP-015: Contract 07 CF-21 approval/request separation and WITHDRAWN/REVOKED conflict.
- GAP-016: emergency pause and in-flight external action.
- GAP-018: Contract 12 publishing authorization and operation boundary.
- GAP-022: WP1–WP6 exact clause-level traceability.
- GAP-023: Batch 17–26 cross-cutting reconciliation.
- GAP-024: Batch 20/25 security overlap.
- GAP-026: Artifact 07 ↔ WP6 test-level traceability.
- GAP-027: Contract 07 / Batch 17 / Batch 19 crosswalk follow-through.
- New field/entity mapping work: Batch 19 rights_state/rights_status, ApprovalRequest mapping, package/checksum representation and authorization entity mapping.

## 11. Next sequence

1. B-WP5-03: Batch 17 transition-edge reconciliation using these four matrices.
2. B-WP1-04: Batch 19 field/entity mapping against Data Dictionary v1.1.
3. B-WP5/6-05: protected-action and negative acceptance mapping to Contract 12 and Artifact 07/WP6.
4. B-GOV-06: consolidated owner-review pack, presenting choices without selecting owner-reserved options.
5. B-QA-07: independent freeze-readiness review.

**Current disposition:** B-WP5-02 is a working candidate for owner review. No governance state machine, request lifecycle, physical schema, contract or implementation task is frozen or authorized.

END OF DOCUMENT
