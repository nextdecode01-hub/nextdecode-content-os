# NEXTDECODE Content OS
## Artifact 12 — P0 Repository Baseline Capture Workbook & Evidence Register 1.0

**Document status:** Fillable inspection workbook — not an inspection result  
**Version:** 1.0  
**Purpose:** Capture repository observations in a consistent, auditable format after a separate read-only authorization is issued.  
**Related artifacts:** Artifacts 06–11; Accepted P0 Architecture Decision Baseline 1.0.

---

## 1. How to use this workbook

This workbook is the practical companion to Artifact 11. Artifact 11 explains how an authorized reviewer should inspect the repository; this document provides the tables and evidence records in which to capture the findings.

**Do not fill this workbook with guesses or historical assumptions.** Use `NOT INSPECTED`, `NOT PROVIDED`, `NOT VERIFIED`, or `NOT APPLICABLE` where appropriate.

This is a template only:
- no repository has been inspected through this artifact;
- no current branch, commit, file path, runtime version, or test result is asserted;
- no coding agent has been assigned;
- no repository access or modification is authorized.

### 1.1 Evidence labels

| Label | Meaning |
|---|---|
| OBSERVED | Directly seen in the authorized repository or environment |
| VERIFIED | Behavior confirmed by an authorized test or reproducible check |
| HISTORICAL | Reported in older project evidence; not rechecked |
| INFERRED | Reasoned interpretation; not direct proof |
| UNKNOWN | Insufficient evidence |
| NOT INSPECTED | Outside the authorized inspection scope |
| NOT APPLICABLE | Confirmed not relevant to this repository/task |

### 1.2 Confidence labels

- **HIGH:** Direct source/configuration evidence plus relevant behavioral verification.
- **MEDIUM:** Direct source/configuration evidence, but limited behavioral verification.
- **LOW:** Indirect, partial, or ambiguous evidence.
- **UNKNOWN:** No reliable evidence.

## 2. Inspection authorization record

Complete this section before any repository inspection.

| Field | Value |
|---|---|
| Authorization ID | NOT PROVIDED |
| Authorized by | NOT PROVIDED |
| Authorization date | NOT PROVIDED |
| Expiry / stop condition | NOT PROVIDED |
| Assigned inspector | NOT PROVIDED |
| Repository name | NOT PROVIDED |
| Repository URL or exact local path | NOT PROVIDED |
| Permitted branch / commit | NOT PROVIDED |
| Allowed operations | NOT PROVIDED |
| Explicitly prohibited operations | NOT PROVIDED |
| Test execution permitted? | NO — unless separately specified |
| External network permitted? | NO — unless separately specified |
| Secrets/data handling rules | NOT PROVIDED |
| Required report destination | NOT PROVIDED |

**Readiness result:** `NOT READY — authorization details are incomplete`

## 3. Repository identity record

Complete only from direct, authorized observation.

| Field | Observed value | Evidence ID | Notes |
|---|---|---|---|
| Repository name | NOT INSPECTED | — | |
| Remote URL | NOT INSPECTED | — | Redact embedded credentials |
| Local working path | NOT INSPECTED | — | |
| Current branch | NOT INSPECTED | — | |
| Full commit hash | NOT INSPECTED | — | |
| Working tree clean/dirty | NOT INSPECTED | — | |
| Untracked files present? | NOT INSPECTED | — | |
| Submodules present? | NOT INSPECTED | — | |
| Relevant tags | NOT INSPECTED | — | Historical tags are not proof of current state |
| Inspection timestamp | NOT INSPECTED | — | Include timezone |
| Inspector identity | NOT PROVIDED | — | |

### 3.1 Working-tree safety check

Record unexpected user changes before proceeding.

| Check | Result | Evidence | Action |
|---|---|---|---|
| Existing modified files | NOT INSPECTED | — | Stop if unexpected |
| Existing staged changes | NOT INSPECTED | — | Stop if unexpected |
| Untracked user files | NOT INSPECTED | — | Do not delete or overwrite |
| Active processes using repository | NOT INSPECTED | — | Do not terminate without authorization |
| Local databases or generated data | NOT INSPECTED | — | Do not modify |

## 4. Project structure inventory

Record only meaningful architectural areas. Exclude virtual environments, caches, build output, generated media, and dependency vendor directories from detailed listings.

| Area | Observed path(s) | Responsibility | Evidence ID | Status | Confidence |
|---|---|---|---|---|---|
| Application entry points | NOT INSPECTED | UNKNOWN | — | NOT INSPECTED | UNKNOWN |
| API/interface | NOT INSPECTED | UNKNOWN | — | NOT INSPECTED | UNKNOWN |
| Orchestration/scheduling | NOT INSPECTED | UNKNOWN | — | NOT INSPECTED | UNKNOWN |
| Worker execution | NOT INSPECTED | UNKNOWN | — | NOT INSPECTED | UNKNOWN |
| Domain models/lifecycle | NOT INSPECTED | UNKNOWN | — | NOT INSPECTED | UNKNOWN |
| Persistence/database | NOT INSPECTED | UNKNOWN | — | NOT INSPECTED | UNKNOWN |
| Queue/events | NOT INSPECTED | UNKNOWN | — | NOT INSPECTED | UNKNOWN |
| Artifact/media storage | NOT INSPECTED | UNKNOWN | — | NOT INSPECTED | UNKNOWN |
| Quality/rights | NOT INSPECTED | UNKNOWN | — | NOT INSPECTED | UNKNOWN |
| Publishing/distribution | NOT INSPECTED | UNKNOWN | — | NOT INSPECTED | UNKNOWN |
| Configuration | NOT INSPECTED | UNKNOWN | — | NOT INSPECTED | UNKNOWN |
| Tests/fixtures | NOT INSPECTED | UNKNOWN | — | NOT INSPECTED | UNKNOWN |
| CI/developer tooling | NOT INSPECTED | UNKNOWN | — | NOT INSPECTED | UNKNOWN |
| Documentation | NOT INSPECTED | UNKNOWN | — | NOT INSPECTED | UNKNOWN |

## 5. Runtime and dependency inventory

Keep declared configuration separate from the installed environment.

| Component | Declared version/config | Observed installed value | Evidence ID | Confidence | Notes |
|---|---|---|---|---|---|
| Operating system | NOT INSPECTED | NOT INSPECTED | — | UNKNOWN | |
| Shell / execution environment | NOT INSPECTED | NOT INSPECTED | — | UNKNOWN | |
| Primary language runtime | NOT INSPECTED | NOT INSPECTED | — | UNKNOWN | |
| Secondary runtime | NOT INSPECTED | NOT INSPECTED | — | UNKNOWN | |
| Package manager | NOT INSPECTED | NOT INSPECTED | — | UNKNOWN | |
| Dependency manifest | NOT INSPECTED | N/A | — | UNKNOWN | |
| Lockfile | NOT INSPECTED | N/A | — | UNKNOWN | |
| Database client/driver | NOT INSPECTED | NOT INSPECTED | — | UNKNOWN | |
| Test framework | NOT INSPECTED | NOT INSPECTED | — | UNKNOWN | |
| Linter/type checker | NOT INSPECTED | NOT INSPECTED | — | UNKNOWN | |
| Build tooling | NOT INSPECTED | NOT INSPECTED | — | UNKNOWN | |
| External SDKs | NOT INSPECTED | NOT INSPECTED | — | UNKNOWN | |

## 6. Test and CI inventory

### 6.1 Static inventory

| Test group / workflow | Location | Declared command | External dependency? | Execution authorized? | Status |
|---|---|---|---|---|---|
| Unit tests | NOT INSPECTED | NOT INSPECTED | UNKNOWN | NO | NOT INSPECTED |
| Integration tests | NOT INSPECTED | NOT INSPECTED | UNKNOWN | NO | NOT INSPECTED |
| Contract tests | NOT INSPECTED | NOT INSPECTED | UNKNOWN | NO | NOT INSPECTED |
| End-to-end tests | NOT INSPECTED | NOT INSPECTED | UNKNOWN | NO | NOT INSPECTED |
| Security tests | NOT INSPECTED | NOT INSPECTED | UNKNOWN | NO | NOT INSPECTED |
| Lint/type checks | NOT INSPECTED | NOT INSPECTED | UNKNOWN | NO | NOT INSPECTED |
| Build checks | NOT INSPECTED | NOT INSPECTED | UNKNOWN | NO | NOT INSPECTED |
| CI workflows | NOT INSPECTED | NOT INSPECTED | UNKNOWN | NO | NOT INSPECTED |

### 6.2 Test execution record

Only complete this section if each command was explicitly authorized.

| Run ID | Exact command | Revision | Environment | Exit code | Pass | Fail | Skip | Side effects |
|---|---|---|---|---|---:|---:|---:|---|
| — | NOT RUN | — | — | — | — | — | — | — |

**Execution status:** `NOT RUN — no test execution authorization recorded`

### 6.3 Test result interpretation

For every test run, record:
- what behavior the test actually covers;
- which requirement or contract it supports;
- what it does not prove;
- whether external services, credentials, or real data were involved;
- whether files, caches, databases, or generated outputs were created.

Never report a historical test count as a current result without re-verification.

## 7. ADR implementation mapping

Use the status values in Artifact 11. Do not mark an ADR implemented based only on a class name, comment, TODO, mock, or documentation statement.

| ADR | Required evidence focus | Status | Evidence IDs | Gap / risk | Confidence |
|---|---|---|---|---|---|
| ADR-001 | UUIDv7 canonical identity | NOT ASSESSED | — | — | UNKNOWN |
| ADR-002 | Authoritative PostgreSQL-compatible persistence | NOT ASSESSED | — | — | UNKNOWN |
| ADR-003 | Durable queue and transactional outbox/inbox | NOT ASSESSED | — | — | UNKNOWN |
| ADR-004 | Versioned HTTP/JSON and schema validation | NOT ASSESSED | — | — | UNKNOWN |
| ADR-005 | Worker identity, scoped credentials, capabilities | NOT ASSESSED | — | — | UNKNOWN |
| ADR-006 | Relational artifact metadata and storage abstraction | NOT ASSESSED | — | — | UNKNOWN |
| ADR-007 | Centralized authorization and adapter enforcement | NOT ASSESSED | — | — | UNKNOWN |
| ADR-008 | Four QA outcomes and hard-blocker enforcement | NOT ASSESSED | — | — | UNKNOWN |
| ADR-009 | Evidence-backed, use-specific rights enforcement | NOT ASSESSED | — | — | UNKNOWN |
| ADR-010 | Separate lifecycle state machines | NOT ASSESSED | — | — | UNKNOWN |

### 7.1 ADR evidence notes

For each ADR, capture:
- relevant source paths and symbols;
- relevant configuration or schema;
- test references;
- observed behavior;
- missing behavior;
- any contradiction with the accepted ADR;
- confidence and limitations.

## 8. Historical blocker reconciliation

These identifiers come from earlier project reports and must be reconciled against original acceptance criteria and current evidence.

| Item | Original report/evidence | Current code evidence | Test evidence | Current status | Follow-up |
|---|---|---|---|---|---|
| G1 | NOT LOCATED | NOT INSPECTED | NOT RUN | UNKNOWN | Locate original criterion |
| G2 | NOT LOCATED | NOT INSPECTED | NOT RUN | UNKNOWN | Locate original criterion |
| G3 | NOT LOCATED | NOT INSPECTED | NOT RUN | UNKNOWN | Locate original criterion |
| U1 | NOT LOCATED | NOT INSPECTED | NOT RUN | UNKNOWN | Locate original criterion |
| D1 | NOT LOCATED | NOT INSPECTED | NOT RUN | UNKNOWN | Locate original criterion |
| Traceability v2 | NOT LOCATED | NOT INSPECTED | NOT RUN | UNKNOWN | Locate original criterion |
| Run-tracker runtime integration | NOT LOCATED | NOT INSPECTED | NOT RUN | UNKNOWN | Locate original criterion |

Do not close a blocker because a similarly named module exists. Closure requires the original expected behavior and current verification evidence.

## 9. Security and sensitive-file inventory

Do not expose secret values. Record only category, safe path reference, and handling status.

| Category | Path/location | Tracked? | Content read? | Exposure concern | Recommended action |
|---|---|---|---|---|---|
| Environment files | NOT INSPECTED | UNKNOWN | NO | UNKNOWN | Avoid reading values |
| API keys/tokens | NOT INSPECTED | UNKNOWN | NO | UNKNOWN | Never copy into report |
| Private keys/certificates | NOT INSPECTED | UNKNOWN | NO | UNKNOWN | Restrict access |
| Local databases/dumps | NOT INSPECTED | UNKNOWN | NO | UNKNOWN | Do not open without scope |
| Personal/customer data | NOT INSPECTED | UNKNOWN | NO | UNKNOWN | Synthetic data preferred |
| Creator media/rights evidence | NOT INSPECTED | UNKNOWN | NO | UNKNOWN | Do not export |
| Production configuration | NOT INSPECTED | UNKNOWN | NO | UNKNOWN | Do not activate |
| Logs/diagnostics | NOT INSPECTED | UNKNOWN | NO | UNKNOWN | Check for sensitive values before sharing |

If a secret exposure is found, report the location and risk without reproducing the secret. Do not rotate or revoke credentials unless separately authorized.

## 10. Reuse and gap assessment

| P0 capability | Existing component | Evidence | Reuse suitability | Gap | Proposed bounded action |
|---|---|---|---|---|---|
| Canonical identifiers | NOT INSPECTED | — | UNKNOWN | UNKNOWN | Pending |
| Shared persistence | NOT INSPECTED | — | UNKNOWN | UNKNOWN | Pending |
| Durable job queue | NOT INSPECTED | — | UNKNOWN | UNKNOWN | Pending |
| API contracts/schema validation | NOT INSPECTED | — | UNKNOWN | UNKNOWN | Pending |
| Worker identity | NOT INSPECTED | — | UNKNOWN | UNKNOWN | Pending |
| Authorization | NOT INSPECTED | — | UNKNOWN | UNKNOWN | Pending |
| Artifact metadata | NOT INSPECTED | — | UNKNOWN | UNKNOWN | Pending |
| Artifact transfer | NOT INSPECTED | — | UNKNOWN | UNKNOWN | Pending |
| QA outcomes | NOT INSPECTED | — | UNKNOWN | UNKNOWN | Pending |
| Rights enforcement | NOT INSPECTED | — | UNKNOWN | UNKNOWN | Pending |
| Audit/correlation | NOT INSPECTED | — | UNKNOWN | UNKNOWN | Pending |
| Shorts Studio integration | NOT INSPECTED | — | UNKNOWN | UNKNOWN | Pending |

Prefer preserving working components and integrating through bounded interfaces when evidence supports reuse. Do not recommend a wholesale rewrite without documenting why existing components cannot satisfy the approved contracts.

## 11. Proposed path ownership map

This map is a proposal only. It becomes actionable only after owner approval and a separate implementation authorization.

| Work package | Candidate paths | Shared paths | Proposed owner | Reviewer | Owner approval |
|---|---|---|---|---|---|
| WP-0 Baseline | Report/documentation only | None | To be assigned | Kilo | Pending |
| WP-1 Contracts/schema | Pending inspection | Pending | To be assigned | Kilo | Pending |
| WP-2 Identity/authorization | Pending inspection | Pending | To be assigned | Kilo | Pending |
| WP-3 Jobs/leases/queue | Pending inspection | Pending | To be assigned | Kilo | Pending |
| WP-4 Worker identity/capabilities | Pending inspection | Pending | To be assigned | Kilo | Pending |
| WP-5 Artifact metadata/transfer | Pending inspection | Pending | To be assigned | Kilo | Pending |
| WP-6 QA/rights/audit/integration | Pending inspection | Pending | To be assigned | Kilo | Pending |

## 12. Risk and decision log

| ID | Finding / uncertainty | Evidence | Impact | Severity | Owner decision required | Status |
|---|---|---|---|---|---|---|
| RB-001 | Repository target not yet recorded | Authorization section | Inspection cannot start | High | Confirm exact target and scope | Open |
| RB-002 | Detailed contracts awaiting owner review | Artifact 08 status | Implementation requirements may be ambiguous | High | Approve/amend/defer contracts | Open |
| RB-003 | Current runtime and test baseline unknown | No fresh inspection | Compatibility and test planning uncertain | Medium | Authorize baseline capture | Open |
| RB-004 | Historical blockers not reconciled | Prior reports only | Closure status uncertain | High | Locate original evidence | Open |
| RB-005 | Path ownership not established | No current file map | Agent edit conflicts possible | High | Review proposed ownership map | Open |
| RB-006 | Operational/provider choices remain open | ADR baseline and Artifact 08 | Deployment choices cannot be finalized | Medium | Decide only first-slice necessities | Open |

Add rows as evidence emerges. Do not lower severity without a recorded rationale.

## 13. Evidence register

Every material finding should point to an evidence record.

| Evidence ID | Type | Source/path | Revision | Location (line/symbol) | Observation | Requirement/ADR | Confidence |
|---|---|---|---|---|---|---|---|
| EV-001 | Authorization | NOT PROVIDED | — | — | No inspection authorization recorded in this workbook | Artifact 10 | HIGH |
| EV-002 | Repository metadata | NOT INSPECTED | — | — | Repository identity not captured | Baseline | UNKNOWN |
| EV-003 | Test result | NOT RUN | — | — | No current test execution evidence | Test baseline | UNKNOWN |

### 13.1 Evidence record template

```text
Evidence ID:
Evidence type: Source | Configuration | Test | Log | Git metadata | Documentation | Other
Repository revision:
Exact path or source:
Line range / symbol / command:
Observed fact:
Related requirement / ADR / contract:
Interpretation (separate from observed fact):
Confidence: HIGH | MEDIUM | LOW | UNKNOWN
Limitations:
Sensitive data reviewed/redacted:
Collected by:
Timestamp:
```

## 14. Findings and recommendation format

For each finding, use:

```text
Finding ID:
Title:
Category: Architecture | Contract | Security | Reliability | Testing | Integration | Operations
Severity: Critical | High | Medium | Low | Informational
Status: Confirmed | Partially confirmed | Unverified | Not found | Contradicted
Observed fact:
Evidence IDs:
Affected ADR/contract:
Impact:
Recommended action:
Owner decision required:
Confidence:
```

Separate:
- what was directly observed;
- what the inspector believes it means;
- what remains unknown;
- what action is recommended.

## 15. Final baseline summary

Complete only after authorized inspection.

| Summary item | Result |
|---|---|
| Repository identity confirmed | NOT INSPECTED |
| Branch and commit captured | NOT INSPECTED |
| Working tree assessed | NOT INSPECTED |
| Project structure mapped | NOT INSPECTED |
| Runtime/dependencies mapped | NOT INSPECTED |
| Test/CI inventory complete | NOT INSPECTED |
| Tests executed under authorization | NO |
| ADR mapping complete | NO |
| Historical blockers reconciled | NO |
| Sensitive-file boundary assessed | NO |
| Reuse/gap assessment complete | NO |
| Path ownership proposed | NO |
| Owner review completed | NO |

Select one final conclusion after the inspection:
- `BASELINE COMPLETE — READY FOR OWNER REVIEW`
- `BASELINE PARTIAL — OWNER DECISIONS REQUIRED`
- `BASELINE BLOCKED — AUTHORIZATION OR ACCESS ISSUE`
- `BASELINE INCONCLUSIVE — EVIDENCE INSUFFICIENT`

A baseline report is not permission to implement.

## 16. Final handoff checklist

Before sending the baseline report to the owner:
- [ ] Authorization ID and scope are recorded.
- [ ] Repository identity and exact revision are recorded.
- [ ] No unapproved operation was performed.
- [ ] No files or Git state were changed.
- [ ] Test execution is clearly separated from static inspection.
- [ ] Historical evidence is labeled historical.
- [ ] Every substantive finding has an evidence ID.
- [ ] Secrets and personal data are excluded or safely redacted.
- [ ] ADR mappings use evidence-based statuses.
- [ ] Historical blockers are not marked closed without proof.
- [ ] Unknowns and uninspected areas are explicit.
- [ ] Proposed path ownership is clearly labeled as a proposal.
- [ ] Owner decisions and next gates are listed.

## 17. Current workbook state

**Workbook status:** Blank template prepared.  
**Repository inspection:** Not performed.  
**Authorization:** Not issued.  
**Implementation:** Not authorized.

The next legitimate action is to complete the owner review and issue a separate, bounded read-only authorization. Once authorized, an inspector can populate this workbook using Artifact 11's protocol.

**End of Artifact 12 — P0 Repository Baseline Capture Workbook & Evidence Register 1.0**
