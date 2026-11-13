# NEXTDECODE — P0 WP-6
## Vertical-Slice Integration & Recovery Validation

**Version:** 0.1  
**Status:** DESIGN CANDIDATE — OWNER REVIEW REQUIRED  
**Scope:** P0 foundation  
**Implementation status:** Not authorized  
**Primary deliverable:** `P0_Acceptance_Evidence_Report_1.0`

---

## 1. Purpose

WP-6 demonstrates that the P0 foundation works together through one controlled, deterministic, end-to-end scenario.

It validates integration across:
- canonical domain and persistence (WP-1);
- durable workflow, jobs, leases and recovery (WP-2);
- worker identity, trust and contract boundary (WP-3);
- artifact registration, integrity and transfer (WP-4);
- governance, QA, rights and authorization (WP-5).

The goal is not to prove the entire future NEXTDECODE Content OS. It is to prove one narrow, reliable platform backbone and document what remains unverified.

## 2. Decision labels

- **ACCEPTED:** Established by accepted architecture or owner decisions.
- **SOURCE-DEFINED:** Explicitly required by the P0 execution and acceptance framework.
- **RECOMMENDED:** Proposed validation detail for owner review.
- **OPEN:** Requires decision, evidence or an approved test environment.
- **DEFERRED:** Intentionally postponed.

This document is a validation design candidate. It does not authorize repository inspection, implementation, tests, agents, deployment or production actions.

## 3. Accepted validation principles

1. Use one isolated, non-production vertical slice.
2. Create one test content item and variant.
3. Create a workflow and dependent task.
4. Dispatch a durable job.
5. Claim it with an authenticated, eligible worker.
6. Produce deterministic test output.
7. Register an immutable artifact.
8. Record results and state transitions.
9. Inject worker, process, event and transfer failures.
10. Verify recovery and audit reconstruction.
11. Run security-negative and governance tests.
12. Complete independent read-only QA through Kilo under existing ownership.
13. No unauthorized external side effects.
14. Document known limitations and all unverified claims.

A passing test suite does not establish production readiness.

## 4. Test environment and safety boundary

### Required environment

**RECOMMENDED:** An isolated test environment with:
- test-only workspace and brand reference;
- test content and variant;
- test database or isolated schema approved for the test;
- test worker identity and test credentials;
- controlled test artifact storage;
- deterministic fixture inputs and outputs;
- test-only policy/authorization configuration;
- outbound external publishing and upload paths disabled.

The actual environment and provider are **OPEN** and must be approved before execution.

### Prohibited during WP-6

- Public publishing.
- Real platform uploads.
- Production account actions.
- Paid provider activation or charge-generating infrastructure.
- Real customer or personal content.
- Destructive migrations or cleanup.
- Unapproved Git operations.
- Unapproved source, test, configuration or environment changes.
- Secret exposure in logs, reports or test output.

A dry-run must not silently become a live action.

## 5. Canonical vertical-slice scenario

### Scenario

A single test content item moves through a minimal workflow. One durable job is claimed by one registered worker. The worker creates a deterministic test output. The output is registered as an immutable artifact. The workflow records the result and can recover from interruption.

### Expected sequence

1. Create a test workspace and brand reference.
2. Create a test content item with canonical identity.
3. Create one content variant.
4. Create a workflow run bound to its workflow version.
5. Create a task with explicit input/output contract and dependency rules.
6. Create a durable job with an idempotency key and required capability.
7. Scheduler determines that the job is eligible.
8. A registered worker authenticates.
9. Worker claims the job under a valid, bounded lease.
10. Control plane verifies worker identity, trust, capability and assignment authorization.
11. Worker executes a deterministic test operation.
12. Worker produces a test output.
13. Worker registers the output as an artifact with media type, byte size and checksum.
14. Control plane verifies transfer integrity and artifact metadata.
15. Completion is accepted only from the current valid attempt/lease.
16. Workflow advances only after valid completion evidence.
17. Audit records permit an authorized reviewer to reconstruct the complete sequence.
18. A protected distribution request is denied because no separate publishing authorization has been granted.

The test output should be a simple deterministic fixture, not a production video or externally publishable asset.

## 6. End-to-end evidence checkpoints

| Checkpoint | Required evidence |
|---|---|
| Domain creation | Canonical IDs, ownership and relationship validation |
| Workflow creation | Workflow/run version and task dependency records |
| Job creation | Durable job identity, schema version and idempotency key |
| Scheduling | Eligibility decision and reason |
| Worker claim | Worker identity, approved capability and lease evidence |
| Execution | Attempt identity, input references and deterministic result |
| Artifact registration | Immutable artifact/version, checksum, media type and size |
| Completion | Current lease/attempt validation and accepted result |
| Workflow transition | Valid state transition and causation/correlation references |
| Governance denial | Protected action denied with policy reason |
| Audit reconstruction | Ordered, attributable trace across the complete path |

Evidence must show actual test outcomes, not merely the intended design.

## 7. Failure-injection plan

Every failure scenario must be run in the isolated environment, with a defined expected outcome and retained evidence.

| ID | Injected failure | Expected safe behavior |
|---|---|---|
| F-01 | Control-plane restart after job creation | Pending durable work survives and becomes eligible after recovery |
| F-02 | Worker termination after lease claim | Lease expires or is reconciled; job can be safely recovered |
| F-03 | Worker terminates after output creation but before result callback | Duplicate/retry path does not create an unsafe duplicate logical effect; output is reconciled |
| F-04 | Duplicate event delivery | Inbox/deduplication prevents duplicate logical processing |
| F-05 | Stale callback after lease supersession | Rejected; stale worker cannot overwrite newer attempt |
| F-06 | Interrupted artifact transfer | Partial bytes are not treated as a durable available artifact; safe retry is possible |
| F-07 | Artifact checksum mismatch | Artifact is blocked or quarantined; downstream use denied |
| F-08 | Worker credential revoked | New claims and protected artifact access denied |
| F-09 | Worker credential expired | Authentication/claim denied |
| F-10 | Worker claims unsupported capability | Assignment denied |
| F-11 | Emergency pause activated before protected action | New protected action denied |
| F-12 | Missing authorization | Protected action denied |
| F-13 | Authorization bound to different artifact hash | Protected action denied |
| F-14 | Authorization bound to different destination | Protected action denied |
| F-15 | Ordinary approval attempted for `BLOCKED` QA result | Hard blocker remains enforced |
| F-16 | Protected use attempted with `UNKNOWN`/`PENDING_REVIEW` rights | Denied under accepted policy baseline |
| F-17 | Dry-run request attempts to become live execution | Denied without separate authorization |
| F-18 | Direct adapter attempts governance bypass | Denied and auditable |

Some recovery details depend on still-open numeric lease/retry parameters and exact policy schemas. Those parameters must not be guessed for a production configuration. Test values must be explicitly scoped to the approved test environment.

## 8. Security-negative test groups

### Identity and worker boundary

- Unknown worker identity denied.
- Revoked worker denied.
- Expired credential denied.
- Unsupported contract version rejected explicitly.
- Malformed worker message rejected.
- Worker cannot claim an unsupported capability.
- Worker A cannot update Worker B's lease.
- Stale worker cannot commit after lease supersession.
- Worker cannot expand its own authority.
- Secrets are absent from logs and test output.

### Artifact boundary

- Expired transfer grant denied.
- Cross-job artifact access denied.
- Storage locator alone does not grant access.
- Checksum mismatch blocks downstream use.
- Quarantined artifact rejected.
- New artifact version does not mutate the old version.
- Interrupted transfer is recoverable without treating partial data as complete.

### Governance boundary

- Missing authorization denied.
- Expired authorization denied.
- Revoked authorization denied.
- Resource/version/hash mismatch denied.
- Destination mismatch denied.
- `BLOCKED` QA cannot pass through ordinary approval.
- Unknown or pending rights block the affected protected use.
- Emergency pause blocks new protected actions.
- Direct adapter and direct pipeline bypasses denied.
- Automatic public publishing remains disabled.
- Policy denial cannot be bypassed through retry.

## 9. Acceptance result vocabulary

| Result | Meaning |
|---|---|
| `PASS` | Requirement satisfied with evidence |
| `PASS_WITH_WARNINGS` | Requirement satisfied; documented non-blocking warnings remain |
| `NEEDS_REVIEW` | Human or specialist assessment required |
| `BLOCKED` | A hard requirement failed or a required prerequisite is absent |
| `NOT_RUN` | Test has not been executed |
| `NOT_APPLICABLE` | Test does not apply to approved scope, with rationale |

A test must never be marked `PASS` merely because it was not run or because documentation describes the expected behavior.

## 10. Acceptance thresholds

P0-A cannot be accepted if:
- any critical test fails;
- any mandatory test is `NOT_RUN`;
- a protected-action bypass exists;
- a worker can exceed its lease or capability scope;
- durable state is lost on restart;
- artifact integrity or access controls fail;
- failure recovery cannot be demonstrated;
- the audit trail cannot reconstruct the workflow;
- independent read-only QA has not reviewed the evidence;
- unauthorized external side effects occur.

Non-critical warnings require documented owner disposition. A warning must not conceal a hard blocker.

The final acceptance matrix and criticality assignments must be reconciled against the authoritative Artifact 07 matrix before execution.

## 11. Evidence package requirements

The deliverable is `P0_Acceptance_Evidence_Report_1.0`.

It must include:

1. Work-package ID and approved scope.
2. Exact implementation revision or frozen review target, if implementation is later authorized.
3. Environment and configuration summary without secrets.
4. Contract/schema versions used.
5. Test identifiers and test execution environment.
6. Exact test commands and sanitized output.
7. Pass/fail/skip/not-run counts.
8. Failure-injection results.
9. Security-negative test results.
10. Relevant audit traces and correlation IDs.
11. Artifact identity/version/checksum evidence.
12. Recovery and reconciliation evidence.
13. Known limitations and unverified behavior.
14. Confirmation that no unauthorized external side effects occurred.
15. Independent reviewer disposition.

Evidence must distinguish:
- test executed and passed;
- test executed and failed;
- test not executed;
- result inferred from documentation;
- result not verified.

Do not combine historical test totals from different reports unless overlap is known.

## 12. Independent QA and ownership

Existing ownership remains unchanged:

| Owner | Existing responsibility | WP-6 role |
|---|---|---|
| Qoder | Phase 11 engineering owner | No new assignment from this document |
| OpenCode | Phase 10 engineering/closure owner | No new assignment from this document |
| Kilo | Independent read-only QA | Review the frozen evidence target; no source, test, configuration or Git modifications |
| Product owner | Final authority | Review evidence and make the P0 acceptance decision |

Kilo's review should assess:
- scope compliance;
- reproducibility and evidence completeness;
- test coverage against mandatory acceptance criteria;
- failure/recovery behavior;
- governance and security-negative results;
- known gaps and unsupported claims;
- whether the evidence supports the stated conclusion.

Independent QA must not be represented as passed until Kilo has actually completed and reported it.

## 13. Stop conditions

Stop the affected validation and escalate if:
- a test could touch a production account or external platform;
- a live upload or publishing side effect is possible;
- an unapproved Git operation appears necessary;
- destructive migration or data rewrite is proposed;
- existing work-in-progress ownership conflicts;
- dependency or environment changes are required but unauthorized;
- a secret or credential is exposed;
- direct publishing paths cannot be contained;
- a hard rights, safety or integrity rule is ambiguous;
- provider cost exceeds the approved envelope;
- the test scope requires broad refactoring;
- independent QA cannot obtain a stable read-only target.

Do not improvise around a stop condition.

## 14. Stage gates and final decision

| Gate | Evidence required | Decision |
|---|---|---|
| G0 — Contract review | Detailed contracts reviewed; unresolved values accepted or deferred | Contract baseline may be frozen |
| G1 — Baseline readiness | Authorized system baseline and preservation evidence | Implementation proposal readiness |
| G2 — P0 design readiness | Work packages, security design and acceptance matrix | Bounded implementation scope may be proposed |
| G3 — Implementation authorization | Explicit scope, permissions, ownership, environment and safeguards | Owner may authorize implementation |
| G4 — P0 acceptance | Mandatory tests, recovery evidence, independent QA, no critical failures | Accept or reject P0-A completion |
| G5 — Operational readiness | Separately approved infrastructure, budget, backup/restore, monitoring and runbooks | Separate operational decision |
| G6 — Production distribution | Governance paths verified, rights/quality gates verified, explicit action authorization | Separate production decision |

Passing one gate does not automatically pass the next.

## 15. Dependencies and handoffs

- **WP-1:** Canonical entities, identity, ownership and versioning.
- **WP-2:** Durable jobs, leases, idempotency, outbox/inbox and recovery.
- **WP-3:** Authenticated worker, trust, capabilities and revocation.
- **WP-4:** Immutable artifact versions, integrity and controlled transfer.
- **WP-5:** Central authorization, QA, rights, approval and emergency pause.

WP-6 integrates and validates these boundaries; it does not replace their owning contracts.

## 16. Implementation safety boundary

This document does not authorize:
- repository inspection or code changes;
- tests or command execution against the repository;
- Git operations;
- dependency or environment changes;
- agent task assignment or execution;
- provider activation or paid services;
- cloud deployment;
- production generation;
- external upload or public publishing.

Any such action requires separate, explicit owner authorization.

## 17. Plain-language explanation

WP-6 is the final exam for the P0 foundation.

We create one fake content item, move it through the workflow, let one trusted worker perform a small deterministic task, register its output, and confirm that every step is recorded.

Then we deliberately break things: restart the control plane, stop the worker, duplicate an event, interrupt a file transfer, revoke credentials and attempt unauthorized actions.

The system passes only when it recovers safely, blocks prohibited actions and leaves enough evidence to reconstruct what happened.

For NEXTDECODE, this is the difference between having six architecture documents and proving that the foundation can actually work together.

---

**WP-6 outcome:** The integrated P0 vertical slice, failure-injection plan, security-negative tests, evidence package and acceptance gates are defined. Execution remains unauthorized. A completed design package is not a passed test or production-readiness claim.
