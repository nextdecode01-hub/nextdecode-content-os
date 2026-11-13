# MOB-01 — Telegram Mobile Approval Owner Decision Matrix
## Proposal 0.1 — Decision aid only

**Document ID:** NEXTDECODE-INT-MOB01-OWNER-MATRIX-0.1
**Status:** OWNER DECISION AGENDA — NOT APPROVED
**Authority:** Subordinate to accepted P0 ADR/CF decisions, canonical contracts and Artifact 10.
**Implementation / test / provider activation:** NOT AUTHORIZED

## 1. Purpose and decision rules

This matrix turns MOB-DEC-01..07 from the MOB-01 security/interaction contract into explicit owner questions, neutral options and consequences. It does not select an option, freeze a contract, approve a Telegram transport or authorize implementation.

Authority/dependency handoff:
- Artifact 10 governs separate action authorization.
- Telegram Mobile Major-Approval Proposal 0.1 and MOB-01 Security & Interaction Contract 0.1 define the candidate product/security scope.
- CF-21 approval lifecycle and decision vocabulary remain open.
- CF-22 centralized authorization direction is accepted at a high level; detailed semantics remain open.
- GOV-09 is OPEN — no owner disposition recorded.
- API-LC-03/05/09, Contract 12 and WP1/WP2/WP3/WP5/WP6 dependencies remain open.
- Artifact 07 and REG-069 crosswalk control acceptance traceability; all tests remain NOT_RUN.

For every decision, the owner must record exact selected wording, rationale, rejected alternatives, affected sources, date/version and any required contract amendment. “Next”, a preference on another decision, or a general approval of the proposal is not a selection of a specific MOB-DEC option.

## 2. Decision summary

| ID | Decision | Primary dependency | Current status |
|---|---|---|---|
| MOB-DEC-01 | Identity pairing and recovery | Identity/session authority, WP3, security | **DECIDED — Option B selected (5 Nov 2026); detailed protocol remains open** |
| MOB-DEC-02 | First-slice major decision categories and no-response policy | CF-21, P0-A scope, product, risk/approval policy | **CONDITIONALLY SELECTED — Option C; operational parameters OPEN** |
| MOB-DEC-03 | Telegram identity attributes and binding | Identity contract, WP1/WP3 | OPEN |
| MOB-DEC-04 | Update transport | API-LC-09, runtime/security | OPEN |
| MOB-DEC-05 | Step-up authentication | Authentication policy, risk classification | OPEN |
| MOB-DEC-06 | Privacy, retention and message content | Privacy/security, data lifecycle | OPEN |
| MOB-DEC-07 | Idempotency and correlation semantics | API-LC-03/05, WP2, WP6 | OPEN |

## 3. Detailed owner decisions

### MOB-DEC-01 — Pairing and recovery

**Question:** How should the owner bind and recover the Telegram private account?

- A — Authenticated-session pairing: challenge initiated in authenticated Content OS session and claimed in private bot chat; recovery only through authenticated desktop session.
- B — Authenticated-session pairing plus independent step-up: same binding flow, with a second factor or fresh session confirmation for recovery and high-risk decisions.
- C — Defer mobile pairing: complete read-only notification design first; no decision callbacks until identity/recovery policy is approved.

Consequences: A is simpler but depends heavily on owner-session security; B adds friction and stronger recovery assurance; C reduces immediate risk but delays interactive approval.

**Guardrail:** username/display name alone is never identity proof. No Telegram-only recovery.

**Owner disposition:** **OPTION B SELECTED — 5 November 2026.** Authenticated-session pairing plus independent step-up verification for account recovery and high-risk decisions. The exact factor, risk classification and protocol remain open. See `03_P0_GOVERNANCE_AND_DECISIONS/02_OWNER_REVIEW_AND_AUTHORIZATION/NEXTDECODE_MOB_DEC01_Owner_Decision_Record_0.1.md` for the owner record.

### MOB-DEC-02 — Decision categories in first owner-only slice

**Question:** Which major decisions may be presented for owner action?

- A — Research/topic selection only.
- B — Research/topic selection and script/editorial review.
- C — Research/topic, script/editorial and final-video review.
- D — Notification-only first; defer all Telegram decision actions until a later owner-approved slice.

Consequences: A is narrowest; B adds editorial scope; C matches the current proposal's three candidate categories; D avoids mobile decision authority until the end-to-end contract is fully proven.

**Guardrail:** publishing authorization, actual upload/publication and platform account actions remain excluded from this decision.

**Owner disposition:** **OPTION C CONDITIONALLY SELECTED — 5 November 2026.** Scope includes research/topic selection, script/editorial review and final-video review, subject to the governed no-response/conditional auto-decision policy in `03_P0_GOVERNANCE_AND_DECISIONS/02_OWNER_REVIEW_AND_AUTHORIZATION/NEXTDECODE_MOB_DEC02_Conditional_Auto_Decision_Owner_Record_0.1.md` (REG-073). Auto-acceptance requires explicit owner enablement and an exact predefined owner-approved rule; prior explicit owner decisions may ground rules. AI confidence/similarity alone can never trigger approval. Critical, high-impact, uncertain, conflicting, rights-sensitive or policy-exception cases require human intervention; timeout can escalate but cannot bypass the human gate. Publishing authorization remains separate and excluded. Exact timeout windows, critical-case taxonomy, stage-specific eligibility matrix, rule lifecycle and audit schema remain OPEN; this is not operational or implementation authorization.

### MOB-DEC-03 — Telegram identity attribute

**Question:** Which Telegram-side identity attribute may be stored as a binding reference after authenticated pairing?

- A — Telegram numeric user identifier only, with private-chat context verified on every interaction.
- B — Numeric user identifier plus numeric private-chat identifier, both bound to the authenticated owner.
- C — Defer exact attribute representation to the canonical identity contract; prohibit implementation until WP1/WP3 define it.

Consequences: A minimizes stored identity attributes but requires strict context validation; B provides stronger chat-context binding with additional data handling; C avoids freezing physical fields prematurely.

**Guardrail:** username, display name, profile photo and user-supplied identity text are not authentication factors.

**Owner disposition:** OPEN. **Rationale / approved wording:** __________________________________

### MOB-DEC-04 — Telegram update transport

**Question:** Which transport should be evaluated for the first authorized non-production adapter?

- A — Long polling candidate: outbound worker, durable offset checkpointing and restart recovery; no inbound webhook receiver.
- B — Webhook candidate: HTTPS ingress, configured secret header, replay controls, key rotation and durable enqueue before acknowledgement.
- C — Keep transport unselected until runtime inventory and API-LC-09 security review compare both modes.

Consequences: A avoids inbound exposure but requires a continuously running worker; B can be event-driven but adds public ingress and authentication/replay responsibilities; C is safest while hosting/runtime constraints remain unknown.

**Guardrail:** this decision aid does not activate either transport. Webhook cannot be exposed while API-LC-09 remains open.

**Owner disposition:** OPEN. **Rationale / approved wording:** __________________________________

### MOB-DEC-05 — Step-up authentication

**Question:** Should Telegram account binding alone be sufficient for major decisions?

- A — Bound Telegram identity plus backend revalidation; no extra step-up for the approved low-risk major decision set.
- B — Require fresh authenticated Content OS confirmation for every decision callback.
- C — Risk-tiered: fresh step-up for decisions classified high-impact; other allowed decisions use bound identity plus backend revalidation.
- D — Defer all interactive decisions; notification-only until risk tiers and authentication policy are approved.

Consequences: A is low-friction but relies on device/account security; B is strongest but may reduce usability; C balances friction and assurance but requires approved risk classification; D narrows the initial capability.

**Owner disposition:** OPEN. **Rationale / approved wording:** __________________________________

### MOB-DEC-06 — Privacy, retention and message content

**Question:** What content may appear in Telegram and how should it be retained?

- A — Minimal notification only: category, non-sensitive reference and authenticated review link; no content preview.
- B — Minimal notification plus short non-sensitive summary; detailed artifact review only in authenticated Content OS.
- C — Permit a constrained preview only after privacy/security review defines allowed content classes, retention and deletion.
- D — Defer provider activation until privacy/data residency/retention review is complete.

Consequences: A minimizes exposure; B improves context but needs classification; C provides richer UX with higher review burden; D delays activation until governance is clearer.

**Guardrail:** no secrets, full scripts, unpublished video, private prompts, raw research dumps or credentials in chat by default.

**Owner disposition:** OPEN. **Rationale / approved wording:** __________________________________

### MOB-DEC-07 — Idempotency and correlation

**Question:** How should Telegram updates and callbacks relate to canonical command idempotency and correlation?

- A — Transport dedup only at adapter plus canonical command idempotency at backend; correlation follows API-LC-03/05 once resolved.
- B — Require a canonical interaction/request idempotency key for every decision callback; Telegram update ID is retained only as transport evidence.
- C — Defer exact envelope and dedup representation until API-LC-03/05 owner decisions; block implementation meanwhile.

Consequences: A preserves layered boundaries but depends on clear backend idempotency; B makes command replay control explicit but requires canonical request/key lifecycle; C avoids physical schema assumptions but delays implementation.

**Guardrail:** Telegram update ID is not a substitute for canonical request identity, causation or correlation. Event deduplication is not command idempotency.

**Owner disposition:** OPEN. **Rationale / approved wording:** __________________________________

## 4. Cross-decision invariants

Regardless of option:
- backend remains authoritative; Telegram cannot self-approve or grant authority;
- only one authenticated owner identity is in the initial scope;
- exact request, workspace, artifact/review version and current policy are revalidated server-side;
- stale, duplicate, expired, revoked, superseded and uncertain interactions fail closed;
- rights, quality, lifecycle and central authorization gates remain mandatory;
- content approval is distinct from publishing authorization;
- P0-A remains pre-distribution; public automatic publishing remains disabled;
- desktop review remains available as a fallback;
- no new canonical states, fields, IDs, FK or API envelope are frozen by this matrix.

## 5. Approval and implementation gates

1. Owner records each MOB-DEC disposition separately.
2. Relevant canonical contracts and API/Event decisions are reconciled and amended only under their own authority.
3. Security/privacy review validates pairing, recovery, transport, secrets, message content and retention.
4. REG-069 mapping is reviewed; MOB-A07-01..10 are closed, deferred or promoted through governed change.
5. Owner explicitly approves the bounded implementation work package and exact files/commands/environment under Artifact 10.
6. Tests require separate environment and execution authorization. No provider activation, deployment, upload or publishing follows implicitly.

**Current disposition (updated 5 November 2026):** MOB-DEC-01 Option B is selected and recorded (REG-072). MOB-DEC-02 Option C remains conditionally selected (REG-073); the owner has additionally selected **Path A** for MOB-RECON-01 (REG-073 §6; reconciliation REG-074): a separately governed automated workflow disposition may permit only an eligible internal transition within a previously authorized policy envelope and is NOT a human CF-21 ApprovalDecision or `APPROVED`. MOB-DEC-02 operational parameters and canonical representation remain OPEN. MOB-DEC-03..07 remain OPEN. GOV-09 remains OPEN. This matrix remains a decision aid; no canonical contract is amended/frozen and no implementation, tests, bot/token or provider activation is authorized.
