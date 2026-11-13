# MOB-DEC-02 — Stage Risk & Eligibility Decision Aid
**Document ID:** NEXTDECODE-INT-MOB-DEC02-STAGE-RISK-0.1  
**Version:** 0.1  
**Date:** 5 November 2026 (Asia/Kolkata)  
**Status:** CANDIDATE OWNER / SECURITY / QA DECISION AID — NOT AN APPROVED POLICY  
**Related records:** REG-073..076, GAP-041, GAP-043, GAP-044  
**Implementation / contract freeze:** NOT AUTHORIZED

## 1. Purpose
Translate the owner's Path A principles into a stage-by-stage review aid for research/topic selection, script/editorial review and final-video review. This document makes the questions and hard exclusions visible; it does not enable automation, approve any transition, assign final R0–R5 tiers or define thresholds.

## 2. Governing invariants
- Path A automated workflow disposition is distinct from CF-21 human ApprovalDecision and cannot satisfy required human approval.
- Owner enablement and an exact owner-approved rule are necessary but not sufficient; the proposed action must also be within a previously authorized internal policy envelope.
- AI confidence, similarity, score or prediction cannot independently trigger a disposition.
- Silence, timeout, missed notification or owner unavailability never means consent.
- Rights, quality, safety, privacy, legal, security, policy and emergency hard gates cannot be bypassed.
- Changed artifact/version/scope/policy must be re-evaluated; no approval or eligibility carries forward by assumption.
- Protected actions still require their own central CF-22 authorization. PublishingAuthorization remains separate.
- If a condition is unknown, conflicting or unverifiable, fail closed to human review/escalation.

## 3. Risk factor inventory
Contract 07 §13 requires centrally versioned risk evaluation across:
1. Claim criticality and uncertainty.
2. Rights, licence, permissions and intended-use scope.
3. Personal data and privacy exposure.
4. Safety, legal and reputational sensitivity.
5. Platform restrictions.
6. Commercial relationships and sponsorship.
7. Audience interaction and potential harm.
8. Originality, attribution and derivative use.
9. Approval and identity assurance status.

Policy Matrix §17 defines R0 read-only, R1 reversible preparation, R2 bounded internal execution, R3 consequential internal change, R4 external/public or financial action, and R5 foundational/security authority. Tiers determine controls, not permission. Uncertainty raises the required tier. This aid does not assign a definitive tier to any MOB stage or action.

## 4. Cross-stage hard exclusions
The following require human intervention or block progression regardless of any score:
- Critical/high-impact or materially uncertain claims.
- Conflicting evidence, unresolved factual dispute or missing material evidence.
- Rights-sensitive, unclear, restricted, expired, revoked or denied rights.
- Safety-sensitive, legal, privacy or personal-data concern.
- Policy exception, platform restriction or unresolved commercial/sponsorship disclosure.
- Identity, owner enablement, rule version, artifact hash, scope or audit evidence cannot be verified.
- Material change to the content, assets, destination, use, applicable policy or review version.
- Active emergency pause or any hard quality/security/integrity blocker.
- Proposed action would send externally, publish/upload, spend, accept terms, alter permissions/security/policy or otherwise exceed the pre-authorized internal envelope.

These exclusions are protective carry-forwards from owner decisions and canonical sources, not a complete approved taxonomy.

## 5. Stage-by-stage decision aid
| Stage | Evidence that must be considered | Candidate bounded internal work (not approved eligibility) | Human-only / hard-stop cases | Questions still requiring owner/domain decision |
|---|---|---|---|---|
| Research/topic selection | Source quality, claim uncertainty/criticality, provenance, personal data, rights of research material, commercial context, audience/safety implications, identity/policy version | Internal queue organization, metadata normalization or research continuation only if already explicitly within authorized scope | Sensitive claims; uncertain/conflicting sources; private/personal data; rights restrictions; regulated/legal/safety themes; sponsorship or policy exception; topic selection requiring owner/editorial judgment | Which internal queue transitions are reversible and pre-authorized? Which topic categories are categorically human-reviewed? What evidence threshold is required? |
| Script/editorial review | Claim-to-source mapping, context/fairness, factual uncertainty, attribution, derivative/originality, rights and licence, privacy, safety/legal/reputation, commercial disclosure, exact script/version | Internal annotation, revision task creation or review routing within existing authorized scope | Material claim uncertainty/conflict; rights or attribution issue; personal data; legal/safety-sensitive framing; policy exception; any decision that constitutes editorial approval | What constitutes a material script change? Which review comments can be auto-routed versus require human disposition? How are prior explicit owner decisions matched to a new script/context? |
| Final-video review | Exact render/hash, script-to-video consistency, assets/manifest, rights/use scope, audio/visual claims, disclosures, privacy/safety, QA results, destination/use, policy/emergency state | Internal evidence collation, review routing or safe hold preparation only | Any artifact/hash mismatch; unreviewed asset; changed manifest; rights uncertainty; quality hard blocker; unsafe visual/audio content; disclosure/platform issue; any attempt to mark human-approved or proceed to upload/publish | Which final-render checks are hard gates? What evidence binds the reviewed render to its script/manifest? Which changes force a new human review? |

## 6. Proposed evaluation order — conceptual only
For each candidate stage, reviewers should be able to answer in order:
1. Is the actor/owner enablement authenticated, current and in scope?
2. Is the exact artifact/request/stage/version/hash identified?
3. Is the applicable rule/policy version explicit and previously owner-approved?
4. Are all required QA, rights, provenance and source evidence current?
5. Do any categorical hard exclusions apply?
6. Is the proposed transition internal, bounded, reversible/containable and previously authorized?
7. Does its risk classification permit the proposed autonomy under the central policy?
8. Is a separate CF-22 authorization required for the protected action?
9. Can the complete rationale and evidence be audited and recovered?
10. If any answer is unknown or false, does the workflow pause/escalate without treating silence as approval?

This sequence is a review checklist, not an executable policy algorithm or frozen transition guard.

## 7. Historical decision reuse guardrails
Prior explicit owner-approved decisions may inform a future owner-approved rule only where exact matching criteria are formally defined. Similarity alone is insufficient. The criteria must consider at minimum:
- Same decision subject and stage.
- Same material context, use and destination where relevant.
- Same content/artifact version lineage and relevant manifest/assets.
- Same applicable policy/rule version or an explicitly approved compatibility rule.
- No superseding, expired or revoked decision.
- No newly introduced uncertainty, rights, safety, privacy, legal, platform or commercial risk.
- Evidence that the prior decision was genuinely explicit and attributable to the owner.

Exact matching, supersession, revocation, version lineage and rule lifecycle remain OPEN; this aid does not authorize reuse.

## 8. Owner/security/QA decisions still required
1. Approve the categorical critical/high-impact taxonomy and stage-specific exclusions.
2. Define which candidate internal transitions, if any, are already within an authorized policy envelope.
3. Define material-change triggers and exact version/hash/manifest evidence for each stage.
4. Decide stage-specific human review requirements and reviewer roles.
5. Define how risk factors raise tiers and which hard gates are non-scoreable.
6. Define evidence sufficiency and missing/conflicting evidence behavior.
7. Define historical-decision matching and supersession/revocation behavior.
8. Map each future oracle to existing Artifact 07/WP6 cases; create new test IDs only through governed approval.
9. Close relevant SEC-MOB findings and API-LC dependencies before any operational design or activation.

## 9. Acceptance checks for this decision aid
- All three MOB-DEC-02 stages are covered.
- Contract 07 risk factors and Policy Matrix R0–R5 semantics are accurately distinguished.
- No final tier, threshold, eligible transition or auto-accept rule is invented.
- Human-only exclusions and fail-closed behavior are explicit.
- AI confidence and timeout cannot independently create consent or authority.
- Publishing authorization, central authorization and human ApprovalDecision remain separate.
- Open owner/security/QA decisions are enumerated.

**Result:** Stage-specific questions and protective exclusions are documented for owner/security/QA review. No operational eligibility is approved and no automation is enabled.

## 10. Authorization boundary
Documentation-only. No repository/source-code changes, tests, contract freeze, agent dispatch, Telegram bot/tokens/credentials/provider activation, deployment, spending, production generation, upload or publishing is authorized. Artifact 10 restrictions and all existing central authorization, human approval, rights, quality, exact-version and emergency controls remain in force.
