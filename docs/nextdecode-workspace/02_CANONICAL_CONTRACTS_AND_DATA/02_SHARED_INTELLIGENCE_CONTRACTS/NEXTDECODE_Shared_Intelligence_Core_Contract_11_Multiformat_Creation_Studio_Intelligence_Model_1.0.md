# NEXTDECODE Shared Intelligence Core Contract 11
## Multiformat Creation & Studio Intelligence Model
**Version:** 1.0  
**Status:** Working architecture contract — documentation only  
**Scope:** Shared creation foundation, format adaptation, specialized studios, production handoff, content lineage, and studio-level learning  
**Authority:** Derived from accepted NEXTDECODE product architecture and Creator Success Intelligence decisions. This document does not authorize repository access or changes, provider connections, subscriptions, spending, deployments, production execution, or publishing.

---

## 1. Purpose

Define how NEXTDECODE turns a shared, evidence-backed content opportunity and research foundation into multiple independently designed content products.

The system must support multiple specialized studios and distribution formats without becoming a generic one-click repurposing machine. Each studio has its own editorial identity, audience context, storytelling conventions, production contract, quality requirements, and channel constraints.

A shared source of truth should reduce duplicated research and preserve evidence lineage. It must not force every format to use the same angle, script, structure, visuals, pacing, or call to action.

**Core rule:** One shared intelligence foundation; multiple independently authored format experiences; separate validation and authorization for every derivative.

## 2. Design principles

1. **Shared facts, distinct storytelling:** reuse verified evidence and knowledge, not necessarily the same narrative.
2. **Format-native creation:** each studio designs for its medium instead of mechanically resizing another format.
3. **Studio identity is explicit:** every output inherits parent-brand constraints and its studio-specific editorial identity.
4. **Audience-aware adaptation:** adapt framing and depth to the relevant audience segment without assuming cross-platform identities are the same people.
5. **Evidence lineage survives transformation:** factual claims in derivatives remain traceable to evidence and source versions.
6. **Independent quality gates:** every derivative receives its own content, format, technical, accessibility, rights, and policy checks.
7. **No approval inheritance:** approval of one asset or format does not authorize another derivative or channel.
8. **Production engines remain specialized:** existing Shorts Studio remains a specialized production engine and is integrated through contracts rather than replaced wholesale.
9. **Human editorial authority remains:** sensitive editorial decisions and material changes are escalated.
10. **Creation is not distribution:** a completed asset or schedule recommendation does not authorize publication.

## 3. Position in the architecture

The creation capability sits between Shared Intelligence Core and specialized studios.

Inputs may include:

- Approved opportunity and opportunity assessment.
- Research brief and evidence/claim ledger.
- Shared knowledge references.
- Parent brand and studio identity profiles.
- Audience and strategy context.
- Format requirements and channel constraints.
- Rights-cleared asset references.
- Resource and agent capability availability.

Outputs include:

- Studio-specific creative brief.
- Format-native concept and narrative structure.
- Script, outline, storyboard, shot plan, or article structure.
- Production instructions and asset manifest.
- Rendered or assembled artifact references.
- QA evidence and review package.
- Derivative lineage and handoff records.

The creation engine coordinates these objects but does not replace the Research Intelligence, Brand Intelligence, Quality/Governance, Agent Orchestration, Asset Management, or Distribution capabilities.

## 4. Core object model

### 4.1 CreationProject

A `CreationProject` groups related format outputs derived from a shared opportunity or editorial initiative.

Required fields:

- `creation_project_id`: UUIDv7.
- Workspace, brand, and initiative references.
- Opportunity and research references.
- Audience context reference.
- Parent brand profile version.
- Strategy/portfolio reference.
- Project objective and intended outcomes.
- Priority, target window, and resource envelope.
- Project owner and accountable editor.
- Lifecycle state and timestamps.

A project may contain multiple `StudioProduction` records. It does not imply that all planned formats must be produced.

### 4.2 StudioIdentity

A `StudioIdentity` defines a specialized editorial product.

It includes:

- Stable studio ID and immutable profile version.
- Studio name and purpose.
- Intended audience and audience exclusions.
- Editorial promise and subject boundaries.
- Voice, tone, vocabulary, and narrative posture.
- Depth, pacing, and storytelling conventions.
- Visual/audio identity references.
- Format and platform scope.
- CTA principles.
- Quality rubric and prohibited patterns.
- Rights, safety, and disclosure requirements.
- Owner-approved change history.

The parent NEXTDECODE brand supplies shared identity and trust constraints. Studio identity may specialize those constraints but cannot contradict higher-level brand policy.

### 4.3 FormatProfile

A `FormatProfile` describes the output medium and its constraints.

Potential profiles include:

- Short-form vertical video.
- Long-form video.
- Social-native text or image post.
- Article/blog.
- Newsletter.
- Podcast/audio.
- Future formats through versioned extension.

A format profile defines:

- Intended consumption context.
- Aspect ratio, duration or length range where relevant.
- Structure and narrative conventions.
- Required components and metadata.
- Accessibility requirements.
- Technical delivery constraints.
- Platform-specific limitations.
- Validation rules and version.

Exact numeric limits should be maintained in versioned platform/format profiles rather than hard-coded into shared creation logic.

### 4.4 StudioProduction

A `StudioProduction` is one studio's attempt to create one specific format output.

It includes:

- Production ID and project reference.
- Studio and identity version.
- Format profile and version.
- Channel target, if known.
- Audience segment/context.
- Creative brief and concept versions.
- Input evidence/knowledge references.
- Production pipeline/engine contract.
- Required agents/capabilities.
- Resource estimate and reservation reference.
- Current state, blockers, and timestamps.

A separate production record is required for every derivative. It has its own lifecycle, QA, rights assessment, review and approval state.

## 5. Creative planning and format adaptation

### 5.1 CreativeDirectionBrief

A `CreativeDirectionBrief` translates strategy and research into a studio-specific creative assignment.

It should specify:

- Why this subject matters to the intended audience.
- The audience need, question, or tension.
- The editorial angle and intended takeaway.
- Evidence-backed facts and claims that may be used.
- Known uncertainties, contradictions, and caveats.
- Studio identity and format profile.
- Narrative and emotional direction.
- Required context and prohibited simplifications.
- Visual/audio/textual direction.
- CTA intent, if appropriate.
- Success hypothesis and evaluation criteria.

The brief distinguishes sourced facts from editorial interpretation, estimates, hypotheses, and creative proposals.

### 5.2 CreativeConcept

A concept is a proposed execution, not merely a title.

It may contain:

- Working title and premise.
- Core audience promise.
- Hook or opening proposition.
- Narrative arc or information architecture.
- Key beats/sections.
- Evidence placement.
- Visual or interaction concept.
- Differentiation from existing content.
- Risks, sensitivities, and limitations.
- Expected production complexity.

Concept selection may be autonomous within approved editorial boundaries. Sensitive or materially reputation-affecting topics require escalation.

### 5.3 Format adaptation

The adaptation process should:

1. Retrieve the shared evidence and knowledge package.
2. Load the target studio identity and format profile versions.
3. Reassess audience need and format-native promise.
4. Develop an independent concept and structure.
5. Select claims and evidence appropriate to the format.
6. Preserve caveats, uncertainty, and source lineage.
7. Create a format-specific production plan.
8. Run derivative-specific quality and rights checks.

A short video may focus on one surprising implication; a long-form video may explain the underlying system; an article may provide a reference-oriented structure. These are independent editorial decisions built on shared evidence.

## 6. Narrative and artifact contracts

Depending on format, a production may create:

- Editorial outline.
- Script or narration.
- Segment/section plan.
- Storyboard.
- Shot plan.
- Visual direction and asset requests.
- On-screen text and captions.
- Audio and voice direction.
- Article draft and references.
- Newsletter structure.
- Podcast rundown.
- Metadata and packaging plan.

Every artifact should include:

- Stable ID and immutable version.
- Parent production/project reference.
- Authoring agent or human identity.
- Input artifact versions.
- Evidence and claim references where applicable.
- Studio and format profile versions.
- Creation timestamp.
- Status and review history.
- Content hash or integrity reference where applicable.

Edits create new versions. Do not silently overwrite an artifact that has already been reviewed, approved, or used downstream.

## 7. Production engine integration

### 7.1 Adapter boundary

Each studio connects to a specialized production engine through a versioned adapter contract.

The adapter defines:

- Accepted input schema.
- Required artifact references.
- Supported capabilities and formats.
- Execution requirements.
- Resource estimate.
- Progress and checkpoint reporting.
- Output manifest schema.
- Failure classification.
- Cancellation and recovery behavior.
- Engine/version metadata.

The shared creation layer should not depend on internal implementation details of a specific engine.

### 7.2 Shorts Studio integration

Shorts Studio remains the specialized short-form video production engine.

Its integration contract should accept a validated studio production package and return:

- Script and narration references.
- Storyboard and shot-plan versions.
- Visual/audio asset references.
- Per-shot production manifest.
- Rendered output reference and technical metadata.
- QA results and warnings.
- Engine/run identity and traceability metadata.
- Failure and recovery information.

Existing Shorts Studio components should be reused where their contracts meet the shared architecture. Integration work must first reconcile actual engine behavior and existing safeguards. This contract does not claim that all listed outputs are currently implemented or verified.

### 7.3 Long-form studio

Long-form production is a separate specialized studio, not an assumed extension of the Shorts Studio pipeline.

It should support deeper research synthesis, chapter/segment planning, sustained narrative structure, richer evidence presentation, longer asset timelines, and its own production and QA contract.

The accepted target discussed for long-form is approximately 9–11 minutes. Treat this as a planning target, not a universal hard validation rule.

### 7.4 Future studios

Social, blog/newsletter, and podcast studios should be introduced through the same adapter principles while retaining medium-specific editorial and technical requirements.

A studio must not be marked production-ready merely because its format profile or UI exists.

## 8. Content lineage and derivative graph

The Content Graph must represent relationships such as:

`Opportunity → Research Package → Evidence/Claims → Creation Project → Studio Production → Creative Brief → Concept → Script/Outline → Production Artifacts → Final Asset → QA/Review → Distribution Package`

For every derivative, retain:

- Source project and opportunity.
- Research package version.
- Claim/evidence references.
- Parent/child derivative relationships.
- Studio identity and format profile versions.
- Creative brief and concept versions.
- Production engine and version.
- Asset manifest and hashes.
- QA/review outcomes.
- Approval references, if any.
- Distribution and performance references, if later authorized.

Lineage must support impact analysis. If a source claim, asset right, or policy is later invalidated, the system can identify every affected derivative and distribution record.

A derivative can add new research and claims. Those additions must be separately sourced and validated; they cannot inherit the source package's evidence status automatically.

## 9. Asset and rights handoff

The creation engine references assets through the shared Asset Management capability.

Asset requests should declare:

- Intended use and placement.
- Format and technical requirements.
- Required duration/resolution or dimensions.
- Subject and creative purpose.
- Source preference and permitted acquisition method.
- Rights status required.
- Attribution/disclosure requirements.
- Expiry or territory restrictions, if applicable.

Before an asset is included in a production, its rights state must be checked for the specific use. Access to an asset does not imply ownership or permission.

Rights states remain centrally governed: `CLEARED`, `RESTRICTED`, `PENDING_VERIFICATION`, `PROHIBITED`, and `UNKNOWN`.

Unverified or prohibited assets must not pass a hard rights gate. A visual placeholder may be used during planning only if clearly marked and excluded from final release until cleared.

## 10. Quality and editorial governance

Each `StudioProduction` receives its own assessment across relevant dimensions:

- Editorial relevance and audience value.
- Factual accuracy and evidence integrity.
- Narrative coherence and originality.
- Studio/brand consistency.
- Format-native quality.
- Visual/audio/design quality.
- Accessibility and usability.
- Rights and provenance.
- Safety, privacy, and disclosure.
- Technical delivery compliance.

Outcomes:

- `PASS`
- `PASS_WITH_WARNINGS`
- `NEEDS_REVIEW`
- `BLOCKED`

Hard blockers cannot be overridden by ordinary approval. Approval of a source research package, concept, script, or another derivative does not automatically approve the final artifact.

Sensitive editorial choices, uncertain rights, material factual disputes, and high-impact reputational issues must be escalated under centralized governance.

## 11. Packaging and channel handoff

A completed production may create a `PackagingPlan` containing:

- Title/headline alternatives.
- Thumbnail/cover direction.
- Description/caption.
- Search/discovery metadata.
- CTA and destination.
- Disclosure and attribution text.
- Channel adaptation notes.
- Experiment hypothesis.
- Intended publication window.

A `DistributionPackage` binds a specific approved asset version to a specific channel and platform profile.

The Distribution Studio remains responsible for channel-specific validation, scheduling, platform authorization, and publishing controls. Creation completion, packaging completion, or a recommended schedule does not authorize public distribution.

Publishing remains disabled for autonomous execution until a separate owner-approved publishing policy is established.

## 12. Studio-specific autonomy

Agents may, within approved contracts and scopes:

- Generate and compare concepts.
- Draft scripts, outlines, storyboards, and production plans.
- Prepare format-native adaptations.
- Request and organize assets.
- Execute permitted production steps.
- Run automated QA and prepare review packages.
- Create metadata and packaging recommendations.
- Identify derivative updates when evidence or policy changes.

Agents must escalate:

- Sensitive editorial decisions.
- Material changes to brand positioning or mission.
- Unverified rights or legal concerns.
- High-impact factual disputes.
- Public commitments or external communications outside approved templates.
- Any action requiring spending, new services, or expanded permissions.
- Publishing or other irreversible external side effects without explicit authorization.

No studio agent may approve its own high-risk output or bypass central governance.

## 13. Learning across studios

Shared learning may include:

- Evidence quality and research efficiency.
- Narrative patterns and audience response.
- Format-specific retention or engagement observations.
- Production bottlenecks and defect patterns.
- Packaging experiment results.
- Accessibility and usability findings.

Every learning record must carry:

- Source studio and format.
- Applicable audience/context.
- Evidence quality and sample/window.
- Confidence and limitations.
- Applicability scope.
- Validation status.
- Promotion decision and history.

A pattern observed in one studio is not automatically a universal rule. Cross-studio promotion requires sufficient evidence and validation in the target context. Correlation must not be represented as causation.

## 14. Lifecycle and state model

Suggested project states:

`IDEA` → `PLANNED` → `ACTIVE` → `COMPLETED` / `CANCELLED`

Suggested studio production states:

`BRIEFING` → `CONCEPTING` → `READY_FOR_PRODUCTION` → `IN_PRODUCTION` → `ASSEMBLED` → `QA_IN_PROGRESS` → `NEEDS_REVIEW` / `BLOCKED` / `APPROVED_FOR_HANDOFF`

Additional states may include `PAUSED`, `FAILED`, `CANCELLED`, and `SUPERSEDED`.

The authoritative lifecycle must distinguish production completion, QA outcome, human review, approval, and distribution authorization. These are not interchangeable states.

## 15. APIs and events

Illustrative versioned interfaces:

- `POST /v1/creation-projects`
- `GET /v1/creation-projects/{project_id}`
- `POST /v1/studio-productions`
- `POST /v1/studio-productions/{production_id}/briefs`
- `POST /v1/studio-productions/{production_id}/concepts`
- `POST /v1/studio-productions/{production_id}/adapt`
- `POST /v1/studio-productions/{production_id}/production-jobs`
- `POST /v1/studio-productions/{production_id}/artifacts`
- `POST /v1/studio-productions/{production_id}/qa`
- `POST /v1/studio-productions/{production_id}/packaging`
- `GET /v1/studio-productions/{production_id}/lineage`
- `POST /v1/studio-adapters/{adapter_id}/capabilities`

Illustrative events:

- `creation.project.created.v1`
- `studio.production.created.v1`
- `studio.brief.approved.v1`
- `studio.concept.selected.v1`
- `studio.production.started.v1`
- `studio.artifact.created.v1`
- `studio.production.completed.v1`
- `studio.qa.completed.v1`
- `studio.production.blocked.v1`
- `studio.packaging.prepared.v1`
- `content.lineage.updated.v1`
- `content.source.invalidated.v1`

Events require schema versioning, durable delivery, idempotency, workspace scope, actor provenance, and policy context. Events do not themselves grant publishing permission.

## 16. Acceptance criteria

The contract is ready for implementation design when:

1. Every studio has a versioned identity and explicit editorial contract.
2. Every format has a versioned profile with its own requirements.
3. Shared evidence is reusable without forcing identical narratives.
4. Every derivative has an independent production record and lifecycle.
5. Every derivative preserves evidence and source lineage.
6. New claims introduced during adaptation are separately verified.
7. Production engines integrate through versioned adapters.
8. Shorts Studio remains specialized and is not replaced wholesale.
9. Long-form has an independent production and QA contract.
10. Asset rights are checked for the actual intended use.
11. Every derivative has independent quality, review, and approval status.
12. Approval does not transfer from one format or channel to another.
13. Packaging recommendations remain separate from distribution authorization.
14. Cross-studio learning is scope-aware and evidence-validated.
15. Source invalidation can identify affected derivative assets.
16. Agent autonomy remains within approved editorial, resource, security, and governance boundaries.

## 17. Open implementation details

Not fixed by this contract:

- Exact studio taxonomy and initial studio launch order.
- Detailed format schemas and numeric platform constraints.
- Script, storyboard, article, and media artifact schemas.
- Adapter protocol and engine capability negotiation.
- Long-form production technology and worker topology.
- Asset manifest and claim-linking granularity.
- Studio-specific QA rubrics and numeric thresholds.
- Packaging experiment methodology.
- UI/workspace interaction patterns.
- API payloads, event schemas, and database implementation.

These should be resolved during implementation design and validated against actual engine capabilities. This contract does not claim that future studios or features already exist.

## 18. Decision traceability

This contract operationalizes accepted decisions covering:

- Shared Intelligence Core with specialized studios and channels.
- Parent brand identity plus studio-specific editorial identities.
- One research foundation producing multiple independent format variants.
- Independent QA and approval for every derivative.
- Shorts Studio integration rather than wholesale replacement.
- Long-form as a separate studio, with approximately 9–11 minutes as the current planning target.
- Shared evidence and audience context with scope-aware cross-studio learning.
- Rights-based asset ownership and use-specific rights clearance.
- Human oversight for sensitive editorial authority.
- Distribution recommendations separated from publishing authorization.
- Content Graph lineage, source invalidation, and learning feedback.

It is subordinate to the Master Blueprint, System Architecture Master Reference, Shared Data Model & Content Graph, Shorts Studio Pipeline Contract, Shared Intelligence Core contracts, Content Quality/Rights/Governance contract, Studio Integration APIs & Artifact Management contract, and owner-approved decision register. Conflicts must be recorded and reconciled rather than silently resolved by weakening a higher-priority rule.

---

**End of Contract 11 — Multiformat Creation & Studio Intelligence Model 1.0**