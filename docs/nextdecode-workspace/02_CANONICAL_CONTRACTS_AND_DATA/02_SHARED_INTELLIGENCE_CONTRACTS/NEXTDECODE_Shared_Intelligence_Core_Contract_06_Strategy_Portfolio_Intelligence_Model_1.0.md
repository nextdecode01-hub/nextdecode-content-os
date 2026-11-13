# NEXTDECODE Shared Intelligence Core Contract 06
## Strategy & Portfolio Intelligence Model
**Version:** 1.0  
**Status:** Working architecture contract — documentation only  
**Scope:** Shared Intelligence Core; strategic planning, content portfolio, editorial programming, capacity alignment, and initiative tracking  
**Authority:** Derived from accepted Creator Success Intelligence decisions and architecture baselines. This document does not authorize repository changes, external integrations, spending, production execution, or publishing.

---

## 1. Purpose

Define how NEXTDECODE converts audience needs, research, opportunity assessments, brand direction, validated learning, and business objectives into a coherent, adaptive content and initiative portfolio.

The model must help answer:

- What should the brand focus on?
- Which audience needs and opportunities deserve attention?
- How should the portfolio balance timely, evergreen, original, and experimental work?
- Which formats, studios, series, and channels are appropriate?
- What should be planned now, later, tested, or declined?
- Can the approved work be delivered with available people, agents, providers, time, and resource limits?
- What evidence would justify changing the plan?

Strategy Intelligence recommends and coordinates. The owner retains authority over fundamental mission, positioning, strategic priorities, material resource reallocations, and other consequential decisions as defined by the governance model.

## 2. Core principles

1. **Evidence-led, not trend-led:** trends are inputs, not strategy by themselves.
2. **Audience value first:** portfolio choices must articulate the audience need or value being served.
3. **Brand coherence:** every initiative must fit the approved parent brand and applicable studio identity.
4. **Portfolio balance:** optimize the portfolio as a whole, not only individual content items.
5. **Multiple horizons:** combine timely opportunities with durable knowledge and long-term brand assets.
6. **Capacity-aware planning:** recommendations must account for real production capacity, approved resources, and dependencies.
7. **Uncertainty visible:** distinguish evidence, assumptions, forecasts, and strategic hypotheses.
8. **Adaptive, not erratic:** new evidence can trigger review, but temporary performance swings must not cause uncontrolled strategy changes.
9. **Owner-ratified strategy:** AI may propose strategic changes and scenario options; fundamental changes require owner approval.
10. **No unauthorized commitments:** a plan does not authorize spending, contracts, sponsorship acceptance, paid campaigns, or public publishing.
11. **Learning loop:** actual outcomes inform future recommendations, with causal uncertainty and scope preserved.
12. **Traceable decisions:** every consequential prioritization records rationale, evidence, constraints, and decision authority.

## 3. Strategic hierarchy

The planning model separates levels that should not be collapsed into a single content calendar.

| Level | Purpose | Example record |
|---|---|---|
| Mission and principles | Durable purpose and non-negotiable commitments | Mission/Principle references |
| Brand strategy | Positioning, promise, pillars, audience commitments | BrandStrategyVersion |
| Strategic objective | Measurable outcome or direction | StrategicObjective |
| Portfolio strategy | Balance of themes, formats, studios, and horizons | PortfolioStrategyVersion |
| Editorial program | Series, campaigns, recurring franchises, thematic plans | EditorialProgram |
| Initiative | Bounded body of work supporting an objective | StrategicInitiative |
| Content opportunity | Candidate item or cluster of items | Opportunity |
| Content plan item | Scheduled work with dependencies and target dates | PortfolioItem / PlanItem |
| Production workflow | Authorized execution of a selected item | Workflow/Job reference |

A lower-level plan cannot independently change a higher-level mission, brand promise, or approved strategic objective.

## 4. Core entities

### 4.1 StrategicObjective

Represents an owner-approved or formally proposed strategic objective.

Fields:

- `objective_id`: UUIDv7.
- Workspace and brand scope.
- Objective title and description.
- Strategic dimension: audience, editorial, brand, platform, business, learning, or operational.
- Intended outcome and rationale.
- Baseline, target, and measurement method where defined.
- Time horizon and review cadence.
- Supporting evidence and assumptions.
- Dependencies, risks, and constraints.
- Status: proposed, approved, active, paused, achieved, superseded, or cancelled.
- Owner, approver, policy version, timestamps, and schema version.

A target must not be invented when no baseline or owner-approved target exists. Proposed objectives remain clearly marked until approved.

### 4.2 PortfolioStrategyVersion

Represents the intended composition and operating direction of the content portfolio for a defined period.

It includes:

- Portfolio scope and planning horizon.
- Parent brand and participating studios.
- Approved strategic objectives.
- Audience segments and needs served.
- Brand pillars and editorial themes.
- Content categories and opportunity types.
- Format and channel intentions.
- Portfolio balance principles.
- Capacity and resource assumptions.
- Approved budget/resource constraints.
- Risk tolerance and experiment boundaries.
- Measurement and review approach.
- Version, author, owner approval, effective dates, and supersession history.

Portfolio strategy is versioned. Changes create a new version and preserve the rationale and evidence.

### 4.3 PortfolioItem

Represents a candidate or selected unit of portfolio work.

It may reference an Opportunity, EditorialProgram, StrategicInitiative, ResearchBrief, or existing content asset.

Required fields:

- `portfolio_item_id`: UUIDv7.
- Workspace, brand, and studio scope.
- Item type and title.
- Linked opportunity and evidence references.
- Audience need and expected value.
- Brand pillar and strategic objective references.
- Proposed format/channel.
- Priority assessment.
- Estimated effort, capacity requirements, and dependencies.
- Timing sensitivity and useful lifespan.
- Status and decision history.
- Owner and timestamps.

A PortfolioItem is a planning record, not an execution authorization.

### 4.4 EditorialProgram

Represents a recurring series, franchise, thematic program, or coordinated editorial initiative.

Fields include:

- Program ID and version.
- Purpose, audience promise, and editorial premise.
- Parent brand and studio ownership.
- Related pillars and objectives.
- Recurring themes and boundaries.
- Supported formats and channels.
- Cadence proposal, if approved.
- Quality and identity requirements.
- Content lineage and episode/edition references.
- Performance and learning criteria.
- Owner, status, and review dates.

A program should have a clear audience reason to exist. Repetition alone is not a strategy.

### 4.5 StrategicInitiative

Represents a bounded project intended to advance an approved objective.

It includes:

- Initiative ID, title, and description.
- Objective and portfolio references.
- Expected outcomes and evidence rationale.
- Scope, exclusions, and deliverables.
- Milestones, dependencies, and risks.
- Required capabilities and resource estimates.
- Approved authority and budget/resource envelope.
- Success measures and review gates.
- Owner, status, and decision history.

AI may execute work within an already-approved initiative and delegated authority. New strategic initiatives and material scope changes require the applicable owner approval.

### 4.6 PortfolioAssessment

An immutable, versioned evaluation of a portfolio item or portfolio composition.

It records:

- Assessment ID and evaluated portfolio version.
- Assessment date and assessor/model version.
- Policy and scoring-model version.
- Eligibility and hard-gate outcomes.
- Audience, brand, strategic, evidence, business, timing, and feasibility dimensions.
- Confidence and uncertainty.
- Capacity/resource implications.
- Portfolio balance implications.
- Recommendation and rationale.
- Human decision/override, if any.

Reassessment creates a new record; it does not overwrite history.

## 5. Portfolio composition and balance

The portfolio should deliberately consider several complementary categories:

- **Timely:** current developments with a limited relevance window.
- **Evergreen:** durable explanations and reference content.
- **Original:** distinctive analysis, research, viewpoints, or formats.
- **Experimental:** bounded tests designed to produce learning.
- **Series/franchise:** repeatable editorial properties with a clear audience promise.
- **Community-responsive:** work informed by audience questions and feedback, subject to privacy and moderation rules.
- **Business-supporting:** content that supports approved products or commercial objectives without compromising editorial integrity.

These categories are planning lenses, not fixed quotas. No percentage allocation or fixed content mix is approved by this contract.

Portfolio assessments should identify concentration risk, over-reliance on one topic or platform, excessive trend chasing, underinvestment in durable assets, and conflicts between audience value and short-term commercial pressure.

## 6. Prioritization and eligibility

Prioritization follows the Opportunity & Evidence Model: eligibility gates first, weighted assessment second.

Recommended portfolio dimensions:

| Dimension | Evaluation |
|---|---|
| Audience value | Importance and usefulness of the audience need |
| Brand contribution | Fit with positioning, pillars, and audience promise |
| Evidence strength | Quality, freshness, corroboration, and uncertainty |
| Differentiation | Originality and distinctive value |
| Strategic contribution | Progress toward approved objectives |
| Business contribution | Defensible support for approved business goals |
| Timing | Urgency, relevance window, and opportunity expiry |
| Portfolio balance | Contribution to breadth, durability, and diversity |
| Feasibility | Capacity, capability, dependencies, and resource constraints |
| Learning value | Potential to test an important hypothesis or reduce uncertainty |

Rules:

- Hard eligibility gates cannot be offset by a high score.
- Weights are configurable and versioned; no fixed weights are approved here.
- Missing evidence remains missing and affects confidence.
- Scores are prioritization aids, not predictions of success.
- The system must explain why an item is recommended and what trade-offs it creates.
- Portfolio-level decisions should consider opportunity cost, not only item-level scores.

## 7. Planning horizons

The system should support several horizons without assuming universal calendar lengths:

1. **Immediate:** time-sensitive work and current approved commitments.
2. **Near-term:** planned content, production capacity, and scheduled initiatives.
3. **Mid-term:** series development, thematic clusters, and portfolio balance.
4. **Long-term:** brand assets, capability building, audience development, and strategic initiatives.

Exact durations are configurable by workspace and planning process. A short-lived trend must not displace an approved commitment without an explicit reprioritization decision.

## 8. Editorial calendar and scheduling

The editorial calendar is a projection of portfolio decisions and execution states; it is not the source of truth for all strategy.

A `PlanningWindow` may include:

- Calendar period and timezone.
- Approved portfolio strategy version.
- Planned items and milestones.
- Studio and channel allocation.
- Target dates and timing constraints.
- Capacity reservations and dependencies.
- Review/approval checkpoints.
- Uncertainty and provisional dates.

Scheduling rules:

- Distinguish proposed, tentatively scheduled, committed, in production, ready for review, approved, published, delayed, and cancelled states.
- Do not represent a proposed date as a confirmed publishing schedule.
- Respect production dependencies, asset availability, review windows, and channel constraints.
- Do not infer public publishing authorization from a calendar entry.
- Do not let scheduling bypass the centralized approval and publishing governance model.
- Rescheduling must preserve the original plan and record the reason.

## 9. Capacity and resource-aware portfolio planning

Portfolio recommendations must use the Resource Management and Agent Intelligence contracts.

Capacity dimensions may include:

- Human review availability.
- Agent capability and availability.
- Studio production capacity.
- Local rendering worker availability.
- Remote worker eligibility.
- Provider quotas and reset windows.
- Approved infrastructure/service capacity.
- Asset and rights availability.
- Time-sensitive deadlines and dependencies.

The planner may:

- Estimate workload and identify bottlenecks.
- Recommend sequencing and workload balancing.
- Reserve resources within approved limits.
- Recommend eligible provider or worker alternatives.
- Defer work when capacity is insufficient.
- Identify opportunities that should be declined because they are infeasible.

It may not:

- Authorize new spending, subscriptions, contracts, or budget increases.
- Expand approved resource limits.
- Reassign restricted resources across workspaces without authorization.
- Reduce required quality, rights, security, or approval checks to meet a deadline.

## 10. Strategy recommendations and scenario planning

A `StrategyRecommendation` should contain:

- The strategic question.
- Current approved strategy and version.
- Evidence and knowledge references.
- Scenario assumptions.
- Options considered, including maintaining the current approach.
- Expected benefits and trade-offs.
- Risks, dependencies, and uncertainty.
- Resource and capacity implications.
- Reversibility and possible failure signals.
- Recommendation and confidence.
- Decisions requiring owner approval.

Scenario analysis may model changes in audience demand, platform conditions, provider costs, production capacity, business performance, or strategic assumptions. Forecasts must be labelled as forecasts, with assumptions and uncertainty visible.

The AI must not present a scenario as a guaranteed outcome or quietly change approved strategy based on a modelled result.

## 11. Portfolio governance and decision authority

Authority boundaries:

- AI may discover opportunities and prepare portfolio assessments.
- AI may recommend themes, series, formats, timing, and resource allocation.
- AI may schedule or initiate tasks only within explicitly approved automation policies and resource envelopes.
- AI may execute already-approved initiatives within their authorized scope.
- Human owner approval is required for fundamental mission, positioning, strategic priorities, material scope changes, significant resource reallocations, and other reserved decisions.
- Financial authority remains recommendation and preparation only for commercial commitments and spending.
- Publishing automation remains disabled pending separate policy approval.

Owner unavailability does not convert a proposed decision into an approved decision. Work may continue only within previously granted authority.

## 12. Strategy review and adaptation

A `PortfolioReview` evaluates performance and continued relevance at a defined cadence or trigger.

It should consider:

- Progress against approved objectives.
- Audience and opportunity changes.
- Brand and editorial consistency.
- Portfolio mix and concentration.
- Content quality and rights outcomes.
- Production capacity and reliability.
- Channel and distribution results.
- Business performance and commercial integrity.
- Validated learning and unresolved hypotheses.
- Risks, dependencies, and external changes.

Review outcomes may include:

- Continue current strategy.
- Adjust execution within existing authority.
- Run a bounded experiment.
- Reprioritize within an approved envelope.
- Prepare a strategic change proposal for owner review.
- Pause or retire an initiative.

A review recommendation does not itself change the approved strategy version.

## 13. APIs and events

Illustrative versioned interfaces:

- `GET /v1/strategy/objectives`
- `POST /v1/strategy/objectives/proposals`
- `GET /v1/strategy/portfolio/current`
- `POST /v1/strategy/portfolio/assessments`
- `POST /v1/strategy/portfolio/proposals`
- `GET /v1/portfolio/items`
- `POST /v1/portfolio/items`
- `POST /v1/portfolio/items/{item_id}/prioritize`
- `POST /v1/editorial-programs`
- `POST /v1/strategic-initiatives`
- `POST /v1/strategy/reviews`
- `POST /v1/planning-windows`

Illustrative events:

- `strategy.objective.proposed.v1`
- `strategy.objective.approved.v1`
- `strategy.portfolio.assessed.v1`
- `strategy.portfolio.proposed.v1`
- `strategy.portfolio.approved.v1`
- `portfolio.item.created.v1`
- `portfolio.item.selected.v1`
- `portfolio.item.deprioritized.v1`
- `editorial.program.created.v1`
- `initiative.approved.v1`
- `initiative.scope_change_requested.v1`
- `strategy.review.completed.v1`

All events require durable delivery, schema versioning, idempotency, actor provenance, and workspace/brand scope. An event must not be interpreted as permission to execute a consequential action unless the relevant authorization is separately present.

## 14. Audit and explainability

Retain:

- Strategy and portfolio versions.
- Evidence, opportunity, audience, brand, and learning references.
- Assessment dimensions, weights, confidence, and rationale.
- Capacity and resource assumptions.
- Options considered and trade-offs.
- Owner approvals, rejections, and overrides.
- Policy version and actor identity.
- Calendar changes and reasons.
- Initiative scope, milestones, and outcomes.

The system must answer: **Why was this work prioritized, what was deprioritized, which audience and brand objectives does it serve, what assumptions were used, what resources does it consume, and who approved the decision?**

## 15. Acceptance criteria

The contract is ready for implementation design when:

1. Mission, brand strategy, objectives, portfolio strategy, programs, initiatives, and content items are distinct entities.
2. Portfolio assessments link to opportunity, evidence, audience, brand, and learning records.
3. Eligibility gates run before weighted prioritization.
4. Portfolio balance can be evaluated without imposing unapproved fixed percentages.
5. Multiple planning horizons and provisional versus committed dates are supported.
6. Scheduling respects capacity, dependencies, resource policies, and governance gates.
7. AI recommendations preserve assumptions, uncertainty, trade-offs, and alternatives.
8. Owner approval is required for reserved strategic changes.
9. Existing approved initiatives can continue within scope during owner unavailability.
10. No plan or calendar state silently authorizes spending, contracts, or public publishing.
11. Portfolio reviews use validated learning and avoid overreacting to isolated performance events.
12. Decisions and strategy versions are immutable, traceable, and explainable.

## 16. Open implementation details

Not fixed by this contract:

- Initial approved strategic objectives and measurable targets.
- Final portfolio categories and any target mix.
- Planning horizon durations and review cadence.
- Exact scoring dimensions, weights, and thresholds.
- Capacity estimation and workload models.
- Calendar integration and scheduling implementation.
- Initiative approval roles and scope-change thresholds.
- Forecasting methodology and uncertainty calibration.
- API/event payload schemas and database design.
- Exact owner notification and escalation thresholds.

These require owner review or technical evidence. This contract does not authorize calendar integrations, new services, spending, or implementation.

## 17. Decision traceability

This contract operationalizes accepted decisions covering:

- Intelligent portfolio planning across timely, evergreen, original, and experimental content.
- Configurable opportunity scoring with hard eligibility gates.
- Diversified creator-business objectives with editorial integrity protected.
- Shared Intelligence Core and specialized studio autonomy.
- Governed cross-studio collaboration and learning propagation.
- Resource/quota intelligence and budget-bounded capacity management.
- Owner-approved strategy, mission, and material resource decisions.
- Policy-governed automation and continuity during owner unavailability.
- Evidence-based strategic reviews, scenario planning, and decision records.
- Separate publishing and commercial authority boundaries.

It is subordinate to the Master Blueprint, System Architecture Master Reference, Opportunity & Evidence Model, Brand & Editorial Intelligence Model, Shared Knowledge & Learning Model, Research Intelligence & Evidence Operations, centralized governance contracts, and owner-approved decision register. Conflicts must be recorded and reconciled rather than silently resolved by weakening a higher-priority rule.

---

**End of Contract 06 — Strategy & Portfolio Intelligence Model 1.0**
