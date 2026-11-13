# NEXTDECODE Content OS — P0 Foundation Implementation Specification 1.0

**Document status:** Proposed implementation specification — owner review required  
**Version:** 1.0  
**Date:** 31 October 2026  
**Scope:** P0 foundation only  
**Authority:** Product owner  
**Related documents:**
- `NEXTDECODE_Master_Blueprint_2.0.docx`
- `NEXTDECODE_Architecture_Reconciliation_Implementation_Readiness_Report_1.0.md`
- `NEXTDECODE_Canonical_Contracts_Pack_1.0.md`
- `NEXTDECODE_Architecture_Decision_Register_1.0.md`
- `NEXTDECODE_Architecture_Decision_Records_Pack_1.0.md`
- Architecture Parts 1–8

---

## 1. Executive summary

This specification converts the proposed NEXTDECODE Content OS architecture into a bounded P0 foundation plan. It describes what the first foundation increment should establish, how its components relate, what must be decided first, and how completion should be demonstrated.

**P0 is not the whole Content OS.** It is the minimum reliable platform foundation on which research, creation studios, governance, distribution and analytics can be added without repeatedly rebuilding identity, state, job execution and artifact handling.

The P0 foundation should establish:

1. Canonical entities and identity.
2. A cloud-authoritative persistence boundary.
3. Durable jobs, leases and recovery.
4. Worker registration and capability-aware execution.
5. Versioned control-plane and worker contracts.
6. Artifact metadata and controlled transfer.
7. Separate lifecycle state machines.
8. A centralized governance boundary that prevents publishing bypass.
9. Testable quality/rights policy interfaces, even if complete policy catalogues are delivered incrementally.
10. Observability, auditability and operational recovery hooks.

The initial implementation should use a **vertical-slice approach**: one content item moves through a minimal workflow, a durable job is claimed by a worker, an output artifact is registered, the result is recorded, and the workflow can recover from interruption. This proves the platform backbone before multiple studios and complex agent workflows are introduced.

**No repository inspection, code changes, Git operations, dependency installation, deployment, real upload or publishing is authorized by this document.**

---

## 2. Product and architecture constraints

### 2.1 Locked constraints

- Product: NEXTDECODE Content OS.
- Initial mode: single-owner Creator Mode, one brand (NEXTDECODE).
- Deployment direction: **Hybrid**.
- Cloud control plane remains available independently of the user's PC.
- Shared workflow/control state is cloud-authoritative.
- Local worker provides access to the existing Shorts Studio and heavy local rendering when online.
- Shorts Studio is integrated as a specialized engine; it is not replaced wholesale.
- Human approval remains required for critical actions unless a separate conditional-publishing policy is approved.
- No production generation, uploads or publishing without explicit authorization.
- Existing agent ownership is unchanged:
  - Qoder — Phase 11 engineering owner.
  - OpenCode — Phase 10 engineering/closure owner.
  - Kilo — independent read-only QA.
- No Git operations of any kind until explicit superseding permission.
- Preserve all existing work in progress. No destructive cleanup, reset, revert, broad staging or unrelated overwrite.
- Cloud provider, database provider, queue technology, storage provider, budget and deployment target remain unselected.

### 2.2 Architecture implications

- A local worker being offline must not make cloud workflow records disappear.
- Local-only rendering waits safely when the PC is offline; the system must not imply that local compute continues while powered off.
- The control plane owns scheduling, authoritative state, policy and authorization.
- Workers execute assigned work; they do not become independent sources of truth.
- Agents perform bounded reasoning/tool tasks under contracts; they are not schedulers, queues or workers.
- Large media binaries are transferred through controlled artifact storage, not ordinary JSON API payloads.
- Approval, authorization and execution remain separate concepts.

---

## 3. Scope

### 3.1 Included in P0

| Capability | P0 outcome |
|---|---|
| Canonical identity | Stable IDs and explicit entity relationships |
| Core data model | Minimal relational model for workspace, brand, content, workflow, task, job, worker and artifact |
| State management | Separate, validated state transitions |
| Durable queue | Persistent job records, leases, retry and recovery |
| Scheduler/orchestration boundary | Clear separation of scheduling, orchestration and execution |
| Worker registry | Machine identity, capabilities, heartbeat and revocation |
| Contracts | Versioned API/event envelopes and validation |
| Artifact management | Immutable artifact metadata, checksums and controlled transfer interface |
| Governance boundary | Central authorization check before consequential distribution |
| QA/rights interfaces | Structured policy result and hard-block representation |
| Audit/observability | Correlation IDs, structured events, state history and operational diagnostics |
| Vertical-slice test | Demonstrate durable workflow through one worker and one artifact |

### 3.2 Explicitly excluded from P0

- Full research intelligence and trend radar.
- Complete brand intelligence and strategy engines.
- Full multiformat creation engine.
- Full visual asset discovery and asset marketplace.
- Production-grade agent fleet or autonomous agent swarms.
- Automatic public publishing.
- Full platform-specific publishing rollout.
- Analytics dashboards and learning/recommendation engine.
- Multi-user teams, roles beyond the initial owner model, tenancy and SaaS billing.
- Vector database or advanced semantic search infrastructure.
- Replacing or rewriting Shorts Studio.
- Cloud rendering of all Shorts Studio workloads.
- Selection or purchase of a cloud provider or paid service without owner approval.

---

## 4. P0 completion definition

P0 is complete only when the following are demonstrated in a controlled, non-production environment:

1. A content item and variant can be created with stable canonical IDs.
2. A workflow can be created and its state persisted.
3. A task can create a durable job.
4. A registered worker can authenticate and claim only eligible work.
5. A lease prevents two workers from concurrently owning the same active attempt.
6. Worker interruption results in recoverable work after lease expiry.
7. Duplicate event delivery does not create duplicate logical side effects.
8. A worker can register an immutable artifact with size and checksum metadata.
9. Artifact transfer is scoped and unauthorized access is denied.
10. State transitions reject invalid or stale updates.
11. A protected distribution request is denied when authorization is absent, expired, revoked or bound to a different artifact/version/destination.
12. Hard-block policy results cannot be bypassed by ordinary editorial approval.
13. All key transitions can be traced through correlation IDs and audit records.
14. A restart of the control-plane process does not lose durable workflow/job state.
15. The vertical-slice acceptance suite passes reproducibly.

A green unit-test suite alone is not sufficient. P0 requires integration and failure-recovery evidence.

---

## 5. Logical architecture

```text
                  OWNER / CONTROL DASHBOARD
                           |
                           v
                 CLOUD CONTROL PLANE
       +--------------------------------------+
       | API boundary and authentication      |
       | Workspace / Brand / Content services |
       | Workflow orchestrator                |
       | Scheduler                            |
       | Policy / Approval / Authorization    |
       | Worker registry and lease manager    |
       | Artifact metadata service            |
       | Audit / Observability                |
       +------------------+-------------------+
                          |
             +------------+-------------+
             |                          |
             v                          v
    CANONICAL DATABASE            OBJECT STORAGE
    - entity records              - media binaries
    - workflow/job state          - generated artifacts
    - leases                      - source assets
    - policy/approval             - previews/manifests
    - event outbox/inbox
             |
             v
       DURABLE JOB DISPATCH
             |
       +-----+----------------------+
       |                            |
       v                            v
 LOCAL WORKER                  REMOTE WORKER
 (when PC online)              (only approved capabilities)
       |                            |
       v                            v
 SHORTS STUDIO /                Research or lightweight
 LOCAL EXECUTION                cloud-compatible tasks
       |
       v
 Artifact upload + checksum + result callback
```

This is a logical architecture, not a provider or deployment selection. Queue implementation may initially use database-backed dispatch with outbox/inbox semantics. A separate broker is not assumed.

---

## 6. Component specifications

### 6.1 Canonical identity and core domain model

**Purpose:** Provide stable identity across content, workflows, workers, runs and artifacts.

**Minimum entities:**
- Workspace
- Brand
- ContentIdea
- ContentItem
- ContentVariant
- Workflow
- WorkflowTask
- Job
- JobAttempt or lease/attempt record
- Worker
- Artifact
- Asset (minimal P0 metadata boundary)
- ReviewPackage
- Approval
- Authorization
- DistributionRequest / DistributionAttempt
- Event / OutboxMessage / InboxReceipt

**Rules:**
- Use opaque, globally unique IDs; UUIDv7 is a proposed candidate, not yet owner-approved.
- Entity type is explicit.
- Content item and content variant are separate.
- A production run is an execution attempt, not the content identity.
- Artifact versions are immutable.
- Legacy Shorts Studio IDs and paths are external references, not canonical IDs.
- Every entity has created/updated timestamps and ownership/relationship fields appropriate to its domain.

**Acceptance criteria:**
- Duplicate IDs are rejected.
- Foreign-key and relationship constraints are enforced.
- Content item can have multiple variants.
- One variant can have multiple production attempts.
- Historical artifact references remain stable after a newer artifact is created.

### 6.2 Canonical persistence

**Purpose:** Persist shared state independently of local worker availability.

**Proposed baseline:** PostgreSQL-compatible relational database. Provider and cost are open.

**Rules:**
- One authoritative owner for each shared state field.
- Transactions protect related state changes.
- Schema migrations are versioned.
- No hidden dual-write between local SQLite and cloud state.
- Local worker cache is disposable/reconcilable.
- Large binary media is not stored as database BLOBs by default.

**Acceptance criteria:**
- Control-plane restart preserves workflow and job state.
- Concurrent state updates cannot silently overwrite valid newer state.
- Referential integrity prevents orphaned critical records.
- Backup and restore procedure is documented and tested before production use.

### 6.3 Workflow orchestrator

**Purpose:** Coordinate task dependencies and aggregate workflow progress.

**Responsibilities:**
- Create tasks from a workflow definition.
- Enforce dependencies.
- Submit eligible work to durable dispatch.
- Receive durable results.
- Apply validated state transitions.
- Trigger next steps only after prerequisites are satisfied.
- Stop progression when a hard blocker is present.

**Non-responsibilities:**
- Does not execute media rendering itself.
- Does not act as the scheduler.
- Does not authenticate workers by trusting payload claims.
- Does not independently publish content.

**Acceptance criteria:**
- A dependent task cannot run before its prerequisite.
- A failed task does not erase successful prior artifacts.
- Replaying an event does not create duplicate task progression.
- Workflow summary is derived from explicit child states.

### 6.4 Scheduler

**Purpose:** Decide when work becomes eligible.

**P0 responsibilities:**
- Immediate dispatch of eligible tasks.
- Basic scheduled-at timestamp support.
- Respect task dependencies, worker capability and policy holds.
- Recover eligible pending work after restart.

**Deferred:** Complex recurring campaign calendars, optimization and sophisticated time-window planning.

**Acceptance criteria:**
- Future-scheduled work does not run early.
- Due work becomes eligible after scheduler restart.
- Time-zone handling is explicit for user-entered schedules.
- Scheduler does not bypass workflow or governance checks.

### 6.5 Durable job dispatch and leases

**Purpose:** Ensure asynchronous work survives process interruption.

**Proposed baseline:** Database-backed queue with transactional outbox/inbox. Dedicated broker remains an evidence-driven future option.

**Minimum job fields:**
- job ID and job type;
- owning workflow/task;
- payload schema version;
- capability requirements;
- priority and eligible-at time;
- attempt count and retry policy;
- state;
- lease owner, lease expiry and heartbeat;
- idempotency key;
- timestamps and structured failure details.

**Rules:**
- At-least-once delivery is expected; exactly-once execution is not assumed.
- Side effects must be idempotent or protected by idempotency keys.
- A lease is time-bounded.
- Expired leases are recoverable.
- A stale worker cannot overwrite a newer attempt.
- Retries are bounded and classified.
- Terminal failures require explicit remediation/requeue policy.

**Acceptance criteria:**
- Worker killed mid-job; job recovers after lease expiry.
- Duplicate dispatch; only one valid lease holder.
- Stale result callback; rejected.
- Retry count and failure reason remain auditable.
- Control-plane restart preserves pending work.

### 6.6 Worker registry and execution boundary

**Purpose:** Register and govern local/remote execution capacity.

**Minimum worker record:**
- worker ID;
- machine identity;
- status and last heartbeat;
- software/contract version;
- declared capabilities;
- execution environment label;
- credential status;
- registration and revocation timestamps.

**Security baseline:** Unique worker identity and scoped short-lived credentials are proposed.

**Rules:**
- Workers claim jobs only through the control plane.
- Capabilities are checked server-side.
- Workers receive minimum required permissions.
- A worker can update only jobs with a valid lease.
- Revoked workers cannot claim new jobs or fetch new artifacts.
- Worker credentials are not user login credentials.
- Worker logs redact secrets.

**Local worker behavior:**
- If PC is offline, local-only work remains queued or waiting.
- On reconnect, worker re-authenticates, advertises capabilities and resumes eligible work.
- Local temporary files are not authoritative shared state.

**Acceptance criteria:**
- Worker cannot claim unsupported job type.
- Revoked worker is denied.
- Expired credential is denied.
- Worker A cannot update Worker B's active lease.
- Local worker reconnect does not duplicate completed work.

### 6.7 Versioned API and event contracts

**Proposed baseline:** Versioned HTTP/JSON with schema validation.

**Minimum envelope fields:**
- message/request ID;
- schema version;
- producer identity;
- created-at timestamp;
- correlation ID;
- causation ID where applicable;
- entity references;
- typed payload.

**Rules:**
- Validate inbound messages.
- Reject invalid critical enum values.
- Do not embed large binaries in ordinary API messages.
- Do not expose database internals as the worker contract.
- Keep secrets out of payloads.
- Use structured errors with safe diagnostics.

**Acceptance criteria:**
- Malformed payload rejected at boundary.
- Unsupported schema version handled explicitly.
- Correlation ID preserved across workflow, job and worker events.
- Duplicate event is deduplicated.
- Contract compatibility tests run in CI once CI is authorized and configured.

### 6.8 Artifact management

**Purpose:** Register, transfer and retrieve durable outputs.

**Proposed baseline:** Artifact metadata in canonical database; binary storage behind an object-storage abstraction. Provider remains open.

**Minimum metadata:**
- artifact ID and immutable version;
- content item/variant/workflow/run references;
- artifact type and media type;
- size and checksum;
- producer and created-at;
- storage reference;
- validation state;
- provenance and rights references;
- retention class.

**Rules:**
- New output creates a new immutable version.
- Approval binds to exact version/hash.
- Storage locator is not authorization.
- Upload/download access is scoped and time-limited.
- Checksum mismatch blocks downstream use.
- Temporary files are not marked durable until transfer and registration complete.

**Acceptance criteria:**
- Uploaded artifact checksum matches local checksum.
- Expired transfer authorization is denied.
- Cross-job artifact access is denied.
- A new artifact version does not mutate prior version.
- Interrupted transfer can be retried safely.

### 6.9 Governance boundary

**Purpose:** Prevent unsafe or unauthorized consequential actions.

**P0 implementation requirement:** Establish the centralized authorization boundary and route any distribution request through it. Production publishing remains disabled unless separately authorized.

**Concepts:**
- Review = evaluation.
- Approval = editorial decision tied to exact versions.
- Authorization = permission for a particular action, destination and time.
- Execution = adapter performs the authorized action.

**Rules:**
- Adapter cannot self-authorize.
- Approval alone is insufficient.
- Authorization binds to content/variant/artifact version, platform/account, action and policy version.
- Hard rights, safety and integrity blockers cannot be overridden by ordinary approval.
- Emergency pause blocks new consequential actions.
- Denials and failures are auditable.

**Acceptance criteria:**
- Missing authorization denies distribution.
- Expired or revoked authorization denies distribution.
- Authorization for a different artifact hash denies distribution.
- Authorization for a different destination denies distribution.
- Emergency pause blocks all protected actions.
- Dry-run cannot silently become live execution.

### 6.10 Quality and rights policy interfaces

Full policy catalogues may evolve, but the data and enforcement interfaces must exist in P0.

**Quality outcomes:**
- PASS
- PASS_WITH_WARNINGS
- NEEDS_REVIEW
- BLOCKED

**Rights states proposed:**
- CLEARED
- RESTRICTED
- PENDING_VERIFICATION
- PROHIBITED
- UNKNOWN

**Rules:**
- Policy result includes policy version, check IDs, severity, evidence references and remediation.
- UNKNOWN/PENDING/PROHIBITED rights states block the affected protected use until the approved policy says otherwise.
- Ordinary editorial approval cannot override hard rights/safety/integrity blockers.
- Numeric quality scores do not replace explicit hard gates.

**Acceptance criteria:**
- BLOCKED package cannot pass through ordinary approval.
- Rights scope mismatch blocks use.
- Policy version used for a decision is retained.
- Warnings remain visible in review evidence.

### 6.11 Audit and observability

**Purpose:** Make execution and governance explainable.

**P0 requirements:**
- Structured logs.
- Correlation IDs across workflow/task/job/worker/artifact.
- Durable state-transition history for critical entities.
- Worker heartbeat and lease visibility.
- Retry and failure classification.
- Authorization decision audit.
- Secret redaction.
- Health/readiness endpoints for control-plane components.

**Acceptance criteria:**
- A workflow can be reconstructed from audit records.
- Failed job includes actionable safe diagnostic details.
- Secrets do not appear in logs or test output.
- Worker offline/lease-expired condition is visible.
- Authorization denial reason is queryable by an authorized owner.

---

## 7. P0 vertical slice

Build and verify one narrow end-to-end path before expanding the surface area.

### Scenario

1. Owner creates a content item and one variant.
2. System creates a workflow and one eligible task.
3. Orchestrator persists the task and dispatchable job.
4. Scheduler marks it eligible.
5. A registered worker claims the job under a lease.
6. Worker performs a deterministic test operation (not a real public content production or upload).
7. Worker creates a small test artifact and calculates a checksum.
8. Worker transfers/registers the artifact.
9. Control plane validates the result and records artifact metadata.
10. Workflow advances using a valid state transition.
11. A simulated distribution request without authorization is denied.
12. Worker/control-plane interruption tests verify durable recovery.

### Required failure scenarios

- Control-plane restart after job creation.
- Worker process termination during execution.
- Duplicate event delivery.
- Lease expiry and reassignment.
- Stale worker result after reassignment.
- Artifact transfer interruption.
- Checksum mismatch.
- Invalid state transition.
- Expired/revoked worker credential.
- Missing/expired/mismatched publishing authorization.
- Hard-block quality/rights result.

### Explicit non-goals of the slice

- No real YouTube/Instagram/TikTok upload.
- No public publishing.
- No production API credentials.
- No expensive cloud rendering.
- No autonomous publishing.
- No replacement of Shorts Studio's rendering pipeline.

---

## 8. Workstreams and dependency order

| Workstream | Deliverable | Depends on | Exit evidence |
|---|---|---|---|
| W0 — Decision closure | Owner-approved ADR baseline | Owner review | Decision log updated |
| W1 — Domain foundation | IDs, entities, relationships, migrations | ADR-001, ADR-002, ADR-010 | Schema and contract tests |
| W2 — Durable execution | Jobs, leases, retries, outbox/inbox | W1, ADR-003 | Recovery and dedup tests |
| W3 — Worker boundary | Registry, auth, capabilities, heartbeat | W2, ADR-004, ADR-005 | Security and lease tests |
| W4 — Artifact boundary | Metadata, storage abstraction, transfer | W1, W3, ADR-006 | Checksum/access tests |
| W5 — Governance foundation | Policy result, approval, authorization, pause | W1, W4, ADR-007–009 | Negative authorization tests |
| W6 — Vertical slice | End-to-end controlled workflow | W1–W5 | Acceptance suite and evidence |
| W7 — Operational readiness | Backup/restore, monitoring, runbooks | W1–W6 | Recovery drill and runbook review |

Workstreams may be planned in parallel, but file-level implementation ownership must be explicit and non-overlapping. No agent ownership is changed by this plan.

---

## 9. Acceptance-test matrix

| ID | Area | Test | Expected result |
|---|---|---|---|
| P0-001 | Identity | Create duplicate canonical ID | Rejected |
| P0-002 | Domain | Create multiple variants for one content item | Valid relationship |
| P0-003 | State | Attempt invalid state transition | Rejected with reason |
| P0-004 | Persistence | Restart control plane with pending job | State preserved |
| P0-005 | Queue | Two workers claim same job | Only one valid lease |
| P0-006 | Recovery | Kill worker during job | Lease expires and job recovers |
| P0-007 | Stale result | Old lease holder submits result | Rejected |
| P0-008 | Idempotency | Deliver same event repeatedly | One logical effect |
| P0-009 | Scheduler | Scheduled job before due time | Not dispatched |
| P0-010 | Worker auth | Use expired/revoked credential | Denied |
| P0-011 | Capability | Worker claims unsupported task | Denied |
| P0-012 | Artifact | Checksum mismatch | Artifact not accepted for downstream use |
| P0-013 | Artifact access | Worker accesses unrelated artifact | Denied |
| P0-014 | Artifact versioning | Create new artifact output | Previous version unchanged |
| P0-015 | Governance | Distribution without authorization | Denied |
| P0-016 | Governance | Authorization has wrong artifact hash | Denied |
| P0-017 | Governance | Emergency pause active | Protected action denied |
| P0-018 | Quality | Hard-block result receives ordinary approval | Remains blocked |
| P0-019 | Rights | Unknown/restricted rights for intended use | Blocked per policy |
| P0-020 | Audit | Trace one workflow end to end | Correlated audit trail available |
| P0-021 | Secrets | Inject secret into failure path | Secret redacted |
| P0-022 | Hybrid | Local worker offline | Local-only task waits; cloud state persists |
| P0-023 | Hybrid | Local worker reconnects | Eligible work resumes without duplicate effects |
| P0-024 | Recovery | Restore from backup in test environment | State and references recover within agreed objectives |

These are proposed acceptance tests, not tests already executed.

---

## 10. Implementation safety and ownership protocol

Before any code work begins, the owner must separately authorize the implementation scope.

Required protocol:

1. Confirm ADR decisions and version the approved baseline.
2. Obtain explicit permission for repository inspection if needed.
3. Produce a current worktree/file ownership map without Git operations unless separately permitted.
4. Assign non-overlapping file ownership to the existing engineering owners.
5. Keep Kilo read-only for independent QA.
6. Define protected files and WIP preservation rules.
7. Establish a test baseline using approved commands and environment.
8. Make small, reviewable changes; no broad rewrites.
9. Do not install dependencies or change the environment without explicit approval.
10. Do not run production generation, upload or publishing.
11. Report exact files changed, tests executed, results, limitations and remaining risks.
12. Do not claim a phase complete without acceptance evidence.

**No agent assignment or execution is initiated by this document.**

---

## 11. Open decisions required before implementation authorization

| Decision | Current status | Needed |
|---|---|---|
| UUIDv7 or alternative | Proposed | Owner acceptance |
| Database technology/provider | Open | Technology and cost decision |
| Database-backed queue or broker | Open | Initial dispatch choice |
| API transport/schema tooling | Proposed | Owner acceptance |
| Worker credential mechanism | Proposed | Security review and acceptance |
| Object storage provider | Open | Provider, region, cost and retention |
| State-machine transition tables | Proposed | Detailed domain review |
| Initial quality hard gates | Open | Check catalogue and severity |
| Rights evidence policy | Open | Evidence types and exception rules |
| Backup RPO/RTO | Open | Operational targets |
| Monitoring and alerting | Open | Provider and alert ownership |
| Local/remote capability matrix | Open | Which jobs can run where |
| Implementation permissions | Not granted | Explicit owner authorization |

---

## 12. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Premature provider selection | Cost and lock-in | Keep provider interfaces abstract until requirements/cost review |
| Overbuilding queue infrastructure | Complexity | Start with durable DB dispatch; add broker only with evidence |
| Local/cloud dual authority | State divergence | Cloud owns shared state; local cache is disposable |
| Publishing bypass | Public unintended release | Central authorization boundary and negative tests |
| Weak rights evidence | Copyright/usage exposure | Unknown/restricted states block protected use |
| Overlapping agent edits | Conflicts and lost WIP | Explicit file ownership and no concurrent ownership |
| Unverified legacy assumptions | Integration regressions | Inspect only after explicit authorization; build adapter contract tests |
| Testing only happy paths | Fragile recovery | Failure-injection acceptance matrix |
| Cloud costs creep | Unexpected spend | Cost envelope and usage monitoring before deployment |
| Confusing test completion with production readiness | Unsafe launch | Separate implementation, operational and production gates |

---

## 13. Readiness gates

### Gate A — Architecture decisions
- ADR-001 through ADR-006 and ADR-010 reviewed.
- ADR-007 through ADR-009 governance policy direction reviewed.
- Canonical contracts reconciled with accepted ADRs.

### Gate B — Implementation authorization
- Exact scope and repository access permissions explicitly granted.
- File ownership and preservation plan approved.
- No ambiguity about prohibited Git or production actions.

### Gate C — Foundation acceptance
- P0 acceptance matrix passes.
- Failure recovery demonstrated.
- Security and authorization negative tests pass.
- Evidence and test reports retained.

### Gate D — Hybrid operational readiness
- Cloud control plane and storage configured under approved budget.
- Worker registration, revocation and reconnect verified.
- Backup/restore and monitoring operational.
- Runbooks and incident controls reviewed.

### Gate E — Production distribution readiness
- Every publishing path passes centralized governance.
- Rights and quality hard gates verified.
- Platform privacy defaults checked independently.
- Emergency pause tested.
- Production action separately authorized.

**Passing one gate does not automatically pass the next.**

---

## 14. Current status and next action

- P0 foundation scope: **DEFINED — PROPOSED**
- Component boundaries: **DEFINED — PROPOSED**
- Vertical slice: **DEFINED — NOT IMPLEMENTED**
- Acceptance matrix: **DEFINED — NOT EXECUTED**
- ADR owner approvals: **PENDING**
- Provider and budget decisions: **OPEN**
- Implementation authorization: **NOT GRANTED**
- Repository inspection / Git operations: **NOT AUTHORIZED**
- Production deployment / publishing: **NOT AUTHORIZED**

### Recommended next step

Conduct an owner decision review of the P0 ADRs in dependency order. Record each outcome as ACCEPT, ACCEPT WITH AMENDMENT, REJECT or DEFER. After the decisions are recorded, prepare a narrowly scoped implementation authorization brief and a preservation-safe execution plan. Do not start coding merely because this specification exists.

---

## 15. Change log

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-10-31 | Initial P0 foundation implementation specification |
