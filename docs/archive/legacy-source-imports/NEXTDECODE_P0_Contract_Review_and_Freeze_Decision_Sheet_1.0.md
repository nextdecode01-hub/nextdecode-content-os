# NEXTDECODE P0 Contract Review & Freeze Decision Sheet 1.0

**Document status:** Owner review worksheet — NOT FROZEN  
**Purpose:** Capture explicit owner decisions on the detailed P0 contracts before implementation.  
**Related baseline:** `NEXTDECODE_Accepted_P0_Architecture_Decision_Baseline_1.0.md`  
**Related draft:** `NEXTDECODE_P0_Detailed_Contract_Freeze_Pack_1.0.md`

---

## 1. Decision rules

For each section, select exactly one outcome:

- **ACCEPT** — accept the section as written for the P0 contract baseline.
- **ACCEPT WITH AMENDMENT** — accept only after recording the required changes.
- **DEFER** — do not freeze this section yet; identify the missing evidence or decision.
- **REJECT** — do not use the proposed contract; explain the reason and replacement direction.

An ACCEPT decision freezes only the detailed contract scope described in that section. It does not authorize repository inspection, code changes, tests, dependency changes, cloud provisioning, deployment, production generation, uploads, or publishing.

### Already accepted high-level architecture decisions

These decisions are recorded as owner-approved and should not be reopened by this worksheet unless the owner explicitly changes them:

1. UUIDv7 canonical IDs.
2. PostgreSQL-compatible relational database as the authoritative shared store.
3. Database-backed durable queue with transactional outbox/inbox initially.
4. Versioned HTTP/JSON contracts with schema validation.
5. Unique worker identity, scoped short-lived credentials, and capability-based authorization.
6. Artifact metadata in PostgreSQL; binary files in an object-storage abstraction with immutable versions.
7. Separate lifecycle state machines.
8. Centralized governance and authorization boundary; no adapter bypass; emergency pause; automatic publishing remains disabled pending separate policy approval.
9. Quality outcomes: `PASS`, `PASS_WITH_WARNINGS`, `NEEDS_REVIEW`, `BLOCKED`; hard blockers cannot be overridden by ordinary approval.
10. Centralized rights registry and evidence-backed use-specific policy; rights states: `CLEARED`, `RESTRICTED`, `PENDING_VERIFICATION`, `PROHIBITED`, `UNKNOWN`.

This worksheet reviews the detailed contracts and operational parameters beneath those accepted principles.

---

## 2. Section decision register

### Section 1 — Domain entities, identity and relationships

**Review scope**
- Canonical entity definitions and UUIDv7 identity.
- Relationships among content idea, content item, content variant, workflow, task, job, job attempt, studio job, production run, artifact, asset, review package, approval, authorization and distribution record.
- Ownership and lifecycle boundaries for each entity.
- Required versus optional references; uniqueness and deletion/retention expectations.

**Decision:** `PENDING`

- [ ] ACCEPT
- [ ] ACCEPT WITH AMENDMENT
- [ ] DEFER
- [ ] REJECT

**Required amendments / notes:**

> Record entity or relationship changes here.

**Freeze conditions**
- Every entity has one clear purpose and canonical identity.
- No ambiguous identity reuse across workflow, job, studio run or distribution.
- Required relationships and ownership boundaries are explicit.

---

### Section 2 — Lifecycle state machines

**Review scope**
- Separate state machines for content, variant, workflow, task, job, job attempt, worker, production run, review package, approval, authorization and distribution.
- Allowed transitions, terminal states, retries, cancellation, reopening and superseding.
- Mapping between related state machines without collapsing them into one status field.
- Handling of stale or out-of-order events.

**Decision:** `PENDING`

- [ ] ACCEPT
- [ ] ACCEPT WITH AMENDMENT
- [ ] DEFER
- [ ] REJECT

**Required amendments / notes:**

> Record transition changes and unresolved edge cases here.

**Freeze conditions**
- Every state has defined entry/exit conditions.
- Invalid transitions fail safely.
- Retry, cancellation, expiry and recovery semantics are unambiguous.
- State ownership is clear.

---

### Section 3 — Durable jobs, leases, retries, idempotency and events

**Review scope**
- Job submission, dispatch, claim, lease, heartbeat, expiry and reclaim.
- Retryable versus non-retryable failures; attempt limits and backoff policy.
- Idempotency keys and duplicate submission/consumption behavior.
- Transactional outbox/inbox, event envelope, ordering expectations and consumer deduplication.
- Cancellation and recovery behavior when a worker disappears.

**Decision:** `PENDING`

- [ ] ACCEPT
- [ ] ACCEPT WITH AMENDMENT
- [ ] DEFER
- [ ] REJECT

**Required amendments / notes:**

> Record lease, heartbeat, retry, backoff and idempotency changes here.

**Freeze conditions**
- Duplicate delivery cannot cause duplicate side effects.
- Expired leases can be safely reclaimed.
- Retry behavior is bounded and observable.
- Event delivery guarantees and ordering limitations are explicit.

---

### Section 4 — Worker identity, authentication and capabilities

**Review scope**
- Worker registration and unique machine identity.
- Scoped, short-lived credentials and credential renewal/revocation.
- Capability declaration and server-side authorization.
- Worker eligibility for local versus remote execution.
- Trust boundaries, secret handling and auditability.

**Decision:** `PENDING`

- [ ] ACCEPT
- [ ] ACCEPT WITH AMENDMENT
- [ ] DEFER
- [ ] REJECT

**Required amendments / notes:**

> Record identity, credential, capability or trust-boundary changes here.

**Freeze conditions**
- A worker can execute only jobs it is authorized and capable of handling.
- Credentials are scoped, revocable and not stored in ordinary logs.
- Worker identity cannot be impersonated by a client-supplied label alone.

---

### Section 5 — Artifact metadata, immutable versions and transfer

**Review scope**
- Artifact versus asset versus manifest distinction.
- Artifact identity, versioning, checksums, media metadata and provenance.
- Immutable approved versions and superseding behavior.
- Binary storage abstraction and controlled transfer between cloud and local workers.
- Partial transfer, interrupted transfer, integrity verification and retention metadata.

**Decision:** `PENDING`

- [ ] ACCEPT
- [ ] ACCEPT WITH AMENDMENT
- [ ] DEFER
- [ ] REJECT

**Required amendments / notes:**

> Record metadata, versioning, transfer or retention changes here.

**Freeze conditions**
- Every artifact version is addressable and integrity-verifiable.
- Approval references an exact immutable version.
- Transfer authorization and integrity checks are defined.
- Storage-provider details remain abstract unless separately selected.

---

### Section 6 — Quality outcomes and rights evidence

**Review scope**
- The accepted quality outcome vocabulary: `PASS`, `PASS_WITH_WARNINGS`, `NEEDS_REVIEW`, `BLOCKED`.
- Quality check definitions, severity, evidence and policy version.
- Rights states: `CLEARED`, `RESTRICTED`, `PENDING_VERIFICATION`, `PROHIBITED`, `UNKNOWN`.
- Use-specific rights decisions, evidence provenance, expiry and re-verification.
- Hard blockers and the rule that ordinary editorial approval cannot override them.

**Decision:** `PENDING`

- [ ] ACCEPT
- [ ] ACCEPT WITH AMENDMENT
- [ ] DEFER
- [ ] REJECT

**Required amendments / notes:**

> Record quality thresholds, rights evidence or exception-policy changes here.

**Freeze conditions**
- Each outcome has deterministic downstream behavior.
- Hard blockers are fail-closed.
- Rights clearance is specific to the intended use and platform/context.
- Evidence and policy versions are auditable.

---

### Section 7 — Review, approval, authorization and distribution governance

**Review scope**
- Review package contents and exact-version binding.
- Approval identity, scope, expiry, revocation and audit record.
- Separation of editorial approval from technical/policy authorization.
- Central authorization checks at the distribution boundary.
- Emergency pause and policy-version behavior.
- Automatic publishing remains disabled until separately approved.

**Decision:** `PENDING`

- [ ] ACCEPT
- [ ] ACCEPT WITH AMENDMENT
- [ ] DEFER
- [ ] REJECT

**Required amendments / notes:**

> Record approval scope, authorization checks or distribution changes here.

**Freeze conditions**
- No adapter or direct path can bypass centralized authorization.
- Approval cannot silently transfer to a changed artifact version.
- Hard rights, safety and integrity blockers remain non-overridable by ordinary approval.
- Automatic publishing is not enabled by accepting this section.

---

### Section 8 — Errors, audit events and correlation

**Review scope**
- Stable error taxonomy and retry classification.
- Sanitized diagnostics and secret redaction.
- Correlation identifiers across content, workflow, job, attempt, worker, production run and distribution.
- Append-only audit events for security-sensitive and governance-sensitive actions.
- Operational visibility without exposing credentials or sensitive payloads.

**Decision:** `PENDING`

- [ ] ACCEPT
- [ ] ACCEPT WITH AMENDMENT
- [ ] DEFER
- [ ] REJECT

**Required amendments / notes:**

> Record error codes, audit coverage or correlation changes here.

**Freeze conditions**
- Failures can be traced across the workflow without relying on free-text logs.
- Secrets and sensitive values are excluded or redacted.
- Security, approval, rights and distribution actions are auditable.
- Retry classification is consistent with Section 3.

---

## 3. Cross-section consistency review

Before freezing the pack, confirm:

- [ ] Entity identifiers and references are consistent across all sections.
- [ ] State machines agree with job, worker, approval and distribution contracts.
- [ ] Job retries cannot bypass governance or duplicate external side effects.
- [ ] Worker capabilities are checked server-side for every assignment.
- [ ] Artifact immutability is respected by review and approval.
- [ ] Quality and rights blockers are enforced at the centralized authorization boundary.
- [ ] Audit and correlation fields are present across all critical contracts.
- [ ] No detailed proposal silently changes an already accepted high-level ADR.

**Cross-section notes:**

> Record any conflict or required reconciliation here.

---

## 4. Freeze summary

| Section | Decision | Amendments incorporated? | Owner/date |
|---|---|---|---|
| 1. Domain entities and relationships | PENDING | PENDING | PENDING |
| 2. Lifecycle state machines | PENDING | PENDING | PENDING |
| 3. Jobs, leases, retries and events | PENDING | PENDING | PENDING |
| 4. Worker identity and security | PENDING | PENDING | PENDING |
| 5. Artifacts and transfer | PENDING | PENDING | PENDING |
| 6. Quality and rights | PENDING | PENDING | PENDING |
| 7. Approval and distribution governance | PENDING | PENDING | PENDING |
| 8. Errors, audit and correlation | PENDING | PENDING | PENDING |

### Overall contract-pack status

- [ ] FROZEN — all required sections accepted and cross-section review passed.
- [ ] FROZEN WITH RECORDED AMENDMENTS — all required amendments incorporated and reviewed.
- [ ] PARTIALLY FROZEN — only explicitly accepted sections are frozen.
- [ ] NOT FROZEN — further review required.

**Owner decision notes:**

> Record the overall decision and any conditions here.

---

## 5. What this review does not authorize

Even after the contract pack is frozen, the following require separate explicit authorization:

- Repository inspection or file changes.
- Git operations of any kind.
- Test execution against the repository.
- Dependency installation or environment modification.
- Cloud account/resource creation or paid services.
- Deployment or production operation.
- Production content generation, external uploads or publishing.
- Enabling conditional or automatic publishing.

Freezing contracts is a design decision, not implementation authorization.

---

## 6. Recommended review order

Review one section at a time, in this order:

1. Domain entities and relationships.
2. Lifecycle state machines.
3. Jobs, leases, retries and events.
4. Worker identity and security.
5. Artifacts and transfer.
6. Quality and rights.
7. Approval and distribution governance.
8. Errors, audit and correlation.

**Suggested first review:** Section 1 — Domain entities, identity and relationships. Confirm whether the entity boundaries and relationships are understandable and complete before reviewing state transitions that depend on them.
