# NEXTDECODE — Shared Intelligence Core
## Contract 01: Audience & Identity Context Model
### Working Specification 1.0

**Document status:** Proposed domain contract — owner review through the standing delegation rule  
**Date:** 31 October 2026  
**Parent architecture:** NEXTDECODE Three-Layer Product Architecture — Working Baseline 1.0  
**Scope:** Audience concepts, platform identity boundaries, segmentation, audience insights, provenance, privacy and cross-studio reuse  
**Implementation status:** Not authorized

---

## 1. Purpose

The Audience & Identity Context Model gives NEXTDECODE a consistent way to represent:

- The audiences the brand intends to serve.
- Evidence-backed observations about audience needs and behavior.
- Strategic personas and observed or emerging segments.
- Platform-scoped audience identifiers and metrics.
- Relationships between audience segments across platforms without assuming that identities match.
- The permitted use, provenance, confidence and retention of audience information.

This is a shared intelligence contract. It is not a mandate to collect new personal data, connect new services, scrape platforms, or identify individuals.

## 2. Design principles

1. **Audience-first, not identity-first.** The system should understand needs and groups without requiring identification of individual people.
2. **No assumed cross-platform identity match.** Similar usernames, behavior or demographics do not prove that two platform accounts belong to the same person.
3. **Evidence before assertion.** Every material audience insight must retain its source, observation window, method and confidence.
4. **Strategic and observed segments are different.** A human-defined persona is not the same thing as a segment inferred from observed evidence.
5. **Privacy by design.** Minimize personal data, enforce purpose limitation, respect permissions and consent where applicable, and apply retention/deletion rules.
6. **Shared insight, scoped access.** Studios may reuse eligible audience insights without receiving unnecessary raw or restricted data.
7. **No unsupported representativeness.** Comments, polls, analytics samples and platform audiences are biased or incomplete unless evidence establishes otherwise.
8. **No automatic sensitive profiling.** Do not infer or build sensitive personal profiles or cross-platform identity graphs.
9. **Time matters.** Audience segments and insights can change; records must preserve observation periods and version history.
10. **Uncertainty remains visible.** Conflicting, incomplete or stale evidence must not be presented as certainty.

## 3. Audience model

### 3.1 Audience

An **Audience** is a conceptual group of people or organizations that a brand or studio intends to serve or understand.

An Audience record is not a person record and must not contain a list of identifiable individuals by default.

Proposed fields:

| Field | Meaning |
|---|---|
| `audience_id` | Canonical UUIDv7 identifier |
| `workspace_id` | Owning workspace |
| `brand_id` | Brand context, where applicable |
| `name` | Human-readable audience name |
| `description` | What the audience represents |
| `purpose` | Why the audience definition exists |
| `status` | Draft, active, archived |
| `created_at` / `updated_at` | Audit timestamps |
| `version` | Immutable definition version |

### 3.2 Strategic Persona

A **Strategic Persona** is a human-defined planning model describing an intended audience archetype, its needs, context, goals, questions and constraints.

It is a planning abstraction, not a verified description of every person in a population.

Proposed fields:

- `persona_id`
- `audience_id`
- `name`
- `needs_and_goals`
- `questions_and_pain_points`
- `knowledge_context`
- `content_preferences` (only where supported and relevant)
- `assumptions`
- `owner_or_author`
- `reviewed_at`
- `version`

Assumptions must be explicitly labelled. Personas must not be used to infer sensitive traits about real individuals.

### 3.3 Audience Segment

An **Audience Segment** is a scoped grouping used for analysis or planning.

The model supports three segment classes, consistent with the selected hybrid segmentation approach:

1. **Strategic segment:** Defined deliberately by a human for planning.
2. **Observed segment:** Derived from authorized, aggregated or otherwise permitted evidence.
3. **Emerging segment:** A provisional pattern detected in evidence and awaiting validation.

Proposed fields:

| Field | Meaning |
|---|---|
| `segment_id` | Canonical UUIDv7 |
| `audience_id` | Parent audience |
| `segment_type` | Strategic, observed, emerging |
| `name` | Segment label |
| `definition` | Inclusion logic or qualitative description |
| `scope` | Workspace, brand, studio, platform or dataset scope |
| `valid_from` / `valid_to` | Period for which the definition applies |
| `evidence_refs` | Supporting evidence references |
| `confidence` | Confidence with rationale, where applicable |
| `status` | Proposed, active, under_review, retired |
| `version` | Immutable version |

Observed and emerging segments must record the method and evidence used to derive them. A segment must not silently become a verified fact merely because an algorithm created it.

## 4. Platform audience and identity boundaries

### 4.1 Platform Audience Snapshot

A **Platform Audience Snapshot** stores a time-bounded, platform-scoped view of audience information made available through an authorized source.

Examples may include aggregate follower counts, audience geography summaries, engagement summaries or platform-provided audience categories, where access and use are permitted.

Proposed fields:

- `snapshot_id`
- `workspace_id`
- `brand_id`
- `platform`
- `channel_id` or authorized channel reference
- `source_connection_ref` (optional; never a credential)
- `metric_or_attribute`
- `value`
- `unit`
- `observed_at`
- `period_start` / `period_end`
- `source_type` (platform-reported, first-party, public, authorized external)
- `permission_scope_ref`
- `data_classification`
- `freshness_status`
- `provenance_ref`

Do not store access tokens, passwords or secrets in audience records.

### 4.2 Platform Identity Reference

A **Platform Identity Reference** represents an account or channel identifier within one platform, only when there is a valid purpose and authorization to retain it.

It is not a universal person identity.

Proposed fields:

- `platform_identity_ref_id`
- `platform`
- `platform_account_or_channel_id` (minimized or pseudonymized where possible)
- `workspace_id` and applicable brand scope
- `purpose`
- `source_and_permission_ref`
- `classification`
- `retention_policy_ref`
- `created_at`

### 4.3 Cross-platform relationship

Cross-platform audience relationships must be represented as relationships between audiences, segments or aggregate observations—not as an assumed person-to-person identity match.

A proposed relationship record may include:

- `relationship_id`
- `source_segment_id`
- `target_segment_id`
- `relationship_type` (overlap hypothesis, shared interest, complementary audience, migration signal)
- `evidence_refs`
- `confidence`
- `method`
- `valid_period`
- `review_status`

The system must not merge platform identities or assert that two accounts represent the same individual without a separately authorized, lawful and verified basis. The default is **no identity resolution**.

## 5. Audience Insight contract

An **Audience Insight** is a claim or observation about an audience, persona or segment.

Examples:
- A recurring question appears in a permitted set of comments.
- A particular topic receives stronger engagement in a defined observation window.
- A segment appears underserved by existing content.
- A newsletter survey indicates a stated preference among respondents.

Proposed fields:

| Field | Meaning |
|---|---|
| `insight_id` | Canonical UUIDv7 |
| `workspace_id` / `brand_id` | Ownership and brand scope |
| `subject_type` / `subject_id` | Audience, persona or segment |
| `insight_type` | Need, question, interest, behavior, preference, barrier, trend |
| `statement` | Concise insight |
| `evidence_refs` | Supporting evidence |
| `source_mix` | First-party, public, authorized external |
| `method` | How the insight was derived |
| `observation_window` | Start and end of evidence window |
| `confidence` | Calibrated value or qualitative level plus rationale |
| `limitations` | Sampling, bias, missingness and other caveats |
| `classification` | Public, Internal, Confidential, Restricted |
| `purpose` | Approved purpose for use |
| `valid_from` / `review_after` | Validity and review dates |
| `status` | Draft, validated, disputed, stale, retired |
| `version` | Immutable version |

Insights must distinguish:
- Verified observations.
- Platform-reported metrics.
- Survey or self-reported statements.
- Estimates.
- Hypotheses.
- Opinions or interpretations.

These categories must not be collapsed into a single confidence label.

## 6. Evidence and provenance requirements

Every material insight must link to evidence records or an auditable evidence package.

At minimum, provenance should identify:

- Source identity or source reference.
- Source type and access basis.
- Collection or observation time.
- Measurement period.
- Method of collection or analysis.
- Relevant transformations or aggregation.
- Known limitations and sampling bias.
- Permission and purpose scope.
- Data classification and retention policy.
- Confidence rationale and reviewer, if reviewed.

If evidence is contradictory, the insight should be marked disputed or qualified. If evidence is too weak, preserve it as a hypothesis rather than promoting it to validated audience knowledge.

The Audience model should reuse the shared Research & Evidence contracts; it must not create a duplicate claim-verification system.

## 7. Privacy, access and retention

The following are mandatory design constraints carried forward from the accepted privacy and data-governance decisions:

### 7.1 Data minimization
Collect and retain only the minimum information required for a defined audience-intelligence purpose.

### 7.2 Purpose limitation
Every dataset and insight must have a declared purpose. Reuse outside that purpose requires an applicable permission or authorization.

### 7.3 Classification
Use the shared classifications:
- Public
- Internal
- Confidential
- Restricted

### 7.4 Workspace and brand isolation
Audience data is isolated by workspace and applicable brand scope. Cross-workspace sharing is not automatic.

### 7.5 Consent and permissions
Respect source permissions, platform terms, applicable consent requirements and revocation. A connection being technically available does not itself authorize every use.

### 7.6 Retention and deletion
Audience records must inherit or reference lifecycle, retention, deletion and legal-hold policies. Deletion must propagate to eligible derived records where required, with auditable evidence.

### 7.7 Sensitive data
Do not build sensitive personal profiles or infer sensitive traits. Restrict personal-data profiling and cross-platform identity matching.

## 8. Cross-studio reuse contract

Studios may consume audience intelligence through scoped, versioned references.

A studio request should declare:

- Requesting workspace, brand and studio.
- Intended purpose.
- Required audience or segment scope.
- Minimum data needed.
- Required freshness.
- Permitted output type (aggregate insight, segment definition, report, etc.).

Default reusable output:
- Audience and segment definitions.
- Validated, appropriately classified insights.
- Evidence references or safe evidence summaries.
- Confidence and limitations.
- Applicable period and version.

Raw platform identity references and restricted source data are not exposed by default.

A studio must record which audience insight versions informed a brief, creative direction or distribution recommendation. This preserves lineage and allows later review if an insight becomes stale or is corrected.

## 9. Lifecycle and state model

Proposed lifecycle for an Audience Insight:

`DRAFT → VALIDATED → ACTIVE → STALE → RETIRED`

Additional transitions:
- `DRAFT → DISPUTED`
- `VALIDATED → DISPUTED`
- `ACTIVE → DISPUTED`
- `DISPUTED → VALIDATED` after review
- `STALE → ACTIVE` only after freshness review
- Any eligible state → `RETIRED`

These are proposed states and transitions, not a frozen implementation contract. Invalid transitions must be rejected and audited. Retired records remain available for historical lineage subject to retention and deletion rules.

Segments have their own lifecycle and versioning; changing a segment definition creates a new version rather than silently rewriting historical meaning.

## 10. API and event boundaries

The domain should expose versioned contracts rather than direct database access between modules.

Candidate operations:
- Create or update a strategic persona.
- Propose an audience segment.
- Record an audience snapshot.
- Create an audience insight with evidence references.
- Validate, dispute or retire an insight.
- Request scoped audience context for a studio.
- Record the audience context versions used by a content brief.

Candidate events:
- `audience.persona.versioned`
- `audience.segment.proposed`
- `audience.segment.activated`
- `audience.snapshot.recorded`
- `audience.insight.created`
- `audience.insight.validated`
- `audience.insight.disputed`
- `audience.insight.staled`
- `audience.insight.retired`
- `audience.context.accessed`

Events are notifications, not authoritative state. Consumers must be idempotent and respect workspace, brand, purpose and classification scopes.

## 11. Acceptance criteria

The contract is acceptable for detailed implementation planning only when the design can demonstrate:

1. Strategic, observed and emerging segments are distinguishable.
2. Every material insight has provenance, observation window, method and limitations.
3. Platform snapshots remain platform-scoped and time-bounded.
4. The default model does not merge identities across platforms.
5. Sensitive personal profiling is prohibited by default.
6. Workspace and brand isolation are enforced at the service boundary.
7. Cross-studio reuse returns only data authorized for the requesting purpose.
8. Stale, disputed and retired insights are not silently treated as current validated knowledge.
9. Changes preserve version history and lineage.
10. Retention, deletion and legal-hold controls apply to source and derived audience data.
11. Platform-reported metrics, estimates, hypotheses and verified observations remain distinguishable.
12. No new data source or service connection is activated by implementing this contract.

## 12. Open implementation details

These are deliberately not decided by this domain contract:

- Exact database tables and indexes.
- Exact confidence scale and calibration method.
- Segment minimum sample sizes and validation thresholds.
- Source-specific retention periods.
- Exact platform APIs and permitted scopes.
- Identity-reference pseudonymization technique.
- Event transport and API schema tooling.
- Which aggregate metrics are available from each connected platform.
- Any new data-source connection or collection workflow.

These details require technical evidence, applicable platform/legal review, or a later scoped owner decision. They must not be guessed.

## 13. Decision alignment

This contract is designed to implement the previously recorded direction for:

- Hybrid strategic, observed and emerging audience segmentation.
- First-party, public and authorized external sources with provenance and permissions.
- Privacy-first governance and workspace/brand isolation.
- No automatic cross-platform identity matching.
- Shared Intelligence Core with specialized studios.
- Evidence-based source trust and learning.
- Purpose-specific consent and customer data portability.
- Data sovereignty and auditable lifecycle controls.

This document does not restate the full 146-decision register and does not supersede it.

## 14. Authorization boundary

This is a documentation artifact only.

It does not authorize:
- Repository inspection or Git operations.
- Code, test or configuration changes.
- Dependency installation or environment changes.
- New platform connections, data collection or scraping.
- Cloud provisioning, paid services or deployment.
- Production generation, uploads or publishing.
- Changes to existing agent ownership.

---

**End of Contract 01 — Audience & Identity Context Model 1.0**
