# NEXTDECODE — P0 ODR-22 Source Reconciliation & Decision-Register Integrity

**Document ID:** `NEXTDECODE_P0_ODR22_Source_Reconciliation_Decision_Register_Integrity_0.1`  
**Version:** 0.1  
**Date:** 1 November 2026  
**Status:** SOURCE RECONCILIATION — OWNER REVIEW REQUIRED  
**Scope:** X-11; ODR-22; master decision-register traceability  
**Detailed contract freeze:** NOT GRANTED  
**Implementation authorization:** NOT GRANTED

---

## 1. Executive finding

ODR-22 in `NEXTDECODE_P0_Decision_Resolution_Register_0.1.md` is **not traceable to a distinct accepted owner decision with the same identifier and exact wording** in the authoritative Artifact 08 owner-decision records inspected.

The ODR-22 row currently combines two different categories:

1. Product-scope/operating constraints: single-owner Creator Mode at initial scope.
2. Existing engineering and QA responsibility assignments: Qoder, OpenCode and Kilo ownership.

The source records support these as established project constraints. They do **not** establish that they were jointly accepted as a single decision called “ODR-22 — Scope and ownership.”

Therefore:

> **ODR-22 disposition: PROVISIONAL GROUPING — SOURCE RECONCILIATION REQUIRED. Do not cite ODR-22 itself as an owner-approved decision.**

The underlying constraints remain in force through their own source records. This reconciliation does not reopen them, remove them, weaken them or ask the owner to approve them again.

## 2. Sources inspected and authority

### 2.1 Higher-authority source records inspected

1. `NEXTDECODE_Artifact_08_Implementation_Reference_Accepted_Contract_Decisions_1.0.md`
2. `NEXTDECODE_Artifact_08_Consolidated_Owner_Decision_Record_Contract_Freeze_Closure_1.0.md`
3. `Artifact_08_Contract_Reconciliation_and_Freeze_Candidate_1.1.md`
4. `NEXTDECODE_P0_Owner_Review_Contract_Freeze_Decision_Record_0.1.md`
5. `NEXTDECODE_P0_Detailed_Contract_Freeze_Pack_1.0.md` (identified as a source in the Artifact 08 reconciliation record)
6. `NEXTDECODE_P0_Detailed_Contract_Freeze_Open_Decisions_Closure_1.0.md` (identified as a source in the Artifact 08 reconciliation record)
7. `NEXTDECODE_Architecture_Decision_Register_1.0.md`
8. `NEXTDECODE_Architecture_Decision_Records_Pack_1.0.md`
9. `NEXTDECODE_P0_Decision_Resolution_Register_0.1.md`
10. `NEXTDECODE_P0_Cross_Document_Consistency_Gap_Review_0.1.md`

The search/read pass found the ODR-22 wording in the derived P0 Decision Resolution Register and the X-11 analysis in the cross-document review. It did not establish a separate original master decision record whose source identifier is ODR-22.

### 2.2 Authority precedence

For this reconciliation, use:

1. Explicit owner decision records and accepted ADR/CF decisions.
2. Locked project constraints and architecture decision records.
3. Governing canonical data dictionary and contract standards.
4. WP-1 through WP-6 source specifications.
5. Derived decision-resolution and consolidation registers.
6. Reconciliation documents and summaries.

A derived register may index or group source decisions. It cannot create owner authority or change the source wording.

### 2.3 Search limitation

The inspected Library results did not expose a separate, complete original ODR master register with an independent ODR-22 entry. This is a **provenance limitation**, not evidence that the underlying project constraints are absent.

No claim is made that every historical source file or conversation record has been exhaustively recovered. If a distinct original ODR register is later located, its exact row should be compared and this reconciliation superseded where necessary.

## 3. What the authoritative sources actually support

### 3.1 Single-owner Creator Mode — SOURCE-SUPPORTED PROJECT CONSTRAINT

The P0 Owner Review Contract Freeze Decision Record states that NEXTDECODE remains a single-owner Creator Mode product at initial scope.

The Architecture Decision Register records:

- `L-08` — Initial operating mode: single-owner Creator Mode, one initial workspace and NEXTDECODE brand.
- `L-09` — Future expansion posture: architecture should not block future studios, teams or SaaS evolution, but those are not initial implementation scope.

The P0 Owner Decision Review Sheet separately records:
- `C-01` — NEXTDECODE Content OS, single-owner Creator Mode first.
- `C-02` — One initial brand: NEXTDECODE.

**Disposition:** Preserve these constraints under their existing source identifiers. Do not relabel them as an ODR-22 owner decision.

### 3.2 Engineering and QA ownership — SOURCE-SUPPORTED PROJECT CONSTRAINT

The Artifact 08 Implementation Reference records the existing agent ownership:

- Qoder — Phase 11 engineering owner.
- OpenCode — Phase 10 engineering/closure owner.
- Kilo — independent read-only QA.

The P0 Owner Review Contract Freeze Decision Record repeats the same ownership assignments and explicitly states that they remain unchanged.

The Architecture Decision Register records:
- `L-13` — Existing agent ownership remains locked: Qoder, OpenCode and Kilo with the responsibilities above.

**Disposition:** Preserve these assignments under the existing source identifiers. They are operating/role constraints, not evidence of a separate combined ODR-22 decision.

### 3.3 No scope expansion — SOURCE-SUPPORTED INTERPRETATION

The existing single-owner initial scope and the deferred future expansion posture support the interpretation that initial scope must not silently expand into multi-user/team/SaaS operation.

The agent ownership assignments define responsibilities; they do not grant agents independent product authority, approval authority or permission to expand scope.

**Disposition:** Preserve the boundaries. Do not infer additional permissions or authority from role assignments.

## 4. What ODR-22 currently says — DERIVED REGISTER ONLY

The derived Decision Resolution Register contains:

- **Master ID:** ODR-22
- **Area:** Scope and ownership
- **Proposed resolution:** Carry forward single-owner Creator Mode and existing engineering/QA responsibilities; no scope expansion.
- **Status:** `CARRIED FORWARD — verify detailed row wording at final reconciliation`
- **Source column:** Accepted owner decision record; project constraints.
- **Caveat:** Original full register wording should be reconciled before final freeze.

This row is internally cautious because it already says the detailed wording requires verification. It should not be upgraded to `OWNER-ACCEPTED`, `FROZEN` or `VERIFIED`.

## 5. Reconciliation result

| ODR-22 component | Best-supported source | Correct status | Register treatment |
|---|---|---|---|
| Single-owner Creator Mode at initial scope | P0 Owner Review Decision Record; Architecture Register L-08; Owner Decision Review Sheet C-01 | SOURCE-SUPPORTED / LOCKED CONSTRAINT | Carry forward by source ID |
| One initial workspace and NEXTDECODE brand | Architecture Register L-08; Owner Decision Review Sheet C-02 | SOURCE-SUPPORTED / LOCKED CONSTRAINT | Carry forward by source ID |
| Future teams/studios/SaaS are not initial scope | Architecture Register L-09 | SOURCE-SUPPORTED / LOCKED CONSTRAINT | Carry forward by source ID |
| Qoder Phase 11 engineering ownership | Artifact 08 Implementation Reference; Owner Review Decision Record; Architecture Register L-13 | SOURCE-SUPPORTED / LOCKED CONSTRAINT | Carry forward by source ID |
| OpenCode Phase 10 engineering/closure ownership | Same as above | SOURCE-SUPPORTED / LOCKED CONSTRAINT | Carry forward by source ID |
| Kilo independent read-only QA ownership | Same as above | SOURCE-SUPPORTED / LOCKED CONSTRAINT | Carry forward by source ID |
| Combined decision called “ODR-22 — Scope and ownership” | No distinct authoritative source entry identified | NOT VERIFIED / PROVISIONAL GROUPING | Do not cite as an accepted owner decision |

### 5.1 Recommended register correction

Replace the current ODR-22 row with the following:

| Field | Corrected entry |
|---|---|
| Master ID | `ODR-22` (retain for historical traceability only) |
| Area | `PROVISIONAL GROUPING — scope and responsibility constraints` |
| Source wording | `No single authoritative ODR-22 source wording verified` |
| Status | `PROVISIONAL GROUPING — SOURCE RECONCILIATION REQUIRED` |
| Supported source references | `Architecture Register L-08, L-09, L-13; Owner Decision Review Sheet C-01, C-02; Artifact 08 Implementation Reference; P0 Owner Review Contract Freeze Decision Record` |
| Authority | Existing source constraints only; no new authority created |
| Freeze treatment | Do not include ODR-22 as an accepted decision. Include the underlying constraints individually with their original source IDs. |
| Notes | Preserve source IDs; do not renumber other ODR or package-local IDs. |

The corrected row should remain in the register as a traceability note until the owner decides whether to retire the grouping or whether an original ODR source record is found.

## 6. What this reconciliation does not change

This reconciliation does not change:

- Single-owner Creator Mode at initial scope.
- One initial workspace and NEXTDECODE brand.
- The deferred status of future multi-user/team/SaaS expansion.
- Qoder / OpenCode / Kilo ownership assignments.
- Kilo's independent read-only QA boundary.
- Product-owner authority and the rule that agents cannot self-approve or expand scope.
- Any accepted ADR-001–ADR-010 or CF-01–CF-24.
- The standing delegation rule for routine decisions.
- The requirement for separate explicit authorization before implementation, agent execution, repository changes, tests, deployment, spending, production generation, upload or publishing.

No previously accepted decision is reopened.

## 7. Decision-register integrity rules

**PROPOSED register rules for owner review:**

1. Every accepted decision row must cite an authoritative source record and exact source identifier.
2. A derived master ID must never be presented as the original source ID unless that mapping is verified.
3. If one row combines independent constraints, preserve each source identifier separately and label the grouping as derived.
4. `CARRIED FORWARD` means an existing decision/constraint is retained; it does not prove that the derived wording is exact.
5. `OWNER-ACCEPTED` requires an explicit owner decision or documented acceptance under standing delegation.
6. `FROZEN` requires formal inclusion in an approved detailed contract baseline.
7. `VERIFIED` requires current implementation or independent evidence with scope and date.
8. Preserve historical IDs. Do not renumber ODR rows or package-local O/J/W/A/G/F identifiers merely to make a register look cleaner.
9. A later source correction must be traceable; do not silently overwrite the earlier decision history.
10. A project constraint does not grant implementation, agent, security, legal or external-action authority unless the source explicitly says so.

These are register-quality recommendations, not newly accepted owner decisions.

## 8. X-11 closure assessment

| Criterion | Result |
|---|---|
| Locate ODR-22 in derived register | COMPLETE |
| Identify higher-authority source records | COMPLETE for records inspected |
| Verify exact original ODR-22 wording | NOT VERIFIED |
| Verify underlying Creator Mode constraint | SOURCE-SUPPORTED |
| Verify engineering/QA ownership assignments | SOURCE-SUPPORTED |
| Separate the two source-backed topics | COMPLETE |
| Preserve existing constraints without reopening | COMPLETE |
| Recommend corrected register wording | COMPLETE |
| Confirm exhaustive recovery of all historical ODR sources | NOT VERIFIED |

**X-11 disposition:** The semantic ambiguity is resolved sufficiently to prevent misuse of ODR-22. Its original source provenance remains unverified. Keep the master row provisional and carry forward the underlying constraints by their own source IDs.

This is a **register-integrity clarification**, not a technical contract-freeze blocker by itself.

## 9. Handoff to X-12

X-12 should produce one controlled glossary that separates four independent dimensions:

1. **Decision authority:** OWNER-ACCEPTED, PROPOSED, OPEN, DEFERRED.
2. **Design maturity:** DRAFT, RECONCILED, CANDIDATE, FROZEN.
3. **Implementation state:** NOT IMPLEMENTED, IMPLEMENTED, PARTIALLY IMPLEMENTED.
4. **Evidence state:** NOT VERIFIED, VERIFIED, FAILED, NOT RUN, NOT APPLICABLE.

Avoid using one status word to imply another. For example:

- `OWNER-ACCEPTED` does not mean `FROZEN`.
- `FROZEN` does not mean `IMPLEMENTED`.
- `IMPLEMENTED` does not mean `VERIFIED`.
- `VERIFIED` must identify the exact build, environment, scope and evidence.
- `CARRIED FORWARD` is a register disposition, not a substitute for source provenance.

The glossary must preserve the source precedence in Section 2 and mark each field/state/envelope as accepted, source-defined, proposed or open.

## 10. Safety and authorization boundary

This document does not authorize:

- repository or code changes;
- Git operations;
- tests or runtime execution;
- agent execution or delegation;
- provider selection, provisioning or deployment;
- paid services or charge-generating infrastructure;
- production generation, upload or publishing;
- changes to Qoder, OpenCode or Kilo ownership.

**Detailed contract freeze:** NOT GRANTED.  
**Implementation authorization:** NOT GRANTED.

---

## Plain-language explanation

The existing rules are clear: NEXTDECODE starts as a single-owner product, and Qoder, OpenCode and Kilo already have defined responsibilities. What was unclear was whether those separate rules originally came from one accepted decision called ODR-22. The records inspected do not prove that. So we keep the actual rules, point to their real source IDs, and stop treating the combined ODR-22 label as an approved decision.

**Reconciliation outcome:** X-11 is clarified; ODR-22 remains a provisional grouping pending any original source record. The underlying project constraints remain unchanged.
