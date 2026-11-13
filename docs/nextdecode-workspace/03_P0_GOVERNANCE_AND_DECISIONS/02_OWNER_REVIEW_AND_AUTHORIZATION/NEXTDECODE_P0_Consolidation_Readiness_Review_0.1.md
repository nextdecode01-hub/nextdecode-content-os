# NEXTDECODE — P0 Consolidation & Readiness Review

**Document ID:** `NEXTDECODE_P0_Consolidation_Readiness_Review_0.1`  
**Version:** 0.1  
**Date:** 1 November 2026  
**Status:** CONSOLIDATED REVIEW DRAFT — OWNER REVIEW REQUIRED  
**Scope:** Design reconciliation of WP-0 through WP-6  
**Implementation status:** NOT AUTHORIZED

---

## 1. Executive disposition

The seven P0 work packages now have design or assessment material:

| Package | Subject | Current disposition |
|---|---|---|
| WP-0 | Current-system baseline and preservation | Conditionally complete as assessment only |
| WP-1 | Canonical domain and persistence | Design candidate v0.3 |
| WP-2 | Durable job and workflow execution | Design candidate v0.1 |
| WP-3 | Worker registry and contract boundary | Design candidate v0.1 |
| WP-4 | Artifact registration, storage and transfer | Design candidate v0.1 |
| WP-5 | Governance, quality, rights and authorization | Design candidate v0.1 |
| WP-6 | Vertical-slice integration and recovery validation | Design candidate v0.1 |

**Overall finding:** The package set is directionally coherent with the accepted ADR-001–ADR-010 and CF-01–CF-24 baseline. It is not yet a frozen, implementation-ready contract set. Several cross-package details must be made explicit, and the owner must review the consolidated open-decision register before declaring detailed contract freeze.

This review does not approve implementation, repository inspection, tests, agent execution, provider selection, deployment, paid services, production generation, uploads or publishing.

## 2. Authority and evidence labels

Use these labels consistently:

- **OWNER-ACCEPTED:** Explicit owner decision or accepted under standing delegation.
- **SOURCE-DEFINED:** Defined in an authoritative project source or accepted contract.
- **REPORT-BACKED:** Stated in an existing report, but not freshly retested.
- **RECOMMENDED:** Proposed resolution for owner review; not accepted yet.
- **OPEN:** Requires a decision or specification.
- **DEFERRED:** Intentionally postponed.
- **VERIFIED:** Independently confirmed by current evidence or tests.
- **NOT VERIFIED:** Current evidence is absent or insufficient.

A design document is not implementation evidence. Historical test reports do not establish the current repository's state.

## 3. Accepted baseline — do not reopen

The following remain accepted and are carried into this review:

1. ADR-001: UUIDv7 canonical identifiers.
2. ADR-002: PostgreSQL-compatible relational database as authoritative shared-state store.
3. ADR-003: Database-backed durable queue with transactional outbox/inbox initially.
4. ADR-004: Versioned HTTP/JSON contracts with schema validation.
5. ADR-005: Unique worker identity, scoped short-lived credentials and capability authorization.
6. ADR-006: Relational artifact metadata; binary storage behind an abstraction.
7. ADR-007: Centralized authorization; publishing adapters cannot bypass it; automatic publishing disabled pending separate policy.
8. ADR-008: QA outcomes `PASS`, `PASS_WITH_WARNINGS`, `NEEDS_REVIEW`, `BLOCKED`; hard blockers cannot be bypassed by ordinary approval.
9. ADR-009: Evidence-backed rights states and use-specific enforcement.
10. ADR-010: Separate lifecycle state machines for content, workflow, execution, review, approval, authorization and distribution.
11. CF-01–CF-24 as recorded in the accepted owner decision reference.
12. Existing Shorts Studio remains a specialised Python/FFmpeg engine behind a bounded adapter.
13. Initial operating direction remains local-first/free-first, with a hybrid-ready future architecture. No provider or deployment target is selected.
14. Human approval remains required for critical actions. Automatic public publishing remains disabled.
15. Existing agent ownership remains unchanged: Qoder (Phase 11 engineering), OpenCode (Phase 10 engineering/closure), Kilo (independent read-only QA).

## 4. Cross-package architecture reconciliation

### 4.1 Canonical identity and ownership

**Consistent direction:** WP-1 defines canonical entities and typed relationships; WP-2, WP-3, WP-4 and WP-5 refer to those identities rather than creating competing identifiers.

**Required contract clarification before freeze:**
- Use one canonical identifier for each logical entity.
- Keep entity ID, content/version ID, schema version, job attempt ID, worker ID, artifact version ID and event/message IDs distinct.
- A typed reference does not confer ownership, access, approval or authorization.
- Each canonical entity has one authoritative owning domain; domain ownership does not imply a separate microservice.
- Cross-domain state changes must pass through the owning domain's command/transition boundary.

**Disposition:** Baseline is consistent; exact physical schema, nullability, constraints and ownership mappings remain open.

### 4.2 Workflow, task, job and attempt boundaries

**Consistent direction:** WP-1 provides canonical references; WP-2 owns durable execution semantics; WP-3 supplies authenticated worker identity and capability checks; WP-6 validates the integrated path.

**Required clarification:**
- Workflow definition, workflow run, workflow task, job, job attempt, queue message, command, event, outbox message and inbox receipt are separate concepts.
- Orchestration determines dependency progression; scheduling determines eligibility; queue delivery transports work; workers execute bounded assignments.
- Workflow completion is not identical to job completion.
- At-least-once delivery is the contract; idempotency protects logical effects. Do not promise exactly-once execution.
- Every retry creates a new attempt identity while preserving the logical job identity.
- A stale attempt must not overwrite a newer attempt's state.

**Disposition:** Accepted semantics are aligned. Detailed lifecycle vocabularies, transitions, cancellation/compensation, numerical lease/retry policy and replay/retention remain open.

### 4.3 Worker trust and execution

**Consistent direction:** WP-3 owns worker registration/trust; WP-2 owns assignment/lease semantics; WP-5 remains the central authorization authority.

**Required clarification:**
- Declared, verified, available and authorized capabilities must remain separate.
- Capability declaration is not permission.
- Worker identity is independent of hostname or machine name.
- Credentials are unique, scoped, short-lived and revocable.
- Local and remote workers use the same trust model.
- Workers cannot self-assign, expand capabilities, grant permissions or commit after losing valid authority.
- Job isolation scopes filesystem, network, credentials, artifacts and resource use.
- Revocation effects on already-running assignments need an explicit policy.

**Disposition:** Security direction is consistent; enrollment protocol, issuer, capability catalogue, isolation technology, quotas and lifecycle transitions remain open.

### 4.4 Artifact registration and transfer

**Consistent direction:** WP-1 provides artifact identity/version references; WP-4 owns metadata registration, binary abstraction, transfer and integrity; WP-5 supplies rights/authorization constraints; WP-6 validates recovery.

**Required clarification:**
- Asset and Artifact are distinct.
- Artifact metadata is authoritative; binaries sit behind a provider-neutral storage abstraction.
- Artifact versions are immutable; repairs or changed bytes create new versions.
- Manifests reference exact artifact versions and preserve lineage.
- Transfer authorization is scoped and time-limited.
- Checksum/size/type validation is separate from availability, factual accuracy, rights, QA and approval.
- Quarantine blocks normal downstream use.
- A storage locator alone never grants access.
- Temporary files are not registered as durable artifacts.

**Disposition:** Core boundaries align. Manifest ownership/schema, transfer protocol, storage provider, retention, encryption, quarantine transitions and recovery policy remain open.

### 4.5 Governance, quality, rights and authorization

**Consistent direction:** WP-5 is the policy enforcement boundary; other packages consume its decisions and must not implement competing authorization authorities.

**Required clarification:**
- QA, rights, review, approval, authorization, execution and confirmed distribution outcome are separate records/concepts.
- QA outcomes use the accepted four-value vocabulary.
- Rights use the accepted vocabulary: `UNKNOWN`, `PENDING_REVIEW`, `CLEARED`, `RESTRICTED`, `EXPIRED`, `REVOKED`, `DENIED`.
- Approval decisions use: `APPROVED`, `REJECTED`, `CHANGES_REQUESTED`, `EXPIRED`, `REVOKED`.
- Authorization is centralized, default-deny and fail-closed.
- Authorization binds to exact action, resource, version/hash, destination and applicable policy context; expiry and revocation are enforced.
- Hard QA blockers, unknown rights and emergency pause cannot be bypassed by ordinary approval or retry.
- Every publishing route, including direct adapters and direct pipeline entry points, must enforce the same central boundary.
- P0 tests must not perform live uploads or publishing.

**Disposition:** Accepted principles align. The exact policy request/decision schema, policy versioning, emergency-pause authority and enforcement coverage evidence remain open.

### 4.6 Shorts Studio compatibility

The existing Shorts Studio remains a bounded specialist engine. The P0 foundation should orchestrate it through an adapter with explicit input/output contracts, run identity, artifact registration and governance checks. The P0 work must not wholesale replace the current rendering pipeline or silently bypass it through direct production paths.

**Disposition:** Accepted constraint; adapter contract and exact entry-point coverage must be demonstrated during implementation and WP-6.

## 5. Dependency and ownership matrix

| Package | Owns the design boundary | Depends on | Supplies to |
|---|---|---|---|
| WP-0 | Baseline and preservation evidence | Existing system evidence | All packages; risk context |
| WP-1 | Canonical entities, identity, relationships, persistence boundary | Accepted data dictionary/contracts | WP-2, WP-3, WP-4, WP-5, WP-6 |
| WP-2 | Workflow execution, jobs, attempts, leases, retries, outbox/inbox | WP-1; WP-3 identity; WP-5 policy interface | WP-6 |
| WP-3 | Worker identity, trust, capabilities, credentials, bounded execution | WP-1; WP-2 assignment contract; WP-5 authorization | WP-2, WP-6 |
| WP-4 | Artifact metadata/versioning, transfer, integrity, provenance | WP-1; WP-2 attempt/run refs; WP-3 transfer identity; WP-5 access policy | WP-5, WP-6 |
| WP-5 | QA/rights/review/approval/authorization policy boundary | WP-1 identities; WP-2 execution context; WP-3 worker context; WP-4 artifact/version evidence | All protected actions; WP-6 |
| WP-6 | Integrated acceptance scenario, failure recovery and evidence report | WP-1 through WP-5 plus WP-0 limitations | Owner acceptance decision |

**Ownership caution:** This is logical package ownership, not a decision to create seven services or to change Qoder/OpenCode/Kilo assignments.

## 6. Cross-package interface contracts that must be explicit

Before detailed contract freeze, the consolidated contract set should define the following interfaces:

1. **Canonical reference envelope:** entity type, canonical ID, workspace scope and version where applicable.
2. **Command envelope:** command ID, actor/worker identity, idempotency key, correlation/causation references, schema version and requested operation.
3. **Event envelope:** event ID, owning domain, aggregate identity/version, event type/schema version, occurred/recorded timestamps, correlation/causation references.
4. **Job assignment envelope:** job ID, attempt ID, worker ID, lease/fencing token, capability requirement, input references and expiry.
5. **Worker completion envelope:** assignment identity, attempt identity, outcome, structured error, output artifact references and attributable evidence.
6. **Artifact manifest:** exact artifact/version references, hashes, media types, sizes, lineage and production-run provenance.
7. **Policy evaluation request:** actor/worker, action, target/resource, exact version/hash, destination, intended use, rights/QA/approval references and policy context.
8. **Policy decision:** allow/deny, reason codes, policy version, evaluated context, expiry/revocation reference and audit identity.
9. **Review/approval record:** immutable review snapshot, exact target version(s), reviewer, decision, scope and timestamp.
10. **Acceptance evidence record:** test ID, requirement ID, environment, build/source identity, inputs, outputs, result, logs/evidence references and reviewer.

These are required interface categories, not frozen JSON schemas. Field-level schemas and compatibility rules remain a contract-freeze task.

## 7. Consolidated open-decision register

The following are the major open decision groups gathered from WP-1 through WP-6 and the governing Artifact 08 material. Existing package-local O/J/W/A/G/F identifiers remain valid in their source documents; this master register groups them for review and does not renumber or silently close them.

| Master ID | Decision area | Required resolution | Blocking status |
|---|---|---|---|
| ODR-01 | Entity schema | Final fields, nullability, keys, constraints, FK behavior, indexes and lifecycle transitions | Contract freeze blocker |
| ODR-02 | Content versioning | Exact ContentVersion schema and relation to ContentItem/ContentVariant | Contract freeze blocker |
| ODR-03 | Workflow model | Workflow definition/run/task schemas, version pinning and dependency rules | Contract freeze blocker |
| ODR-04 | Job lifecycle | Job/attempt states, terminal outcomes, cancellation, retry and remediation semantics | Contract freeze blocker |
| ODR-05 | Lease/fencing | Lease duration, heartbeat cadence, fencing token semantics and expiry recovery | Contract freeze blocker |
| ODR-06 | Retry/idempotency | Attempt limits by class, backoff/jitter, key scope/retention, poison messages and manual requeue authority | Contract freeze blocker |
| ODR-07 | Outbox/inbox | Ordering scope, deduplication, retention, replay, purge, poison handling and DB claim strategy | Contract freeze blocker |
| ODR-08 | Worker identity | Enrollment protocol, trust lifecycle, identity proof and credential issuer/format/rotation | Contract freeze blocker |
| ODR-09 | Worker capability | Capability catalogue/versioning, verification evidence, availability and authorization transitions | Contract freeze blocker |
| ODR-10 | Worker isolation | Isolation technology/threat model, network/filesystem/secret scopes, resource quotas and revocation during active work | Contract freeze blocker |
| ODR-11 | Artifact model | Artifact/Asset/Manifest schemas, ownership, lineage, validation and quarantine transitions | Contract freeze blocker |
| ODR-12 | Artifact transfer | Transfer protocol, signed/time-limited access, interrupted-transfer recovery and cross-job isolation | Contract freeze blocker |
| ODR-13 | Artifact lifecycle | Retention, legal hold, deletion, backup, recovery and provider-neutral encryption requirements | Some details may be deferred if abstracted safely |
| ODR-14 | Governance schema | QA result/check schema, rights evidence schema, approval snapshot and policy decision schema | Contract freeze blocker |
| ODR-15 | Authorization binding | Exact canonical binding for action/resource/version/hash/destination/use/policy version and revocation semantics | Contract freeze blocker |
| ODR-16 | Emergency pause | Authority, scope, propagation, audit and recovery/unpause conditions | Contract freeze blocker |
| ODR-17 | Adapter enforcement | Complete list of direct/indirect Shorts Studio and distribution entry points and central gate placement | Acceptance blocker |
| ODR-18 | Error taxonomy | Stable error codes, severity/retryability, reconciliation ownership and diagnostic access | Contract freeze blocker |
| ODR-19 | Audit/correlation | Required correlation/causation propagation, audit event schema and retention | Contract freeze blocker |
| ODR-20 | Operational choices | Provider, region, deployment topology, monitoring, backup/RPO/RTO, sizing and budget | Deferred; must not be guessed |
| ODR-21 | WP-6 environment | Isolated test environment, deterministic fixtures, evidence capture and cleanup rules | Acceptance prerequisite |
| ODR-22 | Independent QA | Kilo read-only QA scope, evidence format, defect severity and sign-off criteria | Acceptance prerequisite |

### 7.1 Safe deferrals

The following can remain deferred only if interfaces are genuinely provider-neutral and the deferral does not weaken security, integrity or recoverability:

- Cloud/database/storage provider and region.
- Production deployment topology and worker fleet sizing.
- Paid infrastructure and operational budget.
- Production monitoring vendor and numerical alert thresholds.
- Numerical retention durations, backup retention and legal-hold schedules, where the contract defines ownership and enforcement hooks.
- RPO/RTO targets and restore cadence, provided production readiness is not claimed.
- Advanced broker adoption beyond the accepted initial database-backed queue.
- Advanced multi-user, SaaS, billing, multi-brand and broad cloud-rendering capabilities.

No deferred item authorizes spending or provider activation.

## 8. P0 acceptance checklist

This checklist is the proposed evidence gate for P0-A. It is not evidence that the checks have already passed.

### A. Canonical model and persistence
- [ ] Canonical IDs are immutable UUIDv7 and never reused.
- [ ] Workspace scope is enforced on all tenant-scoped records.
- [ ] One authoritative owner exists per canonical entity.
- [ ] Entity ID, content version, schema version and attempt/version IDs are distinct.
- [ ] Typed references do not grant access or authority.
- [ ] Cross-domain state changes use owning-domain commands.
- [ ] State transitions are validated and auditable.
- [ ] Existing Shorts Studio identifiers are preserved as external/legacy references where appropriate.

### B. Durable workflow and jobs
- [ ] Workflow definition/run/task/job/attempt/message/event are distinct.
- [ ] Pending work survives control-plane restart.
- [ ] Only eligible jobs are dispatched.
- [ ] Two workers cannot hold the same active lease.
- [ ] Lease expiry and recovery are demonstrated.
- [ ] Stale worker/attempt callbacks are rejected.
- [ ] Retries create new attempt identities and preserve history.
- [ ] Duplicate delivery does not create duplicate logical effects.
- [ ] Idempotency key reuse with a different payload is rejected.
- [ ] Failure classification, retryability and remediation are auditable.

### C. Worker trust and security
- [ ] Worker identity is independent of hostname.
- [ ] Untrusted/unregistered workers cannot claim work.
- [ ] Revoked workers cannot claim new work.
- [ ] Expired credentials are denied.
- [ ] Unsupported capabilities are denied.
- [ ] Capability declaration does not grant permission.
- [ ] One worker cannot update another worker's lease.
- [ ] Worker access is bounded to assigned job resources.
- [ ] Secrets are not exposed in logs or test output.

### D. Artifact integrity and provenance
- [ ] Artifact metadata is authoritative and binary storage is abstracted.
- [ ] Artifact versions are immutable.
- [ ] Checksum and size mismatch block downstream use.
- [ ] Expired transfer authorization is denied.
- [ ] Cross-job artifact access is denied.
- [ ] Interrupted transfer recovers safely.
- [ ] Temporary files are not registered as durable artifacts.
- [ ] Manifest references exact artifact versions.
- [ ] Lineage and production provenance are reconstructable.
- [ ] Quarantined artifacts cannot be used normally.

### E. Governance and protected actions
- [ ] QA, rights, review, approval, authorization and execution are distinct.
- [ ] `BLOCKED` cannot pass through ordinary approval.
- [ ] Unknown/unresolved rights fail closed for protected use.
- [ ] Approval is exact-version and scope bound.
- [ ] Missing, expired, revoked or mismatched authorization is denied.
- [ ] Authorization for a different hash or destination is denied.
- [ ] Emergency pause blocks protected actions.
- [ ] Direct adapters and direct pipeline entry points cannot bypass central enforcement.
- [ ] No live upload or publishing occurs during P0 testing.

### F. Integration and recovery
- [ ] One synthetic test ContentItem and ContentVariant are created.
- [ ] Workflow and dependent task are created.
- [ ] Durable job is dispatched and claimed by an authenticated worker.
- [ ] Deterministic test output is produced.
- [ ] Immutable artifact is registered.
- [ ] Results and state transitions are recorded.
- [ ] Control-plane restart, worker loss, duplicate events, stale callbacks and interrupted transfer are injected.
- [ ] Recovery and audit reconstruction are demonstrated.
- [ ] Security-negative and governance tests are completed.
- [ ] Known limitations are documented.

### G. Independent acceptance
- [ ] Kilo performs independent read-only QA.
- [ ] Kilo's evidence identifies source/build, environment, tests, results and limitations.
- [ ] Findings are classified and assigned to the correct owner.
- [ ] No self-approval by the implementing agent.
- [ ] Owner reviews the acceptance evidence and explicitly records disposition.

## 9. Failure-injection coverage map

WP-6 defines 18 failure-injection cases. The integrated evidence report should map each case to a requirement and package owner. At minimum, the suite must cover:

- Control-plane restart and worker termination.
- Lease expiry, duplicate claims and stale completion.
- Duplicate/out-of-order event delivery and idempotency conflict.
- Interrupted artifact transfer, checksum mismatch and expired transfer authorization.
- Worker credential expiry/revocation and capability mismatch.
- Authorization mismatch for action, target, version/hash or destination.
- `BLOCKED` QA, unknown/restricted rights and emergency pause.
- Direct adapter/pipeline bypass attempts.
- Ambiguous external outcome reconciliation without performing a real external side effect.

Any test not run must be marked `NOT_RUN`, not passed by implication.

## 10. Known inherited risks — not freshly verified

The following findings were carried forward from historical Phase 10/11 reports. They are important acceptance targets, not claims about the current code state:

- G1: storyboard approval gate historically defaulted to `warn`.
- G2: rights evidence historically not enforced end-to-end by publishing.
- G3: unsupported factual claims historically warning-only.
- U1: direct platform adapters historically could bypass the parent publisher gate.
- D1: direct pipeline entry historically bypassed governed orchestration/run identity/quality gates.
- T1: shot/beat/render traceability historically incomplete.
- R1: Run Tracker runtime/recovery evidence historically missing.

These must be re-evaluated against current source and test evidence only after the relevant inspection/testing is explicitly authorized.

## 11. Readiness gates

| Gate | Required outcome | Current status |
|---|---|---|
| G0 — Design package completeness | WP-0 through WP-6 design/assessment materials exist | Prepared; WP-0 conditional |
| G1 — Cross-package consistency | Interfaces, ownership and boundaries reconciled | Review draft; owner review pending |
| G2 — Detailed contract freeze | ODR critical items resolved or explicitly accepted as safe deferrals | NOT FROZEN |
| G3 — Implementation authorization | Explicit bounded owner authorization, prerequisites and permissions recorded | NOT GRANTED |
| G4 — Implementation evidence | Approved code/tests and reproducible evidence | NOT STARTED under this plan |
| G5 — Independent QA | Kilo read-only acceptance review | PENDING |
| G6 — Owner acceptance | Explicit owner decision based on evidence and known limitations | PENDING |

**Important:** G0 does not imply G1–G6. Preparing design packages does not mean implementation is complete or accepted.

## 12. Required owner review decisions

The owner review should resolve only the genuinely consequential items:

1. Accept, amend or reject the cross-package interface boundaries in Section 6.
2. Decide which ODR items are required for detailed contract freeze and which may remain safely abstracted/deferred.
3. Confirm that WP-1 through WP-6 remain design candidates until the detailed freeze is explicitly recorded.
4. Confirm that implementation, agent execution, repository writes, tests, environment changes, provider activation and deployment each require their own bounded authorization.
5. Confirm the acceptance evidence and independent QA gate in Sections 8–11.

No routine decision should be escalated if it is already covered by accepted ADR/CF decisions or the standing delegation rule. No unresolved security, rights, authorization, spending or production-side-effect decision should be guessed.

## 13. Implementation and operational safety boundary

This review does not authorize:
- Repository or code changes, including tests, fixtures, scripts or documentation.
- Git operations or changes to branches/remotes.
- Dependency installation, environment or credential changes.
- Running Qoder, OpenCode, Kilo or other agents on implementation work.
- Database migrations or destructive data operations.
- Worker enrollment or credential issuance.
- Cloud resources, deployment, paid services or charge-generating APIs.
- Production rendering, uploads, publishing or distribution.

Existing working-tree changes and untracked work must remain preserved. No cleanup, reset, revert, stash, broad staging, commit or push is implied.

## 14. Plain-language explanation

The six work packages are the parts of a reliable production line:

- WP-1 gives every piece of work a stable identity and a proper record.
- WP-2 makes sure work orders survive restarts and retries.
- WP-3 makes sure only trusted workers perform assigned tasks.
- WP-4 makes sure outputs are stored, traceable and unaltered.
- WP-5 makes sure quality, rights, human approval and permission are checked separately.
- WP-6 proves the whole line still behaves safely when things fail.

This review checks that the parts connect correctly. It does not switch the production line on.

---

**Final disposition:** P0 design package set is prepared for consolidated owner review. Detailed contract freeze is still pending. Implementation authorization remains NOT GRANTED.
