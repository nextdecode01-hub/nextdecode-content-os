# P0-WP1 Owner Decision Register

**Document ID:** `P0_WP1_OWNER_DECISION_REGISTER`  
**Version:** 0.1  
**Status:** AWAITING OWNER DISPOSITION — no decision is accepted by this document  
**Scope:** P0 WP-1 — Canonical Domain and Persistence Foundation  
**Related report:** `reports/unattributed/P0_WP1_CONTRACT_CLOSURE_REPORT.md`  
**Implementation authorization:** NOT GRANTED

> This register contains only decisions that require owner authority. Technical defaults that do not change contract meaning are listed in the report and are approved as part of OD-10, not as separate owner decisions. No option is selected here on the owner’s behalf.

---

## How to use this register

For each decision, record one disposition:

- **ACCEPT** — approve the recommendation.
- **ACCEPT WITH AMENDMENT** — approve only with the recorded change.
- **REJECT** — do not adopt; record the alternative.
- **DEFER** — leave open; name the condition for resolution.

Do not infer acceptance from silence, a prior discussion, an agent report or completion of this document.

---

## Decision index

| ID | Decision | Blocks |
|---|---|---|
| WP1-OD-01 | Logical naming and data-dictionary baseline | Physical schema, API envelopes, WP-2 inheritance |
| WP1-OD-02 | ContentItem editorial fields, title and origin | ContentItem table, version pointer |
| WP1-OD-03 | ContentVersion payload and immutability | ContentVersion table, approval binding |
| WP1-OD-04 | ContentVariant dimensions and revision model | Variant table, uniqueness |
| WP1-OD-05 | Artifact/ArtifactVersion physical boundary | Variant/artifact refs, WP-4 boundary |
| WP1-OD-06 | WorkflowTask/Job/JobAttempt persistence boundary | WP-1 scope, P0-A slice |
| WP1-OD-07 | Deletion, archival and FK actions | All FK/delete behavior |
| WP1-OD-08 | Database engine and migration tooling | Types, migrations, test environment |
| WP1-OD-09 | Lifecycle vocabularies for WP-1 entities | State columns, transition tests |
| WP1-OD-10 | Approval of the proposed physical schema | Schema/migration implementation |
| WP1-OD-11 | WP-1-A implementation authorization | Any code/migration/test work |

---

## WP1-OD-01 — Logical naming and data-dictionary baseline

**Exact question:** Do we freeze WP-1 on `workflow_run`/`workflow_run_id` and `workflow_task`, and how do we close the canonical data-dictionary gap for `ContentVersion`, `ContentVariant` and `WorkflowTask`?

**Relevant sources:**
- Report §4 I-01/I-02/I-03/I-04/I-07.
- `NEXTDECODE_P0_WP1_Final_Schema_Contract_Candidate_0.3.md` §4.4, §4.5, §4.7.
- `NEXTDECODE_P0_WP1_Design_Resolution_Record_0.2.md` §3.2, §3.4, §3.6.
- `NEXTDECODE_Canonical_Data_Dictionary_Entity_Ownership_Registry_1.0.md` §5.4, §5.5, §15.5.
- `NEXTDECODE_Canonical_Contracts_Pack_1.0.md` §1.1, §3.2.

**Existing accepted constraints:** UUIDv7 identity; one owner per entity; separate state machines; accepted CF-01/CF-02.

**Options:**

| Option | Description | Trade-off |
|---|---|---|
| A | Adopt `workflow_run`/`workflow_run_id` and `workflow_task`; extend the data dictionary for ContentVersion/ContentVariant/WorkflowTask before freeze | One vocabulary; requires a dictionary update |
| B | Keep `workflow_id`/`WorkflowTask` and add a mapping note to WorkflowRun/Task | Less documentation churn; two vocabularies persist |
| C | Defer naming to implementation | Fastest now; highest risk of schema/API divergence |

**Technical recommendation:** A.

**Consequences if unresolved:** Physical tables, API envelopes and WP-2 will use competing names; content version/variant definitions remain non-canonical.

**Owner disposition:** ☐ ACCEPT  ☐ ACCEPT WITH AMENDMENT  ☐ REJECT  ☐ DEFER  
**Amendment / note:** ______________________________________________

---

## WP1-OD-02 — ContentItem editorial fields, title and origin

**Exact question:** Which ContentItem fields are required in WP-1-A, where does `title` live, and which origin reference is canonical (`origin_opportunity_id` vs `source_idea_id`)?

**Relevant sources:**
- Report §4 I-05; report §5 D-02.
- `NEXTDECODE_P0_WP1_Final_Schema_Contract_Candidate_0.3.md` §4.3.
- `NEXTDECODE_P0_WP1_Design_Resolution_Record_0.2.md` §3.1, §3.3.
- `NEXTDECODE_Canonical_Data_Dictionary_Entity_Ownership_Registry_1.0.md` §5.4.

**Existing accepted constraints:** ContentItem is the shared editorial identity; ContentIdea ≠ ContentItem; typed cross-domain references; no duplicate status field.

**Options:**

| Option | Description | Trade-off |
|---|---|---|
| A | ContentItem stores identity/scope/type/lifecycle/origin/current-version pointer; title lives on ContentVersion; no title projection | Clean version provenance; listing may need a join |
| B | A plus denormalized current title on ContentItem for listing | Faster reads; projection must be kept consistent |
| C | Title on ContentItem only | Simple; weak version/title history |

**Technical recommendation:** A, with `origin_opportunity_id` nullable and `title` on ContentVersion. Add a read projection later only if measured need exists.

**Consequences if unresolved:** Required/nullable fields, title indexing and version provenance cannot be frozen.

**Owner disposition:** ☐ ACCEPT  ☐ ACCEPT WITH AMENDMENT  ☐ REJECT  ☐ DEFER  
**Amendment / note:** ______________________________________________

---

## WP1-OD-03 — ContentVersion payload and immutability

**Exact question:** What is the authoritative ContentVersion schema: payload representation, title placement, version numbering and integrity hash?

**Relevant sources:**
- Report §4 I-03; report §5 D-03.
- `NEXTDECODE_P0_WP1_Final_Schema_Contract_Candidate_0.3.md` §4.4, §6.1.
- `NEXTDECODE_P0_WP1_Design_Resolution_Record_0.2.md` §3.2.
- `NEXTDECODE_P0_WP1_Canonical_Domain_Persistence_Boundary_0.1.md` §5.4.
- `NEXTDECODE_Canonical_Data_Dictionary_Entity_Ownership_Registry_1.0.md` §5.4.

**Existing accepted constraints:** ContentVersion is immutable; entity ID, version ID and schema version are distinct; material change creates a new version.

**Options:**

| Option | Description | Trade-off |
|---|---|---|
| A | `version_number integer`, `title text`, `editorial_payload jsonb`, optional `content_sha256`; unique `(content_item_id, version_number)` | Compact, immutable, testable; JSONB is PostgreSQL-specific |
| B | Normalize payload into section/paragraph child tables | Strong relational structure; larger schema and migration scope |
| C | External payload reference by URI/hash | Storage-agnostic; adds artifact/storage ownership before WP-4 |

**Technical recommendation:** A for WP-1-A; use `text` instead of `jsonb` if a portable SQL dialect is required. Add `content_sha256` only when canonicalization rules are approved.

**Consequences if unresolved:** Cannot create the first immutable version, enforce version uniqueness or bind approvals/QA to exact content.

**Owner disposition:** ☐ ACCEPT  ☐ ACCEPT WITH AMENDMENT  ☐ REJECT  ☐ DEFER  
**Amendment / note:** ______________________________________________

---

## WP1-OD-04 — ContentVariant dimensions and revision model

**Exact question:** Are format/platform/language/treatment separate typed columns or a versioned profile reference, and is a separate variant revision identity required?

**Relevant sources:**
- Report §4 I-04/I-11; report §5 D-04.
- `NEXTDECODE_P0_WP1_Final_Schema_Contract_Candidate_0.3.md` §4.5.
- `NEXTDECODE_P0_WP1_Design_Resolution_Record_0.2.md` §3.4.
- `NEXTDECODE_P0_WP1_Canonical_Domain_Persistence_Boundary_0.1.md` §5.5.
- `NEXTDECODE_Artifact_08_v1.2_Consolidated_Freeze_Candidate.md` CF-01.

**Existing accepted constraints:** ContentVariant is a derivative, not a second ContentItem; format/platform/language/treatment are the accepted dimensions.

**Options:**

| Option | Description | Trade-off |
|---|---|---|
| A | Typed columns for format/platform/language/treatment, optional `variant_profile_version_id`; no separate revision table in WP-1-A | Simple; profile contract remains partial |
| B | Versioned profile reference only | Central Contract 11 profile; WP-1 cannot validate dimensions locally |
| C | Separate `content_variant_version` table now | Strong revision history; larger scope |

**Technical recommendation:** A for WP-1-A; defer the profile contract to Contract 11. Use a new variant or a later version for material changes; do not silently mutate history. Omit `current_artifact_version_id` unless OD-05 approves the reference.

**Consequences if unresolved:** Variant uniqueness, nullability and lifecycle tests cannot be defined; duplicate content identities may appear.

**Owner disposition:** ☐ ACCEPT  ☐ ACCEPT WITH AMENDMENT  ☐ REJECT  ☐ DEFER  
**Amendment / note:** ______________________________________________

---

## WP1-OD-05 — Artifact/ArtifactVersion physical boundary

**Exact question:** Does WP-1-A create Artifact/ArtifactVersion tables, or only typed references owned by WP-4/Part 7?

**Relevant sources:**
- Report §4 I-06/I-11; report §5 D-05.
- `NEXTDECODE_P0_WP1_Final_Schema_Contract_Candidate_0.3.md` §4.8, §4.9.
- `NEXTDECODE_P0_WP1_Design_Resolution_Record_0.2.md` §3.5, §5.
- `NEXTDECODE_P0_WP1_Canonical_Domain_Persistence_Boundary_0.1.md` §5.9.
- `NEXTDECODE_Canonical_Data_Dictionary_Entity_Ownership_Registry_1.0.md` §17.
- `NEXTDECODE_P0_04_Engineering_Work_Orders_WP1_to_WP6.md` WP-4.

**Existing accepted constraints:** Artifact and Asset are distinct; artifact versions immutable; Part 7 owns artifact metadata; WP-4 owns storage/transfer.

**Options:**

| Option | Description | Trade-off |
|---|---|---|
| A | Reference-only in WP-1-A; no artifact tables; `artifact_version_id` is a typed cross-domain ref | Preserves WP-4 ownership; no local FK |
| B | Minimal Artifact/ArtifactVersion metadata tables in WP-1-A | Local FK integrity; overlaps WP-4 schema |
| C | Full artifact and transfer implementation now | Complete; out of WP-1 scope and unauthorized |

**Technical recommendation:** A. Acceptance tests validate the reference shape/version and reject malformed refs; WP-4 provides the owner validation.

**Consequences if unresolved:** Cross-domain artifact pointers have no agreed integrity story, or WP-1 preempts WP-4 and creates a competing artifact owner.

**Owner disposition:** ☐ ACCEPT  ☐ ACCEPT WITH AMENDMENT  ☐ REJECT  ☐ DEFER  
**Amendment / note:** ______________________________________________

---

## WP1-OD-06 — WorkflowTask/Job/JobAttempt persistence boundary

**Exact question:** Does WP-1-A persist a minimal Job identity, or defer Job/JobAttempt entirely to WP-2?

**Relevant sources:**
- Report §5 D-06.
- `NEXTDECODE_P0_WP1_Final_Schema_Contract_Candidate_0.3.md` §4.7.
- `NEXTDECODE_P0_WP1_Design_Resolution_Record_0.2.md` §3.6, §5.
- `NEXTDECODE_P0_WP1_Canonical_Domain_Persistence_Boundary_0.1.md` §5.7, §5.8.
- `NEXTDECODE_P0_WP2_Durable_Job_Workflow_Execution_0.1.md` §4–§7.

**Existing accepted constraints:** WorkflowTask ≠ Job ≠ JobAttempt; execution semantics belong to WP-2; a task may create one or more jobs.

**Options:**

| Option | Description | Trade-off |
|---|---|---|
| A | No Job table in WP-1-A; `workflow_task` and typed refs only | Preserves WP-1/WP-2 boundary; P0-A needs WP-2 for job persistence |
| B | Minimal Job identity table in WP-1-A, no leases/queue | Enables early job persistence; overlaps WP-2 identity boundary |
| C | Full WP-2 implementation now | Out of scope; violates ordering |

**Technical recommendation:** A. Choose B only if the owner changes the vertical-slice acceptance to require a persisted Job before WP-2.

**Consequences if unresolved:** WP-1 scope expands into execution, or the P0-A slice lacks a durable job identity when needed.

**Owner disposition:** ☐ ACCEPT  ☐ ACCEPT WITH AMENDMENT  ☐ REJECT  ☐ DEFER  
**Amendment / note:** ______________________________________________

---

## WP1-OD-07 — Deletion, archival and FK actions

**Exact question:** What exact FK delete/update actions and archival/tombstone behavior apply to WP-1-A?

**Relevant sources:**
- Report §4 I-08; report §5 D-07; report §6.6.
- `NEXTDECODE_P0_WP1_Final_Schema_Contract_Candidate_0.3.md` §6.5.
- `NEXTDECODE_P0_WP1_Design_Resolution_Record_0.2.md` §3.8.
- `NEXTDECODE_P0_WP1_Canonical_Domain_Persistence_Boundary_0.1.md` §7.3.
- Accepted CF-06 reference as cited in S2 §3.8; exact CF wording must be reproduced from the authoritative CF record before freeze.

**Existing accepted constraints:** Archival, logical deletion and physical deletion are distinct; lineage/evidence preserved; local deletion ≠ external deletion.

**Options:**

| Option | Description | Trade-off |
|---|---|---|
| A | `ON DELETE RESTRICT`, no cascade; no physical delete in WP-1-A; archival later | Conservative; may require explicit cleanup workflows later |
| B | Soft-delete/archival columns from day one | Earlier policy support; more fields and rules |
| C | Cascade deletes | Rejected: destroys lineage/evidence |

**Technical recommendation:** A. It preserves lineage and defers retention policy to the owning governance work.

**Consequences if unresolved:** Migrations may bake in destructive delete semantics that conflict with evidence retention.

**Owner disposition:** ☐ ACCEPT  ☐ ACCEPT WITH AMENDMENT  ☐ REJECT  ☐ DEFER  
**Amendment / note:** ______________________________________________

---

## WP1-OD-08 — Database engine and migration tooling

**Exact question:** Which PostgreSQL-compatible engine, driver/ORM and migration tool are approved for WP-1-A?

**Relevant sources:**
- Report §7.
- ADR-002 in `NEXTDECODE_Accepted_P0_Architecture_Decision_Baseline_1.0.md`.
- `NEXTDECODE_P0_WP1_Design_Resolution_Record_0.2.md` §3.9.
- `NEXTDECODE_P0_02_P0_Implementation_Master_Plan.md` §2, §5.
- `NEXTDECODE_P0_Batch13...docx` §10.

**Existing accepted constraints:** PostgreSQL-compatible relational store; free-first; no paid service or dependency installation without authorization.

**Options:**

| Option | Description | Trade-off |
|---|---|---|
| A | PostgreSQL 16 + SQLAlchemy 2 + Alembic, local free instance | Matches ADR-002; mature migrations; adds dependencies |
| B | PostgreSQL + psycopg 3 + plain SQL migrations | Explicit SQL; fewer abstractions; manual tooling |
| C | SQLite + SQLAlchemy/Alembic | Zero service; not PostgreSQL-compatible enough for acceptance |
| D | Managed PostgreSQL free tier | Less operations; possible billing/limit exposure |

**Technical recommendation:** A; B as the dependency-minimal alternative; C only as a fast test adapter; D only with explicit cost approval.

**Consequences if unresolved:** Types, migration commands, test environment and implementation scope cannot be fixed.

**Owner disposition:** ☐ ACCEPT  ☐ ACCEPT WITH AMENDMENT  ☐ REJECT  ☐ DEFER  
**Amendment / note:** ______________________________________________

---

## WP1-OD-09 — Lifecycle vocabularies for WP-1 entities

**Exact question:** Which lifecycle vocabularies and transition rules apply to Workspace, ContentItem, ContentVersion, ContentVariant, WorkflowRun and WorkflowTask in WP-1-A?

**Relevant sources:**
- Report §5 D-09.
- `NEXTDECODE_Canonical_Data_Dictionary_Entity_Ownership_Registry_1.0.md` §2.1, §3.1, §19.
- `NEXTDECODE_P0_WP1_Final_Schema_Contract_Candidate_0.3.md` §4, §6.4.
- `NEXTDECODE_P0_WP1_Design_Resolution_Record_0.2.md` §3.4, §3.6.
- `NEXTDECODE_Canonical_Contracts_Pack_1.0.md` §2.
- `NEXTDECODE_API_Event_Contract_Standard_1.0.md` §7.

**Existing accepted constraints:** Separate state machines; no universal status; owning domain validates transitions.

**Options:**

| Option | Description | Trade-off |
|---|---|---|
| A | Define minimum domain-specific states and transition guards for WP-1-A | Testable; requires owner/domain agreement |
| B | Define only initial state; defer transitions to WP-2/WP-5 | Faster; lifecycle tests incomplete |
| C | One generic status field | Rejected by ADR-010 |

**Technical recommendation:** A for the minimum states needed by the vertical slice; do not invent WP-2 execution states.

**Consequences if unresolved:** State columns and tests remain undefined; generic statuses may collapse distinct meanings.

**Owner disposition:** ☐ ACCEPT  ☐ ACCEPT WITH AMENDMENT  ☐ REJECT  ☐ DEFER  
**Amendment / note:** ______________________________________________

---

## WP1-OD-10 — Approval of the proposed physical schema

**Exact question:** Does the owner approve the physical schema in `reports/unattributed/P0_WP1_CONTRACT_CLOSURE_REPORT.md` §6, including types, nullability, PK/FK, uniqueness, indexes and cross-domain reference handling?

**Relevant sources:**
- Report §6.
- `NEXTDECODE_P0_WP1_Final_Schema_Contract_Candidate_0.3.md` §6, §8.
- `NEXTDECODE_P0_WP1_Design_Resolution_Record_0.2.md` §4.
- `NEXTDECODE_P0_WP1_Canonical_Domain_Persistence_Boundary_0.1.md` §7.2.
- `NEXTDECODE_API_Event_Contract_Standard_1.0.md` §10.2.

**Existing accepted constraints:** UUIDv7; workspace isolation; ownership; immutable versions; PostgreSQL-compatible.

**Options:**

| Option | Description | Trade-off |
|---|---|---|
| A | Approve §6 with technical defaults and fields marked OPEN | Enables test-first schema work; some fields remain pending |
| B | Amend specific fields/constraints before approval | More precise; delays freeze |
| C | Defer physical schema | Blocks migration and repository work |

**Technical recommendation:** A with explicit amendments for the fields tied to OD-02–OD-07.

**Consequences if unresolved:** No migration/repository can be implemented without inventing a schema.

**Owner disposition:** ☐ ACCEPT  ☐ ACCEPT WITH AMENDMENT  ☐ REJECT  ☐ DEFER  
**Amendment / note:** ______________________________________________

---

## WP1-OD-11 — WP-1-A implementation authorization

**Exact question:** After contract freeze, does the owner authorize a bounded WP-1-A implementation?

**Relevant sources:**
- Report §10.
- `NEXTDECODE_P0_Owner_Review_Contract_Freeze_Decision_Record_0.1.md` §7.
- `NEXTDECODE_P0_Batch13...docx` §13.
- `NEXTDECODE_P0_Batch15...docx` authorization status.
- `NEXTDECODE_P0_Implementation_Authorization_Brief_1.0.md` §10–§12.

**Existing accepted constraints:** Implementation authorization is separate from contract freeze; exact paths, tests, evidence, owner and stop conditions required.

**Options:**

| Option | Description | Trade-off |
|---|---|---|
| A | Authorize WP-1-A only after OD-01–OD-10 are dispositioned | Controlled; slower |
| B | Defer until after a final candidate 0.4 is written | Safer; more documentation |
| C | Reject/defer entirely | No implementation progress |

**Technical recommendation:** B now; A immediately after the final candidate and physical schema are approved.

**Consequences if unresolved:** No code, migration or test may be written under project governance.

**Owner disposition:** ☐ ACCEPT  ☐ ACCEPT WITH AMENDMENT  ☐ REJECT  ☐ DEFER  
**Amendment / note:** ______________________________________________

---

## Technical defaults proposed for OD-10 (not separate owner decisions)

These are engineering defaults in the report; the owner approves or amends them through OD-10:

- UUIDv7 primary keys; immutable IDs.
- `timestamptz` UTC timestamps.
- `schema_version text` (record shape) distinct from `record_version bigint` (optimistic concurrency).
- `workspace_id` on every tenant table; composite workspace-scoped FKs.
- `ON DELETE RESTRICT`; no cascade.
- `content_version` append-only; no UPDATE/DELETE.
- Cross-domain references have no local FK; they are validated by the owning service.
- `READ COMMITTED` plus unique constraints/conditional updates; `SERIALIZABLE` optional for multi-row invariants.
- No partitioning, partial indexes or JSONB indexes in WP-1-A.

---

## Register status

- **Decisions recorded:** 11.
- **Decisions dispositioned:** 0.
- **Contract ready:** **NO — NOT READY FOR FREEZE.**
- **Implementation authorization:** **NOT GRANTED.**
- **Next action:** owner dispositions on WP1-OD-01–11, then a final WP-1 candidate and physical schema appendix, then a separate implementation authorization.

No code, migration, database operation, test execution or existing-document change was performed.

---

## Final status

- **CONTRACT READY: NO — NOT READY FOR FREEZE.**
- **Remaining owner decisions:** WP1-OD-01 through WP1-OD-11.
- **Implementation authorization:** NOT GRANTED.
- **Recommended next action:** Owner dispositions on this register, then a final WP-1 contract candidate and physical schema appendix, then a separate bounded WP-1-A implementation authorization.
