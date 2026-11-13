# NEXTDECODE Content OS
## Part 8 — Hybrid Deployment, Security, Monitoring, Backup & Recovery
**Version:** 1.0  
**Status:** Architecture proposal — not implementation approval  
**Date:** 31 October 2026

---

## 1. Purpose

This document defines the deployment and operational architecture for NEXTDECODE Content OS under the selected hybrid direction: an always-on cloud control plane coordinated with local and remote execution workers.

The central principle is:

> The cloud control plane owns durable system state and coordination. Workers execute bounded tasks. Local compute may go offline without taking the Content OS itself offline.

The system should remain useful when the user's PC is shut down or unavailable for an extended period. Supported cloud workflows can continue; tasks that specifically require local compute must wait or be assigned to an eligible remote worker. The architecture must not imply that local rendering can occur while the local machine is powered off.

This document is a proposed architecture baseline. It does not select vendors, authorize infrastructure spending, or authorize deployment.

### 1.1 Goals

- Define cloud control plane and execution plane responsibilities.
- Support local-first rendering with optional remote execution.
- Keep workflow and job state durable when local devices disconnect.
- Secure APIs, workers, artifacts, credentials, and external integrations.
- Provide monitoring, alerting, backup, restore, and disaster recovery.
- Define operational behavior during outages and partial failures.
- Keep the initial architecture cost-conscious and evolution-ready.

### 1.2 Non-goals

- Selecting a cloud vendor or region.
- Deploying production infrastructure.
- Enabling paid services or incurring recurring costs.
- Promising uninterrupted operation or an unverified recovery time.
- Moving all rendering to the cloud.
- Implementing multi-tenant SaaS, billing, or enterprise operations in the initial Creator Mode.

---

## 2. Locked deployment direction

The selected architecture is **Hybrid**.

### 2.1 High-level topology

```text
                         USER / DASHBOARD
                                |
                                v
+----------------------------------------------------------------+
|                    CLOUD CONTROL PLANE                          |
|                                                                |
|  API Gateway / Auth                                            |
|       |                                                        |
|  Workspace + Content Graph + Knowledge                         |
|       |                                                        |
|  Workflow Orchestrator <----> Durable Queue / Scheduler        |
|       |                         |                              |
|       +---- Agent Coordination |                              |
|       |                         +---- Cloud Worker Pool        |
|       |                                                        |
|  Governance / Approval / Publishing Authorization              |
|       |                                                        |
|  Artifact Registry + Durable Object Storage                    |
|       |                                                        |
|  Monitoring / Audit / Alerting / Backup                        |
+------------------------------+---------------------------------+
                               |
                     Authenticated secure channel
                               |
                   +-----------v-----------+
                   |   LOCAL WORKER        |
                   |   User's PC           |
                   |                       |
                   |   Shorts Studio       |
                   |   FFmpeg / Rendering  |
                   |   Local cache         |
                   |   Worker agent        |
                   +-----------------------+
```

This is a logical topology. The first implementation may combine services in fewer deployable units, provided the responsibility boundaries remain explicit.

### 2.2 Cloud control plane responsibilities

The cloud control plane is authoritative for:
- user and workspace identity;
- canonical content and workflow records;
- job queue and scheduler state;
- agent and worker registration;
- studio capability registry;
- artifact metadata and durable storage references;
- policy, quality, rights, approval, and authorization records;
- audit history;
- dashboard and operational status;
- notifications and monitoring.

The control plane must not rely on the local PC as its only source of durable state.

### 2.3 Execution plane responsibilities

Execution workers perform tasks assigned by the control plane:
- local worker: Shorts Studio, FFmpeg, local files, and resource-intensive local production;
- cloud worker: supported research, coordination, lightweight processing, and other explicitly approved remote capabilities;
- future remote rendering worker: optional capability, subject to cost, data, and quality evaluation.

Workers do not own global workflow state or policy decisions.

### 2.4 Authority and synchronization

- Cloud state is authoritative for workflow, job, approval, and artifact metadata.
- A worker may maintain local execution state and cache for resilience.
- Worker updates are reconciled through authenticated, idempotent APIs.
- Conflicting local state must not overwrite newer authoritative cloud state.
- Offline work is accepted only within a bounded lease or offline-execution policy.
- The system records what actually happened; it must not invent completion events for work that was not confirmed.

---

## 3. Deployment environments

Separate environments reduce the risk that experiments affect real content or external accounts.

### 3.1 Proposed environments

| Environment | Purpose | External side effects |
|---|---|---|
| Local development | Contract and component development | Disabled by default |
| Test / CI | Automated tests and integration simulations | Mocked or sandboxed |
| Staging | End-to-end validation with controlled test data | Sandbox accounts only |
| Production | Real workspace and approved workflows | Only through centralized authorization |

Environment separation should cover:
- databases and storage;
- queue and scheduler namespaces;
- API credentials and secrets;
- worker identities;
- external platform accounts;
- logs and audit records;
- policy versions and approval records.

Production data and credentials must not be copied into development or test environments without an explicit, secure, approved process.

### 3.2 Configuration management

- Keep configuration separate from application code.
- Validate required configuration at startup.
- Use environment-specific configuration profiles.
- Never commit secrets to source control.
- Record the effective non-secret configuration version for important operations.
- Apply changes through a controlled, auditable process.
- Do not allow an agent to silently modify production configuration.

---

## 4. Local and remote worker lifecycle

### 4.1 Worker registration

Each worker should register:
- stable worker identity;
- owner and workspace scope;
- execution location;
- supported capabilities;
- software and adapter versions;
- available resources;
- concurrency limits;
- health state;
- last heartbeat;
- current leases and running jobs.

A worker may receive only jobs matching its declared capabilities and authorization scope.

### 4.2 Worker states

Proposed states:
- `registered`;
- `ready`;
- `busy`;
- `degraded`;
- `offline`;
- `draining`;
- `disabled`;
- `quarantined`.

The scheduler must distinguish an unavailable worker from a failed job.

### 4.3 Heartbeats and leases

- Workers send periodic heartbeats while connected.
- The control plane tracks last-seen time and health.
- Jobs are claimed using a lease with an expiry.
- A worker must renew its lease while executing.
- If a lease expires, the orchestrator determines whether the job can be safely reassigned.
- Non-idempotent operations must be reconciled before retry or reassignment.
- A stale worker must not be allowed to commit results for an expired lease without validation.

Exact heartbeat intervals, lease duration, and renewal cadence remain open engineering decisions. They should be based on expected task duration and network reliability.

### 4.4 Graceful shutdown

When a local worker is shutting down:
1. Stop accepting new jobs.
2. Report `draining`.
3. Finish safe tasks where practical.
4. Checkpoint resumable tasks.
5. Release or allow leases to expire safely.
6. Upload completed artifacts and state updates.
7. Report final health state.

Forced shutdowns must be handled through lease expiry and recovery, not by assuming graceful completion.

---

## 5. PC-offline and extended-unavailability behavior

This is a key product requirement.

### 5.1 When the local PC is off

The cloud control plane continues to:
- accept user requests;
- store content and workflow changes;
- run supported cloud agents and research tasks;
- schedule and coordinate jobs;
- track approvals and pending work;
- monitor services;
- notify the user of important outcomes.

Local-only tasks:
- remain queued with a clear `waiting_for_local_worker` reason; or
- are assigned to a compatible remote worker if such capability has been explicitly enabled.

### 5.2 When the user is unavailable for a week

The system should continue only within previously configured permissions and policies.

It may:
- run approved research and analysis workflows;
- prepare drafts and production packages;
- render on remote workers if that capability is configured;
- run deterministic quality and rights checks;
- hold items requiring human review;
- publish only if a separately approved conditional-publishing policy explicitly permits the exact action and all gates pass.

It must not:
- interpret user silence as approval;
- expand its own permissions;
- change brand or publishing policy;
- bypass rights or safety blockers;
- publish content outside pre-authorized scope;
- spend money beyond an explicitly configured budget;
- continue indefinitely after a required credential, approval, or policy expires.

### 5.3 Reconnection and reconciliation

When the local PC reconnects:
1. Authenticate the worker.
2. Validate worker software and capability version.
3. Reconcile outstanding job leases.
4. Compare local checkpoints with authoritative job state.
5. Verify hashes and artifact versions.
6. Resume only jobs that remain eligible.
7. Upload and register missing artifacts.
8. Report conflicts for safe recovery.

The worker must not replay a completed external side effect merely because its local completion receipt was lost.

---

## 6. Security architecture

Security applies across the control plane, workers, agents, artifacts, and connected services.

### 6.1 Identity and access management

- Use a distinct identity for each user, service, worker, and integration.
- Apply least privilege by default.
- Scope access to workspace, job, artifact, and operation.
- Separate human roles from service identities.
- Require explicit authorization for administrative and high-risk actions.
- Support credential rotation and revocation.
- Record authentication and authorization events.

### 6.2 API security

- Require authenticated API access.
- Authorize every request against the requested resource and action.
- Validate schemas, sizes, and allowed values.
- Apply rate limits and abuse controls.
- Use idempotency keys for state-changing operations.
- Protect against replay and forged callbacks.
- Use secure transport for network communication.
- Avoid exposing internal service endpoints publicly without a defined need.

### 6.3 Worker security

- Authenticate workers using unique identities.
- Do not embed long-lived shared secrets in worker images or source code.
- Scope worker credentials to assigned capabilities and jobs.
- Keep local caches separate from user personal files where practical.
- Restrict filesystem access to approved working directories.
- Restrict network egress where feasible.
- Validate downloaded inputs before processing.
- Isolate untrusted media and documents from privileged services.
- Support remote disablement and credential revocation.

### 6.4 Agent security

- Agents receive task-scoped context and tool profiles.
- Agents do not receive ambient shell, filesystem, or publishing credentials.
- External content is treated as untrusted data, not system instruction.
- Tool services independently validate agent requests.
- Agent outputs are validated before being persisted or used downstream.
- Agents cannot modify their own permissions, policies, or qualification status.

### 6.5 Artifact and data security

- Encrypt data in transit and at rest where supported.
- Use private storage by default.
- Grant access to exact artifacts and versions.
- Use expiring access grants for file transfers.
- Validate file type and integrity.
- Apply retention and deletion rules.
- Avoid exposing permanent public object-storage URLs.
- Keep rights and provenance metadata linked to artifacts.

### 6.6 Secrets management

Secrets include API keys, OAuth refresh tokens, passwords, signing keys, and platform credentials.

Requirements:
- store secrets in a dedicated secret-management facility;
- never place secrets in prompts, source files, or ordinary logs;
- retrieve secrets only inside the service that needs them;
- use scoped and short-lived credentials where possible;
- rotate and revoke credentials;
- redact values from exceptions and telemetry;
- audit secret access without recording the secret itself.

The exact secrets provider remains undecided.

---

## 7. Network and trust boundaries

### 7.1 Trust zones

Proposed trust zones:
1. User browser and dashboard.
2. Cloud public API boundary.
3. Private control-plane services.
4. Durable database, queue, and object storage.
5. Cloud worker network.
6. Local worker and local cache.
7. External providers and publishing platforms.

Every boundary needs explicit authentication, authorization, and data-flow rules.

### 7.2 Local worker connectivity

Prefer an outbound authenticated connection from the local worker to the control plane. Avoid requiring inbound access to the user's home network unless a specific capability justifies it.

The local worker should:
- poll or receive work through an authenticated channel;
- download only authorized inputs;
- upload only registered outputs;
- report health and job state;
- renew or release leases;
- disconnect safely.

### 7.3 External provider boundaries

Research providers, AI model providers, storage providers, analytics providers, and social platforms are separate trust domains.

For each integration, define:
- data sent to the provider;
- credentials and scopes;
- retention and logging implications;
- rate limits and failure behavior;
- cost controls;
- provider outage handling;
- fallback and portability strategy.

No provider is assumed approved merely because an integration is technically possible.

---

## 8. Monitoring and observability

Monitoring must cover both business workflow health and infrastructure health.

### 8.1 System health

Monitor:
- API availability and latency;
- database health and connection saturation;
- queue depth and oldest-job age;
- scheduler execution and missed schedules;
- worker availability and heartbeat age;
- artifact storage capacity and transfer failures;
- authentication and authorization errors;
- provider availability and rate limits;
- backup completion and restore-test results.

### 8.2 Workflow health

Monitor:
- jobs queued, running, blocked, and failed;
- jobs waiting for local versus remote workers;
- retry and dead-letter counts;
- workflows stuck in a state beyond expected duration;
- approval backlog and expiry;
- quality and rights gate failure rates;
- artifact validation failures;
- distribution attempts and reconciliation status.

### 8.3 Business and cost visibility

Track:
- content items by workflow stage;
- output volume by format;
- cost per research, generation, render, and distribution task where measurable;
- storage growth;
- provider usage and quota;
- remote worker compute usage;
- recurring infrastructure costs.

Cost dashboards should distinguish estimated from invoiced or provider-reported actual cost.

### 8.4 Alerts

Alerts should be actionable and severity-based.

Examples:
- **Critical:** unauthorized publishing attempt, suspected credential compromise, data integrity failure.
- **High:** control-plane outage, database unavailable, emergency pause failure, backup failure beyond policy.
- **Medium:** queue backlog, worker offline, repeated provider errors, storage approaching limit.
- **Low:** non-urgent capacity trend, stale dashboard metric, routine warning.

Notification channels and thresholds remain open decisions.

### 8.5 Audit versus telemetry

- Audit records are durable evidence of security- and governance-relevant decisions.
- Operational logs support troubleshooting.
- Metrics support trends and alerting.
- Traces connect requests across services.

Do not treat short-retention telemetry as a substitute for durable audit history. Avoid logging secrets or unnecessary personal data.

---

## 9. Backup and recovery

Backups are useful only if restoration is tested.

### 9.1 Data classes

| Data | Protection approach |
|---|---|
| Canonical database | Automated backups and point-in-time recovery if supported |
| Artifact/object storage | Versioning, replication, or backup according to cost and risk |
| Queue and scheduler state | Durable storage and recovery/reconciliation procedures |
| Policies and approval records | Versioned durable storage and audit protection |
| Configuration | Version-controlled non-secret configuration and protected secret backup |
| Credentials | Provider-supported secure recovery and rotation process |
| Local worker cache | Disposable; rebuild from durable artifact references |
| Logs and metrics | Retention policy based on operational and audit needs |

### 9.2 Backup policy

A backup policy must define:
- data scope;
- frequency;
- retention;
- encryption;
- storage location and isolation;
- access permissions;
- backup verification;
- restore-test cadence;
- deletion and expiry;
- responsible owner.

Exact frequencies and retention periods should be selected based on acceptable data loss, cost, and provider capabilities.

### 9.3 Recovery objectives

Two values must be explicitly decided for each critical service:

- **RPO (Recovery Point Objective):** maximum acceptable amount of data loss measured in time.
- **RTO (Recovery Time Objective):** target time to restore service after a failure.

Do not invent RPO/RTO targets before the database, storage, deployment, and cost model are selected.

### 9.4 Restore testing

A restore test should verify:
1. database restoration;
2. artifact availability and checksum integrity;
3. queue and workflow reconciliation;
4. policy and approval record consistency;
5. worker re-registration;
6. credential rotation where needed;
7. dashboard and API operation;
8. audit continuity;
9. prevention of duplicate external side effects.

A backup that has never been restored is not sufficient evidence of recoverability.

---

## 10. Disaster recovery and failure scenarios

| Scenario | Expected system behavior |
|---|---|
| Local PC shutdown | Cloud control plane continues; local-only jobs wait |
| Local network outage | Worker disconnects; leases and jobs recover safely |
| Cloud worker failure | Reassign only safe, eligible jobs |
| Model provider outage | Retry or use an explicitly approved fallback; otherwise pause |
| Database outage | Stop state-changing operations that cannot be made durable |
| Queue outage | Do not silently run untracked jobs; recover from durable workflow state |
| Artifact storage outage | Pause transfers and dependent gates; preserve job state |
| Credential compromise | Revoke affected credentials, pause relevant operations, investigate |
| Publishing provider outage | Reconcile operation status before retrying |
| Accidental policy change | Pause affected workflow and restore an approved policy version |
| Corrupt artifact | Quarantine, preserve evidence, regenerate or restore from verified source |
| Cloud region/service outage | Follow provider-specific recovery plan; do not claim failover unless configured and tested |

### 10.1 Fail-safe behavior

When a critical dependency is unavailable:
- preserve known durable state;
- stop unsafe state transitions;
- do not assume a gate passed;
- do not issue publishing authorization;
- expose a clear blocked or degraded reason;
- resume only after state reconciliation.

### 10.2 Recovery priority

A proposed recovery order:
1. identity, secrets, and security controls;
2. database and canonical workflow state;
3. queue and scheduler;
4. artifact registry and storage;
5. governance and authorization services;
6. dashboard and monitoring;
7. workers and studios;
8. optional integrations and analytics.

The exact order may vary with dependency design and should be validated in the deployment runbook.

---

## 11. Cost and resource governance

The initial product is local-first and free-first, with a target of avoiding unnecessary recurring cost. “Free-first” is a design goal, not a guarantee that all infrastructure or provider usage will be free.

### 11.1 Cost controls

- Set explicit budgets and usage ceilings before enabling paid services.
- Track model, storage, bandwidth, and compute usage.
- Prefer local rendering where it is operationally practical.
- Use remote workers only for supported tasks and within configured limits.
- Apply job concurrency and resource limits.
- Avoid keeping idle compute running without a measured need.
- Set storage lifecycle and retention rules.
- Require explicit authorization before enabling a paid provider or increasing a budget.
- Alert before usage reaches configured limits.

### 11.2 Graceful degradation

When a budget or quota is reached:
- stop or defer optional work;
- preserve queued tasks;
- prioritize critical workflow and security operations;
- do not silently switch to a paid provider;
- report which capabilities are paused and why.

---

## 12. Operational runbooks

Before production operation, create concise runbooks for:
- local worker installation, update, pause, and removal;
- worker authentication and credential rotation;
- worker offline and reconnect recovery;
- stuck job and expired lease recovery;
- queue backlog and dead-letter inspection;
- artifact transfer and checksum failure;
- provider outage and rate limiting;
- emergency publishing pause;
- credential compromise;
- database restore;
- artifact restore;
- policy rollback;
- publishing outcome reconciliation.

Runbooks should include owner, prerequisites, safe steps, verification, rollback, and escalation route. Do not rely on an agent improvising recovery for a high-risk incident.

---

## 13. Open decisions

The following remain intentionally undecided:

1. Cloud provider, region, and deployment topology.
2. Database and durable queue technology.
3. Object-storage provider and replication strategy.
4. Local worker packaging and update mechanism.
5. Worker authentication and secret-management provider.
6. Monitoring, logging, tracing, and alerting providers.
7. Backup frequency, retention, and storage isolation.
8. RPO and RTO targets.
9. Remote rendering availability and cost limits.
10. Provider fallback rules and data-transfer constraints.
11. Notification channels and severity thresholds.
12. Budget ceilings and approval process for paid usage.
13. Data retention, archival, and deletion rules.
14. Security review and incident-response ownership.

These decisions require a technology comparison and cost model before infrastructure selection.

---

## 14. Implementation sequence

### Stage A — Operational design
- Define trust boundaries and service identities.
- Define worker lifecycle, heartbeat, lease, and reconnect behavior.
- Define environment separation.
- Define monitoring and audit requirements.

### Stage B — Durable foundation
- Deploy the selected database, queue, and artifact storage.
- Establish backups and test restoration.
- Add authenticated worker registration.
- Add local worker heartbeat and safe job claiming.

### Stage C — Hybrid operations
- Integrate the Shorts local worker.
- Add remote-capable worker execution for approved tasks.
- Test PC-offline and extended-unavailability scenarios.
- Validate idempotency and reconciliation.

### Stage D — Security and resilience
- Run permission-boundary and secret-leak tests.
- Simulate provider, worker, database, queue, and storage failures.
- Test emergency pause and credential revocation.
- Perform restore and disaster-recovery exercises.

### Stage E — Controlled production readiness
- Confirm budgets, operational ownership, runbooks, alerts, and recovery objectives.
- Validate all governance controls from Part 6.
- Conduct end-to-end dry runs.
- Enable real external side effects only after separate explicit authorization.

This is a proposed sequence, not deployment approval.

---

## 15. Acceptance criteria

Part 8 is ready to guide implementation when:

- [ ] Hybrid deployment responsibilities are explicit.
- [ ] Cloud control plane is authoritative for durable workflow state.
- [ ] Local and remote workers have authenticated identities and scoped capabilities.
- [ ] Worker heartbeat, lease, shutdown, and reconnect behavior are defined.
- [ ] PC-offline behavior is truthful and testable.
- [ ] User unavailability does not imply approval or permission expansion.
- [ ] Environments and credentials are separated.
- [ ] API, worker, agent, artifact, and secret security controls are defined.
- [ ] Monitoring covers system, workflow, governance, and cost health.
- [ ] Audit records are distinguished from telemetry.
- [ ] Backup scope, retention, restore, RPO, and RTO are defined before production.
- [ ] Restore tests validate data and artifact integrity.
- [ ] Disaster scenarios have safe recovery behavior.
- [ ] Cost limits and paid-service authorization are defined.
- [ ] Operational runbooks exist for high-risk incidents.
- [ ] Production readiness is demonstrated through tests, not assumed from architecture documents.
- [ ] No infrastructure deployment or production operation is inferred or authorized by this document.

---

## 16. Relationship to the other architecture parts

| Part | Relationship |
|---|---|
| Part 1 — System Architecture Master Reference | Defines the overall Content OS architecture |
| Part 2 — Shorts Studio Pipeline Contract | Defines the first production engine and its workflow boundary |
| Part 3 — Shared Data Model & Content Graph | Defines canonical data, identities, versions, and relationships |
| Part 4 — Persistent Job Queue, Scheduler & Worker Architecture | Defines durable execution and recovery mechanics |
| Part 5 — Agent Contracts & Orchestration | Defines bounded agent tasks, tools, and handoffs |
| Part 6 — Centralized Quality, Rights, Approval & Publishing Governance | Defines centralized authorization and safety enforcement |
| Part 7 — Studio Integration APIs & Artifact Management | Defines studio interfaces and durable artifact exchange |
| Part 8 — Hybrid Deployment, Security, Monitoring, Backup & Recovery | Defines how the platform is deployed and operated reliably |

---

## 17. Eight-part architecture completion

The eight architecture documents now form a proposed system reference:

1. System Architecture Master Reference.
2. Shorts Studio Pipeline Contract.
3. Shared Data Model & Content Graph.
4. Persistent Job Queue, Scheduler & Worker Architecture.
5. Agent Contracts & Orchestration.
6. Centralized Quality, Rights, Approval & Publishing Governance.
7. Studio Integration APIs & Artifact Management.
8. Hybrid Deployment, Security, Monitoring, Backup & Recovery.

Completion of these documents does not mean the system is implemented, fully specified, secure, or production-ready.

### Recommended next activity — Architecture Reconciliation & Implementation Readiness Review

Before implementation:
- reconcile terminology, IDs, state models, and contracts across all eight parts;
- identify contradictions, duplicate responsibilities, and unresolved dependencies;
- classify decisions as locked, proposed, or open;
- validate assumptions against the existing Shorts Studio reports when repository inspection is explicitly authorized;
- produce a prioritized foundation implementation plan with acceptance tests and migration boundaries;
- separately decide technology choices and budget;
- obtain explicit authorization before repository, infrastructure, or production work.

**Document status:** Proposed architecture baseline. No implementation, repository access, code modification, deployment, infrastructure spending, account change, upload, or publishing authorization is granted by this document.
