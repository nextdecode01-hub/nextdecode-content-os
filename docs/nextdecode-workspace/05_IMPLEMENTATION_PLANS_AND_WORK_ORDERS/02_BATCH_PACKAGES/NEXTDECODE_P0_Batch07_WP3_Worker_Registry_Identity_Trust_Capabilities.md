NEXTDECODE CONTENT OS

# P0 Batch 07
WP-3 Worker Registry, Identity, Trust & Capabilities

Design working pack • 01 November 2026

Purpose: define a reviewable candidate boundary for worker registration, identity, trust lifecycle, capability declaration/verification and scoped execution credentials. This document is a design candidate only. It does not register workers, issue credentials, change infrastructure, run agents or authorize implementation.

## 1. Status and interpretation

| Label | Meaning |
| --- | --- |
| ACCEPTED DIRECTION | Recorded owner-accepted architecture rule or decision. |
| DESIGN CANDIDATE | Proposed structure requiring reconciliation against authoritative source contracts. |
| SOURCE REQUIRED | Exact fields, enums, lifecycle transitions or operational rules are not verified in the current source set. |
| OWNER DECISION | A genuinely owner-reserved choice; no inferred approval. |
| NOT AUTHORIZED | No worker registration, credential issuance, code change, agent run, deployment or external action. |

The accepted worker-trust direction includes: worker identity is independent of hostname/machine; registration and trust lifecycle are explicit; declared, verified, available and authorized capabilities are distinct; credentials are scoped, short-lived and revocable; local and remote workers follow the same trust model; and trust changes are auditable. Capability declarations are not permissions.

## 2. WP-3 mission and responsibility boundary

| WP-3 owns | WP-3 does not own |
| --- | --- |
| Worker identity and registry lifecycle | Canonical content/workflow domain identity (WP-1) |
| Registration, trust state and attestation/evidence references | Durable job orchestration, retry and workflow progression (WP-2) |
| Capability declaration and verification model | Artifact binary storage/transfer implementation (WP-4) |
| Credential issuance/revocation integration boundary | Central policy definitions, rights and approval governance (WP-5) |
| Worker eligibility and assignment contract | End-to-end P0 integration and recovery sign-off (WP-6) |
| Worker-scoped access boundary and audit events | Provider selection, cloud deployment or unrestricted remote execution |

WP-3 is a trust and execution-principal boundary. It must not become a second authorization service. The centralized authorization authority remains the only authority for granting protected actions.

## 3. Accepted trust invariants

- Worker identity is independent of hostname, IP address, machine name or physical device identity.

- Worker registration and trust lifecycle are explicit, auditable and revocable.

- Declared capability, verified capability, current availability and authorization are four different facts.

- Capability declaration is not proof of capability and never grants permission.

- Credentials are scoped, short-lived and revocable; long-lived shared secrets are not the default model.

- Local and remote workers use the same trust principles and policy boundary.

- Workers execute bounded assignments and cannot self-expand filesystem, network, credential, artifact or administrative scope.

- Worker identity, trust and capability never bypass centralized authorization.

- Administrative, production, QA and publishing permissions remain separated.

- Every registration, trust change, capability verification and credential lifecycle event is attributable and auditable.

## 4. Candidate worker identity model

| Concept | Candidate definition | Important boundary |
| --- | --- | --- |
| Worker ID | Immutable canonical UUIDv7 identity for a registered worker principal | Not derived from hostname, IP, username or hardware serial. |
| Worker instance | A runtime process/session associated with a worker identity | A restart may create a new instance/session without changing canonical worker identity. |
| Machine / host metadata | Optional descriptive and operational metadata | Not the source of worker identity or authorization. |
| Environment | Declared execution environment such as local development, isolated runner or remote runtime | Environment label alone does not establish trust. |
| Owner / operator | Principal accountable for registering or managing the worker | Operator identity is separate from worker identity. |
| Credential set | Scoped, expiring credentials associated with worker identity and purpose | Credential possession alone does not grant arbitrary access. |
| Capability profile | Declared and verified ability set, versioned over time | Capabilities describe what the worker can technically do, not what it may do. |

The exact identity fields, registration ownership rules and versioning requirements must be reconciled with the authoritative data dictionary and CF source pack.

## 5. Worker registration lifecycle

Candidate lifecycle only. Exact state names and legal transitions remain SOURCE REQUIRED until the governing worker lifecycle contract is inspected.

| Candidate state | Meaning | Possible transitions | Guard / evidence |
| --- | --- | --- | --- |
| UNREGISTERED | No worker identity is registered | REGISTRATION_PENDING | Registration request is attributable. |
| REGISTRATION_PENDING | Registration request awaiting verification | TRUSTED, REJECTED, SUSPENDED | Identity proof and operator authority validated. |
| TRUSTED | Worker identity is accepted for defined scopes | ACTIVE, SUSPENDED, REVOKED | Trust evidence is current and not revoked. |
| ACTIVE | Worker is connected and eligible for scheduling consideration | IDLE, BUSY, DEGRADED, OFFLINE, SUSPENDED | Availability is runtime observation, not permission. |
| IDLE | Worker reports available capacity | BUSY, DEGRADED, OFFLINE, SUSPENDED | Scheduler still checks capability and authorization. |
| BUSY | Worker has one or more bounded assignments | IDLE, DEGRADED, OFFLINE, SUSPENDED | Active job scopes remain bounded. |
| DEGRADED | Worker is registered but health/capability confidence is reduced | ACTIVE, SUSPENDED, OFFLINE | Do not assign work requiring unavailable capability. |
| OFFLINE | No current heartbeat/session is observed | ACTIVE, SUSPENDED | Offline does not erase identity or trust history. |
| SUSPENDED | Worker is temporarily blocked from new assignments | TRUSTED, REVOKED | Suspension reason and authority are recorded. |
| REVOKED | Trust is withdrawn; credentials and access are invalidated | (terminal or new registration) | No automatic reactivation; explicit re-enrolment policy required. |
| REJECTED | Registration was not accepted | (terminal or resubmission) | Retain reason and evidence without granting access. |

## 6. Four separate capability dimensions

| Dimension | Question answered | Evidence / source | Must not be confused with |
| --- | --- | --- | --- |
| Declared capability | What does the worker claim it can do? | Worker-provided versioned manifest | Verified ability or permission |
| Verified capability | What has an accepted test/attestation demonstrated? | Verification result, test version, timestamp and evidence | Current availability |
| Available capability | What can the worker do right now, given health, load and resources? | Heartbeat, capacity and runtime telemetry | Authorization |
| Authorized capability | What is this worker permitted to do for this principal, job and scope? | Central authorization decision | Technical ability or self-declaration |

Scheduling eligibility is a derived check over trust state, verified capability, current availability, job constraints and centralized authorization. It must not be represented by a single self-reported boolean.

## 7. Capability manifest and verification candidate

| Manifest field | Candidate purpose | Validation / control |
| --- | --- | --- |
| manifest_id + version | Identify exact capability declaration version | Immutable version; changes create a new version. |
| worker_id | Bind declaration to registered worker principal | Must reference a valid worker identity. |
| capability_name | Named bounded function, e.g. video_render or transcription | Controlled vocabulary; exact taxonomy SOURCE REQUIRED. |
| capability_version | Worker implementation/version supporting the capability | Record build or toolchain identity where possible. |
| input/output contract refs | Describe accepted inputs and produced outputs | Must match versioned job/artifact contracts. |
| resource profile | Declare supported resource classes and limits | Declaration is not trusted until verified; numeric limits deferred. |
| network scope | Declare required destinations/protocol classes | Default deny; policy and sandbox enforce actual access. |
| filesystem scope | Declare permitted read/write locations or artifact handles | No unrestricted host filesystem access. |
| verification status | Record pending/pass/fail/stale disposition | Exact enum values SOURCE REQUIRED; retain test evidence. |
| verified_at / verifier | Record when and by whom verification occurred | Verification is version-bound and can expire or be revoked. |
| availability snapshot | Current health/load/resource snapshot | Ephemeral runtime observation; not a durable capability guarantee. |
| authorization reference | Central policy decision for this job/action | Never supplied or self-approved by worker. |

## 8. Trust establishment and re-verification

1. An accountable operator initiates registration for a specific intended execution scope.

1. The system creates or references an immutable worker identity independent of machine naming.

1. Registration proof is checked using the approved trust procedure; exact method is SOURCE REQUIRED.

1. Worker submits a versioned capability manifest; the manifest is treated as an untrusted declaration.

1. Verification runs in a bounded, controlled process and records test/build/evidence references.

1. Central policy determines whether the worker may receive a particular job and scope.

1. Runtime availability is monitored separately through authenticated heartbeats and capacity signals.

1. Material changes to worker build, environment, capabilities, credentials or trust evidence trigger the required re-verification policy.

1. Suspension/revocation invalidates relevant credentials and blocks new protected assignments; active work is reconciled safely.

No specific hardware attestation technology, certificate authority, identity provider or cloud provider is selected by this candidate.

## 9. Credential lifecycle and access scope

| Credential property | Candidate rule | Required negative test |
| --- | --- | --- |
| Short lifetime | Credentials expire automatically; lifetime set by risk and operational policy | Expired credential cannot claim a new job. |
| Narrow scope | Bind credential to worker identity, job/attempt, artifact handles and permitted actions | Credential cannot access unrelated job or artifact. |
| Revocability | Central authority can revoke credentials and invalidate sessions | Revoked credential is rejected at next protected operation. |
| Audience binding | Credential accepted only by intended service/resource | Token for one service cannot be replayed against another. |
| Purpose binding | Separate registration, heartbeat, job execution and artifact transfer scopes | Execution token cannot perform administrative registration. |
| Rotation | Renewal does not require sharing a permanent secret | Old credential becomes invalid after rotation window. |
| Secure storage | Use approved secret handling; never log token material | Logs, error messages and artifacts contain no credential secret. |
| Attribution | Credential issuance, renewal, use and revocation are auditable | Audit event identifies worker, scope, issuer and reason. |
| No privilege escalation | Worker cannot mint credentials or enlarge its own scope | Worker request for broader scope is denied. |

## 10. Bounded execution sandbox

| Boundary | Candidate default | What must be verified |
| --- | --- | --- |
| Filesystem | Allowlisted workspace/artifact paths only; no unrestricted host access | Path traversal, symlink escape and cross-job isolation tests. |
| Network | Deny by default; allow only approved destinations/protocols | Egress restrictions and DNS/IP bypass tests. |
| Credentials | Inject only short-lived credentials required for this attempt | No environment-wide or unrelated secret exposure. |
| Artifacts | Access only exact input/output artifact references assigned to job | Cross-tenant/workspace/job access denied. |
| Processes | Run with least privilege and controlled process tree | No privilege escalation or uncontrolled daemonization. |
| Resources | CPU, memory, disk, duration and concurrency bounded by job class | Numeric limits deferred pending workload measurement. |
| Admin functions | No general administrative or production control by default | Admin endpoints and secrets unavailable to worker. |
| QA/publishing | Separate principals and policy; worker cannot self-approve or self-publish | Direct publish and QA-bypass negative tests. |

Sandbox enforcement must be implemented at the execution boundary, not merely documented in the worker manifest.

## 11. Local and remote worker parity

| Concern | Local worker | Remote worker | Shared rule |
| --- | --- | --- | --- |
| Identity | Stable registered worker identity on the local runtime | Stable registered identity independent of host | Same trust and authorization model. |
| Availability | Depends on PC/runtime being online | Depends on remote runtime health | Availability is observed separately. |
| Filesystem | Local workspace access only within explicit allowlist | Remote filesystem access only within explicit allowlist | No unrestricted host access. |
| Network | Restricted local egress | Restricted remote egress | Default deny and explicit scope. |
| Credentials | Short-lived local job credentials | Short-lived remote job credentials | Same revocation and attribution rules. |
| Scheduling | Local-only job waits if local worker unavailable | Remote assignment only when policy and job scope permit | No automatic paid/cloud fallback. |
| Audit | Same lifecycle and attempt events | Same lifecycle and attempt events | Consistent traceability. |

The architecture may support remote workers, but this pack does not approve a remote provider, cloud deployment or paid infrastructure.

## 12. Worker/job assignment handshake

| Step | Interaction | Required checks |
| --- | --- | --- |
| 1. Candidate selection | Scheduler selects workers matching job capability requirements | Declared capability is not enough; use verified capability. |
| 2. Trust check | Registry returns worker trust state and credential status | Must be trusted, not suspended/revoked, and evidence current. |
| 3. Availability check | Worker reports current health/capacity | Do not dispatch when offline, degraded or over capacity. |
| 4. Authorization | Central authority evaluates worker + job + action + resource scope | Explicit allow required for protected operation. |
| 5. Lease/claim | WP-2 issues bounded assignment/lease | Stable job/attempt ID and fencing/lease generation. |
| 6. Credential issuance | Credential broker issues short-lived scoped credential | Only the minimum required scope and audience. |
| 7. Execution | Worker executes within sandbox | No self-expansion; all artifact/network/filesystem access scoped. |
| 8. Completion | Worker returns result/evidence references | WP-2 validates attempt; WP-4 validates artifact integrity. |
| 9. Credential closeout | Credential expires/revokes; worker releases lease | Audit completion and revoke temporary access. |

## 13. Candidate registry records

| Record family | Conceptual data | Owner boundary |
| --- | --- | --- |
| worker_record | worker_id, operator/owner ref, registration state, trust state, created/updated timestamps | WP-3 |
| worker_instance | instance/session ID, worker_id, runtime version, environment metadata, session status | WP-3 |
| worker_capability_manifest | manifest ID/version, capability declarations, contract refs, resource/network/filesystem profile | WP-3 |
| capability_verification | manifest version, verifier, test/build ref, outcome, evidence, verified_at, expiry/revocation | WP-3 |
| worker_heartbeat | worker/instance ref, observed time, health, capacity and availability snapshot | WP-3 |
| worker_credential_reference | credential ID/type, scope metadata, audience, expiry, issuer, revocation state; never plaintext secret | WP-3 / security boundary |
| worker_trust_event | registration, trust transition, verification, suspension, revocation and actor/reason | WP-3 |
| worker_job_binding | worker, job, attempt, lease generation and assignment scope | WP-2 owns assignment; WP-3 validates worker eligibility |

Exact physical tables and fields must be reconciled with WP-1's authoritative data dictionary. Do not create overlapping identity or authorization tables.

## 14. Security, privacy and abuse cases

| Threat / failure | Required control | Acceptance evidence |
| --- | --- | --- |
| Worker spoofs another worker ID | Authenticated identity proof and credential binding | Impersonation test denied. |
| Worker changes hostname and claims a new identity | Identity is independent of host metadata | Identity remains stable; host change is audited. |
| Worker overstates capabilities | Independent verification and version-bound evidence | Unverified capability cannot satisfy scheduling requirement. |
| Worker becomes compromised | Suspend/revoke trust and credentials; reconcile active attempts | Revocation propagation and denial evidence. |
| Credential stolen/replayed | Short lifetime, audience/scope binding, revocation and replay controls | Replay outside scope or after expiry denied. |
| Cross-job artifact access | Job-scoped artifact handles and authorization | Worker A cannot access Worker B's job artifacts. |
| Network exfiltration | Default-deny egress and monitored allowlist | Unapproved destination blocked and logged. |
| Filesystem escape | Sandbox and path canonicalization | Traversal/symlink escape denied. |
| Worker self-approves or publishes | Separate principals and central governance gates | Direct approval/publishing path blocked. |
| Stale verification | Version binding and expiry/re-verification policy | Changed build cannot use old verification silently. |

## 15. WP-3 acceptance test catalogue

| Test ID | Acceptance assertion | Evidence expected | Status |
| --- | --- | --- | --- |
| WP3-ID-01 | Worker identity remains stable across hostname/IP/runtime changes | Identity lifecycle test | NOT RUN |
| WP3-REG-01 | Unverified registration cannot receive protected jobs | Negative registration/dispatch test | NOT RUN |
| WP3-CAP-01 | Declared capability is not treated as verified capability | Scheduler negative test | NOT RUN |
| WP3-CAP-02 | Stale or failed capability verification blocks matching job assignment | Version/expiry test | NOT RUN |
| WP3-AVL-01 | Availability is separate from capability and authorization | State-combination test | NOT RUN |
| WP3-AUTH-01 | Worker cannot self-authorize or expand action scope | Authorization denial test | NOT RUN |
| WP3-CRED-01 | Expired/revoked credential cannot perform protected action | Credential lifecycle test | NOT RUN |
| WP3-CRED-02 | Credential is bound to worker, audience, job and attempt scope | Cross-scope replay test | NOT RUN |
| WP3-SBX-01 | Filesystem/network/artifact access is bounded | Sandbox escape and egress tests | NOT RUN |
| WP3-REV-01 | Revocation blocks new assignments and safely reconciles active work | Revocation/recovery evidence | NOT RUN |
| WP3-LOC-01 | Local-only job waits safely when local worker is unavailable | No remote fallback evidence | NOT RUN |
| WP3-AUD-01 | Trust and credential lifecycle changes are attributable | Audit trail inspection | NOT RUN |
| WP3-PAR-01 | Local and remote workers use equivalent trust rules | Contract parity test | NOT RUN |

## 16. Open items and deferred decisions

| Item | Current disposition | Closure trigger |
| --- | --- | --- |
| Exact worker/trust state enum values | SOURCE REQUIRED | Import governing worker lifecycle and CF source wording. |
| Registration proof/attestation method | DEFERRED / SOURCE REQUIRED | Threat model, local/remote operating constraints and owner review. |
| Identity provider / certificate authority | NOT SELECTED | Separate security/provider decision; no activation implied. |
| Credential token format and issuer | DEFERRED | Security design review and explicit owner approval. |
| Credential lifetime and renewal thresholds | DEFERRED | Risk-based policy and operational evidence. |
| Capability taxonomy and verification suite | CANDIDATE / SOURCE REQUIRED | Approved job types and versioned contract catalogue. |
| Numeric sandbox resource limits | DEFERRED | Measured workload classes and owner-approved limits. |
| Remote worker hosting provider | NOT SELECTED | Separate owner decision and cost/security review. |
| Revocation propagation SLO | DEFERRED | Threat model and measured architecture design. |
| Worker metadata retention | SOURCE REQUIRED | Authoritative retention/privacy policy. |

## 17. WP-3 acceptance gates

| Gate | Exit condition | Current status |
| --- | --- | --- |
| G1 — Identity | Identity independent of host and stable across runtime changes | ACCEPTED DIRECTION; implementation NOT VERIFIED |
| G2 — Registration/trust | Lifecycle, proof and revocation rules trace to authoritative source | DESIGN CANDIDATE / SOURCE REQUIRED |
| G3 — Capability separation | Declared, verified, available and authorized remain distinct | ACCEPTED DIRECTION; implementation NOT VERIFIED |
| G4 — Credentials | Short-lived, scoped, revocable and attributable | ACCEPTED DIRECTION; detailed contract SOURCE REQUIRED |
| G5 — Sandbox | Filesystem/network/credential/artifact boundaries enforceable | DESIGN CANDIDATE |
| G6 — WP-2 integration | Assignment, lease and attempt handshake consistent | NOT VERIFIED |
| G7 — Local/remote parity | Same trust and authorization rules; no implicit paid fallback | ACCEPTED DIRECTION; implementation NOT VERIFIED |
| G8 — Owner approval | Exact WP-3 contract reviewed and approved | NOT REQUESTED |

## 18. Draft WP-3 work order — not active

| Field | Draft definition |
| --- | --- |
| Objective | Implement worker registry, trust lifecycle, capability verification and scoped credential boundary. |
| Preconditions | Authoritative worker/CF sources verified; contract freeze approved; WP-2 assignment contract and WP-1 data model approved; separate implementation authorization issued. |
| Allowed after authorization | Implement approved worker records, registration/trust transitions, capability manifest/verification, heartbeat/availability, credential integration and scoped sandbox enforcement within file allowlist. |
| Forbidden without separate approval | Provider activation, cloud deployment, broad host access, permanent shared credentials, privilege escalation, paid services, publishing, broad Git operations or agent self-expansion. |
| Required outputs | Registry implementation, versioned capability contract, trust/credential audit events, sandbox tests, revocation evidence and traceability matrix. |
| Exit criteria | All mandatory WP-3 acceptance tests pass; local/remote parity and negative security tests demonstrated; independent read-only QA disposition recorded. |
| Rollback boundary | Revoke temporary credentials, disable affected worker registrations and restore prior compatible registry version using a tested procedure. |

## 19. Readiness decision

| Question | Current answer |
| --- | --- |
| Is worker trust direction accepted? | Yes — the core invariants are recorded as accepted. |
| Is this the final worker contract? | No — candidate only; source reconciliation remains necessary. |
| Are identity proof, credential format and exact state enums selected? | No — deliberately deferred or source-required. |
| Is worker registration or credential issuance authorized? | No. |
| Can this be used for design review? | Yes — reconcile against authoritative sources before freeze. |

Recommended next step: review this WP-3 candidate against the authoritative worker lifecycle, capability, credential and API/event sources. Then continue with WP-4 Artifact Registry, Storage Abstraction, Integrity & Transfer design.

END OF BATCH 07


## Source document metadata (preserved from DOCX)

- **Footer:** NEXTDECODE • P0 design candidate • Not frozen • Not implementation authorization

