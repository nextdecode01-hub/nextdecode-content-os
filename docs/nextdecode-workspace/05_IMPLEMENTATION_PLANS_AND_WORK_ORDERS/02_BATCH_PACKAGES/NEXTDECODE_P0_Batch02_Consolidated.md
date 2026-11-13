NEXTDECODE

P0 IMPLEMENTATION PACKAGE

BATCH 02 — CONSOLIDATED DOCUMENT

Six coordinated documents • Version 0.1 • 1 November 2026

Planning and reconciliation material — not implementation authorization

## 01 — Master Traceability Register

Version: 0.1

Status: Consolidation candidate; owner review required

Authority: This register indexes decisions and requirements. It does not create or alter owner decisions.

### 1. Purpose

Connect authoritative decisions, contracts, work packages, acceptance oracles and evidence. Keep decision authority, design maturity, implementation state and verification state independent.

### 2. Register conventions

Four status dimensions are tracked independently:

- Decision: OWNER-ACCEPTED, PROPOSED, OPEN, DEFERRED, plus provenance/disposition labels such as SOURCE-DEFINED, CARRIED_FORWARD, OWNER-RESERVED.

- Design: DRAFT, RECONCILED, CANDIDATE, FROZEN.

- Implementation: NOT_IMPLEMENTED, IN_PROGRESS, IMPLEMENTED, PARTIALLY_IMPLEMENTED, RETIRED.

- Evidence: NOT_RUN, NOT_VERIFIED, VERIFIED, FAILED, NOT_APPLICABLE, INCONCLUSIVE.

These dimensions must never be inferred from one another. PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW, and BLOCKED are QA outcomes. UNKNOWN_OUTCOME is an execution/side-effect state.

### 3. Accepted architecture decisions

The following were recorded as accepted in the existing owner decision history. This register carries them forward; it does not re-approve them.

| ID | Accepted decision | Primary traceability | Implementation/evidence |
| --- | --- | --- | --- |
| ADR-001 | UUIDv7 canonical immutable IDs | Architecture Decision Register | Not established by acceptance |
| ADR-002 | PostgreSQL-compatible relational DB as authoritative shared-state store | Architecture Decision Register | Provider/runtime not selected |
| ADR-003 | DB-backed durable queue with transactional outbox/inbox initially | Architecture Decision Register | Not established |
| ADR-004 | Versioned HTTP/JSON contracts with schema validation | Architecture Decision Register | Not established |
| ADR-005 | Unique worker identity, scoped short-lived credentials and capability authorization | Architecture Decision Register | Not established |
| ADR-006 | Relational artifact metadata; binaries behind storage abstraction | Architecture Decision Register | Not established |
| ADR-007 | Centralized authorization; publishing adapters cannot bypass; automatic publishing disabled pending policy | Architecture Decision Register | Historical bypass risks remain to be verified |
| ADR-008 | QA outcomes PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW, BLOCKED; hard blockers not bypassed by ordinary approval | Architecture Decision Register | Not established |
| ADR-009 | Evidence-backed rights states and use-specific enforcement | Architecture Decision Register | Not established |
| ADR-010 | Separate lifecycle state machines for content, workflow, execution, review, approval and distribution | Architecture Decision Register | Not established |

### 4. Accepted contract decisions

| ID | Accepted decision | Status note |
| --- | --- | --- |
| CF-01 | ContentItem is shared editorial identity; ContentVariant is a format/platform/language/treatment derivative | Owner-accepted |
| CF-02 | One authoritative owner per canonical entity; typed cross-domain refs; relationships do not imply permission | Owner-accepted |
| CF-03–CF-12 | Refer to authoritative Artifact 08 decision record for exact individual wording | Owner-accepted per prior decision history; exact rows must be imported verbatim in final source-backed register |
| CF-13 | Worker identity independent of hostname/machine; registration/trust lifecycle; declared/verified/available/authorized capabilities distinct; scoped revocable credentials | Owner-accepted |
| CF-14 | Capability declarations are not permissions; bounded job isolation and scoped access; resource limits by job class; admin/production/QA/publishing permissions separated | Owner-accepted |
| CF-15 | Refer to authoritative Artifact 08 decision record for exact wording | Owner-accepted per prior decision history |
| CF-16–CF-21 | Refer to authoritative Artifact 08 decision record for exact individual wording | Accepted under standing delegation per prior decision history |
| CF-20 | Rights vocabulary: UNKNOWN, PENDING_REVIEW, CLEARED, RESTRICTED, EXPIRED, REVOKED, DENIED | Owner-accepted; legacy mapping needs migration plan |
| CF-21 | Approval vocabulary: APPROVED, REJECTED, CHANGES_REQUESTED, EXPIRED, REVOKED | Owner-accepted |
| CF-22 | Centralized authorization authority | Explicitly owner-accepted |
| CF-23 | Refer to authoritative Artifact 08 decision record for exact wording | Accepted under standing delegation |
| CF-24 | No paid services; operational/provider choices remain deferred | Explicitly owner-accepted |

Source limitation: The exact wording of CF-03–CF-12, CF-15–CF-19 and CF-23 is not reproduced here because the original decision rows are not present in this register's source context. The authoritative source must be consulted before a final verbatim register is frozen. Do not reconstruct missing wording from memory.

### 5. P0 work package traceability

| Requirement domain | Work package | Principal design artifact | Acceptance evidence |
| --- | --- | --- | --- |
| Canonical entities, ownership, persistence | WP-1 | WP-1 boundary and schema candidate | Migrations, constraints, repository and transaction tests |
| Workflow/task/job/attempt/lease | WP-2 | Durable execution, state transition and API/event reconciliations | Idempotency, restart, lease and duplicate-delivery tests |
| Worker identity/trust/capabilities | WP-3 | Worker trust and credential reconciliation | Enrollment, revocation, scope and authorization-negative tests |
| Artifact/version/manifest/transfer | WP-4 | Artifact contract and lifecycle reconciliations | Integrity, transfer, quarantine and lifecycle tests |
| QA/rights/review/approval/authorization | WP-5 | Governance and authorization reconciliation | Hard-blocker and adapter-bypass-negative tests |
| Integrated recovery and QA | WP-6 | Acceptance contract and test oracle reconciliation | VS-01–VS-18, failure injection, Kilo review |

### 6. Cross-document gaps and reconciliations

| Gap | Topic | Current disposition |
| --- | --- | --- |
| X-01 | Workflow lifecycle vs execution ownership | Reconciled candidate; exact state contract remains open |
| X-02 | ArtifactVersion and manifest detail | Reconciled in artifact contract candidate |
| X-03 | Transfer/validation/quarantine records | Reconciled in artifact contract candidate |
| X-04 | Governance concept labels/count | Reconciled into distinct governance concepts |
| X-05 | Central authorization/emergency pause | Central authorization accepted; emergency policy owner-reserved |
| X-06 | Worker trust/credential/revocation | Reconciled candidate; security decisions remain owner-reserved |
| X-07 | WorkflowTask/Job/JobAttempt cardinality/state mapping | Reconciled candidate; exact schema/transitions open |
| X-08 | Command/event envelope and compatibility | Reconciled candidate; final exact contract requires approval |
| X-09 | Artifact deletion/lifecycle/legal hold | Logical lifecycle clarified; authority/durations remain open |
| X-10 | WP-6 test oracles/environment | Substantially clarified; tests not executed |
| X-11 | ODR-22 provenance/source reconciliation | Underlying constraints traced to L-08/L-09/L-13; ODR-22 itself remains provisional grouping |
| X-12 | Unified status vocabulary/source precedence/evidence | Candidate produced; owner review pending |

### 7. Owner-reserved decisions

At minimum:

- Legal-hold authority and release.

- Irreversible physical purge authority and audit/backup purge policy.

- Retention classes and durations.

- Emergency pause authority and scope.

- Break-glass policy.

- Treatment of in-flight external actions during pause/revocation.

- Worker identity assurance and isolation threat model.

- Active lease revocation semantics and worker quarantine/recovery.

- Numeric lease, heartbeat, retry, backoff, retention and idempotency windows where not already approved.

- Any provider, paid service, cloud account, production deployment or public publishing authorization.

### 8. Traceability completeness rules

A final master register must add:

- Exact source filename, version and hash where available.

- Exact decision wording and source row.

- Requirement/contract clause ID.

- Implementation path and commit/build only after implementation exists.

- Test oracle ID and evidence pointer only after a real run.

- Supersession and conflict records.

- Owner approval evidence for frozen baselines.

Never invent missing source wording, hashes, commits, build IDs or test outcomes.

### 9. Current state

This is a consolidated candidate based on the recorded project decision history and artifact index. It is not a substitute for the authoritative source files. It does not freeze contracts, authorize implementation or assert that any test has run.

## 02 — Decision & Owner-Reserved Register

Version: 0.1

Status: Candidate register; no new decisions accepted here

### 1. Purpose

Separate decisions already accepted from detailed design choices that remain open, deferred or reserved for the owner.

### 2. Already accepted — do not re-ask without a real source conflict

- ADR-001–ADR-010.

- CF-01–CF-15.

- CF-16–CF-21 under standing delegation.

- CF-22 explicitly accepted.

- CF-23 under standing delegation.

- CF-24 explicitly accepted: no paid services; provider choices remain deferred.

See the Master Traceability Register and original Artifact 08 sources for exact wording. This document does not alter those decisions.

### 3. Owner-reserved decision register

| ID | Decision required | Why it matters | Safe interim posture |
| --- | --- | --- | --- |
| OR-01 | Who may place/release legal hold? | Legal and evidence preservation authority | Do not purge held material |
| OR-02 | Who may authorize irreversible physical purge? | Irreversible data loss | No physical purge |
| OR-03 | Retention classes and durations | Storage, compliance and audit lifecycle | Retain; do not invent durations |
| OR-04 | Whether/how audit evidence may be purged | Accountability and forensic integrity | Preserve audit evidence |
| OR-05 | How backup copies inherit deletion/hold policy | Residual copies and restore behavior | No claim of complete deletion |
| OR-06 | Emergency pause authority and scope | System-wide safety control | No unapproved break-glass |
| OR-07 | Break-glass roles, approvals and audit | Emergency exceptions | Deny by default |
| OR-08 | Treatment of in-flight external actions during pause/revocation | Avoid duplicate/ambiguous side effects | Reconcile outcome before retry |
| OR-09 | Worker identity assurance level | Prevent worker impersonation | Do not trust unverified identity |
| OR-10 | Worker isolation technology/threat model | Bound filesystem/network/process access | Use no privileged execution |
| OR-11 | Active lease revocation semantics | Stop compromised or untrusted worker | Revoke future claims; reconcile active attempt |
| OR-12 | Worker quarantine and recovery authority | Containment after suspicious behavior | Quarantine pending review |
| OR-13 | Output treatment from quarantined worker | Prevent unsafe artifact promotion | Quarantine output |
| OR-14 | Numeric lease/heartbeat/retry/backoff parameters | Operational reliability | Keep configurable; conservative non-production defaults only after approval |
| OR-15 | Idempotency retention and scope | Duplicate prevention | Do not assume indefinite or global scope |
| OR-16 | External provider idempotency/reconciliation strategy | Avoid duplicate external actions | No automatic retry of ambiguous non-idempotent action |
| OR-17 | Local database/runtime implementation choice | Development environment and cost | Provider-neutral; no paid activation |
| OR-18 | Cloud provider and deployment topology | Future remote control plane | Deferred; no account activation |
| OR-19 | Public publishing automation policy | External irreversible side effects | Automatic public publishing disabled |
| OR-20 | Production release authorization | Real users/data/operations | Synthetic P0 only |

### 4. Deferred is not default approval

A deferred decision:

- Remains unresolved.

- Must carry a reason and revisit trigger where practical.

- Must not be replaced by an agent's preference.

- Must not grant permission to choose a provider, spend money or perform a protected action.

### 5. Decision submission format

For each owner-reserved item, provide:

- Exact decision question.

- Options and consequences.

- Recommended safe option, if useful.

- Reversibility and operational risk.

- Dependencies.

- What remains blocked if deferred.

Ask the owner only when the decision is genuinely needed for the next authorized work package. Do not interrupt the user with the full list prematurely.

## 03 — Dependency & Sequencing Map

Version: 0.1

Status: Planning candidate

### 1. Purpose

Show what must precede what, where parallel preparation is safe, and where implementation dependencies prohibit premature work.

### 2. Dependency graph

Source reconciliation + master traceability
                  |
                  v
        Owner detailed-contract review
                  |
                  v
        Explicit contract freeze (G1)
                  |
                  v
        Explicit WP-1 authorization (G2)
                  |
                  v
                 WP-1
                  |
                  v
                 WP-2
                /    \
               v      v
             WP-3    WP-4
                \    /
                 v  v
                 WP-5
                  |
                  v
                 WP-6
                  |
                  v
       Independent read-only Kilo QA
                  |
                  v
        Owner acceptance of exact scope

WP-3 and WP-4 may be planned in parallel after WP-2 contracts stabilize, but integration order and shared schema ownership must be explicit. WP-5 depends on stable identity, execution and artifact references. WP-6 depends on all required packages.

### 3. What can happen in parallel now (design/review only)

- Consolidate master traceability and exact source references.

- Reconcile source conflicts and identify missing original decision wording.

- Prepare owner-reserved decision briefs for only near-term blockers.

- Prepare implementation work-order templates.

- Prepare deterministic synthetic test fixtures and environment checklist at design level.

- Map logical integration boundaries without editing repository files.

### 4. What must not happen yet

- Implement detailed schemas before the contract baseline is approved.

- Launch multiple agents against overlapping files.

- Select a paid provider or activate cloud resources.

- Run destructive migrations against existing data.

- Enable public publishing.

- Treat historical tests as current verification.

- Mark WP-1–WP-6 complete based on document preparation.

### 5. Gate-by-gate outputs

| Gate | Output |
| --- | --- |
| G0 Reconciliation | Master traceability, conflict register, candidate contract set |
| G1 Contract freeze | Owner-approved baseline ID, version, scope and exclusions |
| G2 WP authorization | WP-1 work order with repository boundaries |
| WP-1 exit | Schema/repository evidence and accepted migration strategy |
| WP-2 exit | Durable execution and recovery evidence |
| WP-3 exit | Worker trust and scope enforcement evidence |
| WP-4 exit | Artifact integrity and lifecycle evidence |
| WP-5 exit | Central governance and bypass-negative evidence |
| WP-6 exit | Integrated vertical-slice evidence and recovery report |
| G5 Acceptance | Independent QA findings and owner acceptance record |

### 6. Recommended next action

Finish the source-backed master register by importing exact CF-03–CF-12, CF-15–CF-19 and CF-23 wording from the authoritative Artifact 08 decision record, then reconcile all source filenames/versions. Do not guess missing wording from summaries.

## 04 — Agent Execution & Change-Control Protocol

Version: 0.1

Status: Proposed operating protocol; agents not activated

### 1. Purpose

Make engineering delegation predictable, auditable and safe. An agent receives a bounded work order, not broad authority over the product or repository.

### 2. Role boundaries

| Role | May do | May not do |
| --- | --- | --- |
| Owner | Approve scope, contracts, implementation, external actions and acceptance | Delegate away final product authority by implication |
| Architecture coordinator | Reconcile sources, prepare contracts, review evidence | Claim owner approval or authorize external operations |
| Engineering owner | Implement assigned package within permitted paths | Expand scope, approve own work, bypass governance |
| Independent QA | Inspect and test read-only, report findings | Modify implementation or accept on owner's behalf |

Existing assignments: Qoder is Phase 11 engineering owner; OpenCode is Phase 10 engineering/closure owner; Kilo is independent read-only QA. These role assignments do not constitute a new task launch.

### 3. Mandatory work-order header

Every agent task must include:

- Work order ID and version.

- Named owner and reviewer.

- Approved contract baseline ID.

- Exact scope and out-of-scope list.

- Permitted paths and prohibited paths.

- Known user modifications/untracked files to preserve.

- Dependencies and expected outputs.

- Required tests and evidence.

- Stop/escalation conditions.

- Explicit prohibited operations.

### 4. Change-control rules

Unless separately approved, agents must not:

- Reset, revert, stash, clean, delete, overwrite, rename or broadly stage user files.

- Commit, push, alter branches/remotes or rewrite history.

- Install paid services, activate providers, incur spend or deploy.

- Migrate or delete real data.

- Publish/upload externally.

- Modify central authorization policy or approval requirements.

- Self-approve or represent a proposal as an owner decision.

If a collision or ambiguity is found, stop only the affected work and report exact paths, source clauses and options. Do not “fix” by overwriting.

### 5. Required completion report

1. Work order and baseline used.

1. Exact changed paths.

1. Summary of each material change.

1. Tests/commands actually run and exit results.

1. Evidence pointers and hashes where generated.

1. Known limitations and tests not run.

1. Contract deviations or newly discovered conflicts.

1. Confirmation that prohibited actions were not performed.

1. Recommended next step.

### 6. QA independence

Engineering owner does not select its own work as accepted. Kilo receives a fixed commit/build and evidence bundle, operates read-only, and reports independent findings. Any remediation returns to engineering; QA rechecks. Owner accepts the exact scope.

### 7. No implied activation

This document creates no agent run, task assignment, repository change or execution authorization.

## 05 — Risk Register & Mitigation Plan

Version: 0.1

Status: Planning candidate; risks require review as evidence emerges

| ID | Risk | Potential impact | Mitigation / control | Trigger to revisit |
| --- | --- | --- | --- | --- |
| R-01 | Contract ambiguity or conflicting source | Wrong schema/API implementation | Source precedence, conflict register, owner freeze | Conflicting clauses found |
| R-02 | Existing uncommitted user work overwritten | Loss of project work | Preservation rules, narrow paths, isolated worktree only if approved | Any path overlap |
| R-03 | Agent scope creep | Unreviewed architecture or behavior | Bounded work orders and stop conditions | Unrequested file/scope changes |
| R-04 | Duplicate queue delivery | Duplicate work or side effects | Idempotency, inbox deduplication, attempt history | Retry/replay tests fail |
| R-05 | Stale worker completes after lease expiry | State corruption | Lease ownership/version checks and stale-attempt rejection | Concurrent claim scenario |
| R-06 | Ambiguous external side effect retried | Duplicate publication/action | Reconciliation and provider idempotency; no blind retry | Timeout after request dispatch |
| R-07 | Publisher bypasses central authorization | Unauthorized public action | Central enforcement and adapter negative tests | Any direct adapter path |
| R-08 | Rights/approval ambiguity treated as permission | Legal/reputational exposure | Fail-closed gates and exact-version binding | Missing or conflicting evidence |
| R-09 | Artifact integrity/manifest mismatch | Wrong or corrupted media | Checksums, immutable versions, validation/quarantine | Transfer interruption or mismatch |
| R-10 | Legal hold/purge semantics undefined | Irreversible data loss or retention breach | Owner-reserved policy; no purge by default | Deletion lifecycle implementation |
| R-11 | Worker compromise or impersonation | Data access or unsafe output | Identity assurance, scoped credentials, isolation | Worker trust design/implementation |
| R-12 | Local worker unavailable | Workflow stalls | Explicit waiting state and safe re-dispatch policy | Worker offline |
| R-13 | Premature provider/cloud selection | Cost and lock-in | Provider-neutral abstractions; defer selection | External deployment proposed |
| R-14 | Historical test report mistaken for current proof | False readiness claim | Evidence bound to commit/build/environment | Acceptance review |
| R-15 | Incomplete audit/correlation | Cannot reconstruct incidents | Trace IDs, append-only transitions, evidence records | Missing actor/correlation fields |
| R-16 | Over-parallelized engineering | Merge conflicts and incompatible contracts | Dependency gates and file ownership | Multiple agents touch same boundary |
| R-17 | Overbuilt abstraction before vertical slice | Slow delivery and complexity | P0-A narrow synthetic slice first | Scope expansion |
| R-18 | Local test environment differs from target | False confidence | Environment manifest and explicit scope | Runtime/dependency change |

### Risk handling rules

- A risk is not closed by writing a mitigation; closure requires evidence.

- High-impact unresolved risks block the affected protected operation.

- Risk acceptance belongs to the owner when it changes product, legal, security, cost or external-side-effect posture.

- No risk score is assigned without a defined scoring method and evidence.

## 06 — Implementation Readiness Scorecard

Version: 0.1

Status: Initial assessment based on recorded project context; not an audit or approval

### 1. Readiness dimensions

| Dimension | Current assessment | Why |
| --- | --- | --- |
| Product direction | Defined at high level | Single-owner Creator Mode, NEXTDECODE, 12 modules, lifecycle |
| Architecture decisions | Substantially decided | ADR-001–ADR-010 and CF-01–CF-24 accepted per decision history |
| Detailed contracts | Not frozen | X-01–X-12 reconciliation and owner review remain |
| Source traceability | Partial | Exact source wording/version/hash still needs consolidation |
| Repository baseline | Historical snapshot available | Not freshly inspected; preserve existing changes |
| WP-1–WP-6 design | Candidate packages prepared | Not owner-frozen or implemented by this package |
| Engineering authorization | Not granted | Must be explicit and scoped |
| Runtime verification | Not established | Historical reports are not current proof |
| Independent QA | Pending | Kilo evidence not yet available |
| Provider/deployment | Deferred | No paid services; no provider selected |
| Publishing policy | Restricted | Automatic public publishing disabled |

### 2. Gate readiness

| Gate | Status |
| --- | --- |
| G0 — Design reconciliation | IN_PROGRESS / candidate materials prepared |
| G1 — Detailed contract freeze | NOT_READY pending source-complete owner review |
| G2 — WP-1 implementation authorization | NOT_AUTHORIZED |
| G3 — Integration authorization | NOT_AUTHORIZED |
| G4 — External operations | NOT_AUTHORIZED |
| G5 — P0 acceptance | NOT_RUN |

### 3. What would make us ready for WP-1?

- Exact authoritative source rows imported into master register.

- Contradictions and missing details explicitly resolved or deferred.

- Exact WP-1 schema candidate and migration constraints reviewed.

- Contract baseline version and approval evidence recorded.

- WP-1 work order names permitted paths and preservation constraints.

- Owner explicitly authorizes WP-1 implementation.

- Engineering owner and acceptance reviewer are named.

### 4. Recommendation

Do not start broad implementation yet. Complete source-backed consolidation and the detailed owner review. Once the owner approves the baseline, authorize WP-1 as a narrow first implementation package. Keep WP-2–WP-6 planned but not implicitly authorized.


## Source document metadata (preserved from DOCX)

- **Footer:** NEXTDECODE P0 • Batch 02 • Page

