# NEXTDECODE Shared Intelligence Core Contract 10
## Agent Intelligence, Resource Management & Orchestration
**Version:** 1.0  
**Status:** Working architecture contract — documentation only  
**Scope:** Shared Intelligence Core; agent registry, capability routing, model/provider selection, resource governance, task orchestration, and durable recovery  
**Authority:** Derived from accepted Creator Success Intelligence decisions and architecture baselines. This document does not authorize repository access or changes, provider connections, subscriptions, spending, credential creation, cloud provisioning, production execution, or publishing.

---

## 1. Purpose

Define the operating contract for how NEXTDECODE discovers, selects, authorizes, coordinates, monitors, and recovers AI agents, models, tools, providers, and execution workers.

The system must route work to the most suitable eligible capability while respecting task scope, data classification, provider protections, quotas, budgets, quality requirements, and owner-approved authority.

It must continue supported cloud-coordinated work when the user's PC is offline. Local-only tasks, including the current local Shorts Studio rendering path, must wait safely or use a separately approved eligible remote worker. The system must never pretend a local-only task completed while its required worker was unavailable.

## 2. Core principles

1. **Capability before identity:** route tasks based on declared and evaluated capabilities, not agent names or model popularity alone.
2. **Least privilege:** every agent and worker receives only the permissions needed for its specific task.
3. **No self-granted authority:** agents cannot grant themselves permissions, expand scopes, approve their own access, or bypass policy.
4. **Provider eligibility before optimization:** data-protection, residency, classification, and authorization requirements are hard eligibility filters.
5. **Quality, cost, latency, quota, and reliability are trade-offs:** optimize only among eligible candidates.
6. **Resource limits are authoritative:** forecasts and optimization cannot increase approved budgets or authorize new expenditure.
7. **Durable orchestration:** tasks, checkpoints, outputs, and recovery state survive process or machine interruption.
8. **Idempotent side effects:** uncertain external operations must be reconciled before retrying.
9. **Fallback is policy-bound:** fallback may use only already-approved providers, agents, tools, and workers for the same task/data scope.
10. **Human approval remains explicit:** sensitive, financial, policy, security, and publishing decisions retain their separate authority boundaries.
11. **Independent evaluation:** agent performance and consequential outputs must be assessed with evidence; an agent cannot self-certify.
12. **Auditability:** every routing, delegation, resource, recovery, and execution decision is traceable.

## 3. Logical architecture

The orchestration capability consists of the following logical services:

1. **Agent Registry:** agent identities, versions, capabilities, contracts, health, and lifecycle.
2. **Capability Catalog:** normalized descriptions of task capabilities and required inputs/outputs.
3. **Model & Provider Registry:** approved models, providers, terms, data protections, regions, and operational status.
4. **Policy & Authorization Engine:** task-scoped identity, permissions, data access, delegation, and operation authorization.
5. **Task Planner & Router:** decomposes work and selects eligible capabilities.
6. **Resource Manager:** quotas, budgets, reservations, usage, forecasts, and cost attribution.
7. **Orchestration Coordinator:** dependencies, state transitions, durable queue integration, and workflow control.
8. **Worker Registry & Scheduler:** local and remote execution workers, availability, leases, and capacity.
9. **Checkpoint & Recovery Manager:** checkpoints, retry classification, recovery, and reconciliation.
10. **Evaluation & Observability:** quality, latency, cost, failure, and security telemetry.

These are logical boundaries. They do not require ten separately deployed services.

## 4. Agent identity and registry

### 4.1 AgentIdentity

Each agent has a stable identity separate from the model/provider it uses.

Required fields:

- `agent_id`: UUIDv7 or another stable immutable identifier.
- `agent_name`: human-readable name.
- `agent_type`: planner, researcher, analyst, creator, reviewer, operator, monitor, or other versioned category.
- `workspace_scope`: permitted workspace references.
- `owner_ref`: accountable owner or system authority.
- `lifecycle_status`: proposed, active, suspended, retired.
- `created_at`, `updated_at`, and schema version.

An agent identity must not be reused for an unrelated capability or ownership scope.

### 4.2 AgentVersion

Each deployed agent definition is immutable and versioned.

It includes:

- Version identifier and sequence.
- Capability declarations.
- Input/output contracts.
- Tool requirements.
- Model/provider compatibility.
- Permission requirements.
- Data-classification ceiling.
- Resource profile.
- Reliability and quality baselines.
- Evaluation results.
- Change rationale and approval.
- Prior version and rollback reference.

A new version does not inherit expanded permissions automatically. Permissions are separately granted and reviewed.

### 4.3 AgentCapability

A capability declaration describes what an agent is allowed and able to do.

Fields include:

- Capability ID and version.
- Task types supported.
- Required input schema and produced output schema.
- Supported languages, modalities, and formats.
- Required tools and provider capabilities.
- Data classifications supported.
- Permission scopes required.
- Resource estimates and constraints.
- Quality expectations and evaluation evidence.
- Known limitations and prohibited uses.

A capability declaration is not proof of quality. Routing may use it as an eligibility input, while actual performance is evaluated separately.

## 5. Capability-based task routing

A `RoutingDecision` records why a capability was selected.

Routing sequence:

1. Parse task intent and required output contract.
2. Identify task risk, data classification, workspace, brand, and studio scope.
3. Determine required capabilities and tool access.
4. Filter out agents/providers/workers that fail security, privacy, rights, region, or permission gates.
5. Check quota, budget, availability, and capacity.
6. Evaluate eligible candidates against task-specific quality, reliability, latency, cost, and quota conditions.
7. Select a candidate or route to review/queue.
8. Record the routing rationale and policy version.

Candidate evaluation may consider:

- Task-specific quality and evaluation history.
- Output schema compatibility.
- Model strengths and known limitations.
- Data-protection eligibility.
- Cost and quota remaining.
- Latency and availability.
- Reliability and failure rate.
- Context window or modality support.
- Reproducibility and version stability.

A cheaper or faster candidate cannot be selected if it fails a hard eligibility requirement. No single universal ranking score is required; the routing policy may use constraints and task-specific weights.

## 6. Model and provider registry

### 6.1 ProviderRecord

A provider record includes:

- Provider identity and service category.
- Approved products/models/endpoints.
- Contract and data-protection terms, with verification date.
- Training-use and retention terms.
- Data residency and processing regions.
- Encryption and security evidence.
- Supported classifications and permitted purposes.
- Quota, pricing, and billing model.
- Availability and incident status.
- Approved workspace scopes.
- Verification owner and next review date.

### 6.2 Provider eligibility

Before sending task data, verify:

- Provider is approved for the task purpose and data classification.
- Data-protection terms are verified and current.
- Training use is prohibited unless explicitly authorized.
- Retention, processing location, and security protections are acceptable.
- Required redaction/minimization has occurred.
- Credentials are scoped and valid.
- Resource use is within approved limits.

If protections cannot be verified, the provider is ineligible for that task. The system must pause or use an already-approved fallback; it must not silently downgrade data protections.

### 6.3 ModelRecord

A model record captures:

- Provider and model identifier.
- Version or deployment revision where available.
- Modalities and capabilities.
- Known limitations and supported schemas.
- Pricing and quota characteristics.
- Evaluation results and benchmark context.
- Data-processing eligibility.
- Availability and deprecation status.

Model names alone are insufficient for reproducibility; retain the exact model/deployment identifier and relevant request configuration where permitted.

## 7. Task contract and delegation

Every orchestrated unit of work is represented by a durable `Task`.

Required fields:

- `task_id`: UUIDv7.
- `workflow_id` and parent task reference.
- Workspace, brand, and studio scope.
- Task type and objective.
- Input artifact/data references.
- Required output schema and acceptance criteria.
- Data classification and purpose.
- Required capabilities and risk level.
- Resource policy and limits.
- Assigned agent/version and worker identity.
- Permission/delegation reference.
- Priority, deadline, and dependencies.
- Idempotency key for side effects.
- Current state, checkpoint, and timestamps.

### 7.1 Task-scoped delegation

A `DelegationGrant` must specify:

- Agent and exact agent version.
- Task and workflow scope.
- Workspace/brand/studio scope.
- Permitted data and artifact references.
- Allowed operations and tools.
- Read/write/execute distinctions.
- Provider/model eligibility.
- Resource ceilings.
- Start and expiry time.
- Delegating authority and policy version.
- Revocation status.

Delegation is not transferable unless an explicit policy permits a narrowly scoped sub-delegation. The receiving agent cannot widen the grant or delegate higher authority than it holds.

### 7.2 Permission classes

At minimum, distinguish:

- Read permitted data.
- Create derived artifacts.
- Modify task-owned artifacts.
- Execute approved internal operations.
- Access external services.
- Perform external side effects.
- Request human approval.

Sensitive actions require explicit authorization at the relevant boundary. Tool availability does not imply permission to use the tool for every task.

## 8. Resource Management

### 8.1 Resource dimensions

Track resource consumption across:

- Provider/model tokens or usage units.
- API requests and rate limits.
- Image, audio, video, and storage operations.
- Local CPU, GPU, memory, and disk.
- Remote worker capacity.
- Queue concurrency and execution time.
- Object storage and data transfer.
- Paid third-party services and platform fees.

### 8.2 ResourceAccount

A resource account represents an approved quota or budget envelope.

Fields include:

- Account ID and owner scope.
- Provider/service/resource category.
- Billing or quota period.
- Approved limit and currency/unit.
- Current usage.
- Reserved usage.
- Remaining available amount.
- Reset time and reporting source.
- Alert thresholds.
- Hard-stop behavior.
- Policy version and audit history.

Resource accounts must distinguish provider-reported values from internal estimates.

### 8.3 UsageRecord and reservation

Every material resource operation should record:

- Task/workflow/agent/provider references.
- Resource type and quantity.
- Measurement source.
- Timestamp and billing period.
- Estimated or provider-reported classification.
- Cost calculation and price version, where applicable.
- Reservation and reconciliation status.

Preflight reservations prevent concurrent tasks from oversubscribing the same quota. After execution, actual provider usage is reconciled against the reservation. Differences remain visible.

### 8.4 Resource optimization authority

The system may:

- Forecast usage and remaining quota.
- Recommend lower-cost eligible alternatives.
- Route tasks among already-approved providers.
- Reserve resources within approved limits.
- Pause, defer, or reduce non-critical work when limits approach.
- Scale eligible infrastructure within already-approved services and budgets.
- Alert when a quota, budget, or provider reset is approaching.

It may not:

- Increase a budget or quota.
- Buy credits or subscriptions.
- Authorize a new provider/service/contract.
- Spend money or initiate payment.
- Expand financial limits.
- Transfer restricted data to an unapproved provider.

Autonomous optimization is limited to approved providers, services, capabilities, and resource envelopes.

## 9. Workflow orchestration

A `Workflow` groups tasks into a durable graph of dependencies.

The orchestration coordinator must support:

- Sequential, parallel, and conditional tasks.
- Dependency validation.
- Durable state transitions.
- Priority and deadline handling.
- Task leases and worker heartbeats.
- Checkpoint creation and restoration.
- Retry classification and bounded backoff.
- Dead-letter handling and escalation.
- Cancellation and safe pause.
- Idempotent result recording.
- Workflow-level audit and resource accounting.

Suggested task states:

`CREATED` → `READY` → `QUEUED` → `LEASED` → `RUNNING` → `CHECKPOINTED` → `SUCCEEDED`

Alternative states:

`RETRY_WAIT`, `BLOCKED`, `NEEDS_REVIEW`, `FAILED`, `CANCELLED`, `EXPIRED`, `RECONCILIATION_REQUIRED`

State transitions must be enforced centrally. Agents may report task results but cannot arbitrarily set authoritative workflow states.

## 10. Hybrid worker architecture

The accepted deployment direction is Hybrid:

- Cloud control plane remains available.
- Durable shared database and queue hold authoritative task state.
- Always-on scheduler coordinates work.
- Remote workers perform only approved supported tasks.
- Local worker executes PC-dependent tasks such as local Shorts Studio/FFmpeg rendering.
- Shared artifact storage retains durable references and versions.
- Dashboard and monitoring remain accessible independently of the user's PC.

### 10.1 WorkerIdentity

Each worker has:

- Stable worker ID.
- Worker type: local, remote, or managed service.
- Host/environment metadata.
- Supported capabilities.
- Resource capacity and constraints.
- Software/runtime version.
- Health and heartbeat status.
- Credential/delegation scope.
- Registration and expiry metadata.

### 10.2 Local worker offline behavior

When the PC is offline:

- Cloud-supported research, planning, monitoring, reporting, and coordination may continue if all required providers and services are available.
- Tasks requiring local files, local tools, or local rendering remain queued or safely deferred.
- The scheduler must not assign a local-only task to an unavailable worker.
- Local temporary state must not be the sole authoritative copy of workflow state.
- When the worker reconnects, it authenticates, refreshes eligibility, reconciles its state, and resumes only valid leased tasks.

### 10.3 Remote execution

Remote execution is permitted only for tasks whose data, code, assets, provider use, and resource scope are explicitly approved. Remote rendering is a future capability, not an assumed current capability.

## 11. Failure classification and recovery

Classify failures before retry:

- `TRANSIENT`: temporary network/service/resource issue.
- `RATE_LIMITED`: provider quota or rate limit.
- `AUTHORIZATION`: expired, revoked, or insufficient permission.
- `POLICY_BLOCKED`: data, rights, security, or governance prohibition.
- `INVALID_INPUT`: schema or required input failure.
- `QUALITY_FAILURE`: output does not meet acceptance criteria.
- `WORKER_LOST`: worker disappeared or lease expired.
- `PROVIDER_UNAVAILABLE`: eligible provider unavailable.
- `UNKNOWN_OUTCOME`: external side effect may have occurred but confirmation is missing.
- `PERMANENT`: non-recoverable task or contract failure.

Recovery rules:

1. Preserve completed outputs and checkpoint state.
2. Retry only classified recoverable failures.
3. Use bounded exponential backoff with jitter as an implementation policy.
4. Use fallback only to an eligible preapproved capability.
5. Resume from the last valid checkpoint when safe.
6. Never overwrite successful artifacts without explicit version creation.
7. Reconcile uncertain external side effects before retry.
8. Never blindly retry a publish, payment, message, or other external side effect.
9. Do not retry around authorization, policy, rights, or hard QA blockers.
10. Escalate repeated, unexplained, or high-impact failures.

## 12. Checkpoint contract

A `TaskCheckpoint` records:

- Task/workflow ID and sequence.
- Agent/version and worker identity.
- Completed steps and outputs.
- Input/output artifact references and hashes.
- Relevant state and progress markers.
- Resource reservations and usage reconciliation.
- External operation IDs and idempotency keys.
- Policy/delegation version.
- Timestamp and integrity metadata.

Checkpoint data must be sufficient to resume safely without repeating completed irreversible actions. Sensitive data in checkpoints remains subject to classification, encryption, access, and retention policies.

## 13. Agent evaluation and lifecycle

Agent evaluation should consider:

- Task-specific quality and correctness.
- Schema/contract compliance.
- Factuality and evidence handling.
- Reliability and recovery behavior.
- Latency and throughput.
- Resource consumption and cost.
- Security and permission compliance.
- Regression across representative test cases.
- Human review findings.

Lifecycle:

`PROPOSED` → `EVALUATED` → `APPROVED` → `ACTIVE` → `SUSPENDED` / `DEPRECATED` → `RETIRED`

New versions require appropriate testing and review. Independent evaluation is required for consequential capabilities. An agent cannot certify its own safety, permissions, or release readiness.

## 14. Observability and alerts

Track:

- Queue depth, age, and priority.
- Task/workflow state and duration.
- Worker availability and lease expiry.
- Provider/model availability and errors.
- Agent quality and regression.
- Resource usage, remaining quota, and forecasts.
- Cost attribution and anomalies.
- Retry, fallback, dead-letter, and reconciliation rates.
- Permission denials and policy violations.
- Checkpoint/restore outcomes.
- Emergency pause and revocation events.

Alerts should be risk-prioritized and delivered through the centralized notification system. Sensitive payloads should not be exposed in notification previews.

## 15. APIs and events

Illustrative versioned interfaces:

- `POST /v1/agents/registry`
- `GET /v1/agents/{agent_id}/versions`
- `POST /v1/agents/{agent_id}/evaluations`
- `GET /v1/providers/eligible`
- `POST /v1/tasks`
- `POST /v1/tasks/{task_id}/delegate`
- `POST /v1/tasks/{task_id}/checkpoints`
- `POST /v1/workflows`
- `POST /v1/routing/evaluate`
- `POST /v1/resources/preflight`
- `POST /v1/resources/reservations`
- `POST /v1/resources/usage`
- `POST /v1/workers/register`
- `POST /v1/workers/{worker_id}/heartbeat`
- `POST /v1/tasks/{task_id}/reconcile`

Illustrative events:

- `agent.version.approved.v1`
- `agent.suspended.v1`
- `routing.decision.created.v1`
- `task.created.v1`
- `task.queued.v1`
- `task.leased.v1`
- `task.checkpoint.created.v1`
- `task.succeeded.v1`
- `task.blocked.v1`
- `task.reconciliation_required.v1`
- `resource.reservation.created.v1`
- `resource.limit.warning.v1`
- `resource.limit.reached.v1`
- `worker.offline.v1`
- `worker.reconnected.v1`
- `provider.eligibility_changed.v1`

All events require durable delivery, schema versioning, idempotency, actor provenance, and workspace scope. Events do not grant permissions or authorize external side effects.

## 16. Audit and explainability

Retain:

- Agent identity and exact version.
- Model/provider and deployment version.
- Task/workflow and routing decision.
- Input/output references and hashes.
- Delegation grants and permission checks.
- Resource preflight, reservations, actual usage, and reconciliation.
- Worker identity, lease, and heartbeat history.
- Checkpoints, retries, fallback, and failure classifications.
- External operation IDs and idempotency records.
- Human reviews and approval decisions.
- Policy versions and security events.

The system must answer: **Why was this agent/provider/worker selected, what data and permissions did it receive, what resources did it consume, what did it produce, and how did the system recover if execution failed?**

## 17. Acceptance criteria

The contract is ready for implementation design when:

1. Agent identities and immutable versions are distinct from model/provider identities.
2. Capabilities have explicit input/output contracts and permission requirements.
3. Routing filters security, privacy, rights, residency, and authorization before optimization.
4. Every task has workspace scope, data classification, acceptance criteria, and resource policy.
5. Delegation is task-scoped, time-limited, revocable, and least-privilege.
6. Provider protections are verified before task data is transmitted.
7. Usage and quota tracking distinguishes reported values from estimates.
8. Reservations prevent concurrent quota oversubscription.
9. No autonomous path can increase budgets, buy services, or authorize new spending.
10. Workflows and checkpoints are durable across process and PC interruption.
11. Local-only work waits safely while the PC is offline.
12. Recovery preserves successful outputs and never blindly retries uncertain external side effects.
13. Fallback is limited to already-approved eligible capabilities.
14. Agent evaluation is independent, versioned, and auditable.
15. Emergency pause, credential revocation, and policy blocks cannot be bypassed by orchestration.
16. Every routing, permission, resource, and recovery decision is explainable.

## 18. Open implementation details

Not fixed by this contract:

- Exact agent capability taxonomy and registry schema.
- Model/provider allowlist and verification evidence.
- Task risk classification and routing weights.
- Resource accounting units and provider reconciliation behavior.
- Reservation expiry and concurrency policy.
- Retry/backoff values, lease durations, and heartbeat intervals.
- Checkpoint frequency and artifact integrity implementation.
- Worker operating-system/runtime support.
- Exact cloud and local worker technology.
- Agent evaluation datasets and acceptance thresholds.
- API/event payload schemas and database implementation.
- Budget amounts, provider subscriptions, and deployment region.

These require technical design and, where authority or spending is affected, explicit owner approval. No provider, model, budget, credential, subscription, or deployment is selected or authorized by this contract.

## 19. Decision traceability

This contract operationalizes accepted decisions covering:

- Capability-based Agent Intelligence and immutable agent versions.
- Task-scoped least-privilege permissions and short-lived delegation.
- Durable checkpoint-based recovery and idempotent side-effect handling.
- Intelligent Resource Management, quota tracking, reservations, forecasting, and safe pause.
- Approved-provider restrictions and external AI data-processing safeguards.
- Hybrid cloud control plane with local execution workers.
- Owner-unavailability continuity and silence-never-approval.
- Budget-bounded infrastructure scaling and resource allocation.
- Independent evaluation, security assurance, observability, and auditability.
- Centralized governance and emergency controls.

It is subordinate to the Master Blueprint, System Architecture Master Reference, Persistent Job Queue/Scheduler/Worker Architecture, Agent Contracts & Orchestration, Shared Knowledge & Learning Model, Research Intelligence & Evidence Operations, Content Quality/Rights/Governance Intelligence, Hybrid Deployment/Security/Monitoring contract, and owner-approved decision register. Conflicts must be recorded and reconciled rather than silently resolved by weakening a higher-priority rule.

---

**End of Contract 10 — Agent Intelligence, Resource Management & Orchestration 1.0**
