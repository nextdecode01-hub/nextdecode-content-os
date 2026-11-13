# NEXTDECODE Shared Intelligence Core Contract 04
## Shared Knowledge & Learning Model
**Version:** 1.0  
**Status:** Working architecture contract — documentation only  
**Scope:** Shared Intelligence Core; workspace knowledge, studio knowledge, validated learning, and controlled knowledge reuse  
**Authority:** Derived from accepted Creator Success Intelligence decisions and architecture baselines. This document does not authorize repository changes, external integrations, data collection, production execution, spending, or publishing.

---

## 1. Purpose

Define how NEXTDECODE captures, organizes, validates, versions, retrieves, reuses, and retires knowledge across the workspace and its specialized studios.

The system must preserve the difference between raw information, evidence, claims, interpretations, hypotheses, experiments, and validated learning. It must make useful knowledge discoverable without allowing an unverified observation, one successful video, a weak correlation, or an AI-generated explanation to become permanent strategy.

The Knowledge layer is the durable memory and retrieval foundation for Creator Success Intelligence. It connects Research Intelligence, Audience Intelligence, Opportunity Intelligence, Brand Intelligence, Strategy, specialized studios, Performance Intelligence, and Business Intelligence.

## 2. Core principles

1. **Preserve epistemic status:** facts, evidence, estimates, opinions, assumptions, hypotheses, and validated learnings must remain distinguishable.
2. **Provenance is mandatory:** knowledge records retain origin, author/agent, timestamps, method, scope, and source references.
3. **Validation before promotion:** a candidate insight does not become validated strategic knowledge without meeting the relevant evidence standard.
4. **Context before reuse:** knowledge is reusable only when its audience, format, platform, time period, geography, brand, and other scope constraints are applicable.
5. **No universalization from a single result:** one viral or failed item cannot permanently determine strategy.
6. **Versioned and reversible:** updates create history; superseded knowledge remains auditable and can be reinstated when justified.
7. **Privacy and rights by design:** classification, purpose, permissions, retention, and deletion constraints travel with the knowledge record.
8. **Workspace isolation by default:** cross-workspace sharing requires explicit authorization and eligible privacy-preserving treatment.
9. **Human authority over consequential policy:** AI may identify gaps and recommend changes, but cannot rewrite owner-approved governance, mission, or brand principles.
10. **Retrieval is not authority:** finding a record does not grant permission to use its restricted content or execute an action based on it.

## 3. Knowledge layers

The system should distinguish at least these logical layers:

| Layer | Purpose | Typical records |
|---|---|---|
| Source layer | Records where information originated | Source, source snapshot, access/permission record |
| Evidence layer | Captures specific observations and support | EvidenceItem, metrics snapshot, ClaimEvidenceLink |
| Research layer | Organizes investigation and findings | Research brief, research run, synthesis, contradiction |
| Knowledge layer | Stores reusable, contextualized knowledge | KnowledgeItem, concept, relationship, playbook |
| Learning layer | Captures tested conclusions and operational learning | Hypothesis, experiment, result, LearningRecord |
| Decision layer | Preserves consequential choices | DecisionRecord, ADR, policy decision, review outcome |

These are logical responsibilities, not a mandated physical database or service decomposition. Existing source/evidence/claim contracts should be reused rather than duplicated.

## 4. Core entities

### 4.1 KnowledgeItem

A reusable unit of knowledge.

Required attributes:

- `knowledge_id`: UUIDv7.
- `workspace_id`: UUIDv7.
- `brand_id` and `studio_id`: optional scoped references.
- `knowledge_type`: versioned classification.
- `title` and concise `statement`.
- `epistemic_status`: explicit status from the taxonomy below.
- `scope`: audience, format, platform, geography, time period, brand/studio, and use case as applicable.
- `source_refs`, `evidence_refs`, `claim_refs`, and `learning_refs`.
- `confidence_assessment_ref`: separate from any opportunity or performance score.
- `limitations` and known contradictions.
- `classification`, `purpose`, `permission_refs`, and retention policy.
- `created_by`, `reviewed_by`, timestamps, and schema version.
- `current_version_ref` and supersession lineage.

Knowledge statements must be atomic enough to evaluate and reuse. Broad narrative summaries should link to their supporting items rather than pretending every sentence has identical confidence.

### 4.2 KnowledgeType

Suggested types:

- `FACT`
- `CONCEPT`
- `DEFINITION`
- `PROCESS`
- `AUDIENCE_INSIGHT`
- `MARKET_INSIGHT`
- `EDITORIAL_INSIGHT`
- `CREATIVE_PATTERN`
- `PRODUCTION_PATTERN`
- `DISTRIBUTION_PATTERN`
- `BUSINESS_INSIGHT`
- `OPERATIONAL_PLAYBOOK`
- `EXPERIMENT_LEARNING`
- `DECISION_RATIONALE`
- `OPEN_QUESTION`

The taxonomy is extensible and versioned. A type describes what a record is; it does not determine whether the record is sufficiently validated.

### 4.3 EpistemicStatus

The model must distinguish at least:

| Status | Meaning |
|---|---|
| `OBSERVED` | Directly observed information with recorded context |
| `SOURCE_REPORTED` | A source or platform reports the information; independent verification may be absent |
| `VERIFIED` | Supported to the defined verification standard for the stated scope |
| `ESTIMATED` | Derived estimate with method and uncertainty |
| `INTERPRETATION` | Reasoned explanation of evidence |
| `HYPOTHESIS` | Testable proposition not yet validated |
| `EXPERIMENTAL_LEARNING` | Result from a defined experiment, limited to its test conditions |
| `VALIDATED_LEARNING` | Learning meeting a documented validation standard for its scope |
| `DISPUTED` | Material credible evidence conflicts |
| `SUPERSEDED` | Replaced by a newer record while retaining history |
| `RETRACTED` | Withdrawn because it is erroneous, invalid, or no longer supportable |

`VERIFIED` and `VALIDATED_LEARNING` are not interchangeable: the first concerns a claim or fact; the second concerns a tested learning or operational conclusion.

### 4.4 KnowledgeVersion

An immutable version of a KnowledgeItem.

Each version stores:

- Version identifier and sequence.
- Statement and structured content.
- Status and scope.
- Evidence/source/claim references.
- Confidence and limitations.
- Change rationale.
- Author/reviewer and timestamps.
- Prior version and supersession relationship.

A correction, scope change, status promotion, or material reinterpretation creates a new version. Do not overwrite the historical record.

### 4.5 KnowledgeRelationship

Connects knowledge items and other domain records.

Suggested relationship types:

- `SUPPORTS`
- `CONTRADICTS`
- `QUALIFIES`
- `DERIVED_FROM`
- `RELATED_TO`
- `DUPLICATES`
- `APPLIES_TO`
- `NOT_APPLICABLE_TO`
- `SUPERSEDES`
- `TESTED_BY`
- `IMPLEMENTED_BY`
- `INFORMS_DECISION`

Each relationship records its source, author, timestamp, scope, and rationale. Relationships do not imply unrestricted access to either endpoint.

### 4.6 LearningRecord

A reusable record of what was learned from an experiment, production cycle, audience interaction, operational event, or business outcome.

Required fields:

- Learning ID and workspace/brand/studio scope.
- Learning statement and question it addresses.
- Originating hypothesis or decision.
- Experiment/run/content/variant references.
- Observation and measurement windows.
- Sample size and relevant cohort/context.
- Metrics and their source classification.
- Result, uncertainty, limitations, and confounders.
- Applicability scope and known exclusions.
- Validation status and validation method.
- Reviewer/approver where required.
- Policy/model version and audit history.

A LearningRecord must never claim causation when the method only supports correlation or association.

## 5. Knowledge lifecycle and promotion

Proposed lifecycle:

`CAPTURED` → `STRUCTURED` → `EVIDENCE_LINKED` → `REVIEW_REQUIRED` / `VALIDATION_PENDING` → `VALIDATED` → `ACTIVE` → `REVIEW_DUE` → `SUPERSEDED` / `RETRACTED` / `ARCHIVED`

Interpretation:

- `CAPTURED`: recorded but not yet normalized or checked.
- `STRUCTURED`: classified, scoped, and assigned an epistemic status.
- `EVIDENCE_LINKED`: relevant source, claim, and evidence references attached.
- `REVIEW_REQUIRED`: conflicts, sensitivity, uncertainty, or policy triggers review.
- `VALIDATION_PENDING`: a validation method or experiment is in progress.
- `VALIDATED`: meets the documented validation standard for the specified scope.
- `ACTIVE`: available for eligible retrieval and reuse.
- `REVIEW_DUE`: freshness or review interval requires reassessment.
- `SUPERSEDED`: replaced by a newer version or conclusion.
- `RETRACTED`: no longer supportable.
- `ARCHIVED`: retained under policy but not ordinarily used for current recommendations.

Promotion must be policy-driven. An AI agent may propose promotion and assemble evidence; it cannot bypass the applicable review or approval requirements.

## 6. Validation standards

Validation requirements depend on knowledge type and impact.

### 6.1 Factual knowledge

Require appropriate source reliability, claim-to-evidence traceability, corroboration where material, recency, and clear scope. High-impact or contested claims require stronger review.

### 6.2 Audience and performance learning

Require:

- Defined question or hypothesis.
- Clear audience, platform, format, and observation window.
- Relevant sample size and representativeness assessment.
- Metric definitions and source classification.
- Baseline or comparison where appropriate.
- Confounders and uncertainty.
- Distinction between correlation and causation.
- Replication or additional evidence before broad strategic promotion when warranted.

### 6.3 Operational learning

Require reproducible steps, environment/context, observed outcome, failure modes, and evidence that the procedure remains compatible with current system versions and policies.

### 6.4 Business learning

Require source classification for revenue/cost data, attribution caveats, time period, currency and accounting context where applicable, and separation of observed results from estimates or forecasts.

No universal numeric sample-size threshold is set in this contract. Thresholds must be defined by metric, experiment type, risk, and decision impact.

## 7. Shared Knowledge Registry and scope

The Shared Knowledge Registry is a logical capability that makes eligible knowledge discoverable across studios.

Each record must carry an explicit applicability scope, such as:

- Workspace or brand.
- Studio.
- Audience persona/segment.
- Platform/channel.
- Content format.
- Topic/domain.
- Geography/language.
- Time period.
- Production environment or software version.
- Commercial or operational context.

Retrieval must filter by both access permission and applicability. A record may be visible but not applicable; it may also be relevant but inaccessible. These conditions must not be conflated.

Cross-studio propagation rules:

1. Evidence and learning may be shared with provenance and scope intact.
2. A studio-specific result is not automatically a workspace-wide rule.
3. Workspace-level promotion requires validation for the broader scope.
4. Studio owners retain their editorial identity and local operating context.
5. Cross-studio resource or production transfers require explicit permissions/contracts.
6. Cross-workspace learning is disabled by default and requires explicit authorized, privacy-preserving contribution.

## 8. Retrieval and knowledge context assembly

Knowledge retrieval should be hybrid and permission-aware. Candidate mechanisms may include relational filtering, full-text search, embeddings/vector retrieval, and graph traversal. No specific vendor or implementation is selected here.

A retrieval request should include:

- Workspace and brand scope.
- Requesting actor/agent identity and permissions.
- Task purpose.
- Target audience, studio, format, platform, and time context.
- Required epistemic status or minimum evidence standard.
- Freshness requirements.
- Data classification permitted for the task.

A `KnowledgeContextPackage` should return:

- Relevant knowledge items and exact versions.
- Epistemic status and confidence assessment.
- Source/evidence/claim references.
- Applicability explanation.
- Known contradictions and limitations.
- Freshness/review status.
- Access and usage constraints.
- Retrieval policy/model version.

The package must not silently flatten disagreements into a single confident answer. Conflicting items should be shown as conflicting, or the retrieval result should be marked insufficient.

## 9. Autonomous knowledge improvement

The accepted self-evolving intelligence direction permits the system to:

- Detect knowledge gaps and stale records.
- Identify duplicate or contradictory knowledge.
- Suggest new relationships and taxonomies.
- Recommend retrieval/index improvements.
- Propose knowledge corrections and status changes.
- Identify recurring patterns across validated records.
- Recommend workflow improvements supported by evidence.

Autonomous activity must remain within approved boundaries:

- Low-risk retrieval organization and recommendations may be autonomous and audited.
- Low-risk reversible workflow optimizations may occur only within approved scope.
- Knowledge status promotion must follow validation rules.
- Owner-approved mission, brand principles, governance policies, security permissions, and financial/publishing limits cannot be changed autonomously.
- Agents cannot grant themselves access or expand their authority.
- Sensitive or restricted knowledge cannot be moved into broader contexts merely to improve retrieval.

## 10. Memory and learning separation

The system should keep three related but distinct concepts:

1. **Knowledge memory:** what is currently believed or known, with evidence and scope.
2. **Operational memory:** what happened in a run, workflow, experiment, or incident.
3. **Strategic learning:** what has been validated sufficiently to inform future planning or policy proposals.

Operational logs are not automatically knowledge. A repeated event is not automatically a validated pattern. A validated learning does not automatically become an owner-approved strategy or policy.

## 11. Privacy, rights, and retention

Every knowledge item and version inherits or explicitly records:

- Data classification: Public, Internal, Confidential, or Restricted.
- Purpose limitation and permitted processing.
- Source permissions/consent where applicable.
- Workspace/brand isolation.
- Retention and deletion policy.
- Rights and licensing constraints.
- Personal-data minimization and anonymization requirements.
- Legal hold or other retention restrictions.
- Audit history for access, export, promotion, and deletion.

Embeddings, summaries, indexes, caches, and derived records are also governed data. Deleting or restricting a source may require corresponding action on derived knowledge and retrieval indexes. The implementation must provide traceable deletion assurance rather than assuming removal from the primary record is sufficient.

## 12. APIs and events

Illustrative versioned interfaces:

- `POST /v1/knowledge/items`
- `GET /v1/knowledge/items/{knowledge_id}`
- `GET /v1/knowledge/items/{knowledge_id}/versions`
- `POST /v1/knowledge/items/{knowledge_id}/versions`
- `POST /v1/knowledge/items/{knowledge_id}/relationships`
- `POST /v1/knowledge/retrieval`
- `POST /v1/knowledge/validation-requests`
- `POST /v1/learning-records`
- `GET /v1/learning-records/{learning_id}`
- `POST /v1/learning-records/{learning_id}/promotion`

Illustrative events:

- `knowledge.item.captured.v1`
- `knowledge.item.structured.v1`
- `knowledge.evidence.linked.v1`
- `knowledge.validation.requested.v1`
- `knowledge.item.validated.v1`
- `knowledge.item.retracted.v1`
- `knowledge.item.superseded.v1`
- `knowledge.conflict.detected.v1`
- `learning.record.created.v1`
- `learning.record.promoted.v1`
- `knowledge.review.due.v1`

Events must use the durable event architecture, transactional outbox/inbox, idempotency, schema versioning, actor provenance, and workspace scope. An event is a record of a domain change, not authorization for an unrelated action.

## 13. Audit and explainability

For consequential retrieval, promotion, correction, or retirement, preserve:

- Actor, agent/model/version, and task purpose.
- Knowledge item and exact version.
- Sources, evidence, claims, and experiment references.
- Scope and applicability decision.
- Validation method, evidence coverage, and limitations.
- Status transition and rationale.
- Policy and retrieval/scoring versions.
- Human review/approval where applicable.
- Downstream decisions and workflows informed by the record.

The system must be able to answer:

- Where did this knowledge come from?
- What evidence supports it?
- What is its epistemic status?
- Where and when does it apply?
- What contradicts or limits it?
- Why was it promoted or retired?
- Which decisions or content workflows used it?

## 14. Acceptance criteria

The contract is ready for implementation design when:

1. Raw sources, evidence, claims, knowledge, operational records, and learning are distinct but linked.
2. Every knowledge item has provenance, scope, epistemic status, classification, and version history.
3. Knowledge updates preserve prior versions.
4. Factual verification is distinct from experiment/strategic learning validation.
5. Validation standards vary by knowledge type and decision impact.
6. One content result cannot automatically become permanent workspace strategy.
7. Contradictions, uncertainty, stale records, and missing evidence remain visible.
8. Retrieval enforces permissions and applicability, not semantic similarity alone.
9. Cross-studio learning retains scope and provenance.
10. Cross-workspace sharing is disabled unless explicitly authorized.
11. Deletion and restriction propagate to derived indexes and governed artifacts.
12. AI self-improvement cannot change owner-approved policies or grant itself permissions.
13. Consequential knowledge changes and retrievals are auditable.
14. APIs and events are versioned, durable, and idempotently consumable.

## 15. Open implementation details

Not fixed by this contract:

- Exact relational and graph schema.
- Search/index/vector technology and provider.
- Knowledge chunking and embedding strategy.
- Confidence methodology and thresholds.
- Validation thresholds by metric/experiment type.
- Review cadence and freshness windows by knowledge category.
- Retention periods and derived-data deletion mechanics.
- Exact status enum compatibility with existing contracts.
- API/event payload schemas.
- Human review roles and approval routing.
- Deployment provider, region, and infrastructure cost.

These details require technical evidence and policy review. This contract does not authorize a new provider, service, data collection source, or deployment.

## 16. Decision traceability

This contract operationalizes accepted decisions covering:

- Evidence-based source intelligence and claim verification.
- Validated performance learning and controlled experimentation.
- Shared Learning Registry with applicability controls.
- Hybrid audience segmentation and cross-platform identity caution.
- Privacy-first governance and workspace isolation.
- Autonomous self-evolving intelligence within owner-controlled boundaries.
- Durable operational memory, checkpoint recovery, and auditability.
- Data sovereignty, exportability, deletion assurance, and provider restrictions.
- Strategic knowledge integration and owner-ratified mission/strategy changes.

It is subordinate to the Master Blueprint, System Architecture Master Reference, Opportunity & Evidence Model, Brand & Editorial Intelligence Model, centralized governance contracts, and owner-approved decision register. Conflicts must be recorded and reconciled rather than silently resolved by weakening a higher-priority rule.

---

**End of Contract 04 — Shared Knowledge & Learning Model 1.0**
