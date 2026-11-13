# NEXTDECODE P0 — Wave A Documentation Propagation Report

**Document ID:** ND-P0-WA-PROP-REPORT-001  
**Version:** 0.1  
**Date:** 3 November 2026  
**Status:** Documentation propagation completed; consolidated detailed contract freeze remains pending  
**Authorization:** Owner explicitly authorized bounded documentation-only propagation on 3 November 2026.

## 1. Scope and boundaries

This package applies the accepted Wave A source-authority determinations to subordinate documentation. It does not create or amend owner decisions.

**Included:** documentation updates, version increments, source-authority notes, vocabulary alignment, derived-register provenance and documentation-only consistency review.

**Excluded:** Artifact 08 owner decision records, repository or Git activity, code, software tests, schema execution, migrations, agent coding tasks, credentials, provider activation, infrastructure, production generation, upload, publishing, merge or deployment.

## 2. Authority preserved

- ADR-001–ADR-010 remain accepted as high-level architecture decisions.
- CF-01–CF-15 remain explicitly accepted by the owner.
- CF-16–CF-21 remain accepted under the standing delegation rule.
- CF-22 remains the explicit owner choice, Option A — centralized authorization.
- CF-23 remains accepted under the standing delegation rule.
- CF-24 remains the explicit no-paid-services constraint; provider and operational selections remain deferred.
- CF-20 rights vocabulary: `UNKNOWN`, `PENDING_REVIEW`, `CLEARED`, `RESTRICTED`, `EXPIRED`, `REVOKED`, `DENIED`.
- CF-21 approval vocabulary: `APPROVED`, `REJECTED`, `CHANGES_REQUESTED`, `EXPIRED`, `REVOKED`.
- ODR-01–ODR-22 remain a derived working index, not 22 independently verified original owner decisions. ODR-22 remains provisional.
- Artifact 08 v1.1 supplements, but does not supersede, Artifact 08 v1.0.
- Detailed contract freeze remains **NOT GRANTED**. Implementation authorization remains **NOT GRANTED**.

## 3. Updated documents

| Updated artifact | New version | Propagation |
|---|---:|---|
| P0 Detailed Contract Freeze Pack | 1.1 | CF-20 canonical rights vocabulary; documentation-only legacy mapping; CF-21 full approval outcomes and exact-version binding; freeze boundary |
| Canonical Data Dictionary & Entity Ownership Registry | 1.1 | Rights and approval vocabularies aligned; incomplete review-package/manifest/checksum field representation explicitly OPEN |
| Architecture Decision Records Pack | 1.1 | ADR-001–010 accepted high-level status overlay; historical draft statuses reconciled; ADR-009 legacy rights vocabulary marked historical |
| Architecture Decision Register | 1.1 | ADR-001–010 accepted with Artifact 08 provenance; CF acceptance routes recorded; detailed contract freeze and implementation gates kept separate |
| Decision Resolution Register | 0.2 | ODR register classified as derived; ODR-22 changed from carried-forward to provisional grouping |
| Master Register Change Log & Document Index | 0.2 | Added current Wave A source-authority documents, propagated versions, current gates and ODR provenance rules |
| Batch 18 API/Event Schema Specification Pack | 0.2 | Complete CF-20/CF-21 token sets, exact-version binding and unsupported/legacy-value handling; field names and schema details remain OPEN |
| Batch 19 Database Schema/ERD/Persistence Specification | 0.2 | Artifact 08 lineage; CF-20/CF-21 vocabulary provenance; `rights_state` vs `rights_status` and `approval_outcome` vs `decision` naming reconciliation explicitly OPEN |

## 4. Existing documents verified and intentionally not rewritten

- **Batch 16 — Domain & Interface Contract Closure Pack:** already contains the exact CF-20 and CF-21 vocabularies, Artifact 08 v1.0/v1.1 lineage, and ODR-22 provisional treatment. No redundant edit made.
- **Batch 17 — State-Machine & Transition Catalogue:** already contains the exact CF-20/CF-21 vocabularies, separates rights/approval/authorization state ownership, and identifies accepted vocabularies versus proposed lifecycle details. No redundant edit made.
- **Batch 02 — Decision & Owner-Reserved Register:** already carries the correct ADR/CF acceptance routes and owner-reserved boundaries. No redundant edit made.
- **ODR-22 Source Reconciliation & Decision-Register Integrity 0.1:** retained as the provenance evidence source; not rewritten.
- **Artifact 08 v1.0 and v1.1:** not modified.

## 5. Important compatibility and schema notes

1. `PENDING_VERIFICATION` → `PENDING_REVIEW` and `PROHIBITED` → `DENIED` are documentation-compatibility references only. They do not establish perfect semantic equivalence and do not authorize data migration, backfill or runtime coercion.
2. `EXPIRED` and `REVOKED` remain distinct from `DENIED`.
3. Local `reuse_rights: permitted` must not be mapped to `CLEARED`.
4. CF-21 approval must bind to the immutable review package and exact content/artifact/manifest version plus checksum. The precise field-level representation remains OPEN where the canonical dictionary does not define it.
5. Batch 19 candidate field names differ from the current Data Dictionary (`rights_state` vs `rights_status`; `approval_outcome` vs `decision`). This is explicitly OPEN for schema-owner reconciliation; no rename or alias was silently introduced.
6. Unsupported enum values must not be silently dropped or coerced; protected actions remain fail-closed.

## 6. Documentation-only validation performed

- Checked the CF-20 and CF-21 token sets across the updated detailed contract, data dictionary, Batch 18 and Batch 19.
- Confirmed the old rights tokens occur only in explicitly labelled documentation-compatibility or historical-draft notes in the updated artifacts.
- Confirmed the ADR register and ADR pack carry ADR-001–ADR-010 as accepted high-level decisions.
- Confirmed ADR-011 and later decisions remain open/deferred as previously recorded.
- Confirmed ODR-22 no longer appears as a carried-forward accepted decision in the updated working register.
- Confirmed Artifact 08 v1.0/v1.1 relationship is explicitly supplementary, not superseding.
- Confirmed detailed contract freeze and implementation authorization remain ungranted.

No software tests, repository inspection, code execution against the product, migrations or production operations were performed.

## 7. Remaining owner-review docket

The following remain open and must not be treated as accepted by this propagation:

- Consolidated detailed contract freeze for exact versions of the subordinate documents.
- Exact review-package/manifest/checksum field representation for CF-21 approval binding.
- Batch 19 canonical field-name reconciliation (`rights_state` / `rights_status`; `approval_outcome` / `decision`).
- Rights evidence taxonomy, use/purpose model and evidence sufficiency rules.
- Approval reviewer roles, expiry/revocation timing and delegation details.
- Remaining entity cardinalities, physical schema details, lifecycle enums, API schema fields, compatibility/error behavior and other open contract details.
- Any separate implementation authorization after detailed contract freeze.

## 8. Change manifest

The original source files remain preserved. The updated versions are new versioned artifacts; no original source file was overwritten. The ZIP package contains the eight updated documents, the propagation report and the README.
