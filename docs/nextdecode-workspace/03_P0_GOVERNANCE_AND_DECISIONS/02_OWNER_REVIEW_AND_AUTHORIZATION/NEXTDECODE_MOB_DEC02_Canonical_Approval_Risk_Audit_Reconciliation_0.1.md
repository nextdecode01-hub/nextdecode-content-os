# MOB-DEC-02 — Canonical Approval, Risk & Audit Reconciliation
**Document ID:** NEXTDECODE-INT-MOB-DEC02-CANONICAL-RECON-0.1  
**Version:** 0.1  
**Date:** 5 November 2026 (Asia/Kolkata)  
**Status:** DOCUMENTATION RECONCILIATION — OWNER PATH A SELECTED; DETAIL/SCHEMA REVIEW OPEN  
**Scope:** MOB-DEC-02 / MOB-RECON-01; Telegram major-approval channel policy boundary  
**Implementation / contract freeze:** NOT AUTHORIZED

## 1. Purpose and authority
Record the owner's Path A disposition and reconcile conditional no-response handling against existing approval, risk, authorization and audit sources. This document clarifies boundaries; it does not amend canonical schemas or accepted contracts.

Owner disposition is recorded in `NEXTDECODE_MOB_DEC02_Conditional_Auto_Decision_Owner_Record_0.1.md`, §6. Path A means a permitted automated workflow disposition is distinct from human approval.

## 2. Source handoff and precedence
| Source | Version/status | Relevant authority |
|---|---|---|
| MOB-DEC-02 owner record | 0.1; owner disposition | Option C principles and selected Path A |
| Policy & Authorization Decision Matrix | 1.0; architecture specification | §2 explicit human approval; §3 default-deny; §4 principal authority; §18–20 automation and test invariants |
| Shared Intelligence Core Contract 07 | 1.0; working architecture contract | §9 GovernanceDecision; §10 approval; §10.3 timeout/silence; §11 publishing gate; §13 risk; §16 audit |
| WP5 Governance State & Decision Matrices | 0.1; working candidate, owner review required | §4 ApprovalRequest separation; §5 CF-21; §6 CF-22 |
| WP5 Governance & Authorization Contract Reconciliation | 0.1; design reconciliation | §§3–5 separation of QA, rights, review, approval, authorization and execution |
| MOB-DEC-01 security/interaction contract and review | 0.1; candidate/review | Pairing, recovery, callback, transport, privacy and audit blockers remain open |

Precedence remains the accepted owner decisions/ADRs/CFs and canonical standards first, then workstream candidates. This reconciliation cannot silently upgrade a candidate into an accepted contract.

## 3. Owner disposition and canonical resolution
**MOB-RECON-01: RESOLVED AT POLICY-BOUNDARY LEVEL BY OWNER PATH A.**

An owner-enabled, exact-rule automated disposition may permit only a bounded internal workflow transition already within a previously authorized policy envelope. It is not a CF-21 ApprovalDecision and is not `APPROVED`.

The following invariants remain:
- CF-21 `APPROVED` is attributable to an authenticated human decision-maker and exact immutable review scope/version (WP5 §§5.2–5.4).
- Contract 07 §10.3: expiry never implies approval; silence or owner unavailability never counts as consent; work requiring new approval pauses or uses a preapproved safe fallback; critical unresolved issues escalate.
- Policy Matrix §2: silence, inactivity, missed notifications and expired requests do not qualify as owner approval.
- AI confidence/similarity is advisory only and cannot grant authority.
- Missing, stale, conflicting or unverifiable evidence fails closed.
- An automated disposition cannot satisfy a required human approval, waive a hard gate, change scope/version, or authorize an external side effect.
- PublishingAuthorization remains separately issued by the central publishing gate and validated by the adapter at execution time (Contract 07 §11).

No new ApprovalDecision outcome, ApprovalRequest state, principal type, event, API, schema field or state-machine transition is introduced here.

## 4. Stage and risk boundary crosswalk
MOB-DEC-02 covers research/topic selection, script/editorial review and final-video review. Each stage still needs its own eligibility/exclusion rules; approval at one stage does not imply approval at another.

Contract 07 §13 provides risk factors, not a completed tier taxonomy. The factors include claim criticality/uncertainty, rights/licence, personal data/privacy, safety/legal/reputational sensitivity, platform restrictions, commercial relationships, audience interaction, originality/derivative use, and approval/identity status. Risk levels and thresholds must be centrally versioned; numeric scores cannot replace categorical hard gates.

For this reconciliation, the following are mandatory human-intervention exclusions carried from MOB-DEC-02: critical/high-impact, uncertain, conflicting, rights-sensitive, safety-sensitive and policy-exception cases. This is a protective exclusion, not a complete risk taxonomy. Exact definitions, thresholds, stage mapping and any additional exclusions remain OPEN. A timeout may notify/escalate but cannot bypass these gates.

## 5. Workflow disposition versus approval — conceptual distinction
| Concern | Meaning | Authority boundary |
|---|---|---|
| ApprovalRequest | Request for review; lifecycle remains unresolved in WP5 §4 | Does not itself approve |
| ApprovalDecision | Human decision on exact reviewed scope/version | CF-21 outcomes remain unchanged |
| Automated workflow disposition | Candidate separate policy/workflow result allowing a bounded internal transition | Path A owner disposition; canonical representation remains to be designed/approved |
| AuthorizationDecision | Central policy decision for a protected action | CF-22 centralized, default-deny/fail-closed |
| PublishingAuthorization | Scoped, short-lived grant for exact artifact/destination/action | Separate publishing gate; not created by workflow disposition |
| Execution/distribution outcome | What actually happened externally | Recorded separately; never inferred from approval or authorization |

This table is conceptual only. It does not establish entity cardinality, persistence shape, event names, transition tokens or API behavior.

## 6. Audit and evidence requirements to carry forward
Contract 07 §§9–10 and §16 require traceability across exact content/artifact and manifest hashes, QA/rights evidence, policy/identity versions, request/reviewer/decision/rationale, and publishing authorization issue/validation/use/expiry/revocation plus adapter outcomes.

For any future automated workflow disposition, the owner-record principles require evidence of:
- exact subject, version/hash, stage and intended internal transition;
- authenticated owner enablement state and applicable policy/rule identity/version;
- timeout/deadline event and relevant timestamps;
- exact eligibility/exclusion evaluation and source evidence;
- references to prior explicit owner decisions only where an approved rule explicitly relies on them;
- AI advisory output, if used, clearly distinguished from the authority basis;
- resulting workflow disposition, reason, actor class and audit correlation;
- revalidation, expiry/revocation, policy change and failure/recovery outcomes.

These are requirements to reconcile, not a frozen audit schema. Field names, event taxonomy, retention, integrity protection and correlation contracts remain OPEN.

## 7. Open dependencies — do not invent
1. Define and approve the canonical representation/owner of the separate workflow disposition.
2. Define which internal workflow transitions are eligible and prove they are within an already authorized policy envelope.
3. Define stage-specific eligibility and exclusions, plus critical/high-impact taxonomy.
4. Set timeout, reminder and escalation parameters; timeout never grants human approval.
5. Define rule identity, versioning, approval, activation/deactivation, rollback and in-flight behavior.
6. Define historical-decision matching, context equivalence, supersession and revocation handling.
7. Reconcile audit events/schema, retention, tamper evidence, correlation and recovery oracles.
8. Resolve ApprovalRequest lifecycle/cardinality and CF-22 AuthorizationDecision / PublishingAuthorization relationship independently; GOV-09 remains OPEN.
9. Close applicable Telegram security/privacy findings SEC-MOB-01..09 before any provider or bot activation.

## 8. Safe continuation sequence
1. Update owner-decision/control registers to reference Path A without changing CF-21 or Contract 07 semantics.
2. Produce a documentation-only conceptual crosswalk for the separate workflow disposition and existing lifecycle/authorization records.
3. Identify exact owner/schema/security decisions needed for any later contract amendment.
4. Submit unresolved operational parameters for owner review; no inferred defaults.
5. Only after separate authorization may implementation planning or execution be considered.

## 9. Authorization boundary
This reconciliation is documentation-only. It does not authorize repository/source changes, tests, contract freeze, agent dispatch, Telegram bot/tokens/credentials/provider activation, deployment, spending, production generation, upload or publishing. Human approval before publishing and all existing central authorization, rights, quality, exact-version, emergency and fail-closed controls remain in force.

**Disposition:** MOB-RECON-01 resolved at policy-boundary level by owner Path A; operational representation and parameters OPEN. MOB-DEC-03..07 OPEN. GOV-09 OPEN.
