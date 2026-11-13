# NEXTDECODE Content OS
## Artifact 09 — P0 Coding-Agent Handoff Specification 1.0

**Document status:** Draft handoff specification — not an execution authorization  
**Version:** 1.0  
**Purpose:** Define how a future, explicitly authorized P0 implementation task is handed to coding agents  
**Related artifacts:**  
- Artifact 06 — Implementation Readiness & Risk Register 1.0  
- Artifact 07 — P0 Foundation Execution Plan & Acceptance Framework 1.0  
- Artifact 08 — P0 Detailed Contract Freeze & Open Decisions Closure 1.0  
- Accepted P0 Architecture Decision Baseline 1.0 (ADR-001 through ADR-010)

---

## 1. Executive summary

This specification converts the approved high-level architecture and the P0 planning artifacts into a controlled, evidence-led handoff process for coding agents.

It defines:
- the responsibilities and limits of Qoder, OpenCode, and Kilo;
- the minimum inputs required before implementation can begin;
- how work is divided into bounded packages;
- how repository ownership and file boundaries must be established;
- the required engineering, testing, security, and reporting evidence;
- how agents coordinate without creating conflicting changes;
- stop conditions and approval gates.

**This document does not start implementation.** It does not assign a task, grant repository access, authorize inspection, authorize Git operations, authorize code or configuration changes, provision infrastructure, deploy services, or authorize production generation, uploads, or publishing.

The next action after this document is owner review of Artifact 08's detailed contract freeze and open decisions. A separate explicit authorization must define the permitted repository, task, access mode, scope, and allowed operations before any agent begins work.

## 2. Authority and precedence

When instructions conflict, use this precedence order:

1. Explicit, current owner authorization for the specific task and permitted operations.
2. Accepted P0 Architecture Decision Baseline 1.0 (ADR-001–ADR-010).
3. Owner-approved detailed contract freeze derived from Artifact 08.
4. Artifact 07 — P0 Foundation Execution Plan & Acceptance Framework.
5. This handoff specification.
6. Agent-generated plans, suggestions, and implementation notes.

An agent must not interpret a lower-level document, an old conversation, a repository convention, or a tool capability as permission to exceed the current authorization.

### 2.1 Accepted high-level architecture baseline

The following are accepted at the architecture-decision level:

| ADR | Accepted decision |
|---|---|
| ADR-001 | UUIDv7 canonical identifiers |
| ADR-002 | PostgreSQL-compatible authoritative shared database |
| ADR-003 | Database-backed durable queue with transactional outbox/inbox initially |
| ADR-004 | Versioned HTTP/JSON interfaces with schema validation |
| ADR-005 | Unique worker identity, scoped short-lived credentials, capability-based authorization |
| ADR-006 | Relational artifact metadata with binary content behind an object-storage abstraction |
| ADR-007 | Centralized authorization; adapters cannot bypass it; automatic publishing remains disabled pending separate policy |
| ADR-008 | QA outcomes: PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW, BLOCKED; hard blockers cannot be bypassed by ordinary approval |
| ADR-009 | Evidence-backed rights states with use-specific enforcement |
| ADR-010 | Separate lifecycle state machines |

These decisions do not settle every implementation parameter. Provider, region, budget, exact database version, queue details, token issuer and format, object-storage provider, retention values, monitoring provider, backup/recovery targets, and other operational choices remain open unless separately approved.

### 2.2 Contract status

Artifact 08 contains proposed detailed contracts and closure checkpoints. Those contracts are **not considered frozen merely because they appear in a handoff document**. Agents must receive a specific owner-approved contract version and checksum or immutable revision reference before implementing contract-dependent behavior.

If the contract pack is not explicitly marked owner-approved and frozen, the agent may prepare a gap analysis or implementation plan only within an authorized read-only scope. It must not silently convert proposals into final schemas or behavior.

## 3. Agent roles and boundaries

The following role allocation is retained from the existing project direction. This document does not initiate or modify those assignments.

### 3.1 Qoder — Phase 11 engineering owner

**Intended role when separately authorized**
- Own the assigned Phase 11 engineering implementation.
- Produce a scoped implementation plan before editing.
- Implement only the approved work package and its accepted contracts.
- Maintain traceability from requirements to code and tests.
- Run the prescribed checks and provide reproducible evidence.
- Report deviations, blockers, and decisions required from the owner.

**Must not**
- Expand scope into unrelated phases or refactor unrelated modules.
- change accepted ADRs or detailed contracts unilaterally.
- self-approve security, rights, QA, or publishing policy.
- enable automatic publishing or bypass centralized authorization.
- provision paid services, deploy, or publish without separate authorization.

### 3.2 OpenCode — Phase 10 engineering and closure owner

**Intended role when separately authorized**
- Own the assigned Phase 10 engineering and closure work.
- Reconcile the assigned implementation with approved requirements and historical evidence.
- Close only the specific gaps included in its authorized scope.
- Supply tests, evidence, and a clear closure statement for each assigned item.
- Identify any dependency on Phase 11 or P0 foundation work without taking over another agent's ownership.

**Must not**
- claim historical blockers are closed without current evidence;
- alter another work package's owned files without coordination and approval;
- treat a passing test suite as proof of untested governance or runtime behavior;
- change the architecture baseline or broaden the authorized scope.

### 3.3 Kilo — independent read-only QA

**Intended role when separately authorized**
- Review the specified baseline and implementation independently.
- Inspect evidence and test results within the authorized read-only boundary.
- challenge requirement coverage, security assumptions, state transitions, error handling, and failure cases.
- reproduce tests where authorized and technically feasible.
- report findings with severity, evidence, reproduction steps, and affected requirement IDs.

**Read-only boundary**
- No source edits, configuration edits, migrations, commits, pushes, deployments, or production actions.
- No “quick fixes” during review.
- Findings must be returned to the designated engineering owner for remediation.
- Any request to expand beyond read-only QA requires explicit owner authorization.

### 3.4 Separation of duties

- The implementation owner cannot independently approve their own work as complete.
- Kilo's independent review is evidence, not a substitute for owner acceptance.
- An agent cannot grant itself credentials, permissions, budget, or access.
- An agent cannot approve its own generated content for distribution.
- Approval of a code change does not authorize deployment or production use.

## 4. Preconditions for any coding-agent task

A task is not ready for implementation until all applicable items below are satisfied.

| Gate | Required input | Evidence of readiness |
|---|---|---|
| G-01 | Explicit owner authorization | Written scope, repository, agent, access mode, permitted operations, and expiry/stop condition |
| G-02 | Repository identity | Confirmed repository URL or local path and target branch/commit |
| G-03 | Baseline evidence | Authorized read-only status, branch, commit, working-tree state, and relevant test baseline |
| G-04 | Contract freeze | Owner-approved contract pack revision and list of applicable contract IDs |
| G-05 | Work package | One bounded package with objective, in-scope behavior, exclusions, dependencies, and acceptance criteria |
| G-06 | File ownership | Confirmed path-level ownership map and shared-file coordination rules |
| G-07 | Environment | Approved runtime/tool versions, dependency policy, and test commands |
| G-08 | Security boundary | Credential handling, secrets policy, data classification, and permitted external connections |
| G-09 | Data safety | Migration, backup, fixture, and destructive-operation constraints |
| G-10 | Completion gate | Required test/evidence bundle and named owner acceptance step |

If any critical gate is missing, the agent must stop before making changes and return a readiness report. It may perform only explicitly authorized preparatory work.

## 5. Repository baseline and file ownership

No current repository path, branch, file list, or commit is asserted by this document. Historical repository details are not a substitute for a fresh, authorized baseline.

Before assigning path-level ownership, the owner must authorize a read-only baseline capture. The resulting baseline record should include:

- repository identity and local working directory;
- current branch and commit hash;
- working-tree status, including untracked files;
- relevant tags and submodule state, if applicable;
- runtime and package-manager versions;
- dependency lockfile status;
- test commands and baseline outcomes;
- existing CI checks and known failures;
- generated, ignored, secret-bearing, or user-data directories that must not be touched.

### 5.1 Ownership map template

Complete this table only after the repository has been inspected under explicit authorization.

| Work package | Primary owner | Allowed paths | Shared paths | Forbidden paths | Reviewer |
|---|---|---|---|---|---|
| WP-0 Baseline and repository map | To be authorized | Pending inspection | Pending | All paths not explicitly allowed | Kilo, read-only |
| WP-1 Contract and schema foundation | To be authorized | Pending inspection | Pending | Secrets, production data, unrelated modules | Kilo, read-only |
| WP-2 Identity and authorization foundation | To be authorized | Pending inspection | Pending | Credential stores and live identity systems unless explicitly authorized | Kilo, read-only |
| WP-3 Job, lease, and durable queue foundation | To be authorized | Pending inspection | Pending | Production queues and live workloads | Kilo, read-only |
| WP-4 Worker registration and capability boundary | To be authorized | Pending inspection | Pending | Real credentials and uncontrolled worker execution | Kilo, read-only |
| WP-5 Artifact metadata and transfer foundation | To be authorized | Pending inspection | Pending | Real user media and external buckets unless explicitly authorized | Kilo, read-only |
| WP-6 QA, rights, audit, and integration gates | To be authorized | Pending inspection | Pending | Live publishing and policy bypasses | Kilo, read-only |

This is a planning template, not a grant of file access.

### 5.2 Shared-file rule

A file may have only one active editing owner at a time. Shared files require:
1. a named coordinating owner;
2. a declared change proposal;
3. notification to affected work-package owners;
4. explicit approval before overlapping edits;
5. integration tests covering all affected packages.

If two agents independently modify the same file, both must stop integration and report the conflict. They must not overwrite or automatically merge the other agent's work.

## 6. Work-package handoff structure

Use the following bounded work-package sequence as the default planning structure. The sequence is inherited from Artifact 07; exact implementation order and dependencies must be confirmed against the frozen contracts and repository baseline.

### WP-0 — Baseline and repository map
**Objective:** Establish the authorized technical baseline and identify existing components that can be reused.

**Expected outputs**
- repository baseline record;
- architecture-to-repository mapping;
- existing component reuse assessment;
- test and CI baseline;
- path-level ownership proposal;
- unresolved dependency and risk list.

**Acceptance**
- every claim is tied to observed repository evidence;
- no source or configuration files are changed;
- no historical test result is presented as current;
- unknowns are clearly marked.

### WP-1 — Contract and schema foundation
**Objective:** Implement only the owner-frozen shared contracts and validation boundaries.

**Expected outputs**
- versioned contract definitions;
- schema validation;
- compatibility and invalid-input tests;
- contract-to-requirement traceability.

**Acceptance**
- only approved contract revisions are implemented;
- validation rejects malformed and unsupported payloads;
- compatibility behavior is documented and tested;
- no proposed field or state is silently promoted to a requirement.

### WP-2 — Identity and authorization foundation
**Objective:** Establish canonical identity and centralized authorization boundaries.

**Expected outputs**
- UUIDv7 identity handling consistent with ADR-001;
- identity and principal model;
- scoped capability checks;
- authorization decision records and tests;
- negative tests for privilege escalation and adapter bypass.

**Acceptance**
- identity is not inferred from untrusted client input;
- permissions are checked at the authoritative boundary;
- credentials are not hard-coded or logged;
- denied, expired, malformed, and insufficient-capability requests fail closed.

### WP-3 — Job, lease, and durable queue foundation
**Objective:** Implement durable job lifecycle and safe execution coordination.

**Expected outputs**
- job lifecycle implementation;
- lease and heartbeat behavior;
- retry and idempotency behavior;
- transactional outbox/inbox behavior;
- duplicate, timeout, stale-lease, and recovery tests.

**Acceptance**
- duplicate delivery does not create duplicate side effects;
- expired leases can be recovered according to frozen rules;
- retry limits and terminal outcomes are deterministic;
- event delivery does not become the source of truth.

### WP-4 — Worker registration and capability boundary
**Objective:** Register workers and constrain execution to declared capabilities.

**Expected outputs**
- worker identity and registration flow;
- capability declaration and enforcement;
- credential lifecycle integration;
- worker health and lease integration tests.

**Acceptance**
- each worker has a unique identity;
- credentials are scoped and short-lived as specified by the frozen contract;
- workers cannot self-grant capabilities;
- unauthorized or revoked workers cannot claim work.

### WP-5 — Artifact metadata and transfer foundation
**Objective:** Manage artifact metadata and safe transfer without coupling the control plane to a specific storage vendor.

**Expected outputs**
- relational artifact metadata;
- immutable/versioned artifact references where required;
- object-storage abstraction;
- transfer authorization and integrity checks;
- size, expiry, and failure-path tests.

**Acceptance**
- binary content is not placed in relational records contrary to the approved design;
- metadata and content references remain consistent;
- transfer access is scoped and auditable;
- incomplete or corrupted transfers are detected.

### WP-6 — QA, rights, audit, and integration gates
**Objective:** Enforce quality outcomes, rights evidence, auditability, and integration-level safety.

**Expected outputs**
- QA outcome model;
- rights state and evidence model;
- audit and correlation coverage;
- integration and negative tests;
- owner-facing readiness report.

**Acceptance**
- only the four accepted QA outcomes are used unless a later owner-approved contract says otherwise;
- hard blockers cannot be cleared through ordinary approval;
- rights decisions are evidence-backed and use-specific;
- audit records identify the relevant actor, action, target, outcome, and correlation context;
- publishing remains disabled unless separately authorized under a distinct policy.

## 7. Standard task brief

Every agent task must begin with a completed brief. Missing values must be marked `NOT PROVIDED`; agents must not invent them.

```yaml
task_id: NOT_PROVIDED
document_version: "1.0"
authorized_by: NOT_PROVIDED
authorization_reference: NOT_PROVIDED
assigned_agent: NOT_PROVIDED
role: NOT_PROVIDED
repository: NOT_PROVIDED
working_directory: NOT_PROVIDED
base_branch: NOT_PROVIDED
base_commit: NOT_PROVIDED
contract_pack_revision: NOT_PROVIDED
work_package: NOT_PROVIDED
objective: NOT_PROVIDED
in_scope:
  - NOT_PROVIDED
out_of_scope:
  - NOT_PROVIDED
allowed_paths:
  - NOT_PROVIDED
forbidden_paths:
  - NOT_PROVIDED
permitted_operations:
  - NOT_PROVIDED
prohibited_operations:
  - NOT_PROVIDED
dependencies:
  - NOT_PROVIDED
acceptance_criteria:
  - NOT_PROVIDED
required_tests:
  - NOT_PROVIDED
required_evidence:
  - NOT_PROVIDED
external_services_allowed: false
paid_services_allowed: false
production_data_allowed: false
deployment_allowed: false
publishing_allowed: false
authorization_expiry_or_stop_condition: NOT_PROVIDED
```

The values above are placeholders, not defaults that grant permission. In particular, a missing authorization reference means no implementation may begin.

## 8. Agent operating protocol

### Phase A — Acknowledge and validate
The agent returns:
- task ID and assigned role;
- repository and base revision it believes it is authorized to use;
- scope and exclusions restated in its own words;
- permitted and prohibited operations;
- missing inputs, contradictions, and risks;
- a clear `READY`, `NOT_READY`, or `BLOCKED` status.

No edits occur during this phase.

### Phase B — Plan
The agent produces:
- a concise implementation approach;
- files expected to change, restricted to authorized paths;
- dependencies and sequencing;
- test plan mapped to acceptance criteria;
- migration and rollback considerations, if applicable;
- risks and owner decisions required.

The owner approves the plan when the task authorization requires plan approval. An agent must not assume silence means approval.

### Phase C — Implement
During implementation the agent must:
- remain within the assigned package and allowed paths;
- make small, reviewable changes;
- preserve existing behavior unless the requirement explicitly changes it;
- avoid opportunistic refactors;
- keep secrets and personal data out of source, logs, prompts, and evidence;
- add or update tests alongside behavior changes;
- document deviations immediately;
- stop if a required change crosses a boundary.

### Phase D — Verify
The agent runs only authorized checks and reports:
- exact commands;
- environment and versions;
- exit codes;
- pass/fail/skip counts;
- relevant logs or concise excerpts;
- tests not run and why;
- known limitations;
- whether the acceptance criteria are met.

A statement such as “tests pass” without commands and results is insufficient.

### Phase E — Handoff for independent review
The engineering owner supplies a review bundle to Kilo, if independent QA has been separately authorized. Kilo reviews the exact commit or patch and returns findings without modifying files.

### Phase F — Owner acceptance
The owner decides whether to:
- accept the package;
- request remediation;
- return it for clarification;
- reject it;
- authorize a separate next package.

Agent completion is not owner acceptance. Owner acceptance is not deployment authorization.

## 9. Required engineering quality rules

All implementation work must follow these rules unless a frozen contract explicitly specifies a stricter requirement.

1. **Traceability:** Every implemented behavior maps to a requirement, contract, or acceptance criterion.
2. **Idempotency:** Retried or duplicated requests must not create unintended duplicate effects.
3. **Fail closed:** Missing, invalid, expired, or insufficient authorization must deny protected actions.
4. **Explicit lifecycle:** State transitions must be validated; arbitrary state mutation is not allowed.
5. **Version awareness:** Contract and artifact versions must be explicit where required.
6. **Auditability:** Security-sensitive decisions and consequential state changes must be traceable.
7. **Least privilege:** Components receive only the capabilities required for their assigned work.
8. **No hidden bypass:** Adapters, workers, or agents cannot bypass centralized policy.
9. **Safe defaults:** Publishing, external transfer, paid resources, and production operations remain disabled unless separately authorized.
10. **Reproducibility:** Tests and evidence must identify the code revision and environment.
11. **Compatibility:** Breaking changes require an explicit migration and compatibility plan.
12. **Scope discipline:** No unrelated cleanup, broad refactoring, or dependency upgrades without approval.

## 10. Security, privacy, and data handling

### 10.1 Secrets
- Never commit API keys, passwords, tokens, private keys, or credential files.
- Never paste secrets into agent prompts, task reports, screenshots, or test output.
- Use approved secret injection mechanisms only when separately authorized.
- If a secret is exposed, stop, report the exposure, and follow the owner's rotation procedure.

### 10.2 Data
- Use synthetic or approved test data by default.
- Do not copy production or personal data into local fixtures, logs, screenshots, or external services without explicit authorization.
- Do not upload repository contents to third-party services unless the task authorization explicitly permits it.
- Do not use real creator media, customer data, or rights evidence in tests unless specifically approved.

### 10.3 External services and costs
- No paid API, cloud resource, SaaS subscription, hosted database, storage bucket, or external compute may be created or used without explicit authorization.
- No new provider is selected by an agent simply because it is convenient.
- External network access must be limited to the task's approved destinations and purpose.

### 10.4 Production and publishing
- No deployment, production migration, live worker activation, media generation at production scale, upload, distribution, or publishing is included in P0 coding authorization by default.
- Publishing adapters must not bypass centralized authorization.
- Automatic publishing remains disabled pending a separate policy and explicit authorization.

## 11. Testing and evidence requirements

Every implementation package must produce an evidence bundle.

| Evidence ID | Required evidence |
|---|---|
| EV-01 | Task authorization reference and scope |
| EV-02 | Repository, branch, base commit, and final commit/patch reference |
| EV-03 | Changed-file list and path-boundary confirmation |
| EV-04 | Requirement-to-code-to-test traceability |
| EV-05 | Exact test commands and environment versions |
| EV-06 | Test results, exit codes, and relevant logs |
| EV-07 | Security and negative-test results |
| EV-08 | Migration/rollback evidence, if applicable |
| EV-09 | Known limitations, skipped tests, and unresolved risks |
| EV-10 | Engineering owner completion statement |
| EV-11 | Independent QA report, when authorized |
| EV-12 | Explicit owner acceptance or rejection |

Evidence must be attributable to the exact code revision under review. Screenshots alone are not sufficient when machine-readable test output or logs are available.

### 11.1 Minimum test categories

As applicable to the package:
- happy-path behavior;
- invalid and malformed input;
- unauthorized and insufficient-capability access;
- duplicate and idempotent requests;
- concurrency and race conditions;
- timeout, retry, and recovery;
- stale or expired credentials and leases;
- state-transition rejection;
- persistence and transaction boundaries;
- audit and correlation completeness;
- compatibility and version handling;
- failure isolation and safe shutdown.

### 11.2 Test interpretation

- A unit-test pass proves only the tested unit behavior.
- An integration-test pass proves only the exercised integration path.
- A successful local run does not prove production readiness.
- A historical test count is not a current baseline.
- Untested requirements remain unverified, not implicitly passed.

## 12. Independent QA protocol for Kilo

When separately authorized, Kilo receives:
- the exact task brief;
- approved requirements and frozen contract revision;
- base and target commit/patch;
- changed-file list;
- test commands and raw results;
- known limitations and deviations;
- security-relevant design notes.

Kilo returns findings using this format:

| Field | Description |
|---|---|
| Finding ID | Stable identifier, e.g. `QA-001` |
| Severity | Critical / High / Medium / Low / Informational |
| Requirement | Requirement or contract ID affected |
| Location | File and line, or precise behavior |
| Evidence | Reproduction, test, log, or code reference |
| Impact | What can fail or be abused |
| Recommendation | Minimal corrective action |
| Status | Open / Resolved / Accepted risk / Not reproducible |

Kilo must distinguish:
- confirmed defect;
- requirement not implemented;
- insufficient evidence;
- test gap;
- design concern;
- accepted deviation;
- false positive.

Kilo does not make code changes under this read-only role. A finding is not closed merely because the engineering owner says it is fixed; the revised evidence must be reviewed.

## 13. Change control and contract deviations

Any need to change an accepted ADR, frozen contract, work-package boundary, security rule, or acceptance criterion must be raised as a change request.

A change request must contain:
1. change ID;
2. current approved statement;
3. proposed replacement;
4. reason and evidence;
5. affected contracts, packages, files, tests, and agents;
6. security, privacy, reliability, cost, and migration impact;
7. compatibility and rollback plan;
8. decision required from the owner.

Agents may recommend a change. They may not approve it.

Until approval is recorded, the existing accepted baseline remains authoritative. If implementation cannot safely proceed under the current baseline, the agent stops and reports the blocker.

## 14. Stop conditions

An agent must stop the affected work immediately if any of the following occurs:

- authorization is missing, expired, ambiguous, or contradicted;
- repository identity or base revision differs from the task brief;
- a required file is outside the allowed path list;
- the working tree contains unexpected user changes that could be overwritten;
- another agent is editing the same shared file without coordination;
- a secret or sensitive data exposure is detected;
- the task requires unapproved external access, paid services, or production data;
- a contract is ambiguous or conflicts with an accepted ADR;
- a migration could destroy or irreversibly alter data without an approved recovery plan;
- tests reveal a critical security or data-integrity defect;
- the implementation would enable publishing or bypass centralized authorization;
- a request attempts to expand the task without updated authorization.

The stop report must state what happened, what was not changed, what evidence is available, and what owner decision is required.

## 15. Agent reporting templates

### 15.1 Readiness report

```text
Task ID:
Agent:
Role:
Authorization reference:
Repository / base commit:
Status: READY | NOT_READY | BLOCKED

Scope understood:
Allowed operations:
Prohibited operations:
Missing inputs:
Conflicts or ambiguities:
Risks:
Proposed next step:
No changes made: YES | NO
```

### 15.2 Implementation report

```text
Task ID:
Agent:
Work package:
Base commit:
Final commit or patch:
Summary:
Requirements addressed:
Files changed:
Files intentionally not changed:
Tests run (exact commands):
Test results and exit codes:
Security checks:
Acceptance criteria: MET | PARTIAL | NOT MET
Deviations:
Known limitations:
Open risks:
Evidence locations:
Recommended next action:
```

### 15.3 QA report

```text
Task ID:
Reviewer: Kilo
Reviewed revision:
Review scope:
Read-only boundary maintained: YES | NO
Requirements sampled:
Tests reproduced:
Findings by severity:
Evidence gaps:
Regression concerns:
Overall result: PASS | PASS_WITH_WARNINGS | NEEDS_REVIEW | BLOCKED
Recommendation:
```

The QA report's overall result must use the accepted four-outcome vocabulary. It must not imply that a hard blocker can be waived by ordinary approval.

## 16. Integration and multi-agent coordination

- One engineering owner is assigned to each active work package.
- Only one agent may edit a given path at a time.
- Agents exchange explicit artifacts: task brief, plan, patch/commit, test evidence, and handoff report.
- No agent should rely on another agent's undocumented local state.
- Integrations occur against a named base revision.
- Conflicts are resolved by the designated engineering owner, not by silent overwrite.
- Kilo reviews a stable candidate revision, not a moving working tree.
- Each package is accepted before dependent work is treated as complete.
- Cross-package changes require a change request or explicit revised task authorization.

## 17. Completion definition

A work package is complete only when all applicable conditions are true:

- its authorization and scope are traceable;
- its implementation matches the owner-frozen contracts;
- only permitted paths were changed;
- acceptance criteria are individually evidenced;
- required tests have been run and results reported;
- security and negative tests are addressed;
- deviations and risks are disclosed;
- independent QA has been completed when required;
- all critical and high-severity findings are resolved or explicitly handled through the authorized risk process;
- the owner has recorded acceptance.

Completion of all P0 coding packages still does not automatically authorize deployment, production workloads, external content distribution, or publishing.

## 18. Current project status and next gate

At the time this specification is issued:

| Item | Status |
|---|---|
| ADR-001 through ADR-010 | Accepted in the Accepted P0 Architecture Decision Baseline 1.0 |
| Artifact 06 readiness and risk register | Delivered |
| Artifact 07 P0 execution and acceptance framework | Delivered |
| Artifact 08 detailed contract freeze and open decisions | Delivered; owner review still required |
| Detailed contract freeze | Pending explicit owner approval |
| Repository inspection | Not authorized by this artifact |
| Git operations | Not authorized by this artifact |
| Code/configuration changes | Not authorized by this artifact |
| Coding-agent task assignment | Not initiated by this artifact |
| Infrastructure provisioning or paid services | Not authorized |
| Deployment, production generation, uploads, or publishing | Not authorized |

### Required next gate

1. Review Artifact 08 and record which detailed contracts are approved, amended, or deferred.
2. Approve the open operational decisions that are necessary for the first implementation package; defer the rest explicitly.
3. If repository mapping is needed, issue a separate read-only repository-baseline authorization.
4. Complete the task brief for one bounded work package.
5. Confirm agent assignment, path boundaries, permitted operations, tests, and stop conditions.
6. Only then may the specifically authorized agent begin the specifically authorized task.

**No agent should interpret “next”, this document, or the existence of a task template as permission to inspect or modify the repository.**

---

## 19. Owner decision record

Complete this record when reviewing the handoff specification.

| Decision | Owner response |
|---|---|
| Accept Artifact 09 as the handoff process baseline | Pending |
| Confirm Qoder / OpenCode / Kilo role allocation remains unchanged | Pending |
| Approve Artifact 08 detailed contracts | Pending |
| Authorize read-only repository baseline | Not authorized |
| Authorize any coding-agent implementation task | Not authorized |
| Approve any paid/external service use | Not authorized |
| Approve deployment or production activity | Not authorized |

### Approval record

```text
Decision:
Approved version:
Approved by:
Date:
Scope:
Conditions:
Related authorization reference:
```

**End of Artifact 09 — P0 Coding-Agent Handoff Specification 1.0**
