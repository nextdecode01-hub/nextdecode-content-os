NEXTDECODE CONTENT OS

# P0 Batch 10
WP-6 Vertical-Slice Integration, Recovery & Acceptance

Integration design working pack • 01 November 2026

Purpose: define a bounded P0 vertical slice proving WP-1 through WP-5 operate together under normal, failure and governance-blocked conditions. This is an integration/acceptance design candidate only. It does not authorize repository changes, migrations, runtime execution, agent assignments, deployment, paid services, production generation, uploads or publishing.

## 1. Status and use

| Label | Meaning |
| --- | --- |
| ACCEPTED DIRECTION | Recorded owner-accepted architecture decision or invariant. |
| DESIGN CANDIDATE | Proposed integration behavior requiring source reconciliation. |
| SOURCE REQUIRED | Exact field, event, state, policy or test oracle not verified in authoritative source set. |
| OWNER DECISION | Genuinely owner-reserved choice; no inferred approval. |
| NOT AUTHORIZED | No implementation or external execution is permitted. |

Exact original CF wording and full source inventory remain incomplete as recorded in Batch 04. WP-6 does not redefine WP-1 to WP-5; it verifies their boundaries when connected.

## 2. WP-6 mission and boundaries

Demonstrate one end-to-end NEXTDECODE content workflow through the shared control plane and bounded specialist worker, with durable state, scoped artifacts, verified worker trust, central governance and recoverable execution.

| WP-6 owns | WP-6 does not own |
| --- | --- |
| Integration topology and contract compatibility proof | Rewriting domain model (WP-1) |
| Vertical-slice scenario and end-to-end test oracle | Replacing workflow/job semantics (WP-2) |
| Worker trust integration proof | Redesigning worker identity/credentials (WP-3) |
| Artifact transfer/integrity integration proof | Selecting/provisioning storage provider (WP-4) |
| Governance gate/no-bypass integration proof | Changing policy/rights rules without WP-5/owner approval |
| Recovery, reconciliation and release evidence | Production deployment or automatic publishing |

## 3. Governing integration invariants

- One authoritative owner per canonical entity; no competing IDs or shadow state stores.

- ContentItem is the shared editorial identity; ContentVariant is a format/platform/language/treatment derivative.

- Workflow, execution, review, approval, authorization and distribution states remain separate.

- At-least-once delivery is assumed; idempotency and attempt traceability are mandatory.

- Central authorization is authoritative; adapters and workers cannot bypass it.

- Unknown, missing or ambiguous rights, approval or authorization fail closed for protected actions.

- Artifacts are immutable/versioned and integrity checked; repair creates a new version.

- Worker identity is independent of host; declared, verified, available and authorized capabilities remain distinct.

- Approval is exact-version and purpose-bound; it is not authorization or proof of external success.

- Local-only work waits safely if its local worker is unavailable; no paid/cloud fallback is implied.

- Human approval remains required before critical publishing actions; automatic public publishing stays disabled pending separate policy.

- Existing Python/FFmpeg Shorts Studio remains a bounded specialist engine, not something to replace wholesale.

## 4. Proposed P0 vertical slice

Scenario: create and review a NEXTDECODE short-form content item using controlled research inputs, generate a draft/render through the existing Shorts Studio adapter, register and validate outputs, complete quality/rights review, and stop at a human-approved pre-distribution boundary. Actual upload/public publishing is outside this slice.

| Stage | Action | Package / system | Required evidence |
| --- | --- | --- | --- |
| 1 Intake | Create ContentItem and ContentVariant with immutable IDs/versions | WP-1 | Canonical IDs, ownership and version refs |
| 2 Research | Attach source references and claim/evidence records | Research modules + WP-5 contract | Source provenance and claim support |
| 3 Plan | Create workflow instance bound to definition and content version | WP-1/WP-2 | Workflow ID, definition version, target ref |
| 4 Authorize | Check permission to dispatch protected work | WP-5 | Central policy decision and scope |
| 5 Schedule | Persist job/outbox event and deliver queue reference | WP-2 | Job ID, idempotency key, outbox/inbox trace |
| 6 Select worker | Choose trusted, verified, available worker | WP-2/WP-3 | Worker ID, capability version, availability |
| 7 Execute | Run bounded Shorts Studio operation via adapter | Shorts Studio + WP-2/3 | Attempt, logs, build/toolchain, outputs |
| 8 Register | Register script, audio, video, captions and assets | WP-4 | Artifact IDs, hashes, sizes, lineage |
| 9 Validate | Verify integrity, media properties and required checks | WP-4/WP-5 | Version-bound validation results |
| 10 Review | Evaluate claims, rights, quality and exact-version approval | WP-5 | QA outcome, rights evidence, approval |
| 11 Hold | Stop at pre-distribution decision boundary | WP-2/WP-5 | No upload/publish call; held state/evidence |

This vertical slice proves the workflow through a controlled pre-distribution boundary. It does not publish, upload or create a public side effect.

## 5. Integration topology and trust boundaries

| Boundary | Owner(s) | Integration rule |
| --- | --- | --- |
| Control plane ↔ relational store | WP-1 | Shared state authoritative; no shadow canonical store. |
| Workflow ↔ queue | WP-2 | Durable job state, outbox/inbox, at-least-once delivery. |
| Scheduler ↔ worker registry | WP-2/WP-3 | Verified capability and availability inform selection; authorization separate. |
| Worker ↔ sandbox | WP-3 | Bounded filesystem, network, credential and artifact scope. |
| Worker ↔ artifact service | WP-3/WP-4 | Short-lived scoped handles; exact version; integrity checked. |
| Workflow ↔ governance | WP-2/WP-5 | Central policy decision before protected actions. |
| Shorts Studio ↔ adapter | Existing engine + WP-2/3/4 | Preserve specialist engine; bounded inputs/outputs; no bypass. |
| Artifact ↔ review/approval | WP-4/WP-5 | Review/approval bound to exact immutable version and purpose. |
| Distribution ↔ external platform | WP-5/WP-6 | Outside P0 slice; no action without separate authorization. |

## 6. Contract compatibility matrix

| Producer | Consumer | Contract elements to verify | Failure if incompatible |
| --- | --- | --- | --- |
| WP-1 | WP-2 | Canonical IDs, versions, job/workflow persistence, state separation | Duplicate identity/inconsistent state |
| WP-1 | WP-3 | Worker refs, ownership and audit model | Untraceable worker identity |
| WP-1 | WP-4 | Artifact/version metadata, retention and lineage | Orphaned artifacts |
| WP-1 | WP-5 | Review, approval, rights, policy and audit refs | Unbound approval/unauditable decision |
| WP-2 | WP-3 | Claim/lease, assignment, attempt, cancellation, heartbeat | Stale worker updates |
| WP-2 | WP-4 | Artifact input/output refs and transfer completion | Missing/duplicate registration |
| WP-2 | WP-5 | Authorization checkpoints, block/hold and reconciliation | Protected work dispatched without permission |
| WP-3 | WP-4 | Scoped credential/handle and transfer session | Cross-job access |
| WP-4 | WP-5 | Integrity, quarantine, lineage and rights evidence | Invalid artifact passes governance |
| WP-5 | WP-6 | Quality, approval, authorization and no-bypass oracle | False release readiness |

## 7. End-to-end acceptance scenarios

| ID | Scenario | Expected result | Evidence |
| --- | --- | --- | --- |
| E2E-01 | Happy path through pre-distribution hold | One content item flows through research, job, worker, artifact, QA and approval; no external publishing | Correlated IDs, state history, hashes, review/approval |
| E2E-02 | Duplicate job/outbox delivery | No duplicate logical side effect; attempts traceable | Idempotency/inbox and attempt history |
| E2E-03 | Worker lost during render | Lease expires; stale worker fenced; safe retry/reconciliation | Heartbeat, lease generation, attempts |
| E2E-04 | Local worker unavailable for local-only task | Task waits; no remote/paid fallback | Queue state; no remote dispatch |
| E2E-05 | Artifact checksum mismatch | Artifact quarantined; workflow cannot advance | Integrity check and blocked transition |
| E2E-06 | Rights missing or ambiguous | Protected step blocked | WP-5 denial and audit |
| E2E-07 | Quality hard blocker plus approval attempt | BLOCKED remains; approval cannot bypass | QA outcome and denied transition |
| E2E-08 | Approval refers to prior content version | Current version remains unapproved | Version mismatch evidence |
| E2E-09 | Central authorization denied | No protected dispatch or adapter call | Policy decision and no side effect |
| E2E-10 | Authorization revoked during task | Protected step stops or safely reconciles | Revocation event and attempt state |
| E2E-11 | External operation timeout (test stub only) | UNKNOWN_OUTCOME; reconcile before replay | Stub receipt lookup and reconciliation |
| E2E-12 | Restart with queued/leased jobs | Recovery preserves state and resolves lease classes | Before/after state and recovery log |
| E2E-13 | Direct publishing adapter bypass attempt | Blocked; external call not made | Negative test and audit event |
| E2E-14 | Artifact repair after corruption | New immutable version; old evidence retained | Version/hash/repair history |

## 8. Failure injection and recovery plan

| Failure point | Injected condition | Required behavior | Do not claim |
| --- | --- | --- | --- |
| After DB commit, before outbox publish | Process terminates | Outbox later publishes stable event; job remains durable | Exactly-once delivery |
| After queue delivery, before claim | Duplicate/lost acknowledgement | Inbox/delivery reconciliation prevents duplicate logical work | No duplicate messages |
| After worker lease, before start | Worker crashes | Lease expires; attempt remains traceable; safe requeue after fencing | Prior worker definitely stopped |
| During render | Worker interruption | Attempt traceable; partial outputs staged/quarantined | Partial output is valid |
| After artifact upload, before metadata finalization | Connection lost | Reconcile object/hash and complete or quarantine | Upload definitely failed |
| After external request submission | Timeout/no receipt | UNKNOWN_OUTCOME and read-only reconciliation | Safe blind retry |
| During authorization revocation | Policy changes mid-job | Re-check protected checkpoint; stop/reconcile | Prior access is permanent |
| During migration (only if separately authorized) | Process interrupted | Use tested recovery/restore boundary | Rollback automatically safe |

## 9. Independent state and evidence reconciliation

| Dimension | Evidence | Integration check |
| --- | --- | --- |
| Content | ContentItem/Variant version and editorial state | Does not change merely because job succeeds. |
| Workflow | Workflow instance and stage events | Advances only after required evidence. |
| Execution | Job/attempt outcome including UNKNOWN_OUTCOME | Worker exit code alone is not business success. |
| Artifact | Artifact version, integrity and quarantine status | Only validated exact versions enter governed use. |
| Quality | PASS / PASS_WITH_WARNINGS / NEEDS_REVIEW / BLOCKED | Hard blockers remain blocking. |
| Review/approval | Reviewer and exact-version approval | Stale/wrong-purpose approval rejected. |
| Authorization | Central decision, policy version and scope | Explicit valid allow at protected boundary. |
| Distribution | Intent, attempt and confirmed external outcome | Pre-distribution slice has no distribution attempt. |

## 10. Observability and trace correlation

- Correlate workflow, job, attempt, worker, artifact, review, approval, authorization and audit events.

- Preserve parent-child chain: workflow → stage/job → attempt → artifact/version → review/approval → future distribution intent.

- Record event time and ingestion/observation time distinctly where needed.

- Keep telemetry separate from authoritative business state.

- Redact credentials, signed URLs, secrets and sensitive media content.

- Capture test run ID, code/build identity, environment, configuration, source contract version and test oracle version.

- Record recovery actions and operator dispositions as attributable events.

- Do not infer success from missing error logs or process exit alone.

## 11. Release and evidence gates

| Gate | Required proof | Current status |
| --- | --- | --- |
| G0 Source authority | CF wording, data dictionary, lifecycle, API/event and WP specs reconciled | NOT READY |
| G1 Contract freeze | Cross-WP semantics consistent; owner approves exact version | NOT READY |
| G2 WP-1 | Schema/model, identity, version and audit tests pass | NOT VERIFIED |
| G3 WP-2 | Outbox/inbox, idempotency, lease, retry and recovery tests pass | NOT VERIFIED |
| G4 WP-3 | Identity, capability, credential scope and revocation tests pass | NOT VERIFIED |
| G5 WP-4 | Integrity, transfer, quarantine, lineage and access tests pass | NOT VERIFIED |
| G6 WP-5 | Rights, blockers, exact-version approval, central auth and no-bypass tests pass | NOT VERIFIED |
| G7 WP-6 | Happy path and critical negative/failure paths pass with correlated evidence | NOT RUN |
| G8 Independent QA | Read-only QA reviews exact build/evidence and records disposition | PENDING |
| G9 Owner release authorization | Owner approves exact version and external-action scope | NOT REQUESTED |

A gate does not pass merely because a design document exists. It requires implementation evidence tied to exact build, environment, scope and test oracle.

## 12. Release-readiness decision rules

| Outcome | When appropriate | Meaning |
| --- | --- | --- |
| READY FOR OWNER REVIEW | Source/design and test evidence assembled; no critical ambiguity | May be reviewed; not deployment authorization. |
| READY FOR LIMITED INTERNAL TEST | Owner explicitly authorizes bounded test scope and safety prerequisites pass | Only that scope may run. |
| BLOCKED | Critical source, rights, authorization, integrity, recovery or QA gate fails | Do not proceed until remediated and retested. |
| INCONCLUSIVE | Evidence incomplete, environment differs or outcome unknown | Not a pass; obtain valid evidence. |
| RELEASE APPROVED | Owner approves exact version/scope after evidence review | Only approved scope/actions authorized. |

## 13. Scope control and repository preservation

- Project path previously reported: /home/demon/shorts_studio. Historical snapshot reported 23 tracked modified files and 56 untracked paths; preserve all such work.

- Do not reset, revert, stash, clean, delete, overwrite, rename, broadly stage, commit, push, change branches or remotes without explicit approval.

- Preserve existing Shorts Studio as bounded specialist engine; integrate through adapter, do not replace wholesale.

- No migrations, code edits, tests, agent runs or deployment under this design pack.

- No paid providers, cloud activation, public uploads or publishing.

- Do not repeat repository inventory checks merely to progress this document workflow.

- Qoder owns Phase 11 engineering; OpenCode owns Phase 10 engineering/closure; Kilo is independent read-only QA. No agent assignment is authorized.

## 14. WP-6 work order — draft only

| Field | Draft definition |
| --- | --- |
| Objective | Integrate WP-1 to WP-5 and prove one bounded content workflow through a pre-distribution human-approved hold. |
| Preconditions | Source reconciliation and contract freeze; approved WP contracts; separate implementation authorization; preserved repository baseline. |
| Allowed after authorization | Approved adapters/glue, integration tests, failure injection, recovery and evidence capture within file allowlist. |
| Forbidden without separate approval | Public publishing, paid services, provider activation, destructive migrations, broad refactors/Git operations, agent self-expansion. |
| Outputs | Vertical-slice implementation, end-to-end tests, recovery evidence, traceability matrix, independent QA report and owner release brief. |
| Exit criteria | Happy path and critical negative/failure paths pass; no critical invariant violation; independent QA disposition; owner reviews evidence. |
| Rollback boundary | Safe stop, queue pause, credential revocation and artifact quarantine validated before external exposure. |

## 15. Critical unresolved items before freeze

| Gap | Why it matters | Closure evidence |
| --- | --- | --- |
| Exact CF wording gaps | Summaries do not replace governing contract text | Artifact 08 rows captured verbatim with source locators. |
| Full authoritative source inventory | Partial folder visibility cannot prove completeness | Inventory reconciled against original source location. |
| ODR-22 register reconciliation | Avoid treating provisional grouping as authoritative | Complete ODR master register inspected and disposition recorded. |
| X-12 status vocabulary precedence | Avoid mixing decision/design/implementation/evidence/QA status | Source precedence reviewed and owner disposition recorded. |
| Exact API/event/state schemas | Integration tests need stable contracts | Versioned contract definitions and compatibility matrix. |
| Retention/legal hold policy | Artifact lifecycle/deletion require policy | Authoritative retention/legal-hold requirements. |
| Historical implementation reports | Historical test counts are not fresh runtime evidence | Fresh scoped tests/recovery evidence after authorization. |
| Independent Kilo QA | Owners cannot self-certify independent acceptance | Read-only QA report tied to exact build/evidence. |

## 16. Owner decision and authorization boundary

Accepted architecture decisions and CF outcomes remain recorded; this pack does not ask the owner to reapprove them. Owner action is required only for genuinely reserved decisions, formal contract freeze, implementation authorization and external/production release.

| Action | Required approval |
| --- | --- |
| Approve design candidate | Owner review of exact version; does not authorize implementation. |
| Freeze P0 contract | Explicit owner approval of source-reconciled consolidated contract version. |
| Authorize implementation | Separate explicit scope, file allowlist, permitted operations, tests and rollback boundary. |
| Authorize paid/provider activation | Separate explicit cost/provider decision. |
| Authorize deployment | Separate explicit environment/release approval. |
| Authorize production generation/upload/publishing | Separate explicit action approval; human and central policy gates still apply. |

## 17. Readiness decision

| Question | Current answer |
| --- | --- |
| Are WP-1 through WP-6 design candidates prepared? | Yes — design packages exist for all six work packages. |
| Are all original source contracts verified? | No — Batch 04 source gaps remain. |
| Is P0 contract frozen? | No. |
| Has WP-6 been implemented or tested? | No — this is acceptance design, not runtime evidence. |
| Is independent QA complete? | No — pending. |
| Is implementation or release authorized? | No. |
| Next sensible step | Consolidate all six WP candidates into one source-traceable P0 integration contract, close source gaps, and prepare owner freeze review. |

Recommended next batch: P0 Master Integration Blueprint & Owner Freeze Review — one consolidated document linking all six WPs, interfaces, dependencies, invariants, acceptance gates, unresolved source gaps and decisions required for formal freeze.

END OF BATCH 10


## Source document metadata (preserved from DOCX)

- **Footer:** NEXTDECODE • P0 integration design candidate • Not frozen • Not implementation authorization

