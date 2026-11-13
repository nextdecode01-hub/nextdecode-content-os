# External Provider Adapter Reference Architecture

**Document ID:** INT-ARCH-001 | **Version:** 0.1 draft | **Date:** 2026-11-04  
**Status:** Proposed reference architecture; subordinate to P0 canonical contracts and accepted ADRs/CFs. No implementation authorization.

## 1. Objective

Define one repeatable way to integrate LLMs, research feeds, TTS, generated media, stock media, object storage, notifications, analytics and platform distribution without coupling Content OS business logic to vendor APIs.

The existing Shorts Studio remains the specialist production engine. It is integrated through a bounded adapter. This design does not rewrite it or move its internal provider chains into the Content OS domain model.

## 2. Logical layers

1. **Domain service** — owns the business capability and state transition (research, script, asset, review, distribution, analytics).
2. **Policy/authorization layer** — decides whether the requested operation is permitted, using canonical rights, approval, quality and authorization records.
3. **Integration port** — versioned internal interface owned by the domain/contract owner.
4. **Provider adapter** — maps the port to one provider's API/SDK; handles auth, serialization, pagination, rate limits, retries and provider error normalization.
5. **External provider** — remote API/service; never treated as the system of record for Content OS workflow state.
6. **Evidence/telemetry recorder** — stores safe request metadata, provider/version, usage, provenance and outcome references through canonical persistence/event mechanisms.

## 3. Separation of responsibility

| Concern | Owner | Must not be delegated to |
|---|---|---|
| Business lifecycle and state | Content OS domain service | Provider adapter or n8n |
| Rights, approval, authorization | Governance/policy service | Agent prompt, workflow node or platform adapter |
| Provider API translation | Provider adapter | Domain service |
| Durable jobs, attempts and recovery | Canonical workflow/queue services | Provider callback alone |
| Artifact identity/version/metadata | Artifact domain and relational store | Object storage bucket |
| Binary bytes | Object-storage adapter | Relational DB as a large binary store |
| Human review | Review/approval service and authorized human | Provider quality score or automation |
| Analytics ingestion | Read-only analytics adapter | Publishing adapter |
| Orchestration trigger | n8n or another workflow adapter | Canonical durable state |

## 4. Port families and minimum operations

| Port family | Illustrative operations | Special rules |
|---|---|---|
| Model generation | generate_text, classify, embed, generate_image | Capture provider/model, prompt template version, token/image usage, safety outcome and data policy |
| Research source | search, fetch_item, fetch_page, fetch_feed | Store source identity, canonical URL, publisher, source time, retrieval time, evidence excerpt and freshness |
| Speech | synthesize, inspect_capabilities | Capture voice/model, language, format, duration, character/credit usage and commercial-use eligibility |
| Media source | search_assets, fetch_asset_metadata, download_asset | Require licence/creator/page evidence and immutable source snapshot before asset becomes publishable |
| Object storage | put_object, get_object, head_object, delete_object | Object keys are opaque; DB stores metadata/version/checksum; deletion follows retention/purge authorization |
| Notification | send_notice, get_delivery_status | No secrets or sensitive payloads; notifications never grant approval or authorization |
| Platform distribution | validate_package, create_upload, get_remote_status | Authorization check immediately before side effect; human approval; private/unlisted destination defaults; reconcile unknown outcomes before retry |
| Analytics | query_metrics, fetch_report | Read-only; preserve source, dimensions, period, attribution window and freshness |

Operations are illustrative only; exact names and schemas must be approved through the canonical API/Event and domain contracts.

## 5. Request/response and lifecycle

A provider operation should follow this logical lifecycle:

1. Domain service creates an internal operation request with a stable correlation identity.
2. Policy layer validates actor/service capability, content state, rights, approval, quality and requested external action.
3. Durable workflow service records the attempt before dispatch.
4. Adapter validates request schema and provider capability/version, then sends the minimum payload.
5. Adapter maps provider response/error into a normalized outcome and retains safe provider references.
6. Domain service records the result and emits canonical events.
7. If response is lost after a possible side effect, outcome is `unknown`; recovery queries provider state or requires manual reconciliation. It must not blindly replay.

The actual entity names, status vocabulary, event envelope, state-version and retry semantics must be mapped to the accepted canonical standards. This document must not introduce competing lifecycle states.

## 6. Error classification and retry policy

| Class | Examples | Default behavior |
|---|---|---|
| Invalid request | 400, schema mismatch, unsupported model | Permanent failure; do not retry unchanged request |
| Authentication/authorization | 401/403, expired or insufficient scope | Stop; alert credential owner; no repeated retries |
| Quota/rate limit | 429, provider quota exhausted | Respect Retry-After; bounded backoff; do not retry billing/quota exhaustion indefinitely |
| Transient provider fault | 5xx, connection reset before request accepted | Bounded retry only if operation is safe/idempotent |
| Timeout before dispatch certainty | Client timed out, provider acceptance unknown | Mark unknown; reconcile before retry for side-effecting operations |
| Provider accepted async job | 202/job ID/prediction ID | Persist remote operation reference; poll/webhook with bounded schedule |
| Partial response | Missing asset URL, incomplete metadata | Validate; preserve diagnostic evidence; fail closed for publishability |
| Rights/policy failure | Missing licence, prohibited content, terms uncertainty | Block downstream use; no fallback that silently removes rights requirements |

## 7. Security and data boundaries

- Adapter credentials are service-scoped, least-privilege, environment-specific and never exposed to agents.
- Provider allowlists and tool annotations are defense-in-depth, not the security boundary. Enforce process/container/OS permissions and network egress policy where appropriate.
- Request payloads are classified before egress. Default deny for sensitive/private project material.
- Logs contain correlation IDs and redacted error metadata, not raw secrets, tokens, full private prompts or personal data.
- Webhooks require signature/authentication validation, replay protection, timestamp checks and idempotent event ingestion.
- Provider callback payloads are untrusted input; validate schema, size, content type and ownership.
- Publishing/distribution authorization is rechecked at the side-effect boundary. No workflow/agent/provider adapter may bypass it.

## 8. Provider capability and configuration registry

A future registry should track, per provider and operation:
- stable provider ID, adapter version and supported operation list;
- provider API version and model/endpoint IDs;
- data classification allowed, region and retention/training terms;
- auth mechanism and scope set (secret references only, never secret values);
- price unit, quota dimensions, account-specific limit snapshot and budget policy;
- request/response schema version, timeout, concurrency and retry policy;
- idempotency support, remote status lookup and webhook support;
- rights/licensing constraints, attribution requirements and commercial-use flag;
- health evidence timestamp, source and confidence;
- enabled/disabled state and owner approval record.

A provider marked enabled does not itself authorize a business operation. Authorization remains domain/policy-owned.

## 9. Integration rollout waves

| Wave | Work | Exit criteria | Explicitly out of scope |
|---|---|---|---|
| W0 — Inventory closure | Audit every adapter and caller; map contracts, secrets by reference, provider docs and runtime evidence | Complete evidence-backed provider matrix; source conflicts resolved or explicitly retained | Installing or activating providers |
| W1 — Contract mapping | Map provider operations to canonical domain/API/Event/Artifact/Rights/Approval/Distribution contracts | Owner-reviewed port definitions and error/outcome mapping | New canonical state vocabulary without owner decision |
| W2 — Local contract harness | Mock provider responses; test schema, error classes, retries and unknown outcomes offline | Deterministic contract tests and sanitized fixtures | Live API calls, credentials, uploads |
| W3 — Non-side-effecting sandbox | Only after approval, run low-risk read-only operations with scoped credentials and cost ceilings | Observability, quota, privacy and rollback evidence | Publishing, destructive writes |
| W4 — Controlled generation | Owner-approved generation operations with explicit spend cap and asset provenance | Reproducible provider/model lineage, rights review and quality gates | Public publishing |
| W5 — Distribution pilot | Only after separate explicit authorization and all P0 policy gates close | Private/unlisted pilot, human approval, unknown-outcome reconciliation, audit evidence | Public/automatic publishing unless separately authorized |

## 10. Contract and workstream dependencies

- **WP1:** canonical identity, ownership, typed references and persistence boundaries. No provider-owned primary entities.
- **WP2:** durable workflow/job/attempt lifecycle and recovery; provider async jobs are external references, not canonical jobs.
- **WP3:** worker identity, capability authorization, scoped credentials and trust boundaries.
- **WP4:** Artifact/ArtifactVersion, manifests, object storage, retention and deletion.
- **WP5:** rights evidence, quality outcomes, review/approval and action authorization.
- **WP6:** adapter contract tests, fault injection, unknown outcomes, webhook security, rollback and acceptance evidence.

P0-A remains a narrow durable content-workflow vertical slice. This adapter catalogue is not permission to expand P0-A into a complete integration platform or Control Center.

## 11. Decisions still required

1. Canonical owner and exact contract version for each port family.
2. Whether model-provider routing policy is centralized in Content OS or remains inside the Shorts Studio adapter during P0.
3. Provider-specific data classification and permitted payload rules.
4. Secret manager/runtime design and credential rotation owner.
5. Artifact storage and retention decisions under WP4.
6. Retry, deduplication, idempotency and reconciliation semantics under WP2/WP6.
7. Per-provider spend caps and free-tier/commercial-use acceptability.
8. Whether any live provider test is authorized, by whom, against which account and with what exact operation.

## 12. Acceptance gate

No adapter may be activated until its port contract, provider terms, data policy, credential scope, cost ceiling, failure semantics, rights evidence, tests, rollback and owner approval are recorded. Distribution adapters additionally require the complete human-approval and centralized-authorization chain.

## 13. Change log

- 0.1 — First-pass provider-neutral architecture and rollout waves. Planning only; no code or configuration changed.
