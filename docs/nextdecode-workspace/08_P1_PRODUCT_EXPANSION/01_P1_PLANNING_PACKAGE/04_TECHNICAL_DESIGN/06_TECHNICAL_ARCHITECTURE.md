# NEXTDECODE Content OS — P1 Technical Architecture

**Document ID:** ND-P1-TECH-001 | **Version:** 0.1.0-draft | **Date:** 2026-11-04  
**Status:** DRAFT — logical technical design, not provider selection or implementation approval.

## 1. Architectural shape

Recommended implementation shape: modular domain architecture with explicit boundaries and versioned interfaces. Do not introduce microservices solely because logical components are distinct. Follow P0 accepted hybrid architecture and technology decisions.

## 2. Runtime roles

- Control plane: authoritative identity, workspace, workflow, policy, approval, authorization and distribution state.
- Orchestrator: advances workflow graph and dependencies.
- Scheduler: determines when jobs become eligible.
- Durable queue: stores work and dispatch state.
- Workers: execute authorized tasks under unique identity and capabilities.
- Agents: perform bounded reasoning/transformation tasks; they are not workers, schedulers or policy authorities.
- Studios: specialist production engines behind adapters.
- Artifact service: metadata, immutable versions, manifests, checksums and scoped transfer.
- Governance services: quality, rights, approval, authorization and emergency pause.
- Observability: logs, metrics, traces, domain events and durable audit.

These roles preserve Parts 1–8 and P0 contracts.

## 3. Data ownership and persistence

- Each domain owns its records and write rules.
- Cross-domain reads use documented query/API contracts or materialized projections with explicit freshness.
- No direct mutation of another domain's tables/storage.
- PostgreSQL-compatible authoritative shared-state direction is already accepted in P0.
- Local cache is not a competing source of truth.
- Binary storage provider remains open behind accepted abstraction.
- Schema migrations are versioned and tested.
- Artifact versions are immutable; edits create new versions.
- Data retention/deletion/hold must follow existing P0 lifecycle and legal-hold contracts; do not introduce a competing retention policy.

## 4. Identity and authorization

P0 unique worker identity, scoped credentials and capabilities remain authoritative. Recommended P1 extension:
- creator/collaborator/agent/service/integration identity types;
- role + contextual attributes + explicit capability scopes;
- delegation chain and expiry;
- central authorization for high-risk action;
- local validation of approved immutable snapshots for bounded operations;
- immediate revocation and audit history.

Do not create a second IAM implementation without reconciling canonical P0 worker/auth contracts.

## 5. Workflow and orchestration

Use versioned workflow definitions and persisted execution graphs. A task must specify:
- task/workflow IDs and parent relationships;
- task type and contract version;
- exact input entity/artifact versions;
- capability/tool profile;
- idempotency key and attempt metadata;
- worker eligibility and execution constraints;
- structured outcome/error;
- output references and provenance;
- correlation/trace ID.

State changes are validated by the relevant domain state machine. Stale writers must not overwrite newer state. Queue redelivery is expected and consumers must be idempotent.

## 6. Evidence and provenance

Recommended logical model:
- Source Registry: origin identity and metadata.
- Evidence Store: extracted passage/data point and source location.
- Claim Registry: claim text/type/scope and uncertainty.
- Claim-Evidence Links: supports, contradicts, contextualizes, derived-from.
- Research Package: immutable synthesis version referencing claims/evidence.
- Content Lineage: links research and brief versions to studio artifacts.
- Production Manifest: exact inputs, assets, tools/config versions and outputs.
- Audit Ledger: governance, authorization, approval and execution events.

P0 canonical contracts and shared-intelligence contracts must be used as source-of-truth; this is not a new parallel evidence schema.

## 7. Studio integration

Each studio adapter should expose a stable contract for:
- supported capability and format;
- accepted input contract/version;
- execution request and correlation IDs;
- progress/status;
- structured completion/failure;
- output artifact registration;
- cancellation and recovery behavior;
- resource constraints.

Shorts Studio remains unchanged internally unless a separately approved work package says otherwise. Its adapter must not directly publish or bypass centralized governance.

## 8. Failure isolation and resilience

Recommended failure domains:
- identity and authorization;
- workflow orchestration and queue;
- research/model providers;
- content generation;
- each specialist studio;
- artifact storage/transfer;
- governance;
- export/integrations;
- analytics/learning.

Failure in one independent domain should not automatically stop safe unrelated capabilities. Operations dependent on failed/unknown authorization, rights, integrity or policy must stop. Use dependency-aware degradation and visible blocked reasons.

## 9. Observability

- Logs: diagnostic events, structured and redacted.
- Metrics: counts, latency, quality, costs and capacity.
- Traces: cross-module execution paths.
- Domain events: state transitions and business facts.
- Audit: durable attributable record for governance/security decisions.

Never use ordinary logs as the canonical approval or audit ledger. Define retention and access separately.

## 10. Backup, recovery and restore

Backups require integrity checks and restore tests. Define RPO/RTO only after provider, workload, cost and service criticality are known. Recover:
1. identity, secret and security controls;
2. canonical database;
3. queue/orchestration state;
4. artifact registry and binary store;
5. governance/approval state;
6. dashboard and operational views;
7. workers and integrations.

This proposed order must be validated against actual dependency graph before production.

## 11. Security controls

- Least privilege and task-scoped access.
- Unique machine identities and revocation.
- Schema validation at boundaries.
- Idempotency on state-changing APIs/events.
- Private artifact storage with scoped expiring access.
- Secrets kept outside prompts/source/logs.
- External content treated as untrusted data.
- File/media validation and isolated processing.
- Emergency pause and policy freeze.
- No public publishing by default.

## 12. Technology decisions intentionally not made

Do not select:
- hosting/cloud provider or region;
- object storage vendor;
- queue broker beyond accepted DB-backed initial queue direction;
- monitoring/logging vendor;
- AI model provider;
- vector database;
- deployment packaging;
- paid plans or budget ceiling.

These require comparative evidence, data handling review and explicit owner decision. P0 accepted PostgreSQL-compatible system-of-record direction is not permission to provision a service.

## 13. Technical acceptance

- Contracts are versioned and validated at boundaries.
- Each entity has one canonical owner.
- Workflow state survives restart.
- Retry/recovery is idempotent.
- Artifact checksums and immutable versions are verified.
- Authorization/rights/quality failures stop protected actions.
- Agent permissions are task-scoped and revocable.
- Failure isolation does not permit unsafe work.
- Audit is durable and distinguishable from telemetry.
- Restore procedure is demonstrated before production.
