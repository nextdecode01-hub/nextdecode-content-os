# NEXTDECODE Content OS
## Artifact 11 — P0 Read-Only Repository Baseline Inspection Protocol 1.0

**Document status:** Prepared protocol — inspection not authorized  
**Version:** 1.0  
**Purpose:** Define a repeatable, evidence-led method for capturing the current repository baseline before implementation planning.  
**Related artifacts:** Artifacts 06–10; Accepted P0 Architecture Decision Baseline 1.0.

---

## 1. Executive summary

This protocol defines how a coding agent or reviewer should inspect the existing NEXTDECODE codebase without changing it. The purpose is to establish what actually exists today, what can be reused, what is incomplete, and what evidence is needed before any P0 implementation task is assigned.

The protocol is intentionally conservative:
- it separates observation from modification;
- it requires an explicit repository target and authorization;
- it avoids assuming historical paths, branches, commits, test counts, or runtime versions are still current;
- it records uncertainty rather than filling gaps with guesses;
- it treats commands that may write caches or generated files as non-read-only unless separately approved.

**No inspection is initiated by this document.** It does not authorize opening a repository, running commands, installing dependencies, running tests, editing files, using Git to modify state, or contacting external services.

## 2. Objectives and non-objectives

### 2.1 Objectives

The baseline inspection should establish:
1. exact repository identity and location;
2. branch, commit, and working-tree condition;
3. current project structure and major application boundaries;
4. runtime, dependency, and build configuration;
5. existing tests and their execution requirements;
6. CI and automation configuration;
7. existing security, secrets, data, and generated-file boundaries;
8. current implementation evidence relevant to P0 contracts;
9. reuse opportunities and gaps;
10. a path-level ownership proposal for future bounded work packages.

### 2.2 Non-objectives

The inspection must not:
- implement or repair anything;
- clean, format, refactor, or reorganize the repository;
- install or upgrade packages;
- create branches, commits, tags, or pull requests;
- run database migrations or mutate application data;
- start workers, schedulers, services, or production pipelines;
- provision infrastructure or paid services;
- upload media, publish content, or contact production platforms;
- declare a component production-ready solely because it exists.

## 3. Authorization gate

Before inspection, a separate read-only authorization must be completed using Artifact 10, Section 8.

At minimum it must identify:
- authorization ID and approver;
- exact repository URL or local path;
- permitted branch or commit;
- assigned reviewer/agent;
- permitted inspection operations and commands;
- forbidden operations;
- whether any tests may be run;
- whether local configuration files may be read;
- secret and personal-data handling rules;
- output format and delivery location;
- authorization expiry and stop conditions.

If any of these are unclear, the agent must return `NOT_READY` and ask for clarification. A project name or historical path is not sufficient repository identification.

## 4. Inspection safety model

Use three operation classes.

| Class | Meaning | Default |
|---|---|---|
| R0 — Passive observation | Read metadata and source without executing project code | Permitted only if listed in authorization |
| R1 — Local execution | Run tests, linters, build tools, scripts, or application code | Not permitted unless individually listed |
| R2 — Mutation or external action | Write files, install packages, change Git state, access live systems, or call external services | Prohibited unless a separate explicit authorization permits the exact action |

### 4.1 Examples

**Potential R0 operations** (still subject to authorization):
- list files and directories;
- read README and architecture documentation;
- inspect Git status, branch, and commit metadata;
- inspect dependency manifests and lockfiles;
- read test configuration and CI workflow definitions;
- search source for relevant symbols and route definitions.

**R1 operations**:
- run pytest, npm test, build, lint, type-check, or application startup;
- import application modules;
- run scripts that may initialize local services;
- execute migration validation or integration tests.

These may create caches, bytecode, reports, temporary files, local databases, or other state. They are not assumed read-only.

**R2 operations**:
- edit, create, delete, move, or format files;
- install or update dependencies;
- run migrations;
- commit, checkout, reset, merge, rebase, tag, or push;
- provision cloud resources;
- access production credentials or datasets;
- upload, publish, or deploy.

R2 is outside this protocol.

## 5. Repository identity and baseline capture

Capture the following before analyzing implementation details.

| Field | Required evidence |
|---|---|
| Repository name | Repository metadata or owner-confirmed identity |
| Repository URL | Exact remote URL, if applicable |
| Local path | Exact authorized path |
| Branch | Current branch name |
| Commit | Full commit hash |
| Working tree | Clean/dirty status and untracked-file presence |
| Submodules | Presence and recorded revisions, if applicable |
| Tags | Relevant tags only; do not assume they represent current status |
| Inspection timestamp | Date, time, and timezone |
| Inspector | Agent/reviewer identity |
| Authorization | Authorization ID |

### 5.1 Baseline command examples

The following are examples only. They must not be run until the exact target and permitted commands are authorized. Use commands appropriate to the confirmed environment.

```bash
# Identify the working directory
pwd

# Inspect repository status without changing it
git status --short --branch

# Capture the current commit
git rev-parse HEAD

# Capture the current branch
git branch --show-current

# Inspect configured remotes (redact credentials if present)
git remote -v

# Inspect recent history without changing Git state
git log -5 --oneline --decorate
```

If remote URLs contain embedded credentials or private tokens, do not include them in the report. Redact the sensitive portion and report that redaction occurred.

Do not use checkout, reset, clean, stash, pull, fetch, merge, rebase, commit, tag, or push as part of this baseline protocol.

## 6. Project structure inventory

The inspector should create a concise directory map that focuses on architectural boundaries, not every generated or dependency file.

Capture:
- application entry points;
- API and interface layers;
- orchestration and scheduling components;
- worker execution modules;
- domain models and lifecycle logic;
- database and persistence modules;
- queue and event infrastructure;
- artifact/media storage and transfer;
- quality and rights enforcement;
- publishing/distribution adapters;
- configuration and dependency manifests;
- tests, fixtures, and test utilities;
- CI workflows and developer documentation.

Exclude or summarize rather than enumerate:
- virtual environments;
- dependency vendor directories;
- caches and bytecode;
- build output;
- generated media;
- local datasets;
- secret stores;
- large binary assets.

Do not open or copy secret-bearing files merely to complete the inventory. Record their presence and access restriction.

### 6.1 Structure inventory template

| Area | Observed path(s) | Existing responsibility | Evidence | Confidence |
|---|---|---|---|---|
| Application entry points | Pending | Pending | Pending | Unknown |
| API/interface | Pending | Pending | Pending | Unknown |
| Orchestration | Pending | Pending | Pending | Unknown |
| Worker execution | Pending | Pending | Pending | Unknown |
| Domain/state models | Pending | Pending | Pending | Unknown |
| Persistence | Pending | Pending | Pending | Unknown |
| Queue/events | Pending | Pending | Pending | Unknown |
| Artifact/media | Pending | Pending | Pending | Unknown |
| QA/rights | Pending | Pending | Pending | Unknown |
| Publishing adapters | Pending | Pending | Pending | Unknown |
| Tests | Pending | Pending | Pending | Unknown |
| CI/tooling | Pending | Pending | Pending | Unknown |

## 7. Runtime and dependency inventory

Record observed versions from project declarations and, only if authorized, from the installed local environment.

| Item | Declared value | Observed local value | Evidence source | Notes |
|---|---|---|---|---|
| Operating system | Pending | Pending | Pending | |
| Shell/environment | Pending | Pending | Pending | |
| Python/Node/runtime | Pending | Pending | Pending | |
| Package manager | Pending | Pending | Pending | |
| Dependency manifest | Pending | N/A | Pending | |
| Lockfile | Pending | N/A | Pending | |
| Database client/driver | Pending | Pending | Pending | |
| Test framework | Pending | Pending | Pending | |
| Build/lint/type tools | Pending | Pending | Pending | |
| External SDKs | Pending | Pending | Pending | |

Rules:
- distinguish declared versions from installed versions;
- do not infer installed dependencies from a manifest;
- do not install missing tools;
- do not upgrade deprecated packages during inspection;
- note version conflicts without attempting to resolve them;
- never print environment variables or secret values.

## 8. Test and CI baseline

First inspect test definitions and CI configuration. Running tests requires separate R1 authorization.

### 8.1 Static test inventory

Capture:
- test framework and version declarations;
- test directory structure;
- unit, integration, end-to-end, security, and contract test groups;
- fixtures and mock services;
- environment variables required by tests (names only, never values);
- tests that require network, credentials, databases, or external services;
- test markers and exclusions;
- CI jobs, triggers, and required checks.

### 8.2 Optional execution baseline

Only if exact test commands are explicitly authorized:
- record the exact command;
- record the working directory and runtime versions;
- record start/end time and exit code;
- capture pass, fail, skip, and error counts;
- retain relevant logs without secrets or personal data;
- note files or caches created by execution;
- record external dependencies contacted, if any.

If execution would require unapproved credentials, services, or data, do not run it. Mark the test group `NOT RUN — authorization/dependency unavailable`.

### 8.3 Baseline interpretation

A passing test suite is evidence only for the tested revision, environment, and exercised behaviors. It does not prove that all P0 contracts are implemented, that governance controls are complete, or that production readiness has been achieved.

Historical test results must be labeled `HISTORICAL — NOT REVERIFIED`.

## 9. P0 architecture-to-repository mapping

Map each accepted ADR to current implementation evidence. An ADR may be fully implemented, partially implemented, absent, contradicted, or not assessable.

Use these statuses:

- `IMPLEMENTED — VERIFIED`: direct evidence and relevant tests support the claim.
- `PARTIALLY IMPLEMENTED`: some behavior exists; gaps are identified.
- `PRESENT — UNVERIFIED`: code or configuration exists, but behavior has not been validated.
- `NOT FOUND`: no supporting implementation evidence located within inspected scope.
- `CONTRADICTED`: observed behavior conflicts with the accepted ADR.
- `NOT ASSESSABLE`: inspection scope or evidence is insufficient.

| ADR | Required mapping focus | Status | Evidence references | Gaps / risks |
|---|---|---|---|---|
| ADR-001 | UUIDv7 canonical identity usage | Pending | Pending | Pending |
| ADR-002 | Authoritative shared relational persistence | Pending | Pending | Pending |
| ADR-003 | Durable queue and transactional outbox/inbox | Pending | Pending | Pending |
| ADR-004 | Versioned HTTP/JSON and schema validation | Pending | Pending | Pending |
| ADR-005 | Worker identity, scoped credentials, capability checks | Pending | Pending | Pending |
| ADR-006 | Relational artifact metadata and storage abstraction | Pending | Pending | Pending |
| ADR-007 | Centralized authorization and adapter enforcement | Pending | Pending | Pending |
| ADR-008 | Four QA outcomes and hard-blocker enforcement | Pending | Pending | Pending |
| ADR-009 | Evidence-backed, use-specific rights enforcement | Pending | Pending | Pending |
| ADR-010 | Separate lifecycle state machines | Pending | Pending | Pending |

Do not mark an ADR `IMPLEMENTED — VERIFIED` based only on class names, comments, TODOs, documentation, or a mock implementation.

## 10. Historical blocker reconciliation

Previous project reports referenced unresolved governance and integration identifiers:
- G1
- G2
- G3
- U1
- D1
- Traceability v2
- Run-tracker runtime integration

These are historical report-backed items. This protocol does not assume their current status.

For each item, the inspector must:
1. locate the original report or evidence, if included in the authorized scope;
2. identify the exact requirement and expected behavior;
3. map it to current code and tests;
4. classify the current status using evidence;
5. identify any gap or reason it cannot be assessed.

| Item | Original evidence located? | Current implementation evidence | Current status | Required follow-up |
|---|---|---|---|---|
| G1 | Pending | Pending | Unknown | Pending |
| G2 | Pending | Pending | Unknown | Pending |
| G3 | Pending | Pending | Unknown | Pending |
| U1 | Pending | Pending | Unknown | Pending |
| D1 | Pending | Pending | Unknown | Pending |
| Traceability v2 | Pending | Pending | Unknown | Pending |
| Run-tracker runtime integration | Pending | Pending | Unknown | Pending |

Do not claim closure from an agent's summary alone. Closure requires the original acceptance condition and current evidence.

## 11. Security and sensitive-file boundary inventory

The inspector should identify categories and paths without exposing their contents.

Check for:
- environment files;
- private keys and certificates;
- API credentials or tokens;
- local databases and dumps;
- personal or customer data;
- creator media and rights evidence;
- production configuration;
- deployment secrets;
- generated logs that may contain sensitive values.

Report:
- category;
- path or location (redacted if needed);
- whether it is tracked or untracked, if safely observable;
- whether access was avoided;
- recommended handling.

Never paste secret values into the report. If a secret appears in a source file or Git history, report the location and exposure risk without reproducing the value. Do not attempt rotation unless separately authorized.

## 12. Reuse and gap assessment

For each P0 capability, distinguish reuse from new work.

| Capability | Existing component | Reuse evidence | Gap | Proposed action | Confidence |
|---|---|---|---|---|---|
| Canonical IDs | Pending | Pending | Pending | Pending | Unknown |
| Shared persistence | Pending | Pending | Pending | Pending | Unknown |
| Durable job queue | Pending | Pending | Pending | Pending | Unknown |
| API contracts | Pending | Pending | Pending | Pending | Unknown |
| Worker identity | Pending | Pending | Pending | Pending | Unknown |
| Authorization | Pending | Pending | Pending | Pending | Unknown |
| Artifact metadata | Pending | Pending | Pending | Pending | Unknown |
| Artifact transfer | Pending | Pending | Pending | Pending | Unknown |
| QA outcomes | Pending | Pending | Pending | Pending | Unknown |
| Rights enforcement | Pending | Pending | Pending | Pending | Unknown |
| Audit/correlation | Pending | Pending | Pending | Pending | Unknown |
| Existing Shorts Studio integration | Pending | Pending | Pending | Pending | Unknown |

Do not recommend a rewrite without evidence that reuse is unsafe or insufficient. Prefer bounded adapters and incremental integration where they satisfy the approved contracts.

## 13. Path ownership proposal

The output of inspection should propose—not grant—path-level ownership.

| Proposed package | Candidate paths | Shared dependencies | Conflict risk | Proposed owner | Reviewer |
|---|---|---|---|---|---|
| WP-0 Baseline | Documentation/report only | None | Low | To be assigned | Kilo |
| WP-1 Contracts/schema | Pending inspection | Pending | Pending | To be assigned | Kilo |
| WP-2 Identity/authorization | Pending inspection | Pending | Pending | To be assigned | Kilo |
| WP-3 Jobs/leases/queue | Pending inspection | Pending | Pending | To be assigned | Kilo |
| WP-4 Worker identity/capabilities | Pending inspection | Pending | Pending | To be assigned | Kilo |
| WP-5 Artifact metadata/transfer | Pending inspection | Pending | Pending | To be assigned | Kilo |
| WP-6 QA/rights/audit/integration | Pending inspection | Pending | Pending | To be assigned | Kilo |

The owner must approve the map separately before any editing task begins. A proposed path is not an allowed path.

## 14. Evidence quality rules

Every substantive finding must include:
- evidence ID;
- exact path and line or symbol where appropriate;
- observed fact;
- interpretation separated from fact;
- relevant ADR, contract, or requirement ID;
- confidence level;
- limitation or missing evidence.

Confidence values:
- `HIGH`: direct implementation and relevant test evidence;
- `MEDIUM`: direct source evidence, but limited behavioral verification;
- `LOW`: indirect evidence, incomplete scope, or ambiguous implementation;
- `UNKNOWN`: insufficient evidence.

Do not use broad statements such as “the platform already supports authorization” without identifying the enforcement point and relevant negative tests.

## 15. Required baseline report structure

The final baseline report must contain:

1. Executive summary and readiness conclusion.
2. Authorization reference and inspection scope.
3. Repository identity and Git baseline.
4. Project structure map.
5. Runtime and dependency inventory.
6. Test and CI inventory, with execution status clearly separated.
7. ADR-001–ADR-010 implementation mapping.
8. Historical blocker reconciliation.
9. Security and sensitive-file boundary inventory.
10. Reuse and gap assessment.
11. Proposed work-package ownership map.
12. Risks, unknowns, and decisions required.
13. Evidence index.
14. Explicit statement of what was not inspected or not verified.
15. Confirmation that no files or Git state were changed.

### 15.1 Final status

Use one of these conclusions:

- `BASELINE COMPLETE — READY FOR OWNER REVIEW`
- `BASELINE PARTIAL — OWNER DECISIONS REQUIRED`
- `BASELINE BLOCKED — AUTHORIZATION OR ACCESS ISSUE`
- `BASELINE INCONCLUSIVE — EVIDENCE INSUFFICIENT`

A completed baseline is not an implementation approval.

## 16. Stop conditions

Stop inspection and report if:
- the repository or branch does not match the authorization;
- the working tree contains unexpected user changes;
- the requested inspection requires reading secrets or personal data outside scope;
- a command may mutate files or state and is not explicitly permitted;
- tests require unapproved external services or credentials;
- the repository contains active production configuration that could be triggered accidentally;
- evidence conflicts with the accepted ADR baseline;
- an agent asks to make a “small fix” during inspection;
- a task requires broader access than the authorization provides.

## 17. Handoff to Artifact 09 process

After the baseline report is delivered:
1. owner reviews the evidence and unresolved questions;
2. owner approves or rejects the proposed path ownership map;
3. owner confirms the contract revision to implement;
4. owner selects one bounded work package;
5. owner issues a separate implementation authorization using Artifact 10;
6. assigned engineering agent follows Artifact 09;
7. Kilo performs independent read-only QA only when separately authorized.

No implementation agent should treat the baseline report as permission to edit.

## 18. Current status

| Activity | Status |
|---|---|
| Protocol prepared | Complete |
| Repository target confirmed | Not provided in this artifact |
| Read-only inspection authorization | Not issued |
| Repository inspected under this artifact | No |
| Runtime/test baseline refreshed | No |
| ADR implementation mapping | Pending authorized inspection |
| Historical blocker reconciliation | Pending authorized evidence |
| Path ownership map | Pending inspection and owner approval |
| Implementation authorization | Not issued |

**End of Artifact 11 — P0 Read-Only Repository Baseline Inspection Protocol 1.0**
