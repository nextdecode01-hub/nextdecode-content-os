# NEXTDECODE — Handoff Register Update: ND-GOV-005 B3

**Record date:** 2026-11-02  
**Record type:** Proposed append-only handoff-register update  
**Status:** Ready for incorporation into the canonical register

> The canonical master Handoff Register was not located during the source search. This document is an append-only update proposal; it does not claim that the master register itself has been updated.

## 1. Owner decision

- B3 remediation: **APPROVED**
- Future compatibility mapping: **DEFERRED**
- Integration / merge: **NOT AUTHORIZED**
- Production publishing: **NOT AUTHORIZED**

The owner decision record is `ND_GOV_005_B3_OWNER_DECISION_RESOLUTION_2026-11-02.md`.

## 2. Source documents and authority

Before execution, the engineering lead must locate and confirm the current authoritative copies and versions of:

1. `ND_GOV_005_B3_REMEDIATION_SPEC_FINAL_2026-10-31.md` — frozen B3 requirements R1–R6.
2. `GOV_005_report.md` — implementation report; treat as reported evidence, not independent verification.
3. `NEXTDECODE_P0_WP5_Governance_Quality_Rights_Authorization_0.1.md` — design candidate; owner review required.
4. `NEXTDECODE_Artifact_08_Implementation_Reference_Accepted_Contract_Decisions_1.0.md` — accepted contract reference; CF-20 canonical rights states, CF-21 approval separation, CF-22 central authorization.
5. `NEXTDECODE_P0_Governance_Authorization_Contract_Reconciliation_0.1.md` — reconciliation candidate; do not treat unaccepted proposals as decisions.
6. `NEXTDECODE_Artifact_09_P0_Coding_Agent_Handoff_Specification_1.0.md` — handoff process; it does not itself authorize implementation or operational actions.

If a required document, version, section, or baseline is missing or conflicting, name the exact gap and stop the affected work. Do not invent an owner decision or silently reconcile contracts.

## 3. Scope and implementation boundary

The only approved implementation scope is the frozen B3 remediation specification R1–R6:

- R1: normalize `reuse_rights` from string or dictionary status; trim/lowercase; only exact `permitted` passes.
- R2: support persisted list and in-memory dictionary collection shapes; malformed collection/card blocks.
- R3: missing `cutouts` means an empty list, subject to R5 proof.
- R4: non-empty cards require a valid `rights_gate` dictionary with integer `checked == len(cards)` and integer `blocked == 0`; booleans do not count as integers; malformed/missing/contradictory evidence blocks with `PublishNotAuthorized(code="blocked_rights")`.
- R5: zero-cutout proof requires `evidence.cutout_selection` dictionary, non-empty string `reason`, and integer `budget`; no brittle exact-reason matching; do not consult `rights_gate.publish_ready` in the zero-cutout case.
- R6: persist `cutout_selection` in pipeline evidence.

Do not expand scope into global rights policy, canonical rights-state mapping, `visual_quality` asset licensing, `cutouts.rights_gate` computation, or storyboard reason logic.

## 4. Rights and contract boundary

Contract 07 owns canonical rights assessment. CF-20 canonical states are `UNKNOWN`, `PENDING_REVIEW`, `CLEARED`, `RESTRICTED`, `EXPIRED`, `REVOKED`, and `DENIED`.

The local R9 compatibility input `reuse_rights: permitted` is not a canonical rights state and must not be automatically mapped to `CLEARED` or any other CF-20 state. Compatibility mapping is deferred pending a separate owner decision.

Keep QA, rights assessment, review snapshot, approval, authorization, and execution as distinct concepts. Human approval before publishing remains required; automatic public publishing remains disabled.

## 5. Work ownership and coordination

- **OpenCode — primary implementer/evidence owner:** preserve the existing isolated worktree and implementation; provide exact baseline, status, diff, changed-file list, test commands/results, and reproducible evidence. Do not integrate.
- **Copilot — read-only comparison:** compare the frozen specification and source snapshot with the implementation/evidence; report mismatches and gaps; make no code changes.
- **Qoder — security review:** perform only after the target snapshot and authorization are clear; report security and boundary findings; do not modify code.
- **Kilo — independent read-only acceptance:** review only when the evidence package is complete and the review is explicitly authorized; do not change code.
- **Antigravity:** remain paused unless separately assigned.

These are coordination assignments, not permission to exceed the stated scope or perform integration.

## 6. Required evidence package

Before acceptance review, collect:

- exact repository and worktree path;
- exact base commit and current HEAD;
- clean/dirty working-tree status;
- complete changed-file list and full diff;
- hashes for relevant source files and evidence bundle;
- exact test commands, environment details, complete output, and exit codes;
- targeted test results for each R1–R6 requirement;
- regression test results and clear separation of pre-existing failures;
- bundle manifest and reproducibility/replay instructions;
- explicit list of deviations, unresolved issues, and known limitations.

The existing report's 29/29 targeted tests and two unrelated failures remain report-backed until independently reproduced. Do not describe them as independently verified before that occurs.

## 7. Acceptance checklist

- [ ] Source documents and versions confirmed.
- [ ] Owner decision and authority boundaries confirmed.
- [ ] Baseline and worktree identity confirmed.
- [ ] R1 normalization behavior verified.
- [ ] R2 supported collection shapes and malformed-input blocking verified.
- [ ] R3 missing-cutouts behavior verified with R5 evidence.
- [ ] R4 integer checks, boolean rejection, mismatch blocking, and error code verified.
- [ ] R5 zero-cutout evidence validation verified; no `publish_ready` dependency.
- [ ] R6 evidence persistence verified.
- [ ] Tests independently reproduced; unrelated failures identified.
- [ ] Diff and bundle integrity reviewed.
- [ ] Deviations and unresolved issues documented.
- [ ] Independent acceptance review completed, if authorized.

Passing this checklist does not itself authorize integration, merge, deployment, or production publishing.

## 8. Prohibited actions without separate explicit owner authorization

No integration, merge, commit, push, deployment, production generation, external upload, public publishing, credential or permission changes, paid-service activation, destructive Git operations, broad staging, or overwriting/discarding existing work.

## 9. Exact execution prompt for the engineering coordination chat

Copy and paste the following prompt after attaching this document and the owner decision record:

---

You are coordinating the NEXTDECODE ND-GOV-005 B3 engineering handoff.

Read the attached `ND_GOV_005_B3_OWNER_DECISION_RESOLUTION_2026-11-02.md` and `HANDOFF_REGISTER_B3_UPDATE_2026-11-02.md` in full, then reconcile them against the authoritative source documents listed in the handoff record.

### Binding owner decisions

- B3 remediation is APPROVED, limited strictly to frozen requirements R1–R6.
- Future compatibility mapping is DEFERRED.
- Integration/merge is NOT AUTHORIZED.
- Production publishing is NOT AUTHORIZED.
- `reuse_rights: permitted` remains a local R9 compatibility input only. Do not map it automatically to CF-20 `CLEARED` or another canonical rights state.
- Contract 07 owns canonical rights assessment.
- Human approval before publishing remains required; automatic public publishing remains disabled.

### First phase: documentation and evidence reconciliation only

Do not begin coding immediately. First:

1. Identify each relevant P0/source document, exact version, status, and authority.
2. Confirm accepted decisions, deferred decisions, unresolved decisions, conflicts, and missing sections.
3. Confirm the exact repository, worktree, baseline commit, current HEAD, and working-tree state from available evidence.
4. Inventory the implementation report, bundle, manifest, hashes, diffs, and test evidence.
5. Separate report-backed claims from independently verified facts.
6. Identify whether the existing implementation matches each frozen requirement R1–R6.
7. Record every new documentation dependency or gap, naming the exact missing document/section and whether work can safely proceed.

Do not invent owner decisions, silently change contracts, or treat candidate documents as accepted decisions.

### Agent boundaries

- OpenCode: primary implementation/evidence owner; preserve the existing worktree and report exact evidence.
- Copilot: read-only specification/source comparison; no code changes.
- Qoder: security review only after target snapshot and authorization are clear; no code changes.
- Kilo: independent read-only acceptance only after evidence is complete and review is authorized; no code changes.
- Antigravity: paused unless separately assigned.

### Scope

Use only the frozen ND-GOV-005 B3 remediation specification R1–R6. Do not expand into global rights policy, canonical compatibility mapping, `visual_quality` licensing, `cutouts.rights_gate` computation, or storyboard reason logic.

### Safety restrictions

Do not integrate, merge, commit, push, deploy, run production generation, publish, upload externally, change credentials/permissions, activate paid services, perform destructive Git operations, broadly stage files, or overwrite/discard existing work. No action in this handoff grants those permissions.

### Required first response

Return:

1. Documentation/version/authority matrix.
2. Accepted, deferred, unresolved, and conflicting decisions.
3. Repository/worktree/baseline evidence inventory.
4. Report-backed versus independently verified evidence table.
5. R1–R6 compliance/evidence matrix.
6. Agent responsibility and boundary confirmation.
7. Exact blockers and missing documents/sections.
8. A clear statement of what can safely proceed next.

Stop after this reconciliation and handoff assessment. Do not start coding or integration until the documentation and evidence review is complete and any required separate authorization is obtained.

---
