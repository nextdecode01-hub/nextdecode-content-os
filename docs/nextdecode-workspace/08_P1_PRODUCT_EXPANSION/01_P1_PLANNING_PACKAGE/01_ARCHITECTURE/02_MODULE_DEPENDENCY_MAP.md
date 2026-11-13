# NEXTDECODE Content OS — P1 Module Dependency Map

**Document ID:** ND-P1-ARCH-002 | **Version:** 0.1.0-draft | **Date:** 2026-11-04  
**Status:** DRAFT — planning map; dependencies must be reconciled with the P0 module-to-contract traceability matrix.

## 1. Dependency principles

- Shared contracts are the integration boundary.
- Domain ownership remains explicit; consumers use contracts, not private storage.
- P0 canonical identity, persistence, job, worker, artifact and governance boundaries are prerequisites.
- P1 module dependencies are logical dependencies, not necessarily separate deployable services.
- No module is considered implemented merely because it appears in this map.

## 2. Logical module dependency map

| Module/capability | Depends on | Provides | Status |
|---|---|---|---|
| Workspace & Creator Control | Identity, workspace, permissions, workflow state, audit | Creator interaction, configuration, review actions | Recommended default |
| Content Graph | Canonical entities, IDs, persistence, versioning | Topic/idea/item/variant relationships and lineage | P0/P1 boundary; reconcile |
| Knowledge Management | Source/evidence/artifact registry, provenance | Reusable knowledge and indexed evidence references | Recommended default |
| Research Intelligence | Topic discovery, source registry, evidence/claim contracts, model adapters | Research packages, claim maps, uncertainty and source assessments | Recommended default |
| Brand Intelligence | Brand profile/context contracts, content graph | Brand constraints, audience/voice context | Recommended default |
| Strategy & Planning | Research, brand context, content graph, feedback signals | Priorities, content plans, opportunity recommendations | Recommended default |
| Content Quality Intelligence | Claims/evidence, brand rules, rights, quality policy | Evaluation reports, defects, warnings and blockers | Governance dependent |
| Multiformat Creation Studios | Briefs, research, brand context, studio contracts, artifacts | Scripts, posts, newsletters, podcast/video production artifacts | Recommended default |
| Asset Management | Artifact/asset metadata, rights registry, storage abstraction | Reusable asset references and use-specific rights evidence | P0 contract dependency |
| Agent Orchestration | Workflow/task/job, worker registry, capabilities, policy and audit | Bounded task execution and coordinated workflows | P0 execution dependency |
| Distribution Studio / Export | Approved artifact versions, rights, approval and authorization policy | Private export bundles and delivery records | Export-only direction |
| Analytics & Learning | Content/version/run/distribution links, event/metric contracts | Performance evidence, feedback and improvement proposals | Data lineage dependency |

## 3. Recommended dependency sequence

1. P0 WP-1 minimum canonical domain/persistence contracts.
2. P0 WP-2 durable execution and job semantics.
3. P0 WP-3 worker identity/capabilities/contracts.
4. P0 WP-4 artifact registration and transfer boundary.
5. P0 WP-5 quality/rights/approval/authorization enforcement.
6. P0 WP-6 vertical-slice integration and recovery validation.
7. P1 shared intelligence context and content-graph extensions.
8. Research and evidence workflows.
9. Brand and strategy workflows.
10. Multiformat studio adapters and content production.
11. Quality review, export, analytics and controlled learning.
12. Workspace surfaces and operational reporting aligned to stable backend contracts.

This is a dependency-oriented proposal, not a sprint schedule or implementation authorization.

## 4. Critical cross-domain relationships

- Research Package references sources, evidence items and claims; it does not copy authoritative source records.
- Content Brief references exact Research Package and Brand Profile versions.
- Content Item references its Content Idea and format/studio identity.
- Studio workflow references exact input versions and emits Artifact versions.
- Quality evaluation references exact claims, evidence, artifact and applicable policy versions.
- Approval references exact reviewed item/artifact version and review package.
- Authorization is separate from approval and is checked at the protected action boundary.
- Export package includes artifact manifest, checksums, provenance and applicable rights/approval evidence.
- Analytics events reference immutable content/version/run/distribution identities.
- Learning proposals reference the evidence, affected policy/configuration versions and evaluation report.

## 5. Parallel development boundaries (Recommended default)

Parallel feature development may proceed only when:
- shared contracts are versioned and agreed;
- one owner controls each contract;
- backend and frontend use the same schema version;
- integration tests validate both sides;
- breaking changes use explicit migration windows;
- P0 vertical-slice scope is not expanded into a full dashboard.

## 6. Blockers

- Detailed P0 domain and lifecycle contracts are not fully frozen.
- Canonical contract pack requires full review and owner disposition of open/proposed details.
- P0 current repository baseline and implementation ownership are governed by separate authorization.
- Research/Brand/Strategy contracts must be cross-checked with Shared Intelligence Core Contracts 01–12 and traceability matrix.
- UI scope must be checked against P0-A exclusions and separate approvals.

## 7. Acceptance criteria

- Every module has an explicit data/contract owner.
- Every dependency references a versioned contract.
- No circular dependency requires direct access to another module's internals.
- P0 foundation dependencies are distinguished from P1 module dependencies.
- Each output has a downstream consumer and validation criteria.
- Export and learning remain blocked by required governance and provenance evidence.

