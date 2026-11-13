# NEXTDECODE Shared Intelligence Core Contract 05
## Research Intelligence & Evidence Operations
**Version:** 1.0  
**Status:** Working architecture contract — documentation only  
**Scope:** Shared Intelligence Core; research discovery, investigation, evidence validation, synthesis, monitoring, and downstream handoff  
**Authority:** Derived from accepted Creator Success Intelligence decisions and architecture baselines. This document does not authorize repository changes, external integrations, new data collection, provider subscriptions, spending, production execution, or publishing.

---

## 1. Purpose

Define the end-to-end research operating model that converts questions, audience needs, and opportunity candidates into traceable research outputs suitable for strategic decisions and content creation.

Research Intelligence must provide a consistent, reusable process for:

- Discovering relevant information from permitted sources.
- Evaluating source reliability, freshness, and relevance.
- Extracting and verifying factual claims.
- Detecting contradictions, uncertainty, and missing evidence.
- Producing structured research briefs and evidence-backed synthesis.
- Monitoring selected topics and developments on scheduled or event-driven triggers.
- Handing validated findings to Opportunity Assessment, Knowledge Management, Strategy, and specialized studios.

Research must not treat search-result volume, source popularity, model confidence, or repeated claims as proof. Its outputs are decision-support artifacts with explicit evidence, scope, limitations, and status.

## 2. Core principles

1. **Question-led research:** every substantive research run begins with a question, decision need, or approved monitoring objective.
2. **Permitted sources only:** source access and processing must comply with authorization, purpose limitation, privacy, retention, and provider restrictions.
3. **Source quality over source count:** independent, relevant, primary evidence is preferred to repeated copies of the same assertion.
4. **Claim-level traceability:** material factual statements link to evidence and verification outcomes.
5. **Contradictions remain visible:** conflicting evidence is recorded and assessed, not silently discarded.
6. **Freshness is contextual:** a source may be reliable but stale for a fast-changing topic.
7. **Uncertainty is explicit:** distinguish verified facts, source-reported information, estimates, interpretation, opinion, and hypothesis.
8. **Research and editorial judgment are distinct:** research supports editorial decisions; it does not independently authorize sensitive editorial positions.
9. **Research and production are distinct:** a completed research brief does not authorize production, spending, or publishing.
10. **Reusable with context:** findings may be reused only with their source, scope, rights, freshness, and applicability preserved.
11. **Resource-aware execution:** monitoring and research use approved budgets, quotas, schedules, and fallback policies.
12. **Owner-controlled boundaries:** research agents cannot grant themselves permissions, change policies, or bypass governance.

## 3. Research request contract

A `ResearchRequest` defines the question and permitted scope of an investigation.

Required fields:

- `research_request_id`: UUIDv7.
- `workspace_id` and optional `brand_id` / `studio_id`.
- `request_type`: opportunity research, fact verification, background research, audience research, market research, monitoring follow-up, or other versioned type.
- `primary_question`: explicit question to answer.
- `decision_context`: what decision or downstream task the research may inform.
- `scope`: topic, geography, audience, platform, format, time window, language, and other relevant boundaries.
- `required_depth`: lightweight, standard, or deep, with policy-defined meaning.
- `freshness_requirement`: how current evidence must be.
- `source_policy_ref`: permitted source classes and access constraints.
- `data_classification_ceiling`: maximum data classification allowed in this task.
- `resource_policy_ref`: approved quota/budget and provider eligibility.
- `output_contract`: required sections, evidence standard, and downstream consumers.
- `priority` and optional deadline.
- `created_by`, timestamps, and schema version.

Optional fields may include opportunity references, hypotheses, claims to verify, prior research runs, and explicit exclusions.

A request missing a decision context may still be exploratory, but its output must be labelled exploratory and must not be treated as an approved strategic decision.

## 4. Research lifecycle

Proposed lifecycle:

`REQUESTED` → `TRIAGED` → `PLANNED` → `RUNNING` → `SYNTHESIZING` → `QUALITY_REVIEW` → `COMPLETED`

Alternative outcomes:

- `NEEDS_CLARIFICATION`
- `BLOCKED`
- `FAILED`
- `CANCELLED`
- `PARTIALLY_COMPLETED`
- `EXPIRED`

Lifecycle rules:

- `TRIAGED`: scope, duplication, priority, permissions, and resource eligibility checked.
- `PLANNED`: research plan, source strategy, claim targets, and stopping criteria recorded.
- `RUNNING`: permitted discovery and evidence capture underway.
- `SYNTHESIZING`: findings, claim relationships, and contradictions organized.
- `QUALITY_REVIEW`: completeness, traceability, freshness, and policy checks evaluated.
- `COMPLETED`: output meets its declared completion criteria; this does not mean every claim is verified.
- `PARTIALLY_COMPLETED`: useful findings exist, but material questions remain unresolved.
- `BLOCKED`: policy, permissions, rights, security, or resource constraints prevent continuation.
- `FAILED`: execution failed without a valid completed output.
- `EXPIRED`: research is no longer current enough for its intended use.

Every transition records actor, timestamp, reason, policy version, and run reference. State transitions are enforced by the workflow service, not by free-form agent assertions.

## 5. Research planning

Before execution, create a versioned `ResearchPlan` containing:

- Research question and subquestions.
- Hypotheses to test, if any.
- Required claim inventory or expected factual areas.
- Preferred primary and secondary source classes.
- Search/discovery strategy and source diversity goals.
- Geographic, temporal, audience, and platform scope.
- Freshness and evidence sufficiency criteria.
- Known risks, sensitive topics, and exclusions.
- Permitted tools/providers and task-scoped permissions.
- Estimated resource use and preflight reservation.
- Stopping conditions and escalation conditions.
- Required output sections and review path.

The plan should identify whether the work is exploratory, verification-focused, comparative, monitoring-driven, or decision-support research.

The research planner may recommend additional investigation. It must not exceed approved resource limits or use an unapproved provider to complete the task.

## 6. Source discovery and evaluation

### 6.1 Source classes

The source registry should distinguish:

- First-party sources.
- Primary documents and official records.
- Public secondary reporting.
- Authorized external datasets and services.
- Expert statements and interviews, where permitted.
- Internal workspace records.
- User-provided materials.
- Platform-reported analytics and metrics.

The source class describes origin, not guaranteed reliability.

### 6.2 Source assessment

Each material source should be evaluated for:

- Identity and publisher provenance.
- Primary versus secondary status.
- Relevant expertise and authority for the specific claim.
- Publication and retrieval timestamps.
- Methodology and transparency.
- Independence from other cited sources.
- Potential conflicts of interest.
- Geographic and temporal relevance.
- Corrections, retractions, and known limitations.
- Permission, licence, and permitted use.
- Data classification and retention requirements.

A source credibility assessment must include rationale and assessor/model version. Avoid a single universal source score that hides context.

### 6.3 Independence and duplication

Multiple pages repeating one original report do not constitute independent corroboration. The system should identify syndication, quotation chains, shared datasets, and likely common origin where feasible.

If independence cannot be established, record it as uncertain rather than assuming corroboration.

## 7. Evidence and claim verification

Research outputs reuse the shared `EvidenceSource`, `EvidenceItem`, `Claim`, `ClaimEvidenceLink`, and `ClaimVerification` contracts.

For every material claim:

1. Capture the claim as a testable statement.
2. Identify its scope, time period, and relevant qualifiers.
3. Link supporting, contradicting, and contextual evidence.
4. Assess evidence quality, source independence, and freshness.
5. Record verification outcome and rationale.
6. Preserve unresolved uncertainty and limitations.

Suggested claim outcomes, subject to compatibility with the existing contract:

- `VERIFIED`
- `PARTIALLY_SUPPORTED`
- `UNSUPPORTED`
- `CONTRADICTED`
- `NOT_VERIFIED`
- `NOT_APPLICABLE`

Do not upgrade `NOT_VERIFIED` to `VERIFIED` merely because a model-generated summary repeats the claim.

### 7.1 Claim criticality

Claims may be classified by consequence:

- Low impact: contextual details that do not materially affect the main conclusion.
- Material: claims central to the explanation or recommendation.
- High impact: claims involving health, safety, law, finance, allegations, public figures, or other sensitive consequences.

Higher-impact claims require stronger evidence and review. The exact policy and specialist review requirements must be defined centrally; this contract does not authorize research agents to make regulated professional determinations.

## 8. Contradiction and uncertainty handling

A `ResearchConflict` records disagreement between claims, sources, datasets, or interpretations.

Required fields:

- Conflict ID and research-run reference.
- Conflicting claim/evidence references.
- Nature of disagreement.
- Whether the conflict is factual, temporal, definitional, methodological, or interpretive.
- Source quality and independence comparison.
- Potential explanation or missing context.
- Resolution status and reviewer rationale.

Possible statuses:

- `OPEN`
- `PARTIALLY_RESOLVED`
- `RESOLVED_WITH_RATIONALE`
- `UNRESOLVED`
- `NO_LONGER_RELEVANT`

The system must not force a resolution when evidence is insufficient. Research synthesis should state the disagreement and its impact on the conclusion.

## 9. Research synthesis and deliverables

A `ResearchBrief` is the principal structured output. It should include:

1. Research question and decision context.
2. Executive findings with confidence and scope.
3. Key verified facts and material claims.
4. Evidence table or linked evidence register.
5. Important source assessments and independence notes.
6. Contradictions and unresolved questions.
7. Estimates, opinions, and hypotheses clearly separated.
8. Audience, brand, and opportunity implications where supported.
9. Limitations, freshness, and missing evidence.
10. Recommended next steps, each labelled as recommendation rather than authorization.
11. Source list and claim/evidence traceability.
12. Research plan, run, and policy/model versions.

A brief may be `COMPLETED` while still containing unresolved claims, provided the declared completion criteria are met and the limitations are prominent. Completion must never be presented as blanket verification.

## 10. Research quality assessment

A `ResearchQualityAssessment` evaluates:

- Question coverage.
- Source relevance and reliability.
- Primary-source coverage where available.
- Source independence.
- Claim/evidence traceability.
- Contradiction handling.
- Freshness.
- Method transparency and reproducibility.
- Scope match.
- Privacy, rights, and permission compliance.
- Clarity of uncertainty and limitations.
- Output usability for the declared decision.

Use the shared quality outcomes:

- `PASS`
- `PASS_WITH_WARNINGS`
- `NEEDS_REVIEW`
- `BLOCKED`

Hard policy, rights, privacy, security, or permission blockers cannot be overridden by ordinary approval. Quality assessment is distinct from content quality assessment of a later script or rendered artifact.

## 11. Scheduled and event-driven research monitoring

A `ResearchMonitor` defines an approved, bounded monitoring objective.

Required fields:

- Monitor ID and workspace/brand scope.
- Topic, query, source set, or event condition.
- Purpose and intended decision/use.
- Schedule or event trigger.
- Permitted source/provider policy.
- Frequency, time window, and expiry/review date.
- Resource/quota policy and maximum execution bounds.
- Deduplication and material-change criteria.
- Alert priority and routing policy.
- Owner and status.
- Last successful run and next eligible run.

Monitoring behavior:

1. Run only within the approved schedule, source permissions, and resource policy.
2. Deduplicate repeated findings and identify material changes.
3. Preserve observation timestamps and source snapshots/versions where permitted.
4. Validate material evidence before escalating it as a substantive finding.
5. Generate alerts according to priority and owner notification preferences.
6. Pause safely when quotas, provider protections, permissions, or reliability constraints fail.
7. Continue supported cloud-coordinated monitoring independently of the user's PC, subject to deployment and provider availability.
8. Never let a discovery alert automatically authorize expensive research, production, spending, or public publishing.

Event-driven triggers must be explicit and auditable. The system must not infer permission to monitor unrelated topics.

## 12. Resource and provider controls

Before a research run:

- Check provider eligibility and approved data-protection terms.
- Confirm task-scoped credentials and data classification compatibility.
- Check quota, usage, reset window, budget, and forecast where available.
- Distinguish provider-reported usage from system estimates.
- Reserve or preflight resources according to the resource-management contract.
- Select only eligible providers within approved policy.
- Apply fallback only when the fallback provider is already approved for the same data class and purpose.
- Pause or escalate when no eligible provider or resource remains.

Research agents cannot authorize a new paid service, subscription, contract, budget increase, or transfer of restricted data to an unapproved provider.

## 13. Agent responsibilities and boundaries

Possible capability roles:

- `RESEARCH_PLANNER`: decomposes question, scope, source plan, and stopping conditions.
- `SOURCE_DISCOVERY`: discovers candidate sources within permitted access.
- `SOURCE_ASSESSOR`: evaluates provenance, relevance, credibility, freshness, and independence.
- `CLAIM_EXTRACTOR`: identifies testable claims from permitted materials.
- `EVIDENCE_ANALYST`: links evidence to claims and assesses support/contradiction.
- `SYNTHESIS_AGENT`: creates structured findings with uncertainty and limitations.
- `RESEARCH_QA`: independently checks traceability, coverage, and quality.
- `MONITORING_AGENT`: executes approved bounded monitoring and material-change detection.

These are logical capabilities, not a requirement for separate deployed agents. They must use registered identities, immutable versions, capability contracts, least-privilege task scopes, and auditable delegation.

No research agent may:

- Fabricate sources, quotations, data, or citations.
- Hide contradictions to make a conclusion cleaner.
- Treat an inaccessible source as inspected.
- Bypass rights, privacy, provider, or security restrictions.
- Expand monitoring scope without authorization.
- Trigger prohibited spending, commercial commitments, or public publishing.
- Self-approve a hard-blocked research output.

## 14. Downstream handoff contracts

### 14.1 Opportunity Intelligence

Research may update an OpportunityAssessment with new evidence, confidence, contradictions, and feasibility context. Research does not itself select an opportunity or approve execution.

### 14.2 Knowledge Management

Eligible findings may be proposed as KnowledgeItems with explicit epistemic status, scope, provenance, and review requirements. Research completion does not automatically promote findings to validated strategic knowledge.

### 14.3 Strategy & Planning

Research may provide evidence and scenario inputs for portfolio and strategic recommendations. Fundamental strategy and mission changes remain subject to owner approval.

### 14.4 Specialized studios

A studio receives a scoped `ResearchContextPackage` containing:

- Research brief and exact version.
- Relevant verified claims and claim-verification status.
- Evidence references and permitted source access.
- Unresolved claims and conflicts.
- Freshness and limitations.
- Audience, brand, and opportunity context.
- Rights and usage constraints.
- Required attribution/disclosure notes.

The studio must not remove qualifiers or present uncertain findings as verified facts. Each content variant still requires its own quality, rights, and approval path.

## 15. APIs and events

Illustrative versioned interfaces:

- `POST /v1/research/requests`
- `GET /v1/research/requests/{research_request_id}`
- `POST /v1/research/requests/{research_request_id}/plans`
- `POST /v1/research/runs`
- `GET /v1/research/runs/{research_run_id}`
- `GET /v1/research/runs/{research_run_id}/brief`
- `POST /v1/research/runs/{research_run_id}/quality-assessments`
- `POST /v1/research/monitors`
- `POST /v1/research/monitors/{monitor_id}/pause`
- `POST /v1/research/monitors/{monitor_id}/resume`
- `POST /v1/research/conflicts`

Illustrative events:

- `research.requested.v1`
- `research.planned.v1`
- `research.started.v1`
- `research.evidence.recorded.v1`
- `research.conflict.detected.v1`
- `research.synthesis.completed.v1`
- `research.quality.assessed.v1`
- `research.completed.v1`
- `research.blocked.v1`
- `research.monitor.finding_detected.v1`
- `research.monitor.material_change.v1`
- `research.monitor.paused.v1`

All events require durable delivery, schema versioning, idempotency, actor provenance, and workspace/brand scope. Event publication is not authorization for downstream execution.

## 16. Audit and explainability

For every research run, retain:

- Original request and decision context.
- Research plan and revisions.
- Agent identities and versions.
- Provider/tool identities and policy eligibility.
- Sources discovered, accessed, rejected, or unavailable, with reasons.
- Evidence and claim records with exact links.
- Search/collection timestamps and permitted source snapshots.
- Conflicts, verification outcomes, and quality assessments.
- Resource consumption and whether values are provider-reported or estimated.
- Human reviews, overrides, and decisions.
- Output versions and downstream consumers.

The system must be able to answer: **What question was asked, what sources were actually examined, what claims were supported, what remained uncertain, what resources were used, and which downstream decisions relied on the result?**

## 17. Acceptance criteria

The contract is ready for implementation design when:

1. Research requests carry explicit purpose, scope, permissions, freshness, and resource constraints.
2. Every run has a versioned plan and auditable lifecycle.
3. Source discovery records source provenance and retrieval time.
4. Source credibility and independence are assessed with rationale.
5. Material claims link to evidence and verification outcomes.
6. Contradictions and uncertainty remain visible in synthesis.
7. Research quality is assessed separately from downstream content quality.
8. Completion status does not imply all claims are verified.
9. Monitoring is bounded, deduplicated, resource-aware, and independently pausable.
10. Research can continue through the cloud control plane when the local PC is offline, where deployment supports it.
11. No research path bypasses privacy, rights, provider, or security controls.
12. Downstream handoffs preserve evidence, qualifiers, scope, and usage constraints.
13. Resource usage distinguishes measured provider reports from estimates.
14. Consequential research decisions and outputs are reproducible from retained records.

## 18. Open implementation details

Not fixed by this contract:

- Exact source credibility rubric and thresholds.
- Claim criticality taxonomy and specialist review requirements.
- Minimum corroboration standards by topic and claim type.
- Freshness windows by source category.
- Research depth definitions and stopping thresholds.
- Search strategy algorithms and deduplication implementation.
- Exact conflict-resolution workflow.
- Monitoring schedules and resource ceilings.
- Provider allowlist and regional processing choices.
- API and event payload schemas.
- Database, search, and indexing implementation.
- Exact quality thresholds and reviewer roles.

These require technical and policy design. No provider, budget, external source connection, or deployment choice is made here.

## 19. Decision traceability

This contract operationalizes accepted decisions covering:

- Evidence-based Source Intelligence and claim verification.
- Scheduled and event-driven discovery with bounded resource budgets.
- Audience and Opportunity Intelligence integration.
- Shared Knowledge Registry and validated learning promotion.
- Privacy-first data governance and authorized source use.
- Capability-based agent identities and task-scoped permissions.
- Durable job execution, checkpoint recovery, and owner-unavailability continuity.
- Resource quota tracking and approved provider fallback.
- Centralized quality, rights, and governance boundaries.
- Explainability, auditability, and owner-controlled strategic authority.

It is subordinate to the Master Blueprint, System Architecture Master Reference, Opportunity & Evidence Model, Shared Knowledge & Learning Model, centralized governance contracts, and owner-approved decision register. Conflicts must be recorded and reconciled rather than silently resolved by weakening a higher-priority rule.

---

**End of Contract 05 — Research Intelligence & Evidence Operations 1.0**
