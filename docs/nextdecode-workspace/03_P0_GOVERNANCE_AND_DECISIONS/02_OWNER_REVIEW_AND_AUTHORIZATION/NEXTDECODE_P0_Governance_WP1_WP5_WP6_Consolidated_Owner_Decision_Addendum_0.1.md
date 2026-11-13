# NEXTDECODE P0 — Governance, WP1 and WP6 Consolidated Owner Decision Addendum

**Document ID:** NEXTDECODE-P0-GOV-WP1-WP5-WP6-OWNER-ADDENDUM-0.1  
**Version:** 0.1  
**Date:** 4 November 2026  
**Status:** OWNER DECISION AGENDA — NOT APPROVED  
**Parent authority:** Artifact 08, Artifact 10, P0 Owner Review & Contract Freeze Decision Record 0.1  
**Scope:** Consolidated owner decisions arising from B-WP5-01/02/03, B-WP1-04 and Contract 12/WP6 acceptance-oracle reconciliation  
**Detailed contract freeze:** NOT GRANTED  
**Implementation / agent execution / test authorization:** NOT GRANTED

## 1. Purpose and authority

This addendum consolidates the decision points discovered during the current documentation-only reconciliation wave. It is intended to make the next owner review efficient and auditable without reopening decisions already accepted.

It supplements, and does not replace or amend:
- Artifact 08 — Consolidated Owner Decision Record & Contract Freeze Closure 1.0 and its accepted implementation reference;
- Artifact 10 — P0 Owner Review & Authorization Pack 1.0;
- P0 Owner Review & Contract Freeze Decision Record 0.1;
- accepted ADR-001..010 and CF-01..CF-24;
- canonical contracts, Data Dictionary, Batch 17/19, WP1/WP5/WP6 and Artifact 07.

**Decision authority:** Product Owner. No disposition is made by this addendum. Blank fields, a prior “next”, completion of documentation or an agent recommendation do not count as owner approval.

## 2. Current state — verified source record

| Area | Current verified disposition |
|---|---|
| High-level architecture ADR-001..010 | ACCEPTED; carry forward without reopening |
| CF-20 rights semantics | Accepted vocabulary; detailed compatibility and transition treatment remains open |
| CF-21 approval decision vocabulary | Accepted outcomes; request lifecycle and exact review-package/version/checksum representation remain open |
| CF-22 centralized authorization | ACCEPTED — Option A; canonical persisted record relationship remains open |
| WP1 logical schema candidate v0.3 | OWNER REVIEW REQUIRED; not frozen |
| Batch 19 persistence specification | DESIGN CANDIDATE; not frozen |
| WP5 governance matrices / Batch 17 crosswalk | Working reconciliation candidates; not frozen |
| Contract 12 reconciliation C12-01..07 | Partial logical closure; exact protected-action and operation details remain open |
| Artifact 07 / WP6 acceptance | Artifact 07 remains authoritative; WP6 test execution and environment not authorized |
| Detailed contract freeze | NOT FROZEN |
| Repository baseline / implementation | NOT AUTHORIZED |
| Agent task assignment / execution | NONE ISSUED / NOT AUTHORIZED |
| Provider activation, spending, deployment, production generation, upload, publishing | NOT AUTHORIZED |

## 3. Accepted invariants — do not reopen in this review

1. Canonical IDs use immutable UUIDv7.
2. PostgreSQL-compatible relational persistence is the authoritative shared-state direction; provider/hosting remains open.
3. Database-backed durable queue with transactional outbox/inbox is the accepted initial direction.
4. One canonical owner per entity; typed references do not imply permission or ownership.
5. Entity identity, immutable version identity and schema version remain distinct.
6. ContentItem is the shared editorial identity; ContentVariant is a format/platform/language/treatment derivative.
7. Artifact and ArtifactVersion remain distinct; artifact versions are immutable.
8. Workflow, task, job, attempt, worker, governance and distribution state remain separate.
9. QA outcomes are PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW, BLOCKED; hard blockers cannot be bypassed by ordinary approval.
10. CF-20 rights vocabulary: UNKNOWN, PENDING_REVIEW, CLEARED, RESTRICTED, EXPIRED, REVOKED, DENIED.
11. CF-21 approval outcomes: APPROVED, REJECTED, CHANGES_REQUESTED, EXPIRED, REVOKED.
12. CF-22 centralized authorization Option A is authoritative; default-deny, fail-closed, least privilege, exact action/resource/version/destination binding, expiry and revocation.
13. Approval is not authorization; authorization is not execution; execution/accepted request is not proof of external publication.
14. Automatic public publishing remains disabled pending a separate explicit owner-approved policy.
15. P0-A remains a narrow vertical slice ending at the pre-distribution hold; no live upload/public publishing.

## 4. Owner decision agenda — WP5 governance semantics

### GOV-01 — Legacy CF-20 rights-token compatibility

**Question:** How should historical Contract 07 tokens PENDING_VERIFICATION and PROHIBITED be treated relative to accepted CF-20 vocabulary?

| Option | Meaning | Consequence |
|---|---|---|
| A | Preserve legacy tokens as historical-only; require explicit owner-approved mapping before any future migration/runtime conversion | Safest against semantic loss; requires a compatibility policy if legacy records are ever ingested |
| B | Define explicit one-to-one or one-to-many mappings with rationale and scope | Easier migration planning, but must not assume semantic equivalence; mapping evidence required |
| C | Defer legacy data migration and keep the tokens documented as incompatible historical values | No migration now; future ingestion must fail closed or quarantine unknown legacy values |

**Guardrail:** EXPIRED, REVOKED and DENIED remain distinct. Do not equate PROHIBITED with DENIED or PENDING_VERIFICATION with PENDING_REVIEW without explicit evidence and owner approval.

**Owner disposition:** OPEN — ACCEPT / ACCEPT WITH AMENDMENT / REJECT / DEFER  
**Rationale / approved wording:** ______________________________________

### GOV-02 — ApprovalRequest lifecycle and withdrawal

**Question:** What lifecycle, if any, applies to an ApprovalRequest independently of an ApprovalDecision?

| Option | Meaning | Consequence |
|---|---|---|
| A | Keep request lifecycle minimal and explicitly specified only for request handling; define no extra outcome tokens beyond an owner-approved set | Smaller model; exact closure/withdrawal behavior still needs definition |
| B | Define a distinct request lifecycle state machine separate from CF-21 decision outcomes | Strong audit separation; requires a full transition/actor/guard matrix |
| C | Defer request lifecycle detail while preserving immutable request and decision records and a fail-closed protected-action boundary | Less schema detail now; any implementation needing lifecycle transitions remains blocked until resolved |

**Guardrail:** CF-21 decision outcomes remain unchanged. WITHDRAWN in Contract 07 is not silently mapped to REVOKED. A request closure/withdrawal is not automatically a reviewer decision.

**Owner disposition:** OPEN  
**Rationale / approved wording:** ______________________________________

### GOV-03 — Rights record decomposition

**Question:** Is Data Dictionary AssetRightsRecord the canonical aggregate, or should the Batch 19 RightsEvidence and RightsDetermination concepts be separate authoritative records?

| Option | Meaning | Consequence |
|---|---|---|
| A | One canonical AssetRightsRecord aggregate with separately attributable evidence references/children | Closest to current dictionary naming; evidence lifecycle detail still needed |
| B | Separate RightsEvidence and RightsDetermination records under Contract 07 ownership | Clear evidence-versus-decision separation; requires explicit aggregate/link/cardinality decisions |
| C | Keep the logical decomposition open and defer physical persistence mapping | Avoids premature schema choice; governance persistence cannot be frozen |

**Owner disposition:** OPEN  
**Rationale / approved wording:** ______________________________________

### GOV-04 — Canonical rights field name

**Question:** Which field name is canonical for the rights state in the detailed persistence contract?

- Option A: `rights_status` as used by Data Dictionary v1.1.
- Option B: `rights_state` as used by Batch 19.
- Option C: defer the field-level name until the owner approves the canonical entity decomposition.

**Guardrail:** selecting a name does not change CF-20 semantics or authorize migration/renaming.

**Owner disposition:** OPEN  
**Rationale / approved wording:** ______________________________________

### GOV-05 — GovernanceDecision persistence

**Question:** How should Data Dictionary GovernanceDecision be represented in the WP1/Batch 19 model?

- Option A: retain a separate append-oriented GovernanceDecision record.
- Option B: represent it through an existing owner-approved record only if semantic equivalence and provenance are explicitly demonstrated.
- Option C: defer physical persistence outside the minimum P0 slice while keeping the governance decision as an authoritative logical concept.

**Guardrail:** do not collapse GovernanceDecision into AuthorizationDecision by assumption.

**Owner disposition:** OPEN  
**Rationale / approved wording:** ______________________________________

### GOV-06 — Review record boundary

**Question:** What is the canonical Review record and how does it relate to QualityAssessment and ApprovalRequest?

- Option A: Review is a distinct governance record for reviewer assignment, findings and review disposition.
- Option B: Review is a structured activity/evidence record linked to QualityAssessment and ApprovalRequest, without a separate canonical aggregate.
- Option C: defer its physical model pending Contract 07/review-package owner reconciliation.

**Guardrail:** QA outcome, reviewer assessment and formal approval remain distinct.

**Owner disposition:** OPEN  
**Rationale / approved wording:** ______________________________________

### GOV-07 — ApprovalRequest and ApprovalDecision linkage

**Question:** Confirm the canonical request-to-decision relationship and whether ApprovalRequest is persisted.

- Option A: persist ApprovalRequest and require each ApprovalDecision to identify the request it resolves.
- Option B: use an alternative owner-approved relationship only if it preserves request identity, history and exact subject/action context.
- Option C: defer persistence detail; no approval workflow implementation until resolved.

**Guardrail:** Data Dictionary v1.1 §12.4 currently defines `approval_request_id` on ApprovalDecision. Batch 19 summary omits it. No physical FK/cardinality is selected here.

**Owner disposition:** OPEN  
**Rationale / approved wording:** ______________________________________

### GOV-08 — CF-21 immutable review-package binding

**Question:** What exact representation binds ApprovalDecision to the immutable review package and exact content/artifact/manifest version plus checksum?

Potential design directions for owner review (not field names):
- an immutable review-package identity/version that enumerates exact versioned materials and integrity references;
- an explicit relation from approval evidence to the exact reviewed content/artifact/manifest versions and checksums;
- a source-defined manifest/package reference if the authoritative Artifact 07/review-package contract already provides it.

**Guardrail:** no new field names, join table, cardinality, checksum algorithm or package lifecycle is approved by this addendum.

**Owner disposition:** OPEN  
**Rationale / approved wording:** ______________________________________

### GOV-09 — AuthorizationDecision versus PublishingAuthorization

**Question:** How do the two source concepts relate under accepted CF-22 centralized authorization?

- Option A: one canonical authorization record; the two terms are reconciled as terminology only after the owner confirms semantics.
- Option B: separate policy evaluation/AuthorizationDecision and issued/consumable PublishingAuthorization records with explicit linkage and authority.
- Option C: defer record-model selection; preserve centralized authorization as the only authority and block schema freeze.

**Guardrail:** no duplicate authorization authorities. ApprovalDecision is not authorization. Exact DistributionOperation reference remains open until this decision is made.

**Owner disposition:** OPEN  
**Rationale / approved wording:** ______________________________________

## 5. Owner decision agenda — Contract 12 / protected actions / WP6

### C12-AO-01 — Authorization binding tuple

**Question:** Approve the complete set of facts a central authorization decision must bind before a distribution-side effect.

Candidate dimensions already supported conceptually by Contract 12 §8.1/§8.4 and CF-22 include workspace/brand/studio scope; exact resource and artifact version/hash; exact distribution package version; channel/account; operation/action; intended destination and visibility; schedule/time window; policy version; QA/rights/approval evidence; account permission and expiry/revocation.

**Decision required:** confirm mandatory dimensions, conditional dimensions, canonical source for each fact and how changed material invalidates prior authorization. Exact physical field names remain open.

**Owner disposition:** OPEN  
**Rationale / approved wording:** ______________________________________

### C12-AO-02 — Upload, publication and visibility outcome model

**Question:** How should internal operation state and platform-observed outcome be represented separately?

Candidate distinctions in Contract 12 §9.1 include package validated, upload requested/initiated/confirmed, publication requested/scheduled/confirmed, public visibility independently verified, and monitoring active. Platform states such as private, unlisted, processing, rejected, removed or restricted must not be inferred from intent.

**Decision required:** approve evidence required to claim each outcome, including what counts as independent public-visibility verification and how conflicting provider observations are handled.

**Owner disposition:** OPEN  
**Rationale / approved wording:** ______________________________________

### C12-AO-03 — PublishOperation and execution records

**Question:** What is the logical relationship between the distribution-owned PublishOperation and orchestration-owned WorkflowRun/Job/JobAttempt?

- Option A: PublishOperation is the distribution business record referencing orchestration execution/attempt records.
- Option B: PublishOperation is an execution aggregate with a clearly defined owner boundary and linked orchestration attempts.
- Option C: defer exact relationship/cardinality pending Contract 10/WP2 owner reconciliation.

**Guardrail:** do not duplicate authoritative job/attempt state or infer cardinality from a conceptual ERD.

**Owner disposition:** OPEN  
**Rationale / approved wording:** ______________________________________

### C12-AO-04 — Unknown provider outcome and retry

**Question:** What evidence is required before retrying an external action after timeout/lost response?

**Minimum invariant:** mark uncertain outcome for reconciliation; preserve operation/idempotency/package/version/hash/account/destination/provider correlation; query only supported provider/simulator mechanisms; retry only after the prior side effect is determined not to have occurred and authorization is still valid.

**Decision required:** approve simulator-only P0 oracle, source of truth for reconciliation and escalation when provider outcome cannot be resolved. No real provider test is in scope for P0-A.

**Owner disposition:** OPEN  
**Rationale / approved wording:** ______________________________________

### C12-AO-05 — Emergency pause and in-flight requests

**Question:** Define separate behavior for (a) new actions, (b) queued but not submitted work, (c) already submitted/in-flight requests and (d) unknown external outcomes.

**Guardrail:** a pause can block new protected actions; it cannot be assumed to recall a request already accepted by a provider. Provider-specific cancel/lookup capabilities require evidence.

**Owner disposition:** OPEN  
**Rationale / approved wording:** ______________________________________

### C12-AO-06 — ChannelAccount credential boundary

**Question:** Who owns account connection and credential lifecycle, and how are scopes, expiry, revocation and audit evidence represented?

**Guardrail:** worker identity credentials and channel account credentials are different security principals and must not be treated as interchangeable. No raw secret may be stored in ordinary records/logs.

**Owner disposition:** OPEN  
**Rationale / approved wording:** ______________________________________

### C12-AO-07 — Protected-action catalogue

**Question:** Which action classes require centralized authorization and what human approval/second-person/step-up requirements apply?

Candidate Contract 12 actions include upload, schedule execution, publish, update, delete, correction/takedown and community actions. The owner must decide per-action scope, risk class, reversibility, required approval, evidence, pause behavior and escalation.

**Guardrail:** this list is a candidate catalogue, not a frozen enum or exhaustive set.

**Owner disposition:** OPEN  
**Rationale / approved wording:** ______________________________________

### C12-AO-08 — P0-A scope and supplemental tests

**Question:** Confirm which distribution-specific behaviors are (a) mandatory P0-A negative tests, (b) simulator-only supplemental tests, or (c) deferred beyond P0-A.

**Source boundary:** Artifact 07 §6.2 expects a protected distribution request to be denied without separate publishing authorization. Batch 10 §4 ends the slice at a human-approved pre-distribution hold. Real upload/publication, live visibility checks, account actions and community actions are not part of this slice.

**Owner disposition:** OPEN  
**Rationale / approved wording:** ______________________________________

## 6. WP6 acceptance and evidence decisions

The following are owner-review matters, not assumed test permissions:

1. Confirm Artifact 07 §7.2 remains the authoritative test-ID/severity source; preserve all criticality and mandatory requirements exactly.
2. Approve a test-case-level manifest mapping every Artifact 07 ID to source clause, WP6 trace ID, fixture, environment, observable oracle, evidence artifact and result field.
3. Decide whether API-EVT-19 unknown external outcome is included as a controlled simulator-only test or deferred. No real provider is used.
4. Confirm ENV-01..14 preconditions, isolated test environment, synthetic fixtures, outbound upload/publish denial, no-cost boundary, stop/abort proof and test-only parameters.
5. Preserve NOT_RUN as not passed. NOT_APPLICABLE requires explicit approved scope rationale.
6. Independent Kilo QA occurs only after an authorized implementation/evidence target exists; it remains read-only.
7. Owner acceptance/rejection is separate from Kilo's review and separate from implementation authorization.

**Owner disposition:** OPEN  
**Rationale / approved wording:** ______________________________________

## 7. WP1 persistence decisions — dependency summary

B-WP1-04 records eleven decision questions. For this owner agenda they group as follows:

| Decision group | B-WP1-04 IDs | Owner must settle |
|---|---|---|
| Rights entity/field | B19-GOV-01..02 | AssetRightsRecord decomposition and canonical rights field name |
| Governance/review | B19-GOV-03..04 | GovernanceDecision representation; Review record and relationship to QualityAssessment/ApprovalRequest |
| Approval request/decision | B19-GOV-05..07 | ApprovalRequest persistence/link; exact CF-21 review-package/version/checksum binding; WITHDRAWN/REVOKED compatibility |
| Authorization/distribution | B19-GOV-08..09 | AuthorizationDecision vs PublishingAuthorization model; DistributionOperation authorization reference |
| State and relational integrity | B19-GOV-10..11 | ApprovalRequest lifecycle authority; direct FK vs typed-link strategy |

No schema migration, DDL, ORM field, FK, cardinality, enum or transition is approved by this summary.

## 8. Decision process and recording template

For every decision above, record:
- Decision ID and exact question;
- selected disposition: ACCEPT / ACCEPT WITH AMENDMENT / REJECT / DEFER / NOT APPLICABLE;
- selected option or approved wording;
- rationale and rejected alternatives;
- affected contracts, data dictionary sections, Batch 17/19 and WP6 oracle IDs;
- implementation/test consequences;
- owner name/signature and date;
- immutable decision-record version/reference.

A deferral must name an accountable owner, trigger/condition for reopening and downstream work blocked by the unresolved point.

## 9. Contract-freeze and execution gates

This addendum does not itself freeze any contract. The existing owner review record requires all mandatory contract completeness and owner-governance items to be resolved or explicitly deferred before detailed freeze.

**Detailed contract freeze requires at minimum:**
- all owner-reserved decisions accepted/amended/rejected/deferred in an attributable record;
- accepted wording reflected in the canonical source contracts and versioned;
- no unresolved critical ambiguity in governance, persistence, API/event, lifecycle or protected-action boundaries;
- Batch 17/19 candidate mappings reconciled to owner-approved decisions;
- Artifact 07/WP6 test oracles and criticality traceability complete;
- exact schema/field/relationship and state-transition details required for the first slice approved;
- a formal freeze disposition recorded by the owner.

**Implementation remains a separate gate after contract freeze.** It requires explicit scope, repository identity, baseline permission, preservation rules, path-level ownership, allowed commands/tests, agent assignments, environment, data/credential boundaries, cost ceiling, stop conditions and independent review.

No implementation, repository inspection, tests, Git, agent dispatch, provider activation, spending, deployment, production generation, upload or publishing is authorized here.

## 10. Agent coordination — no dispatch

Prepared task prompts exist in:
`06_AGENT_HANDOFFS/NEXTDECODE_P0_WP5_Governance_Matrix_Agent_Handoff_Prompts_0.1.md`.

Role boundaries remain:
- **Qoder:** sole writer for the current governance-closure implementation milestone only after separate owner authorization and frozen inputs.
- **OpenCode:** read-only API/backend architecture review within an assigned scope.
- **Copilot:** focused regression-test review within an assigned scope.
- **Kilo:** independent read-only QA/security acceptance after implementation and evidence are complete and separately authorized.
- **Antigravity:** conditional targeted product/UI review only when separately assigned.

Prompts are prepared, not dispatched. No task assignment is issued by this addendum. No reviewer may write to the artifact under review.

## 11. Current recommendation to the owner

The most efficient owner-review sequence is:
1. Resolve the WP5 semantics that govern the persistence model: rights compatibility, ApprovalRequest lifecycle, review/approval binding and authorization record relationship.
2. Resolve WP1 entity/field/relationship mapping against those governance decisions.
3. Resolve Contract 12 protected-action catalogue, authorization binding, account credential boundary, unknown outcome and emergency pause behavior.
4. Approve the corresponding Artifact 07/WP6 test-case oracles and P0-A scope.
5. Incorporate only owner-approved dispositions into canonical contracts and the detailed freeze pack.
6. Make a separate contract-freeze decision.
7. Only after freeze, consider a separate bounded repository baseline and implementation authorization.

This sequence avoids schema work that would need to be rewritten when governance authority and operation binding are clarified.

**Current disposition:** OWNER DECISION AGENDA — NOT APPROVED. All owner decisions remain OPEN until explicitly recorded. Detailed contract freeze, implementation, agent execution and test execution remain NOT AUTHORIZED.

