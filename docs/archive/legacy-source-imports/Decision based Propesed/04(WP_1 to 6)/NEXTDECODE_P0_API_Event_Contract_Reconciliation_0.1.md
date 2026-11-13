# NEXTDECODE P0 — API & Event Contract Reconciliation
**Document ID:** `NEXTDECODE_P0_API_Event_Contract_Reconciliation_0.1`  
**Version:** 0.1  
**Date:** 1 November 2026  
**Status:** DESIGN CANDIDATE — SOURCE CONFORMANCE RECONCILIATION  
**Finding addressed:** X-08 — Command/event envelope and compatibility rules  
**Scope:** WP-1 through WP-6 cross-domain API, command, event, delivery and compatibility boundaries

**Detailed contract freeze:** NOT GRANTED  
**Implementation authorization:** NOT GRANTED  
**Repository inspection/modification, tests, agent execution, provider selection, deployment, spending and external side effects:** NOT AUTHORIZED

---

## 1. Purpose and disposition

This document reconciles the P0 Consolidated Contract Appendix with the governing `NEXTDECODE_API_Event_Contract_Standard_1.0` and the cross-document review finding X-08.

The governing API/Event Contract Standard remains authoritative. This document does not replace it, silently amend it, or convert recommendations into accepted owner decisions. The consolidated appendix is illustrative wherever it is less complete than the governing standard.

**Disposition:** X-08 is substantially clarified at the logical-contract level by this field-by-field conformance map. Several implementation-level details remain open and must be specified before detailed contract freeze.

## 2. Authority and status vocabulary

Use these labels throughout:

- **ACCEPTED BASELINE** — accepted ADR/CF decision carried forward.
- **SOURCE-DEFINED** — normative requirement already stated in a governing source.
- **PROPOSED** — conservative candidate detail for owner review; not frozen.
- **OPEN** — requires further specification or an owner/security decision.
- **DEFERRED** — intentionally postponed where a stable abstraction preserves safety.
- **NOT VERIFIED** — no implementation or test evidence is asserted.

### Source precedence

1. Accepted ADR-001–ADR-010 and CF-01–CF-24 owner decision record.
2. Governing API/Event Contract Standard 1.0, Unified Lifecycle & State Transition Standard 1.0, and Canonical Data Dictionary & Entity Ownership Registry 1.0.
3. WP-1 through WP-6 package contracts, within their defined ownership.
4. P0 Consolidated Contract Appendix, as a derivative cross-package index.
5. This reconciliation, as a conformance aid—not a replacement authority.

If a P0 draft conflicts with a governing source, preserve the governing source and record the discrepancy; do not silently harmonize it by inventing a new rule.

## 3. Core communication boundaries

The three patterns remain distinct:

| Pattern | Meaning | Must not be confused with |
|---|---|---|
| Query API | Reads an authorized current representation | A state-changing command |
| Command API | Requests an action or transition from the owning domain | Proof that the action completed |
| Event | Announces a committed fact | An instruction, permission or approval |

Rules:
- A query is read-only.
- A command expresses intent and is validated/authorized by the domain that owns the transition.
- An event is emitted only for a fact committed by its authoritative owner.
- Consumers do not write directly into another domain's authoritative tables.
- An event never grants permission to perform a protected action.
- An HTTP acceptance response does not replace durable event notification when downstream consumers require reliable notification.

## 4. Command envelope conformance

### 4.1 Governing command fields

The API/Event Standard defines the following command envelope fields as **SHOULD** fields. State-changing commands also require expected-version protection, and retryable commands require idempotency.

| Field | Source meaning | Reconciliation disposition |
|---|---|---|
| `command_id` | Unique command identifier | SOURCE-DEFINED |
| `command_type` | Stable command name | SOURCE-DEFINED |
| `command_version` | Command schema version | SOURCE-DEFINED |
| `target_type` / `target_id` | Target entity, if already known | SOURCE-DEFINED |
| `workspace_id` and relevant scope IDs | Authorized scope | SOURCE-DEFINED |
| `requested_by` | Actor reference supplied as context | Server must derive identity from authenticated context; caller value is not proof |
| `requested_at` | UTC request time | SOURCE-DEFINED |
| `expected_state_version` | Conditional transition guard | Required for state-changing commands |
| `idempotency_key` | Retry identity | Required for retryable commands |
| `correlation_id` | End-to-end business operation | SOURCE-DEFINED |
| `causation_id` | Prior event/command that led to request | SOURCE-DEFINED |
| `policy_context_ref` | Policy context reference, not a permission assertion | SOURCE-DEFINED |
| `payload` | Domain-specific command data | SOURCE-DEFINED |

**Security rule:** The server derives the authenticated actor and effective permissions. It MUST NOT trust caller-supplied `requested_by` as proof of identity. Delegation context must be verifiable and cannot exceed the delegator's authority.

### 4.2 Proposed canonical command handling rules

The following are conservative contract clarifications; exact schema constraints remain **PROPOSED** until owner review:

1. `command_id` identifies one submitted command envelope; it is not the idempotency key, entity ID, correlation ID or causation ID.
2. `command_type` identifies the semantic operation; `command_version` versions its input contract.
3. A target reference is typed and canonical. A command that creates a new entity may omit the target entity ID but must identify its creation scope.
4. `workspace_id` and any applicable brand/studio/resource scope are explicit and validated against authenticated authority.
5. `requested_by` is informational/audit context only after the server has bound it to the authenticated principal.
6. `expected_state_version` is mandatory for state-changing commands that target an existing versioned aggregate. Creation commands use a documented creation/idempotency rule instead.
7. `policy_context_ref` is a reference only. The owner service must evaluate current central authorization; a caller cannot supply an `ALLOW` decision as a substitute.
8. Payloads contain only fields required by the command schema. Unknown required schema versions are rejected safely; unknown optional fields follow the compatibility policy.
9. Command validation, authorization and state-transition validation occur at the owning domain boundary.

### 4.3 Command outcomes

The governing minimum outcome distinctions are:

- `ACCEPTED` — passed initial validation and durably accepted; later work may still be pending.
- `COMPLETED` — synchronous operation committed successfully.
- `REJECTED` — not accepted.
- `CONFLICT` — stale state/version or equivalent conflict; caller must reload/reconcile.

For asynchronous commands, `ACCEPTED` includes a durable job/workflow/resource reference and a status-retrieval path. It does not promise successful completion.

**Proposed rejection response:** use the standard error envelope with a stable machine-readable `error.code`, safe human-readable message, `retryable` classification, optional non-sensitive `details`, and request metadata. Do not create a second competing rejection envelope.

## 5. Event envelope conformance

### 5.1 Governing minimum event envelope

Every event must comply with the common envelope in the Unified Lifecycle & State Transition Standard. The API/Event Standard lists these minimum fields:

| Field | Meaning | Disposition |
|---|---|---|
| `event_id` | Unique immutable event identity | SOURCE-DEFINED |
| `event_type` | Stable committed-fact name | SOURCE-DEFINED |
| `event_version` | Event contract version | SOURCE-DEFINED |
| `occurred_at` | Time the fact occurred | SOURCE-DEFINED |
| `recorded_at` | Time it was recorded | SOURCE-DEFINED |
| `producer` | Producing domain/service identity | SOURCE-DEFINED |
| `entity_type` / `entity_id` | Affected canonical entity | SOURCE-DEFINED |
| `workspace_id` and applicable scope | Scope context | SOURCE-DEFINED |
| `state_machine` | Relevant state machine | SOURCE-DEFINED |
| `state_version` | Aggregate/state-machine version | SOURCE-DEFINED |
| `previous_state` / `new_state` | State transition values, where applicable | SOURCE-DEFINED |
| `actor_ref` / `actor_type` | Actor context | SOURCE-DEFINED |
| `reason_code` | Normalized reason | SOURCE-DEFINED |
| `correlation_id` | End-to-end operation | SOURCE-DEFINED |
| `causation_id` | Immediate causal command/event reference | SOURCE-DEFINED |
| `policy_version` | Applicable policy version, where relevant | SOURCE-DEFINED |
| `data` | Minimal event payload | SOURCE-DEFINED |
| `schema_version` | Payload schema version | SOURCE-DEFINED |

The event envelope and lifecycle envelope must align. One physical schema or a clearly mapped composition is acceptable, but the same field must not acquire competing meanings.

### 5.2 Event naming and payload

**Source-defined:**
- Recommended event names follow `<domain>.<aggregate>.<past-tense-fact>`.
- Names describe what happened, not what a consumer should do.
- A central catalogue prevents semantic collisions.
- Payloads contain the affected entity identity/version and minimum consumer-required data.
- Larger or sensitive records are referenced, not copied wholesale.
- Events must not contain credentials, access tokens, secrets, unnecessary personal data, unrestricted raw research content, unredacted provider payloads, private prompts or internal reasoning traces.

**Proposed additional validation:** event catalogue entries should declare owner, event type, schema version, data classification, state machine, known consumers, replay policy and conformance tests. This extends catalogue completeness but does not create a new event authority.

## 6. Identity, correlation and causation

### 6.1 Distinct identifiers

Do not reuse one identifier for different meanings:

| Identifier | Identifies |
|---|---|
| Canonical entity ID | The domain entity |
| Entity/content/artifact version | An immutable or versioned representation |
| `command_id` | One command submission |
| `event_id` | One committed event |
| `idempotency_key` | A retry-equivalence scope for a command |
| `correlation_id` | An end-to-end business operation |
| `causation_id` | The immediate command/event that caused this message |
| `request_id` | One API request/response interaction |
| `trace_id` | Distributed technical trace |
| `job_id` / `attempt_id` | Logical job and one execution attempt |

Canonical entity IDs remain immutable UUIDv7 values under the accepted baseline. They are not substituted for request, command, event, trace or idempotency identifiers.

### 6.2 Correlation and causation constraints

**SOURCE-DEFINED:** requests should carry or receive request ID, correlation ID, trace ID, authenticated identity, workspace scope and API/contract version. Events and asynchronous jobs must preserve correlation across service boundaries.

**PROPOSED:**
- A new user/business operation establishes a correlation root.
- A command/event produced as a direct consequence records the immediate parent in `causation_id`.
- A consumer-created command carries forward the original correlation context and points causation to the event that triggered it.
- `causation_id` must reference a known command/event identity type; do not place arbitrary prose or a trace ID there.
- `request_id` and `trace_id` remain operational observability identifiers and do not replace business causation.
- Missing correlation/causation is permitted only for documented origin cases (for example, an externally initiated root event); it must not be silently fabricated as if a parent existed.

Exact nullability, identifier format constraints, and whether causation is represented as a typed pair or a globally unique reference remain **OPEN** pending the lifecycle standard's exact field definition.

## 7. Event ordering, state versions and delivery

### 7.1 Ordering

**SOURCE-DEFINED:**
- Assume at-least-once delivery.
- Consumers are idempotent.
- Duplicate events are safe.
- Ordering is defined per aggregate/state machine using `state_version`.
- Consumers tolerate delayed and out-of-order delivery.
- A version gap should trigger authorized reconciliation with the owning domain.
- Poison messages are isolated and observable.
- The platform does not promise global exactly-once delivery.

**PROPOSED consumer algorithm:**
1. Authenticate producer/message and validate envelope/schema.
2. Deduplicate by immutable `event_id` within the declared consumer scope.
3. Compare `state_version` with the consumer's last applied version for that aggregate/state machine.
4. If the event is the next applicable version, apply the local projection/effect idempotently.
5. If it is an already-applied or duplicate version, record duplicate/stale disposition without repeating effects.
6. If there is a gap or incompatible ordering, pause the affected aggregate's projection and request authorized reconciliation from the owning domain.
7. Do not infer missing events or invent intermediate state.
8. Preserve the original event and diagnostic evidence for review.

This algorithm is a candidate implementation contract, not an accepted code design. Exact sequence scope, handling of multiple events emitted for one aggregate version, and projection rebuild strategy remain open.

### 7.2 Transactional outbox/inbox

**ACCEPTED BASELINE:** database-backed durable queue with transactional outbox/inbox direction; at-least-once delivery; no exactly-once claim.

**SOURCE-DEFINED:**
- Producer state transition and outbox event are persisted atomically.
- Consumer inbox/dedup record and local side effect should be atomic when they share a transaction boundary.
- Cross-service effects require idempotent commands or explicit reconciliation.
- Do not assume distributed transactions.

**PROPOSED minimum record semantics:**
- Outbox record points to one immutable event envelope and records publication/delivery attempts separately from the domain event.
- Inbox record stores consumer identity/scope plus event identity and processing disposition.
- Deduplication key is consumer-scoped and based on immutable event identity.
- A failed consumer transaction must not leave a committed inbox marker that falsely claims the side effect completed.
- Delivery retry does not mutate the original event identity or historical event payload.
- A poison event is isolated with reason, attempt history and controlled redrive/reconciliation path.

Exact table names, indexes, retention periods, lock/claim protocol and redrive permissions remain **OPEN**.

## 8. Idempotency, concurrency and retry semantics

### 8.1 Idempotency

**SOURCE-DEFINED:**
- Retryable commands accept an idempotency key.
- Key scope should include caller identity, command type and target resource or intended creation scope.
- Server stores request fingerprint and original outcome.
- Same key + same request returns the original outcome.
- Same key + different request is rejected.
- State-changing commands include `expected_state_version` or equivalent conditional token.
- Stale requests return structured conflict and do not silently overwrite state.

**ACCEPTED BASELINE:** same key/same canonical payload returns the original logical result; same key/different payload conflicts; idempotency keys are not entity IDs or correlation IDs; external effects require provider idempotency or reconciliation.

**OPEN:** exact key retention period, canonicalization algorithm, key length/entropy constraints, uniqueness scope details and behavior after retention expiry.

### 8.2 Retry classification

| Operation | Required handling |
|---|---|
| Read-only query | Bounded retry policy |
| Pure computation | Retry only when inputs/configuration are stable |
| Durable job submission | Retry with same idempotency key |
| Idempotent provider operation | Retry only under documented provider semantics |
| Non-idempotent external operation | Reconcile before retry |
| Unknown external outcome | Record `UNKNOWN_OUTCOME`; reconcile before unsafe retry |

Retrying must not bypass rights, QA, approval, authorization, worker trust or emergency-pause gates. A retry after credential expiry/revocation must reauthorize.

### 8.3 Error taxonomy

Keep independent:
- transport/protocol failure;
- authentication/authorization denial;
- schema/validation rejection;
- state/version conflict;
- business-rule rejection;
- transient dependency failure;
- retry exhaustion/dead-letter;
- timeout with known non-execution;
- timeout with ambiguous external outcome (`UNKNOWN_OUTCOME`);
- internal fault.

The governing source requires stable machine-readable error codes and safe messages. **PROPOSED:** maintain a central error-code catalogue with owner, category, retryability, safe remediation hint and whether reconciliation is required. Numeric retry/backoff/retention values remain deferred.

## 9. Schema versioning and compatibility

### 9.1 Keep version dimensions separate

**SOURCE-DEFINED dimensions:**
- API major version (for example `/v1`);
- resource representation schema version;
- command schema version;
- event schema version;
- state-machine version;
- policy version;
- artifact/content version.

Changing one dimension does not automatically increment all others.

### 9.2 Compatibility matrix

| Change | Governing treatment |
|---|---|
| Add optional response field | Generally compatible |
| Add optional event payload field | Generally compatible |
| Add endpoint or event type | Generally compatible |
| Add optional query filter | Generally compatible |
| Remove/rename field | Potentially breaking |
| Change field type or meaning | Potentially breaking |
| Change requiredness | Potentially breaking |
| Change legal state transitions | Potentially breaking |
| Change authorization semantics | Potentially breaking |
| Change ordering/delivery assumptions | Potentially breaking |
| Change identifier semantics | Potentially breaking |

Breaking changes require a new major or explicitly versioned contract and a migration plan.

### 9.3 Consumer behavior

**SOURCE-DEFINED:**
- Ignore unknown optional fields.
- Reject unsupported required schema versions safely.
- Do not assume undeclared fields are required.
- Handle unknown event types without crashing the whole consumer.
- Record unsupported messages for controlled review.
- Producers should maintain contract tests against known consumers.
- Deprecation includes replacement, date/condition, migration guide, consumer visibility and removal approval/compatibility assessment.

**PROPOSED clarification:**
- Unknown optional fields are ignored only where the schema marks them optional and their presence cannot alter security or state semantics.
- Unknown required fields or unsupported major schema versions fail closed for that message/command, with a stable error/disposition.
- Unknown event types are isolated/observed and do not crash unrelated partitions or consumers.
- A consumer must never treat an unknown event as a command.
- A schema change affecting authorization, state meaning or event ordering is breaking even if JSON shape appears additive.

Exact schema registry format, supported-version window, dual-publish period and deprecation durations remain **OPEN**.

## 10. Replay, retention and poison-message handling

### 10.1 Replay

**SOURCE-DEFINED:**
- Replay may support projection rebuild or consumer recovery.
- Preserve original event identity and timestamps.
- Identify replay mode and replay actor/process.
- Do not re-trigger external side effects by default.
- Use idempotency and replay-safe consumer behavior.
- Revalidate current authorization before any newly requested external action.
- A replayed historical event is not a new approval.

**PROPOSED:** replay is a controlled operational mode, separately authorized and audited. Rebuild-only replay should target projections/read models; side-effecting handlers remain disabled unless a distinct, current, action-specific authorization is obtained.

### 10.2 Retention

The reviewed API/Event Standard does not establish numeric event/outbox/inbox retention periods. Retention, archival, legal hold, deletion and purge must align with the separate data-lifecycle contract and owner-reserved decisions.

**OPEN:** event retention duration, archival format, replay horizon, outbox cleanup, inbox dedup retention and evidence preservation periods.

### 10.3 Poison messages

**SOURCE-DEFINED:** poison messages must be isolated and observable; unsupported messages are recorded for controlled review.

**PROPOSED:** quarantine records should preserve event ID, producer, schema version, consumer, failure category, attempt history, first/last failure time and a safe diagnostic reference. Redrive must be authorized, bounded and idempotent. Do not mutate the original event or repeatedly retry a deterministic schema/security failure.

Exact redrive authority and dead-letter retention remain **OPEN**.

## 11. Security, scope and data minimization

The following remain mandatory:
- Authenticate API callers and event producers.
- Enforce workspace/resource scope at the service boundary.
- Apply field-level authorization and redaction.
- Keep human, agent, service, worker and external integration identities distinct.
- Do not permit agent/worker impersonation or self-granted permissions.
- Reauthorize retries after expiry/revocation.
- Do not expose secrets, private prompts, internal reasoning traces, restricted evidence or unnecessary personal data in events, errors, logs or webhooks.
- External API exposure requires separate approval and security/data-classification review.
- Webhook signatures must be validated and replay detected.
- Protected actions require current centralized, action-specific authorization.

A message being well-formed, signed, delivered by a trusted worker or replayed from a historical event does not itself confer authority.

## 12. Field-level conformance summary

| Contract area | Governing source | Appendix gap | Reconciliation |
|---|---|---|---|
| Query/command/event distinction | API/Event §3 | Needs explicit normative mapping | Preserved and clarified |
| Command envelope | API/Event §5 | Required/optional rules under-specified | Field map added; source SHOULD/MUST levels retained |
| Command outcome | API/Event §5.2 | Rejection details incomplete | Standard error envelope reused |
| Event envelope | API/Event §7.2 + lifecycle standard | Lifecycle alignment not fully mapped | Minimum field map added |
| Correlation/causation | API/Event §§5, 7, 15 | Nullability/constraints unclear | Semantics clarified; exact constraints open |
| Event ordering | API/Event §7.5 | Aggregate version behavior unclear | Per-aggregate/state-machine version model |
| Outbox/inbox | API/Event §7.6; accepted CF | Atomicity/dedup wording compressed | Producer/consumer transaction semantics restored |
| Idempotency | API/Event §10; accepted baseline | Retention/scope details open | Existing accepted behavior preserved |
| Compatibility | API/Event §8 | Unknown fields/versions incomplete | Consumer rules and breaking-change matrix |
| Replay | API/Event §7.7 | Replay controls incomplete | Side-effect suppression and current reauthorization |
| Error handling | API/Event §§4.5, 14–15 | Stable taxonomy/reconciliation not mapped | Proposed taxonomy; numeric policy open |
| Retention/dead letter | API/Event §§7, 17–19 | Exact lifecycle absent | Owner/lifecycle contract remains open |
| Security/redaction | API/Event §§5, 7, 9, 15 | Payload minimization insufficient | Explicit security rules retained |

## 13. WP-6 acceptance oracle proposals

These are proposed test specifications, not executed tests or authorization to run them. All tests must use isolated synthetic non-production fixtures and must not invoke external publishing, upload, spending or provider side effects.

| Test ID | Scenario | Expected oracle |
|---|---|---|
| API-EVT-01 | Query attempts mutation | Rejected or no mutation; authoritative state/version unchanged |
| API-EVT-02 | Command accepted for async work | `ACCEPTED` includes durable job/workflow reference; no completion implied |
| API-EVT-03 | Invalid command schema | Stable machine-readable validation error; no state change/outbox event |
| API-EVT-04 | Same idempotency key, same canonical payload | Original logical result returned; no duplicate logical operation |
| API-EVT-05 | Same idempotency key, changed payload | Conflict/rejection; no second operation |
| API-EVT-06 | Stale expected state version | Structured conflict; no overwrite or event for rejected transition |
| API-EVT-07 | Producer transaction rolls back | No committed state transition and no publishable outbox event |
| API-EVT-08 | Event duplicate delivery | Consumer logical effect occurs once; duplicate disposition observable |
| API-EVT-09 | Event arrives out of order | No unsafe state regression; gap recorded and authorized reconciliation requested |
| API-EVT-10 | Unknown event type | Consumer remains healthy; message safely ignored/quarantined and observable |
| API-EVT-11 | Unsupported required schema version | Safe rejection/quarantine; no guessed interpretation |
| API-EVT-12 | Unknown optional field | Consumer tolerates it without changing declared semantics |
| API-EVT-13 | Breaking schema change without version/migration | Contract compatibility check fails |
| API-EVT-14 | Event replay | Original event ID/timestamps preserved; external side effects not repeated |
| API-EVT-15 | Replay attempts protected action | Denied unless current action-specific authorization independently exists |
| API-EVT-16 | Event payload contains secret fixture | Schema/security test rejects or redacts before publication; secret absent from logs |
| API-EVT-17 | Cross-workspace message/request | Scope check denies; no data leakage or state change |
| API-EVT-18 | Poison message repeatedly fails | Isolated with bounded attempts and retained diagnostic evidence |
| API-EVT-19 | Provider timeout after possible submission | `UNKNOWN_OUTCOME`; no unsafe automatic retry |
| API-EVT-20 | Revoked worker retries command | Reauthorization fails; no protected transition |
| API-EVT-21 | Command rejection | Stable error code, safe message, request ID; no private details |
| API-EVT-22 | Correlation chain across command/job/event | Correlation preserved; causation points to immediate parent as specified |
| API-EVT-23 | Event state-version gap | Owning domain is queried through authorized reconciliation; no invented state |
| API-EVT-24 | Webhook invalid signature/replay | Rejected; no event/command side effect |
| API-EVT-25 | Direct adapter attempts publishing without exact authorization | Central authorization denies; no external request is sent |

**Evidence required per test:** fixture IDs, schema/contract version, request/event IDs, state versions before/after, normalized outcome/error code, outbox/inbox disposition, sanitized logs and reviewer. Evidence retention/cleanup must follow WP-6 environment controls and the data-lifecycle policy; no user data may be used as a fixture.

## 14. Remaining open decisions

| ID | Open item | Why it remains open | Freeze impact |
|---|---|---|---|
| API-OD-01 | Exact command/event schema nullability and requiredness | Needs field-level schema and lifecycle-standard alignment | Blocker |
| API-OD-02 | Exact correlation/causation typed-reference constraints | Source semantics exist; precise schema constraints absent | Blocker |
| API-OD-03 | Event sequence scope, including multiple events per aggregate version | Needed for deterministic consumer ordering | Blocker |
| API-OD-04 | Supported schema-version window and compatibility test policy | Requires explicit producer/consumer support policy | Blocker |
| API-OD-05 | Idempotency retention and canonical request fingerprint algorithm | Numeric/algorithmic details not accepted | Blocker for retryable command freeze |
| API-OD-06 | Event/outbox/inbox/dead-letter retention and replay horizon | Must align with owner-reserved lifecycle decisions | Blocker for retention-dependent contracts |
| API-OD-07 | Poison-message redrive authority and controls | Operational/security authority not specified | Blocker for redrive contract |
| API-OD-08 | Exact error-code catalogue and retry/backoff values | Taxonomy can be designed; numeric policy deferred | Partial; values may be deferred safely |
| API-OD-09 | Replay actor identity and authorization policy | Replay must be auditable; exact role/authority open | Blocker for operational replay |
| API-OD-10 | Lifecycle-standard field-by-field physical mapping | Must ensure no duplicate meanings or incompatible names | Blocker |
| API-OD-11 | Contract catalogue governance and removal approval workflow | Catalogue required; operational owner process not fully defined | Blocker for final catalogue freeze |
| API-OD-12 | Exact external webhook signing/replay protocol | Standard requires safety; provider/protocol choices open | Blocker before external webhook exposure |

Provider, broker, framework, schema registry, deployment topology and infrastructure choices remain deferred. This reconciliation does not select them.

## 15. Required document updates before final freeze

1. Keep the governing API/Event Contract Standard 1.0 authoritative.
2. Update the Consolidated Contract Appendix to reference the canonical command/event fields and compatibility rules rather than abbreviated illustrative envelopes.
3. Add a field-level mapping to the Unified Lifecycle & State Transition Standard so `state_version`, event identity, timestamps, actor and reason fields have one meaning.
4. Align WP-1 and WP-2 command/job submission, idempotency and event publication references with this standard.
5. Ensure WP-3 worker identity and credential revocation rules apply to API/event producers and consumers.
6. Ensure WP-5 central authorization is enforced by command owners and protected-action adapters; events never carry permission.
7. Add the proposed API-EVT test IDs to WP-6's acceptance traceability matrix only after owner review.
8. Keep retention, replay authority, dead-letter redrive and external webhook exposure open until their owners and safeguards are explicit.

## 16. Final assessment

**X-08 logical reconciliation:** SUBSTANTIALLY CLARIFIED.  
**Field-level physical schema:** NOT FROZEN.  
**Lifecycle-envelope mapping:** OPEN.  
**Compatibility and consumer behavior:** SOURCE RULES RESTORED; operational support window OPEN.  
**Replay/retention/dead-letter controls:** PARTIALLY SPECIFIED; owner/lifecycle decisions remain open.  
**WP-6 evidence:** PROPOSED ONLY; NOT EXECUTED.  
**Independent QA:** NOT PERFORMED / NOT ACCEPTED.

This document does not:
- change accepted ADR-001–ADR-010 or CF-01–CF-24;
- grant owner acceptance to proposed details;
- close owner-reserved security or lifecycle decisions;
- authorize repository inspection/modification, tests, Git operations or agents;
- select a provider, broker, framework or schema registry;
- authorize spending, deployment, external account connection, uploads or publishing;
- establish implementation readiness or production readiness.

**Detailed contract freeze: NOT GRANTED.**  
**Implementation authorization: NOT GRANTED.**

---

## Plain-language explanation

We have now aligned the API and event design with the main standard instead of letting the shorter P0 appendix accidentally define a weaker version.

The key distinction is simple: a command asks the system to do something; an event says something has already happened. Commands need validation, authorization and retry protection. Events need immutable identity, ordering rules, deduplication and safe replay. Neither one can grant publishing permission.

The remaining work is mostly precise contract decisions—especially exact field requirements, event sequence rules, version support, replay authority and retention. No code or tests have been run as part of this document.

**NEXTDECODE principle:** a message can be delivered more than once, arrive late, or be replayed; the platform must still preserve one authoritative truth and never turn a historical fact into fresh permission.
