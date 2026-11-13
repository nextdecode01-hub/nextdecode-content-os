# NEXTDECODE — Canonical Data Dictionary & Entity Ownership Registry
## Architecture Reconciliation Artifact 01
**Version:** 1.0  
**Date:** 31 October 2026  
**Status:** Working architecture standard — documentation only  
**Scope:** Shared Intelligence Core, Content Graph, orchestration, specialized studios, governance and distribution  
**Authority:** Reconciliation proposal derived from NEXTDECODE Shared Intelligence Core Contracts 01–12, System Architecture & Pipeline Parts 1–8, and the accepted three-layer product architecture. This document does not authorize repository access or changes, schema migrations, integrations, provider connections, spending, deployments, account changes, production execution or publishing.

---

## 1. Purpose

This document establishes a single proposed source-of-truth map for NEXTDECODE's shared entities and data domains.

It addresses a key architecture risk identified in the Integration & Consistency Review: multiple contracts describe related entities independently. Without explicit ownership, the system could create duplicate audience segments, studio identities, claims, evidence records, workflow states, assets or metrics.

The goals are to:

1. Assign one authoritative owning domain to every canonical entity.
2. Define shared naming, identity, versioning, scope and provenance conventions.
3. Establish which modules may create, update, reference, extend or consume each entity.
4. Prevent duplicate definitions and conflicting lifecycle state.
5. Preserve traceability across research, knowledge, strategy, creation, QA, distribution, analytics and business intelligence.
6. Provide a stable basis for the next lifecycle, API/event and authorization standards.

**Important:** This is a logical data dictionary and ownership standard. It is not a final SQL schema, ORM model, migration, API specification or proof of current implementation.

## 2. Architecture principles

### 2.1 One canonical owner per entity

Every canonical entity has exactly one owning domain responsible for:
- Its authoritative definition and schema version.
- Creation and lifecycle transition rules.
- Validation and integrity constraints.
- Retention and archival requirements in coordination with central policy.
- Publishing canonical events for material changes.
- Compatibility and deprecation decisions.

Other domains may maintain read models, caches or typed extensions, but must not create competing canonical identities.

### 2.2 UUIDv7 is the canonical identity

- Every internal entity uses a UUIDv7 canonical ID.
- Human-readable prefixes such as `cnt_`, `art_` or `job_` may be used only as optional display/reference aliases.
- A prefix is not a second identity system and must never be used as a database identity substitute.
- External platform identifiers remain separate, namespaced fields.
- IDs are immutable and never reused.

This resolves the mismatch between UUIDv7 in the Shared Intelligence Core contracts and prefixed examples in System Architecture Part 3.

### 2.3 Stable identity versus immutable version

Use two distinct concepts:

- **Entity identity:** the stable UUIDv7 representing the logical object.
- **Version identity:** a separate immutable UUIDv7 or immutable version key representing a specific revision.

An entity may have many versions. A version is never silently overwritten.

### 2.4 Scope is explicit

Where applicable, canonical records carry:
- `workspace_id`
- `brand_id`
- `studio_id`
- `platform_id`
- `channel_account_id`
- `owner_actor_ref`
- `classification`
- `purpose`

Not every record needs every scope field. Required scope is defined by the owning entity contract. Absence must mean genuinely not applicable, not an implicit global scope.

### 2.5 Domain ownership is not deployment topology

Logical domains do not imply one microservice per entity or product module. The initial system may implement multiple domains within a modular application, provided ownership boundaries and contracts remain explicit.

### 2.6 Central policy is authoritative

Data classification, access, retention, privacy, rights, external provider eligibility and authorization are governed centrally. Domain ownership does not permit a domain to weaken central policy.

---

## 3. Canonical field conventions

| Field | Convention | Meaning |
|---|---|---|
| `{entity}_id` | UUIDv7 | Stable canonical identity |
| `{entity}_version_id` | UUIDv7 or immutable version key | Exact immutable revision |
| `workspace_id` | UUIDv7 | Owning workspace |
| `brand_id` | UUIDv7 | Brand scope, when applicable |
| `studio_id` | UUIDv7 | Studio scope, when applicable |
| `*_ref` | Typed canonical reference | Reference to another entity or actor |
| `*_refs` | Array of typed references | Multiple related entities |
| `status` | Avoid as an unqualified field in new contracts | Use a named lifecycle, epistemic, quality or authorization field |
| `lifecycle_status` | Domain-owned enum | State in the entity's lifecycle |
| `epistemic_status` | Shared enum | Nature/validation status of a knowledge assertion |
| `provenance_type` | Shared enum with domain extensions | Origin or derivation of a value |
| `classification` | Central policy enum | Public, Internal, Confidential, Restricted |
| `purpose` | Controlled description/reference | Authorized purpose for collection and use |
| `schema_version` | Versioned contract identifier | Shape/meaning of record |
| `created_at` / `updated_at` | UTC timestamp | Record audit timestamps |
| `created_by` / `updated_by` | Actor reference | Human, agent, service or worker responsible |
| `valid_from` / `valid_to` | UTC timestamp, nullable | Domain validity interval |
| `observed_at` | UTC timestamp | When an observation occurred |
| `captured_at` | UTC timestamp | When system captured the observation |
| `correlation_id` | UUIDv7 | Trace across related operations |
| `causation_id` | UUIDv7, nullable | Immediate triggering event/command |
| `content_hash` | Algorithm + digest | Integrity reference for exact bytes/content |

### 3.1 Avoid ambiguous generic fields

Do not use one `status` field to represent several different concepts. Use explicit fields such as:
- `lifecycle_status`
- `epistemic_status`
- `quality_outcome`
- `governance_disposition`
- `approval_outcome`
- `execution_status`
- `external_operation_status`

### 3.2 Timestamps and time windows

- Store machine timestamps in UTC.
- Preserve source timezone and source-reported time when relevant.
- Record observation windows as explicit start/end pairs.
- A metric without a defined time window must not be treated as directly comparable to a windowed metric.

---

## 4. Canonical domain ownership registry

| Domain | Canonical owner | Primary responsibility |
|---|---|---|
| Workspace & Content Graph | Shared Data Model / Part 3 | Workspace, canonical IDs, graph relationships and cross-domain references |
| Audience & Identity Context | Contract 01 | Personas, segments, audience identity boundaries and audience insights |
| Opportunity & Evidence | Contract 02 | Opportunities, source records, evidence items, claims and claim-evidence links |
| Brand & Editorial Intelligence | Contract 03 | Parent brand, brand versions, studio identities, voice, visual and editorial profiles |
| Knowledge & Learning | Contract 04 | Reusable knowledge, knowledge versions, epistemic status and validated learning |
| Research Intelligence | Contract 05 | Research requests/runs, source assessment, synthesis, monitoring and handoffs |
| Strategy & Portfolio | Contract 06 | Objectives, portfolio strategy, editorial programs, initiatives and planning |
| Quality, Rights & Governance | Contract 07 | QA assessments, rights registry, governance decisions, approvals and authorization |
| Audience & Performance | Contract 08 | Metric definitions, performance snapshots, experiments, attribution and audience-performance analysis |
| Business & Monetization | Contract 09 | Commercial opportunities, prospects, proposals, financial records and business performance |
| Agent & Resource Orchestration | Contract 10 + Parts 4/5/8 | Agent/provider/model registry, task delegation, resource accounts, workers and durable execution |
| Multiformat Creation | Contract 11 + Part 7 | Creation projects, studio productions, format profiles and format-native artifacts |
| Distribution & Publishing | Contract 12 + Contract 07 | Channel profiles, distribution packages, schedules, publish operations and publication reconciliation |
| Artifact & Asset Management | Part 7 + Contract 07 | Binary metadata, immutable artifact versions, asset provenance and rights references |
| Security & Data Governance | Part 8 + central policy layer | Classification, access, retention, provider eligibility, identity and security controls |

---

## 5. Entity registry — Workspace and Content Graph

### 5.1 Workspace

**Owner:** Shared Data Model / Workspace layer.

**Purpose:** Top-level tenant and isolation boundary.

**Canonical fields**
- `workspace_id`
- `name`
- `workspace_type`
- `lifecycle_status`
- `owner_actor_ref`
- `default_classification_policy_ref`
- `default_retention_policy_ref`
- `created_at`, `updated_at`
- `schema_version`

**Rules**
- Every tenant-scoped entity belongs to one workspace.
- Workspace membership and access are controlled by identity/security policy.
- Workspace boundaries are not crossed by implicit retrieval or learning.
- Future workspace federation requires explicit policy and sharing authorization.

### 5.2 Actor

**Owner:** Identity and Security layer.

**Purpose:** Represent a human, agent, service, worker or external system participating in an operation.

**Canonical fields**
- `actor_id`
- `actor_type`: `HUMAN`, `AGENT`, `SERVICE`, `WORKER`, `EXTERNAL_SYSTEM`
- `display_name`
- `identity_provider_ref`, where applicable
- `lifecycle_status`
- `created_at`, `updated_at`

**Rules**
- Human, agent and worker identities are distinct.
- Actor identity does not itself grant permissions.
- Authorization is evaluated separately for each action and scope.

### 5.3 Brand and Studio references

Canonical definitions are owned by Contract 03. Workspace and Content Graph store references, not duplicate brand identity objects.

### 5.4 ContentItem

**Owner:** Shared Content Graph.

**Purpose:** Canonical editorial/content concept independent of any one format derivative.

**Canonical fields**
- `content_item_id`
- `workspace_id`
- `brand_id`
- `origin_opportunity_id`, nullable
- `primary_audience_refs`
- `editorial_pillar_refs`
- `content_type`
- `lifecycle_status`
- `current_content_version_id`
- `created_by`, `created_at`, `updated_at`
- `schema_version`

**Rules**
- A ContentItem represents the shared editorial subject or content initiative.
- It is not the same as a StudioProduction, render, distribution package or publication.
- Format derivatives reference the ContentItem and maintain independent production/QA histories.

### 5.5 Relationship

**Owner:** Shared Content Graph.

**Purpose:** Typed relationship between canonical entities.

**Canonical fields**
- `relationship_id`
- `workspace_id`
- `source_entity_type`, `source_entity_id`
- `relationship_type`
- `target_entity_type`, `target_entity_id`
- `valid_from`, `valid_to`
- `created_by`, `created_at`
- `schema_version`

**Rules**
- Relationship types are controlled and versioned.
- Invalid or unauthorized cross-workspace links are rejected.
- Relationships do not grant access or ownership.

---

## 6. Entity registry — Audience and Identity (Contract 01)

Contract 01 is the single canonical owner of audience identity concepts. Contract 08 references these entities.

### 6.1 Audience

**Fields**
- `audience_id`
- `workspace_id`
- `name`, `description`, `purpose`
- `lifecycle_status`
- `current_version_id`
- audit fields and `schema_version`

### 6.2 StrategicPersona

**Fields**
- `persona_id`
- `audience_id`
- `name`, `description`
- `needs`, `goals`, `questions`, `barriers`
- `assumptions_and_limitations`
- `evidence_refs`
- `confidence_assessment_ref`
- `lifecycle_status`
- `persona_version_id`

**Rules**
- Strategic personas are human-defined strategic models.
- They must not be presented as observed individual-level facts.
- Assumptions and supporting evidence are explicitly distinguished.

### 6.3 AudienceSegment

**Canonical field name:** `audience_segment_id`.

**Fields**
- `audience_segment_id`
- `audience_id`
- `segment_type`: `STRATEGIC`, `OBSERVED`, `EMERGING`
- `name`, `definition`
- `scope`
- `evidence_refs`
- `confidence_assessment_ref`
- `valid_from`, `valid_to`
- `lifecycle_status`
- `segment_version_id`

**Rules**
- Contract 01 owns the canonical entity.
- Contract 08 must not create a second `AudienceSegment` identity.
- Platform-specific observations remain scoped to the relevant platform/dataset.
- No cross-platform person identity matching is assumed.

### 6.4 PlatformAudienceSnapshot

**Fields**
- `platform_audience_snapshot_id`
- `audience_segment_id`, nullable
- `platform_id`
- `channel_account_id`
- `observation_window`
- `metric_observation_refs`
- `provenance_type`
- `limitations`
- `captured_at`

### 6.5 AudienceInsight

**Canonical field name:** `audience_insight_id`.

**Fields**
- `audience_insight_id`
- `workspace_id`, `brand_id`, optional `studio_id`
- `subject_type`, `subject_id`
- `insight_type`
- `statement`
- `evidence_refs`
- `method`
- `observation_window`
- `confidence_assessment_ref`
- `limitations`
- `classification`, `purpose`
- `lifecycle_status`
- `insight_version_id`

**Rules**
- Contract 01 owns canonical audience insights.
- Contract 08 may link performance observations as supporting evidence.
- A performance-derived interpretation must not silently overwrite an audience insight; it creates a new version or a linked assessment.

---

## 7. Entity registry — Opportunity and Evidence (Contract 02)

Contract 02 owns canonical opportunity, source, evidence and claim identities.

### 7.1 Opportunity

**Fields**
- `opportunity_id`
- `workspace_id`, optional `brand_id`
- `opportunity_type`
- `title`, `summary`, `problem_or_need`
- `target_audience_refs`
- `related_brand_pillar_refs`
- `origin_ref`
- `first_observed_at`, `last_observed_at`, optional `valid_until`
- `lifecycle_status`
- `owner_ref`
- `created_by`, `updated_by`
- `schema_version`

### 7.2 EvidenceSource

**Fields**
- `evidence_source_id`
- `source_type`
- `canonical_locator`, where permitted
- `publisher_or_origin`
- `published_at`, `accessed_at`, `captured_at`
- `source_status`
- `credibility_assessment_ref`
- `permission_ref`
- `classification`
- `schema_version`

**Rules**
- Source records describe origin/provenance; they are not themselves claims.
- Access and use permissions are separately recorded.
- A source may be inaccessible, withdrawn, expired or restricted without deleting historical provenance.

### 7.3 EvidenceItem

**Fields**
- `evidence_item_id`
- `evidence_source_id`
- `evidence_type`
- `statement`
- `observed_at`, `captured_at`
- `valid_from`, `valid_to`
- `scope`
- `method`
- `limitations`
- `reliability_assessment_ref`
- `classification`
- `permission_ref`
- `content_hash`
- `schema_version`

### 7.4 Claim

**Fields**
- `claim_id`
- `workspace_id`
- `claim_text`
- `claim_type`
- `criticality`
- `scope`
- `epistemic_status`
- `confidence_assessment_ref`
- `valid_from`, `review_after`
- `lifecycle_status`
- `claim_version_id`

### 7.5 ClaimEvidenceLink

**Fields**
- `claim_evidence_link_id`
- `claim_id`
- `evidence_item_id`
- `relationship`: supports, contradicts, qualifies, contextualizes
- `strength_assessment`
- `reviewer_ref`
- `created_at`

### 7.6 OpportunityAssessment

**Fields**
- `opportunity_assessment_id`
- `opportunity_id`
- `assessment_version_id`
- `eligibility_results`
- `weighted_score`
- `dimension_scores`
- `confidence_assessment_ref`
- `rationale`
- `assessed_by`
- `assessed_at`

**Rules**
- Eligibility gates execute before weighted scoring.
- A hard failure cannot be offset by a high score.
- An assessment is a versioned decision input, not an authorization to execute.

---

## 8. Entity registry — Brand and Editorial Intelligence (Contract 03)

Contract 03 owns canonical brand and studio identity. Contract 11 references immutable versions.

### 8.1 WorkspaceBrand

**Fields**
- `brand_id`
- `workspace_id`
- `brand_name`
- `brand_purpose`, `brand_promise`, `positioning_statement`
- `primary_audience_refs`
- `brand_pillar_refs`
- `brand_principle_refs`
- `lifecycle_status`
- `current_identity_version_id`
- `owner_actor_ref`

### 8.2 BrandIdentityVersion

**Fields**
- `brand_identity_version_id`
- `brand_id`
- `version_label`
- `positioning`
- `voice_profile_ref`
- `visual_language_ref`
- `editorial_principle_refs`
- `effective_from`, `effective_to`
- `approval_ref`
- `created_at`

### 8.3 StudioIdentity

**Fields**
- `studio_id`
- `workspace_id`, `brand_id`
- `studio_name`, `studio_purpose`
- `editorial_focus`, `editorial_personality`
- `voice_profile_ref`, `visual_language_ref`
- `format_profile_refs`
- `parent_brand_identity_version_id`
- `lifecycle_status`
- `current_studio_identity_version_id`

### 8.4 StudioIdentityVersion

**Fields**
- `studio_identity_version_id`
- `studio_id`
- `parent_brand_identity_version_id`
- `editorial_focus`
- `voice_profile_ref`, `visual_language_ref`
- `format_profile_refs`
- `effective_from`, `effective_to`
- `approval_ref`
- `created_at`

**Rules**
- Contract 11 must reference `studio_identity_version_id`.
- Production-specific settings belong to FormatProfile or StudioProduction, not StudioIdentity.
- Brand evolution requires owner approval under Contract 03.

---

## 9. Entity registry — Knowledge and Learning (Contract 04)

### 9.1 KnowledgeItem

**Fields**
- `knowledge_item_id`
- `workspace_id`, optional `brand_id`, `studio_id`
- `knowledge_type`
- `title`, `statement_or_content_ref`
- `scope`
- `epistemic_status`
- `confidence_assessment_ref`
- `source_refs`, `evidence_refs`, `claim_refs`
- `classification`, `purpose`
- `lifecycle_status`
- `current_knowledge_version_id`

### 9.2 KnowledgeVersion

**Fields**
- `knowledge_version_id`
- `knowledge_item_id`
- `content_ref` or structured content
- `epistemic_status`
- `scope`
- `evidence_refs`
- `limitations`
- `valid_from`, `review_after`
- `created_by`, `created_at`

### 9.3 KnowledgeRelationship

**Fields**
- `knowledge_relationship_id`
- `source_knowledge_item_id`
- `relationship_type`
- `target_knowledge_item_id`
- `scope`
- `created_at`

### 9.4 LearningRecord

**Fields**
- `learning_record_id`
- `workspace_id`
- `learning_type`
- `statement`
- `hypothesis_ref`, optional
- `experiment_result_ref`, optional
- `supporting_evidence_refs`
- `validated_scope`
- `epistemic_status`
- `confidence_assessment_ref`
- `limitations`
- `promotion_status`
- `created_at`, `review_after`

**Rules**
- Contract 04 owns shared epistemic status.
- `VERIFIED` and `VALIDATED_LEARNING` remain distinct.
- Learning promotion is scope-aware and evidence-backed.
- Knowledge access does not imply ownership of the underlying asset or IP.

---

## 10. Entity registry — Research Intelligence (Contract 05)

### 10.1 ResearchRequest

**Fields**
- `research_request_id`
- `workspace_id`
- `request_type`
- `primary_question`
- `decision_context`
- `scope`
- `required_depth`
- `freshness_requirement`
- `source_policy_ref`
- `data_classification_ceiling`
- `resource_policy_ref`
- `output_contract`
- `requested_by`
- `lifecycle_status`

### 10.2 ResearchRun

**Fields**
- `research_run_id`
- `research_request_id`
- `plan_version_id`
- `source_refs`
- `evidence_refs`
- `claim_refs`
- `contradiction_refs`
- `research_output_artifact_ref`
- `quality_assessment_ref`
- `started_at`, `completed_at`
- `lifecycle_status`

### 10.3 SourceAssessment

**Fields**
- `source_assessment_id`
- `evidence_source_id`
- `assessment_method`
- `credibility_dimensions`
- `independence_assessment`
- `freshness_assessment`
- `limitations`
- `assessed_at`
- `assessment_version_id`

### 10.4 ResearchSynthesis

**Fields**
- `research_synthesis_id`
- `research_run_id`
- `summary`
- `findings`
- `claim_refs`
- `evidence_refs`
- `unresolved_questions`
- `contradiction_refs`
- `limitations`
- `freshness`
- `output_artifact_ref`

**Rules**
- Research execution is owned by Contract 05.
- Canonical source/evidence/claim identities remain owned by Contract 02.
- Research `COMPLETED` does not mean every claim is verified.
- Downstream use must inspect claim-level support and unresolved issues.

---

## 11. Entity registry — Strategy and Portfolio (Contract 06)

### 11.1 StrategicObjective

**Fields**
- `strategic_objective_id`
- `workspace_id`, optional `brand_id`
- `objective_dimension`
- `title`, `description`
- `success_measures`
- `target_window`
- `lifecycle_status`
- `approval_ref`
- `owner_ref`

### 11.2 PortfolioStrategyVersion

**Fields**
- `portfolio_strategy_version_id`
- `workspace_id`, `brand_id`
- `objective_refs`
- `portfolio_balance`
- `planning_horizon`
- `assumptions`
- `resource_envelope_ref`
- `approval_ref`
- `effective_from`, `effective_to`

### 11.3 PortfolioItem

**Fields**
- `portfolio_item_id`
- `opportunity_id` or `content_item_id`
- `portfolio_strategy_version_id`
- `priority_assessment_ref`
- `target_window`
- `capacity_estimate`
- `dependencies`
- `lifecycle_status`

### 11.4 EditorialProgram

**Fields**
- `editorial_program_id`
- `workspace_id`, `brand_id`, optional `studio_id`
- `name`, `promise`, `editorial_scope`
- `audience_refs`
- `brand_pillar_refs`
- `format_profile_refs`
- `portfolio_strategy_version_id`
- `lifecycle_status`

### 11.5 StrategicInitiative

**Fields**
- `strategic_initiative_id`
- `objective_refs`
- `title`, `scope`
- `owner_ref`
- `milestones`
- `resource_envelope_ref`
- `lifecycle_status`

**Rules**
- Contract 06 owns strategic planning records.
- A strategy recommendation does not authorize production, expenditure or publication.
- Mission, positioning and major strategic priority changes remain owner-approved.

---

## 12. Entity registry — Quality, Rights and Governance (Contract 07)

### 12.1 QualityAssessment

**Fields**
- `quality_assessment_id`
- `subject_entity_type`, `subject_entity_id`
- `subject_version_id`
- `assessment_type`
- `quality_dimensions`
- `quality_outcome`: `PASS`, `PASS_WITH_WARNINGS`, `NEEDS_REVIEW`, `BLOCKED`
- `findings`
- `assessed_by`
- `assessment_version_id`
- `assessed_at`

### 12.2 AssetRightsRecord

**Fields**
- `rights_record_id`
- `asset_id` or `artifact_version_id`
- `rights_holder_ref`
- `source_ref`
- `license_or_permission_ref`
- `permitted_uses`
- `prohibited_uses`
- `territory`, `platform`, `duration`, where applicable
- `rights_status`: `CLEARED`, `RESTRICTED`, `PENDING_VERIFICATION`, `PROHIBITED`, `UNKNOWN`
- `evidence_refs`
- `review_after`
- `rights_record_version_id`

### 12.3 GovernanceDecision

**Fields**
- `governance_decision_id`
- `subject_entity_type`, `subject_entity_id`
- `subject_version_id`
- `action`
- `governance_disposition`: `ELIGIBLE`, `PENDING_APPROVAL`, `BLOCKED`, `EXPIRED`
- `policy_version`
- `hard_blockers`
- `conditions`
- `reason_codes`
- `decided_at`
- `decision_actor_ref`

### 12.4 ApprovalRequest and ApprovalDecision

**ApprovalRequest fields**
- `approval_request_id`
- `subject_entity_type`, `subject_entity_id`
- `subject_version_id`
- `requested_action`
- `destination_context`
- `policy_version`
- `expires_at`
- `requested_by`

**ApprovalDecision fields**
- `approval_decision_id`
- `approval_request_id`
- `decision`: `APPROVED`, `REJECTED`, `EXPIRED`, `REVOKED`
- `decided_by`
- `decided_at`
- `reason`
- `signature_or_attestation_ref`, where supported

### 12.5 PublishingAuthorization

**Fields**
- `publishing_authorization_id`
- `approval_decision_id`, when required
- `subject_version_id`
- `distribution_package_version_id`
- `channel_account_id`
- `requested_action`
- `policy_version`
- `authorized_by`
- `authorized_at`
- `expires_at`
- `authorization_status`
- `idempotency_key`

**Rules**
- Contract 07 owns central QA, rights, governance and authorization.
- `APPROVED_FOR_HANDOFF` in Contract 11 is not a publishing approval.
- Hard blockers cannot be overridden by ordinary approval.
- Autonomous public publishing remains disabled pending separate owner-approved policy.

---

## 13. Entity registry — Audience and Performance (Contract 08)

Contract 08 owns performance observations and measurement, not canonical audience identity.

### 13.1 MetricDefinition

**Fields**
- `metric_definition_id`
- `metric_name`
- `definition`
- `unit`
- `aggregation_rule`
- `source_requirements`
- `valid_dimensions`
- `metric_version_id`

### 13.2 MetricObservation

**Fields**
- `metric_observation_id`
- `metric_definition_id`
- `subject_entity_type`, `subject_entity_id`
- `platform_id`, optional `channel_account_id`
- `value`
- `observation_window`
- `provenance_type`
- `source_ref`
- `captured_at`
- `limitations`

### 13.3 PerformanceSnapshot

**Fields**
- `performance_snapshot_id`
- `subject_entity_type`, `subject_entity_id`
- `metric_observation_refs`
- `comparison_context`
- `measurement_window`
- `provenance_summary`
- `created_at`

### 13.4 Experiment and ExperimentResult

**Experiment fields**
- `experiment_id`
- `hypothesis`
- `scope`
- `variables`
- `control_or_comparison`
- `sample_requirements`
- `measurement_window`
- `success_criteria`
- `approval_ref`
- `lifecycle_status`

**ExperimentResult fields**
- `experiment_result_id`
- `experiment_id`
- `observations`
- `result_classification`: positive, negative, mixed, inconclusive, invalid
- `limitations`
- `confidence_assessment_ref`
- `validated_scope`

### 13.5 AttributionRecord

**Fields**
- `attribution_record_id`
- `conversion_or_outcome_ref`
- `touchpoint_refs`
- `attribution_model_version`
- `attributed_value`
- `provenance_type`
- `limitations`

**Rules**
- Contract 08 references Contract 01 audience entities.
- Platform observations retain platform/account scope.
- Correlation is not causation.
- A single viral item cannot permanently change strategy.

---

## 14. Entity registry — Business and Monetization (Contract 09)

### 14.1 BusinessOpportunity

**Fields**
- `business_opportunity_id`
- `workspace_id`, `brand_id`
- `business_model_type`
- `title`, `summary`
- `audience_value`
- `commercial_assumptions`
- `evidence_refs`
- `lifecycle_status`
- `owner_ref`

### 14.2 CommercialProspect

**Fields**
- `commercial_prospect_id`
- `organization_or_person_reference`
- `relationship_context`
- `source_ref`
- `classification`
- `contact_permission_ref`
- `lifecycle_status`

### 14.3 CommercialProposal

**Fields**
- `commercial_proposal_id`
- `business_opportunity_id`
- `prospect_ref`
- `proposal_version_id`
- `scope`, `deliverables`
- `commercial_terms_draft`
- `financial_assumptions`
- `owner_review_status`

### 14.4 FinancialRecord

**Fields**
- `financial_record_id`
- `record_type`: revenue, refund, expense, fee, tax, receivable, payable, adjustment
- `amount`, `currency`
- `transaction_or_service_date`
- `source_reference`
- `value_classification`: confirmed, platform-reported, attributed, estimated, forecast
- `reconciliation_status`
- `related_content_refs`
- `related_business_opportunity_ref`
- `created_at`

### 14.5 BusinessPerformanceSnapshot

**Fields**
- `business_performance_snapshot_id`
- `measurement_window`
- `financial_record_refs`
- `revenue`, `cost`, `margin`, `pipeline` views
- `concentration_metrics`
- `provenance_summary`
- `limitations`

**Rules**
- Contract 09 owns financial records and business performance.
- Contract 08 owns general metric definitions and experiments.
- Financial truth is not inferred solely from platform analytics.
- AI may research and prepare commercial material, but cannot accept agreements, sign, negotiate binding terms, spend or create commitments.

---

## 15. Entity registry — Agent, Resource and Orchestration (Contract 10; Parts 4 and 5)

### 15.1 AgentIdentity and AgentVersion

**AgentIdentity fields**
- `agent_id`
- `agent_name`
- `agent_type`
- `owner_ref`
- `workspace_scope`
- `lifecycle_status`
- `current_agent_version_id`

**AgentVersion fields**
- `agent_version_id`
- `agent_id`
- `capability_refs`
- `instruction_contract_version`
- `tool_allowlist`
- `data_access_profile_ref`
- `evaluation_profile_ref`
- `created_at`

### 15.2 AgentCapability

**Fields**
- `agent_capability_id`
- `agent_id`, `agent_version_id`
- `capability_name`
- `input_contract_ref`
- `output_contract_ref`
- `quality_requirements`
- `constraints`
- `evaluation_results`

### 15.3 ProviderRecord and ModelRecord

**ProviderRecord fields**
- `provider_id`
- `provider_name`
- `provider_type`
- `data_protection_assessment_ref`
- `permitted_classification_ceiling`
- `retention_terms_verified`
- `training_use_policy`
- `region_constraints`
- `lifecycle_status`

**ModelRecord fields**
- `model_id`
- `provider_id`
- `model_name`
- `capability_profile`
- `quality_evaluation_ref`
- `cost_profile_ref`
- `latency_profile_ref`
- `quota_profile_ref`
- `availability_status`

**Rules**
- Provider/model eligibility is policy-evaluated before task routing.
- An agent cannot add providers or grant itself new capabilities.
- No provider connection or subscription is authorized by this document.

### 15.4 Task

**Fields**
- `task_id`
- `workflow_run_id`
- `task_type`
- `input_refs`
- `required_capabilities`
- `priority`
- `assigned_agent_ref`
- `delegation_ref`
- `resource_reservation_ref`
- `lifecycle_status`
- `idempotency_key`

### 15.5 WorkflowDefinition and WorkflowRun

**WorkflowDefinition fields**
- `workflow_definition_id`
- `workflow_name`
- `workflow_version_id`
- `step_contracts`
- `policy_requirements`

**WorkflowRun fields**
- `workflow_run_id`
- `workflow_definition_version_id`
- `workspace_id`
- `subject_refs`
- `correlation_id`
- `lifecycle_status`
- `started_at`, `completed_at`

### 15.6 Job and JobAttempt

**Job fields**
- `job_id`
- `workflow_run_id`
- `task_id`, nullable where a job is not agent-task-backed
- `step_key`
- `job_type`
- `contract_version`
- `input_refs`
- `required_worker_capabilities`
- `priority`
- `lifecycle_status`
- `scheduled_at`, `deadline_at`
- `attempt_count`, `max_attempts`
- `idempotency_key`
- `policy_version`
- `correlation_id`

**JobAttempt fields**
- `job_attempt_id`
- `job_id`
- `attempt_number`
- `worker_id`
- `started_at`, `ended_at`
- `failure_classification`
- `result_refs`
- `sanitized_diagnostics`

### 15.7 WorkerIdentity

**Fields**
- `worker_id`
- `worker_type`: `LOCAL`, `REMOTE`, `MANAGED_SERVICE`
- `capability_refs`
- `credential_profile_ref`
- `workspace_scope`
- `health_status`
- `last_heartbeat_at`
- `lifecycle_status`

### 15.8 ResourceAccount and UsageRecord

**ResourceAccount fields**
- `resource_account_id`
- `provider_or_service_ref`
- `resource_type`
- `quota_limit`
- `quota_remaining`
- `reset_window`
- `approved_budget_ref`
- `policy_version`
- `account_status`

**UsageRecord fields**
- `usage_record_id`
- `resource_account_id`
- `task_ref`, `job_ref`, `workflow_run_ref`
- `quantity`, `unit`
- `usage_source`: provider-reported or estimated
- `estimated_cost`, optional
- `confirmed_cost_ref`, optional
- `observed_at`

**Rules**
- Technical quota and approved financial budget are separate.
- Resource allocation may optimize within an approved envelope only.
- No new spending, subscription, contract or budget increase is permitted.
- Uncertain external side effects must be reconciled before retry.

---

## 16. Entity registry — Multiformat Creation (Contract 11)

### 16.1 CreationProject

**Fields**
- `creation_project_id`
- `content_item_id`
- `workspace_id`, `brand_id`
- `objective_refs`
- `audience_refs`
- `studio_production_refs`
- `lifecycle_status`
- `owner_ref`

### 16.2 FormatProfile

**Fields**
- `format_profile_id`
- `studio_id`
- `format_type`
- `technical_specification_version`
- `narrative_requirements`
- `packaging_requirements`
- `accessibility_requirements`
- `quality_rubric_ref`
- `format_profile_version_id`

### 16.3 CreativeDirectionBrief

**Fields**
- `creative_direction_brief_id`
- `content_item_id`
- `studio_identity_version_id`
- `format_profile_version_id`
- `research_refs`
- `claim_refs`
- `audience_refs`
- `creative_intent`
- `narrative_direction`
- `visual_direction`
- `approval_ref`
- `brief_version_id`

### 16.4 CreativeConcept

**Fields**
- `creative_concept_id`
- `creative_direction_brief_id`
- `concept_type`
- `concept_summary`
- `story_structure`
- `distinctive_angle`
- `evidence_refs`
- `concept_version_id`

### 16.5 StudioProduction

**Fields**
- `studio_production_id`
- `creation_project_id`
- `content_item_id`
- `studio_id`
- `studio_identity_version_id`
- `format_profile_version_id`
- `creative_direction_brief_version_id`
- `workflow_run_id`
- `artifact_refs`
- `quality_assessment_refs`
- `rights_assessment_refs`
- `lifecycle_status`

### 16.6 DerivativeRelationship

**Fields**
- `derivative_relationship_id`
- `source_content_or_artifact_ref`
- `derived_content_or_artifact_ref`
- `transformation_type`
- `shared_evidence_refs`
- `independent_qa_required`
- `created_at`

**Rules**
- Contract 03 owns StudioIdentity.
- Contract 11 references exact immutable identity and format profile versions.
- Each derivative receives its own production, QA, rights and approval records.
- Shared research does not imply shared approval.
- Shorts Studio remains a specialized engine integrated through an adapter; it is not replaced by this data model.

---

## 17. Entity registry — Artifact and Asset Management (Part 7 and Contract 07)

### 17.1 Artifact

**Fields**
- `artifact_id`
- `workspace_id`
- `artifact_type`
- `owner_entity_type`, `owner_entity_id`
- `current_artifact_version_id`
- `classification`
- `lifecycle_status`
- `created_by`, `created_at`

### 17.2 ArtifactVersion

**Fields**
- `artifact_version_id`
- `artifact_id`
- `version_number`
- `storage_ref`
- `content_hash`
- `media_type`
- `size_bytes`
- `metadata`
- `created_by`, `created_at`
- `parent_artifact_version_refs`

**Rules**
- Artifact versions are immutable.
- A material edit creates a new version.
- A storage path is not the artifact identity.
- Approvals and QA bind to exact artifact versions and hashes.

### 17.3 Asset

**Fields**
- `asset_id`
- `workspace_id`
- `asset_type`
- `source_artifact_version_id`
- `creator_or_rightsholder_ref`
- `provenance_refs`
- `rights_record_refs`
- `classification`
- `lifecycle_status`

**Rules**
- Asset represents a reusable source/creative resource.
- Artifact represents a stored deliverable or work product.
- Rights are evaluated for the exact intended use.
- Access to an asset does not imply ownership or unrestricted reuse.

---

## 18. Entity registry — Distribution and Publishing (Contract 12)

### 18.1 ChannelProfile

**Fields**
- `channel_profile_id`
- `platform_id`
- `channel_type`
- `technical_constraints`
- `metadata_requirements`
- `policy_reference`
- `profile_version_id`

### 18.2 ChannelAccount

**Fields**
- `channel_account_id`
- `workspace_id`, `brand_id`
- `platform_id`
- `external_account_id`
- `account_display_name`
- `credential_reference`
- `permission_scope`
- `connection_status`
- `lifecycle_status`

**Rules**
- Credentials are held by a secure credential service, not copied into ordinary records or logs.
- Account connection is not authorized by this document.

### 18.3 DistributionStrategy

**Fields**
- `distribution_strategy_id`
- `content_item_id` or `studio_production_id`
- `channel_suitability_assessment_refs`
- `target_channel_refs`
- `adaptation_requirements`
- `strategy_version_id`

### 18.4 DistributionPackage and Version

**Fields**
- `distribution_package_id`
- `studio_production_id`
- `channel_account_id`
- `artifact_version_refs`
- `metadata_version_id`
- `rights_assessment_refs`
- `quality_assessment_refs`
- `governance_decision_ref`
- `distribution_package_version_id`

### 18.5 ScheduleProposal

**Fields**
- `schedule_proposal_id`
- `distribution_package_version_id`
- `channel_account_id`
- `proposed_time`
- `timezone`
- `schedule_status`
- `authorization_ref`
- `expires_at`

### 18.6 PublishOperation

**Fields**
- `publish_operation_id`
- `distribution_package_version_id`
- `publishing_authorization_id`
- `channel_account_id`
- `requested_action`
- `idempotency_key`
- `external_operation_id`
- `execution_status`
- `requested_at`, `completed_at`
- `reconciliation_status`

### 18.7 Publication

**Fields**
- `publication_id`
- `publish_operation_id`
- `platform_id`
- `external_publication_id`
- `visibility_state`
- `published_at`
- `last_verified_at`
- `reconciliation_status`
- `platform_observation_refs`

**Rules**
- Recommendation, schedule and publishing authorization are separate.
- Upload confirmation does not prove public visibility.
- Unknown external outcomes require reconciliation, not blind retry.
- Autonomous public publishing remains disabled pending separate owner-approved policy.

---

## 19. Shared status and vocabulary registries

These are cross-domain vocabularies. Domain contracts may define additional states, but must not redefine the meanings below.

### 19.1 Data classification

- `PUBLIC`
- `INTERNAL`
- `CONFIDENTIAL`
- `RESTRICTED`

### 19.2 Canonical epistemic status

Owned by Contract 04:
- `OBSERVED`
- `SOURCE_REPORTED`
- `VERIFIED`
- `ESTIMATED`
- `INTERPRETATION`
- `HYPOTHESIS`
- `EXPERIMENTAL_LEARNING`
- `VALIDATED_LEARNING`
- `DISPUTED`
- `SUPERSEDED`
- `RETRACTED`

### 19.3 Canonical quality outcome

Owned by Contract 07:
- `PASS`
- `PASS_WITH_WARNINGS`
- `NEEDS_REVIEW`
- `BLOCKED`

### 19.4 Canonical rights status

Owned by Contract 07:
- `CLEARED`
- `RESTRICTED`
- `PENDING_VERIFICATION`
- `PROHIBITED`
- `UNKNOWN`

### 19.5 Provenance type

Shared base vocabulary; domain-specific additions require mapping:
- `DIRECTLY_OBSERVED`
- `PLATFORM_REPORTED`
- `SOURCE_REPORTED`
- `INDEPENDENTLY_VERIFIED`
- `OWNER_ENTERED`
- `CALCULATED`
- `ESTIMATED`
- `ATTRIBUTED`
- `FORECAST`

Do not confuse provenance type with epistemic status or lifecycle status.

### 19.6 Governance disposition

Owned by Contract 07:
- `ELIGIBLE`
- `PENDING_APPROVAL`
- `BLOCKED`
- `EXPIRED`

### 19.7 Approval decision

Owned by Contract 07:
- `APPROVED`
- `REJECTED`
- `EXPIRED`
- `REVOKED`

These vocabularies do not create an authorization by themselves. A decision must always be tied to the subject version, action, scope, actor and policy version.

---

## 20. Cross-domain reference rules

1. Use typed references: entity type + canonical ID + version ID where version-sensitive.
2. Do not copy another domain's mutable canonical fields into a second authoritative record.
3. A denormalized read model must identify its source owner and refresh/invalidation mechanism.
4. A reference to an entity does not grant permission to read or modify it.
5. Cross-workspace references are denied by default.
6. Cross-brand and cross-studio reuse must follow explicit scope and sharing policy.
7. Evidence references must retain their source, capture time, scope and permission context.
8. Review/approval references must point to exact immutable versions.
9. External platform identifiers must include platform namespace and account scope.
10. Deleted or retracted records retain only the minimum tombstone/audit data required by retention and legal policy; ordinary retrieval must not present them as current facts.

---

## 21. Canonical ownership and change-control rules

### 21.1 Owner responsibilities

The owning domain must:
- Maintain its entity definition.
- Publish schema and lifecycle changes.
- Provide migration/compatibility notes.
- Define required references and validation.
- Preserve historical versions.
- Publish material domain events.
- Provide a deprecation path.

### 21.2 Extension rules

A consuming domain may add a typed extension only when:
- The owning domain approves the extension point.
- The extension has its own owner and version.
- It does not redefine canonical fields or lifecycle.
- It preserves canonical references.
- It passes privacy, rights and security policy.

### 21.3 Breaking changes

Breaking schema or meaning changes require:
- Impact analysis across dependent contracts.
- Versioned migration plan.
- Compatibility window where feasible.
- Data integrity checks.
- Rollback/recovery plan.
- Owner approval for foundational or security-sensitive changes.

AI agents may propose schema changes and migration plans. They cannot independently ratify foundational architecture, security policy or owner authority changes.

---

## 22. Acceptance criteria

This artifact is ready for architecture review when all the following can be demonstrated in a future design validation:

- [ ] Every canonical entity has exactly one owner.
- [ ] Every entity has a canonical UUIDv7 identity.
- [ ] Versioned entities distinguish stable identity from immutable version identity.
- [ ] Contract 08 references Contract 01 audience entities.
- [ ] Contract 11 references Contract 03 StudioIdentity versions.
- [ ] Contracts 05, 11 and 12 reference canonical evidence/claim records from Contract 02.
- [ ] Contracts 11 and 12 reference Contract 07 quality, rights and governance decisions.
- [ ] Contract 12 references Contract 08 metrics and Contract 09 financial records without duplicating their ownership.
- [ ] Task, Job, WorkflowRun, StudioProduction and Artifact have distinct responsibilities.
- [ ] Lifecycle, epistemic, provenance, quality and authorization states are separate.
- [ ] Every reviewable artifact and approval is bound to an immutable version.
- [ ] Workspace and brand isolation rules are explicit.
- [ ] Provider and worker data eligibility is evaluated before transfer.
- [ ] No module can grant itself permissions or bypass central governance.
- [ ] Public publishing remains disabled unless a separate owner-approved policy changes that status.
- [ ] All unresolved implementation choices remain visibly open rather than silently assumed.

**Acceptance status:** Not executed. This document defines criteria for future design validation; it does not claim they have been technically tested.

---

## 23. Open implementation details

The following remain intentionally undecided:

- Physical database schema, indexes and partitioning.
- UUID storage representation and public serialization.
- Exact entity versioning implementation.
- Relational modeling of polymorphic references.
- Event store and outbox/inbox implementation.
- API framework and generated schema tooling.
- Search/index strategy.
- Object storage provider and artifact transfer.
- Retention periods and legal-hold implementation.
- Data deletion propagation and tombstone rules.
- Exact metric registry and financial reconciliation sources.
- Exact provider/model registry data and approved provider list.
- Exact queue, scheduler and workflow engine.
- Exact schema migration tooling.
- Exact implementation split between modular application and services.

These choices require later technical evaluation. This document does not select vendors or authorize services.

---

## 24. Decision summary

### Adopt as the recommended canonical standard

1. UUIDv7 for all internal canonical identities.
2. Prefixes only as optional display aliases.
3. Stable entity identity separated from immutable version identity.
4. One canonical owner per entity.
5. Contract 01 owns Audience, Persona, AudienceSegment and AudienceInsight.
6. Contract 02 owns Opportunity, EvidenceSource, EvidenceItem, Claim and ClaimEvidenceLink.
7. Contract 03 owns WorkspaceBrand and StudioIdentity versions.
8. Contract 04 owns Knowledge and shared epistemic status.
9. Contract 05 owns research execution and synthesis, not canonical evidence identity.
10. Contract 07 owns QA, rights, governance, approval and publishing authorization.
11. Contract 08 owns metrics, performance, experiments and attribution, not audience identity.
12. Contract 09 owns financial records and commercial pipeline.
13. Contract 10 + Parts 4/5/8 own agent, resource, worker and durable execution contracts.
14. Contract 11 owns creation projects and studio production, referencing canonical brand identity.
15. Contract 12 owns distribution and external operation records, subject to Contract 07 authorization.
16. Part 7 owns artifact integration and immutable artifact registration.
17. Central security/data governance owns classification, access, retention and provider eligibility.

### Not approved by this document

- Any source-code or repository change.
- Any schema migration or database deployment.
- Any external integration or account connection.
- Any cloud/provider provisioning or subscription.
- Any budget or spending change.
- Any production run or public publishing authorization.

---

**End of NEXTDECODE Canonical Data Dictionary & Entity Ownership Registry 1.0**
