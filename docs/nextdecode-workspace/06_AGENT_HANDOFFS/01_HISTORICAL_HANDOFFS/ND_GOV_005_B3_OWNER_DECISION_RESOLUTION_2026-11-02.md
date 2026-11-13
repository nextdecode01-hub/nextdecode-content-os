# NEXTDECODE — ND-GOV-005 B3 Owner Decision Resolution

**Record date:** 2026-11-02  
**Project:** NEXTDECODE  
**Work package:** ND-GOV-005 — B3 remediation  
**Record type:** Owner decision record

## 1. Binding owner disposition

| Item | Owner decision |
|---|---|
| B3 remediation | **APPROVED** |
| Future compatibility mapping | **DEFERRED** |
| Integration / merge | **NOT AUTHORIZED** |
| Production publishing | **NOT AUTHORIZED** |

This approval is limited to the B3 remediation scope defined by the final remediation specification. It does not grant permission to integrate, merge, deploy, generate production content, upload externally, or publish.

## 2. Rights-state boundary

Contract 07 owns the canonical rights assessment. CF-20 canonical rights states are:

- `UNKNOWN`
- `PENDING_REVIEW`
- `CLEARED`
- `RESTRICTED`
- `EXPIRED`
- `REVOKED`
- `DENIED`

The local value `reuse_rights: permitted` is only an R9 compatibility input under ND-GOV-005. It must **not** be automatically mapped to `CLEARED` or to any other canonical rights state. Future compatibility mapping remains deferred and requires a separate owner decision.

## 3. Approved implementation boundary

Preserve the frozen ND-GOV-005 requirements R1–R6 without silently changing their meaning:

- **R1 — Normalize `reuse_rights`:** dictionary input uses its `status`; string input is used directly; trim and lowercase; permit only the exact normalized value `permitted`.
- **R2 — Collection shapes:** support persisted list and in-memory dictionary collection shapes. Malformed collections or cards block.
- **R3 — Missing cutouts:** a missing `cutouts` key is treated as an empty list, subject to the R5 zero-cutout evidence requirement.
- **R4 — Non-empty cards:** require a `rights_gate` dictionary with integer `checked == len(cards)` and integer `blocked == 0`. Booleans must not be accepted as integers. Missing, malformed, or contradictory evidence blocks. Raise `PublishNotAuthorized(code="blocked_rights")`.
- **R5 — Zero-cutout proof:** require `evidence.cutout_selection` to be a dictionary with a non-empty string `reason` and integer `budget`. Do not use brittle exact-reason matching. Do not consult `rights_gate.publish_ready` in the zero-cutout case.
- **R6 — Evidence persistence:** persist `cutout_selection` in pipeline evidence.

Out of scope: changing global rights policy; changing the meaning of `permitted`; computing `cutouts.rights_gate`; licensing `visual_quality` assets; or changing storyboard reason logic.

## 4. Evidence status

The implementation report states that work was performed in an isolated worktree `/tmp/nd_gov_005`, based on R9 baseline `9d38f81`, with changes to:

- `publish_authorization.py`
- `app/script/pipeline.py`
- `tests/governance_fixtures.py`
- `tests/test_publish_governance.py`

The report states that 29/29 targeted tests passed and notes two pre-existing unrelated `motion_director` failures. It also reports an acceptance bundle with SHA-256:

`5759b58b76a5776823fa937d2ba1e6181e56983a54bcd107362eb740806a3a67`

These are **report-backed claims, not independent verification**. The bundle, test results, baseline, and implementation must be independently inspected before any later integration decision. A stock provider mapping to `permitted` is implementation behavior; it is not proof that every asset is licensed for every intended use.

## 5. Authority and safety restrictions

Unless separately authorized by the owner, do not:

- integrate, merge, commit, push, deploy, or promote;
- run production generation or production publishing;
- upload content externally or publish publicly;
- change credentials, permissions, or provider configuration;
- activate paid services;
- perform destructive Git operations, including reset, revert, stash, cleanup, or broad staging;
- overwrite or discard existing work.

The implementation report is not independent verification. Approval of B3 remediation is not approval of integration or production publishing.

## 6. Required status language

Use these exact distinctions in future reports:

- B3 remediation: **APPROVED**
- Future compatibility mapping: **DEFERRED**
- Integration / merge: **NOT AUTHORIZED**
- Production publishing: **NOT AUTHORIZED**
- Independent verification: **PENDING**
