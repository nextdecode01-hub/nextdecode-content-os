# NEXTDECODE P0 — API-EVT-01..25 to Artifact 07 Test Oracle Crosswalk

**Document ID:** NEXTDECODE-P0-API-EVT-A07-XREF-0.1  
**Version:** 0.1  
**Date:** 4 November 2026  
**Status:** WORKING TRACEABILITY CANDIDATE — OWNER / QA REVIEW REQUIRED  
**Authority:** Artifact 07 v1.0 §7.2 controls P0 acceptance IDs, expected results and severity  
**Execution authorization:** NOT GRANTED

## 1. Purpose

This crosswalk reconciles the 25 proposed API-EVT tests in API/Event Contract Reconciliation 0.1 §13 with the authoritative Artifact 07 acceptance tests and WP6 VS/F/SEC suites.

The API-EVT identifiers are companion conformance tests, not new Artifact 07 requirements. A mapping is considered direct only where the Artifact 07 oracle materially proves the same behavior. A shared theme (for example, idempotency, retry or versioning) is not enough to claim equivalence.

## 2. Source precedence and method

1. Artifact 07 v1.0 §7.2 — authoritative P0 acceptance IDs, expected outcomes and severity.
2. WP6 Acceptance Contract & Test Oracle Reconciliation 0.1 §§4–9, 13–14 — candidate VS/F/SEC/API-EVT oracles, fixture/environment safeguards and companion test relationships.
3. API/Event Contract Reconciliation 0.1 §§3–16 — API-EVT-01..25 scenarios and expected oracles.
4. API/Event + Unified Lifecycle Cross-Contract Reconciliation 0.1 — common envelope, version, causation, replay and state-version semantics.
5. Batch 21 and the observability crosswalk — supplemental diagnostics/operations evidence only.

The mapping does not change Artifact 07 IDs, severity or source wording. It does not establish that any test ran. All tests remain NOT_RUN.

## 3. API-EVT-01..25 crosswalk

| API-EVT ID | API/Event scenario and expected oracle | Related Artifact 07 ID(s) | Related WP6 trace | Relationship | Mapping note / limitation |
|---|---|---|---|---|---|
| API-EVT-01 | Query attempts mutation; rejected/no mutation and state/version unchanged | API-01 (partial) | VS-16; API-EVT-01 | Partial | API-01 is malformed-request rejection, not query/command separation. Add a distinct oracle if query mutation must be mandatory P0. |
| API-EVT-02 | Async command returns ACCEPTED with durable job/workflow reference; no completion implied | Q-01 (partial) | VS-06; VS-04..06 | Partial | Q-01 proves durable job creation, not full HTTP/command outcome semantics or response reference. |
| API-EVT-03 | Invalid command schema; stable machine-readable validation error and no state/outbox mutation | API-01 | SEC-W-05; API-EVT-01..07 | Direct/partial | API-01 malformed request rejection is closest; confirm the fixture specifically exercises command schema validation and no mutation. |
| API-EVT-04 | Same idempotency key and same canonical payload returns original logical result | No exact Artifact 07 equivalent | API-EVT-01..07 | GAP | Duplicate event delivery (API-03/Q-05) is not command idempotency. Keep separate companion test. |
| API-EVT-05 | Same idempotency key with changed payload conflicts; no second operation | No exact Artifact 07 equivalent | API-EVT-01..07 | GAP | Requires command fingerprint/idempotency oracle; do not infer from event deduplication or stale-version rejection. |
| API-EVT-06 | Stale expected_state_version yields structured conflict; no overwrite or event | ST-03 (partial), ST-04 (partial) | F-05 only for stale worker callback; API-EVT-01..07 | Partial | F-05 proves stale lease/attempt fencing, not generic API expected-state-version conflict. Keep separate API-level evidence. |
| API-EVT-07 | Producer transaction rollback leaves no committed state transition or publishable outbox event | ST-01 (partial) | F-01; API-EVT-01..07 | Partial | Restart durability is not atomic rollback proof. Needs explicit transaction-failure oracle. |
| API-EVT-08 | Duplicate event delivery produces one consumer logical effect | API-03 | F-04; API-EVT-08..10 | Direct | Same duplicate-event/idempotent-consumer behavior. Evidence must show one logical effect, not just duplicate receipt. |
| API-EVT-09 | Out-of-order event does not regress state; version gap triggers authorized reconciliation | ST-03/ST-04 (partial) | API-EVT-08..10; API-EVT-21..23 | Partial | No Artifact 07 oracle fully proves out-of-order event reconciliation. Preserve separate companion oracle. |
| API-EVT-10 | Unknown event type does not crash consumer; safely isolated/observed | API-02 (partial) | API-EVT-08..10 | Partial | API-02 concerns unsupported schema version, not unknown event type. Distinct unknown-event behavior remains. |
| API-EVT-11 | Unsupported required schema version safely rejected/quarantined | API-02 | SEC-W-04; API-EVT-11..13 | Direct | Same unsupported contract/schema version behavior; pin exact schema-version fixture. |
| API-EVT-12 | Unknown optional field tolerated without semantic change | No exact Artifact 07 equivalent | API-EVT-11..13 | GAP | API-02 rejects unsupported schema version; it does not prove additive optional-field compatibility. |
| API-EVT-13 | Breaking schema change without version/migration fails compatibility check | API-02 (partial) | API-EVT-11..13 | Partial | Unsupported version rejection is related but does not prove compatibility checker detects unversioned breaking change. |
| API-EVT-14 | Replay preserves original event identity/timestamps and does not repeat external effects | No exact Artifact 07 equivalent | API-EVT-14..15 | GAP | No Artifact 07 replay test is listed. Requires separately approved replay scope and side-effect suppression oracle. |
| API-EVT-15 | Replay cannot cause protected action without current action-specific authorization | GV-01 (partial) | F-12; SEC-G-01; VS-18 | Partial | GV-01 proves missing authorization denial, not specifically replay-handler suppression. Do not treat as replay proof. |
| API-EVT-16 | Secret fixture in event payload rejected/redacted before publication; absent from logs | WK-07, OP-05 | SEC-W-10; ENV-09; OBS-T04 | Direct/partial | Artifact 07 log redaction is direct for logs; payload publication prevention requires a separate API/event schema/security assertion. |
| API-EVT-17 | Cross-workspace request/message denied; no leakage or state change | WK-06, AR-04 | SEC-A-02; API-EVT-16..17 | Direct/partial | Artifact 07 artifact cross-workspace denial is direct for artifact access; API/event boundary scope needs its own evidence. |
| API-EVT-18 | Poison message isolated with bounded attempts and diagnostic evidence | Q-06 (partial) | API-EVT-18; Batch 21 OBS-T03 | Partial | Retry-limit terminal handling is not equivalent to poison-message quarantine/redrive. Exact dead-letter policy remains open. |
| API-EVT-19 | Provider timeout after possible submission yields UNKNOWN_OUTCOME and blocks unsafe retry | No exact Artifact 07 equivalent | API-EVT-19; Contract 12 C12-AO-04 | GAP | Keep outside P0-A unless owner explicitly includes controlled simulator-only scope. Never call a real provider. |
| API-EVT-20 | Revoked worker retry is reauthorized and denied | WK-03 | F-08; SEC-W-02 | Direct | Same revoked-worker denial for new claims/access; prove no protected transition or lease mutation. |
| API-EVT-21 | Command rejection has stable error code, safe message and request ID | API-01 (partial), OP-02 (partial) | API-EVT-21..23; OBS-T03 | Partial | Artifact 07 API-01 is malformed-request rejection; OP-02 diagnostics are broad. Exact envelope fields need explicit evidence. |
| API-EVT-22 | Correlation preserved across command/job/event; causation points to immediate parent | API-04, OP-01 | VS-17; API-EVT-21..23; OBS-T01/02 | Direct/partial | API-04/OP-01 prove trace continuity; exact causation-parent semantics remain API-LC-03 and need dedicated oracle. |
| API-EVT-23 | Event state-version gap triggers owner-authorized reconciliation; no invented state | ST-03 (partial), ST-05 (partial) | API-EVT-21..23; VS-17 | Partial | ST-03 stale-version and ST-05 history do not alone prove event-gap reconciliation. |
| API-EVT-24 | Webhook invalid signature/replay rejected without side effect | No exact Artifact 07 equivalent | API-EVT-24 | GAP | Webhook exposure is optional/deferred unless explicitly included; signature/nonce/replay protocol remains open. |
| API-EVT-25 | Direct adapter publishing bypass denied by central authorization; no external request | API-06, GV-09 | F-18; SEC-G-09 | Direct | Same direct adapter/pipeline bypass. Must capture egress/no-request evidence, not merely a denial response. |

## 4. Consolidated gap disposition

| Gap ID | API-EVT ID(s) | Required distinct oracle | Suggested scope disposition |
|---|---|---|---|
| API-XREF-01 | 01 | Query/command separation and mutation denial | Add to P0 only if command/query ownership is mandatory acceptance; otherwise companion contract conformance |
| API-XREF-02 | 04–05 | Command idempotency same-payload replay and changed-payload conflict | Keep as distinct companion API/Event tests; Artifact 07 currently has no exact equivalent |
| API-XREF-03 | 06 | API expected-state-version conflict and no outbox mutation | Keep distinct from F-05 worker fencing; map to ST-03/04 only as partial |
| API-XREF-04 | 07 | Atomic state + outbox rollback behavior | Keep distinct from restart durability |
| API-XREF-05 | 09–10 | Out-of-order version-gap reconciliation and unknown event isolation | Preserve separate tests; Artifact 07 mappings are partial |
| API-XREF-06 | 12–13 | Optional-field compatibility and unversioned breaking-change detection | Companion compatibility suite; API-02 only partially related |
| API-XREF-07 | 14–15 | Replay identity/timestamp preservation and suppression of external side effects | Scope-gated; side-effecting replay remains prohibited absent fresh authorization |
| API-XREF-08 | 16–17 | Payload secret minimization and API/event workspace scope | Artifact 07 log/artifact cases are partial; dedicated message-boundary proof required |
| API-XREF-09 | 18 | Poison-message isolation, bounded redrive and audit | Distinct from generic retry-limit terminal handling; policy owner decision needed |
| API-XREF-10 | 19 | Unknown external outcome and reconciliation-before-retry | Controlled simulator only if separately approved; not P0-A live-provider test |
| API-XREF-11 | 21–23 | Exact error envelope, causation parent and version-gap reconciliation | Existing OP/API tests partial; pin exact field-level oracles and owner-approved lifecycle constraints |
| API-XREF-12 | 24 | Webhook signature, nonce/timestamp and replay protection | Defer until webhook exposure is in approved scope and protocol is frozen |
| API-XREF-13 | 25 | Adapter bypass denial with outbound egress proof | Direct mapping to API-06/GV-09; ensure evidence includes no external request |

## 5. Manifest integration rules

The Artifact 07 test-case manifest may record API-EVT references as supplemental companion coverage, subject to QA review. It must not:
- change Artifact 07 IDs or severity;
- count API-EVT-04/05 as covered by Q-05 event dedup;
- count API-EVT-06 as covered solely by F-05 worker fencing;
- count API-EVT-07 as covered by F-01 restart durability;
- count API-EVT-10 as covered solely by API-02 unsupported schema version;
- count API-EVT-14/15 as covered by GV-01 without replay-specific evidence;
- count API-EVT-18 as covered by Q-06 without poison isolation/redrive evidence;
- count API-EVT-19 as an executed provider test;
- count API-EVT-24 as in scope without webhook approval;
- count API-EVT-22 as full causation proof when only correlation continuity is evidenced.

One execution may satisfy multiple requirements only where the evidence demonstrates every oracle.

## 6. Test environment and evidence restrictions

- All API-EVT tests remain NOT_RUN.
- No test command or environment is selected or approved.
- ENV-01..14 from WP6 remain the pre-execution gate.
- Use synthetic fixtures only; no production or personal data.
- API-EVT-19 must be simulator-only if separately approved; no real provider.
- API-EVT-24 is deferred unless webhook exposure is explicitly included and protocol approved.
- API-EVT-14/15 replay must not re-trigger side effects by default.
- Preserve exact request/event/schema/state/policy versions, IDs, before/after state, outbox/inbox disposition and sanitized logs.
- No provider, broker, schema registry, framework or infrastructure choice is made.
- No implementation, repository inspection, test execution, agent dispatch, deployment, spending, upload or publishing is authorized.

## 7. Owner/QA review checklist

- [x] All API-EVT-01..25 scenarios represented.
- [x] Existing Artifact 07 IDs retained; no replacement test IDs created.
- [x] Direct, partial and missing mappings distinguished.
- [x] Similar-but-not-equivalent cases explicitly separated.
- [x] Unknown external outcome and webhook exposure scope-gated.
- [ ] Approve which companion API-EVT tests are mandatory P0-A versus supplemental/deferred.
- [ ] Resolve API-LC-01..10 envelope/lifecycle decisions before detailed contract freeze.
- [ ] Approve exact API/event fixture and evidence schema.
- [ ] Approve isolated environment and test-only parameters.
- [ ] Separately authorize test execution.
- [ ] Execute tests and create immutable evidence records.
- [ ] Independent Kilo read-only QA after evidence exists.
- [ ] Product owner acceptance/rejection.

**Disposition:** API-EVT-01..25 to Artifact 07 traceability candidate created. Several mappings are partial or genuinely uncovered; no test is claimed as run or passed. Detailed contract freeze and test execution remain NOT AUTHORIZED.

