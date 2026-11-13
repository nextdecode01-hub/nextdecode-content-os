# NEXTDECODE P0 — WP-6 Acceptance Contract & Test Oracle Reconciliation
**Document ID:** `NEXTDECODE_P0_WP6_Acceptance_Contract_Test_Oracle_Reconciliation_0.1`  
**Version:** 0.1  
**Date:** 1 November 2026  
**Status:** DESIGN CANDIDATE — ACCEPTANCE SPECIFICATION RECONCILIATION  
**Finding addressed:** X-10 — WP-6 test oracles and environment controls  
**Scope:** P0-A vertical slice, failure injection, security-negative validation, evidence, independent QA and owner acceptance

**Detailed contract freeze:** NOT GRANTED  
**Implementation authorization:** NOT GRANTED  
**Test execution authorization:** NOT GRANTED  
**Repository inspection/modification, agents, Git operations, deployment, spending and external side effects:** NOT AUTHORIZED

---

## 1. Purpose and disposition

This document strengthens WP-6 from a scenario-and-category plan into a proposed acceptance specification. It reconciles:

- `NEXTDECODE_P0_WP6_Vertical_Slice_Integration_Recovery_Validation_0.1`;
- `NEXTDECODE_P0_Consolidated_Contract_Appendix_0.1`;
- `NEXTDECODE_P0_Cross_Document_Consistency_Gap_Review_0.1`, finding X-10;
- `NEXTDECODE_P0_API_Event_Contract_Reconciliation_0.1`;
- the accepted ADR/CF baseline and the governing QA/lifecycle/API standards.

The governing WP-6 plan remains authoritative for the intended scenario and its 18 failure-injection cases. This document adds traceability, candidate oracles, evidence requirements and environment safeguards. It does not silently replace Artifact 07's authoritative acceptance matrix or set final criticality thresholds.

**Disposition:** X-10 is substantially clarified as a design specification. Final acceptance readiness remains conditional on reconciling test IDs and criticality with Artifact 07, approving an isolated test environment, resolving required contract blockers, and obtaining explicit execution authorization.

## 2. Source authority and status labels

### 2.1 Source precedence

1. Accepted ADR-001–ADR-010 and CF-01–CF-24 owner decision record.
2. Governing Canonical Data Dictionary, API/Event Contract Standard and Unified Lifecycle & State Transition Standard.
3. Artifact 07 P0 Foundation Execution Plan & Acceptance Framework, for the authoritative acceptance requirements and criticality.
4. WP-1 through WP-6 package contracts, each within its scope.
5. P0 Consolidated Contract Appendix as a derivative cross-package index.
6. This reconciliation as a proposed test-oracle and evidence aid.

Where this document proposes additional test IDs, they are traceability identifiers only. They do not supersede existing WP-6 IDs, Artifact 07 identifiers or package-local identifiers.

### 2.2 Status labels

- **ACCEPTED BASELINE** — already accepted architecture/owner decision.
- **SOURCE-DEFINED** — required by the governing WP-6 or higher-authority source.
- **PROPOSED** — candidate oracle, evidence rule or test detail for review.
- **OPEN** — requires owner/security decision, authoritative source reconciliation or environment approval.
- **DEFERRED** — may remain unresolved only where a safe abstraction permits it.
- **NOT RUN** — no execution evidence exists.
- **NOT VERIFIED** — no implementation/runtime claim is made.

## 3. Acceptance objective and boundary

### 3.1 What P0-A is intended to demonstrate

One isolated, deterministic, non-production vertical slice:

1. Create a synthetic workspace/brand reference.
2. Create one canonical `ContentItem`, exact `ContentVersion` and `ContentVariant`.
3. Create a version-pinned workflow run and dependent task.
4. Create a durable job with an idempotency key and required capability.
5. Authenticate an eligible, trusted worker.
6. Claim the job under a valid lease/fencing generation.
7. Execute a deterministic test operation.
8. Register an immutable artifact version and manifest.
9. Verify transfer integrity, metadata and provenance.
10. Accept completion only from the current valid attempt/lease.
11. Advance workflow/task state only through owning-domain rules.
12. Reconstruct event, correlation, causation and attempt history.
13. Inject failures and demonstrate safe recovery.
14. Exercise security-negative and governance-denial paths.
15. Demonstrate that protected distribution is denied without separate current authorization.
16. Submit the evidence package for independent read-only Kilo QA and owner decision.

This proves a narrow platform backbone, not the whole future Content OS and not production readiness.

### 3.2 Prohibited scope

- Public publishing or real platform uploads.
- Production account actions or real customer/personal content.
- Paid provider activation or charge-generating infrastructure.
- Live external AI/provider transfer unless separately approved and specifically required (not required for this synthetic slice).
- Destructive migration, cleanup or deletion of user data.
- Unapproved source, test, configuration or environment changes.
- Unapproved Git operations.
- Agent execution or assignment.
- Any dry-run path that can silently become a live action.

## 4. Test environment contract

The actual environment/provider is **OPEN**. The following is the minimum proposed environment acceptance checklist; execution cannot begin until it is explicitly approved.

| ENV ID | Requirement | Evidence before test execution | Failure disposition |
|---|---|---|---|
| ENV-01 | Isolated test-only workspace/brand | Environment inventory and scope proof | BLOCKED |
| ENV-02 | Dedicated test database or approved isolated schema | Connection target and isolation proof; no production target | BLOCKED |
| ENV-03 | Test-only worker identity and credentials | Worker identity, scope and expiry evidence; secrets redacted | BLOCKED |
| ENV-04 | Controlled test artifact storage | Storage boundary and test namespace evidence | BLOCKED |
| ENV-05 | Deterministic synthetic fixtures only | Fixture manifest and provenance | BLOCKED |
| ENV-06 | Test-only authorization/policy configuration | Policy version and protected-action deny configuration | BLOCKED |
| ENV-07 | Outbound publishing/upload paths disabled | Negative connectivity/configuration proof | BLOCKED |
| ENV-08 | No paid/charge-generating resources | Configuration and cost-boundary review | BLOCKED |
| ENV-09 | Sanitized logs and evidence destination | Redaction test and access scope | BLOCKED |
| ENV-10 | Controlled teardown that cannot delete user data | Resource ownership tags and cleanup plan | BLOCKED |
| ENV-11 | Approved test parameters for lease/retry/timeout | Explicit test-only parameter record | BLOCKED if needed for scenario |
| ENV-12 | Stable source/configuration review target | Exact revision/config identity recorded, if later authorized | BLOCKED |
| ENV-13 | Clock/timestamp behavior documented | Clock source and timestamp convention | REVIEW if material ambiguity |
| ENV-14 | Stop/abort mechanism tested | Evidence that test can be halted without live side effects | BLOCKED |

**Environment gate:** every ENV-01–ENV-14 applicable item must be evidenced and approved before execution. A missing proof is not a pass. Environment selection and approval remain owner-reserved.

## 5. Fixture and deterministic-output contract

### 5.1 Synthetic fixture

**PROPOSED minimum fixture manifest:**

| Fixture field | Requirement |
|---|---|
| `fixture_set_id` | Stable identifier for this test run |
| `workspace_ref` | Test-only workspace reference |
| `brand_ref` | Test-only brand reference |
| `content_item_ref` | Canonical synthetic content identity |
| `content_version_ref` | Exact immutable content version |
| `content_variant_ref` | Exact format/platform/language derivative |
| `workflow_definition_ref` / version | Pinned workflow definition |
| `workflow_run_ref` | Unique test workflow run |
| `task_ref` | One dependent task |
| `job_ref` | One logical durable job |
| `worker_ref` | Test worker identity |
| `capability_ref` | Capability required and verified for this test |
| `artifact_ref` / version | Immutable output artifact |
| `manifest_ref` | Manifest referencing exact artifact version |
| `policy_version_ref` | Test-only policy version |
| `created_at` | UTC timestamp |
| `cleanup_scope_ref` | Only resources created by this fixture set |

Fixture identities must not collide with real content or be presented as production records.

### 5.2 Deterministic output

**PROPOSED:** use a tiny fixed byte fixture or deterministic generated text payload, not a production video, real media asset or publishable content.

The test specification must record:
- exact input bytes or canonical input representation;
- operation/version and configuration;
- expected output bytes or deterministic output-generation rule;
- media type and byte size;
- cryptographic checksum algorithm and calculated checksum;
- output artifact identity/version and manifest reference.

The expected checksum must be calculated from the approved fixture at test time or recorded in a versioned fixture manifest. Do not invent a checksum in this design document.

A deterministic test passes only when repeated execution under the same declared fixture/configuration produces the expected byte-level output or an explicitly defined canonical-equivalence result.

## 6. Canonical vertical-slice test matrix

The following IDs are proposed traceability IDs. They do not replace WP-6's existing numbered scenario or Artifact 07 IDs. Each oracle is a testable expected result, not a claim that the test has been run.

| Test ID | Requirement / step | Preconditions | Expected oracle | Minimum evidence |
|---|---|---|---|---|
| VS-01 | Create synthetic workspace/brand scope | ENV gate passed | Records exist only in approved test scope; canonical IDs and owner domains valid | IDs, scope proof, creation responses |
| VS-02 | Create ContentItem | Test workspace exists | One canonical immutable UUIDv7 identity; owning domain authoritative | Entity ID, owner, schema version |
| VS-03 | Create ContentVersion and ContentVariant | ContentItem exists | Exact version and derivative relationships valid; no ID conflation | IDs, version refs, relationship validation |
| VS-04 | Create version-pinned workflow run | Workflow definition/version exists | Run references exact definition version and test scope | Workflow/run IDs and version |
| VS-05 | Create dependent task | Workflow run exists | Task dependency and input/output contract recorded | Task ID, dependency graph, contract refs |
| VS-06 | Create durable job | Task ready; idempotency key supplied | Durable job exists with stable logical identity and required capability | Job ID, key fingerprint reference, persisted state |
| VS-07 | Scheduler eligibility | Job created | Eligibility decision is explicit with reason; no unauthorized claim | Decision, reason code, state before/after |
| VS-08 | Authenticate worker | Test worker enrolled/trusted | Correct identity and scoped credential validated; no impersonation | Worker ref, credential metadata without secret |
| VS-09 | Claim with lease/fencing | Worker eligible and authorized | Exactly one current claim/lease generation accepted for the logical job attempt | Attempt, lease, fencing generation |
| VS-10 | Verify assignment trust/capability | Claim established | Identity, trust, verified capability and assignment authorization all independently pass | Trust/capability/authorization evidence refs |
| VS-11 | Execute deterministic operation | Current lease valid | Declared operation runs against declared fixture; deterministic result produced | Operation version, input/output refs, result |
| VS-12 | Register artifact | Output produced | New immutable ArtifactVersion created; prior versions unchanged | Artifact/version IDs, media type, size, checksum |
| VS-13 | Register manifest | ArtifactVersion exists | Manifest references exact immutable version and required provenance/validation refs | Manifest ID, refs, hash evidence |
| VS-14 | Verify transfer/integrity | Transfer completed | Hash, size, media type and provenance match; partial data is not available as complete | Transfer/validation records, comparison result |
| VS-15 | Accept completion | Current lease/attempt valid | Completion accepted only for current attempt/fencing generation | Completion response, attempt/lease state |
| VS-16 | Advance task/workflow | Accepted completion evidence exists | Owning orchestrator advances only according to approved predicates | State transitions, versions, causation |
| VS-17 | Reconstruct audit history | Slice completed | Authorized reviewer can reconstruct ordered actor/action/state/event/job/artifact chain | Correlation trace, event IDs, audit refs |
| VS-18 | Deny protected distribution | No separate publishing authorization exists | Protected distribution request denied; no external request emitted | Denial code/policy reason, egress proof |

**Canonical-slice exit condition:** VS-01–VS-18 are all executed with evidence and no mandatory failure. Any test not run remains `NOT_RUN`, not `PASS`.

## 7. Failure-injection matrix

Preserve WP-6's existing F-01–F-18 identifiers and source wording. The following clarifies the test oracle and evidence.

| Source ID | Injected failure | Expected oracle | Minimum evidence |
|---|---|---|---|
| F-01 | Control-plane restart after job creation | Pending durable work survives and becomes eligible after recovery; no lost committed job | Before/after job state, DB/outbox evidence, recovery trace |
| F-02 | Worker termination after lease claim | Lease expires or is reconciled under test parameters; job becomes safely recoverable | Lease expiry/reconciliation, attempt history, next eligibility |
| F-03 | Worker terminates after output creation but before result callback | No unsafe duplicate logical effect; orphan output is reconciled or safely isolated | Output identity/hash, retry attempt, reconciliation disposition |
| F-04 | Duplicate event delivery | Inbox/dedup prevents duplicate logical processing | Same event ID, delivery attempts, one logical effect |
| F-05 | Stale callback after lease supersession | Rejected; stale worker cannot overwrite newer attempt or task/job state | Old/new fencing generations, rejection, unchanged current state |
| F-06 | Interrupted artifact transfer | Partial bytes are not registered as complete/available; safe resume/retry path | Transfer state, partial-byte isolation, retry evidence |
| F-07 | Artifact checksum mismatch | Artifact blocked or quarantined; downstream use denied | Expected/actual hash, validation outcome, access denial |
| F-08 | Worker credential revoked | New claims and protected artifact access denied | Revocation record, denied claim/access, audit |
| F-09 | Worker credential expired | Authentication/claim denied; no new protected work | Expiry metadata, denial, no lease/job mutation |
| F-10 | Worker claims unsupported capability | Assignment denied; worker cannot self-declare verification/authorization | Declared vs verified vs available vs authorized capability evidence |
| F-11 | Emergency pause before protected action | New protected action denied | Pause state/scope, denial, no external request |
| F-12 | Missing authorization | Protected action denied | Authorization lookup/result, denial reason |
| F-13 | Authorization bound to different artifact hash | Protected action denied | Authorized hash vs requested hash, denial |
| F-14 | Authorization bound to different destination | Protected action denied | Authorized vs requested destination, denial |
| F-15 | Ordinary approval attempted for `BLOCKED` QA | Hard blocker remains enforced | QA result, approval attempt, denial |
| F-16 | Protected use with `UNKNOWN`/`PENDING_REVIEW` rights | Denied for affected protected use | Rights state/use scope, denial |
| F-17 | Dry-run attempts live execution | Denied absent separate authorization; no external effect | Mode/config, action denial, egress evidence |
| F-18 | Direct adapter governance bypass | Central authorization denies and records attempt | Adapter path, policy decision, no external request |

**Recovery tests must not invent production lease/retry values.** Any numerical timeout or retry setting used in a test must be explicitly approved for that isolated test environment and must not be generalized to production.

## 8. Security-negative acceptance matrix

The source WP-6 groups are retained. Proposed test IDs below provide traceability and may be mapped to existing test identifiers during final reconciliation.

### 8.1 Identity and worker boundary

| Test ID | Negative attempt | Expected oracle |
|---|---|---|
| SEC-W-01 | Unknown worker identity | Denied before claim or protected access |
| SEC-W-02 | Revoked worker | Denied; no new protected work |
| SEC-W-03 | Expired credential | Denied; renewal is not assumed |
| SEC-W-04 | Unsupported contract version | Explicit safe rejection; no guessed interpretation |
| SEC-W-05 | Malformed worker message | Rejected; no state mutation |
| SEC-W-06 | Unsupported capability claim | Assignment denied |
| SEC-W-07 | Worker A updates Worker B lease | Denied; B's lease unchanged |
| SEC-W-08 | Stale worker commits after supersession | Fencing rejects stale completion |
| SEC-W-09 | Worker attempts authority expansion | Denied and audited |
| SEC-W-10 | Secret placed in log/test output | Redaction/security control prevents disclosure |

### 8.2 Artifact boundary

| Test ID | Negative attempt | Expected oracle |
|---|---|---|
| SEC-A-01 | Expired transfer grant | Transfer/access denied |
| SEC-A-02 | Cross-job artifact access | Denied |
| SEC-A-03 | Storage locator used as permission | Denied without authorization |
| SEC-A-04 | Checksum mismatch | Artifact blocked/quarantined; downstream use denied |
| SEC-A-05 | Quarantined artifact access | Denied |
| SEC-A-06 | New artifact version mutates old version | Immutability check fails; old version remains unchanged |
| SEC-A-07 | Partial transfer treated as complete | Registration/availability denied |

### 8.3 Governance boundary

| Test ID | Negative attempt | Expected oracle |
|---|---|---|
| SEC-G-01 | Missing authorization | Protected action denied |
| SEC-G-02 | Expired authorization | Protected action denied |
| SEC-G-03 | Revoked authorization | Protected action denied |
| SEC-G-04 | Resource/version/hash mismatch | Protected action denied |
| SEC-G-05 | Destination mismatch | Protected action denied |
| SEC-G-06 | Ordinary approval overrides `BLOCKED` QA | Denied; hard blocker persists |
| SEC-G-07 | Unknown/pending rights used for protected purpose | Denied for affected use |
| SEC-G-08 | Emergency pause active | New protected action denied |
| SEC-G-09 | Direct adapter/pipeline bypass | Central authorization denies |
| SEC-G-10 | Automatic public publishing | Remains disabled |
| SEC-G-11 | Retry after policy denial | Denial cannot be bypassed through retry |

## 9. API/Event cross-reference

The API/Event reconciliation proposed API-EVT-01–API-EVT-25. These remain a companion suite, not duplicate new WP-6 requirements. Their execution evidence should be cross-linked rather than run twice where an existing test proves the same requirement.

| API-EVT IDs | WP-6 coverage relationship |
|---|---|
| 01–07 | Query/command semantics, validation, idempotency, stale version and transactional outbox; map to VS-06/VS-16 and relevant F-01 |
| 08–10 | Duplicate, ordering and unknown event handling; map to F-04 and audit reconstruction |
| 11–13 | Schema compatibility; map to SEC-W-04 and contract conformance suite |
| 14–15 | Replay safety; separate replay test if replay is included in approved scope |
| 16–17 | Secret minimization and workspace scope; map to SEC-W-10 and cross-workspace negative tests |
| 18 | Poison-message isolation; add explicit recovery test if dead-letter behavior is in P0 scope |
| 19 | Ambiguous external outcome; validate only in a controlled simulator, never against a real provider |
| 20 | Revoked worker retry; map to F-08 and SEC-W-02 |
| 21–23 | Error envelope, correlation/causation and version-gap reconciliation; map to VS-17 and event tests |
| 24 | Webhook signature/replay; external webhook exposure may be deferred if not part of P0 slice |
| 25 | Direct adapter publishing bypass; map to F-18 and SEC-G-09 |

**No duplicate execution requirement:** one test execution may satisfy multiple requirements only when the evidence explicitly proves every mapped oracle. Traceability is not proof by association.

## 10. Acceptance result vocabulary and test disposition

The WP-6 source defines:

| Result | Meaning |
|---|---|
| `PASS` | Requirement satisfied with evidence |
| `PASS_WITH_WARNINGS` | Requirement satisfied; documented non-blocking warnings remain |
| `NEEDS_REVIEW` | Human or specialist assessment required |
| `BLOCKED` | Hard requirement failed or prerequisite absent |
| `NOT_RUN` | Test has not been executed |
| `NOT_APPLICABLE` | Test does not apply to approved scope, with rationale |

Rules:
1. `NOT_RUN` is never `PASS`.
2. A design statement, code inspection alone or historical test total is not runtime test evidence.
3. `NOT_APPLICABLE` requires an approved scope rationale and reviewer.
4. `PASS_WITH_WARNINGS` cannot hide a hard blocker.
5. `NEEDS_REVIEW` is not acceptance.
6. A test that cannot be run safely is `BLOCKED` or `NOT_RUN` with explanation; do not improvise.
7. Each result is bound to the exact test version, fixture set, environment and implementation/review target.

### 10.1 Proposed severity labels — not yet authoritative

**PROPOSED only:** use `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` for risk triage. Do not assign final criticality until Artifact 07's authoritative matrix is reconciled. The proposed labels below indicate obvious safety significance, not accepted threshold policy.

- Critical candidates: protected-action bypass, data/secret leakage, loss of durable committed state, stale worker acceptance, artifact integrity bypass, rights/QA hard-blocker bypass, unauthorized external side effect.
- High candidates: recovery failures, incorrect workflow progression, broken audit reconstruction, credential revocation failure, cross-workspace access.
- Medium candidates: compatibility/replay/poison handling failures where they do not violate a hard safety invariant.
- Low candidates: non-blocking observability/documentation defects.

## 11. Evidence record and evidence package

### 11.1 Per-test evidence record

**PROPOSED minimum fields:**

| Field | Purpose |
|---|---|
| `evidence_id` | Unique evidence record identity |
| `requirement_ref` | Requirement/test oracle being demonstrated |
| `test_id` and test version | Stable test identity |
| `test_run_id` | One execution of that test |
| `source_build_ref` | Exact implementation/review target, if applicable |
| `environment_ref` | Approved isolated environment |
| `fixture_set_id` | Exact synthetic fixture set |
| `contract_schema_refs` | API/event/entity/state/policy schema versions |
| `input_refs` / `output_refs` | Exact test inputs and outputs |
| `result` | Accepted QA/test disposition |
| `observed_at` | Execution timestamp |
| `request_id` / `correlation_id` / `causation_id` | Trace reconstruction |
| `job_id` / `attempt_id` / `lease_ref` | Execution evidence where applicable |
| `artifact_version_ref` / `manifest_ref` | Artifact proof where applicable |
| `log_refs` | Sanitized supporting logs |
| `reviewer_ref` | Attributable reviewer |
| `limitations` | What evidence does not prove |

Do not store credentials, tokens, unrestricted provider payloads, private prompts or unnecessary personal data in evidence.

### 11.2 Required evidence package

The deliverable remains `P0_Acceptance_Evidence_Report_1.0`, containing:

1. Work-package ID and approved scope.
2. Exact implementation revision or frozen review target, if later authorized.
3. Environment/configuration summary without secrets.
4. Contract/schema versions used.
5. Test identifiers, versions and environment.
6. Exact commands and sanitized output.
7. Pass/fail/skip/not-run counts.
8. Failure-injection results.
9. Security-negative test results.
10. Audit traces and correlation IDs.
11. Artifact identity/version/checksum evidence.
12. Recovery and reconciliation evidence.
13. Known limitations and unverified behavior.
14. Confirmation no unauthorized external side effects occurred.
15. Independent reviewer disposition.
16. Owner acceptance/rejection record, if made.

The report must distinguish executed-and-passed, executed-and-failed, not executed, inferred from documentation, and not verified.

### 11.3 Evidence integrity

**PROPOSED:**
- Preserve original test output and logs as immutable evidence references.
- Corrections append a new evidence record; do not silently rewrite a prior result.
- Evidence references bind to exact test, fixture, environment and source/config version.
- Any redaction is documented and must not remove information needed to verify the oracle.
- Evidence retention and deletion follow the separately approved data-lifecycle policy; no retention duration is invented here.

## 12. Independent QA and owner acceptance

Existing responsibilities remain unchanged:

| Role | Responsibility |
|---|---|
| Qoder | Phase 11 engineering owner; no new assignment created here |
| OpenCode | Phase 10 engineering/closure owner; no new assignment created here |
| Kilo | Independent read-only QA; reviews a stable evidence target without source/test/config/Git modifications |
| Product owner | Final authority to accept or reject P0-A based on evidence and limitations |

### 12.1 Kilo QA review checklist

Kilo's read-only review should determine whether:
- scope and environment match the approved test plan;
- test IDs map to authoritative requirements;
- every mandatory oracle has evidence;
- deterministic fixtures and outputs are reproducible;
- failure injection demonstrates safe recovery;
- security-negative tests prove denial, not merely expected configuration;
- governance and external-side-effect controls are evidenced;
- audit history can be reconstructed;
- limitations and unverified claims are explicit;
- the conclusion is supported by the evidence.

Kilo must report `PASS`, `PASS_WITH_WARNINGS`, `NEEDS_REVIEW` or `BLOCKED` using the accepted QA vocabulary and explain blockers/warnings. No QA pass is claimed in this design document.

### 12.2 Owner acceptance record

Owner acceptance is a separate decision after independent QA. It should record:
- exact P0-A scope and evidence package version;
- Kilo QA disposition and unresolved findings;
- mandatory tests not run or not applicable;
- known limitations and accepted residual risks;
- decision: accept / reject / return for remediation;
- decision maker and timestamp.

No acceptance is implied by completion of this document or by an agent's self-report.

## 13. Acceptance thresholds and stop conditions

### 13.1 Source-defined non-acceptance conditions

P0-A cannot be accepted if:
- any critical test fails;
- any mandatory test is `NOT_RUN`;
- a protected-action bypass exists;
- a worker exceeds lease or capability scope;
- durable state is lost on restart;
- artifact integrity or access controls fail;
- recovery cannot be demonstrated;
- audit cannot reconstruct the workflow;
- independent read-only QA has not reviewed evidence;
- unauthorized external side effects occur.

Non-critical warnings require documented owner disposition. A warning cannot conceal a hard blocker.

### 13.2 Stop conditions

Stop the affected validation and escalate if:
- production account or external platform interaction is possible;
- live upload/publishing could occur;
- unapproved Git operation appears necessary;
- destructive migration/data rewrite is proposed;
- WIP ownership conflicts;
- dependency/environment changes are required but unauthorized;
- secret/credential is exposed;
- direct publishing paths cannot be contained;
- rights, safety or integrity requirement is ambiguous;
- cost exceeds approved envelope;
- scope requires broad refactoring;
- independent QA lacks a stable read-only target.

Do not improvise around a stop condition.

## 14. Traceability and reconciliation gaps

| Gap ID | Required action | Authority needed | Status |
|---|---|---|---|
| X10-R01 | Map every VS/F/SEC/API-EVT test to Artifact 07 requirement IDs | Source reconciliation | OPEN |
| X10-R02 | Reconcile criticality and mandatory/optional classification with Artifact 07 | Governing acceptance matrix | OPEN |
| X10-R03 | Approve isolated environment and ENV checklist | Owner approval | OPEN |
| X10-R04 | Define exact deterministic fixture and output-generation specification | WP-1/WP-4/WP-6 contract owners | PROPOSED |
| X10-R05 | Define evidence retention and cleanup consistent with lifecycle policy | Owner/data-lifecycle decision | OPEN |
| X10-R06 | Confirm test-only lease/retry/timeout values | WP-2 contract and environment approval | OPEN |
| X10-R07 | Confirm exact worker identity/capability test fixture | WP-3 contract/security review | OPEN |
| X10-R08 | Confirm authorization/emergency-pause test setup and authority | WP-5 owner-reserved decision | OPEN |
| X10-R09 | Define Kilo evidence handoff format and read-only boundary | Existing QA owner process | OPEN |
| X10-R10 | Define owner acceptance record and residual-risk disposition | Product owner | OPEN |
| X10-R11 | Confirm external webhook/replay tests are in P0 scope or deferred | API/event contract scope | OPEN |
| X10-R12 | Confirm no destructive cleanup is needed; test fixtures isolated | Environment owner | OPEN |

## 15. Final assessment

**X-10 specification completeness:** SUBSTANTIALLY CLARIFIED.  
**Canonical vertical-slice oracles:** PROPOSED AND TRACEABLE.  
**Failure-injection oracles:** WP-6 F-01–F-18 PRESERVED AND CLARIFIED.  
**Security-negative tests:** GROUPS PRESERVED; TEST TRACE IDS PROPOSED.  
**Environment controls:** CHECKLIST DEFINED; ENVIRONMENT NOT APPROVED.  
**Fixture/output determinism:** CONTRACT PROPOSED; FIXTURE NOT CREATED.  
**Artifact 07 mapping and criticality:** OPEN.  
**Evidence package:** SPECIFIED; NO EVIDENCE GENERATED.  
**Independent Kilo QA:** NOT PERFORMED / NOT ACCEPTED.  
**P0-A execution:** NOT AUTHORIZED.

This document does not:
- alter accepted ADR-001–ADR-010 or CF-01–CF-24;
- replace Artifact 07's authoritative acceptance matrix;
- approve the environment or test parameters;
- authorize tests, repository inspection/modification, Git operations or agent execution;
- authorize provider activation, spending, deployment, uploads or publishing;
- establish implementation readiness, P0 acceptance or production readiness.

**Detailed contract freeze: NOT GRANTED.**  
**Implementation authorization: NOT GRANTED.**  
**Test execution authorization: NOT GRANTED.**

---

## Plain-language explanation

WP-6 is the final exam for the P0 foundation. The earlier plan told us what to test; this reconciliation makes the expected result and the proof much clearer.

For example, if a worker dies after claiming a job, we do not just write “recovery works.” We require evidence that the lease is handled, the job remains recoverable, a stale worker cannot later overwrite the new attempt, and the audit trail shows what happened.

The same standard applies to artifacts, credentials, rights, approvals, authorization and publishing denial. A test only passes when the approved synthetic test actually runs and the evidence proves the expected result.

The remaining major step is to map these proposed test IDs to Artifact 07's authoritative acceptance requirements and criticality. No tests have been run or authorized.

**NEXTDECODE principle:** every important requirement needs a test, every test needs an observable oracle, and every claimed pass needs evidence.
