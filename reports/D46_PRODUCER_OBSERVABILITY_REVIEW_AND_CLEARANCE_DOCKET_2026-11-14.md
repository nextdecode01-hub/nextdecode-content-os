# D46 — Producer Observability Review & Clearance Docket

**Date:** 2026-11-14  
**Status:** CANDIDATE — REVIEW ROUTING ONLY; NO IMPLEMENTATION OR TEST AUTHORITY  
**Depends on:** D44 Production Pipeline Observability Gap Closure Assessment; D45 Producer Stage Instrumentation Contract & Acceptance Plan; canonical M6-P / REG-131; M6-AH / REG-149  
**Purpose:** Convert D45 into a bounded review docket, identify the decisions and evidence needed before any implementation entry, and prevent local RunTracker instrumentation from being mistaken for canonical WP2 workflow execution.

## 1. Executive disposition

D45 is technically prepared for review as a candidate. It is **not cleared for implementation or test execution**.

The proposed increment concerns the existing local Shorts Studio RunTracker and production-run manifest path. It does not establish or implement:
- canonical WP2 WorkflowRun, Job, JobAttempt, Lease or durable execution;
- WP3 worker identity, enrollment, trust or registry;
- WP1 domain persistence or physical schema;
- WP4 artifact registry or lifecycle;
- WP5 approval, rights or protected-action governance;
- a canonical event bus, scheduler, recovery service or publishing workflow.

The dashboard may display only persisted evidence already exposed by the existing authenticated API. It must not infer stage progress, artifact lineage, approval, publishability, analytics or provider activity.

**Decision requested:** determine whether this narrow local observability increment is an acceptable separately bounded engineering task, or whether it must remain deferred until the relevant canonical contract and package gates are closed.

## 2. Evidence baseline carried forward

| Evidence | Source-backed finding | Consequence |
|---|---|---|
| D44 | The current producer records one aggregate `strong_pipeline` stage after successful pipeline return; failure paths can lose internal stage detail | Historical manifests cannot be upgraded by inference |
| D44 | Existing observed manifests have no granular stage/artifact records; detached logs lack reliable run-ID linkage | No retroactive log-to-run association |
| D45 | The producer pipeline has identifiable real stage boundaries from topic selection through metadata assembly | Candidate stage instrumentation can follow actual execution boundaries |
| D45 | RunTracker artifact recording already enforces run-directory containment and SHA-256 hashing | Reuse existing safeguards; do not weaken or bypass them |
| D45 | The API is manifest-backed and authenticated; dashboard can distinguish granular, aggregate-only and not-recorded traces | Preserve read-only API and legacy compatibility |
| M6-P / REG-131 | Implementation and test authorization are separate; named roles, exact paths, owner concurrence, baseline and rollback are required | No code or test action until package entry facts are recorded |
| M6-AH / REG-149 | D01–D12 remain pending owner; Q099 roles/paths are unassigned; M6-P remains binding | No assumed owner, path grant or successor activation |

## 3. Scope decision and boundary tests

Reviewers must disposition each statement independently.

| ID | Boundary statement | Proposed disposition | Required reviewer |
|---|---|---|---|
| D46-B01 | This is local RunTracker observability, not canonical WP2 durable execution | ACCEPT / AMEND / REJECT | Product Owner + architecture |
| D46-B02 | Existing run manifests remain the only source of run/stage/artifact truth for this increment | ACCEPT / AMEND / REJECT | Architecture + engineering owner |
| D46-B03 | No database, DDL, ORM, migration, event bus, worker registry or canonical entity changes are included | ACCEPT / AMEND / REJECT | Architecture + WP1/WP2 as applicable |
| D46-B04 | No historical backfill from detached logs or output folders is allowed | ACCEPT / AMEND / REJECT | Product Owner + security |
| D46-B05 | Only finalized, run-contained artifacts may be recorded using existing integrity checks | ACCEPT / AMEND / REJECT | Security + artifact-domain reviewer |
| D46-B06 | Dashboard progress is stage evidence, never a percentage inferred from stage count | ACCEPT / AMEND / REJECT | Product Owner + UI reviewer |
| D46-B07 | QA completion does not imply rights clearance, approval, publishability or publication | ACCEPT / AMEND / REJECT | WP5/security + Product Owner |
| D46-B08 | No live provider calls, production generation, credentials, uploads, publishing, deployment or spend | ACCEPT / AMEND / REJECT | Security + Product Owner |

A reviewer acknowledgement is not an owner disposition. Each disposition must identify the named decision-maker, role, authority basis, exact sources reviewed, rationale, conditions and effective date.

## 4. Candidate implementation boundary — not an approved allowlist

D45 identifies the following candidate files. They must be re-inspected and converted into an exact path allowlist only after the relevant authority grants it.

| Candidate path | Intended bounded responsibility | Boundary / exclusion |
|---|---|---|
| `app/tracking/run_tracker.py` | Add explicit stage lifecycle persistence to existing manifest mechanism | No new database or canonical workflow model |
| `app/script/pipeline.py` | Emit lifecycle notifications at actual stage boundaries | No provider behavior or production-flow redesign |
| `pipelines/short.py` | Bind stage observer to current run and record finalized run-contained outputs | No promotion/publishing authorization changes |
| `api/main.py` | Serialize bounded, sanitized manifest-backed trace | Preserve auth and read-only behavior |
| `tests/test_run_tracker.py` and focused new tests | Deterministic tracker lifecycle and integrity tests | Tests require separate authorization |
| `tests/test_production_run_observability.py` | API compatibility, auth and legacy-manifest cases | No live provider or production fixtures |
| `dashboard/src/types.ts`, `dashboard/src/api.ts`, `dashboard/src/pages/production-runs.tsx` | Consume and display actual recorded trace | Verify exact current paths and ownership before authorization |
| `reports/` | Record review, implementation and verification evidence | Documentation does not grant implementation authority |

No wildcard path authorization is proposed. Existing dirty and untracked work must be preserved; no cleanup, reset, stash, overwrite or commit is implied.

## 5. Required review outcomes

### 5.1 Product and architecture

- Confirm the user-visible value and exact scope of local producer observability.
- Confirm it does not conflict with the specialist Shorts Studio boundary or P0-A's narrow vertical slice.
- Confirm whether the local manifest format is an acceptable interim source of truth.
- Confirm whether stage lifecycle semantics are compatible with accepted API/Event and lifecycle standards, or explicitly remain local/non-canonical.
- Decide whether the increment can be reviewed independently or must wait for D01 and other upstream owner decisions.

### 5.2 Security and artifact integrity

- Review manifest mutation and interruption semantics.
- Confirm no raw exception, secret, absolute path or unbounded metric is exposed.
- Confirm artifact containment, symlink handling, hash verification and duplicate-name behavior remain fail-closed.
- Confirm no detached logs are trusted as run evidence.
- Confirm read-only authenticated API behavior and no external side effects.

### 5.3 QA and acceptance

- Review the 33 proposed OBS scenarios in D45.
- Confirm which are suitable deterministic local tests and which need additional acceptance authority.
- Confirm malformed/legacy manifest behavior and interrupted-run semantics.
- Confirm test commands, fixture roots, synthetic data, expected evidence and rollback.
- Do not promote proposed OBS identifiers into Artifact 07 IDs. They are candidate local test labels only.

## 6. M6-P entry gate mapping

| M6-P gate | Current state for this candidate | Required closure evidence |
|---|---|---|
| ENTRY-01 source/handoff verification | Must be verified in implementation context | Read canonical handoff and assigned source set |
| ENTRY-02 accepted contract baseline | PARTIAL / PACKAGE-DEPENDENT | Pin accepted sources and record unresolved candidate conflicts |
| ENTRY-03 named writer/reviewer/integration | BLOCKED | Actual Q099 assignments; no inferred roles |
| ENTRY-04 exact writable paths | BLOCKED | Explicit exact path allowlist |
| ENTRY-05 domain/architecture/security concurrence | BLOCKED / PACKAGE-DEPENDENT | Separate attributable dispositions |
| ENTRY-06 branch/base/dirty state | NOT VERIFIED for this package baseline | Authorized read-only inspection and recorded base |
| ENTRY-07 accepted contract versions | PARTIAL | Pin versions; do not promote candidates to frozen standards |
| ENTRY-08 implementation authorization | BLOCKED | Explicit bounded authorization for exact paths and scope |
| ENTRY-09 test authorization | BLOCKED | Separate authorization for exact commands and fixtures |
| ENTRY-10 ENV-01..14 | NOT GRANTED | Applicable environment approvals and no-egress proof; confirm whether any apply to deterministic local-only tests |
| ENTRY-11 commands/fixtures/rollback | PARTIAL | Package-specific approved execution and rollback record |
| ENTRY-12 integration owner | BLOCKED | Named integration owner and conflict-resolution route |

A missing required entry fact means NOT CLEARED. Documentation review does not satisfy implementation or test authorization.

## 7. Review decision record template

For each reviewer, record one separate response:

| Field | Required entry |
|---|---|
| Reviewer | Named individual |
| Role / authority | Product Owner, architecture, security, QA, domain owner or integration owner |
| Decision item | D46-B01..B08 or review section |
| Disposition | ACCEPT / AMEND / REJECT / DEFER; or CONCUR / CONCUR WITH CONDITIONS / OBJECT / DEFER for reviewer concurrence |
| Sources | Exact path, version and clause |
| Rationale | Source-grounded reason |
| Conditions / exclusions | Exact accepted boundary |
| Required successor | Exact document/path/version, or no change |
| Effective date | Explicitly recorded by authority |
| Evidence reference | Durable decision record |

Silence, generic “go ahead”, a technical recommendation or an unassigned role is not a disposition under M6-AH.

## 8. Stop conditions

Stop before implementation if any of the following remains unresolved:
- a reviewer treats this increment as WP2 canonical workflow implementation;
- an accepted contract conflicts with the proposed local stage semantics;
- manifest writes could weaken existing integrity or containment guarantees;
- the API cannot preserve authentication, bounded output and legacy compatibility;
- a proposed dashboard state requires inferred or fabricated data;
- exact writer/reviewer/integration ownership or path authorization is missing;
- implementation authorization or separate test authorization is absent.

No code changes, tests, agent dispatch, database writes, schema/DDL/ORM/migrations, credentials, provider calls, production generation, uploads, publishing, deployment, spend, commit or push are authorized by this docket.

## 9. Recommended sequence after review

1. Obtain separate Product Owner and architecture disposition on D46-B01..B03 and whether this is an independently bounded local increment.
2. Obtain security/artifact-integrity concurrence on D46-B04, D46-B05 and D46-B08.
3. Obtain product/UI and WP5 boundary concurrence on D46-B06 and D46-B07.
4. Reconcile any conflict with accepted API/Event, lifecycle, artifact or governance contracts; do not edit canonical sources from this docket.
5. Only if the increment is accepted as a bounded package, complete M6-P's named roles, exact paths, accepted contract baseline, branch/base/dirty record, implementation authorization and rollback.
6. Obtain separate test authorization, exact deterministic commands/fixtures and applicable environment approval.
7. Implement and verify one bounded increment; report evidence and remaining limitations without claiming WP2–WP6 integration.

The sequence is a prerequisite order, not a delivery estimate or authorization.

## 10. Final disposition

**D46 outcome:** REVIEW DOCKET PREPARED; OWNER/DOMAIN/ARCHITECTURE/SECURITY/QA DISPOSITIONS NOT RECEIVED.

D45 remains a candidate specification. The production observability gap remains open. Home/dashboard stage progress remains limited to what current persisted manifests actually contain. No implementation or test authority is created.

M6-P / REG-131 remains binding. M6-AH / REG-149 remains the controlled activation register. P0 release readiness is not changed by this docket.

---
