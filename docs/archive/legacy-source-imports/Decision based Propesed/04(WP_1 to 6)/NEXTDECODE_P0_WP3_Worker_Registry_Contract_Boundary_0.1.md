# NEXTDECODE — P0 WP-3
## Worker Registry & Contract Boundary

**Version:** 0.1  
**Status:** DESIGN CANDIDATE — OWNER REVIEW REQUIRED  
**Scope:** P0 foundation  
**Implementation status:** Not authorized

---

## 1. Purpose

Define a secure, consistent contract for registering, trusting, monitoring and authorizing local or remote execution workers.

A worker is an execution endpoint. It performs an assigned, bounded job under control-plane governance. It does not own global workflow orchestration, business decisions or authorization policy.

The same trust boundary must apply to local and remote workers.

## 2. Decision labels

- **ACCEPTED:** Already established by accepted ADR/CF decisions.
- **SOURCE-DEFINED:** Requirements stated in the P0 specification or contract documents.
- **RECOMMENDED:** Proposed design detail for owner review.
- **OPEN:** Requires further decision or evidence.
- **DEFERRED:** Intentionally postponed.

This document does not freeze detailed contracts or authorize implementation.

## 3. Accepted architecture baseline

The following are accepted requirements under ADR-005, CF-13 and CF-14:

1. Canonical worker identity is independent of hostname or machine name.
2. Worker registration and trust have explicit lifecycles.
3. Declared, verified, available and authorized capabilities are distinct.
4. Credentials are unique, scoped, short-lived and revocable.
5. Assignment and completion validate worker identity and authorization.
6. Local and remote workers follow the same trust boundary.
7. Worker trust changes are auditable.
8. Capabilities are versioned and independently verified.
9. Capability declarations do not grant permissions.
10. Jobs execute inside controlled isolation boundaries.
11. Filesystem, network, credentials and artifact access are scoped.
12. Resource requirements and limits are defined by job class.
13. Administrative, production, QA and publishing permissions remain separated.
14. Numerical resource limits remain deferred.

## 4. Responsibility boundary

### Control plane owns

- Canonical worker identity and registration records.
- Trust and enrollment decisions.
- Capability verification and approval.
- Assignment eligibility and authorization.
- Credential issuance policy and revocation.
- Job-to-worker assignment records.
- Worker lifecycle and audit history.
- Central enforcement of access policy.

### Worker owns

- Local execution environment and its reported health.
- Capability declarations and supporting evidence.
- Authentication when communicating with the control plane.
- Execution of valid assigned jobs.
- Heartbeats and lease renewal.
- Attributable completion and failure reports.
- Secure handling of temporary execution data.

### Worker must not

- Assign itself arbitrary jobs.
- Grant itself new capabilities or permissions.
- Change global workflow state outside its authorized contract.
- Claim success after losing its valid assignment.
- Reuse human login credentials as machine credentials.
- Access unrelated files, artifacts, secrets or network resources.
- Bypass central authorization through direct adapters.

## 5. Conceptual worker model

**RECOMMENDED logical record — exact schema remains open.**

| Field | Purpose |
|---|---|
| `worker_id` | Canonical immutable worker identity |
| `machine_identity_reference` | Reference to verified machine identity evidence |
| `environment_type` | Local or remote execution context |
| `worker_status` | Registration/trust lifecycle state |
| `software_version` | Installed worker version |
| `contract_version` | Supported worker contract version |
| `declared_capabilities` | Capabilities claimed by the worker |
| `verified_capabilities` | Capabilities independently verified |
| `approved_capabilities` | Capabilities approved for eligibility |
| `last_heartbeat_at` | Most recent accepted heartbeat |
| `credential_status` | Credential lifecycle status |
| `registered_at` | Registration timestamp |
| `revoked_at` | Revocation timestamp, when applicable |
| `metadata` | Minimised, non-sensitive operational metadata |

The hostname and machine name are attributes or references, not canonical identity.

## 6. Keep four capability facts separate

These must not be collapsed into a single `capabilities` field.

### 6.1 Declared

What the worker claims it can perform.

Example: a local machine declares `shorts.render.local`.

A declaration is a claim, not proof.

### 6.2 Verified

What the control plane or an approved verification process has evidence that the worker can perform.

Verification may include compatibility checks, software versions, environment checks and controlled capability tests.

The exact verification protocol is **OPEN**.

### 6.3 Available

What the worker can perform now.

A verified rendering capability may be unavailable because the machine is offline, unhealthy, busy or missing a required resource.

Availability is time-sensitive and should be refreshed.

### 6.4 Authorized

What the control plane permits the worker to perform for a particular assignment.

Authorization must consider the worker identity, approved capability, job requirements, resource scope, policy and current assignment.

A worker can be verified and available but still not authorized for a particular job.

## 7. Worker lifecycle

**RECOMMENDED lifecycle model — final state names and transitions are OPEN.**

Conceptual progression:

`UNREGISTERED → REGISTERED → TRUST_PENDING → TRUSTED → ACTIVE`

Additional operational conditions may include:

- `UNAVAILABLE`
- `DRAINING`
- `QUARANTINED`
- `SUSPENDED`
- `REVOKED`

These are candidate labels, not accepted final enum values.

Important distinctions:

- Registration does not mean trusted.
- Trusted does not mean online.
- Online does not mean healthy.
- Healthy does not mean authorized.
- Revoked means access must be denied even if the machine is still online.

Trust changes must be attributable and auditable. Re-enrollment and recovery must not silently restore revoked permissions.

## 8. Registration and enrollment boundary

### Registration request — proposed information

- Machine identity proof or reference.
- Worker software version.
- Supported contract versions.
- Declared capabilities.
- Environment type (`local` or `remote`).
- Optional resource profile.
- Registration request/correlation identity.

### Control-plane response — proposed information

- Canonical `worker_id`.
- Registration/trust status.
- Contract compatibility result.
- Approved capability set, if any.
- Credential issuance instructions.
- Heartbeat policy reference.
- Any restrictions or required follow-up verification.

The server may approve a narrower capability set than the worker declares.

**OPEN:** Enrollment protocol, machine identity attestation requirements, recovery process and registration approval authority.

## 9. Credential contract

### Accepted direction

- Unique worker identity.
- Scoped, short-lived/renewable credentials.
- Independent revocation.
- Worker credentials are separate from human login credentials.

### Recommended enforcement rules

1. Credential audience is the control plane or an explicitly approved service.
2. Scope is restricted to required worker actions.
3. Expiry is always enforced.
4. Renewal or reissue requires proof of worker identity.
5. Revocation prevents new claims and new protected artifact access.
6. Credentials never appear in job payloads, logs, traces or error messages.
7. A worker cannot use another worker's credentials.
8. Revocation and trust changes produce audit evidence.

**OPEN:**

- Credential issuer and protocol.
- Token format.
- Renewal and rotation cadence.
- Revocation propagation target.
- Local secret-storage mechanism.
- Enrollment and recovery procedure.
- Machine identity attestation requirements.

No issuer, token technology or secret-storage provider is selected here.

## 10. Capability contract

A capability is a typed permission to execute a particular class of work, not an unrestricted role.

Illustrative capability names from the source contract:

- `research.fetch`
- `script.generate`
- `visuals.prepare`
- `shorts.render.local`
- `artifact.upload`
- `artifact.download`
- `quality.validate`

These names are examples, not a frozen catalogue.

### Assignment rules

1. Each job declares its required capabilities.
2. The worker must have every required capability approved.
3. The control plane checks capability eligibility server-side.
4. Sensitive capabilities require explicit server approval.
5. A local-only capability is eligible only while the required local worker is online and healthy.
6. If the local worker is unavailable, the durable workflow waits safely rather than silently substituting an unsuitable worker.
7. Capability versions must be compatible with the job and contract versions.

A capability declaration never creates authorization.

## 11. Execution isolation and resource boundary

Each assignment must be bounded.

### Filesystem

- Permit only explicitly scoped input and output locations.
- Prevent access to unrelated user files.
- Keep temporary execution data separate from authoritative shared state.
- Avoid broad filesystem permissions.

### Network

- Network access must be restricted by job requirements and policy.
- A worker must not receive unrestricted outbound access by default.
- Network permissions must not be inferred from capability declarations.

### Credentials

- Provide only the credentials needed for the specific assignment.
- Do not expose general user sessions or unrelated provider credentials.
- Never place secrets in ordinary job payloads or logs.

### Artifacts

- Access must be scoped to exact authorized artifact references.
- Transfers must be attributable and integrity-verifiable.
- Quarantined or otherwise disallowed artifacts cannot be used through normal downstream paths.

### Resources

Resource requirements and limits belong to job classes. Numerical CPU, memory, disk, concurrency and execution-time limits remain deferred until measured and reviewed.

The isolation technology itself is also open.

## 12. Local and remote worker parity

Both worker types use the same identity, trust, capability, authorization and audit model.

| Concern | Local worker | Remote worker |
|---|---|---|
| Canonical identity | Independent of machine name | Independent of host name |
| Trust | Centrally governed | Centrally governed |
| Credentials | Scoped and revocable | Scoped and revocable |
| Capability verification | Required | Required |
| Job authorization | Server-side | Server-side |
| Artifact access | Scoped | Scoped |
| Audit | Required | Required |

### Local worker offline behavior

- Local-only jobs remain queued or waiting.
- The control plane retains workflow state.
- The local worker re-authenticates after reconnecting.
- Capabilities and health are refreshed.
- Only eligible work is resumed.
- Completed work must not be duplicated merely because the worker reconnects.
- Local temporary files are not authoritative shared state.

## 13. Assignment and completion checks

Before accepting a claim or assignment, the control plane should verify:

1. Worker identity is valid.
2. Worker trust state permits execution.
3. Credential is valid, scoped and unexpired.
4. Contract version is compatible.
5. Worker is currently eligible and available.
6. Required capabilities are approved and verified.
7. Job requirements match the worker's approved capabilities.
8. The assignment is valid and has an authoritative lease.
9. Central authorization permits the requested action.

Before accepting completion, verify:

- Worker identity and credential remain valid for the operation.
- The worker owns the current valid assignment/lease.
- The attempt identity matches.
- The completion is attributable and schema-valid.
- A stale worker cannot overwrite a newer attempt.
- Results and artifacts reference the correct job and attempt.

A successful worker response alone does not establish workflow completion or authorize downstream publishing.

## 14. Revocation, suspension and quarantine

**RECOMMENDED behavior:**

- Revoked workers cannot claim new jobs.
- Revoked workers cannot fetch new protected artifacts.
- Expired credentials are rejected.
- Suspended or quarantined workers are excluded from normal assignment.
- Existing active assignments are reconciled under explicit policy.
- Re-enrollment requires a fresh trust decision.
- Historical audit records remain available.

**OPEN:** Exact behavior for active leases during revocation, quarantine triggers, recovery authority and revocation propagation timing.

## 15. Audit and observability

Record attributable events for:

- Registration requests and decisions.
- Trust verification and trust changes.
- Capability declarations, verification and approval.
- Credential issuance, renewal and revocation.
- Heartbeats and availability changes.
- Assignment claims and rejections.
- Lease renewal and expiry.
- Worker suspension, quarantine and recovery.
- Completion, failure and reconciliation.

Logs must redact secrets. Audit records must distinguish what the worker claimed, what was verified, what was available and what was authorized.

## 16. Proposed acceptance criteria

These are design acceptance targets, not executed tests.

1. A worker cannot claim a job requiring an unapproved capability.
2. A worker with a declared but unverified capability is denied.
3. An unavailable local worker does not cause a local-only job to disappear.
4. An expired credential is denied.
5. A revoked worker cannot claim new work.
6. A revoked worker cannot fetch new protected artifacts.
7. Worker A cannot update Worker B's active lease.
8. A stale worker cannot commit completion after lease supersession.
9. A worker cannot expand its own capability or authorization set.
10. Local and remote workers pass the same trust-boundary tests.
11. Worker credential values do not appear in logs or job payloads.
12. Trust and capability changes are auditable.
13. A worker reconnect does not duplicate completed work.
14. A malformed or unsupported worker contract is rejected safely.

## 17. Open decisions

| ID | Open item | Required before |
|---|---|---|
| W-01 | Enrollment protocol and approval workflow | Detailed contract freeze |
| W-02 | Machine identity proof and attestation | Security implementation |
| W-03 | Credential issuer, protocol and token format | Credential implementation |
| W-04 | Renewal, rotation and revocation timing | Security implementation |
| W-05 | Local secret-storage mechanism | Local worker implementation |
| W-06 | Final capability catalogue and versioning | Adapter integration |
| W-07 | Capability verification evidence and procedure | Worker trust implementation |
| W-08 | Lifecycle states and allowed transitions | Schema/contract freeze |
| W-09 | Heartbeat and availability policy | Runtime implementation |
| W-10 | Resource quotas by job class | Isolation implementation |
| W-11 | Isolation technology and threat model | Worker implementation |
| W-12 | Active assignment behavior during revocation | Recovery contract |
| W-13 | Quarantine, suspension and recovery authority | Governance freeze |
| W-14 | Contract compatibility and upgrade policy | Worker rollout |

These decisions are intentionally not guessed or silently frozen.

## 18. Dependencies and handoffs

- **WP-1:** Canonical identity, relational ownership and versioned references.
- **WP-2:** Job assignment, attempt identity, lease, fencing, retry and recovery.
- **WP-4:** Scoped artifact transfer and integrity checks.
- **WP-5:** Central authorization, rights and QA enforcement.
- **WP-6:** Integrated local-worker vertical slice and failure-recovery validation.

## 19. Implementation safety boundary

This document does not authorize:

- Repository or code changes.
- Worker enrollment or credential issuance.
- Agent execution or machine registration.
- Changes to local or remote permissions.
- Provider activation or paid services.
- Cloud deployment.
- Production rendering, uploads or publishing.

Any such action requires the appropriate separate authorization.

## 20. Plain-language explanation

Think of a worker as a trusted technician receiving one specific work order.

The technician may say, “I can render videos.” NEXTDECODE must still verify that claim, check whether the technician is online and healthy, and decide whether that particular job is permitted.

The technician receives only the access needed for that assignment. If trust is revoked or the assignment expires, the technician cannot simply declare the work complete.

For NEXTDECODE, this means your desktop can render a video when it is available, while the central workflow remains safe and durable. A future remote worker can follow the same rules without becoming a separate, less-governed system.

---

**WP-3 outcome:** Worker identity, trust, capability, availability and assignment authorization are separated into explicit boundaries. Detailed protocols, numeric policies and implementation choices remain open for owner review.
