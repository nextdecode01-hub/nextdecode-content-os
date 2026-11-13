# NEXTDECODE MOB-DEC-01 — Owner Decision Record

**Document ID:** NEXTDECODE-INT-MOB-DEC-01-OWNER-RECORD-0.1  
**Version:** 0.1  
**Decision date:** 5 November 2026 (Asia/Kolkata)  
**Decision owner:** Product owner  
**Decision:** MOB-DEC-01 — Telegram identity pairing and recovery  
**Status:** OWNER DECISION RECORDED — OPTION B SELECTED  
**Authority:** Owner disposition for MOB-01 only; subordinate to accepted P0 decisions, canonical contracts and Artifact 10.

## 1. Exact owner disposition

The owner explicitly selected **Option B — Authenticated-session pairing plus independent step-up**.

Approved direction:
- Pair the private Telegram account through an authenticated Content OS session.
- Require independent step-up verification for account recovery.
- Require independent step-up verification for decisions classified as high-risk.
- Telegram username, display name or profile information alone must never establish identity.
- Telegram-only recovery is not permitted.

The owner's confirmation was: **“B go”**, following a comparison of options A, B and C and a recommendation explaining the security/convenience trade-off.

## 2. Rationale recorded from the decision discussion

Option B was recommended because a compromised Telegram session should not become a route around Content OS identity and governance controls. It provides stronger assurance for recovery and high-risk decisions while retaining Telegram as a convenient interaction interface. The owner explicitly approved that option.

## 3. Scope and interpretation limits

This is a high-level policy direction, not a complete authentication protocol. It does not select:
- the independent factor or step-up mechanism;
- risk classification or the list of high-risk decisions;
- session lifetime, freshness thresholds or challenge expiry;
- pairing token format, storage or revocation implementation;
- canonical identity fields, schema, API/event envelope or provider transport.

Those details remain subject to WP1/WP3, API/Event, security/privacy and canonical contract reconciliation.

## 4. Invariants preserved

- Content OS backend remains authoritative; Telegram cannot grant itself authority.
- Exact request, workspace, artifact/review version and current policy must be revalidated server-side.
- Rights, quality, lifecycle and central authorization gates remain mandatory.
- Content approval remains distinct from publishing authorization.
- Public automatic publishing remains disabled absent separate explicit authorization.
- Desktop review remains an available fallback.
- Fail-closed behavior applies to stale, duplicate, expired, revoked, superseded or uncertain interactions.

## 5. Remaining decisions and dependencies

- MOB-DEC-02 through MOB-DEC-07 remain OPEN.
- GOV-09 remains OPEN; this decision does not decide the AuthorizationDecision/PublishingAuthorization record relationship.
- CF-21/CF-22 detailed semantics, API-LC-03/05/09, Contract 12, WP1/WP2/WP3/WP5/WP6 and Artifact 07 acceptance dependencies remain open.
- SEC-MOB-01..09 findings are not automatically closed by this high-level owner selection. In particular, SEC-MOB-02 still requires detailed pairing/recovery/step-up design and evidence.

## 6. Authorization boundary

This owner decision does **not** authorize:
- Telegram bot creation or token/credential requests;
- transport selection or provider activation;
- repository/source-code changes or tests;
- agent dispatch;
- deployment, spending, upload or publishing;
- canonical contract freeze or schema/API/event changes.

Any such work requires its own explicit authorization under Artifact 10 and the applicable project gates.

**Recorded disposition:** MOB-DEC-01 Option B — SELECTED.  
**Other MOB decisions:** OPEN.  
**GOV-09:** OPEN — no owner disposition recorded.
