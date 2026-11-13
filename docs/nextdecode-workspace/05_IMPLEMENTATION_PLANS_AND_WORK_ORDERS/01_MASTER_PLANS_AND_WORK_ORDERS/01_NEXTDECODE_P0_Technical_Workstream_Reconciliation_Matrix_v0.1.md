# NEXTDECODE P0 — Technical Workstream Reconciliation Matrix
**Document ID:** ND-P0-TECH-REC-001  
**Version:** 0.1  
**Prepared:** 3 November 2026  
**Status:** Source-based reconciliation candidate — owner freeze pending  
**Authority:** Documentation and planning only. Not implementation authorization.

## 1. Purpose and reading rules

This matrix consolidates the technical design and acceptance implications of Batches 14, 16, and 19–24. It is intended to prevent parallel workstreams from producing internally consistent documents that still conflict at their boundaries.

Status terms used here:
- **Accepted baseline** — supported by an accepted ADR/CF or canonical standard already identified in the source set.
- **Candidate** — detailed design proposed by a batch document; not formally frozen.
- **Open** — requires owner or designated domain-owner disposition.
- **Not verified** — source or implementation evidence has not established the claim.
- **Not authorized** — action remains outside the current permission boundary.

Do not promote a candidate or open item to accepted by inference, silence, a generic “next”, an agent completion message, or a passing isolated test.

## 2. Executive findings

1. **Batch 14 is the governing acceptance framework, not evidence that P0 has passed.** Its G0–G8 gates require source authority, contract freeze, implementation integrity, functional acceptance, resilience/security, governance, independent QA, owner release decision, and controlled release/post-check.
2. **Batch 16 is the consolidated domain/interface candidate, not a frozen contract.** It explicitly retains open detail around fields, enums, endpoints, payloads, timeouts, retry values, retention, providers and operational thresholds.
3. **Batch 19 is a logical/physical persistence candidate.** It does not establish that a physical database deployment or migration exists or has been run.
4. **Batch 20 is a security/threat-model candidate.** Identity provider, MFA, principal taxonomy, policy composition, token/session lifetimes, worker bootstrap trust, key management, network boundaries, data classification and emergency-pause operations remain open.
5. **Batch 21 is an observability/runbook candidate.** No telemetry stack, exporter, alert destination, dashboard, SLO target or rehearsed operational runbook is established by the document.
6. **Batch 22 is a configuration/release candidate.** No environment, CI/CD pipeline, deployment, migration, credential activation or release is verified by that document.
7. **Batch 23 is a recovery candidate.** No backup or restore is proven; RPO/RTO/WRT and backup/recovery mechanics remain owner decisions.
8. **Batch 24 is a performance/capacity/cost candidate.** No benchmark, production capacity, SLA/SLO, resource quota or spend threshold is approved by that document.
9. The design can be prepared in parallel, but **contract freeze, implementation authorization, independent verification, owner acceptance and release authorization remain separate gates**.

## 3. Cross-workstream reconciliation matrix

| Workstream | Source basis | Candidate design contribution | Open closure requirements | Evidence required before acceptance |
|---|---|---|---|---|
| WP-1 — Canonical data & persistence | Canonical Data Dictionary; API/Event Standard; Lifecycle Standard; B17; B19 | Entity identity/version separation; relational persistence; constraints, transaction boundaries, indexes and migration controls | Exact physical DB/version/topology; physical table/column types; FK strategy; indexes; isolation; retention/legal hold; migration and compatibility policy | Owner-frozen entity ownership/cardinality; reviewed ERD/schema; migration plan; deterministic DB integration tests; backup/restore compatibility |
| WP-2 — Workflow/job execution | Lifecycle Standard; API/Event Standard; B17–B19; B16 | WorkflowRun, TaskInstance, Job, JobAttempt, lease/fencing, outbox/inbox, idempotency and durable dispatch boundaries | TaskInstance↔Job cardinality; state ownership; claim algorithm; lease/heartbeat/retry values; stale result handling; cancellation/recovery semantics | State-transition tests; duplicate delivery; crash/restart; lease expiry/reassignment; stale result rejection; unknown external outcome reconciliation |
| WP-3 — Worker registry/trust | ADR-005; B16; B18; B20 | Stable worker identity separated from credential/session; scoped credentials; capability checks; bounded assignments | Enrollment/bootstrap trust; credential issuer/TTL/revocation; capability catalogue; machine trust; fencing mechanism; local worker policy | Enrollment and revocation tests; capability denial; expired credential; lease fencing; unauthorized worker cannot claim/execute |
| WP-4 — Artifact registry/storage/integrity | ADR-006; Data Dictionary; B16; B18; B19; B23 | Artifact and immutable ArtifactVersion; metadata/binary separation; manifest/checksum and quarantine concepts | Exact storage abstraction/provider; typed FK vs validated polymorphic references; manifest schema; transfer protocol; retention/deletion; backup consistency | Immutable version tests; checksum mismatch quarantine; lineage; interrupted transfer; restore manifest/binary mapping; no silent overwrite |
| WP-5 — QA/rights/review/approval/authorization | ADR-007–009; CF-20/21/22; Contract 07; B16; B20 | Distinct QA, rights, approval and authorization decisions; centralized policy; emergency pause | Resolve competing rights vocabularies at authoritative owner; evidence/use binding; policy model; principal permissions; pause scope/propagation/recovery | Unknown/denied rights fail closed; approval without authorization denied; BLOCKED cannot be waived; adapter bypass denied; pause enforced at execution |
| WP-6 — Vertical slice/integration/recovery | B14; B16; B17–B24 | End-to-end traceability and controlled candidate acceptance | Exact in-scope journey; versioned contract bundle; adapter boundaries; disposable test environment; test corpus; rollback and recovery evidence | E2–E7 evidence by requirement; complete run trace; independent QA; reproducible candidate manifest; owner acceptance |
| Operations/observability | B21; B14; B22 | Correlation, structured logs, metrics, tracing, health semantics, alerts and runbooks | Stack/exporters; event/error taxonomy; sampling/cardinality; retention; thresholds; owners/on-call and response windows | Secret-redaction tests; DB outage; queue/outbox backlog; unknown outcome; runbook rehearsal; dashboard-to-authoritative-record reconciliation |
| Configuration/release | B22; B14; B19–B21 | Environment separation, config registry, secret references, build provenance, release process | Environment count/topology; config precedence; secret mechanism; CI/CD; migration sequencing; rollback compatibility; release operator | Reproducible build; config validation; environment isolation; migration rehearsal; exact candidate manifest; post-deploy checks |
| Backup/DR/continuity | B23; B19; B21–B22 | Data-class inventory, consistency groups, restore order, event replay and staged reactivation | RPO/RTO/WRT; backup frequency/retention; DB PITR; object storage versioning; key recovery; offline/local-worker continuity; incident roles | Disposable backup/restore rehearsal; checksum and lineage; queue/outbox/inbox reconciliation; unknown external outcome handling; measured objectives |
| Performance/capacity/cost | B24; B21–B23 | Workload model, admission control, backpressure, quotas, resource pools and capacity reviews | Workload profile; latency/queue-age targets; concurrency and resource caps; storage quotas; retry/lease numbers; SLOs; paid spend approval | Reproducible baseline/load/stress tests; resource measurements; recovery backlog-drain test; no production load without separate authorization |

## 4. Non-negotiable cross-workstream invariants

- One authoritative owner for each canonical domain state; consumers use owner commands rather than direct cross-domain writes.
- Query is read-only; command is intent; event is a committed fact, not permission.
- Entity identity and immutable version identity remain distinct.
- Workflow lifecycle, task/job execution, worker/lease, artifact, quality, rights, approval, authorization and external-operation outcome remain separate state dimensions.
- Approval is not authorization; authorization is not execution; execution is not confirmed external outcome.
- Unknown external outcomes must be reconciled before retry; no blind retry of potentially successful publishing or other side effects.
- Expired/revoked credentials, stale attempts, stale lease generations and unsupported schema versions fail closed.
- Artifact repair/regeneration creates a new immutable version; do not overwrite history.
- No in-memory fallback may become authoritative shared state during database failure.
- Public automatic publishing remains disabled unless separately authorized; human approval remains required for critical publishing actions.
- Local-first/free-first and ₹0 initial target remain in force; no paid provider activation is implied.
- Preserve user work; no destructive Git/repository operations without explicit authorization.

## 5. Cross-document issues that must not be silently reconciled

### 5.1 Rights vocabulary
The accepted ADR-009 baseline uses `CLEARED`, `RESTRICTED`, `PENDING_VERIFICATION`, `PROHIBITED`, `UNKNOWN`. Later CF-20/B16/B19 material uses `UNKNOWN`, `PENDING_REVIEW`, `CLEARED`, `RESTRICTED`, `EXPIRED`, `REVOKED`, `DENIED`. Contract 07 / CF-20 must determine the canonical model and any compatibility semantics. Do not map local `reuse_rights: permitted` to `CLEARED`.

### 5.2 ADR status and source authority
The Accepted P0 Architecture Decision Baseline 1.0 says ADR-001–010 are accepted, while the separate ADR records pack and register retain proposed/pending labels. Resolve through original owner decision evidence and a supersession/provenance trail; do not overwrite one status with another.

### 5.3 ODR provenance
Batch 14 says a complete independent original ODR register has not been confirmed and ODR-22 is provisional. Batch 15 similarly treats ODR-22 as a provisional grouping note. Do not represent a derived working register as 22 original owner-authored decisions.

### 5.4 Artifact 08 version lineage
Batches 16 and 24 refer to Artifact 08 v1.1 as a reconciliation candidate that supplements, but does not supersede, v1.0 accepted owner decision/reference records. Establish the exact authoritative files, hashes, provenance and intended relationship before using v1.1 to alter accepted semantics.

### 5.5 Contract freeze vs implementation authorization
Detailed contract freeze is still pending. Even after contract freeze, implementation authorization must be a separate, explicit, scoped decision. Neither is granted by these technical candidates.

## 6. Recommended closure order

**Wave A — authority and cross-domain semantics**
1. Close ADR/CF/ODR provenance and Artifact 08 version lineage.
2. Resolve rights vocabulary with Contract 07 owner.
3. Close entity ownership/cardinality and AgentIdentity↔Actor linkage.
4. Close WorkflowRun/TaskInstance/Job/JobAttempt cardinality, state ownership and lease/fencing semantics.
5. Freeze API/event schemas and compatibility/error behavior.

**Wave B — persistence and trust**
6. Freeze WP-1 logical schema/ERD and record unresolved physical DB choices separately.
7. Freeze WP-3 worker identity, enrollment, credential and capability semantics.
8. Freeze WP-4 artifact/version/manifest/transfer semantics.
9. Freeze WP-5 policy decision inputs, decision outputs, emergency pause and distribution adapter enforcement.

**Wave C — operations and recovery**
10. Resolve B21 telemetry taxonomy, correlation, redaction and health semantics; defer numeric SLOs until measurement.
11. Resolve B22 config registry and environment separation; defer provider-specific choices.
12. Resolve B23 recovery priorities and test oracles; owner must set RPO/RTO/WRT.
13. Resolve B24 workload model and measurement protocol; owner must set numeric budgets/quotas and approve any spend separately.

**Wave D — acceptance and authorization**
14. Build requirement-to-contract-to-test traceability.
15. Complete G0 source authority and G1 contract freeze.
16. Obtain separate G2 implementation authorization for exact work package and target.
17. Execute G3–G6 evidence and independent QA.
18. Obtain G7 owner acceptance and separate G8 release authorization/execution only if explicitly approved.

## 7. Current disposition

| Gate / dimension | Current disposition |
|---|---|
| Source inventory | Partial; missing/ambiguous source records remain |
| Architecture direction | Accepted baseline exists, but provenance/status conflict requires closure |
| Detailed contract freeze | NOT GRANTED |
| Implementation authorization | NOT GRANTED |
| Implementation completion | Not assessed by this document |
| Independent verification | Not demonstrated for the complete candidate |
| Owner P0 acceptance | NOT GRANTED |
| Release/public publishing | NOT AUTHORIZED |

This matrix is a reconciliation aid, not a replacement for the canonical documents or owner decision register.
