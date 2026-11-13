# MOB-01 — Telegram Security & Privacy Review
## Read-only architecture assessment 0.1

**Document ID:** NEXTDECODE-INT-MOB01-SEC-PRIV-REVIEW-0.1
**Date:** 4 November 2026
**Status:** READ-ONLY DESIGN REVIEW — OWNER / SECURITY / PRIVACY REVIEW REQUIRED
**Scope:** Telegram major-approval channel, owner-only first slice
**Review type:** Documentation-based architecture review; not penetration testing, code review, privacy legal opinion, provider due diligence or production security certification.
**Implementation authorization:** NOT GRANTED
**Provider / transport activation:** NOT GRANTED

## 1. Executive disposition

**Verdict: NOT READY FOR BOT CREATION, CREDENTIAL ISSUANCE, PROVIDER ACTIVATION OR IMPLEMENTATION.**

The MOB-01 contract contains a sound high-level security posture: Telegram is untrusted, the canonical backend remains authoritative, interactions are bound to exact pending requests/versions, decisions fail closed, and content approval is separate from publishing authorization.

However, several critical control details are only proposed or depend on unresolved canonical decisions. In particular, Telegram bot service identity is not yet defined by the worker credential contract; owner pairing and recovery are not approved; transport and API-LC-09 are open; privacy/retention/data processing for Telegram chat content are not established; and audit/idempotency contracts remain unresolved.

This is a design review of documents only. No Telegram bot, token, Telegram account, repository code, provider connection, runtime, test environment or external operation was inspected or activated.

## 2. P0 source handoff and dependency status

Reviewed source documents:
1. Artifact 10 — P0 Owner Review & Authorization Pack 1.0.
2. Accepted P0 Architecture Decision Baseline 1.0 (referenced by Artifact 10 and MOB-01).
3. WP3 Worker Trust & Credential Contract Reconciliation 0.1.
4. WP4 Artifact Lifecycle, Retention, Deletion & Legal Hold Reconciliation 0.1.
5. WP5 Governance & Authorization Contract Reconciliation 0.1.
6. External Provider Adapter Reference Architecture 0.1.
7. Telegram Mobile Major-Approval Channel Design & Implementation Proposal 0.1.
8. MOB-01 Telegram Security & Interaction Contract 0.1.
9. MOB-01 Artifact 07 / WP6 Acceptance Scenario Crosswalk 0.1.
10. MOB-01 Owner Decision Matrix 0.1.
11. API/Event & Lifecycle Owner Decision Matrix 0.1 and Artifact 07 / API-EVT crosswalks (via current control references).

Authority and status:
- ADR-005 establishes the high-level principle of unique, scoped, short-lived credentials and capability authorization for workers. It does not automatically define a Telegram bot/service identity.
- ADR-007 / CF-22 establish centralized authorization and adapter non-bypass. Detailed authorization semantics remain open.
- WP3's credential contract is specifically framed around canonical worker identity and worker execution. Reusing it as a bot identity model without an owner-approved service-identity mapping would be an unsupported extension.
- WP4 governs artifact lifecycle and retention; it does not establish Telegram message retention, provider-side copies, notification previews, chat deletion or data residency.
- WP5 separates QA, rights, review, approval and authorization. Approval does not itself grant execution authority.
- Artifact 10 explicitly states that proposals are not approvals and that repository, implementation, agent, provider and production permissions require separate explicit authorization.
- GOV-09 remains OPEN — no owner disposition recorded. MOB-DEC-01..07 remain OPEN.

## 3. Findings summary

| Finding | Severity / gate | Assessment |
|---|---|---|
| SEC-MOB-01 Service identity and bot credential contract | BLOCKER | WP3 worker credentials do not establish a Telegram adapter service identity, scope, issuer, secret storage or rotation policy. |
| SEC-MOB-02 Owner pairing, recovery and account takeover | BLOCKER | Pairing concept exists, but identity proof, challenge handling, revocation, recovery and step-up policy are not approved. |
| SEC-MOB-03 Callback trust, replay and exact-version enforcement | BLOCKER | High-level controls exist; canonical interaction envelope, idempotency, concurrency and correlation details depend on open API/contract decisions. |
| SEC-MOB-04 Transport security and runtime ownership | BLOCKER | Webhook vs long polling is unselected; API-LC-09 remains open; no runtime/ingress owner or operational checkpoint contract is approved. |
| SEC-MOB-05 Chat data privacy, retention and provider processing | BLOCKER | No Telegram-specific data classification, provider terms/data processing review, retention/deletion or data-residency disposition is recorded. |
| SEC-MOB-06 Audit and incident response | HIGH / activation gate | Audit principles exist, but exact events, fields, retention, compromise response and recovery evidence are unresolved. |
| SEC-MOB-07 Approval vs authorization boundary | HIGH / activation gate | Central authorization is accepted; CF-21/CF-22/GOV-09/Contract 12 remain unresolved for detailed interaction semantics. |
| SEC-MOB-08 Notification content and preview exposure | HIGH / activation gate | Data minimization is stated, but allowed content classes, link behavior, preview policy and stale-message handling are not approved. |
| SEC-MOB-09 Acceptance evidence and operational recovery | HIGH / activation gate | REG-069 identifies Telegram-specific gaps; owner/QA disposition and security/privacy review remain pending. |

All findings are open. Severity indicates a gate for Telegram activation, not a claim that a vulnerability has been exploited.

## 4. Detailed findings and required closure

### SEC-MOB-01 — Service identity and bot credential contract

**Evidence:** WP3 §§3–4 and §§8–10 define worker identity, unique scoped short-lived credentials, separation from human credentials, revocation and central authorization. The document's subject is a worker identity, not an external notification bot.

**Gap:** The Telegram adapter needs a distinct, attributable service identity and credential lifecycle. It is not safe to assume a Telegram bot token is equivalent to a WP3 worker credential or that a worker credential should be embedded in the bot.

**Required closure:**
- define the adapter's canonical service identity and owner;
- define permitted operations as narrowly scoped notification delivery and callback forwarding;
- prohibit direct domain-state mutation, arbitrary API calls and publishing-provider access;
- define secret storage boundary, access control, rotation, revocation, compromise response and environment separation;
- decide whether adapter runtime is a registered worker, a separate service principal or another canonical identity type through WP1/WP3 owner review;
- ensure secret values never enter chat, source control, callback data, telemetry or agent prompts.

**Gate:** No bot token request, creation, storage or provider connection until this contract is owner-approved and separately authorized.

### SEC-MOB-02 — Owner pairing, recovery and account takeover

**Evidence:** MOB-01 §4 proposes authenticated Content OS session plus private Telegram chat, single-use challenge, numeric Telegram account identifier and authenticated recovery. MOB-DEC-01/03/05 remain open.

**Gap:** Challenge entropy, expiry, attempt limits, binding persistence, account replacement, lost-device recovery, step-up requirements, notification of binding changes and session invalidation are not approved. A Telegram account/device takeover could otherwise impersonate the owner.

**Required closure:**
- owner-approved pairing and recovery sequence;
- canonical identity binding and exact account/chat attributes;
- challenge lifetime, one-time consumption, attempt throttling and abuse monitoring;
- rebind procedure that revokes the previous binding and invalidates outstanding callbacks;
- independent recovery route that does not depend on the Telegram account being recovered;
- step-up policy for consequential decisions;
- alert/confirmation when a binding is created, changed or revoked.

**Gate:** No approval callback may be enabled until identity and recovery policy are approved and tested in an authorized isolated environment.

### SEC-MOB-03 — Callback trust, replay and exact-version enforcement

**Evidence:** MOB-01 §§5–7 define opaque references, backend revalidation, exact-version checks and fail-closed behavior. WP5 §§3–5 require approval to bind to exact review evidence/version and authorization to bind exact action/resource/scope. API-LC-03/05 remain open.

**Gap:** The canonical interaction request, idempotency key, correlation/causation mapping, concurrency control and atomic decision write are not frozen. Telegram update IDs are transport evidence, not canonical command idempotency.

**Required closure:**
- canonical request/decision envelope and owner-approved field semantics;
- exact immutable target/version/scope binding;
- single-use or otherwise governed callback reference semantics;
- backend idempotency and concurrency strategy;
- stale, duplicate, revoked, expired, superseded and wrong-chat denial behavior;
- reconciliation for timeout before/after durable commit;
- audit linking Telegram update evidence to canonical request and decision without trusting callback data as authority.

**Gate:** No callback action implementation before API-LC-03/05 and relevant CF-21/CF-22 decisions are resolved.

### SEC-MOB-04 — Transport security and runtime ownership

**Evidence:** Telegram proposal and MOB-01 §8 leave webhook vs long polling open. API-LC-09 remains open. Telegram webhook secret header is a transport control only; it does not authenticate the human owner or authorize a decision.

**Gap:** No approved runtime owner, network boundary, ingress model, durable update checkpoint, secret rotation process, replay handling or availability/recovery objective exists.

**Required closure:**
- document runtime inventory and operator ownership;
- compare webhook and long polling against attack surface, uptime, update loss, checkpoint durability and recovery;
- if webhook is selected, approve HTTPS ingress, secret-header validation, replay/duplicate controls, key rotation, rate limits and durable enqueue-before-ack;
- if long polling is selected, approve worker identity, durable offset checkpoint, restart behavior, duplicate/out-of-order handling and network egress;
- define health/disable/incident procedures and ensure a disabled adapter leaves canonical pending requests unchanged.

**Gate:** No transport activation until owner selects it, API-LC-09 closes and the exact environment is authorized.

### SEC-MOB-05 — Chat data privacy, retention and provider processing

**Evidence:** MOB-01 §9 prohibits sensitive content by default and calls for privacy review. WP4 §§3–4 and §§12–14 distinguish retention, deletion, purge, audit preservation and central authorization but explicitly leave retention durations and some authority decisions open. External Provider Adapter Architecture §7 requires payload classification before egress and default-deny for sensitive/private material.

**Gap:** No Telegram-specific assessment defines what data leaves NEXTDECODE, who can see it on device/lock-screen notifications, how Telegram handles it, provider terms/data processing, retention/deletion, regional processing, backups, exports or incident handling. WP4 artifact retention is not a substitute for messaging-provider retention policy.

**Required closure:**
- data-flow inventory for notifications, callbacks, review links, identifiers, metadata and diagnostics;
- data classification and allowlist of fields permitted in Telegram messages;
- default no full scripts, unpublished video, prompts, rights documents, raw research, personal data or credentials;
- owner-approved preview policy, including notification lock-screen exposure and message forwarding risk;
- provider terms/privacy/data processing review and data residency/transfer assessment by the responsible owner;
- retention, deletion, backup, audit-evidence and legal-hold treatment, including provider-side copies and residual backups;
- authenticated review-link design with no long-lived bearer token in URL or message;
- incident/breach notification and response process.

**Gate:** No live message content or provider activation until privacy/security review is explicitly approved. Minimal notification is the conservative candidate, not an approved privacy policy.

### SEC-MOB-06 — Audit, monitoring and incident response

**Evidence:** WP3 requires attributable worker trust changes and central revocation; WP5 requires attributable authorization decisions and audit references; WP4 requires evidence preservation. Adapter architecture §7 prohibits secrets in logs and requires webhook replay controls.

**Gap:** Telegram-specific audit schema, retention, monitoring signals, compromise escalation, bot disablement authority and evidence collection are not finalized. Generic worker revocation cannot be assumed to revoke Telegram account bindings or bot credentials.

**Required closure:**
- define audit events for pairing, rebind, revoke, callback accepted/rejected, stale/duplicate request, durable decision outcome and adapter disable;
- distinguish notification sent, update received, callback clicked, backend decision committed and any later protected action;
- redact tokens, challenge values, raw callback payloads and sensitive content;
- define alert thresholds and incident owner;
- define emergency disable/revocation and post-compromise re-pairing;
- align retention and audit preservation with WP4/WP5 and API-LC-03/05.

### SEC-MOB-07 — Approval versus authorization and protected action

**Evidence:** WP5 §3 separates QA, rights, review snapshot, approval and authorization. WP5 §§5–7 require exact-action/resource/scope authorization and default-deny. Artifact 10 states automatic publishing remains disabled. GOV-09 is OPEN.

**Gap:** Telegram UI must not imply that content approval authorizes publishing. Detailed relationship between AuthorizationDecision and PublishingAuthorization remains unresolved. The mobile proposal's publishing request display is future/separately gated, not part of the current owner-only major review scope.

**Required closure:**
- keep research/script/final-video review actions distinct from protected distribution authorization;
- define canonical command/action for each allowed major decision only after CF-21;
- resolve CF-22/Contract 12 and GOV-09 before any publishing-authorization interaction is designed;
- ensure adapter has no distribution provider credentials or direct publishing route;
- retain separate human and central authorization checks at any later protected-action boundary.

**Gate:** Publishing, upload, scheduling, account actions and public visibility are excluded from MOB-01 and remain separately unauthorized.

### SEC-MOB-08 — Notification content, previews and review links

**Evidence:** MOB-01 §9 and adapter architecture §4/§7 call for minimal payloads, classified egress and no sensitive content in logs.

**Gap:** There is no owner-approved field allowlist, title/summary policy, link TTL, message edit/delete behavior, stale-message policy or protection against link forwarding and lock-screen preview exposure.

**Required closure:**
- define an explicit allowlist and denylist for notification fields;
- prefer opaque non-authoritative reference plus authenticated review destination;
- no long-lived bearer token or authorization capability in deep links;
- require authentication and current workspace access when opening a review link;
- define link expiry/revocation, forwarded-link behavior and stale message handling;
- do not include full artifact content or private context in notification previews by default.

### SEC-MOB-09 — Acceptance evidence and operational recovery

**Evidence:** REG-069 maps Telegram scenarios to Artifact 07/WP6 with direct/partial/gap distinctions. MOB-A07-01..10 remain candidate closure items; all tests remain NOT_RUN.

**Gap:** Existing generic worker identity, event deduplication, authorization denial and log redaction tests do not prove Telegram-specific pairing, callback idempotency, chat privacy, webhook authenticity or end-to-end adapter integration.

**Required closure:**
- owner/QA disposition each MOB-A07-01..10;
- preserve Artifact 07 IDs and severity; any new mandatory test must follow governed amendment;
- approve isolated synthetic environment and test commands separately;
- cover account takeover/rebind, wrong chat/group/forwarded update, stale version, duplicate/concurrent callback, unknown write outcome, provider outage, token compromise, message privacy and disable/recovery;
- no live Telegram/provider test without separate explicit scope, account and operation authorization.

## 5. Security/privacy control disposition

| Control area | Current disposition | Evidence needed before activation |
|---|---|---|
| Central backend authority | Accepted high-level invariant | Prove adapter cannot bypass through its approved interface |
| Owner identity | Candidate design only | Approved pairing, recovery, step-up and binding lifecycle |
| Adapter service identity | GAP | Canonical identity type, scope and credential lifecycle |
| Bot secret handling | Principle documented; implementation unspecified | Approved secret store, rotation, revocation and incident runbook |
| Callback integrity | High-level rules documented | Frozen envelope, idempotency, replay and exact-version tests |
| Transport | Unselected | API-LC-09 closure and runtime security review |
| Chat privacy | Principles documented | Provider due diligence, data flow, field allowlist and retention decision |
| Audit | Requirements candidate | Canonical event mapping, retention and alerting/incident process |
| Revocation | Worker trust principles exist | Telegram binding and bot credential revocation contract |
| Publishing separation | Accepted high-level rule | CF-21/CF-22/GOV-09/Contract 12 closure; still separately authorized |
| Acceptance | Partial mapping exists | Owner/QA approval and MOB-A07 gap disposition |

## 6. Required owner/security/privacy decisions

These items map to existing MOB-DEC IDs and do not create new canonical decisions:

1. MOB-DEC-01: approve pairing, recovery, revocation and account-takeover response.
2. MOB-DEC-02: confirm exact first-slice decision categories; publishing authorization excluded.
3. MOB-DEC-03: approve Telegram account/chat binding attributes and identity model.
4. MOB-DEC-04: select transport only after runtime/security comparison and API-LC-09 closure.
5. MOB-DEC-05: approve step-up authentication/risk policy.
6. MOB-DEC-06: approve privacy classification, message allowlist, provider terms/data processing, retention/deletion and incident response.
7. MOB-DEC-07: resolve canonical idempotency/correlation semantics with API-LC-03/05.
8. Security owner: approve service identity, bot credential storage/rotation/revocation and incident runbook.
9. WP6 owner/QA: approve REG-069 and disposition MOB-A07-01..10.
10. Product owner: keep GOV-09 OPEN unless and until a separate explicit decision is recorded.

## 7. Release gates

MOB-01 must remain documentation-only until all applicable gates are satisfied:

- [ ] MOB-DEC-01..07 explicitly decided or deliberately deferred with safe blocked behavior.
- [ ] Telegram adapter service identity and credential contract approved.
- [ ] Pairing, recovery, step-up and revocation model approved.
- [ ] Callback/API envelope and API-LC-03/05 decisions resolved.
- [ ] Transport selected; API-LC-09 closed; runtime owner and environment approved.
- [ ] Privacy/data-flow/provider review and retention/deletion policy approved.
- [ ] Notification field allowlist and authenticated review-link behavior approved.
- [ ] Audit, monitoring, incident response and emergency disable procedures approved.
- [ ] REG-069 reviewed; MOB-A07-01..10 closed/deferred/promoted through governance.
- [ ] Separate Artifact 10 implementation authorization identifies exact files, commands, environment, tests, reviewer and expiry.
- [ ] Separate authorization for any provider activation or live Telegram operation.

Until then, no bot/token, code, tests, agents, provider activation, deployment, upload or publishing.

## 8. Final review conclusion

MOB-01 has a sound conceptual trust boundary but lacks the approved service identity, pairing/recovery, transport, privacy, audit and canonical interaction details required for safe activation. The strongest current project controls are the accepted central authorization invariant, exact-version approval principle, least-privilege credential direction and explicit prohibition on inferring authorization from a proposal or the word “next”.

**Disposition:** Return to owner/security/privacy review. Do not implement or activate. Keep Telegram as a proposed private interface only. Keep GOV-09 OPEN and preserve all existing human approval, rights, quality, lifecycle and central authorization gates.

## 9. Change log

- 0.1 — Documentation-based security/privacy assessment of MOB-01. Findings SEC-MOB-01..09 recorded. No tests, penetration testing, provider due diligence, implementation or external activation performed.
