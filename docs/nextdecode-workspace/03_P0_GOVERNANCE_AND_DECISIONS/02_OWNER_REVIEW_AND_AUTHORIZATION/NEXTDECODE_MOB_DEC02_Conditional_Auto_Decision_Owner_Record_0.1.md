# NEXTDECODE MOB-DEC-02 — Owner Decision Record
**Document ID:** NEXTDECODE-INT-MOB-DEC-02-OWNER-RECORD-0.1  
**Version:** 0.1  
**Decision date:** 5 November 2026 (Asia/Kolkata)  
**Decision owner:** Product owner  
**Decision:** MOB-DEC-02 — First-slice major decision categories and conditional no-response handling  
**Status:** OPTION C CONDITIONALLY SELECTED — POLICY PRINCIPLES RECORDED; OPERATIONAL PARAMETERS OPEN  
**Authority:** Owner disposition for MOB-01 only; subordinate to accepted P0 decisions, canonical contracts and Artifact 10.

## 1. Exact owner disposition
The owner selected **Option C**, covering:
- research/topic selection;
- script/editorial review; and
- final-video review.

The selection is conditional on a governed no-response policy intended to prevent eligible workflow stages from remaining blocked indefinitely, without weakening human control over critical decisions.

## 2. Approved conditional auto-decision principles
1. **Explicit owner enablement:** Auto-approval/auto-accept must be an explicit owner-controlled setting. When disabled, timeout never creates approval; the request remains pending or is escalated under the approved human-intervention process.
2. **Bounded no-response handling:** When enabled, a request may be considered for automatic acceptance only after its separately configured response window has elapsed. Exact timeout durations and escalation schedule are not selected by this record.
3. **Pre-authorized eligibility only:** Automatic acceptance is permitted only where a predefined, owner-approved rule explicitly covers the decision category and current case. Absence of a matching rule means no automatic acceptance.
4. **Historical-decision grounding:** Prior explicit owner-approved decisions may be used as reference evidence for a matching rule. The system must not infer a new approval rule merely from patterns, frequency or implicit behavior.
5. **AI is advisory, not an authority:** AI may assess similarity, confidence and rule-match evidence, but AI confidence, score or prediction alone must never trigger approval or auto-acceptance. The governing rule and owner-authorized policy must independently permit the action.
6. **Critical cases require a human:** Critical, high-impact, uncertain, conflicting, rights-sensitive, safety-sensitive or policy-exception cases must wait for human intervention. Timeout may trigger escalation/notification but cannot bypass the human gate.
7. **Stage-specific boundaries:** Research/topic, script/editorial and final-video decisions must have separately defined eligibility and risk rules. Approval at one stage does not imply approval at another.
8. **Publishing remains separate:** This decision does not authorize upload, distribution, publication or any PublishingAuthorization. All existing central authorization, rights, quality, lifecycle and protected-action gates remain mandatory.
9. **Auditability and fail-closed behavior:** Every automatic decision must record the applicable policy/rule version, owner enablement state, timeout event, matching prior owner decision references, eligibility evidence, AI advisory output if used, decision reason and resulting state. Missing, stale, conflicting or unverifiable evidence fails closed to human review.
10. **No silent scope expansion:** The policy cannot approve a new category, waive required review, override a revocation, accept stale artifact versions or bypass exact request/artifact/version/policy revalidation.

## 3. What is selected and what remains open
**Selected conditionally:** Option C and the policy principles in §2.

**Still open and required before operational use:**
- exact timeout durations, reminders and escalation intervals;
- the stage-by-stage eligibility matrix and explicit excluded categories;
- the formal definition and owner approval of critical/high-impact cases;
- the rule representation, versioning, activation/deactivation and rollback controls;
- minimum evidence and matching criteria for prior explicit owner decisions;
- treatment of conflicting, superseded, revoked or contextually different historical decisions;
- audit event/schema and canonical state transitions;
- how the owner enables/disables the feature and how setting changes take effect for in-flight requests;
- security, privacy, acceptance-test and failure-recovery evidence.

No default timeout, confidence threshold, automatic rule or risk classification is invented by this record.

## 4. Invariants and authority boundary
- Content OS backend and central governance remain authoritative; Telegram is only an interaction/notification interface.
- Human approval remains the default unless the owner explicitly enables the governed feature and an exact pre-authorized rule applies.
- Critical cases always require human intervention.
- AI cannot independently grant approval.
- Research/script/final-video approval remains distinct from publishing authorization.
- Rights, quality, lifecycle, exact-version and central authorization checks remain mandatory.
- GOV-09 remains OPEN and is not decided by this record.
- MOB-DEC-01 Option B remains selected; this record does not change its identity/step-up direction.

## 5. Authorization boundary
This record does **not** authorize:
- Telegram bot creation, tokens, credentials or transport/provider activation;
- repository/source-code changes, tests or contract/schema/API/event freeze;
- agent dispatch;
- deployment, spending, production generation, upload or publishing.

Any such action requires separate explicit authorization under Artifact 10 and all applicable project gates.

**Recorded disposition:** MOB-DEC-02 Option C — CONDITIONALLY SELECTED, subject to §2; operational parameters and implementation remain OPEN.  
**MOB-DEC-03..07:** OPEN.  
**GOV-09:** OPEN — no owner disposition recorded.

[executed on device: Anish (45b43f72-8ac0-4429-8be6-36afb8b5226a)]

## 6. Canonical reconciliation owner disposition — Path A
**Disposition date:** 5 November 2026 (Asia/Kolkata)  
**Decision reference:** MOB-RECON-01  
**Selected path:** **PATH A — AUTOMATION IS A SEPARATE WORKFLOW/POLICY DISPOSITION, NOT HUMAN APPROVAL.**

The owner selects Path A for reconciliation with CF-21, Contract 07 and the central Policy & Authorization Decision Matrix:

1. A narrowly scoped, owner-enabled and rule-governed automated disposition may permit an eligible, pre-authorized **internal workflow transition** within an already approved policy envelope.
2. Such an automated disposition MUST NOT be represented as CF-21 `ApprovalDecision: APPROVED`, MUST NOT populate or impersonate a human decision-maker, and MUST NOT satisfy a required human ApprovalDecision.
3. Human approval remains explicit, authenticated, attributable and bound to the exact immutable review scope/version. Silence, inactivity, missed notification, timeout or expiry is never human consent.
4. Automation cannot override a hard quality, rights, privacy, safety, legal, security or policy gate; cannot waive a required human review; cannot authorize a new scope; and cannot carry approval across changed/stale versions.
5. AI similarity, confidence, score or prediction may be advisory evidence only; it cannot independently trigger a disposition or create authority.
6. Publishing authorization remains a separate central decision. This disposition grants no upload, distribution, publication, account or adapter permission. Human approval and all existing central authorization, rights, quality, exact-version and emergency-state gates remain mandatory wherever required.
7. Where the internal workflow transition cannot be proven to fall within a previously owner-authorized policy envelope, or where evidence is missing, stale, conflicting or uncertain, the workflow fails closed to pending human review/escalation.

**Canonical effect:** This owner disposition resolves MOB-RECON-01 at the policy-boundary level without amending CF-21 or reinterpreting Contract 07's human approval semantics. It does not define a new entity, state token, event, schema field, API, enum or transition.

**Still open before operational use:** canonical representation and ownership of the separate workflow disposition; permitted internal transitions; rule identity/version/lifecycle; exact eligibility and exclusion matrix; risk/critical taxonomy; timeout and escalation parameters; historical-decision matching; in-flight setting changes; audit event/schema; recovery and acceptance evidence. These require source reconciliation and any necessary subsequent owner/schema/security decisions.

**Authorization boundary unchanged:** documentation-only work remains the only authorized activity under the current instruction. No contract freeze, implementation, repository/code/test changes, agent dispatch, Telegram bot/token/provider activation, deployment, spending, production generation, upload or publishing is authorized.

**MOB-DEC-03..07:** OPEN. **GOV-09:** OPEN.
