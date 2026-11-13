# NEXTDECODE — Artifact 08
## Consolidated Implementation Reference & Detailed Contract Freeze Candidate

**Version:** 1.2  
**Status:** **CONSOLIDATED FREEZE CANDIDATE — OWNER CONFIRMATION PENDING**  
**Prepared:** 1 November 2026  
**Scope:** P0 foundation and implementation contract reference

> **Status and authorization notice:** This document consolidates accepted owner decisions and proposes remaining detail for review. It is not a formal declaration that the detailed contract is frozen. It does not authorize repository changes, implementation, tests, agent execution, dependency installation, Git operations, environment/credential changes, provider activation, deployment, spending, production generation, upload, or publishing. Those actions require appropriate separate authorization.

---

# 1. Executive summary

NEXTDECODE is a single-owner Creator Mode content operating system for the NEXTDECODE brand. It governs the content lifecycle from discovery and research through creation, review, production, distribution, analytics, and learning.

The system is not intended to replace the existing Shorts Studio. Shorts Studio remains a specialist Python/FFmpeg production engine integrated through a bounded adapter. The wider system provides canonical content identity, workflow orchestration, evidence and rights governance, worker coordination, artifact registration, review and approval, authorization, and distribution controls.

The long-term direction is hybrid:
- A cloud control plane is intended to become authoritative for shared workflow and control state.
- Local workers may perform local-only or heavy rendering when the user's PC is available.
- Remote workers may be supported under the same identity, trust, capability, authorization, and audit rules.
- This does not select a cloud provider or authorize deployment or paid infrastructure.

Initial development remains local-first and free-first, with a ₹0 initial spending target. No paid service or charge-generating infrastructure may be activated without explicit approval.

## 1.1 Lifecycle

`Discover → Research → Verify → Strategize → Brief → Create → Review → Produce → Approve → Distribute → Analyze → Improve`

## 1.2 Twelve logical modules

These are product-level capability areas, not a mandate to create twelve deployable services:

1. Workspace & Control Center
2. Content Graph
3. Knowledge Management
4. Research Intelligence
5. Brand Intelligence
6. Strategy & Planning
7. Content Quality Intelligence
8. Multiformat Creation Engine
9. Asset Management
10. Automation & Agent Orchestration
11. Distribution Studio
12. Analytics & Learning

The exact canonical contract ownership mapping must be reconciled against the original Canonical Contracts Pack before being treated as frozen.

## 1.3 Shorts Studio pipeline

`Topic / Brief → Research and Evidence → Claim Ledger → Script → Storyboard and Shot Planning → Visual Assets → Rendering → QA → Review Package → Approval → Publishing → Analytics and Learning`

---

# 2. Authority, status and decision precedence

This document distinguishes four classes:

| Class | Meaning |
|---|---|
| **ACCEPTED** | Explicitly accepted by the owner or accepted under standing delegation for CF-01–CF-24. |
| **PROPOSED** | Recommended implementation detail or example; not yet owner-frozen. |
| **DEFERRED** | Deliberately left for later decision, measurement, or provider-specific design. |
| **OPEN BLOCKER** | Must be resolved or explicitly bounded before detailed contract freeze or acceptance of affected implementation. |

Decision precedence:
1. The accepted owner decision record and implementation reference using **CF-01–CF-24** are authoritative.
2. Older detailed freeze-pack and open-decision documents are supporting review material; their older CF numbering must not be mixed into the accepted numbering.
3. Where older proposals conflict with accepted CF-01–CF-24, the accepted owner decision governs.
4. Recommendations in this document do not become accepted merely by appearing here.

### CF numbering discrepancy

An older open-decision matrix uses CF-01–CF-25 for a different breakdown. Its topic mapping differs from the accepted owner decision record. Use accepted owner CF-01–CF-24 as the decision authority. Treat the older matrix as historical review-process material only; do not copy its numbering into implementation tickets, schemas, or migration names without an explicit cross-reference.

---

# 3. Accepted owner decisions — CF-01 to CF-24

This is a concise implementation summary, not a replacement for the complete authoritative decision record.

| Decision | Accepted direction |
|---|---|
| CF-01 | `ContentItem` is the shared editorial identity. `ContentVariant` is a derivative for format, platform, language, or treatment. |
| CF-02 | One authoritative owner per canonical entity; typed cross-domain references; no competing IDs. Relationships do not imply permission. Twelve contract ownership categories do not imply twelve services. |
| CF-03–CF-12 | Retain the accepted decisions in the authoritative owner record and implementation reference. Do not infer missing details from this summary or the older differently numbered matrix. |
| CF-13 | Worker identity independent of hostname/machine; registration/trust lifecycle; declared, verified, available and authorized capabilities are distinct; scoped short-lived revocable credentials; local and remote workers follow the same trust model. |
| CF-14 | Capability declarations are not permissions. Jobs are bounded and isolated with scoped filesystem, network, credential and artifact access. Resource limits are by job class; numeric limits deferred. Admin, production, QA and publishing permissions remain separated. |
| CF-15–CF-19 | Retain the accepted decisions in the authoritative owner record and implementation reference. Do not silently replace their wording with illustrative schemas. |
| CF-20 | Rights vocabulary: `UNKNOWN`, `PENDING_REVIEW`, `CLEARED`, `RESTRICTED`, `EXPIRED`, `REVOKED`, `DENIED`. |
| CF-21 | Approval vocabulary: `APPROVED`, `REJECTED`, `CHANGES_REQUESTED`, `EXPIRED`, `REVOKED`. |
| CF-22 | Centralized authorization authority — Option A. |
| CF-23 | Retain the accepted decision in the authoritative owner record and implementation reference; do not infer an alternate meaning from the older matrix. |
| CF-24 | No paid services, silent billing exposure, or charge-generating infrastructure without explicit approval. Provider and operational choices remain deferred. |

**Traceability requirement:** Before sign-off, reproduce the exact accepted wording of every CF-01–CF-24 row from the authoritative owner decision record. This summary intentionally does not invent missing row text for CF-03–CF-12 or CF-15–CF-19.

---

# 4. Core domain model

## 4.1 Content identity — ACCEPTED direction

- `ContentItem` is the shared editorial identity.
- `ContentVariant` is a derivative for format, platform, language, or treatment.
- Canonical identity is not duplicated across modules.
- Cross-domain relationships do not grant access or permission.

**PROPOSED:** Give each canonical entity an immutable UUIDv7 identifier; store explicit schema/contract versions; represent derivation relationships explicitly; keep editorial identity separate from renders, uploads, review packages and distribution attempts.

**Plain explanation:** A video idea is the enduring content item. A YouTube Short, Instagram Reel, Hindi adaptation or alternate cut is a variant. A particular MP4 export is an artifact, not a new content identity.

## 4.2 Canonical ownership

**ACCEPTED:** Each canonical entity has one authoritative owner; cross-domain relationships are typed references; no competing canonical IDs; relationships do not imply authorization; twelve ownership categories do not mean twelve services.

**OPEN:** Reconcile exact ownership-category names and mappings against the original Canonical Contracts Pack. Do not freeze an invented domain-to-entity table.

**Plain explanation:** One place owns the truth for a record. Other parts may refer to it, but cannot quietly create a second source of truth.

## 4.3 Identity and versioning

Canonical identity is stable and immutable; versions are explicit; reviews, approvals, QA results, manifests and authorizations refer to exact versions where relevant.

**PROPOSED:** UUIDv7 is the accepted ID direction recorded in ADR-001. Version identifiers should be unambiguous. A material edit creates a new version. New versions do not inherit prior approval automatically.

**OPEN:** Exact version numbering, revision semantics, uniqueness constraints and migration behavior require final schema specification.

---

# 5. Workflow, jobs and durable execution

## 5.1 Accepted principles

- Durable job execution is required; process-local in-memory state is insufficient as shared workflow authority.
- At-least-once delivery is the operating assumption; do not promise exactly-once execution.
- Attempts and state transitions are durable and traceable.
- Idempotency is required for safe retries.
- Leases prevent stale workers from overwriting newer attempts.
- Transactional outbox/inbox is the initial accepted direction.
- Failure, retry, cancellation and recovery are auditable.
- Policy denials cannot be bypassed by retrying.

## 5.2 Proposed job states — NOT FROZEN

Illustrative lifecycle: `QUEUED → DISPATCHED → CLAIMED → RUNNING → SUCCEEDED`.

Possible additional states include `RETRY_WAIT`, `FAILED`, `CANCELLED`, `EXPIRED`, `BLOCKED`, and `RECONCILIATION_REQUIRED`. This is an example only; the final state machine and transition contract remain open.

## 5.3 Lease and retry

**ACCEPTED:** A worker claims a bounded assignment; a lease has an owner and expiry; heartbeat/renewal demonstrates continued ownership; stale workers cannot overwrite newer attempts; attempts are durable; idempotency protects against duplicate delivery and uncertain retries.

**DEFERRED numeric parameters:** lease duration, heartbeat interval/tolerance, retry count, backoff, jitter, dead-letter/reconciliation policy, idempotency scope/retention, and outbox/inbox retention. Choose through job-class measurements and recovery tests, not guesses.

**Plain explanation:** A job can be delivered more than once. Duplicate delivery must be safe, every attempt recorded, and an old worker prevented from claiming success after its lease expires.

---

# 6. Worker identity, trust and capability

**ACCEPTED:**
- Worker identity is independent of hostname and machine.
- Worker enrollment and trust have an explicit lifecycle.
- Declared, verified, available and authorized capabilities are separate facts.
- Credentials are scoped, short-lived and revocable.
- Local and remote workers use the same governance model.
- Capability declaration is not permission.
- Jobs are bounded and isolated, with scoped filesystem, network, credential and artifact access.
- Admin, production, QA and publishing permissions remain separated.

**PROPOSED model:** Keep trust, availability, capability verification and assignment authorization as separate dimensions.

**OPEN:** Enrollment protocol and issuer; credential rotation/revocation; capability catalogue and evidence; numeric resource quotas; isolation technology; worker draining, quarantine, suspension and recovery transitions.

**Plain explanation:** A machine saying “I can render video” does not prove it is trusted, online, technically capable, or authorized for this particular job. Those checks are separate.

---

# 7. Artifact and asset management

**ACCEPTED:**
- Asset and Artifact are distinct concepts.
- Artifact metadata is relational and authoritative.
- Binary storage sits behind an abstraction.
- Artifact IDs and versions are immutable.
- Checksums/integrity evidence are required.
- Transfers are controlled and attributable.
- Manifests reference exact artifact versions.
- Quarantine is supported.
- Repair creates a new version rather than silently replacing an immutable artifact.

**PROPOSED, not frozen:** Example artifact lifecycle: `REGISTERED → AVAILABLE`, with possible `TRANSFER_PENDING`, `QUARANTINED`, `UNAVAILABLE`, `RETIRED`, or `SUPERSEDED` states.

**OPEN:** Exact schemas; manifest and exact-version reference rules; checksum algorithms; transfer/resume protocol; quarantine rules; retention/deletion/legal hold; storage provider.

**Plain explanation:** The database records what a file is and which exact version it is. The bytes may live elsewhere. Repair creates a new version so old approvals and evidence remain meaningful.

---

# 8. Research evidence, claims and rights

## 8.1 Rights vocabulary — ACCEPTED CF-20

`UNKNOWN`, `PENDING_REVIEW`, `CLEARED`, `RESTRICTED`, `EXPIRED`, `REVOKED`, `DENIED`.

## 8.2 Older proposal reconciliation — compatibility note only

| Older proposed term | Accepted CF-20 term | Status |
|---|---|---|
| `PENDING_VERIFICATION` | `PENDING_REVIEW` | Proposed mapping; migration requires approval. |
| `PROHIBITED` | `DENIED` | Proposed mapping; confirm semantic equivalence before migration. |

`EXPIRED` and `REVOKED` remain distinct from `DENIED`. Do not migrate data based solely on this table.

## 8.3 Evidence and claims

Rights must be evidence-backed and enforcement is use-specific. Unknown or ambiguous rights do not grant permission. Evidence and decisions are attributable and auditable.

**PROPOSED:** Link claim records to supporting evidence and source lineage. Distinguish factual support from permission to reuse an asset. Preserve historical decisions when evidence changes.

**OPEN:** Evidence fields/types; use-scope dimensions (asset, territory, platform, format, duration, purpose, monetization, attribution); expiry/revocation rules; reviewer authority; rights-to-artifact and rights-to-distribution enforcement; legacy migration.

**Plain explanation:** “This source supports the fact” and “we are allowed to use this source in a published video” are different questions. Check both.

---

# 9. Quality assurance and review

## 9.1 QA outcomes — ACCEPTED CF-08 direction

`PASS`, `PASS_WITH_WARNINGS`, `NEEDS_REVIEW`, `BLOCKED`.

QA evidence is immutable and tied to the exact content/artifact version and applicable policy. A score cannot override a hard blocker.

## 9.2 Approval decisions — ACCEPTED CF-21

`APPROVED`, `REJECTED`, `CHANGES_REQUESTED`, `EXPIRED`, `REVOKED`.

An older request example containing only `APPROVED` and `REJECTED` is incomplete and must not narrow the accepted vocabulary.

## 9.3 Review binding

**PROPOSED:** Bind each review/approval record to exact content item and variant, content version, artifact/manifest version and checksum where applicable, review package version, actor and timestamp, decision and reason, and policy/scope context. New versions do not inherit approval.

**OPEN:** QA catalogue/severity; policy versioning; evidence required per outcome; re-review triggers; expiry/revocation; exact schema and transition preconditions.

**Plain explanation:** Approval applies to the exact thing reviewed—not every future edit, render or upload with the same title.

---

# 10. Authorization and distribution governance

## 10.1 Central authorization — ACCEPTED CF-22 Option A

- One centralized authorization authority.
- Default-deny and fail-closed.
- Authorization is distinct from approval.
- Authorization binds action, resource, version, destination, policy and time context.
- APIs, workers and adapters enforce authorization.
- Expiry and revocation are enforced.
- Agents cannot expand their own authority.
- Publishing adapters cannot bypass central governance.

## 10.2 Separate concepts

| Concept | Question |
|---|---|
| Review/approval | Has a reviewer accepted this exact version for the stated review purpose? |
| Authorization | May this actor perform this exact action on this exact resource/version and destination now? |
| Execution | Did the system actually carry out the authorized action? |
| Publication result | Did the external platform confirm the intended distribution outcome? |

## 10.3 Publishing safety

Automatic public publishing remains disabled pending separate policy. Direct platform adapters and direct pipeline entry points must not bypass governed orchestration, run identity, QA and authorization. Ambiguous external outcomes require reconciliation before repeating. Human approval is required for critical actions.

**OPEN:** Authorization request/decision schema; policy language/version; decision lifetime and revocation propagation; destination/platform-account binding; delegation; external-action reconciliation; audit retention.

**Plain explanation:** Clicking “approve” does not automatically give every worker permission to publish. The system separately checks who may do what, to which version, where and when.

---

# 11. Errors, audit and recovery

**ACCEPTED:** Failures and attempts are durable and traceable. Severity and retryability are independent. Retries cannot bypass policy denials. Ambiguous external actions are reconciled before repetition. Audit history supports reconstruction. Diagnostics access is controlled.

**PROPOSED error categories, not frozen:** validation/contract; authentication/authorization; rights/policy; worker capability/availability; lease/ownership; dependency/network; artifact transfer/integrity; external platform/ambiguous outcome; internal processing/resource limit.

**OPEN:** Canonical error codes/payload; severity; retryability by action; reconciliation workflow; audit schema/retention; sensitive-data redaction; recovery objectives.

**Plain explanation:** The system should explain what failed, which attempt failed, whether retry is safe, and whether an external action may already have happened.

---

# 12. Architecture decisions and technology boundaries

| ADR | Accepted direction |
|---|---|
| ADR-001 | UUIDv7 canonical IDs; opaque and immutable. |
| ADR-002 | PostgreSQL-compatible relational DB as authoritative shared-state store. |
| ADR-003 | DB-backed durable queue with transactional outbox/inbox initially. |
| ADR-004 | Versioned HTTP/JSON contracts with schema validation. |
| ADR-005 | Unique worker identity, scoped short-lived credentials and capability authorization. |
| ADR-006 | Relational artifact metadata; binaries behind object-storage abstraction. |
| ADR-007 | Centralized authorization; publishing adapters cannot bypass; automatic publishing disabled pending separate policy. |
| ADR-008 | QA outcomes defined above; hard blockers cannot be bypassed by ordinary approval. |
| ADR-009 | Evidence-backed rights states with use-specific enforcement. |
| ADR-010 | Separate lifecycle state machines for content, workflow, execution, review, approval, authorization and distribution. |

Provider selection, deployment topology, storage product, managed database, queue product, model provider and cloud operational plan remain deferred.

The long-term hybrid target is a cloud control plane authoritative for shared workflow/control state, with local workers for local-only or heavy rendering when available and optional remote workers under the same trust model. This target does not authorize deployment, provider activation, paid services, public network exposure or production credentials.

**Plain explanation:** Design for cloud and local machines without choosing or paying for a cloud provider today.

---

# 13. Existing system boundary and preservation

Shorts Studio remains a specialist engine integrated through a bounded adapter; it is not to be replaced wholesale.

Historical baseline observations (not freshly retested):
- `api/main.py` used process-local in-memory job state and a lock, not durable shared workflow state.
- `n8n_runner.py` was an authenticated fixed-command local runner, not a worker registry or durable lease dispatcher.
- Inspected n8n workflow called runner endpoints rather than FastAPI `/start`.
- Inspected compose setup had n8n and runner, without the proposed PostgreSQL durable workflow/queue foundation.
- `workspace_sync.py` used a SQLite prototype plus external mirrors, not the canonical workflow/task model.
- `review_ledger.py` was a CSV feedback ledger, not canonical immutable approval history.
- `review_bundle.py` produced a JSON review package, not immutable event-sourced approval history.
- Publishing checks existed, but direct platform adapters could be invoked separately.
- Inspected YouTube uploaders explicitly set `privacyStatus` to `public`.
- Analytics JSON was not proven linked to canonical immutable versions.

These observations came from an earlier remote-baseline inspection and may be stale. They are not claims about the current local tree or fresh test results.

Preserve existing tracked modifications, untracked work, tests, fixtures, docs, scripts and generated evidence. No reset, revert, stash, clean, delete, overwrite, rename, broad-stage, commit, push, branch or remote changes without explicit authorization.

**Plain explanation:** Wrap and govern useful Shorts Studio capabilities. Do not throw away existing work or assume older components are safe to delete.

---

# 14. P0 foundation work packages

These seven P0 work packages are distinct from the seven explanatory batches.

| WP | Work package | Purpose |
|---|---|---|
| WP-0 | Current system baseline and preservation assessment | Understand the existing system and protect current work. |
| WP-1 | Canonical domain and persistence foundation | Canonical entities, identity, versions and durable shared state. |
| WP-2 | Durable job and workflow execution | Durable orchestration, attempts, leases, idempotency and recovery. |
| WP-3 | Worker registry and contract boundary | Worker identity, trust, capabilities and bounded execution. |
| WP-4 | Artifact registration and transfer | Immutable metadata, manifests, integrity and controlled transfer. |
| WP-5 | Governance, quality and rights foundation | Evidence, rights, QA, review, approval and authorization. |
| WP-6 | Vertical-slice integration and recovery validation | Governed end-to-end path and recovery behavior. |

## WP-0 status

**Conditionally complete as a baseline/preservation assessment only.** It does not establish current local runtime health, fresh test results, independent Kilo QA acceptance, formal detailed contract freeze or production readiness. No further repetitive Git inventory is required merely to restate this status.

## P0-A vertical slice acceptance target — proposed, not executed

1. Create one test content item and variant.
2. Create a workflow and dependent task.
3. Dispatch a durable job.
4. Claim it with an authenticated worker.
5. Produce deterministic test output.
6. Register an immutable artifact.
7. Record results and state transitions.
8. Inject failures and demonstrate recovery/audit reconstruction.

**Plain explanation:** Prove one small content item can travel through the governed system, including a deliberate failure and safe recovery, before scaling it.

---

# 15. Phase 10, Phase 11 and independent QA

## Phase 10 — historical report

OpenCode was engineering owner. A historical handover reported 535 passing tests, focused tests and shell/compile checks, and Run Tracker/promotion journal/review provenance integration.

Still open or unverified in that historical report: live production run; runtime storm/recovery; post-promotion failure edge; independent Kilo QA. Do not label Phase 10 fully closed or production-ready on this evidence alone.

## Phase 11 — historical report

Qoder was engineering owner. Historical reports included ShotPlan traceability and focused tests.

Inherited reported gaps:
- G1: storyboard approval gate defaulted to `warn`, not enforced by default.
- G2: rights evidence not enforced end-to-end by publishing.
- G3: unsupported factual claims warning-only.
- U1: direct platform adapters could bypass parent publisher gate.
- D1: direct pipeline could bypass governed orchestration/run identity/quality gates.
- T1: shot/beat/render traceability incomplete.
- R1: Run Tracker runtime/recovery evidence missing.

These are inherited report findings, not freshly retested results.

Kilo is independent read-only QA owner. Independent acceptance evidence remains pending/unavailable in the supplied status.

**Plain explanation:** A past test report is useful evidence, but it does not prove today's code is healthy or that an independent reviewer accepted it.

---

# 16. Open blockers before detailed contract freeze

1. Reconcile twelve canonical ownership categories against the original Canonical Contracts Pack.
2. Specify exact entity fields, types, nullability, constraints, foreign keys, uniqueness and indexes.
3. Specify lifecycle states, transition preconditions, terminal behavior, reopening, cancellation, expiry and revocation.
4. Specify worker enrollment, credential issuer/protocol, capability catalogue, verification evidence, revocation and numeric limits.
5. Specify job lease, heartbeat, retry, backoff, jitter, dead-letter, idempotency and outbox/inbox retention.
6. Specify asset/artifact schemas, manifest, checksums, transfer, quarantine, retention and repair.
7. Specify rights evidence, use-specific scope, expiry/revocation and legacy vocabulary migration.
8. Specify QA catalogue, policy versions, review package binding, actor/reason schema and re-review triggers.
9. Specify authorization request/decision, policy evaluation, destination binding, expiry/revocation and adapter enforcement.
10. Specify error codes, severity/retryability, reconciliation, audit schema and retention.
11. Keep provider/deployment deferred under CF-24 unless separately approved.
12. Obtain implementation, failure-injection, recovery-reconstruction and independent QA evidence separately.

---

# 17. Implementation and operational guardrails

- No paid services, silent billing exposure or charge-generating infrastructure without explicit approval.
- No provider activation or cloud deployment from this document.
- No repository mutation, Git operation, tests, dependency installation, environment/credential changes or agent execution without appropriate explicit authorization.
- No production generation, upload or publishing without explicit authorization.
- Automatic public publishing remains disabled pending separate policy.
- Human approval is required for critical actions.
- Approval, authorization, execution and publication result remain separate.
- Unknown/missing/ambiguous rights, approval or authorization fail closed.
- Hard QA, rights and policy blockers cannot be bypassed by ordinary approval.
- Workers and agents cannot expand their own scope.
- Existing work must be preserved.

---

# 18. Final consistency audit — corrections incorporated

1. Accepted owner CF-01–CF-24 is authoritative; older CF-01–CF-25 matrix is historical and must not be mixed in.
2. CF-20 accepted rights vocabulary governs. Older `PENDING_VERIFICATION` and `PROHIBITED` are compatibility proposals only; `EXPIRED` and `REVOKED` remain distinct from `DENIED`.
3. CF-21 includes all five approval decisions, not only `APPROVED` and `REJECTED`.
4. Job state examples are proposed, not accepted.
5. Worker trust, availability, capability verification and authorization remain separate.
6. Artifact lifecycle examples are proposed, not accepted.
7. Central authorization is accepted; detailed schemas and transitions remain open.
8. Twelve domain names/mappings require canonical-pack reconciliation.
9. Error categories are recommendations, not frozen.
10. Exact schemas and transition preconditions remain open.
11. Acceptance criteria are proposed, not executed evidence.
12. This document does not authorize implementation, deployment, spending, production generation, upload or publishing.

---

# 19. Owner confirmation checklist

Before declaring formal detailed contract freeze, confirm:

- [ ] Consolidated accepted-decision summary matches the authoritative CF-01–CF-24 record.
- [ ] Twelve canonical ownership categories are reconciled against the original Canonical Contracts Pack.
- [ ] Proposed schemas and state machines are reviewed and accepted or explicitly left open.
- [ ] Worker enrollment, capability verification and credential lifecycle are specified.
- [ ] Job lease, retry, idempotency and recovery parameters are specified or safely deferred.
- [ ] Artifact manifest, integrity, transfer and retention rules are specified.
- [ ] Rights evidence and legacy vocabulary migration are specified.
- [ ] QA/review package and exact-version approval binding are specified.
- [ ] Central authorization contract and enforcement points are specified.
- [ ] Error, reconciliation and audit contracts are specified.
- [ ] Provider/deployment choices remain deferred unless separately approved.
- [ ] Formal freeze is explicitly declared by the owner.

Until then, status remains **CONSOLIDATED FREEZE CANDIDATE — OWNER CONFIRMATION PENDING**.

---

# Appendix A — Plain-language glossary

| Term | Meaning |
|---|---|
| Canonical entity | The one authoritative record for a thing. |
| Content item | The enduring editorial idea or piece of content. |
| Content variant | A specific format/platform/language/treatment derivative. |
| Artifact | A concrete output file or immutable deliverable. |
| Manifest | A structured list of exact artifact versions that belong together. |
| Idempotency | Repeating a request safely without accidentally doing the action twice. |
| Lease | A time-limited claim to work on a job. |
| Outbox/inbox | Durable records that safely pass events between database transactions and workers. |
| Worker | A machine/process that executes a bounded assignment. |
| Capability | A task type a worker can technically perform; not permission. |
| QA | Evidence-based checks on a particular version. |
| Approval | A review decision on an exact version for a stated purpose. |
| Authorization | Permission for a specific action on a specific resource/version/destination. |
| Reconciliation | Determining what happened when an external action's result is uncertain. |
| Fail closed | Missing or ambiguous evidence/permission means deny rather than guess. |
| Vertical slice | One small end-to-end path through the system, including recovery. |

# Appendix B — Source and evidence limitations

This consolidation is based on the accepted owner decisions and detailed freeze-pack/open-decision materials surfaced during the consistency audit, together with the project baseline and historical phase reports summarized in the working record.

The complete authoritative wording for every accepted CF row should be checked against the original owner decision record during final sign-off. This document deliberately avoids inventing missing CF-03–CF-12 and CF-15–CF-19 wording.

Historical code and test observations are not fresh verification. No repository inspection, test execution, independent QA, implementation or deployment was performed to create this candidate.

---

**End of Artifact 08 v1.2 — Consolidated Freeze Candidate**
