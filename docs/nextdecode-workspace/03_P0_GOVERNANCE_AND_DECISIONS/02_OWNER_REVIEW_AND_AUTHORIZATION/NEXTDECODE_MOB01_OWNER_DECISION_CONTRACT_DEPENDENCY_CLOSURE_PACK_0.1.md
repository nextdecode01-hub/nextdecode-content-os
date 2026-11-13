# NEXTDECODE MOB-01 — Owner Decision & Contract Dependency Closure Pack

**Document ID:** NEXTDECODE-INT-MOB01-OWNER-CLOSURE-PACK-0.1  
**Version:** 0.1  
**Date:** 5 November 2026 (Asia/Kolkata)  
**Status:** DOCUMENTATION-ONLY DECISION AGENDA — NOT APPROVED  
**Scope:** Telegram mobile major-approval channel; owner-only first slice  
**Authority:** Subordinate to accepted P0 ADR/CF decisions, canonical contracts and Artifact 10  
**Contract freeze:** NOT GRANTED  
**Implementation / tests / agents / provider activation:** NOT AUTHORIZED

## 1. Purpose

This pack consolidates unresolved owner, contract, security, privacy and acceptance dependencies for MOB-01. It is a decision aid, not a new source of authority. It does not select options, assign unrecorded owners, amend canonical contracts, freeze schemas, or authorize implementation.

The purpose is to let the product owner and the relevant contract/security/QA authorities decide the remaining questions in a controlled order, while preserving the accepted boundaries:
- Telegram is an untrusted interaction/notification channel; the Content OS backend and central governance remain authoritative.
- MOB-DEC-01 Option B is selected; MOB-DEC-02 Option C is conditionally selected; MOB-RECON-01 Path A is selected. See REG-072, REG-073 and REG-074.
- Path A automated workflow disposition is not a human CF-21 ApprovalDecision and cannot satisfy a required human approval.
- Human approval, rights, quality, exact-version, central authorization and emergency-state gates remain mandatory where required.
- PublishingAuthorization, upload, distribution and publication remain separate; no Telegram decision grants them.
- P0-A remains pre-distribution. Public automatic publishing remains disabled absent separate explicit authorization.

## 2. Source handoff and authority

Reviewed for this consolidation:
1. REG-070 — MOB-01 Owner Decision Matrix 0.1 (MOB-DEC-01..07).
2. REG-071 — MOB-01 Security & Privacy Review 0.1 (SEC-MOB-01..09).
3. REG-072 — MOB-DEC-01 owner record (Option B).
4. REG-073 — MOB-DEC-02 owner record and §6 Path A disposition.
5. REG-074 — canonical approval/risk/audit reconciliation.
6. REG-075 — workflow disposition and lifecycle crosswalk.
7. REG-076 — API/Event and WP6 dependency crosswalk.
8. REG-077 — stage risk and eligibility decision aid.
9. REG-065 — API/Event & Lifecycle Owner Decision Matrix (API-LC-01..10).
10. REG-066 — GOV-09 correction: no owner disposition recorded.
11. REG-055 / REG-057 / REG-058 / REG-059 — WP5 matrices, Batch 17 transitions, Batch 19 governance mapping, Contract 12/WP6 protected-action oracle.
12. Contract 07 v1.0, Policy & Authorization Decision Matrix 1.0, Artifact 07 and Artifact 10.

Authority order is unchanged: accepted ADR/CF owner decisions; governing standards and canonical contracts; Data Dictionary/owner-ratified domain contracts; WP and acceptance specifications; reconciliation/decision aids. Where a source conflict remains, this pack records it; it does not choose a winner beyond already accepted authority.

## 3. Existing owner dispositions — do not reopen by implication

| Item | Current disposition | What remains open |
|---|---|---|
| MOB-DEC-01 | Option B selected: authenticated Content OS session pairing plus independent step-up for recovery and high-risk decisions | Factor, freshness, risk tiers, challenge/recovery protocol, canonical identity attributes and credential lifecycle |
| MOB-DEC-02 | Option C conditionally selected: research/topic, script/editorial and final-video review | Timeout/escalation, stage eligibility, critical taxonomy, rule lifecycle, historical-decision matching, audit and in-flight setting behavior |
| MOB-RECON-01 | Path A selected: automated disposition is a separate bounded internal workflow/policy disposition, not human approval | Canonical owner/representation and permitted internal transition catalogue |
| GOV-09 | OPEN — no owner disposition recorded | AuthorizationDecision / PublishingAuthorization relationship; no A/B/C option may be inferred |

These recorded choices are not contract freeze or implementation authorization. MOB-DEC-03..07 remain OPEN.

## 4. Owner decision agenda — MOB-DEC-03..07

| ID | Decision question | Existing neutral options | Main dependencies / consequence |
|---|---|---|---|
| MOB-DEC-03 | Which Telegram identity attributes may be bound after authenticated pairing? | A numeric user ID with private-chat verification; B numeric user and private-chat IDs; C defer exact representation to canonical identity contract | WP1/WP3 identity model, privacy minimization, authenticated owner binding. Username/display name/profile photo are not identity proof. |
| MOB-DEC-04 | Which update transport should be evaluated for a future authorized non-production adapter? | A long polling; B webhook; C defer pending runtime/API-LC-09 comparison | API-LC-09, ingress exposure, runtime ownership, durable offsets/replay and security review. No transport selected or activated. |
| MOB-DEC-05 | What step-up is required for decision callbacks? | A bound identity + backend revalidation; B fresh authenticated confirmation for every callback; C risk-tiered step-up; D notification-only/defer | MOB-DEC-01 Option B, risk taxonomy, session policy and UX. No risk tiers or factor inferred. |
| MOB-DEC-06 | What may be sent to Telegram and retained? | A minimal notification only; B minimal notification + short non-sensitive summary; C constrained preview after review; D defer provider activation pending privacy review | WP4 data lifecycle, provider processing/data residency, privacy/legal review, notification preview exposure. |
| MOB-DEC-07 | How do Telegram updates/callbacks map to canonical idempotency and correlation? | A transport dedup + backend command idempotency; B canonical interaction/request idempotency key; C defer exact envelope to API-LC-03/05 | WP2, API-LC-03/05, audit/trace and WP6. Telegram update ID is not canonical request, causation or correlation identity. |

**Decision discipline:** record each item separately with exact selected wording, rationale, rejected alternatives, affected source clauses, date/version and required contract amendments. A broad “go ahead”, “next”, or selection on another decision is not a disposition for these items.
## 5. Cross-contract owner decision agenda

### 5.1 GOV-09 — AuthorizationDecision / PublishingAuthorization
**Status:** OPEN; REG-066 explicitly corrects the earlier unsupported Option C claim.  
**Question:** What is the canonical relationship between the authorization decision concept and the publishing permission/grant concept?  
**Dependencies:** Contract 07 / CF-22, Contract 12, Data Dictionary v1.1, Batch 19 governance entity mapping, WP5/WP6 protected-action oracle.  
**Freeze impact:** BLOCKER for authorization persistence, exact grant binding and protected-action consumption. Do not merge or split records by implementation convenience; do not invent fields, FKs, cardinality, states or grant issuance behavior.

### 5.2 CF-20 rights vocabulary
**Conflict:** Contract 07 v1.0 uses PENDING_VERIFICATION / PROHIBITED; accepted CF-20 and Data Dictionary v1.1 use PENDING_REVIEW / EXPIRED / REVOKED / DENIED. Batch 19 also exposes rights_state versus canonical rights_status.  
**Question:** Confirm authoritative vocabulary, mapping/compatibility and field naming without silent aliases or coercion.  
**Dependencies:** Contract 07, CF-20, Data Dictionary v1.1, Batch 17 SM-11, Batch 19, WP5/WP1 and rights evidence model.  
**Freeze impact:** BLOCKER for rights-state persistence and exact rights gates.

### 5.3 CF-21 and ApprovalRequest lifecycle
**Conflict:** Contract 07 §10.2 includes WITHDRAWN among approval outcomes; accepted CF-21 uses APPROVED, REJECTED, CHANGES_REQUESTED, EXPIRED and REVOKED. WP5 distinguishes ApprovalRequest lifecycle from ApprovalDecision lifecycle, but request states and cardinality remain unresolved.  
**Question:** Define request lifecycle separately from human decision lifecycle; settle expiry/withdrawal/revocation semantics, request-to-decision cardinality and exact immutable review-package/version/checksum binding.  
**Dependencies:** Contract 07 §§9–10, CF-21, WP5 matrices §§4–5, Batch 17 SM-12, Batch 19, WP6.  
**Freeze impact:** BLOCKER for approval request/decision persistence, Telegram callback binding and acceptance oracles. Do not alias WITHDRAWN to REVOKED without an approved contract correction.

### 5.4 MOB-DEC-02 Path A canonical workflow disposition
**Status:** Policy boundary reconciled by REG-074; canonical representation and transition catalogue remain open under GAP-043.  
**Question:** Determine whether/how a separate workflow disposition is represented and owned, and which already-authorized internal transitions it may permit.  
**Dependencies:** Contract 07, WP5 lifecycle matrix, Unified Lifecycle standard, API/Event standards, WP1 persistence, WP2 execution, WP6 acceptance.  
**Freeze impact:** BLOCKER before any automatic internal transition is operationalized. No new entity/state/enum/event/API/schema may be assumed from Path A.

### 5.5 API-LC-01..10 — envelope and lifecycle decisions
All ten remain OPEN under REG-065. The decision subjects are:
- API-LC-01 event_version versus schema_version.
- API-LC-02 multiple events per state_version and ordering.
- API-LC-03 correlation/causation nullability and typed references.
- API-LC-04 state_version scope.
- API-LC-05 request_id / trace_id propagation.
- API-LC-06 outbox/inbox retention and redrive.
- API-LC-07 poison-message quarantine, replay and redrive authority.
- API-LC-08 schema compatibility policy.
- API-LC-09 webhook authentication and replay protection.
- API-LC-10 external side-effect outcome envelope.

**MOB-01 priority:** API-LC-03 and API-LC-05 are direct callback/audit trace dependencies; API-LC-09 is a hard gate if webhook is selected. API-LC-01/02/04/06/07/08 affect broader event/lifecycle and audit reliability; API-LC-10 protects external side-effect outcome semantics and must not be conflated with approval. All decisions remain subject to the API/Event and Lifecycle standards; this pack selects no option.
## 6. Security and privacy closure agenda — SEC-MOB-01..09

REG-071 records all findings OPEN. Severity is an activation gate, not evidence of an exploited vulnerability.

| Finding | Gate | Required closure evidence / dependency |
|---|---|---|
| SEC-MOB-01 Service identity and bot credential contract | BLOCKER | Distinct adapter service identity/owner; narrow notification and callback-forwarding capabilities; secret storage, rotation, revocation, compromise response and environment separation. WP3 worker credentials do not automatically define bot identity. |
| SEC-MOB-02 Pairing, recovery and account takeover | BLOCKER | Detailed MOB-DEC-01 Option B protocol: identity proof, step-up factors, session freshness, challenge expiry, revocation, recovery and takeover response. |
| SEC-MOB-03 Callback trust, replay and exact-version enforcement | BLOCKER | Canonical callback envelope, untrusted-input validation, exact request/artifact/version/policy binding, replay/idempotency/concurrency and API-LC-03/05 alignment. |
| SEC-MOB-04 Transport security and runtime ownership | BLOCKER | MOB-DEC-04 transport comparison, runtime owner, ingress/egress boundary, durable update handling, monitoring and recovery. Webhook also requires API-LC-09 closure. |
| SEC-MOB-05 Chat privacy, retention and provider processing | BLOCKER | MOB-DEC-06 content classes, data minimization, provider processing/terms, data residency, retention/deletion, backup and privacy/legal review. WP4 artifact retention is not Telegram chat retention. |
| SEC-MOB-06 Audit and incident response | HIGH / activation gate | Canonical audit events/evidence, correlation, retention, incident triage, token compromise and recovery procedures aligned with API-LC and WP6. |
| SEC-MOB-07 Approval versus authorization boundary | HIGH / activation gate | CF-21/CF-22/GOV-09/Contract 12 semantics and server-side enforcement; callback or Telegram UI cannot grant authority. |
| SEC-MOB-08 Notification content and preview exposure | HIGH / activation gate | MOB-DEC-06 decision, approved content classification, safe authenticated links, preview behavior, stale-message handling and no bearer-token links. |
| SEC-MOB-09 Acceptance evidence and recovery | HIGH / activation gate | MOB-A07-01..10 owner/QA disposition, exact Artifact 07/WP6 mapping, failure/recovery evidence and security review. All tests remain NOT_RUN. |

**Minimum common security invariants:** Telegram identity/display metadata is not authentication; callbacks and webhook payloads are untrusted; backend revalidates current owner, workspace, request, artifact hash/version, policy and gates; Telegram delivery/tap is not proof of canonical approval; no local approval on backend outage; unknown durable-write outcome requires canonical reconciliation; desktop review remains fallback; secrets and sensitive artifact content are excluded from chat/logs by default.

## 7. Blockers versus safely deferrable items

### 7.1 Blockers before any bot/token/provider activation or interactive implementation
1. Close SEC-MOB-01..05 and SEC-MOB-07..09 to an owner/security/privacy-approved state; SEC-MOB-06 audit/incident controls must also be defined before activation.
2. Record MOB-DEC-03..07 dispositions or explicitly narrow/defer the affected capability under an owner-approved scope.
3. Close CF-20/CF-21 request/decision semantics and exact immutable review binding.
4. Resolve GOV-09 and Contract 12 protected-action authorization relationship for any path that could invoke a protected action.
5. Close API-LC-03/05; close API-LC-09 before webhook exposure. Confirm relevant API-LC-01/02/04/06/07/08/10 decisions for the chosen interaction/transport and audit design.
6. Approve Telegram-specific privacy/provider processing, retention and data handling.
7. Owner/QA disposition of REG-069 MOB-A07-01..10 and the applicable Artifact 07/WP6 acceptance oracle.
8. Separate Artifact 10 authorization for exact implementation scope, files, commands, environment, credentials/provider and any test execution.

### 7.2 Deferrable only if the owner explicitly narrows scope
- Webhook-specific protocol and ingress may be deferred if webhook is not selected; no webhook receiver/exposure meanwhile.
- Rich message previews may be deferred by choosing a minimal notification policy; no preview content by default.
- Optional long-term telemetry dashboards, advanced operator tooling and non-P0 convenience UX may be deferred if required audit, incident and recovery controls remain satisfied.
- Nonessential future transport/provider alternatives may remain unselected until runtime evidence exists.
- Numeric retention periods or operational thresholds may remain open only where governing policy permits a safe non-production/documentation scope; they must not be guessed or silently defaulted.

“Deferrable” does not mean approved. Any narrowed scope requires an explicit owner disposition and must preserve fail-closed behavior.
## 8. Dependency sequence and closure evidence

| Sequence | Work item | Required output before dependent work proceeds |
|---|---|---|
| 1 | Owner decision capture: MOB-DEC-03..07, GOV-09, CF-20/CF-21, Path A representation | Explicit owner dispositions, rationale, source clauses and affected contract amendments identified |
| 2 | Canonical WP1/WP5 contract reconciliation | Rights vocabulary/field mapping; ApprovalRequest versus ApprovalDecision lifecycle; exact review package/version/checksum binding; authorization record relationship; Path A representation/transition authority |
| 3 | API/Event and Lifecycle reconciliation | API-LC-01..10 decisions as applicable; exact request/correlation/causation/trace semantics; replay/retention/compatibility and transport security |
| 4 | Security/privacy closure | Service identity, pairing/step-up/recovery, callback trust, transport/runtime, privacy/provider processing, audit/incident, notification exposure and recovery controls |
| 5 | WP6/QA acceptance closure | MOB-A07-01..10 dispositions mapped to existing authoritative Artifact 07 IDs/severity and WP6 evidence; fixtures/environment and recovery oracle defined |
| 6 | Artifact 10 authorization review | Separate explicit owner authorization for bounded implementation and, separately, test/provider/credential/production actions |

The sequence is dependency-aware, not a claim that every item must be solved serially. Parallel contract/security/QA analysis may occur only within separately authorized documentation scope and must use versioned shared decisions. No agent is dispatched by this pack.

## 9. Decision capture template

For each open decision, the owner record should capture:
- decision ID and exact question;
- selected option or explicit defer/reject/accept-with-amendment wording;
- rationale and rejected alternatives;
- affected canonical source document, clause and version;
- required contract/schema/API/event/acceptance changes (if any), without pre-emptively implementing them;
- accountable decision authority and required security/privacy/legal/QA concurrence;
- unresolved dependencies, effective scope and reopening trigger;
- decision date and immutable record reference.

Do not treat a proposed option, silence, expiry, “next”, a notification tap, AI confidence or a prior decision from a different scope as owner consent.

## 10. Acceptance criteria for this documentation package

- MOB-DEC-01/02 and Path A dispositions accurately reflect REG-072/073/074.
- MOB-DEC-03..07 remain open and options match REG-070.
- GOV-09 remains open with no inferred disposition.
- CF-20, CF-21, ApprovalRequest lifecycle and Path A representation conflicts remain visible.
- API-LC-01..10 remain open; priority distinctions do not imply option selection.
- SEC-MOB-01..09 remain open with source-grounded closure evidence.
- Blockers and conditional deferrals are distinguished without authorizing scope reduction.
- No new canonical entity, state, enum, field, event, API, schema, test ID or transition is introduced.
- Artifact 10 restrictions remain unchanged.

## 11. Current status and authorization boundary

**Disposition:** B-MOB-12 documentation-only owner decision and dependency closure agenda.  
**MOB-DEC-03..07:** OPEN. **GOV-09:** OPEN. **API-LC-01..10:** OPEN. **SEC-MOB-01..09:** OPEN.  
**MOB-A07-01..10:** candidate closure items only; all tests NOT_RUN.  
**Phase 4:** ACTIVE. **Phase 5 owner-review pack:** not started. **Phase-count progress:** 60% (3/5).

This pack does not authorize contract freeze, implementation, repository/source-code changes, tests, agent dispatch, Telegram bot/token/credential issuance, transport/provider activation, deployment, spending, production generation, upload or publishing. Human approval before publishing and the separate central PublishingAuthorization gate remain mandatory. Artifact 10 restrictions are unchanged.
