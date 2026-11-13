# NEXTDECODE P0 — Batch 21 to Artifact 07 Observability Acceptance Crosswalk

**Document ID:** NEXTDECODE-P0-B21-A07-OBS-XREF-0.1  
**Version:** 0.1  
**Date:** 4 November 2026  
**Status:** WORKING TRACEABILITY CANDIDATE — OWNER / QA REVIEW REQUIRED  
**Authority:** Artifact 07 v1.0 §7.2 remains authoritative for P0 acceptance IDs and severity  
**Execution authorization:** NOT GRANTED

## 1. Purpose and boundary

This crosswalk connects Batch 21's candidate observability/operations tests OBS-T01..OBS-T20 to relevant Artifact 07 acceptance tests and WP6 VS/F/SEC/API-EVT identifiers. It closes traceability only where the underlying behavior is genuinely the same.

Batch 21 is a detailed observability and operational runbook candidate. Its OBS-T tests are not automatically Artifact 07 acceptance tests, do not replace Artifact 07 severity, and do not prove implementation or runtime behavior. No telemetry stack, alert destination, dashboard, backup/restore environment or production runbook is approved by this document.

## 2. Source authority

1. Artifact 07 v1.0 §7.2 controls P0 acceptance IDs, expected results and severity.
2. WP6 validation/oracle reconciliation controls the P0 vertical-slice, failure-injection and security-negative test references.
3. Batch 21 v0.1 §2–§10, §11–§17 supplies candidate observability objectives, logging, metrics, tracing, health, alerting, dashboards, runbooks and OBS-T01..OBS-T20.
4. API/Event and Lifecycle standards control correlation/causation and event semantics.
5. This crosswalk is a traceability aid only. It does not create new accepted test IDs or declare tests passed.

## 3. OBS-T01..OBS-T20 mapping

| Batch 21 ID | Batch 21 scenario / oracle | Relevant Artifact 07 IDs | Relevant WP6 trace | Mapping disposition |
|---|---|---|---|---|
| OBS-T01 | Correlation propagation across command, event, workflow, task, job, attempt, artifact and external operation | API-04, OP-01 | VS-17; API-EVT-21..23 | Strong conceptual alignment; verify complete trace scope in test evidence |
| OBS-T02 | Causation linkage to triggering command/event | API-04, ST-05, OP-01 | VS-17; API-EVT-21..23 | Strong conceptual alignment; exact causation nullability/typed-reference contract remains open |
| OBS-T03 | Structured logs with stable fields and machine-readable error codes | OP-02, OP-04 | API-EVT-21..23; Batch21 logging/error taxonomy | Partial; Artifact 07 requires safe diagnostics, while Batch 21 supplies candidate log fields |
| OBS-T04 | Secret redaction in logs/traces | WK-07, OP-05 | SEC-W-10; ENV-09 | Direct supporting oracle; Batch 21 does not replace Artifact 07 severity |
| OBS-T05 | Metric cardinality excludes raw IDs and personal data | No direct Artifact 07 §7.2 equivalent | Batch 21 metric-cardinality requirements | Supplemental operational/security test; scope and SLO policy require owner disposition |
| OBS-T06 | Untrusted external trace headers cannot impersonate a principal or overwrite trusted correlation | API-06; ST-06 only where domain authority boundary is involved | API-EVT-16..17; security boundary | Partial/supplemental; exact identity/trace trust test needs security-owner approval |
| OBS-T07 | Liveness, readiness and startup checks are distinct | No direct Artifact 07 §7.2 test | Batch 21 health/readiness specification | Supplemental operational test; environment/dependency readiness must be approved |
| OBS-T08 | Database outage fails readiness safely; no in-memory authoritative fallback | ST-01; Q-01 | F-01; VS-06; ENV-02 | Partial; durable restart test is related but does not alone prove DB-outage readiness behavior |
| OBS-T09 | Queue backlog alert identifies oldest ready job age and configured alert | Q-07, OP-03 | VS-07; Batch 21 OBS alerting/runbook | Partial; alert thresholds and notification behavior are not set in Artifact 07 and remain owner-open |
| OBS-T10 | Outbox backlog metrics identify dispatcher failure | Q-01, Q-07; API-03 | F-01; F-04; API-EVT-01..07 | Partial; persistence/dedup tests do not alone prove alert correctness |
| OBS-T11 | Lease expiry visible in telemetry and stale worker result fenced | Q-03, Q-04, OP-03 | F-02; F-05; VS-09/VS-15 | Strong alignment for lease expiry/fencing; heartbeat/dashboard visibility remains an additional oracle |
| OBS-T12 | Checksum mismatch emits diagnostic event and quarantine reference | AR-02; OP-02 | F-07; SEC-A-04 | Strong alignment; verify diagnostic/audit evidence and quarantine reference separately |
| OBS-T13 | Authorization denial is traceable without sensitive policy disclosure | GV-01..GV-05; OP-04 | F-11..F-16; SEC-G-01..05; VS-18 | Strong alignment for denial and traceability; exact evidence fields depend on CF-22 record decision |
| OBS-T14 | Unknown external outcome is displayed distinctly; retry blocked pending reconciliation | No direct Artifact 07 §7.2 equivalent for provider-side unknown outcome | API-EVT-19; Contract 12 C12-AO-04; WP6 external-outcome boundary | Supplemental / scope-gated; controlled simulator only if owner approves; never a real provider in P0-A |
| OBS-T15 | Operator can follow each runbook using documented IDs, dashboards and evidence | No direct Artifact 07 §7.2 equivalent | Batch 21 RB-01..RB-10 | Supplemental operational usability test; requires approved runbook, operator and test environment |
| OBS-T16 | Operator recovery action records actor, reason, time and affected references | ST-05, OP-02, OP-04 | VS-17; API-EVT-21..23 | Strong alignment for attributable recovery/audit evidence; actual runbook exercise remains separate |
| OBS-T17 | Process restart preserves durable queue/outbox/attempt evidence | ST-01, Q-07 | F-01; VS-06/VS-17 | Strong alignment; scheduler-specific recovery must be distinguished from control-plane restart |
| OBS-T18 | Dashboard values reconcile to authoritative records for a test fixture | No direct Artifact 07 §7.2 equivalent | Batch 21 dashboard consistency | Supplemental operational consistency test; dashboard provider and implementation remain unselected |
| OBS-T19 | Every alert has owner, severity, runbook and first action | No direct Artifact 07 §7.2 equivalent | Batch 21 alerting/ownership sections | Supplemental governance/operations test; real staffing/escalation roster remains open |
| OBS-T20 | Telemetry retention/access follow approved classification and retention policy | OP-05 only for secret/privacy handling; no exact retention test | Batch 21 privacy/retention controls | Partial/supplemental; retention periods and policy are open; no retention duration inferred |

## 4. Artifact 07 manifest amendments recommended

The following supplemental references may be added to the test-case manifest after owner/QA review. They do not change the Artifact 07 ID or expected result.

| Artifact 07 ID | Add supplemental Batch 21 reference | Reason | Constraint |
|---|---|---|---|
| API-04 | OBS-T01, OBS-T02 | Correlation and causation propagation | Keep business IDs distinct from trace IDs |
| ST-05 | OBS-T02, OBS-T16 | Transition/recovery causation and attribution | Audit source remains authoritative |
| ST-01 | OBS-T08, OBS-T17 | Restart durability and safe readiness | OBS-T08 is not equivalent to full database outage test |
| Q-07 | OBS-T09, OBS-T10, OBS-T17 | Queue recovery and outbox/alert visibility | Alert thresholds remain open |
| Q-03 / Q-04 | OBS-T11 | Lease expiry and stale-result fencing | Heartbeat visibility needs its own check |
| AR-02 | OBS-T12 | Integrity failure diagnostics/quarantine | Do not equate log emission with quarantine enforcement |
| WK-07 / OP-05 | OBS-T04 | Secret redaction | Preserve Artifact 07 severity |
| GV-01..GV-05 / OP-04 | OBS-T13 | Authorization denial traceability | Exact CF-22 evidence fields remain open |
| OP-02 | OBS-T03, OBS-T16 | Structured diagnostics and recovery audit | Runbook usability not proved |
| OP-03 | OBS-T11 | Lease visibility | Current dashboard/metric not implemented or verified |

OP-06 backup restore remains a genuine gap. Batch 21 RB-02 refers to an approved backup/restore procedure and OBS-O12 leaves backup/restore process open, but OBS-T01..OBS-T20 contains no dedicated backup restore acceptance test. Do not infer restore proof from teardown (ENV-10) or process restart (OBS-T17).

## 5. Supplemental tests versus P0-A acceptance

- Artifact 07 remains the authoritative P0-A acceptance suite.
- Batch 21 OBS-T01..OBS-T20 are candidate operational tests; they may supplement Artifact 07 only where the owner approves the scope.
- Tests for metrics cardinality, readiness probes, alert actionability, dashboard reconciliation, runbook usability, telemetry retention and backup restore may be outside the narrow P0-A vertical slice unless separately included.
- A test may satisfy more than one requirement only if the same execution evidence explicitly proves each oracle.
- No provider, telemetry stack, alert channel, dashboard, backup provider, retention duration or production SLO is selected here.
- No test command, fixture, environment or execution permission is created.

## 6. Open closure items

| Gap ID | Required action | Current status |
|---|---|---|
| B21-A07-01 | Approve which OBS-T tests are mandatory P0-A versus supplemental/deferred | OPEN |
| B21-A07-02 | Map exact Batch 21 observability evidence fields to OP-02/03/04/05 | PARTIAL |
| B21-A07-03 | Define dedicated isolated backup/restore acceptance oracle for OP-06 or owner-approved deferral | OPEN |
| B21-A07-04 | Approve telemetry/alert/dashboard implementation profile and no-cost boundary | OPEN |
| B21-A07-05 | Approve retention/classification policy and evidence access scope | OPEN |
| B21-A07-06 | Approve operator/runbook usability scope, named operator role and safe environment | OPEN |

## 7. Restrictions and handoff

No source contract, Artifact 07 test ID/severity, Batch 21 candidate, environment or owner decision is modified by this crosswalk. No tests have been run. No implementation, agent dispatch, provider activation, spending, deployment, production activity, upload or publishing is authorized.

**Handoff:** Batch 21's twenty observability tests are now mapped to Artifact 07 where a genuine relationship exists; supplemental tests and genuine gaps remain explicit. Owner/QA review is required before any test manifest mapping is treated as final.

[executed on device: Anish (45b43f72-8ac0-4429-8be6-36afb8b5226a)]