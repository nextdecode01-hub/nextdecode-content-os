# NEXTDECODE — Telegram Mobile Major-Approval Channel
## Design & Implementation Proposal 0.1

**Document ID:** NEXTDECODE-INT-TELEGRAM-MOBILE-APPROVAL-0.1  
**Version:** 0.1 | **Date:** 4 November 2026  
**Status:** OWNER-ALIGNED DESIGN PROPOSAL — NOT CONTRACT-FROZEN / NOT IMPLEMENTATION-AUTHORIZED  
**Owner preference:** Major approvals only; Telegram as the initial mobile interface  
**Authority:** Subordinate to accepted P0 ADRs/CFs, canonical contracts, Artifact 10 and explicit owner authorizations.

## 1. Executive decision

The owner selected:
- **Control scope:** Major approvals only.
- **Initial mobile interface:** Telegram Bot.
- **Product intent:** Make consequential content decisions from a phone without requiring the owner to open the desktop workspace.
- **Architecture rule:** Telegram is a user interface and notification transport only. NEXTDECODE's canonical backend, governance services and durable records remain the source of truth.

This is a design proposal. It does not adopt Telegram as an active provider, create a bot, select transport mode, define frozen API fields/states, authorize code changes or enable any publishing action.

## 2. Product boundary

### 2.1 In scope for the proposed first experience

The bot may eventually present owner decision requests for:
1. **Research/topic selection** — review a proposed topic and evidence summary.
2. **Script/editorial approval** — review a specific script version and request approval, rejection or changes.
3. **Final-video review** — inspect a specific rendered artifact/version and its QA/rights summary, then record the applicable human review decision.
4. **Publishing authorization request** — show a separate, explicit request for the protected publishing action only when the canonical governance model and policy permit such a request.

The fourth item is not a promise that publishing will be enabled. P0-A remains at the human-approved pre-distribution boundary; the protected distribution request is expected to be denied when no separate publishing authorization exists. Actual upload, publication, scheduling execution and public visibility are outside this proposal's initial P0-A implementation scope.

### 2.2 Out of scope

- Full mobile Control Center or general-purpose dashboard.
- Editing scripts, storyboards, video timelines or assets inside Telegram.
- Direct shell, repository, database or infrastructure commands.
- Manual retry/redrive, worker control, queue manipulation or arbitrary workflow mutation.
- Credential management or display of secrets.
- Direct calls from Telegram to social-platform publishing APIs.
- Telegram message/button as a source of authorization.
- Automatic or unattended public publishing.
- Group-based approval, multi-user delegation or role administration in the first owner-only experience.
- Replacing the existing Shorts Studio or its specialist production responsibilities.

## 3. User experience concept

The bot sends a private notification when a major decision is ready. A message should contain only the minimum useful context:
- decision category and short title;
- stable human-readable content reference;
- exact artifact/review version label where available in the approved contract;
- short evidence/QA/rights summary;
- why a decision is needed and what happens next;
- a private review link or safe preview when the relevant artifact access model supports it.

Illustrative interaction:
1. Owner receives a private message: “Final video review is ready.”
2. Owner opens the secure review destination or preview.
3. Owner chooses a supported decision action (for example, approve, reject or request changes).
4. The bot sends the interaction to the Content OS approval interface.
5. The backend revalidates identity, pending request, exact version, current lifecycle and policy prerequisites.
6. The canonical service records the decision and audit evidence.
7. The bot reports only the backend-confirmed outcome. It must never display “approved” merely because a button was tapped.

Button labels and exact decision vocabulary remain illustrative until CF-21 and relevant canonical contracts are owner-resolved. Do not introduce new canonical states or reason codes in this proposal.

## 4. Logical architecture

**Content OS domain / governance services** remain authoritative.

**Telegram notification adapter**:
- sends minimal private notifications;
- renders approved decision choices;
- receives interaction callbacks;
- forwards an opaque interaction reference to the authenticated Content OS interface;
- displays only the backend-confirmed result.

**Central approval/authorization services**:
- validate the authenticated owner and workspace scope;
- resolve the pending request from canonical state;
- verify that the decision applies to the exact artifact/review version;
- validate current rights, quality, lifecycle and policy prerequisites;
- distinguish content approval from protected-action authorization;
- persist the canonical decision and audit trail;
- return a normalized outcome to the adapter.

**Workflow service**:
- advances only state transitions already allowed by approved contracts;
- remains the durable authority for workflow/job execution;
- does not treat Telegram delivery, callback receipt or n8n orchestration as authorization.

Telegram must never be a second system of record.

## 5. Non-negotiable security and integrity controls

1. **Private owner binding:** Initial operation is one-owner-only. Bind the bot to a verified Telegram numeric account identity through a separately approved pairing procedure. A username or display name alone is insufficient.
2. **No group approvals:** Do not accept decisions from groups, forwarded messages or unbound accounts in the first version.
3. **Backend authorization:** Every interaction is revalidated by the central backend. The adapter cannot create or self-issue approval/authorization.
4. **Opaque callback reference:** A callback is only a pointer to a pending interaction. It is not trusted as proof of identity, permission, action scope or artifact version.
5. **Exact-version binding:** A decision must resolve to the precise reviewable artifact/version represented by the pending request. If the artifact changes, the old request must not silently approve the new version.
6. **Stale/duplicate/replay protection:** Expired, already-consumed, superseded or duplicate interactions must be rejected safely. Backend idempotency and audit semantics must be specified in the approved API/Event contract.
7. **Fail closed:** If the backend, identity check, policy service or durable store is unavailable or returns an uncertain result, no approval or protected action is accepted.
8. **Least privilege:** Bot credentials are service-scoped, stored outside messages and logs, rotated/revocable and never shared with agents or users.
9. **Data minimization:** No secrets, access tokens, private prompts, unnecessary personal data or full sensitive artifacts in chat. Use a protected review link or approved preview mechanism.
10. **Auditability:** The canonical service records actor identity, decision, target/version, time, request/correlation evidence and backend outcome under approved contracts. Telegram delivery receipts are not approval evidence.
11. **Publishing separation:** Content approval is not automatically publishing authorization. The publishing adapter must recheck central authorization immediately before any protected side effect.
12. **Safe failure:** Bot outage, message-delivery failure or Telegram API unavailability must never cause the workflow to assume approval or trigger publishing.

## 6. Telegram transport and integration decisions — deliberately open

No transport choice is made in this document.

- **Webhook:** Requires an externally reachable receiver and a resolved API-LC-09 webhook authentication/replay-protection decision, plus security/environment authorization.
- **Long polling:** Avoids an inbound public webhook endpoint but still requires a continuously running outbound-connected service, credential handling, network policy, availability and operational ownership.
- **Other Telegram delivery patterns:** Must be evaluated against the same identity, replay, privacy, durability and operational controls.

The first implementation proposal should compare webhook and long polling using official Telegram Bot API documentation and current hosting/runtime constraints. It must not activate either mode until the owner selects it and authorizes the exact environment.

## 7. Canonical contract dependencies — no fields or states frozen here

| Dependency | Why it matters | Current status |
|---|---|---|
| Contract 07 / CF-21 | Approval request lifecycle, decision vocabulary, exact review package/version binding | Owner reconciliation open |
| Contract 07 / CF-22 | Centralized authorization and protected-action authority | High-level direction accepted; detailed semantics open |
| GOV-09 | AuthorizationDecision vs PublishingAuthorization relationship | **OPEN — no owner disposition recorded**; no record relationship selected |
| Contract 12 | Protected distribution action, account/destination/action binding and side-effect boundary | C12-01..07 remain open |
| API-LC-03 / API-LC-05 | Causation, request/correlation/trace propagation | Open |
| API-LC-09 | Webhook authentication and replay protection | Open; blocks webhook exposure |
| Batch 19 / WP1 | Canonical persistence, typed relationships and exact-version references | Candidate mapping; owner decisions open |
| WP2 / WP3 | Durable workflow, actor/service identity, credentials and capability enforcement | Contract reconciliation open |
| WP6 / Artifact 07 | Exact approval, authorization, replay, stale-version, audit and fail-closed acceptance oracles | Manifest/crosswalk exists; tests NOT_RUN and execution unauthorized |
| Artifact 10 | Separate owner authorization for repository, implementation, agents, external services and publishing | Current permissions remain not granted |

The bot adapter must consume canonical contracts; it must not invent a parallel approval model or local state machine.

## 8. Proposed delivery sequence

### MOB-00 — Documentation and owner alignment (current)
- Record owner preference: major approvals only; Telegram first.
- Preserve GOV-09 as OPEN; no owner disposition has been received.
- Map use cases, security invariants, P0/P1 boundaries and open contract dependencies.
- **Exit:** owner-reviewed design proposal and documented open-decision list.
- **Status:** design proposal prepared; owner review pending.

### MOB-01 — Contract and threat-model closure
- Reconcile approval request/decision semantics and exact artifact-version binding.
- Map mobile actions to canonical commands/decisions without creating new states.
- Resolve identity pairing, replay/idempotency, audit and callback expiry semantics.
- Decide webhook versus long polling only after API-LC-09 and environment/security review.
- Define denial, stale request, duplicate callback, backend timeout and unknown result behavior.
- **Exit:** versioned owner-approved interface contract, threat model and acceptance oracle.
- **Status:** blocked on owner decisions and contract freeze.

### MOB-02 — Read-only notification adapter proposal
- Define minimal notification content, delivery/retry behavior and safe review links.
- Use synthetic fixtures for any later authorized local contract harness.
- Do not transmit sensitive content or create approval actions in this stage.
- **Exit:** approved notification contract, privacy review and offline contract evidence.
- **Status:** proposed only; no code or tests authorized.

### MOB-03 — Owner-only approval interaction
- Implement only after separate bounded implementation authorization.
- Bind one verified owner identity.
- Accept only explicitly supported major decision types.
- Route decisions through the central governance API and durable workflow.
- Reject stale, duplicate, expired, wrong-version and unauthorized interactions.
- **Exit:** independently reviewed acceptance evidence for the approved non-production scope.
- **Status:** not authorized.

### MOB-04 — Publishing authorization integration (future / separately gated)
- Revisit only after GOV-09 and Contract 07/12 decisions are resolved and frozen.
- Require separate owner approval for the publishing policy and exact protected-action scope.
- Keep actual upload/publication disabled until a further explicit authorization.
- **Exit:** separately approved distribution contract, security review, WP6 evidence and explicit operational authorization.
- **Status:** outside current scope; not authorized.

## 9. Proposed acceptance scenarios (not approved test IDs)

Future acceptance design should cover:
- authorized owner receives a notification;
- unbound account cannot view or decide;
- group/forwarded interaction is rejected;
- stale artifact version cannot be approved;
- duplicate callback cannot create a second decision;
- expired or superseded request is rejected;
- bot cannot bypass rights or QA hard blockers;
- backend outage or uncertain response does not create an approval;
- notification delivery does not change canonical state;
- bot callback does not grant publishing authorization by itself;
- old message/button cannot authorize a new action or version;
- audit evidence links the decision to the exact reviewed target/version;
- bot disable/revocation prevents new interactions safely;
- P0-A protected distribution request remains denied absent separately approved authorization.

These are proposed scenarios only. They do not replace Artifact 07 IDs/severity or authorize test execution.

## 10. Operational and privacy requirements

- One owner identity initially; no additional approver roles or delegation until separately designed.
- Bot token must be stored as a secret reference in an approved secret-management boundary; never in source control, chat or logs.
- No token or raw callback payload in diagnostics.
- Bot messages should expire or become visibly stale when the underlying request is no longer actionable, to the extent supported by Telegram and the backend.
- Notifications should avoid sensitive project content; detailed review occurs through an authenticated destination.
- Delivery is best-effort; the canonical pending-decision queue remains authoritative.
- A manual desktop review path must remain available if Telegram is unavailable.
- Monitoring must distinguish sent, delivered where available, callback received, backend accepted/rejected and canonical decision recorded. Telegram delivery status must not be conflated with decision success.
- Retention, deletion, data residency and Telegram's handling of message data require a privacy review before activation.

## 11. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Stolen Telegram account or device | Pairing, backend identity checks, revocation and additional authentication for high-risk actions |
| Old button approves new artifact | Exact-version binding and backend revalidation |
| Callback replay or duplicate delivery | Server-side idempotency, consumed-request checks and audit |
| Bot token leakage | Secret manager, redaction, rotation and no token in repository/chat |
| Telegram unavailable | Desktop fallback; fail closed; no implicit approval |
| Notification reveals private content | Minimal payload and authenticated review link |
| Bot becomes an authorization bypass | Bot only forwards decisions; central governance service is authoritative |
| Confusion between approval and publish permission | Separate user experience and backend checks; GOV-09 remains open |
| Webhook exposure before security decision | No webhook until API-LC-09 and security review close |

## 12. Owner decisions still required before implementation

1. Confirm the proposed four major decision categories and which are allowed in the first owner-only slice.
2. Confirm exact owner identity-pairing/recovery approach.
3. Resolve CF-21 approval request/decision and review-package/version binding.
4. Resolve relevant CF-22 protected-action and authorization semantics; GOV-09 remains OPEN pending an explicit owner disposition.
5. Resolve API-LC-03, API-LC-05 and API-LC-09 as applicable.
6. Decide transport after security and hosting comparison.
7. Approve data/privacy/retention rules and a secret-management approach.
8. Approve exact implementation work package, permitted files/commands, tests and reviewer under Artifact 10.

## 13. Explicit non-authorization statement

This proposal does **not** authorize:
- creating a Telegram bot or Telegram account integration;
- creating, requesting or storing a bot token;
- inspecting or modifying the repository;
- editing notify_review.py, notify_status.py, n8n workflows or any project code;
- API endpoint/schema/state changes;
- tests, fixtures, agent dispatch or implementation;
- webhook exposure, long-polling service activation or provider connection;
- spending, paid services, deployment, upload or publishing.

All such work requires separate explicit owner authorization under Artifact 10. Existing human approval, central authorization, rights and quality gates remain mandatory. Automatic public publishing remains disabled.

## 14. Source references

- Accepted P0 Architecture Decision Baseline 1.0, especially ADR-004, ADR-005, ADR-007, ADR-008, ADR-009 and ADR-010.
- Artifact 10 — P0 Owner Review & Authorization Pack 1.0.
- Contract 07 / CF-21 and CF-22 governance reconciliation.
- Contract 12 distribution/publishing reconciliation.
- API/Event & Lifecycle Owner Decision Matrix 0.1, API-LC-03/05/09.
- Existing Technology and Integration Baseline 0.1, §§2–3 (existing review/approval and notification modules; Telegram documented but not live-verified).
- External Integration Catalogue 0.1, INT-NOTIFY-01 (Telegram/other messaging providers documented/candidate; activation and consent unknown).
- External Provider Adapter Reference Architecture 0.1, §§2–7 (notification adapter and central authorization boundaries).
- WP5 Governance State & Decision Matrices 0.1; Batch 17/19 reconciliations.
- Contract 12 Protected-Action & WP6 Acceptance-Oracle Crosswalk 0.1.
- Artifact 07 Test-Case-Level Acceptance Manifest 0.1 and Batch 21/API-EVT crosswalks.

## 15. Change log

- 0.1 — Owner preference captured; major-approval-only Telegram design and staged implementation proposal prepared. Documentation only; no bot, credentials, repository changes, tests, agent dispatch, provider activation or external action.
