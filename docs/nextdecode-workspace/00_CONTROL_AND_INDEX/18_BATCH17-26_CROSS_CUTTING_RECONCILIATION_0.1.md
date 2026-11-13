# NEXTDECODE P0 — Batch 17–26 Cross-Cutting Reconciliation
**Document ID:** NEXTDECODE-P0-B17-B26-XREF-0.1  
**Version:** 0.1  
**Status:** WORKING SOURCE RECONCILIATION — OWNER REVIEW REQUIRED  
**Updated:** 2026-11-04  
**Scope:** Documentation-only; no contract freeze, implementation, test execution or release authorization.

## 1. Authority and method
Accepted owner decisions, ADR-001–ADR-010, CF-01–CF-24 and canonical standards remain controlling. Batches 17–26 are detailed candidate specifications. Their own status statements preserve owner-freeze and implementation gates. Illustrative identifiers, enums, metrics, thresholds, environment names and commands are not frozen merely because they appear in a candidate.

This is a first-pass cross-cutting reconciliation from the local Markdown source copies. It is not yet a clause-by-clause DOCX visual/format verification or a formal owner disposition.

## 2. Batch-to-domain crosswalk

| Batch | Primary concern | Work-package relationship | Reconciliation rule / current status |
|---|---|---|---|
| 17 State-Machine & Transition Catalogue | Domain-owned state machines, transition guards, events, versions, unknown outcomes | WP1 entity identity; WP2 execution; WP3 worker trust; WP4 artifact/transfer; WP5 QA/rights/approval/authorization; WP6 acceptance | Accepted QA, rights and approval vocabularies remain fixed. Other proposed states/transitions remain candidates. Commands request transitions; events report committed transitions. Owner-only state commits and expected-state-version checks must align with API, persistence and lifecycle standards. |
| 18 API/Event/Schema Specification Pack | Versioned command/event envelopes, schemas, errors, idempotency, compatibility and integration contracts | WP1 persistence interfaces; WP2 orchestration; WP3 worker callbacks; WP4 artifact/transfer; WP5 policy decisions; WP6 contract tests | Must conform to canonical API/Event Standard. Examples and proposed field/enumeration details do not silently amend it. Reconcile schema_version vs event_version, correlation/causation, actor identity, state version, idempotency and external-operation unknown outcomes. |
| 19 Database Schema/ERD/Persistence Specification | Relational entities, constraints, relationships, indexes, migrations and persistence | WP1 owns canonical domain/persistence boundary; WP2 execution records; WP3 worker registry; WP4 artifact metadata; WP5 governance evidence | ADR-002/003/006 remain controlling: PostgreSQL-compatible authoritative relational store, durable DB-backed queue and transactional outbox/inbox initially, relational artifact metadata. Candidate ERD/table names and physical ownership require reconciliation with WP1/WP2/WP4 boundaries; no schema freeze or migration authorization. |
| 20 Security, Identity, Access Control & Threat Model | Identity, authorization, worker trust, secrets, protected side effects, audit and threat catalogue | WP3 worker trust; WP5 central authorization; all WPs consume security boundaries | Candidate security architecture. Preserve central authorization, default deny, least privilege, exact action/resource/version/destination binding, execution-time revalidation and no adapter bypass. Provider, identity, key, network and numeric choices remain open. |
| 21 Observability & Operational Runbook | Logs, metrics, traces, health, alerts, dashboards, errors and operator runbooks | All WPs; particularly WP2 execution, WP3 worker health, WP4 integrity, WP5 authorization, WP6 recovery evidence | Logs are diagnostic, not authoritative domain state or publication truth. Correlation chain must link commands, transitions, jobs, attempts, artifacts, governance and distribution operations. Thresholds, retention, exporters, SLOs and alert destinations remain open. No telemetry stack configured. |
| 22 Configuration, Environment, Deployment & Release | Configuration governance, environment separation, provenance, CI/release gates, migration/rollback coordination | All WPs; WP6 consumes approved release/test environments | Local-first/free-first and ₹0 initial spend remain constraints; no provider/topology selected. Safe defaults, strict config validation, no implicit provider activation, preservation of user work and separate release approval are required candidate controls. No environment/deployment/CI verified or configured. |
| 23 Backup, Disaster Recovery & Business Continuity | Backup/restore, recovery objectives, restore sequencing, integrity and continuity | WP1 persistence; WP2 durable execution; WP4 binaries/manifests; WP5 audit/governance; WP6 recovery acceptance | Recovery must preserve relational and binary consistency, outbox/inbox and execution state, immutable artifact identity, authorization revocation and deletion/tombstone handling. Backup existence is not restore evidence. RPO/RTO, schedules, storage/provider, retention and restore test authorization remain open. |
| 24 Performance, Scalability, Capacity & Cost Control | Workload sizing, quotas, concurrency, queue/storage capacity, cost guardrails | WP2 scheduling/queues; WP3 worker capacity; WP4 storage/transfer; WP6 performance/recovery acceptance | Must preserve ₹0/local-first baseline and bounded resource use. Numeric limits, concurrency, throughput, SLOs and capacity targets require workload evidence and owner approval. Capacity pressure is not permission to weaken governance, drop evidence or delete retained data. |
| 25 Security Architecture & Defensive Controls | Threat boundaries, prompt injection, supply chain, file safety, privacy, incident response and security acceptance | WP3, WP4, WP5, WP6 and all integration boundaries | Complements Batch 20 but overlaps identity, authorization, worker trust, secrets, audit, protected publishing and threat tests. Treat as one security-control family for reconciliation, not two competing authorities. Establish a single owner-approved control catalogue and map duplicate controls/tests before freeze. |
| 26 Privacy, Data Governance, Retention, Consent & Compliance | Data classification, purpose, minimization, rights requests, derivatives, retention, deletion, legal holds and privacy assessment | Cross-cutting; WP1 data ownership; WP4 artifact lifecycle; WP5 rights/governance; WP6 privacy acceptance | No legal applicability, lawful basis, consent requirement, retention period, deletion schedule, provider location or compliance status may be inferred. Legal/privacy review and owner decisions required. Coordinate with WP4 lifecycle and Batch 23 backups; no cascade deletion or complete-erasure promise without lineage and backup analysis. |

## 3. Cross-batch conflicts and required reconciliation

| ID | Conflict / risk | Safe boundary | Required owner disposition / evidence |
|---|---|---|---|
| B17-01 | Candidate state enums may be mistaken for accepted lifecycle vocabulary | Only accepted vocabularies are baseline; all other proposed states remain candidate | State-machine owner approval and exact transition matrix against Lifecycle Standard |
| B17-02 | State transition event fields may diverge from API/Event envelope | One canonical envelope; state-specific payload is an extension governed by schema | Batch 18 ↔ API/Event Standard field-by-field crosswalk |
| B18-01 | event_version vs schema_version naming/semantics | Separate event identity/type version from payload schema compatibility only if owner-approved | Explicit version semantics, compatibility policy and examples |
| B18-02 | Event delivery/replay vs external side effects | Inbox/outbox idempotency does not itself make third-party side effects exactly-once | Provider idempotency and reconciliation acceptance cases |
| B19-01 | ERD physical tables may conflict with WP1 logical model/WP2 execution ownership | WP1 owns canonical domain boundary; WP2 owns physical execution records | Approved entity-to-table ownership and migration map |
| B19-02 | SQLite/local fallback vs ADR-002 authoritative shared state | No competing authoritative shared store; local bounded cache/test use only if separately permitted | Explicit compatibility boundary and persistence decision |
| B20/25-01 | Two security specifications duplicate control families | Consolidate controls under one owner-approved catalogue; preserve both sources and traceability | Security owner names primary control register and resolves duplicate IDs/tests |
| B20/25-02 | Candidate security test catalogues overlap WP6/Artifact 07 | Security specs define scenarios; Artifact 07 governs P0 acceptance identifiers/criticality | SEC-T ↔ Artifact 07 ↔ WP6 crosswalk |
| B21-01 | Metrics/logs/traces may be treated as authoritative records | Authoritative domain/audit/operation records own business truth; telemetry links to them | Data ownership and retention map; redaction tests |
| B22-01 | Release gates could be mistaken for authorization to deploy | Passing gates is evidence; exact artifact/environment/scope still needs explicit owner release approval | Approved release policy and separate deployment authorization |
| B22-02 | Configuration flags or credentials may be mistaken for permission | Configuration/provider presence cannot grant protected action | Central authorization enforcement and negative tests |
| B23-01 | Backup restore may reintroduce revoked credentials, deleted records or stale work | Restore must reconcile revocations, deletion tombstones, external outcomes and immutable versions before normal use | Recovery sequence, tombstone/credential controls and restore evidence |
| B23-02 | Backup existence mistaken for recoverability | Restore rehearsal and integrity verification required | Approved RPO/RTO, backup scope and restore acceptance evidence |
| B24-01 | Numeric capacity/retry/timeouts introduced without workload evidence | No production numeric policy inferred from examples | Owner-approved test parameters and measured workload evidence |
| B24-02 | Cost optimization could weaken safety or retention | Cost controls cannot bypass QA, rights, authorization, audit or legal hold | Explicit policy invariants in capacity/release tests |
| B26-01 | Deletion/retention conflicts with immutable artifacts and audit evidence | No automatic cascade; classify records, legal holds, derivatives and exceptions | Legal/privacy-approved retention matrix and purge authority |
| B26-02 | Privacy deletion vs backups/replicas/provider copies | Track active stores, derivatives, logs, exports, backups and processors; avoid absolute deletion claims | Data lineage, tombstone propagation and expiry evidence |
| B26-03 | Rights clearance confused with privacy consent | Copyright/licensing/publicity rights and personal-data consent are distinct determinations | Separate evidence and policy records with explicit ownership |

## 4. Global invariants that survive the cross-batch review
1. Accepted ADR/CF and canonical standards outrank candidate batches.
2. A state machine has one authoritative owner; commands request transitions and events describe committed transitions.
3. Approval, QA, rights, authorization, execution and external publication outcome remain distinct.
4. Unknown external side effects require reconciliation before retry.
5. PostgreSQL-compatible relational persistence remains the authoritative shared-state direction; no silent volatile or SQLite authoritative fallback.
6. ArtifactVersion remains immutable; manifests pin exact versions; metadata and binary storage are distinct.
7. Central authorization is fail-closed and enforced at protected side-effect boundaries.
8. Logs/metrics/traces are not substitutes for authoritative domain, audit or operation records.
9. Provider configuration, credentials, green tests or release-gate completion do not independently authorize external side effects or deployment.
10. Local-first/free-first/₹0 initial-spend constraints remain; no paid provider/service selected or activated.
11. Retention, legal hold, deletion and backup expiry require explicit owner/legal policy; no implicit cascade.
12. Documentation or proposed test oracles are not implementation, test-pass or release evidence.

## 5. Required next work
1. Build clause-level crosswalks for Batch 17↔Lifecycle Standard, Batch 18↔API/Event Standard, Batch 19↔ADR-002/003/006 and WP1/WP2/WP4.
2. Consolidate Batch 20 and Batch 25 security controls into a deduplicated source-linked catalogue without discarding either source.
3. Build Batch 21 observability ownership/retention map and Batch 22 release-gate ↔ WP6/Artifact 07 crosswalk.
4. Reconcile Batch 23 recovery/deletion with WP4 and Batch 26; record unresolved RPO/RTO and legal decisions as OPEN.
5. Map Batch 24 capacity parameters to measured evidence; do not invent production values.
6. Build Artifact 07 ↔ WP6 ↔ Batch 17/20/21/22/23/25/26 acceptance traceability.
7. Add exact source clause references, accountable decision owners, alternatives and consequences to the consolidated owner-review pack.
8. Update master index, document register, open gaps, QA report and progress tracker only after all new documents are read-back verified.

## 6. Status and authorization
This register is a working reconciliation aid only. It does not freeze any batch, schema, API, event, state enum, metric, threshold, environment, deployment topology, security mechanism, retention period or recovery objective. No repository/code changes, migrations, tests, agent dispatch, credentials, provider activation, spending, deployment, production generation, upload or publishing are authorized. Automatic public publishing remains disabled absent separate authorization.
