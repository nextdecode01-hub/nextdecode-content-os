# NEXTDECODE Shared Intelligence Core Contract 07
## Content Quality, Rights & Governance Intelligence
**Version:** 1.0  
**Status:** Working architecture contract — documentation only  
**Scope:** Shared Intelligence Core; content quality assessment, rights and provenance, approval governance, and safe publishing eligibility  
**Authority:** Derived from accepted Creator Success Intelligence decisions and architecture baselines. This document does not authorize repository changes, external integrations, production execution, spending, uploads, or publishing.

---

## 1. Purpose

Define a centralized governance model that evaluates content and its associated assets across the full lifecycle—from research and creative development through production, review, distribution preparation, and post-publication correction.

The model must ensure that quality, rights, and approval decisions are consistent across specialized studios while respecting format-specific requirements. It must prevent individual pipelines, agents, APIs, or publishing adapters from bypassing the central governance boundary.

The system must answer:

- Is the content factually and editorially reliable?
- Does it meet the applicable creative, production, accessibility, and brand standards?
- Are all assets and uses appropriately cleared?
- Are unresolved risks visible and correctly classified?
- Has the required human or policy authorization been obtained?
- Is the exact artifact being distributed the same artifact that was reviewed and approved?
- Is publishing currently permitted under the active policy?

A successful quality assessment is not itself publishing authorization. An approval is not permission to override a hard blocker.

## 2. Core principles

1. **Centralized governance:** all studios and publishing paths use the same authoritative governance boundary.
2. **Multi-dimensional quality:** factual, editorial, creative, production, accessibility, and brand quality are assessed distinctly.
3. **Separate artifact and content quality:** a strong script does not prove the rendered output is correct; a technically valid render does not prove the claims are true.
4. **Rights are use-specific:** asset access or ownership does not automatically establish permission for every medium, territory, duration, or commercial use.
5. **Unknown is not cleared:** unknown, unverified, or pending rights must never be treated as permission.
6. **Hard blockers remain hard:** ordinary approval cannot override legal, rights, privacy, security, safety, or other designated hard blockers.
7. **Approval binds to an exact version:** content, assets, policy, and relevant manifests must be fingerprinted.
8. **No adapter bypass:** direct calls to publishing adapters cannot skip governance.
9. **Human authority is explicit:** sensitive editorial and consequential decisions route to authorized humans.
10. **Policy is versioned:** every assessment and authorization records the policy version applied.
11. **Publishing autonomy is separate:** conditional auto-publishing remains disabled until a separate explicit publishing policy is approved.
12. **Auditable outcomes:** findings, overrides, approvals, denials, and publishing attempts are retained.

## 3. Governance architecture

The logical governance flow is:

`Content/Asset → Quality Assessment → Rights Assessment → Governance Decision → Approval Workflow → Publishing Eligibility → Distribution Adapter`

These are distinct stages and may execute asynchronously. The central governance service owns the final eligibility decision.

### 3.1 Quality Assessment Service

Evaluates the content and production artifact against the applicable quality policies.

### 3.2 Rights & Provenance Service

Evaluates each asset and intended use against ownership, licence, consent, attribution, restrictions, and provenance records.

### 3.3 Governance Policy Engine

Combines policy requirements, quality outcomes, rights outcomes, risk classification, approval requirements, and emergency state to produce a deterministic decision.

### 3.4 Approval Service

Manages human review tasks, evidence, decisions, expiry, reminders, and audit history.

### 3.5 Publishing Authorization Gate

Issues a short-lived, scoped authorization for an exact artifact and destination only when all required conditions are met. It must be checked by every publishing adapter at execution time.

## 4. Quality dimensions

A `QualityAssessment` may contain multiple dimension-specific assessments.

| Dimension | What it evaluates |
|---|---|
| Factual | Claim accuracy, evidence strength, source traceability, uncertainty, and corrections |
| Editorial | Relevance, clarity, context, fairness, completeness, and audience usefulness |
| Creative | Originality, storytelling, hook, structure, pacing, and execution of creative intent |
| Production | Audio, video, rendering, subtitles, timing, encoding, visual integrity, and technical delivery |
| Brand | Parent-brand and studio identity alignment |
| Accessibility | Captions, readability, contrast, language clarity, and other applicable accessibility requirements |
| Platform | Format compatibility, metadata, technical specifications, and current platform rules |

Each dimension has its own findings, severity, evidence, policy version, and status. A single aggregate score must not conceal a critical failure in one dimension.

## 5. Quality outcomes

The shared outcome vocabulary is:

- `PASS`: applicable requirements satisfied with no material unresolved issue.
- `PASS_WITH_WARNINGS`: requirements satisfied, but documented non-blocking issues remain.
- `NEEDS_REVIEW`: a human or specialist assessment is required before progression.
- `BLOCKED`: a hard blocker prevents progression.

Rules:

- `BLOCKED` cannot be converted to pass by ordinary approval.
- `NEEDS_REVIEW` is not equivalent to pass.
- Warnings must identify their impact and recommended treatment.
- The overall outcome is the strictest applicable result across required dimensions and gates.
- A missing required assessment cannot be interpreted as pass.
- A stale assessment must be rerun or explicitly deemed applicable under policy.

## 6. Claim and factual integrity

Reuse the existing Claim, Evidence, ClaimEvidenceLink, and ClaimVerification contracts.

For each material claim:

- Preserve exact claim text and scope.
- Link supporting and contradicting evidence.
- Record verification outcome and rationale.
- Retain publication/retrieval dates and relevant qualifiers.
- Flag unsupported, disputed, stale, or high-impact claims.
- Ensure the final script or artifact does not remove material qualifiers from the research.

Research completion does not automatically mean all claims are verified. Content QA must inspect the actual claims used in the final artifact, not rely solely on a general research brief status.

High-impact claims require stronger evidence and may require specialist review according to central policy. This contract does not authorize agents to make regulated professional determinations.

## 7. Rights and provenance model

### 7.1 AssetRightsRecord

Each asset used in content must have a rights record linked to the centralized Asset Management system.

Required fields:

- `rights_record_id`: UUIDv7.
- `asset_id` and asset version.
- Rights holder/licensor, where known.
- Source/provenance reference.
- Licence, consent, permission, or other legal basis.
- Permitted media and formats.
- Permitted platforms/channels.
- Territory and duration.
- Commercial, promotional, and derivative-use permissions.
- Attribution and disclosure requirements.
- Restrictions and exclusions.
- Effective and expiry dates.
- Evidence/document references.
- Assessment status, assessor, and policy version.
- Workspace/brand scope and audit history.

A rights record applies only to the uses it explicitly covers.

### 7.2 Rights states

The shared rights states are:

- `CLEARED`
- `RESTRICTED`
- `PENDING_VERIFICATION`
- `PROHIBITED`
- `UNKNOWN`

Interpretation:

- `CLEARED`: evidence supports the specific intended use.
- `RESTRICTED`: use is permitted only within recorded conditions.
- `PENDING_VERIFICATION`: evidence or confirmation is outstanding.
- `PROHIBITED`: the intended use is not permitted.
- `UNKNOWN`: status cannot be established.

Only `CLEARED`, or `RESTRICTED` with all conditions satisfied, may pass the rights gate. `PENDING_VERIFICATION`, `PROHIBITED`, and `UNKNOWN` block the affected use.

### 7.3 Rights scope evaluation

Evaluate rights against the actual intended use:

- Asset and exact asset version.
- Content item and derivative.
- Medium/format.
- Platform/channel.
- Territory.
- Publication and licence period.
- Commercial or non-commercial purpose.
- Editing, transformation, and attribution conditions.

A prior clearance cannot automatically be reused when any material use dimension changes.

### 7.4 Provenance and asset integrity

Preserve source, creator, licence, attribution, transformation history, and content hash where applicable. A changed asset creates a new version and may require reassessment.

## 8. Content and asset manifest

Before final governance evaluation, each content variant must have a versioned `ContentManifest`.

It should include:

- Content and variant IDs.
- Script, narration, subtitle, and metadata versions.
- Shot/scene/beat references.
- Asset IDs and exact asset versions.
- Claim and evidence references.
- Audio/music/voice references.
- Render configuration and toolchain versions.
- Output artifact hash and technical metadata.
- Required attribution/disclosure.
- Studio, format, and channel scope.
- Parent/studio identity versions.
- Research and creative brief versions.

The manifest provides the traceability boundary between intended content and the actual artifact. Missing or inconsistent manifest entries may require review or block release under policy.

## 9. GovernanceDecision

A `GovernanceDecision` is the authoritative outcome for a specific content version, intended use, destination, and policy version.

Required fields:

- `governance_decision_id`: UUIDv7.
- Content/variant and exact artifact hash.
- ContentManifest version/hash.
- QualityAssessment references and outcomes.
- RightsAssessment references and outcomes.
- Applicable policy and identity versions.
- Intended destination and use context.
- Required approval roles/actions.
- Emergency-state and publishing-policy evaluation.
- Final decision: `ELIGIBLE`, `PENDING_APPROVAL`, `BLOCKED`, or `EXPIRED`.
- Rationale and finding references.
- Decision actor/service identity and timestamp.
- Expiry and revocation conditions.

The decision must be reproducible from the referenced records. A decision for one artifact or destination cannot authorize a different artifact or destination.

## 10. Approval workflow

### 10.1 ApprovalRequest

An approval request contains:

- Exact content version and artifact hash.
- Manifest and assessment references.
- Intended platform/channel and use.
- Requested approval type.
- Risks, warnings, and unresolved questions.
- Policy version and deadline/expiry.
- Requester and assigned reviewer/role.
- Decision and rationale history.

### 10.2 Approval outcomes

- `APPROVED`
- `REJECTED`
- `CHANGES_REQUESTED`
- `EXPIRED`
- `WITHDRAWN`

Approval must be bound to the exact reviewed artifact and scope. If the content, asset, metadata, destination, or relevant policy changes materially, approval must be re-evaluated or renewed.

### 10.3 Expiry and owner unavailability

- Approval deadlines and reminders are risk-based and policy-configured.
- Expiry never implies approval.
- Silence or owner unavailability never counts as consent.
- Already-authorized work may continue within its existing scope.
- Work requiring a new approval pauses or follows a preapproved safe fallback.
- Critical unresolved issues are escalated through the owner notification system.

## 11. Publishing authorization and adapter enforcement

The publishing gate is the only authority that may issue a publishing authorization.

A `PublishingAuthorization` must be:

- Short-lived.
- Scoped to one content variant and exact artifact hash.
- Scoped to a destination/account/channel and intended operation.
- Bound to current quality, rights, approval, and policy versions.
- Revocable by emergency state or policy change.
- Single-use or idempotently consumable with a unique operation key.
- Auditable.

Every adapter must validate authorization immediately before the external side effect. The adapter must reject:

- Missing or expired authorization.
- Artifact hash mismatch.
- Destination or account mismatch.
- Revoked authorization.
- Active emergency pause.
- Changed policy or stale required assessments.
- Missing required approval.
- Any hard-blocked quality or rights outcome.

No direct adapter, CLI flag, API endpoint, or agent tool may bypass this gate.

### 11.1 Publishing autonomy status

Conditional automatic publishing was discussed as a future operating preference, but it is not approved or enabled. This contract therefore defines the architecture boundary only. A separate owner-approved policy must specify eligible formats/channels, content classes, risk limits, rate limits, account scopes, and emergency behavior before any auto-publishing is activated.

Long-form and short-form publishing must both use the same central governance and authorization model.

## 12. Corrections, takedowns, and post-publication governance

Governance continues after publication.

The system should support:

- Correction requests and factual updates.
- Rights complaints and licence expiry.
- Platform policy changes.
- Privacy or safety escalations.
- Asset replacement and derivative impact analysis.
- Takedown recommendations and authorized takedown execution.
- Content status changes and version lineage.
- Audience-facing correction records where required.

AI may detect, investigate, classify, and prepare remediation. Public statements, sensitive commitments, and other reserved actions require appropriate human authorization unless a specific legal obligation and verified procedure require otherwise.

A correction to one item should identify affected derivatives, clips, posts, and assets through lineage records.

## 13. Risk classification and policy evaluation

The policy engine should classify risk using factors such as:

- Claim criticality and uncertainty.
- Rights and licence status.
- Personal data and privacy exposure.
- Safety, legal, and reputational sensitivity.
- Platform restrictions.
- Commercial relationships.
- Audience interaction context.
- Content originality and derivative use.
- Approval and identity status.

Risk levels and thresholds must be centrally versioned. A risk score is not a substitute for categorical hard gates.

Policy evaluation must be deterministic for the same inputs and policy version, and it must return explainable reasons for each gate.

## 14. Emergency controls

The governance service must consult the centralized emergency-state registry.

Required control scopes include:

- Global publishing pause.
- Workspace or brand pause.
- Studio or channel pause.
- Agent/integration isolation.
- Credential revocation.
- Financial lock.
- Specific content/asset hold.

Emergency controls must be effective independently of the user's local PC. They must preserve evidence and work-in-progress rather than deleting or overwriting it.

An emergency pause blocks new publishing authorization and, where technically possible, prevents pending operations from proceeding. The exact treatment of an already in-flight external request must be documented per adapter.

## 15. APIs and events

Illustrative versioned interfaces:

- `POST /v1/quality/assessments`
- `GET /v1/quality/assessments/{assessment_id}`
- `POST /v1/rights/assessments`
- `GET /v1/assets/{asset_id}/rights`
- `POST /v1/content-manifests`
- `POST /v1/governance/evaluate`
- `GET /v1/governance/decisions/{decision_id}`
- `POST /v1/approvals/requests`
- `POST /v1/approvals/{approval_id}/decisions`
- `POST /v1/publishing/authorizations`
- `POST /v1/publishing/authorizations/{authorization_id}/revoke`

Illustrative events:

- `quality.assessment.completed.v1`
- `quality.review_required.v1`
- `rights.assessment.completed.v1`
- `rights.blocker.detected.v1`
- `content.manifest.created.v1`
- `governance.decision.created.v1`
- `approval.requested.v1`
- `approval.decided.v1`
- `approval.expired.v1`
- `publishing.authorization.issued.v1`
- `publishing.authorization.revoked.v1`
- `governance.emergency_pause.activated.v1`
- `content.correction.required.v1`

All events require durable delivery, schema versioning, idempotency, actor provenance, and workspace/brand scope. Publishing authorization is validated through the authoritative gate, not inferred from event receipt.

## 16. Audit and explainability

Retain:

- Exact content and asset versions.
- ContentManifest and artifact hashes.
- Claim/evidence/verification references.
- Quality and rights assessments.
- Findings, severity, and remediation.
- Policy and identity versions.
- Approval request, reviewer, decision, and rationale.
- Publishing authorization issuance, validation, use, expiry, and revocation.
- Adapter request/response identifiers and sanitized outcomes.
- Emergency-state changes.
- Post-publication corrections and takedown history.

The system must answer: **What exact artifact was evaluated, which rules applied, what risks were found, which rights covered the use, who approved it, what authorization was issued, and what happened at the publishing boundary?**

## 17. Acceptance criteria

The contract is ready for implementation design when:

1. Every studio uses the same central governance decision boundary.
2. Quality is assessed across distinct dimensions without hiding critical failures in an aggregate score.
3. The four shared quality outcomes are enforced consistently.
4. Rights are evaluated per asset version and intended use.
5. Unknown and pending rights cannot pass as cleared.
6. Every final content variant has a versioned manifest and artifact hash.
7. Governance decisions bind to exact artifact, destination, and policy versions.
8. Approval expiry or owner silence never implies approval.
9. Material content changes invalidate or trigger reassessment of prior approval.
10. Every publishing adapter rejects calls without valid central authorization.
11. Direct pipeline, CLI, API, and agent paths cannot bypass governance.
12. Conditional auto-publishing remains disabled until separately authorized.
13. Emergency pause and revocation work independently of the local PC.
14. Post-publication corrections can trace all known derivatives.
15. Every consequential decision and external side effect is auditable.

## 18. Open implementation details

Not fixed by this contract:

- Exact quality rubrics, thresholds, and dimension weights.
- Claim criticality definitions and specialist review policies.
- Rights evidence requirements by asset type and jurisdiction.
- Exact asset manifest schema and hashing algorithm.
- Approval roles, delegation, and review routing.
- Authorization token format, lifetime, and revocation propagation.
- Adapter-specific in-flight request handling.
- Publishing rate limits and eligible content classes for any future auto-publishing.
- Takedown/correction authority by platform and legal context.
- Database, API, and event payload schemas.
- Exact retention and audit-log storage implementation.

These require technical and owner review. No auto-publishing policy, provider, platform connection, or implementation is authorized by this contract.

## 19. Decision traceability

This contract operationalizes accepted decisions covering:

- Multi-dimensional Content Quality Intelligence.
- Shared quality outcomes: PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW, BLOCKED.
- Centralized rights registry and use-specific rights states.
- Claim/Evidence/ClaimVerification reuse.
- Human approval and immutable artifact provenance.
- Centralized governance boundary and adapter enforcement.
- Emergency pause, revocation, and owner-controlled policy authority.
- Conditional automation boundaries with publishing still disabled pending separate approval.
- Risk-based AI transparency and correction handling.
- Auditable decisions, identity, and policy versions.

It is subordinate to the Master Blueprint, System Architecture Master Reference, Shorts Studio Pipeline Contract, Shared Data Model & Content Graph, Agent Contracts & Orchestration, Studio Integration APIs & Artifact Management, Hybrid Deployment/Security/Monitoring contract, and owner-approved decision register. Conflicts must be recorded and reconciled rather than silently resolved by weakening a higher-priority rule.

---

**End of Contract 07 — Content Quality, Rights & Governance Intelligence 1.0**
