# NEXTDECODE P0 — Master Progress & Evidence Register

**Document ID:** ND-P0-REG-001  
**Version:** 0.1  
**Date:** 3 November 2026  
**Status:** Initial evidence-backed register — incomplete inventory; owner review required  
**Phase:** P0  
**Part:** Programme-wide  
**Work package:** P0-CLOSE / source inventory  
**Layer:** Shared governance and evidence  
**Implementation authorization:** NOT GRANTED  
**Storage:** `P0/10-evidence-and-audit/master-registers`

## 1. Purpose

Provide one control point for batch coverage, source status, contract closure, implementation and evidence. This is not a replacement for canonical ADR/CF/ODR registers. It does not create owner decisions.

## 2. Status legend

| Status | Meaning |
|---|---|
| LOCATED | File found in accessible Library |
| CONTENT_PARTIAL | Relevant excerpt found; full source not yet reconciled |
| REVIEWED_PARTIAL | Some content inspected, not a complete audit |
| NEEDS_INVENTORY | Batch/file identity not yet verified |
| OWNER_REVIEW | Document says owner review is required |
| FROZEN | Only when explicit owner freeze evidence exists |
| IMPLEMENTED | Code exists and is verified in the authorized baseline |
| VERIFIED | Evidence is current, reproducible and traceable |
| BLOCKED | A known dependency or authorization prevents progression |

Do not infer one dimension from another.

## 3. Batch inventory — current evidence

| Batch | Current evidence | Working status | Next action |
|---|---|---|---|
| 01 | Exact artifact set not yet verified in this inventory pass | NEEDS_INVENTORY | Locate files and record versions |
| 02 | `NEXTDECODE_P0_Batch02_Consolidated.docx` located; six coordinated docs inside | LOCATED / REVIEWED_PARTIAL | Verify original component files and latest status |
| 03 | `NEXTDECODE_P0_Batch03_Final_Contract_Consolidation_Owner_Review.docx` located | LOCATED / OWNER_REVIEW | Reconcile against later owner decisions and source completeness |
| 04 | Exact batch artifact set not yet verified | NEEDS_INVENTORY | Locate files and record versions |
| 05 | `NEXTDECODE_P0_Batch05_WP1_Domain_and_Persistence_Design_Candidate.docx` located | LOCATED / REVIEWED_PARTIAL | Compare to WP-1 0.3 candidate and latest source |
| 06–11 | Exact batch artifact set not yet verified in this pass | NEEDS_INVENTORY | Locate files; do not assume absent |
| 12 | `NEXTDECODE_P0_Batch12_Authoritative_Source_Verification_Contract_Reconciliation.docx` located | LOCATED / REVIEWED_PARTIAL | Complete provenance/source precedence and ODR verification |
| 13–16 | Pasted terminal snapshots reference Batch 13 and reconciliation packages; exact batch deliverables need Library inventory | CONTENT_PARTIAL / NEEDS_INVENTORY | Locate source artifacts and determine what is actually complete |
| 17 | `NEXTDECODE_P0_Batch17_State_Machine_Transition_Catalogue.docx` located | LOCATED / OWNER_REVIEW | Reconcile states and transitions to owner-approved CF/ADR sources |
| 18 | `NEXTDECODE_P0_Batch18_API_Event_Schema_Specification_Pack.docx` located | LOCATED / OWNER_REVIEW | Close Agent–Worker and schema/source conflicts |
| 19–23 | Exact batch artifact set not yet verified in this pass | NEEDS_INVENTORY | Locate files and record versions |
| 24 | `NEXTDECODE_P0_Batch24_Performance_Scalability_Capacity_Cost_Control.docx` located | LOCATED / OWNER_REVIEW | Close workload profile, measurable targets and cost-control owner decisions |
| Latest handoff | `NEXTDECODE_P0_B12_AGW_Source_Inventory_and_Contract_Reconciliation_Handoff_v0.1.md` created 3 Nov 2026 | CREATED / PROPOSED | Give to receiving agent; await report |

**Important:** This table is an honest partial inventory, not a claim that unlisted batches are missing or incomplete. A complete inventory requires locating each batch and recording every constituent file.

## 4. Known cross-batch control artifacts

| Artifact | Current known status | Use |
|---|---|---|
| `NEXTDECODE_P0_07_Master_Register_Change_Log_and_Document_Index.md` | Located; v0.1 coordination index | Navigation; lists WP-1–WP-6 and reconciliation packages |
| `NEXTDECODE_P0_05_P0_Acceptance_Evidence_and_Release_Gates.md` | Located; v0.1 candidate acceptance framework | Acceptance criteria and evidence planning |
| `NEXTDECODE_P0_Workflow_Job_Contract_Reconciliation_0.1.md` | Located; design reconciliation, owner review required | WP-1/WP-2 boundary |
| `NEXTDECODE_AGENT_WORKER_CONTRACT_CLOSURE_HANDOFF_ND-P0-AGW-001.md` | Located; proposed handoff, owner freeze pending | Agent–Worker contract closure |
| `NEXTDECODE_P0_B12_AGW_Source_Inventory_and_Contract_Reconciliation_Handoff_v0.1.md` | Created 3 Nov 2026 | Current source/agent handoff |

## 5. WP progress — design vs implementation vs evidence

| WP | Domain | Design/documentation position | Implementation position | Evidence position | Main closure dependency |
|---|---|---|---|---|---|
| WP-1 | Canonical domain and persistence | Candidate documents listed in master index; exact latest versions need verification | Not established by this register | Not established | Source-complete schema freeze and separate authorization |
| WP-2 | Durable workflow/job execution | v0.1 reconciliation located; owner review required | Not established | Not established | Job/attempt/lease/outbox semantics and WP-1 boundary |
| WP-3 | Worker registry/trust | v0.1 contract listed in master index; latest file/version needs verification | Not established | Not established | Identity, enrollment, capability and credential policy |
| WP-4 | Artifacts | v0.1 contract listed in master index; reconciliation package listed | Not established | Not established | Artifact identity/version/provenance/transfer |
| WP-5 | Governance/quality/rights/authorization | v0.1 contract and reconciliation package listed | Not established | Not established | Rights vocabulary and central authorization closure |
| WP-6 | Vertical slice/integration/recovery | v0.1 contract and acceptance-oracle reconciliation listed | Not established | Historical audit reports hermetic evidence but live whole-chain verification absent | Frozen interfaces and bounded authorized test scope |

"Not established" is not the same as "not implemented"; it means this register has not yet verified it.

## 6. Source conflicts and dependencies

| ID | Issue | Source evidence | Owner / route | Closure evidence |
|---|---|---|---|---|
| SRC-01 | ADR acceptance status | Accepted baseline says ADR-001–010 accepted; ADR pack/register still pending | Governance / owner | Original approval evidence and supersession trail |
| SRC-02 | Rights vocabulary | ADR-009 baseline vocabulary differs from CF-20/Batch17 vocabulary | Contract 07 owner | Explicit owner disposition; no automatic mapping |
| SRC-03 | Artifact 08 duplicate copies | Multiple Library copies including duplicate suffix and text extraction | Documentation control | Hash/metadata/provenance comparison |
| SRC-04 | Detailed freeze vs accepted ADR | Artifact 08 and Batch 18 say detailed freeze pending | Owner | Formal detailed contract freeze record |
| SRC-05 | Batch inventory completeness | Batch 01–24 not fully inventoried in this pass | Documentation controller | Complete file list with version and identity |
| SRC-06 | Notion source access | Notion connector search reported Business-access requirement | Workspace access owner | Valid access or documented alternative source |
| SRC-07 | Master handoff register | Canonical master register not confirmed | Governance/documentation owner | Exact authoritative file and change history |

## 7. Required register fields for the completed version

Every artifact row must include:
- Batch and artifact ID;
- exact filename and storage location;
- file identity/hash if available;
- version and created/modified dates;
- document status and authority level;
- owner/approver and approval evidence;
- supersedes/superseded-by links;
- phase, part, WP, domain owner and backend/frontend/shared classification;
- dependencies and conflicts;
- decision status, design status, implementation status and evidence status;
- acceptance criteria and evidence references;
- next action and accountable role.

## 8. Progress calculation rule

Do not calculate a single percentage from file count. Once the inventory is complete, calculate separate measures:
1. Source inventory coverage.
2. Contract closure coverage.
3. Owner decision closure.
4. Implementation completion.
5. Verification evidence completion.
6. P0 exit-gate completion.

A P0 overall percentage may be reported only if the owner accepts the weighting and denominator. Until then, report gate statuses and counts.

## 9. Immediate actions

1. Finish Library inventory for all 24 batches and component files.
2. Reconcile the master index against actual files; identify duplicate, missing, superseded and unindexed artifacts.
3. Complete source provenance and owner-decision evidence.
4. Reconcile WP-1–WP-6 plus Batch 17/18/24 cross-cutting contracts.
5. Prepare one consolidated owner-review pack.
6. Obtain formal contract freeze and separate implementation authorization.
7. Complete authorized implementation and independent evidence before P0 acceptance.


## 6. Workspace location verification — 2026-11-04
A follow-up filename search across `D:\MsP` located all seven P0 cross-batch control artifacts 01–07 in `D:\MsP\NEXTDECODE_WORKSPACE\05_IMPLEMENTATION_PLANS_AND_WORK_ORDERS\01_MASTER_PLANS_AND_WORK_ORDERS\`:

- `NEXTDECODE_P0_01_X12_Unified_Status_Vocabulary_Source_Precedence_Evidence_Classification.md`
- `NEXTDECODE_P0_02_P0_Implementation_Master_Plan.md`
- `NEXTDECODE_P0_03_Repository_Integration_and_Preservation_Map.md`
- `NEXTDECODE_P0_04_Engineering_Work_Orders_WP1_to_WP6.md`
- `NEXTDECODE_P0_05_P0_Acceptance_Evidence_and_Release_Gates.md`
- `NEXTDECODE_P0_06_Owner_Review_and_Implementation_Authorization_Checklist.md`
- `NEXTDECODE_P0_07_Master_Register_Change_Log_and_Document_Index.md`

This closes their *location* gap only. Their source-declared statuses remain unchanged: reconciliation candidate, planning candidate, logical path map, draft templates, candidate acceptance framework, review aid and coordination index respectively. No owner approval, contract freeze or implementation authorization is implied.

Contract 11 remains a separate missing source: the traceability matrix and data dictionary assign it to Multiformat Creation & Studio Intelligence / creation projects and studio production, but no corresponding file was located. Batch 16 was found in ChatGPT Library as a detailed contract candidate and converted to a local Markdown reading copy; its original DOCX remains in Library and its formatting/authority reconciliation is still open.
