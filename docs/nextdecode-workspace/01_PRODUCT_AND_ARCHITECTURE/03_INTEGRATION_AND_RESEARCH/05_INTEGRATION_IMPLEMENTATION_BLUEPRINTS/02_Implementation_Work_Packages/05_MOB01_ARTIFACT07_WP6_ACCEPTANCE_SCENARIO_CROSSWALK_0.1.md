# MOB-01 — Artifact 07 / WP6 Acceptance Scenario Crosswalk
## Proposal 0.1 — Documentation only

**Document ID:** NEXTDECODE-INT-MOB01-A07-WP6-XREF-0.1
**Status:** WORKING TRACEABILITY CANDIDATE — OWNER / QA REVIEW REQUIRED
**Authority:** Artifact 07 v1.0 §7.2 controls IDs, expected results and severity; WP6 crosswalks control traceability interpretation.
**Test execution / environment approval:** NOT GRANTED

## 1. Purpose and boundaries

This crosswalk maps the proposed Telegram MOB-01 security and interaction scenarios to existing Artifact 07 IDs and WP6 trace identifiers where the source evidence supports a relationship. It does not create or rename tests, alter severity, assert full coverage from adjacent tests, approve P0-A scope, authorize test execution or claim any test passed.

Sources reviewed:
- MOB-01 Telegram Major-Approval Security & Interaction Contract 0.1.
- Artifact 07 Test-Case-Level Acceptance Manifest 0.1; Artifact 07 v1.0 §7.2 remains authoritative.
- API-EVT-01..25 to Artifact 07 Test Oracle Crosswalk 0.1.
- Contract 12 Protected-Action & WP6 Acceptance-Oracle Crosswalk 0.1.
- WP6 Acceptance Contract & Test Oracle Reconciliation 0.1 and Vertical Slice Integration, Recovery & Acceptance Validation 0.1.
- Batch 21 Observability ↔ Artifact 07 crosswalk 0.1.

**Interpretation:** Direct = the existing test's authoritative expected result materially exercises the same security property. Partial = adjacent evidence exists but does not prove the full Telegram-specific behavior. Gap = no exact existing oracle. Supplemental = useful operational evidence, not a replacement for Artifact 07.

## 2. Scenario-to-oracle mapping

| MOB-01 scenario | Artifact 07 ID(s) | Existing WP6 trace / companion | Status | Boundary / missing proof |
|---|---|---|---|---|
| Owner identity is authenticated and bound to the intended account | WK-01..WK-03 (worker identity only) | VS-08; F-08/F-09; SEC-W-02/03 | PARTIAL | Worker authentication/expiry/revocation is not Telegram account pairing, numeric account binding or proof of private-chat ownership. |
| Unbound, wrong, revoked or mismatched Telegram account cannot decide | API-06; GV-09 (adapter bypass); WK-03 (adjacent) | F-08; SEC-W-02; F-18; SEC-G-09; API-EVT-25 | PARTIAL | No exact Telegram sender/chat binding oracle; must test private chat, account mismatch and revoked bot binding separately if approved. |
| Group, forwarded-message and wrong-chat interactions rejected | None exact | No direct Telegram-specific trace | GAP | Artifact 07 has no explicit group/forwarded Telegram context case. |
| Username/display-name spoofing does not establish identity | None exact | No direct Telegram-specific trace | GAP | Need exact identity proof oracle; do not infer from worker identity tests. |
| Callback reference cannot authorize another workspace, request or artifact version | GV-04/GV-05 (authorization target mismatch); AR-04 (artifact scope) | F-13/F-14; SEC-G-04/05; SEC-A-02 | PARTIAL | These cover authorization hash/destination or artifact scope mismatches, not Telegram callback-to-request binding end-to-end. |
| Stale/expired/revoked/superseded request or old artifact version is rejected | ST-03; GV-02/GV-03/GV-04; AR-05 | F-05 (worker fencing only); SEC-G-02/03/04; VS-12/13 | PARTIAL | Stale state, authorization expiry/revocation and artifact immutability are adjacent; no exact stale Telegram callback/request oracle. |
| Duplicate Telegram update/callback cannot create a second decision | API-03; Q-05 | F-04; API-EVT-08..10 | PARTIAL | Event deduplication is not automatically equivalent to command/callback idempotency. API-EVT-04/05 are closer command-idempotency companions but remain distinct from transport update dedup. |
| Concurrent taps produce at most one canonical decision | ST-04; API-03 (not concurrency by itself) | API-EVT-04/05 (command idempotency) | PARTIAL / GAP | ST-04 concerns concurrent state updates; API-EVT-04/05 cover command idempotency. Exact concurrent Telegram callback oracle and persistence constraint remain unspecified. |
| Backend timeout / unknown durable result is reconciled without duplicate decision | Q-05; OP-02 (broad diagnostics only) | API-EVT-19 (simulator-only if separately approved) | GAP / PARTIAL | No Artifact 07 test proves Telegram callback unknown-outcome reconciliation. API-EVT-19 is not a real provider test and requires separate simulator scope. |
| Rights, quality, lifecycle and policy hard blockers prevent approval | GV-06/GV-07; ST-02; GV-01 | F-15/F-16; SEC-G-06/07; F-12; SEC-G-01 | DIRECT for underlying gates | Must verify Telegram adapter routes through the same canonical gate; existing tests alone do not prove adapter integration. |
| Notification delivery/read status does not change canonical state | None exact | No direct WP6 trace | GAP | Requires a dedicated notification-only invariant oracle; delivery is not a domain decision. |
| Bot disable/revocation prevents new interactions | WK-03 (worker revocation only); API-06/GV-09 (generic denial) | F-08; SEC-W-02; F-18; SEC-G-09 | PARTIAL | Bot credential/binding revocation and callback invalidation are not the same as worker revocation. |
| Audit evidence identifies actor, request, exact target/version and durable outcome | API-04; ST-05; OP-01/OP-02 (as applicable) | VS-17; API-EVT-21..23; OBS-T01/02 | PARTIAL | Correlation continuity and transition history are not a complete Telegram decision audit oracle; API-LC-03/05 remain open. |
| Webhook forgery/replay is rejected | None exact | API-EVT-24 | GAP / DEFERRED | API-EVT-24 has no exact Artifact 07 equivalent and webhook scope/protocol is open under API-LC-09. No webhook exposure authorized. |
| Callback payload/notification does not leak secrets or private content | WK-07 (log-secret redaction); API-EVT-16 | SEC-W-10; OP-05; ENV-09; API-EVT-16 | PARTIAL | Log redaction and API payload minimization do not prove Telegram chat content minimization or provider-side message privacy. |
| Telegram interaction cannot create PublishingAuthorization or trigger protected side effect by itself | GV-01/GV-09; API-06 | F-12; SEC-G-01; F-18; SEC-G-09; API-EVT-25; VS-18 | DIRECT for central protected-action denial; PARTIAL for Telegram adapter | Existing tests cover central denial and adapter bypass at a generic boundary; Telegram-specific adapter integration still needs evidence. |
| P0-A remains pre-distribution; public upload/publishing remains disabled | GV-01/GV-12 | F-12; SEC-G-01; VS-18; Contract 12 crosswalk | DIRECT for denial boundary | Does not authorize or prove successful publishing, platform visibility or real provider integration. |

## 3. Critical non-equivalences to preserve

1. Event deduplication (Q-05 / F-04) is not command idempotency or Telegram callback idempotency (API-EVT-04/05).
2. Worker identity/revocation (WK-01..03) is not Telegram owner-account pairing, bot credential revocation or private-chat verification.
3. Artifact hash/destination authorization mismatch (GV-04/05) is not end-to-end binding of a Telegram callback to a canonical pending request and exact review version.
4. Worker lease fencing (F-05) is not stale approval-request rejection.
5. Generic audit/correlation continuity (API-04 / VS-17 / API-EVT-21..23) is not a complete mobile decision audit record.
6. Secret redaction in logs (WK-07) is not proof that chat messages, notification previews or provider-side message storage are privacy-safe.
7. Generic protected-action denial (GV-01/GV-09) is not proof of Telegram adapter integration, and is not permission to publish.

## 4. MOB-01 mapping gaps requiring explicit closure

- MOB-A07-01: Telegram private-account pairing, wrong-chat, group and forwarded-message rejection.
- MOB-A07-02: callback/request/version binding and stale/expired/superseded callback rejection.
- MOB-A07-03: callback command idempotency, duplicate Telegram update and concurrent tap behavior.
- MOB-A07-04: uncertain backend write outcome and reconcile-before-retry.
- MOB-A07-05: notification delivery/read state does not mutate canonical approval state.
- MOB-A07-06: bot binding/token revocation and outstanding callback invalidation.
- MOB-A07-07: exact Telegram decision audit record and API-LC-03/05 correlation semantics.
- MOB-A07-08: Telegram chat payload privacy and secret minimization.
- MOB-A07-09: webhook signature/replay oracle only if webhook is later approved; otherwise explicitly deferred.
- MOB-A07-10: prove the Telegram adapter routes to central rights/quality/authorization gates without creating a local approval authority.

These gaps are not new Artifact 07 IDs. They are candidate closure items for owner/QA review. Any new mandatory P0-A test requires the applicable owner approval and a governed Artifact 07 amendment; do not silently add tests to the authoritative manifest.

## 5. Scope, status and authorization

- All Artifact 07 tests remain NOT_RUN.
- All API-EVT companion tests remain NOT_RUN.
- No environment, fixture, command or test execution is approved.
- API-EVT-19 remains simulator-only if separately approved; never call a real provider.
- API-EVT-24 remains deferred unless webhook exposure is explicitly included and API-LC-09 is resolved.
- P0-A protected distribution remains denied absent separate authorization; actual upload/public publishing remains outside this mobile slice.
- No bot, token, transport, repository change, code, agent, provider activation, deployment, spending, upload or publishing is authorized.

## 6. Owner / QA disposition checklist

- [x] Existing Artifact 07 and WP6 sources inspected.
- [x] Direct, partial and missing mappings distinguished.
- [x] Non-equivalent adjacent tests called out.
- [x] Telegram-specific acceptance gaps enumerated without inventing Artifact 07 IDs.
- [ ] Owner/QA approves scope and mapping.
- [ ] MOB-A07-01..10 are closed, explicitly deferred or promoted through a governed test change.
- [ ] API-LC-03/05/09 and CF-21/CF-22 dependencies resolved as applicable.
- [ ] Security/privacy review completed.
- [ ] Separate environment and test-execution authorization obtained.
- [ ] Tests executed and immutable evidence reviewed.

**Disposition:** Traceability candidate only. The existing acceptance suite gives useful partial/direct coverage for central governance gates, worker identity, artifact integrity and generic adapter bypass. It does not currently prove Telegram-specific pairing, callback idempotency, stale request handling, privacy or webhook security end-to-end.
