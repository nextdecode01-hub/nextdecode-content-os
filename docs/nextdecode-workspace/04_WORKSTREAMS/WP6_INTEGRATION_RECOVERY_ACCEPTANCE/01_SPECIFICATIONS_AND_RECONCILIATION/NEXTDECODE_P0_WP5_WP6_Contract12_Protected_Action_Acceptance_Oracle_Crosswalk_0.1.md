# NEXTDECODE P0 — Contract 12 Protected-Action & WP6 Acceptance-Oracle Crosswalk

**Document ID:** NEXTDECODE-P0-WP5-WP6-C12-A07-ORACLE-0.1  
**Version:** 0.1  
**Date:** 4 November 2026  
**Status:** WORKING TRACEABILITY CANDIDATE — OWNER / ACCEPTANCE REVIEW REQUIRED  
**Scope:** Contract 12 C12-01..07 against Artifact 07 v1.0 and WP6 acceptance oracles  
**Contract freeze:** NOT GRANTED  
**Implementation / test execution authorization:** NOT GRANTED

## 1. Purpose and boundary

This crosswalk advances the existing family-level Artifact 07 ↔ WP6 crosswalk into a protected-action and distribution-specific mapping. It reconciles Contract 12 v1.0 and its source reconciliation C12-01..07 against:
- Artifact 07 v1.0 §6, §7.2 and §7.3;
- WP6 Vertical Slice Integration, Recovery & Acceptance Validation 0.1;
- WP6 Acceptance Contract & Test Oracle Reconciliation 0.1;
- existing Artifact 07 ↔ WP6 Acceptance Traceability Crosswalk 0.1;
- Contract 07 / CF-20, CF-21, CF-22 governance boundary;
- Batch 19 persistence candidate and the B-WP1-04 governance entity/field mapping.

This is a documentation-only traceability artifact. It does not change Artifact 07 IDs/severity, freeze Contract 12 fields or states, define provider behavior, create a live publishing test, approve an environment, or authorize tests, agents, implementation, uploads or publishing.

## 2. Source authority and interpretation

1. Artifact 07 v1.0 §7.2 is authoritative for P0-A acceptance test IDs, expected results and severity.
2. Contract 12 v1.0 is authoritative for distribution-domain concepts and its own candidate operational boundaries, subject to accepted central governance decisions.
3. Contract 07 / CF-22 owns centralized authorization; Contract 12 cannot grant its own publishing authority.
4. WP6 IDs (VS, F, SEC, API-EVT, ENV) are traceability/oracle identifiers. They do not replace Artifact 07 requirements or severity.
5. Batch 19 and the Data Dictionary are persistence design references, not proof that fields or relationships are frozen.
6. If a source has no exact test oracle for a behavior, this crosswalk records the gap; it does not infer coverage from a nearby test name.

## 3. Protected-action invariant set

For any external upload, publish, schedule execution, update, delete, takedown or community action:
- authorization must come from the centralized authority at the protected-action boundary;
- the decision must be current, valid, unexpired and not revoked or paused;
- the decision must bind to the exact requested action, resource/version, package/version, destination/account and policy context as defined by owner-approved contracts;
- rights, QA hard blockers, disclosure/privacy/platform policy and account permission checks remain independent prerequisites;
- a schedule, prior approval, cached UI state, caller-provided ALLOW, event receipt or successful package validation is not an authorization grant;
- adapters, direct API calls, scripts, retries, manual tools and alternate workers cannot bypass the same boundary;
- public automatic publishing remains disabled absent a separate explicit owner-approved policy;
- accepted/queued, upload confirmed, publication confirmed and independently verified public visibility remain distinct outcomes;
- uncertain external outcomes require reconciliation before retry;
- emergency pause cannot be assumed to recall an already accepted external request.

The exact field names, token model, state transitions, signature/attestation method, provider lookup semantics and in-flight cancellation behavior remain open where not defined by accepted sources.

## 4. C12-01..07 to Artifact 07 / WP6 traceability

| Contract 12 issue | Contract 12 source | Artifact 07 authoritative tests | WP6 trace IDs / scenarios | Oracle status |
|---|---|---|---|---|
| C12-01 Authorization binding tuple | §§8.1, 8.4 | GV-01..GV-05, GV-11; GV-06/07 where QA/rights prerequisites apply | VS-18; F-11..F-16; SEC-G-01..11; API-EVT-25 for direct adapter bypass where applicable | Partial. Existing tests cover deny, expiry, revocation, resource/hash and destination/action mismatch, hard QA/rights gates and audit. Complete package/account/visibility/time/policy tuple and exact field representation still need owner-approved oracle. |
| C12-02 Upload vs publication vs visibility | §§9.1–9.2, 10, 14 | OP-01/OP-02 for evidence reconstruction; GV-12 only for public auto-publishing denial | API-EVT-19 for ambiguous external outcome; VS-17 for trace reconstruction; Contract 12 stages | Gap. Artifact 07 has no dedicated live visibility-state test in the bounded P0-A pre-distribution slice. Real platform visibility is out of scope. A simulator oracle may be proposed separately; do not claim live visibility coverage. |
| C12-03 PublishOperation vs WorkflowRun/Job/JobAttempt | §§9.2, 15; Contract 10 boundary | Q-01..Q-08; ST-01..ST-06; API-03/API-04; OP-01..OP-04 | VS-05..VS-10, VS-15..VS-17; F-01..F-05; API-EVT-01..23 as applicable | Partial. Durable orchestration and traceability are covered at requirement-family level. Exact PublishOperation-to-job/attempt cardinality and ownership remain open; no relationship is inferred here. |
| C12-04 Unknown provider outcome and retry | §9.3; Contract 10 recovery boundary | Q-05/Q-06; OP-02; API-03; API-06 where authorization is rechecked | API-EVT-19; F-03/F-04 only for their stated worker/event scenarios; controlled simulator only if separately approved | Gap / partial adjacent coverage. Existing F-03 is worker loss after output creation, not proof of provider-side publish reconciliation. No blind-retry oracle may be claimed from it. |
| C12-05 Emergency pause during in-flight provider request | §§8.1, 13 | GV-08 covers new protected actions blocked after pause; GV-01/GV-09 for denied action/bypass | F-11; VS-18; SEC-G family | Partial. New-action denial is represented. Post-submit in-flight cancellation, accepted-request behavior and reconciliation are not proven by GV-08. No assumption that a request can be recalled. |
| C12-06 ChannelAccount credentials and scope | §§4.2, 8.1 | GV-01/GV-05 for protected-action authorization context; WK-02/WK-03 apply only to worker credentials | SEC-W tests apply to worker identity only; SEC-G-01..11 apply to governance checks; account-specific oracle not explicit | Gap. Worker credentials are not ChannelAccount credentials. Token vault, account connection, granted scopes, expiry/revocation and account ownership require separate owner-approved control/test mapping. |
| C12-07 Update/delete/takedown/community actions | §§8.1, 8.4, 11, 13 | GV-01/GV-05, GV-08/GV-09, GV-11; API-06 | F-11..F-16/F-18 only for their exact stated scope; SEC-G suite | Partial. Generic protected-action denial and destination/action mismatch are covered; a canonical protected-action catalogue, per-action human-approval requirements, reversibility and community safety escalation are not frozen. |

**Severity preservation:** the Artifact 07 test IDs above retain the exact severity declared in Artifact 07 §7.2. This document does not reproduce or modify severity labels. WP6 proposed labels never downgrade Artifact 07 severity.

## 5. Exact oracle gaps and non-equivalence rules

### 5.1 No false coverage from adjacent tests

- F-03 is a worker-loss/output-reconciliation scenario; it is not a provider upload timeout test.
- F-11/GV-08 proves the specified pause-before-protected-action denial only; it does not prove cancellation of an already accepted provider request.
- WK-02/WK-03 cover worker credentials/identity; they do not establish ChannelAccount credential safety.
- GV-05 covers authorization for a different destination/action; it does not fully specify every operation type or platform scope.
- GV-12 proves public automatic publishing remains disabled/denied; it does not prove successful publication or public visibility.
- API-EVT-19 concerns ambiguous external outcome handling; it must be run only in a controlled simulator if included in approved scope, never against a real provider under this P0-A plan.

### 5.2 P0-A distribution boundary

Artifact 07 §6.2 expects a protected distribution request to be denied because no separate publishing authorization exists. Batch 10 §4 states P0-A stops at a human-approved pre-distribution boundary and excludes actual upload/public publishing. Therefore:
- a negative protected-action denial oracle is in P0-A;
- real account connection, upload, publication, scheduling execution, visibility verification, update/delete/takedown and community action are not implied P0-A tests;
- any simulator-only external-operation test requires explicit test scope, fixture and environment approval;
- no real platform credentials or outbound publishing paths may be used.

### 5.3 Authorization record dependency

B-WP1-04 records the unresolved AuthorizationDecision vs PublishingAuthorization model and DistributionOperation authorization reference. This crosswalk does not select an FK or field name. Before any persistence or implementation freeze, the owner must identify the authoritative authorization record and the exact reference consumed by the distribution operation.

## 6. Owner decision queue

| Decision ID | Required owner disposition | Depends on |
|---|---|---|
| C12-AO-01 | Approve canonical action/resource/version/package/account/destination/visibility/time/policy binding dimensions and exact field representation | CF-22, Contract 07, Data Dictionary, Batch 19, B-WP1-04 |
| C12-AO-02 | Define distinct internal and platform-observed upload/publication/visibility outcomes and evidence thresholds | Contract 12 §§9–10; lifecycle standard |
| C12-AO-03 | Decide PublishOperation relationship to WorkflowRun/Job/JobAttempt without duplicating execution authority | Contract 10, WP2, Batch 19 |
| C12-AO-04 | Define simulator-only unknown-provider-outcome oracle and when retry is permitted | Contract 12 §9.3, API-EVT-19, WP2 recovery |
| C12-AO-05 | Define emergency-pause scopes and behavior for not-yet-submitted vs already-submitted provider requests | Contract 07, Contract 12 §13, CF-22 |
| C12-AO-06 | Define ChannelAccount credential ownership, vault reference, scope, expiry/revocation and audit controls | Contract 12 §4.2, Contract 10/WP3 identity boundary, security |
| C12-AO-07 | Approve protected-action catalogue covering upload, schedule execution, publish, update, delete, takedown and community actions; define human-approval and escalation rules | Contract 07/WP5, Contract 12 §§8/11/13 |
| C12-AO-08 | Decide which additional distribution tests are supplemental vs deferred from P0-A; preserve Artifact 07 severity and mandatory status | Artifact 07, WP6, owner-approved P0 scope |

No owner decision is made in this document.

## 7. Documentation acceptance and evidence boundary

- [x] Contract 12 C12-01..07 mapped to exact Artifact 07 test IDs where direct coverage exists.
- [x] WP6 trace identifiers mapped without treating them as replacements for Artifact 07.
- [x] Gaps and adjacent-but-non-equivalent tests explicitly distinguished.
- [x] P0-A pre-distribution boundary preserved.
- [x] ChannelAccount credentials separated from worker credentials.
- [x] In-flight pause and provider unknown-outcome gaps retained.
- [x] Owner decision queue created.
- [ ] Owner dispositions recorded.
- [ ] Protected-action catalogue approved.
- [ ] Test-case-level manifest and any supplemental simulator oracle approved.
- [ ] Environment and test execution separately authorized.
- [ ] Tests executed and evidence reviewed.

No test has been run as part of this crosswalk. No PASS, acceptance, implementation readiness or production readiness is claimed.

## 8. Authorization and coordination restrictions

This document does not authorize repository access or modification, tests, commands against the project repo, Git operations, agent dispatch, provider connection, credentials, spending, deployment, real upload, publishing, external communications or account actions.

Agent roles remain unchanged: Qoder sole writer for the current governance-closure milestone when separately authorized; OpenCode read-only API/backend review; Copilot focused regression review; Kilo independent read-only QA after implementation/evidence is authorized and complete; Antigravity conditional targeted UI only. No agent is dispatched by this crosswalk.

**Handoff:** C12-01..07 are mapped to Artifact 07/WP6 with direct coverage, partial coverage and genuine gaps distinguished. Owner review and exact oracle decisions remain required before any protected distribution implementation or test execution.

