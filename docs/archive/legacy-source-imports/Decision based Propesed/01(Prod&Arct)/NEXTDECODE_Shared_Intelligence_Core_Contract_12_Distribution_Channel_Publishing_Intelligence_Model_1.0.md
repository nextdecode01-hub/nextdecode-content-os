# NEXTDECODE Shared Intelligence Core Contract 12
## Distribution, Channel & Publishing Intelligence Model
**Version:** 1.0  
**Status:** Working architecture contract — documentation only  
**Scope:** Channel intelligence, distribution strategy, platform adaptation, scheduling, publishing governance, post-publication monitoring, and distribution learning  
**Authority:** Derived from accepted NEXTDECODE product architecture and Creator Success Intelligence decisions. This document does not authorize repository access or changes, provider connections, subscriptions, spending, deployments, account connections, public publishing, or external communications.

---

## 1. Purpose

Define how NEXTDECODE decides where, when, and how approved content should be distributed; prepares channel-native packages; coordinates schedules; enforces publishing authority; and learns from post-publication performance.

Distribution is not a final button attached to content creation. It is a governed capability that connects audience context, content suitability, channel requirements, resource constraints, publishing permissions, and measurable outcomes.

**Core rule:** A distribution recommendation is not a schedule authorization, a schedule is not publishing authorization, and a successful upload is not proof that the content is publicly visible or correctly presented.

## 2. Design principles

1. **Audience and channel fit:** choose channels based on audience relevance and content suitability, not simply maximum reach.
2. **Channel-native adaptation:** each platform package respects platform conventions, technical limits, accessibility, and audience expectations.
3. **One canonical asset, controlled variants:** retain canonical asset lineage while recording platform-specific derivatives and metadata.
4. **Governance before execution:** policy, rights, quality, approval, account authorization, and platform constraints are evaluated before any external side effect.
5. **No inherited approval:** approval for one asset version, channel, account, or publication window does not approve another.
6. **Publishing authority is separate:** distribution agents cannot grant themselves permission to publish.
7. **Idempotent external operations:** uncertain upload or publish outcomes must be reconciled before retry.
8. **Privacy and platform compliance:** audience data and platform access are used only for approved purposes and within applicable permissions.
9. **Evidence-based learning:** distinguish platform-reported metrics, observed outcomes, estimates, and forecasts.
10. **Owner control:** emergency pause, policy versioning, revocation, and audit remain available at every stage.

## 3. Position in the architecture

Distribution Intelligence consumes:

- Approved content asset versions and production manifests.
- Content Graph lineage and evidence references.
- Brand and studio identity profiles.
- Audience segments and validated insights.
- Strategy and portfolio priorities.
- Channel/platform capability profiles.
- Rights and disclosure assessments.
- QA outcomes and review/approval records.
- Resource and agent orchestration decisions.

It produces:

- Channel suitability assessments.
- Distribution strategies and channel recommendations.
- Platform-specific distribution packages.
- Scheduling proposals and calendar entries.
- Publishing authorization requests.
- Upload/publish execution records.
- Post-publication monitoring and analytics references.
- Distribution learning records and recommendations.

The Distribution Studio coordinates channel operations but does not own content creation, central rights governance, identity authorization, financial authority, or the platform's external systems.

## 4. Core object model

### 4.1 ChannelProfile

A `ChannelProfile` describes a distribution destination or platform surface.

Fields include:

- Stable channel ID and immutable profile version.
- Platform/provider identity.
- Channel type and supported content formats.
- Audience/context characteristics.
- Technical constraints and supported metadata.
- Accessibility and disclosure requirements.
- API or integration capabilities.
- Account/identity requirements.
- Rate limits and quota characteristics.
- Scheduling and publication capabilities.
- Analytics availability and known limitations.
- Geographic or policy restrictions.
- Verification date and source.
- Active, restricted, deprecated, or unavailable status.

Platform requirements must be versioned and refreshed. The system must not assume a platform API or policy remains unchanged.

### 4.2 ChannelAccount

A `ChannelAccount` represents an authorized account or destination controlled by the owner or organization.

It includes:

- Account reference and platform.
- Workspace/brand scope.
- Account owner and authorized human identity.
- Connection and credential reference (never raw secrets in ordinary records).
- Granted scopes and permission evidence.
- Connection health and last verification.
- Revocation and expiry state.
- Permitted operations.
- Account-specific publication restrictions.

A connected account does not imply every operation is authorized. Permissions must be checked for the exact action and content.

### 4.3 DistributionStrategy

A `DistributionStrategy` describes how a content asset or campaign should reach a defined audience.

It includes:

- Strategy ID/version.
- Source content and asset versions.
- Objective and intended audience.
- Candidate channels and rationale.
- Channel-specific role in the overall strategy.
- Adaptation requirements.
- Timing hypothesis and constraints.
- Resource envelope.
- Measurement plan and success criteria.
- Risks, dependencies, and exclusions.
- Approval status and owner/policy references.

A strategy may recommend channels without creating a schedule or authorizing publication.

### 4.4 ChannelSuitabilityAssessment

A suitability assessment evaluates whether a specific content asset is appropriate for a channel.

Consider:

- Audience relevance.
- Format compatibility.
- Editorial and brand fit.
- Platform-native value.
- Asset quality and technical readiness.
- Rights, disclosure, and policy compatibility.
- Accessibility.
- Channel saturation or timing context where reliable data exists.
- Resource and account availability.
- Confidence and evidence freshness.

Hard eligibility failures must be reported separately from weighted suitability. A high score cannot offset a rights, policy, authorization, or technical blocker.

### 4.5 DistributionPackage

A `DistributionPackage` binds a particular content version to one channel/account context.

It may contain:

- Canonical asset reference and hash.
- Channel-specific derivative reference, if required.
- Title, caption, description, tags, and metadata.
- Thumbnail/cover reference.
- Accessibility text, captions, and transcript.
- Disclosure and attribution.
- CTA and destination.
- Channel profile version.
- Account reference.
- Validation results.
- Intended schedule and expiry.
- Content lineage and approval references.

Changes to a material field create a new package version and may invalidate prior approval.

## 5. Channel intelligence and selection

The channel recommendation workflow:

1. Identify the content asset, version, studio, and intended audience.
2. Load current channel profiles and authorized account capabilities.
3. Apply hard eligibility gates for rights, policy, format, privacy, account access, and technical compatibility.
4. Assess audience and editorial fit.
5. Evaluate channel-specific adaptation effort and expected value.
6. Consider portfolio balance and existing distribution commitments.
7. Estimate resource requirements within the approved envelope.
8. Produce a recommendation with evidence, confidence, and rationale.
9. Route uncertain or high-impact choices for human review.

Recommendations should explain:

- Why the channel is suitable.
- Which audience need it serves.
- What adaptation is required.
- What evidence supports the recommendation.
- What assumptions and uncertainties remain.
- What the estimated effort/resource impact is.
- Which other channels were excluded and why, where useful.

Do not assume the largest platform or highest historical view count is automatically the best channel.

## 6. Platform adaptation and packaging

Platform adaptation may include:

- Title/headline and caption changes.
- Description and metadata.
- Thumbnail/cover and preview.
- Aspect ratio, dimensions, duration, or encoding changes.
- Subtitle, transcript, alt-text, and accessibility adjustments.
- Hashtag/tag selection where supported.
- Disclosure, attribution, and source references.
- CTA and link destination.
- Platform-specific content warnings or labels.

Adaptation must preserve the factual meaning and editorial intent of the canonical asset. If adaptation introduces a new factual claim, it must be independently verified and linked to evidence.

The package must be validated against the exact version of the channel profile and the selected account's permissions.

## 7. Scheduling and calendar intelligence

### 7.1 ScheduleProposal

A schedule proposal includes:

- Distribution package and version.
- Channel/account.
- Proposed date/time and timezone.
- Timing rationale and evidence.
- Dependencies and conflicts.
- Campaign/portfolio context.
- Expiry or review deadline.
- Resource and rate-limit considerations.
- Required approvals and policy version.

Recommended posting times are estimates based on available evidence, not guarantees of performance.

### 7.2 Schedule states

Suggested states:

`PROPOSED` → `VALIDATED` → `AWAITING_AUTHORIZATION` → `AUTHORIZED` → `SCHEDULED`

Alternative states:

`REJECTED`, `EXPIRED`, `CANCELLED`, `PAUSED`, `BLOCKED`, `SUPERSEDED`, `EXECUTION_FAILED`.

A proposed or validated schedule is not an authorized schedule. A schedule may be authorized for a defined account, asset version, time window, and operation only.

### 7.3 Calendar coordination

The calendar should expose:

- Planned and scheduled content.
- Channel and studio.
- Asset/package version.
- Approval and authorization state.
- Dependencies and campaign grouping.
- Conflicts, capacity, and rate-limit warnings.
- Publication outcome and reconciliation status.

Calendar visibility must distinguish an idea, recommendation, pending schedule, authorized schedule, and confirmed publication.

## 8. Publishing governance and authorization

### 8.1 Separate authorization boundary

Every external upload or publish operation must pass through a centralized authorization boundary.

The boundary validates:

1. Current emergency pause and policy status.
2. Workspace, brand, studio, and channel scope.
3. Exact asset and package versions.
4. Required QA outcomes and hard blockers.
5. Rights clearance and permitted use.
6. Disclosure, privacy, and platform compliance.
7. Human approval requirements and approval provenance.
8. Account connection, scopes, and credential validity.
9. Schedule window, duplicate checks, and idempotency key.
10. Resource and rate-limit constraints.
11. Publishing policy eligibility and action limits.

Adapters must not offer a bypass path. Direct API calls, scripts, manual retry tools, or alternative workers must enforce the same centralized authorization contract.

### 8.2 Current autonomy status

Autonomous public publishing is **disabled pending a separate explicit owner-approved publishing policy**.

The previously discussed conditional automatic publishing approach is a proposal, not an activated policy. This contract does not enable it.

Until that separate policy is approved:

- Agents may research channel suitability.
- Agents may prepare and validate packages.
- Agents may propose schedules and prepare authorization requests.
- Agents may monitor already published content within authorized access.
- Agents may not independently publish, make public, or expand publication permissions.
- Human silence or unavailability never counts as approval.

### 8.3 Future conditional automation

If a separate policy is approved in the future, it must define:

- Eligible formats, channels, and account scopes.
- Content and risk eligibility.
- Mandatory QA and rights gates.
- Human approval exceptions.
- Per-channel frequency and volume limits.
- Schedule windows and expiry.
- Retry/reconciliation behavior.
- Emergency pause and correction procedure.
- Policy version and audit requirements.

Long-form content is not assumed eligible for autonomous publishing. Any future eligibility must be explicitly specified.

### 8.4 Approval binding

Approval must bind to:

- Exact asset hash/version.
- Exact distribution package version.
- Channel and account.
- Operation type (upload, schedule, publish, update, delete, or other).
- Intended time window.
- Policy version.
- Approver identity and timestamp.

A material change invalidates the affected approval and requires revalidation.

## 9. Upload, publish, and reconciliation

### 9.1 Distinct execution stages

Do not collapse these stages:

1. Package validated.
2. Upload requested.
3. Upload initiated.
4. Upload confirmed by platform.
5. Publication requested or scheduled.
6. Publication confirmed by platform.
7. Public visibility independently verified where possible.
8. Post-publication monitoring active.

An upload may remain private, unlisted, processing, scheduled, rejected, or otherwise not publicly visible. Report the actual confirmed platform state, not the intended state.

### 9.2 PublishOperation

A `PublishOperation` records:

- Operation ID and idempotency key.
- Distribution package and exact version.
- Channel/account and operation type.
- Authorization decision and policy version.
- Request/response metadata, safely redacted.
- External platform operation/content ID.
- Start/completion timestamps.
- Confirmed platform state.
- Retry/reconciliation status.
- Error classification.
- Actor and worker identity.

Never store access tokens or secrets in ordinary operation logs.

### 9.3 Uncertain outcomes

If a request times out or the response is lost:

- Mark the operation `RECONCILIATION_REQUIRED`.
- Query the platform using supported identifiers or idempotency mechanisms.
- Check whether the upload/publication already exists.
- Record the confirmed state.
- Retry only after determining that the prior side effect did not occur and policy still authorizes the retry.

Never blindly retry an uncertain publish operation. Duplicate public posts are a material failure.

## 10. Post-publication monitoring

A `PublicationRecord` tracks the confirmed platform object and its lifecycle.

Monitor, where permitted and available:

- Platform processing and visibility state.
- Publication URL/ID.
- Content availability and removal.
- Platform warnings or moderation notices.
- Caption, thumbnail, metadata, and link correctness.
- Disclosure and attribution presentation.
- Performance metrics and reporting windows.
- Comments/community signals only within authorized scope.
- Corrections, takedowns, and owner interventions.

Monitoring cadence must respect platform limits, approved resource budgets, and user notification preferences.

If an asset, source claim, or rights status is invalidated after publication, create an impact assessment and escalation. The system may prepare correction, restriction, or takedown recommendations, but must not exceed its explicit authority.

## 11. Community and audience interaction

Where authorized platform capabilities exist, the system may:

- Classify and summarize audience feedback.
- Identify recurring questions and themes.
- Draft suggested responses.
- Surface support or moderation priorities.
- Detect potential safety, privacy, or reputational escalation.
- Prepare moderation recommendations.

Broad autonomous community management remains bounded by explicit platform permissions and policy.

Escalate legal, financial, contractual, sensitive reputational, safety, privacy, harassment, or other high-impact matters. Agents must not make binding commitments, disclose private information, impersonate a human, or exceed approved response templates and authority.

Community actions must be rate-limited, logged, reversible where possible, and subject to emergency pause.

## 12. Analytics and attribution handoff

Distribution events and platform metrics feed the shared Analytics and Learning capabilities.

Every metric should identify:

- Platform/channel and account scope.
- Content and package version.
- Metric definition and platform schema/version.
- Reporting window and timezone.
- Collection timestamp.
- Value and unit.
- Data provenance: platform-reported, observed, estimated, or forecast.
- Completeness and known limitations.

Avoid comparing metrics with incompatible definitions or reporting windows. Attribution must distinguish direct evidence from inferred contribution.

Distribution Intelligence provides context for learning but does not independently declare causation from correlation.

## 13. Correction, takedown, and incident response

A distribution incident may be triggered by:

- Factual error or invalidated claim.
- Rights or licensing dispute.
- Privacy/security issue.
- Platform policy violation.
- Incorrect disclosure or attribution.
- Wrong asset/account/channel.
- Defective or misleading package.
- Unauthorized publication.
- Compromised account or credential.

Required process:

1. Record incident and affected publication references.
2. Preserve evidence and operation logs.
3. Assess severity, scope, and ongoing harm.
4. Pause affected queued operations where authorized.
5. Revoke compromised credentials or isolate affected integration when authorized.
6. Prepare correction, restriction, or takedown actions.
7. Obtain required human authorization for external actions.
8. Verify platform outcome.
9. Record remediation and lessons learned.
10. Review affected derivatives and related workflows.

Emergency controls must be available at global, workspace, brand, studio, agent, integration, channel, and publishing-only scopes.

## 14. Lifecycle and state model

Suggested distribution package lifecycle:

`DRAFT` → `VALIDATING` → `VALIDATED` → `READY_FOR_REVIEW` → `APPROVED_FOR_AUTHORIZATION` → `ARCHIVED` / `SUPERSEDED`

Suggested publication lifecycle:

`NOT_REQUESTED` → `AUTHORIZATION_PENDING` → `AUTHORIZED` → `UPLOAD_PENDING` → `UPLOADING` → `UPLOAD_CONFIRMED` → `PUBLISH_PENDING` → `SCHEDULED` / `PUBLISHING` → `PUBLISHED_CONFIRMED`

Alternative states:

`PRIVATE`, `UNLISTED`, `PROCESSING`, `REJECTED`, `FAILED`, `RECONCILIATION_REQUIRED`, `REMOVED`, `RESTRICTED`, `CANCELLED`.

The exact platform state must be preserved separately from NEXTDECODE's internal workflow state.

## 15. APIs and events

Illustrative versioned interfaces:

- `GET /v1/channels/profiles`
- `POST /v1/channels/accounts/verify`
- `POST /v1/distribution/assessments`
- `POST /v1/distribution/strategies`
- `POST /v1/distribution/packages`
- `POST /v1/distribution/packages/{package_id}/validate`
- `POST /v1/distribution/schedules/propose`
- `POST /v1/distribution/schedules/{schedule_id}/authorize`
- `POST /v1/publishing/authorize`
- `POST /v1/publishing/operations`
- `POST /v1/publishing/operations/{operation_id}/reconcile`
- `GET /v1/publications/{publication_id}`
- `POST /v1/publications/{publication_id}/metrics`
- `POST /v1/distribution/incidents`

Illustrative events:

- `distribution.suitability.assessed.v1`
- `distribution.strategy.created.v1`
- `distribution.package.created.v1`
- `distribution.package.validated.v1`
- `distribution.schedule.proposed.v1`
- `distribution.schedule.authorized.v1`
- `publishing.authorization.denied.v1`
- `publishing.operation.started.v1`
- `publishing.operation.reconciliation_required.v1`
- `publishing.upload.confirmed.v1`
- `publishing.publication.confirmed.v1`
- `publication.visibility.changed.v1`
- `publication.metrics.collected.v1`
- `publication.incident.created.v1`
- `distribution.emergency_pause.activated.v1`

Events require durable delivery, schema versioning, idempotency, workspace scope, actor provenance, and policy context. Events do not themselves authorize an external operation.

## 16. Acceptance criteria

The contract is ready for implementation design when:

1. Channel profiles are versioned and reflect verified platform capabilities.
2. Channel accounts have explicit scopes, ownership, health, expiry, and revocation.
3. Suitability hard gates are separate from weighted recommendations.
4. Platform-specific packages preserve canonical asset lineage.
5. Scheduling proposals are distinct from authorized schedules.
6. Every external operation passes through centralized governance.
7. Approval binds to exact asset/package versions, account, operation, and policy.
8. Autonomous public publishing remains disabled until a separate owner-approved policy exists.
9. Human silence never counts as approval.
10. Upload, publication, and public visibility are represented as distinct confirmed states.
11. Uncertain external operations are reconciled before retry.
12. No adapter or direct execution path bypasses central authorization.
13. Monitoring and analytics preserve metric provenance and reporting windows.
14. Community actions remain within explicit permission and escalation boundaries.
15. Corrections and takedowns have evidence preservation and authorization controls.
16. Emergency pause and credential revocation can stop affected operations.
17. Distribution outcomes feed shared learning without overstating causal conclusions.

## 17. Open implementation details

Not fixed by this contract:

- Initial platform/channel allowlist.
- Platform-specific API scopes and verification procedures.
- Exact channel suitability weights and thresholds.
- Channel-specific metadata and media schemas.
- Scheduling and calendar integration.
- Platform metric registry and collection cadence.
- Notification thresholds and escalation routing.
- Future conditional publishing eligibility and limits.
- Community response templates and moderation thresholds.
- Correction/takedown approval matrix.
- Platform-specific retention and data residency details.

These require technical validation and, where permissions, external side effects, spending, or public publishing are involved, explicit owner approval. No platform, account, credential, policy, or publishing capability is activated by this contract.

## 18. Decision traceability

This contract operationalizes accepted decisions covering:

- Distribution Intelligence as a shared capability.
- Channel-specific adaptation and audience fit.
- Unified analytics and attribution with observed/platform-reported/estimated/forecast distinctions.
- Recommendations and scheduling separated from publishing authorization.
- Centralized policy enforcement across adapters.
- Publishing autonomy disabled pending explicit owner policy approval.
- Silence never counts as approval.
- Conditional automation discussed only as a future policy option, not an active setting.
- Risk-based human oversight for community management and sensitive decisions.
- Commercial authority restrictions and no unauthorized commitments.
- Emergency pause, audit, revocation, and incident response.
- Content lineage, independent derivative QA, and rights-based asset governance.

It is subordinate to the Master Blueprint, System Architecture Master Reference, Shared Data Model & Content Graph, Agent Contracts & Orchestration, Content Quality/Rights/Governance Intelligence, Studio Integration APIs & Artifact Management, Hybrid Deployment/Security/Monitoring contract, and owner-approved decision register. Conflicts must be recorded and reconciled rather than silently resolved by weakening a higher-priority rule.

---

**End of Contract 12 — Distribution, Channel & Publishing Intelligence Model 1.0**
