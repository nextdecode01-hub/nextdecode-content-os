# NEXTDECODE Shared Intelligence Core Contract 08
## Audience & Performance Intelligence Model
**Version:** 1.0  
**Status:** Working architecture contract — documentation only  
**Scope:** Shared Intelligence Core; audience understanding, content/channel performance, experimentation, attribution, and evidence-based learning  
**Authority:** Derived from accepted Creator Success Intelligence decisions and architecture baselines. This document does not authorize repository changes, external integrations, analytics-account connections, data collection, spending, production execution, or publishing.

---

## 1. Purpose

Define a unified model for understanding audiences, measuring content and channel performance, evaluating experiments, and converting observed outcomes into scoped, evidence-backed learning.

The system must connect the full chain:

`Audience Need → Opportunity → Research → Creative Variant → Production → Packaging → Distribution → Audience Response → Business Outcome → Validated Learning`

It must support decisions across the parent brand, specialized studios, formats, and channels while preserving the limits of available data. Platform metrics, estimates, forecasts, and causal conclusions must never be presented as interchangeable.

## 2. Core principles

1. **Audience value over vanity metrics:** views and reach are useful signals but do not alone establish audience value or business success.
2. **Contextual measurement:** metrics must retain platform, format, audience, time window, content version, and measurement method.
3. **Observed versus inferred:** platform-reported, directly observed, estimated, and forecast values remain distinct.
4. **Attribution is not causation:** correlation or attributed conversion does not automatically prove that content caused the outcome.
5. **Learning needs evidence:** one viral or failed item cannot permanently rewrite strategy.
6. **Experimentation is controlled:** hypotheses, baselines, sample sizes, windows, budgets, and stop conditions are explicit.
7. **Shared learning is scoped:** a studio-specific result is not automatically universal across studios, audiences, or channels.
8. **Privacy first:** use only authorized data, minimize personal data, and avoid unauthorized cross-platform identity matching.
9. **Business insight preserves editorial integrity:** commercial value cannot silently change factual conclusions or audience-trust commitments.
10. **No metric creates authority:** an analytics recommendation does not authorize spending, commitments, policy changes, or publishing.
11. **Data gaps remain visible:** missing, delayed, sampled, or incomparable data must not be silently filled.
12. **Owner-controlled strategy:** AI recommends and prepares evidence; fundamental strategic changes require owner approval.

## 3. Measurement hierarchy

The model distinguishes multiple measurement levels.

| Level | Measurement focus | Example |
|---|---|---|
| Audience | Needs, segments, satisfaction, trust, and relationship | Audience questions or survey findings |
| Content | Performance of a content item or variant | Views, retention, completion |
| Packaging | Title, thumbnail, hook, metadata, and presentation | Click-through rate where available |
| Distribution | Channel, timing, cadence, and delivery | Reach, impressions, referral |
| Engagement | Audience response and interaction | Comments, saves, shares, meaningful replies |
| Conversion | Movement toward an intended action | Newsletter signup or product interest |
| Business | Revenue, cost, margin, and commercial outcomes | Attributed revenue and production cost |
| Portfolio | Aggregate performance and strategic contribution | Studio/series/format comparisons |
| Learning | Change in validated understanding | Experiment result and reusable learning |

Metric definitions and availability vary by platform. The registry must not assume that similarly named metrics are directly comparable across services.

## 4. Core entities

### 4.1 AudienceSegment

Represents a scoped audience grouping.

Required fields:

- `audience_segment_id`: UUIDv7.
- Workspace and brand scope.
- Segment type: strategic persona, observed segment, or emerging segment.
- Name and description.
- Needs, interests, behaviors, and context supported by permitted evidence.
- Source and evidence references.
- Platform scope, where applicable.
- Observation window and last-reviewed time.
- Confidence, limitations, and known sampling bias.
- Classification, purpose, permissions, and retention policy.
- Version, owner, and audit metadata.

Segmentation rules:

- Strategic personas are human-defined planning constructs.
- Observed segments are derived from authorized, aggregated evidence.
- Emerging segments are provisional hypotheses requiring validation.
- Platform-scoped segments remain platform-scoped unless lawful, explicit evidence supports a permitted relationship.
- Do not assume two accounts or audiences on different platforms represent the same individuals.
- Do not infer sensitive personal traits or build sensitive profiles without explicit lawful basis and authorization.

### 4.2 AudienceInsight

A versioned finding about audience needs, expectations, behavior, or response.

It includes:

- Insight ID and statement.
- Segment and workspace/brand scope.
- Supporting and contradicting evidence.
- Collection method and observation window.
- Sample size and representativeness, where relevant.
- Confidence and limitations.
- Status: hypothesis, observed, validated, disputed, superseded, or retracted.
- Applicable formats/channels and known exclusions.
- Review and provenance history.

An audience insight must distinguish direct feedback from inferred behavior.

### 4.3 MetricDefinition

A registry entry defining a metric.

Required fields:

- Metric ID and version.
- Canonical name and description.
- Formula or platform-provided definition.
- Numerator/denominator, if applicable.
- Unit, aggregation method, and time basis.
- Source platform/provider.
- Content/format/channel scope.
- Known limitations and comparability rules.
- Data classification and retention.
- Effective date and supersession history.

A canonical internal metric may map to multiple platform-specific definitions, but the mapping must preserve the original definition and comparability limitations.

### 4.4 PerformanceSnapshot

An immutable measurement snapshot for a content item, variant, channel, audience segment, or portfolio.

Fields:

- Snapshot ID and workspace/brand/studio scope.
- Content and exact variant references.
- Platform/channel/account reference, appropriately protected.
- Measurement window start/end and capture timestamp.
- Metric definitions and values.
- Value type: `PLATFORM_REPORTED`, `DIRECTLY_OBSERVED`, `ESTIMATED`, or `FORECAST`.
- Source connector/report reference.
- Sampling, delay, missingness, and known limitations.
- Currency and conversion basis for financial metrics.
- Data quality assessment and provenance.
- Schema and connector version.

Snapshots are append-only. Corrections create a new snapshot or correction record with lineage; they do not silently overwrite historical measurements.

### 4.5 ContentPerformanceProfile

A derived, versioned view of performance across one or more snapshots.

It may summarize:

- Reach and discovery.
- Engagement quality.
- Retention and completion.
- Audience response and sentiment signals, where permitted.
- Conversion and downstream actions.
- Production/resource cost.
- Business outcomes.
- Comparison baseline and cohort.
- Uncertainty and data coverage.

It must link to the underlying snapshots and calculation version. It is not itself a raw platform measurement.

### 4.6 Experiment

Represents a controlled test of a defined hypothesis.

Required fields:

- Experiment ID and workspace/brand/studio scope.
- Hypothesis and rationale.
- Independent variable(s) and treatment(s).
- Outcome metric(s) and metric definitions.
- Target audience and channel scope.
- Baseline or comparison method.
- Sample-size rationale and measurement window.
- Budget/resource envelope already approved.
- Start/end criteria and stop conditions.
- Confounders and risk controls.
- Owner, status, and approval references.

Experiment statuses may include proposed, approved, scheduled, running, paused, completed, inconclusive, stopped, and archived.

### 4.7 ExperimentResult

Records the observed result of an experiment.

It includes:

- Experiment and treatment references.
- Actual sample size and observation window.
- Metric snapshots and baseline.
- Statistical or qualitative analysis method.
- Effect estimate and uncertainty, where appropriate.
- Missing data and confounders.
- Result: positive, negative, mixed, inconclusive, or invalid.
- Limitations and applicability scope.
- Reviewer and validation status.

A result must not claim causation unless the experimental design and analysis support that conclusion.

### 4.8 AttributionRecord

Represents an observed or estimated relationship between content/distribution and a downstream action or business outcome.

Fields:

- Attribution ID.
- Content, campaign, channel, and conversion references.
- Attribution model and version.
- Lookback window and touchpoint coverage.
- Observed/estimated classification.
- Revenue/cost data source and currency.
- Known missing touchpoints and limitations.
- Confidence and alternative explanations.
- Consent and data-processing references.

Attribution models describe how credit is assigned; they do not prove causality.

### 4.9 LearningRecord

A validated or provisional conclusion derived from audience observations, performance snapshots, or experiments.

It must reuse the Shared Knowledge & Learning Model and include:

- Learning statement and question.
- Supporting experiment and snapshot references.
- Audience, platform, format, and time scope.
- Validation standard and status.
- Confidence, uncertainty, and limitations.
- Applicability and exclusions.
- Review date and supersession history.

## 5. Metric taxonomy

The metric registry may organize metrics into categories such as:

- Discovery: impressions, reach, traffic sources.
- Packaging: click-through and entry rates, where defined.
- Consumption: views, watch time, reading time, completion.
- Retention: average duration, audience retention curve, return behavior.
- Engagement: comments, shares, saves, meaningful interactions.
- Audience growth: follows, subscribers, returning audience.
- Conversion: clicks, signups, downloads, leads, purchases.
- Business: revenue, expenses, gross contribution, margin, pipeline.
- Production: time, render cost, provider usage, rework, failure rates.
- Quality: QA outcomes, corrections, rights incidents, review findings.

Each metric must have a defined source, formula, time window, and interpretation. Do not combine unlike metrics into a universal score without a transparent and validated method.

## 6. Measurement windows and comparison

A measurement is meaningful only in context.

Each comparison should specify:

- Content publication time and age at measurement.
- Measurement window and timezone.
- Format and platform.
- Audience/cohort scope.
- Distribution conditions.
- Paid versus organic exposure, where applicable.
- Content and packaging version.
- Relevant external events or seasonality.
- Baseline and comparison population.

Avoid comparing a new item measured for one day with an older item measured for several weeks unless the method normalizes the observation window and explains limitations.

## 7. Experimentation framework

The experiment lifecycle is:

`IDEA → HYPOTHESIS → DESIGN → REVIEW/APPROVAL → SCHEDULED → RUNNING → ANALYSIS → VALIDATION → LEARNING_PROMOTION`

An experiment brief must specify:

1. Problem or uncertainty.
2. Testable hypothesis.
3. Variable(s) to change.
4. Outcome and guardrail metrics.
5. Audience and platform scope.
6. Baseline or comparison group.
7. Sample-size and duration rationale.
8. Approved resource/budget envelope.
9. Stop conditions and risk limits.
10. Analysis plan and decision criteria.

### 7.1 Autonomous experimentation boundaries

AI may propose and conduct experiments only within preapproved policies, scopes, and resource limits.

It may not:

- Increase budgets or authorize new spending.
- Change owner-approved brand, editorial, privacy, or publishing policies.
- Run experiments involving sensitive editorial or personal-data processing without required review.
- Mislead audiences or conceal material experimental treatment.
- Publish content outside the separate publishing authorization model.
- Promote an inconclusive result as validated learning.

### 7.2 Staged rollout

Where appropriate, rollout should be staged:

- Small controlled test.
- Evidence and guardrail review.
- Limited expansion within the approved envelope.
- Broader use only after validation.
- Rollback or stop when guardrails fail.

Exact sample sizes, effect thresholds, and rollout percentages are not fixed in this contract.

## 8. Audience feedback and interaction signals

Audience feedback may include comments, questions, surveys, support requests, community discussions, and direct feedback where access is authorized.

Processing rules:

- Use purpose-limited collection and minimum necessary data.
- Prefer aggregate or anonymized analysis where feasible.
- Preserve source, context, time, and sampling bias.
- Distinguish a single comment from a representative audience trend.
- Detect abuse, sensitive disclosures, safety concerns, and privacy risks for appropriate escalation.
- Do not infer cross-platform identity without explicit authorized basis.
- Do not use sensitive personal data for targeting or profiling without required authorization and safeguards.

The broad community-management authority defined elsewhere does not expand data collection rights or override privacy, safety, platform, or commercial boundaries.

## 9. Unified attribution and business measurement

The analytics model should connect:

- Content and variant lineage.
- Research and opportunity references.
- Production time and resource consumption.
- Packaging and distribution actions.
- Platform performance snapshots.
- Audience acquisition and engagement.
- Website/newsletter conversions where authorized.
- Sponsorship and affiliate outcomes.
- Product sales and membership outcomes.
- Expenses, cost allocation, and profitability.

Business reporting must distinguish:

- Confirmed revenue versus attributed revenue.
- Observed costs versus allocated estimates.
- Actual profit versus forecast.
- Gross revenue versus net contribution.
- Platform-reported values versus internally calculated values.

Financial data access is restricted and auditable. Analytics can prepare reports and recommendations; it cannot authorize spending, accept sponsorships, sign agreements, or make binding commercial commitments.

## 10. Cross-studio and cross-platform learning

Shared learning must retain:

- Originating studio and content format.
- Audience and channel scope.
- Measurement window.
- Metric definitions and connector version.
- Experiment design or observational method.
- Confidence and limitations.
- Validation and approval status.

A finding from one studio may be recommended to another as a hypothesis, not automatically applied as a rule. Workspace-level promotion requires evidence that supports the broader applicability.

Cross-platform comparisons must account for different metric definitions, recommendation systems, audience composition, and measurement availability.

## 11. Privacy, consent, and data governance

All audience and performance data is subject to the central data-governance model.

Required safeguards:

- Purpose limitation and data minimization.
- Classification: Public, Internal, Confidential, Restricted.
- Source permissions and consent where applicable.
- Workspace/brand isolation.
- Retention and deletion controls.
- Restricted access to account-level and financial data.
- Aggregation/anonymization where appropriate.
- No unauthorized identity matching across platforms.
- No sensitive-trait inference or sensitive profiling without explicit lawful basis and authorization.
- Audit access, export, and processing.
- Respect provider terms and data-protection commitments.

Derived metrics, embeddings, audience segments, and attribution records remain governed data and must follow source restrictions and deletion requirements.

## 12. APIs and events

Illustrative versioned interfaces:

- `POST /v1/audience/segments`
- `GET /v1/audience/segments/{segment_id}`
- `POST /v1/audience/insights`
- `POST /v1/metrics/definitions`
- `POST /v1/performance/snapshots`
- `GET /v1/content/{content_id}/performance`
- `POST /v1/experiments`
- `POST /v1/experiments/{experiment_id}/results`
- `POST /v1/attribution/records`
- `POST /v1/learning-records`

Illustrative events:

- `audience.insight.detected.v1`
- `audience.insight.validated.v1`
- `performance.snapshot.recorded.v1`
- `performance.data_quality.warning.v1`
- `experiment.proposed.v1`
- `experiment.approved.v1`
- `experiment.started.v1`
- `experiment.completed.v1`
- `experiment.inconclusive.v1`
- `attribution.record.created.v1`
- `learning.validation.requested.v1`
- `learning.record.promoted.v1`

Events require durable delivery, schema versioning, idempotency, actor provenance, and workspace/brand scope. Analytics events do not authorize downstream spending or publishing.

## 13. Audit and explainability

Retain:

- Metric definitions and versions.
- Raw or source-linked snapshots, within retention and permission limits.
- Connector/provider and collection timestamps.
- Content/variant and campaign lineage.
- Experiment hypotheses, design, approvals, and results.
- Attribution model and calculation versions.
- Data quality, missingness, and uncertainty.
- Learning validation and promotion decisions.
- Access and processing audit records.
- Policy, consent, and retention versions.

The system must answer: **What was measured, from which source, for which audience and time window, using which definition, what was missing, what can be concluded, and what remains uncertain?**

## 14. Acceptance criteria

The contract is ready for implementation design when:

1. Audience segments distinguish strategic, observed, and emerging types.
2. Cross-platform identity is not assumed.
3. Metric definitions are versioned and platform-specific.
4. Snapshots preserve source, time window, value classification, and limitations.
5. Observed, platform-reported, estimated, and forecast data remain distinguishable.
6. Content performance links to exact content/variant and distribution history.
7. Experiments define hypotheses, metrics, sample-size rationale, windows, budgets, and stop conditions.
8. Inconclusive or weak results cannot be promoted as validated learning.
9. Attribution does not claim causation without appropriate evidence.
10. Cross-studio learning preserves applicability and provenance.
11. Privacy, consent, retention, and workspace isolation are enforced.
12. Business reporting distinguishes actual, attributed, estimated, and forecast values.
13. Analytics cannot authorize spending, commercial commitments, or publishing.
14. All consequential calculations and learning promotions are reproducible and auditable.

## 15. Open implementation details

Not fixed by this contract:

- Initial platform connectors and authorized data sources.
- Exact metric catalogue and platform mappings.
- Data collection cadence and retention periods.
- Statistical methods and confidence thresholds.
- Minimum sample-size standards by experiment type.
- Attribution models and lookback windows.
- Audience segmentation algorithms and privacy thresholds.
- Sentiment/feedback classification methods and validation.
- Currency conversion and cost allocation rules.
- Dashboard and reporting implementation.
- API/event payload schemas and storage technology.

These require technical, privacy, and owner review. This contract does not authorize analytics-account connections, new data collection, paid providers, or deployment.

## 16. Decision traceability

This contract operationalizes accepted decisions covering:

- Hybrid audience segmentation and privacy boundaries.
- Unified analytics and attribution across content, production, distribution, audience, and business outcomes.
- Evidence-based performance learning and controlled experimentation.
- Cross-studio Learning Registry with applicability controls.
- Business intelligence and financial reporting with confirmed/estimated/forecast distinctions.
- Privacy-first data governance and no unauthorized cross-platform identity matching.
- Owner-controlled strategy and commercial authority.
- Policy-governed automation and resource limits.
- Explainability, auditability, and validated knowledge promotion.

It is subordinate to the Master Blueprint, System Architecture Master Reference, Opportunity & Evidence Model, Brand & Editorial Intelligence Model, Shared Knowledge & Learning Model, Research Intelligence & Evidence Operations, Strategy & Portfolio Intelligence Model, centralized governance contracts, and owner-approved decision register. Conflicts must be recorded and reconciled rather than silently resolved by weakening a higher-priority rule.

---

**End of Contract 08 — Audience & Performance Intelligence Model 1.0**
