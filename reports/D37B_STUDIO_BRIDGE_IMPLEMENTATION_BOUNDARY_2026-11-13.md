# D37-B — Shorts Studio Bridge: Exact Implementation Boundary

**Date:** 2026-11-13  
**Status:** BOUNDARY DEFINED — IMPLEMENTATION NOT AUTHORIZED BY SOURCE DOCUMENTS  
**Inputs:** D37-A reconciliation; accepted P0 architecture baseline; Artifact 08 accepted-contract reference; Artifact 10 owner review/authorization pack; Artifact 09 coding-agent handoff; WP2–WP6 design candidates; Contract 10/X-01 reconciliation.

## 1. Decision

D37-B does **not** authorize implementation of a canonical Studio adapter, schema, API, migration, workflow, worker registry, artifact registry, approval service, or publishing path.

The smallest safe engineering boundary is a **future, non-authoritative local adapter seam** around existing Shorts Studio specialists. It may be specified now, but it must not be implemented as a canonical WP2–WP6 integration until the relevant contracts are owner-reviewed/frozen and a specific implementation authorization is recorded.

This is not a request to redesign Shorts Studio. The existing Python/FFmpeg engine remains the specialized production engine behind a bounded adapter (Artifact 08, project-wide invariant §2.4). No wholesale replacement is in scope.

## 2. Authority check — why implementation stops here

The current source-of-truth documents are explicit:

| Source | Current status / rule | Consequence |
|---|---|---|
| Artifact 10 Owner Review & Authorization Pack | Owner decision pack awaiting review; explicitly says repository inspection, Git operations, code/config changes, agent assignment, infrastructure, deployment, production generation, upload and publishing are not authorized (§§1, 8–9, 20, 22, 357–364). | Does not grant implementation authority. |
| Artifact 09 Coding Agent Handoff Specification | Draft handoff, not execution authorization; detailed contract freeze pending explicit owner approval; implementation authorization not granted (§§1, 2.2, 18). | Agents cannot convert design candidates into schemas or code. |
| WP2 v0.1 | Design candidate; owner review required; implementation not authorized (§§1–2). | No canonical workflow/job adapter contract can be assumed. |
| WP3 v0.1 | Design candidate; owner review required; implementation not authorized (§§1–3). | No canonical worker identity, assignment, lease or fencing integration can be assumed. |
| WP4 v0.1 | Design candidate; owner review required; implementation not authorized (§§1–3). | No canonical Artifact/ArtifactVersion registration or transfer can be implemented. |
| WP5 v0.1 | Design candidate; owner review required; implementation not authorized (§§1–3). | No canonical review/approval/authorization API can be assumed. |
| WP6 v0.1 | Design candidate; validation design only; implementation/tests not authorized (§§1–3). | No end-to-end acceptance claim or test execution. |
| Contract 10/X-01 | Working source reconciliation; contract freeze and implementation authorization not granted (§§1, 9, 11). | Entity vocabulary, cardinalities and ownership boundaries remain unresolved. |

Accepted ADR/CF decisions establish architectural direction, not implementation permission. Artifact 08 also explicitly separates accepted contract decisions from implementation authorization.

## 3. Safe boundary for the future adapter

### In scope for a later, specifically authorized increment

1. Preserve the existing research and script specialists as bounded implementation capabilities.
2. Preserve the existing Shorts Studio engine; invoke it only through a versioned, bounded adapter interface once approved.
3. Keep local autonomy identifiers, plan/task records, run IDs and artifact IDs in their own namespace.
4. Preserve exact local input/output provenance and hashes as local execution evidence.
5. Return a typed result to the owning canonical control-plane boundary; do not write another domain's authoritative state.
6. Keep all consequential side effects disabled. Human review, approval and centralized authorization remain separate.
7. Fail closed on missing canonical references, unsupported contract versions, invalid artifact integrity, missing rights/quality evidence, worker trust uncertainty, or authorization ambiguity.

### Explicitly out of scope

- Creating or assigning canonical WorkflowRun, WorkflowTask, Job, JobAttempt or Worker IDs locally.
- Treating local plan/task/run IDs as aliases for canonical WP2/WP3 identities.
- Creating canonical Artifact/ArtifactVersion/Manifest records outside WP4.
- Treating local JSON artifacts, file paths or SHA-256 values as canonical artifact registration.
- Creating ApprovalRequest/ApprovalDecision or authorization decisions inside the Studio/local autonomy runtime.
- Making review completion imply approval, or approval imply protected-action authorization.
- Activating public-web research, model providers, cloud services or paid providers beyond the already authorized local specialist scope.
- Production rendering, uploads, publishing, distribution, deployment or external side effects.
- Changing database schema, migrations, API contracts, worker credentials, lease/retry parameters or retention/purge behavior.
- Replacing the current engine, changing architecture ownership, or redesigning the dashboard.

## 4. Ownership boundary — canonical owner writes, adapter correlates

| Concern | Authority | Adapter responsibility | Forbidden shortcut |
|---|---|---|---|
| Workflow/run/task/job/attempt lifecycle | WP2 | Submit/receive through approved execution interface; correlate returned canonical references | Local task ID becomes canonical job ID |
| Worker identity/trust/assignment/lease/fencing | WP3, coordinated with WP2 per reconciled final contract | Execute only an authenticated, scoped assignment and return attributable completion evidence | Hostname, process ID or local worker ID becomes canonical worker identity |
| Artifact/ArtifactVersion/Manifest and transfer | WP4 | Supply bytes/metadata through approved registration/transfer boundary; retain returned canonical references | Local path/hash or generated artifact ID is called an ArtifactVersion |
| QA, rights, review, approval, authorization and audit | WP5 | Consume explicit outcomes; stop on missing/negative/unknown outcomes | Local review flag or UI button becomes approval/authorization |
| End-to-end acceptance and recovery evidence | WP6 | Emit traceable evidence for approved scenarios | Local unit tests or dry-run outputs are described as WP6 acceptance |
| Studio production/business lifecycle | Contract 11 / relevant domain owner | Execute bounded engine operation and return result for domain acceptance | Workflow/job success mutates content/studio business lifecycle automatically |

**Conflict requiring reconciliation:** Contract 10/X-01 §1–3 describes WP3 as owning lease/fencing, while the WP1–WP6 traceability register §2 describes WP2 as authoritative for durable lease/attempt state and WP3 as supplying worker trust/heartbeat/fencing evidence. No implementation may choose one interpretation silently. The final WP2/WP3 owner decision must explicitly resolve authority and evidence boundaries.

## 5. Minimal logical flow — target only, not a frozen API

1. A canonical owner submits an approved execution request with canonical references and an idempotency scope.
2. WP2 creates and owns the durable workflow/task/job/attempt progression.
3. WP3 authenticates the worker and supplies authoritative assignment/trust evidence under the reconciled lease/fencing model.
4. The bounded adapter invokes the existing research/script/Studio specialist using a validated, versioned input contract.
5. The local specialist produces a local output and attributable execution evidence.
6. The adapter validates output shape and integrity, then submits it to WP4 for canonical artifact registration and immutable version creation.
7. The adapter returns canonical artifact references and completion evidence to WP2; the owning business domain decides whether to accept/commit its result.
8. WP5 owns quality/rights/review/approval/authorization outcomes. No protected side effect is permitted without an explicit valid central authorization decision.
9. WP6 validates the approved synthetic vertical slice and recovery/denial cases in an authorized isolated environment.

This sequence is a conceptual ownership flow only. It does not define endpoint paths, request fields, event names, database tables, canonical IDs, state enums, timeout values, retry values or API schemas.

## 6. Required closure gates before coding

| Gate | Required evidence | Current status |
|---|---|---|
| G1 — Contract authority | WP1/WP2 canonical entity vocabulary, relationships, cardinalities and physical ownership frozen | OPEN |
| G2 — WP2 execution contract | Workflow/task/job/attempt state transitions, idempotency, retry, cancellation, recovery and lease authority settled | OPEN |
| G3 — WP3 worker contract | Worker identity, registration/trust, capability verification, assignment, credential, revocation, heartbeat and fencing settled | OPEN |
| G4 — WP4 artifact contract | Artifact/ArtifactVersion/Manifest schema, exact-version references, transfer, integrity, quarantine and lifecycle settled | OPEN |
| G5 — WP5 governance contract | QA/rights/review/approval/authorization separation, protected-action catalogue, fail-closed rules and audit interface settled | OPEN |
| G6 — Studio adapter contract | Part 7 proposal reconciled with Contracts 10/11, WP2–WP5 and owner-approved decision record | OPEN |
| G7 — WP6 test authority | Artifact 07 crosswalk, isolated environment, synthetic data, test parameters and execution authorization | OPEN |
| G8 — implementation authorization | Explicit owner approval naming exact work package, repository baseline, allowed paths, actions, tests and stop conditions | NOT GRANTED |

No single gate should be inferred from another. In particular, approval of a code patch is not deployment or production authorization.

## 7. Recommended next engineering unit after gates close

The first implementation increment should be a **contract-conformance harness**, not a live workflow bridge:

- Validate versioned adapter request/response envelopes against the frozen contracts.
- Use synthetic fixtures only.
- Assert canonical IDs are typed and never derived from local identifiers.
- Assert local run/task/artifact identifiers remain provenance references, not canonical identity.
- Assert artifact references pin exact immutable versions.
- Assert approval and authorization are distinct and missing authorization fails closed.
- Assert duplicate delivery, stale worker/attempt, invalid artifact, and partial failure are rejected or reconciled.
- Keep all network/provider/publishing actions disabled.

Only after this harness passes should a separately authorized synthetic WP6 vertical slice connect actual canonical services.

## 8. Source references

- `docs/nextdecode-workspace/03_P0_GOVERNANCE_AND_DECISIONS/02_OWNER_REVIEW_AND_AUTHORIZATION/NEXTDECODE_Artifact_10_P0_Owner_Review_Authorization_Pack_1.0.md` — §§1, 8–9, 20, 22.
- `docs/nextdecode-workspace/06_AGENT_HANDOFFS/NEXTDECODE_Artifact_09_P0_Coding_Agent_Handoff_Specification_1.0.md` — §§1, 2.2, 18.
- `docs/nextdecode-workspace/04_WORKSTREAMS/WP2_WORKFLOW_EXECUTION/01_SPECIFICATIONS_AND_CANDIDATES/NEXTDECODE_P0_WP2_Durable_Job_Workflow_Execution_0.1.md` — §§1–2.
- `docs/nextdecode-workspace/04_WORKSTREAMS/WP3_WORKER_TRUST/01_SPECIFICATIONS_AND_RECONCILIATION/NEXTDECODE_P0_WP3_Worker_Registry_Contract_Boundary_0.1.md` — §§1–3.
- `docs/nextdecode-workspace/04_WORKSTREAMS/WP4_ARTIFACT_STORAGE/01_SPECIFICATIONS_AND_RECONCILIATION/NEXTDECODE_P0_WP4_Artifact_Registration_Storage_Transfer_0.1.md` — §§1–3.
- `docs/nextdecode-workspace/04_WORKSTREAMS/WP5_GOVERNANCE_QUALITY_RIGHTS/01_SPECIFICATIONS_AND_RECONCILIATION/NEXTDECODE_P0_WP5_Governance_Quality_Rights_Authorization_0.1.md` — §§1–3.
- `docs/nextdecode-workspace/04_WORKSTREAMS/WP6_INTEGRATION_RECOVERY_ACCEPTANCE/01_SPECIFICATIONS_AND_RECONCILIATION/NEXTDECODE_P0_WP6_Vertical_Slice_Integration_Recovery_Validation_0.1.md` — §§1–3.
- `docs/nextdecode-workspace/02_CANONICAL_CONTRACTS_AND_DATA/02_SHARED_INTELLIGENCE_CONTRACTS/NEXTDECODE_Contract_10_X01_Workflow_Job_Worker_Ownership_Reconciliation_0.1.md` — §§1–3, 9, 11.
- `docs/nextdecode-workspace/00_CONTROL_AND_INDEX/17_WP1-WP6_CONTRACT_TRACEABILITY_REGISTER_0.1.md` — §§2–4.
- `reports/D37_STUDIO_AUTOMATION_BRIDGE_RECONCILIATION_2026-11-13.md` — D37-A local-to-canonical mapping matrix.

## 9. Final disposition

**D37-B boundary definition: COMPLETE.**  
**Canonical adapter implementation: BLOCKED — contract freeze and explicit implementation authorization absent.**  
**Safe next action:** close the owner/contract gates and prepare the contract-conformance harness specification. Do not create a parallel local canonical adapter or invent missing canonical fields.
