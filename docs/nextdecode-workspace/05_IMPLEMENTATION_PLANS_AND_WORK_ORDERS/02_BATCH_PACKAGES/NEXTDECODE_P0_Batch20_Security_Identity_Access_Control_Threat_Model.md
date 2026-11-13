# P0 Security, Identity, Access Control & Threat Model Specification

NEXTDECODE Content OS | Batch 20 | Version 0.1 — Design Candidate

Status: Detailed security architecture candidate; formal owner freeze pending; implementation authorization not granted.

Purpose: define security boundaries and controls for identity, authentication, worker trust, access decisions, secrets, protected operations, auditability and threat-driven validation.

Scope boundary: documentation and design only. This batch does not configure identity providers, create credentials, change repository files, deploy infrastructure, activate paid services, run security scans or authorize production operations.

## 1. Authority and interpretation

| Classification | Meaning |
| --- | --- |
| Accepted baseline | Explicitly accepted owner decision or canonical standard; treated as a binding design constraint. |
| Derived control candidate | A proposed control that operationalizes the accepted baseline; requires detailed review/freeze. |
| Open decision | A detail not established by source records; it must not be silently assumed. |
| Illustrative example | Example role, permission, claim, route or policy expression; not a frozen production identifier. |

- ADR-005 establishes unique worker identity, scoped short-lived credentials and capability authorization.

- ADR-007 establishes centralized authorization; publishing adapters cannot bypass it; automatic publishing remains disabled pending a separate policy.

- ADR-008 establishes quality outcomes and hard-blocker behavior; BLOCKED cannot be bypassed by ordinary approval.

- ADR-009 establishes evidence-backed, use-specific rights enforcement.

- ADR-010 requires separate state machines for content, workflow, execution, review, approval, authorization and distribution.

- CF-22 establishes Option A: centralized authorization, default deny.

- CF-24 establishes the no-paid-services constraint; provider and operational choices are deferred.

- The source baseline does not freeze an identity provider, authentication protocol configuration, secret manager, cryptographic key service, network topology or final RBAC/ABAC policy catalogue.

## 2. Security objectives and non-negotiable invariants

| ID | Security invariant | Required consequence |
| --- | --- | --- |
| SEC-01 | Default deny | No access or protected action is allowed without an explicit applicable policy decision. |
| SEC-02 | Identity is authenticated, not self-asserted | Actor identity is derived from a trusted authentication context; request-body actor fields are not proof. |
| SEC-03 | Authorization is centralized | All protected operations, especially distribution/publishing, pass through the authoritative policy enforcement path. |
| SEC-04 | Approval ≠ authorization | Human approval does not independently grant permission to execute a protected action. |
| SEC-05 | Authorization is exact-bound | Bind action, resource, exact version, destination, policy version and validity window. |
| SEC-06 | Revalidate at execution | Check expiry, revocation, emergency pause, rights and policy immediately before side effect. |
| SEC-07 | Workers are untrusted execution principals | A worker receives only a bounded assignment and scoped capability; it does not own domain truth. |
| SEC-08 | Secrets are never ordinary data | No plaintext credentials in source, logs, normal tables, prompts or artifacts. |
| SEC-09 | Fail closed on uncertainty | Unknown rights, missing approval, missing authorization, integrity uncertainty or hard QA blockers deny protected use. |
| SEC-10 | Audit protected decisions | Record attributable decision and execution evidence with correlation and causation. |
| SEC-11 | Preserve user work | Security remediation must not trigger destructive repository or Git operations without explicit approval. |
| SEC-12 | No automatic public publishing | Automatic public publishing remains disabled pending a separately approved policy. |

## 3. Assets, actors and trust boundaries

| Category | Examples | Security concern |
| --- | --- | --- |
| Human principal | Workspace owner; authorized reviewer/operator | Account compromise, session theft, mistaken approval. |
| Application principal | API service, scheduler, outbox dispatcher, policy evaluator | Service identity, privilege creep, forged internal calls. |
| Worker principal | Local Shorts Studio worker, future remote worker | Credential theft, stale lease, malicious/compromised output. |
| External principal | Platform API, storage provider, webhook sender | Untrusted payloads, replay, provider compromise, ambiguous outcomes. |
| Content assets | Scripts, research, source media, exports, captions, thumbnails | Confidentiality, integrity, rights and prompt-injection risks. |
| Governance evidence | Rights records, QA results, approvals, authorizations | Tampering, stale evidence, incorrect version binding. |
| Operational assets | Credentials, signing keys, queue records, audit trail | Exfiltration, replay, denial of service, privilege escalation. |

Trust boundaries:

- TB-01 Human client → authenticated API: client input is untrusted until validated and authorized.

- TB-02 API → domain/policy services: service-to-service identity and explicit action/resource context required.

- TB-03 Control plane → worker: assignment is bounded, authenticated, time-limited and revocable.

- TB-04 Worker → artifact storage: worker receives only the minimum object and operation permissions required.

- TB-05 Control plane → external platform: external side effects require authorization and durable operation tracking.

- TB-06 Webhook/provider → callback receiver: payload is untrusted; verify authenticity, freshness, scope and replay protection.

- TB-07 Logs/events/analytics: data may be copied widely; minimize and redact sensitive payloads.

- TB-08 Local machine → cloud control plane (future): local-only files and secrets must not be implicitly uploaded.

## 4. Identity model

| Principal type | Candidate identity | Required controls |
| --- | --- | --- |
| Human owner | Stable internal actor ID linked to an authenticated account subject | Strong authentication; session expiry/revocation; recovery controls; owner actions audited. |
| Human reviewer | Stable actor ID plus explicit reviewer capability/scope | Approval authority limited to assigned scope; approval bound to exact version. |
| Service principal | Unique service identity per logical service/role | Non-interactive credentials; narrow scopes; rotation/revocation; no shared generic admin token. |
| Worker | Unique immutable worker identity and registration record | Short-lived scoped credentials; trust state; capability allowlist; assignment binding; revocation. |
| External provider account | Internal destination/account record plus provider mapping | No provider ID as canonical identity; credential reference protected; scope and account ownership verified. |
| Webhook sender | Configured sender identity and signing-key reference | Signature verification, timestamp tolerance, nonce/event dedup and source allowlist where applicable. |

Identity resolution rules:

- Never accept actor_id, requested_by, owner_id or role claims from request payload as authoritative identity.

- Resolve the authenticated principal from verified credentials/session and map it to internal actor/service/worker records.

- A worker identity is not equivalent to the human owner or service administrator.

- External provider account identifiers are scoped mappings, not internal principal identities.

- Identity linking, account recovery, MFA requirements and owner lockout recovery remain open policy decisions.

## 5. Authentication and session controls

| Control area | Candidate requirement | Status |
| --- | --- | --- |
| Authentication | Use a trusted authentication mechanism with verified identity; exact protocol/provider not selected. | Open implementation choice. |
| Strong authentication | Require stronger authentication for owner administration, credential changes and protected distribution decisions. | Candidate; MFA method/policy open. |
| Session lifecycle | Short-lived access context; revocation and re-authentication for sensitive actions. | Candidate; exact TTL open. |
| Credential storage | Store only protected verifier/reference; never log or expose raw secrets. | Required security principle. |
| Account recovery | Recovery must not silently bypass identity proof or owner authorization. | Open policy and threat review. |
| Session binding | Where practical, detect session/token reuse anomalies and invalidate compromised sessions. | Candidate. |
| Rate limiting | Throttle authentication, recovery, token issuance and sensitive command endpoints. | Candidate; thresholds open. |

Do not invent access-token lifetime, refresh-token lifetime, MFA product, OAuth scopes or provider settings. Freeze them only after a threat model and deployment model exist.

## 6. Authorization architecture

Authorization must be evaluated centrally. The enforcement point must be unavoidable for protected actions; individual UI controls or publishing adapters are not security boundaries.

| Component | Responsibility |
| --- | --- |
| Policy Enforcement Point (PEP) | Intercept protected command/operation; prevent execution until a valid decision is obtained. |
| Policy Decision Point (PDP) | Evaluate principal, action, resource/version, scope, destination, context and policy version. |
| Policy Information Points (PIPs) | Supply authoritative facts: identity, ownership, rights, QA, approval, worker trust, destination and emergency pause. |
| Policy Administration | Manage policy versions and approved changes; separate policy authoring from routine execution. |
| Decision record | Persist allow/deny, reason, policy version, evaluated resource/version, destination, actor and validity. |
| Execution-time guard | Recheck decision validity and revocation immediately before irreversible side effect. |

Illustrative authorization decision inputs:

principal = authenticated_actor_or_service
action = exact_action
resource = canonical_resource_id
resource_version = immutable_version_id
workspace_scope = verified_workspace_id
destination = exact_destination_id_or_null
approval_decision = current_exact_version_decision
rights_determination = use_specific_rights_state
quality_outcome = current_evaluation
policy_version = active_policy_version
emergency_pause = current_pause_state
requested_at = trusted_server_time

Illustrative only: field names and policy expression are not a frozen API or schema. The evaluator must obtain authoritative facts from trusted sources, not caller-supplied booleans.

## 7. Role, capability and attribute model

A pure role-based model is unlikely to express exact-version and destination-bound decisions by itself. Candidate direction: combine a small set of human/service roles with resource attributes, action capabilities and explicit policy conditions. The final model is open.

| Illustrative role/principal | Potential permitted scope | Explicitly not implied |
| --- | --- | --- |
| Workspace Owner | Workspace configuration, strategy, policy review and owner-reserved decisions | No automatic bypass of rights, quality, authorization or audit controls. |
| Content Editor | Create/edit draft content within assigned workspace/brand scope | No approval, credential administration or publishing authority by default. |
| Reviewer | Review assigned exact versions and submit review findings | No authorization or distribution execution merely by reviewing. |
| Approver | Record approval decision for permitted scope and exact version | Approval is not a publish authorization. |
| Operator | Inspect operations, resolve eligible failures and request retry | No privilege to override policy or suppress audit evidence. |
| Worker | Execute only assigned task/capability with bounded inputs and outputs | No broad workspace browsing, policy editing or autonomous distribution. |
| System Service | Perform a narrowly defined machine operation | No generic administrator or implicit owner authority. |

- Role names are illustrative, not approved product roles.

- Capabilities must be action-specific and constrained by resource, workspace, version, destination, time and policy.

- Avoid wildcard permissions such as admin:* unless explicitly threat-reviewed and owner-approved.

- Separate policy administration, credential administration, approval and execution where feasible; any single-owner exception must be explicitly documented.

## 8. Worker identity, trust and capability security

- Register each worker with a unique immutable worker identity; do not identify a worker solely by hostname, IP address or mutable display name.

- Issue scoped, short-lived credentials tied to the worker identity and permitted capability set.

- Authenticate worker-to-control-plane and worker-to-storage communications; use authenticated transport and protect credential material.

- Authorize every assignment against current worker trust state, capability, resource scope and policy.

- Bind assignment to a job, attempt, lease/fencing context, permitted inputs, output contract and expiry.

- Do not allow a worker to widen its own capabilities or self-approve its result.

- Support credential revocation and worker quarantine; prevent new assignments after revocation/quarantine.

- Treat worker-produced files, metadata, logs and callback payloads as untrusted until validated.

- Validate output paths, file types, size limits, checksums, manifests and provenance before registration or downstream use.

- Reject stale results from expired or superseded attempts; retain evidence for investigation.

Open worker-security details: enrollment/bootstrap, attestation level, credential issuer, rotation cadence, mutual TLS requirement, local machine trust, capability vocabulary, sandbox/isolation model and emergency revocation propagation.

## 9. Secrets, keys and sensitive configuration

| Secret class | Storage/handling rule | Prohibited pattern |
| --- | --- | --- |
| Human/provider credentials | Secret-manager reference or approved protected vault; least privilege and rotation. | Plaintext in database, .env committed to Git, prompt or logs. |
| Worker credential | Short-lived scoped credential; store hash/reference and metadata only. | Long-lived shared worker token. |
| Signing key | Protected key service or secret store; version and rotate; restrict signing use. | Embedding private key in worker package or source. |
| Webhook secret | Per-sender secret/key reference; verify signature and freshness. | Accepting unsigned callbacks as trusted. |
| Encryption key | Managed key lifecycle with access separation and recovery plan. | Hard-coded key or same key reused indiscriminately. |
| Local development secret | Ignored local configuration, restrictive filesystem permissions, redaction. | Committing .env, backup secrets or copied credential dumps. |

- Secret scanning is a proposed CI/repository control; it has not been run in this documentation batch.

- Rotation and revocation procedures must include downstream workers, callbacks, storage grants and provider sessions.

- Backups containing secrets require the same access controls and retention discipline as primary stores.

- Exact key management service and paid/free service choices remain open under CF-24.

## 10. Protected publishing and external side effects

1. A distribution request identifies the exact package version, destination/account, requested action and correlation context.

1. The centralized authorization path evaluates identity, workspace scope, rights, QA, exact-version approval, policy version, destination and emergency pause.

1. A durable DistributionOperation is created before the external side effect; it references the exact authorization decision.

1. Immediately before the side effect, the adapter revalidates expiry, revocation, policy and emergency pause.

1. The adapter performs only the authorized operation and records the external request/reference and observed response.

1. If outcome is unknown, reconcile with the external platform before retry; never assume failure or blindly repeat a potentially successful publish.

1. Record confirmed external outcome separately from command acceptance and local execution completion.

Automatic public publishing remains disabled. No generic approved=true flag, worker capability or adapter-local check can substitute for centralized authorization.

## 11. Input validation, content and prompt-injection risks

- Validate all API, webhook, worker and imported metadata against versioned schemas; reject unexpected or malformed fields where safe.

- Treat research pages, comments, uploaded documents, captions, transcripts, metadata and generated content as untrusted data.

- Instructions embedded in external content must not override system policy, tool permissions, owner decisions or execution authorization.

- Separate data from instructions in agent prompts and tool interfaces; pass only the minimum required context.

- Use allowlisted tools/actions and constrained arguments for agents; do not expose arbitrary shell, filesystem or network access by default.

- Validate file paths against an approved workspace boundary; defend against traversal, symlink escape and archive extraction abuse.

- Apply upload size/type limits, content inspection and malware scanning where available; exact scanner/provider remains open.

- Escape output for the target context (HTML, SQL, shell, Markdown, platform API) and use parameterized database queries.

- Prevent SSRF by restricting outbound destinations and validating redirects/DNS/IP ranges; exact network policy open.

- Rate-limit expensive generation, research, transfer and callback operations to reduce abuse and cost-exhaustion risk.

## 12. Audit, logging and security monitoring

| Evidence type | Minimum candidate fields |
| --- | --- |
| Authentication event | event_id, principal_ref, event_type, occurred_at, result, source context, correlation_id |
| Authorization decision | decision_id, principal_ref, action, resource/version, destination, policy_version, allow/deny, reason, evaluated_at, expiry |
| Approval decision | decision_id, approver_ref, exact_version_ref, outcome, reason, decided_at |
| Worker assignment | worker_id, job_id, attempt_id, lease_ref, capability, scope, issued_at, expiry |
| Credential lifecycle | credential_ref, principal_ref, issue/rotate/revoke event, actor, time; never secret value |
| Distribution operation | operation_id, package/version, destination, authorization_ref, external_ref, observed outcome, reconciliation evidence |
| Administrative change | actor, action, before/after references, reason, policy/config version, time |
| Security incident | incident_id, severity, affected principal/resource, detection source, containment and resolution evidence |

- Use append-oriented audit evidence with restricted write/delete permissions.

- Do not log passwords, access tokens, refresh tokens, signing keys, full sensitive payloads or unnecessary personal data.

- Correlate command, event, workflow run, job, attempt, artifact and external operation with correlation_id and causation_id.

- Define alerting for repeated denials, unusual credential issuance, worker trust changes, authorization bypass attempts, lease anomalies and suspicious publish outcomes.

- Audit immutability/tamper-evidence mechanism, log retention and alert thresholds remain open.

## 13. Threat model methodology

This is a first-pass threat catalogue using assets, actors, boundaries, attack paths and mitigations. Severity is provisional and must be validated against the actual deployment, data classification and exposure.

| Threat ID | Threat / attack path | Impact | Candidate mitigation |
| --- | --- | --- | --- |
| T-01 | Owner account or session compromise | Unauthorized access, approvals or configuration changes | Strong authentication, session revocation, sensitive-action re-authentication, alerts and audit. |
| T-02 | Forged actor_id/requested_by in API body | Privilege impersonation | Derive identity from authenticated context; ignore caller identity claims. |
| T-03 | Worker credential theft | Unauthorized job execution or artifact access | Short-lived scoped credentials, rotation, revocation, worker quarantine. |
| T-04 | Worker capability escalation | Access to unrelated resources or operations | Central capability evaluation; assignment-bound scope; deny unknown capability. |
| T-05 | Publishing adapter bypasses central gate | Unapproved public side effect | Mandatory PEP; adapter cannot publish without valid authorization reference; negative integration tests. |
| T-06 | Approval reused for changed version | Unreviewed content distributed | Exact immutable version binding; stale approval rejection. |
| T-07 | Authorization replay to different destination | Wrong account/channel receives content | Bind destination/action/version/policy/time; nonce/idempotency; execution-time recheck. |
| T-08 | Rights evidence absent or ambiguous | Copyright/privacy/legal exposure | Fail closed; use-specific rights determination; evidence provenance. |
| T-09 | BLOCKED QA downgraded or ignored | Unsafe/defective content proceeds | Central hard-block enforcement; append-only QA outcomes; test every path. |
| T-10 | Prompt injection in research/upload | Agent leaks data or invokes unauthorized tools | Untrusted-data boundary, tool allowlists, scoped context and independent policy enforcement. |
| T-11 | Webhook spoof/replay | Forged status or duplicate action | Signature verification, freshness window, nonce/event dedup and source identity. |
| T-12 | Path traversal or malicious archive | Local file disclosure/overwrite or code execution | Workspace path confinement, safe extraction, type/size validation and sandboxing. |
| T-13 | Secret committed or logged | Credential compromise | Secret scanning, redaction, access control, rotation and incident procedure. |
| T-14 | SSRF via URL ingestion | Internal service/metadata access | Outbound allowlist, DNS/IP validation, redirect controls and egress restrictions. |
| T-15 | Database injection or overbroad query | Data disclosure or mutation | Parameterized queries, least-privilege DB roles, validation and query review. |
| T-16 | Outbox/inbox duplicate delivery | Duplicate downstream effects | Transactional outbox, inbox uniqueness and idempotent handlers. |
| T-17 | Stale worker result/lease race | Incorrect state overwrite or duplicate operation | Fencing token, expected state version, attempt binding and stale-result rejection. |
| T-18 | Audit evidence alteration | Loss of accountability | Append-only permissions, tamper-evidence, independent backup and restricted administration. |
| T-19 | Denial of service/cost exhaustion | Service unavailability or unexpected spend | Rate limits, quotas, bounded retries, concurrency limits and kill switch. |
| T-20 | Cross-workspace reference/IDOR | Unauthorized access to another scope | Scope checks on every object lookup; composite constraints; negative tests. |
| T-21 | Backup exposure | Bulk disclosure of content/secrets | Encryption, least privilege, restore controls and retention policy. |
| T-22 | External publish outcome unknown | Duplicate or unintended publication on retry | Persist operation before call; reconcile provider state; no blind retry. |

## 14. Incident response and emergency controls

| Phase | Candidate response |
| --- | --- |
| Detect | Alert on credential misuse, repeated policy denials, unexpected public operation, suspicious worker behavior or integrity failure. |
| Contain | Revoke affected credentials, quarantine worker, pause relevant destination/action and block new assignments. |
| Preserve | Retain audit, operation, attempt, artifact and callback evidence; avoid destructive cleanup. |
| Investigate | Trace correlation/causation chain; identify affected versions, destinations, principals and time window. |
| Recover | Rotate secrets, restore trusted configuration, revalidate artifacts/rights and reconcile external side effects. |
| Notify | Use approved incident and notification policy; legal/regulatory requirements remain to be determined. |
| Review | Record root cause, control gap, corrective action and regression tests. |

Emergency pause must be centrally enforced and checked at execution time. Its authority, scope, propagation latency, override conditions and recovery approval are open decisions; no implementation is implied here.

## 15. Security acceptance and failure-injection tests

| Test ID | Scenario | Acceptance oracle |
| --- | --- | --- |
| SEC-T01 | Unauthenticated request | Protected API command is denied and no state change occurs. |
| SEC-T02 | Forged actor identity | Body-supplied actor_id cannot impersonate another principal. |
| SEC-T03 | Cross-workspace IDOR | A valid ID from another workspace is denied without leaking protected data. |
| SEC-T04 | Default deny | Unknown action, role, capability or policy version produces deny. |
| SEC-T05 | Approval is not authorization | APPROVED record alone cannot invoke distribution. |
| SEC-T06 | Exact version binding | Approval for version N cannot authorize version N+1. |
| SEC-T07 | Destination binding | Authorization for destination A cannot be reused for destination B. |
| SEC-T08 | Expired/revoked decision | Execution-time check denies an expired or revoked authorization. |
| SEC-T09 | Emergency pause | Protected operation is blocked while applicable pause is active. |
| SEC-T10 | Rights unknown | UNKNOWN/PENDING_REVIEW rights state blocks protected use. |
| SEC-T11 | QA hard blocker | BLOCKED outcome cannot be overridden by ordinary approval. |
| SEC-T12 | Worker credential expiry | Expired credential prevents assignment and execution. |
| SEC-T13 | Worker revocation | Revoked worker cannot claim new work or submit accepted results. |
| SEC-T14 | Capability boundary | Worker cannot access unassigned artifact, resource or operation. |
| SEC-T15 | Stale lease/fencing | Old worker attempt cannot commit after lease expiry/reassignment. |
| SEC-T16 | Webhook forgery/replay | Invalid signature or replayed event is rejected/deduplicated. |
| SEC-T17 | Secret redaction | Test tokens/keys do not appear in logs, errors, audit payloads or generated artifacts. |
| SEC-T18 | Prompt injection | Malicious instructions in source material cannot expand tool authority or override policy. |
| SEC-T19 | Path traversal | Traversal/symlink/archive attacks cannot escape approved workspace boundary. |
| SEC-T20 | SSRF | Disallowed internal/private destinations are blocked by outbound policy. |
| SEC-T21 | Duplicate outbox delivery | Repeated event delivery causes one protected downstream effect. |
| SEC-T22 | Unknown external outcome | System reconciles before retry and does not blindly repeat publish. |
| SEC-T23 | Audit continuity | Denied and allowed sensitive actions have attributable evidence. |
| SEC-T24 | Emergency credential response | Revocation/rotation blocks the compromised credential within the approved propagation target. |
| SEC-T25 | Backup access | Unauthorized principal cannot access backup material or restore secrets. |
| SEC-T26 | Rate limiting | Repeated authentication, callback and expensive operation attempts are bounded. |

## 16. Security operations and ownership matrix

| Control domain | Accountable logical owner | Supporting responsibilities |
| --- | --- | --- |
| Human identity and account lifecycle | Workspace & Control Center / identity boundary | Authentication integration, session policy, recovery and owner audit. |
| Central authorization | Central Authorization domain | Policy evaluation, decision records, revocation and emergency pause. |
| Worker trust | Worker Registry | Enrollment, credentials, capabilities, quarantine and assignment checks. |
| Secrets | Platform/security operations | Vault/key integration, rotation, access and incident response. |
| Content rights and QA | Governance / Quality domains | Evidence, determinations and hard-block facts supplied to PDP. |
| Distribution execution | Distribution Studio | Enforce authorization; record external operation; reconcile unknown outcomes. |
| Audit | Cross-cutting platform control | Append-only evidence, correlation, access and retention. |
| Application/API security | Each domain owner under common standards | Validation, scope checks, safe errors and least privilege. |

Logical ownership does not require separate microservices. A single-owner deployment may implement these boundaries within a modular application, provided the enforcement boundaries remain testable.

## 17. Open security decisions

| ID | Decision required |
| --- | --- |
| SEC-O01 | Identity provider, authentication protocol, account linking and recovery process. |
| SEC-O02 | MFA requirements and re-authentication triggers for owner, approval and distribution actions. |
| SEC-O03 | Human roles, service principals, worker principal taxonomy and exact permission catalogue. |
| SEC-O04 | RBAC/ABAC/capability policy composition and policy authoring governance. |
| SEC-O05 | Access-token/session TTL, refresh, revocation and device/session inventory. |
| SEC-O06 | Worker enrollment, bootstrap trust, attestation, mutual TLS and local machine trust. |
| SEC-O07 | Credential issuer, secret manager, key management service and rotation cadence. |
| SEC-O08 | Network segmentation, egress policy, webhook ingress and private service exposure. |
| SEC-O09 | Data classification taxonomy, sensitive content handling and workspace isolation enforcement. |
| SEC-O10 | Audit tamper-evidence, retention, access and independent backup. |
| SEC-O11 | Emergency pause authority, propagation target, scope and recovery procedure. |
| SEC-O12 | Security incident severity, response owner, notification and legal review. |
| SEC-O13 | Malware scanning, file inspection and sandbox technology. |
| SEC-O14 | Threat-model review against final deployment and external platform integration. |
| SEC-O15 | Security test automation, CI gates, vulnerability scanning and dependency policy. |
| SEC-O16 | Privacy, retention, deletion, legal hold and backup lifecycle. |

## 18. Freeze and implementation gate checklist

- Trace each security control to an accepted ADR/CF, API command, event, state machine and persistence record.

- Confirm centralized authorization is the only permitted path for protected actions and that all adapters are covered.

- Approve the principal taxonomy, identity lifecycle and exact policy model.

- Approve worker enrollment, credential lifecycle, capability enforcement and stale-result fencing.

- Approve secrets/key management, network boundaries, data classification and audit protections.

- Resolve emergency pause and incident response ownership.

- Run a deployment-specific threat-model review before selecting concrete products or configurations.

- Define security acceptance evidence and independent QA ownership.

- Record owner disposition for open decisions; silence or continuing documentation is not approval.

- Obtain separate explicit implementation authorization before repository changes, credential creation, deployment or operational tests.

## 19. Final status and boundary

Batch 20 provides a security architecture and threat-model candidate. It does not claim that authentication, authorization, secret management, worker trust, audit protection or security testing has been implemented or verified.

Current gate: security design candidate → deployment-specific threat review → owner decision and contract freeze → separate explicit implementation authorization.

Safety invariant: no paid services, credential provisioning, cloud deployment, destructive repository operation, production generation, upload or public publishing is authorized by this document.


## Source document metadata (preserved from DOCX)

- **Header:** NEXTDECODE CONTENT OS  |  P0 ARCHITECTURE SERIES
- **Footer:** Batch 20 — Security, Identity, Access Control & Threat Model  |  Design candidate — not implementation authorization

