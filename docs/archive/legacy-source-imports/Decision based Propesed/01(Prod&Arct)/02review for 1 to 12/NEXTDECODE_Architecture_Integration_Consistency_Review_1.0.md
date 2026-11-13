# NEXTDECODE Architecture Integration & Consistency Review
## Shared Intelligence Core Contracts 01–12 + System Architecture Parts 1–8
**Review version:** 1.0  
**Date:** 31 October 2026  
**Status:** Architecture review — documentation only; implementation readiness not approved  
**Review basis:** The 12 Shared Intelligence Core contract documents, the Three-Layer Product Architecture Working Baseline, and System Architecture & Pipeline Parts 1–8 available in this conversation. This is a document-level review, not a repository audit, schema validation, security test, or implementation verification.

---

## 1. Executive conclusion

The 12 contracts form a coherent functional architecture for NEXTDECODE's Shared Intelligence Core and its interfaces with specialized studios and distribution. They consistently support the intended product direction:

- One shared intelligence foundation.
- Specialized studios with distinct editorial and production responsibilities.
- Evidence and provenance carried through the content lifecycle.
- Centralized quality, rights, approval, and publishing governance.
- Capability-based agent orchestration and bounded resource use.
- Hybrid cloud control plane with local and remote execution.
- Audience, performance, business, and learning feedback loops.

**The architecture is directionally coherent, but it is not yet a single implementation-ready contract set.** The principal remaining work is normalization: canonical entity ownership, ID conventions, shared lifecycle semantics, common evidence/provenance vocabulary, policy decision interfaces, API/event envelopes, and cross-module dependency rules.

No repository or Git operations were performed. No code, tests, integrations, providers, infrastructure, accounts, credentials, or publishing settings were changed.

### Overall assessment

| Area | Assessment | Meaning |
|---|---|---|
| Product direction | Strong | Modules support the stated integrated ecosystem |
| Functional coverage | Strong | Main intelligence, creation, business and distribution domains are represented |
| Governance boundaries | Strong direction; needs one wording reconciliation | Centralized enforcement and owner authority are repeatedly specified |
| Entity and data consistency | Needs normalization | Some concepts are independently defined in multiple contracts |
| Lifecycle/state consistency | Needs normalization | Separate state machines are appropriate, but shared envelope and transition authority need formalization |
| API/event consistency | Incomplete | Contracts contain illustrative endpoints/events, not one common protocol |
| Implementation specificity | Deliberately open | Providers, infrastructure, exact thresholds and some schemas remain undecided |
| Implementation readiness | Not approved | Reconciliation and implementation design are still required |

## 2. What is already consistent and should be preserved

### 2.1 Architecture layers and ownership

The three-layer product architecture is reflected across the contracts:

1. Creator Success Intelligence defines the eight success domains.
2. Shared Intelligence Core owns reusable audience, opportunity, evidence, brand, knowledge, strategy, quality, performance, business and orchestration intelligence.
3. Specialized studios and distribution channels own format-specific creation and delivery.

The System Architecture Parts 1 and 7 reinforce the key boundary: shared services own canonical identity, workflow, governance and artifact registration; studios own format-specific creation and production.

**Preserve this separation.** Do not turn every studio into a thin UI over one generic production engine.

### 2.2 Governance and quality outcomes

Contract 07 defines the shared quality outcomes:

- `PASS`
- `PASS_WITH_WARNINGS`
- `NEEDS_REVIEW`
- `BLOCKED`

The same four outcomes are referenced in the wider architecture. Contract 11 correctly requires independent validation for each derivative, and Contract 12 separates distribution recommendation, scheduling and publishing authorization.

**Preserve these outcomes as the canonical quality result enum.** A production lifecycle state such as `APPROVED_FOR_HANDOFF` must not replace or obscure the underlying QA outcome.

### 2.3 Rights state vocabulary

Contract 07 defines:

- `CLEARED`
- `RESTRICTED`
- `PENDING_VERIFICATION`
- `PROHIBITED`
- `UNKNOWN`

Contracts 11 and 12 reuse this vocabulary and correctly require use-specific clearance.

**Preserve Contract 07 as the canonical rights-state owner.** Other modules should reference its rights assessment rather than define their own competing rights status.

### 2.4 Evidence-based learning

Contracts 02, 04, 05 and 08 consistently distinguish sources, evidence, claims, knowledge, estimates, hypotheses, experiments and validated learning. They also preserve scope, freshness, uncertainty and limitations.

**Preserve the rule that a result is only reusable within its validated scope.** A single viral result or one studio's experiment must not silently become a workspace-wide rule.

### 2.5 Agent, resource and worker authority

Contract 10 aligns with Parts 4, 5 and 8 on durable execution, bounded agents, least privilege, task-scoped delegation, local/remote workers, checkpoints and safe recovery.

**Preserve the distinction between agent, orchestrator, tool/service and worker.** Runtime content agents are not the same thing as the existing engineering agents Qoder, OpenCode and Kilo.

### 2.6 Commercial and publishing boundaries

Contract 09 preserves recommendation/preparation authority without allowing agents to accept sponsorships, sign agreements, spend, or create binding commitments. Contracts 07 and 12 preserve centralized publishing authorization and the disabled state of autonomous public publishing.

**Preserve these as non-negotiable policy constraints.** Owner silence is never approval.

---

## 3. Findings requiring reconciliation

The findings below are document-level inconsistencies or gaps. Recommended resolutions are proposed for the architecture baseline; they do not silently amend the source documents or authorize implementation.

### F-01 — Canonical ID convention is inconsistent

<badge>High priority</badge>

**Evidence**

- Contracts 01–12 generally specify UUIDv7 canonical identifiers.
- Part 3 illustrates prefixed IDs such as `wsp_`, `brd_`, `cnt_`, `art_`, `job_`, `pub_`.
- Contract 10 allows UUIDv7 “or another stable immutable identifier,” which weakens the otherwise consistent UUIDv7 direction.

**Risk**

Different services may generate incompatible identifiers, duplicate identity logic, or confuse display IDs with database identity.

**Recommended resolution**

- Use UUIDv7 as the canonical machine identity for every entity.
- Treat prefixes as optional human-readable display keys only, never as a second identity system.
- Remove “or another stable immutable identifier” from Contract 10 when the canonical data standard is ratified.
- Define one shared ID field convention: `{entity}_id`, plus `workspace_id` and required scope references.
- Keep external platform IDs in separate namespaced fields, never as canonical internal IDs.

**Owner:** Shared Data Model / Content Graph.

### F-02 — AudienceSegment is defined in two contracts

<badge>High priority</badge>

**Evidence**

- Contract 01 defines `AudienceSegment` with `segment_id`, `audience_id`, `segment_type`, scope, evidence, confidence, status and version.
- Contract 08 independently defines `AudienceSegment` with `audience_segment_id`, and repeats strategic persona / observed / emerging segment types.
- Contract 08 also defines `AudienceInsight`, while Contract 01 defines an `Audience Insight` contract with overlapping fields.

**Risk**

Two records may represent the same segment or insight with different IDs, lifecycle rules, ownership and schema.

**Recommended resolution**

- Contract 01 owns canonical audience identity, persona, segment and audience-insight entities.
- Contract 08 owns performance observations, metric definitions, snapshots, experiments, attribution and performance-derived learning.
- Contract 08 should reference Contract 01 audience/segment/insight IDs rather than create a second audience entity.
- If performance-specific insight metadata is needed, use a typed extension or linked performance observation.

**Owner:** Audience Intelligence / Shared Data Model.

### F-03 — StudioIdentity is duplicated across Brand and Creation contracts

<badge>High priority</badge>

**Evidence**

- Contract 03 defines parent brand, brand identity versions and studio identity, including voice and visual profile references.
- Contract 11 defines `StudioIdentity` again with editorial focus, audience, tone, visual/audio identity, format scope and quality rubric.

**Risk**

Brand identity and creation identity may drift; a production could reference one studio profile while brand evaluation uses another.

**Recommended resolution**

- Contract 03 owns the canonical `StudioIdentity` and immutable identity version.
- Contract 11 owns `StudioProduction`, `FormatProfile`, `CreativeDirectionBrief` and format-specific production settings.
- Contract 11 references `studio_identity_version_id` from Contract 03.
- Format-specific production configuration must not mutate the canonical brand/studio identity.

**Owner:** Brand Intelligence.

### F-04 — Evidence, source and claim objects need a canonical shared registry

<badge>High priority</badge>

**Evidence**

- Contract 02 defines `EvidenceSource`, `EvidenceItem`, `Claim`, `ClaimEvidenceLink` and opportunity assessment.
- Contract 04 describes source/evidence/research/knowledge layers and knowledge relationships.
- Contract 05 defines research requests, source assessment, claim extraction, evidence analysis, contradictions and research synthesis.
- Contract 11 and Contract 12 rely on claim/evidence lineage for derivatives and distribution.

**Risk**

The same source or claim may be recreated in multiple modules, producing broken lineage, conflicting freshness states and incomplete impact analysis when evidence is invalidated.

**Recommended resolution**

- Contract 02 / Content Graph owns canonical `EvidenceSource`, `EvidenceItem`, `Claim` and evidence-link identities.
- Contract 05 owns research execution records and references those canonical objects.
- Contract 04 owns reusable `KnowledgeItem`, `KnowledgeVersion` and `LearningRecord`, each linked to source/evidence/claim IDs.
- Contract 11 and 12 consume evidence references; they do not recreate evidence identity.
- Define a shared invalidation event so affected knowledge, briefs, derivatives and publications can be found.

**Owner:** Content Graph + Research Intelligence.

### F-05 — Epistemic status, lifecycle status and metric provenance are not yet cleanly separated

<badge>High priority</badge>

**Evidence**

- Contract 04 defines epistemic statuses: `OBSERVED`, `SOURCE_REPORTED`, `VERIFIED`, `ESTIMATED`, `INTERPRETATION`, `HYPOTHESIS`, `EXPERIMENTAL_LEARNING`, `VALIDATED_LEARNING`, `DISPUTED`, `SUPERSEDED`, `RETRACTED`.
- Contract 08 defines performance value types: `PLATFORM_REPORTED`, `DIRECTLY_OBSERVED`, `ESTIMATED`, `FORECAST`.
- Contract 09 adds financial value classifications: `CONFIRMED`, `PLATFORM_REPORTED`, `ATTRIBUTED`, `ESTIMATED`, `FORECAST`.
- Other contracts use `status` for lifecycle state.

**Risk**

A single generic `status` or `value_type` field may mix whether a record is current, what kind of knowledge it represents, and where a measurement came from.

**Recommended resolution**

Use separate dimensions:

1. `lifecycle_status`: draft, active, stale, superseded, retracted, archived, etc.
2. `epistemic_status`: observed, source-reported, verified, estimated, interpretation, hypothesis, validated learning, disputed, etc.
3. `provenance_type`: platform-reported, directly observed, independently verified, calculated/estimated, forecast, owner-entered, etc.
4. `confidence_assessment`: value/level plus method, rationale and limitations.
5. `scope` and `observation_window`: required context for interpretation.

Contract 04 should own the shared epistemic vocabulary. Contracts 08 and 09 may define domain-specific provenance extensions but should map to the shared dimensions.

**Owner:** Knowledge & Learning / Analytics.

### F-06 — State machines are correctly separate but lack a shared lifecycle envelope

<badge>High priority</badge>

**Evidence**

Distinct lifecycles exist for:
- Opportunity (Contract 02).
- Knowledge (Contract 04).
- Research (Contract 05).
- Agent/task/workflow (Contract 10).
- Creation project and studio production (Contract 11).
- Distribution package, schedule and publication (Contract 12).
- Persistent jobs and workers (Part 4).

This separation is appropriate. However, each contract independently describes statuses and transitions, while cross-module state authority and transition events are not yet expressed in one common standard.

**Risk**

A local module may mark its work complete while the orchestrator still considers a dependency pending, blocked or unreconciled. Teams may also conflate `APPROVED`, `SUCCEEDED`, `COMPLETED`, `PUBLISHED` and `ACTIVE`.

**Recommended resolution**

Do not force one universal state enum. Instead define a common lifecycle envelope for every stateful entity:

- `entity_id`, `entity_type`, `lifecycle_state`
- `state_version` / optimistic concurrency token
- `occurred_at`, `recorded_at`
- `actor_ref` and actor type
- `reason_code` and structured reason
- `correlation_id`, `causation_id`
- `policy_version` where relevant
- `previous_state`, `new_state`
- `evidence_refs` / result references

The owning domain controls its entity state. The orchestrator controls workflow/job progression. Central governance controls authorization decisions. A domain event reports a transition; it does not grant permission.

**Owner:** Workflow Orchestration / Shared Data Model.

### F-07 — Approval, QA, governance eligibility and publishing authorization need one explicit decision chain

<badge>High priority</badge>

**Evidence**

- Contract 07 defines QA outcomes, governance decisions, approval workflow and a publishing authorization gate.
- Contract 11 defines studio production outcomes including `APPROVED_FOR_HANDOFF`.
- Contract 12 defines package validation, schedule authorization and publish operations.
- Part 1 describes `Auto Publish`, `Pending Approval`, and `Blocked` as publishing outcomes.
- Contract 12 explicitly says autonomous public publishing is disabled pending separate owner-approved policy.

**Risk**

The phrase “Auto Publish” in Part 1 could be interpreted as an active capability, conflicting with the later explicit disabled status. Also, approval for handoff may be confused with publishing authorization.

**Recommended resolution**

Adopt this explicit chain:

`Production completed` → `QA outcome recorded` → `Governance eligibility decision` → `Human approval if required` → `Distribution package validated` → `Schedule authorization` → `Publish authorization` → `External operation` → `Platform state reconciled`

- `APPROVED_FOR_HANDOFF` means only that a production may be handed to the next workflow stage.
- It does not mean approved for public publication.
- `ELIGIBLE` is not authorization.
- Every public external side effect requires a fresh policy authorization for the exact asset/package/account/action.
- Autonomous publishing remains disabled. Update Part 1's “Auto Publish” language to clearly label it a future conditional mode, unavailable until a separate policy is explicitly approved.

**Owner:** Central Quality/Rights/Governance.

### F-08 — `Task`, `Job`, `Workflow`, `WorkflowRun` and `StudioProduction` boundaries need a canonical mapping

<badge>High priority</badge>

**Evidence**

- Part 4 defines Workflow Definition, Workflow Run, Workflow Step, Job, Job Attempt, Queue Entry, Worker and related records.
- Contract 10 defines Workflow, Task, TaskCheckpoint, AgentIdentity and WorkerIdentity.
- Contract 11 defines CreationProject and StudioProduction.
- Part 7 defines studio job and artifact integration boundaries.

**Risk**

The architecture could create overlapping durable work records and competing sources of truth for execution state.

**Recommended resolution**

Use a clear hierarchy:

- `CreationProject`: business/editorial grouping of related format work.
- `StudioProduction`: one studio's production instance for one format output.
- `WorkflowDefinition`: versioned reusable process definition.
- `WorkflowRun`: one execution of a workflow definition.
- `Task`: logical unit of work assigned to an agent/capability.
- `Job`: durable executable/dispatch unit assigned to a worker.
- `JobAttempt`: one execution attempt for a job.
- `Artifact`: immutable output/input record.
- `Worker`: execution identity and capability.
- `Agent`: bounded reasoning/capability identity.

A Task may produce one or more Jobs; a WorkflowRun may coordinate many Tasks and Jobs. A StudioProduction references its WorkflowRun and output artifacts. Avoid duplicating state fields unless one is explicitly a projection/cache.

**Owner:** Workflow Orchestration + Studio Integration.

### F-09 — API and event envelopes are illustrative and not yet unified

<badge>Medium priority</badge>

**Evidence**

Contracts 01–12 define their own example endpoints and events. Part 7 defines integration contracts, idempotency and adapter behavior. Part 4 defines durable job/event behavior. The documents do not yet define one canonical envelope for every API/event.

**Risk**

Inconsistent workspace scope, actor provenance, schema version, trace IDs, idempotency, event ordering and error formats across modules.

**Recommended resolution**

Define shared API/event conventions before implementation:

- Versioned path and schema.
- `workspace_id` on scoped records and events.
- Canonical entity IDs and references.
- `actor_ref` / actor type.
- `correlation_id` and `causation_id`.
- `idempotency_key` for retriable commands/side effects.
- `occurred_at` and `recorded_at`.
- `policy_version` where a policy decision applies.
- Structured error and reason codes.
- Explicit command versus event semantics.
- Durable outbox/inbox and duplicate delivery handling.
- Compatibility and deprecation policy.

Keep endpoint names in domain contracts illustrative until the shared API standard is ratified.

**Owner:** Platform Integration / Architecture.

### F-10 — Resource and financial authority are aligned but need a single policy vocabulary

<badge>Medium priority</badge>

**Evidence**

- Contract 10 defines resource accounts, quota, usage, reservations, forecasts and budget-bounded optimization.
- Contract 09 defines financial records, cost attribution and commercial authority.
- Part 8 requires cost limits and paid-service authorization.
- Accepted decisions prohibit new spending, subscriptions, contracts, budget increases or unauthorized financial commitments.

**Risk**

A provider quota, prepaid credit balance, operating budget, forecast and actual financial expense may be treated as interchangeable.

**Recommended resolution**

Separate:
- Technical quota/capacity (requests, tokens, minutes, storage).
- Approved financial budget (currency and period).
- Reserved resource amount.
- Provider-reported usage/cost.
- Internally estimated usage/cost.
- Confirmed financial transaction.
- Forecast.

Resource Manager may schedule or pause work within the approved envelope; Business Intelligence records financial truth and analysis. Neither module can increase the approved budget or create a new financial commitment.

**Owner:** Resource Management + Business Intelligence.

### F-11 — Data classification and privacy controls need one authoritative policy reference

<badge>Medium priority</badge>

**Evidence**

Contracts 01, 02, 04, 08 and 10 use `Public`, `Internal`, `Confidential`, `Restricted`. They also refer to purpose limitation, consent, workspace/brand isolation, minimization, retention and deletion. Part 8 defines broader security controls.

**Risk**

Individual modules may interpret classification, retention or allowed processing differently, especially when data is sent to external AI providers or remote workers.

**Recommended resolution**

- Establish one central Data Governance policy and classification registry.
- Store classification and purpose on data-bearing records and task envelopes.
- Evaluate provider/worker eligibility against classification and purpose before transfer.
- Treat retention, legal hold and deletion as centrally governed lifecycle policies.
- Keep external AI provider requirements strict: verified data-protection terms, no training use without explicit authorization, and block if retention/location/security protections cannot be verified.
- Module-specific contracts should reference the central policy rather than restate or reinterpret it.

**Owner:** Security & Data Governance.

### F-12 — Artifact, asset, knowledge and content versioning need a single lineage rule

<badge>Medium priority</badge>

**Evidence**

- Part 3 defines stable identities and immutable artifact versions.
- Part 7 requires immutable artifact versions, hashes and provenance.
- Contract 04 defines KnowledgeVersion.
- Contract 07 defines content/asset manifests and approval binding.
- Contract 11 defines artifact versions and derivative lineage.
- Contract 12 binds distribution packages and approvals to exact asset/package versions.

**Risk**

A content derivative or approval may refer to a mutable path or a newer asset revision, breaking reproducibility and approval validity.

**Recommended resolution**

- Stable entity ID + immutable version ID for every reviewable artifact.
- Content hash for integrity, not as the only identity.
- Canonical artifact registry owns binary metadata, versions, hashes and storage references.
- Asset registry owns reusable source asset identity and rights provenance.
- Knowledge registry owns knowledge versions and evidence references.
- Any material artifact/package change creates a new version and re-runs impacted checks.
- Approval binds to exact immutable versions and destination/action context.

**Owner:** Artifact Management / Content Graph.

### F-13 — Research completion and claim verification need explicit separation

<badge>Medium priority</badge>

**Evidence**

Contract 05 explicitly states `COMPLETED` does not mean every claim is verified. Contract 02 distinguishes evidence and claim support; Contract 04 distinguishes `VERIFIED` from `VALIDATED_LEARNING`.

**Risk**

Downstream production could treat a completed research brief as proof that all claims are ready for use.

**Recommended resolution**

Every research package should expose:
- Overall research completion state.
- Per-claim verification/support state.
- Unresolved material questions.
- Contradictions and limitations.
- Freshness and scope.
- Claims approved for a specific intended use.

Production briefs must reference claim-level readiness, not only research-package completion.

**Owner:** Research Intelligence.

### F-14 — Analytics and business financial metrics need explicit metric ownership and reconciliation

<badge>Medium priority</badge>

**Evidence**

Contract 08 owns metric definitions, performance snapshots, experiments and attribution. Contract 09 owns financial records and business performance. Contract 12 collects platform metrics and publication outcomes.

**Risk**

Revenue, cost, conversion and performance values may be duplicated with different sources, periods or reconciliation states.

**Recommended resolution**

- Contract 08 owns general metric definitions, performance snapshots, experiments and attribution methodology.
- Contract 09 owns authoritative business financial records and business performance views.
- Contract 12 owns platform collection provenance and publication context, then hands metric observations to Contract 08.
- Financial facts must be reconciled to the appropriate authoritative financial source before being marked `CONFIRMED`.
- Every metric records unit, definition/version, time window, timezone, source, collection time, provenance type and limitations.

**Owner:** Analytics & Learning / Business Intelligence.

### F-15 — “Twelve modules” and “eight architecture parts” need a formal traceability matrix

<badge>Medium priority</badge>

**Evidence**

The 12 contracts describe Shared Intelligence Core domains and its adjacent creation/distribution capabilities. Parts 1–8 describe system architecture, execution, governance, integration and deployment. These are different document groupings, not competing module counts.

**Risk**

A reader may interpret the 12 contracts as twelve deployable services or assume one-to-one mapping with the original 12 product modules.

**Recommended resolution**

Create a traceability matrix with:
- Product module.
- Shared Intelligence Core capability.
- Owning contract.
- Supporting architecture part.
- Canonical entities.
- APIs/events.
- Implementation stage.
- Current-state evidence.
- Open decisions and acceptance tests.

Explicitly state that module boundaries are logical capabilities, not a mandate for twelve separate services or deployments.

**Owner:** Architecture / Product.

---

## 4. Canonical ownership proposal

This table is the recommended source-of-truth map for the next architecture revision.

| Canonical domain/object | Owning contract/document | Other modules should |
|---|---|---|
| Workspace, canonical IDs, Content Graph relationships | Part 3 + shared data model | Reference canonical IDs |
| Audience, persona, segment, audience insight | Contract 01 | Contract 08 references audience entities |
| Opportunity, evidence source/item, claim and claim links | Contract 02 | Contracts 05/11/12 reference canonical evidence |
| Parent brand, brand identity, studio identity | Contract 03 | Contract 11 references immutable identity versions |
| Knowledge item/version, epistemic status, learning record | Contract 04 | Other domains publish evidence-backed inputs |
| Research request/run, source assessment, synthesis, monitoring | Contract 05 | Uses canonical evidence and claim registry |
| Objectives, portfolio, editorial programs, initiatives | Contract 06 | Studios consume approved plans |
| QA, rights, governance decision, approval, publish authorization | Contract 07 | All studios/adapters use central gates |
| Metric definition, performance snapshot, experiment, attribution | Contract 08 | Contract 12 supplies platform observations; Contract 09 supplies business metrics |
| Commercial pipeline, financial record, business performance | Contract 09 | Other domains provide references and measurements |
| Agent/provider/model registry, task delegation, resource account, worker routing | Contract 10 + Parts 4/5/8 | Use central task/resource/worker contracts |
| Creation project, studio production, format profile, creative artifacts | Contract 11 + Part 7 | Uses identity, evidence, rights and QA references |
| Channel profile/account, distribution package, schedule, publish operation, publication | Contract 12 + Contract 07 | Uses central authorization and analytics handoff |

This ownership map is a proposed reconciliation, not a claim that the source documents already implement these boundaries.

## 5. Recommended canonical lifecycle and decision model

Do not create one giant state machine. Keep domain-specific states, but standardize the surrounding rules.

### 5.1 Separate these concepts

| Concept | What it answers | Example |
|---|---|---|
| Lifecycle state | Where is this record in its own process? | `RUNNING`, `STALE`, `SUPERSEDED` |
| Execution outcome | Did this attempt complete? | `SUCCEEDED`, `FAILED`, `RETRY_WAIT` |
| Quality outcome | Does the output meet requirements? | `PASS`, `NEEDS_REVIEW`, `BLOCKED` |
| Governance eligibility | May it progress to the next governed stage? | `ELIGIBLE`, `PENDING_APPROVAL`, `BLOCKED`, `EXPIRED` |
| Human approval | Did an authorized person approve the exact request? | `APPROVED`, `REJECTED`, `EXPIRED` |
| External operation state | What did the platform actually do? | `UPLOAD_CONFIRMED`, `PUBLISHED_CONFIRMED`, `RECONCILIATION_REQUIRED` |
| Epistemic status | What kind of knowledge is this? | `VERIFIED`, `HYPOTHESIS`, `ESTIMATED` |
| Provenance type | Where did this value come from? | `PLATFORM_REPORTED`, `DIRECTLY_OBSERVED` |

### 5.2 Authority order

1. Owner-approved mission, policy and authority boundaries.
2. Central security, privacy, rights and governance policy.
3. Domain-specific eligibility and validation rules.
4. Workflow orchestrator and durable execution state.
5. Agent recommendations and worker execution reports.

A lower layer cannot override a higher layer. Agents cannot self-grant permissions. Human approval cannot bypass a hard blocker that policy marks non-overridable.

### 5.3 Publishing chain

The only acceptable interpretation is:

`QA` ≠ `Governance eligibility` ≠ `Human approval` ≠ `Schedule authorization` ≠ `Publish authorization` ≠ `Platform confirmation`.

Autonomous public publishing remains disabled until a separate owner-approved policy is explicitly established.

---

## 6. Cross-module end-to-end workflow

The following is the recommended logical path. It is a target workflow, not a claim that the complete system currently exists.

1. **Discover:** Audience and Opportunity Intelligence identify an audience need or opportunity.
2. **Assess:** Opportunity eligibility gates run before weighted scoring.
3. **Research:** Research Intelligence gathers source-backed evidence and resolves or records contradictions.
4. **Preserve:** Evidence, claims and knowledge are registered with scope, provenance and versions.
5. **Plan:** Strategy & Portfolio Intelligence selects the opportunity and defines the initiative/portfolio context.
6. **Brief:** Brand Intelligence and the selected studio create a studio-specific creative direction brief.
7. **Create:** Multiformat Creation produces independent format-native derivatives from shared evidence.
8. **Produce:** A specialized studio executes through a versioned adapter and durable workflow/job contracts.
9. **Validate:** Each derivative receives independent QA, rights and governance evaluation.
10. **Review:** Required human decisions bind to exact immutable versions.
11. **Package:** Distribution Intelligence prepares channel-native packages and schedule proposals.
12. **Authorize:** Central governance validates the exact account, asset, package, action and policy. Publishing remains disabled for autonomous execution.
13. **Execute:** An authorized operation is submitted through the centralized publishing boundary.
14. **Reconcile:** Platform upload, publication and visibility states are verified separately.
15. **Measure:** Platform observations and business outcomes are recorded with provenance and windows.
16. **Learn:** Experiments and performance evidence become scoped learning, then are validated before broader reuse.

## 7. Dependency and implementation sequence

Recommended implementation order, subject to a later implementation plan:

### Foundation A — Canonical data and governance
- Ratify canonical IDs and ownership map.
- Normalize evidence, claim, audience, brand and artifact references.
- Define shared lifecycle envelope and event conventions.
- Formalize data classification and provider eligibility.
- Formalize QA, rights, approval and authorization interfaces.

### Foundation B — Durable execution
- Reconcile WorkflowRun, Task, Job, JobAttempt and Worker boundaries.
- Define durable queue/outbox/inbox and idempotency behavior.
- Define resource reservations and budget/quota semantics.
- Validate local worker offline/reconnect behavior and cloud continuity.

### Foundation C — First integrated studio
- Define the thin Shorts Studio adapter against Part 7.
- Map current engine artifacts to canonical artifact records.
- Ensure the central QA/rights/governance path cannot be bypassed.
- Validate failure recovery and immutable artifact registration.
- Keep public publishing disabled during integration.

### Foundation D — Intelligence and multiformat expansion
- Connect audience, opportunity, research, knowledge and strategy workflows.
- Add independent format-native production contracts.
- Introduce long-form and other studios only when their contracts and QA are ready.

### Foundation E — Distribution and learning
- Implement channel profiles, package validation and schedule proposals.
- Preserve centralized publishing authorization.
- Add post-publication analytics and business reconciliation.
- Promote learning only within validated scopes.

This is a sequencing recommendation, not a task assignment or authorization to access the repository.

## 8. Decisions register

### 8.1 Accepted direction — preserve

- Three-layer architecture: Creator Success Intelligence, Shared Intelligence Core, specialized studios/channels.
- Single-owner Creator Mode initially; architecture remains evolution-ready.
- Hybrid deployment: always-on cloud control plane with local execution workers.
- Cloud-authoritative durable workflow state.
- Shorts Studio remains specialized; integrate rather than replace.
- UUIDv7 canonical ID direction.
- PostgreSQL-compatible relational system-of-record direction.
- Durable DB-backed queue and transactional outbox/inbox direction.
- Versioned HTTP/JSON API direction.
- Least-privilege worker/agent identities and short-lived scoped credentials.
- Centralized governance, quality, rights and authorization.
- Four canonical QA outcomes.
- Central rights registry and use-specific rights states.
- Immutable artifact versions and approval bound to exact versions/hashes.
- Evidence-backed research and scope-aware learning.
- No self-granted permissions, no policy bypass, and no silence-as-approval.
- No unauthorized spending, subscriptions, contracts or budget increases.
- No customer-data sale/licensing/monetization.
- Strict external AI provider data-protection requirements.
- Autonomous public publishing remains disabled pending separate explicit approval.

### 8.2 Open implementation choices — do not guess

- Exact database schema and migration strategy.
- Queue, scheduler and event transport technology.
- API framework and authentication implementation.
- Object storage provider and artifact transfer protocol.
- Cloud provider and deployment region.
- Model/provider allowlist and data-processing verification evidence.
- Numeric retry, lease, heartbeat, quota and alert thresholds.
- QA thresholds and evaluation datasets.
- Retention periods and legal-hold implementation.
- Initial platform/account integration list.
- Exact conditional publishing policy, if ever considered.
- Detailed UI framework and workspace interaction model.

### 8.3 Explicitly not authorized

- Repository or Git access and changes.
- Code/test/configuration modifications.
- Agent ownership changes.
- Dependency installation.
- Provider connections or credential creation.
- Cloud provisioning or deployment.
- New spending, subscriptions, contracts or budget increases.
- Account changes, uploads, public publishing or external commitments.

---

## 9. Required follow-up artifacts before implementation

The next architecture work should produce these documents:

1. **Canonical Data Dictionary & Entity Ownership Registry** — one definition per shared entity, required fields, ownership, relationships, versioning and references.
2. **Unified Lifecycle & State Transition Standard** — state ownership, transition authority, common lifecycle envelope, event semantics and invalid transitions.
3. **API & Event Contract Standard** — request/event envelopes, schema versioning, idempotency, outbox/inbox, errors, compatibility and security.
4. **Policy & Authorization Decision Matrix** — action-by-action authority, hard blockers, approvals, scopes, expiry and emergency controls.
5. **Module-to-Contract Traceability Matrix** — product modules, contracts, architecture parts, entities, APIs, dependencies, implementation stage and acceptance tests.
6. **Implementation Readiness & Risk Register** — unresolved choices, evidence needed, risk severity, owner, prerequisites and go/no-go criteria.

These are reconciliation artifacts, not new product modules.

## 10. Final recommendation

**Do not start implementation directly from the 12 contracts as they stand.** First ratify the canonical ownership map and normalize IDs, duplicated entities, state semantics, evidence provenance, authorization chain, and API/event envelopes.

The good news: this is not a reason to redesign the product. The architecture's main direction is sound. The remaining work is to make the 12 contracts and eight system parts behave like one precise system specification rather than a collection of individually useful documents.

**Review outcome:** `CONDITIONALLY COHERENT — NORMALIZATION REQUIRED — IMPLEMENTATION NOT YET APPROVED`

---

**End of NEXTDECODE Architecture Integration & Consistency Review 1.0**
