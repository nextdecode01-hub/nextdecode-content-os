# Integration Maintenance, Version and Lifecycle Governance

**Document ID:** INT-GOV-001 | **Version:** 0.1 draft | **Date:** 2026-11-04  
**Status:** Proposed governance standard; owner approval required  
**Authority:** P0 ADRs/CFs, canonical API/Event and Lifecycle standards take precedence.

## 1. Purpose

External providers, SDKs, models, APIs, licences and quotas change independently. This standard defines how NEXTDECODE tracks those changes, prevents silent breakage and retires integrations without losing artifacts, evidence or workflow history.

It applies to all external provider adapters and developer tools used by Content OS or the Shorts Studio integration boundary.

## 2. Integration lifecycle

| State | Meaning | Entry evidence | Permitted actions |
|---|---|---|---|
| DISCOVERED | Candidate found | Source/reference and use case | Research only |
| EVALUATING | Technical, security, cost or licence review underway | Named owner, scorecard and review checklist | Read-only investigation, offline fixtures |
| APPROVED_FOR_PILOT | Owner approved a bounded pilot | Scope, account, data class, spend/call cap, rollback and expiry | Only explicitly approved pilot operations |
| PILOT_ACTIVE | Pilot currently running | Start record and monitored controls | Exact pilot scope only |
| APPROVED | Accepted for specified production use | Acceptance evidence, owner/security approval, support owner | Approved operation set |
| DEGRADED | Provider or adapter is unreliable/limited | Alert or evidence-backed incident | Fail-safe behavior, bounded retries, optional disable |
| SUSPENDED | Use temporarily blocked | Security, legal, quota, reliability or owner decision | No new calls except approved reconciliation |
| DEPRECATED | Replacement or retirement scheduled | Migration plan and sunset date | Existing workloads only as explicitly allowed |
| RETIRED | No longer used | Migration and cleanup evidence | Read-only historical evidence |
| REJECTED | Not acceptable for this use case | Rejection rationale | No use; reconsider only on material change |

Lifecycle state is an integration governance record, not a new Content OS business lifecycle. Map it to the canonical standards before implementation.

## 3. Version dimensions — track separately

Do not collapse all versioning into one field.

1. **Internal adapter version** — code and contract implementation version.
2. **Canonical contract version** — approved Content OS port/API/event schema version.
3. **Provider API version** — remote endpoint/API version.
4. **Provider model/version** — model ID, snapshot or alias and deprecation state.
5. **SDK/library version** — package name, version, lockfile and transitive dependencies.
6. **Provider terms/pricing snapshot** — date, URL, plan/account context and relevant restrictions.
7. **Credential/scope profile version** — non-secret identifier for the granted scope and rotation generation.
8. **Configuration profile version** — validated non-secret configuration revision.

Each generated or externally sourced artifact should retain the provider/model/adapter/contract lineage relevant to its creation, subject to canonical artifact and provenance contracts.

## 4. Compatibility policy

| Change | Classification | Required response |
|---|---|---|
| Add optional response field | Usually backward-compatible | Fixture test; update parser safely |
| Remove/rename response field | Breaking | New adapter/API version; migration and rollback plan |
| Change enum/status semantics | Breaking until proven otherwise | Contract owner review; state mapping and replay review |
| Model alias changes underlying model | Potentially breaking | Pin snapshot where possible; benchmark and lineage update |
| Provider API version sunset | Breaking | Migration work package and deadline |
| SDK major version change | Potentially breaking | Changelog review, lockfile update, regression suite |
| Pricing/quota/free-tier change | Operationally material | Budget review; adjust limits or suspend |
| Terms/privacy/licence change | Legal/security gate | Immediate use review; suspend if unacceptable |
| Credential scope or auth flow change | Security gate | Re-consent, rotate, audit and test least privilege |
| Webhook payload/signature change | Security/reliability gate | Validate version, replay handling and fixtures |
| Provider outage or elevated errors | Operational incident | Degrade, disable, reconcile unknown outcomes |

Semantic version numbers are not proof of compatibility. Provider API changelogs and behavior take precedence over assumptions based on package version alone.

## 5. Monitoring and review cadence

| Cadence | Activity | Evidence |
|---|---|---|
| Per operation | Capture provider, model, adapter version, operation, outcome, latency, usage and correlation ID | Redacted operation record |
| Daily while pilot/active | Review failures, quota exhaustion, retries, unknown outcomes and spend | Health summary |
| Weekly | Review provider/API incidents, rate limits, cost trend and deprecation notices | Weekly integration health note |
| Monthly | Re-check pricing, terms, data handling, commercial-use eligibility and account limits | Dated terms/pricing snapshot |
| Quarterly | Dependency/security review, credential scope, access list, backup/restore and exit readiness | Quarterly review record |
| On provider notice | Assess breaking changes, security incident, model deprecation, terms update | Change impact assessment |
| Before release | Contract tests, migration/rollback, compatibility and acceptance evidence | Release gate record |

Cadence may be tightened for high-risk distribution or credential-bearing integrations. No health check should generate paid calls or side effects unless included in an approved budget/scope.

## 6. Health indicators and triggers

Track at minimum:
- request success/error rate by operation and provider;
- p50/p95 latency and timeout rate;
- 429/quota exhaustion and Retry-After frequency;
- retry count and retry exhaustion;
- unknown remote outcomes and reconciliation age;
- usage and cost per task, provider, model and account;
- provider/model/SDK version drift and upcoming sunset dates;
- rights evidence completeness and blocked asset count;
- credential expiry/rotation age and permission drift;
- webhook signature failures and replay attempts.

**Immediate suspend triggers:** suspected credential exposure, provider terms/data-use change that invalidates approved use, rights/licensing failure, unauthorized external side effect, security incident, or inability to reconcile a potentially duplicated distribution action.

Threshold numbers are not invented here. They must be defined by service owner and risk class after baseline data exists.

## 7. Incident and rollback playbook

1. Stop new requests using a provider-level disable switch.
2. Preserve safe diagnostics and operation correlation IDs; redact payloads and secrets.
3. Classify in-flight calls: confirmed success, confirmed failure, or unknown.
4. For unknown side effects, reconcile remote state before retry or fallback.
5. Prevent fallback from bypassing rights, approval, quality, budget or data-class constraints.
6. Route eligible work to an approved alternative only if semantic/quality compatibility has been demonstrated.
7. Record incident, scope, impact, timeline, root cause, provider response and remediation.
8. Re-enable only after owner/security approval and required acceptance tests.

A rollback must not delete historical artifacts, immutable versions, approvals or audit evidence. Data retention and purge follow WP4 and legal policy.

## 8. Deprecation and exit plan

Every APPROVED integration must document:
- provider/model/API sunset notice source and monitoring owner;
- replacement candidate and compatibility gaps;
- export format and ability to retrieve user-owned artifacts/data;
- migration mapping for provider-specific IDs;
- credential revocation and deletion request process;
- cost/contract termination steps;
- final verification and evidence retention;
- fallback behavior during migration.

Provider-specific IDs are external references only; canonical Content OS IDs remain stable. Never rewrite immutable ArtifactVersion identity because a provider is replaced.

## 9. Ownership and separation of duties

| Responsibility | Accountable role |
|---|---|
| Business capability and canonical port | Domain/contract owner |
| Provider adapter and SDK compatibility | Integration maintainer |
| Credentials and permission scope | Security/credential owner |
| Cost and quota | Service owner / budget owner |
| Rights and commercial terms | Rights/legal owner |
| Quality and benchmark | Editorial/QA owner |
| Distribution action authorization | Central governance/authorization owner |
| Incident coordination | Named service owner |
| Provider retirement | Domain owner + integration maintainer + security |

Agent roles can assist with research, code review and test generation; they do not inherit owner approval or credentials by default.

## 10. Required integration register fields

Each integration record must contain:
- integration ID, provider ID, capability, purpose and owner;
- lifecycle state, status evidence and last verified timestamp;
- internal adapter, canonical contract, provider API, model and SDK versions;
- source paths, official docs, changelog and terms/pricing URLs;
- allowed data class, retention/training/region notes;
- auth scope profile reference (never secret value);
- cost model, budget cap, quota and alert threshold;
- timeout, retry, idempotency and unknown-outcome strategy;
- rights/licence/attribution constraints;
- tests, acceptance evidence, rollback and disable procedure;
- next review date, deprecation date and replacement plan.

## 11. Open owner decisions

- GOV-OD-01: Approve lifecycle states and responsible owner roles.
- GOV-OD-02: Define numeric health thresholds after operational baselines exist.
- GOV-OD-03: Set review cadence for active, pilot and read-only integrations.
- GOV-OD-04: Define retention for provider request metadata and external IDs under WP4/privacy policy.
- GOV-OD-05: Confirm incident severity and escalation ownership.
- GOV-OD-06: Confirm provider/model pinning and upgrade windows for production use.

## 12. Change log

- 0.1 — First-pass integration lifecycle, compatibility, monitoring, incident and retirement governance. Proposed only; no runtime monitoring or provider activation performed.
