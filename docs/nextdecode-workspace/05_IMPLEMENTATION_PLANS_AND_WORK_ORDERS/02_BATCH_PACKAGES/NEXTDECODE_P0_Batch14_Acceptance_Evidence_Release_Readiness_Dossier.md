NEXTDECODE

# P0 Acceptance, Evidence &
Release Readiness Dossier

BATCH 14  |  CONTROLLED DELIVERY DOCUMENT

Version 1.0  •  1 November 2026  •  Design / governance pack

## Document control

| Field | Value |
| --- | --- |
| Document ID | ND-P0-B14 |
| Title | P0 Acceptance, Evidence & Release Readiness Dossier |
| Series position | Batch 14; follows Batches 02–13 |
| Purpose | Define how P0 work is tested, evidenced, independently reviewed, accepted and released. |
| Authority | Operational acceptance framework; does not itself freeze contracts or authorize implementation/release. |
| Status | Prepared for review. Source reconciliation ongoing; contract freeze and implementation authorization remain separate gates. |
| Owner | Project owner — final acceptance and release decisions remain with the owner. |
| Review roles | Engineering execution, independent read-only QA, governance/policy review, project owner. |
| Supersession | Does not silently supersede Artifact 08, canonical data dictionary, API/event standard, lifecycle standard, traceability matrix or accepted owner decisions. |

## Executive summary

This dossier establishes a verifiable path from an accepted requirement to a tested implementation, independent QA finding, owner acceptance and controlled release. It is designed to prevent a common failure mode: treating a passing unit-test count, a successful demo, a green dashboard or an agent completion message as proof that the complete system is safe and ready.

P0 acceptance is evidence-led, scope-bound and fail-closed. Every acceptance claim must identify the exact requirement, contract version, code revision, environment, test procedure, result, evidence location, reviewer and disposition. A release candidate is a precisely identified set of immutable artifacts and configuration—not simply the current state of a branch or a developer machine.

This document is a readiness framework, not a declaration that P0 has passed. It does not authorize repository changes, migrations, worker activation, paid infrastructure, production generation, uploads, public publishing or release.

## 1. Purpose, scope and boundaries

### 1.1 Objectives

- Define acceptance criteria and evidence expectations across WP-0 through WP-6.

- Make source-to-release traceability auditable and reproducible.

- Separate implementation completion, test success, independent QA, owner acceptance, authorization and release execution.

- Define negative testing, failure injection, recovery proof and operational-readiness evidence.

- Provide reusable records and sign-off templates so that later execution is controlled rather than improvised.

### 1.2 In scope

- Acceptance model, evidence taxonomy, traceability and test governance.

- WP1 domain/persistence; WP2 durable workflow/job execution; WP3 worker registry/trust; WP4 artifact registry/storage/integrity/transfer; WP5 quality/rights/review/approval/authorization; WP6 vertical-slice integration/recovery.

- Release candidate manifest, operational readiness, rollback/stop conditions, audit package and post-release monitoring.

- Read-only independent QA protocol and defect/waiver governance.

### 1.3 Out of scope / prohibited by this dossier

- Declaring unresolved source wording, ODR entries or contract gaps approved by implication.

- Selecting or activating a paid provider, cloud deployment, production credential or billing-bearing service.

- Changing the repository, running migrations, starting workers, enabling external side effects or deploying software.

- Generating production content, transferring production assets, uploading or publishing to a public platform.

- Turning a QA warning, score, owner preference or ordinary waiver into permission to bypass a hard rights, security, integrity or authorization blocker.

### 1.4 Relationship to earlier batches

| Prior batch | How Batch 14 uses it |
| --- | --- |
| 02–04 | Traceability, owner review, source authority, provenance and freeze preparation. |
| 05–10 | WP1–WP6 candidate designs, integration expectations and acceptance scenarios. |
| 11 | Master integration blueprint and cross-package ownership/interface model. |
| 12 | Source verification and contract reconciliation process; unresolved items remain open until evidenced. |
| 13 | Controlled execution discipline, work-order boundaries, delegation, stop-work triggers and authorization separation. |

## 2. Acceptance vocabulary and decision boundaries

| Term | Meaning in this dossier | Not equivalent to |
| --- | --- | --- |
| Requirement | A uniquely identified, source-backed obligation or explicit approved constraint. | A suggestion or inferred preference. |
| Contract | A versioned, owner-approved interface, schema, invariant or state-transition rule. | A design sketch or illustrative example. |
| Implementation artifact | A code/config/schema artifact tied to a specific revision and provenance. | A screenshot or verbal completion claim. |
| Test | A defined procedure with preconditions, inputs, oracle and expected result. | A manual click-through without an oracle. |
| Evidence | A retained, attributable record supporting a claim about a defined scope and revision. | A status label or unsupported assertion. |
| QA disposition | Independent assessment of evidence quality, coverage and defects. | Owner acceptance. |
| Acceptance | Owner decision that a defined scope meets defined criteria, subject to stated exclusions. | Authorization to perform external actions. |
| Authorization | Policy decision permitting a specific actor to perform a specific action on a specific resource/version/destination. | Approval, acceptance or successful execution. |
| Release | Controlled promotion of an identified release candidate under an approved release record. | Merge, tag, deployment or publishing in isolation. |
| Outcome confirmation | Evidence that an external side effect actually occurred as intended. | Command accepted or request queued. |

The following distinctions are mandatory: approval ≠ authorization ≠ execution ≠ confirmed outcome; implementation complete ≠ independently verified; test pass ≠ release approval; release approval ≠ permission for a separately governed public-publishing action.

## 3. Acceptance principles

1. Trace every acceptance claim to a source requirement or explicitly approved design constraint.

1. Test the actual deployed/integrated behavior at the boundary where the risk exists; unit tests alone are insufficient for cross-domain guarantees.

1. Prefer independent, reproducible evidence over self-attestation by the implementer.

1. Test negative paths and prohibited actions as deliberately as happy paths.

1. Bind evidence to immutable identifiers: commit/revision, contract/schema version, test run, artifact version and environment.

1. Treat unknown, missing, stale, conflicting or unverifiable rights/approval/authorization/integrity as a blocker where the protected action depends on it.

1. Preserve failed attempts, logs and defect history; do not overwrite evidence to make a later run look clean.

1. Re-run affected tests after a code, contract, configuration, fixture or dependency change; explain the impact boundary.

1. Do not infer acceptance from a high aggregate score if a hard gate fails.

1. Keep release approval and execution authorization as separate recorded decisions.

## 4. End-to-end traceability model

Each requirement must be traceable through the following chain. Missing links are visible gaps, not blanks to be silently filled.

| Stage | Required reference / evidence | Control question |
| --- | --- | --- |
| Source | Source ID, exact text or locator, authority, version/date, provenance. | Why is this requirement authoritative? |
| Decision | CF / ODR / ADR / owner decision ID, exact wording, acceptance status. | Was it accepted, delegated, provisional or still pending? |
| Architecture | Module, domain owner, invariant and relevant WP. | Where does responsibility live? |
| Contract | API/event/schema/state-machine version and compatibility rule. | What precisely must producers/consumers obey? |
| Implementation | Repository, path, commit, migration/config version, owner. | What exact implementation realizes it? |
| Test | Test ID, type, environment, fixture, procedure and oracle. | How is conformance demonstrated? |
| Evidence | Run ID, timestamps, logs/reports/hashes, artifact refs. | Can another reviewer reproduce and verify it? |
| Independent QA | Reviewer, scope, sampling, finding IDs and disposition. | Was the evidence independently challenged? |
| Owner acceptance | Acceptance record, scope, exclusions, residual risks. | What exactly is accepted? |
| Release | Candidate manifest, authorization, deployment record and post-checks. | What exact candidate was promoted, and did it behave correctly? |

### 4.1 Traceability rules

- Use stable IDs for requirements, decisions, contracts, tests, evidence, defects, risks and release candidates.

- One requirement may map to multiple tests; one test may cover multiple requirements only when each mapping is explicit.

- Do not mark a requirement covered merely because a related module or endpoint exists.

- Record negative coverage: what is deliberately not tested, why, and what compensating control exists.

- Changes to a source or contract must trigger impact analysis for all linked implementation and evidence records.

- Keep decision status visible: ACCEPTED, ACCEPTED UNDER DELEGATION, PROVISIONAL, PENDING OWNER DECISION, REJECTED, SUPERSEDED or NOT VERIFIED, using the governing register's exact vocabulary.

## 5. Evidence model

### 5.1 Evidence classes

| Class | Examples | Minimum quality bar |
| --- | --- | --- |
| E0 — Source | Accepted decision, approved specification, source register. | Authority, exact wording/locator, version and status. |
| E1 — Static | Schema validation, migration review, dependency scan, config inspection. | Exact revision, command/tool version, complete output and reviewer. |
| E2 — Unit/component | Domain rules, validators, state transitions, idempotency functions. | Deterministic fixture, assertion/oracle, pass/fail and test ID. |
| E3 — Integration | Database, queue, worker, storage, policy and adapter interactions. | Controlled environment, correlation IDs, dependency versions, logs. |
| E4 — End-to-end | Full workflow from request through artifact, review and gated distribution simulation. | Traceable run, exact artifact versions, expected state sequence and side-effect proof. |
| E5 — Resilience/security | Crash/restart, duplicate delivery, lease expiry, fencing, credential revoke, denial tests. | Failure injection plan, observed recovery, no unauthorized side effect. |
| E6 — Operational | Backup/restore, alerting, runbooks, rollback rehearsal, capacity/cost checks. | Measured evidence, owner, environment and acceptance threshold. |
| E7 — Independent QA | Read-only reproduction, negative test, evidence sampling, defect report. | Reviewer independence, exact scope and reproducible finding. |

### 5.2 Evidence record minimum fields

| Field | Required content |
| --- | --- |
| evidence_id | Stable unique ID; never reused. |
| requirement_ids / test_ids | All claims supported by this evidence. |
| evidence_type | E0–E7 plus a precise subtype. |
| subject | Entity/resource and exact version under test. |
| source_revision | Commit SHA or immutable source snapshot; include dirty-tree status when relevant. |
| contract_versions | Relevant API, event, schema, lifecycle and policy versions. |
| environment | OS/runtime, DB/queue/storage versions, configuration profile, feature flags; redact secrets. |
| procedure | Exact command/procedure, operator and prerequisites. |
| result | PASS / FAIL / INCONCLUSIVE / NOT_RUN with observed vs expected. |
| timestamps | Started/finished in UTC; include collection time. |
| correlation | Trace, request, job, attempt, event and artifact IDs where applicable. |
| integrity | Hash/checksum for retained files and artifacts where practical. |
| review | Collector, independent reviewer, review date and disposition. |
| limitations | Known gaps, sampling limits, flaky dependencies and excluded scope. |

### 5.3 Evidence freshness and reproducibility

- Evidence is valid only for the revision, contract versions, configuration and environment it actually covers.

- Any material change to relevant code, schema, policy, dependency, fixture or deployment configuration invalidates affected evidence until impact analysis and retest are complete.

- Store raw output and machine-readable summaries where possible; screenshots may supplement but must not replace underlying logs/results.

- Redact secrets and unnecessary personal data before evidence retention; never put credentials in logs or test fixtures.

- Record failed and flaky runs. A rerun that passes does not erase the original failure; classify and explain it.

- Define reproducibility steps so an independent reviewer can rerun safely without production credentials or real external side effects.

## 6. Test strategy and minimum coverage

### 6.1 Test layers

| Layer | Purpose | Required coverage |
| --- | --- | --- |
| Static / contract | Catch structural and compatibility defects before runtime. | Schema validity, required fields, enums, unknown-field policy, versioning, producer/consumer compatibility. |
| Unit | Verify deterministic domain rules. | Identity/version rules, state guards, policy decisions, retry classification, rights/approval logic. |
| Component | Verify a module with controlled dependencies. | Persistence transactions, repository boundaries, validators, adapters and error mapping. |
| Integration | Verify cross-component guarantees. | DB/outbox/inbox/queue, worker leases, artifact storage, authorization, audit and event propagation. |
| End-to-end | Verify user-visible and system-level flows. | P0 vertical slice, exact artifact version, review, approval, authorization and distribution simulation. |
| Resilience | Verify recovery under controlled failure. | Duplicate delivery, crash/restart, timeout, stale lease, partial side effect, storage failure and DB unavailability. |
| Security / negative | Prove prohibited actions remain blocked. | Wrong workspace, revoked worker, expired token, unknown rights, wrong artifact version, unauthorized destination. |
| Operational | Prove supportability. | Backup/restore, alerts, logs, runbooks, rollback and incident response. |

### 6.2 WP acceptance matrix

| WP | Acceptance objective | Minimum evidence / test families | Hard blockers |
| --- | --- | --- | --- |
| WP-0 | Preservation and baseline are known; no destructive assumption. | Baseline inventory, preservation record, known dirty/untracked state, risk register. | Unreviewed destructive Git or filesystem action; missing preservation plan. |
| WP-1 | Canonical domain and persistence enforce ownership, identity, version and scope. | Schema/migration review; uniqueness/FK/scope tests; transaction/rollback; null-vs-unknown; concurrency/version tests. | Duplicate canonical identity; cross-workspace leakage; silent inference of critical unknowns; destructive migration. |
| WP-2 | Durable workflows/jobs survive retries, duplicates and process failure. | State-machine tests; outbox/inbox; at-least-once duplicate delivery; idempotency; lease/fencing; retry/recovery; reconciliation. | Lost accepted job; duplicate harmful side effect; stale worker commits; unreconciled ambiguous external operation. |
| WP-3 | Workers have unique identity, bounded capabilities and revocable trust. | Registration/heartbeat; declared-vs-verified capability; scoped credential; expiry/revoke; wrong-scope and privilege escalation tests. | Shared identity; unbounded privilege; revoked/expired worker continues protected action. |
| WP-4 | Artifacts have immutable versions, integrity and controlled transfer. | Metadata/binary consistency; checksum; manifest; lineage; transfer state; quarantine; repair-new-version; retention/delete/hold. | Silent overwrite; checksum mismatch accepted; approval points to mutable/latest alias; unauthorized export. |
| WP-5 | Quality, claims, rights, review, approval and authorization fail closed. | QA outcome tests; hard blocker tests; evidence-backed use-specific rights; exact-version review/approval; central auth; emergency pause; audit. | Unknown/denied rights permitted; warning-only bypass of hard blocker; generic approved=true grants authority; publisher bypass. |
| WP-6 | Integrated vertical slice and recovery are independently demonstrated. | E2E traces; correlation IDs; failure injection; restart/replay; compatibility; independent QA; release candidate evidence. | Missing cross-WP trace; no reproducible recovery; unresolved P0 blocker; external side effect not reconciled. |

### 6.3 WP-specific detailed acceptance criteria

#### WP-1 — Domain and persistence

- Canonical IDs are immutable and generated/validated according to the accepted UUIDv7 rule; identity and version identity are not conflated.

- Exactly one authoritative domain owner commits each entity's lifecycle transition.

- Uniqueness, referential integrity, tenant/workspace scope and expected-version concurrency are enforced at persistence boundaries.

- Null, empty, unknown, not-applicable and missing business-critical values retain their defined distinctions.

- Migrations are reviewed, reversible where feasible, and tested against representative prior data; backup/restore evidence exists before any destructive or data-shaping operation.

- Audit/provenance captures actor, reason, time, prior/new state and correlation without leaking secrets or unnecessary PII.

#### WP-2 — Workflow and job execution

- Workflow definition, workflow run, task definition/instance, job, attempt, queue message and domain event remain distinct concepts.

- At-least-once delivery is assumed; durable idempotency prevents duplicate logical effects.

- Every attempt has a durable identity and attributable start/end/outcome; retry creates a new attempt.

- Leases use fencing so an expired/stale worker cannot commit after a newer lease holder.

- Accepted asynchronous commands have a durable reference; queue outage or worker absence does not silently lose work.

- Ambiguous external side effects are reconciled before retry; policy denials are not retried around.

#### WP-3 — Worker registry, identity and trust

- Each worker has unique identity, status/trust lifecycle and auditable registration/revocation.

- Declared capability, verified capability, currently available capability and policy-authorized capability are separately represented.

- Credentials are short-lived, scoped, revocable and not embedded in source, logs or durable queue payloads.

- Workers receive bounded assignments and least-privilege access to files, network, credentials and artifacts.

- Resource limits and execution isolation are defined by job class; capability changes are versioned and re-verified.

#### WP-4 — Artifact registry and integrity

- Artifact identity and immutable version identity are separate; a repair or transformation creates a new version.

- Manifest entries reference exact artifact versions and include provenance/lineage and integrity metadata.

- Asset and Artifact concepts remain distinct where the canonical model requires it.

- Binary storage is abstracted from relational metadata; transfer has explicit source, destination, authorization, integrity and outcome records.

- Validation is type-aware and does not imply factual accuracy, rights clearance, approval or authorization.

- Quarantine, retention, legal hold, logical deletion and physical deletion are distinct and auditable.

#### WP-5 — Governance and protected actions

- QA outcomes use the accepted vocabulary: PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW, BLOCKED; hard blockers remain non-bypassable by ordinary approval.

- Rights are use-specific and evidence-backed; UNKNOWN/PENDING_REVIEW/RESTRICTED/EXPIRED/REVOKED/DENIED do not authorize use.

- Review packages and decisions are immutable and bind to exact artifact/version and scope.

- Approval records who decided, when, for what version/scope and with what outcome; expiry/revocation are enforced.

- Central authorization evaluates actor, capability, action, resource/version, workspace, destination, policy version and expiry/revocation; default deny.

- Emergency pause and policy-denial behavior are tested at every relevant adapter boundary; adapters cannot bypass central policy.

- Human approval before publishing remains mandatory; automatic public publishing remains disabled unless separately approved under a distinct policy.

#### WP-6 — Integrated vertical slice

- Trace one controlled content request through canonical content identity, workflow, tasks/jobs/attempts, worker assignment, artifacts, QA, rights, review, approval, authorization and simulated distribution.

- Prove each transition is committed by its authoritative owner and linked by correlation/causation identifiers.

- Exercise duplicate delivery, process crash/restart, worker loss, stale lease, storage failure, policy denial and ambiguous external outcome.

- Use test destinations or no-op adapters; do not invoke production upload/publishing during P0 validation.

- Capture an end-to-end evidence bundle and independent QA report for the exact release candidate.

## 7. Required negative and failure-injection catalogue

| ID | Scenario | Expected result / acceptance oracle |
| --- | --- | --- |
| NEG-01 | Unknown rights state; attempt restricted use. | Denied; no artifact transfer or publish side effect; auditable reason. |
| NEG-02 | Approval refers to prior artifact version; request uses newer version. | Denied or re-review required; no implicit approval carry-forward. |
| NEG-03 | Authorization absent, expired, revoked or wrong destination. | Default deny; no adapter bypass. |
| NEG-04 | Hard QA blocker with high score or owner request to proceed. | Blocked; ordinary waiver cannot override hard blocker. |
| NEG-05 | Duplicate queue delivery / repeated command. | One logical effect; duplicate safely acknowledged/deduplicated. |
| NEG-06 | Worker lease expires; stale worker attempts commit. | Fencing rejects stale commit. |
| NEG-07 | Worker credential revoked while task queued/running. | Protected action denied; task safely stops or transitions to governed failure. |
| NEG-08 | Wrong workspace/brand/channel scope. | Access denied; no cross-scope data leakage. |
| NEG-09 | Checksum mismatch or malformed artifact. | Quarantine; not eligible for approval/distribution. |
| NEG-10 | Artifact repair after approval. | New version created; previous approval does not automatically cover it. |
| NEG-11 | External request times out after remote side effect may have occurred. | Outcome UNKNOWN/RECONCILIATION_REQUIRED; query/reconcile before retry. |
| NEG-12 | DB unavailable during command/outbox commit. | No false ACCEPTED response without durable record. |
| NEG-13 | Worker unavailable for local-only job. | Job waits safely or enters explicit governed state; no silent cloud substitution. |
| NEG-14 | Emergency pause enabled during publish attempt. | Protected action denied; auditable policy result. |
| NEG-15 | Migration fails midway. | Documented rollback/recovery; data integrity preserved; no untracked partial state. |
| NEG-16 | Attempted automatic public publishing. | Disabled path rejects; no public side effect. |

The test owner must add implementation-specific scenarios for every discovered adapter, storage provider, queue backend, authentication path and state machine. This catalogue is a minimum, not an exhaustive security certification.

## 8. Migration, backup, restore and data safety acceptance

- Before a migration: identify source/target schema versions, affected tables/records, data volume, compatibility window, lock/availability impact and rollback strategy.

- Use representative anonymized fixtures and production-like volume where practical; never copy secrets or unnecessary personal data into test environments.

- Demonstrate migration idempotency or explicitly document why it is one-shot and how rerun is prevented.

- Verify row counts, key relationships, uniqueness, scope constraints, checksums or domain invariants before and after migration.

- Prove backup completion and restore into an isolated environment; a backup job reporting success is not restore evidence.

- Define recovery point and recovery time objectives only after owner approval; do not invent numeric targets.

- Record schema version, migration ID, execution actor, start/end, outcome, verification results and recovery action.

- Do not execute destructive migrations against the user's working repository or any live database under this dossier.

## 9. Independent QA protocol

### 9.1 Independence and access

- QA operates read-only against the approved candidate and evidence package; no unapproved edits, migrations, deployment or production credentials.

- Implementers do not self-close their own critical findings. A separate reviewer verifies remediation and retests.

- QA records exact revision, test environment, test scope, sampling method, tools and limitations.

- QA may request a safe reproduction or additional evidence; missing evidence is recorded as INCONCLUSIVE or NOT_VERIFIED, not assumed passed.

### 9.2 Review procedure

1. Confirm candidate identity and scope; reject an unpinned or dirty/ambiguous candidate.

1. Verify source and contract status for each sampled requirement.

1. Inspect traceability links and evidence metadata before trusting test summaries.

1. Reproduce representative positive, negative and failure-recovery scenarios in a safe environment.

1. Challenge high-risk boundaries: rights, exact-version approval, central authorization, worker trust, artifact integrity, idempotency and external side-effect reconciliation.

1. Record each finding with severity, affected requirement, reproduction steps, expected/actual behavior, evidence and remediation owner.

1. Retest remediations against the same candidate lineage; preserve original finding and retest record.

1. Publish a QA disposition with explicit scope, exclusions, residual risks and recommendation.

### 9.3 Finding severity

| Severity | Definition | Default release effect |
| --- | --- | --- |
| Critical | Unauthorized public/external side effect; rights/privacy/security breach; data corruption/loss; bypass of a hard gate. | Release blocked. No ordinary waiver. |
| High | Core invariant or critical workflow/recovery guarantee fails; exploitable privilege/scope defect; material evidence gap. | Release blocked until fixed and independently retested. |
| Medium | Significant function/operability defect with bounded impact and viable workaround. | Normally blocks affected scope; any exception needs owner risk acceptance and documented mitigation. |
| Low | Minor issue with limited impact and no effect on protected invariants. | May be accepted with owner, rationale and follow-up date. |
| Observation | Improvement or non-defect note. | Track; does not imply acceptance. |

### 9.4 QA outcomes

| Outcome | Use |
| --- | --- |
| PASS | All in-scope mandatory criteria demonstrated; no blocking findings. |
| PASS_WITH_WARNINGS | Mandatory criteria pass; only bounded, explicitly accepted non-blocking issues remain. |
| NEEDS_REVIEW | Evidence incomplete, ambiguous, stale or contradictory; decision cannot yet be made. |
| BLOCKED | A mandatory criterion fails or a hard blocker is present. |

QA outcome is not an owner release decision. A PASS does not itself authorize release or external actions.

## 10. Defect, risk, waiver and change control

### 10.1 Defect record

| Field | Required detail |
| --- | --- |
| defect_id | Stable ID and title. |
| severity / status | Critical/High/Medium/Low/Observation; Open, Triaged, Fixing, Ready for Retest, Verified, Reopened, Deferred. |
| traceability | Requirement, contract, WP, code revision, test and evidence IDs. |
| reproduction | Environment, preconditions, exact steps/input and expected vs actual. |
| impact | Data, security, rights, authorization, reliability, user and external side-effect impact. |
| owner / target | Remediation owner, target milestone and dependency. |
| resolution | Fix revision, tests rerun, independent retest and closure authority. |

### 10.2 Waiver policy

- Waivers must be exceptional, scope-limited, time-limited, owned and recorded with rationale, impact, mitigation, expiry and compensating monitoring.

- Critical findings, unknown/uncleared rights, missing authorization, cross-workspace access, checksum/integrity failures, stale-worker fencing failures and automatic public-publishing prohibition are not waivable through ordinary acceptance.

- A waiver cannot alter a source decision or contract; that requires the proper owner decision/change process.

- Expired waivers automatically return the affected requirement to blocked/pending status until renewed through authorized governance.

- Never use a waiver to hide a missing test, absent source, failed control or unverified external side effect.

### 10.3 Change impact

Any change to source decision, contract, schema, policy, code, dependency, configuration, fixture or release manifest must identify affected requirements, tests, evidence, approvals and candidate hashes. Evidence is selectively invalidated only with a documented impact analysis; otherwise rerun the relevant acceptance suite.

## 11. Vertical-slice evidence package

The P0 vertical slice must produce one indexed, immutable evidence package. It must be safe to reproduce without public side effects.

| Bundle item | Required contents |
| --- | --- |
| Index | Bundle ID, candidate ID, owner, collection time, scope, evidence map and checksums. |
| Trace | Content/workflow/task/job/attempt/worker/artifact/review/approval/authorization/distribution correlation IDs. |
| State history | Authoritative state transitions with actor, reason, prior/new state, state version and timestamps. |
| Execution | Queue messages, idempotency keys, lease/fencing evidence, attempts, retries and terminal outcomes. |
| Worker | Identity, trust/capability verification, assignment scope and revocation/expiry behavior. |
| Artifacts | Manifest, immutable version refs, checksums, validation/quarantine status, lineage and transfer records. |
| Governance | QA result, claims/evidence refs, use-specific rights, review package, exact-version approval and authorization decision. |
| Failure recovery | Injected failure, observed state, recovery/reconciliation action and proof of no duplicate/unauthorized side effect. |
| Distribution simulation | No-op/test destination request, policy decision and confirmed simulated outcome; no production publish. |
| QA report | Independent findings, severity, retest evidence, disposition, exclusions and residual risks. |
| Integrity | Hashes for all bundle files and a signed/attributable manifest where signing capability is approved. |

## 12. Release candidate definition and manifest

A release candidate is immutable and uniquely identified. It must not be described only as 'latest main', 'the working tree' or 'the version that passed'.

| Manifest field | Required content |
| --- | --- |
| candidate_id | Unique stable ID. |
| source_revision | Exact commit SHA; dirty-tree state and patch inventory if applicable. Release candidates should normally be clean and pinned. |
| build_identity | Build pipeline/run ID, toolchain versions and reproducible build metadata. |
| contract_set | Exact API/event/schema/lifecycle/policy contract versions. |
| migration_set | Ordered migration IDs, checksums and compatibility notes. |
| configuration | Non-secret configuration profile, feature flags and environment-specific differences. |
| dependency_inventory | Direct/transitive dependency lockfiles and relevant image/binary digests. |
| artifact_inventory | Immutable artifact refs and checksums. |
| test_evidence | Required suite IDs, results, evidence bundle IDs and freshness assessment. |
| QA_disposition | Independent QA report ID, outcome and unresolved findings. |
| known_limits | Explicit exclusions, known defects, unsupported modes and operational constraints. |
| approval | Owner acceptance record and separate release authorization reference. |

### 12.1 Candidate integrity checks

- Verify manifest completeness and checksums before promotion.

- Ensure tested revision equals candidate revision; no untested changes after evidence capture.

- Verify secrets are externalized and absent from source, build logs and manifest.

- Confirm only intended features/configuration are enabled; public publishing remains disabled.

- Confirm rollback target and required data compatibility are known before release.

## 13. Operational readiness

| Area | Required proof before release |
| --- | --- |
| Monitoring | Health/readiness signals, queue depth/age, job latency/failure, worker heartbeat/trust, artifact validation, authorization denials and external operation reconciliation. |
| Alerting | Actionable alerts with owner, severity, routing, suppression and escalation; test that alerts fire. |
| Logging/tracing | Structured, correlated, privacy-safe logs; trace/request/job/attempt/artifact IDs; retention and access controls. |
| Runbooks | Startup/shutdown, stuck job, duplicate delivery, worker revoke, queue outage, DB outage, storage failure, rights incident, policy pause and external side-effect reconciliation. |
| Backup/restore | Successful isolated restore with integrity checks; documented recovery procedure and approved RPO/RTO. |
| Rollback | Known-good candidate, compatibility constraints, rollback rehearsal and explicit limits for irreversible data/external effects. |
| Security | Credential rotation/revocation, least privilege, secret handling, access review and incident escalation. |
| Capacity | Measured workload profile and bottleneck limits; no invented capacity claims. |
| Cost | Provider and spend controls; local-first/free-first; no paid service activated without explicit approval. |
| Support | Named operational owner, escalation route, incident record and maintenance window. |
| Retention/deletion | Approved retention schedule, legal hold, logical/physical deletion separation and audit preservation. |

Where a provider, environment, operational target or owner has not been selected, record NOT DECIDED / NOT VERIFIED. Do not substitute generic values or treat the absence of a decision as permission.

## 14. Release gates G0–G8

| Gate | Purpose | Required evidence | Decision authority / fail condition |
| --- | --- | --- | --- |
| G0 — Source authority | Requirements and decisions are authoritative and reconciled. | Source inventory, exact decision wording, provenance, ODR/ADR status, unresolved conflict list. | Owner/governance. Fail if a critical source or decision is provisional/unverified. |
| G1 — Contract freeze | Cross-WP contracts are internally consistent and approved. | Versioned domain/API/event/schema/lifecycle contracts, traceability and compatibility review. | Owner. Fail if ownership, states, interfaces or policy semantics remain ambiguous. |
| G2 — Implementation integrity | Candidate is identifiable, preserved and reproducible. | Pinned revision, change inventory, build record, migration/config inventory, no unexplained changes. | Engineering + owner. Fail if candidate cannot be reproduced or provenance is unclear. |
| G3 — Functional acceptance | Mandatory WP1–WP6 behavior works. | Unit/component/integration/E2E evidence and requirement coverage. | Engineering. Fail on mandatory acceptance failure. |
| G4 — Resilience and security | Failure, trust and protected-action boundaries hold. | Negative tests, failure injection, restore/recovery, least privilege, revocation and policy enforcement. | Independent QA/security review. Fail on Critical/High findings or unverified hard gates. |
| G5 — Governance acceptance | Quality, rights, review, approval and authorization work end-to-end. | Exact-version records, rights evidence, centralized authorization, pause and audit tests. | Governance + owner. Fail if unknown/denied rights or missing auth can pass. |
| G6 — Independent QA | Evidence and implementation are independently challenged. | QA report, reproduced tests, findings, retests and disposition. | Independent QA. Fail if evidence incomplete or blocking findings open. |
| G7 — Owner release decision | Owner accepts defined candidate and residual risk. | Candidate manifest, QA disposition, residual risk, exclusions and signed acceptance. | Owner only. Fail without explicit recorded acceptance. |
| G8 — Controlled release & post-check | Approved candidate is promoted safely and observed. | Release authorization, execution log, health checks, rollback readiness and monitoring review. | Authorized release operator + owner. Fail on drift, unauthorized action or failed post-check. |

Gates are sequential for authorization purposes. Preparation work may run in parallel, but a later gate cannot be treated as passed by completing a document or workstream early. Gate evidence must be reviewed against the exact candidate.

## 15. Release decision and sign-off record

| Field | Record |
| --- | --- |
| Release decision ID | [RELEASE-DECISION-ID] |
| Candidate ID / manifest hash | [ID] / [SHA-256] |
| Scope accepted | [Modules, workflows, environments, users and supported actions] |
| Scope excluded | [Explicit exclusions and unsupported modes] |
| Gate results | G0–G8: [PASS / FAIL / NOT_RUN / NOT_APPLICABLE with evidence refs] |
| QA outcome / report | [Outcome] / [QA report ID] |
| Open defects / waivers | [IDs, severity, rationale, expiry and owner] |
| Residual risks | [Risk IDs, impact, mitigation, monitoring and acceptance owner] |
| Data migration / restore | [Migration set and restore evidence refs] |
| External side effects | [Explicitly allowed actions; otherwise disabled/no-op] |
| Publishing policy | Human approval required; automatic public publishing disabled unless separately approved. |
| Owner decision | [ACCEPT / REJECT / DEFER] with rationale and timestamp |
| Release authorization | [Separate authorization ID, actor, action, target and expiry] |
| Execution record | [Operator, time, environment, result and evidence refs] |
| Post-release review | [Health window, findings, rollback decision and closure] |

A blank sign-off field is not approval. Silence, a chat acknowledgement, a green test badge or an agent report cannot substitute for the required recorded decision.

## 16. Post-release monitoring, rollback and stop-work

### 16.1 Stop-work triggers

- Any unauthorized or potentially unauthorized external side effect.

- Evidence of rights, privacy, security, credential or cross-workspace breach.

- Artifact checksum mismatch, silent overwrite or broken lineage.

- Stale worker committing after lease expiry or revoked identity performing protected work.

- Queue/job state divergence, lost accepted work or duplicate harmful side effect.

- Unknown external outcome that is being retried without reconciliation.

- Emergency pause or central authorization enforcement fails.

- Release candidate differs from the tested/approved manifest.

- Unexpected spend, paid-provider activation or billing exposure without explicit approval.

- Data loss, failed restore, migration corruption or rollback uncertainty.

### 16.2 Rollback principles

- Rollback is a controlled operation with its own authorization, evidence and compatibility assessment.

- Do not assume database rollback reverses external side effects or public publishing.

- Preserve audit logs, incident evidence and affected artifact versions.

- Disable or pause affected workers/adapters before attempting recovery where necessary and authorized.

- Prefer forward repair with a new immutable artifact/version when rollback would destroy lineage.

- Record trigger, decision-maker, target candidate, data compatibility, external reconciliation and post-rollback verification.

### 16.3 Post-release review

Review health, queue age, failed/retried jobs, worker trust, artifact validation, rights/authorization denials, external-operation reconciliation, security events, support burden and cost against owner-approved thresholds. Thresholds must be explicitly set before release; this dossier does not invent them.

## 17. Audit package and records retention

- Maintain an index of all accepted requirements, decision records, contracts, implementation revisions, test runs, evidence bundles, QA findings, waivers, release manifests and sign-offs.

- Keep immutable original evidence and append corrections/retests rather than silently editing history.

- Apply access control and approved retention rules; preserve legal holds and required audit records.

- Do not retain secrets, unnecessary personal data, raw credentials or uncontrolled copies of sensitive artifacts.

- Ensure an auditor can answer: what was approved, by whom, for which exact version/scope, based on what evidence, under which policy, and what actually happened.

## 18. Current readiness position and unresolved controls

| Control area | Current position from project record | What changes the status |
| --- | --- | --- |
| Accepted architecture decisions | Artifact 08 and supporting standards have been located; CF-01–CF-24 acceptance status is recorded in the source material. | Reconcile all higher-authority records and exact wording; preserve accepted/provisional distinctions. |
| Canonical data dictionary | Located in Library; authoritative ownership and naming conventions are available for reconciliation. | Map every WP schema/entity and close discrepancies. |
| API/event standard | Located in Library; command/query/event separation and envelope principles available. | Complete cross-WP endpoint/event mappings and validate compatibility. |
| Lifecycle standard | Located in Library; domain-owned state machines and transition audit requirements available. | Resolve all X-01 and related state ownership/cardinality gaps. |
| Module traceability matrix | Located in Library; module-to-contract mapping exists. | Reconcile against final contract set and work packages. |
| ODR master register | A complete independent original ODR register has not yet been confirmed; ODR-22 has a provisional grouping record. | Locate authoritative register and reconcile every ODR entry to exact source wording. |
| Cross-document findings | Consistency review records X-01–X-12, including several high-priority gaps. | Close each finding with source, contract, owner and evidence references. |
| Contract freeze | Not granted by this dossier. | Owner-approved, versioned contract freeze record. |
| Implementation authorization | Not granted by this dossier. | Separate explicit owner authorization after prerequisites. |
| Independent QA | Not yet demonstrated for this candidate. | Read-only independent QA report on exact candidate. |
| P0 acceptance / release | Not accepted or released. | All applicable gates pass; owner signs exact candidate; separate release authorization. |

The current position is intentionally conservative. Locating a source document improves the evidence base but does not by itself close every reconciliation finding or authorize implementation.

## 19. Open issue register — minimum closure set

| Issue ID | Issue / risk | Closure evidence required | Status |
| --- | --- | --- | --- |
| SRC-01 | Original ODR master register not fully confirmed. | Authoritative register file, version, owner provenance and row-by-row source mapping. | OPEN |
| SRC-02 | ODR-22 is documented as provisional grouping, not a verified distinct accepted decision. | Exact original owner decision row or explicit owner disposition replacing the provisional grouping. | OPEN |
| X-01 | Workflow/task/job ownership, cardinality and state boundaries need reconciliation. | Approved lifecycle/state model, entity cardinality and transition ownership tests. | OPEN |
| X-02 | ArtifactVersion/manifest contract detail may be incomplete in prior WP documents. | Canonical entity and manifest schemas plus immutable version/lineage tests. | OPEN |
| X-03 | Transfer/validation/quarantine records need complete definitions. | Transfer state machine, validation evidence model and quarantine/release controls. | OPEN |
| X-04 | Governance concept labels/counts inconsistent across documents. | Canonical glossary and reconciled WP5 model; exact enum values. | OPEN |
| X-05 | Authorization/emergency-pause contract requires complete operational semantics. | Versioned policy contract, decision inputs/outputs and adapter enforcement tests. | OPEN |
| X-06 | Worker trust/credential/revocation semantics need precise cross-contract alignment. | Worker lifecycle, capability versioning, credential expiry/revoke and negative tests. | OPEN |
| X-07 | Job/task/workflow mapping needs explicit cardinality and boundaries. | Approved mapping, examples and persistence/integration tests. | OPEN |
| X-08 | Command/event envelope compatibility and validation need completion. | Contract schemas, compatibility rules, producer/consumer tests. | OPEN |
| X-09 | Artifact deletion/legal hold/access semantics need complete alignment. | Retention/deletion policy, access matrix, legal-hold and audit tests. | OPEN |
| X-10 | WP6 acceptance evidence/test oracle/environment controls need strengthening. | E2E evidence schema, controlled environment and reproducible test oracle. | OPEN |
| X-11 | ODR-22 is not faithful transcription of a confirmed source row. | Resolve under SRC-02; do not treat provisional grouping as approval. | OPEN |
| X-12 | Status and document authority language varies. | Controlled vocabulary and document authority header applied consistently. | OPEN |

This register carries forward known documentation findings. It is not an assertion that no additional gaps exist; new findings must be added with provenance and impact.

## 20. Reusable templates

### 20.1 Requirement trace record

| Field | Template |
| --- | --- |
| requirement_id / exact text | [REQ-ID] / [Verbatim source-backed requirement] |
| source authority | [Document, version, exact locator, owner/provenance] |
| decision status | [Accepted / delegated / provisional / pending / rejected / superseded / not verified] |
| decision refs | [CF / ODR / ADR / owner decision IDs] |
| architecture mapping | [Module, domain owner, WP, invariant] |
| contract mapping | [API/event/schema/lifecycle/policy version] |
| implementation mapping | [Repository/path/commit/artifact] |
| test mapping | [Test IDs and coverage type] |
| evidence mapping | [Evidence IDs and hashes] |
| QA / acceptance | [Finding IDs, disposition, owner acceptance ref] |

### 20.2 Test run record

| Field | Template |
| --- | --- |
| test_run_id | [Stable ID] |
| test_id / requirement IDs | [IDs] |
| candidate / source revision | [Exact candidate and commit] |
| environment | [OS/runtime/dependencies/config profile] |
| preconditions / fixture | [Known deterministic setup] |
| procedure / oracle | [Exact steps and expected result] |
| observed result | [Actual result and machine-readable output] |
| status | [PASS / FAIL / INCONCLUSIVE / NOT_RUN] |
| evidence refs | [Logs, reports, hashes, correlation IDs] |
| collector / reviewer | [Names/roles and timestamps] |
| limitations | [Flakes, exclusions, known environmental constraints] |

### 20.3 QA finding record

| Field | Template |
| --- | --- |
| finding_id / severity | [ID] / [Critical, High, Medium, Low, Observation] |
| scope | [Candidate, module, requirement, contract, test] |
| reproduction | [Environment, exact steps, inputs] |
| expected / actual | [Oracle] / [Observed behavior] |
| impact | [Safety, rights, privacy, security, data, reliability, external effects] |
| evidence | [Evidence IDs, logs, hashes] |
| remediation / owner | [Action and accountable role] |
| retest | [New run ID, independent reviewer, result] |
| disposition | [Open / Verified / Deferred / Reopened; rationale] |

### 20.4 Risk record

| Field | Template |
| --- | --- |
| risk_id / statement | [ID] / [Cause → uncertain event → impact] |
| category / scope | [Technical, security, governance, operational, cost, source] |
| likelihood / impact | [Qualitative scale approved by owner; do not invent numeric score] |
| controls / mitigation | [Preventive, detective, corrective] |
| owner / trigger | [Accountable role and observable trigger] |
| residual risk | [Remaining exposure and accepted scope] |
| review date / decision | [Date and owner disposition] |

### 20.5 Waiver record

| Field | Template |
| --- | --- |
| waiver_id / linked finding | [ID] / [Finding ID] |
| scope / expiry | [Exact requirement/candidate/scope] / [Expiry] |
| rationale | [Why acceptance with limitation is proposed] |
| impact / mitigation | [Impact and compensating controls] |
| monitoring / rollback trigger | [Signals and action] |
| approver | [Authorized owner role] |
| prohibited use check | Confirm it does not waive a hard blocker or alter an accepted source decision. |

### 20.6 Release candidate and sign-off record

| Field | Template |
| --- | --- |
| candidate_id / manifest hash | [ID] / [Hash] |
| source revision / build | [Commit SHA] / [Build ID] |
| contract / migration versions | [Exact versions and migration IDs] |
| test and QA evidence | [Test run IDs, bundle IDs, QA report] |
| gate outcomes | [G0–G8 with evidence refs] |
| known limits / residual risks | [Explicit list and owners] |
| owner acceptance | [ACCEPT / REJECT / DEFER; scope; date] |
| release authorization | [Separate authorization; actor/action/target/expiry] |
| execution and post-check | [Operator, result, health evidence, rollback status] |

## 21. Completion checklist

- ☐ All in-scope requirements have authoritative source and decision status.

- ☐ ODR/ADR/CF records are reconciled; provisional and unverified entries remain visible.

- ☐ All X-01–X-12 findings are closed or explicitly dispositioned by the proper authority.

- ☐ Cross-WP contracts, schemas, state machines and compatibility rules are versioned and owner-approved.

- ☐ WP1–WP6 mandatory acceptance criteria have reproducible evidence.

- ☐ Negative tests prove fail-closed rights, approval, authorization, worker trust and artifact integrity.

- ☐ Migration, backup and isolated restore have been verified.

- ☐ Vertical-slice E2E evidence bundle is complete and hash-indexed.

- ☐ Independent QA has reviewed the exact candidate and all Critical/High findings are closed.

- ☐ Operational readiness, monitoring, runbooks, rollback and support ownership are approved.

- ☐ Release candidate manifest matches the tested and reviewed revision exactly.

- ☐ Owner acceptance is recorded for exact scope and residual risks.

- ☐ Separate release authorization exists for the specific promotion action.

- ☐ Public publishing remains disabled unless a separate policy and explicit authorization say otherwise.

## 22. Final control statement

Batch 14 defines the acceptance and release evidence framework for NEXTDECODE Content OS P0. It is a controlled design document. It does not assert that P0 has passed, that the contract set is frozen, that source reconciliation is complete, or that implementation/release is authorized.

The next work should continue in parallel where safe: (1) authoritative source/ODR reconciliation, (2) X-01–X-12 contract closure proposals, (3) bounded engineering work orders and implementation tickets, and (4) detailed QA fixtures and test-oracle preparation. These preparation activities must not mutate the repository, activate workers, run migrations, incur spend or create external production side effects.

The next numbered documentation batch should consolidate the remaining P0 governance and operational-control material only after the source reconciliation findings are updated, so that later documents do not repeat obsolete 'source not found' assumptions.


## Source document metadata (preserved from DOCX)

- **Header:** NEXTDECODE CONTENT OS  |  P0 CONTROLLED DELIVERY SERIES
- **Footer:** Batch 14 — Acceptance, Evidence & Release Readiness  •  Controlled design document

