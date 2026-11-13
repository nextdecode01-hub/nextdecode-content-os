# P0 Observability, Logging, Metrics, Tracing & Operational Runbook Specification

NEXTDECODE Content OS | Batch 21 | Version 0.1 — Design Candidate

Status: Detailed observability and operations candidate; formal owner freeze pending; implementation authorization not granted.

Purpose: specify how operators understand system health, trace work across domains and workers, detect and diagnose failures, preserve evidence and recover safely.

Scope boundary: documentation and design only. No monitoring stack, telemetry exporter, alert destination, cloud provider, dashboard, repository change or production runbook has been configured or executed by this batch.

## 1. Authority, status and design interpretation

| Classification | Meaning |
| --- | --- |
| Accepted baseline | Explicit accepted ADR/CF or canonical contract requirement. |
| Derived candidate | Operational design proposed to satisfy the baseline; requires review. |
| Open decision | A value, provider, threshold or procedure not approved in the source baseline. |
| Illustrative example | Example field, metric, dashboard or alert name; not a frozen implementation identifier. |

- The API/Event Contract Standard requires correlation and causation context to flow through commands, events and downstream work.

- The lifecycle standard requires attributable state transitions, actor, reason, time and prior/new state.

- The database and persistence candidate includes audit events, domain events, outbox/inbox, idempotency and execution attempt records.

- The security baseline requires sensitive data and credentials to be excluded from logs, with protected decisions auditable.

- Unknown external side effects must be reconciled, not blindly retried.

- The initial architecture remains local-first/free-first; no paid observability service is authorized or selected.

- This document does not assert current telemetry coverage, service-level objectives, production readiness or completed incident-response capability.

## 2. Observability objectives

| Objective | Question the system must answer | Evidence required |
| --- | --- | --- |
| Availability | Can the control plane and critical dependencies serve requests? | Health checks, dependency status, request success/error metrics. |
| Workflow visibility | Where is a workflow run and which task is blocking it? | Workflow/task states, timestamps, dependency and correlation links. |
| Execution visibility | Which worker claimed a job, which attempt ran and what happened? | Job, attempt, lease, worker and result records. |
| Artifact integrity | Was the expected artifact version created, transferred and validated? | Artifact/version IDs, checksum, manifest, validation and quarantine evidence. |
| Governance visibility | Why was a protected operation allowed or denied? | QA, rights, approval, authorization and policy decision references. |
| External operation certainty | Did the platform actually accept or publish the operation? | External operation state, provider reference and reconciliation evidence. |
| Recovery readiness | Can work resume after process/worker restart without duplicate side effects? | Durable state, replay records, recovery logs and acceptance tests. |
| Security investigation | Which principal performed a sensitive action and what was affected? | Audit evidence, actor, action, resource/version, destination and time. |

## 3. Telemetry model and correlation chain

Every user-visible or operationally significant action should be traceable through a common correlation chain. Correlation IDs group related work; causation IDs identify the direct triggering event or command.

User / API command
  -> command outcome + correlation_id
  -> aggregate transition + state_version
  -> domain event + causation_id
  -> transactional outbox -> dispatcher
  -> workflow_run -> task_instance -> job
  -> job_attempt -> worker assignment + lease
  -> artifact / artifact_version / manifest / validation
  -> QA + rights + review + approval + authorization
  -> distribution_operation -> external provider reference
  -> observed outcome / reconciliation / audit event

Minimum correlation fields (candidate): correlation_id, causation_id, command_id, event_id, workspace_id, aggregate_type, aggregate_id, state_version, workflow_run_id, task_instance_id, job_id, attempt_id, worker_id, artifact_version_id, authorization_decision_id and distribution_operation_id.

- Identifiers should be propagated, not regenerated at every boundary.

- Do not put secrets, access tokens or full sensitive content into trace baggage.

- A missing correlation ID on a critical path should be treated as an observability defect and surfaced in tests.

## 4. Structured logging specification

Logs are diagnostic records, not the authoritative source of domain state, approval, authorization or external publication truth. Durable business facts belong in domain records, audit events and operation records.

| Field | Requirement |
| --- | --- |
| timestamp | UTC event time with sufficient precision. |
| severity | Controlled severity: DEBUG, INFO, WARN, ERROR; FATAL only if runtime convention requires it. |
| service/component | Stable logical component name, not host-specific free text. |
| environment | Explicit environment label; never infer production from hostname. |
| event_name | Stable machine-readable event identifier. |
| message | Short human-readable explanation; avoid dumping payloads. |
| correlation_id / causation_id | Propagated identifiers for cross-component investigation. |
| principal_ref | Authenticated actor/service/worker reference where relevant; never raw credential. |
| workspace_id | Scope reference where applicable; avoid exposing unnecessary personal data. |
| resource_ref / version_ref | Canonical resource and exact immutable version where relevant. |
| operation_ref | Command, job, attempt, transfer or distribution operation identifier. |
| result / error_code | Stable outcome/error code; avoid parsing message strings. |
| duration_ms | Elapsed time for measured operation; use monotonic clock for duration. |
| trace_id / span_id | Tracing identifiers when distributed tracing is enabled. |
| redaction_state | Optional marker indicating sensitive fields were filtered. |

Log event families (illustrative): command.accepted/rejected, state.transitioned, outbox.published/failed, inbox.duplicate, job.claimed/started/retried/failed, lease.expired, worker.quarantined, artifact.validated/quarantined, authorization.allowed/denied, distribution.started/unknown/confirmed, reconciliation.completed and system.dependency_unavailable.

### 4.1 Logging rules

- Emit structured JSON or an equivalent parseable format; avoid relying on unstructured console text for operational evidence.

- Use stable event names and error codes; message wording may evolve without breaking alert rules.

- Record state transitions with prior state, new state, actor, reason and state_version in authoritative audit/domain records; logs may link to them.

- Redact credentials, tokens, signing keys, private URLs, sensitive user data and content bodies.

- Do not log entire prompts, research documents, transcripts or media metadata by default.

- Use sampling only for high-volume diagnostic traces where critical errors and audit facts remain fully retained.

- Keep log retention and access aligned with classification and retention policy; exact periods remain open.

- Prevent untrusted strings from forging log lines; encode/escape control characters and validate structured fields.

## 5. Metrics catalogue

| Metric family | Illustrative metric | Useful dimensions / caution |
| --- | --- | --- |
| API | api_requests_total, api_request_duration_seconds | Route template, method, status class; avoid raw URL/user IDs as labels. |
| Command | commands_total, command_duration_seconds | Command type, outcome, bounded error code. |
| Workflow | workflow_runs_total, workflow_run_age_seconds | Workflow type, execution status, age bucket. |
| Task | task_instances_total, task_wait_seconds | Task type, execution status. |
| Queue | jobs_ready, jobs_oldest_age_seconds, job_claim_latency_seconds | Queue/priority class; avoid unbounded job IDs as labels. |
| Execution | job_attempts_total, job_duration_seconds, job_retries_total | Task type, outcome, worker class. |
| Lease | active_leases, lease_expirations_total, lease_renewal_failures_total | Worker class; per-worker detail belongs in logs/traces. |
| Worker | workers_registered, workers_eligible, worker_heartbeat_age_seconds | Trust state, capability class. |
| Outbox/inbox | outbox_pending, outbox_oldest_age_seconds, inbox_duplicates_total | Consumer class, event family. |
| Artifact | artifact_validation_failures_total, transfer_duration_seconds | Artifact type, validation category; no file names as labels. |
| Governance | authorization_decisions_total, authorization_denials_total, blocked_quality_total | Action class, reason code; do not expose sensitive policy facts. |
| Distribution | distribution_operations_total, external_operation_unknown_total | Destination class, operation outcome; exact account IDs not labels. |
| Reliability | process_restarts_total, dependency_errors_total | Component, dependency class. |
| Security | auth_failures_total, credential_revocations_total, policy_denials_total | Reason category; avoid principal IDs as metric labels. |

Metric names are examples only. Final naming, units, cardinality limits and exporter conventions are open implementation decisions.

### 5.1 Metric cardinality and privacy

- Never use UUIDs, email addresses, content titles, URLs, tokens or raw provider references as metric labels.

- Use bounded enums and normalized classes for labels; keep high-cardinality identifiers in logs/traces.

- Metrics must not contain content payloads or secrets.

- Separate aggregate service metrics from per-workspace business analytics.

- Define cardinality budgets before instrumenting high-volume event families.

## 6. Distributed tracing

| Span | Candidate attributes |
| --- | --- |
| HTTP/API request | method, route template, status class, authenticated principal class, correlation_id |
| Command handling | command type/version, target type, expected state version, outcome |
| Policy evaluation | action class, resource type, policy version, allow/deny reason class; never include sensitive policy payload |
| Database transaction | operation class, outcome, retry/conflict indicator; avoid SQL parameter capture |
| Outbox dispatch | event type/schema version, attempt count, delivery outcome |
| Workflow/task execution | workflow type, task type, run/task IDs, execution outcome |
| Job attempt | job type, attempt number, worker class, lease context, duration |
| Artifact operation | artifact type/version ref, validation category, transfer outcome |
| External operation | destination class, operation type, provider response class, reconciliation state |

- Represent asynchronous handoffs with trace links or propagated context; do not keep a span open indefinitely while a job waits in a durable queue.

- Trace context must be validated at trust boundaries; untrusted external trace headers cannot establish authenticated identity.

- Sampling must preserve traces for errors, slow operations and critical protected-action paths according to an approved policy.

- Trace storage provider, sampling percentages, retention and exporter remain open.

## 7. Health checks and dependency readiness

| Check | Purpose | Failure behavior |
| --- | --- | --- |
| Liveness | Is the process alive and able to make progress? | Restart only when the process is genuinely unhealthy; avoid restart loops. |
| Readiness | Can this instance safely accept the traffic/work it advertises? | Remove from service or stop claiming work when critical dependencies are unavailable. |
| Startup | Has initialization and schema/config validation completed? | Do not accept work before startup checks pass. |
| Database | Can the authoritative persistence layer perform required operations? | Fail readiness for critical DB unavailability; preserve queued work. |
| Queue/outbox | Can durable work be claimed/dispatched safely? | Pause claims or dispatch; retain pending records. |
| Object storage | Can required artifact operations be performed? | Do not mark transfer or artifact complete on uncertain storage result. |
| Policy service | Can protected actions be evaluated authoritatively? | Fail closed for protected operations. |
| Worker heartbeat | Is worker registration/trust/capability still valid? | Stop assigning work to stale, revoked or quarantined workers. |

A health endpoint must not reveal secrets, detailed internal topology or sensitive dependency configuration. Liveness and readiness must not be conflated.

## 8. Alerting principles and candidate alerts

| Alert ID | Condition (conceptual) | Response intent |
| --- | --- | --- |
| OBS-A01 | Control-plane readiness unavailable beyond approved tolerance | Assess service/dependency health; protect queued work. |
| OBS-A02 | Database errors or connection saturation exceed approved threshold | Stop unsafe work intake; investigate DB and capacity. |
| OBS-A03 | Oldest ready job age exceeds target | Inspect worker availability, queue claim and blocked dependencies. |
| OBS-A04 | Outbox backlog/oldest event age grows continuously | Inspect dispatcher, transport and consumer failures. |
| OBS-A05 | Lease expiry or renewal failures spike | Inspect worker health, network, clock and fencing behavior. |
| OBS-A06 | Worker heartbeat stale or trust state changes unexpectedly | Quarantine/stop assignments; inspect identity and credentials. |
| OBS-A07 | Artifact checksum or validation failures occur | Quarantine affected version and preserve evidence. |
| OBS-A08 | Authorization denials or bypass attempts spike | Inspect policy mismatch, abuse or integration defect. |
| OBS-A09 | Protected distribution operation has unknown outcome | Pause retry; reconcile with provider. |
| OBS-A10 | Unexpected public distribution event | Treat as high-severity incident; contain and investigate. |
| OBS-A11 | Credential expiry/revocation or authentication failure anomaly | Review principal, rotation and possible compromise. |
| OBS-A12 | Critical error rate or latency breaches approved SLO | Triage affected path and dependency. |

Thresholds, notification channels, severity mapping, escalation timing and on-call expectations are not established here. Avoid alert fatigue: alerts should have an owner, a runbook and a clear action.

## 9. Dashboard specification

| Dashboard | Core panels |
| --- | --- |
| System Overview | API availability/latency, DB health, dependency status, active workers, queue backlog, critical alerts. |
| Workflow Operations | Runs by execution status, oldest active run, blocked tasks, task wait time, workflow failure trends. |
| Job & Worker Operations | Ready/running/retrying jobs, oldest queue age, attempts, lease expiries, worker eligibility and heartbeat age. |
| Artifact Integrity | Transfers by outcome, validation failures, checksum mismatches, quarantined versions and repair lineage. |
| Governance & Distribution | QA outcomes, rights states, approval outcomes, authorization allow/deny, distribution operations and unknown outcomes. |
| Security & Audit | Authentication failures, credential lifecycle events, worker quarantine, policy denials, sensitive administrative changes. |
| Recovery & Reliability | Restart/recovery events, outbox backlog, inbox duplicates, reconciliation queue and recovery-test status. |

Dashboards should link from aggregate metrics to filtered logs/traces and then to authoritative entity/operation records. Dashboard counts are not themselves authoritative business state.

## 10. Error taxonomy and operator-facing diagnostics

| Error class | Examples | Required diagnostic behavior |
| --- | --- | --- |
| Validation | Malformed request, unsupported schema version | Stable code, field path where safe, no internal stack disclosure. |
| Authentication | Missing/invalid/expired credential | Safe denial, principal reference if known, security event. |
| Authorization | Denied action, stale decision, emergency pause | Reason class and decision reference; never suggest bypass. |
| Conflict | Expected state version mismatch, duplicate idempotency mismatch | Return conflict with current version/reference where safe. |
| Dependency | DB, storage, queue, provider unavailable | Dependency class, retryability and correlation reference. |
| Execution | Worker failure, timeout, invalid result | Attempt record, error code, worker/job references. |
| Integrity | Checksum mismatch, manifest inconsistency | Quarantine and preserve exact version/evidence. |
| External outcome | Provider timeout after request, uncertain publish | Mark unknown; reconcile before retry. |
| Internal defect | Unhandled exception, invariant violation | Traceback restricted to diagnostics; safe external error and incident record. |

- Errors should distinguish retryable, non-retryable, conflict, blocked and unknown-outcome conditions.

- Do not retry authorization denial, rights denial, schema incompatibility or integrity failure as if transient.

- Never convert unknown external outcome into ordinary failure without reconciliation evidence.

## 11. Operational runbooks

### RB-01 — API/control-plane unavailable

1. Confirm alert and affected scope.

1. Check liveness/readiness and recent deployment/config changes.

1. Inspect database and critical dependency health.

1. Preserve queued/outbox state; do not clear queues as a first response.

1. Restore service using approved recovery procedure.

1. Verify readiness and reconcile in-flight operations; record incident evidence.

### RB-02 — Database unavailable or degraded

1. Confirm DB health and connection saturation.

1. Stop unsafe intake/claims if authoritative state cannot be committed.

1. Preserve pending durable work; do not switch silently to an in-memory source of truth.

1. Check approved backup/restore and failover procedure.

1. After recovery, verify constraints, outbox consistency and state versions.

1. Reconcile operations that may have crossed external boundaries.

### RB-03 — Queue backlog or stuck jobs

1. Inspect oldest ready job, queue age and eligible worker count.

1. Check job state, attempt history, lease expiry and dependency failures.

1. Determine whether work is waiting, executing, blocked or unknown.

1. Retry only when policy permits and side effects are known safe.

1. Record operator action and reason; verify backlog drains without duplicate effects.

### RB-04 — Worker lost or lease expired

1. Identify worker, job, attempt and lease references.

1. Check worker heartbeat, trust state, credential expiry and host status.

1. Fence the old attempt before reassigning work.

1. Determine whether the previous worker could have completed an external side effect.

1. Reconcile before retry; quarantine worker if compromise is suspected.

1. Verify stale result cannot overwrite current state.

### RB-05 — Artifact integrity failure

1. Identify exact ArtifactVersion and manifest.

1. Prevent downstream use and create/confirm quarantine record.

1. Preserve checksum, transfer and validation evidence.

1. Inspect source, transfer and storage integrity without overwriting the version.

1. If repair is authorized, create a new version with lineage and new validation.

1. Release only through approved disposition and revalidation.

### RB-06 — Authorization or rights denial

1. Capture decision ID, action, resource/version and destination.

1. Inspect authoritative rights, QA, approval, policy and emergency-pause facts.

1. Do not bypass the denial or edit a decision to make the operation pass.

1. Correct source evidence or request the appropriate review/decision.

1. Re-evaluate through the central policy path and retain both decisions.

### RB-07 — Unknown external publish outcome

1. Mark operation outcome unknown and block blind retry.

1. Preserve request time, destination, package/version and provider reference.

1. Query/reconcile external platform through an approved adapter/process.

1. Determine whether the side effect occurred and record evidence.

1. If confirmed, update observed outcome; if not, authorize a safe retry through policy.

1. Escalate unresolved ambiguity; do not claim success or failure without evidence.

### RB-08 — Suspected credential compromise

1. Identify principal, credential reference and affected scope.

1. Revoke/disable credential and stop affected worker/service assignments.

1. Preserve audit, authentication and operation evidence.

1. Rotate related secrets and inspect downstream access.

1. Assess affected artifacts, decisions and external operations.

1. Restore only after identity/trust verification and documented approval.

### RB-09 — Outbox dispatcher failure

1. Inspect pending count and oldest event age.

1. Check dispatcher health, transport availability and schema compatibility.

1. Retain outbox rows; do not delete or mark delivered manually without evidence.

1. Resume dispatch with idempotent delivery and consumer inbox deduplication.

1. Verify events are consumed and aggregate state remains consistent.

### RB-10 — Unexpected public distribution

1. Treat as high severity; pause applicable distribution action/destination.

1. Preserve exact package/version, destination, actor, authorization and provider evidence.

1. Determine whether operation is still in progress and prevent duplicate actions.

1. Notify the owner through the approved incident path.

1. Assess rights, approval, policy and adapter enforcement gap.

1. Record containment, external remediation and regression tests.

## 12. Operational safety rules

- Never delete, truncate, purge or manually edit queue, outbox, inbox, audit or operation records as a routine recovery shortcut.

- Never reset/revert/stash/clean/overwrite/rename user repository files or perform broad Git operations without explicit authorization.

- Never retry a potentially successful external side effect until it has been reconciled.

- Never bypass centralized authorization, rights checks, hard QA blockers or emergency pause to restore throughput.

- Do not mark a job complete because a worker process exited successfully; validate the expected result and artifact evidence.

- Do not treat a green health endpoint as proof that workflow correctness, governance or publishing safety is intact.

- Operator actions that change state must be attributable, reasoned and auditable.

- Use the least destructive recovery action first; preserve evidence before remediation.

## 13. Reliability indicators and SLO preparation

The source baseline does not define availability, latency, throughput, queue-age or recovery-time objectives. This section proposes how to define them without inventing targets.

| Indicator | Definition to agree | Measurement notes |
| --- | --- | --- |
| API availability | Successful eligible requests / total eligible requests over a window | Exclude expected client validation errors only by an explicit rule. |
| API latency | Percentiles for key command/query classes | Separate synchronous API latency from asynchronous completion time. |
| Workflow completion | Runs reaching an accepted terminal outcome / eligible runs | Define treatment of cancelled, blocked and manually stopped runs. |
| Queue age | Time from job becoming claimable to first claim | Track percentiles and oldest item; split by priority class. |
| Execution duration | Start-to-finish duration per task/job type | Separate worker execution from queue wait and external wait. |
| Recovery time | Time from incident detection to restored safe operation | Define safe restoration, not merely process uptime. |
| External outcome certainty | Operations with confirmed outcomes / operations requiring external side effects | Track unknown outcomes as a distinct risk metric. |
| Artifact integrity | Validated artifact versions / artifact versions requiring validation | Define required validators by artifact class. |

- Define service-level indicators first; owner-approved SLO targets second; alert thresholds third.

- Set objectives per critical journey, not one blended availability number.

- Do not claim an SLO is met until instrumentation, measurement window and exclusions are agreed.

- Error budgets and release gating are future policy decisions, not accepted requirements in this batch.

## 14. Operational ownership and escalation

| Operational area | Logical owner | Escalation trigger |
| --- | --- | --- |
| API/control plane | Workspace & Control Center / platform operations | Critical path unavailable or state integrity at risk. |
| Workflow and queue | Automation & Agent Orchestration | Stuck runs, growing backlog or inconsistent task/job state. |
| Workers | Worker Registry / execution operations | Worker trust, credential, lease or stale-result anomaly. |
| Artifacts | Asset Management | Checksum mismatch, quarantine, transfer or manifest integrity issue. |
| Governance | Quality and Governance domains | Rights/approval/authorization conflict or hard blocker bypass attempt. |
| Distribution | Distribution Studio with central authorization | Unknown outcome, wrong destination or unexpected public operation. |
| Security | Security/identity control owner | Credential compromise, unauthorized access or audit tampering. |
| Owner escalation | Workspace owner | Policy change, emergency pause, destructive recovery or external incident decision. |

The named logical owners are domain responsibilities, not a staffing/on-call roster. Actual people, response windows and escalation channels remain open.

## 15. Observability and operations acceptance tests

| Test ID | Scenario | Acceptance oracle |
| --- | --- | --- |
| OBS-T01 | Correlation propagation | A single command can be traced through event, workflow, task, job, attempt, artifact and external operation. |
| OBS-T02 | Causation linkage | Each asynchronous event/operation records the triggering command/event reference. |
| OBS-T03 | Structured logs | Critical events emit stable structured fields and machine-readable error codes. |
| OBS-T04 | Secret redaction | Tokens, keys, passwords and sensitive payloads are absent from logs and traces. |
| OBS-T05 | Metric cardinality | Metric labels use bounded dimensions and exclude raw entity IDs and personal data. |
| OBS-T06 | Trace trust boundary | Untrusted external trace headers cannot impersonate a principal or overwrite trusted correlation. |
| OBS-T07 | Health semantics | Liveness, readiness and startup checks produce distinct expected results. |
| OBS-T08 | DB outage | Readiness fails safely; no false success or in-memory authoritative fallback occurs. |
| OBS-T09 | Queue backlog alert | Oldest ready job age and backlog metrics trigger the configured alert in test. |
| OBS-T10 | Outbox backlog | Pending/oldest outbox event metrics identify dispatcher failure. |
| OBS-T11 | Lease expiry | Expired lease is visible in metrics/logs and old worker result is fenced. |
| OBS-T12 | Artifact integrity | Checksum mismatch emits diagnostic event and quarantine reference. |
| OBS-T13 | Authorization denial | Denied decision is traceable without exposing sensitive policy details. |
| OBS-T14 | Unknown external outcome | Dashboard/alert shows unknown distinctly; retry is blocked pending reconciliation. |
| OBS-T15 | Runbook usability | An operator can follow each runbook using the documented IDs, dashboards and evidence. |
| OBS-T16 | Recovery audit | Operator recovery action records actor, reason, time and affected references. |
| OBS-T17 | Restart recovery | Process restart preserves durable queue/outbox/attempt evidence. |
| OBS-T18 | Dashboard consistency | Dashboard values can be reconciled to authoritative records for a test fixture. |
| OBS-T19 | Alert actionability | Every alert has an owner, severity, runbook and clear first action. |
| OBS-T20 | Retention/privacy | Telemetry retention and access follow approved classification and retention policy. |

## 16. Open decisions

| ID | Decision required |
| --- | --- |
| OBS-O01 | Telemetry stack, libraries, exporters and local development profile. |
| OBS-O02 | Log format, event naming convention, severity mapping and error-code registry. |
| OBS-O03 | Trace propagation standard, async trace-link strategy and sampling policy. |
| OBS-O04 | Metric naming, units, cardinality budget and exporter conventions. |
| OBS-O05 | Dashboard platform, ownership and access controls. |
| OBS-O06 | Alert thresholds, severity levels, notification channels and escalation timing. |
| OBS-O07 | Availability, latency, throughput, queue-age and recovery SLO targets. |
| OBS-O08 | Telemetry retention, redaction, classification and data residency. |
| OBS-O09 | Health-check endpoint contract and dependency criticality matrix. |
| OBS-O10 | Incident commander/owner, on-call model and response windows. |
| OBS-O11 | External provider reconciliation procedures and operational access. |
| OBS-O12 | Audit immutability, log tamper-evidence and backup/restore process. |
| OBS-O13 | Local worker observability when offline or intermittently connected. |
| OBS-O14 | Cost limits and sampling/retention controls consistent with no-paid-services baseline. |
| OBS-O15 | Production runbook approval, rehearsal frequency and evidence storage. |

## 17. Freeze checklist and implementation boundary

- Confirm correlation fields and event naming against the API/Event Contract Standard and Batch 18.

- Confirm workflow/job/attempt/lease/artifact references against Batches 17 and 19.

- Confirm sensitive-data redaction, principal references and audit boundaries against Batch 20.

- Define critical user journeys and SLI measurement rules before setting SLO targets.

- Approve telemetry stack and local-first/free-first operational profile separately.

- Approve alert thresholds, owners, escalation and incident response channels.

- Rehearse runbooks in a disposable environment and retain evidence before relying on them operationally.

- Record owner disposition for open decisions; documentation progress does not equal approval.

- Obtain separate explicit implementation authorization before adding instrumentation, dashboards, alerts or operational configuration.

## 18. Final status

Batch 21 provides an observability and operational runbook design candidate. It does not claim telemetry has been instrumented, dashboards or alerts exist, SLOs are approved, runbooks have been rehearsed or production operations are ready.

Current gate: observability design candidate → source/contract reconciliation → owner review and freeze → separate explicit implementation authorization.

Safety invariant: preserve durable state and user work; fail closed on protected actions; reconcile uncertain external side effects; no paid services or production operation is authorized by this document.


## Source document metadata (preserved from DOCX)

- **Header:** NEXTDECODE CONTENT OS  |  P0 ARCHITECTURE SERIES
- **Footer:** Batch 21 — Observability, Logging, Metrics, Tracing & Operational Runbook  |  Design candidate

