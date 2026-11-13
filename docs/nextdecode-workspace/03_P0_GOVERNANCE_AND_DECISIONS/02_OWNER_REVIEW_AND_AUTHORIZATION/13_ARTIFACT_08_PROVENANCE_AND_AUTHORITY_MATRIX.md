# Artifact 08 — Provenance, Authority & Version Matrix

**Created:** 2026-11-04  
**Status:** Evidence-based reconciliation aid; not an owner decision and not a contract freeze  
**Purpose:** Distinguish the accepted owner decision record from reconciliation candidates, detailed contract proposals and review worksheets. Prevent filename/version recency from being mistaken for authority.

## 1. Governing conclusion

The source set supports the following distinction:

1. **ADR-001–ADR-010 and CF-01–CF-24 are recorded as accepted owner decisions** in the owner decision record and the accepted-decision implementation reference.
2. **The detailed P0 contract baseline is not frozen.** The owner decision record explicitly says final consolidated contract freeze approval is pending. The v1.1 and v1.2 documents also say owner confirmation is pending.
3. **Implementation authorization is not granted** by any of these Artifact 08 documents.
4. No candidate should be promoted to the authoritative frozen baseline solely because it has a higher version number or a more consolidated title.

## 2. Source inventory and authority roles

| Source | Version / date | Source-declared status | Role and authority interpretation |
|---|---|---|---|
| `NEXTDECODE_Artifact_08_Consolidated_Owner_Decision_Record_Contract_Freeze_Closure_1.0.md` | 1.0 / 31 Oct 2026 | Consolidated owner-review record; final freeze approval pending | Primary consolidated record of the owner CF-01–CF-24 decision history and ADR-001–ADR-010. Carries accepted decisions; does not freeze every detailed proposal. |
| `NEXTDECODE_Artifact_08_Implementation_Reference_Accepted_Contract_Decisions_1.0.md` | 1.0 / 31 Oct 2026 | Implementation reference / decision-reconciliation aid | Explicitly records CF-01–CF-15 as owner-accepted, CF-16–CF-21 under standing delegation, CF-22 as explicit Option A, CF-23 under standing delegation and CF-24 as no-paid-services. Not implementation authorization or detailed freeze. |
| `NEXTDECODE_Artifact_08_P0_Detailed_Contract_Freeze_Open_Decisions_Closure_1.0.md` | 1.0 / 31 Oct 2026 | Consolidated contract-review baseline; owner review required | Broad detailed review framework and open decisions. Explicitly says detailed contract freeze not yet approved. |
| `NEXTDECODE_P0_Detailed_Contract_Freeze_Pack_1.0.md` | 1.0 / 31 Oct 2026 | Proposed detailed contract baseline; owner review required | Detailed proposed contract clauses and schemas. Proposal material, not frozen. |
| `Artifact_08_Contract_Reconciliation_and_Freeze_Candidate_1.1.md` | 1.1 / 1 Nov 2026 | Reconciliation candidate; owner confirmation required | Explicitly says it supersedes nothing and supplements Artifact 08 v1.0. Reconciliation layer, not replacement. |
| `NEXTDECODE_Artifact_08_v1.2_Consolidated_Freeze_Candidate.md` | 1.2 / 1 Nov 2026 | Consolidated freeze candidate; owner confirmation pending | More recent consolidated candidate. It explicitly defers to the accepted owner decision record and implementation reference for CF-01–CF-24, warns about the older CF-01–CF-25 numbering discrepancy and says its own proposals are not frozen. |
| `NEXTDECODE_P0_Contract_Review_and_Freeze_Decision_Sheet_1.0.md` | 1.0 | Owner review worksheet — NOT FROZEN | Decision instrument for ACCEPT / ACCEPT WITH AMENDMENT / DEFER / REJECT. No completed owner response is evidenced in the reviewed opening section. |
| `NEXTDECODE_P0_Owner_Review_Contract_Freeze_Decision_Record_0.1.md` | 0.1 / 1 Nov 2026 | Owner decision draft — NOT YET APPROVED | Draft owner decision record consolidating WP1–WP6 review. Not approved by its own status. |

## 3. Verified source identities

SHA-256 hashes were computed for the seven main review/candidate files in the owner-review folder on 2026-11-04. They identify the inspected copies; they do not prove owner approval.

| File | Bytes | Lines | SHA-256 |
|---|---:|---:|---|
| Artifact_08_Contract_Reconciliation_and_Freeze_Candidate_1.1.md | 19,180 | 456 | `78f81143ff38ff6f63210bca6654dfe81441f3ece113b1ece7a59bc2f1ca729f` |
| NEXTDECODE_Artifact_08_Consolidated_Owner_Decision_Record_Contract_Freeze_Closure_1.0.md | 15,282 | 200 | `02c5e262c803e549c5a3528c533b3126797f1ef04940ebb7a07364dc2a3e4940` |
| NEXTDECODE_Artifact_08_P0_Detailed_Contract_Freeze_Open_Decisions_Closure_1.0.md | 41,899 | 1,016 | `d1480014498e554fee449acb50ce30ff185da8de710e139fe26c6c20f3200b29` |
| NEXTDECODE_Artifact_08_v1.2_Consolidated_Freeze_Candidate.md | 31,244 | 508 | `183915734ba4cf1967d444e270c772efb836b672ca04e150c6cbc943a7e1be10` |
| NEXTDECODE_P0_Detailed_Contract_Freeze_Pack_1.0.md | 35,075 | 1,189 | `c34a4663ff50009343d1197d50dc9b267f5802bdab3669368f27ae0c0aef8eba` |
| NEXTDECODE_P0_Contract_Review_and_Freeze_Decision_Sheet_1.0.md | 12,542 | 338 | `629fd957ee33a25bd2618849227ab2e2b6953b98710ced829078db8cda532c27` |
| NEXTDECODE_P0_Owner_Review_Contract_Freeze_Decision_Record_0.1.md | 18,871 | 317 | `d06499a2be90b17135aec47ddb5846889f78dc1a845542e057e7ec420da1d07e` |

## 4. Duplicate status

The two files previously sharing the exact Artifact 08 consolidated owner-decision filename were compared in full. Their content was identical. One active Markdown copy remains in this folder; the second is retained in `09_ARCHIVE_AND_SUPERSEDED` with `IDENTICAL_DUPLICATE_ARCHIVED` in its name.

The file previously labelled as a second copy of Shared Intelligence Contract 02 was not a duplicate. It is the separate **Unified Lifecycle & State Transition Standard 1.0** and has been reclassified into the canonical contract pack.

## 5. Numbering and source conflicts

- Accepted owner decision numbering is CF-01–CF-24, as recorded by the owner decision record and implementation reference.
- The v1.2 candidate explicitly warns that an older review matrix uses CF-01–CF-25 with a different topic breakdown. Do not mix the older numbering into implementation work orders or schema identifiers.
- The v1.2 candidate intentionally does not reconstruct missing exact wording for CF-03–CF-12 and CF-15–CF-19 from summaries. The exact accepted wording must be imported from the authoritative owner decision record/reference.
- Contract 11 is referenced by the Module-to-Contract Traceability Matrix and Data Dictionary as **Multiformat Creation & Studio Intelligence**, owning creation projects and studio production. The source `NEXTDECODE_Shared_Intelligence_Core_Contract_11_Multiformat_Creation_Studio_Intelligence_Model_1.0.md` was found in ChatGPT Library and copied into the local canonical contract folder on 2026-11-04. Its source-declared status is working architecture contract — documentation only; it is not frozen.
- The Unified Lifecycle & State Transition Standard 1.0 has been located, but its authority/version relationship with the Canonical Contracts Pack, API/Event standard, Contract 11 and WP2/WP4 state specifications still requires reconciliation.

## 6. Recommended handling

1. Treat the consolidated owner decision record and implementation reference as the sources for accepted ADR/CF decisions.
2. Treat v1.0 detailed closure/contract packs, v1.1 reconciliation and v1.2 consolidated candidate as review/design sources, not frozen contracts.
3. Keep the decision worksheet and owner review draft as instruments for an explicit owner decision; do not fill or infer approval.
4. Build a clause-by-clause contract status matrix with exact source section, accepted decision ID, candidate clause, conflict, owner decision required, and evidence.
5. Only after the owner explicitly approves a specific revision should it be marked FROZEN. Implementation authorization remains a separate decision.

**No owner decision has been created by this matrix. No contract freeze, repository work or implementation authorization is implied.**
