# NEXTDECODE — MIGRATION MANIFEST AND PATH MAP

Version: 0.1.0-draft | Date: 2026-11-04
Migration target: D:\MsP\NEXTDECODE_WORKSPACE\
Operation: source files moved (cut/paste) into canonical folders. File contents were not intentionally edited during relocation.

## 1. Folder-level source mapping
| Former source | New canonical destination |
|---|---|
| D:\MsP root loose files | 00_CONTROL_AND_INDEX, 01_PRODUCT_AND_ARCHITECTURE, 05_IMPLEMENTATION_PLANS_AND_WORK_ORDERS, 09_ARCHIVE_AND_SUPERSEDED |
| Decision based Propesed\01(Prod&Arct) | 02_CANONICAL_CONTRACTS_AND_DATA\02_SHARED_INTELLIGENCE_CONTRACTS and 01_PRODUCT_AND_ARCHITECTURE |
| Decision based Propesed\01(Prod&Arct)\02review for 1 to 12 | 02_CANONICAL_CONTRACTS_AND_DATA\03_DATA_DICTIONARY_AND_TRACEABILITY and 01_PRODUCT_AND_ARCHITECTURE\03_INTEGRATION_AND_RESEARCH |
| Decision based Propesed\02(Artfact_01 to 12) | 02_CANONICAL_CONTRACTS_AND_DATA, 03_P0_GOVERNANCE_AND_DECISIONS, 06_AGENT_HANDOFFS, 07_TESTING_EVIDENCE_AND_RELEASE, 09_ARCHIVE_AND_SUPERSEDED |
| Decision based Propesed\02(Artfact_01 to 12)\04WPO | 03_P0_GOVERNANCE_AND_DECISIONS and 06_AGENT_HANDOFFS |
| Decision based Propesed\03(WP-0 final reconciliation) | 03_P0_GOVERNANCE_AND_DECISIONS\03_WP0_CLOSURE_AND_PRESERVATION |
| Decision based Propesed\04(WP_1 to 6)\WP1 | 04_WORKSTREAMS\WP1_DOMAIN_PERSISTENCE |
| Decision based Propesed\04(WP_1 to 6)\WP2 | 04_WORKSTREAMS\WP2_WORKFLOW_EXECUTION |
| Decision based Propesed\04(WP_1 to 6) WP3–WP6 files | Matching WP3–WP6 folders under 04_WORKSTREAMS |
| Decision based Propesed\05(P0_Impementation_plan) | 05_IMPLEMENTATION_PLANS_AND_WORK_ORDERS |
| Decision based Propesed\required file | 06_AGENT_HANDOFFS\01_HISTORICAL_HANDOFFS |
| D:\MsP\P1 | 08_P1_PRODUCT_EXPANSION\01_P1_PLANNING_PACKAGE |

## 2. Content placement rules used
- Product vision and broad blueprint documents → 01_PRODUCT_AND_ARCHITECTURE.
- Architecture Pipeline Parts 1–8 and diagrams → 01_PRODUCT_AND_ARCHITECTURE\02_SYSTEM_ARCHITECTURE.
- Canonical Contracts Pack, API/Event standard and reconciliations → 02_CANONICAL_CONTRACTS_AND_DATA\01_CANONICAL_CONTRACT_PACK.
- Shared Intelligence contracts → 02_CANONICAL_CONTRACTS_AND_DATA\02_SHARED_INTELLIGENCE_CONTRACTS.
- Data Dictionary v1.0 and Module-to-Contract Matrix → 02_CANONICAL_CONTRACTS_AND_DATA\03_DATA_DICTIONARY_AND_TRACEABILITY.
- Data Dictionary v1.1, located in ChatGPT Library, copied alongside v1.0 in the same canonical folder; preserve both until version precedence is confirmed.
- Accepted ADRs and decision registers → 03_P0_GOVERNANCE_AND_DECISIONS\01_ACCEPTED_DECISIONS.
- Owner review, freeze candidates and authorization packs → 03_P0_GOVERNANCE_AND_DECISIONS\02_OWNER_REVIEW_AND_AUTHORIZATION.
- WP-0 closure and preservation → 03_P0_GOVERNANCE_AND_DECISIONS\03_WP0_CLOSURE_AND_PRESERVATION.
- WP1–WP6 source specifications and reconciliations → matching folder under 04_WORKSTREAMS.
- Master plans/work orders and Batch DOCX packs → 05_IMPLEMENTATION_PLANS_AND_WORK_ORDERS.
- Agent protocols and prior handoffs → 06_AGENT_HANDOFFS.
- Acceptance and repository baseline records → 07_TESTING_EVIDENCE_AND_RELEASE.
- P1 package → 08_P1_PRODUCT_EXPANSION.
- Loose images, verified duplicate copy of Artifact 08, and original-source copies → 09_ARCHIVE_AND_SUPERSEDED.

## 3. Important items requiring attention
1. Shared Intelligence Contract 11 — Multiformat Creation & Studio Intelligence Model 1.0 — was located in ChatGPT Library and copied into the canonical local folder. Contracts 01–12 are now present locally. Its source-declared status remains working architecture contract, documentation only; reconcile its authority and dependencies before any freeze.
2. A file initially mislabelled as a second copy of Shared Intelligence Contract 02 was found in the Artifact folder. Content inspection identified it as the separate Unified Lifecycle & State Transition Standard 1.0; it has been moved into the canonical contract pack. It is not a duplicate.
3. Artifact 08 has multiple candidate/closure variants. All are retained in owner review; none is automatically declared authoritative by filename alone.
4. Batch 16 was located in ChatGPT Library as `NEXTDECODE_P0_Batch16_Domain_Interface_Contract_Closure_Pack.docx`; a Markdown reading copy now exists in the canonical batch folder. The original DOCX remains in Library and has not been mirrored to the local drive.
5. Batch 17–26 are in the local workspace. Batch 16 is now represented by a Markdown reading copy in the local workspace; its original DOCX remains in ChatGPT Library.
6. The seven P0 control artifacts 01–07 listed in Batch 03 Appendix A have now been located under 05_IMPLEMENTATION_PLANS_AND_WORK_ORDERS/01_MASTER_PLANS_AND_WORK_ORDERS. Their presence does not imply approval, completeness or implementation authorization.
7. Loose JPG reference images were archived as references, not accepted product design.
8. The historical P1 package remains draft and subordinate to P0.

## 4. Path migration warning
File relocation can invalidate hard-coded paths, relative links, or cross-document references inside existing files. The Markdown scan found no relative link references and no broken links. One stale P1 target directory was corrected. Canonical absolute workspace paths and historical path labels in this manifest are intentional; remaining non-Markdown path references and P1-to-P0 source references still require review. Do not move files again or create duplicate copies as a workaround.

## 5. Preservation
No source file was intentionally deleted. P0 source content was not intentionally edited as part of moving. The distinct Unified Lifecycle & State Transition Standard was preserved and reclassified; the verified duplicate Artifact 08 copy is archived. The legacy source folders may remain as empty directory shells; they are not the canonical workspace.

## 6. Format conversion and duplicate-resolution — 2026-11-04
- 27 DOCX files were converted into same-basename Markdown files. All original DOCX sources remain preserved. Two originals (Master Blueprint 2.0 and Where NEXTDECODE Stands Today) are stored under 09_ARCHIVE_AND_SUPERSEDED with SOURCE_ORIGINAL__ prefixes; the remaining originals are alongside their Markdown conversions.
- The historical readiness snapshot was converted to Markdown tables. Its original TXT is preserved under 09_ARCHIVE_AND_SUPERSEDED with a SOURCE_ORIGINAL__ prefix.
- The proposed strategy/technical blueprint TXT was already Markdown-formatted and was renamed to `.md` without content rewriting.
- Four files whose names ended in `.md.txt` were normalized to `.md`; their text content was not rewritten.
- Artifact 08 duplicate: full text comparison confirmed identical content. The canonical `.md` remains in owner review; the redundant copy is archived as `...IDENTICAL_DUPLICATE_ARCHIVED.md`.
- The file labelled as a second Contract 02 copy was not a duplicate. Its contents identify it as the Unified Lifecycle & State Transition Standard 1.0; it was moved to the canonical contract pack and renamed accordingly.
- Conversion preserves document-body paragraphs and tables. Original DOCX files remain preserved for visual/formatting comparison. Hyperlink targets, headers/footers, numbering semantics, drawings and complex layout still require targeted QA; do not treat Markdown output as semantic authority until this review is complete.
