# NEXTDECODE Content OS
## Part 5 — Agent Contracts & Orchestration
**Version:** 1.0  
**Status:** Architecture proposal — not implementation approval  
**Date:** 31 October 2026

---

## 1. Purpose

This document defines how agents participate in NEXTDECODE Content OS without turning the platform into an uncontrolled collection of autonomous bots.

The governing principle is:

> The orchestrator owns workflow state and policy enforcement. Agents perform bounded tasks. Tools enforce permissions. Humans retain control over critical decisions.

This part builds on the shared Content Graph and persistent job architecture described in Parts 3 and 4. It defines role boundaries, task contracts, handoffs, permissions, context handling, evaluation, and failure recovery.

This is a proposed future architecture. It does not describe a fully implemented agent system.

### 1.1 Design goals

- Make every agent's responsibility explicit and narrow.
- Use structured inputs and outputs rather than informal agent-to-agent chat.
- Keep workflow state, retries, scheduling, and authorization outside individual agents.
- Apply least-privilege tool access.
- Preserve evidence, provenance, and version history.
- Make work resumable after failures or long periods of user unavailability.
- Require human authorization for policy changes and other critical actions.
- Keep providers and model vendors replaceable where practical.

### 1.2 Non-goals

- Creating a large autonomous agent fleet at the start.
- Giving agents unrestricted shell, repository, browser, account, or publishing access.
- Allowing an agent to approve its own work or bypass a failed gate.
- Replacing deterministic code with an LLM when ordinary software is more reliable.
- Making every agent continuously active.

---

## 2. Architectural responsibility boundaries

The platform separates five kinds of responsibility.

| Component | Owns | Must not own |
|---|---|---|
| Orchestrator | Workflow state, task dispatch, dependencies, retries, timeouts, handoffs | Creative truth, unrestricted policy changes |
| Agent | A bounded reasoning or transformation task | Global workflow state, permission escalation |
| Tool/service | A specific operation with validated inputs and permissions | Deciding whether the overall workflow is authorized |
| Policy and gate services | Deterministic validation and authorization decisions | Creative generation |
| Human owner | Critical approvals, policy changes, exceptions, emergency controls | Routine mechanical execution |

### 2.1 Orchestrator versus agent

The orchestrator is ordinary application logic, not another unconstrained agent. It:

1. Loads the workflow and its current version.
2. Determines which task is eligible to run.
3. Checks prerequisites and policy.
4. Selects an eligible agent capability.
5. Issues a scoped task envelope.
6. Validates the returned result against the contract.
7. Persists the result and provenance.
8. Advances, pauses, retries, or blocks the workflow.

An agent may recommend the next action, but it cannot directly advance the authoritative workflow state.

### 2.2 Deterministic services versus agents

Use deterministic services for:
- schema validation and ID generation;
- permission checks and policy evaluation;
- rights and safety gates;
- file hashing and artifact integrity;
- scheduling, leases, retries, and idempotency;
- rendering, transcoding, upload mechanics, and status polling;
- database writes and audit-event creation.

Use agents where judgment or language understanding adds value:
- research synthesis and source comparison;
- content strategy suggestions;
- script drafting and editorial critique;
- storyboard and shot-plan proposals;
- asset discovery and relevance assessment;
- performance interpretation and experiment suggestions.

An agent may request a deterministic operation. The service independently validates and executes it.

---

## 3. Agent capability model

An agent is registered by capability, not merely by a friendly name or model.

### 3.1 Capability registry

A proposed registry record includes:

| Field | Meaning |
|---|---|
| `agent_id` | Stable platform identity |
| `display_name` | Human-readable name |
| `capabilities` | Supported task types |
| `contract_versions` | Input/output schemas supported |
| `provider` | Model/runtime provider, if applicable |
| `model_profile` | Approved model configuration identifier |
| `tool_profile` | Allowlisted tool set |
| `data_access_profile` | Permitted data scope |
| `execution_location` | Cloud, local, or either |
| `status` | Available, paused, disabled, or unhealthy |
| `limits` | Runtime, token, concurrency, and cost limits |
| `evaluation_status` | Current qualification state |

The registry is authoritative platform configuration. An agent cannot edit its own permissions, capability declaration, or qualification status.

### 3.2 Initial logical agent roles

These are logical roles, not a requirement to deploy a separate model or process for each one. Early versions may combine several roles behind one runtime while keeping contracts separate.

| Role | Primary responsibility | Typical output |
|---|---|---|
| Research Analyst | Gather and synthesize evidence from permitted sources | Research brief with source records |
| Claim Reviewer | Assess factual claims and evidence coverage | Claim assessment and unresolved items |
| Strategy Planner | Propose audience, angle, format, and content brief | Versioned content brief |
| Scriptwriter | Draft narration and structure from an approved brief | Script draft |
| Editorial Reviewer | Assess clarity, accuracy, originality, and audience fit | Review findings and revision suggestions |
| Storyboard Planner | Convert approved script into beats and proposed shots | Storyboard and shot-plan proposal |
| Asset Researcher | Find candidate assets and assess relevance and rights evidence | Asset candidates with provenance |
| Quality Analyst | Interpret QA results and identify defects | QA analysis; not the authoritative gate decision |
| Performance Analyst | Interpret linked performance data | Insights and experiment proposals |

### 3.3 Do not create an agent for every stage

Start with the smallest useful set of capabilities. A single agent runtime may perform Research Analyst and Strategy Planner tasks if it has distinct contracts and scoped permissions. Separate them later only when quality, security, cost, or operational isolation justifies it.

---

## 4. Standard task contract

Every agent invocation must use a versioned task envelope. The orchestrator creates the envelope and records it before dispatch.

### 4.1 Input envelope

Illustrative schema (conceptual, not a finalized API):

```json
{
  "task_id": "task_<stable-id>",
  "workflow_id": "workflow_<stable-id>",
  "content_id": "content_<stable-id>",
  "task_type": "research.synthesize",
  "contract_version": "1.0",
  "attempt": 1,
  "issued_at": "ISO-8601 timestamp",
  "deadline_at": "ISO-8601 timestamp",
  "input_refs": [
    {
      "entity_id": "entity_<stable-id>",
      "version": 3,
      "role": "approved_brief"
    }
  ],
  "constraints": {
    "language": "en",
    "brand_profile_version": "brand_v1",
    "max_output_tokens": 5000
  },
  "allowed_tools": ["source_search", "document_read"],
  "output_schema": "research_brief.v1"
}
```

The envelope should contain references to versioned records and artifacts rather than copying large documents into every task. Sensitive or bulky content should be fetched through scoped services.

### 4.2 Output envelope

```json
{
  "task_id": "task_<stable-id>",
  "agent_id": "agent_research",
  "contract_version": "1.0",
  "status": "completed",
  "result": {
    "artifact_ref": "artifact_<stable-id>",
    "summary": "Concise result summary"
  },
  "evidence_refs": ["source_<stable-id>"],
  "warnings": [],
  "limitations": [],
  "created_at": "ISO-8601 timestamp"
}
```

Allowed task outcomes should include:
- `completed` — valid result returned;
- `needs_input` — a required input or clarification is missing;
- `needs_human_review` — judgment or authorization is required;
- `failed_retryable` — transient failure may be retried;
- `failed_terminal` — invalid or unrecoverable task;
- `cancelled` — cancelled by the orchestrator or authorized user.

An agent's self-reported status is not sufficient. The orchestrator validates the envelope, schema, referenced artifacts, and task state before accepting it.

### 4.3 Contract requirements

Each contract must specify:
- purpose and explicit non-goals;
- required and optional inputs;
- accepted input versions;
- output schema and required fields;
- evidence and provenance requirements;
- allowed tools and data scope;
- quality checks and evaluation cases;
- timeout and retry classification;
- escalation conditions;
- idempotency expectations;
- version and compatibility policy.

A schema-valid response is not automatically a correct or approved response.

---

## 5. Handoffs and workflow orchestration

### 5.1 Handoff protocol

Agents do not directly invoke other agents. They return a result or a handoff recommendation to the orchestrator.

A handoff record should include:

- originating task and agent;
- proposed next task type;
- reason for the handoff;
- exact input artifact references and versions;
- unresolved questions or warnings;
- whether the handoff is mandatory or optional.

The orchestrator checks workflow dependencies, policy, task limits, and available capability before creating the next task.

### 5.2 Example research-to-production flow

```text
User request
    |
    v
Orchestrator creates workflow and brief task
    |
    v
Research Analyst
    |
    v
Evidence validation service
    |
    v
Claim Reviewer
    |
    v
Strategy Planner
    |
    v
Human review where required
    |
    v
Scriptwriter
    |
    v
Editorial Reviewer
    |
    v
Storyboard Planner
    |
    v
Shorts Studio production workflow
```

This is an illustrative dependency flow. Exact gates and mandatory review points are governed by the relevant workflow and policy versions.

### 5.3 Handoff invariants

- Every handoff references immutable, versioned inputs.
- A downstream task cannot silently consume a newer version than the one specified.
- A failed or blocked prerequisite prevents dependent tasks from starting.
- Re-running an upstream task creates a new version and triggers explicit downstream invalidation or revalidation.
- Agents cannot mark another agent's task complete.
- Cyclic handoffs are rejected unless a bounded revision loop is explicitly defined.
- Every loop has a maximum iteration policy and a clear exit condition.

### 5.4 Revision loops

Revision loops are useful for script and editorial work, but they must be bounded.

A revision cycle should record:
1. the artifact version reviewed;
2. structured findings;
3. the requested changes;
4. the revised artifact version;
5. whether previous findings were resolved.

The orchestrator enforces the loop limit. If the limit is reached, the workflow pauses for human decision rather than cycling indefinitely.

---

## 6. Tool permissions and least privilege

### 6.1 Permission model

Permissions should be granted to a task through an approved tool profile, not inherited as broad ambient access from the agent runtime.

Use separate permission dimensions:

- **Read scope:** which workspace entities, sources, and artifacts can be read.
- **Write scope:** which draft entities or artifact locations can be created or updated.
- **Execution scope:** which deterministic operations can be requested.
- **External access:** which domains, APIs, or connected accounts are available.
- **Approval scope:** normally none for agents.
- **Administrative scope:** none for agents by default.

### 6.2 Example permission profiles

| Profile | Permitted | Explicitly excluded |
|---|---|---|
| Research read-only | Search approved sources; read supplied documents | Publishing, account settings, arbitrary local files |
| Draft writer | Create draft artifacts in assigned workspace | Editing approved policy, publishing |
| Review read-only | Read specified versions; emit review findings | Altering the reviewed artifact |
| Asset discovery | Search approved asset sources; record candidates | Declaring legal rights without evidence |
| Production request | Submit validated production jobs | Arbitrary shell or unrestricted filesystem |
| Analytics read-only | Read authorized metrics and linked content | Changing platform accounts or publishing |

### 6.3 High-risk operations

The following operations must be mediated by dedicated services and explicit policy:
- public publishing or distribution;
- deletion or destructive replacement of assets;
- changing rights, privacy, or safety policy;
- connecting or disconnecting external accounts;
- changing credentials or secrets;
- modifying agent permissions or model profiles;
- repository or infrastructure changes;
- spending money or enabling paid services.

Agents may prepare recommendations or requests for these actions. They do not authorize them.

### 6.4 Secret handling

- Never place API keys, OAuth tokens, passwords, or private credentials in prompts, agent-visible logs, or generated artifacts.
- Tools obtain credentials through a secret-management boundary.
- Return only the minimum operation result needed by the task.
- Redact sensitive values from traces and error messages.
- Use short-lived scoped credentials where supported.
- Record access events without recording secret values.

---

## 7. Human review and escalation

Human review is a workflow state, not a conversational suggestion that can be ignored.

### 7.1 Escalation triggers

An agent or deterministic validator may request human review when:
- source evidence is conflicting or insufficient;
- a factual claim cannot be supported;
- rights or asset provenance is unclear;
- the output materially departs from brand constraints;
- a policy exception is requested;
- confidence or evaluation falls below a defined threshold;
- the task requires an irreversible or externally visible action;
- the agent detects ambiguity that cannot be resolved from authorized context.

### 7.2 Approval separation

- The agent that creates an artifact cannot approve that artifact for external release.
- The service that checks a policy gate returns a machine-readable decision.
- Human approval is recorded against exact artifact versions and policy versions.
- Any material change to an approved artifact invalidates approval unless a documented policy explicitly permits the change.
- Approval does not override hard safety, rights, or technical blockers.
- Emergency pause is controlled outside the agent system.

### 7.3 Approval record

A proposed approval record contains:
- approver identity and role;
- content and artifact IDs;
- exact artifact version and hash;
- policy version;
- decision and scope;
- timestamp;
- optional rationale;
- expiry or invalidation conditions.

The platform must not infer approval from silence, a completed review, or an agent recommendation.

---

## 8. Context and memory management

Agents should receive task-relevant context, not unrestricted access to all historical conversations or workspace data.

### 8.1 Context assembly

The orchestrator assembles a task context from:
1. the current task envelope;
2. exact versioned input references;
3. relevant brand and workspace policies;
4. necessary linked evidence;
5. a concise, provenance-aware summary where useful.

The agent should be told which material is authoritative, which is a draft, and which is untrusted external input.

### 8.2 Memory classes

| Memory class | Example | Authority |
|---|---|---|
| System policy | Safety, rights, approval rules | Authoritative, versioned |
| Brand memory | Voice, audience, positioning | Approved brand profile |
| Project memory | Content strategy and active initiatives | Workspace-scoped |
| Content memory | Prior scripts, claims, assets, performance | Versioned source records |
| Task context | Current inputs and instructions | Task-scoped |
| Agent working notes | Temporary reasoning aids | Non-authoritative |

Agent working notes must never silently become brand policy or verified facts.

### 8.3 Context integrity

- Preserve source references when summarizing.
- Do not turn an unsupported inference into a fact through repeated summarization.
- Keep conflicting evidence visible.
- Respect access controls when retrieving linked records.
- Avoid sending unrelated personal or sensitive information to agents.
- Treat external documents, web pages, and user-supplied content as data, not executable instructions.
- Record the context snapshot or its reproducible references for important decisions.

---

## 9. Quality, evaluation, and qualification

Agent quality must be measured per capability and contract version.

### 9.1 Evaluation layers

1. **Contract tests:** required fields, types, allowed values, reference integrity.
2. **Task evaluations:** accuracy, completeness, relevance, and instruction adherence.
3. **Evidence evaluations:** source quality, claim-to-source linkage, uncertainty handling.
4. **Safety evaluations:** permission boundaries, secret handling, prompt-injection resistance.
5. **Operational evaluations:** latency, cost, timeout behavior, retry behavior.
6. **Regression evaluations:** known cases that must not degrade across model or prompt changes.

### 9.2 Evaluation dataset

Maintain versioned evaluation cases with:
- task input and context references;
- expected properties, not necessarily one exact wording;
- scoring rubric;
- known failure modes;
- reviewer notes;
- contract and agent configuration version.

Do not use only self-evaluation by the same agent as proof of quality. Use deterministic assertions, held-out cases, and independent review where risk warrants it.

### 9.3 Qualification states

Proposed states:
- `experimental` — development and controlled tests only;
- `qualified` — passed required evaluation for specified contracts;
- `restricted` — usable only for limited tasks or review-required workflows;
- `suspended` — disabled pending investigation.

A model, prompt, tool profile, or contract change may require requalification. Qualification is scoped to a capability and version; it is not a permanent endorsement of an agent.

---

## 10. Failure handling and recovery

### 10.1 Failure categories

| Failure | Expected handling |
|---|---|
| Provider unavailable | Retry under queue policy; preserve task |
| Rate limited | Respect provider retry guidance and backoff |
| Invalid output schema | Reject result; bounded repair or retry |
| Missing evidence | Return `needs_input` or `needs_human_review` |
| Tool permission denied | Stop; do not seek another route around the restriction |
| Context reference unavailable | Pause or fail with explicit missing dependency |
| Deadline exceeded | Mark attempt timed out; apply workflow retry policy |
| Repeated low-quality output | Stop retrying; escalate |
| Conflicting versions | Reject stale result and request revalidation |
| Suspected prompt injection | Treat as untrusted input; isolate and escalate if needed |

### 10.2 Retry rules

- Retry only failures classified as retryable.
- Use the persistent queue's retry and backoff policy.
- Preserve every attempt and its diagnostic record.
- Do not create duplicate external side effects on retry.
- Use idempotency keys for tool operations that may be repeated.
- Do not let an agent choose unlimited retries.
- Route exhausted tasks to a dead-letter or manual recovery state.

### 10.3 Partial completion

If an agent produces a valid partial result, the contract may allow it to be saved as a draft with explicit completeness metadata. A partial result must not be mislabeled as complete or silently passed through a gate requiring full coverage.

### 10.4 Cancellation

The orchestrator must support cancellation of queued and running tasks where technically possible. Cancellation does not erase prior artifacts or audit history. For an operation that cannot be safely interrupted, the platform records the operation's actual outcome and prevents duplicate execution.

---

## 11. Auditability and observability

For each task, preserve:
- task and workflow IDs;
- agent and capability identity;
- contract, prompt/configuration, and model profile versions;
- input references and versions;
- tool calls and authorization decisions;
- output artifact references and hashes;
- validation and evaluation results;
- retries, timestamps, duration, and cost where available;
- escalation and human decisions;
- final task outcome.

Logs should be useful for debugging without retaining secrets or unnecessary personal data. Observability records must distinguish agent statements from verified service results.

---

## 12. Existing engineering-agent ownership — unchanged

The current project ownership arrangement is preserved. This section records existing responsibilities; it does not create a new assignment or authorize repository work.

| Existing agent | Existing responsibility | Boundary |
|---|---|---|
| Qoder | Phase 11 engineering owner | Existing Phase 11 scope only |
| OpenCode | Phase 10 engineering and closure owner | Existing Phase 10 scope only |
| Kilo | Independent read-only QA | No source, test, configuration, or Git modifications |

These existing project agents are not automatically the same thing as future runtime content agents defined in Section 3.

No ownership change, new assignment, repository inspection, Git operation, code modification, dependency installation, or execution is authorized by this architecture document. Any such work requires separate explicit authorization.

---

## 13. Implementation sequence

A staged approach avoids building an elaborate agent platform before the shared data and queue foundations exist.

### Stage A — Contract foundation
- Define a small contract registry.
- Define task and result envelopes.
- Validate inputs and outputs with deterministic schemas.
- Store task, attempt, and artifact references in the shared data model.
- Start with one or two bounded capabilities.

### Stage B — Orchestrated execution
- Dispatch tasks through the persistent queue.
- Enforce timeouts, retries, and idempotency.
- Persist handoffs and dependency state.
- Add cancellation and manual recovery.

### Stage C — Governance
- Add tool profiles and scoped data access.
- Centralize human review and policy gates.
- Add audit events and context snapshots.
- Test prompt-injection and permission-boundary cases.

### Stage D — Qualification and expansion
- Add evaluation datasets and regression runs.
- Qualify capabilities by contract version.
- Expand to more studios only when justified by measured value.
- Reassess local versus cloud execution based on capability and data requirements.

This sequence is a proposal and must be reconciled with the actual system before implementation.

---

## 14. Open decisions

The following decisions are intentionally not fabricated or prematurely locked:

1. Initial model/provider selection for each capability.
2. Whether the first runtime combines several logical roles.
3. Exact task timeout, retry, token, and cost limits.
4. Exact evaluation thresholds and qualification criteria.
5. Whether any agent capability should run locally, remotely, or both.
6. Which external research and asset providers are approved.
7. Retention periods for prompts, traces, and context snapshots.
8. Which content decisions require mandatory human review beyond hard safety and rights gates.

These should be decided using measured quality, cost, security, and operational evidence.

---

## 15. Acceptance criteria

Part 5 is ready to guide foundation implementation when:

- [ ] Agent and orchestrator responsibilities are separated.
- [ ] Every task type has a versioned input and output contract.
- [ ] Handoffs are mediated by the orchestrator.
- [ ] Tool access is allowlisted and scoped per task.
- [ ] Agents cannot grant themselves permissions or approve their own outputs.
- [ ] Critical actions require the relevant policy and human authorization.
- [ ] Context references preserve provenance and version identity.
- [ ] Retries, timeouts, cancellation, and partial results have defined behavior.
- [ ] Evaluation and qualification are capability- and version-specific.
- [ ] Audit records capture decisions without exposing secrets.
- [ ] Existing Qoder, OpenCode, and Kilo ownership remains unchanged.
- [ ] No repository or production work is inferred from this document.

---

## 16. Relationship to the other architecture parts

| Part | Relationship |
|---|---|
| Part 1 — System Architecture Master Reference | Defines the overall Content OS and studio architecture |
| Part 2 — Shorts Studio Pipeline Contract | Defines the production pipeline boundary that agents may support |
| Part 3 — Shared Data Model & Content Graph | Provides the entities, versions, and artifact references used in task contracts |
| Part 4 — Persistent Job Queue, Scheduler & Worker Architecture | Executes and recovers agent tasks durably |
| Part 5 — Agent Contracts & Orchestration | Defines bounded agent behavior, permissions, handoffs, and evaluation |

**Next architecture document:** Part 6 — Centralized Quality, Rights, Approval & Publishing Governance.

---

**Document status:** Proposed architecture baseline. No implementation, deployment, agent reassignment, repository access, Git operation, or publishing authorization is granted by this document.
