# NEXTDECODE P0 — Engineering Work Orders WP-1 to WP-6

**Version:** 0.1  
**Status:** Draft work-order templates; not agent assignments or implementation authorization

## Common instructions for every work package

- Use only the formally approved detailed contract baseline once one exists.
- Do not infer approval from a proposal, chat summary or prior implementation.
- Preserve all existing tracked modifications and untracked files.
- Do not reset, revert, stash, clean, delete, overwrite, rename or broadly stage user work.
- Do not commit, push, change branch/remotes, deploy, spend, activate providers or publish externally.
- Do not expand scope. Stop and report any contract conflict or repository collision.
- Return changed-path list, concise diff summary, commands run, test results, logs, limitations and unresolved decisions.
- No hard-coded secrets; no real user/customer content in synthetic P0 fixtures.
- No public publishing or real external side effects in P0.

## WP-1 — Canonical domain and persistence foundation

**Goal:** Establish canonical entity identity, relational persistence and schema migration discipline.

**Inputs:** Approved canonical data dictionary, entity ownership registry, WP-1 design package, accepted ADR/CF decisions.

**Scope:**
- Implement only approved canonical entities and relationships.
- Enforce immutable IDs, ownership boundaries, uniqueness and referential integrity.
- Add versioned, additive migrations and repository interfaces.
- Define transaction boundaries needed for later outbox/inbox integration.
- Use synthetic fixtures only.

**Out of scope:** Full worker system, public UI, cloud deployment, production data migration.

**Acceptance evidence:**
- Migration up/down or documented forward-recovery strategy.
- Schema constraints and repository tests.
- Duplicate ID/owner/FK/invalid relationship negative tests.
- Transaction rollback tests.
- Data dictionary traceability.

**Stop conditions:** unresolved entity ownership, schema collision with existing user work, migration requiring destructive transformation, unclear authoritative source.

## WP-2 — Durable workflow and job execution

**Goal:** Implement durable workflow/task coordination and job/attempt/lease execution.

**Inputs:** Approved WP-1 schema and WP-2/state-transition/API-event contracts.

**Scope:**
- Workflow and WorkflowTask coordination.
- Job, JobAttempt and Lease lifecycle.
- Durable queue using DB-backed records and transactional outbox/inbox.
- Idempotency, claim/lease expiry, retry scheduling and attempt history.
- Restart recovery and ambiguous-outcome handling.

**Acceptance evidence:**
- Same idempotency key/same payload returns same logical result.
- Same key/different payload conflicts.
- Stale lease cannot overwrite newer attempt.
- Duplicate event delivery does not duplicate logical processing.
- Restart recovers eligible work and preserves history.
- External ambiguous outcome is reconciled, not blindly retried.

**Stop conditions:** unresolved state ownership, undefined transition guards, no safe idempotency behavior.

## WP-3 — Worker registry and trust boundary

**Goal:** Register and authorize workers as distinct identities, independent of hostnames.

**Inputs:** Approved worker trust/credential contract and WP-2 execution contracts.

**Scope:**
- Worker identity and enrollment lifecycle.
- Trust state separated from operational availability.
- Capability declaration separated from verification and authorization.
- Scoped short-lived credentials and revocation hooks.
- Bounded job execution and audit events.

**Acceptance evidence:**
- Unknown/untrusted worker cannot claim protected work.
- Capability declaration alone grants no permission.
- Revoked/expired credential is rejected.
- Worker cannot exceed job scope.
- Local and remote worker identities follow equivalent policy.
- Worker identity remains stable across hostname changes where identity assurance supports it.

**Owner/security-reserved decisions:** identity assurance, isolation technology/threat model, active lease revocation semantics, quarantine/recovery and output treatment.

## WP-4 — Artifact registration, storage and transfer

**Goal:** Track immutable output versions and safely transfer/validate artifacts.

**Inputs:** Approved artifact contract, lifecycle/retention/deletion decisions and WP-1 persistence.

**Scope:**
- Asset vs Artifact distinction.
- Immutable ArtifactVersion metadata and checksums.
- Manifest with exact-version references.
- Transfer, validation and quarantine records.
- Storage abstraction with local implementation only if approved.
- Repair creates a new version, never mutates prior evidence.

**Acceptance evidence:**
- Checksum mismatch is detected.
- Incomplete transfer cannot be marked complete.
- Quarantined artifacts cannot be consumed by protected workflows.
- Manifest references exact immutable versions.
- Shared dependencies are not cascade-deleted.
- Metadata/binary partial failure is recoverable and auditable.

**Owner-reserved:** retention durations, legal-hold authority/release, irreversible purge authority, audit purge and backup propagation.

## WP-5 — Governance, quality, rights and authorization

**Goal:** Enforce centralized gates across APIs, workers and adapters.

**Inputs:** Accepted ADR-007/ADR-008/ADR-009/ADR-010 and reconciled governance contract.

**Scope:**
- Separate QA, rights assessment, review snapshot, approval decision and authorization decision.
- Central authorization for protected actions.
- Exact action/resource/version/hash/destination/time binding.
- Expiry and revocation.
- Hard blockers and emergency pause handling according to approved owner policy.
- Audit trail and bypass-negative tests.

**Acceptance evidence:**
- Missing/unknown rights or approval denies protected action.
- QA hard blocker cannot be overridden by ordinary approval.
- Approval alone does not authorize execution.
- Authorization for one version/destination does not authorize another.
- Worker/API/publisher adapter cannot bypass central gate.
- Expired/revoked authorization is rejected.
- Automatic public publishing remains disabled.

**Owner-reserved:** emergency pause authority/scope, break-glass, in-flight action handling and any exception policy.

## WP-6 — Vertical-slice integration and recovery validation

**Goal:** Demonstrate the P0 foundation working end-to-end without real external side effects.

**Inputs:** Accepted WP-1–WP-5 contracts and implementations.

**Scope:**
- Synthetic content item and variant.
- Workflow and dependent task.
- Durable job dispatch and authenticated worker claim.
- Deterministic test output.
- Immutable artifact registration.
- State transition and audit reconstruction.
- Failure injection, restart and recovery.
- Security-negative and governance tests.
- Independent read-only Kilo QA.

**Acceptance evidence:** VS-01–VS-18 and F-01–F-18 oracle mapping, environment manifest, test logs, artifact hashes, run IDs, audit reconstruction and Kilo findings.

**Not acceptance:** a green unit-test count alone, a screenshot without provenance, a historical report, or a self-declared “complete” status.

## Agent allocation — proposed, not activated

- Qoder: Phase 11 engineering owner as previously assigned; only a named work order may be issued.
- OpenCode: Phase 10 engineering/closure owner as previously assigned; only a named work order may be issued.
- Kilo: independent read-only QA; no implementation authority.
- Assistant: architecture coordination, source reconciliation and evidence review.
- Owner: scope, contract freeze, implementation authorization and acceptance authority.

No agent has been started or assigned by this document.
