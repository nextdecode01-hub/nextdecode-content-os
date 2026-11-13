# NEXTDECODE Contract 12 — Distribution, Publishing & Authorization Boundary Reconciliation
**Document ID:** NEXTDECODE-C12-RECON-0.1  
**Version:** 0.1 | **Date:** 2026-11-04  
**Status:** Working source reconciliation — documentation only  
**Contract freeze:** NOT GRANTED | **Implementation authorization:** NOT GRANTED

## 1. Purpose and disposition
Reconcile Contract 12 (Distribution, Channel & Publishing Intelligence Model 1.0) against accepted centralized authorization, Contract 07 governance, Contract 10 orchestration, Contract 11 creation, Part 7 artifact integration, the Data Dictionary, and common lifecycle/API-event standards.

**Disposition:** Contract 12 owns distribution-domain records and coordinates adapters; Contract 07 owns quality/rights/governance/approval and centralized authorization; WP2/Contract 10 owns durable execution coordination; WP3 owns worker trust; Part 7/WP4 owns artifact registration and immutable artifact-version integrity. Contract 12 must not grant publishing authority to itself or treat schedule approval as authorization.

This is a logical ownership reconciliation, not a frozen schema, endpoint set, enum catalogue or provider implementation.

## 2. Source set reviewed
- Contract 12 v1.0, especially §§1–4, 7–9, 13–15.
- Contract 07 v1.0 and Contract 07 CF-20/CF-21 reconciliation 0.1.
- Accepted ADR-007/008 and CF-20/21/22 baseline.
- Data Dictionary v1.1 as latest working reference for CF-20/21; v1.0 retained pending formal supersedes decision.
- Contract 10 v1.0; Contract 11 v1.0 and its cross-source reconciliation.
- API/Event Contract Standard 1.0; Unified Lifecycle & State Transition Standard 1.0; Batch 16 reading copy.
- WP5 and WP6 ownership/acceptance boundaries.

## 3. Canonical ownership map

| Record / capability | Canonical owner | Contract 12 relationship | Status |
|---|---|---|---|
| ChannelProfile and capability snapshot | Distribution / Contract 12 | Owns versioned platform capability context | Source-aligned; details open |
| ChannelAccount reference and permitted-operation context | Distribution references account; identity/credential authority remains centralized | Must not own raw credentials or infer permission from connection | Owner detail open |
| DistributionStrategy | Contract 12 | Owns recommendation and channel rationale | Source-aligned |
| ChannelSuitabilityAssessment | Contract 12 | Owns assessment, evidence and confidence | Source-aligned |
| DistributionPackage and package versions | Contract 12 | Owns channel-specific package metadata and version lineage | Source-aligned; immutable binding open |
| ScheduleProposal / schedule calendar record | Contract 12 | Owns proposal and scheduling domain state | Source-aligned |
| Quality result / rights decision / approval decision | Contract 07 / WP5 | Consumes authoritative references; never duplicates writable authority | Accepted boundary |
| PublishingAuthorization decision | Contract 07 / WP5 | Requests and consumes decision; cannot issue it | Accepted boundary |
| PublishOperation / external operation attempt | Distribution business record; execution coordinated by WP2, adapter performs side effect | Owns business-facing operation record; execution/attempt semantics align with WP2 | Dependency open |
| Worker identity, credentials, lease, fencing | WP3 | Consumes eligible worker assignment only | Accepted boundary |
| Artifact / ArtifactVersion / integrity metadata | Part 7 / WP4 | References exact immutable versions and hashes | Accepted boundary |
| Publication / platform object and confirmed visibility | Contract 12 | Owns observed distribution outcome, not platform truth beyond evidence | Source-aligned |
| Analytics metric definitions and attribution | Contract 08 | Supplies channel context and provenance | Accepted boundary |
| Emergency pause and protected-action policy | Contract 07 / centralized policy | Checks at action boundary; distribution may surface operation status | Semantics open |

A distribution record may reference governance and execution records, but must not create shadow writable copies of their authoritative state.

## 4. Mandatory authorization binding at side-effect boundary
Contract 12 §8 requires centralized authorization before every external upload/publish action. Reconcile with ADR-007 and CF-22:

1. Adapter/executor obtains a current authorization decision from the centralized authority. A caller-provided ALLOW, prior UI state, cached approval, event receipt or schedule state is not proof.
2. Decision must be checked against exact operation context: workspace/brand/studio; canonical content and exact ArtifactVersion; artifact hash/integrity reference; exact DistributionPackage version and package hash where defined; channel/platform; account identity; operation type; intended visibility/destination; schedule/time window; policy version; required QA and rights evidence; approver/actor context; expiry/revocation state.
3. Fail closed when any required identity, version, evidence, permission, policy or outcome is missing, ambiguous, expired, revoked or unverifiable.
4. Material changes to asset bytes/version, package metadata, destination/account, operation type, visibility, schedule window or policy invalidate the relevant authorization and require revalidation.
5. Authorization is distinct from approval, execution, upload confirmation, publication confirmation and independent public-visibility verification.
6. The same boundary applies to API calls, scheduled jobs, manual tools, direct scripts, retries, alternate workers and provider adapters. No bypass path.
7. Public automatic publishing remains disabled unless a separate explicit owner-approved policy authorizes a narrowly defined scope. Human silence/unavailability is never approval.

**Open exactness:** The sources support these binding dimensions conceptually. Final canonical field names, decision-token structure, signature/attestation method, expiry semantics and policy-version lookup protocol remain to be specified and owner-reviewed; this document does not invent them.

## 5. External operation and uncertain outcome rules
Contract 12 §9 and Contract 10 recovery rules align: an unknown external outcome must be reconciled before retry.

Keep distinct: intent/request accepted; durable operation/job created; provider request submitted; upload confirmed; publication/schedule confirmed; public visibility independently verified; failed/rejected; reconciliation required; and platform-confirmed private/unlisted/processing/removed/restricted states.

For timeout, lost response or worker loss after submission:
1. Mark outcome unknown / reconciliation required.
2. Preserve operation ID, idempotency key, package/version/hash, account, destination and provider correlation identifiers.
3. Query provider through supported lookup/reconciliation mechanisms.
4. Record observed evidence and confidence; missing search results are not proof of non-execution unless provider semantics support that conclusion.
5. Retry only after the prior side effect is determined not to have occurred, authorization remains valid, and retry is authorized.
6. If provider cannot resolve outcome, keep unresolved and escalate; do not blind-retry.

Provider lookup strategy and retention horizons are provider-specific and remain open.

## 6. Lifecycle and event alignment
Contract 12 contains at least three state families: DistributionPackage lifecycle; ScheduleProposal/schedule lifecycle; PublishOperation and Publication/external outcome lifecycle.

Do not compress these into one distribution_status or reuse workflow/job status. WorkflowRun/Job/JobAttempt belong to orchestration; package state belongs to distribution; governance decisions belong to Contract 07; platform-observed publication state belongs to Contract 12 as an evidence-backed observation.

Each committed transition uses the common lifecycle/event envelope and owner-domain state version. A schedule event does not authorize publishing. A publish-requested event is not proof of publication. A platform response is evidence to record and verify, not permission to continue unrelated operations.

## 7. Confirmed conflicts, gaps and owner decisions

| ID | Issue | Evidence / impact | Required disposition |
|---|---|---|---|
| C12-01 | Authorization binding not expressed as one complete cross-contract tuple | Contract 12 §8.4 lists asset hash/version, package version, channel/account, operation, time window, policy version, approver/time; Contract 07 owns authorization | Owner review exact fields, expiry, revocation and signature/evidence semantics |
| C12-02 | Public visibility vs upload/publication confirmation | Contract 12 §9 distinguishes upload, publish and visibility; schema vocabulary not normalized across lifecycle/dictionary | Define separate observable states and evidence; no inference |
| C12-03 | PublishOperation vs WorkflowRun/Job/JobAttempt boundary | Contract 12 records external operation; Contract 10/WP2 owns durable execution and attempts | Agree relationships/cardinality and authoritative state ownership |
| C12-04 | Unknown provider outcome / retry | Contract 12 §9.3 and Contract 10 §11 require reconciliation before retry | WP2/WP6/provider adapter test oracle; provider semantics open |
| C12-05 | Emergency pause during in-flight provider request | Contract 12 §13 requires pause controls; cannot recall an already accepted external request by assumption | Owner decision on pause scopes, cancellation capability, escalation and post-submit reconciliation |
| C12-06 | ChannelAccount credential ownership | Contract 12 stores credential reference/scopes; WP3 owns worker trust and central identity/security policy governs secrets | Clarify account-credential vault/identity boundary; no raw secret in records/logs |
| C12-07 | Authorization of update/delete/takedown/community actions | Contract 12 lists operation types and community/takedown workflows; protected-action catalogue open | Contract 07/WP5 enumerate action classes and human-approval requirements |

## 8. Dependency map to workstreams
- **WP1:** canonical identities, typed references, versioned relationships and persistence boundary; do not expand WP1 into provider execution.
- **WP2:** durable operation scheduling, job/attempt relationship, idempotency, retry classification and reconciliation orchestration.
- **WP3:** worker identity, scoped credentials, capability checks, lease/fencing and revocation.
- **WP4:** exact Artifact/ArtifactVersion/hash references, immutable manifests and integrity verification.
- **WP5:** quality/rights/approval/authorization, protected-action catalogue, policy versioning, emergency pause and revocation.
- **WP6:** acceptance oracle for denied action, changed artifact/package, expired/revoked authorization, duplicate request, uncertain provider outcome, pause in-flight, private/unlisted vs public visibility, and audit trail.

## 9. Acceptance criteria for reconciliation closure
- Every Contract 12 entity has one canonical owner and typed references to other owners.
- Every external side effect is guarded by current centralized authorization at adapter boundary.
- Authorization binding identifies exact content/artifact/package version, hash, account, destination, operation, visibility, time window and policy context.
- Public auto-publishing remains disabled absent separate owner authorization.
- Upload, publication, visibility and monitoring are distinct evidence-backed outcomes.
- Unknown outcomes cannot trigger blind retry.
- Workflow/job/attempt state is not conflated with distribution or publication state.
- Pause, revocation and in-flight operation behavior is specified or visibly owner-reserved.
- API/event and lifecycle envelopes use one common semantic model.
- WP6 tests are defined before separately authorized implementation.

## 10. Disposition
**Contract 12 reconciliation: PARTIALLY CLOSED at logical ownership and safety-invariant level.** C12-01 through C12-07 remain open for exact schema/owner decisions. No contract freeze, repository change, provider connection, agent assignment, test execution, public publishing or implementation authorization is granted.
