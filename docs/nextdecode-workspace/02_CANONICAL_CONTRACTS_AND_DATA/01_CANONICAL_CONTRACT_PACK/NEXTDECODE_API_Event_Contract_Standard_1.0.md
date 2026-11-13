# NEXTDECODE — API & Event Contract Standard
**Version:** 1.0  
**Status:** Architecture specification — documentation only  
**Scope:** Shared Intelligence Core, specialized studios, orchestration, workers, Control Center and external integrations  
**Companions:** System Architecture Master Reference 1.0; Parts 3–8; Shared Intelligence Core Contracts 01–12; Canonical Data Dictionary & Entity Ownership Registry 1.0; Unified Lifecycle & State Transition Standard 1.0

---

## 1. Purpose

This standard defines the communication contracts that allow NEXTDECODE modules, studios, agents, workers and integrations to work as one platform without becoming tightly coupled.

It establishes:
- API design conventions for synchronous request/response interactions.
- Command contracts for requesting state changes or work.
- Event contracts for notifying other domains of committed facts.
- Identity, scope, authentication and authorization requirements.
- Versioning, compatibility, idempotency, error handling and pagination.
- Asynchronous job submission and status/result retrieval.
- External adapter boundaries and webhook safety.
- Contract ownership, documentation and conformance testing.

The goal is not to expose every internal object as an API. It is to provide stable, versioned boundaries around domain capabilities and durable events.

**Documentation-only boundary:** This standard does not authorize repository inspection or changes, API implementation, external account connection, provider selection, infrastructure provisioning, spending, uploads or publishing.

## 2. Normative language

**MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT** and **MAY** are requirements:

- **MUST / MUST NOT:** mandatory.
- **SHOULD / SHOULD NOT:** expected default; deviations require a documented rationale.
- **MAY:** optional.

## 3. Contract architecture

### 3.1 Three communication patterns

| Pattern | Use it for | Example |
|---|---|---|
| Query API | Read an authorized current view or retrieve a resource | Get a content item or research run |
| Command API | Request an action or state transition from its owner | Submit a research request; request approval |
| Event | Publish a committed fact for interested consumers | Research run completed; quality assessment recorded |

These patterns MUST remain conceptually distinct.

- A query MUST NOT mutate authoritative state.
- A command expresses intent; it is not proof the requested action succeeded.
- An event records a fact that the owning domain has committed.
- An event consumer MUST NOT reinterpret an event as permission to perform a protected action.
- A synchronous HTTP response does not replace a durable event when downstream consumers need reliable notification.

### 3.2 Domain ownership

Each API and event MUST have one owning domain.

The owner:
- defines its schema and semantics;
- validates commands;
- authorizes and commits its state transitions;
- publishes authoritative events;
- documents compatibility;
- maintains contract tests.

Consumers may request changes through the owner's command interface. They MUST NOT write directly into another domain's tables or state store.

### 3.3 Internal and external APIs

The same semantic contract SHOULD be reusable across internal services and selected external integrations, but exposure is not automatic.

Internal-only fields, operational details, confidential evidence and privileged commands MUST NOT be exposed merely because an internal API exists.

External APIs require a separately approved exposure policy, authentication model, data classification review, rate limits and support commitments.

---

## 4. API conventions

### 4.1 Protocol and representation

The architecture baseline is versioned HTTP/JSON with schema validation.

Recommended defaults:
- HTTPS for network communication.
- JSON request and response bodies encoded as UTF-8.
- Explicit content types.
- UTC timestamps in ISO 8601/RFC 3339 form.
- UUIDv7 canonical identifiers serialized as strings.
- Decimal strings or integer minor units for financial values; do not use binary floating-point for money.
- Explicit units and currency codes for measured values.
- No implicit timezone assumptions.

The exact HTTP framework, gateway, service mesh and deployment topology remain implementation decisions.

### 4.2 Resource naming

Use stable, plural resource paths with lowercase kebab-case where appropriate.

Illustrative patterns:

```text
GET    /v1/content-items/{content_item_id}
GET    /v1/research-runs/{research_run_id}
POST   /v1/research-requests
POST   /v1/approval-requests
GET    /v1/jobs/{job_id}
GET    /v1/workflows/{workflow_id}
GET    /v1/distribution-packages/{package_id}
```

These are contract examples, not a final endpoint inventory.

Rules:
- Resource IDs are canonical UUIDv7 values.
- Display slugs and human-readable labels are not identifiers.
- Avoid embedding mutable names in resource paths.
- Use explicit action/command subresources only when the operation is not naturally represented by resource creation or a standard update.
- Do not expose database table names as public API design.

### 4.3 HTTP method semantics

| Method | Intended semantics |
|---|---|
| `GET` | Read; safe and idempotent |
| `POST` | Create a resource or submit a command |
| `PUT` | Replace a resource representation where full replacement is intended |
| `PATCH` | Apply a defined partial update |
| `DELETE` | Request deletion according to retention/legal-hold policy |

A `POST` command MUST NOT be treated as completed merely because the request was accepted.

For long-running work, return a durable job/workflow reference and an explicit accepted/queued result.

### 4.4 Response envelope

Responses SHOULD use a consistent outer structure while preserving domain-specific resource schemas.

Successful resource response example:

```json
{
  "data": {
    "id": "0195f4b2-7d30-7a21-9f9d-0e1d1d0f0001",
    "type": "research_run",
    "state": "COMPLETED",
    "state_version": 7
  },
  "meta": {
    "request_id": "0195f4b2-7d30-7a21-9f9d-0e1d1d0f0002",
    "schema_version": "1.0"
  }
}
```

The example UUIDs are illustrative only.

Responses MUST NOT expose fields the caller is not authorized to read. Redaction must happen at the service boundary, not only in the UI.

### 4.5 Error envelope

Errors SHOULD use a stable structure:

```json
{
  "error": {
    "code": "STATE_VERSION_CONFLICT",
    "message": "The resource changed after the supplied version.",
    "retryable": false,
    "details": {
      "current_state_version": 8
    }
  },
  "meta": {
    "request_id": "0195f4b2-7d30-7a21-9f9d-0e1d1d0f0003"
  }
}
```

Error messages MUST be safe for the caller and MUST NOT reveal secrets, internal stack traces, private prompts, credentials or restricted evidence.

The machine-readable `code` is authoritative for client behavior. Human-readable `message` may change without changing the code's semantics.

---

## 5. Command contracts

### 5.1 Command envelope

Commands SHOULD include:

| Field | Meaning |
|---|---|
| `command_id` | Unique command identifier |
| `command_type` | Stable command name |
| `command_version` | Command schema version |
| `target_type` / `target_id` | Target entity, if already known |
| `workspace_id` and relevant scope IDs | Authorized scope |
| `requested_by` | Authenticated actor reference |
| `requested_at` | UTC request time |
| `expected_state_version` | Required for state-changing commands |
| `idempotency_key` | Required for retryable commands |
| `correlation_id` | End-to-end business operation |
| `causation_id` | Event or command that led to this request |
| `policy_context_ref` | Reference to applicable policy context; not a caller assertion of permission |
| `payload` | Domain-specific command data |

The server MUST derive actor identity and effective permissions from authenticated context. It MUST NOT trust caller-supplied `requested_by` as proof of identity.

### 5.2 Command outcomes

A command response MUST distinguish at least:

- `ACCEPTED`: request passed initial validation and was durably accepted; work may still be pending.
- `COMPLETED`: synchronous operation committed successfully.
- `REJECTED`: request was not accepted.
- `CONFLICT`: state/version conflict requires reload or reconciliation.

For asynchronous commands, `ACCEPTED` MUST include the durable job/workflow/resource reference and a way to query its status.

A command being accepted is not a guarantee that all later workflow stages will succeed.

### 5.3 Command authorization

Every command MUST be checked for:
1. Authenticated actor identity.
2. Workspace and resource scope.
3. Capability/role authorization.
4. Current policy and security constraints.
5. State-machine legality.
6. Expected state version where applicable.
7. Required approval or governance decision.
8. Resource/budget limits where relevant.

The service owning the transition makes the authoritative decision. An API gateway may perform coarse checks but MUST NOT replace domain authorization.

### 5.4 Commands that request protected actions

Commands such as publish, upload, schedule, spend, invite, delete or change policy require action-specific authorization.

For a publishing command, the service MUST validate the exact:
- artifact ID and immutable version;
- distribution package/version;
- destination account/channel;
- operation type;
- applicable governance authorization;
- policy version and validity window;
- emergency pause status.

The client MUST NOT be allowed to submit a generic `approved: true` field as authorization.

Autonomous public publishing remains disabled pending explicit owner approval of a separate policy. This API standard does not enable it.

---

## 6. Query contracts

### 6.1 Query rules

Queries MUST:
- be read-only;
- enforce workspace and resource scope;
- apply field-level authorization and redaction;
- identify freshness when reading an eventually consistent projection matters;
- avoid returning internal secrets or unnecessary personal data.

Queries SHOULD return canonical IDs and version references rather than duplicating mutable domain data.

### 6.2 Pagination

Collection endpoints SHOULD use cursor-based pagination.

Recommended response metadata:
- `next_cursor`;
- `has_more`;
- `page_size`;
- optional `snapshot_version` or `as_of` value.

Rules:
- Cursors are opaque to clients.
- Clients MUST NOT construct or modify cursors.
- Stable ordering MUST be defined.
- A cursor MUST be bound to the caller's scope and query context.
- Pagination MUST NOT leak records across workspaces.

Offset pagination MAY be used for small, stable administrative lists where its limitations are understood.

### 6.3 Filtering and sorting

- Filter fields MUST be documented and allowlisted.
- Sort fields MUST be allowlisted.
- Filtering MUST not bypass authorization.
- Large or expensive queries SHOULD be bounded.
- Search semantics SHOULD be explicit about exact, prefix, full-text or semantic matching.

---

## 7. Event contract standard

### 7.1 Event meaning

An event announces a committed fact, not an intention.

Examples:
- `research.run.completed`
- `quality.assessment.recorded`
- `rights.decision.recorded`
- `approval.request.expired`
- `studio.production.completed`
- `distribution.operation.outcome_unknown`
- `performance.snapshot.recorded`

Names are illustrative. A central catalogue MUST prevent semantic collisions.

### 7.2 Event envelope

Every event MUST comply with the common envelope in the Unified Lifecycle & State Transition Standard 1.0.

At minimum:
- `event_id`;
- `event_type`;
- `event_version`;
- `occurred_at`;
- `recorded_at`;
- `producer`;
- `entity_type`;
- `entity_id`;
- `workspace_id` and applicable scope;
- `state_machine`;
- `state_version`;
- `previous_state` and `new_state`, where it is a state transition;
- `actor_ref` and `actor_type`;
- `reason_code`;
- `correlation_id`;
- `causation_id`;
- `policy_version`, where applicable;
- `data` payload;
- `schema_version`.

The event envelope and lifecycle envelope MUST be aligned. Implementations may use one physical schema or a clearly mapped composition, but MUST NOT create competing meanings for the same field.

### 7.3 Event naming

Recommended convention:

`<domain>.<aggregate>.<past-tense-fact>`

Examples:
- `research.run.completed`
- `audience.segment.updated`
- `quality.assessment.recorded`
- `governance.authorization.denied`
- `studio.production.failed`
- `distribution.publication.confirmed`

Event names MUST describe what happened, not what a consumer should do.

Avoid command-like names such as `publish.now` or `create.video` as event types.

### 7.4 Event payload design

Payloads SHOULD contain:
- the identity and version of the affected entity;
- the minimum data needed for consumers to react;
- references to larger or sensitive records;
- explicit schema version.

Payloads SHOULD NOT duplicate entire mutable domain objects. Consumers that need the latest authorized representation should query the owning API.

Events MUST NOT contain:
- credentials, access tokens or secrets;
- unnecessary personal data;
- unrestricted raw research content;
- unredacted provider payloads;
- private prompts or internal reasoning traces.

### 7.5 Delivery semantics

The event backbone SHOULD assume at-least-once delivery.

Therefore:
- consumers MUST be idempotent;
- duplicate events MUST be safe;
- ordering MUST be defined per aggregate/state machine using `state_version`;
- consumers MUST tolerate delayed and out-of-order delivery;
- events with a version gap SHOULD trigger authorized reconciliation with the owning domain;
- poison messages MUST be isolated and observable.

The architecture MUST NOT promise global exactly-once delivery.

### 7.6 Transactional outbox and inbox

A producer MUST persist its state transition and outbox event atomically.

A consumer SHOULD persist its inbox/deduplication record and local side effect atomically where both share a transaction boundary.

Cross-service effects require idempotent commands or explicit reconciliation; a distributed transaction MUST NOT be assumed.

### 7.7 Replay

Event replay MAY be supported for rebuilding projections or recovering consumers.

Replay MUST:
- preserve original event identity and timestamps;
- identify replay mode and replay actor/process;
- avoid re-triggering external side effects by default;
- use idempotency and replay-safe consumer behavior;
- revalidate current authorization before any newly requested external action.

A replayed historical event is not a new approval.

---

## 8. API and event versioning

### 8.1 Version dimensions

Keep these version dimensions separate:
- API major version (`/v1`);
- resource representation schema version;
- command schema version;
- event schema version;
- state-machine version;
- policy version;
- artifact/content version.

A change to one does not automatically increment all the others.

### 8.2 Compatibility policy

Compatible changes generally include:
- adding optional response fields;
- adding optional event payload fields;
- adding new endpoints;
- adding new event types;
- adding optional query filters.

Potentially breaking changes include:
- removing or renaming fields;
- changing field type or meaning;
- changing requiredness;
- changing state transition legality;
- changing authorization semantics;
- changing event ordering or delivery assumptions;
- changing identifier semantics.

Breaking changes require a new major or explicitly versioned contract and a migration plan.

### 8.3 Consumer-driven compatibility

Producers SHOULD maintain contract tests against known consumers.

Consumers MUST:
- ignore unknown optional fields;
- reject unsupported required schema versions safely;
- avoid assuming fields not declared required;
- handle unknown event types without crashing the whole consumer;
- record unsupported messages for controlled review.

### 8.4 Deprecation

A deprecated endpoint/event MUST have:
- a replacement;
- a published deprecation date or condition;
- a migration guide;
- usage/consumer visibility;
- a removal approval and compatibility assessment.

No contract should be removed solely because the producer no longer uses it; consumer impact must be checked.

---

## 9. Authentication, identity and authorization

### 9.1 Identity model

The architecture distinguishes:
- owner/human identity;
- other human roles;
- agent identity;
- service identity;
- worker identity;
- external integration identity.

An agent or worker MUST NOT impersonate the owner.

### 9.2 Authentication

Network APIs MUST authenticate callers.

Preferred architecture properties:
- short-lived credentials;
- scoped tokens;
- secure secret storage;
- rotation and revocation;
- strong human authentication, with MFA/passkeys where supported;
- separate identities for services, agents and workers.

Exact identity provider and protocol remain open implementation decisions.

### 9.3 Authorization

Use least-privilege, capability-based authorization with explicit scope.

An authorization decision SHOULD include:
- subject/actor;
- requested action;
- resource and version;
- workspace/brand/studio scope;
- policy version;
- decision and reason;
- validity window;
- obligations/conditions;
- audit reference.

Permissions MUST NOT be inferred from the ability to call an endpoint.

### 9.4 Agent and worker restrictions

- Agents receive task-scoped permissions.
- Workers receive only the capabilities needed for their assigned job.
- Credentials are short-lived and revocable.
- Agents cannot grant themselves or other agents permissions.
- A task payload is not an authorization token.
- Tool/provider access must be checked at execution time.
- A retry after expiry or revocation must reauthorize.

### 9.5 Service-to-service access

Service calls MUST carry authenticated service identity and end-user/agent delegation context where applicable.

Delegation context MUST be verifiable and bounded by the delegator's own authority. A downstream service MUST NOT accept arbitrary caller-supplied claims of delegation.

---

## 10. Idempotency, concurrency and retries

This section aligns with the Unified Lifecycle & State Transition Standard.

### 10.1 Idempotency keys

Retryable commands MUST accept an idempotency key.

The key scope SHOULD include:
- caller identity;
- command type;
- target resource or intended creation scope.

The server MUST store a request fingerprint and original outcome. Same key + same request returns the original outcome; same key + different request is rejected.

### 10.2 Conditional updates

State-changing commands MUST include `expected_state_version` or an equivalent conditional token.

Stale requests return a structured conflict. They MUST NOT overwrite current state silently.

### 10.3 Retry classification

| Operation | Retry rule |
|---|---|
| Read-only query | Retry according to bounded client policy |
| Pure computation | Retry if inputs/configuration are stable |
| Durable job submission | Retry with same idempotency key |
| Idempotent provider operation | Retry only under provider's documented idempotency semantics |
| Non-idempotent external operation | Reconcile before retry |
| Unknown external outcome | Never blindly retry |

Retry/backoff values are implementation configuration and remain open.

---

## 11. Asynchronous APIs and durable work

### 11.1 Accepted job pattern

For work that may outlive an HTTP request, return an accepted response with durable references.

Illustrative response:

```json
{
  "data": {
    "command_status": "ACCEPTED",
    "workflow_id": "0195f4b2-7d30-7a21-9f9d-0e1d1d0f0010",
    "job_id": "0195f4b2-7d30-7a21-9f9d-0e1d1d0f0011",
    "status_url": "/v1/jobs/0195f4b2-7d30-7a21-9f9d-0e1d1d0f0011"
  }
}
```

Illustrative IDs and paths are not assigned production values.

### 11.2 Status and result

A job status API SHOULD expose:
- job ID and state;
- workflow/correlation references;
- attempt count;
- created/started/updated timestamps;
- safe progress summary;
- checkpoint availability;
- result/artifact references when complete;
- sanitized failure code and retryability;
- cancellation/pause state.

It MUST NOT expose secrets, private prompts or restricted source material.

### 11.3 Callback and webhook

Webhooks MAY notify an authorized consumer that a durable event or job result is available.

Webhook requirements:
- authenticated sender;
- signature or equivalent message integrity;
- timestamp and replay protection;
- stable event ID;
- bounded retry policy;
- idempotent receiver;
- secret rotation;
- delivery logs without secret leakage.

A webhook is a notification mechanism, not the authoritative state store. Consumers SHOULD retrieve the canonical resource/event after notification.

---

## 12. External integration and adapter contracts

### 12.1 Adapter boundary

Each external provider/platform integration MUST be isolated behind an adapter contract.

The adapter translates:
- internal canonical commands to provider requests;
- provider responses to canonical result states;
- provider identifiers to stored external references;
- provider errors to safe normalized error classes.

Domain services MUST NOT spread provider-specific semantics throughout the platform.

### 12.2 Capability declaration

An adapter SHOULD declare:
- provider and adapter version;
- supported operations;
- supported idempotency behavior;
- status-query/reconciliation support;
- cancellation support;
- rate limits and quota behavior;
- required scopes/permissions;
- data categories transferred;
- known limitations.

A declared capability is not proof that the owner has authorized its use.

### 12.3 Provider errors

Normalize errors into stable categories, such as:
- authentication/authorization;
- validation;
- rate limit;
- quota/billing limit;
- transient transport;
- permanent provider failure;
- unsupported capability;
- uncertain outcome.

Preserve a sanitized provider code/reference for diagnosis. Never expose credentials or unrestricted raw response bodies.

### 12.4 External data protection

Before transmitting data to an external AI or other provider:
- verify the provider is approved for the data category;
- verify contractual/data-protection terms and training-use restrictions;
- minimize and redact data;
- verify retention and processing location requirements;
- block the transfer if required protections cannot be verified.

Provider connection or data transfer requires separate authorization.

---

## 13. Resource governance and budgets

APIs that schedule work or allocate compute MUST enforce approved resource limits.

Distinguish:
- technical quota (CPU, memory, concurrency, storage, API calls);
- provider quota/rate limit;
- financial budget and actual expenditure;
- strategic allocation within an approved envelope.

An agent may recommend resource changes. It may redistribute only within already approved boundaries where policy permits. It MUST NOT increase budgets, create subscriptions, incur new commitments or spend funds without explicit owner authorization.

A request that exceeds a limit MUST return a structured denial or a pending owner-approval outcome; it MUST NOT silently provision more capacity.

---

## 14. Data classification and field-level exposure

Every API field and event payload MUST be classified or inherit classification from its governed source.

Minimum classes:
- `PUBLIC`
- `INTERNAL`
- `CONFIDENTIAL`
- `RESTRICTED`

Requirements:
- apply least-privilege field filtering;
- minimize payloads;
- avoid cross-workspace leakage;
- use references for sensitive data;
- enforce retention and deletion;
- honor consent and purpose limitation;
- prevent unauthorized audience identity matching across platforms;
- do not expose customer data for monetization or intelligence resale.

Access to a resource does not imply ownership of its IP or permission to redistribute it.

---

## 15. Observability and operational error handling

Every API request SHOULD carry or receive:
- request ID;
- correlation ID;
- trace ID;
- authenticated actor/service identity;
- workspace scope;
- API/contract version.

Every event and asynchronous job MUST preserve correlation across service boundaries.

Metrics SHOULD include:
- request rate and latency;
- error rate by normalized code;
- command acceptance/rejection;
- queue age and job duration;
- retry and dead-letter counts;
- event lag and consumer failures;
- provider rate limits;
- unknown external outcomes;
- reconciliation backlog;
- authorization denials;
- resource consumption.

Logs MUST be structured and sanitized. Monitoring data MUST respect classification and access boundaries.

---

## 16. Contract catalogue and ownership

A central machine-readable and human-readable catalogue SHOULD register:

| Catalogue field | Purpose |
|---|---|
| Contract ID | Stable identifier |
| Name and domain | Ownership and discoverability |
| Contract type | Query API, command, event, webhook or schema |
| Owner | Authoritative domain/team |
| Consumers | Known authorized consumers |
| Schema/version | Compatibility reference |
| Data classification | Exposure requirements |
| Required capabilities | Authorization needs |
| Idempotency behavior | Retry safety |
| State-machine reference | Lifecycle semantics |
| Deprecation status | Migration planning |
| Conformance tests | Evidence of compatibility |

The catalogue MUST be version-controlled through an explicitly authorized process. This specification does not authorize repository changes.

---

## 17. Contract testing and acceptance criteria

### 17.1 API tests
- [ ] Every endpoint has an owner, schema and version.
- [ ] Authentication is required for protected resources.
- [ ] Workspace/resource scope is enforced.
- [ ] Field-level redaction is tested.
- [ ] Query endpoints do not mutate state.
- [ ] Commands distinguish accepted from completed.
- [ ] State-changing commands enforce expected version.
- [ ] Idempotency behavior is tested.
- [ ] Errors use stable codes and safe messages.
- [ ] Pagination is stable and scope-bound.

### 17.2 Event tests
- [ ] Events represent committed facts.
- [ ] Envelope fields align with the lifecycle standard.
- [ ] Producer state and outbox event are atomic.
- [ ] Duplicate delivery is safe.
- [ ] Out-of-order and delayed events are handled.
- [ ] Unknown event types do not crash consumers.
- [ ] Replay does not repeat external side effects.
- [ ] Event payloads contain no secrets or unnecessary personal data.

### 17.3 Security tests
- [ ] Human, agent, service and worker identities are distinct.
- [ ] Delegation cannot exceed the delegator's authority.
- [ ] Expired/revoked credentials are rejected.
- [ ] Agents cannot grant permissions.
- [ ] Cross-workspace access is denied.
- [ ] Sensitive fields are not exposed through errors, logs or webhooks.
- [ ] External provider transfer is blocked without verified protections.

### 17.4 External-operation tests
- [ ] Adapter validates action-specific authorization.
- [ ] Submission and confirmation remain distinct.
- [ ] Unknown outcomes are reconciled before unsafe retry.
- [ ] Provider error classes are normalized.
- [ ] Emergency pause is enforced.
- [ ] No API can infer public publishing permission from handoff or review state.

### 17.5 Compatibility tests
- [ ] Supported schema versions are explicit.
- [ ] Additive changes preserve consumers.
- [ ] Breaking changes require a migration plan.
- [ ] Deprecated contracts have replacement guidance.
- [ ] Consumer-driven tests run against proposed producer changes.

---

## 18. Required test scenarios

At minimum, test:

1. Unauthenticated request to protected endpoint is rejected.
2. Authenticated actor outside workspace scope is denied.
3. Caller cannot read restricted fields without permission.
4. Query has no side effect.
5. Command accepted returns durable job/workflow references.
6. Command rejection includes a stable machine-readable reason.
7. Duplicate command with same idempotency key returns original result.
8. Same idempotency key with altered payload is rejected.
9. Stale state version returns conflict.
10. Event is emitted only after authoritative commit.
11. Duplicate event delivery does not duplicate effects.
12. Out-of-order state event triggers safe handling/reconciliation.
13. Unknown event type is quarantined or safely ignored and observed.
14. Replay does not reissue publishing or other external side effects.
15. Agent cannot impersonate owner or expand its permission.
16. Revoked worker credential cannot continue protected work.
17. Webhook signature failure is rejected.
18. Webhook replay is detected.
19. Provider timeout after possible submission becomes `UNKNOWN_OUTCOME`.
20. Non-idempotent uncertain operation is reconciled before retry.
21. Publishing command without exact authorization is denied.
22. `APPROVED_FOR_HANDOFF` cannot satisfy publish authorization.
23. External AI transfer without verified data protections is blocked.
24. Resource/budget limit cannot be exceeded by autonomous provisioning.
25. API error/log output contains no secrets or restricted payload.
26. Breaking schema change is rejected without version/migration path.

---

## 19. Open implementation decisions

The following remain deliberately open:

- API gateway and service topology.
- Exact authentication/identity provider and protocol.
- Token format, lifetime and rotation schedule.
- HTTP framework and schema technology.
- API specification format and registry tooling.
- Event transport, partitioning and retention.
- Event schema registry and compatibility enforcement.
- Webhook signing and retry implementation.
- Rate limits and API quotas.
- Pagination cursor implementation.
- Exact endpoint and event inventory.
- Data classification mapping at field level.
- Audit retention and deletion implementation.
- Service-level objectives and observability stack.
- Provider-specific idempotency and reconciliation capabilities.
- External API exposure and customer-facing access policy.

No provider, cloud region, paid service or infrastructure choice is made here.

---

## 20. Explicit non-goals and authority boundaries

This document does not:
- approve implementation readiness;
- authorize repository, GitHub or code access;
- authorize API implementation or deployment;
- connect external accounts or providers;
- select a cloud provider, region, gateway or event broker;
- provision infrastructure, create subscriptions or incur expenditure;
- authorize external data transfer;
- authorize uploads, distribution or public publishing;
- grant agents, services or workers new permissions;
- change owner-approved policies or product strategy.

Such actions require separate explicit authorization.

## 21. Architecture decision summary

| Decision | Standard |
|---|---|
| Communication patterns | Query, command and event are distinct |
| API baseline | Versioned HTTP/JSON with schema validation |
| Contract ownership | One authoritative domain owner per contract |
| State mutation | Through owning domain command boundary |
| Events | Committed facts, not commands or permissions |
| Event delivery | At-least-once; idempotent consumers |
| State concurrency | Expected state version required |
| Long-running work | Durable job/workflow reference |
| External operations | Isolated adapters with reconciliation semantics |
| Authentication | Distinct human, agent, service and worker identities |
| Authorization | Least privilege, scoped and policy-versioned |
| Data exposure | Classified, minimized and scope-filtered |
| Public publishing | Disabled pending separate explicit owner policy approval |
| Spending/provisioning | No autonomous increase beyond approved envelope |

---

**End of Artifact 03 — API & Event Contract Standard 1.0**

**Next recommended artifact:** Artifact 04 — Policy & Authorization Decision Matrix 1.0.
