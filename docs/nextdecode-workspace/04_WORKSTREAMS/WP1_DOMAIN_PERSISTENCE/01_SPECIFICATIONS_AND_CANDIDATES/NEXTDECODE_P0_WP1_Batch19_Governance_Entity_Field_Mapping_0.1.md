# NEXTDECODE — WP-1 Batch 19 Governance Entity & Field Mapping

**Document ID:** NEXTDECODE-P0-WP1-B19-GOV-MAP-0.1  
**Version:** 0.1  
**Date:** 4 November 2026  
**Work package:** WP-1 — Canonical Domain and Persistence Foundation  
**Status:** WORKING TRACEABILITY CANDIDATE — OWNER REVIEW REQUIRED  
**Implementation / schema-freeze status:** NOT AUTHORIZED

## 1. Purpose and boundary

This document reconciles the governance-related logical entities and field references in Batch 19 against the Canonical Data Dictionary v1.1, the WP-1 schema candidate v0.3, WP-5 governance reconciliation records and accepted CF-20/CF-21/CF-22 decisions.

It is a documentation crosswalk only. It does not approve a physical schema, add or rename fields, settle cardinality, define new state transitions, authorize migrations, or grant implementation authority. Batch 19 remains a design candidate pending owner freeze.

The objective is to make omissions and naming conflicts explicit before any schema or implementation work is considered.

## 2. Authority and source set

| Source | Version / section | Use in this crosswalk |
|---|---|---|
| Canonical Data Dictionary & Entity Ownership Registry | 1.1, §12.2–12.5 | Governance entity ownership and canonical logical fields |
| Batch 19 Database Schema, ERD & Persistence Specification | 0.1, §3, §5, §6, §8, §12 | Candidate entity catalogue, relationships and persistence notes |
| WP-1 Final Schema Contract Candidate | 0.3, §1–3 and governance boundary | WP-1 logical model boundary; owner review remains required |
| WP-1 Design Resolution Record | 0.2, §1–5 | Existing WP-1 decisions and unresolved design details |
| WP-5 Governance State & Decision Matrices | 0.1 | CF-20/21/22 separation and open decisions |
| WP-5 Batch 17 Transition-Edge Reconciliation | 0.1 | State/transition evidence classification |
| Contract 07 / CF-20, CF-21, CF-22 | Accepted source decisions | Governance authority and semantics |

**Authority rule:** the Data Dictionary is the current field-level ownership baseline; accepted CF decisions govern semantics. Batch 19 is a candidate and cannot silently override either. Where sources conflict or omit a detail, this document records the gap for owner disposition.

## 3. Entity mapping summary

| Governance concept | Data Dictionary v1.1 | Batch 19 | Mapping result |
|---|---|---|---|
| Rights evidence | Included as `evidence_refs` on AssetRightsRecord; Batch 19 separately lists RightsEvidence | RightsEvidence entity | Concept aligned; exact evidence-record fields and link cardinality require reconciliation |
| Rights determination | AssetRightsRecord | RightsDetermination | Concept aligned; field-name conflict: `rights_status` vs `rights_state` |
| Governance decision | GovernanceDecision | No separate entity in §5 catalogue | Missing explicit entity mapping |
| Review | Not separately defined in §12.1–12.5 as a standalone entity | Review | Batch 19 candidate needs owner/field authority and relationship clarification |
| Approval request | ApprovalRequest | No separate entity in §5 catalogue | Missing entity and request-to-decision relationship in candidate catalogue |
| Approval decision | ApprovalDecision, includes `approval_request_id` | ApprovalDecision | Concept aligned, but Batch 19 core fields omit the request link and complete CF-21 package binding |
| Central authorization | PublishingAuthorization in Data Dictionary | AuthorizationDecision in Batch 19 | Relationship and canonical record model unresolved; do not assume equivalence |
| Distribution operation | Contract 12 / Batch 19 distribution model | DistributionOperation | Must reference the exact authorization evidence required for the operation; exact FK/model remains open |

## 4. Ownership and semantic boundaries

1. Contract 07 owns quality, rights, governance, approval and central authorization.
2. Contract 12 owns distribution operations and external publishing reconciliation, subject to Contract 07 authorization.
3. Rights determination is not approval.
4. Approval is not authorization.
5. Authorization is not proof that an external operation occurred.
6. A distribution operation accepted or queued by an API is not proof of publication.
7. A new content/artifact/manifest version does not inherit an earlier approval automatically.
8. Typed references and database relationships do not themselves grant access, permission or authority.

No universal governance status field may collapse these independent dimensions.
## 5. M-01 — Rights evidence and rights determination

### 5.1 Canonical source fields

Data Dictionary §12.2 defines AssetRightsRecord with:
- `rights_record_id`
- `asset_id` or `artifact_version_id`
- `rights_holder_ref`
- `source_ref`
- `license_or_permission_ref`
- `permitted_uses`, `prohibited_uses`
- `territory`, `platform`, `duration`, where applicable
- `rights_status`
- `evidence_refs`
- `review_after`
- `rights_record_version_id`

The canonical CF-20 vocabulary is: UNKNOWN, PENDING_REVIEW, CLEARED, RESTRICTED, EXPIRED, REVOKED, DENIED.

Batch 19 separates RightsEvidence and RightsDetermination and uses `rights_state` for the determination. This separation may be a useful persistence decomposition, but it is not yet a frozen one-to-one physical mapping to AssetRightsRecord.

### 5.2 Reconciliation

- Preserve the semantic distinction between source evidence and an attributable rights determination.
- Do not rename `rights_status` to `rights_state`, or vice versa, without an explicit owner decision and compatibility plan.
- Do not treat `evidence_refs` as proof that a separate RightsEvidence entity has been fully specified.
- Preserve subject identity, exact version where applicable, intended use/purpose, source provenance, policy version, actor and decision time as required by accepted governance sources.
- Do not infer that a rights determination for one use, territory, platform or duration clears every other use.

**Open:** whether AssetRightsRecord is the canonical aggregate with evidence child records, whether RightsDetermination is a distinct append-oriented decision record, or whether Batch 19's two entities are a physical decomposition of the dictionary concept. Owner must settle entity identity and ownership before schema freeze.

## 6. M-02 — GovernanceDecision

Data Dictionary §12.3 defines GovernanceDecision with:
- `governance_decision_id`
- subject entity type, subject entity ID and subject version ID
- `action`
- `governance_disposition`: ELIGIBLE, PENDING_APPROVAL, BLOCKED, EXPIRED
- `policy_version`
- `hard_blockers`, `conditions`, `reason_codes`
- `decided_at`, `decision_actor_ref`

Batch 19 §5 does not list GovernanceDecision as a separate entity. It must not be silently collapsed into AuthorizationDecision: the former records a governance disposition under Contract 07; the latter represents a centralized authorization decision bound to a requested action/resource/destination and policy context.

**Required owner disposition:** decide whether GovernanceDecision is persisted as an authoritative append-oriented record, represented by an explicitly approved alternative, or held outside the minimum P0 persistence slice. Until then, retain it as a missing entity mapping, not as an assumed new table.

## 7. M-03 — Review, ApprovalRequest and ApprovalDecision

### 7.1 Review

Batch 19 lists Review with target version, reviewer, outcome and reason. The Data Dictionary §12 governance catalogue does not define Review as a separate standalone entity in the same field-level manner. Contract 07 §10.1 does require reviewer assignment/role, decision/rationale history and exact content version/artifact hash/manifest references.

Therefore, Review is source-supported as a governance activity/evidence concept, but its canonical record identity, ownership boundary, relationship to QualityAssessment and ApprovalRequest, and exact field set remain open.

### 7.2 ApprovalRequest

Data Dictionary §12.4 defines:
- `approval_request_id`
- `subject_entity_type`, `subject_entity_id`, `subject_version_id`
- `requested_action`
- `destination_context`
- `policy_version`
- `expires_at`
- `requested_by`

Batch 19 does not list ApprovalRequest as a separate entity in its §5 catalogue. The ERD depicts ContentVersion to Review/ApprovalDecision but does not establish the ApprovalRequest record and its relationship to ApprovalDecision.

Do not invent a full ApprovalRequest lifecycle enum. WP-5 reconciliation records that the request lifecycle is not completely specified by accepted sources.

### 7.3 ApprovalDecision

Data Dictionary §12.4 includes `approval_decision_id`, `approval_request_id`, decision, `decided_by`, `decided_at`, `reason`, and optional `signature_or_attestation_ref`.

CF-21 outcomes are APPROVED, REJECTED, CHANGES_REQUESTED, EXPIRED, REVOKED. Contract 07 §10.2's legacy WITHDRAWN token is a documented conflict; it must not be silently aliased to REVOKED.

Batch 19 lists ApprovalDecision but its catalogue summary does not show `approval_request_id`. This is a traceability omission, not permission to choose a different relationship.

### 7.4 Exact review-package binding

CF-21 requires approval to bind to the immutable review package and exact content/artifact/manifest version plus checksum reviewed. The Data Dictionary acknowledges that its current field list does not fully define the representation.

Keep the representation OPEN. Do not invent names such as `review_package_id`, `manifest_checksum` or a new join table in this crosswalk. The owner must choose the exact representation against the authoritative review-package and artifact contracts.
## 8. M-04 — AuthorizationDecision and PublishingAuthorization

Batch 19 lists AuthorizationDecision under Central Authorization, with action, resource reference, resource version, destination, policy version, validity window and decision. Its design principle is centralized authorization, default deny and execution-time revalidation.

Data Dictionary §12.5 defines PublishingAuthorization with:
- `publishing_authorization_id`
- `approval_decision_id`, when required
- `subject_version_id`
- `distribution_package_version_id`
- `channel_account_id`
- `requested_action`
- `policy_version`
- `authorized_by`, `authorized_at`, `expires_at`
- `authorization_status`
- `idempotency_key`

The source materials do not yet establish whether PublishingAuthorization is the canonical persisted authorization record, whether AuthorizationDecision is the decision/evaluation record that produces it, or whether one of these is an alternate naming/model proposal.

**Do not** silently equate the two, create duplicate independent authorities, or infer a one-to-many relationship from the ERD's ApprovalDecision → AuthorizationDecision line.

**Owner decisions required:**
1. Select the canonical authorization entity/record model and its owning contract.
2. Define whether an authorization decision and a resulting usable authorization grant are separate records or one record with explicitly distinct semantics.
3. Define how any required approval decision, exact subject version, distribution package version, channel account, action, policy version, validity and idempotency binding is represented.
4. Define revocation/expiry and execution-time revalidation references without inventing state transitions.

Until resolved, keep both source names visible in the crosswalk and mark their mapping OPEN.

## 9. DistributionOperation relationship

Batch 19 places DistributionOperation under Distribution Studio and separates it from ExternalOperationEvent. Contract 12 owns distribution operations; Contract 07 owns central authorization.

The persistence design must preserve the distinction between:
- the exact distribution package/version and destination/account;
- the authorization evidence required for the requested action;
- the operation attempt and provider-observed outcome;
- reconciliation evidence when the external result is unknown.

The exact FK/reference from DistributionOperation to AuthorizationDecision or PublishingAuthorization is not frozen by this crosswalk. The owner must choose the canonical target after §8 is resolved. Do not add a guessed `authorization_id` field or assume that an approval decision is sufficient.

## 10. Field and relationship conflict register

| ID | Conflict / omission | Evidence | Safe treatment pending owner decision |
|---|---|---|---|
| MAP-01 | `rights_status` vs `rights_state` | Dictionary §12.2 vs Batch 19 §5/§8 | Preserve both source terms; no rename or alias |
| MAP-02 | AssetRightsRecord vs RightsEvidence + RightsDetermination | Dictionary §12.2 vs Batch 19 §5 | Entity decomposition unresolved |
| MAP-03 | GovernanceDecision absent from Batch 19 catalogue | Dictionary §12.3 vs Batch 19 §5 | Record missing mapping; do not collapse into authorization |
| MAP-04 | Review canonical field set/owner unclear | Contract 07 §10.1 and Batch 19 §5 | Keep Review candidate; reconcile against QualityAssessment and approval |
| MAP-05 | ApprovalRequest absent from Batch 19 catalogue | Dictionary §12.4 vs Batch 19 §5 | Add no physical entity until owner disposition |
| MAP-06 | `approval_request_id` absent from Batch 19 ApprovalDecision summary | Dictionary §12.4 vs Batch 19 §5/§12 | Preserve source relationship as a required reconciliation item |
| MAP-07 | CF-21 review-package/version/checksum binding representation incomplete | CF-21 and Dictionary §12.4 | Keep exact representation OPEN |
| MAP-08 | AuthorizationDecision vs PublishingAuthorization | Batch 19 §5/§12 vs Dictionary §12.5 | No equivalence or duplicate authority assumption |
| MAP-09 | DistributionOperation authorization reference unresolved | Batch 19 §3/§5/§12 and Contract 12 boundary | Do not invent FK; resolve after MAP-08 |
| MAP-10 | ApprovalRequest lifecycle not fully specified | WP-5 governance matrix / Batch 17 reconciliation | Do not invent enum or transitions |
| MAP-11 | Legacy CF-21 WITHDRAWN token conflict | Contract 07 §10.2 vs accepted CF-21 | Preserve conflict; owner disposition required |

## 11. Owner decision queue

| Decision ID | Owner question | Minimum evidence needed |
|---|---|---|
| B19-GOV-01 | Is AssetRightsRecord one canonical aggregate or a logical grouping decomposed into RightsEvidence and RightsDetermination? | Contract 07, CF-20 and Data Dictionary |
| B19-GOV-02 | Which canonical field name is authoritative: `rights_status` or `rights_state`? | Accepted field contract and compatibility disposition |
| B19-GOV-03 | How is GovernanceDecision represented in the canonical persistence model? | Contract 07 ownership and P0 vertical-slice scope |
| B19-GOV-04 | What is the canonical Review record, and how does it relate to QualityAssessment and ApprovalRequest? | Contract 07 §10.1, QA contract and review-package contract |
| B19-GOV-05 | Is ApprovalRequest a persisted entity in the approved model, and what is its relationship to ApprovalDecision? | Dictionary §12.4 and CF-21 |
| B19-GOV-06 | What exact immutable package/version/checksum linkage implements CF-21? | Review package, Artifact/Manifest contracts and CF-21 |
| B19-GOV-07 | How is legacy WITHDRAWN resolved against accepted CF-21 REVOKED? | Contract 07 §10.2 and owner compatibility decision |
| B19-GOV-08 | Are AuthorizationDecision and PublishingAuthorization separate records or alternate models? | CF-22, Dictionary §12.5 and Batch 19 |
| B19-GOV-09 | Which exact authorization record must DistributionOperation reference? | Contract 12 and CF-22 |
| B19-GOV-10 | What is the approval-request lifecycle and which transitions are authoritative? | Accepted state-machine owner decision; not Batch 17 candidate tokens alone |
| B19-GOV-11 | Which fields are direct FKs versus typed references/link records for governance relationships? | Relational ownership boundaries and integrity requirements |

## 12. Foreign-key and integrity traceability

The following are logical integrity requirements, not frozen physical FK definitions:

- ApprovalDecision must be traceable to its ApprovalRequest if the owner confirms the Data Dictionary relationship.
- Governance decisions and rights determinations must retain subject identity and exact subject version where applicable.
- CF-21 approval evidence must be traceable to the immutable review package and exact content/artifact/manifest version and checksum.
- Authorization must be bound to the requested action, exact resource/version, destination/account and policy/validity context.
- DistributionOperation must be traceable to the exact authorization evidence used for the operation.
- Rights evidence, determinations, reviews, approvals, authorizations and external-operation outcomes must preserve attributable history; no destructive cascade may erase required evidence.
- Polymorphic entity references do not provide ordinary FK enforcement. Batch 19 §6 already recognizes typed link tables or explicit FKs as possible high-integrity strategies; the exact strategy remains an owner/schema decision.
- A typed reference is not a permission grant, ownership transfer or authorization.

## 13. Scope and implementation restrictions

This mapping does not authorize:
- SQL DDL, ORM models, migrations, seed data or database changes;
- code or repository edits, test creation/execution, or Git operations;
- changes to Batch 19, the Data Dictionary, Contract 07, Contract 12, Artifact 07 or accepted CF decisions;
- enum/transition freeze, field rename, cardinality selection or physical FK selection;
- agent dispatch or implementation execution;
- provider activation, spending, deployment, generation, upload or publishing.

Qoder remains the sole writer for the current governance-closure implementation milestone only when separately authorized. OpenCode and Copilot retain their assigned read-only review scopes; Kilo remains an independent read-only QA/security reviewer after implementation/evidence is authorized and complete; Antigravity remains conditional and targeted to UI. This document does not dispatch any agent.

## 14. Acceptance criteria and handoff

- [x] Batch 19 governance entities compared against Data Dictionary v1.1 §12.2–12.5.
- [x] CF-20 rights vocabulary and rights naming conflict explicitly recorded.
- [x] GovernanceDecision and ApprovalRequest omissions recorded.
- [x] ApprovalDecision request linkage and CF-21 exact-version/package/checksum binding gap recorded.
- [x] AuthorizationDecision / PublishingAuthorization ambiguity recorded without assuming equivalence.
- [x] DistributionOperation authorization relationship left open.
- [x] Owner decisions listed with evidence requirements.
- [x] Implementation and schema-freeze boundaries stated.
- [ ] Owner dispositions recorded.
- [ ] Canonical field/relationship mapping approved and incorporated into an owner-frozen schema contract.
- [ ] Documentation QA and cross-document link validation completed after control-register updates.

**Handoff status:** Documentation crosswalk drafted. Owner review required. No schema freeze, agent dispatch or implementation authorization implied.

**Next dependency:** owner disposition of B19-GOV-01 through B19-GOV-11, plus reconciliation with Contract 12 and Artifact 07 before any physical governance persistence contract can be frozen.
