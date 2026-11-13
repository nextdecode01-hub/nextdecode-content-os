# MOB-DEC-02 — API/Event & WP6 Dependency Crosswalk
**Document ID:** NEXTDECODE-INT-MOB-DEC02-API-WP6-XREF-0.1  
**Version:** 0.1  
**Date:** 5 November 2026 (Asia/Kolkata)  
**Status:** DOCUMENTATION-ONLY DEPENDENCY MAP — API-LC-01..10 OWNER DECISIONS OPEN  
**Related records:** REG-073, REG-074, REG-075, GAP-041, GAP-043  
**Implementation / test / contract freeze:** NOT AUTHORIZED

## 1. Purpose
Identify which API/Event and WP6 contracts must be reconciled before a Path A workflow disposition could ever be represented or operated. This document maps dependencies; it does not choose API-LC options, amend standards, create test IDs or authorize execution.

## 2. Source handoff
| Source | Relevant authority |
|---|---|
| API/Event & Unified Lifecycle Cross-Contract Reconciliation 0.1 | Common message semantics, command commit, delivery/recovery and API-LC-01..10 |
| API/Event & Lifecycle Owner Decision Matrix 0.1 | API-LC-01..10 remain owner agenda; no option selected |
| WP6 Batch 21 / Artifact 07 Observability Acceptance Crosswalk 0.1 | OBS-T01..T20 mapping; candidate only, tests not run |
| WP6 API-EVT-01..25 Artifact 07 Test Oracle Crosswalk 0.1 | Existing API/Event acceptance oracles; candidate crosswalk, execution not authorized |
| MOB-DEC-02 lifecycle crosswalk 0.1 / REG-075 | Path A lifecycle boundary and open dependencies |
| Contract 07 1.0 | Governance, approval, publishing authorization, risk and audit semantics |

## 3. API-LC dependency mapping
| Decision | Relationship to Path A | What must remain unresolved / safe handling |
|---|---|---|
| API-LC-01 event_version vs schema_version | Any future disposition event or audit message would need versioned semantics and payload shape | Do not choose one or conflate semantic event revision with schema revision |
| API-LC-02 multiple events per state_version | A single internal workflow transition may cause more than one audit/notification fact | Do not assume one event per state version or assign sequence numbers; define authoritative transition fact vs secondary facts first |
| API-LC-03 correlation_id / causation_id | A disposition must be traceable to its triggering request/command/event and prior decision evidence | Nullability, root-origin behavior and typed-reference representation remain OPEN; no guessed IDs or nullable rules |
| API-LC-04 state_version scope | Any state-changing command or event must use the owning state machine's version authority | Per entity/state-machine versus other scope remains OPEN; do not assign a version counter in this crosswalk |
| API-LC-05 request_id / trace_id propagation | The owner enablement, timeout trigger, workflow request and resulting disposition may span API, async work and event boundaries | Keep request_id, correlation_id, causation_id and trace_id semantically distinct; exact propagation requirements remain OPEN |
| API-LC-06 outbox/inbox retention and redrive | Future durable disposition facts may need replay, retention and evidence recovery | No retention duration, redrive role or cleanup behavior inferred |
| API-LC-07 poison message and replay controls | Duplicate/stale/malformed disposition triggers must not cause duplicate internal transitions | Quarantine, replay authority and duplicate-effect controls remain OPEN |
| API-LC-08 schema compatibility | Any future contract addition must respect compatibility and consumer rollout policy | No field or schema is added; compatibility policy remains OPEN |
| API-LC-09 webhook authentication/replay | Relevant only if a webhook transport is later selected for Telegram or another ingress | Transport remains unselected; no webhook exposure, secret/header, nonce or signature design is approved here |
| API-LC-10 external side-effect outcome envelope | Path A explicitly excludes external side effects; publishing/upload outcomes remain separate | Do not merge internal disposition with PublishOperation, JobAttempt or external outcome; unknown external outcomes require separate reconciliation |

**Primary blockers for Path A representation:** API-LC-02/03/04/05/06/07/08 where event/state/audit representation is needed. API-LC-09 is a Telegram ingress activation blocker if webhook is selected. API-LC-10 preserves the external-outcome boundary. This is dependency relevance, not a proposed priority change or owner disposition.

## 4. WP6 observability and acceptance mapping
| Existing oracle | Relevant Path A concern | Mapping status / limit |
|---|---|---|
| OBS-T01 / Artifact 07 API-04 / WP6 VS-17, API-EVT-21..23 | Correlation propagation across request, workflow, job and artifact | Strong conceptual relevance; API-LC-03/05 exact rules still open |
| OBS-T02 / Artifact 07 API-04, ST-05 / WP6 VS-17 | Causation from triggering command/event | Strong conceptual relevance; typed/nullability semantics open |
| OBS-T04 / Artifact 07 WK-07, OP-05 / SEC-W-10, ENV-09 | Secret redaction | Direct supporting oracle; no credential or provider use authorized |
| OBS-T06 / Artifact 07 API-06 / API-EVT-16..17 | Untrusted external trace headers and trusted correlation | Partial/supplemental; security owner must approve trust semantics |
| OBS-T13 / Artifact 07 GV-01..GV-05 / F-11..F-16, SEC-G-01..05, VS-18 | Authorization denial traceability | Strong conceptual relevance; CF-22 exact evidence model remains open |
| OBS-T16 / Artifact 07 ST-05, OP-02, OP-04 / VS-17 | Attributable recovery action and audit | Strong conceptual relevance; no recovery action or test execution authorized |
| API-EVT-19 / Contract 12 C12-AO-04 | Unknown external outcome | Boundary evidence only; Path A cannot trigger or settle external outcomes |

The crosswalks are traceability aids. No OBS-T or API-EVT case is declared passed. Artifact 07 remains authoritative for P0 acceptance IDs and severity. MOB-A07-01..10 remain candidate closure items, not new canonical test IDs.

## 5. Telegram-specific ingress boundary
- Telegram is an interaction/notification surface; Content OS remains authoritative.
- A callback or webhook payload is untrusted input, not proof of owner identity, approval, authorization or causation.
- If webhook transport is ever proposed, API-LC-09 and SEC-MOB-04 must be closed first; pairing, callback integrity, replay protection, transport/runtime and privacy blockers SEC-MOB-01..09 remain open.
- If a non-webhook transport is considered, its own polling identity, checkpoint, replay and recovery model still requires owner/security review.
- No transport has been selected; no bot, token, credential, provider activation or inbound endpoint is authorized.

## 6. Required next decisions and handoffs
1. Product/API-Event owner resolves API-LC-03 and API-LC-05 semantics before any disposition audit/event contract is drafted.
2. API-Event/Lifecycle owners resolve API-LC-02 and API-LC-04 before defining transition event multiplicity or version scope.
3. WP2/WP6/security owners resolve API-LC-06/07/08 recovery, replay and compatibility constraints.
4. Telegram security owner resolves API-LC-09 only after transport comparison; do not assume webhook.
5. WP5/Contract 07 owner decides whether a separate workflow-disposition concept needs a canonical record and how it relates to GovernanceDecision without merging with CF-21.
6. WP6/QA reviews existing Artifact 07/API-EVT/OBS mappings and identifies genuine missing oracles through governed change; no duplicate IDs or test execution.
7. Contract 12/WP2/WP6 keep API-LC-10 external outcome handling separate from internal workflow progression.

## 7. Acceptance checks for this documentation package
- API-LC-01..10 are mapped without selecting any option.
- Request, correlation, causation and trace identities remain distinct.
- Telegram callback/webhook input is treated as untrusted.
- Existing WP6/Artifact 07 references retain their authoritative IDs and candidate status.
- No new test ID, event, schema field, API, entity, enum, state or transition is introduced.
- External side effects and publishing authorization remain outside Path A.

**Result:** Path A has a documented API/Event and WP6 dependency map. API-LC-01..10 remain OPEN; no canonical event or lifecycle representation is approved.

## 8. Authorization boundary
Documentation-only. No repository/source-code changes, tests, contract freeze, agent dispatch, Telegram bot/tokens/credentials/provider activation, deployment, spending, production generation, upload or publishing is authorized. All Artifact 10 restrictions and existing human approval, central authorization, rights, quality, exact-version and emergency controls remain in force.
