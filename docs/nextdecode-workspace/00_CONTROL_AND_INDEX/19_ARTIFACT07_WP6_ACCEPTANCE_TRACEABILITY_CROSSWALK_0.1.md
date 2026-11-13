# NEXTDECODE P0 — Artifact 07 ↔ WP6 Acceptance Traceability Crosswalk
**Document ID:** NEXTDECODE-P0-A07-WP6-XREF-0.1  
**Version:** 0.1  
**Status:** WORKING CROSSWALK — OWNER/ACCEPTANCE REVIEW REQUIRED  
**Updated:** 2026-11-04  
**Scope:** Documentation-only. Artifact 07 remains the authoritative P0 acceptance matrix and criticality source. No tests are run or authorized.

## 1. Authority and interpretation
Artifact 07 v1.0, section 7.2, defines the authoritative P0-A acceptance test families, IDs and severity labels. WP6 Acceptance Contract/Test Oracle Reconciliation 0.1 defines proposed traceability IDs ENV-01..14, VS-01..18, F-01..18, SEC-W-01..10, SEC-A-01..07, SEC-G-01..11 and API-EVT-01..25. These WP6 identifiers clarify test setup, oracles and evidence; they do not replace Artifact 07 identifiers or severity.

WP6 explicitly states that its proposed severity labels are not authoritative until mapped to Artifact 07. This crosswalk preserves Artifact 07's criticality. One test execution may satisfy multiple requirements only when the evidence explicitly proves every mapped oracle; traceability alone is not proof.

## 2. Artifact 07 authoritative family crosswalk

| Artifact 07 family / IDs | Artifact 07 severity baseline | WP6 traceability mapping | Evidence/oracle alignment |
|---|---|---|---|
| ID-01..ID-06 — identity/domain model | HIGH | VS-01..VS-03, VS-12..VS-13; relevant SEC-A-06 | Canonical UUIDv7 identity, distinct ContentItem/Version/Variant, valid relationships, immutable ArtifactVersion and exact manifest reference |
| ST-01 — restart durability | CRITICAL | F-01; VS-06, VS-17 | Committed job/state survives control-plane restart; durable state and audit reconstruction |
| ST-02..ST-05 — lifecycle/version/history/concurrency | HIGH | VS-15..VS-17; relevant F-05 | Invalid/stale transition rejection, current attempt/lease check, attributable ordered history and no silent lost update |
| ST-06 — cross-domain mutation | CRITICAL | VS-16; SEC-W-09; relevant SEC-G checks | Owning domain is sole transition authority; unauthorized cross-domain mutation denied |
| Q-01..Q-08 — durable queue, lease, retry, dependency | Q-02..Q-05 and ST-01 criticalities retained as Artifact 07 specifies; Q-01/Q-06..Q-08 HIGH | VS-05..VS-10, VS-15..VS-16; F-01..F-05 | Durable job, eligibility, single lease holder, expiry recovery, stale callback rejection, deduplication, retry and dependency ordering |
| WK-01..WK-08 — worker identity/capability | HIGH for WK-01/WK-08; CRITICAL for WK-02..WK-07 | VS-08..VS-10; F-08..F-10; SEC-W-01..SEC-W-10 | Authentication, credential expiry/revocation, capability and assignment scope, worker isolation, stale fencing and secret redaction |
| API-01..API-06 — API/events/contracts | HIGH for API-01/API-02/API-04/API-05; CRITICAL for API-03/API-06 | VS-06, VS-15..VS-17; F-04; API-EVT-01..25 as applicable; SEC-W-04/10 | Schema validation, safe unsupported-version behavior, idempotency, correlation/causation, unauthorized command denial and bounded binary transfer |
| AR-01..AR-07 — artifact integrity/access | HIGH for AR-01/AR-05/AR-06/AR-07; CRITICAL for AR-02/AR-03/AR-04 | VS-12..VS-14; F-06..F-07; SEC-A-01..SEC-A-07 | Immutable version, manifest, checksum, transfer completion, access scope, quarantine and partial-transfer handling |
| GV-01..GV-12 — quality/rights/authorization | HIGH for GV-11; CRITICAL for GV-01..GV-10 and GV-12 | VS-18; F-11..F-18; SEC-G-01..SEC-G-11 | Deny by default, exact version/hash/destination, expiry/revocation, hard QA block, rights gate, emergency pause, no adapter bypass, dry-run separation and public-publishing disabled |
| OP-01..OP-06 — audit/observability/recovery | HIGH for OP-01..OP-04/OP-06; CRITICAL for OP-05 | VS-17; F-01..F-07; F-17..F-18; ENV-09 | End-to-end reconstruction, failure diagnostics, lease visibility, authorization reason, redaction and test backup restoration evidence |

**Severity rule:** The family row above summarizes Artifact 07's individual labels; the exact ID-level severity in Artifact 07 section 7.2 remains authoritative. No WP6 candidate severity can downgrade it.

## 3. WP6 environment gates are preconditions, not acceptance tests

| WP6 environment ID | Purpose | Artifact 07 relationship | Required evidence before any test |
|---|---|---|---|
| ENV-01..ENV-04 | Isolated test scope, database/storage, worker and fixture prerequisites | Preconditions for all applicable test families | Approved environment and resource isolation proof |
| ENV-05..ENV-08 | Test-only policy, publishing/upload egress disabled, no paid/charge-generating resources | Required for GV/API/security tests and no-side-effect acceptance | Configuration and outbound-denial evidence; cost boundary |
| ENV-09 | Sanitized logs/evidence destination | OP-05 and security acceptance | Seeded-secret redaction and evidence access-scope proof |
| ENV-10 | Safe teardown boundary | ID/ST/AR and all fixture-based tests | Resource ownership tags and cleanup plan that cannot delete user data |
| ENV-11 | Test-only lease/retry/timeout parameters | Q-03/Q-06 and F-01..F-05 | Explicit approved test parameter record |
| ENV-12 | Stable source/configuration review target | All evidence | Exact review target identity, only after separate authorization |
| ENV-13 | Clock/timestamp behavior | ST-05, Q lease tests, API correlation and audit | Clock source/timestamp convention where material |
| ENV-14 | Stop/abort mechanism | All test families | Demonstrated safe abort without external side effects |

Environment approval is a separate gate. An ENV item being described does not mean the environment exists or is approved.

## 4. Failure-injection traceability

| WP6 failure ID | Artifact 07 family / IDs | Core acceptance oracle |
|---|---|---|
| F-01 | ST-01; Q-01/Q-07; OP-01/OP-06 | Durable committed work survives restart and is recoverable |
| F-02 | Q-02/Q-03; WK-08; OP-03 | Lease expiry and controlled reassignment; no concurrent active lease |
| F-03 | Q-03/Q-04; AR-06; OP-01 | Output after worker loss is reconciled; no unsafe duplicate effect |
| F-04 | Q-05; API-03 | Duplicate event delivery does not duplicate logical processing |
| F-05 | Q-04; ST-03; WK-05; OP-03 | Stale attempt/callback cannot overwrite current state |
| F-06 | AR-06/AR-07 | Partial transfer is not treated as complete; safe retry |
| F-07 | AR-02; AR-04 | Checksum mismatch quarantines/blocks; downstream use denied |
| F-08..F-10 | WK-02..WK-07 | Expired/revoked identity and unsupported capability denied |
| F-11..F-16 | GV-01..GV-08; GV-11 | Protected actions denied for pause, missing/mismatched authorization, hard QA block or unresolved rights |
| F-17 | GV-10/GV-12; API-06 | Dry-run cannot become live action; public publishing remains disabled |
| F-18 | GV-09; API-06 | Direct adapter/pipeline bypass denied and audited |

## 5. Security-negative suite relationship

- WP6 SEC-W-01..10 map primarily to Artifact 07 WK-01..WK-07, API-02/API-06 and OP-05. Exact one-to-one mapping must be maintained in the test case manifest.
- WP6 SEC-A-01..07 map primarily to Artifact 07 AR-02..AR-07.
- WP6 SEC-G-01..11 map primarily to Artifact 07 GV-01..GV-12.
- Batch 20 and Batch 25 security catalogues add broader threat scenarios. They must be mapped into this same traceability graph; do not create duplicate execution merely because multiple documents describe the same oracle.
- Any additional security scenario without an Artifact 07 mapping must be labelled supplemental, owner-reviewed and explicitly classified as in-scope or deferred.

## 6. Acceptance status and gaps
1. Artifact 07 remains the acceptance authority; this crosswalk does not change its IDs or severity.
2. WP6 ENV/VS/F/SEC/API-EVT identifiers remain proposed traceability identifiers.
3. A complete test-case-level manifest with exact test IDs, source clauses, test command, fixture, environment, evidence artifact and result field remains to be produced after owner approval.
4. Artifact 07 says all critical tests must pass and mandatory tests cannot remain NOT RUN for P0-A acceptance. WP6 preserves NOT_RUN as a distinct status; it is not PASS.
5. WP6 environment, fixture, numeric test parameters and Kilo review target remain unapproved.
6. No tests have been executed under this reconciliation; no PASS is claimed.
7. Implementation, repository inspection/modification, Git, agent dispatch, provider activation, spending, deployment, upload and publishing remain unauthorized.

## 7. Next work
- Build a test-case-level manifest with one row per Artifact 07 ID, mapping WP6 IDs and Batch 17/20/21/22/23/25/26 controls.
- Reconcile duplicate or overlapping security test oracles from Batch 20 and Batch 25.
- Record owner-approved mandatory/deferred scope and any not-applicable rationale.
- Obtain explicit environment/test execution authorization before running anything.
- Keep automatic public publishing disabled absent separate authorization.

END OF CROSSWALK
