# NEXTDECODE Content OS — Contract Inventory & Change Control

**Document ID:** ND-P1-CON-001 | **Version:** 0.1.0-draft | **Date:** 2026-11-04  
**Status:** DRAFT — P0 remains authoritative; this inventory does not freeze new schemas.

## 1. Authority

Primary contract sources:
- NEXTDECODE Canonical Contracts Pack 1.0.
- Accepted P0 Architecture Decision Baseline 1.0.
- P0 WP-0 Final Reconciliation Closure Record 1.0.
- Existing Shared Intelligence Core Contracts 01–12.
- NEXTDECODE Module-to-Contract Traceability Matrix 1.0.
- Architecture Parts 1–8.
- API/Event Contract Standard 1.0 and P0 WP reconciliation records.

P0 WP-0 explicitly says existing artifacts must be reused and not duplicated. This file is only a navigation/inventory aid.

## 2. Existing contract families to reconcile

| Contract family | Existing source | P1 use | Review status |
|---|---|---|---|
| Audience identity/context | Shared Intelligence Core Contract 01 | Audience context for research/strategy/content | Not fully reviewed in this pass |
| Opportunity/evidence | Shared Intelligence Core Contract 02 | Research/claims/evidence | Not fully reviewed in this pass |
| Brand/editorial intelligence | Shared Intelligence Core Contract 03 | Brand rules and voice | Not fully reviewed in this pass |
| Knowledge/learning | Shared Intelligence Core Contract 04 | Knowledge and learning lifecycle | Not fully reviewed in this pass |
| Research intelligence operations | Shared Intelligence Core Contract 05 | Research workflows and evidence operations | Not fully reviewed in this pass |
| Strategy/portfolio intelligence | Shared Intelligence Core Contract 06 | Planning and prioritization | Not fully reviewed in this pass |
| Content quality/rights governance | Shared Intelligence Core Contract 07 | Quality and rights | Not fully reviewed in this pass |
| Audience performance | Shared Intelligence Core Contract 08 | Analytics/feedback | Not fully reviewed in this pass |
| Business/monetization | Shared Intelligence Core Contract 09 | Future business intelligence | Not assumed in initial P1 implementation |
| Agent/resource orchestration | Shared Intelligence Core Contract 10 | Agent permissions and orchestration | Not fully reviewed in this pass |
| Distribution/channel publishing | Shared Intelligence Core Contract 12 | Export/distribution boundary | Publishing remains disabled absent separate policy |
| Canonical API/event | API/Event Contract Standard 1.0 | Cross-module communication | Existing baseline; detail review pending |
| Canonical entities/states/artifacts | Canonical Contracts Pack 1.0 | P0/P1 shared identity and artifacts | Partial content review; approval pending |
| Job/worker contracts | Architecture Parts 4–5 and WP-3 reconciliations | Durable execution | Need cross-check of detailed final freeze artifacts |
| Governance/approval/authorization | Architecture Part 6; policy authorization matrix; CF/ADR records | Protected actions and learning | Need canonical enum/contract reconciliation |

## 3. Canonical invariants to preserve

- UUIDv7 canonical identity; entity IDs and version identity are distinct.
- ContentItem and ContentVariant semantics follow accepted CF decisions; do not substitute a conflicting ContentIdea hierarchy without formal decision.
- Every cross-domain reference is typed; a reference does not imply permission.
- Separate lifecycle state machines remain separate.
- P0 CF-20 rights and CF-21 approval vocabularies from WP-0 closure are authoritative.
- Quality outcomes follow P0 accepted ADR-008.
- Approval, authorization, execution and publication are distinct.
- Event delivery is at-least-once tolerant; consumers idempotent.
- Large media binaries use artifact storage, not queue JSON payloads.
- Shorts Studio remains specialist engine and is not replaced.

## 4. Contract catalogue needed for P1

| Proposed P1 contract | Required fields/concepts | Dependency |
|---|---|---|
| Research Package | run/version, topic, sources, evidence, claims, uncertainty, methods, provenance | Shared Core 02/05 |
| Claim/Evidence link | claim/source/evidence IDs, relation type, source location, confidence, version | Shared Core 02 |
| Brand Context | brand profile version, voice, audience, constraints, allowed/prohibited patterns | Shared Core 03 |
| Content Brief | content item ID, format/studio, research refs, brand ref, audience, objective, constraints | Shared Core 01/03/05 |
| Studio Execution Request | workflow/task refs, studio, capability, input refs, version, idempotency, deadline | Parts 2/4/5/7 |
| Production Manifest | run, exact inputs/assets/tools/config, outputs/checksums and provenance | Parts 2/7 |
| Quality Evaluation | artifact/version, checks, outcome, severity, evidence and policy version | Shared Core 07 / Part 6 |
| Rights Assessment | asset ID, rights state, intended use, territory/platform/commercial scope, evidence, expiry/revocation | Shared Core 07 / CF-20 |
| Approval Record | reviewer, decision, exact artifact/hash and version, review package, timestamp | CF-21 / Part 6 |
| Authorization Decision | actor, capability, resource, destination, policy version, result, reason, expiry | Part 6 |
| Learning Proposal | evidence, problem, impact, risk, dependencies, candidate version, rollback and test report | Shared Core 04 |
| Notification Policy | creator bounds, critical exceptions, digest cadence, event grouping, preferences | Governance design; schema open |
| Incident Record | severity, trigger/evidence, affected capability, containment, recovery, recurrence | Governance/operations; schema open |
| Export Package | exact artifacts, manifests, checksums, rights/provenance and delivery metadata | Shared Core 12 / Part 7 |

All rows above are inventory proposals, not finalized schemas.

## 5. Compatibility and versioning rules (Recommended default)

- Each contract has a stable ID, semantic version and designated owner.
- Additive optional changes may be backward-compatible only if consumers ignore unknown fields safely.
- Changes to required fields, semantics, enums or authorization meaning require a new major version or explicit migration.
- Consumers declare supported version ranges.
- Producers cannot silently change the meaning of existing fields.
- Deprecation requires migration guidance, telemetry and an agreed sunset window.
- Policy/security contract changes require governance review and staged activation.
- Breaking changes require consumer inventory and test evidence.
- Keep previous contract definitions immutable in history.

Exact version policy (SemVer vs alternative), support window and migration duration remain Open.

## 6. Contract change process

1. Change proposal with reason, owner and affected contracts.
2. Consumer/provider dependency analysis.
3. Compatibility and security impact review.
4. Migration plan and rollback.
5. Candidate schema validation.
6. Unit, contract and cross-module integration tests.
7. Staging validation.
8. Owner authorization for accepted changes.
9. Versioned release and controlled migration.
10. Monitor and rollback where required.

No P1 agent or module may unilaterally edit a canonical shared contract.

## 7. Known blockers and missing review

- Canonical Contracts Pack was partially retrieved (first 1,000 of 1,499 lines); remaining 499 lines require review.
- Master Blueprint 2.0 DOCX was located but not extracted in this pass.
- Fast Closure Master Plan exact path read failed; locate/confirm its path before claiming review.
- Shared Intelligence Core Contracts 01–12 and traceability matrix need full reconciliation with the P1 scope.
- Detailed WP-1 through WP-6 contract reconciliation artifacts and accepted CF-01–CF-24 references must be cross-checked before contract freeze.
- Do not invent field-level schemas from summary material.

## 8. Acceptance criteria

- Every P1 contract maps to an existing canonical source or is explicitly proposed as new.
- Each contract has an owner and consumers.
- No duplicate conflicting entity or enum definitions.
- Rights and approval enums match accepted CF decisions.
- Version changes have compatibility and migration tests.
- Security-sensitive contract changes require explicit approval.
- Contract acceptance evidence is recorded in the existing decision/contract process.
