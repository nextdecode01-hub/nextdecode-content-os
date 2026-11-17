# D37-D — Owner and Contract Closure Docket

**Date:** 2026-11-13  
**Status:** CONSOLIDATED ACTION REGISTER — OWNER REVIEW REQUIRED  
**Purpose:** Consolidate the minimum decisions blocking the Shorts Studio bridge and WP6 conformance work.  
**Authority:** Artifact 10 owner review/authorization pack; Artifact 09 coding-agent handoff; WP1–WP6 candidate contracts; Contract 10/X-01; Artifact 07 and its WP6 crosswalk/manifest; D37-A/B/C.

## 1. Executive disposition

The next blocker is not a missing Studio UI feature. It is unresolved contract authority and owner disposition across WP1–WP6.

The current documents consistently distinguish:
- accepted architecture principles;
- recommended design details;
- open owner decisions;
- implementation authorization;
- test-environment approval;
- test-execution authorization;
- production authorization.

These are separate gates. Completing this docket does not close them automatically.

**No canonical bridge implementation, schema/API/migration change, harness test execution, agent assignment, provider activation, deployment, upload or publishing is authorized by this docket.**

## 2. Closure register — ordered by dependency

| ID | Priority | Decision / closure required | Accountable owner role | Source of truth | Evidence required to close | Blocks |
|---|---|---|---|---|---|---|
| D37-D-01 | P0 | Confirm WP1 logical schema candidate: ContentVersion payload/title; ContentIdea origin; ContentVariant dimensions/version; StudioProduction ↔ ArtifactVersion link; Job identity boundary; external-reference uniqueness; FK/archive behavior | Product owner with WP1/domain owners | WP1 v0.2 Design Resolution Record; WP1 v0.3 Final Schema Contract Candidate; Canonical Data Dictionary; Contract 11; Part 7 | Explicit accept/change/defer disposition for each remaining WP1 open item; updated decision record | Canonical identity and relationship contracts |
| D37-D-02 | P0 | Resolve WP2/WP3 authority conflict for durable lease, attempt, fencing and worker evidence | Product owner with WP2 and WP3 owners | Contract 10/X-01; WP1–WP6 traceability register; WP2 candidate; WP3 candidate; ADR-005/CF-13/14 | One signed ownership matrix distinguishing authoritative job/attempt/lease state, worker trust/identity, lease evidence, fencing validation and revocation behavior | Any safe workflow/worker bridge |
| D37-D-03 | P0 | Freeze WP2 execution semantics: WorkflowDefinition/Run/Task, Job/JobAttempt, transitions, idempotency, duplicate delivery, retries, cancellation, recovery, outbox/inbox, lease expiry and stale completion | WP2 owner; product owner disposition | WP2 v0.1; API/Event Contract Standard; lifecycle standard; Artifact 07; Batch17/18; Contract 10 | Owner-approved contract and state-transition matrix; all unresolved defaults explicitly accepted or deferred | Durable execution and conformance harness |
| D37-D-04 | P0 | Freeze WP3 worker identity/trust: registration, machine identity evidence, declared/verified/available/authorized capabilities, credential scope/expiry/revocation, assignment, heartbeat and in-flight revocation | WP3 owner; security owner; product owner disposition | WP3 v0.1; Contract 10; ADR-005; CF-13/14; Batch07/20 | Owner-approved lifecycle and trust/assignment contract; revocation and stale-worker behavior resolved | Worker-boundary validation |
| D37-D-05 | P0 | Freeze WP4 artifact lifecycle: Artifact/ArtifactVersion/Manifest, immutable versions, exact-version references, transfer, integrity, quarantine, access scope and retention | WP4 owner; product owner disposition | WP4 v0.1; Part 7; Contract 11; Artifact 07 AR-01..07 | Owner-approved logical contract and exact ownership/linkage rules; no local path/hash promoted to canonical identity | Artifact registration bridge |
| D37-D-06 | P0 | Freeze WP5 quality/rights/review/approval/authorization boundaries and audit semantics | WP5 governance/security owner; product owner disposition | WP5 v0.1; governance contracts; Contract 12; Artifact 07 GV-01..12; D37-A/B | Explicit state/decision ownership; hard QA and rights blockers; approval vs protected authorization; exact artifact/hash/destination binding; denial/audit behavior | Review-to-protected-action boundary |
| D37-D-07 | P0 | Resolve Artifact 07 ↔ WP6 test-case mapping gaps and mandatory scope | WP6 acceptance owner with independent QA and product owner | Artifact 07 §7.2; crosswalk 19; WP6 test-case-level manifest; WP6 validation spec | ID-level mapping/disposition for all gaps; mandatory/deferred/NA rationale; exact oracle per critical test; no severity downgrade | Harness completeness and P0 acceptance |
| D37-D-08 | P0 | Approve WP6 isolated test environment and execution controls | Product owner; environment/security owner | WP6 ENV-01..14; Artifact 07; D37-C | Evidence for isolation, DB/storage/worker, test-only policy, outbound denial, logs/redaction, teardown, test-only lease/retry parameters, clock and abort controls | Any test execution |
| D37-D-09 | P0 | Issue bounded implementation authorization for the contract-conformance harness | Product owner | Artifact 10; Artifact 09; WP6 stage gates; D37-B/C | Explicit authorization naming baseline, allowed files/paths, scope, permitted source/test changes, tools, environment, reviewers, stop conditions and prohibited actions | Harness code implementation |
| D37-D-10 | P1 | Reconcile Studio adapter target (Part 7 proposal) with approved WP2–WP5 contracts and Contract 11 lifecycle | Studio/domain owner with WP2–WP5 owners | Architecture Part 7; Contracts 10/11; WP1–WP5 final contracts; D37-A/B/C | Versioned adapter request/response contract with canonical references returned by owning services; local IDs retained only as provenance | Canonical Studio integration |
| D37-D-11 | P1 | Approve synthetic WP6 vertical-slice execution and independent QA review | Product owner; WP6 acceptance owner; independent QA | Artifact 07; WP6; approved harness evidence; D37-C | Separate execution approval; stable review target; evidence package; independent read-only QA disposition | P0-A acceptance decision |
| D37-D-12 | P2 | Consider production/distribution authorization only after P0 acceptance | Product owner and governance owner | Artifact 07 stage gates; WP5; publishing governance; release decision | Separate production decision and exact protected-action authorization | Any production side effect |

## 3. Decisions that must not be conflated

| Decision | Does not imply |
|---|---|
| Architecture direction accepted | Detailed contract frozen |
| Candidate contract reviewed | Implementation authorized |
| Implementation authorized | Test environment approved |
| Test environment approved | Test execution authorized |
| Harness tests pass | Canonical services integrated |
| WP6 vertical slice passes | Production distribution authorized |
| Human review complete | Approval decision exists |
| Approval exists | Protected-action authorization exists |
| Local task/run/artifact exists | Canonical WP2/WP3/WP4 record exists |

## 4. Exact source gaps that need owner disposition

### WP1 — domain/persistence
WP1 v0.2 already narrows nine open questions, and WP1 v0.3 consolidates the candidate. Do not recreate this design. Owner disposition is needed on:
- ContentVersion detailed schema and payload/title placement.
- ContentIdea origin relationship.
- ContentVariant controlled dimensions/profile/revision.
- ContentVariant ↔ StudioProduction ↔ exact ArtifactVersion lineage.
- Whether a minimal Job identity is physically in WP1 or begins in WP2.
- External-reference uniqueness scope.
- Exact restrictive FK/archive behavior.

WP1 v0.2 marks these as recommended/open/deferred; they are not silently accepted by this docket.

### WP2/WP3 — execution and worker trust
The source documents leave the ownership split requiring explicit resolution:
- WP2 owns durable Job/JobAttempt execution semantics and authoritative workflow progression.
- WP3 owns canonical worker identity, registration/trust, capability verification, credential lifecycle and worker trust evidence.
- Contract 10/X-01 and the WP1–WP6 traceability register are not fully aligned on lease/fencing authority.
- Resolve whether the lease record/state is WP2-owned with WP3-provided worker trust/fencing evidence, or another explicitly documented split. Do not implement either interpretation until the owner decision is recorded.

### WP4 — artifacts
Part 7 is an architecture proposal, not implementation approval. WP4 must freeze the canonical artifact/version/manifest and transfer boundary before the adapter can register outputs. Local SHA-256 and file paths are evidence only until canonical WP4 registration returns an exact version reference.

### WP5 — governance
Keep distinct:
1. QA outcome;
2. rights determination;
3. human review;
4. approval decision;
5. protected-action authorization;
6. external execution outcome;
7. audit evidence.

No local Studio status, checkbox or review completion may substitute for these records.

### WP6 — acceptance
Artifact 07 remains the authority for IDs and severity. The current manifest identifies mapping gaps including ID-02/04, ST-02..04/ST-06, Q-02/Q-06/Q-07, WK-08, API-01/02/05/06, GV-02/03/11 and OP-03/04/06. Each needs direct oracle mapping, explicit deferral or approved not-applicable rationale. No WP6 trace label may downgrade Artifact 07 severity.

## 5. Minimal owner review packet

Use existing documents rather than creating another duplicate contract pack. The owner review should be performed in this order:

1. **WP1:** review WP1 v0.2 and v0.3 together; record each unresolved field/link decision.
2. **WP2/WP3:** resolve X-01 ownership first; then freeze execution and worker contracts as a coordinated pair.
3. **WP4:** freeze exact immutable artifact/version and transfer ownership.
4. **WP5:** freeze review/approval/authorization distinctions and protected-action denial rules.
5. **WP6:** approve Artifact 07 test mapping and mandatory scope only after the contracts above are stable.
6. **Environment:** approve ENV-01..14 evidence and test-only parameters.
7. **Authorization:** issue a separate bounded implementation authorization for D37-C harness coding.

Do not ask each agent to independently invent or freeze the same shared terms. WP2/WP3 and WP4/WP5 must reconcile shared interfaces jointly, with one designated canonical owner per entity/state.

## 6. Agent contribution boundary

Agents may be asked to produce read-only evidence/recommendations only where the governing handoff permits it. This docket does not dispatch agents or grant them implementation rights.

Suggested evidence responsibilities after owner approval:
- WP1 specialist: enumerate exact schema candidate open fields and source citations; no DDL.
- WP2 specialist: propose lease/attempt ownership options with source clauses; no unilateral decision.
- WP3 specialist: propose worker identity/trust and fencing evidence split; no credentials.
- WP4 specialist: reconcile Part 7/Contract 11 artifact lineage; no storage implementation.
- WP5 specialist: reconcile QA/rights/review/approval/authorization; no policy mutation.
- WP6 specialist: complete Artifact 07 ID-level oracle gaps; no tests.
- Independent QA: review the frozen evidence target read-only; no code/config/Git changes.

## 7. Exit criteria

The docket can be marked closed only when:
- Every P0 row D37-D-01 through D37-D-09 has an owner disposition and source-backed evidence.
- WP2/WP3 lease/fencing authority has no unresolved contradiction.
- WP1–WP5 contract versions and ownership are explicitly frozen or open items are formally deferred with impact.
- Artifact 07 criticality is preserved and every mandatory acceptance oracle is mapped.
- Test environment and exact execution parameters are separately approved.
- Bounded implementation authorization names exact scope and stop conditions.

D37-D closure does not itself mean code is implemented or P0 is accepted.

## 8. Current status snapshot

| Area | Status |
|---|---|
| D37-A local/canonical reconciliation | Complete |
| D37-B implementation boundary | Complete |
| D37-C harness specification | Complete |
| WP1 detailed owner disposition | Open |
| WP2/WP3 X-01 lease/fencing reconciliation | Open |
| WP2–WP5 detailed contract freeze | Open |
| Artifact 07/WP6 mapping gaps | Open |
| WP6 environment approval | Not granted |
| Harness implementation authorization | Not granted |
| Test execution authorization | Not granted |
| Production authorization | Not granted |

## 9. Final recommendation

**D37-D closure docket: COMPLETE — documentation consolidation only.**

The next action is owner disposition of the existing WP1–WP6 candidate documents, beginning with the WP2/WP3 X-01 conflict and WP1 v0.2/v0.3 open fields. Avoid another new architecture document. Record decisions in the existing owner decision register and update the relevant candidate versions only after explicit disposition.

No source code, schemas, APIs, migrations, tests, runtime tasks, Git state, external services, uploads, publishing or deployments were changed or executed.
