# NEXTDECODE — Agent–Worker Contract Closure
## Engineering Documentation Handoff

**Handoff ID:** ND-P0-AGW-001  
**Prepared:** 2 November 2026  
**Status:** Proposed engineering handoff — owner freeze pending  
**Scope:** Documentation reconciliation only  
**Implementation authorization:** NOT GRANTED

---

## 1. Purpose

Close the existing documentation gaps between Agent & Resource Orchestration, durable job execution, worker trust, and the API/event contract.

This is a bounded handoff for the engineering/documentation agent. It is not a new architecture standard and must not replace the existing source documents.

**Primary instruction:** Reconcile and prepare the existing Batch 18 API & Event Schema Specification Pack for owner review. Do not create a parallel API standard or silently freeze open decisions.

## 2. Source documents

Verify the exact current file, version, status and sections before making any edits. If a newer version exists, report the discrepancy and use the current canonical source.

| Source | Identified version/status | Responsibility |
|---|---|---|
| `NEXTDECODE_P0_Batch18_API_Event_Schema_Specification_Pack.docx` | Detailed interface candidate; owner freeze pending; implementation not authorized | Primary target |
| `NEXTDECODE_P0_WP2_Durable_Job_Workflow_Execution_0.1.md` | Design candidate; owner review required; implementation not authorized | Job, attempt, lease, idempotency, retry and recovery |
| `NEXTDECODE_P0_WP3_Worker_Registry_Contract_Boundary_0.1.md` | v0.1; design candidate; owner review required; implementation not authorized | Worker identity, trust, capabilities and assignment boundary |
| `NEXTDECODE_System_Architecture_Pipeline_Part_5_Agent_Contracts_Orchestration_1.0.md` | Proposed architecture baseline | Agent task/output envelopes, outcomes and orchestrator responsibility |
| `NEXTDECODE_Shared_Intelligence_Core_Contract_10_Agent_Intelligence_Resource_Management_Orchestration_1.0.md` | Architecture contract | Agent identity/version/capability and orchestration ownership |
| `NEXTDECODE_Canonical_Data_Dictionary_Entity_Ownership_Registry_1.0.md` | v1.0; working architecture standard | Canonical entity identity and ownership |
| `NEXTDECODE_API_Event_Contract_Standard_1.0.md` | v1.0; API/event standard | Common command, event, versioning and ownership rules |

If a version or status cannot be verified, mark it **unverified**. Do not infer a freeze or implementation permission.

## 3. Binding boundaries to preserve

1. **Canonical Actor identity:** Identity & Security owns Actor identity. Actor types include `HUMAN`, `AGENT`, `SERVICE`, `WORKER`, and `EXTERNAL_SYSTEM`. Actor identity does not grant permissions.
2. **Agent definition and version:** Contract 10 and the agent-orchestration architecture own agent identity/definition, immutable agent versions and capabilities.
3. **Worker identity and trust:** WP-3 owns worker registration, trust, capability verification/approval, credential lifecycle and worker eligibility.
4. **Durable execution:** WP-2 owns Workflow/WorkflowTask/Job/JobAttempt/Lease semantics, dispatch, retries, idempotency, recovery and authoritative execution state.
5. **Agent execution:** The Agent Handler executes a bounded task on an assigned worker. It does not become a second identity, trust, workflow or authorization authority.
6. **Artifact identity and integrity:** WP-4 / Asset & Artifact Management owns canonical artifact identity, immutable versions, provenance, validation and integrity.
7. **Rights, QA, approval and authorization:** Contract 07 / WP-5 owns central governance and protected-action authorization.
8. **Orchestration:** The orchestrator validates worker/agent reports and commits authoritative state transitions. A self-reported success is not canonical completion.
9. **Distribution:** Public publishing remains disabled unless separately authorized. This handoff grants no publishing authority.

### Identity linkage proposal — owner review required

The Canonical Data Dictionary defines `Actor` separately from Contract 10's `AgentIdentity`. Proposed explicit link:

- `AgentIdentity.actor_ref` → canonical Actor reference.
- `AgentIdentity.agent_id` remains the agent-domain identity.
- `AgentVersion.agent_version_id` remains an immutable version identifier.
- Worker identity remains a distinct WP-3 identity.

This is a proposal, not a frozen field-level decision. Confirm canonical reference shape and ownership before freezing.

## 4. Work package: reconcile four interface families

Prepare these within the existing Batch 18 structure:

1. Assignment issuance.
2. Assignment acknowledgement / rejection.
3. Result submission / acceptance.
4. Failure reporting / recovery signalling.

Also reconcile lease renewal, expiry and fencing behavior, either within those interface families or by explicit cross-reference to WP-2.

### 4.1 Assignment issuance — field-level reconciliation

| Field/concept | Requirement / authority | Closure state |
|---|---|---|
| `assignment_id` | Unique assignment reference | Proposed; canonical identity/ownership to confirm |
| `job_id` | WP-2 canonical Job identity | Source-defined |
| `attempt_id` | WP-2 canonical JobAttempt identity | Source-defined |
| `worker_id` | WP-3 canonical worker identity | Source-defined |
| `agent_id` / `agent_version_id` | Contract 10 agent identity/version where applicable | Concept source-defined; exact linkage open |
| `capability_refs` and versions | Must match approved/verified WP-3 capabilities | Catalogue/versioning open |
| `contract_version` | Assignment/task payload contract version | Source-defined |
| `input_refs` | Minimum scoped input references; no secrets or large binaries in queue payload | Source-defined |
| `lease_ref` / lease identity | Bind current job, attempt and worker | Concept source-defined; exact shape open |
| `fencing_token` or equivalent generation | Prevent stale attempts from committing | Required behavior; exact mechanism/field open |
| `issued_at`, `expires_at` | UTC timestamps; bounded assignment validity | Exact schema open |
| `correlation_id`, `causation_id` | End-to-end trace and causal chain | Common contract requirement |
| `policy_context_ref` | Reference policy context; worker-supplied values are not proof of authorization | Exact shape open |

Do not place credentials, API keys, passwords or long-lived tokens in assignment payloads. Credential issuance/delivery belongs to WP-3's approved security design.

### 4.2 Acknowledgement / rejection

The contract must distinguish:

- `ACKNOWLEDGED`: worker confirms receipt while identity, credential, assignment, attempt and lease remain valid.
- `REJECTED`: worker cannot accept; returns a structured reason and correlation reference.
- `EXPIRED` / `STALE`: assignment or lease is no longer current; it cannot start or authorize execution.

These are proposed outcomes, not frozen enum values. Reconcile with WP-2 JobAttempt state and WP-3 worker lifecycle. Acknowledgement does not mean job success.

### 4.3 Result submission / acceptance

Bind the result to the exact execution context:

- `job_id`, `attempt_id`, `worker_id`
- `assignment_id` / lease reference
- fencing generation/token or equivalent
- `agent_id` and `agent_version_id`, where applicable
- task/output contract version
- result outcome and structured result reference
- `artifact_refs` and immutable artifact-version references
- evidence/provenance references
- warnings and limitations
- completion timestamp
- `correlation_id` and `causation_id`

The control plane validates identity, credential, current attempt/lease, fencing value, schema, output references and artifact integrity before accepting the result. A worker success claim alone cannot commit authoritative Job or Workflow state.

Do not embed artifact bytes in ordinary job/result messages. Use scoped references and WP-4 transfer/validation contracts.

### 4.4 Failure reporting / recovery signalling

Preserve the separation between agent outcome, job/attempt state and worker/lease state.

Part 5 defines agent outcomes including:

- `completed`
- `needs_input`
- `needs_human_review`
- `failed_retryable`
- `failed_terminal`
- `cancelled`

WP-2 owns whether a job is retried, delayed, blocked, failed, cancelled or dead-lettered. WP-3 owns worker trust/availability lifecycle. Lease expiry is not proof that the task failed.

Failure reports should include job/attempt/worker/assignment references, agent identity/version where applicable, structured failure category/code, retryability recommendation (not unilateral retry authority), sanitized diagnostic/evidence references, timestamp and correlation/causation references.

The orchestrator applies authoritative retry/recovery policy. Unknown outcomes and potentially completed side effects require reconciliation before retry.

## 5. Required invariants

1. Only the control plane creates authoritative assignments and leases.
2. Worker eligibility requires authenticated identity, valid trust state, compatible contract, approved/verified capability, current availability and central authorization.
3. Capability declaration is not proof of capability or permission.
4. Acknowledgement is accepted only for the current assignment/attempt/lease.
5. Lease renewal is accepted only from the authenticated assigned worker while eligible.
6. An expired or superseded lease cannot authorize progress or completion.
7. Reassignment creates a new attempt identity.
8. Stale result submissions are rejected or quarantined; they cannot overwrite newer state.
9. At-least-once duplicate delivery is expected; idempotency/inbox rules prevent duplicate logical effects.
10. Same idempotency key with changed semantic payload must conflict/reject.
11. Agent/worker reports are untrusted until schema, authority, references and integrity are validated.
12. Cross-domain canonical state changes go through the owning domain's command boundary.
13. Events are emitted only after source-state commit; events are not authorization.
14. Approval, rights, QA, authorization, execution and confirmed external outcome remain distinct.
15. No production side effect is part of this documentation closure.

## 6. Proposed acceptance test matrix

Add traceable tests and map them to existing API-01…API-18 where applicable. Do not duplicate an existing test ID without documenting the relationship.

| Proposed test | Scenario | Expected behavior |
|---|---|---|
| AGW-01 | Assignment references unknown job/attempt | Reject; no assignment/lease side effect |
| AGW-02 | Worker identity invalid, revoked or credential expired | Reject; no protected input access |
| AGW-03 | Worker declares but lacks verified/approved capability | Reject assignment |
| AGW-04 | Worker acknowledges current valid assignment | Record acknowledgement; execution may proceed under policy |
| AGW-05 | Worker acknowledges expired/superseded assignment | Reject as stale |
| AGW-06 | Worker A submits for Worker B's assignment | Reject and audit |
| AGW-07 | Lease renewal from wrong worker or stale attempt | Reject; authoritative lease unchanged |
| AGW-08 | Lease expires and a new attempt is issued | Old attempt cannot commit; new attempt has distinct identity/fencing generation |
| AGW-09 | Old result arrives after reassignment | Reject/quarantine; do not overwrite current attempt |
| AGW-10 | Same result delivered twice | One logical result/effect; duplicate recognized |
| AGW-11 | Same idempotency key, changed result payload | Conflict/rejection |
| AGW-12 | Result references missing/unauthorized/invalid artifact | Reject/quarantine; artifact not eligible downstream |
| AGW-13 | Agent says `completed`, but output validation fails | Do not mark Job/Workflow succeeded |
| AGW-14 | Agent reports `failed_retryable` | Orchestrator evaluates WP-2 retry policy |
| AGW-15 | Agent reports `needs_human_review` | Workflow enters review hold; no repeated worker dispatch |
| AGW-16 | Worker disconnects during execution | Lease/recovery policy applies; no unsupported success assumption |
| AGW-17 | Late completion arrives after lease loss | Reconcile/quarantine; stale result cannot change canonical state |
| AGW-18 | Unsupported schema version or unknown enum | Safe reject/quarantine; never map to permissive state |
| AGW-19 | Correlation/causation crosses assignment, result and event | IDs preserved and traceable |
| AGW-20 | Secret appears in assignment/result/error/log | Security test fails; secret redacted/prevented |

Each test needs a versioned schema/fixture, actor and scope, command/event IDs, correlation ID, expected/actual canonical state, timestamps, reproducible test command and reviewer evidence. These are proposed tests, not executed tests.

## 7. Open decisions — do not guess or freeze

| Open item | Owning source/domain | Closure evidence |
|---|---|---|
| JSON Schema types, requiredness, nullability, formats and lengths | Batch 18 / API contract owners | Versioned schema bundle |
| Routes, command/event names and HTTP mappings | Batch 18 | Owner-approved interface catalogue |
| Assignment/attempt/lease canonical field names | WP-2 + WP-3 | Joint reconciliation |
| Fencing mechanism and monotonicity scope | WP-2 | Explicit design and tests |
| Worker enrollment, machine identity and credential protocol | WP-3 / Security | Security design and threat model |
| Capability catalogue, versioning and verification | WP-3 + Contract 10 | Owner-approved catalogue |
| Agent Actor linkage field/reference type | Identity & Security + Contract 10 | Canonical ownership confirmation |
| Artifact transfer/result-reference details | WP-4 | Artifact contract and integrity tests |
| Idempotency key scope, TTL and retention | WP-2 / Batch 18 | Command-family policy |
| Outbox/inbox schema, ordering, retention and dead-letter replay | WP-2 / Batch 18 | Transaction/recovery design |
| Error codes and retry classification | Batch 18 + WP-2 | Canonical error registry |
| Service-to-service authentication | Security / API-OPEN-10 | Security architecture |
| Webhook signature and replay protocol | Security / API-OPEN-11 | Provider-neutral callback standard |
| Audit retention and sensitive-data rules | Security / API-OPEN-13 | Policy decision |
| Exact Contract 01–12 mapping/schema ownership | Batch 18 / API-OPEN-15 | Reconciled traceability matrix |

Numerical lease, heartbeat, retry, timeout, resource and retention values remain open unless an accepted authoritative decision supplies them.

## 8. Required document updates

1. Inspect the current Batch 18 document and its existing open-item register.
2. Add/revise the four interface families and lease/fencing linkage inside Batch 18.
3. Add the AGW acceptance matrix, cross-referenced to API-01…API-18.
4. Close API-OPEN items only when closure evidence exists; otherwise retain OPEN.
5. Add traceability from each field/behavior to WP-2, WP-3, Part 5, Contract 10, the Data Dictionary and API/Event Standard.
6. Identify contradictions, missing source sections and unresolved owner decisions.
7. Prepare a proposed owner-freeze decision sheet.
8. Prepare a revised engineering handoff only after owner disposition is recorded.

Do not edit frozen/accepted source decisions or change ownership boundaries. Prefer a tracked append-only change proposal or a new revision of the existing Batch 18 artifact, according to its document-control rules. Preserve the prior version.

## 9. Completion report required

Return exact files inspected and versions/statuses; exact sections changed; field-level schemas for all four interface families; source traceability; accepted/source-defined/proposed/open/deferred classification; unresolved decisions and owners; proposed versus executed tests; document version/change history; and confirmation that no implementation or prohibited action occurred.

Do not claim the handoff register or canonical architecture documents were updated unless actually changed and verified.

## 10. Explicit authorization boundary

This handoff authorizes documentation reconciliation only, subject to existing document-access and change-control rules.

It does **not** authorize repository access/inspection, code/test/config/workflow changes, running tests or production workflows, agent/worker registration or execution, provider activation, credentials or permission changes, paid services, integration, merge, commit, push, deployment, production generation, external upload, public publishing, destructive Git/file operations, or agent ownership changes.

Separate explicit owner authorization is required for any of these actions.

## 11. Recommended next owner action

Review the proposed interface closure and decide whether to:

**A.** Approve the proposed field-level direction for the four interface families while leaving listed protocol/numeric choices open; or  
**B.** Return specific field/behavior changes before schema freeze.

Until that decision is recorded, Batch 18 remains a detailed interface candidate with owner freeze pending, and implementation remains unauthorized.
