NEXTDECODE

P0 API, EVENT & SCHEMA
SPECIFICATION PACK

Batch 18 | Versioned interface contract candidate

| Document control | Value |
| --- | --- |
| Series | NEXTDECODE Content OS — P0 documentation series |
| Batch | 18 — API, Event & Schema Specification Pack |
| Prepared | 1 November 2026 |
| Status | Detailed interface candidate; not formally frozen |
| Authority | API/Event Standard 1.0 and accepted ADR/CF baseline; exact schemas and routes require owner freeze |
| Implementation | Not authorized by this document |
| Purpose | Specify command, query, event, error, idempotency, compatibility, security and integration contract patterns |

Purpose. Convert the accepted API/Event Contract Standard and the domain/state-machine candidates into a reviewable interface specification. This pack provides envelope structures, schema rules, illustrative payloads and consumer behavior. It does not freeze endpoint paths, every field constraint, transport topology or provider-specific protocol.

Interpretation rule. API/Event Standard 1.0 is the controlling source for interface principles. Illustrative routes and examples in this document are design aids only. Where the standard or accepted decisions do not settle a detail, it is marked OPEN.

## 1. Interface contract principles

- Use versioned HTTP/JSON contracts with schema validation.

- Queries read; commands request state changes; events record committed facts.

- A command response of ACCEPTED does not mean the requested work completed.

- An event is evidence of a committed fact, not permission to perform a protected action.

- Every stateful domain has one canonical owner; cross-domain writes occur through owner commands.

- Canonical identifiers are UUIDv7 and immutable; entity identity and version identity are distinct.

- State transitions use expected versions and conflict behavior; stale writes must not silently overwrite.

- Command and event schemas carry explicit versions and compatibility rules.

- Publishing operations must bind exact artifact/content version, package/version, destination, authorization and policy context.

- Automatic public publishing remains disabled pending a separate policy.

## 1.1 Contract vocabulary

| Term | Meaning |
| --- | --- |
| MUST / MUST NOT | Normative requirement / prohibition. |
| SHOULD | Strong recommendation; deviation requires documented rationale. |
| MAY | Permitted option. |
| OPEN | Not settled by accepted source decisions. |
| ILLUSTRATIVE | Example only; not a frozen endpoint, field constraint or enum. |
| Canonical owner | Only domain authorized to commit its source-of-truth state. |
| Projection | Read model derived from committed source events; not a second authority. |

## 2. Contract surface and interface types

| Interface | Purpose | Authoritative semantics | Typical consumer |
| --- | --- | --- | --- |
| Query | Read canonical state or identified projection | No mutation; response must identify consistency/authority where relevant | UI, reporting, another domain |
| Command | Express intent to perform state-changing operation | Validation, policy and state transition occur under owning domain | UI, orchestrator, worker adapter |
| Event | Publish committed fact | Emitted only after source fact commits; consumer deduplicates | Other domains, projections, audit |
| Callback / webhook | Receive external notification | Untrusted until authenticated, verified and reconciled | Distribution adapter / integration |
| Worker assignment | Deliver bounded execution instruction | Scoped to job/attempt/worker/capability and expiry | Local/cloud worker |
| Result submission | Submit worker output/result | Validated by owner; does not self-authorize downstream action | Worker to orchestrator/asset domain |

The accepted standard establishes versioned HTTP/JSON as the API direction. It does not mandate a particular API gateway, message broker, webhook vendor or deployment topology.

## 3. Canonical identifier and version rules

| Identifier | Purpose | Rules |
| --- | --- | --- |
| entity_id | Stable canonical entity identity | UUIDv7; immutable; never reused. |
| version_id | Immutable version/snapshot identity | Separate from entity_id; identifies exact content/configuration/artifact version. |
| command_id | Unique command identity | Stable across delivery/retry of the same logical command. |
| event_id | Unique committed event identity | Stable on redelivery; consumers deduplicate. |
| idempotency_key | Protects against duplicate command effects | Scope, retention and conflict semantics must be frozen. |
| correlation_id | Connects a workflow/request chain | Propagated across commands, runs, jobs, attempts and events. |
| causation_id | Identifies immediate causal predecessor | Preserves event/command causal chain. |
| operation_id | Tracks asynchronous or external operation | Durable reference returned for ACCEPTED work. |
| attempt_id | Identifies one execution attempt | New identity per retry; historical attempts preserved. |

UUIDv7 is accepted for canonical IDs. The exact choice of UUIDv7 for every non-entity technical identifier, including command/event/idempotency keys, must follow the detailed identifier registry; do not assume every key is a canonical entity ID.

## 4. Common command envelope

The command envelope below reflects the API/Event Contract Standard's required design elements. Exact field names, types, nullability, maximum lengths and schema definitions remain to be frozen in the OpenAPI/JSON Schema bundle.

| Field | Purpose | Rule / status |
| --- | --- | --- |
| command_id | Unique command identity | Required design element. |
| command_type | Select operation semantics | Required; versioned catalogue. |
| command_schema_version | Select payload/envelope schema | Required design element. |
| target_type / target_id | Identify target aggregate/entity | Required where command targets an entity. |
| workspace_id / scope | Constrain workspace/resource context | Required where applicable; exact scope schema open. |
| requested_by | Audit attribution | Actor identity derived from authenticated context; do not trust payload as proof. |
| requested_at | Request timestamp | UTC; exact format/precision follows schema standard. |
| expected_state_version | Optimistic concurrency guard | Required for version-sensitive transitions. |
| idempotency_key | Duplicate-effect prevention | Required for retryable state-changing operations; scope/TTL open. |
| correlation_id / causation_id | Trace request and causal chain | Required design elements. |
| policy_context | Policy references and evaluation context | Required where policy-controlled; exact object open. |
| payload | Command-specific fields | Validated against command_type + schema version. |

## 4.1 Illustrative command JSON

{
  "command_id": "0195f4c0-0000-7000-8000-000000000001",
  "command_type": "content.submit_for_review",
  "command_schema_version": "1.0",
  "target_type": "ContentVersion",
  "target_id": "0195f4c0-0000-7000-8000-000000000002",
  "workspace_id": "0195f4c0-0000-7000-8000-000000000003",
  "requested_at": "2026-11-01T10:00:00Z",
  "expected_state_version": 4,
  "idempotency_key": "illustrative-client-generated-key",
  "correlation_id": "0195f4c0-0000-7000-8000-000000000004",
  "causation_id": null,
  "policy_context": {"policy_version": "illustrative"},
  "payload": {"review_profile_ref": "example-review-profile"}
}

The UUIDs and command name above are illustrative examples, not reserved IDs, a frozen command catalogue or an approved endpoint. Authenticated actor identity is intentionally omitted from the example payload; the server derives it from the security context.

## 5. Command response contract

| Outcome | HTTP mapping | Meaning | Client behavior |
| --- | --- | --- | --- |
| ACCEPTED | Typically 202; exact mapping open | Durably accepted asynchronous operation | Store operation_id/reference; poll/query status; do not show completed. |
| COMPLETED | Typically 200/201; exact mapping open | Command processing reached defined completion | Read resulting canonical state. |
| REJECTED | 4xx class; exact codes open | Invalid, unauthorized or policy-blocked | Show reason; unchanged request is not blindly retried. |
| CONFLICT | Typically 409; exact mapping open | Stale expected version or state conflict | Refresh state and require deliberate new command. |

## 5.1 Illustrative ACCEPTED response

{
  "outcome": "ACCEPTED",
  "command_id": "0195f4c0-0000-7000-8000-000000000001",
  "operation_id": "0195f4c0-0000-7000-8000-000000000005",
  "accepted_at": "2026-11-01T10:00:01Z",
  "correlation_id": "0195f4c0-0000-7000-8000-000000000004"
}

The HTTP status and exact response keys are illustrative pending route/schema freeze. An asynchronous ACCEPTED response must nevertheless provide a durable reference to the accepted operation.

## 6. Query contract

| Concern | Required behavior | Open detail |
| --- | --- | --- |
| Scope | Enforce authenticated workspace/brand/resource scope | Exact scope object and permission matrix. |
| Authority | Identify whether response is canonical or a projection | Consistency metadata and staleness semantics. |
| Pagination | Use stable pagination for large collections | Cursor/offset choice and limits. |
| Filtering | Validate filter fields/operators; avoid arbitrary query execution | Filter grammar and index policy. |
| Sorting | Allow only declared sortable fields | Default ordering and tie-breakers. |
| Version reads | Allow exact immutable version retrieval | Retention and historical access policy. |
| Errors | Return structured error envelope | Exact code catalogue. |

Queries MUST NOT mutate canonical state or imply permission to execute a protected action. A projection may be eventually consistent only where the API clearly documents its consistency behavior.

## 7. Common event envelope

| Field | Purpose | Requirement |
| --- | --- | --- |
| event_id | Unique event identity | Required; stable across redelivery. |
| event_type | Selects event semantics | Required; versioned catalogue. |
| event_schema_version | Schema version | Required. |
| entity_id / entity_type | Changed canonical entity | Required. |
| domain | Owning domain | Required. |
| state_machine_name / version | State machine identity | Required for state transition events. |
| state_version | Committed state version | Required for state transition events. |
| prior_state / new_state | Committed transition | Required for state transition events. |
| occurred_at / recorded_at | Occurrence and record times | UTC; exact precision open. |
| actor_ref / actor_type | Attribution | Required design element. |
| reason | Transition reason | Where relevant; mandatory matrix open. |
| correlation_id / causation_id | Trace chain | Required design elements. |
| policy_version | Policy context | Where relevant. |
| evidence_refs / result_refs | Supporting evidence/results | Where relevant. |
| payload | Event-specific fact | Validated against event schema. |

## 7.1 Illustrative event JSON

{
  "event_id": "0195f4c0-0000-7000-8000-000000000006",
  "event_type": "content.review_submitted",
  "event_schema_version": "1.0",
  "entity_type": "ContentVersion",
  "entity_id": "0195f4c0-0000-7000-8000-000000000002",
  "domain": "content_graph",
  "state_machine_name": "content_editorial",
  "state_machine_version": "candidate-1",
  "state_version": 5,
  "prior_state": "DRAFT",
  "new_state": "READY_FOR_REVIEW",
  "occurred_at": "2026-11-01T10:00:02Z",
  "recorded_at": "2026-11-01T10:00:02Z",
  "actor_type": "human",
  "actor_ref": "authenticated-actor-reference",
  "correlation_id": "0195f4c0-0000-7000-8000-000000000004",
  "causation_id": "0195f4c0-0000-7000-8000-000000000001",
  "payload": {"review_profile_ref": "example-review-profile"}
}

Example event names, state values and versions are illustrative. The event may only be published after the source transition commits. Consumers must not treat this event as an approval or authorization.

## 8. Event catalogue — candidate families

| Domain | Event family examples | Producer / owner | Consumer purpose |
| --- | --- | --- | --- |
| Content Graph | content.created; content.version_created; content.review_submitted; content.archived | Content Graph | Creation, review orchestration, analytics. |
| Knowledge / Research | knowledge.source_registered; research.completed | Owning domain | Provenance and content research workflows. |
| Brand Intelligence | brand.profile_versioned | Brand Intelligence | Creation and QA policy context. |
| Strategy & Planning | plan.approved; calendar_item_scheduled | Strategy & Planning | Workflow trigger and planning views. |
| Quality | quality.evaluation_completed; quality.blocked | Content Quality Intelligence | Governance gates and reporting. |
| Creation Engine | creation.requested; creation.completed; creation.failed | Creation boundary / orchestrator | Worker dispatch and artifact ingestion. |
| Asset Management | artifact.registered; artifact.validated; artifact.quarantined; artifact.superseded | Asset Management | Eligibility, lineage and distribution. |
| Orchestration | workflow.started; job.queued; job.attempt_started; job.completed; worker.revoked | Automation & Agent Orchestration | Execution projections and recovery. |
| Governance | rights.determined; approval.recorded; authorization.revoked | Governance / central authorization | Protected-action policy evaluation. |
| Distribution | distribution.prepared; distribution.submitted; distribution.confirmed; distribution.unknown_outcome | Distribution Studio | External outcome tracking. |
| Analytics | metric.recorded; learning.insight_created | Analytics & Learning | Reporting/learning projections. |

This is a candidate event-family inventory, not a frozen exact event-name catalogue. Final names must be reconciled against the canonical module-to-contract traceability matrix and state-machine registry.

## 9. Command catalogue — candidate operation families

| Domain | Command family examples | Owner | Critical guard |
| --- | --- | --- | --- |
| Content Graph | content.create; content.create_variant; content.create_version; content.submit_for_review; content.archive | Content Graph | Owner scope; immutable version; expected state version. |
| Research / Knowledge | source.register; research.run; knowledge.capture | Owning domain | Provenance, source access and scope. |
| Brand Intelligence | brand.profile.update; brand.profile.activate_version | Brand Intelligence | New immutable config version; authorized owner. |
| Strategy | plan.create; plan.approve; calendar.schedule | Strategy & Planning | Role and planning policy. |
| Quality | quality.evaluate; quality.request_human_review | Quality domain | Exact content/artifact version and policy. |
| Creation | creation.request; creation.cancel | Creation boundary | Bounded inputs, capability and output contract. |
| Assets | artifact.register; artifact.validate; artifact.quarantine; artifact.release | Asset Management | Integrity, version and authorized disposition. |
| Orchestration | workflow.start; workflow.cancel; job.retry; worker.suspend; worker.revoke | Automation | Durable idempotency, owner authority and safe cancellation. |
| Governance | rights.determine; approval.record; approval.revoke; authorization.evaluate | Governance / central authorization | Evidence, exact-version and policy binding. |
| Distribution | distribution.prepare; distribution.authorize; distribution.submit; distribution.reconcile | Distribution / central authorization | Central allow and execution-time recheck. |

Command names above are conceptual. They must not be treated as API routes or an approved public command catalogue.

## 10. Error contract

Errors must be machine-readable, stable, safe to expose and useful for retry classification. Do not leak credentials, secrets or sensitive payloads in error responses.

| Error class | Meaning | Retry guidance |
| --- | --- | --- |
| VALIDATION | Malformed or schema-invalid input | Do not retry unchanged request. |
| AUTHENTICATION | Caller identity cannot be established | Refresh/re-authenticate under security policy. |
| AUTHORIZATION | Actor/action/resource not permitted | Do not retry without changed authority/context. |
| POLICY_BLOCKED | Rights, QA, approval, pause or policy guard failed | Resolve blocker and submit a new deliberate command. |
| NOT_FOUND | Target or reference unavailable in caller scope | Verify ID/scope; avoid leaking existence across scope. |
| CONFLICT | Expected state/version stale | Refresh canonical state; construct new command. |
| RATE_LIMITED | Caller exceeds declared rate policy | Retry only under returned policy guidance; exact headers open. |
| DEPENDENCY_TRANSIENT | Temporary dependency failure | Retry only if idempotent and within policy. |
| DEPENDENCY_PERMANENT | Dependency rejects or cannot process request | Escalate or correct configuration. |
| INTEGRITY_FAILURE | Checksum, signature, manifest or data integrity failed | Quarantine; do not proceed. |
| TIMEOUT_UNKNOWN | Operation may have occurred but response absent | Reconcile before retrying side effect. |
| INTERNAL | Unexpected service failure | Use correlation ID; safe retry policy depends on operation. |

## 10.1 Illustrative error envelope

{
  "error": {
    "code": "CONFLICT",
    "message": "The target changed after the client read it.",
    "retryable": false,
    "correlation_id": "0195f4c0-0000-7000-8000-000000000004",
    "details": {
      "expected_state_version": 4,
      "current_state_version": 5
    }
  }
}

Exact error codes, HTTP mapping, details schema and disclosure policy remain OPEN. Do not expose internal stack traces, tokens, secret values or cross-workspace existence.

## 11. Idempotency and duplicate command handling

- State-changing commands that may be retried must carry an idempotency key.

- The server stores the key with a defined scope and semantic request fingerprint.

- Same key + same semantic request returns the original durable outcome/reference or a defined equivalent response.

- Same key + different semantic request returns a conflict/rejection; it must not silently reuse the prior result.

- Idempotency record and protected effect must be transactionally coordinated or otherwise recoverably linked.

- Key scope, retention, collision handling and expiry behavior are OPEN and must be specified per command family.

- Idempotency prevents duplicate command effects; it does not prove external platform success.

## 11.1 Duplicate delivery matrix

| Scenario | Required behavior |
| --- | --- |
| Same command redelivered before processing | Single logical operation; duplicate recognized. |
| Same command redelivered after ACCEPTED | Return/resolve same durable operation reference. |
| Same key, changed payload | Reject/conflict; no ambiguous execution. |
| Same event redelivered | Consumer inbox/dedup prevents duplicate effect. |
| External request timeout | Reconcile remote state; idempotency key alone may not guarantee provider deduplication. |

## 12. Outbox, inbox and delivery contract

| Component | Required behavior | Open details |
| --- | --- | --- |
| Outbox producer | Commit source state transition and outbox record atomically. | Outbox schema, claim strategy and retention. |
| Publisher | Deliver pending events; retry transient delivery safely. | Backoff, batch size, ordering and dead-letter threshold. |
| Consumer inbox | Persist event receipt/dedup identity and process idempotently. | Inbox schema, transaction boundary and retention. |
| Ordering | Use state_version/sequence to detect stale or missing events. | Partitioning and gap-recovery strategy. |
| Dead-letter | Make poison messages visible and recoverable. | Threshold, operator permissions and replay procedure. |
| Replay | Rebuild projections safely without repeating external side effects. | Replay scope, side-effect suppression and authorization. |

ADR-003 selects a DB-backed durable queue with transactional outbox/inbox initially. The delivery model must tolerate at-least-once delivery. Do not claim exactly-once processing without an explicit mechanism and evidence.

## 13. Versioning and compatibility policy

| Change type | Compatibility treatment | Required process |
| --- | --- | --- |
| Add optional response field | Usually backward-compatible if clients ignore unknown fields | Versioned schema; compatibility test. |
| Add required request field | Breaking for existing clients | New major contract version or explicit negotiated migration. |
| Remove/rename field | Breaking | Deprecation window and migration plan. |
| Change field meaning/unit | Breaking semantic change | New version; never silently reinterpret. |
| Add enum value | Potentially breaking for exhaustive consumers | Consumer compatibility check; documented unknown-value behavior. |
| Remove enum value | Breaking | Versioned migration and historical read strategy. |
| Change event payload requiredness | Potentially breaking | Schema version and consumer rollout plan. |
| Change event meaning | Breaking even if JSON shape unchanged | New event semantic version/type or major version. |
| Change state transition semantics | Breaking contract behavior | New state-machine version and migration/reconciliation plan. |

- Every command and event has an explicit schema version.

- Consumers must declare supported versions and fail safely on unsupported versions.

- Unknown enum values must not be mapped to a permissive state.

- Event consumers should tolerate additive optional fields but must validate required semantics.

- Producer rollout must not publish a new required schema until consumers can safely handle it.

- Historical events remain interpretable under the schema version with which they were produced.

## 14. Security and trust boundaries

- Authenticate every API caller and derive actor identity from authenticated context.

- Authorize every command/query against workspace, brand, entity and action scope.

- Never place long-lived credentials or access tokens in command/event payloads.

- Minimize sensitive information in events; prefer scoped references over copied personal data.

- Treat webhook payloads as untrusted until signature/authentication and replay checks pass.

- Worker assignment must be scoped to worker identity, job/attempt, capability, inputs and expiry.

- Central authorization is required for protected distribution actions; adapter-local booleans cannot bypass it.

- Log identifiers and decisions needed for audit without logging secrets or unnecessary sensitive content.

## 15. Protected publish command contract

The API/Event standard specifically requires publish commands to bind exact artifact/version, package/version, destination, authorization, policy version and emergency pause. A generic approved=true is not sufficient.

| Binding | Required meaning |
| --- | --- |
| action | Exact operation being requested. |
| content/version | Exact editorial subject and immutable version where relevant. |
| artifact/version | Exact binary/manifest version to distribute. |
| package/version | Exact package composition and version. |
| destination | Exact platform/account/channel destination. |
| approval_ref | Current approval bound to exact version and scope. |
| rights_ref | Evidence-backed rights decision for intended use/destination. |
| quality_ref | Exact-version QA outcome and policy context. |
| authorization_ref | Central decision bound to this action and all relevant resources. |
| policy_version | Policy version used to evaluate the operation. |
| emergency_pause_state | Current pause state rechecked immediately before execution. |
| correlation_id | End-to-end operation trace. |

Illustrative conceptual request (not a frozen endpoint):
{
  "command_type": "distribution.submit",
  "payload": {
    "action": "publish",
    "content_version_ref": "content-version-id",
    "artifact_version_ref": "artifact-version-id",
    "package_version_ref": "package-version-id",
    "destination_ref": "destination-id",
    "approval_ref": "approval-decision-id",
    "rights_ref": "rights-decision-id",
    "quality_evaluation_ref": "quality-result-id",
    "authorization_ref": "central-authorization-id",
    "policy_version": "policy-version",
    "correlation_id": "correlation-id"
  }
}

At execution time the adapter rechecks authorization validity, revocation, emergency pause, exact version and destination. If the external response is uncertain, create/retain UNKNOWN_OUTCOME and reconcile before retry. Automatic public publishing remains disabled until separately approved.

## 16. Webhook and external callback contract

| Control | Requirement |
| --- | --- |
| Authentication | Verify sender identity using the approved provider mechanism; protocol open. |
| Signature | Validate signature and key rotation where supported. |
| Replay protection | Check timestamp/nonce/event identity and deduplicate. |
| Schema | Validate callback schema/version; unsupported versions quarantined or rejected. |
| Correlation | Map provider event to local operation_id and correlation_id. |
| Trust | Treat callback as evidence to reconcile, not unquestionable truth. |
| State transition | Only Distribution Studio commits external-operation state after verification. |
| Failure | Persist receipt and processing error safely; avoid dropping callback silently. |

No provider-specific webhook signature algorithm or endpoint is selected in this pack.

## 17. API domain ownership and interface boundaries

| Domain | Owns commands/events for | Cross-domain contract rule |
| --- | --- | --- |
| Workspace & Control Center | Workspace scope/configuration and owner controls | Provides scope/policy references; not owner of other domain lifecycle. |
| Content Graph | ContentItem/Variant/Version | Creation, review, quality and distribution reference exact versions. |
| Knowledge Management | Knowledge sources and provenance | Exposes references; does not authorize use. |
| Research Intelligence | Research records and evidence | Emits completed research facts; source domain retains provenance. |
| Brand Intelligence | Brand profile/config versions | Creation and QA consume exact profile version. |
| Strategy & Planning | Plans, calendars, objectives | Triggers workflow via command; does not own job state. |
| Content Quality Intelligence | Quality evaluations and outcomes | Publishes policy-bound findings; not approval/authorization. |
| Multiformat Creation Engine | Creation requests/results and adapter interface | Returns artifact refs; does not own canonical content or distribution. |
| Asset Management | Artifact versions, manifests, transfers, validation | Controls artifact eligibility and integrity. |
| Automation & Agent Orchestration | Workflow/task/job/attempt/worker state | Dispatches bounded work; cannot decide rights/approval. |
| Distribution Studio | Packages and external operations | Requires central authorization; owns remote outcome record. |
| Analytics & Learning | Metrics and learning records | Consumes events/projections; no retroactive source writes. |

## 18. Observability and audit correlation

- Propagate correlation_id across inbound request, command, workflow run, task, job, attempt, worker assignment, artifact, event and external operation.

- Preserve causation_id to show the immediate triggering command/event.

- Record command outcome separately from job outcome and external operation outcome.

- Audit privileged state changes, approval/rights/authorization decisions, worker credential lifecycle and distribution attempts.

- Use UTC timestamps and explicit schema versions.

- Logs must not be treated as the sole source of canonical state; authoritative records and events remain primary.

- Exact audit retention, tamper-evidence and access rules remain OPEN.

## 19. Interface acceptance scenarios

| Test | Scenario | Expected result |
| --- | --- | --- |
| API-01 | Command missing required schema version | Validation rejection; no side effect. |
| API-02 | Authenticated actor lacks workspace scope | Authorization rejection without leaking cross-scope data. |
| API-03 | Stale expected_state_version | CONFLICT; canonical state unchanged. |
| API-04 | Same idempotency key and same payload | Same logical operation; no duplicate effect. |
| API-05 | Same idempotency key with changed payload | Conflict/rejection. |
| API-06 | Asynchronous command accepted | Durable operation reference returned. |
| API-07 | Event published before source transaction commits | Impossible by outbox/transaction design. |
| API-08 | Event redelivered | Consumer deduplicates. |
| API-09 | Unsupported event schema | Controlled reject/quarantine; no permissive parse. |
| API-10 | Unknown enum value received | Safe handling; never map to allow/cleared/approved. |
| API-11 | Required request field removed in new version | Compatibility gate blocks breaking rollout. |
| API-12 | Webhook replayed | Replay detection/dedup prevents duplicate transition. |
| API-13 | Publish request uses wrong artifact version | Reject; exact binding mismatch. |
| API-14 | Approval exists but central authorization absent | Protected action denied. |
| API-15 | Authorization expires after queueing | Execution-time check denies. |
| API-16 | Publish times out after possible remote success | UNKNOWN_OUTCOME; reconciliation before retry. |
| API-17 | Sensitive secret appears in error/log payload | Security test fails; redact and prevent leakage. |
| API-18 | Consumer attempts cross-domain canonical write | Reject; owner command boundary enforced. |

Evidence per test: contract/schema version, fixture, command/event IDs, actor, correlation ID, expected/actual response and state, timestamps, logs, reviewer and reproducible test command.

## 20. Open interface decisions

| ID | Open item | Closure evidence |
| --- | --- | --- |
| API-OPEN-01 | Exact route/path catalogue | Owner-approved OpenAPI specification. |
| API-OPEN-02 | Exact JSON Schema field types, nullability, lengths and formats | Versioned schema bundle. |
| API-OPEN-03 | HTTP status mapping and response headers | API behavior matrix and contract tests. |
| API-OPEN-04 | Query pagination/filter/sort semantics | Query contract and performance assumptions. |
| API-OPEN-05 | Command/event naming catalogue | Traceable owner-approved catalogue. |
| API-OPEN-06 | Idempotency key scope, TTL and changed-payload behavior | Command family policy and duplicate tests. |
| API-OPEN-07 | Outbox/inbox schema, ordering and dead-letter thresholds | Transaction design and failure tests. |
| API-OPEN-08 | Event schema compatibility and consumer rollout rules | Version policy and compatibility suite. |
| API-OPEN-09 | Error code catalogue and retry classification | Canonical error registry. |
| API-OPEN-10 | Authentication and service-to-service credential protocol | Security architecture and threat model. |
| API-OPEN-11 | Webhook signature and replay protocol | Provider-neutral callback standard plus later provider profile. |
| API-OPEN-12 | Rate limits, payload size limits and timeout values | Measured workload assumptions and owner approval. |
| API-OPEN-13 | Audit retention and sensitive-data policy | Security/privacy policy. |
| API-OPEN-14 | Publish request final schema and emergency pause semantics | Owner-approved distribution/authorization contract. |
| API-OPEN-15 | Exact Contract 01–12 mapping and schema ownership | Traceability matrix reconciled verbatim. |

## 21. Freeze readiness

| Gate | Required evidence | Status |
| --- | --- | --- |
| Envelope | Command/event envelope field-level schema | Candidate included; exact schema open. |
| Command semantics | Outcome and idempotency behavior | Core semantics included; HTTP mapping open. |
| Query semantics | Scope, consistency and pagination | Requirements included; detailed schema open. |
| Event semantics | Committed fact, ordering and dedup | Principles included; exact catalogue open. |
| Compatibility | Schema versions and breaking-change policy | Candidate policy included; owner freeze pending. |
| Security | Authentication, authorization, secret handling | Principles included; protocols open. |
| Publish boundary | Exact version/destination/authorization binding | Requirements included; final payload open. |
| Testability | Contract, failure and compatibility scenarios | 18 scenarios included; execution evidence pending. |
| Formal owner freeze | Explicit approval of exact pack version | NOT FROZEN. |
| Implementation authorization | Separate scope and allowed operations | NOT GRANTED. |

## 22. Implementation handoff

This document does not authorize repository edits, API route implementation, migrations, test execution against the project, agent execution, deployment, paid services, production generation, upload or publishing.

- WP-1: translate canonical data dictionary into versioned entity schemas and ownership constraints.

- WP-2: implement command envelope, durable operation references, outbox/inbox and idempotency only after schema freeze.

- WP-3: define authenticated worker identity and scoped assignment/result contracts.

- WP-4: implement artifact/manifest/transfer/validation event and command schemas.

- WP-5: implement quality, rights, approval and central authorization decision contracts.

- WP-6: run schema compatibility, duplicate delivery, stale version, replay and unknown-outcome tests.

## Appendix A — Source basis and authority

Source basis: NEXTDECODE API & Event Contract Standard 1.0; Canonical Data Dictionary & Entity Ownership Registry 1.0; Unified Lifecycle & State Transition Standard 1.0; Module-to-Contract Traceability Matrix 1.0; Artifact 08 accepted ADR/CF decisions and reconciliation; Batch 15 Source Reconciliation & Contract Closure Dossier; Batch 16 Domain & Interface Contract Closure Pack; Batch 17 State-Machine & Transition Catalogue.

The API/Event standard is documentation-only and does not authorize repository/code/provider/spend/upload/publishing activity. Example paths and payloads remain illustrative. The detailed contract freeze and implementation authorization are still pending.

## Appendix B — Glossary

| Term | Definition |
| --- | --- |
| Command | Request to perform a state-changing action. |
| Query | Read request that does not mutate canonical state. |
| Event | Durable record of a committed fact. |
| Envelope | Common metadata structure around command/event payload. |
| Idempotency key | Identifier used to prevent duplicate logical command effects. |
| Outbox | Durable event-publication intent committed with source state. |
| Inbox | Consumer receipt/deduplication record. |
| Projection | Read model derived from committed events. |
| Schema version | Version identifying payload structure and semantics. |
| Unknown outcome | Side effect may have occurred but evidence is insufficient. |
| Compatibility | Ability of producer and consumer versions to interoperate safely. |


## Source document metadata (preserved from DOCX)

- **Header:** NEXTDECODE CONTENT OS  |  P0 API & EVENT CONTRACT SERIES
- **Footer:** Detailed interface candidate • Owner freeze pending • Implementation not authorized

