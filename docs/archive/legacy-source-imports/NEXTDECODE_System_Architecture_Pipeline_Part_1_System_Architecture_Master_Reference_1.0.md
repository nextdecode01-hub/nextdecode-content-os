# NEXTDECODE System Architecture & Pipeline
## Part 1 — System Architecture Master Reference 1.0

**Document status:** Architecture reference draft  
**Version:** 1.0  
**Purpose:** Establish a shared technical understanding of the existing Shorts Studio, the intended NEXTDECODE Content OS architecture, system boundaries, responsibilities, risks, and the sequence for future technical design.  
**Companion documents:**
- `NEXTDECODE_Master_Blueprint_2.0` — product vision, scope, modules, strategy and roadmap.
- `NEXTDECODE_System_Architecture_Pipeline_Part_2_Shorts_Studio_Pipeline_Contract_1.0` — detailed Shorts Studio stage-by-stage pipeline contract.

---

## 1. Executive summary

NEXTDECODE is intended to evolve from a Shorts-focused production workflow into a broader **Content OS** for one brand, multiple content formats and multiple distribution channels.

The agreed architectural direction is:

> **One shared intelligence system. Multiple content studios. Multiple distribution channels. One unified operating environment.**

The system should not become a collection of disconnected content generators. It should provide shared knowledge, research, brand context, content relationships, orchestration, quality controls, approval and learning. Specialized studios should handle format-specific creation and production.

The existing Shorts Studio remains a specialized Python/FFmpeg production engine. The intended approach is to integrate it into the wider Content OS through explicit contracts, not replace it wholesale.

This document separates:
- what is known from the available reconciliation reports;
- the target architecture proposed in the architecture discussion;
- decisions that remain open and require owner approval.

It is not implementation authorization.

## 2. Product and operating context

### 2.1 Product direction

NEXTDECODE Content OS is being designed initially for:
- one owner/operator;
- one brand: NEXTDECODE;
- local-first operation;
- free-first / ₹0 target;
- human-controlled agents;
- explicit approval for critical actions;
- multiple content formats over time.

The architecture should leave room for future hybrid/cloud execution, additional brands, teams and SaaS evolution, but those capabilities are not part of the initial implementation scope.

### 2.2 Content formats in scope over time

The broader system may support:
- short-form video;
- long-form video;
- Reels and other short social video;
- carousels;
- X posts and threads;
- LinkedIn posts;
- blogs and articles;
- newsletters;
- podcasts and audio;
- campaigns.

Each format should have its own production requirements and configuration. Shared research and knowledge may be reused, but the same copy should not simply be duplicated across every channel.

### 2.3 Existing Shorts Studio

Shorts Studio is an existing production system with Python-based workflow components and FFmpeg rendering. It has research, scripting, visual planning, rendering, QA, review and publishing-related components, as described in Part 2.

The available reports establish meaningful implementation and test evidence, but they do not establish that the complete future Content OS already exists.

---

## 3. Architecture principles

These principles guide the target design. They are not claims that all principles are already enforced in code.

1. **One shared intelligence core:** Research, knowledge, brand context, content relationships and learning should be shared across studios.
2. **Specialized studios:** Format-specific creation and production should remain modular.
3. **Preserve working systems:** Integrate and improve Shorts Studio rather than replacing it without a demonstrated need.
4. **Explicit contracts:** Modules, agents and studios should exchange versioned inputs, outputs, statuses and artifact references.
5. **Deterministic safety controls:** Critical rules such as rights, validation and publishing authorization should be enforced by software policy, not left only to agent instructions.
6. **Human control:** Critical and exceptional actions remain subject to explicit owner-approved rules.
7. **Fail closed:** Missing approval, unresolved rights or hard validation failures must not silently pass into external distribution.
8. **Resumability:** Work should survive interruption and resume from persisted state.
9. **Traceability:** Every important output should be traceable to its brief, research, sources, claims, assets, configuration and approvals.
10. **Provider replaceability:** AI and external service providers should be replaceable behind stable internal interfaces where practical.
11. **Local-first, evolution-ready:** Avoid premature cloud/SaaS complexity while keeping future migration feasible.
12. **Evidence before implementation:** Verify current behavior and contracts before designing changes around assumptions.

---

## 4. High-level target architecture

The proposed architecture has five broad layers:

```text
┌──────────────────────────────────────────────────────────────┐
│                    EXPERIENCE / CONTROL                      │
│ Workspace • Dashboard • Content Calendar • Review Inbox      │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                 SHARED INTELLIGENCE CORE                     │
│ Content Graph • Knowledge • Research • Brand • Strategy      │
│ Quality Intelligence • Analytics / Learning                  │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│               ORCHESTRATION / POLICY LAYER                   │
│ Workflow Engine • Agent Contracts • Queue • Scheduler        │
│ QA Gates • Rights Policy • Approval Manager • Audit Trail    │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                  SPECIALIZED STUDIOS                         │
│ Short Video • Long Video • Social • Blog • Newsletter        │
│ Podcast / Audio • Campaign                                   │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│               EXECUTION / INTEGRATION LAYER                   │
│ Render Workers • AI Providers • Asset Sources • Platforms     │
│ Storage • Publishing Adapters • Analytics Connectors          │
└──────────────────────────────────────────────────────────────┘
```

This is a conceptual target architecture. It is not a diagram of the current deployed system.

### 4.1 Experience and Control layer

**Target responsibilities**
- Provide one workspace for the owner.
- Show content status, work queues, schedules, review requests and alerts.
- Provide a unified view across studios and formats.
- Make automation state and pending decisions visible.

**Current evidence**
- Phase 0 reconciliation did not identify a completed Content OS web workspace.
- An API exists, but the reports identified authentication and in-memory job limitations.

**Status:** Proposed target; not verified as implemented.

### 4.2 Shared Intelligence Core

**Target responsibilities**
- Maintain the Content Graph.
- Store reusable knowledge and research.
- Maintain brand context and strategy.
- Connect claims, sources, briefs, outputs and assets.
- Learn from content performance and feedback.

**Status:** Mostly target architecture. The reports describe some research and analytics components, but not a unified shared intelligence core.

### 4.3 Orchestration and Policy layer

**Target responsibilities**
- Coordinate multi-stage workflows.
- Assign work to specialized agents or workers.
- Persist job state and support retries/resumption.
- Apply QA, rights and approval policies.
- Maintain audit and publishing records.

**Status:** Partially represented by existing scripts, scheduler/n8n-related pieces and run-tracking work; a complete centralized orchestration and policy layer is not established.

### 4.4 Specialized Studios

**Target responsibilities**
- Own format-specific creation and production.
- Accept well-defined inputs.
- Return versioned artifacts, manifests, diagnostics and stage statuses.
- Avoid owning cross-format brand memory or global publishing policy.

**Initial studio:** Short Video / Shorts Studio.

**Future studios:** Long Video, Social/Carousel, X/Thread, Blog/Article, Newsletter, Podcast/Audio and Campaign.

**Status:** Shorts Studio exists in part; future studio set is proposed.

### 4.5 Execution and Integration layer

**Target responsibilities**
- Run rendering and other compute-intensive tasks.
- Connect replaceable AI providers.
- Access permitted asset sources.
- Integrate platform publishing and analytics.
- Provide storage and execution services.

**Status:** Existing components cover parts of this layer. Always-on, persistent and recoverable execution is a target requirement, not a verified current capability.

---

## 5. Shared intelligence and Content Graph

### 5.1 Why a Content Graph is needed

A content item should not be an isolated folder containing a script and video. It should be connected to the decisions and evidence that produced it.

The target graph should connect:
- topics and ideas;
- research packages;
- sources and evidence;
- factual claims;
- brand rules and strategy;
- content briefs;
- scripts and format-specific drafts;
- storyboards and production plans;
- assets and rights records;
- rendered outputs;
- QA results;
- review and approval decisions;
- publishing records;
- analytics and learning.

### 5.2 Conceptual relationship map

```text
Topic / Idea
    |
    v
Research Package -----> Sources / Evidence
    |                         |
    v                         v
Content Brief <---------- Claims
    |
    v
Format-specific Draft
    |
    v
Studio Production Plan
    |
    +------> Assets / Rights
    |
    v
Produced Artifact
    |
    v
QA Result
    |
    v
Review / Approval
    |
    v
Publication Record
    |
    v
Analytics / Feedback
    |
    +------> Strategy and future research
```

This is a conceptual relationship map, not a finalized database schema.

### 5.3 Design requirements

The eventual data model should support:
- stable IDs and explicit entity relationships;
- versioned artifacts and policy records;
- source and claim provenance;
- many outputs derived from one research package;
- multiple studio outputs from one content idea;
- asset reuse with rights and attribution constraints;
- approvals bound to exact artifact versions;
- publication idempotency and history;
- analytics linked to the originating content and publication;
- archival and audit history.

### 5.4 Database decision

SQLite was considered as an initial local-first option, and an existing `workspace_sync.py` SQLite prototype was mentioned in the reconciliation context. SQLite is **not permanently selected** as the final architecture decision.

The target data model should be designed independently, then compared with the prototype. Preserve a migration path to PostgreSQL or another database if future scale and execution topology require it.

---

## 6. Specialized studios and ownership boundaries

### 6.1 Shared core versus studio responsibilities

| Shared Content OS responsibility | Specialized studio responsibility |
|---|---|
| Brand profile and global rules | Format-specific interpretation of brand rules |
| Content Graph and knowledge | Format-specific production artifacts |
| Research packages and source records | Format-specific research presentation needs |
| Cross-format strategy and briefs | Studio-specific scripts, plans and outputs |
| Global QA/rights/approval policy | Studio-specific validation signals |
| Workflow orchestration | Execution of studio production stages |
| Distribution authorization | Platform-ready output preparation |
| Cross-format analytics | Studio-specific production metrics |

### 6.2 Shorts Studio boundary

Shorts Studio should remain responsible for its production-specific work:
- accepting a Shorts production request;
- using the required research/brief inputs;
- producing script and visual planning artifacts;
- selecting/preparing visual assets;
- rendering the short-form video;
- returning artifacts, manifests and diagnostics.

The Content OS should own the shared lifecycle around it:
- content item identity and cross-format relationships;
- shared research and brand context;
- workflow orchestration;
- central QA, rights and approval decisions;
- distribution authorization;
- publication ledger and cross-format learning.

The exact API and artifact contract remain to be designed in Part 3 and reviewed before implementation.

---

## 7. Agent and worker architecture

### 7.1 Design direction

Agents should be specialized and operate under explicit contracts. The system should not rely on a large, loosely coordinated fleet of agents.

A future agent contract should define:
- purpose and scope;
- allowed inputs;
- expected outputs;
- tools and permissions;
- files/resources it may access;
- prohibited actions;
- quality requirements;
- failure and retry behavior;
- handoff conditions;
- evidence and audit requirements.

### 7.2 Agents versus deterministic services

Use agents where judgment, synthesis or creative reasoning is valuable:
- research synthesis;
- topic and angle exploration;
- script drafting and critique;
- creative planning;
- analysis of performance and recommendations.

Use deterministic code/services for critical invariants:
- schema validation;
- identity and version checks;
- rights gate enforcement;
- approval verification;
- idempotency;
- publishing authorization;
- audit records;
- state transitions.

Agents may recommend or prepare an action. They should not be the sole enforcement mechanism for critical safety or authorization rules.

### 7.3 Existing agent ownership

The existing ownership arrangement must remain unchanged unless the owner explicitly approves a change:

- **Qoder:** Phase 11 engineering owner.
- **OpenCode:** Phase 10 engineering/closure owner.
- **Kilo:** independent read-only QA; no source, test, configuration or Git modifications.

This is the ownership arrangement recorded in the architecture context, not a request to assign new work. Do not change ownership or create new agent assignments based on this document.

---

## 8. Workflow orchestration and execution model

### 8.1 Required capabilities

The target system should support:
- persistent workflow state;
- durable task queue;
- scheduling;
- worker execution;
- retries and backoff;
- cancellation;
- resumability after interruption;
- idempotent external actions;
- clear job status and diagnostics;
- manual intervention and review holds.

### 8.2 Control plane and execution plane

The user's requirement that the system continue working while the PC is off or the owner is unavailable for an extended period means a purely local process that depends on the PC being powered on is insufficient for all future workflows.

A proposed separation:

**Control plane**
- content state and workflow coordination;
- schedules and persistent queue;
- policy and approval state;
- monitoring, alerts and audit trail.

**Execution plane**
- research workers;
- AI/provider calls;
- local or remote rendering workers;
- asset processing;
- platform adapters.

A hybrid/cloud worker model may eventually keep orchestration active while local rendering remains an optional execution resource. The deployment model is not yet decided.

### 8.3 Local-first and future hybrid/cloud

Initial direction:
- keep the system free-first and local-first where practical;
- avoid premature infrastructure and paid services;
- define clean interfaces so remote workers can be added later;
- do not claim the system works while the PC is off until an always-on execution/control service is actually deployed and tested.

Cloud infrastructure, SaaS, multi-tenancy, billing and remote teams remain deferred.

---

## 9. Quality, rights, approval and publishing governance

### 9.1 Centralized enforcement

The target architecture should centralize critical decisions so that no alternate entry point can bypass them.

Required policy areas:
- factual evidence and claim support;
- storyboard and shot-plan validity;
- asset rights and attribution;
- technical output validity;
- brand and format compliance;
- review and approval;
- platform-specific publishing authorization.

### 9.2 Publishing outcomes

The conditional publishing model discussed so far is a **proposed preference, not a fully locked implementation policy**.

Conceptual outcomes:
- **Auto Publish:** Routine content that satisfies an owner-approved pre-authorized policy and every required gate.
- **Pending Approval:** Content that requires human review; hold until reviewed.
- **Blocked:** Rights, safety, validation or technical failure. Ordinary approval should not bypass a hard blocker.

Initial eligible formats discussed: `shorts_social` (Shorts, Reels and short-form social content). This remains subject to final policy approval and implementation testing.

Frequency was described as limited, but exact numerical limits are deferred. Platform-wise daily/weekly caps, overflow scheduling and other limits must be configurable rather than silently hardcoded.

Previously discussed review windows—12 hours for Shorts and 48 hours for long-form—remain proposals, not final locked settings. Long-form is not part of the initial auto-publishing eligibility described above.

### 9.3 Essential controls

Proposed controls:
- Automation Policy Engine;
- Quality Gate Engine;
- Approval Manager;
- Scheduler;
- Persistent Task Queue;
- Publishing Ledger and idempotency;
- Emergency Kill Switch;
- policy versioning and audit history.

No production auto-publishing rollout should occur without testing and explicit owner approval.

---

## 10. Analytics and learning loop

The target lifecycle should not end at publication.

It should connect:
- content item and format;
- platform publication record;
- performance metrics;
- audience response and feedback;
- experiment or hypothesis;
- lessons and recommendations;
- future strategy, research and content planning.

The reconciliation reports describe analytics collectors and feedback files, but do not establish that analytics and feedback are fully linked to content runs in one unified graph.

Proposed requirement: every metric or feedback record should be traceable to its platform, publication, content item, format and measurement window.

---

## 11. Current-state evidence versus target architecture

### 11.1 Report-backed current-state summary

Based on the available Phase 10/11 and Phase 0 reconciliation reports:

| Blueprint area | Report-based current state |
|---|---|
| Workspace & Control Center | No completed web workspace identified; API exists with reported limitations |
| Content Graph | Not established; artifacts are largely run/folder oriented |
| Knowledge Management | No unified shared knowledge layer established |
| Research Intelligence | Partial: topic discovery, research desk, claims and lineage components |
| Brand Intelligence | Not established as a shared brand system; brand assets were not supplied in the report context |
| Strategy & Planning | Partial: topic scoring/pillar-related functionality |
| Content Quality Intelligence | Partial; some checks exist, but claim enforcement is warning-oriented |
| Multiformat Creation Engine | Shorts pipeline exists; separate long-form work is reported; unified multiformat model not established |
| Asset Management & Rights | Partial; per-run assets/rights strings, no central registry |
| Automation & Agent Orchestration | Partial: stages, scheduler/n8n-related pieces and run tracker; no complete durable queue/agent contract system established |
| Distribution Studio | Partial: adapters and ledgers exist; direct paths can bypass intended controls |
| Analytics & Learning | Partial: collectors and feedback records exist, but run-level linkage is incomplete |

### 11.2 Important production blockers

The reconciliation identified these issues to carry forward:
- G1 storyboard gate defaults to `warn`, allowing `needs_review` to render.
- G2 rights gate is not reliably enforced at publishing; unknown rights are not reliably blocked.
- G3 unsupported factual claims are warnings rather than consistent publish blockers.
- U1 direct publishing adapters can publish publicly without expected approval; `publish_social.py --execute` was reported to skip approval.
- D1 direct `app.script.pipeline` entry can bypass quality gate, run identity, approval and sanitized failure handling.
- Traceability gaps include colliding ID namespaces, missing complete per-shot render manifest/plan hash and incomplete evidence/coverage checks.
- Run tracker tests exist, but runtime integration in `pipelines/short.py` remains unverified.
- API was reported unauthenticated and jobs in memory.
- Approval uses a single global slot; roles/signatures are not established.
- No centralized rights registry.
- Metadata schema is unversioned and artifact versions are inconsistent.
- Analytics/feedback are not reliably linked to runs.
- No live production publishing was verified.

### 11.3 Evidence limitations

This document relies on the available reconciliation reports and previous architecture decisions. It is not a fresh repository inspection. Exact code paths, schemas, runtime behavior and current working-tree state must be verified by an explicitly authorized agent before implementation.

The Phase 10 and Phase 11 test counts came from different report scopes/times and must not be combined into one universal test result. The independent Kilo QA report was unavailable during reconciliation.

---

## 12. Technology and design choices — open items

The following are design areas, not finalized technology decisions:

| Area | Current direction | Still to decide |
|---|---|---|
| Database | Local-first; SQLite prototype exists | Final schema, SQLite boundaries and migration path |
| Queue | Durable/persistent queue required | Technology and delivery semantics |
| Workers | Separate execution from control plane | Local, remote or hybrid deployment |
| API | Explicit studio/service contracts required | Authentication, schema and versioning |
| Storage | Artifact references and provenance required | Local/object storage strategy |
| AI providers | Replaceable provider interfaces preferred | Exact providers and adapter contracts |
| Scheduler | Persistent schedules required | Scheduler implementation and hosting |
| Observability | Diagnostics and audit history required | Logging, metrics and alerting stack |
| UI | Unified control center desired | Framework and implementation plan |

Technology selection should follow requirements and evidence, not familiarity or premature optimization.

---

## 13. Architecture delivery sequence

The agreed planning sequence is:

### Stage 0 — Existing System Reconciliation
- Understand current repository and existing system.
- Map implemented versus partial versus missing behavior.
- Identify risks and ownership boundaries.
- Do not modify the repository during read-only reconciliation.

### Stage 1 — Creator Workspace
- Define the owner-facing workspace and control center.
- Define core navigation, content status and review surfaces.

### Stage 2 — Shared Intelligence Core
- Define Content Graph and shared data model.
- Define knowledge, brand and research relationships.

### Stage 3 — Research and Strategy
- Define research packages, evidence, claims, topic intelligence and planning.

### Stage 4 — Multiformat Creation
- Define studio contracts and format-specific artifact models.
- Integrate Shorts Studio through a controlled adapter.

### Stage 5 — Quality and Automation
- Define central gates, rights policy, approval, queue, retries and agent contracts.

### Stage 6 — Distribution
- Define platform adapters, authorization, publishing ledger and duplicate protection.

### Stage 7 — Analytics and Learning
- Link performance and feedback to content lineage and future decisions.

### Stage 8 — Studio Expansion
- Add additional formats after the shared core and initial studio integration are stable.

### Priority framing

The Blueprint 2.0 priority direction is:
- **P0:** workspace foundations, Content Graph, brand memory, research/evidence model, briefs, human approval framework, multiformat data model and Shorts integration boundaries.
- **P1:** advanced research, trend radar, content gaps, multiformat creation, assets, automation and distribution preparation.
- **P2:** platform publishing, analytics, experiments, recommendations, scheduled intelligence, teams and hybrid/cloud expansion.

Priority labels do not mean all P0 work belongs in one sprint. Work should be sequenced into small, verifiable increments.

---

## 14. Implementation governance and non-negotiable restrictions

This document does not authorize implementation.

Unless the owner explicitly gives new permission:
- do not use Git or GitHub operations, including read-only operations;
- do not modify the private repository;
- do not edit source, tests, configuration or documentation;
- do not install dependencies or alter environments;
- do not change agent ownership;
- do not deploy;
- do not run production generation, uploads or publishing;
- do not assume a prompt was executed or a backup/commit exists;
- do not discard WIP or use broad cleanup/reset operations.

When implementation is later authorized:
1. Verify the exact current state.
2. Define the scope and file ownership.
3. Record a baseline.
4. Make a small isolated change.
5. Run focused tests, then relevant regression tests.
6. Independently review the change where appropriate.
7. Report exact commands, results, limitations and remaining risks.
8. Obtain approval before external side effects or promotion.

---

## 15. How coding agents should use this reference

When given this document:

1. Read it with `NEXTDECODE_Master_Blueprint_2.0` and Part 2.
2. Treat this document as the high-level architecture reference, not a complete implementation specification.
3. Separate report-backed current behavior from proposed target design.
4. Do not infer that a proposed module or contract already exists.
5. Produce a discrepancy and verification report before implementation.
6. Identify which decisions need owner input.
7. Do not expand scope or alter existing agent ownership.
8. Keep work reversible and preserve unrelated WIP.
9. Never bypass central rights, QA or publishing authorization.
10. Ask for explicit approval before any repository or external-system changes.

---

## 16. Next architecture work — Part 3

**NEXTDECODE System Architecture & Pipeline — Part 3: Technical Architecture Design**

Planned order:
1. Shared data model and Content Graph entities.
2. Persistent job queue and worker architecture.
3. Agent contracts and orchestration boundaries.
4. Centralized QA, rights and approval policy.
5. Shorts Studio integration API and artifact manifest.
6. Local-first now, hybrid/cloud-ready later.

The data model should first be designed independently, then compared with the existing `workspace_sync.py` SQLite prototype. The prototype must not dictate the target architecture merely because it exists.

---

**End of Part 1 — System Architecture Master Reference 1.0**
