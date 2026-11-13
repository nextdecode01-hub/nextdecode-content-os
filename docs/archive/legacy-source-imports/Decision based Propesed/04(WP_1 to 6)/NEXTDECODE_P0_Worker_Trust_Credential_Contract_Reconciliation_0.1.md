# NEXTDECODE — P0 Worker Trust & Credential Contract Reconciliation

**Document ID:** `NEXTDECODE_P0_Worker_Trust_Credential_Contract_Reconciliation_0.1`  
**Version:** 0.1  
**Date:** 1 November 2026  
**Status:** DESIGN RECONCILIATION — OWNER / SECURITY REVIEW REQUIRED  
**Scope:** WP-3; cross-document finding X-06  
**Detailed contract freeze:** NOT GRANTED  
**Implementation authorization:** NOT GRANTED

---

## 1. Purpose and disposition

This document resolves the minimum vendor-neutral worker trust contract needed before local or remote workers can safely claim and execute durable jobs.

It reconciles WP-3 with accepted ADR-005, CF-13 and CF-14, the WP-2 assignment/lease model, and the Cross-Document Consistency & Gap Review.

**Disposition:** X-06 is clarified at the minimum logical-protocol level. Provider and technology choices remain deferred. Owner/security review is still required for machine identity proof, minimum isolation guarantees, revocation behavior for active jobs, and the authority to suspend, quarantine, restore or revoke workers.

This document does not select an identity provider, credential issuer, token format, secret store, isolation technology or cloud provider. It does not authorize worker enrollment, credential issuance, repository changes or tests.

## 2. Authority and decision labels

Source precedence:

1. Accepted owner decision record and ADR-001–ADR-010 / CF-01–CF-24.
2. Governing canonical data dictionary, API/Event Contract Standard and Unified Lifecycle/State Transition Standard.
3. WP-1 through WP-6 package specifications.
4. Consolidated Contract Appendix as a derivative consolidation aid.
5. This reconciliation as a candidate clarification.

Labels:
- **ACCEPTED BASELINE:** already accepted by owner decision.
- **SOURCE-DEFINED:** required by WP-3 or governing source.
- **RECONCILED:** clarifies a boundary without changing accepted policy.
- **PROPOSED:** conservative vendor-neutral candidate detail.
- **OPEN / OWNER-SECURITY-RESERVED:** requires review or explicit authority.
- **DEFERRED:** provider/technology detail intentionally postponed.

## 3. Accepted worker trust invariants

The following remain unchanged:

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

## 4. Responsibility and authority boundary

### 4.1 Control plane — authoritative

The control plane owns:
- canonical worker identity and registration;
- enrollment and trust decisions;
- capability verification and approval;
- assignment eligibility and authorization;
- credential issuance policy, renewal policy and revocation;
- worker lifecycle and audit history;
- assignment records and lease authority;
- central enforcement of access policy.

### 4.2 Worker — bounded execution endpoint

The worker owns:
- its local execution environment and reported health;
- capability declarations and supporting evidence;
- authentication to the control plane;
- execution of valid bounded assignments;
- heartbeat and lease-renewal requests;
- attributable completion/failure reports;
- secure handling of temporary execution data.

### 4.3 Worker must never

- self-assign arbitrary jobs;
- self-approve trust or capabilities;
- grant itself permissions;
- change global workflow state outside its contract;
- claim success after losing its valid assignment;
- reuse human login credentials as machine credentials;
- access unrelated files, artifacts, secrets or network resources;
- bypass central authorization through direct adapters.

A worker report is evidence supplied by the worker, not authoritative proof of its own trust, capability approval, authorization or job completion.

## 5. Worker identity and enrollment

### 5.1 Canonical identity — ACCEPTED BASELINE

`worker_id` is the immutable canonical identity for one registered worker identity. It is not derived from hostname, username, IP address, container ID or machine display name.

Machine identity evidence is linked to the canonical worker identity but does not replace it. Hostnames and machine names are mutable attributes.

### 5.2 Enrollment stages — PROPOSED

Use the following conceptual sequence. Final enum names must be reconciled with the governing lifecycle standard.

`REGISTRATION_REQUESTED → IDENTITY_PENDING → TRUST_REVIEW → TRUSTED`

A request may instead be rejected, suspended or revoked through attributable control-plane decisions. Registration is not trust.

Minimum enrollment sequence:

1. Worker submits an enrollment request with a unique request/correlation identity.
2. Control plane validates protocol and contract compatibility.
3. Control plane evaluates machine identity evidence.
4. Control plane records environment type (`local` or `remote`) and declared capabilities.
5. A trusted authority approves, narrows or rejects the request.
6. Only after trust approval may the control plane issue a scoped machine credential.
7. The worker authenticates and proves possession of the credential.
8. Capability verification proceeds separately.
9. Assignment eligibility is granted only after all required checks.

### 5.3 Vendor-neutral machine identity evidence — PROPOSED

The trust protocol should establish:
- a unique worker enrollment request;
- proof that the enrolling endpoint controls the presented machine/worker identity material;
- binding between proof and the canonical worker registration;
- freshness against replay of an old enrollment proof;
- evidence of software/contract version and environment type;
- an attributable approval or rejection decision.

Possible evidence mechanisms may include a generated key pair with proof of possession, a pre-authorized enrollment secret, or platform-backed attestation. These are alternatives for later security review, not a selected design.

**OPEN / OWNER-SECURITY-RESERVED:**
- required assurance level for local versus remote workers;
- whether local owner-operated machines may use a simpler enrollment path;
- attestation requirements and threat model;
- manual approval versus automated policy for initial enrollment;
- re-enrollment and machine replacement procedure;
- treatment of cloned disks, restored snapshots and duplicated credentials.

No hostname-only or IP-only identity claim is sufficient.

## 6. Worker lifecycle and operational state separation

### 6.1 Do not collapse trust and availability

A worker can be trusted but offline; online but unhealthy; healthy but not approved for a capability; capability-approved but not authorized for a particular job.

### 6.2 Conceptual trust states — PROPOSED

- `PENDING_VERIFICATION`: enrollment evidence is incomplete or awaiting decision.
- `TRUSTED`: identity/trust review accepted.
- `SUSPENDED`: temporarily prevented from normal operation pending review or administrative action.
- `QUARANTINED`: isolated because of a security/integrity concern.
- `REVOKED`: trust relationship terminated; access denied.
- `REJECTED`: enrollment not accepted.

These are candidate labels only. Final states and transitions remain subject to the lifecycle standard and owner/security review.

### 6.3 Operational conditions — separate dimension

Examples:
- `ONLINE`
- `OFFLINE`
- `HEALTHY`
- `UNHEALTHY`
- `DRAINING`
- `BUSY`

These are not trust states and must not be combined into one overloaded `worker_status` field.

### 6.4 Required distinctions

- Registered does not mean trusted.
- Trusted does not mean online.
- Online does not mean healthy.
- Healthy does not mean capability-verified.
- Capability-verified does not mean currently available.
- Available does not mean authorized for a job.
- Revoked means access is denied even if the process remains online.

Trust restoration after suspension/quarantine requires a new attributable decision. Re-enrollment must not silently restore previously revoked permissions.

## 7. Capability contract — preserve four facts

Each capability must be versioned and separately represented as:

1. **Declared:** what the worker claims it can do.
2. **Verified:** what an approved verification process has evidence it can do.
3. **Available:** what it can do now given health, load, resources and connectivity.
4. **Authorized:** what the control plane permits it to do for this exact assignment.

A job declares required capabilities. The control plane checks server-side that the worker has all required approved capabilities, compatible versions and current availability. Sensitive capabilities require explicit approval.

Illustrative names from WP-3 remain examples only:
- `research.fetch`
- `script.generate`
- `visuals.prepare`
- `shorts.render.local`
- `artifact.upload`
- `artifact.download`
- `quality.validate`

A declaration never creates permission. A verified capability does not confer a role, and a capability does not authorize access to arbitrary files, secrets, accounts or destinations.

**OPEN:** final capability catalogue, version compatibility, verification profiles, evidence freshness and approval authority.

## 8. Credential contract — minimum vendor-neutral requirements

### 8.1 Credential properties — ACCEPTED / SOURCE-DEFINED

Every machine credential must be:
- unique to the canonical worker identity;
- separate from human login credentials;
- scoped to required worker operations;
- short-lived and expiring;
- independently revocable;
- bound to an intended audience/service;
- protected against disclosure and reuse by another worker.

### 8.2 Proposed credential claims/binding

A credential or its authoritative server-side record should bind to:
- worker identity (`worker_id`);
- subject/holder identity;
- intended audience/service;
- allowed scopes/actions;
- issued-at and expiry;
- credential identifier or revocation handle;
- relevant trust/registration epoch or version;
- issuer identity.

The token format and exact claim names are OPEN. Do not assume a particular JWT, opaque-token or certificate design.

### 8.3 Authentication and authorization remain separate

Successful authentication proves the presented credential is accepted for its subject/audience/time. It does not itself authorize a job, artifact, administrative action or publishing action.

Every protected operation still requires the relevant central authorization decision and current assignment/lease validation.

### 8.4 Credential handling

- Never place credential values in job payloads, event bodies, logs, traces, exception messages or artifact metadata.
- Do not share one worker's credential with another worker.
- Do not reuse human browser sessions or personal access tokens as worker credentials.
- Store secrets using an approved platform-appropriate secret-protection mechanism.
- Restrict read access to the smallest required process boundary.
- Rotation must not create an interval in which a revoked credential is accepted.
- Renewal/reissue requires fresh proof of worker identity and current trust status.

**OPEN:** issuer/protocol, token format, rotation cadence, renewal window, local secret-storage mechanism, key protection and credential recovery.

No provider or storage product is selected.

## 9. Credential revocation and trust-change propagation

### 9.1 Required behavior — SOURCE-DEFINED

Revoked workers cannot:
- claim new jobs;
- renew leases as a trusted worker;
- fetch new protected artifacts;
- perform new protected control-plane actions.

Expired credentials are rejected. Trust changes are auditable.

### 9.2 Proposed enforcement model

- The control plane is the authoritative revocation source.
- Protected requests validate current trust/credential status at the service boundary.
- Revocation is checked on claim, heartbeat/lease renewal, artifact transfer and completion/commit.
- Long-lived cached authorization must not outlive its permitted validity.
- A worker cannot self-assert that it remains trusted.
- Reconnection requires fresh authentication and refreshed trust/capability/availability checks.

### 9.3 Revocation propagation

A propagation target must be defined for every enforcement point. Until a measured/approved target exists, do not claim instantaneous revocation across disconnected systems.

A disconnected worker cannot be trusted to receive a revocation message. Its authority must therefore expire or require periodic online renewal before further protected operations.

**OPEN:** maximum propagation delay, offline grace behavior (if any), revocation-list/cache strategy, and monitoring/alerting.

## 10. Active jobs, leases and revocation

This is the most important WP-2/WP-3 boundary.

### 10.1 Required invariants

- Worker identity and authorization are checked at claim and completion.
- The worker must hold the current valid lease and attempt identity.
- Fencing prevents stale attempts from committing after takeover.
- Revocation blocks new protected access.
- A worker cannot claim success after losing its valid assignment.
- Job/attempt state remains owned by the execution service, not by the worker.

### 10.2 Proposed conservative handling

When a worker becomes suspended, quarantined or revoked while holding a lease:

1. The control plane records the trust change and its effective time.
2. The worker is immediately excluded from new claims.
3. New protected artifact reads/transfers and lease renewals are denied according to current authorization.
4. The active assignment is marked for controlled reconciliation; do not silently mark the job successful or failed.
5. If the worker is reachable, the control plane may request cooperative stop, but the request is not proof that execution stopped.
6. The control plane applies the WP-2 lease/fencing rules before any new worker may take over.
7. Any output produced after loss of valid authority is not accepted as a successful completion until validated against the current attempt/lease and policy.
8. Ambiguous side effects are recorded as unknown and reconciled before unsafe retry.
9. A new attempt, if allowed, uses the same logical job identity and a new attempt identity.

### 10.3 Distinguish trust events

| Event | New claims | Existing lease | Completion |
|---|---|---|---|
| Credential expires | Deny until renewed | Renewal denied until fresh authentication; reconcile current lease | Accept only if current lease, identity and authorization checks pass |
| Worker voluntarily drains | Deny new claims after drain takes effect | Existing work may finish under current policy | Accept only with valid lease and current checks |
| Worker becomes unavailable/offline | No new claim | Lease expiry/recovery rules apply | Late completion is subject to fencing/current-attempt validation |
| Worker is suspended | Deny | Controlled reconciliation; do not assume process stopped | No success accepted without current trust/lease/authorization |
| Worker is quarantined | Deny; protected artifact access restricted | Treat as security-sensitive; isolate and reconcile | Reject untrusted output pending authorized review |
| Worker is revoked | Deny permanently until a new trust decision | Revoke/expire lease under the approved control-plane procedure; fence stale attempt | Stale/revoked worker cannot commit completion |

The table is a proposed behavior matrix, not a frozen state machine.

### 10.4 Owner/security decision required

Explicitly decide:
- whether revocation immediately fences the active attempt or first requests cooperative stop;
- whether any narrowly scoped read-only evidence export is allowed during investigation;
- who may authorize a replacement attempt after a security incident;
- how to treat local files that remain on a revoked machine;
- whether outputs created before revocation but uploaded after revocation can be reviewed or must be quarantined.

**Safe default pending decision:** no new protected access; no stale completion; active work is reconciled under lease/fencing rules; questionable outputs are not promoted into normal downstream use.

## 11. Minimum isolation guarantees — technology deferred

CF-14 requires controlled isolation and scoped filesystem, network, credentials and artifact access. The isolation technology is not selected, but the minimum security properties cannot be omitted.

### 11.1 Required logical guarantees

- **Filesystem:** assignment receives only explicit input/output paths; unrelated user files and secret stores are inaccessible by default.
- **Network:** outbound/inbound access is denied by default unless explicitly required by the job class and authorized.
- **Credentials:** only assignment-scoped credentials are made available; no general user sessions or unrelated provider secrets.
- **Artifacts:** only exact authorized artifact references are readable/writable; transfer is attributable and integrity checked.
- **Process boundary:** one job cannot freely inspect or control unrelated worker processes or another job's temporary data.
- **Temporary data:** scoped, attributable and cleaned according to an approved non-destructive lifecycle; cleanup must not touch user data.
- **Resource controls:** CPU, memory, disk, concurrency and execution-time requirements are associated with job class.
- **Audit:** isolation policy and access decisions are recorded without logging secrets.
- **Failure behavior:** if the isolation boundary cannot be established, the job does not start.

### 11.2 Local/remote parity

The same policy guarantees apply to local and remote workers. A local worker does not receive broader filesystem/network privileges merely because it runs on the owner's PC.

### 11.3 Deferred implementation choices

Container, OS sandbox, VM, restricted process, filesystem namespace, network policy technology and platform-specific controls remain open.

**OWNER/SECURITY REVIEW REQUIRED:** threat model, minimum acceptable isolation for local desktop workers, trusted administrator boundary, handling of malicious job inputs, and whether some job classes are prohibited on local workers.

Numerical resource limits remain deferred pending measurement and approval.

## 12. Local and remote parity; offline local worker

- Both worker types use the same canonical identity, trust, credential, capability, authorization and audit model.
- Local-only jobs wait durably when the required local worker is unavailable.
- Reconnection requires fresh authentication and updated eligibility checks.
- A completed job must not be duplicated because a worker reconnects.
- Local temporary paths are not canonical shared artifact identity.
- A local worker must not bypass central authorization because it is on the same machine as the owner.

## 13. Assignment and completion validation

### Before claim/assignment

The control plane verifies:
1. canonical worker identity;
2. current trust state;
3. credential validity, audience, scope and expiry;
4. worker contract compatibility;
5. current availability/health;
6. approved and verified required capabilities;
7. job-class/resource compatibility;
8. valid job state and assignment eligibility;
9. authoritative lease and fencing context;
10. central authorization.

### Before accepting completion

Verify:
- same canonical worker identity and expected attempt;
- current lease/fencing token;
- valid completion contract/schema;
- trust and authorization rules for completion/commit;
- output artifact references and integrity evidence;
- no superseding attempt has taken ownership;
- completion is attributable and auditable.

A successful worker response alone does not establish workflow completion, QA pass, rights clearance, approval or permission to publish.

## 14. Audit and observability

Record attributable evidence for:
- enrollment request, machine identity proof reference and decision;
- trust state changes and authority;
- declared, verified, approved and available capability changes;
- credential issuance, renewal, expiry and revocation;
- authentication and authorization denials;
- heartbeat and availability changes;
- job claims, leases and renewals;
- worker drain, suspension, quarantine, revocation and recovery;
- cooperative stop requests and acknowledgements;
- completion, failure, stale completion rejection and reconciliation.

Audit records must not contain credential values, private keys or unnecessary personal data.

## 15. WP-6 acceptance matrix — proposed test oracles

These are design targets, not executed tests. Use isolated synthetic workers, credentials, jobs and artifacts only.

| Test ID | Scenario | Expected oracle |
|---|---|---|
| WRK-01 | Enrollment with hostname only and no valid identity proof | Not trusted; no worker credential issued |
| WRK-02 | Valid enrollment proof submitted | Canonical worker identity created; trust decision separately recorded |
| WRK-03 | Duplicate/replayed enrollment proof | Rejected or safely reconciled; no duplicate trusted identity |
| WRK-04 | Worker declares a capability but has no verification evidence | Capability remains declared only; job claim denied |
| WRK-05 | Capability verified but not approved | Job claim denied |
| WRK-06 | Capability approved but worker unavailable | Job remains waiting; no unsuitable substitution |
| WRK-07 | Credential audience or scope mismatch | Request denied |
| WRK-08 | Expired credential | Request denied |
| WRK-09 | Revoked credential | Request denied at protected service boundary |
| WRK-10 | Worker A presents Worker B credential | Denied and audited |
| WRK-11 | Worker revoked while holding a lease | No new claims/renewals; active attempt reconciled and fenced per policy |
| WRK-12 | Stale worker submits completion after takeover | Completion rejected; newer attempt remains authoritative |
| WRK-13 | Worker reconnects after offline period | Fresh authentication/eligibility; no duplicate completed work |
| WRK-14 | Local worker attempts unrelated filesystem access | Isolation boundary denies access |
| WRK-15 | Job attempts unapproved outbound network access | Denied |
| WRK-16 | Worker tries to access unrelated artifact | Central authorization denies |
| WRK-17 | Isolation boundary cannot be established | Job does not start |
| WRK-18 | Credential appears in logs/payloads | Test fails; secret exposure detected |
| WRK-19 | Trust/capability change occurs | Attributable audit event reconstructable |
| WRK-20 | Local and remote worker run same trust tests | Same policy outcomes |

The WP-6 master acceptance plan remains authoritative for environment isolation, fixtures, evidence retention, cleanup and independent QA. This matrix does not authorize test execution.

## 16. Open-decision register

| ID | Open item | Status / required before |
|---|---|---|
| W-01 | Enrollment protocol and approval workflow | OPEN — detailed contract freeze |
| W-02 | Machine identity proof and attestation level | OWNER/SECURITY REVIEW — trust implementation |
| W-03 | Credential issuer, protocol and token format | DEFERRED — provider/technology selection |
| W-04 | Renewal, rotation and revocation timing | OPEN — security implementation |
| W-05 | Local secret-storage mechanism | DEFERRED — local worker implementation |
| W-06 | Final capability catalogue and versioning | OPEN — adapter integration |
| W-07 | Capability verification evidence and procedure | OPEN — trust implementation |
| W-08 | Final trust lifecycle states/transitions | OPEN — lifecycle/contract freeze |
| W-09 | Heartbeat and availability policy | OPEN — runtime implementation |
| W-10 | Resource quotas by job class | DEFERRED — measurement/isolation implementation |
| W-11 | Isolation technology and threat model | OWNER/SECURITY REVIEW — worker implementation |
| W-12 | Active assignment behavior during revocation | OWNER/SECURITY REVIEW — recovery contract |
| W-13 | Quarantine, suspension and recovery authority | OWNER-RESERVED — governance freeze |
| W-14 | Contract compatibility and upgrade policy | OPEN — worker rollout |
| W-15 | Revocation propagation target and disconnected-worker policy | OPEN — security contract |
| W-16 | Local worker assurance level and permitted job classes | OWNER/SECURITY REVIEW |
| W-17 | Re-enrollment after revocation and machine replacement | OPEN — trust operations |
| W-18 | Output treatment when worker is revoked mid-job | OWNER/SECURITY REVIEW — artifact/governance handoff |

No credential issuer, token technology, secret-storage provider, isolation product, numerical quota or cloud provider is selected here.

## 17. Dependencies and handoffs

- **WP-1:** canonical identity, ownership and versioned references.
- **WP-2:** job assignment, attempt identity, leases, fencing, retry and recovery.
- **WP-4:** scoped artifact transfer, integrity and quarantine.
- **WP-5:** central authorization, rights and QA enforcement.
- **WP-6:** integrated worker vertical slice, failure injection and independent read-only QA.

The control plane remains the authority for worker trust and assignment. The execution service remains the authority for job/attempt/lease state. Worker status must not become a second job-state authority.

## 18. Safety and authorization boundary

This document does not authorize:
- repository/code changes or tests;
- worker enrollment or credential issuance;
- machine registration or trust changes;
- agent execution;
- changes to local/remote permissions;
- provider activation or paid services;
- cloud deployment;
- production rendering, uploads or publishing.

Any such action requires separate appropriate authorization.

## 19. Plain-language explanation

Think of a worker as a technician who wants to receive a work order.

First, NEXTDECODE must know which technician it is. Then it checks whether that technician is trusted. Next it verifies what the technician can do, whether they are available right now, and whether they are allowed to perform this particular job.

The technician receives only the access needed for that work order. If trust is revoked while a job is running, NEXTDECODE must stop granting new access, reconcile the active job and prevent an old worker from overwriting a newer attempt.

For NEXTDECODE, your desktop can act as a local rendering worker when available, while the shared workflow remains governed centrally. A future remote worker follows the same rules—no weaker trust boundary.

**Reconciliation outcome:** X-06 now has a vendor-neutral minimum trust, credential, capability, isolation and active-job revocation contract candidate. Owner/security decisions remain open. P0 is still **NOT READY FOR DETAILED CONTRACT FREEZE**.

**Detailed contract freeze:** NOT GRANTED.  
**Implementation authorization:** NOT GRANTED.
