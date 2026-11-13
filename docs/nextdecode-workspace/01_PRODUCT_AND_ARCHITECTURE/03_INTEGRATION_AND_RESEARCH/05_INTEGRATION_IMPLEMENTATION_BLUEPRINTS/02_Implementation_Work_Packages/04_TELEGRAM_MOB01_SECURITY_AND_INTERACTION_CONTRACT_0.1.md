# MOB-01 — Telegram Major-Approval Security & Interaction Contract
## Proposal 0.1 — Documentation only

**Status:** WORKING CONTRACT CANDIDATE — NOT OWNER-APPROVED / NOT IMPLEMENTATION-AUTHORIZED
**Scope:** Major approvals only; Telegram is a proposed private interaction channel.
**Authority:** Subordinate to accepted P0 ADR/CF decisions, canonical contracts and Artifact 10.

## 1. Purpose and authority boundary

This document specifies security and interaction requirements for a future Telegram adapter. It does not adopt Telegram as an active provider, select a transport, freeze an API, or authorize a bot, token, code, tests, agents, deployment or publishing.

Telegram is an untrusted notification and interaction surface. A message, button, callback, Telegram account identifier, delivery receipt or bot response is never by itself an approval, identity proof, policy decision or publishing authorization.

The canonical Content OS backend remains the sole authority for identity binding, pending-request lookup, exact target/version validation, rights and quality gates, lifecycle eligibility, authorization, durable decision recording and audit evidence.

The adapter may forward an interaction reference and display a backend-confirmed outcome. It must not create or infer a decision locally, advance workflow state independently, or call a publishing provider directly.

## 2. P0 source handoff and dependencies

The following source set governs the work; no lower-authority proposal may override it:
- Accepted P0 Architecture Decision Baseline 1.0 and Artifact 10 — authority, scope and action permissions.
- Telegram Mobile Major-Approval Channel Design & Implementation Proposal 0.1 — owner preference: major approvals only; Telegram first.
- Existing Technology and Integration Baseline 0.1 — Telegram documented as a notification reference; live configuration/credentials not verified.
- External Integration Catalogue 0.1, INT-NOTIFY-01 — Telegram documented/candidate, not adopted.
- External Provider Adapter Reference Architecture 0.1 — provider adapter is subordinate to central policy and domain authority.
- Contract 07 / CF-21 — approval request, decision vocabulary and exact review target/version remain under reconciliation.
- Contract 07 / CF-22 — centralized authorization direction accepted; detailed semantics remain open.
- GOV-09 — OPEN; no explicit owner disposition recorded for AuthorizationDecision versus PublishingAuthorization.
- API-LC-03, API-LC-05 and API-LC-09 — open causation, identity propagation and webhook security decisions.
- Contract 12 and WP1/WP2/WP3/WP5/WP6 — protected action, persistence, workflow, service identity, governance and acceptance dependencies.

**Handoff rule:** If a required source clause is missing, contradictory or not owner-approved, record the gap and block the dependent contract detail. Do not invent a field, state, identity claim, cardinality, transition, authorization grant or owner decision.
## 3. Threat model and trust boundaries

Threats in scope:
1. Telegram account/device takeover or unauthorized account binding.
2. Username/display-name spoofing, forwarded messages, group interactions or wrong-chat delivery.
3. Forged, modified, replayed, duplicated, expired or out-of-order callback data.
4. Stale request or artifact version; approval accidentally applied to a newer version.
5. Concurrent decisions, double taps, retries or callback delivery after backend timeout.
6. Bot-token theft, webhook forgery, polling checkpoint loss or adapter compromise.
7. Sensitive project data exposed in chat, notification previews, logs or diagnostic records.
8. Telegram outage, network partition, backend unavailability or uncertain durable-write outcome.
9. Confusion between content review approval and permission to perform a protected publishing action.

Trust boundaries:
- Telegram identity and callback payloads are external/untrusted input.
- The adapter runtime and bot token are service components, not policy authorities.
- The authenticated Content OS identity/session boundary establishes owner identity.
- Canonical governance and workflow services validate the request and persist the outcome.
- Publishing/distribution providers are separate side-effect boundaries and remain outside this first slice.

## 4. Identity pairing, binding and recovery

Initial scope is one owner identity only. Group approvals, delegated approvers, multi-user roles and username-based authorization are excluded.

Pairing must establish control of both (a) an authenticated NEXTDECODE owner session and (b) the intended Telegram private bot account. A Telegram username, display name, profile photo, phone number supplied by the user or message text is not sufficient identity evidence.

Proposed sequence:
1. Owner starts pairing from an authenticated Content OS session.
2. The canonical backend creates a high-entropy, single-use, short-lived pairing challenge.
3. Owner opens the bot in a private one-to-one chat and submits/claims the challenge through the approved pairing flow.
4. Backend verifies challenge validity, intended owner session, private-chat context and Telegram numeric account identifier.
5. Backend durably records the binding using the canonical identity/security model and returns a confirmation to both authenticated surfaces.
6. Challenge is consumed atomically; it cannot be reused or rebound.

Challenge representation, storage, expiry duration, rate limits and audit fields are unresolved implementation details. Do not place a long-lived bearer credential in a deep link or chat message.

Recovery/rebinding must require a separately authenticated owner recovery path, revoke the previous binding, invalidate outstanding interactions and record attributable audit evidence. A Telegram-only recovery path is prohibited. The exact recovery mechanism requires owner/security approval.

**Fail-closed rule:** Missing, ambiguous, revoked, expired or mismatched binding means no decision is accepted. The owner must use the authenticated desktop recovery/review path.
## 5. Canonical request and interaction lifecycle

The backend creates or exposes a canonical pending approval request before any Telegram notification is sent. The notification adapter receives only the minimum approved presentation data and an opaque reference to that request.

Required logical sequence:
1. Backend confirms that the request is pending, actionable and within the approved major-decision scope.
2. Adapter sends a minimal private notification and records delivery-attempt metadata without treating delivery as a decision.
3. Owner opens an authenticated review destination to inspect the exact target/version and required evidence.
4. Owner submits one supported decision action through the approved interaction surface.
5. Backend authenticates the bound owner, resolves the canonical request and revalidates request status, target/version, workspace, lifecycle, rights, quality and applicable policy.
6. Backend atomically records the decision and idempotency outcome under canonical contracts.
7. Adapter displays success only after receiving a durable, definitive backend result.
8. If the backend result is unknown, adapter displays “status pending / verify in Content OS”; it must not retry as a new decision or claim success.

The canonical lifecycle and decision vocabulary remain those in CF-21 and approved contracts. This document creates no new state, transition, reason code or decision enum.

## 6. Callback and interaction-reference contract

Telegram callback data is untrusted transport input. It must contain only a compact opaque interaction reference or equivalent non-authoritative handle. It must not encode an approval, authorization grant, role, secret, full artifact content or trusted target/version claims.

Telegram Bot API limits callback data to 1–64 bytes. The implementation must respect that transport limit, but the limit does not define the Content OS identifier format or security model.

On every callback, the backend must independently:
- authenticate the Telegram sender against the active owner binding;
- verify the expected private chat and permitted interaction context;
- resolve the opaque reference to a canonical pending request;
- verify workspace, request identity, allowed action and exact artifact/review version;
- verify the request is still pending and not expired, revoked, superseded or consumed;
- re-evaluate current rights, quality, lifecycle and policy gates;
- apply idempotency and concurrency control before durable recording.

Never trust callback text, button label, message contents, client-supplied version, username or Telegram update identifier as the sole authorization evidence. A valid callback reference is a lookup key, not a capability grant.

The exact callback schema, identifier entropy, lifetime, database constraints and API envelope remain open pending API-LC-03/05 and canonical contract closure.
## 7. Replay, duplication, concurrency and uncertain outcomes

The backend is responsible for idempotency. Telegram update identifiers can support transport-level duplicate detection, but they do not replace a canonical decision idempotency key or request-state validation.

Required behavior:
- Same update delivered more than once: process at most one canonical decision; subsequent deliveries return the already-recorded outcome or a safe duplicate response.
- Two taps or concurrent callbacks for the same request: serialize/compare-and-set against canonical request state; only one permitted terminal decision can be committed.
- Old callback after request expiry, revocation, supersession or artifact-version change: reject as stale and provide a safe route to the current review.
- Callback from a different account/chat: reject and record a security-relevant event without exposing request details.
- Backend timeout before durable commit: outcome is unknown; reconcile canonical state before any retry.
- Backend timeout after durable commit but before response: retry must resolve to the original recorded outcome, not create a second decision.
- Adapter restart: recover from durable checkpoints/queue state; do not infer that unacknowledged callbacks were accepted.
- Telegram update retention expiry or missed updates: desktop review path remains authoritative; no silent approval or synthetic decision is permitted.

No automatic approval, fallback approval, timeout approval or publishing action may occur. Any redrive/replay must preserve original request identity and must not repeat external side effects.

## 8. Transport security and operational choice

Telegram supports two mutually exclusive update-receipt modes: long polling via getUpdates and webhook delivery. This proposal does not select either.

Webhook considerations:
- Requires an HTTPS-reachable receiver and a secured ingress boundary.
- Telegram supports a configured webhook secret token delivered in the X-Telegram-Bot-Api-Secret-Token header.
- Receiver must validate the secret using constant-time comparison where applicable, reject missing/invalid headers, rate-limit, minimize request logging and durably enqueue before acknowledging.
- API-LC-09 remains open; no webhook exposure before protocol, replay controls, key rotation, ingress ownership and security review are approved.

Long-polling considerations:
- Avoids an inbound public webhook receiver but requires a continuously running outbound-connected worker.
- Must checkpoint update offsets durably and handle restart, duplicate and out-of-order delivery safely.
- Requires explicit runtime ownership, network egress, secret storage, health monitoring and recovery behavior.
- Long polling is a candidate for evaluation only, not a selected deployment architecture.

Transport selection requires a written comparison against hosting/runtime availability, threat model, operational burden, delivery durability and API-LC-09. No transport is activated by this document.
## 9. Privacy, data minimization and secret handling

Telegram messages must contain only the minimum information needed to notify the owner that a decision is ready. Prefer a short category/title, non-sensitive reference, expiry/staleness hint and authenticated review link.

Do not send full scripts, unpublished video, private prompts, source research dumps, personal data, rights evidence, access tokens, API keys, bot tokens, internal logs or other sensitive project content into chat unless a separate privacy/security assessment explicitly approves a specific preview use case.

Detailed review must occur through an authenticated destination that enforces current owner identity and workspace access. A Telegram deep link must not contain a long-lived bearer token or grant authority by possession.

Bot tokens and any webhook secret must be held in an approved secret-management boundary, never in source control, chat, client-visible URLs or routine logs. Access must be least-privilege, attributable, revocable and rotated under an approved process. Raw callback payloads, pairing challenges and secrets must not be written to diagnostics.

Retention, deletion, data residency, backup, Telegram message handling, notification previews and incident response require privacy/security review before activation. Do not assume Telegram message deletion removes all provider-side copies or notification previews.

## 10. Audit evidence and observability

Canonical backend audit evidence must distinguish:
- canonical approval request identity and current state;
- bound authenticated owner identity and workspace;
- exact reviewed target and immutable/version reference;
- requested action and canonical decision outcome;
- validation results for rights, quality, lifecycle and applicable policy;
- request/correlation/causation/trace references as defined by API-LC-03/05;
- durable commit outcome, timestamp and idempotency result;
- adapter/transport delivery and callback receipt as separate operational facts.

Telegram delivery status, callback receipt, button tap and bot message edit are not proof of a canonical approval. The adapter must never claim “approved” before a definitive durable backend response.

Do not log bot tokens, webhook secrets, pairing challenges, raw callback payloads or sensitive artifact content. Security logs should record enough to investigate rejected interactions without leaking private project data. Exact event names, fields, retention and correlation rules remain subject to canonical API/Event and data-lifecycle decisions.

## 11. Failure behavior and safe fallback

- Identity or binding unavailable: reject; require authenticated desktop recovery.
- Request missing, expired, revoked, superseded or already consumed: reject or return the original recorded outcome; do not mutate workflow.
- Artifact/version mismatch: reject; direct owner to the current authenticated review.
- Rights/quality/policy gate unavailable or failing: fail closed; no approval.
- Backend unavailable: show a retry-later/status-check message; no local decision.
- Durable-write outcome unknown: reconcile canonical request state before retry; never report success based on timeout.
- Telegram outage or update loss: use the existing authenticated desktop review path.
- Bot token suspected compromised: revoke/disable the adapter credential, invalidate outstanding adapter sessions/interactions as appropriate, investigate and require re-pairing through authenticated recovery.
- Adapter disabled: pending requests remain in the canonical backend and are not auto-approved or auto-expired except under their approved lifecycle rules.
## 12. Proposed acceptance scenarios — not approved test IDs

The future acceptance oracle should include, at minimum:
1. Correctly paired owner in the expected private chat can retrieve an eligible pending major request.
2. Unbound, revoked, expired or mismatched Telegram identity cannot view or decide.
3. Group, forwarded-message and wrong-chat interactions are rejected.
4. Username/display-name spoofing does not satisfy owner identity.
5. A valid callback reference cannot approve a different target, workspace or artifact version.
6. Stale, expired, revoked or superseded request is rejected.
7. Duplicate update/callback cannot create a second canonical decision.
8. Concurrent taps produce at most one durable canonical decision.
9. Backend timeout before or after commit is reconciled without duplicate decision or false success.
10. Rights, quality, lifecycle or policy hard blocker prevents approval.
11. Backend outage, adapter outage or Telegram update loss never creates an implicit approval.
12. Notification delivery or message read status never changes canonical request state.
13. Callback replay after bot disable/revocation is rejected.
14. Audit evidence identifies the exact owner, request, target/version and definitive backend outcome.
15. Telegram interaction alone never creates PublishingAuthorization or triggers a protected distribution side effect.
16. P0-A remains at the approved pre-distribution boundary; public upload/publishing stays disabled.

These scenarios are proposed only. They do not replace Artifact 07 test IDs/severity, prove coverage, authorize test execution or establish production readiness. Any mapping to Artifact 07/WP6 must preserve direct/partial/missing distinctions and obtain separate test authorization.

## 13. Owner decisions and unresolved contract dependencies

MOB-DEC-01 — Identity pairing and recovery: approve or amend the proposed authenticated-session + private-chat pairing; specify recovery and revocation authority.

MOB-DEC-02 — Decision scope: confirm the exact major-decision categories permitted in the first owner-only slice. Publishing authorization remains separate and excluded.

MOB-DEC-03 — Telegram identity: confirm the canonical account identifier and how it is bound to authenticated owner identity; do not treat username as identity.

MOB-DEC-04 — Transport: choose webhook or long polling only after runtime/security comparison and API-LC-09 closure. Neither is selected here.

MOB-DEC-05 — Step-up authentication: decide whether any major decision requires a fresh authenticated confirmation beyond the Telegram account binding.

MOB-DEC-06 — Privacy and retention: approve message-content limits, authenticated preview model, retention/deletion, data residency and incident response.

MOB-DEC-07 — Idempotency/correlation: resolve how canonical request identity, idempotency key, Telegram update ID, correlation and causation are related under API-LC-03/05 and canonical contracts.

Additional blockers: CF-21 approval lifecycle and decision vocabulary; CF-22 authorization semantics; GOV-09 relationship (OPEN); Contract 12 protected-action boundary; WP1 identity/persistence; WP2 durable workflow; WP3 service identity; WP5 rights/quality governance; WP6 acceptance oracle.

## 14. Explicit non-authorization and exit criteria

This document does not authorize creating a bot, requesting or storing credentials, connecting Telegram, selecting or activating webhook/long polling, inspecting or modifying the repository, changing APIs/schemas/states, running tests, dispatching agents, spending, deploying, uploading or publishing.

MOB-01 is ready for owner review only after:
- source dependencies and unresolved conflicts are accurately mapped;
- identity/pairing/recovery, callback, stale/duplicate/replay, privacy, failure and audit requirements are complete;
- transport is compared without being silently selected;
- acceptance scenarios are mapped to Artifact 07/WP6 without inventing coverage;
- open owner decisions and exact implementation boundaries are explicit;
- security/privacy review and owner approval are recorded under the applicable governance process.

Implementation remains blocked until separate explicit authorization under Artifact 10 and required canonical contract decisions/freezes.

## 15. Official Telegram transport references

- Telegram Bot API: https://core.telegram.org/bots/api
- Telegram Bots FAQ: https://core.telegram.org/bots/faq

Transport facts used in this proposal: getUpdates and webhook are mutually exclusive update-receipt methods; webhook supports a configured secret token in the X-Telegram-Bot-Api-Secret-Token header; update_id can help identify duplicate/out-of-order updates; callback_data is limited to 1–64 bytes; Telegram does not retain updates indefinitely (Bots FAQ states updates are kept no longer than 24 hours).

These are Telegram platform facts, not Content OS authorization rules. Recheck official documentation at implementation time.

## 16. Change and review status

- 0.1 — Drafted as a documentation-only security and interaction contract candidate. It is not owner-approved, not contract-frozen and not implementation-authorized.
- GOV-09 correction — GOV-09 remains OPEN; no explicit owner disposition recorded. The prior unsupported Option C claim has been corrected in the governance decision-capture record and related indexes.
