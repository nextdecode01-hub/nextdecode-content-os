# NEXTDECODE P0 — Artifact 07 Test-Case-Level Acceptance Manifest

**Document ID:** NEXTDECODE-P0-A07-TEST-MANIFEST-0.1  
**Version:** 0.1  
**Date:** 4 November 2026  
**Status:** PROPOSED TRACEABILITY MANIFEST — OWNER / QA REVIEW REQUIRED  
**Authority:** Artifact 07 v1.0 §7.2 remains authoritative for IDs, expected results and severity  
**Test execution authorization:** NOT GRANTED  
**Environment approval:** NOT GRANTED

## 1. Purpose and authority

This manifest expands the existing Artifact 07 ↔ WP6 family-level crosswalk into one row per Artifact 07 acceptance test ID. It is a documentation-only traceability aid. It does not replace Artifact 07, alter test IDs/severity, authorize test execution, approve a test environment, or claim any test has passed.

Authority order:
1. Artifact 07 v1.0 §7.2 — authoritative requirement/test ID, expected result and severity.
2. WP6 Acceptance Contract & Test Oracle Reconciliation 0.1 — proposed VS/F/SEC/API-EVT/ENV trace IDs and candidate oracles.
3. WP6 Vertical Slice Integration, Recovery & Acceptance Validation 0.1 — scenario, failure and evidence plan.
4. Existing Artifact 07 ↔ WP6 crosswalk 0.1 — family-level traceability.
5. Contract 12 protected-action crosswalk 0.1 — distribution-specific traceability and genuine oracle gaps.
6. Batch 21 Observability/Logging/Metrics/Tracing/Operational Runbook v0.1 and its OBS-T01..OBS-T20 candidate tests, mapped in the Batch 21 ↔ Artifact 07 crosswalk 0.1.

A WP6 trace ID is not a replacement for an Artifact 07 ID. A group-level mapping is not proof of a one-to-one test mapping. Where the current sources do not establish a direct mapping, this manifest says so explicitly.

## 2. Global test manifest contract

These are proposed manifest defaults derived from WP6. They are not environment approval or execution instructions.

| Manifest field | Required value / rule | Current status |
|---|---|---|
| Requirement ID | Exact Artifact 07 ID from §7.2 | Source-defined |
| Requirement source | Artifact 07 v1.0 §7.2, exact family row | Source-defined |
| WP6 trace IDs | Existing VS/F/SEC/API-EVT/ENV identifiers only; do not invent | Proposed / mapping review |
| Fixture set | Synthetic fixture set per WP6 §5.1; exact fixture identity and bytes must be versioned | Not created |
| Environment | Approved isolated non-production environment satisfying ENV-01..14 as applicable | NOT APPROVED |
| Test command | Exact command recorded only after owner authorizes test execution | NOT SPECIFIED / NOT AUTHORIZED |
| Expected oracle | Observable result from Artifact 07 plus approved WP6 detail; no inferred success | Proposed |
| Evidence record | Immutable per-test evidence record with test ID/version, run ID, build/review target, environment, fixture, input/output refs, result, timestamps, correlation IDs and reviewer | Not created |
| Result | PASS / PASS_WITH_WARNINGS / NEEDS_REVIEW / BLOCKED / NOT_RUN / NOT_APPLICABLE | NOT_RUN until executed |
| Severity | Exact Artifact 07 §7.2 severity; never downgraded by WP6 | Source-defined |
| Owner disposition | Required for unresolved oracle, scope or NOT_APPLICABLE rationale | OPEN |

**Common preconditions:** ENV-01 isolated test workspace/brand; ENV-02 test database/schema; ENV-03 test worker identity; ENV-04 test artifact storage; ENV-05 deterministic synthetic fixtures; ENV-06 test-only policy; ENV-07 upload/publish egress disabled; ENV-08 no paid resources; ENV-09 sanitized logs/evidence; ENV-10 safe teardown; ENV-11 approved test parameters; ENV-12 stable review target; ENV-13 clock convention; ENV-14 safe abort. Actual environment remains unselected and unapproved.

**Common evidence bundle:** sanitized command/output, exact source/build/config target, fixture manifest, before/after state, relevant entity/version IDs, policy decision and reason, artifact/version/checksum/manifest references, correlation/causation IDs, audit references, and reviewer disposition as applicable. Evidence is not created by this document.

## 3. Artifact 07 test-case register

### 3.1 Identity and domain model (ID-01..ID-06)

| Artifact 07 ID | Authoritative expected result | Severity | WP6 trace mapping | Candidate fixture / evidence oracle | Mapping status |
|---|---|---|---|---|---|
| ID-01 | Create canonical entities with UUIDv7 IDs; IDs validate and remain immutable | HIGH | VS-01..VS-03 (family-level) | Synthetic workspace, brand, ContentItem, ContentVersion and ContentVariant; capture IDs, schema versions and immutability proof | PARTIAL — family mapping |
| ID-02 | Attempt duplicate canonical ID; rejected | HIGH | No direct VS/F/SEC ID established in current crosswalk | Duplicate-ID fixture against an isolated test store; capture rejection and unchanged canonical record | GAP — direct trace ID/oracle mapping required |
| ID-03 | Create multiple variants for one content item; relationships remain distinct and valid | HIGH | VS-03 | One synthetic ContentItem with at least two distinct variants; capture parent refs and relationship validation | PARTIAL — VS family mapping |
| ID-04 | Create multiple production attempts for one variant; each attempt has separate identity | HIGH | No direct VS/F ID established in current crosswalk | One variant with multiple synthetic production attempts; capture distinct attempt/run identities and unchanged ContentItem identity | GAP — direct trace ID/oracle mapping required |
| ID-05 | Register a new artifact version; previous version remains unchanged | HIGH | VS-12..VS-13; SEC-A-06 | Two immutable artifact versions; compare prior bytes/hash/metadata before and after new version registration | PARTIAL — direct oracle concept, mapping needs exact confirmation |
| ID-06 | Create invalid entity relationship; rejected by domain/persistence constraints | HIGH | VS-01..VS-03 (family-level only) | Synthetic invalid parent/workspace relationship; capture validation/FK denial and no committed invalid link | PARTIAL — family mapping; exact test trace required |

### 3.2 Persistence and lifecycle (ST-01..ST-06)

| Artifact 07 ID | Authoritative expected result | Severity | WP6 trace mapping | Candidate fixture / evidence oracle | Mapping status |
|---|---|---|---|---|---|
| ST-01 | Restart control-plane process; durable state survives | CRITICAL | F-01; VS-06, VS-17; OBS-T08/OBS-T17 (supplemental) | Persist one synthetic job/workflow, restart isolated control plane, prove committed state and audit history survive | DIRECT — F-01 |
| ST-02 | Submit invalid state transition; rejected | HIGH | VS-16 (family-level) | Synthetic entity at known state; submit a transition not permitted by the owner-approved state machine; capture rejection/no mutation | PARTIAL — transition table must first be frozen |
| ST-03 | Submit stale state version; rejected or safely reconciled | HIGH | F-05 and relevant API-EVT stale-version/reconciliation coverage | Two competing updates using stale expected version; capture conflict/reconciliation and final state | PARTIAL — F-05 concerns stale attempt callback; exact state-version oracle must be distinguished |
| ST-04 | Update state concurrently; no silent lost update | HIGH | API-EVT-01..07 only at broad command/version family level; no exact test-level link confirmed | Two concurrent synthetic updates against one aggregate; capture serialization/conflict result and state history | GAP/PARTIAL — direct test mapping required |
| ST-05 | Reconstruct transition history; actor, reason, time and prior/new state available | HIGH | VS-17; OBS-T02/OBS-T16 (supplemental) | Completed synthetic workflow with attributable transitions; reconstruct ordered history from authoritative records | DIRECT — VS-17 |
| ST-06 | Attempt cross-domain direct state mutation; denied by ownership boundary | CRITICAL | VS-16; SEC-W-09 listed as relevant in family crosswalk; relevant SEC-G checks | Actor from non-owning domain attempts mutation; capture owner-boundary denial and audit event | PARTIAL — exact cross-domain oracle and correct security-suite mapping require review |

### 3.3 Durable queue, lease and retry (Q-01..Q-08)

| Artifact 07 ID | Authoritative expected result | Severity | WP6 trace mapping | Candidate fixture / evidence oracle | Mapping status |
|---|---|---|---|---|---|
| Q-01 | Create task and durable job; job persists with valid parent references | HIGH | VS-05..VS-06; F-01 | Synthetic workflow/task/job; verify persisted IDs and valid parent refs, then restart check where scoped | DIRECT — VS-05/06; F-01 for durability |
| Q-02 | Two workers claim same job concurrently; only one active lease holder | CRITICAL | VS-09; WP6 lease/fencing oracle | Two test workers contend for one job; capture exactly one current lease/fencing generation and denied competing claim | PARTIAL — exact concurrent-claim scenario must be specified |
| Q-03 | Kill worker during execution; lease expiry enables controlled recovery | CRITICAL | F-02; OBS-T11 (supplemental lease visibility) | Test worker terminated after claim; capture lease expiry/reconciliation and safe recovery under approved test parameters | DIRECT — F-02 |
| Q-04 | Stale worker submits result after lease expiry; rejected | CRITICAL | F-05; VS-15; OBS-T11 (supplemental lease visibility) | Supersede lease/attempt, then submit stale callback; capture fencing rejection and unchanged current result | DIRECT — F-05 |
| Q-05 | Deliver same event twice; no duplicate logical side effect | CRITICAL | F-04; API-EVT-08..10 | Deliver same event identity twice to synthetic consumer; capture inbox/dedup evidence and exactly one logical effect | DIRECT — F-04 |
| Q-06 | Exceed configured retry limit; job enters defined terminal handling | HIGH | No exact F ID; WP6 retry parameters and terminal policy remain open | Synthetic retryable failure sequence using owner-approved test-only limit; capture terminal disposition and attempt history | GAP — retry-limit policy/oracle not frozen |
| Q-07 | Restart scheduler with due jobs pending; eligible work is recovered | HIGH | F-01; VS-07 (family-level); OBS-T09/OBS-T10/OBS-T17 (supplemental) | Due synthetic job remains pending across scheduler restart; capture eligibility and recovery without duplicate claim | PARTIAL — F-01 is control-plane restart; scheduler-specific oracle needs explicit mapping |
| Q-08 | Submit dependent task before prerequisite completion; execution is blocked | HIGH | VS-05 | Synthetic task graph with unmet prerequisite; capture blocked eligibility and dependency reason | DIRECT — VS-05 |

### 3.4 Worker identity and capability security (WK-01..WK-08)

| Artifact 07 ID | Authoritative expected result | Severity | WP6 trace mapping | Candidate fixture / evidence oracle | Mapping status |
|---|---|---|---|---|---|
| WK-01 | Authenticate registered worker; accepted within scope | HIGH | VS-08 | Test worker identity and scoped test credential; capture authentication and scope proof without secret material | DIRECT — VS-08 |
| WK-02 | Use expired credential; denied | CRITICAL | F-09; SEC-W-03 | Expired test credential; capture authentication/claim denial and no lease mutation | DIRECT — F-09 / SEC-W-03 |
| WK-03 | Use revoked worker identity; denied for new claims/access | CRITICAL | F-08; SEC-W-02 | Revoked test worker; capture denied claim/access and audit evidence | DIRECT — F-08 / SEC-W-02 |
| WK-04 | Claim unsupported job capability; denied | CRITICAL | F-10; SEC-W-06 | Worker lacks verified/authorized capability for synthetic job; capture assignment denial | DIRECT — F-10 / SEC-W-06 |
| WK-05 | Worker updates another worker's lease; denied | CRITICAL | SEC-W-07 | Worker A attempts to mutate Worker B's synthetic lease; capture denial and unchanged lease owner | DIRECT — SEC-W-07 |
| WK-06 | Worker requests unrelated artifact; denied | CRITICAL | SEC-A-02 (cross-job artifact scope) | Worker/job A requests artifact owned by job/workspace B; capture access denial and audit event | PARTIAL — artifact suite rather than worker suite; verify exact scope |
| WK-07 | Inspect logs for credentials; no secrets exposed | CRITICAL | SEC-W-10; OP-05; ENV-09; OBS-T04 (supplemental) | Seed test-only sentinel secret; inspect sanitized logs/evidence; capture redaction result without reproducing secret | DIRECT — SEC-W-10 / OP-05 |
| WK-08 | Local worker reconnects after offline period; re-authenticates without duplicate completion | HIGH | No direct F/VS ID established in current crosswalk | Synthetic worker offline/reconnect lifecycle; prove re-authentication and no duplicate logical completion | GAP — reconnect oracle not explicitly mapped |
### 3.5 API, events and contracts (API-01..API-06)

| Artifact 07 ID | Authoritative expected result | Severity | WP6 trace mapping | Candidate fixture / evidence oracle | Mapping status |
|---|---|---|---|---|---|
| API-01 | Submit malformed request; rejected at boundary | HIGH | SEC-W-05; API-EVT-01..07 at broad request/validation family level | Malformed synthetic request against test endpoint; capture schema/error response and no state mutation | PARTIAL — exact test-level trace needs approval |
| API-02 | Submit unsupported schema version; explicit safe error | HIGH | SEC-W-04; API-EVT-11..13 | Synthetic unsupported schema version; capture explicit rejection/compatibility behavior and no guessed interpretation | DIRECT at family level; exact API-EVT row to pin |
| API-03 | Replay duplicate event; idempotent processing | CRITICAL | F-04; API-EVT-08..10 | Same event identity delivered repeatedly; capture one logical effect and dedup receipts | DIRECT — F-04 |
| API-04 | Trace workflow to worker result; correlation IDs remain linked | HIGH | VS-17; API-EVT-21..23; OBS-T01/OBS-T02 (supplemental) | One synthetic workflow-to-worker execution; capture correlation/causation continuity across records | DIRECT — VS-17 |
| API-05 | Submit oversized binary in ordinary JSON payload; rejected or redirected to artifact transfer path | MEDIUM | No exact API-EVT mapping confirmed; API-EVT-01..07 are broad request/validation family only | Synthetic payload-size boundary test; capture rejection or approved transfer-route response without large/real media | GAP/PARTIAL — size threshold and exact oracle not frozen |
| API-06 | Submit unauthorized command; denied and audited | CRITICAL | F-18 / SEC-G-09 for direct bypass; API-EVT-25 for adapter bypass where applicable | Synthetic unauthorized command and direct adapter attempt; capture central denial, audit and no external side effect | PARTIAL — map both API boundary and adapter bypass distinctly |

### 3.6 Artifact integrity and access (AR-01..AR-07)

| Artifact 07 ID | Authoritative expected result | Severity | WP6 trace mapping | Candidate fixture / evidence oracle | Mapping status |
|---|---|---|---|---|---|
| AR-01 | Register artifact with valid checksum; artifact becomes available | HIGH | VS-12..VS-14 | Deterministic synthetic bytes; register immutable version; verify expected checksum, byte size and availability state | DIRECT — VS-12..VS-14 |
| AR-02 | Register artifact with checksum mismatch; blocked | CRITICAL | F-07; SEC-A-04; OBS-T12 (supplemental diagnostic/quarantine evidence) | Synthetic bytes with deliberately mismatched expected checksum; capture validation failure/quarantine and downstream denial | DIRECT — F-07 / SEC-A-04 |
| AR-03 | Retrieve artifact with expired transfer grant; denied | CRITICAL | SEC-A-01 | Expired test-only transfer grant; capture denied retrieval and no byte disclosure | DIRECT — SEC-A-01 |
| AR-04 | Retrieve artifact across job/workspace scope; denied | CRITICAL | SEC-A-02 | Test worker/job in workspace A requests artifact in workspace B; capture scope denial | DIRECT — SEC-A-02 |
| AR-05 | Register new version; old version remains immutable | HIGH | VS-12..VS-13; SEC-A-06 | Register a second synthetic ArtifactVersion; compare old bytes/hash/metadata and verify no overwrite | DIRECT — VS-12/13; SEC-A-06 |
| AR-06 | Interrupt transfer; safe retry without corrupt registration | HIGH | F-06 | Interrupt controlled synthetic transfer; prove partial bytes are not marked complete and recovery/retry is safe | DIRECT — F-06 |
| AR-07 | Attempt to use unregistered temporary file as durable output; rejected | HIGH | SEC-A-07 | Temporary/unregistered synthetic file reference; attempt downstream use; capture rejection and absence of durable registry record | DIRECT — SEC-A-07 |

### 3.7 Quality, rights and authorization (GV-01..GV-12)

| Artifact 07 ID | Authoritative expected result | Severity | WP6 trace mapping | Candidate fixture / evidence oracle | Mapping status |
|---|---|---|---|---|---|
| GV-01 | Request protected action without authorization; denied | CRITICAL | F-12; SEC-G-01; VS-18 | Synthetic protected distribution request with no authorization record; capture deny reason and proof no external request emitted | DIRECT — F-12 / SEC-G-01 / VS-18 |
| GV-02 | Use expired authorization; denied | CRITICAL | SEC-G-02; F-11..F-16 family mapping | Expired synthetic authorization context; capture expiry check, denial and no side effect | DIRECT at security-suite level; exact F mapping requires pinning |
| GV-03 | Use revoked authorization; denied | CRITICAL | SEC-G-03; F-11..F-16 family mapping | Revoked synthetic authorization context; capture revocation check and denial | DIRECT at security-suite level; exact F mapping requires pinning |
| GV-04 | Use authorization for different artifact hash; denied | CRITICAL | F-13; SEC-G-04 | Authorization hash differs from requested artifact hash; capture mismatch and denial | DIRECT — F-13 / SEC-G-04 |
| GV-05 | Use authorization for different destination/action; denied | CRITICAL | F-14; SEC-G-05 | Authorized destination/action differs from request; capture exact mismatch and denial | DIRECT — F-14 / SEC-G-05 |
| GV-06 | Attempt ordinary approval of BLOCKED package; remains blocked | CRITICAL | F-15; SEC-G-06 | Synthetic package with hard BLOCKED QA result; ordinary approval attempt; capture persistent blocker and denial | DIRECT — F-15 / SEC-G-06 |
| GV-07 | Attempt protected use with UNKNOWN/PENDING rights; denied under accepted policy baseline | CRITICAL | F-16; SEC-G-07 | Rights state UNKNOWN or PENDING_REVIEW for the requested use; capture use-specific denial | DIRECT — F-16 / SEC-G-07 |
| GV-08 | Activate emergency pause; new protected actions blocked | CRITICAL | F-11; SEC-G-08 | Pause active before protected request; capture denial, pause scope and no external request | DIRECT — F-11 / SEC-G-08; does not prove in-flight cancellation |
| GV-09 | Attempt to bypass authorization through adapter; denied | CRITICAL | F-18; SEC-G-09; API-EVT-25 | Direct adapter/pipeline path attempts protected operation; capture centralized denial and no external request | DIRECT — F-18 / SEC-G-09 / API-EVT-25 |
| GV-10 | Attempt to turn dry-run into live execution; denied without separate authorization | CRITICAL | F-17; API-EVT-25 where applicable | Test-only dry-run request attempts live mode/side effect; capture fail-closed denial and egress proof | DIRECT — F-17; API-EVT mapping requires confirmation |
| GV-11 | Verify decision policy version and evidence references; retained and auditable | HIGH | VS-17/VS-18; OP-04; SEC-G suite as applicable | Synthetic decision with policy/evidence references; retrieve authorized audit trace and verify exact version/ref retention | PARTIAL — no dedicated exact test ID in current mapping |
| GV-12 | Attempt automatic public publishing; disabled/denied pending separate policy | CRITICAL | F-17/F-18 family mapping; SEC-G-10; VS-18 denial boundary | Synthetic public-auto-publish attempt with no separate policy; capture disabled/denied outcome and no outbound request | DIRECT for denial; does not prove visibility or publication |

### 3.8 Audit, observability and recovery (OP-01..OP-06)

| Artifact 07 ID | Authoritative expected result | Severity | WP6 trace mapping | Candidate fixture / evidence oracle | Mapping status |
|---|---|---|---|---|---|
| OP-01 | Reconstruct completed workflow; complete trace available | HIGH | VS-17; F-01 recovery context; OBS-T01/OBS-T02 (supplemental) | Completed synthetic slice; reconstruct ordered workflow/task/job/attempt/worker/artifact/governance history | DIRECT — VS-17 |
| OP-02 | Reconstruct failed workflow; safe actionable diagnostics available | HIGH | F-01..F-07 family; API-EVT error/correlation families; OBS-T03/OBS-T12/OBS-T16 (supplemental) | Synthetic controlled failure; reconstruct error classification, attempt history, recovery action and sanitized diagnostics | PARTIAL — family mapping; exact failure fixture to select |
| OP-03 | Inspect worker heartbeat and lease; current health/expiry visible | HIGH | VS-09; F-02/F-05; OBS-T09/OBS-T11 (supplemental) | Synthetic worker lease/heartbeat lifecycle; capture current generation, expiry and stale-attempt handling | DIRECT/PARTIAL — F-02/F-05 cover recovery/fencing; heartbeat view needs explicit oracle |
| OP-04 | Inspect authorization denial; reason and policy reference available to authorized owner | HIGH | VS-18; F-11..F-16; API-EVT denial/error mapping as applicable; OBS-T13 (supplemental) | Synthetic denied protected action; authorized reviewer retrieves reason, policy version and evidence refs | PARTIAL — family-level mapping; exact evidence fields remain open |
| OP-05 | Inspect logs and test output; secrets redacted | CRITICAL | ENV-09; SEC-W-10; OBS-T04 (supplemental) | Test-only sentinel secret in controlled log path; verify redaction and evidence access scope | DIRECT — ENV-09 / SEC-W-10 |
| OP-06 | Restore a test backup; restoration evidence and integrity check available | HIGH | No dedicated WP6 F/VS ID established in current crosswalk; ENV-10 is teardown, not restore proof | Isolated synthetic backup/restore exercise; capture restore integrity and resource-scope proof | GAP — dedicated restore scenario/oracle not mapped |

## 4. Consolidated mapping gaps requiring owner/QA disposition

| Gap ID | Artifact 07 ID(s) | Missing evidence / decision | Safe disposition |
|---|---|---|---|
| MAN-01 | ID-02, ID-04 | Direct WP6 trace IDs for duplicate canonical ID and multiple production attempts | Add explicit proposed oracle rows only after source/owner review |
| MAN-02 | ST-02..ST-04, ST-06 | Exact transition/version/concurrency/cross-domain mutation test mapping | Pin source clauses and distinct oracles; do not reuse F-05 as proof of all stale-state cases |
| MAN-03 | Q-02, Q-06, Q-07 | Concurrent lease contention, retry-limit terminal policy and scheduler restart specifics | Complete WP2-owned semantics and approved test-only parameters |
| MAN-04 | WK-08 | Local worker offline/reconnect behavior | Add explicit oracle or owner-approved deferral |
| MAN-05 | API-01, API-02, API-05, API-06 | Exact request validation, schema compatibility, size boundary and unauthorized-command mapping | Pin API-EVT IDs and approved schema/size policy |
| MAN-06 | GV-02, GV-03, GV-11 | Dedicated expired/revoked decision and evidence/policy-version oracle details | Preserve security-suite mapping; owner approves canonical record fields/decision evidence |
| MAN-07 | OP-03, OP-04 | Batch 21 OBS-T11/OBS-T13 supplemental references identified; exact heartbeat/lease telemetry and authorization evidence fields remain open | Owner/QA to approve fields and evidence mapping against Batch 21 and CF-22 |
| MAN-08 | OP-06 | Backup restore acceptance scenario | Define test-only backup/restore oracle and environment gate; do not infer from teardown |
| MAN-09 | Distribution visibility / unknown outcome / in-flight pause | Artifact 07 P0-A is pre-distribution; no live visibility or provider-side cancellation test | Keep live external behavior outside P0-A; simulator-only test requires explicit owner scope |
| MAN-10 | ChannelAccount credential scope | Worker credential tests do not prove channel-account credential safety | Define separate security test only if account integration enters approved scope |

## 5. Execution and evidence controls

- All rows remain **NOT_RUN** until an explicitly authorized test execution occurs in an approved isolated environment.
- The exact test command is intentionally unspecified. It must be approved and recorded with the implementation/review target and environment before execution.
- The actual database, worker, artifact store, test policy, fixtures and resource cleanup mechanism remain OPEN and unapproved.
- Test-only lease/retry/timeout values must be owner-approved for the isolated environment; no production values are inferred.
- External upload/publish egress must be disabled and proven before any relevant negative test.
- API-EVT-19 unknown external outcome, if included, must use a controlled simulator only; no real provider.
- Kilo's independent read-only review occurs only after a stable authorized evidence target exists. No agent is dispatched by this manifest.
- NOT_APPLICABLE requires approved scope rationale. NOT_RUN is not PASS. A design document is not test evidence.
- Any test that could produce a real external side effect must stop pending separate explicit authorization.

## 6. Owner review and closure checklist

- [x] One row created for every Artifact 07 §7.2 ID (ID/ST/Q/WK/API/AR/GV/OP).
- [x] Artifact 07 severity copied without downgrade.
- [x] Existing WP6 trace IDs used; no replacement test IDs invented.
- [x] Direct, partial and missing mappings distinguished.
- [x] P0-A pre-distribution boundary preserved.
- [x] Test commands, environment and fixtures not fabricated.
- [ ] Exact source clause and one-to-one oracle mapping approved for every Artifact 07 ID.
- [ ] Mandatory/optional scope and any NOT_APPLICABLE rationale approved.
- [ ] ENV-01..14 approved with evidence.
- [ ] Fixture manifest and deterministic bytes/output approved.
- [ ] Test commands and parameters separately authorized.
- [ ] Tests executed with immutable evidence records.
- [ ] Independent Kilo review completed.
- [ ] Product owner records final acceptance/rejection.

**Handoff status:** Proposed test-case-level manifest created for owner/QA review. Mapping gaps remain OPEN. No tests have been run, no PASS is claimed, and test execution remains unauthorized.


## 3.9 API/Event companion conformance references — supplemental only

The companion API-EVT suite is mapped in `NEXTDECODE_P0_API_EVT_01_25_Artifact07_Test_Oracle_Crosswalk_0.1.md`. These references do not replace Artifact 07 IDs, alter severity or imply equivalent coverage where the crosswalk marks partial/gap.

| Artifact 07 ID | API-EVT companion reference(s) | Coverage qualification |
|---|---|---|
| ID-02, ID-04 | None established | API/Event crosswalk does not claim duplicate canonical ID or multiple production-attempt identity coverage |
| ST-01 | API-EVT-07 | Partial only; restart durability does not prove producer transaction rollback |
| ST-03, ST-04 | API-EVT-06, API-EVT-09, API-EVT-23 | Partial only; stale worker fencing and generic stale state do not prove API expected-version or event-gap reconciliation |
| API-01 | API-EVT-01, API-EVT-03, API-EVT-21 | Partial/closest mapping; query mutation, schema validation and full error envelope are distinct oracles |
| API-02 | API-EVT-10, API-EVT-11, API-EVT-12, API-EVT-13 | API-EVT-11 direct for unsupported schema version; unknown event type/optional fields/breaking-change detection remain distinct |
| API-03 | API-EVT-08 | Direct duplicate-event/idempotent-consumer behavior |
| API-04 | API-EVT-22 | Direct correlation continuity; immediate-parent causation detail remains open |
| API-06 | API-EVT-25 | Direct adapter-bypass denial; capture no outbound request/egress proof |
| Q-01 | API-EVT-02 | Partial; durable job creation does not prove command ACCEPTED envelope |
| Q-05 | API-EVT-08 | Direct event dedup; do not use as proof of API-EVT-04/05 command idempotency |
| Q-06 | API-EVT-18 | Partial; retry-limit terminal handling is not poison-message isolation/redrive |
| WK-03 | API-EVT-20 | Direct revoked-worker denial; prove no protected transition |
| WK-06, AR-04 | API-EVT-17 | Partial; artifact-scope denial does not prove all API/event message boundaries |
| WK-07, OP-05 | API-EVT-16 | Partial; log redaction does not alone prove secret rejection before event publication |
| GV-01 | API-EVT-15 | Partial; missing authorization denial is not replay-handler suppression |
| GV-09 | API-EVT-25 | Direct adapter bypass denial |
| OP-01, API-04 | API-EVT-22 | Partial/direct correlation continuity; exact causation semantics remain open |
| OP-02 | API-EVT-21 | Partial error-envelope/diagnostics relationship; exact fields remain to be approved |

**Genuine uncovered companion oracles:** API-EVT-04/05 command idempotency; API-EVT-07 atomic outbox rollback; API-EVT-09 version-gap reconciliation; API-EVT-10 unknown event isolation; API-EVT-12 optional-field compatibility; API-EVT-13 unversioned breaking-change detection; API-EVT-14/15 replay controls; API-EVT-18 poison isolation/redrive; API-EVT-19 unknown provider outcome; API-EVT-24 webhook signature/replay. Their scope and mandatory status require owner/QA disposition.

