# NEXTDECODE — P0 Owner Review & Contract Freeze Decision Record

**Document ID:** `NEXTDECODE_P0_Owner_Review_Contract_Freeze_Decision_Record_0.1`  
**Version:** 0.1  
**Date:** 1 November 2026  
**Status:** OWNER DECISION DRAFT — NOT YET APPROVED  
**Scope:** P0 detailed contract review and freeze gate  
**Implementation authorization:** NOT GRANTED

---

## 1. Purpose

This record gives the product owner one controlled place to review the consolidated P0 design, confirm the already accepted architecture baseline, decide the remaining contract-level issues, and record whether the detailed P0 contracts are ready to be frozen.

It consolidates the decision context from:
- Artifact 08 — accepted owner contract decisions and detailed contract freeze materials.
- Artifact 07 — P0 Foundation Execution Plan & Acceptance Framework.
- P0 Foundation Implementation Specification.
- WP-0 — Current-System Baseline & Preservation Assessment.
- WP-1 — Canonical Domain & Persistence Boundary, v0.3.
- WP-2 — Durable Job & Workflow Execution, v0.1.
- WP-3 — Worker Registry & Contract Boundary, v0.1.
- WP-4 — Artifact Registration, Storage & Transfer, v0.1.
- WP-5 — Governance, Quality, Rights & Authorization, v0.1.
- WP-6 — Vertical-Slice Integration & Recovery Validation, v0.1.
- P0 Consolidation & Readiness Review, v0.1.

This is a decision record, not a replacement for those specifications. It does not authorize implementation or operational activity.

## 2. Decision authority and status vocabulary

The product owner is the final decision authority.

Use one of these dispositions for each decision:
- **ACCEPT** — approve the recommendation or existing wording as written.
- **ACCEPT WITH AMENDMENT** — approve only with a recorded amendment.
- **REJECT** — do not adopt the recommendation; record the alternative or reason.
- **DEFER** — intentionally leave open, with an owner and a condition for resolution.
- **NOT APPLICABLE** — explain why the decision does not apply to P0.

Do not infer acceptance from silence, a previous “next”, a prepared document or an agent recommendation.

A decision can be:
- **OWNER-ACCEPTED** — explicitly accepted by the owner or under the standing delegation rule.
- **RECOMMENDED** — a proposal awaiting owner decision.
- **OPEN** — not resolved.
- **DEFERRED** — deliberately postponed.
- **FROZEN** — incorporated into a formally approved detailed contract baseline.
- **IMPLEMENTED / VERIFIED** — supported by implementation or independent test evidence; never implied by design approval.

## 3. Decisions already accepted — carry forward without reopening

The following decisions are recorded as accepted. This document does not ask the owner to approve them again.

### 3.1 Architecture Decision Records

| ADR | Accepted direction |
|---|---|
| ADR-001 | UUIDv7 canonical IDs |
| ADR-002 | PostgreSQL-compatible relational database as authoritative shared-state store |
| ADR-003 | Database-backed durable queue with transactional outbox/inbox initially |
| ADR-004 | Versioned HTTP/JSON contracts with schema validation |
| ADR-005 | Unique worker identity, scoped short-lived credentials and capability authorization |
| ADR-006 | Relational artifact metadata; binaries behind object-storage abstraction |
| ADR-007 | Centralized authorization; publishing adapters cannot bypass; automatic publishing disabled pending separate policy |
| ADR-008 | QA outcomes `PASS`, `PASS_WITH_WARNINGS`, `NEEDS_REVIEW`, `BLOCKED`; hard blockers cannot be bypassed by ordinary approval |
| ADR-009 | Evidence-backed rights states and use-specific enforcement |
| ADR-010 | Separate lifecycle state machines for content, workflow, execution, review, approval, authorization and distribution |

### 3.2 Contract Freeze decisions

- CF-01–CF-15: explicitly accepted by the owner.
- CF-16–CF-21: accepted under the owner's standing delegation for routine recommendations.
- CF-22: explicitly accepted — Option A, centralized authorization.
- CF-23: accepted under standing delegation.
- CF-24: no-paid-services constraint explicitly accepted; operational/provider choices remain deferred.

### 3.3 Project-wide constraints

- NEXTDECODE remains a single-owner Creator Mode product at the initial scope.
- Existing Shorts Studio remains a specialised Python/FFmpeg engine behind a bounded adapter; no wholesale replacement.
- Future architecture direction remains hybrid: cloud control plane for authoritative shared workflow state, local worker for local-only/heavy rendering when available.
- Local-first/free-first development; no paid services or silent billing exposure.
- Human approval remains required for critical actions; automatic public publishing remains disabled.
- Approval, authorization, execution and confirmed external outcome remain distinct.
- Unknown/missing/ambiguous rights, approval or authorization fail closed for protected actions.
- Existing ownership remains unchanged: Qoder — Phase 11 engineering; OpenCode — Phase 10 engineering/closure; Kilo — independent read-only QA.
- No implementation, agent execution, repository changes, tests, dependency/environment changes, provider activation, deployment, production generation, upload or publishing without the relevant separate explicit authorization.

## 4. Consolidated contract-freeze review

This section identifies the contract-level resolutions needed to make the P0 package implementable without inventing semantics. The recommendations below are proposals, not accepted decisions.

### 4.1 Canonical domain and persistence — WP-1

**Recommended disposition:** Accept the WP-1 v0.3 logical model as the working contract baseline, subject to the following freeze conditions.

1. Canonical Data Dictionary remains authoritative for established entity fields and ownership.
2. `ContentItem` remains the shared editorial identity; `ContentVariant` remains a format/platform/language/treatment derivative.
3. `ContentVersion` identity is distinct from entity identity and schema version.
4. `ContentIdea` remains distinct from `ContentItem`; origin linkage is an explicit typed reference.
5. `Asset` remains distinct from `Artifact`; artifact bytes are immutable by version.
6. `StudioProduction` remains a production/run concept and does not replace `ContentItem`, `WorkflowRun` or `Artifact`.
7. Workspace scope, entity ownership and typed relationship semantics are enforced.
8. Exact field nullability, physical constraints, indexes, deletion behavior and transition tables must be explicitly specified in the canonical schema appendix before freeze.

**Owner disposition:** OPEN  
**Amendment / notes:** ______________________________________________

### 4.2 Workflow, job and event execution — WP-2

**Recommended disposition:** Accept the WP-2 semantic boundaries, with numerical operational settings deferred only where they are not required to define correctness.

Required contract statements:
- Workflow definition, workflow run, workflow task, job, job attempt, queue message, command, domain event, outbox message and inbox receipt are distinct.
- Orchestration, scheduling, queue delivery, worker execution and domain ownership remain separate.
- At-least-once delivery is assumed; idempotency and deduplication protect logical effects.
- A retry creates a new attempt identity while retaining the logical job identity.
- One authoritative active lease exists per job; fencing prevents stale attempts from committing.
- Same idempotency key plus same canonical payload returns the original logical result; same key plus different payload is a conflict.
- Ambiguous external side effects are reconciled before retry.
- Domain state change and corresponding outbox record commit transactionally.
- Workflow completion is distinct from job completion.

**Freeze-critical detail:** state transitions, terminal outcomes, cancellation and compensation, lease/fencing semantics, idempotency scope and conflict behavior, and outbox/inbox deduplication/recovery behavior.

**Potentially deferrable operational values:** numerical lease duration, heartbeat cadence, retry ceilings, backoff/jitter and retention durations, provided safe bounds and configuration ownership are defined and no unsafe default is assumed.

**Owner disposition:** OPEN  
**Amendment / notes:** ______________________________________________

### 4.3 Worker registry and trust — WP-3

**Recommended disposition:** Accept the WP-3 trust model.

Required contract statements:
- Worker identity is independent of hostname or machine name.
- Registration/trust lifecycle is explicit and auditable.
- Declared, verified, available and authorized capabilities are separate.
- Capability declaration never grants permission.
- Credentials are unique, scoped, short-lived and revocable.
- Local and remote workers share the same trust boundary.
- Worker assignment and completion validate identity, current lease and authorization.
- Job execution is bounded by filesystem, network, credential, artifact and resource scopes.
- Administrative, production, QA and publishing permissions remain separate.

**Freeze-critical detail:** worker lifecycle and trust transitions, identity proof/enrollment contract, capability verification contract, authorization interaction, revocation behavior for active jobs, and minimum isolation guarantees.

**Potentially deferrable:** exact credential issuer/format, isolation technology and numerical resource quotas, if the contract defines secure interfaces and prohibits unbounded access.

**Owner disposition:** OPEN  
**Amendment / notes:** ______________________________________________

### 4.4 Artifact registration and transfer — WP-4

**Recommended disposition:** Accept the WP-4 provider-neutral artifact boundary.

Required contract statements:
- Artifact metadata is authoritative; binary storage is abstracted.
- Artifact and ArtifactVersion are distinct; versions are immutable.
- Asset and Artifact are distinct.
- Manifests refer to exact artifact versions and preserve provenance/lineage.
- Transfer authorization is scoped, attributable and time-limited.
- Checksums, byte size and type-aware validation are recorded.
- Validation, availability, factual accuracy, rights, QA and approval are separate.
- Quarantine blocks ordinary downstream use.
- Repairs create new versions; temporary files are not durable registered artifacts.
- Storage locator alone never grants access.

**Freeze-critical detail:** artifact/version/manifest ownership, identity and relationship contracts; registration lifecycle; transfer authorization and completion semantics; integrity failure and quarantine behavior; provenance linkage.

**Potentially deferrable:** provider, region, replication, exact retention schedule and provider-specific encryption configuration, provided abstraction and enforcement requirements are explicit.

**Owner disposition:** OPEN  
**Amendment / notes:** ______________________________________________

### 4.5 Governance, quality, rights and authorization — WP-5

**Recommended disposition:** Accept the WP-5 enforcement boundary as mandatory.

Required contract statements:
- QA, rights, review, approval, authorization, execution and distribution outcome are distinct.
- QA outcomes: `PASS`, `PASS_WITH_WARNINGS`, `NEEDS_REVIEW`, `BLOCKED`.
- Rights states: `UNKNOWN`, `PENDING_REVIEW`, `CLEARED`, `RESTRICTED`, `EXPIRED`, `REVOKED`, `DENIED`.
- Approval decisions: `APPROVED`, `REJECTED`, `CHANGES_REQUESTED`, `EXPIRED`, `REVOKED`.
- Centralized authorization is the sole authorization authority.
- Protected actions are default-deny and fail-closed.
- Authorization is bound to exact action, target/resource, version/hash, destination and policy context; expiry and revocation are enforced.
- Hard QA blockers, unresolved rights and emergency pause cannot be bypassed by ordinary approval or retry.
- Every direct and indirect distribution path must enforce the same central boundary.
- No live upload or publishing occurs during P0 acceptance testing.

**Freeze-critical detail:** canonical policy evaluation request/decision schema; policy version and reason codes; exact action/resource/version/hash/destination binding; approval snapshot identity; emergency pause authority and behavior; enforcement obligations for all adapters.

**Owner disposition:** OPEN  
**Amendment / notes:** ______________________________________________

### 4.6 Vertical-slice acceptance — WP-6

**Recommended disposition:** Accept the WP-6 acceptance structure as the P0 evidence gate.

Required proof:
- One synthetic content item and variant move through a workflow/task and durable job.
- An authenticated eligible worker claims the job and produces deterministic test output.
- An immutable artifact is registered and linked to exact source/run/version references.
- State transitions and audit/correlation history are reconstructable.
- Failure injection proves recovery and stale/duplicate handling.
- Security-negative and governance tests prove deny-by-default behavior.
- No unauthorized external side effects occur.
- Kilo performs independent read-only QA.
- Owner records final acceptance or rejection based on evidence and limitations.

**Owner disposition:** OPEN  
**Amendment / notes:** ______________________________________________

## 5. Safe deferrals — proposed disposition

The following may remain open for P0 only if the contract is provider-neutral and the deferral does not weaken security, integrity, recoverability or acceptance:

| Area | Proposed disposition |
|---|---|
| Cloud provider/account/region/deployment topology | DEFER |
| Hosted database provider and production sizing | DEFER |
| Object-storage provider/region/replication | DEFER |
| Credential issuer and provider-specific token format | DEFER only after protocol/security requirements are frozen |
| Numerical lease/heartbeat/retry values | DEFER only after semantics, bounds and configuration ownership are defined |
| Artifact retention/backup/legal-hold durations | DEFER only after lifecycle ownership and enforcement hooks are defined |
| Monitoring vendor and production alert thresholds | DEFER |
| Production RPO/RTO and restore cadence | DEFER; production readiness cannot be claimed |
| Budget and paid-service activation | DEFER; no spending authorized |
| Advanced broker, multi-user/team, SaaS, billing, multi-brand and broad cloud rendering | OUT OF P0 SCOPE |

**Owner disposition:** OPEN  
**Amendment / notes:** ______________________________________________

## 6. Contract freeze gate checklist

The detailed P0 contract set may be marked FROZEN only when every mandatory item below has explicit evidence or a documented owner-approved exception.

### Contract completeness
- [ ] Canonical entity ownership and definitions align with the 12-contract architecture.
- [ ] ContentItem / ContentVariant / ContentVersion semantics are consistent.
- [ ] Required entity fields, nullability, references and constraints are specified.
- [ ] Lifecycle states, valid transitions, terminal states and reopen/cancel behavior are specified.
- [ ] Workflow/job/attempt/lease/retry/idempotency semantics are implementable without invention.
- [ ] Command/event/outbox/inbox envelopes and compatibility rules are specified.
- [ ] Worker identity, trust, capability, credential and isolation boundaries are specified.
- [ ] Artifact, manifest, transfer, validation, quarantine and provenance semantics are specified.
- [ ] QA, rights, review, approval, authorization and distribution gates are mutually consistent.
- [ ] Error taxonomy, recovery ownership, audit and correlation requirements are specified.
- [ ] Shorts Studio adapter boundary and bypass-prevention obligations are explicit.
- [ ] Provider and cost deferrals are explicit and do not create unsafe ambiguity.

### Owner and governance
- [ ] Each proposed resolution is accepted, amended, rejected or deferred by the owner.
- [ ] All amendments are reflected in the authoritative contract documents.
- [ ] No unresolved critical ambiguity is silently treated as accepted.
- [ ] Consolidated owner decision record is versioned and attributable.
- [ ] Formal freeze disposition is explicitly recorded.

**Freeze decision:** NOT YET MADE.

## 7. Implementation authorization remains a separate decision

Even after detailed contract freeze, implementation does not automatically become authorized.

A separate bounded implementation authorization must specify:
- Exact work package(s) and deliverables.
- Exact repository/project identity and permitted inspection scope.
- Preservation rules for all existing modified and untracked work.
- File-level ownership and allowed write boundaries.
- Whether tests may be run and which commands are permitted.
- Whether dependency, environment or credential changes are permitted.
- Whether Git operations are permitted (default: no).
- Which agents may execute which tasks.
- Acceptance evidence and independent QA plan.
- Explicit prohibition or permission for external side effects.
- Explicit budget/provider/deployment permission, if any.

The existing local working tree must remain preserved. No reset, revert, stash, clean, deletion, broad staging, commit, push, branch change, agent execution, deployment, paid activation, production generation, upload or publishing is authorized by this decision record.

## 8. Owner decision summary

Complete this section only after the owner has made the decisions.

| Decision | Owner disposition | Date / reference |
|---|---|---|
| WP-1 canonical domain contract | PENDING | |
| WP-2 execution contract | PENDING | |
| WP-3 worker trust contract | PENDING | |
| WP-4 artifact contract | PENDING | |
| WP-5 governance contract | PENDING | |
| WP-6 acceptance framework | PENDING | |
| Safe deferrals | PENDING | |
| Consolidated detailed contract freeze | NOT FROZEN | |
| P0 implementation authorization | NOT GRANTED | |

**Owner notes / conditions:**

____________________________________________________________________

____________________________________________________________________

____________________________________________________________________

## 9. Plain-language explanation

This document is the sign-off sheet for the design.

It records what you have already decided, puts the remaining technical choices in front of you, and defines the proof needed before the design can be called frozen. It deliberately keeps implementation permission separate.

A frozen design means the team has clear instructions. It does not mean the software has been built, tested or approved for production.

---

**Current disposition:** OWNER DECISION DRAFT. Accepted ADR/CF decisions are carried forward. Detailed contract freeze is pending. Implementation authorization is NOT GRANTED.
