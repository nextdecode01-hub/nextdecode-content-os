# Data Dictionary 1.0 vs 1.1 — Source Comparison

**Date:** 2026-11-04  
**Status:** Evidence-based version comparison; not an owner decision or contract freeze  
**Compared files:**
- `NEXTDECODE_Canonical_Data_Dictionary_Entity_Ownership_Registry_1.0.md`
- `NEXTDECODE_Canonical_Data_Dictionary_Entity_Ownership_Registry_1.1.md`

## 1. Comparison result

| Measure | v1.0 | v1.1 |
|---|---:|---:|
| Lines | 1,589 | 1,611 |
| Bytes | 44,898 | 46,836 |
| SHA-256 | `bc48cef0bf7f06f2de55a27237ac60c167f507ebbc39ad1ff67c179a7c8d4d85` | `a060c0ec6294b29a1ea938b27b0fc591b21fd6e67a99a80bc92108db1021fa5f` |
| Headings | 118 | 119 |

- 118 headings are common; v1.1 adds one heading, **Wave A source-authority propagation (v1.1)**.
- Normalized line-sequence similarity: approximately 98.7%.
- The comparison found focused source-authority and rights/approval updates rather than a broad data-model redesign.

## 2. Substantive changes in v1.1

### 2.1 Rights vocabulary — CF-20

v1.0 listed:
- `CLEARED`
- `RESTRICTED`
- `PENDING_VERIFICATION`
- `PROHIBITED`
- `UNKNOWN`

v1.1 aligns to the accepted CF-20 vocabulary:
- `UNKNOWN`
- `PENDING_REVIEW`
- `CLEARED`
- `RESTRICTED`
- `EXPIRED`
- `REVOKED`
- `DENIED`

v1.1 includes documentation-only compatibility notes:
- Historical `PENDING_VERIFICATION` → `PENDING_REVIEW`.
- Historical `PROHIBITED` → `DENIED`.
- It explicitly says these are not perfect semantic equivalences and do not authorize migration, backfill or runtime coercion.
- `EXPIRED` and `REVOKED` remain distinct from `DENIED`.
- Local `reuse_rights: permitted` must not be mapped to `CLEARED`.

### 2.2 Approval vocabulary — CF-21

v1.0 listed:
- `APPROVED`
- `REJECTED`
- `EXPIRED`
- `REVOKED`

v1.1 adds `CHANGES_REQUESTED`, aligning the approval vocabulary with accepted CF-21.

### 2.3 Exact review binding — CF-21

v1.1 explicitly requires each approval to bind to:
- The immutable review package.
- The exact content/artifact/manifest version reviewed.
- The checksum of that reviewed version.

The source also says the current field list does not fully define the review-package/manifest/checksum linkage representation. That field-level schema remains **OPEN**; do not invent field names in this propagation pass. A new version does not inherit approval automatically.

### 2.4 Authority and safety notice

v1.1 explicitly states:
- It aligns vocabulary to accepted CF-20 and CF-21.
- It does not freeze the detailed data model.
- Rights-token compatibility references are documentation-only.
- Detailed contract freeze and implementation authorization remain NOT GRANTED.

## 3. Recommended working treatment

1. Preserve v1.0 unchanged as historical provenance.
2. Use v1.1 as the **latest working reference for CF-20/CF-21 vocabulary and binding requirements**, subject to the accepted owner decision record and implementation reference.
3. Do not silently claim that v1.1 is formally owner-ratified as the canonical replacement for v1.0. The source declares version 1.1 and adds focused updates, but this comparison did not find an explicit v1.0 supersedes declaration.
4. Do not migrate, backfill, coerce or reinterpret existing rights data from the compatibility notes.
5. Keep the CF-21 review-package/version/checksum field representation open until the schema owner and owner review process approve exact fields.
6. Reconcile Contract 07, Contract 11, API/Event contracts, Artifact 08 and WP1/WP5 before detailed freeze.

**Conclusion:** v1.1 is a focused, more current working revision that aligns the Data Dictionary with accepted CF-20/CF-21 decisions. It should guide further documentation reconciliation, while v1.0 remains preserved. Neither version is a frozen implementation schema.
