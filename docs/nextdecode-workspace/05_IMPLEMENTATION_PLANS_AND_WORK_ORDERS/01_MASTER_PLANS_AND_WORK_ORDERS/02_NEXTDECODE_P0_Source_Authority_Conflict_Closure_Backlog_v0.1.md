# NEXTDECODE P0 — Source Authority, Conflict & Closure Backlog

**Document ID:** ND-P0-WA-CONFLICT-001  
**Version:** 0.1  
**Prepared:** 3 November 2026  
**Status:** Evidence-based working backlog — owner review required  
**Phase:** P0  
**Part:** Governance, architecture and shared contracts  
**Work package:** Wave A / WA-02 — Authority and conflict reconciliation  
**Layer:** Shared governance; backend contract impact  
**Backend / frontend:** Shared; backend contracts are primary, frontend consumes canonical semantics  
**Implementation authorization:** NOT GRANTED  
**Storage:** `P0/00-governance-and-owner-decisions/source-conflicts`

## 1. Purpose

Convert discovered inconsistencies into an actionable closure backlog. This document does not decide conflicts. Each issue must be routed to its canonical owner and closed with source-backed evidence.

## 2. Source authority order

Batch 15 states this hierarchy:
1. Explicit owner decision records and accepted ADR/CF decisions.
2. Locked project constraints and architecture decision records.
3. Canonical Data Dictionary and API/Event/Lifecycle standards.
4. WP-1 through WP-6 specifications.
5. Derived decision-resolution/consolidation registers.
6. Reconciliation documents and summaries.

A later date, fuller document or newer filename does not automatically supersede a higher-authority source. Preserve both references and obtain the designated owner disposition.

## 3. Conflict register

| ID | Conflict / gap | Evidence | Impact | Owner / route | Required closure evidence | Priority |
|---|---|---|---|---|---|---|
| C-01 | ADR acceptance status differs | Accepted baseline says ADR-001–010 accepted; ADR pack/register still show pending/proposed | Reopening accepted architecture or misclassifying decisions | Governance / owner | Original approval evidence, exact versions, dates and supersession trail | P0 blocker |
| C-02 | Rights vocabulary differs | ADR-009 baseline differs from later CF-20/Batch17 vocabulary | Rights enforcement and persistence schema risk | Contract 07 owner | Explicit disposition and canonical vocabulary/version; no automatic mapping | P0 blocker |
| C-03 | Working ODR vs original owner decisions | B15 says ODR-01–22 is a complete derived working register, not proof every ODR was an original owner decision | Decision authority/traceability risk | Governance controller | Row-by-row mapping to accepted ADR/CF/owner-review source | P0 blocker |
| C-04 | Artifact 08 duplicates and v1.0/v1.1 relationship | Duplicate Library copies and text extraction; B15 describes v1.1 as supplement, not supersession of v1.0 | Wrong source version may be used | Documentation control / owner | Content comparison, hashes, approval metadata and explicit supersession | P0 blocker |
| C-05 | Detailed contract freeze remains pending | B03, B11, B13, B15, B16, B17, B18 and B24 state candidate/review status | Implementation against moving contracts | Owner + domain owners | Freeze record listing exact documents/versions/exceptions | P0 blocker |
| C-06 | Agent Actor linkage is a proposal | AGW-001 proposes `AgentIdentity.actor_ref` | Identity and authorization context | Identity & Security + Contract 10 | Reference type, ownership, uniqueness and lifecycle decision | High |
| C-07 | Batch 18 schemas/routes/errors not fully frozen | B18 says examples illustrative and detailed schemas/routes need owner freeze | Backend/frontend integration mismatch | API owner + WP2/WP3/Part5/WP4/WP5 | Versioned schema bundle and field-level traceability | P0 blocker |
| C-08 | Batch 19 physical schema choices open | B19 leaves DB engine/version, types, indexes, isolation and migration tooling for review | Persistence implementation risk | WP1 + WP2 + owner | Approved physical design and migration/restore plan | High |
| C-09 | Security parameters unresolved | B20 has owner-reserved MFA, roles, permissions, token/session, credentials and key-management decisions | Authentication/authorization risk | Identity & Security / WP3 / WP5 | Approved policy and threat-model disposition | P0 blocker for protected operations |
| C-10 | Observability thresholds/destinations unresolved | B21 is a candidate; no monitoring stack/exporter/alert destination configured | Operational readiness cannot be claimed | Operations owner | Metric definitions, thresholds, routes and privacy/retention decisions | High |
| C-11 | Release/environment details unresolved | B22 candidate; deployment/release and migration choices pending | Cannot claim deployability | Operations/release owner | Environment matrix, release/rollback and migration approval | High |
| C-12 | Backup/DR targets unresolved | B23 candidate; numeric RPO/RTO/WRT need owner targets and rehearsal | Cannot claim recoverability | Data/operations owner | Approved targets and tested restore/recovery evidence | High |
| C-13 | Performance/capacity/cost targets unresolved | B24 leaves workload assumptions, quotas, capacity and spend thresholds open | Cannot claim performance or cost readiness | Owner + operations/architecture | Workload profile, measurement method, approved targets or deferrals | High |
| C-14 | Batch inventory completeness unknown | Current Library search located B02, B03, B05, B11–B24, not exact B01/B04/B06/B09; B07/B10 ambiguous | Progress denominator and dependencies unknown | Documentation controller | Complete inventory and alternate-name mapping | P0 blocker |
| C-15 | Frontend source coverage not established | Current inventory is mainly backend/shared contracts; no authoritative frontend package inventory confirmed | Frontend work may be invented or omitted | Frontend architect / owner | Frontend artifact inventory and contract consumer map | Medium |
| C-16 | Notion source search limitation | Connector search reported Business-access requirement; general results unrelated | Potential source gap | Workspace access owner | Valid access or alternate source-of-truth confirmation | Medium |
| C-17 | P0 implementation/evidence state unproven | B13 is not implementation authorization; prior audit lacked live whole-chain verification | P0 acceptance cannot be claimed | WP6 + independent QA + owner | Current baseline, reproducible tests, independent review and acceptance record | P0 blocker |

## 4. Required conflict treatment

- Do not silently merge enum values.
- Do not treat derived ODR groupings as accepted owner decisions.
- Do not infer detailed freeze from accepted ADR/CF decisions.
- Do not infer implementation permission from tool access, repository access, existing credentials or a detailed work order.
- Do not claim a test passed unless current baseline, command, environment and output are recorded.
- Do not collapse approval, rights, QA, authorization and external-operation outcome into one status.
- Do not map local `reuse_rights: permitted` to canonical `CLEARED`.
- Preserve old versions and evidence; record supersession rather than overwriting.

## 5. Consolidated owner-review pack

The owner-facing pack should contain:
1. Accepted decisions carried forward unchanged, with source/version evidence.
2. Genuine owner-intent conflicts (C-01, C-02, C-04, C-05 and reserved decisions).
3. Already delegated/accepted decisions with evidence; do not ask again.
4. Proposed technical defaults within delegated scope, clearly marked proposed.
5. Deferred decisions and safe interim behavior.
6. Exact contract freeze scope and exclusions.
7. Separate P1 implementation authorization request.
8. Separate protected external-action authorization requests only if later required.

## 6. Priority closure sequence

1. C-14: complete source inventory and denominator.
2. C-01/C-03/C-04: establish owner-decision provenance and source precedence.
3. C-02: rights vocabulary/CF-20 resolution.
4. C-06/C-07: Agent–Worker and Batch 18 interface closure.
5. C-08 through C-13: WP-1/WP-3/WP-6 and operations specifications.
6. C-05: consolidate exact freeze set and owner approval.
7. C-17: authorized implementation, reproducible evidence and independent QA.
8. P0 acceptance and separate P1 authorization.

**This backlog makes remaining work actionable; it does not close conflicts or authorize implementation.**
