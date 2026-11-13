# NEXTDECODE CONTENT OS
## Master Research, Product Strategy & Technical Architecture Blueprint

**Version:** 1.0  
**Date:** 31 October 2026  
**Status:** Strategic Blueprint — Proposed, Pending Owner Approval  
**Product:** NEXTDECODE Content OS  
**Existing Engine:** Shorts Studio  
**Development Strategy:** Hybrid — Proprietary Product + Carefully Selected Open-Source Components

---

# 1. Executive Vision

NEXTDECODE Content OS aims to become an AI-native content operating system that manages the complete lifecycle of content production.

It should not be merely a video generator, editing application, social media scheduler, or collection of AI agents.

It should connect research, editorial planning, script development, evidence verification, visual production, human approval, publishing, analytics, and continuous improvement into one coherent operating environment.

The platform should enable a creator or content team to:

1. Discover relevant topics and opportunities.
2. Research topics using reliable sources.
3. Build evidence-backed content strategies.
4. Generate and review scripts.
5. Plan visual storytelling.
6. Produce multiple content formats.
7. Review and approve deliverables.
8. Publish through controlled integrations.
9. Analyze performance.
10. Improve future content using measured results.

**Long-term vision:** One unified workspace where human creativity, AI agents, production tools, and performance intelligence work together.

## Product positioning

NEXTDECODE Content OS is an AI-powered content production and intelligence platform.

It is designed around:

- Research and evidence.
- Editorial intelligence.
- Controlled AI automation.
- Production reliability.
- Human approval.
- Multi-format output.
- Performance feedback.

It should prioritize quality, traceability, and reliability over simply maximizing automated output volume.

---

# 2. Product Principles

Every major technical and product decision should follow these principles.

## 2.1 Human-directed, AI-assisted

AI agents can research, propose, draft, plan, and execute approved operations.

However, high-impact actions require human authorization.

## 2.2 Evidence before publishing

Factual content must have traceable supporting evidence.

Unsupported factual claims must not silently pass production gates.

## 2.3 Fail closed

If a required production, approval, evidence, provenance, or rights check fails, the system must stop.

A failure must never be converted into a false success.

## 2.4 Reproducible production

Every production run should have:

- Unique run identity.
- Input and output records.
- Artifact hashes.
- Stage-level status.
- Failure diagnostics.
- Review history.
- Provenance.

## 2.5 Modular architecture

Research, scripting, visuals, voice, rendering, approval, publishing, and analytics should be independently testable modules.

## 2.6 Hybrid development

Build proprietary components for differentiated workflows.

Evaluate open-source components for commodity functionality, subject to licensing, security, and maintenance reviews.

## 2.7 Human-readable operations

Users must be able to understand what an agent is doing, why it is doing it, what failed, and what requires approval.

---

# 3. Existing Product Foundation

## 3.1 Shorts Studio

Shorts Studio is the existing production engine and the foundation of the wider platform.

Its current technology direction includes:

- Python backend and pipeline orchestration.
- FFmpeg-based video production.
- Research and claim processing.
- Script generation.
- Visual asset discovery.
- Motion and shot planning.
- Voice generation.
- Rendering and quality checks.
- Review and approval workflows.
- Publishing integrations.

The existing engine should remain specialized in dependable video production rather than being rewritten just to fit a new frontend architecture.

## 3.2 Existing architecture and work

The local working tree previously showed:

- 23 modified tracked files.
- 76 untracked entries.
- New modular rendering components.
- Research evidence and lineage components.
- Script evidence components.
- Visual ShotPlan and storyboard components.
- Run Tracker work.
- Additional tests and phase documentation.

These counts describe the previously reported working-tree state, not a fresh verification.

## 3.3 Important distinction

The remote GitHub repository was inspected previously and did not contain several newer local implementation paths.

Therefore:

- Remote `main` must not be assumed to contain the latest implementation.
- Local WIP must be preserved.
- The current local state and remote state must be reconciled before any future synchronization.
- No synchronization is authorized by this blueprint.

---

# 4. Product Architecture

The proposed architecture has seven major layers.

## Layer 1 — Unified Workspace

The primary interface for users.

Responsibilities:

- Workspace dashboard.
- Projects and channels.
- Content calendar.
- Production runs.
- Approval queue.
- Asset library.
- Notifications.
- System health.
- Activity history.

The user should be able to understand the status of the entire content operation from one location.

## Layer 2 — Agent and Workflow Orchestration

The execution layer connecting specialized AI agents and deterministic services.

Responsibilities:

- Agent registration.
- Task assignment.
- Workflow execution.
- State management.
- Tool permissions.
- Approval checkpoints.
- Retry policies.
- Failure propagation.
- Execution logs.

Agents must not receive unrestricted access to every operation.

Use explicit tool permissions and action-level authorization.

## Layer 3 — Research and Content Intelligence

Responsibilities:

- Topic discovery.
- Trend analysis.
- Source collection.
- Source reliability evaluation.
- Claim extraction.
- Evidence verification.
- Research lineage.
- Topic scoring.
- Content opportunity identification.

Every research package should be versioned and reviewable.

## Layer 4 — Content and Editorial Studio

Responsibilities:

- Content briefs.
- Audience definition.
- Editorial angle.
- Script generation.
- Hook development.
- Story structure.
- Script critique.
- Claim-to-sentence mapping.
- Version management.
- Editorial approval.

The editorial layer should maintain a clear distinction between verified facts, interpretation, opinion, and speculation.

## Layer 5 — Visual and Production Studio

Responsibilities:

- Narration beat extraction.
- ShotPlan generation.
- Storyboard creation.
- Asset discovery.
- Rights verification.
- Visual relevance assessment.
- Voice production.
- Audio processing.
- Motion planning.
- FFmpeg rendering.
- Technical QA.

Shorts Studio remains the initial production engine.

## Layer 6 — Distribution and Publishing

Responsibilities:

- Platform-specific output preparation.
- Upload authorization.
- Metadata validation.
- Privacy configuration.
- Scheduling.
- Publishing status.
- Retry and failure handling.

Publishing must remain approval-controlled.

No public upload should happen without explicit authorization.

## Layer 7 — Analytics and Optimization

Responsibilities:

- Content performance.
- Views and retention.
- Engagement.
- Watch-time analysis.
- Topic performance.
- Hook performance.
- Format comparisons.
- Editorial feedback.
- Future content recommendations.

Analytics should eventually feed insights into research and editorial planning.

It must not automatically rewrite production policy or publish content.

---

# 5. Proposed High-Level Technical Architecture

```text
                  NEXTDECODE CONTENT OS
                           |
                 Unified Workspace UI
                           |
                  Application API
                           |
              Authentication & Permissions
                           |
                Workflow Orchestration
                           |
      +--------------------+--------------------+
      |                    |                    |
  Research Agents     Editorial Agents      Production
      |                    |                    |
  Source Engine        Script Studio       Shorts Studio
  Claim Ledger         Critic Engine       Visual Planning
  Evidence Store       Version Control     Voice & Audio
      |                    |                    |
      +--------------------+--------------------+
                           |
                   Approval Service
                           |
                 Artifact & Run Tracker
                           |
                 Publishing Integrations
                           |
                  Analytics & Feedback
```

Cross-cutting services:

- Database.
- Artifact storage.
- Event and job queue.
- Audit log.
- Observability.
- Secrets management.
- Permission system.
- Configuration management.

This is a logical target architecture, not a claim that all these services already exist.

---

# 6. Recommended Technology Strategy

Technology selection should follow existing engineering strengths and product requirements.

## 6.1 Backend

**Primary recommendation: Python**

Reasons:

- Existing Shorts Studio compatibility.
- FFmpeg integration.
- Research and AI ecosystem.
- Existing modules can be retained.
- Strong testing and automation ecosystem.

FastAPI is a reasonable API candidate if the current API architecture needs to evolve, subject to implementation review.

## 6.2 Frontend

**Proposed direction: React + Next.js**

Use it for:

- Workspace dashboard.
- Project management.
- Content editor.
- Run history.
- Approval interface.
- Analytics dashboards.
- Workflow visualization.

The frontend should communicate with backend APIs rather than directly owning production logic.

## 6.3 Database

**Initial recommendation: SQLite where existing run-tracking requirements permit; PostgreSQL for the multi-user platform.**

PostgreSQL becomes more important when the platform requires:

- Multiple users.
- Concurrent jobs.
- Permissions.
- Shared workspaces.
- Workflow records.
- Analytics.
- Relational content provenance.

Migration should be planned, not rushed.

## 6.4 Background jobs

Evaluate a queue and worker architecture when the current orchestration model reaches its limits.

Potential candidates:

- Celery.
- Dramatiq.
- Redis-backed queues.
- Existing orchestration components.

Do not introduce a queue simply because it is popular.

## 6.5 AI integration

Use provider abstraction layers.

Avoid hard-coding one model provider into core product logic.

The system should support:

- Model selection by task.
- Structured output.
- Tool calling.
- Retry and timeout policies.
- Cost tracking.
- Prompt versioning.
- Evaluation.
- Fallback policy where safe.

Fallbacks must never bypass evidence, approval, or safety requirements.

---

# 7. Open-Source and Competitive Research Strategy

Open-source projects should be treated as research and integration candidates, not automatic dependencies.

## Genfeed.ai

Repository: https://github.com/genfeedai/genfeed.ai

Previously researched architecture:

- Next.js and React.
- NestJS.
- Prisma and PostgreSQL.
- Redis and BullMQ.
- AI-oriented content workflows.

License note: AGPL-3.0-or-later was identified in prior research.

Decision:

- Use it as an architectural reference.
- Do not copy or incorporate code without a license and legal compatibility review.
- Evaluate its workflows, user experience, and product concepts separately from code reuse.

## Other candidates

OpenFilm, Kinocut, Remotion, Langflow, and Flowise were previously identified for evaluation.

Their suitability, licensing, maintenance status, security, and actual integration value must be rechecked before selection.

No candidate is considered adopted by this blueprint.

## Build-versus-buy rule

Build proprietary capabilities when they create product differentiation.

Evaluate external tools for commodity capabilities.

Reject integrations that introduce excessive operational complexity, incompatible licensing, or loss of control over critical production gates.

---

# 8. Data Architecture and Provenance

The platform should maintain clear identities for important entities.

Proposed core entities:

- Workspace
- User
- Project
- Channel
- ContentIdea
- ResearchPackage
- Source
- Claim
- Script
- ScriptVersion
- Storyboard
- ShotPlan
- Asset
- AssetRightsRecord
- ProductionRun
- Artifact
- Approval
- PublishingJob
- PublishedContent
- AnalyticsSnapshot
- AgentTask
- WorkflowExecution
- AuditEvent

## Provenance requirements

Every production run should identify:

- Input content version.
- Research package version.
- Claim ledger version.
- Script version.
- Storyboard version.
- Selected assets.
- Asset rights evidence.
- Model and prompt version where available.
- Output artifact hashes.
- Approval identity and timestamp.
- Final run status.

A review package must not silently mix artifacts from different runs.

Historical records should remain immutable or versioned.

---

# 9. Reliability and Safety Architecture

These requirements are foundational, not optional enhancements.

## 9.1 Strong Pipeline

Strong Pipeline is mandatory for production.

Legacy or standard processing must never become an automatic recovery route.

## 9.2 Fail-Closed Execution

A failed production run must:

- Stop subsequent production stages.
- Avoid false success metadata.
- Avoid overwriting previous successful outputs.
- Record sanitized failure information.
- Preserve diagnostic evidence.

## 9.3 Human approval

Every required research package and storyboard must pass its configured approval requirements.

A `needs_review` state must block rendering where human approval is required.

No timeout-based automatic approval.

## 9.4 Evidence verification

Unsupported factual claims must block production.

Every factual narration sentence must map to claim evidence.

Missing or invalid references must not silently pass.

## 9.5 Media rights

Missing, unknown, or incompatible reuse rights must block publish readiness.

Attribution alone is not permission.

Rights provenance must be explicit.

## 9.6 Artifact integrity

The system must validate consistency between:

- Research package.
- Claim ledger.
- Script.
- Storyboard.
- Metadata.
- Video.
- Review package.
- Run manifest.

Stale or mixed artifacts must be rejected.

## 9.7 Publishing

Upload safety tests and mock integrations do not prove real-world upload safety.

Public publishing must remain disabled unless explicitly authorized.

---

# 10. Current Engineering Governance

Exactly three project agents have defined responsibilities.

## Qoder — Phase 11 Engineering Owner

Responsibilities:

- ShotPlan.
- Beat extraction.
- Visual query deduplication.
- Traceability.
- Phase 11 implementation and handovers.

Restrictions:

- Must preserve Phase 10 work.
- Must not modify unrelated owned files without authorization.
- Must provide evidence for implementation claims.

## OpenCode — Phase 10 Sole Engineering Owner

Responsibilities:

- Strict Fail-Closed closure.
- Run Tracker.
- Promotion journal.
- Failure recording.
- Review provenance.
- Phase 10 tests and handover.

Restrictions:

- Must not modify Phase 11 work owned by Qoder.
- Must not declare production readiness based solely on mocked tests.

## Kilo — Independent QA Owner

Mode: Strictly read-only.

Responsibilities:

- Adversarial testing.
- Static inspection.
- Regression verification.
- Evidence-based findings.
- PASS / FAIL / BLOCKED / NOT VERIFIED verdicts.

Restrictions:

- No source modification.
- No test modification.
- No Git operations.
- No implementation ownership.

## Owner approval

The owner controls:

- Product direction.
- Scope changes.
- File ownership changes.
- Production authorization.
- Publishing authorization.
- Git synchronization.
- Release readiness.

---

# 11. Phase-Based Product Roadmap

## Phase 0 — Repository and Engineering Reconciliation

Goal: Establish a trustworthy source of truth.

Deliverables:

- Local/remote reconciliation.
- WIP inventory.
- Backup verification.
- File ownership.
- Test baseline.
- Documentation organization.
- Release blockers.

Exit criteria:

- All work accounted for.
- No unreviewed destructive operations.
- Reliable test baseline.
- Clear implementation ownership.

## Phase 1 — Unified Workspace

Goal: Create one operational interface.

Deliverables:

- Dashboard.
- Projects and channels.
- Content status.
- Production history.
- Approval queue.
- Asset library.
- System health.

Exit criteria:

- User can inspect and navigate all important content operations from one workspace.

## Phase 2 — Agent and Workflow Layer

Goal: Create controlled AI-assisted execution.

Deliverables:

- Agent registry.
- Task management.
- Workflow definitions.
- Execution state.
- Permission controls.
- Human approval checkpoints.
- Audit trail.

Exit criteria:

- An agent can execute a permitted task with traceable state and without bypassing authorization.

## Phase 3 — Research and Content Intelligence

Goal: Make content discovery evidence-driven.

Deliverables:

- Topic discovery.
- Research packages.
- Claim ledger.
- Source lineage.
- Evidence verification.
- Editorial opportunity scoring.

Exit criteria:

- Research output is traceable and reviewable.

## Phase 4 — Visual and Production Studio

Goal: Stabilize and expand Shorts Studio.

Deliverables:

- Structured ShotPlan.
- Storyboard.
- Visual asset selection.
- Rights checks.
- Voice and audio.
- Rendering.
- Technical QA.
- Review package.

Exit criteria:

- Production is reproducible and blocks unsafe or unapproved outputs.

## Phase 5 — Multi-Format Content Studio

Goal: Move beyond short-form video.

Potential formats:

- YouTube long-form.
- Shorts.
- Instagram Reels.
- Carousels.
- Social posts.
- Newsletters.
- Research briefs.

Exit criteria:

- Shared research and editorial foundations can support multiple output formats without duplicating the entire system.

## Phase 6 — Analytics and Optimization

Goal: Connect published content performance to future editorial decisions.

Deliverables:

- Performance dashboards.
- Retention insights.
- Topic comparisons.
- Hook analysis.
- Format performance.
- Feedback recommendations.

Exit criteria:

- Recommendations are measurable and explainable.

## Phase 7 — Platform Expansion

Potential future capabilities:

- Multiple workspaces.
- Team collaboration.
- Role-based permissions.
- Additional platforms.
- API access.
- External integrations.
- Subscription and billing model.

This phase should only begin when the core product is stable.

---

# 12. Phase 10 and Phase 11 Acceptance Criteria

## Phase 10

Required verification:

1. Strong Pipeline mandatory.
2. CLI and API default to Strong.
3. Standard mode requires explicit opt-in.
4. No automatic legacy fallback.
5. Failed execution cannot produce false success.
6. Previous successful outputs survive failure.
7. Scheduler propagates failures.
8. Diagnostics are sanitized.
9. Run identity is recorded.
10. Promotion journal detects incomplete promotion.
11. Mixed artifacts cannot be approved.
12. Full regression suite passes.

OpenCode reported a full-suite result of 535 passed, 0 failed, 0 skipped on 31 October 2026.

This remains an agent-reported result until independently reproduced.

A live production generation run remains NOT VERIFIED in the supplied handover.

## Phase 11

Required verification:

1. Narration beat extraction.
2. Complete ShotPlan coverage.
3. Stable shot IDs.
4. Narration references.
5. Claim and evidence references.
6. Invalid evidence flags.
7. Query normalization.
8. Global query deduplication.
9. Query reuse limits.
10. Visual-intent preservation.
11. ShotPlan traceability into review and production outputs.
12. Human approval and rights gates.

Qoder's implementation claims and Kilo's static inspection must be distinguished from independently executed tests.

---

# 13. Existing Critical QA Findings

The following findings were present in the supplied Kilo Phase 11 audit.

| Finding | Issue | Required disposition |
|---|---|---|
| G1 | `needs_review` does not block rendering under the reported default warning gate | Open until verified fixed |
| G2 | Missing `reuse_rights` may not block publish readiness | Open until verified fixed |
| G3 | Unsupported factual claims are flagged but may not block execution | Open until verified fixed |
| G4 | Strict Fail-Closed had two reported failing tests in the earlier audit | Reconcile with OpenCode's later reported fixes |
| UPL-03 | No non-public upload destination was available in the reported audit | Do not attempt public upload |

Other reported concerns include empty provenance, missing claim references, unmapped factual sentences, and incomplete end-to-end validation.

These are historical findings. Their current state must be checked against the actual local implementation.

**Release policy:** No release-ready declaration while a P0 safety or approval blocker remains unresolved.

---

# 14. Security, Privacy and Operational Governance

The platform should eventually implement:

- Environment-based secret storage.
- No credentials in source control.
- Least-privilege service permissions.
- Per-agent tool permissions.
- Human approval for high-impact operations.
- Sanitized logs.
- Artifact access controls.
- Audit history.
- Backup and recovery procedures.
- Dependency and license scanning.
- Secure upload handling.

No production credentials or private tokens should be stored in documentation.

---

# 15. Product Quality Metrics

Success should be measured across quality, reliability, and usefulness.

## Research

- Source coverage.
- Claim evidence coverage.
- Unsupported claim rate.
- Research review rejection rate.

## Editorial

- Script acceptance rate.
- Revision count.
- Hook quality.
- Editorial review time.

## Production

- Render success rate.
- Render duration.
- QA rejection rate.
- Asset rights completeness.
- Output reproducibility.

## Operations

- Workflow failure rate.
- Recovery time.
- False-success incidents.
- Approval turnaround.
- Artifact integrity failures.

## Business and audience

- Watch time.
- Retention.
- Engagement.
- Publishing consistency.
- Content performance by topic and format.

Numerical targets should be established only after a baseline measurement period.

---

# 16. Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Over-automation | Unsafe output or publishing | Human approval and explicit permissions |
| Weak evidence | Misinformation | Claim-level verification |
| Rights uncertainty | Legal and platform risk | Fail-closed rights checks |
| Agent overlap | File conflicts | Explicit ownership boundaries |
| Monolithic architecture | Difficult maintenance | Modular services |
| Excessive integrations | Operational complexity | Selective hybrid strategy |
| Unverified QA reports | False release confidence | Independent reproducible tests |
| Data inconsistency | Invalid approvals | Provenance and hashes |
| Provider dependence | Cost and availability risk | Provider abstraction |
| Scope expansion | Delayed delivery | Phase gates and owner approval |

---

# 17. Architecture Decision Log

The following decisions are proposed or previously selected.

| Decision | Status |
|---|---|
| Complete Content OS + Hybrid approach | Previously selected |
| Shorts Studio remains the production engine | Existing strategic direction |
| Python + FFmpeg foundation | Existing technical direction |
| React/Next.js frontend | Proposed |
| PostgreSQL for multi-user scale | Proposed |
| Controlled agent execution | Proposed |
| Human approval for critical actions | Required product principle |
| Genfeed code reuse | Not approved |
| Open-source component adoption | Requires evaluation |
| Public upload | Not authorized |
| GitHub synchronization | Not authorized at this stage |

Any future change should record its reason, alternatives, impact, owner, and approval status.

---

# 18. Next Execution Plan

## Immediate priorities

1. Preserve and reconcile existing local WIP.
2. Complete Phase 10 verification under OpenCode.
3. Continue Phase 11 under Qoder.
4. Have Kilo independently verify implementation and blockers.
5. Reconcile all three agent reports.
6. Establish a verified engineering baseline.
7. Approve the next product architecture phase.

## What must not happen yet

- No GitHub push.
- No public publishing.
- No unapproved agent ownership transfer.
- No automatic fallback to legacy production.
- No weakening of QA assertions.
- No large-scale frontend rewrite before backend boundaries are understood.
- No open-source code adoption without license review.

---

# 19. Definition of Done for NEXTDECODE Content OS

The platform should not be considered mature simply because it can generate a video.

A mature Content OS should demonstrate:

1. Reliable research.
2. Evidence-backed content.
3. Editorial consistency.
4. Structured visual planning.
5. Verified media rights.
6. Reproducible production.
7. Human-controlled approvals.
8. Safe publishing.
9. Measurable analytics.
10. Traceable agent execution.
11. Recoverable failures.
12. Clear user control.

The ultimate measure is whether the platform can reliably manage the complete content lifecycle, with humans retaining meaningful control over decisions and publication.

---

# 20. Final Strategic Recommendation

Do not build a giant platform in one step.

Build the operating foundation first.

**Stage 1:** Make Shorts Studio reliable.

**Stage 2:** Turn its existing capabilities into reusable services.

**Stage 3:** Build the unified workspace and agent orchestration.

**Stage 4:** Connect research, editorial, and production.

**Stage 5:** Add multi-format workflows.

**Stage 6:** Close the feedback loop with analytics.

This sequence reduces unnecessary rewrites and allows the product to grow on a verified engineering foundation.

## Final Product Vision

NEXTDECODE Content OS should become the operating system behind a complete content operation:

**Discover → Research → Verify → Strategize → Create → Produce → Review → Approve → Publish → Analyze → Improve.**

The platform should make complex content operations understandable, controllable, measurable, and repeatable.

**End of Master Blueprint — Version 1.0**