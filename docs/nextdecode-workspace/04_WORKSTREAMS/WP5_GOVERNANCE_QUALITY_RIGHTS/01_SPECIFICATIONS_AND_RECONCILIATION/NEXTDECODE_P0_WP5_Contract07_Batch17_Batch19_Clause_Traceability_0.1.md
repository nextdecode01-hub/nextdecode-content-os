# NEXTDECODE P0 — WP5 Contract 07 / Batch 17 / Batch 19 Clause Traceability

**Document ID:** NEXTDECODE-P0-WP5-C07-B17-B19-XREF-0.1  
**Version:** 0.1  
**Updated:** 2026-11-04  
**Status:** WORKING EVIDENCE CROSSWALK — OWNER REVIEW REQUIRED  
**Scope:** Documentation-only reconciliation of governance semantics, state transitions and persistence field representation.  
**Detailed contract freeze:** NOT GRANTED  
**Implementation authorization:** NOT GRANTED

---

## 1. Purpose and boundary

This crosswalk turns the existing Contract 07 CF-20/CF-21 reconciliation into a clause-linked dependency record across the accepted decision baseline, Contract 07, WP5, Data Dictionary v1.1, Batch 17 and Batch 19.

It is a working evidence artifact. It does not amend Contract 07, Batch 17, Batch 19 or the Data Dictionary; create an owner decision; select a physical schema; authorize migration; or freeze any contract.

The original sources remain unchanged. Any proposed wording below is explicitly a reconciliation disposition for owner review, not an accepted change.

## 2. Authority and source precedence

1. **Accepted owner decisions:** Artifact 08 Implementation Reference / Accepted Contract Decisions 1.0, especially CF-20 (rights), CF-21 (approval) and CF-22 (centralized authorization). The consolidated decision record states CF-16–CF-21 were accepted under standing delegation and CF-22 was explicitly accepted as Option A.
2. **Data Dictionary v1.1:** latest working propagation of CF-20/CF-21 vocabulary and entity fields. Its own header says it is a working architecture standard, not frozen; it does not supersede Data Dictionary v1.0 or Artifact 08 v1.0.
3. **Contract 07 v1.0:** governance-domain source for quality, rights, approval, governance decisions and publishing authorization. Its high-level architecture remains useful, but its rights and approval outcome tokens conflict with accepted CF-20/CF-21.
4. **WP5 v0.1:** design candidate expressing accepted governance invariants and open operational details. It is not a detailed schema freeze.
5. **Batch 17:** state-machine candidate. It reproduces accepted quality, rights and approval vocabularies where known; other transition details remain proposed/open.
6. **Batch 19:** logical/physical persistence candidate. Its entity catalogue and field summaries are not a frozen physical schema.
7. **Existing Contract 07 reconciliation 0.1, authority matrix 0.1, cross-cutting register 0.1 and this crosswalk:** analysis/traceability aids only; none outranks accepted decisions.

**Preservation rule:** Artifact 08 v1.0/v1.1, Batch 16 and Batch 17 are not edited by this work package. ODR-22 remains provisional. No source document is silently promoted to FROZEN.

## 3. Source set inspected

| Source | Version/status | Relevant clauses |
|---|---|---|
| Shared Intelligence Core Contract 07 — Content Quality, Rights & Governance Intelligence | 1.0; working architecture contract | §§2–3, 5, 7.1–7.4, 8–11, 14–16, 17 |
| Accepted Contract Decisions / Artifact 08 Implementation Reference | 1.0; accepted decision reference | CF-20, CF-21, CF-22 |
| Canonical Data Dictionary & Entity Ownership Registry | 1.1; working standard | §5, §8, §§12.2–12.5, §§19.3–19.7 |
| WP5 Governance, Quality, Rights & Authorization Foundation | 0.1; design candidate | §§3–4, 8–14, 17–19 |
| Batch 17 State-Machine & Transition Catalogue | candidate; not frozen | §§1, 3, 13–16, 19–20, 23–25 |
| Batch 19 Database Schema, ERD & Persistence Specification | candidate; not frozen | §§2–8, 12, 19–21 |
| Contract 07 CF-20/CF-21 Governance Reconciliation | 0.1; working analysis | §§1–11 |

### 3.1 Exact source paths

All paths below are relative to `D:\MsP\NEXTDECODE_WORKSPACE\`.

- `02_CANONICAL_CONTRACTS_AND_DATA/02_SHARED_INTELLIGENCE_CONTRACTS/NEXTDECODE_Shared_Intelligence_Core_Contract_07_Content_Quality_Rights_Governance_Intelligence_1.0.md`
- `03_P0_GOVERNANCE_AND_DECISIONS/01_ACCEPTED_DECISIONS/NEXTDECODE_Artifact_08_Implementation_Reference_Accepted_Contract_Decisions_1.0.md`
- `02_CANONICAL_CONTRACTS_AND_DATA/03_DATA_DICTIONARY_AND_TRACEABILITY/NEXTDECODE_Canonical_Data_Dictionary_Entity_Ownership_Registry_1.1.md`
- `04_WORKSTREAMS/WP5_GOVERNANCE_QUALITY_RIGHTS/01_SPECIFICATIONS_AND_RECONCILIATION/NEXTDECODE_P0_WP5_Governance_Quality_Rights_Authorization_0.1.md`
- `05_IMPLEMENTATION_PLANS_AND_WORK_ORDERS/02_BATCH_PACKAGES/NEXTDECODE_P0_Batch17_State_Machine_Transition_Catalogue.md`
- `05_IMPLEMENTATION_PLANS_AND_WORK_ORDERS/02_BATCH_PACKAGES/NEXTDECODE_P0_Batch19_Database_Schema_ERD_Persistence_Specification.md`
- `02_CANONICAL_CONTRACTS_AND_DATA/02_SHARED_INTELLIGENCE_CONTRACTS/NEXTDECODE_Contract_07_CF20_CF21_Governance_Reconciliation_0.1.md`

## 4. Clause-level reconciliation

### C07-X01 — CF-20 rights vocabulary

| Source | Evidence |
|---|---|
| Contract 07 v1.0 §7.2 | Defines `CLEARED`, `RESTRICTED`, `PENDING_VERIFICATION`, `PROHIBITED`, `UNKNOWN`. |
| Accepted CF-20 | Defines `UNKNOWN`, `PENDING_REVIEW`, `CLEARED`, `RESTRICTED`, `EXPIRED`, `REVOKED`, `DENIED`. |
| Data Dictionary v1.1 §§12.2, 19.4 | Uses `rights_status` with the accepted CF-20 vocabulary; historical-token notes are documentation-only. |
| WP5 v0.1 §§3, 8 | Reproduces accepted CF-20 states and explicitly disallows silent substitution of legacy tokens. |
| Batch 17 SM-11 | Reproduces accepted CF-20 vocabulary and says legacy tokens are not silently aliased. |
| Batch 19 §§5, 8, 12 | Uses a `rights_state` field label in its entity/state summaries; this differs from Data Dictionary v1.1's `rights_status`. |

**Disposition for owner review**

- The accepted CF-20 vocabulary is the governing token set for future canonical contract/schema alignment.
- `PENDING_VERIFICATION` and `PROHIBITED` remain historical Contract 07 tokens. The Data Dictionary's compatibility notes are documentation-only and explicitly do not establish perfect semantic equivalence.
- Do not introduce runtime aliases, coercion, backfill or migration from these notes.
- `EXPIRED`, `REVOKED` and `DENIED` remain distinct.
- The canonical field-name discrepancy `rights_state` (Batch 19) versus `rights_status` (Data Dictionary v1.1) is tracked separately as C07-X07.

**Owner decisions still required:** exact Contract 07 successor wording; detailed semantics/transitions for `EXPIRED` and `REVOKED`; whether rights records distinguish permission/licence revocation from another rights-record revocation; legacy-record treatment if a future migration is separately authorized.

### C07-X02 — CF-21 decision vocabulary versus request lifecycle

| Source | Evidence |
|---|---|
| Contract 07 v1.0 §10.2 | Lists approval outcomes `APPROVED`, `REJECTED`, `CHANGES_REQUESTED`, `EXPIRED`, `WITHDRAWN`. |
| Accepted CF-21 | Decision vocabulary is `APPROVED`, `REJECTED`, `CHANGES_REQUESTED`, `EXPIRED`, `REVOKED`. |
| Data Dictionary v1.1 §12.4 and §19.7 | Defines separate ApprovalRequest and ApprovalDecision records; ApprovalDecision uses the CF-21 vocabulary. |
| WP5 v0.1 §§3, 9 | Reproduces the CF-21 decision vocabulary and exact-version/scope binding. |
| Batch 17 SM-12 | Reproduces the CF-21 decision outcomes. Its transition rows include “Approval revoked” but do not define a separate ApprovalRequest lifecycle state machine. |

**Disposition for owner review**

- `WITHDRAWN` is not an accepted CF-21 ApprovalDecision outcome. `REVOKED` is the accepted decision token.
- Do not silently replace `WITHDRAWN` with `REVOKED` in historical records.
- Separate the lifecycle of an ApprovalRequest from the outcome of an ApprovalDecision. A request being withdrawn/closed is not the same fact as a reviewer decision being revoked.
- No complete ApprovalRequest lifecycle enum is established by the inspected accepted decisions or Data Dictionary v1.1. The placement and meaning of request withdrawal therefore remain OPEN; do not introduce a new request-state vocabulary without owner disposition.
- A decision revocation must remain attributable and linked to the prior decision; the exact transition model and authority remain to be specified.

**Owner decisions still required:** whether request withdrawal is supported; which actor may withdraw/close a request and at what point; interaction with a decision already recorded; exact revocation semantics and transition guards; whether a separate request lifecycle state is needed.

### C07-X03 — Immutable review package, exact version and checksum binding

| Source | Evidence |
|---|---|
| Contract 07 §§8, 10.1–10.2 | Requires a versioned ContentManifest and approval bound to the exact reviewed artifact and scope. |
| Accepted CF-21 | Requires immutable review-package binding and exact content/artifact/manifest version plus checksum binding. |
| Data Dictionary v1.1 §12.4 and §19.7 | ApprovalRequest has subject/version and request fields; ApprovalDecision has `approval_request_id`, decision, actor, time and reason. It explicitly states the review-package/manifest/checksum field representation is OPEN. |
| WP5 v0.1 §9 | Describes an immutable review package and exact version/scope decision evidence; exact schema remains a recommendation/open detail. |
| Batch 17 SM-12 | Requires exact-version-bound approval; it does not supply the full persisted review-package/checksum linkage. |
| Batch 19 §§5, 7, 12 | ApprovalDecision summary includes target version and outcome but does not define the complete CF-21 package/version/checksum binding. |

**Disposition for owner review**

The invariant is accepted; the physical field representation is not. The review package must resolve to the exact immutable material reviewed, including applicable content, artifact and manifest versions and checksum evidence. The current Data Dictionary field list is not sufficient to claim the exact linkage has been fully represented.

Do not invent field names, add speculative columns, choose a checksum algorithm, or infer one-to-many approval scope. Preserve the field-level representation as OPEN until the schema owner and governance owner review a complete candidate.

**Owner decisions still required:** package identity/version representation; exact links to content/artifact/manifest immutable version IDs; checksum algorithm/value/reference representation; whether one package can enumerate multiple exact artifacts; invalidation/re-review triggers; evidence retention and verification rules.

### C07-X04 — Separation of quality, rights, approval, authorization and execution

| Source | Evidence |
|---|---|
| Contract 07 §§2–5, 7, 9–11 | Separates quality assessment, rights assessment, governance decision, approval workflow and publishing authorization. |
| Accepted CF-20/CF-21/CF-22 | Rights, approval and centralized authorization are distinct accepted decisions. |
| WP5 v0.1 §4 | Explicitly identifies review/QA, rights, approval and authorization as separate concepts; execution is a fifth step. |
| Batch 17 SM-10–SM-14 and §§19–20 | Separates quality, rights, approval, authorization and external-operation outcome. |
| Data Dictionary v1.1 §§5, 8, 12, 19 | Defines distinct quality, rights, approval, authorization and distribution records/fields. |
| Batch 19 §§2, 5, 8, 12 | Uses purpose-specific fields and distinct records, but requires further schema mapping. |

**Disposition**

Preserve the following boundaries without exception:

- Quality outcome does not grant rights, approval or authorization.
- Rights clearance is use-specific and does not grant approval.
- Approval is an attributable human decision for exact reviewed scope/version; it is not authorization.
- Authorization is a central, default-deny decision for an exact action/resource/version/destination/policy/time context.
- Authorization is not execution.
- A local execution result or accepted API request is not proof of external publication; the distribution operation and remote evidence own that outcome.

No generic `status` field or flattened governance enum may replace these separate concepts.

### C07-X05 — PublishingAuthorization versus AuthorizationDecision

| Source | Evidence |
|---|---|
| Contract 07 §§3.5, 9, 11 | Contract 07's publishing gate issues a short-lived, scoped PublishingAuthorization; adapters validate it before external side effects. |
| Accepted CF-22 | Centralized authorization is authoritative (Option A); default deny, least privilege, exact action/resource/version/destination binding, expiry and revocation. |
| Data Dictionary v1.1 §5 | Lists AuthorizationDecision under Central Authorization. |
| Data Dictionary v1.1 §12.5 | Separately lists PublishingAuthorization and its candidate fields/rules. |
| WP5 v0.1 §§4, 10–11 | Describes a central authorization decision and a logical authorization record; exact schema remains open. |
| Batch 17 SM-13 | Provides candidate conceptual authorization states; exact enum/state model is not frozen. |
| Batch 19 §§3, 5, 8, 12 | Lists AuthorizationDecision but does not show a distinct PublishingAuthorization entity in its entity catalogue. |

**Disposition for owner review**

The central authority and enforcement boundary are accepted. The record model is not yet reconciled. The documents currently use both `AuthorizationDecision` and `PublishingAuthorization`; it is not established whether these are two names for one persisted grant, a policy evaluation plus an issued grant, or distinct linked records.

Do not collapse them or create duplicate authorization authorities. Contract 07/WP5 remains the governance owner. The precise canonical entity relationship and persistence representation must be decided before Batch 19 is treated as schema-ready.

**Owner decisions still required:** canonical record identity; whether evaluation/decision and issued grant are separate records; exact link to DistributionOperation; consumption/idempotency behavior; revocation and expiry linkage; execution-time revalidation and audit evidence.

### C07-X06 — Emergency pause and in-flight external operations

| Source | Evidence |
|---|---|
| Contract 07 §14 | Requires centralized emergency controls; pause blocks new authorization and, where technically possible, prevents pending operations; in-flight behavior is adapter-specific. |
| WP5 v0.1 §12 | New protected actions are denied while pause is active; in-flight operations are reconciled rather than assumed cancelled. Scope, activators and recovery authority remain OPEN. |
| Batch 17 SM-13/SM-14 | Requires pause/revocation checks at execution boundary and unknown-outcome reconciliation; exact pause semantics remain owner-reserved. |
| Contract 12 reconciliation 0.1 | Maps distribution adapter and unknown-outcome dependencies; C12-01..07 remain open. |

**Disposition**

No universal cancellation guarantee may be inferred. Separate new authorization, queued-but-not-submitted work, already-submitted/in-flight requests and unknown external outcomes. Provider-specific capabilities and evidence must determine safe handling.

**Owner decisions still required:** pause scopes; authorized activators/deactivators; treatment of queued operations; treatment of already in-flight requests; provider lookup/cancel capabilities; revocation propagation and fail-closed behavior; audit and recovery evidence.

### C07-X07 — Canonical rights field name and ownership

| Source | Evidence |
|---|---|
| Data Dictionary v1.1 §12.2 | AssetRightsRecord uses `rights_status`. |
| Data Dictionary v1.1 §19.4 | Canonical rights vocabulary is owned by Contract 07. |
| Batch 19 §5 | RightsDetermination core-field summary uses `rights_state`. |
| Batch 19 §8 | Field family is also labelled `rights_state`. |

**Disposition**

Confirmed field-name conflict: `rights_status` (Data Dictionary v1.1) versus `rights_state` (Batch 19). The canonical domain vocabulary owner is Contract 07; the Data Dictionary is the current working entity/field register; Batch 19 is a physical schema candidate. This evidence supports a proposed canonical naming alignment to the Data Dictionary field name, but no physical schema change is made or authorized here.

**Owner decisions still required:** confirm the canonical field name and whether Batch 19 should align to it; confirm the precise persisted entity name/relationship between AssetRightsRecord and RightsDetermination; confirm whether these are the same aggregate/record or distinct evidence/determination records.

### C07-X08 — ApprovalRequest relationship and missing schema linkage

| Source | Evidence |
|---|---|
| Data Dictionary v1.1 §12.4 | Defines ApprovalRequest and ApprovalDecision separately; ApprovalDecision includes `approval_request_id`. |
| Batch 19 §3 | Logical ERD shows ContentVersion linked to Review / ApprovalDecision and ApprovalDecision linked to AuthorizationDecision. |
| Batch 19 §5 | ApprovalDecision summary includes target version, outcome, approver and decision time, but not `approval_request_id`; no ApprovalRequest entity is shown in the entity catalogue. |
| Batch 19 §12 | Uses a conceptual approval decision record but does not provide the complete request/decision/package linkage. |

**Disposition**

The Batch 19 omission is a schema-traceability gap, not proof that the relationship is intentionally forbidden. Reconcile the physical candidate to the Data Dictionary's separate ApprovalRequest and ApprovalDecision records. Do not flatten request and decision into one row or infer cardinality.

**Owner decisions still required:** ApprovalRequest persistence and lifecycle; ApprovalDecision-to-request cardinality; exact subject/version/package links; withdrawal/revocation history; audit and uniqueness constraints.

## 5. Batch 17 transition review — current evidence

1. SM-11 reproduces the accepted CF-20 rights tokens. Its explanatory phrase “prior clearance withdrawn” describes the effect of `REVOKED`; it is not an additional rights enum.
2. SM-12 reproduces the accepted CF-21 decision outcomes. Its row “Approval revoked” describes a decision action, but the table does not define a complete ApprovalRequest lifecycle state machine or a fully specified prior-state → next-state transition edge.
3. SM-13's `NOT_EVALUATED`, `DENIED`, `AUTHORIZED`, `EXPIRED`, `REVOKED` and `INVALIDATED` are candidate conceptual authorization states. CF-22 accepts centralized authorization, not this entire enum set as a frozen vocabulary.
4. The inspected SM-12 table therefore supports the separation of decision outcome from request lifecycle, but it is not sufficient to freeze transition semantics. The exact “contradictory transition” previously flagged must be pinned to a specific source clause/edge before it can be resolved; this crosswalk does not guess which edge was intended.

**Required Batch 17 follow-up:** produce an owner-review transition matrix with explicit aggregate/state owner, current state, requested transition, next state, actor/authority, guards, emitted event and rejection behavior. Keep request lifecycle, approval decision and authorization decision as separate machines.

## 6. Batch 19 schema reconciliation — current evidence

| Concern | Data Dictionary v1.1 | Batch 19 candidate | Finding |
|---|---|---|---|
| Rights field | `rights_status` | `rights_state` | Confirmed naming conflict; owner disposition required. |
| Rights entity | AssetRightsRecord | RightsEvidence / RightsDetermination conceptual records | Entity/aggregate mapping and cardinality require confirmation. |
| Approval decision token | `approval_outcome` with CF-21 vocabulary | `approval_outcome` | Token/field label aligned in current summaries. |
| Approval request link | `approval_request_id` on ApprovalDecision | Not present in Batch 19 core-field summary; ApprovalRequest entity not listed | Incomplete mapping; do not infer omission is intentional. |
| Review package | Required immutable package binding | Not fully represented in Batch 19 core-field summary | OPEN. |
| Exact version | `subject_version_id` | `target_version_id` in ApprovalDecision summary | Semantic alignment likely, but canonical field name and exact relationship need schema-owner confirmation. |
| Checksum binding | CF-21 requires checksum; Data Dictionary says field representation OPEN | No complete review-package checksum linkage defined | OPEN; do not invent columns. |
| Authorization | AuthorizationDecision and PublishingAuthorization both appear in Data Dictionary | AuthorizationDecision appears in Batch 19 | Entity relationship/representation unresolved. |

Batch 19's physical table names, column types, nullability, FK strategy, indexes and cardinalities remain candidates. The source itself says its schema is not frozen and migrations must not run as part of the batch.

## 7. Ownership boundary — no competing source of truth

- **Contract 07 / WP5:** governance-domain semantics and policy ownership for quality, rights, governance decision, approval and central authorization.
- **Data Dictionary:** cross-domain canonical entity/field ownership registry and shared vocabulary propagation; current v1.1 is a working reference, not frozen.
- **Batch 17:** proposed lifecycle/state-transition catalogue; it consumes accepted vocabularies and does not create competing governance authority.
- **Batch 19:** relational schema/persistence candidate; it must map to accepted domain ownership and canonical fields, not redefine them.
- **WP1 / persistence architecture:** cross-domain canonical persistence and relational ownership boundaries must be reconciled with WP5's domain semantics before physical schema freeze.
- **WP6:** acceptance-oracle and negative-test traceability; no test execution is authorized by this crosswalk.

## 8. Open decision register

| ID | Issue | Status | Required disposition |
|---|---|---|---|
| C07-X01 | CF-20 legacy/current rights vocabulary | CONFLICT CONFIRMED | Owner-approved Contract 07 successor wording; no migration/alias inferred. |
| C07-X02 | CF-21 WITHDRAWN vs REVOKED and request lifecycle | CONFLICT CONFIRMED | Separate request lifecycle from decision vocabulary; owner defines withdrawal semantics. |
| C07-X03 | Review package/version/checksum linkage | FIELD REPRESENTATION OPEN | Schema owner maps exact immutable package and version/hash references. |
| C07-X04 | Separate governance concepts | INVARIANT CONFIRMED | Preserve separate records/state families. |
| C07-X05 | AuthorizationDecision vs PublishingAuthorization | ENTITY MODEL OPEN | Decide one record vs linked decision/grant records; no competing authority. |
| C07-X06 | Emergency pause/in-flight behavior | OWNER/ADAPTER DECISION OPEN | Scope, authority and per-adapter reconciliation policy. |
| C07-X07 | rights_status vs rights_state | FIELD-NAME CONFLICT CONFIRMED | Confirm canonical name and update candidate only after owner review. |
| C07-X08 | ApprovalRequest-to-ApprovalDecision mapping | SCHEMA TRACEABILITY GAP | Confirm entity, relationship/cardinality and history. |
| B17-X01 | Approval request lifecycle and exact transition edges | TRANSITION DETAIL OPEN | Produce explicit state/edge/guard matrix; resolve flagged clause by evidence. |
| B19-X01 | Governance physical schema mapping | SCHEMA CANDIDATE OPEN | Reconcile canonical entity/field names, FKs, cardinality and exact binding. |

No item in this register is closed by this crosswalk.

## 9. Next execution sequence

### Wave B — documentation-only sequence

1. **B-WP5-01 — Contract 07 clause traceability:** this document establishes the first source-linked crosswalk. Complete exact source clause pointers and reviewer disposition without editing source contracts.
2. **B-WP5-02 — Approval/request and rights decision matrices:** prepare explicit candidate transition matrices for CF-20 rights, ApprovalRequest lifecycle, CF-21 ApprovalDecision and CF-22 authorization. Keep all owner-reserved values visibly OPEN.
3. **B-WP5-03 — Batch 17 reconciliation:** map each SM-11/SM-12/SM-13 state and transition to accepted CFs, WP5 and the lifecycle standard; resolve the previously flagged transition only when its exact source edge is identified.
4. **B-WP1-04 — Batch 19 field/entity mapping:** reconcile rights_status/rights_state, ApprovalRequest/ApprovalDecision, review-package/checksum binding and AuthorizationDecision/PublishingAuthorization. Do not choose physical types or cardinalities without owner review.
5. **B-WP5/6-05 — Protected-action and acceptance crosswalk:** bind governance decisions to Contract 12, WP6 and Artifact 07 acceptance IDs; test IDs remain proposals until owner scope and test authorization.
6. **B-GOV-06 — Consolidated owner-review pack:** present each conflict, source clause, authority, options, consequences, decision owner and required evidence. Do not preselect reserved decisions.
7. **B-QA-07 — Independent freeze review:** verify source traceability, enum/state separation, field mapping, version/checksum binding and unresolved-decision register. Freeze remains a separate explicit owner action.

### Dependencies and stop conditions

- If an accepted decision's exact wording or provenance is ambiguous, stop that clause and record the missing evidence.
- If a physical field name or relationship is not explicitly accepted, keep it as a candidate.
- If an item needs owner/legal/provider input, leave it OPEN; do not fill it with a plausible default.
- Do not edit Artifact 08 v1.0/v1.1, Batch 16 or Batch 17 in this package.
- Do not perform repository/Git/code changes, tests, agent dispatch, credentials, provider activation, spending, deployment, production generation, uploads or publishing.
- Human approval before publishing remains required; automatic public publishing remains disabled.

## 10. Acceptance criteria for this crosswalk

- Every identified conflict is linked to exact source documents and clauses/sections.
- Accepted CF-20/CF-21/CF-22 invariants are separated from proposed schema/state detail.
- Rights, QA, approval, authorization, execution and external outcome remain separate.
- ApprovalRequest lifecycle is not conflated with ApprovalDecision outcome.
- Exact immutable review-package/content/artifact/manifest/checksum binding is recorded as required, while undefined field representation remains OPEN.
- Batch 19's `rights_state` / `rights_status` conflict is explicit.
- AuthorizationDecision / PublishingAuthorization entity relationship remains OPEN rather than silently collapsed.
- Batch 17's unresolved transition is not guessed.
- Source contracts and frozen/accepted decision records remain unchanged.
- No implementation, test, release or production evidence is claimed.

## 11. Current disposition

**This crosswalk is a working documentation artifact only.** It improves traceability and identifies confirmed conflicts and unresolved mappings. It does not close CF-20/CF-21 owner decisions, amend Contract 07, freeze Batch 17 or Batch 19, approve a physical schema, or authorize implementation.

END OF CROSSWALK
