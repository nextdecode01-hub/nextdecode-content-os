# NEXTDECODE P0 — Acceptance, Evidence & Release Gates

**Version:** 0.1  
**Status:** Candidate acceptance framework; not executed

## 1. Acceptance philosophy

P0 acceptance is evidence-based. A feature is not accepted because a developer says it is complete, a document describes it, or a historical test run was green. Every claim must be tied to an exact scope and baseline.

## 2. Evidence record

For every verification run, capture:
- Evidence ID and test/oracle ID.
- Requirement/contract reference.
- Repository and exact commit/build identifier.
- Environment, OS/runtime/dependency versions and relevant configuration.
- Worker identity and trust state where applicable.
- Fixture/data-set identifier and synthetic-data confirmation.
- Command or test procedure.
- Start/end time and run correlation ID.
- Expected result and observed result.
- Result: `PASS`, `PASS_WITH_WARNINGS`, `NEEDS_REVIEW`, `BLOCKED`, `NOT_RUN`, `NOT_APPLICABLE` or `INCONCLUSIVE` as appropriate to the evidence register.
- Logs, reports, artifact references and checksums.
- Reviewer and review date.
- Known limitations and recheck triggers.

Never fabricate a missing build, commit, hash, environment or run identifier.

## 3. Gate model

| Gate | Entry condition | Exit condition |
|---|---|---|
| Contract gate | Reconciliation package complete | Owner approves exact versioned baseline or returns changes |
| WP gate | Prior dependencies accepted; work order authorized | Package-specific tests and evidence satisfy criteria |
| Integration gate | WP-1–WP-5 implementations accepted | P0-A vertical slice passes required oracles |
| Recovery gate | Deterministic baseline available | Injected failures recover with durable audit history |
| Security gate | Threat boundaries and policy rules defined | Negative tests prove denied paths remain denied |
| Independent QA gate | Evidence bundle complete | Kilo report records pass/warnings/blockers with traceability |
| Owner acceptance gate | QA findings triaged | Owner accepts exact scope or requests remediation |

## 4. P0-A vertical-slice scenario

1. Create synthetic ContentItem and ContentVariant.
2. Create Workflow and dependent WorkflowTask.
3. Create durable Job through approved command contract.
4. Dispatch and claim with authenticated worker.
5. Execute deterministic synthetic operation.
6. Register immutable ArtifactVersion and manifest.
7. Record task/job/attempt/workflow transitions.
8. Reconstruct the execution history from durable records.
9. Inject worker crash, lease expiry, duplicate delivery, checksum mismatch and authorization denial.
10. Demonstrate recovery and prove no unauthorized external side effect occurred.

## 5. Failure and security oracle categories

- Persistence: rollback, uniqueness, referential integrity, concurrent update.
- Queue: duplicate delivery, outbox retry, inbox deduplication, process restart.
- Lease: expiry, heartbeat loss, stale worker completion, re-claim.
- Idempotency: same key/same payload, same key/different payload.
- Worker: unknown identity, revoked credential, undeclared capability, scope escape.
- Artifact: checksum mismatch, incomplete transfer, invalid manifest, quarantine.
- Governance: unknown rights, missing approval, wrong version, wrong destination, expired authorization, hard QA blocker.
- Adapter: direct publisher bypass, direct pipeline bypass, unauthorized execution request.
- Audit: missing correlation, missing actor, incomplete state history, ambiguous external outcome.

## 6. QA result interpretation

- `PASS`: required oracle passed for exact scope.
- `PASS_WITH_WARNINGS`: required behavior passed but documented non-blocking warnings remain.
- `NEEDS_REVIEW`: evidence or interpretation requires human review.
- `BLOCKED`: hard blocker prevents acceptance.
- `NOT_RUN`: test not executed.
- `NOT_APPLICABLE`: outside scope with rationale.
- `INCONCLUSIVE`: run occurred but evidence cannot establish outcome.

Hard blockers cannot be waived by ordinary approval. Any exception mechanism requires explicit owner policy.

## 7. Independent QA protocol

Kilo receives:
- Exact approved contract baseline.
- Exact implementation commit/build.
- Test plan and expected oracles.
- Environment and fixture manifest.
- Logs and evidence pointers.
- Known limitations and previous findings.

Kilo operates read-only. It must not alter code, tests, data or configuration. Findings must identify reproducible evidence and severity. Engineering owners remediate; Kilo rechecks. The owner decides acceptance.

## 8. Current evidence posture

- WP-0: conditionally complete as baseline/preservation assessment only.
- WP-1–WP-6: design specifications and test oracles prepared; no fresh implementation/verification implied.
- Historical Phase 10 report claimed 535 passing tests; this is historical and does not establish current baseline or current P0 acceptance.
- Kilo independent acceptance evidence remains pending.
- Proposed P0 test oracles are `NOT_RUN` until actually executed.

## 9. Release restrictions

P0 validation must not:
- Publish publicly.
- Upload real content to external platforms.
- Spend money or activate paid services.
- Deploy production infrastructure.
- Use real customer/personal data.
- Bypass centralized authorization.
- Treat a successful local synthetic test as production readiness.

## 10. Acceptance statement template

> Accepted scope: [exact package/version/commit/build].  
> Evidence reviewed: [evidence IDs].  
> QA result: [result].  
> Known limitations: [list].  
> Explicit exclusions: [list].  
> Accepted by: [owner].  
> Date: [date].  
> This acceptance does not authorize [deployment/spending/publishing/other excluded actions].
