# NEXTDECODE P0 — Owner Decision & Evidence Closure Docket
**Document ID:** ND-P0-DEC-EVID-002  
**Version:** 0.1  
**Prepared:** 3 November 2026  
**Status:** Consolidated review docket — owner/domain disposition required  
**Authority:** Documentation only; no implementation, release or publishing authorization.

## 1. How to use this docket

This is a focused decision docket for the open items surfaced by Batches 14, 16, and 19–24. It is not a request to decide every provider or operational number immediately. Close decisions in dependency order. Where a decision is genuinely premature, explicitly mark it **DEFERRED**, name the dependency and define the evidence that will make it decidable.

No entry is accepted merely because it appears in this docket. The authorized owner must record ACCEPT / REJECT / DEFER, exact scope, rationale, date, and source/contract version.

## 2. Priority owner decisions

| ID | Priority | Decision / disposition required | Primary source(s) | Proposed owner route | Minimum closure evidence |
|---|---|---|---|---|---|
| DEC-01 | P0 blocker | Confirm authoritative ADR-001–010 status and provenance trail | Accepted Architecture Baseline 1.0; ADR Pack; Decision Register; B15 | Project owner / governance | Original decision record, exact wording, date, approver and supersession link |
| DEC-02 | P0 blocker | Resolve canonical rights vocabulary and state semantics | ADR-009; CF-20; Contract 07; B16; B19 | Contract 07 owner + project owner | Canonical enum, definitions, transitions, use/evidence binding, compatibility rule; explicit rejection of unsafe automatic mapping |
| DEC-03 | P0 blocker | Confirm ODR master source and ODR-22 status | B14; B15; B16; Batch 07 index | Governance/document control | Authoritative register, provenance per row; ODR-22 either source-backed exact decision or explicitly provisional |
| DEC-04 | P0 blocker | Establish Artifact 08 v1.0/v1.1 lineage and precedence | Artifact 08 records; B15; B16; B24 | Project owner / document control | File identity/hash, owner approval evidence, purpose, supersession statement |
| DEC-05 | P0 blocker | Freeze domain ownership and cardinality for WorkflowRun, TaskInstance, Job, JobAttempt | Data Dictionary; Lifecycle Standard; B16; B17; B19 | WP-1/WP-2 owners | ERD/cardinality, state owner, transition authority, lifecycle/execution mapping |
| DEC-06 | P0 blocker | Confirm Actor↔AgentIdentity linkage and result-submission binding | Contract 10; Identity & Security; B16; Batch18; AGW handoff | Identity owner + Contract 10 owner | Canonical actor reference, immutable agent version, worker/attempt/lease/fencing bindings and negative tests |
| DEC-07 | P0 blocker | Freeze API/event schema bundle and compatibility/error behavior | API/Event Standard; B18; B16 | API/domain owners | Versioned schemas, required/optional fields, error catalogue, compatibility rules, event idempotency/correlation |
| DEC-08 | P0 blocker | Freeze WP-4 artifact identity/version/manifest/transfer boundary | Data Dictionary; B16; B18; B19; B23 | Asset Management | Artifact vs ArtifactVersion model, immutable manifest, checksum, quarantine, transfer and restore semantics |
| DEC-09 | P0 blocker | Freeze central authorization decision contract and adapter enforcement | ADR-007; CF-22; Contract 07; B16; B20 | Central Authorization + Distribution | Decision inputs/outputs, policy version, principal/capability, destination/resource binding, pause and adapter tests |
| DEC-10 | P1 | Approve worker enrollment, credential lifecycle, capability model and fencing | ADR-005; B16; B20 | Worker Registry / Security | Principal taxonomy, issuer, expiry/revocation, bootstrap trust, capability registry and test oracles |
| DEC-11 | P1 | Approve physical persistence choices after logical schema freeze | B19; ADR-002/003 | Persistence owner | DB engine/version/topology, extensions, physical schema, indexes, isolation, claim algorithm and migration plan |
| DEC-12 | P1 | Approve configuration registry and environment isolation model | B22; B20 | Platform/config owner | Key registry, precedence, secret-reference method, safe defaults, environment separation and drift controls |
| DEC-13 | P1 | Approve observability contract before selecting tooling | B21; API/Event Standard; B20 | Operations/platform owner | Correlation/cause fields, event/error taxonomy, redaction, metric cardinality, health semantics and retention |
| DEC-14 | P1 | Set recovery priorities and RPO/RTO/WRT | B23; B19–22 | Project owner + operations | Critical journey tiers, target values, backup scope, restore order and measured rehearsal |
| DEC-15 | P1 | Approve performance workload model and numeric budgets | B24; B21–23 | Project owner + domain owners | Representative workload/corpus, baseline measurements, latency/queue-age targets, concurrency/resource quotas |
| DEC-16 | P1 | Approve retention, deletion, legal hold and backup lifecycle | Data Dictionary; B19–23; B20 | Governance/privacy + domain owners | Data-class matrix, deletion authority, legal hold, backup expiry and audit-preservation rules |
| DEC-17 | P1 | Define independent QA reviewer, evidence custody and waiver authority | B14; B13 | Project owner / QA | Named independent reviewer, evidence location, reproducibility standard, non-waivable hard blockers |
| DEC-18 | P2 / deferred | Choose telemetry dashboard, exporter and alert provider | B21; B22; B24 | Operations owner | Only after telemetry contract, no-paid-services review and owner approval |
| DEC-19 | P2 / deferred | Choose cloud hosting, region, object storage and managed queue providers | ADR-002/003/006; B19; B22–24 | Project owner | Architecture fit, ₹0/free-first impact, security/privacy, exit plan and explicit spend authorization |
| DEC-20 | P2 / deferred | Define multi-user/workspace and autoscaling scope | B16; B24 PCD-13/15 | Project owner | Explicit scope change; not part of initial single-owner Creator Mode by default |

## 3. Evidence plan mapped to Batch 14 G0–G8

| Gate | Required closure package | Current evidence position | Stop condition |
|---|---|---|---|
| G0 — Source authority | Source inventory, owner decision provenance, ODR reconciliation, conflict register | Partial inventory and conflicts documented; missing/ambiguous sources remain | Critical source or decision remains provisional/unverified |
| G1 — Contract freeze | Frozen domain/API/event/schema/lifecycle/policy contracts, traceability, compatibility review | Candidate documents exist; detailed freeze not granted | Ownership, states, interfaces, rights or policy semantics remain ambiguous |
| G2 — Implementation integrity | Exact source revision, dirty-tree inventory, build/config/migration provenance | Historical audit baseline exists; current candidate provenance must be refreshed before execution | Candidate cannot be reproduced or provenance unclear |
| G3 — Functional acceptance | WP1–WP6 unit/component/integration/E2E evidence | Existing historical tests are not a complete fresh end-to-end acceptance package | Any mandatory requirement fails or lacks an oracle |
| G4 — Resilience & security | Negative tests, failure injection, restore, revocation, fencing, least privilege | Design test catalogues exist; integrated evidence not established | Critical/high security or recovery finding remains open |
| G5 — Governance acceptance | Rights, QA, approval, central authorization, pause, audit and adapter enforcement | Design exists; rights vocabulary conflict remains unresolved | Unknown/denied rights or missing authorization can pass |
| G6 — Independent QA | Reproduced tests, evidence sampling, findings, retests and disposition | Not demonstrated for the exact complete candidate | Evidence incomplete or blocking findings remain open |
| G7 — Owner release decision | Exact candidate manifest, QA disposition, residual risks, exclusions and signed decision | Not granted | No explicit recorded owner acceptance |
| G8 — Controlled release/post-check | Separate authorization, operator record, health checks, rollback readiness and monitoring | Not authorized | Candidate drift, unauthorized action or failed post-check |

## 4. Suggested parallel closure packages

Parallelize document reconciliation, not authority decisions or side effects.

### Package A — Authority & governance
- Reconcile ADR/CF/ODR and Artifact 08 lineage.
- Resolve rights-state vocabulary with Contract 07.
- Preserve all unresolved owner decisions and source references.
- Output: source authority map, exact conflict dispositions, revised decision register proposal.

### Package B — Domain & persistence
- Reconcile Data Dictionary, Lifecycle Standard, B16, B17 and B19.
- Close entity ownership/cardinality and logical schema.
- Keep physical DB/provider choices explicitly open where not accepted.
- Output: WP-1/WP-2 field/cardinality matrix, ERD changes required, persistence open-decision list.

### Package C — Worker, agent & artifact contracts
- Reconcile Contract 10, Identity & Security, B16, B18, B20 and AGW handoff.
- Close Actor/AgentIdentity linkage, assignment/result binding, fencing, artifact references and immutable version semantics.
- Output: WP-3/WP-4 contract delta and negative-test matrix.

### Package D — Policy & distribution
- Reconcile Contract 07, CF-20/21/22, B16 and B20.
- Close policy decision contract, evidence-bound rights, approval vs authorization, emergency pause and distribution adapter checks.
- Output: WP-5 decision table and fail-closed test matrix.

### Package E — Operations, recovery & capacity
- Reconcile B21–B24 against accepted standards.
- Defer numeric targets until measured and approved; do not invent SLO/RPO/RTO/quota values.
- Output: operations contract, recovery test plan, workload measurement protocol and deferred owner decisions.

### Package F — Acceptance & traceability
- Use B14 G0–G8 as the acceptance framework.
- Build requirement → decision → contract → implementation → test → evidence → QA → owner acceptance links.
- Output: evidence register and gate-by-gate acceptance report.

## 5. Rules for parallel agents

1. Each agent receives exact source filenames/versions and a bounded work package.
2. Read-only reconciliation first. No repository inspection or changes unless separately authorized.
3. No agent may resolve an owner-only decision by choosing a plausible default.
4. Each proposed change must show source section, current wording, proposed wording, reason, impact and owner required.
5. Agents must preserve accepted ADR/CF decisions and standing constraints.
6. Conflicting source evidence must be reported, not normalized away.
7. No code, migration, credentials, infrastructure, paid provider, deployment, production generation, upload or public publishing under this docket.
8. No destructive Git operations, broad staging, reset/revert/stash/clean, commit or push without separate explicit authorization.
9. Implementation report is not independent verification.
10. “Done” requires exact deliverables, unresolved issues, tests/evidence status and explicit statement of what was not done.

## 6. Current authorization boundary

- Detailed contract freeze: **NOT GRANTED**.
- Implementation authorization: **NOT GRANTED**.
- Repository/Git operations: **NOT AUTHORIZED by this docket**.
- Production generation, external upload or public publishing: **NOT AUTHORIZED**.
- Paid services/provider activation, credential provisioning or deployment: **NOT AUTHORIZED**.
- Owner P0 acceptance/release: **NOT GRANTED**.

## 7. Completion report format for each package

Each package report must include:
1. Package ID, owner/agent, date, exact source versions.
2. Documents/sections reviewed.
3. Accepted decisions preserved.
4. Proposed contract changes with source citations.
5. Conflicts and owner decisions required.
6. Tests/evidence specified or executed (clearly distinguish these).
7. Deviations and risks.
8. Files created/modified; confirm no unapproved changes.
9. Explicit “not done / not authorized” list.
10. Recommendation: ACCEPT FOR OWNER REVIEW / REVISE / BLOCKED.

**End state:** a complete, source-backed owner review docket and frozen contract set—not an assumed implementation or release approval.
