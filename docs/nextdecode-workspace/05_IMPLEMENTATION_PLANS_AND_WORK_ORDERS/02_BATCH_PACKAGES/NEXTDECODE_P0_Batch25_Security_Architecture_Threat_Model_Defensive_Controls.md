# P0 Security Architecture, Threat Modelling & Defensive Controls Specification

NEXTDECODE Content OS — Batch 25

Document class: Detailed architecture and security-control specification candidate

Status: DRAFT FOR OWNER REVIEW • NOT A CONTRACT FREEZE • NOT IMPLEMENTATION AUTHORIZATION

Prepared: 1 November 2026

Scope: Security architecture and defensive controls for the initial single-owner Creator Mode, its local worker and bounded Shorts Studio integration, and the longer-term modular Content OS.

## Document control and authority

| Field | Value |
| --- | --- |
| Purpose | Define security boundaries, threat scenarios, control requirements, verification evidence and owner decisions before implementation. |
| Authority baseline | Accepted ADR-001–ADR-010 and CF-01–CF-24 as recorded; Artifact 08 reconciliation candidate v1.1 supplements but does not supersede v1.0. |
| Decision status | Preserve accepted architecture and security invariants. Detailed mechanisms, cryptographic choices, retention, hosting and numeric limits remain open unless explicitly accepted elsewhere. |
| Related specifications | Batch 17 state machines; Batch 18 API/event/schema; Batch 21 observability; Batch 22 configuration/release; Batch 23 backup/DR; Batch 24 performance/capacity. |
| Non-goals | No penetration-test claim, security certification, production audit, code review, deployment, provider activation or implementation authorization. |

Authority rule: accepted decisions remain authoritative. Candidate controls in this document are proposals for owner review, not silently accepted policy. Do not infer approval from silence, document delivery or a generic “next”.

## 1. Executive summary

NEXTDECODE security must be enforced centrally across the control plane, workflow engine, workers, artifact lifecycle, governance checks and distribution adapters. Security is not a UI-only concern and must not depend on a worker, plugin, publisher or user interface behaving correctly.

The product begins as a single-owner, one-workspace Creator Mode, but it still handles valuable credentials, private research, source assets, unpublished content, approval evidence, rights records and potentially consequential external actions. Single-owner scope reduces some multi-user risks; it does not remove threats from compromised credentials, malicious files, prompt injection, vulnerable dependencies, local machine compromise, unsafe automation or external-provider ambiguity.

- Default deny for protected actions; enforce authorization at the server-side policy boundary and again at execution time.

- Separate authentication, identity, scope, capability, approval, authorization, execution and confirmed external outcome.

- Treat external content, uploaded files, tool outputs, model outputs, web pages and worker messages as untrusted data.

- Keep secrets out of source code, logs, artifacts, prompts, reports and diagnostic bundles; use scoped, revocable credentials.

- Preserve local-first/free-first and the ₹0 initial spend target; no paid security product or provider is authorized.

- Fail closed on unknown rights, missing approval, stale authorization, integrity failure or uncertain security state.

- Security controls must preserve evidence, support recovery and avoid destructive operations on user work.

## 2. Security objectives and protected assets

| Asset class | Examples | Security objectives |
| --- | --- | --- |
| Identity and credentials | Owner identity, session tokens, API keys, OAuth refresh tokens, worker credentials, signing keys. | Confidentiality, integrity, least privilege, revocation and rotation. |
| Content and knowledge | Drafts, scripts, plans, research notes, source documents, unpublished media. | Confidentiality, integrity, scope isolation and controlled disclosure. |
| Artifacts and provenance | Source assets, derivatives, manifests, checksums, lineage, immutable versions. | Integrity, authenticity, traceability and recoverability. |
| Governance records | Rights evidence, QA outcomes, reviews, approvals, authorization decisions, audit events. | Integrity, attribution, exact-version binding and non-repudiable operational evidence where feasible. |
| Workflow state | Definitions, runs, tasks, jobs, attempts, leases, queue records and events. | Integrity, consistency, availability and replay safety. |
| External accounts and actions | Social accounts, publishing tokens, platform APIs, upload destinations. | Least privilege, explicit authorization, rate limits and outcome reconciliation. |
| System configuration | Policy versions, feature flags, environment settings, deployment configuration. | Integrity, controlled change and safe defaults. |
| Operational evidence | Logs, traces, incident records, backup/restore records and diagnostics. | Confidentiality, integrity, redaction and retention control. |

## 3. Security principles and mandatory invariants

| ID | Principle / invariant | Required interpretation |
| --- | --- | --- |
| SEC-I01 | Default deny | Absence, ambiguity, stale evidence or policy failure never grants permission. |
| SEC-I02 | Central authorization | Protected actions are authorized by a central policy boundary; adapters cannot bypass it. |
| SEC-I03 | Separation of decisions | Authentication ≠ identity ≠ scope ≠ capability ≠ approval ≠ authorization ≠ execution ≠ external outcome. |
| SEC-I04 | Exact binding | Protected authorization binds action, resource, immutable version, destination, policy version, actor/scope and time validity. |
| SEC-I05 | Execution-time revalidation | Expiry, revocation, emergency pause, policy change and resource/version change are checked at execution. |
| SEC-I06 | Least privilege | Every actor, worker, token and integration receives only the minimum scope and lifetime required. |
| SEC-I07 | Fail closed | Unknown rights, missing approval, invalid integrity, unavailable policy decision or uncertain security state blocks protected work. |
| SEC-I08 | Untrusted input | Files, webpages, tool outputs, agent outputs, model responses and external callbacks are untrusted until validated. |
| SEC-I09 | Secrets hygiene | Secrets are never committed, logged, embedded in artifacts or exposed in diagnostic output. |
| SEC-I10 | Auditability | Security-sensitive decisions and changes are attributable, timestamped and correlated. |
| SEC-I11 | Immutable evidence | Security/approval/rights evidence is versioned and cannot be silently overwritten. |
| SEC-I12 | Safe recovery | Restore, replay and retries must not resurrect revoked credentials or repeat protected external side effects. |
| SEC-I13 | Human publishing control | Human approval is required before critical publishing; automatic public publishing remains disabled pending separate policy. |
| SEC-I14 | Preserve user work | No destructive cleanup/reset/overwrite or broad Git action without explicit owner approval. |
| SEC-I15 | Local-first/free-first | No paid service, external security product or cloud capability is activated without separate explicit approval. |

## 4. System trust boundaries

| Boundary | Crossing / data flow | Security requirement |
| --- | --- | --- |
| Owner interface → control plane | Sessions, commands, files, review and settings. | Authenticate actor; validate CSRF/origin where relevant; enforce scope and server-side policy. |
| Control plane → database/queue | Entities, versions, workflow state, commands, events and leases. | Parameterized queries; transactional consistency; least-privileged service identity; integrity controls. |
| Control plane → worker | Task assignment, capability requirements, scoped credentials and artifacts. | Mutual identity verification; signed/validated assignment; short-lived scoped credentials; replay protection. |
| Worker → control plane | Progress, result, heartbeat, logs, artifact references and completion claims. | Authenticate worker; validate schema, assignment, lease, attempt and artifact provenance. |
| Worker → local machine/filesystem | Source media, scratch paths, subprocesses, caches and outputs. | Sandbox/path confinement; safe subprocess invocation; bounded resources; no arbitrary path access. |
| Content OS → Shorts Studio adapter | Validated input contract, execution request, output manifest and status. | Bounded adapter; schema validation; no direct publisher bypass; preserve provenance. |
| System → external providers | Search, AI/model, storage, social/platform APIs and callbacks. | Explicit provider allowlist/approval; scoped credentials; timeouts, quotas, redaction and outcome reconciliation. |
| External content → model/agent | Webpages, documents, prompts, captions, transcripts and metadata. | Treat as data, not instructions; isolate secrets and privileged tool context; validate outputs. |
| Distribution adapter → platform | Exact artifact/version, destination, approval and authorization. | Central authorization; execution-time checks; private/non-public defaults; no bypass. |
| Backup/restore boundary | Database, artifacts, secrets/configuration and audit evidence. | Encrypt where supported; restrict access; validate integrity; prevent revoked credentials from being reactivated. |

## 5. Threat modelling method

Use a repeatable threat model for each module, API, worker capability, data store, adapter and external integration. Record assets, actor, entry point, trust boundary, preconditions, attack path, impact, existing control, residual risk, test oracle, owner and status.

- Use STRIDE as a coverage aid: spoofing, tampering, repudiation, information disclosure, denial of service and elevation of privilege.

- Assess business impact separately: unauthorized publishing, rights violation, content leakage, evidence tampering, account takeover, data loss and financial exposure.

- Rate likelihood and impact with a documented scale; do not present a numeric risk score as objective without agreed criteria.

- Include abuse cases and benign failure cases: duplicate events, stale authorization, expired lease, provider timeout, malicious media and prompt injection.

- Threat models must be revisited when a new tool, provider, worker capability, data class, external action or trust boundary is added.

## 6. Threat register

| ID | Threat / abuse case | Potential impact | Required defensive control / test |
| --- | --- | --- | --- |
| TH-01 | Stolen owner session or refresh token | Account takeover, private content exposure, unauthorized actions. | Session expiry/revocation, secure storage, re-authentication for critical actions; token theft simulation. |
| TH-02 | Unauthenticated or weakly authenticated API endpoint | Unauthorized job creation, resource exhaustion or state mutation. | Authentication on every non-public route; route inventory and negative authorization tests. |
| TH-03 | Cross-scope identifier substitution / IDOR | Read or mutation of another workspace/resource if scope expands. | Server-side ownership/scope checks on every object access; tampered-ID tests. |
| TH-04 | Worker impersonation or replay | Forged results, task theft, unauthorized capability execution. | Unique worker identity, short-lived scoped credentials, assignment nonce/lease validation; replay tests. |
| TH-05 | Over-privileged worker or agent | Credential exfiltration or actions outside task scope. | Capability allowlist, isolated execution, no ambient secrets, expiry/revocation; capability boundary tests. |
| TH-06 | Prompt injection in webpages/files/transcripts | Agent follows attacker instructions or leaks privileged context. | Treat content as untrusted data; isolate tools/secrets; output validation; injection test corpus. |
| TH-07 | Malicious uploaded media/document | Parser exploit, path traversal, decompression bomb, resource exhaustion. | Type/size validation, safe parsers, sandbox, resource limits, quarantine; malformed-file tests. |
| TH-08 | Path traversal / unsafe filenames | Overwrite or read arbitrary local files. | Canonical path confinement, safe filename handling, symlink checks; traversal test set. |
| TH-09 | Command injection via metadata or filenames | Arbitrary process execution on local worker. | Argument arrays, no shell interpolation, strict input validation; metacharacter tests. |
| TH-10 | Secrets in logs, traces, artifacts or prompts | Credential compromise and private-data exposure. | Central redaction, secret scanning, allowlisted diagnostic fields; seeded-secret tests. |
| TH-11 | Dependency or supply-chain compromise | Malicious package/build artifact executes with application privileges. | Pinned/locked dependencies, provenance, vulnerability review and controlled updates; dependency audit. |
| TH-12 | Database injection or unsafe query construction | Data disclosure or tampering. | Parameterized queries, least privilege, validation; injection tests. |
| TH-13 | Queue/event tampering or duplicate replay | Forged transitions, repeated side effects or state corruption. | Authenticated producers, schema/version validation, idempotency, immutable audit; replay tests. |
| TH-14 | Artifact substitution or checksum bypass | Wrong content rendered/reviewed/published. | Immutable version binding, checksum verification, manifest validation; substitution tests. |
| TH-15 | Approval/authorization confusion | Approval treated as permission to publish. | Separate records and central authorization; exact-version/destination binding tests. |
| TH-16 | Stale authorization or revoked approval | Previously allowed action executes after revocation or policy change. | Execution-time revalidation and emergency pause; time-of-check/time-of-use tests. |
| TH-17 | Direct adapter or script bypass | Publisher or pipeline avoids central gates. | Central enforcement at every protected entry point; direct-entry negative tests. |
| TH-18 | Public destination default or destination substitution | Unintended public release or wrong channel. | Explicit destination, non-public defaults, no hardcoded public privacy; destination mutation tests. |
| TH-19 | External timeout with unknown outcome | Duplicate publish/upload or false success on retry. | External-operation state and reconciliation before retry; ambiguous-outcome simulation. |
| TH-20 | Denial of service / resource exhaustion | Control plane unavailable, disk full, runaway costs. | Admission control, quotas, backpressure, bounded retries and resource limits; stress tests. |
| TH-21 | Webhook spoofing or callback replay | Forged external status or workflow transition. | Signature verification, timestamp/nonce/replay window, schema and source validation. |
| TH-22 | Backup theft or malicious restore | Sensitive data exposure or reactivation of compromised credentials. | Access restrictions, encryption, restore validation, credential rotation/revocation procedure. |
| TH-23 | Audit log tampering or deletion | Loss of incident evidence and accountability. | Append-only/controlled audit store, integrity checks, restricted deletion; tamper tests. |
| TH-24 | Insider or accidental destructive operation | Loss of source assets, records or repository work. | Least privilege, explicit confirmation, backups, protected paths and change audit. |
| TH-25 | Sensitive telemetry or analytics leakage | Private content or credentials exposed through dashboards/logs. | Data minimization, redaction, access control and retention; privacy review. |
| TH-26 | Race condition during concurrent approval/publish | Stale state or duplicate external action. | Version checks, transaction boundaries, idempotency and single-flight execution; race tests. |

## 7. Identity, authentication and session security

- All non-public APIs and administrative actions require authenticated identity. Public health/readiness endpoints, if any, expose only minimal non-sensitive information.

- Actor identity must be derived from verified authentication context, not trusted from caller-supplied actor fields.

- Use secure session handling: protected cookies where browser sessions are used, secure transport, appropriate SameSite/HttpOnly/Secure attributes, CSRF protection for cookie-authenticated state changes and bounded session lifetime.

- Require re-authentication or step-up confirmation for high-impact actions such as credential changes, authorization policy changes, destructive data operations and any future publishing authorization.

- Support session/token revocation and incident response for suspected compromise.

- Do not store plaintext passwords or long-lived tokens in browser local storage or source-controlled configuration.

- Record authentication success/failure and sensitive account changes without logging credentials or unnecessary personal data.

## 8. Authorization architecture

Authorization is a distinct central decision. UI visibility, role labels, approval records and adapter-local checks are not sufficient. Every protected operation must be checked at the authoritative server-side boundary and revalidated immediately before execution.

| Authorization element | Required binding / validation |
| --- | --- |
| Actor | Authenticated owner or explicitly registered service/worker identity; never caller-asserted identity alone. |
| Scope | Workspace, brand, studio, platform account and resource ownership as applicable. |
| Action | Specific operation, not a broad generic permission. |
| Resource | Canonical entity and immutable version where relevant. |
| Destination | Exact platform/channel/account and privacy/delivery mode. |
| Approval | Valid, attributable approval for the exact governed object/version; approval does not itself authorize. |
| Policy | Policy version, ruleset and decision evidence used at decision time. |
| Time | Issued-at, expiry, revocation state and execution-time validity. |
| Emergency control | Global or scoped pause/deny control checked before side effect. |
| Result | Allow/deny with reason, correlation ID and auditable decision record. |

## 9. Worker identity, trust and capability security

| Control area | Requirement candidate | Verification |
| --- | --- | --- |
| Unique identity | Each worker instance has unique identity; no shared static worker secret across a fleet. | Attempt impersonation and identity collision. |
| Credential lifetime | Short-lived, scoped credentials; refresh/revocation controlled by authority. | Expired/revoked token rejection. |
| Capability catalogue | Explicit allowlisted task types, resource access and external connectivity. | Attempt unlisted task/capability. |
| Assignment binding | Worker validates task ID, attempt, lease, scope, input version and expiry. | Replay/stale assignment tests. |
| Isolation | Separate worker process/user/container boundary as feasible; restrict filesystem and network access. | Escape/path/network tests appropriate to chosen runtime. |
| Result validation | Control plane validates schema, provenance, lease ownership and artifact integrity. | Forged result and wrong-worker result tests. |
| Revocation | Compromised/offline worker can be disabled; outstanding credentials expire/revoke. | Revocation propagation and stale worker test. |
| Secrets exposure | Worker receives only task-scoped secrets, preferably via secure delivery and not environment dumps. | Seeded-secret and process-inspection review. |

Exact worker isolation technology, credential issuer, rotation interval and capability catalogue remain open decisions. Do not infer a container, cloud agent or paid secret manager selection.

## 10. Secrets, keys and cryptographic controls

- Keep secrets out of Git, source files, sample fixtures, logs, screenshots, model prompts, artifacts and support bundles.

- Use environment-specific secret injection for local development and deployment; `.env` files must be excluded from version control and protected by filesystem permissions.

- Separate development/test credentials from any future production credentials; never copy live credentials into test fixtures.

- Use scoped credentials and the shortest practical lifetime; rotate after suspected exposure, personnel/role change, provider compromise or incident.

- Encrypt network traffic in transit using current secure transport configurations; encrypt sensitive persistent data and backups where supported by the selected storage architecture.

- Use cryptographic hashes for artifact integrity; a checksum detects modification but does not alone prove who created the artifact.

- Signing keys and encryption keys require separate lifecycle, access, backup and rotation policies. Do not invent or hardcode key material.

- Use constant-time comparison and vetted libraries for security-sensitive token/signature verification; avoid custom cryptographic protocols.

## 11. API, input validation and web security

| Area | Defensive requirement |
| --- | --- |
| Route inventory | Maintain inventory of public/private routes, authentication requirement, scope, action and data classification. |
| Input schema | Strict schema validation, bounded length/depth/array size and explicit unknown-field handling. |
| Object access | Check ownership/scope server-side on every read/write; do not rely on opaque IDs. |
| Injection | Parameterized SQL; safe template rendering; no shell interpolation; contextual output encoding. |
| Browser security | CSRF protection for cookie-authenticated mutations, secure CORS allowlist, CSP and security headers where applicable. |
| Rate limiting | Per-identity and per-route limits for login, expensive search, file ingestion and command creation. |
| Upload handling | Content sniffing/validation, size limits, safe temporary paths, quarantine and malware scanning only if an approved capability exists. |
| Errors | Return safe, stable error codes; no stack traces, secrets, filesystem paths or internal tokens to clients. |
| Versioning | Validate API/event schema versions and reject unsupported protected commands safely. |
| Idempotency | Bind idempotency keys to actor/scope/command and payload fingerprint; reject conflicting reuse. |

## 12. File, media and subprocess security

- Treat every upload and locally discovered input as untrusted, even when it originates from the owner’s machine.

- Validate extension, declared media type, detected format, file size, dimensions, duration, codec and decompression/expansion characteristics against explicit limits.

- Quarantine inputs until validation completes; a failed or incomplete validation must not make an artifact eligible for rendering, review or publishing.

- Resolve paths against an approved workspace root; reject traversal, unexpected symlinks, device files and path collisions.

- Invoke FFmpeg and other subprocesses with argument arrays and controlled environment; do not interpolate untrusted metadata into shell commands.

- Use least-privileged OS identity, bounded process time, CPU/memory/disk limits and restricted network access where feasible.

- Separate source, scratch, output and quarantine areas; preserve immutable source inputs and generated provenance.

- Do not automatically execute macros, scripts, embedded commands or active content in uploaded documents/media.

## 13. AI, agent and prompt-injection security

Research pages, uploaded documents, transcripts, captions, comments, retrieved passages and tool outputs can contain adversarial instructions. They are data, not authority.

- Keep system/developer policy, credentials and privileged tool context outside untrusted content wherever the execution architecture permits.

- Clearly label retrieved or user-provided content as untrusted evidence; do not let it alter authorization policy, tool permissions or approval requirements.

- Agents receive task-scoped tools and minimum capabilities; no general shell, filesystem or publishing permission unless separately approved and bounded.

- Require structured output validation and independent policy checks before outputs become commands, state transitions or external actions.

- Never accept model-generated claims of approval, rights clearance, authorization or successful publishing as authoritative evidence.

- Use allowlisted tool routing and explicit confirmation for irreversible/high-impact actions; automatic public publishing remains disabled.

- Test indirect prompt injection through web pages, PDFs, subtitles, image OCR, metadata, filenames and tool responses.

## 14. Artifact integrity, provenance and supply-chain security

| Control | Requirement |
| --- | --- |
| Artifact identity | Canonical immutable identity and version; do not overwrite a version in place. |
| Manifest | Record content hash, size, media metadata, source references, transformation lineage, producer/worker and creation time. |
| Integrity verification | Verify hash on ingest, transfer and before protected use; quarantine mismatches. |
| Provenance | Distinguish user source, external source, generated derivative, edited output and imported result. |
| Build provenance | Record source revision, dependency lock, build process and artifact digest for released software where applicable. |
| Dependency hygiene | Pin dependencies, review advisories, minimize packages, verify sources and control update changes. |
| SBOM / vulnerability review | Candidate release evidence; exact tooling and severity policy remain to be approved. |
| Reproducibility | Where feasible, retain configuration and input references sufficient to explain how an output was produced. |

## 15. Logging, monitoring and security detection

Batch 21 defines observability. Security telemetry must extend it without creating a new disclosure channel.

- Record authentication failures, authorization denials, policy changes, credential lifecycle events, worker registration/revocation, suspicious file validation, integrity failures and protected-action attempts.

- Include actor/service identity, action, resource reference, scope, result, reason code, timestamp and correlation ID where safe.

- Never log raw secrets, access tokens, passwords, full sensitive prompts, private document contents or unnecessary personal data.

- Redact before persistence, not merely at dashboard display; test redaction using seeded credentials and sensitive strings.

- Restrict access to security logs and diagnostics; protect against tampering and define retention with owner approval.

- Alert on repeated authentication failures, privilege changes, worker identity anomalies, repeated authorization denials, secret exposure indicators and integrity failures.

- Ensure monitoring failure does not cause security controls to fail open.

## 16. Privacy and data protection

- Classify data by sensitivity and purpose; collect only what is required for the product and security controls.

- Scope access to workspace, brand, studio, platform account and owner actor references as applicable.

- Do not send private source assets, unpublished content or credentials to an external AI/provider unless the provider, purpose, data handling and approval are explicitly authorized.

- Define retention, deletion, export, legal hold and backup expiry with owner review; capacity pressure is not deletion authority.

- Minimize telemetry content; prefer identifiers and event metadata over copying user content into logs.

- Review third-party processor terms, data residency, retention and training-use terms before any provider activation.

## 17. Incident response and credential compromise

| Phase | Required actions |
| --- | --- |
| Prepare | Maintain asset/credential inventory, incident contacts/authority, evidence capture, disable procedures and recovery references. |
| Detect | Correlate alerts, user reports, anomalous logins, worker activity, secret scanning and integrity events. |
| Contain | Revoke affected sessions/tokens/workers; pause protected actions; isolate compromised worker or host; disable suspect integration. |
| Preserve | Capture relevant logs, state versions, artifact hashes, authorization records and timeline without copying exposed secrets. |
| Eradicate | Remove malicious persistence, patch vulnerable components, rotate credentials and verify trust boundaries. |
| Recover | Restore only from validated sources; re-register workers; reconcile external outcomes; re-enable capabilities gradually. |
| Learn | Document root cause, impact, affected data/actions, control gaps, remediation and retest evidence. |

Credential compromise response must assume the attacker may have used the credential before detection. Revocation alone does not reverse completed actions. Reconcile platform activity and external-operation records before resuming distribution.

## 18. Security acceptance and verification matrix

| ID | Test scenario | Pass condition / oracle | Evidence |
| --- | --- | --- | --- |
| SEC-T01 | Unauthenticated request to every private API route | Denied before protected state or side effect; safe response. | Route inventory and negative test results. |
| SEC-T02 | Caller forges actor identity in payload | Server derives actor from verified context; forged value ignored/rejected. | API test and audit event. |
| SEC-T03 | Cross-scope object ID substitution | No data read/mutation outside authorized scope. | IDOR test matrix. |
| SEC-T04 | Expired/revoked session or worker credential | Rejected; no protected operation proceeds. | Credential lifecycle test. |
| SEC-T05 | Worker impersonation/replay | Forged or stale assignment rejected; legitimate worker remains traceable. | Worker identity/replay test. |
| SEC-T06 | Unlisted worker capability | Dispatch/execution denied. | Capability negative test. |
| SEC-T07 | Prompt injection in source document/webpage | Untrusted text cannot change policy or invoke unauthorized tool. | Adversarial corpus results. |
| SEC-T08 | Path traversal and symlink upload | Input rejected/quarantined; files outside approved root untouched. | Filesystem test evidence. |
| SEC-T09 | Shell metacharacters in filename/metadata | No shell execution; arguments remain data. | Subprocess injection test. |
| SEC-T10 | Malformed/oversized/decompression-heavy media | Bounded rejection; worker remains healthy; no unbounded resource use. | Fuzz/limit test report. |
| SEC-T11 | Seeded secret in logs/errors/artifacts | Secret absent from persisted diagnostics and client responses. | Redaction scan. |
| SEC-T12 | SQL/HTML/command injection payloads | No injection; safe error and output encoding. | Security test suite. |
| SEC-T13 | Duplicate/replayed command or event | Idempotent result or safe conflict; no duplicate side effect. | Replay test. |
| SEC-T14 | Artifact checksum mismatch/substitution | Artifact quarantined and blocked from protected use. | Manifest and quarantine evidence. |
| SEC-T15 | Approval exists but authorization absent | Protected action denied. | Authorization negative test. |
| SEC-T16 | Authorization expired/revoked after approval | Execution-time check denies action. | TOCTOU test. |
| SEC-T17 | Emergency pause enabled | Protected action denied even if earlier authorization existed. | Pause/revocation test. |
| SEC-T18 | Direct publisher/CLI entry bypass attempt | No protected distribution path bypasses central policy. | Direct-entry negative tests. |
| SEC-T19 | Destination changed after approval | Action denied until exact destination is newly reviewed/authorized. | Destination-binding test. |
| SEC-T20 | External upload timeout with unknown outcome | Reconciliation required before retry; no false success/duplicate action. | Ambiguous-outcome simulation. |
| SEC-T21 | Webhook forged/replayed | Signature/source/timestamp/replay validation rejects event. | Webhook test evidence. |
| SEC-T22 | Worker compromised/revoked during task | Future assignments blocked; in-flight task quarantined/reconciled safely. | Revocation drill. |
| SEC-T23 | Backup restore after credential incident | Revoked credentials are not silently reactivated; secrets rotated as required. | Restore and incident drill. |
| SEC-T24 | Audit record tampering attempt | Tampering detected or denied; original evidence preserved. | Audit integrity test. |
| SEC-T25 | Rate/resource exhaustion | Admission limits protect critical paths; no governance bypass. | Stress and rate-limit report. |
| SEC-T26 | Telemetry privacy review | No prohibited sensitive content exposed; access/retention enforced. | Privacy inspection and access test. |

## 19. Security gates and release criteria

| Gate | Required evidence | Failure disposition |
| --- | --- | --- |
| G-S1 Identity & route coverage | Complete route inventory; all private routes authenticated and scoped. | Block release candidate. |
| G-S2 Central authorization | Protected actions route through central policy; exact binding and execution-time revalidation proven. | Block all protected actions. |
| G-S3 Secrets | Secret scan, redaction tests, credential storage/rotation/revocation procedure. | Block release; rotate exposed credentials. |
| G-S4 Worker trust | Identity, capability, lease, assignment and revocation tests pass. | Disable worker capability until corrected. |
| G-S5 Input/file safety | Upload validation, path confinement, subprocess and resource-limit tests pass. | Quarantine/reject affected inputs. |
| G-S6 Artifact integrity | Manifest, checksum, provenance and immutable version tests pass. | Block artifact use/distribution. |
| G-S7 Governance & distribution | Approval/authorization separation, destination binding, pause and bypass tests pass. | Keep publishing disabled. |
| G-S8 Observability/privacy | Security telemetry, redaction, access control and incident runbooks reviewed. | Block release readiness claim. |
| G-S9 Recovery | Backup/restore and credential compromise recovery evidence reviewed. | Do not claim recoverability. |
| G-S10 Independent review | Independent security acceptance with findings and evidence after implementation is complete. | No security acceptance claim until complete. |

A passing subset does not establish overall security readiness. Any critical/high unresolved issue blocks the affected capability; unresolved protected-action bypass or authentication gaps block release readiness.

## 20. Open owner decisions

| ID | Decision required | Why it matters | Status |
| --- | --- | --- | --- |
| SOD-01 | Approve authentication/session mechanism and session lifetime. | Defines identity assurance and session risk. | OPEN |
| SOD-02 | Approve owner step-up/re-authentication actions. | Protects high-impact operations. | OPEN |
| SOD-03 | Approve worker credential issuer, lifetime, rotation and revocation model. | Defines worker trust lifecycle. | OPEN |
| SOD-04 | Approve worker isolation/runtime boundary and filesystem/network profile. | Limits compromise blast radius. | OPEN |
| SOD-05 | Approve capability catalogue and per-capability permissions. | Prevents over-privileged workers/agents. | OPEN |
| SOD-06 | Approve data classification and handling rules. | Determines storage, logging and provider restrictions. | OPEN |
| SOD-07 | Approve encryption-at-rest and key-management design for selected stores. | Protects persistent data and backups. | OPEN |
| SOD-08 | Approve secret storage/injection mechanism for local and future deployment environments. | Prevents credential leakage. | OPEN |
| SOD-09 | Approve security log retention/access and tamper-protection level. | Balances evidence and privacy. | OPEN |
| SOD-10 | Approve upload size/type/media validation limits and quarantine policy. | Bounds parser and resource risk. | OPEN |
| SOD-11 | Approve dependency vulnerability severity and remediation windows. | Defines supply-chain release gate. | OPEN |
| SOD-12 | Approve webhook signature, replay window and source validation scheme. | Protects callback integrity. | OPEN |
| SOD-13 | Approve threat-risk scoring scale and risk acceptance authority. | Makes prioritization consistent. | OPEN |
| SOD-14 | Approve incident severity, notification and response-time policy. | Defines operational response obligations. | OPEN |
| SOD-15 | Approve privacy, retention, deletion, export and legal-hold policy. | Defines data lifecycle and compliance controls. | OPEN |
| SOD-16 | Approve external provider allowlist and data-transfer conditions. | Controls third-party disclosure and cost. | OPEN |
| SOD-17 | Approve security test tooling and any external assessment budget separately. | No paid tool or service is authorized. | OPEN |
| SOD-18 | Approve emergency pause authority, scope and recovery procedure. | Controls protected action during incidents. | OPEN |

## 21. Implementation and ownership mapping

| Workstream | Primary responsibility | Coordination boundary |
| --- | --- | --- |
| Central identity/authentication | Control-plane owner | All private API routes and sensitive account actions; exact framework remains open. |
| Authorization and policy | Central policy authority | Adapters/workers must call/obey central decisions; no local grant authority. |
| Worker trust | Worker registry and orchestration owner | Unique identity, scoped credentials, capability and revocation. |
| Artifact security | Artifact registry/storage owner | Validation, quarantine, integrity, provenance and retention. |
| AI/agent safety | Orchestration and product policy owners | Untrusted content handling, tool allowlists and output validation. |
| Distribution safety | Distribution domain plus central authorization | No direct publisher bypass; human approval and automatic-public-publishing restriction remain. |
| Observability/incident response | Operations owner | Batch 21 signals, redaction, runbooks and evidence preservation. |
| Independent security acceptance | Kilo, after implementation is complete | Independent read-only acceptance; not a second implementation writer. |

Agent coordination remains unchanged: Qoder is the sole writer for the current governance-closure milestone; Copilot performs focused regression-test review; OpenCode performs read-only API/backend architecture review; Kilo performs independent security acceptance after implementation is complete; Antigravity is reserved for targeted product/UI work. This document does not dispatch agents or authorize coding.

## 22. Freeze checklist and implementation boundary

- Confirm authority of each cited decision and reconcile candidate controls against Artifact 08 v1.0 and reconciliation candidate v1.1.

- Approve threat-model scope, assets, trust boundaries, risk rating method and risk acceptance authority.

- Approve authentication, worker identity, capability, secret and key-management designs.

- Approve central authorization contract and exact protected-action binding, including emergency pause and execution-time revalidation.

- Approve data classification, privacy, retention, telemetry and provider data-transfer restrictions.

- Approve file/media validation, quarantine, isolation, subprocess and resource-limit controls.

- Approve security acceptance test corpus, test environment, evidence format and independent review criteria.

- Resolve critical/high risks or record explicit, scoped owner risk acceptance; silence is not acceptance.

- Record detailed contract freeze separately from implementation authorization.

Implementation boundary: documentation/specification only. This does not authorize repository edits, agent coding, migrations, credential rotation, account creation, provider activation, paid security tools, penetration testing against production, deployment, production generation, upload or publishing. No security audit, certification, penetration test or production security acceptance is claimed.

## 23. Traceability to the P0 baseline

| Baseline source / batch | Security relationship |
| --- | --- |
| Artifact 08 accepted decisions v1.0 | Preserves one owner, existing architecture, human approval, central authorization, fail-closed behaviour and no paid services. |
| Artifact 08 reconciliation candidate v1.1 | Uses exact rights/approval/QA vocabularies; separates approval from authorization; maintains unresolved detailed freeze items. |
| Canonical Data Dictionary & Entity Ownership Registry 1.0 | Uses canonical identity, immutable versions, explicit scope and domain ownership. |
| API & Event Contract Standard 1.0 | Uses authenticated actor context, scoped command envelopes, schema validation, idempotency and protected publish bindings. |
| Unified Lifecycle State & Transition Standard 1.0 | Preserves authoritative state owners, transition evidence and unknown external outcome reconciliation. |
| Batch 17 State-Machine Catalogue | Respects accepted QA, rights and approval outcomes; no ordinary approval bypasses hard blockers. |
| Batch 18 API/Event/Schema Pack | Aligns worker identity, leases, event envelopes, errors, authorization and adapter contracts. |
| Batch 21 Observability | Uses structured logging, redaction, metrics, tracing, alerts and runbooks without exposing secrets. |
| Batch 22 Configuration/Release | Requires controlled configuration, environment separation, build provenance and release gates. |
| Batch 23 Backup/DR | Coordinates restore, credential compromise, recovery ordering and integrity validation. |
| Batch 24 Performance/Capacity | Applies admission control, quotas and bounded retries without weakening security. |

## 24. Glossary

| Term | Meaning |
| --- | --- |
| Authentication | Verification of the identity of an actor or service. |
| Authorization | Decision that an authenticated actor may perform a specific action on a specific resource under policy. |
| Capability | Explicitly bounded operation a worker or agent is permitted to perform. |
| Least privilege | Grant only the minimum permissions needed for a defined task and time. |
| Prompt injection | Untrusted content attempts to manipulate an AI/agent into violating intended instructions or boundaries. |
| Quarantine | Restricted state/location for content not yet trusted or validated for normal use. |
| STRIDE | Threat-modeling mnemonic: spoofing, tampering, repudiation, information disclosure, denial of service, elevation of privilege. |
| TOCTOU | Time-of-check to time-of-use gap where a previously valid condition changes before execution. |
| Trust boundary | Point where data, identity or control crosses between components with different trust assumptions. |

## 25. Final status

Batch 25 establishes a security architecture and defensive-control framework for owner review. Authentication/session design, worker trust mechanisms, key management, isolation, retention, risk thresholds, provider allowlists and numeric limits remain open unless separately accepted. The document preserves current architecture and governance invariants; it does not claim implementation, security audit, certification, penetration testing, production readiness or authorization.

END OF BATCH 25


## Source document metadata (preserved from DOCX)

- **Header:** NEXTDECODE CONTENT OS  |  P0 SPECIFICATION SERIES
- **Footer:** Batch 25 • Security specification candidate • Owner freeze and implementation authorization remain separate

