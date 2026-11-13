# NEXTDECODE P0 — WP5 Governance Matrix Agent Handoff & Engineering Prompts

**Document ID:** NEXTDECODE-P0-WP5-AGENT-PROMPTS-0.1  
**Version:** 0.1  
**Date:** 2026-11-04  
**Status:** PREPARED PROMPT PACK — NOT DISPATCHED  
**Authorization:** Documentation-only work is active; agent execution and implementation are NOT AUTHORIZED.  
**Companion:** NEXTDECODE_P0_WP5_Governance_State_and_Decision_Matrices_0.1.md

---

## 1. Purpose

This pack prepares bounded, copy-paste-ready instructions for the NEXTDECODE engineering and review agents. It is a coordination artifact, not a dispatch, repository permission, implementation authorization or contract freeze.

The user expects the project coordinator to prepare prompts, sequence agent work, protect file ownership, reconcile dependencies and review handoffs. These responsibilities are retained here.

## 2. Authority and dependency check before any dispatch

### Required governing documents

1. 00_CONTROL_AND_INDEX/00_MASTER_INDEX.md
2. 00_CONTROL_AND_INDEX/01_DOCUMENT_REGISTER.md
3. 00_CONTROL_AND_INDEX/02_AGENT_OPERATING_PROTOCOL.md (0.1.0-draft)
4. 00_CONTROL_AND_INDEX/04_OPEN_GAPS_AND_CONFLICTS.md
5. 03_P0_GOVERNANCE_AND_DECISIONS/01_ACCEPTED_DECISIONS/NEXTDECODE_Artifact_08_Implementation_Reference_Accepted_Contract_Decisions_1.0.md
6. 03_P0_GOVERNANCE_AND_DECISIONS/02_OWNER_REVIEW_AND_AUTHORIZATION/NEXTDECODE_P0_Owner_Review_Contract_Freeze_Decision_Record_0.1.md
7. 06_AGENT_HANDOFFS/NEXTDECODE_Artifact_09_P0_Coding_Agent_Handoff_Specification_1.0.md
8. 04_WORKSTREAMS/WP5_GOVERNANCE_QUALITY_RIGHTS/01_SPECIFICATIONS_AND_RECONCILIATION/NEXTDECODE_P0_WP5_Governance_Quality_Rights_Authorization_0.1.md
9. 04_WORKSTREAMS/WP5_GOVERNANCE_QUALITY_RIGHTS/01_SPECIFICATIONS_AND_RECONCILIATION/NEXTDECODE_P0_WP5_Contract07_Batch17_Batch19_Clause_Traceability_0.1.md
10. 04_WORKSTREAMS/WP5_GOVERNANCE_QUALITY_RIGHTS/01_SPECIFICATIONS_AND_RECONCILIATION/NEXTDECODE_P0_WP5_Governance_State_and_Decision_Matrices_0.1.md
11. 02_CANONICAL_CONTRACTS_AND_DATA/03_DATA_DICTIONARY_AND_TRACEABILITY/NEXTDECODE_Canonical_Data_Dictionary_Entity_Ownership_Registry_1.1.md
12. 05_IMPLEMENTATION_PLANS_AND_WORK_ORDERS/02_BATCH_PACKAGES/NEXTDECODE_P0_Batch17_State_Machine_Transition_Catalogue.md
13. 05_IMPLEMENTATION_PLANS_AND_WORK_ORDERS/02_BATCH_PACKAGES/NEXTDECODE_P0_Batch19_Database_Schema_ERD_Persistence_Specification.md
14. Relevant Contract 12 reconciliation and Artifact 07 acceptance framework before protected-action or acceptance work.

### Accepted decisions to preserve

- CF-20 rights vocabulary and Contract 07 ownership.
- CF-21 ApprovalDecision vocabulary, immutable review-package binding and exact-version/scope decision.
- CF-22 Option A centralized authorization; default-deny, least privilege and fail-closed enforcement.
- ADR-007 centralized authorization; ADR-008 QA blockers; ADR-009 rights enforcement; ADR-010 separate state machines.
- Human approval before publishing; automatic public publishing disabled.
- P0-A remains a narrow vertical slice; no broad Control Center expansion.
- Existing Shorts Studio remains a specialised engine behind its bounded adapter; do not replace it.

### Known unresolved dependencies

- GAP-015: ApprovalRequest lifecycle vs ApprovalDecision outcome; Contract 07 WITHDRAWN conflict.
- GAP-016: emergency pause and in-flight provider action semantics.
- GAP-018: Contract 12 publishing authorization / distribution operation boundary.
- GAP-022/023: WP1–WP6 and Batch 17–26 exact traceability.
- GAP-024: Batch 20/25 security overlap.
- GAP-026: Artifact 07 ↔ WP6 test-level mapping.
- GAP-027: Contract 07 / Batch 17 / Batch 19 reconciliation.
- Rights field naming rights_status vs rights_state.
- AuthorizationDecision vs PublishingAuthorization relationship.
- ApprovalRequest persistence and decision cardinality.
- Exact immutable review package/content/artifact/manifest/checksum field representation.

No agent may resolve these by guessing or by promoting a candidate document to accepted/frozen.

## 3. Agent role allocation and writer coordination

| Agent | Preserved role | Allowed mode for this workstream | Current status |
|---|---|---|---|
| Qoder | Phase 11 engineering owner; sole writer for current governance-closure milestone | Sole implementation writer for specifically authorized governance package; one owned file set at a time | NOT DISPATCHED |
| OpenCode | Phase 10 engineering/closure owner | Read-only API/backend architecture review where assigned; no overlapping write ownership | NOT DISPATCHED |
| Kilo | Independent QA/security acceptance | Read-only review after implementation and evidence bundle complete | NOT DISPATCHED |
| Copilot | Focused regression-test review suggestion | Read-only review of explicitly assigned tests/diff/evidence | NOT DISPATCHED |
| Antigravity | Targeted product/UI review suggestion | Only separately assigned, isolated UI task; no broad UI expansion | PAUSED / NOT DISPATCHED |

**One active writer rule:** Qoder is the sole writer for the current governance-closure milestone. Do not assign OpenCode or another agent overlapping write access to Qoder-owned files. Separate workspaces/files may be used only after owner-approved path ownership and explicit authorization. Read-only review agents must not edit the change under review.

## 4. Current authorization status and hard stop

The current Owner Review Contract Freeze Decision Record 0.1 explicitly says implementation and agent execution are NOT GRANTED. Artifact 09 1.0 is a handoff specification, not authorization.

Therefore:
- These prompts are prepared but dormant.
- Do not launch an agent from this document.
- Do not grant repository access or run commands.
- Do not edit source code, tests, dependencies, configuration, schemas or migrations.
- Do not commit, push, merge, deploy, provision, spend, upload, generate production artifacts or publish.
- A separate current owner authorization must identify repository, task, agent, access mode, exact scope, allowed operations and acceptance authority before any agent starts.

## 5. Prompt A — Qoder: governance implementation owner (future, gated)

**Task ID:** ND-P0-WP5-ENG-01  
**Agent:** Qoder  
**Role:** Phase 11 engineering owner / sole writer for this governance-closure milestone  
**Status:** PREPARED — DO NOT START WITHOUT SEPARATE OWNER AUTHORIZATION

### Copy-paste prompt

You are the sole implementation writer for the specifically authorized NEXTDECODE P0 WP5 governance work package. Before doing anything, read the Master Index, Document Register, Agent Operating Protocol, Open Gaps Register, accepted Artifact 08 decisions, Owner Review Contract Freeze Decision Record, Artifact 09, WP5, the Contract 07/Batch 17/Batch 19 crosswalk, the Governance State & Decision Matrices, Data Dictionary v1.1, Batch 17 and Batch 19.

First verify that a current owner authorization explicitly names this task, repository/path, target revision, permitted files, permitted commands and allowed operations. If that authorization is absent, expired, ambiguous or conflicts with a governing source, STOP and return a read-only readiness report. This prompt alone grants no authority.

If authorized, implement only the exact owner-frozen WP5 governance contract assigned. Qoder is the only writer for the assigned governance files. Do not allow another agent to modify the same files. Preserve all existing work and architecture.

Required engineering behavior:
1. Implement CF-20 rights assessment using only the owner-frozen canonical vocabulary and use-specific evidence/scope.
2. Keep ApprovalRequest lifecycle distinct from CF-21 ApprovalDecision outcomes. Do not add WITHDRAWN to ApprovalDecision or silently map it to REVOKED.
3. Bind every approval to the immutable review package and exact content/artifact/manifest version plus checksum according to the frozen field contract.
4. Enforce CF-22 Option A centralized authorization as the only authorization authority; default-deny and fail-closed.
5. Keep QA, rights, approval, authorization, execution and confirmed external outcome separate.
6. Prevent hard QA blockers from being bypassed by ordinary approval.
7. Preserve auditability, exact actor/reason/time/version binding, expiry/revocation checks and emergency-pause boundaries.
8. Do not invent fields, enums, transitions, cardinalities, reason codes, policy defaults or provider behavior. Stop and request owner disposition where the frozen contract is silent.

Permissions and exclusions:
- Write only the paths explicitly named in the separate authorization.
- No unrelated refactor, broad cleanup, architecture replacement or scope expansion.
- No secrets/credentials, production data, live provider actions, paid services, deployment, upload or publishing.
- No Git commit/push/merge unless separately and explicitly authorized.
- No automatic public publishing; human approval remains required.

Required outputs:
- Scoped implementation plan and path ownership declaration before edits.
- Requirement → contract clause → code path → test ID traceability.
- Minimal implementation diff.
- Tests named and executed exactly as authorized, with command, environment, commit/revision and raw results.
- Security/failure-mode evidence for default deny, stale version, checksum mismatch, missing rights, request/decision separation, approval revocation, authorization expiry/revocation, pause and unknown external outcome.
- Deviations, open decisions, risks and rollback notes.
- Handoff using the required template in this pack.

Stop immediately if the owner-frozen contract, repository baseline, test environment, migration boundary or permission is missing.

## 6. Prompt B — OpenCode: read-only API/backend architecture review

**Task ID:** ND-P0-WP5-ARCH-RO-01  
**Agent:** OpenCode  
**Status:** PREPARED — DO NOT START WITHOUT SEPARATE OWNER AUTHORIZATION

### Copy-paste prompt

Perform a strictly read-only architecture review of the specifically assigned NEXTDECODE P0 WP5 API/backend implementation or design evidence. Read the Master Index, Agent Operating Protocol, accepted Artifact 08 decisions, WP5, Contract 07 reconciliation, Governance State & Decision Matrices, Data Dictionary v1.1, Batch 17, Batch 19 and the exact owner-frozen contract revision supplied in the authorization.

Do not edit files, generate patches, change configuration, run migrations, commit, push, merge, deploy or access live providers. Do not become a second writer; Qoder retains sole write ownership for governance closure.

Review:
- central authorization boundary and default-deny enforcement;
- separation of ApprovalRequest and ApprovalDecision;
- CF-20 rights vocabulary and scope binding;
- exact immutable review-package/version/checksum binding;
- AuthorizationDecision / PublishingAuthorization model consistency with the frozen contract;
- event/API envelope, idempotency, expiry/revocation and audit semantics;
- fail-closed behavior and bypass surfaces;
- compatibility with WP1 persistence, Contract 12 distribution and WP6 acceptance boundaries.

For each finding provide severity, exact file/path/line or clause, source authority, impact, reproducible evidence where authorized, recommended disposition and whether owner decision is required. Do not resolve owner-reserved issues or infer implementation permission. Return a read-only architecture report and explicit verdict: PASS / PASS WITH CONDITIONS / BLOCKED, with rationale.

## 7. Prompt C — Copilot: focused regression-test review

**Task ID:** ND-P0-WP5-TEST-REVIEW-01  
**Agent:** Copilot  
**Status:** PREPARED — DO NOT START WITHOUT SEPARATE OWNER AUTHORIZATION

### Copy-paste prompt

Review only the explicitly assigned regression-test files, test diff and acceptance mapping for the NEXTDECODE P0 WP5 governance package. Read the accepted CF-20/21/22 decisions, frozen contract revision, Governance State & Decision Matrices, Artifact 07 acceptance IDs and Qoder's implementation handoff.

Read-only review only. Do not edit tests or source, generate patches, run commands unless separately authorized, or modify the writer's files.

Check that tests distinguish:
- rights state from approval outcome;
- ApprovalRequest lifecycle from ApprovalDecision outcome;
- WITHDRAWN from REVOKED;
- exact review-package/content/artifact/manifest/checksum binding;
- approval from central authorization;
- authorization from execution/external outcome;
- hard QA blocker bypass;
- default-deny and missing/ambiguous evidence;
- expiry, revocation, changed version/destination, emergency pause and unknown external outcome.

Identify missing positive, negative, boundary, stale-version, replay/idempotency and failure-path cases. Map every finding to an acceptance ID, exact test path and source clause. Return a focused review report with severity, evidence, test gap, recommendation and verdict. Do not claim tests passed unless you personally ran the exact authorized command and captured its output.

## 8. Prompt D — Kilo: independent QA/security acceptance

**Task ID:** ND-P0-WP5-INDEPENDENT-ACCEPT-01  
**Agent:** Kilo  
**Status:** PREPARED — WAIT UNTIL IMPLEMENTATION AND EVIDENCE BUNDLE ARE COMPLETE

### Copy-paste prompt

Conduct independent, strictly read-only QA/security acceptance of the specified NEXTDECODE P0 WP5 governance implementation after Qoder has completed the authorized work and supplied the complete evidence bundle.

Before review, confirm the owner-frozen contract revision, implementation revision, path ownership, test environment, test outputs, threat model and acceptance IDs. If any is missing, report BLOCKED rather than infer readiness.

Do not modify source, tests, configuration, schemas, migrations or evidence. Do not run destructive commands, connect to live providers, change credentials, deploy, upload or publish.

Independently challenge:
- central authorization as the sole authority;
- default-deny/fail-closed behavior;
- actor/action/resource/version/destination/policy/time binding;
- rights and approval evidence scope;
- request/decision lifecycle separation;
- review-package/checksum integrity;
- hard QA blocker enforcement;
- expiry/revocation and emergency pause;
- adapter bypass and unknown external outcomes;
- audit evidence and idempotent replay behavior.

For each issue provide severity, exact evidence, affected requirement/acceptance ID, reproduction steps if authorized, impact and required remediation. Return an independent verdict and residual risk list. Do not fix issues in the reviewed change set. Owner retains final acceptance authority.

## 9. Prompt E — Antigravity: targeted UI/product review (conditional)

**Task ID:** ND-P0-WP5-UI-REVIEW-01  
**Agent:** Antigravity  
**Status:** PAUSED — NO CURRENT ASSIGNMENT

### Copy-paste prompt if separately assigned

Review only the exact contract-aligned UI surface and isolated files named in a future owner authorization. P0-A remains a narrow vertical slice, not a full Control Center build. Do not expand navigation, dashboards, settings or product scope.

Read the frozen API/event contract, accepted governance decisions, relevant WP5 acceptance criteria and assigned UI files. Verify that the UI:
- displays QA, rights, approval and authorization as distinct facts;
- never implies approval is authorization;
- makes blocked/unknown/pending states understandable without bypass controls;
- preserves human approval before publishing;
- does not expose a direct publish path that bypasses central authorization;
- handles stale version, expiry, revocation and denied actions safely.

Do not modify backend contracts, security rules or domain policy. Do not publish, deploy, commit or merge. Return screenshots/annotated findings and exact UI requirement mapping only if those outputs are explicitly authorized.

## 10. Dispatch and sequencing plan

No agent is dispatched by this pack. When separate owner authorization exists, use this sequence:

1. Owner confirms detailed contract freeze and task-specific implementation authorization.
2. Capture authorized repository baseline and exact revision.
3. Confirm path-level ownership. Qoder is sole writer for governance closure.
4. Qoder implements the bounded package and returns evidence.
5. OpenCode performs read-only API/backend architecture review on the assigned scope.
6. Copilot performs focused read-only regression-test review on assigned tests.
7. Qoder resolves accepted findings within its owned files under the same authorization or obtains a new authorization if scope changes.
8. Kilo performs independent read-only QA/security acceptance after remediation and evidence freeze.
9. Antigravity remains paused unless a separate, isolated UI review is explicitly assigned.
10. Owner reviews evidence and makes the acceptance/release decision. No agent self-approves.

If parallel lanes are later authorized, they must use separate workspaces/files, approved versioned contracts, named owners and explicit integration responsibilities. No overlapping writers.

## 11. Required agent handoff report template

Every agent must return:

- TASK ID:
- AGENT:
- OBJECTIVE:
- STATUS: NOT_STARTED / IN_PROGRESS / BLOCKED / READY_FOR_REVIEW / ACCEPTED / REJECTED / SUPERSEDED
- AUTHORIZATION REFERENCE:
- INPUT DOCUMENTS (version + exact path):
- ACCEPTED DECISIONS / CONSTRAINTS:
- FILES INSPECTED:
- FILES MODIFIED:
- FILES CREATED:
- FINDINGS:
- CONTRACT / ACCEPTANCE REFERENCES:
- COMMANDS AND TESTS RUN (exact command, environment, revision, output):
- DEFECTS / SEVERITY:
- DEPENDENCIES:
- OWNER QUESTIONS:
- DEVIATIONS:
- RISKS:
- RECOMMENDATION:
- HANDOFF STATUS:

No generic “done” or “all tests pass” without inspectable evidence.

## 12. Current disposition

This prompt pack is PREPARED, NOT DISPATCHED. It provides future-ready agent instructions while respecting the current documentation-only authorization boundary. The next active work remains documentation reconciliation: B-WP5-03 Batch 17 transition-edge mapping, then B-WP1-04 Batch 19 field/entity mapping. Engineering prompts remain dormant until explicit owner authorization and required contract freeze gates are satisfied.

END OF PROMPT PACK
