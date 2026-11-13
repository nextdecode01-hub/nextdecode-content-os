# Contract 07 — CF-20 / CF-21 Governance Reconciliation

**Version:** 0.1  
**Date:** 2026-11-04  
**Status:** Working reconciliation analysis — not owner-approved, not frozen  
**Source contract:** Shared Intelligence Core Contract 07 — Content Quality, Rights & Governance Intelligence 1.0  
**Cross-sources:** Accepted owner decision record and implementation reference; Data Dictionary v1.1; API/Event Standard 1.0; Unified Lifecycle & State Transition Standard 1.0; Contract 11; Contract 12; WP4/WP5/WP6 boundary documents.

**Detailed contract freeze:** NOT GRANTED  
**Implementation authorization:** NOT GRANTED

---

## 1. Executive finding

Contract 07 v1.0 establishes the correct high-level governance architecture: centralized quality, rights, approval and publishing authorization; use-specific rights; exact artifact/version binding; hard blockers; no adapter bypass; versioned policy; human authority; auditability; autonomous public publishing disabled pending separate owner policy.

However, two shared vocabularies require controlled reconciliation against accepted CF-20 and CF-21:

1. Contract 07 rights states are older than the accepted CF-20 vocabulary propagated in Data Dictionary v1.1.
2. Contract 07 approval outcomes include `WITHDRAWN`, while Data Dictionary v1.1's CF-21 decision vocabulary includes `REVOKED`. Contract 07 also has an ApprovalRequest lifecycle concept, so decision and request states must be separated rather than flattened.

The source contract is a working architecture contract. This report identifies the mismatch; it does not amend Contract 07 or decide the owner-reserved semantics.

## 2. Authority

1. Accepted CF-20/CF-21 owner decisions govern.
2. Data Dictionary v1.1 is the latest working propagation of CF-20/CF-21 vocabulary, but its detailed data model is not frozen and formal supersession of v1.0 is not inferred.
3. Contract 07 v1.0 remains the domain source for governance architecture and its current documented fields/flows, subject to the accepted owner decisions.
4. API/Event and lifecycle standards govern cross-domain command/event/lifecycle semantics.
5. Contract 11 and Contract 12 consume Contract 07 decisions; they do not own or recreate governance authorization.

## 3. Rights vocabulary — CF-20

### 3.1 Contract 07 v1.0 source vocabulary

- `CLEARED`
- `RESTRICTED`
- `PENDING_VERIFICATION`
- `PROHIBITED`
- `UNKNOWN`

Contract 07 says only `CLEARED`, or `RESTRICTED` with all conditions satisfied, may pass the rights gate. `PENDING_VERIFICATION`, `PROHIBITED` and `UNKNOWN` block the affected use.

### 3.2 Accepted CF-20 / Data Dictionary v1.1 vocabulary

- `UNKNOWN`
- `PENDING_REVIEW`
- `CLEARED`
- `RESTRICTED`
- `EXPIRED`
- `REVOKED`
- `DENIED`

Data Dictionary v1.1 includes documentation-only historical references:
- `PENDING_VERIFICATION` → `PENDING_REVIEW`
- `PROHIBITED` → `DENIED`

It explicitly says these are not perfect semantic equivalences and do not authorize data migration, backfill or runtime coercion. `EXPIRED` and `REVOKED` remain distinct from `DENIED`. Local `reuse_rights: permitted` must not be mapped to `CLEARED`.

### 3.3 Reconciliation table

| Topic | Contract 07 v1.0 | CF-20 / Data Dictionary v1.1 | Disposition |
|---|---|---|---|
| No known status | UNKNOWN | UNKNOWN | Consistent |
| Review pending | PENDING_VERIFICATION | PENDING_REVIEW | Legacy/current vocabulary conflict; no silent alias |
| Permitted with conditions | RESTRICTED | RESTRICTED | Consistent; conditions must be evaluated for exact use |
| Cleared use | CLEARED | CLEARED | Consistent; evidence must support exact intended use |
| Prohibited use | PROHIBITED | DENIED | Historical/current vocabulary conflict; do not assume perfect semantic equivalence |
| Time validity elapsed | Not separately represented | EXPIRED | New explicit state; semantics and re-review behavior need domain confirmation |
| Permission withdrawn/revoked | Not separately represented | REVOKED | New explicit state; distinguish from denial and expiry |

### 3.4 Required behavior that remains invariant

- Rights are evaluated for the exact asset and version, content/derivative, medium/format, platform/channel, territory, period, commercial purpose, editing/transformation and attribution conditions.
- A rights record does not grant universal permission.
- Unknown or pending rights do not pass the affected use.
- Restricted rights pass only when all recorded conditions are satisfied.
- A changed asset version or material use context can require reassessment.
- No source-level compatibility note authorizes runtime coercion or historical data migration.

### 3.5 Open owner decisions

- Exact semantic definition and transitions for EXPIRED and REVOKED.
- Whether REVOKED applies to a prior clearance/permission decision, a source licence, a consent record, or more than one distinct record type.
- Exact evidence and reassessment requirements when a state becomes EXPIRED or REVOKED.
- How legacy PROHIBITED and PENDING_VERIFICATION records are handled during any future migration, if migration is separately approved.
- Whether Contract 07's rights schema is revised to CF-20 directly or references a shared vocabulary registry.

No migration or runtime alias should be implemented before those decisions.

## 4. Approval vocabulary — CF-21

### 4.1 Contract 07 v1.0 source vocabulary

Approval outcomes listed:
- `APPROVED`
- `REJECTED`
- `CHANGES_REQUESTED`
- `EXPIRED`
- `WITHDRAWN`

Contract 07 describes ApprovalRequest fields including exact content version, artifact hash, manifest and assessment references, intended platform/channel/use, requested approval type, risks, policy version, deadline/expiry, requester, assigned reviewer/role, decision and rationale history.

### 4.2 Accepted CF-21 / Data Dictionary v1.1 vocabulary

Decision vocabulary:
- `APPROVED`
- `REJECTED`
- `CHANGES_REQUESTED`
- `EXPIRED`
- `REVOKED`

CF-21 also requires approval binding to:
- Immutable review package.
- Exact content/artifact/manifest version reviewed.
- Checksum of the reviewed version.

Data Dictionary v1.1 says the field-level linkage representation is still open where not defined; do not invent exact field names in this reconciliation.

### 4.3 Decision state vs request lifecycle

The following separation is required for owner review:

| Concept | Meaning | Candidate state handling |
|---|---|---|
| ApprovalRequest lifecycle | Request is created, routed, reviewed, closed or withdrawn | Request lifecycle may include WITHDRAWN as a request closure state, subject to lifecycle-standard reconciliation |
| ApprovalDecision | Reviewer decision on exact reviewed package/version | CF-21 vocabulary: APPROVED, REJECTED, CHANGES_REQUESTED, EXPIRED, REVOKED |
| Approval validity | Whether a prior approval remains valid for the exact subject/action/scope | Expiry/revocation/review invalidation; not a new approval decision |
| PublishingAuthorization | Permission for one protected external action | Separate short-lived, scoped authorization from Contract 07 |

**Important:** This table is a reconciliation proposal. It does not declare WITHDRAWN accepted as a request state or determine all lifecycle transitions.

### 4.4 Exact review binding

Contract 07 already requires approval for an exact artifact and scope. CF-21/Data Dictionary v1.1 make the immutable review package, exact content/artifact/manifest version and checksum binding explicit.

Required cross-reference behavior:
- Approval references one immutable review package.
- The package resolves to exact content/variant and artifact/manifest version(s).
- Checksum is calculated/recorded under a defined integrity method.
- Reviewer identity, timestamp, decision, rationale, policy version and scope are retained.
- A material change to content, asset, metadata, destination or relevant policy triggers re-evaluation/renewal according to policy.
- Approval of one derivative does not transfer to another derivative.

### 4.5 Open owner decisions

- Exact ApprovalRequest lifecycle state machine and whether WITHDRAWN is retained there.
- Exact approval decision/validity model for REVOKED versus EXPIRED.
- How request withdrawal interacts with an already recorded decision.
- Exact review-package, content/artifact/manifest version and checksum field representation.
- Whether an approval can cover multiple artifacts only when the immutable review package enumerates each exact version/hash.
- Exact invalidation triggers for destination, account, metadata and policy changes.

## 5. Governance decision and authorization boundary

Contract 07 establishes the logical sequence:

`Content/Asset → Quality Assessment → Rights Assessment → Governance Decision → Approval Workflow → Publishing Eligibility → Distribution Adapter`

These are distinct stages. Preserve the following:

| Record/concept | Owner | Does not mean |
|---|---|---|
| QualityAssessment | Contract 07 | Human approval or publishing authorization |
| RightsAssessment / AssetRightsRecord | Contract 07, linked to Part 7 asset identity | Universal ownership or unrestricted reuse |
| GovernanceDecision | Contract 07 | Successful external operation |
| ApprovalRequest / ApprovalDecision | Contract 07 | Permission to bypass hard blockers |
| PublishingAuthorization | Contract 07 | General permission for other artifacts/destinations/actions |
| DistributionPackage / ScheduleProposal | Contract 12 | Publishing authorization |
| PublishOperation / Publication | Contract 12 | A governance decision or approval |

PublishingAuthorization must be short-lived, scoped to exact content/variant and artifact hash, destination/account/channel, intended operation and current policy/assessment/approval versions. The adapter validates it immediately before the external side effect.

## 6. Contract 12 adapter requirements

Contract 12 owns channel, account, package, schedule, PublishOperation and Publication records. Contract 07 owns the authorization decision.

Contract 12 must not:
- Mint its own authorization.
- Infer permission from APPROVED alone.
- Treat schedule validation as authorization.
- Treat upload confirmation as publication confirmation.
- Treat a timeout as proof of failure.
- Blindly retry an unknown external outcome.
- Treat event receipt as permission.

Contract 12 must:
- Check current authorization at the adapter boundary.
- Validate exact package/artifact version, destination/account, operation, policy and expiry.
- Respect emergency pause and revocation.
- Record ambiguous external outcomes as reconciliation-required/unknown.
- Reconcile before unsafe retry.
- Preserve upload, publication and public visibility as distinct states.

## 7. Quality outcomes and hard blockers

Contract 07 quality outcomes:
- `PASS`
- `PASS_WITH_WARNINGS`
- `NEEDS_REVIEW`
- `BLOCKED`

Invariants:
- NEEDS_REVIEW is not PASS.
- BLOCKED cannot be converted to pass by ordinary approval.
- Missing required assessment is not pass.
- Aggregate score cannot conceal a critical failure.
- Quality is multi-dimensional: factual, editorial, creative, production, brand, accessibility and platform.

Quality outcome, rights state, approval decision, governance disposition and publishing authorization must remain separate state vocabularies.

## 8. Emergency pause and in-flight operation gap

Contract 07 requires centralized emergency state and pause controls independent of the local PC. Contract 12 requires adapters to enforce the pause and describes reconciliation for uncertain external outcomes.

Still open:
- Whether pause blocks only new authorizations, also queued operations, and which already-authorized operations may continue.
- Exact handling of an external request already in flight when pause is activated.
- Provider-specific cancellation/lookup capability and evidence requirements.
- Revocation propagation latency and fail-closed behavior when the policy service is unavailable.
- Who can activate/deactivate each pause scope and what audit evidence is mandatory.

No generic answer should be invented across all providers. Require an adapter-specific policy, owner decision and test oracle.

## 9. WP5/WP6 closure mapping

| Work package | Required contribution | Evidence needed |
|---|---|---|
| WP1 | Canonical entity references and versioned identities for quality, rights, approval, decision and authorization | Entity ownership/relationship mapping; no duplicate domain state |
| WP4 | Exact Artifact/ArtifactVersion, manifest, checksum, provenance and retention references | Immutable version and integrity model; no binary-storage/governance conflation |
| WP5 | CF-20/CF-21 vocabularies, quality/rights/approval state machines, governance decision and authorization policy | Owner-reviewed clauses, protected-action catalogue, decision matrix, pause rules |
| WP6 | Adapter conformance and failure/recovery test oracle | Missing/expired/mismatched/revoked authorization rejection; unknown outcome and pause scenarios |
| Contract 12 | Distribution package/operation/publication state and adapter enforcement | Exact operation-to-authorization linkage and provider reconciliation |

## 10. Proposed closure checklist

- [ ] Confirm CF-20 exact state vocabulary and definitions in Contract 07.
- [ ] Confirm legacy rights-token handling is documentation-only until migration approval.
- [ ] Define EXPIRED and REVOKED semantics and transitions.
- [ ] Separate ApprovalRequest lifecycle from ApprovalDecision vocabulary.
- [ ] Confirm WITHDRAWN placement and semantics.
- [ ] Confirm CF-21 immutable review-package/version/checksum binding.
- [ ] Define governance decision inputs and reproducibility.
- [ ] Define PublishingAuthorization exact scope, lifetime, revocation and consumption semantics.
- [ ] Complete protected-action catalogue.
- [ ] Decide emergency pause behavior for queued and in-flight external operations.
- [ ] Define provider-specific adapter reconciliation requirements.
- [ ] Map every decision/state to API command, event, owner and acceptance test.
- [ ] Obtain explicit owner review and exact version freeze decision.

## 11. Current disposition

| Item | Status |
|---|---|
| Contract 07 high-level governance architecture | Source-defined working contract |
| CF-20 rights vocabulary alignment | Conflict confirmed; owner-reviewed revision required |
| CF-21 approval vocabulary alignment | Conflict confirmed; request/decision separation required |
| Exact review package/version/checksum binding | Required by accepted CF-21; field representation open |
| Quality outcomes | Source-defined; retain separate from approval/rights |
| Contract 12 adapter authorization boundary | Source-defined; implementation not verified |
| Emergency pause/in-flight behavior | Open owner/adapter decision |
| Contract 07 detailed freeze | NOT GRANTED |
| Implementation authorization | NOT GRANTED |

**This report does not edit Contract 07, amend accepted CF decisions, create an owner decision, freeze a schema, authorize code changes or enable publishing.**

**End of reconciliation.**
