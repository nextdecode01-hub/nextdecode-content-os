NEXTDECODE

P0 STATE-MACHINE &
TRANSITION CATALOGUE

Batch 17 | Domain-by-domain lifecycle candidate

| Document control | Value |
| --- | --- |
| Series | NEXTDECODE Content OS — P0 documentation series |
| Batch | 17 — State-Machine & Transition Catalogue |
| Prepared | 1 November 2026 |
| Status | Detailed state-machine candidate; not formally frozen |
| Authority | Accepted ADR/CF decisions carried forward; proposed details remain subject to owner freeze |
| Implementation | Not authorized by this document |
| Purpose | Define domain-owned states, transition rules, actors, guards, events, failure handling and acceptance scenarios |

Purpose. Translate lifecycle and state-ownership principles into an explicit catalogue that can be reviewed, tested and later implemented. This is a contract candidate, not evidence that these state machines exist in code.

Source discipline. Accepted vocabularies are reproduced where known. Where source standards establish separation and ownership but do not provide a complete enum or transition matrix, the detail is marked PROPOSED / OPEN rather than presented as accepted.

## 1. Executive state model

NEXTDECODE must not use one universal status field. Each domain owns its state machine and commits its own transitions. Lifecycle, execution, quality, rights, approval, authorization, external-operation and epistemic states answer different questions and must not be collapsed.

| Dimension | Question | Owner | Vocabulary / status |
| --- | --- | --- | --- |
| Entity lifecycle | Where is this entity in its own lifecycle? | Owning domain | Domain-specific; complete enums open |
| Workflow lifecycle | Where is orchestration? | Automation & Agent Orchestration | Proposed run states below |
| Execution | What happened to a job/attempt? | Automation & Agent Orchestration | Exact enum freeze pending |
| Quality | Did this exact version meet quality policy? | Content Quality Intelligence | PASS; PASS_WITH_WARNINGS; NEEDS_REVIEW; BLOCKED |
| Rights | Is intended use supported by evidence? | Governance boundary | UNKNOWN; PENDING_REVIEW; CLEARED; RESTRICTED; EXPIRED; REVOKED; DENIED |
| Approval | What did reviewer decide? | Approval owner | APPROVED; REJECTED; CHANGES_REQUESTED; EXPIRED; REVOKED |
| Authorization | May exact protected action execute now? | Central authorization | Default-deny; action/resource/version/destination/policy/time bound |
| External operation | What is known about remote side effect? | Distribution Studio | Exact enum open; unknown outcome distinct |
| Epistemic/provenance | How verified is the record? | Owning domain | Exact vocabulary open |

### 1.1 Normative rules

- Only the authoritative owner may commit a canonical transition for its state machine.

- Every accepted transition is attributable, auditable, versioned and causally traceable.

- Commands request transitions; events describe transitions that have already committed.

- Expected state version is checked to prevent stale writes.

- Invalid transitions are rejected, not silently coerced.

- Unknown, missing, ambiguous, expired or revoked rights/approval/authorization never grant permission.

- An external timeout after a possible side effect is an unknown outcome requiring reconciliation, not automatic retry.

- State-machine name and version are included in transition evidence.

## 2. Common transition contract

| Field | Meaning | Requirement |
| --- | --- | --- |
| event_id | Unique committed event identity | Required |
| entity_id / entity_type | Canonical target identity and type | Required |
| owning_domain | Domain that owns transition | Required |
| state_machine_name / version | Identifies machine semantics | Required |
| state_version | Monotonic version for entity/machine | Required |
| prior_state / new_state | Explicit transition | Required for transition event |
| occurred_at / recorded_at | Occurrence and persistence time in UTC | Required design element |
| actor_ref / actor_type | Human, system, worker or service | Required |
| reason | Decision basis | Required for governed transitions |
| correlation_id / causation_id | Cross-command/run/job/event trace | Required |
| policy_version | Policy used for guarded decisions | Where relevant |
| evidence_refs / result_refs | Supporting evidence and outputs | Where relevant |
| schema_version | Envelope compatibility version | Required |

### 2.1 Evaluation sequence

1. Authenticate caller and derive actor identity from authenticated context.

1. Resolve canonical entity and verify workspace/brand/resource scope.

1. Load authoritative current state and state_version.

1. Validate command schema and expected_state_version.

1. Check capability, policy guards, required evidence and exact-version binding.

1. Validate requested edge and all transition guards.

1. Commit state update and outbox event atomically where applicable.

1. Return defined command outcome; asynchronous ACCEPTED includes durable operation reference.

1. Consumers deduplicate events and do not infer protected-action permission from event receipt.

| Outcome | Meaning | Behavior |
| --- | --- | --- |
| ACCEPTED | Durably accepted asynchronously | Return durable reference; do not claim completion. |
| COMPLETED | Defined processing completed | Read authoritative result and external outcome. |
| REJECTED | Invalid, unauthorized or policy-blocked | No transition; structured reason. |
| CONFLICT | Expected state/version is stale | No overwrite; refresh authoritative state. |

## 3. State-machine inventory

| ID | Entity / aggregate | Owner | Dimension | Status |
| --- | --- | --- | --- | --- |
| SM-01 | ContentItem / ContentVariant / ContentVersion | Content Graph | Editorial lifecycle | Candidate; enums open |
| SM-02 | WorkflowDefinition | Automation | Definition lifecycle/version | Candidate |
| SM-03 | WorkflowRun | Automation | Run lifecycle | Candidate |
| SM-04 | TaskInstance | Automation | Task execution | Candidate; mapping open |
| SM-05 | Job | Automation | Durable execution | Candidate |
| SM-06 | JobAttempt / lease | Automation | Attempt/lease | Candidate; numeric values open |
| SM-07 | Worker | Automation | Trust/lifecycle | Candidate; protocol open |
| SM-08 | Artifact / ArtifactVersion | Asset Management | Validation/availability | Candidate |
| SM-09 | Transfer | Asset Management | Transfer lifecycle | Candidate |
| SM-10 | Quality evaluation | Content Quality | Quality outcome | Accepted vocabulary |
| SM-11 | Rights determination | Governance | Rights status | Accepted CF-20 |
| SM-12 | Review / approval | Governance | Approval outcome | Accepted CF-21 |
| SM-13 | Authorization decision | Central authorization | Permission decision | Central model accepted |
| SM-14 | Distribution operation | Distribution Studio | External outcome | Candidate |
| SM-15 | Quarantine record | Asset/Governance | Quarantine disposition | Candidate |

## 4. SM-01 — Content editorial lifecycle

Owner: Content Graph. ContentItem is the canonical editorial subject; ContentVariant represents a derivative/format identity; ContentVersion is an immutable snapshot. These identities must not be conflated.

| Proposed state | Meaning |
| --- | --- |
| DRAFT | Editorial subject/variant is being assembled. |
| READY_FOR_REVIEW | A specific immutable version submitted for review. |
| IN_REVIEW | Review work actively assigned or underway. |
| CHANGES_REQUESTED | Review requires revision. |
| APPROVED_FOR_NEXT_STAGE | Editorial/quality prerequisites met; not publish authorization. |
| ARCHIVED | No longer active for ordinary work; retention still applies. |

| Transition | Actor | Guards | Committed event / rule |
| --- | --- | --- | --- |
| DRAFT → READY_FOR_REVIEW | Content owner/workflow | Version exists; required metadata present; immutable | ContentVersionSubmittedForReview |
| READY_FOR_REVIEW → IN_REVIEW | Review workflow | Reviewer assignment valid; exact version captured | ContentReviewStarted |
| IN_REVIEW → CHANGES_REQUESTED | Authorized reviewer | Findings/evidence bound to exact version | ContentChangesRequested |
| IN_REVIEW → APPROVED_FOR_NEXT_STAGE | Authorized reviewer/workflow | Required quality and review policy satisfied | ContentVersionAcceptedForNextStage |
| CHANGES_REQUESTED → DRAFT | Content owner | New editable revision; prior version preserved | ContentRevisionStarted |
| APPROVED_FOR_NEXT_STAGE → ARCHIVED | Owner/retention workflow | No active dependency; retention checked | ContentArchived |

The editorial convenience state APPROVED_FOR_NEXT_STAGE is not a substitute for the separate approval record or central authorization. Exact ContentItem/Variant/Version lifecycle mapping and cardinality remain OPEN.

## 5. SM-02 — WorkflowDefinition lifecycle

Owner: Automation & Agent Orchestration. Definition is reusable, versioned configuration, not a running execution.

| State (proposed) | Meaning |
| --- | --- |
| DRAFT | Being authored. |
| VALIDATED | Schema/dependency validation passed. |
| ACTIVE | Eligible for new runs. |
| SUSPENDED | Unavailable for new runs. |
| RETIRED | No longer eligible for new runs; history retained. |

| Transition | Actor / guard | Rule |
| --- | --- | --- |
| DRAFT → VALIDATED | Owner/validator; schema, dependencies and capability refs valid | Record validation evidence. |
| VALIDATED → ACTIVE | Authorized owner; policy controls satisfied | Activation is not execution. |
| ACTIVE → SUSPENDED | Owner/policy; reason recorded | Define in-flight run handling. |
| SUSPENDED → ACTIVE | Owner; cause resolved and validation current | Revalidate after material changes. |
| ACTIVE/SUSPENDED → RETIRED | Owner; new scheduling stopped | Historical runs remain readable. |

Semantic edits create a new immutable definition version. Each WorkflowRun captures the exact definition ID and version.

## 6. SM-03 — WorkflowRun lifecycle

Owner: Automation & Agent Orchestration. One concrete execution of one WorkflowDefinition version.

| State (proposed) | Meaning |
| --- | --- |
| PENDING | Durably created; not started. |
| RUNNING | Orchestration progressing. |
| WAITING | Blocked on dependency, human input or local worker availability. |
| SUCCEEDED | All required completion conditions satisfied. |
| FAILED | Non-recoverable failure under policy. |
| CANCELLED | Deliberately cancelled. |
| NEEDS_RECONCILIATION | Side effect or result uncertain; resolution required. |

| Transition | Guard | Event / evidence |
| --- | --- | --- |
| PENDING → RUNNING | Definition/run allowed; run durable | WorkflowRunStarted; definition version ref |
| PENDING → CANCELLED | Authorized cancellation | WorkflowRunCancelled |
| RUNNING → WAITING | Concrete blocking dependency recorded | WorkflowRunWaiting |
| WAITING → RUNNING | Dependency resolved; policy/scope rechecked | WorkflowRunResumed |
| RUNNING → SUCCEEDED | All required child work terminal; completion policy satisfied | WorkflowRunSucceeded |
| RUNNING → FAILED | Failure non-retryable or recovery exhausted | WorkflowRunFailed; error refs |
| RUNNING → CANCELLED | Authorized cancellation at safe boundary | WorkflowRunCancelled |
| RUNNING → NEEDS_RECONCILIATION | Possible external effect or uncertain result | WorkflowRunReconciliationRequired |
| NEEDS_RECONCILIATION → RUNNING | Evidence supports safe continuation | WorkflowRunReconciled |
| NEEDS_RECONCILIATION → terminal | Evidence supports terminal disposition | Reconciliation record |

OPEN: fan-out/fan-in, optional tasks, compensations and partial-success semantics. A run is not SUCCEEDED merely because its last dispatched job succeeded.

## 7. SM-04 — TaskInstance lifecycle

Owner: Automation & Agent Orchestration. TaskDefinition is reusable specification; TaskInstance is one occurrence. Exact TaskInstance-to-Job cardinality is unresolved.

| State (proposed) | Meaning |
| --- | --- |
| PENDING | Created; prerequisites pending. |
| READY | Prerequisites met; dispatch eligible. |
| RUNNING | Associated job/attempt executing. |
| WAITING | Blocked on dependency, human decision or resource. |
| SUCCEEDED | Task-specific completion condition met. |
| FAILED | Cannot complete under retry/recovery policy. |
| CANCELLED | Deliberately stopped. |
| NEEDS_RECONCILIATION | Uncertain side effect/result. |

| Transition | Guard / rule |
| --- | --- |
| PENDING → READY | Dependencies and input contract validated. |
| READY → RUNNING | At least one associated job durably accepted. |
| RUNNING → WAITING | Blocking dependency/resource recorded. |
| WAITING → READY/RUNNING | Blocker resolved; scope and policy rechecked. |
| RUNNING → SUCCEEDED | Task-specific completion oracle and output validation pass. |
| RUNNING → FAILED | Permanent failure or retry policy exhausted. |
| PENDING/READY/WAITING → CANCELLED | Authorized cancellation and dependent-work policy satisfied. |
| RUNNING → NEEDS_RECONCILIATION | External or irreversible outcome uncertain. |

OPEN: whether one task creates multiple jobs; fan-out/fan-in representation; whether retries belong only to JobAttempt; which aggregate computes task completion.

## 8. SM-05 — Job lifecycle

Owner: Automation & Agent Orchestration. Job is a durable dispatchable unit; its state is distinct from WorkflowRun and TaskInstance.

| State (proposed) | Meaning |
| --- | --- |
| QUEUED | Durably recorded and eligible for dispatch. |
| CLAIMED | Worker atomically claimed under valid lease. |
| RUNNING | Execution started. |
| RETRY_WAIT | Retry scheduled but not claimable yet. |
| SUCCEEDED | Job result contract passed. |
| FAILED | Terminal failure. |
| CANCELLED | Stopped by authorized cancellation. |
| NEEDS_RECONCILIATION | Execution/side-effect result uncertain. |

| Transition | Guard | Behavior |
| --- | --- | --- |
| Created → QUEUED | Schema/idempotency/dependency checks pass | Persist before dispatch. |
| QUEUED → CLAIMED | Worker authenticated, trusted, capable; lease acquired | Associate JobAttempt. |
| CLAIMED → RUNNING | Worker confirms start under current lease generation | Record start evidence. |
| CLAIMED → QUEUED | Claim expires before start and safe requeue allowed | Preserve attempt history. |
| RUNNING → SUCCEEDED | Result schema, ownership and validation pass | Store result refs. |
| RUNNING → RETRY_WAIT | Retryable failure; budget remains | Close current attempt. |
| RETRY_WAIT → QUEUED | Retry eligible; policy still permits | Next claim creates new attempt. |
| RUNNING → FAILED | Permanent failure or retry budget exhausted | Preserve diagnostics. |
| QUEUED/CLAIMED/RETRY_WAIT → CANCELLED | Authorized cancellation; safe boundary | Record actor/reason. |
| RUNNING → NEEDS_RECONCILIATION | Possible side effect or uncertain completion | Do not blindly retry. |
| NEEDS_RECONCILIATION → disposition | Evidence-backed recovery decision | Requeue only if safe and authorized. |

Numeric retry budgets, backoff, timeout and lease values are intentionally unspecified pending workload evidence and owner review.

## 9. SM-06 — JobAttempt and lease lifecycle

| Attempt state (proposed) | Meaning | Rule |
| --- | --- | --- |
| CREATED | Attempt record exists before execution | Append-oriented history. |
| LEASED | Worker holds valid lease | Lease generation/version required. |
| STARTED | Execution began | Bind worker identity. |
| SUCCEEDED | Attempt produced accepted result | Does not automatically complete task/run. |
| FAILED | Attempt failed | Classify failure and retain evidence. |
| EXPIRED | Lease expired / attempt exceeded allowed window | Late result cannot silently win. |
| CANCELLED | Attempt stopped under authorized action | Retain stop evidence. |
| UNKNOWN_OUTCOME | Side effect may have occurred; evidence insufficient | Reconcile before retry. |

- Every retry creates a new JobAttempt; prior attempts are not overwritten.

- Lease renewal is conditional on current lease owner and generation.

- A stale worker cannot renew or complete a superseded lease.

- Late results are rejected or quarantined unless authoritative owner validates them.

- Lease expiry does not prove no side effect occurred.

- Lease generation, clock-skew tolerance, heartbeat and expiry values remain OPEN.

## 10. SM-07 — Worker lifecycle and trust

| State (proposed) | Meaning | Permitted behavior |
| --- | --- | --- |
| REGISTERED | Identity created, not yet trusted | No protected assignment. |
| ACTIVE | Identity/credential valid; capability checks possible | Only eligible bounded assignments. |
| SUSPENDED | Temporarily prevented from new claims | No new claims; in-flight policy applies. |
| REVOKED | Identity/trust explicitly revoked | No new claims/protected execution. |
| RETIRED | Permanently removed from active pool | Historical identity/audit retained. |

| Transition | Guard |
| --- | --- |
| REGISTERED → ACTIVE | Identity proof accepted; credential and capability registration valid. |
| ACTIVE → SUSPENDED | Authorized operator/policy action with reason. |
| SUSPENDED → ACTIVE | Cause resolved; credential, capability and trust revalidated. |
| REGISTERED/ACTIVE/SUSPENDED → REVOKED | Authorized revocation or security incident control. |
| REVOKED → RETIRED | Administrative closure; revocation is not undone. |
| ACTIVE → RETIRED | No active leases or safe-drain/reconciliation satisfied. |

Credential lifecycle is separate: an ACTIVE worker may hold an expired credential. Credential validity must be checked independently at claim and protected execution time. Protocol, TTL, rotation and revocation propagation remain OPEN.

## 11. SM-08 — ArtifactVersion validation and availability

Owner: Asset Management. Artifact is logical identity; ArtifactVersion is immutable bytes plus metadata. Validation/availability is separate from editorial approval.

| State (proposed) | Meaning |
| --- | --- |
| REGISTERED | Metadata created; binary may not be verified. |
| TRANSFER_PENDING | Binary transfer/ingestion in progress. |
| VALIDATING | Integrity and schema/content checks running. |
| AVAILABLE | Integrity and required validation passed. |
| QUARANTINED | Untrusted, malformed, mismatched or policy-blocked. |
| SUPERSEDED | Newer version exists; old version remains addressable. |
| DELETION_PENDING | Deletion/retention workflow queued; policy semantics open. |

| Transition | Guard | Rule |
| --- | --- | --- |
| REGISTERED → TRANSFER_PENDING | Source/manifest and destination established | Transfer record required. |
| TRANSFER_PENDING → VALIDATING | Transfer receipt recorded | Verify checksum. |
| VALIDATING → AVAILABLE | Integrity/schema checks pass | Store validator/version/evidence. |
| VALIDATING → QUARANTINED | Validation fails | Record reason; block downstream use. |
| AVAILABLE → SUPERSEDED | New immutable version and lineage linked | Old bytes remain immutable. |
| QUARANTINED → VALIDATING | Authorized revalidation after remediation | Never flip directly to AVAILABLE. |
| AVAILABLE/SUPERSEDED → DELETION_PENDING | Retention and legal-hold checks pass | Finalization policy remains OPEN. |

Repair/regeneration creates a new ArtifactVersion. Prior version and review evidence remain intact. DELETION_PENDING is not deletion authorization.

## 12. SM-09 — Transfer lifecycle

| State (proposed) | Meaning |
| --- | --- |
| REQUESTED | Transfer intent durably recorded. |
| IN_PROGRESS | Bytes moving/copying. |
| VERIFYING | Destination receipt/checksum verified. |
| COMPLETED | Destination integrity verified. |
| FAILED | Known failure. |
| CANCELLED | Transfer stopped. |
| UNKNOWN | Result uncertain; reconcile. |

| Transition | Guard / rule |
| --- | --- |
| REQUESTED → IN_PROGRESS | Source, destination, scope and authorization valid. |
| IN_PROGRESS → VERIFYING | Copy complete; destination reference available. |
| VERIFYING → COMPLETED | Expected size/checksum/manifest checks pass. |
| IN_PROGRESS/VERIFYING → FAILED | Known permanent failure or policy exhausted. |
| REQUESTED/IN_PROGRESS → CANCELLED | Authorized stop; partial objects handled safely. |
| IN_PROGRESS/VERIFYING → UNKNOWN | Process/connection lost with uncertain destination result. |
| UNKNOWN → verified disposition | Inspect destination and verify evidence first. |

A local process exit alone does not prove transfer completion; destination-side integrity evidence is required.

## 13. SM-10 — Quality evaluation

The accepted ADR-008 vocabulary is fixed. Each evaluation binds to an exact content/artifact version and QA policy version.

| Outcome | Meaning | Downstream effect |
| --- | --- | --- |
| PASS | Required checks passed | Eligible for next policy gates; not approval/authorization. |
| PASS_WITH_WARNINGS | Checks passed with non-blocking warnings | Retain warnings for downstream policy. |
| NEEDS_REVIEW | Evidence insufficient or human judgment required | Hold for review. |
| BLOCKED | Hard blocker detected | Protected action denied; ordinary approval cannot bypass. |

| Evaluation result | Guard | Rule |
| --- | --- | --- |
| PASS | All mandatory checks pass; evidence complete | Record checks and policy version. |
| PASS_WITH_WARNINGS | Mandatory checks pass; only non-blocking warnings remain | Record each warning. |
| NEEDS_REVIEW | Ambiguous/insufficient evidence | Create review requirement. |
| BLOCKED | Hard rights/security/integrity/policy blocker | Enforce hard stop. |
| Re-evaluation | New run for exact version/policy | Create new record; preserve historical outcome. |

A materially changed content or artifact version requires a new or explicitly revalidated quality result. Do not carry PASS forward to changed bytes.

## 14. SM-11 — Rights determination

Canonical CF-20 vocabulary reproduced exactly. Rights are evidence-backed and use-specific.

| Status | Meaning | Permission effect |
| --- | --- | --- |
| UNKNOWN | Rights not established | Fail closed. |
| PENDING_REVIEW | Evidence submitted but undecided | Fail closed / hold. |
| CLEARED | Evidence supports specified use/scope | Satisfies rights prerequisite only for exact use/context. |
| RESTRICTED | Use limited by conditions | Only if restrictions met and separately authorized. |
| EXPIRED | Clearance validity ended | Fail closed pending renewal/review. |
| REVOKED | Prior clearance withdrawn | Fail closed; invalidate dependent assumptions. |
| DENIED | Use explicitly denied | Protected use denied. |

- Bind rights to asset/source, intended use, territory/platform/destination where relevant, time window, evidence and policy version.

- Rights for one use do not imply rights for another.

- Expiry/revocation checked at protected execution time.

- Legacy PENDING_VERIFICATION and PROHIBITED are not silently aliased; migration/interpretation needs explicit decision.

## 15. SM-12 — Review and approval

Canonical CF-21 vocabulary reproduced exactly. Approval is attributable and exact-version bound.

| Outcome | Meaning | Effect |
| --- | --- | --- |
| APPROVED | Reviewer accepts exact reviewed scope/version | Satisfies approval prerequisite only within scope/validity. |
| REJECTED | Reviewer rejects exact scope/version | No protected permission. |
| CHANGES_REQUESTED | Revision required | New version/review cycle as policy defines. |
| EXPIRED | Approval validity ended | No longer satisfies current prerequisite. |
| REVOKED | Approval withdrawn | Dependent action re-evaluated. |

| Decision / transition | Guard |
| --- | --- |
| Review opened | Reviewer role/access valid for exact version. |
| Decision recorded | Actor authenticated; reason/evidence/version recorded. |
| Approval expired | Validity window or policy condition reached. |
| Approval revoked | Authorized revocation role and reason. |
| New version created | Old approval remains bound to old version; new version requires review. |

Reviewer-role matrix, expiry durations, delegation, appeal/re-review and conditional approval remain OPEN.

## 16. SM-13 — Central authorization decision

CF-22 selects centralized authorization (Option A). Authorization is a decision for a specific action at a specific time, not a lifecycle boolean on content.

| Conceptual state | Meaning | Enforcement |
| --- | --- | --- |
| NOT_EVALUATED | No decision exists | Default deny. |
| DENIED | Policy evaluation denied | Protected action prohibited. |
| AUTHORIZED | Current decision permits exact bound action | Proceed only while bindings valid. |
| EXPIRED | Validity window ended | Deny; re-evaluate. |
| REVOKED | Decision withdrawn | Deny; re-evaluate. |
| INVALIDATED | Bound input changed | Deny; obtain fresh decision. |

| Required binding | Execution-time check |
| --- | --- |
| Action | Requested operation matches exact action. |
| Resource/version | Target and immutable version match. |
| Destination | Exact platform/account/destination matches. |
| Policy version | Current policy still permits action. |
| Time validity | Decision remains within validity window. |
| Approval | Required approval is current and exact-version bound. |
| Rights | Use-specific rights remain applicable. |
| Quality | BLOCKED or policy blocker prevents action. |
| Emergency pause | Current pause state permits execution. |
| Actor/worker capability | Executing identity is permitted for this action. |

Generic approved=true, UI button state, cached token or prior success is never sufficient authorization. Emergency pause scope, authority, propagation and in-flight behavior remain owner decisions.

## 17. SM-14 — Distribution and external operation

Distribution Studio owns the operation record; central authorization owns permission. External side-effect status is distinct from job execution status.

| State (proposed) | Meaning | Safe behavior |
| --- | --- | --- |
| PREPARED | Package and exact versions assembled | No side effect. |
| READY | Package and prerequisites validated | Await central authorization. |
| AUTHORIZED | Central decision bound to operation | Recheck immediately before execution. |
| SUBMITTING | External request in progress | Persist request/correlation details. |
| CONFIRMED | External evidence confirms result | Record remote reference/evidence. |
| REJECTED | External platform definitively rejected | Record response; retry only if safe. |
| UNKNOWN_OUTCOME | May have succeeded; confirmation missing | Reconcile; no blind retry. |
| CANCELLED | Stopped before irreversible action or safely stopped | Record boundary/reason. |
| REVOKED_OR_BLOCKED | Policy/authorization no longer permits | Do not submit/continue. |

| Transition | Guard / evidence |
| --- | --- |
| PREPARED → READY | Integrity, rights, QA, approval and destination checks pass. |
| READY → AUTHORIZED | Central allow for exact operation binding. |
| AUTHORIZED → SUBMITTING | Recheck expiry/revocation, pause, exact version and destination. |
| SUBMITTING → CONFIRMED | Remote response/evidence confirms intended result. |
| SUBMITTING → REJECTED | Remote platform definitively rejects. |
| SUBMITTING → UNKNOWN_OUTCOME | Timeout/loss after possible side effect. |
| UNKNOWN_OUTCOME → CONFIRMED/REJECTED | Remote reconciliation establishes outcome. |
| PREPARED/READY/AUTHORIZED → CANCELLED/BLOCKED | Authorized cancellation, policy change, revoked rights/approval or pause. |

Automatic public publishing remains disabled pending separate policy. A distribution job marked SUCCEEDED does not prove remote publication; the external operation record governs that outcome.

## 18. SM-15 — Quarantine disposition

| State (proposed) | Meaning |
| --- | --- |
| QUARANTINED | Withheld due to validation/security/rights/policy concern. |
| UNDER_INVESTIGATION | Cause/evidence assessed. |
| REMEDIATION_REQUIRED | Corrective action required. |
| REVALIDATION_PENDING | Remediation submitted; checks rerun. |
| RELEASED | Authorized release after checks. |
| REJECTED | Permanently rejected for intended workflow/use. |

| Transition | Guard |
| --- | --- |
| QUARANTINED → UNDER_INVESTIGATION | Authorized reviewer/validator takes ownership. |
| UNDER_INVESTIGATION → REMEDIATION_REQUIRED | Cause and remediation documented. |
| REMEDIATION_REQUIRED → REVALIDATION_PENDING | New version/evidence submitted; history retained. |
| REVALIDATION_PENDING → RELEASED | Checks pass and authorized release recorded. |
| REVALIDATION_PENDING → QUARANTINED | Validation fails or uncertainty remains. |
| UNDER_INVESTIGATION/REVALIDATION_PENDING → REJECTED | Evidence supports rejection; reason recorded. |

Quarantine release must not be a direct status flip by the worker that produced the failed artifact. Release actor and evidence should be independent of the failed check where feasible.

## 19. Cross-machine dependencies and non-inheritance

| Downstream operation | Prerequisites | Never inherit automatically |
| --- | --- | --- |
| Content review | Exact immutable content version; required metadata | Prior version review outcome. |
| Artifact usable | Transfer complete; integrity/validation pass; not quarantined | Storage presence or upload completion. |
| Quality pass | Exact version and policy-bound evaluation | Approval or rights clearance. |
| Approval gate | Authorized reviewer; exact version; current decision | Central authorization. |
| Rights gate | Evidence and intended use match | Rights for another use/destination. |
| Worker job claim | Trusted worker; valid credential; capability; lease | Permission to publish/unrelated resources. |
| Distribution execution | Exact package/version/destination; QA, rights, approval, central authorization, pause check | Authorization for another action/version/destination/time. |
| External success | Remote evidence supports outcome | Local process exit or command ACCEPTED. |

## 20. Forbidden transitions and hard stops

| Unsafe behavior | Required response |
| --- | --- |
| Edit content/artifact version in place after review | Create new immutable version; rerun required checks. |
| Worker directly changes canonical governance state | Reject write; require owner-domain command. |
| BLOCKED QA bypassed by ordinary approval | Deny protected action; resolve blocker and re-evaluate. |
| UNKNOWN/PENDING_REVIEW rights treated as CLEARED | Fail closed; require evidence/review. |
| Approval treated as authorization | Require central authorization. |
| Expired/revoked authorization reused | Deny and re-evaluate. |
| Event receipt treated as permission | Evaluate command and policy separately. |
| Stale attempt overwrites newer result | Reject/quarantine result; preserve history. |
| Unknown external outcome blindly retried | Reconcile destination first. |
| Quarantined artifact enters normal flow | Block until authorized release. |
| Definition edited without version change | Create new immutable definition version. |
| Remote success inferred from local success | Keep external outcome unconfirmed. |

## 21. Recovery, compensation and manual intervention

- Recovery identifies the authoritative state owner before changing state.

- Manual intervention is a privileged, attributable command with reason/evidence, not direct database editing.

- Compensation is a new explicit operation; it does not delete historical events or attempts.

- Unknown external outcomes require destination reconciliation before retry or compensation.

- Event replay may rebuild projections but must not repeat protected external side effects by default.

- Emergency pause and revocation are checked at the protected action boundary.

- Runbooks, RTO/RPO, retry budgets, lease durations and retention periods remain open pending topology/workload decisions.

## 22. Acceptance and failure-injection scenarios

| Test ID | Scenario | Expected result |
| --- | --- | --- |
| SMT-01 | Transition with stale state_version | CONFLICT; no overwrite. |
| SMT-02 | Unauthorized actor requests transition | REJECTED; audit evidence. |
| SMT-03 | Consumer receives duplicate event | Deduplicated; no duplicate effect. |
| SMT-04 | Content version changes after approval | Old approval stays bound to old version. |
| SMT-05 | Definition changes while run active | Run retains captured definition version. |
| SMT-06 | Required sibling job fails | Run not SUCCEEDED unless approved partial-success semantics allow. |
| SMT-07 | Expired lease worker returns late result | Late result cannot overwrite newer attempt. |
| SMT-08 | Worker credential revoked before claim | Claim denied. |
| SMT-09 | Artifact checksum mismatch | Quarantine; not available. |
| SMT-10 | Artifact repaired | New ArtifactVersion; old remains immutable. |
| SMT-11 | QA BLOCKED with approval APPROVED | Protected action denied. |
| SMT-12 | Rights PENDING_REVIEW | Protected use denied/held. |
| SMT-13 | Approval expires before distribution | Authorization denied/re-evaluation required. |
| SMT-14 | Authorization revoked before execution | Execution-time check denies. |
| SMT-15 | Emergency pause before submit | Protected action denied per approved pause semantics. |
| SMT-16 | Publish times out after possible success | UNKNOWN_OUTCOME; reconcile before retry. |
| SMT-17 | Transfer exits but checksum differs | Not COMPLETED; validation fails. |
| SMT-18 | Quarantined asset submitted to creation | Rejected by eligibility check. |
| SMT-19 | Unsupported event schema version | Controlled rejection/quarantine. |
| SMT-20 | Replay historical distribution event | Projection may rebuild; no side effect repeated. |

Evidence for each test: test ID; schema/state-machine version; fixture/entity IDs; command/event/correlation IDs; actor; expected and actual transition; timestamps; logs; policy/evidence references; pass/fail; reviewer. Independent QA must be able to reproduce results.

## 23. Owner-reserved decisions and open values

| ID | Decision required | Why open | Closure evidence |
| --- | --- | --- | --- |
| SMO-01 | Approve exact domain lifecycle enums | Several lifecycle enums are proposed, not accepted. | Owner-reviewed state catalogue. |
| SMO-02 | Confirm ContentItem/Variant/Version boundaries | Identity separation accepted; lifecycle/cardinality open. | ERD and examples. |
| SMO-03 | Confirm workflow/task/job cardinalities | Fan-out/fan-in and completion semantics unresolved. | Orchestration examples/tests. |
| SMO-04 | Confirm terminal/cancellation semantics | Safe stop depends on operation type. | Per-domain cancellation matrix. |
| SMO-05 | Set lease/retry/timeout/heartbeat values | No numeric values accepted. | Workload assumptions and tests. |
| SMO-06 | Confirm credential and revocation lifecycle | Protocol/propagation open. | Threat model and revocation tests. |
| SMO-07 | Confirm artifact deletion/retention/legal hold | Policy/provider not selected. | Owner-approved data lifecycle policy. |
| SMO-08 | Confirm emergency pause scope/authority | High-impact control remains open. | Explicit pause policy and tests. |
| SMO-09 | Confirm reviewer roles and expiry | Vocabulary accepted; role/time rules open. | Role matrix and decision schema. |
| SMO-10 | Confirm rights evidence and use taxonomy | Use-specific principle accepted; exact evidence rules open. | Rights matrix and negative cases. |
| SMO-11 | Confirm destination reconciliation | Unknown outcome requires adapter protocol. | Destination-specific tests. |
| SMO-12 | Confirm quarantine release authority | Exact roles not frozen. | Role matrix and audit test. |
| SMO-13 | Confirm event names/schema versions | Envelope known; schema bundle open. | Versioned event catalogue. |
| SMO-14 | Confirm state ownership registry | Logical owners mapped; aggregate registry open. | Owner registry and write-boundary tests. |

## 24. Freeze readiness checklist

| Gate | Evidence required | Current disposition |
| --- | --- | --- |
| Inventory | Every stateful entity/dimension has named owner | Candidate inventory; owner confirmation pending |
| Vocabularies | Exact enums and terminal semantics | QA/rights/approval accepted; other enums proposed |
| Transitions | Allowed edges, guards, actors, events and rejection behavior | Candidate matrices; review pending |
| Concurrency | State version and stale-write behavior | Rule included; implementation proof pending |
| Event contract | Committed fact and schema version | Envelope carried forward; exact schemas open |
| Authorization | Exact action/resource/version/destination/policy/time | Central model included; emergency pause open |
| Recovery | Unknown outcomes, replay, compensation, manual intervention | Principles included; runbooks/thresholds open |
| Acceptance | Positive, negative, concurrency and failure tests | 20 scenarios; execution evidence pending |
| Owner freeze | Explicit approval of this catalogue version | NOT FROZEN |
| Implementation authorization | Separate scope and permitted operations | NOT GRANTED |

## 25. Implementation handoff boundaries

This catalogue does not authorize repository edits, migrations, project test execution, agent execution, deployment, paid services, production generation, uploads or publishing.

- WP-1: implement canonical entity/version ownership and persistence constraints before lifecycle transitions.

- WP-2: implement durable workflow/job/attempt state and outbox/inbox without collapsing run/task/job/attempt.

- WP-3: implement worker trust, credential validity and capability checks before worker claims are trusted.

- WP-4: implement immutable ArtifactVersion, transfer validation and quarantine before downstream use.

- WP-5: implement accepted QA/rights/approval vocabularies and central authorization before protected actions.

- WP-6: test cross-machine transitions, stale writes, replay, late results, unknown external outcomes and recovery.

## Appendix A — Source basis and interpretation

Source basis identified in the P0 reconciliation series: Artifact 08 Implementation Reference / Accepted Contract Decisions 1.0; Artifact 08 Consolidated Owner Decision Record / Contract Freeze Closure 1.0; Artifact 08 Contract Reconciliation & Freeze Candidate 1.1; Canonical Data Dictionary & Entity Ownership Registry 1.0; API & Event Contract Standard 1.0; Unified Lifecycle & State Transition Standard 1.0; Module-to-Contract Traceability Matrix 1.0; Batch 15 Source Reconciliation & Contract Closure Dossier; Batch 16 Domain & Interface Contract Closure Pack.

Accepted CF-20 and CF-21 vocabularies and ADR-008 quality outcomes are reproduced as accepted. Other detailed lifecycle enums are proposed candidates for owner review, not accepted owner decisions. Artifact 08 v1.1 supplements but does not supersede accepted v1.0 owner decision/reference records. Formal contract freeze remains pending.

## Appendix B — Glossary

| Term | Definition |
| --- | --- |
| State machine | Domain-owned model of states, permitted transitions, guards and emitted facts. |
| Transition | Committed change from one state to another. |
| Guard | Condition that must hold before transition acceptance. |
| State version | Monotonic version used to detect stale writes and preserve ordering. |
| Terminal state | State from which no ordinary forward transition is allowed. |
| Attempt | One bounded execution instance of a durable job. |
| Lease | Time-bounded claim/ownership of a job attempt. |
| Unknown outcome | Side effect may have occurred but evidence cannot confirm it. |
| Reconciliation | Evidence-based resolution against authoritative system or destination. |
| Compensation | New explicit corrective operation preserving historical facts. |


## Source document metadata (preserved from DOCX)

- **Header:** NEXTDECODE CONTENT OS  |  P0 STATE & LIFECYCLE CONTRACT SERIES
- **Footer:** Detailed state-machine candidate • Owner freeze pending • Implementation not authorized

