# NEXTDECODE — Parallel Work Package B
## Agent Intelligence, Capability Routing & Qualification Reconciliation

**Document ID:** `NEXTDECODE_PWB_AGENT_INTELLIGENCE_CAPABILITY_RECONCILIATION_0.1`  
**Version:** 0.1  
**Date:** 2 November 2026  
**Status:** RECONCILIATION REPORT — DOCUMENTATION ONLY  
**Implementation authorization:** NOT GRANTED  
**Authority:** Analysis for cross-track review; no decision below is an owner approval unless explicitly labelled ACCEPTED and traceable to an accepted ADR/CF.

> This report does not authorize code changes, tests, Git operations, integration, deployment, provider connection, credential creation, spending, production execution or publishing. It does not modify OpenCode's reconciliation artifact or any WP-2/WP-3 file.

---

## 1. Purpose and scope

### 1.1 Purpose

Define the agent-intelligence side of NEXTDECODE Automation & Agent Orchestration and reconcile it with the existing accepted architecture, WP-2/WP-3 design candidates, the Canonical Contracts Pack, and OpenCode's execution/Agent Handler boundary.

The report answers one question:

> How should NEXTDECODE identify, qualify, route, constrain and audit reasoning agents without duplicating or weakening the WP-2/WP-3 execution and worker-trust work?

### 1.2 In scope

1. Agent identity, versioning and lifecycle.
2. Agent capability taxonomy.
3. Declared vs verified vs available vs authorized capability facts.
4. Model/provider selection and fallback eligibility.
5. Agent qualification and independent evaluation.
6. Resource, quota, cost and task limits.
7. Agent permission profiles and tool-profile boundaries.
8. Agent registry integration requirements.
9. Interfaces required from WP-2, WP-3 and WP-5.
10. Compatibility with OpenCode's Agent Handler and task/result contracts.

### 1.3 Out of scope

- Redesigning WP-2 durable execution, leases, retries or outbox/inbox.
- Redesigning WP-3 worker enrollment, credentials, trust or isolation.
- Implementing the Agent Handler or any runtime.
- Selecting providers, models, budgets, credentials, regions or deployment topology.
- Creating or approving an agent capability that the owner has not authorized.
- Freezing any candidate decision.

### 1.4 Status vocabulary used in this report

| Label | Meaning |
|---|---|
| **ACCEPTED** | Explicitly accepted in an ADR/CF/owner record; not reopened here |
| **SOURCE-DEFINED** | Required by an accepted or governing source |
| **PROPOSED** | Recommendation for review; not approved |
| **RECOMMENDED DEFAULT** | Conservative default for owner review; not frozen |
| **WORKING CONTRACT** | Logical architecture contract; documentation only; not acceptance |
| **OPEN** | Requires a decision |
| **NOT MOUNTED** | Source referenced by the task but absent from the reviewed filesystem |
| **CONFLICT** | Documents disagree; no silent resolution |

---

## 2. Source inventory, authority and freshness

### 2.1 Reviewed sources

| Source | Version / status | Authority | Use in this report |
|---|---|---|---|
| `NEXTDECODE_Shared_Intelligence_Core_Contract_10_Agent_Intelligence_Resource_Management_Orchestration_1.0.md` | 1.0; “Working architecture contract — documentation only” | Working contract; not accepted/frozen | Primary agent identity, capability, routing, resource and evaluation model |
| `NEXTDECODE_System_Architecture_Pipeline_Part_5_Agent_Contracts_Orchestration_1.0.md` | 1.0; “Architecture proposal — not implementation approval” | Proposal | Agent roles, task/result envelopes, permissions, evaluation, handoffs |
| `NEXTDECODE_P0_WP2_Durable_Job_Workflow_Execution_0.1.md` | 0.1; “DESIGN CANDIDATE — OWNER REVIEW REQUIRED” | Design candidate; not frozen | Job/attempt/lease, dispatch, failure and recovery interface |
| `NEXTDECODE_P0_WP3_Worker_Registry_Contract_Boundary_0.1.md` | 0.1; “DESIGN CANDIDATE — OWNER REVIEW REQUIRED” | Design candidate; not frozen | Worker identity, four capability facts, credentials, assignment authorization |
| `NEXTDECODE_Canonical_Contracts_Pack_1.0.md` | 1.0; “Proposed contract baseline — approval pending” | Proposed baseline | Canonical IDs, entity glossary, task/job/result envelopes, authorization grant |
| `NEXTDECODE_Architecture_Reconciliation_Implementation_Readiness_Report_1.0.md` | 1.0; document-level reconciliation | Analysis; owner authority stated | Cross-document conflicts and readiness context |
| `NEXTDECODE_P0_Owner_Review_Contract_Freeze_Decision_Record_0.1.md` | 0.1; “OWNER DECISION DRAFT — NOT YET APPROVED” | Owner decision draft | WP-2/WP-3 dispositions are OPEN; no freeze |
| `NEXTDECODE_Artifact_08_v1.2_Consolidated_Freeze_Candidate.md` | v1.2; consolidated freeze candidate | Accepted ADRs/CFs plus proposals | Accepted worker/capability constraints; proposed detail |
| `NEXTDECODE_Accepted_P0_Architecture_Decision_Baseline_1.0.md` | Accepted baseline | Accepted ADRs/CFs | ADR-005, ADR-010 and related constraints |
| `NEXTDECODE_P0_Decision_Resolution_Register_0.1.md` | 0.1; proposed/open register | Decision register | ODR-08/09/10 worker capability facts; no agent-specific ODR |
| OpenCode reconciliation report / Agent Handler interface reference | **NOT MOUNTED** | — | Cannot be inspected; interface assumptions are flagged in §12 |

### 2.2 Freshness check

- No newer versioned revision of Contract 10, Part 5, WP-2, WP-3 or the Canonical Contracts Pack was found in the mounted workspace.
- `NEXTDECODE_P0_Batch06_WP2_Durable_Workflow_and_Job_Execution_Design.docx` and `NEXTDECODE_P0_Batch07_WP3_Worker_Registry_Identity_Trust_Capabilities.docx` exist as implementation-planning derivatives. They are not versioned contract revisions and were not treated as superseding the v0.1 design candidates. Their status must be confirmed by Track A/owner before use.
- The OpenCode Agent Handler reconciliation artifact referenced by the task is not present in the mounted workspace. This is a coordination gap, not evidence that the artifact does not exist.

### 2.3 Source-authority conclusion

The only accepted agent-adjacent constraints are the accepted ADRs/CFs and the owner constraints in the freeze decision record. **The agent intelligence model itself is not accepted.** Contract 10 is a working contract; Part 5 is a proposal; the Canonical Pack is a proposed baseline; WP-2/WP-3 are design candidates with owner dispositions still OPEN.

---

## 3. Existing decisions and their authority

### 3.1 Accepted decisions that constrain this work

| ID | Accepted direction | Implication for agents |
|---|---|---|
| ADR-001 | UUIDv7 canonical IDs | Agent and agent-version IDs should use the canonical ID system; no names as identity |
| ADR-002 | PostgreSQL-compatible authoritative shared state | Agent registry persistence, if implemented, must use the approved shared store, not a private store |
| ADR-003 | Database-backed durable queue with outbox/inbox | Agent tasks dispatched through WP-2 must use the durable execution path |
| ADR-004 | Versioned HTTP/JSON contracts with schema validation | Agent task/result/capability records require explicit schema versions |
| ADR-005 | Unique worker identity, scoped short-lived credentials, capability-based authorization | Agent execution on a worker inherits the WP-3 worker boundary; capability is not permission |
| ADR-007 | Centralized authorization; adapters cannot bypass; auto-publishing disabled | Agent permission profiles cannot bypass WP-5; agents cannot authorize publishing |
| ADR-008 | QA outcomes and hard blockers | Agent quality analysis does not replace the QA gate |
| ADR-009 | Evidence-backed rights and use-specific enforcement | Agent outputs that reuse assets/claims remain subject to rights gates |
| ADR-010 | Separate lifecycle state machines for content, workflow, execution, review, approval, authorization and distribution | Agent lifecycle, task lifecycle, job lifecycle and worker lifecycle must remain distinct |
| CF-13/CF-14 | Declared/verified/available/authorized capability facts; capability declaration is not permission; bounded isolation; admin/production/QA/publishing permissions separated | Accepted for workers; this report PROPOSES the same separation for agents — owner confirmation required; do not collapse capability facts |
| CF-20 | Accepted rights vocabulary | Agent outputs and asset use remain subject to the accepted rights states |

### 3.2 Proposed, not accepted

| Source | Proposal | Status |
|---|---|---|
| Contract 10 §4 | AgentIdentity, AgentVersion, AgentCapability | WORKING CONTRACT — not accepted |
| Contract 10 §5–§6 | Capability routing; provider/model eligibility | WORKING CONTRACT — not accepted |
| Contract 10 §8 | ResourceAccount, reservations, usage | WORKING CONTRACT — not accepted |
| Contract 10 §13 | Agent lifecycle and independent evaluation | WORKING CONTRACT — not accepted |
| Part 5 §3–§7 | Agent roles, task/result envelopes, permissions, human review | PROPOSAL — not implementation approval |
| Part 5 §9 | Qualification states and evaluation layers | PROPOSAL — not accepted |
| Canonical Pack §1, §3.2–§3.5 | Agent entity, Task/Job/Result envelopes | PROPOSED BASELINE — approval pending |
| WP-2 §5–§7 | Job/attempt/lease and dispatch | DESIGN CANDIDATE — owner disposition OPEN |
| WP-3 §5–§13 | Worker identity, capability facts, credentials, assignment | DESIGN CANDIDATE — owner disposition OPEN |

### 3.3 Existing ownership distinction

The existing engineering-agent ownership is preserved: Qoder (Phase 11 engineering), OpenCode (Phase 10 engineering/closure), Kilo (independent read-only QA). These are **not** runtime content agents. No ownership change or execution authority is created by this report.

---

## 4. Proposed agent identity and versioning model

> Status: PROPOSED RECONCILIATION. These are logical fields and boundaries, not a frozen schema.

### 4.1 Agent identity

An agent is a bounded reasoning/transformation capability, not a model, provider, worker or workflow. The identity must be stable and independent of the model/provider used.

Proposed minimum fields (reconciling Contract 10 §4.1, Part 5 §3.1 and Canonical Pack §1):

| Field | Requirement |
|---|---|
| `agent_id` | Canonical immutable ID using the `agt_` prefix and the canonical ID system |
| `agent_name` | Human-readable display name; not identity |
| `agent_type` | Versioned category: planner, researcher, analyst, creator, reviewer, operator, monitor |
| `workspace_scope` | Permitted workspace references; no implicit global scope |
| `owner_ref` | Accountable owner or system authority |
| `lifecycle_status` | Agent lifecycle state (§4.3); not task/job/worker state |
| `created_at`, `updated_at`, `schema_version` | Common record envelope |
| `record_version` | Optimistic concurrency / revision token |

### 4.2 Agent version

An agent definition is immutable per version. A new model, prompt, tool profile, permission requirement, data ceiling, provider compatibility or contract version creates a new `AgentVersion`; it does not mutate the old one.

Proposed `AgentVersion` fields:

- `agent_version_id` and monotonic version number.
- Capability declarations (IDs and versions).
- Input/output contract versions.
- Tool profile reference and required tools.
- Compatible provider/model profiles.
- Required permission scopes and data-classification ceiling.
- Resource profile (task-class limits).
- Reliability and quality baselines.
- Evaluation evidence references and qualification status.
- Change rationale and approval reference.
- Prior version and rollback reference.
- Lifecycle/activation status.

Rules:

1. A new version does not inherit expanded permissions automatically.
2. A new version does not inherit qualification automatically.
3. A version is eligible for routing only when its qualification and approval are current.
4. Rollback is to a prior immutable version, never to an edited current version.
5. The exact model/deployment identifier and request configuration are retained for reproducibility where permitted.

### 4.3 Agent lifecycle reconciliation

Contract 10 proposes `PROPOSED → EVALUATED → APPROVED → ACTIVE → SUSPENDED / DEPRECATED → RETIRED`. Part 5 proposes qualification states `experimental`, `qualified`, `restricted`, `suspended`. WP-3 proposes a separate worker lifecycle.

These are **three different state machines** and must not be merged:

| Agent lifecycle (proposed) | Qualification status (Part 5) | Meaning |
|---|---|---|
| `PROPOSED` | `experimental` | Declared; not eligible for normal routing |
| `EVALUATED` | evaluation complete, qualification pending | Evidence exists; approval not granted |
| `APPROVED` | `qualified` or `restricted` | Approved for a scoped capability/version; restrictions recorded |
| `ACTIVE` | `qualified` and active | Eligible for routing within scope |
| `SUSPENDED` | `suspended` | No new tasks; existing tasks handled by policy |
| `DEPRECATED` | no new qualification | No new routing; drain existing work |
| `RETIRED` | terminal | Historical audit only |

Mapping is proposed; final names/transitions are OPEN. Agent lifecycle must not be conflated with WP-2 Job/JobAttempt state or WP-3 worker state (ADR-010).

### 4.4 Agent versus worker versus model/provider

| Concept | Owns | Must not be confused with |
|---|---|---|
| Agent | Bounded reasoning/transformation capability and version | Worker, model, provider, orchestrator |
| AgentVersion | Immutable definition of capability, contracts, tools, permissions, provider compatibility | Model version or deployment version |
| Worker | Execution endpoint that runs an assigned job under WP-3 trust | Agent identity |
| Model/Provider | External or local inference service and deployment | Agent identity or agent version |
| Agent Handler | Execution adapter that runs an agent task | Agent registry or policy engine |

An agent task may execute on a worker; the agent identity and worker identity remain distinct and both are bound to the task/attempt authorization.

---

## 5. Agent capability taxonomy — proposal

> Status: PROPOSED, not a frozen catalogue. Do not implement or route against an unapproved capability name.

### 5.1 Taxonomy shape

Use a two-level namespace: `<domain>.<verb>` with an explicit version and contract.

Proposed domains:

- `research` — discovery and synthesis.
- `evidence` — claim/evidence assessment.
- `strategy` — audience, angle, format and brief.
- `script` — narration and structure drafting.
- `editorial` — clarity, accuracy, originality and audience-fit review.
- `storyboard` — beats, shots and visual plan.
- `asset` — candidate discovery and relevance/rights evidence.
- `quality` — QA interpretation and defect analysis.
- `performance` — metric interpretation and experiment proposals.
- `operations` — bounded operational recommendations (not execution authority).

### 5.2 Mapping of existing logical roles

| Existing role (Part 5 §3.2) | Proposed capability ID | Typical output |
|---|---|---|
| Research Analyst | `research.synthesize` | Research brief with source records |
| Claim Reviewer | `evidence.assess` | Claim assessment and unresolved items |
| Strategy Planner | `strategy.plan` | Versioned content brief |
| Scriptwriter | `script.draft` | Script draft |
| Editorial Reviewer | `editorial.review` | Review findings and revision suggestions |
| Storyboard Planner | `storyboard.plan` | Storyboard and shot-plan proposal |
| Asset Researcher | `asset.discover` | Asset candidates with provenance |
| Quality Analyst | `quality.analyze` | QA analysis; not the authoritative gate decision |
| Performance Analyst | `performance.interpret` | Insights and experiment proposals |

The mapping is proposed; the IDs are not approved.

### 5.3 Capability descriptor

Each capability declaration should include:

- `capability_id` and `capability_version`.
- Supported `task_type` values.
- Required input schema and produced output schema versions.
- Supported languages, modalities and formats.
- Required tools and provider capabilities.
- Supported data classifications and purpose restrictions.
- Permission scopes required (ceiling, not grant).
- Resource profile and task-class limits.
- Quality expectations and evaluation evidence references.
- Known limitations and prohibited uses.
- Execution-location constraints (local/remote/either), if any.

### 5.4 Agent capabilities versus worker capabilities

WP-3 capability names such as `research.fetch`, `script.generate`, `shorts.render.local`, `artifact.upload` are **execution capabilities**. Agent capabilities describe reasoning/transformation tasks. They must not share one unversioned namespace by accident.

Proposed rule: every Agent Handler task declares its agent capability and its execution requirements; the router maps the agent capability to an eligible agent version and the execution requirements to an eligible worker capability. Neither mapping grants permission.

---

## 6. Declared, verified, available, authorized — and qualified

### 6.1 Five facts, not one field

CF-13/14 and WP-3 §6 require four facts to stay separate for workers. This report PROPOSES extending that separation to agents with five facts (adding task-specific eligibility):

| Fact | Agent meaning | Worker meaning | Authority |
|---|---|---|---|
| **Declared** | The AgentVersion claims the capability | Worker claims it can perform a class of work | Agent definition / worker registration |
| **Verified / qualified** | Independent evaluation evidence supports the capability for a contract/version | Control plane has evidence the worker can perform it | Evaluation service / WP-3 verification |
| **Available** | The agent version, provider/model and required runtime are currently usable | Worker is online, healthy, not busy | Runtime/availability service |
| **Eligible** | Data class, provider terms, region, rights, policy and tool constraints permit this task | Job requirements and scope permit this worker | Router / policy |
| **Authorized** | A task-scoped delegation grant permits this agent version to act on this task | Assignment authorization permits this worker for this job | WP-5 / WP-3 assignment |

“Qualified” is the agent-specific evaluation status. “Verified” is the worker-specific capability evidence. They must not be collapsed into a single `capabilities` array.

### 6.2 Non-collapse rules

1. A declaration is not proof.
2. A qualification is not a permanent endorsement; it is scoped to capability, contract version and agent version.
3. Availability is time-sensitive.
4. Eligibility is task-specific.
5. Authorization is task-scoped and revocable.
6. Any one failing fact makes the candidate ineligible; no score can compensate.
7. Capability declaration never grants permission.

---

## 7. Routing and qualification boundaries

### 7.1 Routing sequence

1. Parse the Task envelope: task type, objective, input refs, expected output schema, constraints, risk and data classification.
2. Resolve required agent capability IDs and versions.
3. Apply hard eligibility filters: workspace/brand scope, data classification, provider terms/residency, rights, security, permission ceiling, tool availability, qualification status.
4. Check current availability and capacity of agent version, provider/model and required worker.
5. Preflight resource reservation against the task-class envelope.
6. Optimize only among eligible candidates using task-specific quality, reliability, latency, cost and quota weights.
7. Select the candidate or route to queue/review.
8. Issue a task-scoped delegation/authorization grant.
9. Record a `RoutingDecision` with policy version, candidate set, filters, rationale and fallback chain.

### 7.2 Hard filters versus optimization

Hard filters (never traded for cost/latency): data protection, residency, rights, security, permission, provider approval, qualification, required tool/contract compatibility, workspace scope.

Optimization (only among eligible): quality history, reliability, latency, cost, quota remaining, reproducibility.

No single universal ranking score is required.

### 7.3 Model/provider eligibility and fallback

Provider eligibility must verify, before data is sent:

- Provider/product/model is approved for the purpose and data classification.
- Data-protection and training-use terms are verified and current.
- Retention, residency and security protections are acceptable.
- Required redaction/minimization has occurred.
- Credentials are scoped and valid.
- Resource use is within approved limits.

Fallback rules:

1. Fallback may use only already-approved agents, models, providers, tools and workers for the same task/data scope.
2. Fallback cannot downgrade data protection, rights, residency or permission.
3. Fallback is not a retry path around a policy, authorization or quality blocker.
4. Fallback chains and maximum attempts are bounded and recorded.
5. A provider/model change that alters the agent definition requires a new AgentVersion and requalification; whether a same-version provider substitution is allowed is OPEN.
6. Fallback events are audited and visible in the result provenance.

### 7.4 Qualification boundary

Qualification is capability- and version-specific:

- Contract tests: schema, required fields, reference integrity.
- Task evaluations: accuracy, completeness, relevance, instruction adherence.
- Evidence evaluations: source quality, claim-to-source linkage, uncertainty.
- Safety evaluations: permission boundaries, secret handling, prompt-injection resistance.
- Operational evaluations: latency, cost, timeout, retry behavior.
- Regression evaluations: known cases that must not degrade.

An agent cannot self-certify. Independent evaluation is required for consequential capabilities. Evaluation datasets, rubrics and thresholds are OPEN owner decisions.

---

## 8. Resource governance requirements

### 8.1 Dimensions

Track per agent version, capability, task class, workspace and provider:

- Tokens/usage units and API requests.
- Tool calls and external operations.
- CPU/GPU/memory/disk for local execution.
- Remote worker capacity and concurrency.
- Execution time and queue time.
- Storage and data transfer.
- Paid third-party services and platform fees.

### 8.2 Limits required before a pilot

| Limit | Scope | Status |
|---|---|---|
| Max input/output tokens or usage units | Per task and per agent version | Numeric values OPEN |
| Max execution time | Per task class | OPEN |
| Max tool calls / external calls | Per task | OPEN |
| Max retries and fallback attempts | Per task class | OPEN; bounded by WP-2 |
| Max concurrency | Per agent version and workspace | OPEN |
| Max cost per task / day / period | Per resource account | OPEN |
| Max artifact size | Per task output | OPEN |
| Hard-stop and pause behavior | Resource account | Required; numeric thresholds OPEN |

### 8.3 Rules

- Resource limits are authoritative; forecasts cannot increase budgets.
- Preflight reservations prevent concurrent oversubscription.
- Actual provider-reported usage is reconciled against estimates; differences remain visible.
- No autonomous path may increase a budget, buy credits, authorize a provider or spend money.
- A task that exceeds its envelope pauses or fails closed; it does not silently continue.
- Agent/task limits must not be conflated with WP-3 worker resource limits; both apply.

---

## 9. Agent permission profiles and tool-profile boundaries

### 9.1 Permission dimensions

Use separate dimensions (reconciling Part 5 §6.1 and Contract 10 §7.2):

| Dimension | Agent profile content |
|---|---|
| Read scope | Workspace entities, sources, artifacts the agent may read |
| Write scope | Draft artifacts/locations the agent may create or modify |
| Execution scope | Deterministic operations the agent may request |
| External access | Approved domains/APIs/accounts; default none |
| Approval scope | None for agents by default; agents may request review |
| Administrative scope | None for agents by default |
| Data-classification ceiling | Maximum data class the agent may receive |
| Provider scope | Approved providers/models for this capability |
| Resource ceiling | Task-class limits |

### 9.2 Tool profile

A tool profile should define:

- Tool ID and version; allowed operations.
- Input/output schema and side-effect class (read-only, draft-write, external side effect).
- Whether idempotency is required.
- Scoped credential/secret reference (never the secret itself).
- Network/domain allowlist.
- Rate/quota limits.
- Audit requirements.
- Explicitly prohibited operations.

### 9.3 Boundaries

- Capability and tool availability do not imply permission.
- Permissions are granted per task through a scoped delegation/authorization grant, not inherited from the agent runtime.
- Agents cannot grant themselves permissions, expand data scope, change their capability declaration, or approve their own output.
- High-risk operations (publishing, deletion, rights/privacy/safety policy, account connections, credentials, repository/infrastructure changes, spending) remain mediated by dedicated services and explicit policy.
- Secrets never appear in prompts, agent-visible logs, artifacts or error messages.
- Tool permission denial stops the task; the agent must not seek another route around the restriction.

---

## 10. Agent registry integration requirements

### 10.1 Registry role

The Agent Registry is authoritative platform configuration for agent identities, versions, capability declarations, qualification status, permission ceilings and lifecycle. An agent cannot edit its own registry record.

### 10.2 Proposed record composition

| Record | Key content |
|---|---|
| `AgentIdentity` | `agent_id`, name, type, workspace scope, owner, lifecycle, timestamps, schema version |
| `AgentVersion` | Immutable version, capability refs, contract versions, tool profile ref, provider compatibility, permission ceiling, data ceiling, resource profile, evaluation refs, approval ref, prior version, status |
| `AgentCapabilityDeclaration` | Capability ID/version, task types, input/output schemas, modalities, required tools/providers, data classes, permission scopes, limits, limitations |
| `AgentQualification` | Capability/version scope, evaluation run refs, result, evaluator, date, expiry/requalification trigger, status |
| `AgentPermissionProfile` | Read/write/execution/external/approval/admin scopes, data ceiling, tool profile, provider scope, resource ceiling |
| `AgentStatusHistory` | Lifecycle/qualification changes, actor, reason, policy version, timestamp |

### 10.3 Integration requirements

- Use canonical IDs (`agt_` prefix) and the common record envelope (workspace, schema version, record version, created/updated by).
- Persist through the approved shared store and WP-1 persistence boundary; do not create a private registry database.
- Reference exact versions, never “latest”.
- Record qualification evidence and approval as immutable references.
- Expose versioned registry APIs/events; event names are illustrative until approved (Contract 10 §15).
- Audit every identity, version, capability, qualification, permission and lifecycle change.
- Enforce server-side authorization for all registry mutations.
- Reconcile agent identity with worker identity at execution time; one does not replace the other.

### 10.4 Registry gaps

The Canonical Contracts Pack defines the `Agent` entity and `agt_` prefix but does not define a full Agent record, AgentVersion or qualification schema. Contract 10 defines the logical model but not a physical schema. This is an OPEN persistence/contract gap, not an invitation to invent one in this report.

---

## 11. Interfaces required from WP-2, WP-3 and WP-5

### 11.1 WP-2 — durable execution

| Required interface | Why the agent layer needs it |
|---|---|
| Task identity and envelope | `task_id`, `workflow_run_id`, `task_type`, `task_contract_version`, objective, input refs, expected output schema |
| Job/JobAttempt identity | Agent task execution must correlate to the durable job and attempt; retries create new attempts |
| Required capabilities and execution requirements | Router and worker assignment need declared needs, not inferred names |
| Lease/attempt identity | Result validation must reject stale or wrong-attempt results |
| Failure classification | Agent failures must map to `TRANSIENT`, `PERMANENT`, `POLICY_DENIED`, `CAPABILITY_UNAVAILABLE`, `WORKER_LOST`, `UNKNOWN_OUTCOME`, `CANCELLED` |
| Idempotency keys and retry policy | Agent retries must not duplicate side effects or results |
| Result/outcome envelope | Agent result must be validated and recorded by the orchestrator |

The agent layer does not own workflow state, lease semantics, retry policy or job transitions.

### 11.2 WP-3 — worker identity, trust and capability

| Required interface | Why the agent layer needs it |
|---|---|
| Worker identity and trust status | An agent execution is bound to an authenticated worker where execution occurs |
| Declared/verified/available/authorized worker capabilities | Mapping agent execution requirements to an eligible worker |
| Credential validity and scope | Ensure the worker is currently authorized; no agent bypass |
| Assignment/completion checks | Agent results must come from the valid lease holder and attempt |
| Local/remote parity rules | Agent execution may be local-only, remote or either |
| Revocation/suspension signals | Agent tasks must not continue on a revoked worker |
| Isolation/resource boundary | Agent tools and data access inherit the worker's bounded scope |

The agent layer does not own worker enrollment, credentials, trust, isolation or worker lifecycle.

### 11.3 WP-5 — policy and authorization

| Required interface | Why the agent layer needs it |
|---|---|
| Policy evaluation / decision | Hard eligibility and permission decisions before dispatch and before protected actions |
| Authorization grant | Task-scoped, time-bounded permission for agent/tool/provider actions |
| Approval/QA/rights gates | Agent output does not bypass governance; publishing remains separate |
| Emergency pause | Agent tasks and side effects must stop when paused |
| Denial reasons/codes | Routing and result envelopes must explain policy denial without retry bypass |
| Audit/event contract | Every grant, denial and protected action is attributable |

The agent layer does not grant permissions, approve its own output or publish.

### 11.4 Other dependencies

- **WP-1:** canonical IDs, workspace scope, persistence boundary and schema conventions.
- **WP-4:** artifact registration, exact-version references and scoped transfer for agent inputs/outputs.
- **WP-6:** future integrated acceptance; not a dependency for this design report.

---

## 12. Compatibility with OpenCode's Agent Handler and task/result contracts

### 12.1 Interface status

OpenCode's current reconciliation report and Agent Handler contract are **NOT MOUNTED** in the reviewed workspace. The compatibility statements below are therefore interface assumptions, not confirmed agreements. They must be validated with Track A before any freeze.

### 12.2 Assumed request contract

The Agent Handler is assumed to receive a bounded task request containing at least:

- `task_id`, `workspace_id`, `workflow_run_id`, `task_type`, `task_contract_version`.
- `agent_id` and exact `agent_version_id` (or a capability ID from which the router selects an approved version — OPEN).
- `input_refs` with exact versions.
- `expected_output_schema`, constraints, deadline.
- `required_capabilities`, `allowed_tools`, permission/data-scope references.
- `resource_policy`/limits.
- `idempotency_key`, `correlation_id`.
- Delegation/authorization grant reference.

### 12.3 Assumed result contract

The Agent Handler is assumed to return:

- `task_id`, `agent_id`, `agent_version_id`, `contract_version`.
- Outcome in the accepted task/result vocabulary: `completed`, `needs_input`, `needs_human_review`, `failed_retryable`, `failed_terminal`, `cancelled` (Part 5), or the Canonical Pack job-result vocabulary where a worker job is involved. The authoritative mapping is OPEN.
- `result`/`output_refs` to exact artifact versions.
- `evidence_refs`, `warnings`, `limitations`.
- Provider/model/deployment identity and request configuration reference.
- Usage/resource records and cost attribution reference.
- Error/failure classification and bounded redacted summary.
- `correlation_id` and provenance.

### 12.4 Field compatibility map

| Concern | Canonical Pack / Part 5 | WP-2 / WP-3 | Assumption for Agent Handler |
|---|---|---|---|
| Logical work | `tsk_` Task | WorkflowTask; Job derived | Handler receives a Task execution request, not raw workflow state |
| Execution | `job_` / `jat_` | Job and JobAttempt | Handler result references job/attempt where execution is a job |
| Agent | `agt_` Agent; Part 5 `agent_id` | Worker `wrk_` separate | Handler binds agent version to worker/attempt without merging identities |
| Capability | Task `required_capabilities` | Worker capability facts | Router resolves agent capability; WP-3 verifies worker capability |
| Permission | Authorization Grant `azg_` | WP-3 assignment authorization; WP-5 policy | Handler checks task-scoped grant; never self-grants |
| Result | Part 5 output envelope; Canonical Pack job result | WP-2 attempt result | One authoritative mapping must be agreed; no dual truth |
| Failure | Part 5 outcomes; WP-2 classes | WP-2 retry classification | Handler maps agent errors to WP-2 classes and does not retry policy denials |

### 12.5 Agent Handler assumptions requiring Track A confirmation

| ID | Assumption | Why it matters | If wrong |
|---|---|---|---|
| A-01 | Agent Handler accepts a Task envelope rather than only a Job envelope | Determines identity/correlation and retry semantics | Task/result mapping must be redesigned |
| A-02 | The router selects the approved AgentVersion; the Handler executes it | Prevents Handler from choosing an unqualified version | Capability/qualification boundary moves |
| A-03 | Capability IDs and versions are owned by the agent registry, not the Handler | Prevents divergent catalogues | Duplicate capability namespaces |
| A-04 | The Handler returns the Part 5 result envelope, with job-result mapping where applicable | Prevents dual result truth | Result validation ambiguity |
| A-05 | Agent registry persistence is a shared WP-1-boundary store, not Handler-local | Prevents a private source of truth | Registry cannot be authoritative |
| A-06 | Agent execution always occurs on a WP-3 worker or an equivalent trusted execution boundary | Determines identity/credential/isolation inheritance | Agent execution bypasses worker trust |
| A-07 | Tool-profile enforcement is server-side, not solely Handler-side | Prevents a compromised Handler from expanding tools | Permission bypass |
| A-08 | Provider/model selection is a router/policy decision; the Handler does not silently switch providers | Prevents unapproved data transfer and reproducibility loss | Provider eligibility bypass |
| A-09 | Resource usage is reported in the shared usage-record shape | Enables quota/cost reconciliation | Unaccounted spend/usage |
| A-10 | Qualification/evaluation hooks are exposed by the Handler | Enables regression and independent evaluation | Agent cannot be qualified reliably |
| A-11 | Worker capability and agent capability are separate namespaces with an explicit mapping | Prevents category errors | Routing/assignment mismatch |
| A-12 | The Agent Handler reconciliation report is the interface authority; this report does not freeze it | Preserves Track A ownership | Parallel divergence |

---

## 13. Conflicts and assumptions requiring Track A confirmation

### 13.1 Document-level conflicts

| ID | Conflict | Current position | Required resolution |
|---|---|---|---|
| C-01 | Agent vs Worker identity | Contract 10/Part 5/Canonical Pack distinguish them; WP-3 defines only workers | Confirm the execution binding and which identity owns which fields |
| C-02 | Agent capability vs worker capability | Part 5 uses reasoning capabilities; WP-3 uses execution capabilities | Confirm namespace/mapping ownership |
| C-03 | Task vs Job vs Attempt | Canonical Pack/Part 5 Task; WP-2 Job/Attempt | Confirm Agent Handler input and result correlation |
| C-04 | Result envelope | Part 5 output envelope vs Canonical Pack job result | Confirm one authoritative mapping |
| C-05 | Lifecycle states | Contract 10 agent lifecycle, Part 5 qualification states, WP-3 worker lifecycle | Keep separate; confirm cross-mapping |
| C-06 | Permission authority | Agent profile (Part 5), Authorization Grant (Canonical Pack/WP-5), WP-3 assignment authorization | Confirm order and precedence |
| C-07 | Qualification authority | Contract 10/Part 5 propose evaluation; no accepted authority | Owner decision |
| C-08 | Registry persistence | Contract 10 logical registry; Canonical Pack lacks Agent schema; WP-1 boundary | Confirm WP-1 schema ownership |
| C-09 | Provider fallback and versioning | Contract 10 allows preapproved fallback; no rule on whether provider change creates a new AgentVersion | Owner/Track A decision |
| C-10 | Numeric limits | Contract 10/WP-2/WP-3 defer values | Owner decision; do not invent |

### 13.2 Coordination assumptions

- Track A owns WP-2/WP-3 execution interfaces and the Agent Handler; this report does not modify them.
- Track A's Agent Handler reconciliation report is authoritative for the Handler contract; if it differs from §12, Track A wins and this report must be revised.
- The agent registry is not assumed to be implemented in WP-2/WP-3; it is a separate logical service unless Track A/owner places it within WP-1 or WP-5.
- No owner approval is inferred from the existence of Contract 10, Part 5, the Canonical Pack, WP-2/WP-3 or this report.

---

## 14. Owner decisions still required

| ID | Decision | Why it cannot be inferred |
|---|---|---|
| O-01 | Final agent capability taxonomy and versioning | Contract 10/Part 5 propose; no accepted catalogue |
| O-02 | Agent registry schema, ownership and persistence boundary | Canonical Pack lacks full Agent record; WP-1 boundary open |
| O-03 | Final agent lifecycle and qualification states/transitions | Contract 10 and Part 5 use different vocabularies |
| O-04 | Qualification thresholds, evaluator independence, requalification triggers and expiry | Part 5 explicitly leaves thresholds open |
| O-05 | Initial agent roles, number of runtimes, local/remote placement | Part 5 §14 open decisions |
| O-06 | Approved model/provider allowlist and fallback chains | No provider/model is selected or authorized |
| O-07 | Numeric resource, quota, cost and task limits | Contract 10/WP-2/WP-3 defer values |
| O-08 | Permission-profile and tool-profile catalogue | Part 5 gives examples, not an approved catalogue |
| O-09 | Autonomy level and human-review thresholds | Part 5 §14; owner decision |
| O-10 | Data-classification ceiling per capability/workspace | Security/privacy decision |
| O-11 | Whether agent tasks are executed only as WP-2 jobs on WP-3 workers, or via a separate trusted execution boundary | C-01/C-03/C-06 |
| O-12 | Retention of prompts, traces, context snapshots and evaluation evidence | Part 5 §14; privacy/storage decision |
| O-13 | Freeze of the Agent Handler contract and this agent model | Track A + owner freeze gate |

No owner approval is created by listing these decisions.

---

## 15. Acceptance criteria for a future implementation pilot

> These are design acceptance targets for a later, separately authorized pilot. They are not executed tests and do not authorize implementation.

### 15.1 Pilot scope

One bounded capability (for example `research.synthesize` or `script.draft`), one approved AgentVersion, one dry-run execution path, no external side effects, no paid provider, no production publishing.

### 15.2 Positive criteria

1. The AgentVersion is registered with canonical `agent_id`/version, capability declaration, contract versions, tool profile, provider compatibility, data ceiling, permission ceiling and resource profile.
2. Independent qualification evidence exists for the capability and version; the agent is not self-certified.
3. A Task envelope with exact input refs is validated and routed only to an agent version that is qualified, available, eligible and authorized.
4. The selected provider/model is approved for the task data class; routing rationale and policy version are recorded.
5. A task-scoped delegation/authorization grant is issued; tool profile and resource preflight are enforced.
6. The result envelope validates against the expected schema; output/evidence refs are exact-version; warnings/limitations are preserved.
7. Usage is recorded and reconciled; audit answers why this agent/provider/worker was selected, what it accessed, what it consumed and what it produced.
8. A malformed result, missing input version or unsupported contract version is rejected without advancing the workflow.

### 15.3 Negative criteria

| ID | Scenario | Required result |
|---|---|---|
| P-01 | Agent declares a capability but has no qualification evidence | Not routable |
| P-02 | Agent version is suspended/deprecated/retired | Not assigned |
| P-03 | Provider/model is not approved for the data class | Task blocked before data transfer |
| P-04 | Delegation grant is expired, revoked or out of scope | Task denied |
| P-05 | Agent requests a tool outside its tool profile | Denied and audited |
| P-06 | Agent attempts to expand its capability, permission or data scope | Denied |
| P-07 | Agent attempts to approve its own output or advance workflow state | Denied |
| P-08 | Resource envelope would be exceeded | Task pauses/fails closed; no overspend |
| P-09 | Fallback targets an unapproved provider/agent | Fallback denied |
| P-10 | Policy/authorization denial | No retry path bypasses the denial |
| P-11 | Worker identity/lease is stale or revoked | Result rejected/quarantined |
| P-12 | Duplicate task/result delivery | One logical effect; idempotency preserved |
| P-13 | Secret appears in prompt/log/result | Redaction test fails |
| P-14 | Agent execution occurs without a valid WP-3 worker or accepted equivalent boundary | Denied |
| P-15 | Agent Handler report/contract differs from this report | Track A interface wins; pilot blocked until reconciled |

### 15.4 Evidence required

- Registered agent/version/capability records.
- Qualification/evaluation report with dataset and rubric versions.
- RoutingDecision and policy/authorization references.
- Task/result envelopes and validation results.
- Usage/audit records with redaction evidence.
- Negative-test evidence for P-01–P-15.
- Confirmation that no production side effect, credential, spending, publishing or integration occurred.

---

## 16. Status

**OWNER REVIEW REQUIRED**

The agent-intelligence model is not accepted architecture: Contract 10 is a working contract, Part 5 is a proposal, the Canonical Pack is a proposed baseline, and the WP-2/WP-3 owner dispositions are OPEN. The OpenCode Agent Handler reconciliation report is not mounted, so the interface assumptions in §12 and §13 require Track A confirmation. Several owner decisions in §14 cannot be inferred.

Cross-track review can proceed on this report, but no implementation, pilot, freeze or interface commitment should begin until Track A confirms the Handler contract and the owner resolves the decisions above.
