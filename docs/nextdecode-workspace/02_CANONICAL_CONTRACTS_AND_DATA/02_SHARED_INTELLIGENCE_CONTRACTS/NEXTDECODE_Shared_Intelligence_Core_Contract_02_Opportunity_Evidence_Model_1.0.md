# NEXTDECODE Shared Intelligence Core Contract 02
## Opportunity & Evidence Model
**Version:** 1.0  
**Status:** Working architecture contract — documentation only  
**Scope:** Shared Intelligence Core; reusable across NEXTDECODE studios and workspaces  
**Authority:** Derived from the accepted Creator Success Intelligence decisions and architecture baseline. This document does not authorize repository changes, external data collection, provider connections, spending, production execution, or publishing.

---

## 1. Purpose

Define a common model for discovering, evaluating, recording, prioritizing, and reusing content and business opportunities while preserving the evidence that supports each decision.

The model must let NEXTDECODE identify promising topics, audience needs, formats, series, collaborations, distribution opportunities, and business opportunities without confusing a promising hypothesis with a verified fact or treating a high score as permission to act.

The contract connects:

- Audience Intelligence
- Opportunity Intelligence
- Research Intelligence and the existing Claim/Evidence/ClaimVerification concepts
- Strategy & Planning
- Brand Intelligence
- Content Quality and Rights Governance
- Creative and specialized studios
- Performance, Learning, and Business Intelligence

## 2. Normative principles

1. **Evidence before confidence:** every material assessment must identify its supporting evidence, source provenance, observation window, and limitations.
2. **Eligibility before ranking:** hard eligibility gates are evaluated before weighted scoring. A high score cannot override a failed gate.
3. **Facts are not hypotheses:** verified facts, estimates, opinions, assumptions, and hypotheses remain distinguishable.
4. **Confidence is explicit:** scores must not imply certainty. Confidence, evidence coverage, freshness, and unresolved contradictions are recorded separately.
5. **No guaranteed outcomes:** opportunity scores are decision-support signals, not predictions or guarantees of reach, virality, revenue, or success.
6. **Reuse with provenance:** evidence may be reused across studios only with its source, scope, permissions, freshness, and applicability preserved.
7. **Recommendations are not authorization:** identifying or ranking an opportunity does not authorize research expenditure, production, external commitments, or public distribution.
8. **Human authority remains intact:** sensitive editorial, legal, financial, policy, and strategic decisions follow their separately approved governance boundaries.
9. **No silent commercial influence:** sponsorship or revenue potential must not silently alter factual conclusions, evidence ratings, or editorial judgments.
10. **Workspace isolation by default:** private workspace data is not shared with another workspace unless explicitly authorized under the applicable sharing policy.

## 3. Opportunity taxonomy

An `Opportunity` is a structured, time-bounded candidate for creating value. It may be one of the following:

| Type | Meaning | Example (illustrative) |
|---|---|---|
| `CONTENT_TOPIC` | A topic worth investigating or explaining | A meaningful development in AI tooling |
| `AUDIENCE_NEED` | An unmet question, problem, or learning need | Confusion about a new technology |
| `SERIES` | A repeatable sequence or editorial property | A recurring startup breakdown |
| `FORMAT` | A format or presentation approach worth testing | Explainer versus case-study format |
| `COLLABORATION` | A potential collaboration between studios or parties | Two studios covering complementary angles |
| `DISTRIBUTION` | A channel, packaging, timing, or distribution opportunity | Adapting a verified story for a suitable channel |
| `PRODUCT` | A potential audience-facing product or resource | A template, guide, or learning resource |
| `MONETIZATION` | A potential business model or revenue opportunity | Affiliate, sponsorship, membership, or digital product |
| `PLATFORM` | An internal platform capability or workflow improvement | Improving research-to-production traceability |

The taxonomy is extensible. New types require a versioned taxonomy change and compatibility review; adding a type must not implicitly grant new execution authority.

## 4. Core entities

### 4.1 Opportunity

Represents the candidate itself.

| Field | Type / rule | Description |
|---|---|---|
| `opportunity_id` | UUIDv7 | Stable canonical identifier |
| `workspace_id` | UUIDv7 | Owning workspace |
| `brand_id` | UUIDv7, nullable where applicable | Brand context |
| `opportunity_type` | Versioned enum | Taxonomy classification |
| `title` | Required string | Concise opportunity name |
| `summary` | Required text | Neutral description of the opportunity |
| `problem_or_need` | Text | Audience or business need being addressed |
| `target_audience_refs` | Scoped references | Relevant personas/segments; no assumed identity matching |
| `related_brand_pillars` | References | Applicable brand pillars |
| `origin` | Structured source | Discovery source and method |
| `first_observed_at` | Timestamp | First recorded observation |
| `last_observed_at` | Timestamp | Most recent supporting observation |
| `valid_until` | Nullable timestamp | Known expiry or review-by date |
| `status` | Lifecycle enum | Current opportunity lifecycle |
| `owner_ref` | Actor reference | Responsible human, studio, or authorized service |
| `created_by` / `updated_by` | Actor references | Audit provenance |
| `created_at` / `updated_at` | Timestamps | Record lifecycle |
| `schema_version` | Version | Contract compatibility |

An opportunity must not contain unsupported factual claims as if they were established facts. Claims belong in the evidence/claim model and are linked by references.

### 4.2 EvidenceSource

Represents the origin of information used to support or challenge an opportunity.

Required attributes:

- Stable source identifier and source type.
- Publisher/creator or originating organization, where known.
- Canonical source location or internal artifact reference, subject to access policy.
- Publication time and retrieval/observation time, where available.
- Primary/secondary/first-party/public/authorized-external classification.
- Access permission, purpose limitation, and applicable usage restrictions.
- Source credibility assessment with rationale and assessor/version.
- Freshness and expected validity window where relevant.
- Workspace/data classification and retention policy.
- Source status: available, inaccessible, withdrawn, expired, or restricted.

A URL alone is not sufficient provenance. The record must identify what was observed and when. Credentials, private content, or restricted source material must not be copied into broadly accessible evidence records.

### 4.3 EvidenceItem

Represents a specific observation, data point, document excerpt, measurement, or source-backed finding.

| Field | Type / rule | Description |
|---|---|---|
| `evidence_id` | UUIDv7 | Stable identifier |
| `source_id` | Reference | Originating EvidenceSource |
| `evidence_type` | Versioned enum | Observation, document, dataset, metric, statement, experiment result, etc. |
| `statement` | Required text | What this evidence supports or contradicts |
| `observed_at` | Timestamp | When the underlying event/data was observed |
| `captured_at` | Timestamp | When the system captured it |
| `valid_from` / `valid_to` | Nullable timestamps | Period in which it is valid |
| `scope` | Structured | Geography, platform, audience, format, market, and other applicable boundaries |
| `method` | Required where relevant | How the evidence was collected or derived |
| `limitations` | Text | Known caveats, sampling limitations, missing context |
| `reliability_assessment_ref` | Reference | Versioned source/evidence assessment |
| `classification` | Enum | Public, Internal, Confidential, Restricted |
| `permission_ref` | Reference | Applicable permission/consent record |
| `content_hash` | Optional | Integrity check for retained artifact |
| `schema_version` | Version | Contract version |

Evidence should store a concise supported finding and a pointer to the permitted source artifact, rather than indiscriminately duplicating source content.

### 4.4 Claim and ClaimEvidenceLink

Reuse the existing Claim/Evidence/ClaimVerification contracts rather than creating a parallel fact-checking system.

A `Claim` is a testable factual assertion. A `ClaimEvidenceLink` records whether an evidence item supports, contradicts, qualifies, or is neutral toward the claim.

Claim verification outcomes must preserve the existing distinction between verified, partially supported, unsupported, contradicted, and not yet verified (exact enum compatibility to be confirmed against the existing contract during implementation reconciliation).

Each material claim used in a creative brief or published content should be traceable to its evidence and verification history.

### 4.5 OpportunityAssessment

Represents one versioned evaluation of an opportunity at a point in time.

Required attributes:

- Assessment ID and opportunity reference.
- Assessment timestamp and assessor identity/version.
- Assessment policy and scoring-model version.
- Eligibility gate results and supporting rationale.
- Dimension scores, weights, and normalized scale.
- Evidence coverage, freshness, and confidence.
- Contradictions, unknowns, and material limitations.
- Overall disposition and recommended next action.
- Human review/override record, where applicable, with reason.
- Supersession link to prior assessment.

Assessments are immutable historical records. Reassessment creates a new version; it does not overwrite the earlier assessment.

### 4.6 OpportunityEvidenceLink

Links an opportunity to evidence, claims, audience insights, experiments, or other supporting records. Each link records its relationship:

- `SUPPORTS`
- `CHALLENGES`
- `CONTEXTUALIZES`
- `MEASURES`
- `DERIVED_FROM`
- `DUPLICATES_OR_OVERLAPS`

The link must include scope/applicability and creation provenance. A link does not automatically make the linked evidence relevant to every studio or audience.

## 5. Eligibility gates

Eligibility gates are evaluated before any weighted score. Each gate returns `PASS`, `FAIL`, or `REVIEW_REQUIRED`, plus evidence and rationale.

Recommended gate families:

1. **Evidence integrity:** source provenance is sufficient for the proposed use; material claims are not knowingly misrepresented.
2. **Audience and brand relevance:** there is a defensible connection to an approved audience need, brand pillar, or approved strategic objective.
3. **Rights and legal suitability:** known rights, licensing, privacy, legal, and platform restrictions are respected. Unknown or unverified rights are not treated as cleared.
4. **Editorial suitability:** the opportunity is compatible with approved editorial principles and does not require a prohibited or unauthorized position.
5. **Production feasibility:** required skills, assets, time, capacity, and permitted resources are available or can be assessed without unauthorized expenditure.
6. **Data permissions:** source access and proposed processing are permitted for the intended purpose.
7. **Commercial boundary:** the opportunity does not presume an unapproved financial commitment, sponsorship acceptance, paid campaign, or change to financial limits.

Gate semantics:

- `FAIL` → opportunity disposition is `INELIGIBLE` or `BLOCKED`, according to the reason.
- `REVIEW_REQUIRED` → no progression into autonomous execution; route to the appropriate review.
- `PASS` → eligible for weighted assessment, not automatically approved for execution.

Hard blockers cannot be offset by a high weighted score.

## 6. Weighted scoring model

After gates pass, an assessment may calculate a configurable weighted score.

Recommended dimensions:

| Dimension | What it evaluates |
|---|---|
| Audience value | Relevance, usefulness, unmet need, and likely value to the intended audience |
| Differentiation | Originality, distinct angle, depth, and meaningful advantage over existing coverage |
| Brand fit | Alignment with brand positioning, pillars, voice, and audience expectations |
| Evidence strength | Source quality, corroboration, claim support, freshness, and uncertainty |
| Business potential | Defensible potential to support an approved business objective |
| Production feasibility | Effort, capability, resource availability, and delivery constraints |
| Timing and durability | Timeliness, useful lifespan, and whether the opportunity is evergreen or transient |
| Strategic contribution | Contribution to portfolio balance, learning goals, and approved priorities |

Scoring rules:

- Weights are configurable by workspace/brand and policy version.
- The sum of active weights must be validated by the scoring service.
- Store raw dimension scores, weights, normalized score, and calculation version.
- Store confidence separately from score.
- Store evidence coverage and freshness separately from confidence.
- Missing data must remain missing; it must not silently become a neutral or positive score.
- A score must include a concise rationale and principal factors affecting it.
- Do not compare scores across different scoring-policy versions without an explicit normalization method.
- A score is a prioritization aid, not a probability of virality, guaranteed business result, or authorization.

No fixed numeric weights or thresholds are approved in this contract.

## 7. Confidence and evidence sufficiency

Confidence is a separate assessment of how well the available evidence supports the opportunity assessment.

The assessment should consider:

- Number and independence of relevant sources.
- Primary versus secondary evidence.
- Corroboration and contradiction.
- Source credibility and recency.
- Sample size and representativeness for audience/performance data.
- Method quality and reproducibility.
- Scope match between evidence and intended audience/platform/format.
- Missing data and known limitations.

Recommended qualitative confidence labels:

- `HIGH`
- `MEDIUM`
- `LOW`
- `INSUFFICIENT`

These labels require documented policy definitions before implementation. They must not be treated as precise statistical probabilities unless a validated statistical method explicitly supports that interpretation.

## 8. Source and evidence intelligence

Evidence assessment should reuse the shared source-trust framework:

- Primary/secondary classification.
- Publisher/source credibility and rationale.
- Publication and retrieval timestamps.
- Freshness and relevance to the specific claim.
- Independent corroboration.
- Contradiction detection.
- Claim-to-evidence traceability.
- Confidence and limitations.

The system must distinguish:

- Verified facts.
- Estimates and platform-reported metrics.
- Opinions and interpretations.
- Assumptions.
- Hypotheses requiring validation.

Conflicting or insufficient evidence should lower confidence or trigger review. It must not be silently resolved by selecting the most convenient source.

## 9. Lifecycle

Proposed opportunity lifecycle:

`DETECTED` → `TRIAGED` → `ASSESSED` → `READY_FOR_REVIEW` / `ELIGIBLE` → `SELECTED` → `IN_PROGRESS` → `REALIZED` / `EXPIRED` / `DECLINED` / `BLOCKED`

Additional rules:

- `DETECTED` means a candidate has been recorded, not validated.
- `TRIAGED` means duplicates, basic relevance, and source suitability have been checked.
- `ASSESSED` means eligibility and scoring have been evaluated.
- `READY_FOR_REVIEW` means a human or policy-authorized review is needed.
- `ELIGIBLE` means gates passed; it does not grant execution permission.
- `SELECTED` means chosen within an approved plan or portfolio.
- `IN_PROGRESS` means an authorized downstream workflow has started.
- `REALIZED` means the intended outcome was delivered or the opportunity was otherwise fulfilled.
- `EXPIRED` means its time-sensitive relevance has passed.
- `DECLINED` means it was consciously not selected.
- `BLOCKED` means a hard policy, rights, legal, permission, or safety condition prevents progression.

Transitions must be validated against actor permissions and policy. Every transition records actor, timestamp, reason, policy version, and linked assessment.

## 10. Relationship to research and content production

An opportunity may initiate a research task only when the task is within approved policies, permissions, and resource limits.

Recommended flow:

1. Detect and record candidate opportunity.
2. Deduplicate against existing opportunities and content.
3. Attach audience, brand, and source context.
4. Evaluate eligibility gates.
5. Produce a versioned assessment.
6. Select for research or planning under the applicable authority.
7. Create a research brief and evidence/claim records.
8. Create one or more studio-specific creative variants.
9. Run independent quality, rights, and approval checks for each variant.
10. Record distribution and performance outcomes.
11. Feed validated learning back into the opportunity and shared learning registry.

Research reuse does not imply creative reuse. Each studio/format variant must retain its own editorial purpose, audience fit, production record, quality assessment, and governance path.

## 11. Business opportunity boundary

Business and monetization opportunities may be discovered, evaluated, researched, and prepared for owner review.

Under the accepted commercial-authority boundary:

- AI may research sponsorship prospects, affiliate options, product ideas, pricing scenarios, revenue models, and commercial risks.
- AI may prepare draft proposals, comparison reports, forecasts, and negotiation preparation.
- AI may not accept sponsorships, sign agreements, make binding commitments, negotiate binding terms, spend money, launch unapproved commercial campaigns, or change financial limits.
- Commercial potential must not silently alter factual conclusions or editorial quality decisions.
- Revenue forecasts must be labelled as forecasts, not confirmed revenue.

A business opportunity moving to `SELECTED` does not constitute acceptance of a commercial offer or authorization to commit funds.

## 12. Permissions and access

Access is governed by the centralized identity, authorization, and data-governance contracts.

Minimum rules:

- Workspace isolation by default.
- Brand/studio scope enforced on reads and writes.
- Task-scoped least privilege for agents and workers.
- Short-lived credentials and auditable delegation.
- Restricted evidence is not exposed through summaries or embeddings to unauthorized actors.
- Cross-studio reuse requires explicit scope and applicable permissions.
- Cross-workspace sharing requires explicit authorization and must follow privacy-preserving sharing rules.
- No agent can grant itself permissions or widen its own data scope.

## 13. APIs and events

Illustrative versioned interfaces:

- `POST /v1/opportunities`
- `GET /v1/opportunities/{opportunity_id}`
- `POST /v1/opportunities/{opportunity_id}/triage`
- `POST /v1/opportunities/{opportunity_id}/assessments`
- `GET /v1/opportunities/{opportunity_id}/assessments`
- `POST /v1/opportunities/{opportunity_id}/links`
- `POST /v1/opportunities/{opportunity_id}/transitions`
- `GET /v1/evidence/{evidence_id}`
- `POST /v1/evidence`
- `POST /v1/claims/{claim_id}/evidence-links`

Illustrative domain events:

- `opportunity.detected.v1`
- `opportunity.triaged.v1`
- `opportunity.assessed.v1`
- `opportunity.review_required.v1`
- `opportunity.eligible.v1`
- `opportunity.selected.v1`
- `opportunity.expired.v1`
- `evidence.recorded.v1`
- `evidence.assessment_updated.v1`
- `claim.verification_updated.v1`

Events must use the durable event architecture, transactional outbox/inbox, idempotency keys, schema versions, actor provenance, and workspace/brand scope. Event publication is not an authorization to perform the next action.

## 14. Audit and explainability

For every consequential assessment or transition, retain:

- Opportunity and assessment IDs.
- Actor and agent/model/version, if applicable.
- Input evidence references and source snapshots/versions.
- Eligibility gate outcomes and rationale.
- Scoring policy, weights, raw scores, and calculated result.
- Confidence, evidence coverage, freshness, contradictions, and limitations.
- Human review, override, or decision record.
- Policy version and timestamp.
- Downstream workflow references and outcome.

The system must be able to answer: **Why was this opportunity prioritized, what evidence supported it, what was uncertain, which policy was applied, and who authorized the next action?**

## 15. Acceptance criteria

The contract is ready for implementation design when all of the following can be demonstrated in a controlled environment:

1. An opportunity can be created with a stable UUIDv7 and explicit workspace/brand scope.
2. Multiple source-backed evidence items can be linked without losing provenance or permissions.
3. Claims reuse the existing Claim/Evidence/ClaimVerification model.
4. Eligibility gates run before weighted scoring.
5. A failed hard gate cannot be overridden by a high score.
6. Missing evidence remains explicit and affects confidence/sufficiency.
7. Scores preserve dimension values, weights, rationale, and policy version.
8. Reassessment creates an immutable new assessment.
9. Contradictory and stale evidence is visible to reviewers.
10. Studio-specific relevance and applicability are preserved when evidence is reused.
11. Business opportunities cannot trigger prohibited commitments or spending.
12. Agent and worker access is workspace-scoped, task-scoped, and auditable.
13. Lifecycle transitions enforce actor permissions and record provenance.
14. Events are durable, versioned, and idempotently consumable.
15. Every consequential recommendation can be explained from retained evidence and policy records.

## 16. Open implementation details

These are intentionally not fixed by this 1.0 contract:

- Exact database tables, indexes, and retention implementation.
- Exact enum values and compatibility mapping to existing Claim/Evidence/ClaimVerification code.
- Numeric scoring scale, dimension weights, and thresholds.
- Statistical confidence methodology and minimum evidence/sample-size policies.
- Source credibility rubric and freshness windows by source type.
- Deduplication and opportunity-clustering algorithms.
- Opportunity expiry defaults by type.
- API authentication details and exact request/response schemas.
- Event payload schemas and compatibility policy.
- Human review roles and approval routing.
- Provider selection, deployment region, and infrastructure budget.

These details require evidence-based design and, where they change owner authority, privacy, security, rights, or financial policy, explicit owner approval.

## 17. Decision traceability

This contract operationalizes the accepted decisions covering:

- Audience intelligence and hybrid segmentation.
- Evidence-based opportunity scoring with eligibility gates.
- Source provenance, reliability, freshness, and contradiction handling.
- Privacy-first data governance and workspace isolation.
- Shared Intelligence Core with specialized studios.
- Governed cross-studio evidence reuse and learning propagation.
- Business intelligence with diversified revenue visibility.
- Commercial authority restricted to recommendation and preparation.
- Policy-governed automation and owner-centric governance.
- Durable events, auditability, and explainable consequential decisions.

It is subordinate to the Master Blueprint, System Architecture Master Reference, centralized governance contracts, and the owner-approved decision register. If a conflict is found, the centralized policy-precedence and governance rules take priority; record the conflict for reconciliation rather than silently changing this contract.

---

**End of Contract 02 — Opportunity & Evidence Model 1.0**
