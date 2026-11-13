# NEXTDECODE P0 — API/Event & Lifecycle Owner Decision Matrix

**Document ID:** NEXTDECODE-P0-API-LIFECYCLE-OWNER-MATRIX-0.1  
**Version:** 0.1  
**Date:** 4 November 2026  
**Status:** OWNER DECISION AGENDA — NOT APPROVED  
**Sources:** API/Event Contract Standard 1.0; Unified Lifecycle & State Transition Standard 1.0; API/Event Reconciliation 0.1; API/Event + Lifecycle Cross-Contract Reconciliation 0.1; WP6 oracle reconciliation 0.1  
**Detailed contract freeze:** NOT GRANTED  
**Implementation / test / agent authorization:** NOT GRANTED

## 1. Purpose and authority

This matrix turns API-LC-01..10 from the API/Event + Lifecycle cross-contract reconciliation into explicit owner decision items with candidate dispositions and consequences.

Authority order is unchanged:
1. Accepted ADR/CF owner decisions.
2. Governing API/Event and Unified Lifecycle standards.
3. Canonical Data Dictionary and owner-ratified domain contracts.
4. WP6 and package specifications within their assigned scope.
5. Reconciliation and decision-aid documents.

This matrix does not amend either governing standard, choose an option, approve a schema, define an enum, or authorize implementation. Options are decision aids only. Any accepted disposition must be recorded by the owner and reflected in a versioned canonical contract amendment.

## 2. Decision summary

| Decision ID | Issue | Primary affected areas | Freeze impact |
|---|---|---|---|
| API-LC-01 | event_version vs schema_version | Event envelope, catalogue, compatibility | Blocker |
| API-LC-02 | Multiple events per state_version | Ordering, deduplication, consumer reconciliation | Blocker |
| API-LC-03 | Correlation/causation nullability and typed reference | Command/event envelope, audit trace | Blocker |
| API-LC-04 | state_version scope | Lifecycle, aggregate concurrency, event ordering | Blocker |
| API-LC-05 | request_id/trace_id propagation | API ingress, async jobs, events, observability | Partial/blocker |
| API-LC-06 | Outbox/inbox retention and redrive | Persistence, retry, replay, data lifecycle | Blocker for dependent details |
| API-LC-07 | Poison message and replay controls | Consumer safety, quarantine, redrive authority | Blocker |
| API-LC-08 | Schema compatibility policy | Producer/consumer support, version rollout | Blocker |
| API-LC-09 | Webhook authentication/replay protection | External API boundary, security | Blocker before webhook exposure |
| API-LC-10 | External side-effect outcome envelope | Contract 12 PublishOperation, WP2 JobAttempt, provider correlation | Blocker |

## 3. Owner decision records

### API-LC-01 — event_version versus schema_version

**Source conflict:** API/Event Standard/reconciliation lists both event_version and schema_version; Lifecycle Standard uses schema_version. The cross-contract reconciliation does not assume they are synonyms.

**Question:** Should the contract retain two distinct version dimensions or define one canonical field with a compatibility mapping?

| Option | Meaning | Consequences |
|---|---|---|
| A — Two distinct dimensions | event_version versions the semantic event contract; schema_version versions the serialized payload/envelope shape | Most expressive; requires explicit compatibility matrix and clear rule for when each increments |
| B — One canonical schema version | One version field governs the full event contract; catalogue/versioning rules explain semantic changes | Simpler envelope; risks conflating semantic event evolution with payload representation unless precisely defined |
| C — Defer | Keep both source fields visible but prohibit freeze/implementation assumptions until a field-level owner decision | Avoids premature schema choice; blocks final envelope freeze |

**Owner disposition:** OPEN  
**Approved wording / rationale:** ______________________________________

### API-LC-02 — Multiple events per state_version

**Source ambiguity:** Lifecycle state_version increments once per committed transition. API/Event allows event ordering per aggregate/state machine but does not settle whether multiple events may share one state_version.

**Question:** How should a single state transition that produces multiple event facts be represented and ordered?

| Option | Meaning | Consequences |
|---|---|---|
| A — One authoritative transition event plus secondary events | Exactly one event is the state-transition fact; other events reference its transition/version and have distinct event IDs | Clear state authority; secondary event ordering and relationship still need definition |
| B — Transition-local event sequence | Multiple events may share state_version but carry a transition-local sequence/ordinal | Supports multiple facts; requires new ordering semantics and a canonical sequence scope |
| C — One lifecycle event per transition | Only one event is emitted as the authoritative transition record; other notifications are derived/read-model behavior | Simplifies ordering; may constrain domain event richness and consumer needs |
| D — Defer | Do not freeze event catalogue entries whose multiplicity/ordering is ambiguous | Safest until owner/domain requirements are known; blocks relevant event schema freeze |

**Owner disposition:** OPEN  
**Approved wording / rationale:** ______________________________________

### API-LC-03 — Correlation/causation nullability and typed references

**Source ambiguity:** Both standards define correlation_id and causation_id semantics, but exact nullability, root-origin cases and typed-reference constraints remain open.

**Question:** How must a message identify its correlation root and immediate causal parent?

| Option | Meaning | Consequences |
|---|---|---|
| A — Typed causal reference | causation_id is accompanied by a source type/domain discriminator; root-origin messages may omit it under explicit rules | Strong referential clarity; adds envelope constraints and root-case validation |
| B — Globally unique causal reference | causation_id alone references a globally unique command/event identity | Simpler field shape; requires guaranteed global uniqueness and resolvable identity namespace |
| C — Typed reference object | Causation is a structured reference with kind, ID and optional producer/domain | Explicit and extensible; larger envelope and schema migration considerations |
| D — Defer exact representation | Preserve semantic requirement but leave physical type/nullability open | Avoids invented schema; blocks detailed envelope freeze |

**Owner decision must specify:** root-origin cases; whether correlation_id is mandatory at API ingress; whether causation can point to command or event; how source type is encoded; behavior when parent evidence is unavailable.

**Owner disposition:** OPEN  
**Approved wording / rationale:** ______________________________________

### API-LC-04 — state_version scope

**Source baseline:** Lifecycle reconciliation treats state_version as monotonically increasing for an entity's state machine. Exact handling of entities with multiple independent state machines needs owner/domain confirmation.

**Question:** Is versioning scoped to each entity/state-machine pair, or does one entity-wide version govern all state machines?

| Option | Meaning | Consequences |
|---|---|---|
| A — Per entity + state machine | Each state machine has an independent monotonic version counter | Allows independent lifecycle evolution; every event/command must identify its state machine |
| B — One entity-wide version | All state machines on an entity share one monotonic counter | Easier global entity ordering; unrelated transitions contend and can create false conflicts |
| C — Domain-defined version scope | Each domain contract declares its version scope under a common normative rule | Flexible; requires explicit declaration and conformance checks for every domain |

**Owner disposition:** OPEN  
**Approved wording / rationale:** ______________________________________

### API-LC-05 — request_id and trace_id propagation

**Source baseline:** API requests should carry or receive request ID, correlation ID, trace ID, authenticated identity, workspace scope and API/contract version. Events/jobs preserve correlation across service boundaries. These IDs remain semantically distinct.

**Question:** Which identifiers are mandatory at each boundary and how are they propagated into async work and events?

| Option | Meaning | Consequences |
|---|---|---|
| A — Full propagation | Every ingress creates/validates request_id, correlation_id and trace_id; async work/events preserve correlation and create linked trace/span context | Strong observability; requires precise external-root and trace sampling rules |
| B — Required business correlation, optional technical trace | correlation_id is required or established for business work; request_id is per interaction; trace_id is optional/propagated when tracing is active | Less coupling to tracing infrastructure; some operations may lack full distributed traces |
| C — Boundary-specific requirements | Each API/command/event type declares mandatory fields in a versioned catalogue | Precise per flow; greater catalogue maintenance and risk of inconsistent declarations |

**Guardrail:** request_id, correlation_id, causation_id and trace_id must never be treated as interchangeable.

**Owner disposition:** OPEN  
**Approved wording / rationale:** ______________________________________

### API-LC-06 — Outbox/inbox retention and redrive

**Source baseline:** Transactional outbox/inbox, at-least-once delivery and idempotent consumers are accepted direction. Numeric retention, archival, cleanup, redrive permission and retention horizon remain open and must align with data-lifecycle policy.

**Question:** Who owns retention/redrive policy and what evidence must survive cleanup?

| Option | Meaning | Consequences |
|---|---|---|
| A — Domain-owned retention with central lifecycle constraints | Each event-owning domain proposes retention; common lifecycle policy sets minimum evidence, deletion and legal-hold controls | Domain fit; requires central audit and cross-domain consistency |
| B — Central event-lifecycle policy | One common policy defines retention tiers, archive, purge, dedup horizon and redrive authority | Consistent; may not fit all event classes and needs explicit exceptions |
| C — Defer all numeric values, approve only invariants | Preserve immutability, auditability, legal hold and no premature deletion; defer periods and cleanup jobs | Safe for logical contract; blocks operational retention configuration |

**Required owner details:** outbox/inbox/dedup horizons; archive format; replay horizon; poison/dead-letter retention; deletion/legal-hold authority; redrive authorization; evidence preservation.

**Owner disposition:** OPEN  
**Approved wording / rationale:** ______________________________________

### API-LC-07 — Poison-message isolation and replay controls

**Source baseline:** Poison messages are isolated and observable; replay preserves original identity/timestamps; replay must not repeat external side effects by default; redrive authority remains open.

**Question:** What is the approved quarantine, redrive and replay authority model?

| Option | Meaning | Consequences |
|---|---|---|
| A — Quarantine + separately authorized redrive | Poison messages are quarantined; redrive requires attributable operator/service authorization and bounded idempotent replay | Strong control; requires role/policy and audit design |
| B — Automatic bounded redrive for classified transient failures only | Only explicitly classified transient failures auto-redrive; deterministic schema/security failures remain quarantined | Better recovery; requires stable failure classification and safe retry proof |
| C — Quarantine-only for P0 | No redrive in P0; manual owner review and separate future authorization | Narrow safe slice; limits operational recovery capability |
| D — Defer | Keep replay/redrive out of frozen P0 contract until authority is resolved | Safest if ownership unclear; blocks replay/redrive functionality |

**Guardrails:** replayed historical approval is not a new approval; side-effecting handlers remain disabled unless current action-specific authorization exists; original event identity/payload/timestamps are not mutated.

**Owner disposition:** OPEN  
**Approved wording / rationale:** ______________________________________

### API-LC-08 — Schema compatibility policy

**Source baseline:** Unknown optional fields may be ignored; unsupported required versions must fail safely; unknown event types must not crash consumers; breaking changes require versioning/migration. Supported-version window, registry format, dual-publish and deprecation periods remain open.

**Question:** Which compatibility policy and support window should be normative?

| Option | Meaning | Consequences |
|---|---|---|
| A — Strict major-version compatibility | Consumers accept declared compatible major versions and reject unsupported major versions; additive optional changes are compatible | Predictable; needs support window and schema catalogue |
| B — Explicit producer/consumer compatibility matrix | Each consumer declares accepted schema versions/capabilities; producer rollout checks compatibility | Strong rollout safety; more operational metadata and matrix maintenance |
| C — Hybrid | Common compatibility rules plus per-consumer version matrix for critical event types | Balanced; requires precise catalogue ownership and exception process |

**Owner disposition:** OPEN  
**Approved wording / rationale:** ______________________________________

### API-LC-09 — Webhook authentication and replay protection

**Source baseline:** Webhook signatures must be validated and replay detected. External API exposure requires separate approval/security review. Exact signature, timestamp/nonce, key rotation and replay-store protocol are not specified.

**Question:** Should webhook exposure be included in P0 scope, and if so, what protocol is required?

| Option | Meaning | Consequences |
|---|---|---|
| A — Defer webhook exposure beyond P0-A | No externally reachable webhook receiver in the narrow slice | Lowest scope/risk; webhook protocol remains future contract work |
| B — Include authenticated webhook ingress with signature + freshness + replay controls | Specify signing algorithm, key lifecycle, timestamp/nonce window, replay store, scope and error behavior | Enables integration; increases security and environment obligations |
| C — Internal-only simulated webhook contract | Test envelope/validation with synthetic signed fixtures and no public ingress/provider | Allows contract tests without exposure; must not be represented as production webhook readiness |

**Owner disposition:** OPEN  
**Approved wording / rationale:** ______________________________________

### API-LC-10 — External side-effect outcome envelope

**Source baseline:** Contract 12 PublishOperation and WP2 JobAttempt are distinct state authorities. Upload request/confirmation, publication request/schedule/confirmation and independently observed public visibility are distinct. Unknown external outcome must be reconciled before retry.

**Question:** How should the API/Event envelope link orchestration execution, distribution operation and provider observation without merging their states?

| Option | Meaning | Consequences |
|---|---|---|
| A — Distribution-owned operation references orchestration execution | PublishOperation is authoritative for distribution; it references WorkflowRun/Job/JobAttempt and provider correlation | Clear domain ownership; requires exact typed relationships and idempotency mapping |
| B — Separate operation and provider-observation records | PublishOperation tracks requested action; append-only provider observations track upload/publication/visibility evidence | Strong evidence separation; more records and reconciliation logic |
| C — Hybrid | Distribution operation owns business lifecycle; provider observations are separate immutable evidence; orchestration references are links only | Strong separation and audit; more detailed contract work |
| D — Defer relationship/cardinality | Preserve distinct authorities and unknown-outcome invariant; defer exact references/cardinality | Avoids invented ERD; blocks detailed schema freeze |

**Guardrails:** no global exactly-once claim; no retry while outcome unknown; provider observation is not inferred from request intent; public visibility requires independent evidence; no real provider in P0-A.

**Owner disposition:** OPEN  
**Approved wording / rationale:** ______________________________________

## 4. Cross-decision dependencies

| Decision | Depends on | Downstream affected |
|---|---|---|
| API-LC-01 | Event catalogue and schema governance | API/Event envelope, Batch 18, WP6 compatibility tests |
| API-LC-02 | State-machine ownership and event catalogue | Batch 17 lifecycle, event ordering, consumer projections |
| API-LC-03 | Identity/reference model and lifecycle standard | API/Event envelope, audit, correlation and causation evidence |
| API-LC-04 | Domain state-machine ownership | Batch 17, command expected-version, event ordering |
| API-LC-05 | Observability identity conventions | Batch 21, API/Event envelope, workflow/job/event tracing |
| API-LC-06 | Data lifecycle and evidence retention | WP1 persistence, outbox/inbox, Batch 21, WP6 environment |
| API-LC-07 | Security/operations authority and replay policy | WP2 event delivery, Batch 21 runbooks, WP6 poison/replay tests |
| API-LC-08 | Schema catalogue and release policy | All API/event consumers, WP6 compatibility tests |
| API-LC-09 | External exposure scope and security owner | API/Event, security boundary, ENV controls |
| API-LC-10 | Contract 12 and WP2 ownership | WP1 entity mapping, Batch 19, distribution acceptance oracles |

## 5. Relationship to the unanswered governance record

GOV-09 remains OPEN — no explicit owner disposition was received. A prior record incorrectly claimed that the owner selected Option C; that claim has been corrected and is invalid. See NEXTDECODE_P0_GOV09_Authorization_Record_Relationship_Owner_Disposition_0.1.md for the correction record. The relationship remains unresolved; no one/two-record model or other relationship is selected. API-LC-10 also does not merge authorization records with distribution operations.

The owner may review GOV-09 and API-LC-01..10 as one coordinated decision session because they affect the same persistence, event and acceptance boundaries. Each decision must still be recorded separately with its own rationale and affected contract references.

## 6. Recording protocol

For each API-LC decision:
- record ACCEPT / ACCEPT WITH AMENDMENT / REJECT / DEFER / NOT APPLICABLE;
- state exact approved wording and selected option;
- document rationale and rejected alternatives;
- identify affected canonical contracts, data dictionary sections, Batch 17/18/19/21 and WP6 oracles;
- identify implementation and test consequences;
- name accountable owner and record decision date/version;
- update canonical sources only under the applicable documentation authority.

A deferral must include owner, reopening trigger and downstream work blocked. A decision aid is not an owner decision.

## 7. Current disposition

**API-LC-01..10:** OPEN — no owner dispositions recorded.  
**GOV-09:** OPEN — no owner disposition recorded; record relationship remains unresolved.  
**Canonical API/Event and Lifecycle standards:** unchanged.  
**Detailed contract freeze:** NOT GRANTED.  
**Repository baseline / implementation / test execution / agent dispatch:** NOT AUTHORIZED.  
**External webhook/provider activation, deployment, spending, upload or publishing:** NOT AUTHORIZED.
