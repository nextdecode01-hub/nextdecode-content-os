# NEXTDECODE Shared Intelligence Core — Contracts 01–06 and 08–09 Cross-Domain Reconciliation
**Document ID:** NEXTDECODE-SIC-RECON-01-06-08-09-0.1  
**Version:** 0.1 | **Date:** 2026-11-04  
**Status:** Working source reconciliation — documentation only  
**Contract freeze:** NOT GRANTED | **Implementation authorization:** NOT GRANTED

## 1. Purpose and scope
This document reconciles Shared Intelligence Core Contracts 01–06 and 08–09 against one another and the previously reviewed Contracts 07, 10, 11 and 12, Data Dictionary, accepted ADR/CF decisions, API/Event Standard, Lifecycle Standard, Batch 16 and WP1–WP6 boundaries.

It is a cross-domain ownership and dependency map, not a replacement for any source contract, a schema migration, an enum freeze, or an implementation instruction. Where the sources do not establish one authoritative owner or exact field/cardinality semantics, the issue is explicitly left open.

## 2. Source set reviewed
- Contract 01 — Audience & Identity Context Model 1.0.
- Contract 02 — Opportunity & Evidence Model 1.0.
- Contract 03 — Brand & Editorial Intelligence Model 1.0.
- Contract 04 — Shared Knowledge & Learning Model 1.0.
- Contract 05 — Research Intelligence & Evidence Operations 1.0.
- Contract 06 — Strategy & Portfolio Intelligence Model 1.0.
- Contract 08 — Audience & Performance Intelligence Model 1.0.
- Contract 09 — Business & Monetization Intelligence Model 1.0.
- Previously reviewed Contracts 07, 10, 11 and 12 and their reconciliation documents.
- Data Dictionary v1.0 and v1.1, Module-to-Contract Traceability Matrix, API/Event and Lifecycle standards, Batch 16 reading copy, accepted ADR-001..010 and CF-01..24.

## 3. Canonical domain ownership map

| Domain concept / record | Proposed canonical owner | Other contract consumers | Reconciliation status |
|---|---|---|---|
| Audience, StrategicPersona, AudienceSegment | Contract 01 / Audience Intelligence | Contracts 02, 03, 06, 08, 11 | Logical owner clear; exact entity overlap with C08 needs confirmation |
| PlatformAudienceSnapshot and PlatformIdentityReference | Contract 01 | Contract 08 consumes performance metrics; Contract 12/11 may reference channel context | Contract 01 says time-bounded, platform-scoped and no default identity resolution |
| AudienceInsight | Contract 01 for audience need/context; Contract 08 for performance-derived measurement insight | Contracts 02, 04, 06, 08 | Boundary between audience insight and performance insight requires explicit type/owner split |
| EvidenceSource, EvidenceItem, Claim, ClaimEvidenceLink, ClaimVerification | Shared evidence/claim foundation; canonical service owner is NOT conclusively settled by reviewed source set | Contracts 02, 04, 05, 08, 09, 11 | OPEN: C02 defines reusable evidence primitives; C05 says it reuses them; existing Claim/Evidence/ClaimVerification contracts must be located and precedence confirmed |
| Opportunity and OpportunityAssessment | Contract 02 | Contracts 05, 06, 08, 09, 11 | Generic opportunity and immutable assessment owner clear |
| BusinessOpportunity, CommercialProspect, CommercialProposal, CommercialPipelineRecord | Contract 09 | Contract 02 broad monetization/product opportunity; Contract 06 portfolio; Contract 07 governance | Logical domain specialization clear; relationship to generic Opportunity needs canonical typed-link rule |
| BrandIdentityVersion, EditorialPrinciple, BrandPillar, VoiceProfile, VisualIdentityProfile | Contract 03 | Contracts 06, 11 and specialized studios | Parent/studio identity boundary clear; identity approval is owner-governed |
| FormatProfile | Contract 03 for editorial/creative format identity and quality requirements | Contracts 11 and 12 | Operational technical format capability vs editorial format profile must be separated |
| ChannelProfile | Contract 12 for operational platform/channel constraints; Contract 03 may retain editorial adaptation requirements | Contracts 03, 08, 11 | OPEN: C03 describes channel profile; C12 owns distribution/channel capability. Split editorial guidance from operational capability |
| KnowledgeItem, KnowledgeVersion, KnowledgeRelationship, LearningRecord, KnowledgeContextPackage | Contract 04 | Contracts 05, 08, 11, 06 | Logical owner clear; C08/C05 must reference shared learning records rather than define competing ones |
| ResearchRequest, ResearchPlan, ResearchRun, ResearchBrief, ResearchConflict, ResearchMonitor, ResearchQualityAssessment | Contract 05 | Contracts 02, 04, 06, 08, 11 | Research domain owns research records; workflow/job execution remains WP2 |
| StrategicObjective, PortfolioStrategyVersion, PortfolioItem, EditorialProgram, StrategicInitiative, PortfolioAssessment, PlanningWindow | Contract 06 | Contracts 02, 03, 05, 08, 09, 11 | Logical owner clear; selected plan item is not execution authorization |
| MetricDefinition, PerformanceSnapshot, ContentPerformanceProfile, Experiment, ExperimentResult, AttributionRecord | Contract 08 | Contracts 01, 04, 06, 09, 11, 12 | Performance/experiment owner clear; financial source records remain C09 |
| FinancialRecord, BusinessPerformanceSnapshot, MonetizationModel | Contract 09 | Contracts 02, 06, 08, 12 | Business/financial domain owner clear; financial access restricted and audited |
| QualityAssessment, RightsDecision, ApprovalDecision, PublishingAuthorization | Contract 07 / WP5 | All domains consume applicable decisions | Accepted boundary; no consumer domain self-authorizes |
| CreationProject, StudioProduction | Contract 11 | Contracts 03, 04, 05, 06, 07, 08, 10, 12 | Existing cross-source reconciliation remains controlling working map |
| WorkflowDefinition, WorkflowRun, Task/Job/JobAttempt | WP2 / Contract 10 orchestration boundary | All domains | WP2 owns execution progression, not each business domain lifecycle |
| WorkerIdentity, WorkerSession, Lease, Fencing | WP3 | Contract 10 and WP2 | WP3 trust boundary |
| Artifact, ArtifactVersion, Manifest | Part 7 / WP4 | All domains | Immutable artifact identity/version boundary |
| DistributionPackage, ScheduleProposal, PublishOperation, Publication | Contract 12 | Contracts 03, 07, 08, 09, 10, 11 | Distribution state owner; authorization remains Contract 07 |

The table is a proposed canonical ownership map derived from the source set. Any row marked OPEN requires owner ratification before schema freeze.

## 4. Contract-by-contract reconciliation

### Contract 01 — Audience & Identity Context
**Owns:** audience concepts, strategic personas, strategic/observed/emerging segments, platform-scoped audience snapshots and identity references, audience insights and scoped audience context reuse.

**Confirmed invariants:** audience-first rather than identity-first; no assumed cross-platform identity match; provenance, observation window, method, confidence and limitations; privacy/purpose limitation; workspace/brand isolation; no sensitive profiling by default; cross-studio reuse is scoped and versioned.

**Dependencies:** Contract 03 (brand/studio identity); Contract 02 (opportunity relevance); Contract 05 (research evidence); Contract 08 (performance measurement); Contract 04 (knowledge/learning); Contract 06 (portfolio); Contract 11 (production brief context).

**Open items:**
- C01-01: C01 and C08 both describe AudienceInsight/AudienceSegment concepts. Define one audience-domain canonical entity and distinguish performance-derived observations/metrics from audience-domain insight lifecycle.
- C01-02: Exact source of truth for EvidenceSource/Permission/Provenance references is not settled by C01; do not create a second evidence/consent model.
- C01-03: Retention/deletion propagation to derived segments, embeddings, snapshots and knowledge is a cross-domain data-governance requirement; exact propagation owner/mechanism remains open.
- C01-04: PlatformIdentityReference is a platform-scoped account/channel reference, not a universal person identity. Preserve this boundary when C08 analytics and C12 distribution refer to channel accounts.
- C01-05: Exact confidence calibration, segment sample thresholds and platform API scopes are intentionally not defined.

### Contract 02 — Opportunity & Evidence
**Owns:** generic Opportunity, OpportunityAssessment, opportunity taxonomy, eligibility-gate evaluation, weighted assessment, confidence/evidence sufficiency and opportunity-evidence relationships.

**Confirmed invariants:** eligibility before weighted scoring; hard gates cannot be offset by a high score; missing evidence remains missing; facts, estimates, opinions, assumptions and hypotheses stay distinct; assessments are immutable; opportunity selection is not execution authorization.

**Dependencies:** Contract 01 audience; Contract 03 brand; Contract 05 research and claim/evidence; Contract 04 validated knowledge; Contract 06 portfolio; Contract 07 rights/governance; Contract 09 commercial specialization; Contract 11 production.

**Open items:**
- C02-01: C02 defines EvidenceSource/EvidenceItem/Claim/ClaimEvidenceLink and references existing ClaimVerification contracts. C05 also says it reuses those primitives. The canonical owner and exact source contract must be confirmed; no duplicate evidence or claim-verification subsystem.
- C02-02: Generic Opportunity includes MONETIZATION and PRODUCT types; Contract 09 defines BusinessOpportunity and MonetizationModel. Define whether BusinessOpportunity is a typed specialization/reference to generic Opportunity or a separate domain aggregate linked by a typed relationship. Do not duplicate assessment histories.
- C02-03: C02 and C06 both use eligibility-first prioritization. Define shared eligibility result references and domain-specific scoring policies; do not create a single universal score.
- C02-04: C02 uses lifecycle labels including ELIGIBLE/SELECTED/IN_PROGRESS while execution authority is external. Confirm transitions and owner references against Lifecycle Standard and WP2.
- C02-05: Numeric weights, thresholds, confidence labels and exact enum compatibility are explicitly not fixed.

### Contract 03 — Brand & Editorial Intelligence
**Owns:** parent brand identity and immutable versions, studio identity, editorial principles, brand pillars, voice profiles, visual identity profiles, editorial format guidance and brand-alignment assessments.

**Confirmed invariants:** one parent brand with distinct studio identities; studio rules cannot weaken parent non-negotiables; immutable identity versions; AI can propose but cannot approve identity changes; assets reference centralized rights records; brand alignment cannot override factual/rights/privacy/safety/production blockers.

**Dependencies:** Contract 01 audience; Contract 04 learning; Contract 06 strategy; Contract 07 governance/rights; Contract 08 performance learning; Contract 11 studio production; Contract 12 channel delivery.

**Open items:**
- C03-01: C03 describes ChannelProfile while C12 owns Distribution/ChannelProfile capability context. Split editorial/channel adaptation guidance from operational platform capability, policy and delivery constraints; define typed linkage.
- C03-02: C03 FormatProfile and Contract 11 format profile/Contract 12 distribution packaging may overlap. Define one editorial format profile owner and separate production execution profile and channel delivery requirements.
- C03-03: Contract 11 consumes StudioIdentity and exact identity versions. Confirm immutable version references and no mutable current-profile lookup in historical production packages.
- C03-04: BrandAlignmentAssessment is one quality dimension, not a replacement for Contract 07 governance or content QA. Confirm its reference/aggregation contract.
- C03-05: Exact approved NEXTDECODE identity wording, studio identities, voice scales, visual tokens and scoring thresholds remain owner-reserved.

### Contract 04 — Shared Knowledge & Learning
**Owns:** KnowledgeItem, KnowledgeVersion, KnowledgeRelationship, LearningRecord, knowledge retrieval/context packages, validation/promotion lifecycle and applicability scope.

**Confirmed invariants:** raw information, evidence, claims, interpretations, hypotheses, experiments and validated learning are distinct; immutable versions; validation differs by knowledge type; retrieval filters by access AND applicability; no universalization from one result; derived indexes/embeddings are governed data; AI cannot change owner-approved policy.

**Dependencies:** Contract 02 evidence/opportunities; Contract 05 research; Contract 08 performance/experiments; Contract 06 strategy; Contract 03 brand; Contract 01 audience; Contract 11 creation context.

**Open items:**
- C04-01: C08 defines LearningRecord and C05 proposes KnowledgeItems from research outputs. Both must reference C04 canonical LearningRecord/KnowledgeItem and not define competing lifecycle or schema.
- C04-02: KnowledgeItem epistemic status and ClaimVerification status are distinct. VERIFIED (claim/fact) must not be equated with VALIDATED_LEARNING.
- C04-03: Deletion/restriction propagation includes embeddings, summaries, caches and derived indexes. WP4/WP6 and data governance need explicit acceptance evidence and ownership.
- C04-04: Retrieval may use relational/full-text/vector/graph methods, but no provider/technology is selected. No new vector store or paid service is implied.
- C04-05: Promotion thresholds, freshness windows, retention and review roles remain open.

### Contract 05 — Research Intelligence & Evidence Operations
**Owns:** research requests/plans/runs/briefs, research conflicts, source assessment and bounded monitoring, research quality and downstream research context handoff.

**Confirmed invariants:** source class is not a reliability guarantee; independent corroboration requires independent origins; every material claim links to evidence; contradictions remain visible; completion is not blanket claim verification; monitoring is bounded, deduplicated, permission/resource-aware and pausable; provider eligibility is a hard filter.

**Dependencies:** Contract 02 opportunity/claim-evidence; Contract 04 knowledge; Contract 01 audience; Contract 03 brand; Contract 06 strategy; Contract 07 rights/policy; Contract 10/WP2 orchestration; WP3 worker trust; WP6 acceptance.

**Open items:**
- C05-01: ResearchRun is a business-domain research record; WorkflowRun/Job/JobAttempt are WP2 execution records. Define typed references and one-to-many cardinality without merging their lifecycle states.
- C05-02: C05 reuses EvidenceSource/EvidenceItem/Claim/ClaimEvidenceLink/ClaimVerification. Confirm their canonical source owner and exact contract; C02 currently also defines shared evidence primitives.
- C05-03: ResearchQualityAssessment outcomes reuse PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW, BLOCKED, consistent with accepted ADR-008. Confirm this is a domain-specific quality result and not interchangeable with script/render/content QA.
- C05-04: ResearchMonitor requires approved schedule, source policy, quota, expiry and pause. It must not silently imply a cloud monitoring deployment or independent background service is already authorized.
- C05-05: Source snapshots, retention, provider usage, claim criticality and high-impact review policies remain central-policy/technical decisions.

### Contract 06 — Strategy & Portfolio Intelligence
**Owns:** StrategicObjective, PortfolioStrategyVersion, PortfolioItem, EditorialProgram, StrategicInitiative, PortfolioAssessment, PlanningWindow and strategy review/recommendation.

**Confirmed invariants:** mission/brand/objective/portfolio/program/initiative/opportunity/production workflow are separate levels; eligibility before weighted prioritization; portfolio balance has no fixed quotas; dates can be proposed/tentative/committed; resource-aware plans do not authorize spend; owner approval required for reserved strategic changes.

**Dependencies:** Contract 01 audience; Contract 02 opportunities; Contract 03 brand; Contract 04 validated learning; Contract 05 research; Contract 07 governance; Contract 09 business; Contract 10 resource/agent orchestration; Contract 11 creation; Contract 12 distribution.

**Open items:**
- C06-01: PortfolioItem is a planning record and is not a ContentItem, CreationProject, StudioProduction, WorkflowRun or PublishOperation. Define typed links and transition handoff.
- C06-02: StrategicInitiative may carry an approved resource envelope, but cannot create/raise budget authority. Align with Contract 09 and Contract 10 resource authority.
- C06-03: PlanningWindow/calendar states must not be mistaken for Contract 12 schedule or publishing authorization. Clarify planning date vs distribution schedule.
- C06-04: PortfolioAssessment and OpportunityAssessment share some dimensions; define separate assessment purposes and policy versions, not duplicated or silently combined scores.
- C06-05: Exact planning horizons, review cadence, scoring weights and portfolio allocation are not fixed.

### Contract 08 — Audience & Performance Intelligence
**Owns:** MetricDefinition, PerformanceSnapshot, ContentPerformanceProfile, Experiment, ExperimentResult and AttributionRecord; performance-derived insight and measurement context.

**Confirmed invariants:** source-reported/directly observed/estimated/forecast values remain distinct; snapshots are append-only; metric comparability is explicit; attribution is not causation; experiment design includes guardrails and approved resource envelope; one studio's finding is not universalized; no metric creates authority.

**Dependencies:** Contract 01 audience; Contract 04 LearningRecord; Contract 06 strategy; Contract 09 financial outcomes; Contract 11 content/variant lineage; Contract 12 distribution; WP4 artifact identity; Contract 07 policy.

**Open items:**
- C08-01: C08 AudienceInsight/AudienceSegment overlaps C01. Keep canonical audience entities in C01; C08 owns measurement snapshots and performance-derived evidence, linking to audience references.
- C08-02: C08 LearningRecord must use Contract 04 canonical model; experiment result is not automatically validated learning.
- C08-03: AttributionRecord links to financial outcomes, but C09 owns FinancialRecord and BusinessPerformanceSnapshot. Define typed reference and avoid competing financial truth.
- C08-04: PerformanceSnapshot needs exact ContentItem/ContentVariant/ArtifactVersion/DistributionPackage lineage. Align Contract 11/Part 7/Contract 12 and never infer identity from mutable current content.
- C08-05: Experiment approval, approved budget envelope, and publishing authorization remain separate governance decisions; no experimentation policy can bypass Contract 07.
- C08-06: Metric definitions and platform comparability rules are versioned; no universal cross-platform score or metric equivalence.

### Contract 09 — Business & Monetization Intelligence
**Owns:** MonetizationModel, CommercialProspect, CommercialProposal, CommercialPipelineRecord, FinancialRecord, BusinessPerformanceSnapshot and business-specific opportunity assessment.

**Confirmed invariants:** audience value and editorial independence; eligibility gates before commercial scoring; prospects are not vetted partners without due diligence; proposals remain drafts until owner-authorized; financial values distinguish confirmed/platform-reported/attributed/estimated/forecast; AI cannot accept agreements, negotiate binding terms, spend or alter financial limits; customer-contributed data/intelligence cannot be sold/licensed/monetized.

**Dependencies:** Contract 02 generic opportunity; Contract 06 strategy; Contract 08 performance/attribution; Contract 03 brand/editorial integrity; Contract 07 governance; Contract 10 resource controls; Contract 12 distribution; WP1 canonical finance/persistence.

**Open items:**
- C09-01: Resolve generic Opportunity MONETIZATION/PRODUCT vs BusinessOpportunity specialization and shared assessment lineage.
- C09-02: C08 AttributionRecord must reference C09 FinancialRecord and business snapshot; define one source of financial truth and explicit observed/attributed/estimated classifications.
- C09-03: CommercialPipelineRecord OWNER_AUTHORIZED_CONTACT and ACCEPTED_BY_OWNER are consequential transitions. Define authorization record, actor identity, exact scope, expiry and external communication audit; no implicit authority from proposal status.
- C09-04: Customer data non-monetization is a strong explicit constraint. Cross-workspace learning requires explicit purpose-specific revocable authorization and privacy safeguards; ensure no conflict with general knowledge-sharing proposals.
- C09-05: Accounting grain, cost allocation, currency conversion, source reconciliation and retention are not specified and must not be invented.
- C09-06: BusinessPerformanceSnapshot is derived and immutable/versioned; underlying financial facts remain separately sourced and access-restricted.

## 5. Cross-domain conflict register

| ID | Conflict / ambiguity | Risk if unresolved | Required owner action |
|---|---|---|---|
| SIC-01 | EvidenceSource/EvidenceItem/Claim/ClaimVerification canonical owner unclear between C02 and C05 / existing shared contracts | Duplicate claim/evidence truth, inconsistent verification and provenance | Locate authoritative existing Claim/Evidence contract; declare one owner and mapping |
| SIC-02 | AudienceInsight/AudienceSegment overlap between C01 and C08 | Duplicate segment and insight records; inconsistent lifecycle | C01 owns audience identity/segments; C08 owns performance measurement; approve precise split |
| SIC-03 | KnowledgeItem/LearningRecord duplicated in C04, C05 and C08 | Multiple learning status/version systems | C04 owns canonical knowledge/learning; C05/C08 provide source records and references |
| SIC-04 | Generic Opportunity vs BusinessOpportunity and monetization/product taxonomy overlap | Duplicate opportunity, scoring and history | Define typed specialization/link and assessment lineage across C02/C09 |
| SIC-05 | ChannelProfile and FormatProfile overlap C03/C12/C11 | Editorial guidance confused with platform capability and production format | Separate brand/editorial format, production execution profile and distribution/channel capability |
| SIC-06 | PortfolioItem/Initiative vs CreationProject/StudioProduction/WorkflowRun | Planning state may be treated as execution or production truth | Define typed handoff and owner transitions C06 → C11 → WP2 |
| SIC-07 | Performance attribution vs financial source of truth | Reported/attributed revenue mistaken for confirmed financial record | C09 owns FinancialRecord; C08 attribution links and labels it |
| SIC-08 | ResearchRun vs WorkflowRun/Job/JobAttempt | Duplicate run state and retries | C05 owns research-domain run; WP2 owns execution state/attempts |
| SIC-09 | Validation/quality statuses across knowledge, research, opportunity and content | PASS/VERIFIED/VALIDATED conflated | Keep status vocabularies domain-specific; map only with explicit semantics |
| SIC-10 | Deletion/retention propagation across source, audience, knowledge, evidence, embeddings and analytics | Derived data survives source deletion/restriction | Data governance/WP4/WP6 define traceable propagation and acceptance |
| SIC-11 | Resource envelopes across opportunity, research, strategy, experiments, business | Domain recommendation may be misread as budget authorization | Contract 10 resource governance + centralized owner authorization remain authoritative |
| SIC-12 | API/event examples are illustrative but may be mistaken for frozen contracts | Premature endpoint/schema implementation | Treat as candidates until common envelope and domain contracts are owner-ratified |

## 6. Shared invariants carried forward
- Accepted ADR/CF decisions outrank candidate contract text and reconciliation proposals.
- PostgreSQL-compatible relational DB remains authoritative shared-state store (ADR-002); no SQLite-first replacement of the accepted decision.
- DB-backed durable queue with transactional outbox/inbox initially; at-least-once delivery and idempotent consumers, no global exactly-once claim.
- UUIDv7 canonical IDs and immutable identity; exact entity/version references remain distinct.
- Asset ≠ Artifact ≠ ArtifactVersion; immutable artifact versions and exact manifests.
- ContentItem vs ContentVariant remains distinct.
- Approval ≠ authorization ≠ execution ≠ publication.
- Missing/ambiguous rights, approval, authorization, permissions or provenance never grant permission.
- Each domain owns its own lifecycle; workflow/job state does not replace business-domain state.
- Human approval before publishing; automatic public publishing remains disabled absent separate explicit owner authorization.
- No autonomous spending, paid service activation, provider expansion, budget increase or binding commercial commitments.
- Workspace isolation, purpose limitation, classification, retention and deletion apply to source and derived data.
- Proposed contract fields, enum lists, scoring weights, endpoints and events are not frozen unless an accepted owner decision explicitly says so.

## 7. Workstream dependency implications

| Workstream | Contract dependencies to carry into detailed traceability | Boundary to preserve |
|---|---|---|
| WP1 Domain Persistence | C01–C09 canonical IDs, typed links, ownership, immutable versions, tenant/workspace scope | Persistence model does not decide domain policy or duplicate domain state |
| WP2 Workflow Execution | C05 ResearchRun, C06 initiative/portfolio handoffs, C11 production tasks, C12 PublishOperation; C10 orchestration | Durable execution and attempts separate from business lifecycle |
| WP3 Worker Trust | C05/C08 research/analytics provider use, C10 worker identity, C12 adapters | Worker identity, credentials, leases/fencing and eligibility stay WP3 |
| WP4 Artifact Storage | C03 brand assets, C04 derived knowledge/indexes, C05 evidence artifacts, C08 snapshots, C11 outputs, C12 packages | Immutable artifact/version and retention/deletion provenance |
| WP5 Governance Quality Rights | C01 privacy/purpose, C02 eligibility, C03 editorial principles, C04 knowledge promotion, C05 source permissions, C08 experiments, C09 commercial authority, C12 publishing | Centralized policy/rights/approval/authorization; no domain self-approval |
| WP6 Integration Recovery Acceptance | All above; API-LC-01..10, C12-01..07, X01-01..12 | End-to-end proof for denial, stale versions, duplicate events, unknown side effects, deletion and audit |

## 8. Required next decisions before contract freeze
1. Locate and designate the authoritative shared Evidence/Claim/ClaimVerification contract; reconcile C02 and C05 against it.
2. Ratify the C01/C08 audience vs performance ownership split.
3. Ratify C04 as canonical KnowledgeItem/LearningRecord owner and update C05/C08 references accordingly.
4. Decide generic Opportunity vs BusinessOpportunity specialization/link semantics.
5. Separate C03 editorial FormatProfile/ChannelProfile from C11 production profile and C12 operational channel capability.
6. Define C06 portfolio-to-C11 creation-to-WP2 execution handoff and C08/C09 attribution-to-finance linkage.
7. Complete WP1–WP6 field/relationship/acceptance traceability and produce conformance examples.
8. Only then assemble owner review pack with exact clauses, alternatives, consequences, owners and evidence.

## 9. Disposition
**Contracts 01–06 and 08–09: FIRST-PASS SOURCE RECONCILIATION COMPLETE; CROSS-DOMAIN OWNER DECISIONS OPEN.** The source-level concepts and major dependencies are mapped. SIC-01 through SIC-12 are not owner decisions and are not resolved by this document. No contract freeze, schema freeze, code change, repository action, test execution, agent dispatch, provider connection, spending, deployment or publishing authorization is granted.
