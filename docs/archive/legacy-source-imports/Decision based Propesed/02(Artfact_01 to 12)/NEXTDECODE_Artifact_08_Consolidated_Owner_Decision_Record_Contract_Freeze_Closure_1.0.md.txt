# NEXTDECODE — Artifact 08
## Consolidated Owner Decision Record & Contract Freeze Closure

**Document ID:** NEXTDECODE_Artifact_08_Consolidated_Owner_Decision_Record_Contract_Freeze_Closure_1.0  
**Version:** 1.0  
**Date:** 31 October 2026  
**Status:** Consolidated owner-review record — final contract freeze approval pending  
**Related artifact:** `NEXTDECODE_Artifact_08_P0_Detailed_Contract_Freeze_Open_Decisions_Closure_1.0.md`  
**Supplementary implementation reference:** `NEXTDECODE_Artifact_08_Implementation_Reference_Accepted_Contract_Decisions_1.0.md`

---

## 1. Purpose

This record consolidates the owner decisions made during the CF-01 through CF-24 review sequence and the accepted high-level architecture decisions ADR-001 through ADR-010.

It is a decision record and closure aid. It does **not** silently convert every proposed detailed contract into an approved, implementation-ready specification.

## 2. Executive disposition

| Area | Disposition |
|---|---|
| High-level architecture decisions ADR-001–ADR-010 | ACCEPTED |
| Detailed contract review CF-01–CF-24 | OWNER REVIEW COMPLETED; decisions recorded below |
| Detailed contract freeze | PENDING final consolidated owner approval |
| Implementation authorization | NOT GRANTED |
| Repository modification / Git operations | NOT AUTHORIZED by this record |
| Coding-agent execution | NOT AUTHORIZED by this record |
| Paid services or charge-generating infrastructure | NOT AUTHORIZED |
| Cloud deployment or provider activation | DEFERRED |
| P0-WP-0 baseline assessment | Next controlled activity, read-only, subject to explicit task authorization |

**Important distinction:** Completion of the decision-review conversation is not the same as approval of the consolidated contract pack, implementation readiness, or permission to execute.

## 3. High-level architecture decisions — accepted

| ADR | Accepted decision |
|---|---|
| ADR-001 | UUIDv7 canonical IDs; opaque and immutable |
| ADR-002 | PostgreSQL-compatible relational database as authoritative shared-state store |
| ADR-003 | DB-backed durable queue with transactional outbox/inbox initially |
| ADR-004 | Versioned HTTP/JSON contracts with schema validation |
| ADR-005 | Unique worker identity, scoped short-lived credentials, and capability authorization |
| ADR-006 | Relational artifact metadata with binaries behind an object-storage abstraction |
| ADR-007 | Centralized authorization; publishing adapters cannot bypass it; automatic publishing remains disabled pending separate policy |
| ADR-008 | QA outcomes: PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW, BLOCKED; hard blockers cannot be bypassed by ordinary approval |
| ADR-009 | Evidence-backed rights states with use-specific enforcement |
| ADR-010 | Separate lifecycle state machines for content, workflow, execution, review, approval, authorization, and distribution |

These are accepted architectural directions. They do not select vendors, regions, operational thresholds, or production deployment settings.

## 4. Detailed contract decisions — CF-01 through CF-24

The following records distinguish explicit owner choices from decisions accepted under the standing delegation rule.

### 4.1 Explicit owner decisions

| ID | Owner decision | Recorded disposition |
|---|---|---|
| CF-01 | `ContentItem` is the shared editorial identity; `ContentVariant` is a format/platform/language/treatment derivative. Broader OS entities remain in their respective domain contracts. | ACCEPTED |
| CF-02 | One authoritative owner per entity; typed cross-domain references; no competing canonical identities; relationships do not imply permission; retain the 12-contract ownership structure. | ACCEPTED |
| CF-03 | Entity-specific required/optional fields; shared envelope; explicit nullability; do not infer missing business-critical fields; unknown rights/approval/authorization never grant permission; incomplete drafts cannot pass downstream gates. | ACCEPTED |
| CF-22 | Centralized authorization authority. APIs, studios, workers, and distribution adapters enforce it. Default-deny, fail-closed, least privilege, exact action/resource/version/destination binding, expiry and revocation. Approval is distinct from authorization. Agent delegation cannot expand authority. No competing domain-local authorization authority. | ACCEPTED |
| CF-24 | No paid services activated. No paid subscriptions, usage-based billing, automatic upgrades, paid APIs/models/storage/databases/automation, paid cloud, or charge-generating infrastructure without separate explicit approval. | ACCEPTED |

### 4.2 Decisions accepted under the standing delegation rule

The owner instructed that routine recommendations should be accepted automatically, conservative defaults applied to manageable decisions, and only genuinely critical decisions escalated. The following were accepted under that instruction:

| ID | Accepted contract direction |
|---|---|
| CF-04 | Preserve explicit domain ownership and typed relationships; do not create implicit ownership or permission through cross-domain links. |
| CF-05 | Keep entity identity, version identity, and human-readable aliases distinct; canonical IDs remain opaque and immutable. |
| CF-06 | Use explicit lifecycle and epistemic states rather than ambiguous generic status fields; preserve timestamps and traceability. |
| CF-07 | Validate required fields and state transitions at domain boundaries; reject or hold incomplete business-critical records rather than silently filling them. |
| CF-08 | Use durable workflow/job records with explicit parent purpose and correlation; workflows may span multiple content items and jobs. |
| CF-09 | Keep workflow, task, job, attempt, and worker execution identities distinct. |
| CF-10 | Treat queue delivery as at-least-once; require idempotent handlers and durable attempt history. |
| CF-11 | Use explicit lease ownership, expiry, heartbeat, and recovery semantics; operational numeric thresholds remain deferred. |
| CF-12 | Record events with correlation/causation context and durable state transitions; do not treat event delivery as proof that a business action completed. |
| CF-13 | Workers have unique identities and bounded, explicitly granted capabilities; workers execute assigned work and do not become global workflow authorities. |
| CF-14 | Keep versioned, validated HTTP/JSON contracts and explicit compatibility behavior at integration boundaries. |
| CF-15 | Artifact identity and immutable versions; relational metadata ownership; storage abstraction; checksum verification; controlled transfers; centralized access and rights enforcement. |
| CF-16 | Manifests identify exact immutable component versions, preserve integrity and production provenance, and link approval to the exact artifact/version and distribution lineage. |
| CF-17 | Centralized, scope-aware artifact authorization; distinct read/write/transfer/export/share/delete permissions; rights-aware use; explicit lifecycle and retention; dependency-aware deletion/recovery; local/cloud boundaries and audit lineage. Exact retention durations remain deferred. |
| CF-18 | Type-aware, versioned validation; checksum and structural checks; validation distinct from availability; quarantine blocks downstream use; revalidation preserves history; repairs create new versions; publishing rejects unverified artifacts. |
| CF-19 | Shared QA result contract; immutable/version-bound QA runs; canonical outcomes PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW, BLOCKED; evidence-backed checks; centrally enforced hard blockers; studio-specific checks map to the shared contract; scores are supplementary. QA is distinct from rights, approval, and authorization. |
| CF-20 | Use the Contract 07 rights framework; rights states are evidence-backed and use-specific; unknown rights fail closed; rights propagate through lineage; studios/adapters cannot override; ambiguous cases require legal review. |
| CF-21 | Central approval owner; immutable review packages; attributable human decisions bound to exact version and scope; decisions APPROVED, REJECTED, CHANGES_REQUESTED, EXPIRED, REVOKED; hard blockers cannot be bypassed; approval is distinct from authorization/execution; human approval before publishing; automatic publishing disabled. |
| CF-23 | Shared structured error contract and taxonomy; severity and retryability are independent; retryability explicit; durable failure/attempt history; reconcile ambiguous external actions; defined recovery owners; dependency isolation and bounded retries; policy/authorization denials cannot be bypassed; diagnostics access-controlled. |

**CF-04–CF-14 note:** These rows summarize the accepted directions captured during the review sequence. The detailed field schemas, transition tables, payload schemas, and numeric operational parameters must still be represented in the relevant contract specifications before implementation.

## 5. Cross-cutting invariants

The following invariants apply across the system:

1. One authoritative owner per canonical entity.
2. Canonical identity is immutable; version identity is explicit.
3. Unknown, missing, or ambiguous rights, approval, or authorization never grant permission.
4. Approval is not authorization; authorization is not execution; execution is not successful publication.
5. Hard QA, rights, and policy blockers are centrally enforced and cannot be bypassed by ordinary approval.
6. Workers execute bounded assignments; they do not independently expand their authority or globally orchestrate the system.
7. Queue delivery may be repeated; handlers must be idempotent and attempts must be traceable.
8. Artifacts are versioned and integrity-checked; repair creates a new version rather than rewriting history.
9. Review and approval decisions are attributable and bound to exact versions and scopes.
10. Automatic public publishing remains disabled.
11. The existing Shorts Studio remains a bounded specialist production engine; it is not to be wholesale replaced.
12. Local-only work must wait safely when the local worker is unavailable.
13. The cloud control plane is the long-term target for shared workflow state, but no cloud provider or deployment is selected or authorized here.
14. Development remains local-first and free-first.
15. No paid or charge-generating service may be activated without separate explicit owner approval.

## 6. Deferred operational decisions

These are deliberately unresolved and must not be guessed or silently selected during implementation:

- Cloud provider, account, region, and deployment topology.
- Database provider/hosting and production sizing.
- Queue implementation beyond the accepted initial DB-backed direction.
- Object-storage provider, region, replication, lifecycle, and encryption configuration.
- Credential/token issuer, exact token format, rotation, and revocation mechanics.
- Queue lease durations, heartbeat intervals, retry limits, backoff, and dead-letter thresholds.
- Artifact retention durations, legal hold, backup retention, and deletion windows.
- Monitoring/alerting provider and operational thresholds.
- Backup strategy, recovery objectives (RPO/RTO), and restore-test cadence.
- Cost limits, budgets, and any paid-service activation.
- Production workload placement and cloud/local worker fleet sizing.

Any decision that creates spending, production exposure, external side effects, or materially changes the accepted security boundary must be escalated for explicit approval.

## 7. Contract freeze gate

The detailed contract pack may be marked **FROZEN** only after the consolidated owner record is reviewed and the remaining detailed specifications are complete enough to implement without inventing semantics.

Minimum evidence for the freeze gate:

- The 12-contract ownership structure and canonical entity definitions are mutually consistent.
- The CF-01 `ContentItem` / `ContentVariant` definition is reflected consistently in all affected documents.
- Entity fields, nullability, references, and lifecycle transitions are explicit.
- Job, attempt, lease, retry, idempotency, and event semantics are specified.
- Worker identity, capability, credential, and authorization boundaries are specified.
- Artifact, manifest, transfer, validation, and provenance semantics are specified.
- QA, rights, review, approval, authorization, and distribution gates are consistent.
- Error taxonomy, recovery behavior, audit requirements, and operational assumptions are explicit.
- Deferred provider and cost decisions are clearly marked as non-blocking only where the contracts truly abstract them.
- Contradictions and unresolved critical ambiguities are closed or explicitly escalated.

## 8. Implementation authorization status

**Implementation authorization: NOT GRANTED.**

This record does not authorize:
- Editing or generating repository code.
- Running write-capable commands or modifying the working tree.
- Git commit, reset, clean, stash, checkout, merge, rebase, push, or branch changes.
- Starting Qoder, OpenCode, Kilo, or another coding agent on an execution task.
- Installing dependencies or changing environments.
- Creating cloud resources, enabling paid services, or activating external APIs.
- Uploading, publishing, or distributing content.

The existing local working tree contains significant work in progress. It must be preserved. No destructive cleanup or broad staging is permitted.

## 9. Next controlled activity

After the owner reviews this consolidated record and explicitly confirms the contract-freeze disposition, proceed to **P0-WP-0 — Current System Baseline & Preservation Assessment** as a read-only assessment.

P0-WP-0 should establish:
- Exact repository identity and current local/remote commit relationship.
- Current working-tree state and untracked files without changing them.
- Existing architecture and module boundaries.
- Existing tests and their actual current results, clearly separated from historical reports.
- Phase 10/11 implementation status and evidence.
- Known gaps against the accepted contracts.
- Preservation risks and safe file ownership boundaries.

P0-WP-0 is an assessment, not permission to fix findings. Any subsequent implementation work requires a separate, explicit bounded authorization.

## 10. Agent responsibility remains unchanged

| Agent | Responsibility |
|---|---|
| Qoder | Phase 11 engineering owner |
| OpenCode | Phase 10 engineering/closure owner |
| Kilo | Independent read-only QA |

No new assignment is created by this document. Agent work must remain within separately authorized scopes and cannot self-expand, self-approve, or bypass owner-controlled gates.

## 11. Owner confirmation required

The CF-01 through CF-24 review decisions are recorded above. The remaining owner action is to confirm the **consolidated detailed contract disposition**:

- **Approve the consolidated record as the owner decision baseline**, while keeping detailed contract freeze and implementation authorization as separate gates; or
- **Return specific corrections** to this record before it is treated as the owner decision baseline.

No implementation permission is implied by either choice.

---

**End of Artifact 08 Consolidated Owner Decision Record.**
