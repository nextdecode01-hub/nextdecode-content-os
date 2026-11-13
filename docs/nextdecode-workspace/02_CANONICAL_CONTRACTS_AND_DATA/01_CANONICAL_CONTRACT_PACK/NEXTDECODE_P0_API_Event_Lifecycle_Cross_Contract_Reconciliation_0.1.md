# NEXTDECODE P0 — API/Event & Unified Lifecycle Cross-Contract Reconciliation
**Document ID:** NEXTDECODE-P0-API-LIFECYCLE-RECON-0.1  
**Version:** 0.1 | **Date:** 2026-11-04  
**Status:** Working conformance reconciliation — documentation only  
**Contract freeze:** NOT GRANTED | **Implementation authorization:** NOT GRANTED

## 1. Purpose and authority
Reconcile the governing API/Event Contract Standard 1.0 with the Unified Lifecycle & State Transition Standard 1.0 and existing API/Event Reconciliation 0.1, incorporating the Contract 07, 10, 11 and 12 ownership work.

Authority order remains: accepted ADR/CF owner decisions; governing API/Event and Lifecycle standards; canonical Data Dictionary (with v1.0/v1.1 relationship still formally open); owner-ratified domain contracts; reconciliation aids. This document does not amend either standard or convert proposals into decisions.

## 2. Confirmed common model
The two standards are substantially aligned on these invariants:
- One authoritative owner per domain state machine; consumers request transitions and do not write another domain's canonical state.
- A command requests an action; a committed event reports a fact; a query reads state.
- Every committed transition is auditable and immutable.
- State-changing commands use expected-version protection; retryable commands use idempotency.
- State update and outbox event commit atomically; delivery is at-least-once and consumers are idempotent.
- No global exactly-once delivery promise.
- External side effects are recorded and reconciled; unknown outcome is neither success nor failure and must not be blindly retried.
- Workflow, business lifecycle, worker trust, artifact, quality, approval, authorization and distribution/publication states remain separate.
- UUIDv7 canonical entity identity is distinct from command/event/request/trace/idempotency identities.

## 3. Envelope conformance map

| Semantic field | Lifecycle Standard 1.0 | API/Event Standard 1.0 / reconciliation | Disposition |
|---|---|---|---|
| Event identity | event_id | event_id | Same semantic field; one canonical definition |
| Entity identity/type | entity_id, entity_type | entity_id/entity_type | Same meaning |
| Owning domain | domain | producer/domain context | Lifecycle field is explicit; define producer mapping, not a second owner |
| State machine identity/version | state_machine | state_machine | Same meaning |
| Aggregate/state version | state_version | state_version | Same ordering authority per entity/state machine |
| Transition states | previous_state, new_state | previous_state/new_state where applicable | Same meaning; nullable previous state only on initial creation per lifecycle standard |
| Time | occurred_at, recorded_at | occurred_at, recorded_at | Same meaning; UTC |
| Actor | actor_ref, actor_type | actor_ref/actor_type | Same meaning; authenticated server context is authoritative |
| Reason | reason_code, reason_summary | reason_code | Lifecycle defines summary; API/Event may carry it as additive field |
| Correlation/causation | correlation_id, causation_id | correlation_id, causation_id | Same semantic meaning; nullability/type constraints open |
| Policy | policy_version | policy_version where relevant | Same meaning; nullable only when no policy applies under lifecycle standard |
| Evidence/results | evidence_refs, result_refs | data payload and references | Preserve explicit references; do not bury required provenance in opaque data |
| Schema version | schema_version | event_version and schema_version appear in source/reconciliation | **Conflict/ambiguity:** determine whether event_version is event semantic revision and schema_version envelope/payload schema, or standardize one canonical version field with compatibility mapping |
| Scope | workspace_id, brand_id, studio_id recommended | workspace_id and relevant scope IDs | Common semantics; exact requiredness by domain open |
| Request/idempotency | recommended request_id/idempotency_key | request_id, idempotency_key | Same concepts; command/event presence depends on origin and operation |
| Transition command | transition_command_id recommended | command_id and command envelope | Define typed relationship; do not alias command_id to causation_id |
| Trace | trace_id/span_id recommended | trace_id | Operational tracing only; never business causation or entity identity |

## 4. Important semantic distinction: state_version and event multiplicity
The Lifecycle Standard says state_version is monotonically increasing for an entity's state machine and transition increments it exactly once. API/Event reconciliation says event ordering is per aggregate/state machine using state_version, but flags multiple events emitted for one aggregate version as open.

Do not assume every event emitted during a transition gets a distinct state_version. A single committed transition may have one authoritative lifecycle event plus other domain/notification events. The catalogue must specify which event is the state-transition fact, how additional events reference that transition, and how consumers deduplicate/order them. Owner/domain decision required before schema freeze.

## 5. Command envelope and commit protocol
Preserve API/Event Standard command fields and lifecycle transition rules:
- command_id, command_type, command_version;
- typed target reference where known;
- authenticated workspace and applicable scope;
- requested_by bound to authenticated principal by server, not trusted as caller assertion;
- requested_at;
- expected_state_version for state-changing commands against an existing versioned aggregate;
- idempotency_key for retryable commands;
- correlation_id and causation_id where applicable;
- policy_context_ref as reference only, never as caller-supplied permission;
- domain payload under versioned schema.

The owning domain authenticates, validates scope/capability, loads authoritative state, validates transition/guards/evidence/policy, checks expected version, commits state + immutable event + outbox atomically, then returns committed version/event reference. Stale versions reject; no silent overwrite.

Command acceptance is not completion. Asynchronous ACCEPTED must reference durable work/status. COMPLETED means the synchronous domain operation committed; it does not imply external publication or any unrelated domain transition.

## 6. Delivery, inbox/outbox and recovery
Accepted baseline and governing standards require:
- transactional outbox with state commit;
- durable queue direction;
- at-least-once delivery;
- idempotent consumers and inbox/deduplication;
- no distributed exactly-once claim;
- bounded retry, poison isolation/dead-letter handling and observable reconciliation;
- consumer state version tracking and owner-authorized reconciliation on version gaps.

Still open: outbox/inbox table shape, lock/claim protocol, retention horizons, redrive authority, poison-message terminal handling, consumer projection rebuild, multiple events per state version, and exact sequence scope. Do not invent numerical retry or retention values.

## 7. Cross-domain application
- **Contract 07:** quality, rights, approval and authorization decisions are owner-domain facts; a decision event is not a reusable permission token. Protected actions re-evaluate current centralized authorization at the side-effect boundary.
- **Contract 10 / WP2:** workflow/task/job/attempt transitions use common envelope but remain distinct from business lifecycle; worker identity/lease remains WP3.
- **Contract 11:** CreationProject/StudioProduction state is creation-domain-owned; workflow completion does not commit its business lifecycle automatically.
- **Contract 12:** package, schedule, PublishOperation and Publication have separate state machines; upload, publish and public visibility are distinct observations; unknown outcome requires reconciliation before retry.
- **WP4:** Artifact and ArtifactVersion remain immutable identity/version boundaries; events reference exact versions/hashes.
- **WP6:** acceptance must test duplicate/out-of-order events, version gaps, stale commands, replay, poison messages, revoked authorization and uncertain external outcomes.

## 8. Open decision register

| ID | Issue | Required action |
|---|---|---|
| API-LC-01 | event_version vs schema_version | Decide semantic distinction or canonical mapping; update event catalogue |
| API-LC-02 | Multiple events per state_version | Define authoritative transition event vs secondary events and consumer ordering |
| API-LC-03 | correlation_id/causation_id nullability and typed reference | Define permitted root-origin cases and typed identifier form |
| API-LC-04 | state_version scope | Confirm per entity + state machine and how concurrent independent state machines are versioned |
| API-LC-05 | request_id/trace_id propagation | Define required API metadata and event propagation without conflating identities |
| API-LC-06 | Outbox/inbox retention and redrive | WP2/WP6 propose safe retention/redrive; owner/security review |
| API-LC-07 | Poison message and replay controls | Define quarantine, redrive permission, audit and duplicate-effect prevention |
| API-LC-08 | Schema compatibility policy | Define additive/optional/required field rules, deprecation windows and unknown-version behavior |
| API-LC-09 | Webhook authentication/replay protection | API/Event owner and security define signature, timestamp/nonce/replay semantics |
| API-LC-10 | External side-effect outcome envelope | Align Contract 12 PublishOperation with WP2 JobAttempt and provider correlation without conflating state |

## 9. Closure criteria
- One normative common event envelope is published or a precise field-by-field composition mapping is approved.
- Every event field has one meaning, owner and nullability rule.
- State-transition events and non-transition events are distinguishable.
- State version and event multiplicity rules are deterministic.
- Command expected-version/idempotency and transactional outbox rules are conformance-testable.
- Consumer deduplication, ordering, gap reconciliation, poison isolation and replay controls are specified.
- Contract 07/10/11/12 examples conform without merging their state machines.
- Compatibility and webhook security rules are defined.
- WP6 acceptance cases exist before implementation authorization.

## 10. Disposition
**API/Event + Lifecycle: PARTIALLY ALIGNED; detailed envelope freeze remains OPEN.** The semantic model is consistent, but API-LC-01 through API-LC-10 require explicit resolution. Existing API/Event Reconciliation 0.1 remains a supporting candidate and is not replaced. No schema freeze, implementation authorization, repository change, test execution or agent assignment is granted.
