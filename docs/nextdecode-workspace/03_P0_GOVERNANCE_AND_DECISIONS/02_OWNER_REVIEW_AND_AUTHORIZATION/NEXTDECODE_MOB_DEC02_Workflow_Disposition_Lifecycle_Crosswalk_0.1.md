# MOB-DEC-02 — Workflow Disposition & Lifecycle Crosswalk
**Document ID:** NEXTDECODE-INT-MOB-DEC02-LIFECYCLE-XREF-0.1  
**Version:** 0.1  
**Date:** 5 November 2026 (Asia/Kolkata)  
**Status:** DOCUMENTATION-ONLY CROSSWALK — PATH A OWNER DISPOSITION RECORDED; CANONICAL MODEL OPEN  
**Related records:** REG-073, REG-074, MOB-RECON-01, GAP-041  
**Implementation / contract freeze:** NOT AUTHORIZED

## 1. Purpose
Map the Path A automated workflow-disposition concept against existing approval, governance, authorization and risk lifecycles. This crosswalk identifies safe conceptual boundaries and source dependencies. It does not create a canonical entity, state, enum, event, field, API, relationship cardinality or transition.

## 2. Source handoff and decision precedence
| Source | Relevant sections | Use / limitation |
|---|---|---|
| MOB-DEC-02 owner record 0.1 / REG-073 | §§1–6 | Owner principles and Path A disposition |
| MOB-DEC-02 canonical reconciliation 0.1 / REG-074 | §§3–7 | Path A boundary, risk and audit requirements |
| WP5 Governance State & Decision Matrices 0.1 | §§4–6 | ApprovalRequest remains separate; CF-21 outcomes and exact-version human attribution; CF-22 relationship open |
| Contract 07 1.0 | §§9–11, 13, 16 | GovernanceDecision, approval workflow, expiry/silence, publishing authorization, risk and audit |
| Policy & Authorization Decision Matrix 1.0 | §§2–3, 17–19 | Human owner approval, default-deny authorization, risk tiers and automation invariants |
| WP5 Governance & Authorization Contract Reconciliation 0.1 | §§3–7 | Separation of QA, rights, review, approval, authorization and execution |

Accepted decisions and canonical standards retain precedence over workstream candidates. A conceptual mapping in this document does not upgrade a candidate contract or resolve its open schema details.

## 3. Lifecycle separation crosswalk
| Existing concept | Source-backed purpose | Path A relationship | Boundary / unresolved item |
|---|---|---|---|
| QualityAssessment | Evaluates exact content/artifact against quality policy | Input evidence to eligibility evaluation | Hard blockers remain hard; QA does not approve |
| Rights assessment | Evaluates material for intended use | Input evidence and categorical exclusion | Unknown/pending/restricted/expired/revoked/denied cannot be treated as cleared |
| ReviewSnapshot | Records exact package/evidence shown to reviewer | May be referenced when prior human decisions ground a rule | Exact reference and persistence model remain source-dependent |
| ApprovalRequest | Requests a review; own lifecycle unresolved in WP5 §4 | May be the workflow context in which a no-response condition is observed | No request state or expiry semantics may be invented |
| CF-21 ApprovalDecision | Human decision on immutable exact scope/version | Remains independent; automated disposition cannot create or impersonate it | APPROVED remains human-attributable; accepted outcomes unchanged |
| Automated workflow disposition | Conceptual Path A policy result | May permit only a bounded internal transition already inside a previously authorized policy envelope | Canonical ownership, representation, actor class and transition catalogue OPEN |
| GovernanceDecision | Contract 07 central content eligibility decision | Must continue to evaluate policy, quality, rights, approval requirements and emergency state | Do not conflate with the proposed separate disposition; exact relationship requires reconciliation |
| CF-22 AuthorizationDecision | Central authorization for protected action | Required whenever the internal transition is a protected action | Default-deny/fail-closed; exact relationship to PublishingAuthorization remains GOV-09 OPEN |
| PublishingAuthorization | Short-lived scoped authorization for external publishing | Never produced by Path A disposition | Separate central gate and execution-time adapter validation |
| Execution / distribution outcome | Actual action attempt and external result | No external side effect is authorized by Path A | Must be recorded separately; unknown outcome requires reconciliation |

## 4. Candidate transition envelope — not an approved state machine
Path A allows consideration of an automated disposition only when every condition below is demonstrably satisfied:
1. The proposed transition is internal and non-public; it does not upload, publish, send externally, spend, accept terms, change security/permissions/policy or alter foundational controls.
2. The transition is already within a previously owner-authorized policy envelope; this document does not create that envelope.
3. Owner enablement and the exact applicable rule are authenticated, current and traceable.
4. Subject, artifact/review version, scope, workspace and relevant policy/rule versions are current and match the rule's allowed scope.
5. Required quality and rights evidence is present, current and free of hard blockers.
6. The stage-specific eligibility predicate is satisfied; absence of required evidence is not eligibility.
7. No mandatory human-intervention exclusion applies.
8. The disposition can be audited and safely reversed/contained within the pre-authorized internal scope; if reversibility/containment cannot be demonstrated, pause for human review.
9. Any protected action still obtains its own CF-22 authorization; the workflow disposition is not that authorization.

Failure or uncertainty in any condition means no automated progression; retain the existing safe pending/escalation behavior. Timeout alone is not a qualifying condition.

## 5. Stage mapping — questions for future policy, not eligibility approval
| MOB-DEC-02 stage | Candidate internal work that may be evaluated | Explicit exclusions / required separation |
|---|---|---|
| Research/topic selection | Continue bounded internal research organization, classification or queue preparation if already authorized | Does not authorize external outreach, paid data/provider use, publication, or skipping required human topic/editorial decision |
| Script/editorial review | Route, annotate or prepare a revision/review task within existing scope | Does not create human editorial approval, waive factual/rights/safety review, or approve a changed script/version |
| Final-video review | Preserve evidence, prepare internal review routing or safe hold state | Does not mark final video human-approved, waive artifact/hash/rights/quality checks, or authorize upload/publication |

These are illustrative candidate internal activities only. They are not owner-approved eligible transitions. WP-specific workflow contracts and the product owner must define the exact transition list and any human-required decision points before operational use.

## 6. Risk and exclusion mapping
Policy Matrix §17 defines R0–R5 autonomy tiers. Risk tiers determine controls; they do not grant permission. When classification is uncertain, use the stricter tier. The crosswalk does not assign final tiers to MOB-DEC-02 stages.

Mandatory human-intervention exclusions already carried by MOB-DEC-02 remain: critical/high-impact, uncertain, conflicting, rights-sensitive, safety-sensitive and policy-exception cases. Contract 07 §13 also requires consideration of claim criticality/uncertainty, rights/licence, personal data/privacy, safety/legal/reputational sensitivity, platform restrictions, commercial relationships, audience interaction, originality/derivative use, and approval/identity status.

Numeric risk scores or AI confidence cannot override categorical hard gates. Exact taxonomy, thresholds, stage mapping and any additional exclusions remain OPEN.

## 7. Minimum audit questions — no schema frozen
For each future disposition, the audit design must be able to answer:
- What exact subject, artifact/review version, hash, stage and internal transition were evaluated?
- Which authenticated owner enablement and exact rule/policy version applied?
- What deadline/timeout fact occurred, and when?
- Which eligibility predicates, exclusions, quality/rights evidence and source records were evaluated?
- Which prior explicit owner decision was referenced, if the approved rule depends on one?
- Was AI output used only as advisory evidence, separately from the authority basis?
- What disposition resulted, why, under which actor/authority class and correlation context?
- How were policy/rule changes, expiry/revocation, retries, failure, recovery and audit integrity handled?

These are audit questions, not field names. Event vocabulary, record ownership, retention, integrity, correlation and persistence remain OPEN.

## 8. Dependency register for subsequent reconciliation
| Dependency | Current finding | Required next action |
|---|---|---|
| WP5 ApprovalRequest lifecycle | Request state, withdrawal, expiry, resubmission and request/decision cardinality OPEN | Preserve distinction; do not attach automated disposition as an ApprovalDecision |
| CF-21 | Human approval exact-scope/version semantics accepted | No amendment needed for Path A; ensure any proposed linkage cannot impersonate a human |
| CF-22 / GOV-09 | Central authorization accepted; AuthorizationDecision / PublishingAuthorization relationship open | Reconcile separately; protected transitions remain default-deny |
| Contract 07 | GovernanceDecision and approval workflow defined; no Path A record type defined | Determine whether a separate disposition is needed and how it relates, under owner/schema authority |
| Unified Lifecycle / API-Event | Canonical state/event, version, correlation and idempotency dimensions remain governed by separate standards and open API-LC decisions | No new state/event/API from this crosswalk; obtain canonical mapping through WP1/API-Event decisions |
| Risk policy | R0–R5 autonomy tiers exist; MOB stage assignment and hard-gate taxonomy incomplete | Product/security/legal/QA define stage matrix and exclusion oracles |
| Audit / WP6 | Existing observability and audit requirements provide partial coverage; MOB-specific acceptance cases remain candidate | Map required evidence to existing Artifact 07/WP6 cases; identify true gaps without creating duplicate test IDs |
| Telegram security/privacy | SEC-MOB-01..09 remain open | No bot/token/provider activation until closure and separate authorization |

## 9. Acceptance checks for this documentation package
- Path A is represented as separate from human CF-21 ApprovalDecision.
- ApprovalRequest lifecycle remains unresolved and is not silently specified.
- CF-22 centralized authorization and PublishingAuthorization remain distinct from workflow progression.
- No new state, enum, field, event, API, entity cardinality or transition token is introduced.
- Candidate stage activities are clearly non-authoritative.
- Risk tiers are not misrepresented as permission grants.
- Open dependencies and authorization restrictions are explicit.

**Result:** Crosswalk is a documentation aid only. It resolves no schema or operational parameter. MOB-RECON-01 remains resolved at policy-boundary level; workflow-disposition representation and operational rules remain OPEN.

## 10. Authorization boundary
Documentation-only. No repository/source-code changes, tests, contract freeze, agent dispatch, Telegram bot/tokens/credentials/provider activation, deployment, spending, production generation, upload or publishing is authorized. Human approval before publishing, exact-version binding, central default-deny authorization, hard rights/quality/security gates and emergency controls remain in force.
