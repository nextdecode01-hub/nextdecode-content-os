# NEXTDECODE Shared Intelligence Core Contract 03
## Brand & Editorial Intelligence Model
**Version:** 1.0  
**Status:** Working architecture contract — documentation only  
**Scope:** Shared Intelligence Core; parent brand, brand instances, and specialized studios  
**Authority:** Derived from accepted Creator Success Intelligence decisions and the architecture baseline. This document does not authorize repository changes, external integrations, production execution, spending, or publishing.

---

## 1. Purpose

Define how NEXTDECODE's brand identity and each specialized studio's editorial identity are represented, governed, versioned, applied, and evaluated across the content lifecycle.

The model must preserve one recognizable parent brand while allowing each studio to develop a distinct editorial personality and format-native execution style. It must make brand guidance usable by research, strategy, creative, production, quality, distribution, and learning systems without turning subjective preferences into unsupported facts or allowing an agent to rewrite approved identity rules.

## 2. Core principles

1. **One parent brand, distinct studio identities:** every studio operates within the approved parent-brand promise and principles while retaining its own editorial and format-specific identity.
2. **Identity is structured and versioned:** brand rules are explicit records with owners, scope, status, effective dates, and version history.
3. **Principles outrank stylistic preferences:** accuracy, audience trust, rights, privacy, and approved editorial principles take precedence over engagement or stylistic optimization.
4. **Guidance is contextual:** a rule may apply globally, to a brand, to a studio, to a format, or to a channel. Scope must be explicit.
5. **Creative freedom within boundaries:** AI may propose and develop creative directions within approved identity and editorial policies; sensitive editorial authority remains human-controlled.
6. **Consistency is not sameness:** studios may vary tone, pacing, narrative structure, and visual language while remaining recognizably part of the parent brand.
7. **Evidence-backed learning:** performance can inform recommendations, but a small or biased sample cannot silently rewrite brand identity.
8. **No hidden commercial influence:** sponsorship or monetization considerations cannot silently change factual conclusions, editorial standards, or audience promises.
9. **Recommendations do not grant authority:** a brand recommendation, compliance result, or creative brief does not authorize publishing or a commercial commitment.
10. **Owner authority:** approved brand principles and governance policies cannot be changed autonomously by agents.

## 3. Brand hierarchy and entities

### 3.1 WorkspaceBrand

Represents a brand owned and governed within a workspace.

Required fields:

- `brand_id`: UUIDv7.
- `workspace_id`: UUIDv7.
- `brand_name`: display name.
- `brand_purpose`: concise statement of the brand's purpose.
- `brand_promise`: what the audience can reasonably expect.
- `positioning_statement`: audience, domain, and distinctive value.
- `primary_audiences`: references to approved audience personas/segments.
- `brand_pillars`: versioned references to editorial/content pillars.
- `brand_principles`: references to approved principles.
- `identity_status`: draft, active, deprecated, or archived.
- `current_identity_version`: immutable version reference.
- `owner_actor_ref`: accountable owner.
- `created_at`, `updated_at`, and `schema_version`.

The initial workspace may have one brand, NEXTDECODE. The architecture remains capable of supporting additional brands later; this does not authorize their creation or any multi-brand rollout.

### 3.2 BrandIdentityVersion

An immutable snapshot of a brand's approved identity at a point in time.

It may contain:

- Purpose, promise, positioning, and audience expectations.
- Brand pillars and approved subject domains.
- Editorial principles and non-negotiable standards.
- Parent-brand voice attributes and language guidance.
- Visual identity references and asset-library links.
- Accuracy, sourcing, transparency, and correction principles.
- Audience trust commitments.
- Approved and restricted content treatments.
- Version number, author, approver, effective date, and change rationale.

Changes create a new version. Historical content retains the identity version used at the time of its creation and review.

### 3.3 StudioIdentity

Represents a specialized studio's editorial and execution identity under a parent brand.

Required fields:

- `studio_id`: UUIDv7.
- `workspace_id`, `brand_id`: ownership scope.
- `studio_name`: display name.
- `studio_purpose`: role in the overall brand portfolio.
- `editorial_focus`: subject and audience focus.
- `editorial_personality`: distinctive editorial character.
- `voice_profile_ref`: versioned voice profile.
- `visual_language_ref`: versioned visual profile.
- `format_profile_refs`: supported format profiles.
- `parent_brand_identity_version`: required parent identity version.
- `studio_identity_version`: immutable version.
- `status`, owner, timestamps, and schema version.

A studio cannot redefine or contradict parent-brand non-negotiable principles. Studio-specific guidance may specialize, not weaken, the parent rules.

### 3.4 EditorialPrinciple

A durable rule or commitment governing editorial decisions.

Examples of principle categories:

- Accuracy and evidence.
- Audience trust and usefulness.
- Independence and conflict-of-interest handling.
- Privacy and consent.
- Rights and attribution.
- Transparency and corrections.
- Respectful treatment of people and communities.
- Separation of fact, analysis, opinion, and speculation.

Each principle records:

- Stable ID and version.
- Scope and priority.
- Normative statement.
- Rationale and examples.
- Severity if violated.
- Required evidence or validation method.
- Owner and approval record.
- Effective date and supersession history.

Principles must distinguish mandatory requirements from guidance and optional preferences.

### 3.5 BrandPillar

Represents an approved subject/value area used to guide the brand portfolio.

Fields include:

- Pillar ID and version.
- Name and description.
- Audience value served.
- Included and excluded subject boundaries.
- Related audience segments.
- Related studios and formats.
- Strategic priority, if approved.
- Evidence and review date.

Pillars are planning context, not a claim that every topic within the pillar is suitable.

## 4. Identity dimensions

The model separates the following dimensions so that an AI system does not collapse the entire brand into a single vague style prompt.

| Dimension | Parent brand responsibility | Studio responsibility |
|---|---|---|
| Purpose and promise | Defines overall audience commitment | Explains the studio's contribution |
| Positioning | Defines overall market/editorial identity | Defines a distinct role or angle |
| Audience expectations | Sets trust and value commitments | Defines audience context and format needs |
| Editorial principles | Sets non-negotiable standards | Applies them to studio-specific work |
| Voice | Sets recognizable parent voice boundaries | Defines studio tone, vocabulary, pacing, and narration |
| Visual identity | Sets shared recognizable visual elements | Defines format-native visual language |
| Storytelling | Sets broad narrative values | Defines structure, rhythm, depth, and conventions |
| Accuracy and sourcing | Sets evidence and correction commitments | Defines practical research and citation treatment |
| Transparency | Sets disclosure and correction standards | Applies them to each format/channel |
| Commercial integrity | Sets independence and trust boundaries | Keeps commercial content appropriately separated |

## 5. Voice profile contract

A `VoiceProfile` should be structured rather than stored only as a long free-text prompt.

Recommended fields:

- `voice_profile_id`, version, scope, and status.
- Desired attributes (e.g., clear, curious, analytical, accessible).
- Attributes to avoid (e.g., exaggerated certainty, empty hype, manipulative urgency).
- Formality and conversational range.
- Sentence complexity and terminology expectations.
- Use of examples, analogies, and narrative devices.
- Humor and emotional tone boundaries.
- Language and localization rules.
- Narration and pronunciation guidance where applicable.
- Approved sample passages and counterexamples.
- Evaluation rubric and known limitations.
- Owner and approval history.

The system may generate a task-specific voice brief by combining the active parent and studio profiles. The generated brief must retain the source profile versions and must not invent new identity rules.

## 6. Visual identity contract

A `VisualIdentityProfile` represents approved visual guidance and references.

Recommended fields:

- Profile ID, version, scope, and status.
- Logo/mark references and usage constraints.
- Color tokens and contrast/accessibility requirements.
- Typography references and hierarchy.
- Composition, framing, spacing, and motion principles.
- Illustration, photography, footage, and graphic treatment guidance.
- Thumbnail and title-card principles.
- Subtitle/caption conventions.
- Approved asset references and licence/rights metadata.
- Disallowed treatments and examples.
- Format-specific overrides.
- Review and approval provenance.

Binary assets remain in the artifact/object-storage system; the identity profile stores references, metadata, version, and permitted-use context. A visual reference is not automatically a licence to reuse the asset.

## 7. Format and channel profiles

Brand identity must be adapted to the requirements of a format and distribution channel.

A `FormatProfile` defines:

- Format type and intended audience experience.
- Structural conventions and duration/length ranges, where approved.
- Narrative depth and pacing.
- Visual/audio/subtitle requirements.
- Accessibility requirements.
- Format-specific quality checks.
- Parent and studio identity versions required.

A `ChannelProfile` defines:

- Platform/channel constraints and current policy references.
- Metadata and packaging requirements.
- Disclosure and attribution requirements.
- Technical delivery specifications.
- Audience interaction expectations.
- Channel-specific performance metrics and measurement caveats.

Channel requirements must be refreshed from authorized, reliable sources. A stale profile cannot be treated as current platform policy. Format or channel compliance does not imply publishing authorization.

## 8. Editorial policy and decision hierarchy

When rules conflict, apply the centralized policy-precedence framework. This contract proposes the following domain ordering for editorial interpretation, subject to the authoritative governance precedence contract:

1. Applicable law, safety, privacy, rights, and platform requirements.
2. Owner-approved governance and non-negotiable editorial principles.
3. Active parent-brand identity.
4. Active studio identity.
5. Format and channel requirements.
6. Task-specific creative brief and campaign guidance.
7. Performance-derived recommendations and stylistic preferences.

A lower-level instruction cannot weaken or override a higher-level requirement. Any unresolved conflict becomes `REVIEW_REQUIRED`; the agent must not silently choose the more permissive interpretation.

## 9. Brand context assembly

Before research, creative development, production, or distribution, the orchestrator should assemble a scoped `BrandContextPackage`.

It should include:

- Workspace and brand identifiers.
- Active parent-brand identity version.
- Active studio identity version, if applicable.
- Relevant brand pillars and audience context.
- Applicable editorial principles and policy references.
- Voice and visual profile versions.
- Format and channel profile versions.
- Task-specific approved brief.
- Applicable rights, disclosure, and transparency requirements.
- Known conflicts, missing profiles, and review flags.

The package must be minimal and task-scoped. Restricted information should not be copied into contexts for agents that do not need it. The package should be immutable for the task or carry a content hash so that later reviews can reconstruct the context used.

## 10. Brand alignment assessment

A `BrandAlignmentAssessment` records how a proposed idea, script, visual treatment, finished artifact, or channel package relates to approved identity.

Assessment dimensions may include:

- Purpose and audience-promise alignment.
- Pillar and positioning relevance.
- Voice alignment.
- Visual identity alignment.
- Editorial-principle compliance.
- Audience trust and usefulness.
- Transparency and disclosure.
- Commercial-integrity separation.
- Format/channel fit.

Each finding includes:

- Finding ID and severity.
- Affected artifact/section/asset reference.
- Applicable identity/policy version.
- Evidence or example.
- Explanation and suggested correction.
- Whether it is a hard blocker, review item, or advisory note.

Brand alignment is one dimension of quality; it must not replace factual, rights, privacy, safety, or production QA. A strong brand-alignment score cannot override a hard blocker.

## 11. Creative autonomy and brand evolution

AI may:

- Suggest new creative directions within approved identity.
- Generate scripts, storyboards, visual directions, and packaging proposals.
- Identify repeated brand inconsistencies.
- Recommend voice or visual profile refinements.
- Analyze performance evidence and propose controlled experiments.
- Identify audience expectations that may be changing.

AI may not:

- Change approved parent-brand purpose, promise, positioning, or non-negotiable principles.
- Weaken editorial, accuracy, privacy, rights, or transparency standards.
- Promote a temporary performance pattern into permanent brand identity without validation and approval.
- Treat sponsorship or affiliate value as authority to change editorial conclusions.
- Approve its own proposed identity changes.

Brand changes follow a governed lifecycle:

`PROPOSED` → `IMPACT_ASSESSED` → `TESTED` (where appropriate) → `OWNER_REVIEW` → `APPROVED` → `EFFECTIVE` → `SUPERSEDED`

An approved change creates a new immutable identity version. Historical artifacts keep their original identity references.

## 12. Performance learning and identity protection

Performance Intelligence may compare content against identity versions and recommend experiments. It must distinguish:

- Stable brand commitments.
- Studio-specific editorial conventions.
- Format/channel adaptations.
- Experimental treatments.
- Temporary campaign instructions.

A performance result must not automatically modify a brand profile. Recommendations should include sample size, observation window, audience/platform scope, uncertainty, and possible confounders. Validated learning may inform a proposed profile change, but owner approval remains required for approved identity and principle changes.

## 13. Rights, assets, and provenance

Every logo, font, image, video, music, template, voice, and other brand asset must link to the centralized asset and rights records.

Brand identity records must not imply ownership or reuse permission. The system must retain:

- Asset owner/licensor.
- Licence or permission basis.
- Permitted media, channels, territories, duration, and commercial uses.
- Attribution and disclosure requirements.
- Restrictions and expiry.
- Source/provenance and version.
- Rights assessment status.

Unknown or unverified rights remain uncleared under the central rights policy. Brand alignment cannot turn an uncleared asset into an eligible asset.

## 14. APIs and events

Illustrative versioned interfaces:

- `GET /v1/brands/{brand_id}/identity/current`
- `GET /v1/brands/{brand_id}/identity/versions`
- `POST /v1/brands/{brand_id}/identity/proposals`
- `POST /v1/studios/{studio_id}/identity/proposals`
- `GET /v1/studios/{studio_id}/identity/current`
- `POST /v1/brand-context/assemble`
- `POST /v1/brand-alignment/assessments`
- `GET /v1/brand-alignment/assessments/{assessment_id}`

Illustrative events:

- `brand.identity.proposed.v1`
- `brand.identity.approved.v1`
- `brand.identity.activated.v1`
- `brand.identity.superseded.v1`
- `studio.identity.updated.v1`
- `brand.context.assembled.v1`
- `brand.alignment.assessed.v1`
- `brand.alignment.review_required.v1`

Events must use durable delivery, schema versioning, idempotency, actor provenance, and workspace/brand scope. An identity-change event does not authorize unrelated downstream actions.

## 15. Acceptance criteria

The contract is ready for implementation design when:

1. Parent brand and studio identities can be represented separately.
2. Studio identity cannot weaken parent-brand non-negotiable principles.
3. Identity versions are immutable and historical artifacts retain the versions used.
4. Voice and visual profiles are structured, versioned, and scoped.
5. Format and channel profiles can adapt execution without silently changing parent identity.
6. A task-scoped BrandContextPackage can be reconstructed for audit.
7. Brand alignment findings reference the exact policy/profile versions applied.
8. Brand alignment cannot override factual, rights, privacy, safety, or production blockers.
9. AI can propose but cannot autonomously approve changes to owner-approved identity.
10. Performance learning includes scope, sample size, uncertainty, and observation window.
11. Assets link to centralized rights/provenance records.
12. Workspace and brand access boundaries are enforced for agents and workers.
13. Consequential changes and assessments are auditable and explainable.
14. A missing or conflicting identity rule routes to review instead of permissive guessing.

## 16. Open implementation details

Not fixed by this contract:

- Exact initial NEXTDECODE parent-brand identity wording and approved brand-pillar taxonomy.
- Exact studio list and studio-specific editorial identities.
- Voice attribute scales and automated evaluation rubrics.
- Visual token values and asset-library organization.
- Format/channel profile schemas and update cadence.
- Brand-alignment scoring thresholds.
- Identity proposal approval workflow details.
- Database schemas, API payloads, and event payloads.
- Retention periods and implementation-specific access-control mechanics.

These require owner review or evidence-based technical design. This contract does not assume that any proposed studio identity or brand rule has already been approved.

## 17. Decision traceability

This contract operationalizes the accepted decisions covering:

- Shared parent Brand Intelligence with studio-specific editorial identities.
- Bounded creative autonomy with human authority over sensitive editorial decisions.
- Evidence-based performance learning and controlled experimentation.
- Shared Intelligence Core with specialized studios.
- Cross-studio collaboration while preserving studio ownership and identity.
- Privacy-first workspace and brand isolation.
- Rights-aware asset reuse and centralized governance.
- Risk-based AI transparency.
- Owner-centric governance and versioned policy change management.
- Explainability and auditability of consequential decisions.

It is subordinate to the Master Blueprint, System Architecture Master Reference, centralized governance contracts, and owner-approved decision register. Conflicts must be recorded and reconciled; they must not be silently resolved by weakening a higher-priority rule.

---

**End of Contract 03 — Brand & Editorial Intelligence Model 1.0**
