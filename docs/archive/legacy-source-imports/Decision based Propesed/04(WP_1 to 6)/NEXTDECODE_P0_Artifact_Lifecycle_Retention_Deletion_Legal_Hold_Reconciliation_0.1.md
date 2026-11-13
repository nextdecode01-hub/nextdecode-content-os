# NEXTDECODE — P0 Artifact Lifecycle, Retention, Deletion & Legal Hold Reconciliation

**Document ID:** `NEXTDECODE_P0_Artifact_Lifecycle_Retention_Deletion_Legal_Hold_Reconciliation_0.1`  
**Version:** 0.1  
**Date:** 1 November 2026  
**Status:** DESIGN RECONCILIATION — OWNER REVIEW REQUIRED  
**Scope:** WP-4; X-09; ODR-13; dependencies across WP-1, WP-5 and WP-6  
**Detailed contract freeze:** NOT GRANTED  
**Implementation authorization:** NOT GRANTED  
**Tests executed:** NONE

---

## 1. Purpose and disposition

This document deepens X-09 beyond the partial lifecycle treatment in `NEXTDECODE_P0_Artifact_Contract_Reconciliation_0.1`.

It defines a provider-neutral candidate boundary for artifact retirement, deletion requests, dependency assessment, legal hold, recovery, purge authorization and physical purge. It also addresses metadata/binary consistency, shared references, audit preservation and failure recovery.

It does **not** set legal policy, retention periods, purge authority, provider behavior or implementation details. It does not amend accepted ADR/CF decisions.

**Disposition:** X-09 is substantially clarified at the logical-contract level. It remains **OPEN / OWNER-RESERVED** for legal-hold authority and release, irreversible purge authority, retention obligations and durations, backup deletion propagation, audit-evidence disposition, and shared-resource decisions. This document is a design candidate, not a freeze or execution authorization.

## 2. Source authority and status labels

Apply the existing source precedence:

1. Accepted owner decision record and ADR-001–ADR-010 / CF-01–CF-24.
2. Governing canonical data dictionary, API/Event Contract Standard and Unified Lifecycle/State Transition Standard.
3. WP-1 through WP-6 specifications.
4. Consolidated Contract Appendix.
5. Artifact Contract Reconciliation and this document as subordinate candidate clarifications.

Labels used below:

- **ACCEPTED BASELINE:** already established by accepted ADR/CF decisions.
- **SOURCE-DEFINED:** explicitly required by existing WP/source material.
- **RECONCILED:** clarifies an existing boundary without changing policy.
- **PROPOSED:** conservative candidate detail requiring owner review.
- **OPEN / OWNER-RESERVED:** requires explicit owner or policy decision.
- **DEFERRED:** intentionally postponed; no assumption may be made in its place.

## 3. Accepted and source-defined invariants

The following are not new decisions:

1. Canonical Artifact and ArtifactVersion identities are immutable.
2. An ArtifactVersion represents exact immutable content; changed bytes create a new version.
3. A manifest references exact ArtifactVersions, not a mutable Artifact pointer.
4. Relational metadata is authoritative; binary storage is behind a provider-neutral abstraction.
5. A storage locator is neither canonical identity nor authorization.
6. Read, write, transfer, export, share and delete are distinct permissions.
7. Deletion is dependency-aware and recovery is controlled.
8. Retiring a parent must not cascade-delete historical production evidence, approvals, audit records or artifacts.
9. Retention durations remain deferred.
10. Legal-hold and irreversible-purge authority remain owner-reserved.
11. Rights expiry/revocation/restriction is not equivalent to a deletion instruction.
12. Quarantine blocks ordinary downstream use; it does not itself erase content or evidence.
13. State transitions and protected actions remain attributable and centrally authorized.
14. Approval, authorization, execution and confirmed external outcome remain separate.
15. No production publishing or external side effects are authorized by this design work.

## 4. Lifecycle operations must remain distinct

The following are separate commands/decisions. They must not be collapsed into one generic `DELETED` status.

| Operation | Meaning | Immediate effect | Does it remove bytes? |
|---|---|---|---|
| Retirement | Withdraw an entity/version from ordinary active use | Prevents new ordinary use according to policy; preserves lineage/history | No |
| Deletion request | Attributable request to assess a precisely scoped target | Opens a controlled assessment; does not imply approval | No |
| Dependency assessment | Discover references, obligations, holds and downstream impact | Produces a scoped impact/evidence record | No |
| Logical deletion / tombstone | Mark a target as logically withdrawn/deleted under an approved policy | Hides or denies ordinary access as policy requires; retains control metadata | No, not by itself |
| Legal hold | Preserve specified information and block incompatible disposition | Places a preservation restriction on exact scope | No |
| Purge authorization | Central decision permitting a specific irreversible purge | Authorizes only the exact approved scope and operation | No, authorization only |
| Physical purge | Irreversibly remove eligible bytes and/or metadata | Executes the approved purge plan | Yes |
| Restore / recovery | Re-establish an eligible prior version or service state | Restores verified bytes/metadata under controlled procedure | May reintroduce bytes, never silently rewrites history |

**PROPOSED:** model these as explicit commands and attributable records, not merely values in a single lifecycle column.

A request, assessment, authorization and execution must each have their own identity and outcome. A request is never a purge grant.

## 5. Scope and dependency graph

### 5.1 Dependency discovery

Before any logical deletion or purge can be approved, the system should discover and record, at minimum:

- Artifact and every ArtifactVersion in scope.
- ArtifactManifest versions that include the target version.
- Assets and shared reusable sources, where relevant.
- ContentItem, ContentVersion and ContentVariant references.
- Workflow, WorkflowTask, Job, JobAttempt and execution evidence.
- Research, script, storyboard, visual, voiceover, subtitle, render and export derivatives.
- ValidationRecord and QuarantineRecord evidence.
- Rights evidence and rights assessments.
- QA results, review snapshots and approval decisions.
- Authorization decisions and access/transfer records.
- Distribution records, platform/external references and publication evidence.
- Audit/event history, outbox/inbox references and recovery evidence.
- Backups, replicas, caches, temporary transfer objects and provider-side copies, where their existence is known.
- External references and shared consumers not owned by the artifact domain.

### 5.2 Typed references and no cascade

**ACCEPTED / SOURCE-DEFINED:** canonical entity ownership remains singular; references do not confer ownership or permission. WP-1 recommends restrictive references/no cascade, but exact SQL foreign-key actions are not frozen.

**PROPOSED:**

- Dependency assessment traverses typed references and records the traversal scope, time, source and completeness.
- Unknown or unresolvable references produce `NEEDS_REVIEW` or `BLOCKED`; they do not count as absent.
- Shared artifacts are not purged merely because one consumer retires or requests deletion.
- Parent retirement must not cascade into child artifacts, versions, manifests, approvals, audit or distribution evidence.
- Purge planning must identify references that will be retained, detached, tombstoned, redacted or removed, and why.
- Cross-workspace references must be checked against workspace boundaries and central authorization.
- A dependency graph snapshot is evidence of what was assessed at a point in time; it is not a permanent guarantee that no new references can appear.

**OPEN:** exact graph query semantics, reference catalogue completeness, handling of legacy/untyped references, concurrent reference creation and whether a deletion lock/fence is required.

### 5.3 Revalidation before execution

**PROPOSED:** immediately before physical purge, re-check dependencies, holds, retention constraints, authorization expiry/revocation and target identity/hash/version. A material change since approval invalidates the plan and requires reassessment or renewed authorization.

## 6. Artifact, version and manifest disposition

**ACCEPTED BASELINE:**

- Artifact and ArtifactVersion are distinct.
- ArtifactVersion bytes and historical evidence are immutable.
- Manifest identity/version is immutable and components reference exact ArtifactVersions.
- Approval/review/distribution are bound to exact versions.
- A repaired or changed file creates a new ArtifactVersion.

**PROPOSED:**

1. Retirement may apply to an Artifact, a specific ArtifactVersion, a ManifestVersion or a higher-level content entity; the scope must be explicit.
2. Retiring an Artifact does not rewrite or delete historical ArtifactVersions.
3. A version-specific purge request must identify the exact ArtifactVersion ID and registered content hash.
4. A manifest remains evidence of the composition that existed at its creation time. If a component becomes unavailable or is purged, the manifest's historical record is not silently rewritten.
5. A purge process may mark a manifest component as unavailable under a separate, attributable disposition record, but must preserve the original manifest bytes/identity where policy requires.
6. New versions do not inherit old approvals automatically.
7. If one version is purged but other versions remain, the Artifact's remaining lifecycle and `current_version` semantics require an explicit transition; do not infer that the whole Artifact is purged.
8. If an Artifact is shared by multiple owners/consumers, the dependency and retention obligations of all known references must be considered before purge.

**OPEN:** whether manifest bytes can ever be purged independently of manifest metadata; exact version/parent lifecycle vocabularies; how `current_version_id` behaves after retirement/purge; shared ownership resolution.

## 7. Logical deletion and access behavior

**PROPOSED candidate behavior:**

- A logical deletion/tombstone makes the target unavailable to ordinary user and workflow discovery, subject to separately authorized legal, audit, investigation and recovery access.
- The tombstone retains canonical identity and a minimal disposition pointer so references do not become ambiguous.
- Reads, exports, shares, transfers and writes are evaluated independently; a `DELETE` permission does not imply those permissions.
- Logical deletion does not satisfy a physical purge obligation unless the applicable policy explicitly says so.
- A logically deleted item cannot be silently recreated under the same canonical identity. Reinstatement, if permitted, is a new attributable lifecycle transition, not identity replacement.
- Cached or indexed projections must be reconciled so ordinary discovery does not continue exposing withdrawn content.
- A storage locator or cached local copy cannot bypass the logical access restriction.

**OPEN:** exact visibility rules, tombstone retention, authorized exception roles and reinstatement policy.

## 8. Legal hold and preservation controls

### 8.1 Hold record

**PROPOSED logical record:** `LegalHoldRecord` with:

- immutable `legal_hold_id`;
- workspace and exact target scope (entity/version/manifest/artifact set);
- hold type/source/reference, without exposing sensitive legal detail unnecessarily;
- reason/category and supporting evidence references;
- requested_by and created_at;
- status and effective interval;
- authority/decision reference;
- scope expansion or reduction history;
- release request, release authority and release decision references;
- audit/event references.

The exact fields and vocabulary are not frozen.

### 8.2 Hold enforcement

**PROPOSED:**

- An active hold blocks incompatible logical deletion, physical purge, backup expiration that would destroy held copies, and destructive cleanup of held evidence.
- Hold scope must be explicit. A hold on one ArtifactVersion must not silently expand to every version unless the hold decision says so.
- A hold on a parent may require preserving identified descendants and dependencies; the dependency assessment must record that scope.
- Multiple holds may overlap. Releasing one hold does not release another.
- Hold status is evaluated at request time and rechecked immediately before execution.
- Hold state cannot be overridden by an ordinary content approval, QA pass, worker capability, retry or local operator action.
- A hold must not be inferred from a rights restriction or quarantine flag; these are separate governance dimensions.

### 8.3 Authority reserved to owner

**OPEN / OWNER-RESERVED — no authority invented here:**

- Who may request, impose, expand, narrow or release a legal hold.
- Whether the system may apply an emergency preservation hold automatically and who can confirm/release it.
- Which external legal/compliance sources are authoritative.
- Required evidence and review/appeal route.
- Treatment of conflicting or overlapping holds.
- Required response to an urgent preservation request.

Until those are decided, the safe behavior for a potentially held or ambiguous target is fail-closed: block destructive action and route for owner review.

## 9. Retention classes and durations

No numeric retention period or legal obligation is selected in this document.

**PROPOSED architecture:** define versioned retention policies by record class and applicable context, rather than a single global expiry. Candidate classes for policy design include:

- production content and final deliverables;
- source assets and licensed inputs;
- ArtifactVersions and manifests;
- research/source evidence;
- QA, review and approval evidence;
- rights and licence evidence;
- authorization, access and transfer logs;
- workflow/job/worker execution history;
- distribution and external publication evidence;
- security/quarantine/investigation evidence;
- backups, replicas, caches and temporary transfer data.

Each future policy should identify: record class, scope, trigger event, retention start point, minimum/maximum period if applicable, hold interaction, disposition action, exceptions, policy version, approving authority and evidence requirements.

**OPEN / OWNER-REVIEW:** actual classes, durations, legal basis, trigger semantics, jurisdictional scope, contractual obligations, retention start/end calculations, and whether audit metadata can ever be purged.

**DEFERRED:** provider lifecycle-rule syntax and backup/replication mechanics. Deferral is acceptable only if the future storage boundary can enforce approved policy and report deletion/reconciliation evidence.

## 10. Rights expiry, revocation and restrictions

**ACCEPTED BASELINE:** rights states are `UNKNOWN`, `PENDING_REVIEW`, `CLEARED`, `RESTRICTED`, `EXPIRED`, `REVOKED`, `DENIED`. Rights are use-specific and are not interchangeable with approval or authorization.

**RECONCILED:**

- Rights expiry/revocation/restriction blocks the affected use according to the rights contract.
- It does not automatically mean the source bytes must be deleted.
- It does not erase the evidence that the content was previously created, reviewed, distributed or used.
- A rights-driven removal request may initiate a deletion/disposition assessment, but physical purge still requires the applicable retention, hold, dependency and authorization checks.
- Evidence needed to explain historical use or demonstrate compliance must be preserved where policy requires it.
- Rights status and artifact lifecycle remain separate state dimensions.

**OPEN:** rights-specific preservation obligations, takedown/removal workflow, evidence retention and whether derived artifacts must be restricted, transformed or disposed of under a given rights decision.

## 11. Quarantine, restore and recovery

**ACCEPTED BASELINE:** quarantine blocks ordinary downstream use; revalidation creates new evidence; repair creates a new immutable version; quarantine release does not automatically clear rights, QA, approval or authorization blockers.

**PROPOSED:**

- Quarantine and legal hold are independent. A quarantined item may also be held; neither state implies the other.
- Quarantine does not authorize purge.
- Investigation access is narrowly scoped and centrally authorized.
- Restore is not a shortcut around quarantine, rights, approval or authorization gates.
- Restore must verify exact identity, expected hash/size, provenance and applicable validation profile.
- A restore that creates a new physical copy records the source version, restoration attempt, actor, time, storage boundary and integrity result.
- Restoring an old version does not make it current or approved automatically.
- A failed restore leaves the prior logical state intact and records the failure.
- If bytes are restored after a completed purge due to backup recovery or provider behavior, the system must not silently expose them; they remain isolated pending reconciliation and policy decision.

**OPEN:** restore window, recovery-point/recovery-time objectives, restore authority, quarantine investigation roles, and whether restored bytes re-enter the same ArtifactVersion storage location or a new replica.

## 12. Metadata/binary consistency and partial failure

Relational metadata is authoritative; binary storage is abstracted. The system must handle the fact that metadata and bytes may not commit atomically across different systems.

**PROPOSED purge protocol:**

1. Create a deletion/disposition request with exact target IDs, versions, hashes and reason.
2. Authenticate requester and authorize request creation.
3. Capture dependency graph and relevant retention/hold evidence.
4. Obtain required owner decision(s) and a central authorization decision bound to exact scope, operation, policy version and expiry.
5. Revalidate dependencies, hold state, authorization and target hashes immediately before execution.
6. Mark the target as purge-pending / inaccessible under an approved state transition, without destroying the audit trail.
7. Issue an idempotent provider-neutral binary deletion command for exact storage objects/replicas.
8. Record each storage operation result and reconcile retries/timeouts.
9. Update authoritative metadata only when the defined completion predicate is met; retain a tombstone/disposition record as policy requires.
10. Verify no known replica/cache/temporary object remains in scope, or record an explicit unresolved exception.
11. Close the operation with an immutable evidence summary.

The labels `PURGE_PENDING`, `PURGED`, `PURGE_FAILED` and `RECONCILIATION_REQUIRED` are **PROPOSED**, not accepted lifecycle enums.

### 12.1 Failure cases

- **Metadata committed, binary delete failed:** target remains inaccessible; operation stays incomplete/reconciliation-required; retry only under same valid scope/authorization or obtain renewed authorization.
- **Binary delete succeeded, metadata update failed:** do not restore bytes automatically; reconcile storage observation with authoritative metadata and complete the disposition record safely.
- **Timeout with unknown provider outcome:** treat outcome as unknown, not success or failure; query/reconcile exact object state before retry.
- **Some replicas deleted, others not:** no global purge success; record per-replica outcome and keep target restricted.
- **New reference appears after assessment:** invalidate stale plan; reassess before purge.
- **Authorization expires or is revoked mid-operation:** stop further actions; record what already happened; reconcile partial outcome; do not broaden or silently resume under expired authority.
- **Backup or cache still contains bytes:** do not claim complete physical purge; apply the approved backup/cache policy and record residual state.
- **Provider returns ambiguous confirmation:** retain `UNKNOWN_OUTCOME`/reconciliation status; no success assertion without evidence.

### 12.2 Idempotency and fencing

**PROPOSED:** purge commands must be idempotent for the exact same canonical request. Reusing an idempotency key with a different canonical payload must conflict. Every attempt is attributable. Stale workers/attempts cannot overwrite newer operation state. A retry cannot expand target scope, change hash/version, bypass a hold or renew its own authorization.

## 13. Audit and evidence preservation

**SOURCE-DEFINED:** transitions are attributable; audit/event history is immutable or reconstructable; historical approvals and production evidence must not be cascade-deleted.

**PROPOSED minimum evidence for every lifecycle operation:**

- request/operation ID and operation type;
- exact canonical targets, version IDs and content hashes;
- requester, decision-maker, executor and worker identities;
- reason and evidence references;
- dependency-assessment snapshot and completeness result;
- applicable retention policy version and evaluation;
- legal-hold checks and outcomes;
- QA/rights/approval context where relevant;
- central authorization decision, scope, expiry and revocation status;
- per-object/per-replica operation attempts and outcomes;
- timestamps, correlation/causation/trace references and idempotency identity;
- final disposition and unresolved exceptions.

Do not put secrets, credentials or unnecessary sensitive content in audit/event payloads. Preserve enough non-content evidence to explain what was requested, authorized, executed and observed.

**OPEN / OWNER-RESERVED:** whether audit metadata itself may ever be purged, under what authority, and how immutable audit obligations interact with privacy/legal deletion obligations.

## 14. Central authorization and protected-action rules

**ACCEPTED BASELINE:** ADR-007 / CF-22 establish centralized authorization; default-deny/fail-closed; adapters and workers cannot bypass it.

**PROPOSED protected actions:**

- `ARTIFACT_RETIRE`
- `ARTIFACT_DELETE_REQUEST`
- `ARTIFACT_LOGICAL_DELETE`
- `LEGAL_HOLD_APPLY`
- `LEGAL_HOLD_RELEASE`
- `ARTIFACT_PURGE_AUTHORIZE`
- `ARTIFACT_PURGE_EXECUTE`
- `ARTIFACT_RESTORE`
- `ARTIFACT_AUDIT_PURGE`

These names are candidate action identifiers, not frozen API enums.

Authorization must bind at least: actor, action, workspace, exact targets/versions/hashes, dependency-plan reference, policy version, legal-hold evaluation, destination/storage boundary where relevant, expiry and decision ID.

A general `DELETE` capability, worker capability declaration, approval decision or local administrator flag must not be sufficient by itself to execute irreversible purge.

**OPEN / OWNER-RESERVED:** identity of purge approver, separation-of-duties requirement, dual-control threshold, emergency path, legal-hold authority and audit purge authority.

## 15. WP-6 acceptance test oracles — proposed, not executed

Run only later in an owner-approved isolated synthetic environment. No real user content, production storage or external side effects.

| Test ID | Scenario | Expected oracle | Traceability |
|---|---|---|---|
| LIFE-01 | Retire a ContentItem with historical artifacts, approvals and audit | Parent is retired; historical records remain; no cascade deletion | ART-16, VS-xx |
| LIFE-02 | Submit deletion request | Attributable request exists; no bytes removed | X-09 |
| LIFE-03 | Dependency graph contains a shared ArtifactVersion | Shared consumer is identified; purge is blocked or scoped pending owner decision | X-09 |
| LIFE-04 | Dependency graph has unknown/unresolved reference | Destructive action is blocked/needs review | X-09 |
| LIFE-05 | Active legal hold covers exact version | Logical deletion/purge is denied | ART-17 |
| LIFE-06 | One of two overlapping holds is released | Remaining hold still blocks purge | X-09 |
| LIFE-07 | Hold scope is narrower than Artifact | Unheld version is not silently included; exact scope enforced | X-09 |
| LIFE-08 | Rights state changes to REVOKED | Affected use is blocked; evidence is retained; no automatic purge | CF-20 |
| LIFE-09 | Purge authorization targets version/hash A; bytes change or target B is substituted | Execution denied; authorization cannot be reused | CF-22 |
| LIFE-10 | Authorization expires before execution | Execution denied; new authorization required | CF-22 |
| LIFE-11 | New dependency appears after assessment | Stale plan invalidated; reassessment required | X-09 |
| LIFE-12 | Binary delete fails after logical restriction | Item remains inaccessible; operation is incomplete/reconciliation-required | X-09 |
| LIFE-13 | Binary delete succeeds but metadata update fails | No false success; reconciliation completes without silent byte restoration | X-09 |
| LIFE-14 | Provider outcome times out/unknown | State remains unknown/reconciliation-required until observed | API-EVT |
| LIFE-15 | Only some replicas are deleted | No global purge success; residual replicas recorded | X-09 |
| LIFE-16 | Restore returns bytes with checksum mismatch | Restored bytes remain unavailable/quarantined; failure evidence retained | WP-4 |
| LIFE-17 | Restore succeeds for a historical version | Exact version is restored; current pointer/approval is not silently changed | WP-4 |
| LIFE-18 | A stale worker retries an old purge attempt | Fencing rejects stale mutation; no scope expansion | WP-2/WP-3 |
| LIFE-19 | Same idempotency key, same purge payload | Same logical operation result; no duplicate logical purge | API-EVT |
| LIFE-20 | Same idempotency key, different target/hash | Conflict; no mutation | API-EVT |
| LIFE-21 | Audit evidence is queried after purge | Required disposition and execution evidence remains reconstructable | WP-1/WP-6 |
| LIFE-22 | A storage locator is supplied without authorization | Access/deletion denied | WP-4 |
| LIFE-23 | Purge request is made while retention eligibility is unknown | Destructive action blocked pending policy evaluation | X-09 |
| LIFE-24 | Quarantine exists without legal hold | Quarantine blocks ordinary use; purge still requires independent authorization | WP-4/WP-5 |
| LIFE-25 | Purge completes but cache/index still exposes content | Operation is not declared fully reconciled; exposure is corrected and evidenced | X-09 |

The `VS-xx` reference in LIFE-01 is intentionally not assigned a fabricated WP-6 test number; the exact mapping must be added during the consolidated test-ID crosswalk.

## 16. Open decision register

| ID | Decision | Status |
|---|---|---|
| X09-OD-01 | Retention classes and exact durations | OWNER-REVIEW; no values selected |
| X09-OD-02 | Legal-hold request/apply/expand/release authority | OWNER-RESERVED |
| X09-OD-03 | Irreversible purge approval authority and separation of duties | OWNER-RESERVED |
| X09-OD-04 | Whether emergency preservation holds may be applied automatically | OWNER-RESERVED |
| X09-OD-05 | Whether audit metadata can ever be purged and under what authority | OWNER-RESERVED |
| X09-OD-06 | Shared Asset/Artifact disposition when consumers have different obligations | OWNER-RESERVED |
| X09-OD-07 | Legal/privacy/contractual deletion policy and jurisdictional scope | OWNER-REVIEW |
| X09-OD-08 | Backup/replica/cache retention and deletion propagation | DEFERRED operational design; policy hooks required |
| X09-OD-09 | Restore window, RPO/RTO and restore authority | OPEN / OWNER-REVIEW |
| X09-OD-10 | Tombstone visibility, retention and reinstatement semantics | OPEN |
| X09-OD-11 | Dependency graph completeness and concurrent-reference fencing | OPEN |
| X09-OD-12 | Exact lifecycle state vocabularies and transition ownership | OPEN; reconcile governing Lifecycle Standard |
| X09-OD-13 | Purge command idempotency, retry and unknown-outcome reconciliation | OPEN; reconcile API/Event and WP-2 |
| X09-OD-14 | Provider-specific purge evidence and backup guarantees | DEFERRED; no provider selected |
| X09-OD-15 | Rights-driven takedown and evidence-preservation policy | OWNER-REVIEW |

No numeric retention period, legal policy, purge approver, provider, backup guarantee or audit-purge authority is invented here.

## 17. Cross-document reconciliation and required follow-through

- **WP-1:** retain canonical identity, restrictive/no-cascade recommendation and immutable transition history; exact FK actions remain open.
- **WP-2:** use durable idempotent commands, attempt history, leases/fencing and explicit unknown outcomes for purge/restore work.
- **WP-3:** workers are bounded executors; worker trust/capability does not grant purge authority.
- **WP-4:** ArtifactVersion, Manifest, TransferRecord, ValidationRecord and QuarantineRecord remain distinct; binary storage is provider-neutral.
- **WP-5:** central authorization and rights/QA/review/approval remain separate; holds and purge are protected actions.
- **WP-6:** add LIFE-01–LIFE-25 to the canonical test-ID crosswalk, map severity/criticality and evidence requirements, and preserve owner-approved environment/fixture controls.
- **API/Event:** model requests, decisions, execution attempts and outcomes as separate commands/events/records; unknown external outcome requires reconciliation, not assumed success.
- **Lifecycle Standard:** reconcile proposed lifecycle labels and transitions before freezing any enum.

## 18. Safety and authorization boundary

This document does not authorize:

- repository or code changes, schema migrations or data migrations;
- tests, runtime execution or destructive simulations;
- provider selection, provisioning or activation;
- credential issuance or secret changes;
- paid storage, scanning, bandwidth or infrastructure;
- movement, deletion or modification of existing user files;
- legal-hold placement/release or purge execution;
- production generation, upload or publishing;
- agent execution or delegation.

Any such action requires separate, explicit authorization and the applicable owner decisions.

## 19. Plain-language explanation

Retiring a NEXTDECODE video or content item should take it out of normal use, not erase the history of how it was researched, made, checked and approved. A deletion request is only a request. The system first checks everything that depends on the file, whether it is shared, whether it must be retained and whether a legal hold exists. Only a separately authorized, exact-scope purge can remove bytes. If storage deletion partially fails, the system records the incomplete result and reconciles it rather than pretending the purge succeeded.

**Reconciliation outcome:** X-09 is substantially clarified as a logical design candidate. Owner-reserved policy and authority decisions remain open. This does not make the overall P0 package ready for detailed contract freeze.

**Detailed contract freeze:** NOT GRANTED.  
**Implementation authorization:** NOT GRANTED.
