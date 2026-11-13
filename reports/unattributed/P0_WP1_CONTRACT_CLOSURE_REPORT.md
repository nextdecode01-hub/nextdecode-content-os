# P0-WP1 Contract Closure Report

**Document ID:** `P0_WP1_CONTRACT_CLOSURE_REPORT`  
**Version:** 0.1  
**Status:** CONTRACT NOT READY FOR FREEZE — OWNER DECISIONS REQUIRED  
**Scope:** P0 WP-1 — Canonical Domain and Persistence Foundation  
**Mode:** READ-ONLY investigation and documentation proposal. No code, schema, migration, database, test or existing-document changes were made.  
**Implementation authorization:** NOT GRANTED

---

## 1. Executive result

WP-1 is **not ready for an owner contract-freeze decision**. The logical direction is coherent and most entity boundaries are already source-defined, but the contract still has:

- 11 owner-level decisions (see `docs/workstream-review/wp1/P0_WP1_OWNER_DECISION_REGISTER.md`);
- one naming conflict (`Workflow`/`workflow_id` vs `WorkflowRun`/`workflow_run_id`);
- a data-dictionary gap for `ContentVersion`, `ContentVariant` and `WorkflowTask`;
- an unresolved artifact-table versus artifact-reference boundary;
- an unresolved Job/JobAttempt boundary;
- unresolved deletion/archival actions;
- no selected database/migration tooling;
- no approved physical schema;
- no implementation authorization.

The proposed physical schema in §7 is a concrete starting point for owner review, not an approved schema.

---

## 2. Source set and evidence labels

| ID | Source | Version / status | Used for |
|---|---|---|---|
| S1 | `NEXTDECODE_P0_WP1_Final_Schema_Contract_Candidate_0.3.md` | 0.3; consolidated design candidate — owner review required | Logical entities, fields, open decisions, acceptance candidate |
| S2 | `NEXTDECODE_P0_WP1_Design_Resolution_Record_0.2.md` | 0.2; recommended resolutions — owner review required | Resolution of WP1-O-01–09, minimum slice |
| S3 | `NEXTDECODE_P0_WP1_Canonical_Domain_Persistence_Boundary_0.1.md` | 0.1; design candidate — owner review required | Original WP1-O-01–09, persistence requirements |
| S4 | `NEXTDECODE_Canonical_Data_Dictionary_Entity_Ownership_Registry_1.0.md` | 1.0; canonical field/ownership reference | Workspace, ContentItem, Relationship, WorkflowRun, Artifact |
| S5 | `NEXTDECODE_Canonical_Contracts_Pack_1.0.md` | 1.0; proposed baseline — approval pending | IDs, Task/Job envelopes, workflow naming |
| S6 | `NEXTDECODE_Accepted_P0_Architecture_Decision_Baseline_1.0.md` | 1.0; accepted ADRs | ADR-001, ADR-002, ADR-004, ADR-006, ADR-010 |
| S7 | `NEXTDECODE_Artifact_08_v1.2_Consolidated_Freeze_Candidate.md` | v1.2; freeze candidate | CF-01, CF-02, CF-24, accepted-decision precedence |
| S8 | `NEXTDECODE_P0_Owner_Review_Contract_Freeze_Decision_Record_0.1.md` | 0.1; owner decision draft — not approved | WP-1/2/3 dispositions OPEN; authorization NOT GRANTED |
| S9 | `NEXTDECODE_P0_02_P0_Implementation_Master_Plan.md` | 0.1; planning candidate — owner review required | WP-1 first; parallel-work constraints |
| S10 | `NEXTDECODE_P0_04_Engineering_Work_Orders_WP1_to_WP6.md` | 0.1; draft templates — not assignments | WP-1 scope, out-of-scope, acceptance evidence |
| S11 | `NEXTDECODE_P0_05_P0_Acceptance_Evidence_and_Release_Gates.md` | 0.1; candidate — not executed | Evidence record, gates, QA |
| S12 | `NEXTDECODE_API_Event_Contract_Standard_1.0.md` | 1.0; standard | Command/event separation, idempotency, atomic outbox |
| S13 | `NEXTDECODE_P0_Batch13_Implementation_Readiness_Controlled_Execution_Package.docx` | 1.0; controlled plan — **NOT an implementation authorization** | Execution gates; final status explicitly not authorized |
| S14 | `NEXTDECODE_P0_Batch15_Source_Reconciliation_Contract_Closure_Dossier.docx` | Source reconciliation; not a freeze | Confirms contract freeze pending and implementation authorization not granted |
| S15 | `NEXTDECODE_P0_Implementation_Authorization_Brief_1.0.md` | 1.0; **NOT AUTHORIZED** | Owner authorization state |

Evidence labels used:

- **VERIFIED** — directly checked in the named source.
- **REPORTED** — stated by a source but not independently re-derived.
- **INFERRED** — reasoned from multiple sources; not directly stated.
- **PROPOSED** — a recommendation in this report, not an owner decision.

---

## 3. Accepted constraints that cannot be reopened by WP-1

| Constraint | Source |
|---|---|
| UUIDv7 canonical IDs; immutable and never reused | ADR-001 (S6); S4 §2.2 |
| PostgreSQL-compatible relational database is authoritative shared state | ADR-002 (S6) |
| Versioned HTTP/JSON contracts with schema validation | ADR-004 (S6) |
| Relational artifact metadata; binaries behind storage abstraction | ADR-006 (S6) |
| Separate state machines; no universal status field | ADR-010 (S6); S4 §2.1/§3.1 |
| ContentItem is shared editorial identity; ContentVariant is a format/platform/language/treatment derivative | CF-01 (S7) |
| One authoritative owner per canonical entity; typed cross-domain references; no competing IDs | CF-02 (S7); S4 §2.1 |
| No paid services or charge-generating infrastructure without explicit approval | CF-24 (S7) |
| Existing Shorts Studio remains a specialised engine behind a bounded adapter | P0 Master Plan §2 (S9); S3 §8 |
| Approval, authorization, execution and confirmed outcome remain distinct | ADR-007/ADR-010 (S6); S12 §3.1 |

These constraints are accepted. WP-1 may implement them; it may not weaken them.

---

## 4. Inconsistencies and proposed resolutions

| ID | Inconsistency | Sources | Proposed resolution | Status |
|---|---|---|---|---|
| I-01 | `Workflow` + `workflow_id` vs `WorkflowRun` + `workflow_run_id` | S1 §4.7; S3 §5.6; S4 §15.5; S5 §1.1/§3.2 | Physical table `workflow_run`; `workflow_run_id` PK; prose may call it “workflow”. Do not create both. | PROPOSED; owner in OD-01 |
| I-02 | `WorkflowTask` vs `Task` | S1 §4.7; S3 §5.7; S5 §1.1/§3.2; S4 lacks WorkflowTask | Physical table `workflow_task` as the workflow-scoped Task; no separate `task` table in WP-1-A. Map to API `Task` later. | PROPOSED; OD-01 |
| I-03 | `ContentVersion` is used by S1 but absent from S4 | S1 §4.4; S4 §5.4 (only `current_content_version_id`) | Extend the canonical data dictionary for ContentVersion, or explicitly adopt S1 §4.4 as the interim source, before freeze. | PROPOSED; OD-01/OD-03 |
| I-04 | `ContentVariant` is used by S1/S3 but absent from S4 | S1 §4.5; S3 §5.5; S4 §5.4/§16 | Extend the dictionary or adopt S1 §4.5 as the interim source. Do not create two variant definitions. | PROPOSED; OD-01/OD-04 |
| I-05 | Content origin: `origin_opportunity_id` vs `source_idea_id` | S1 §4.3; S2 §3.3; S3 §5.3 | One nullable typed origin reference. Recommend `origin_opportunity_id` to Contract 02; do not add a second `source_idea_id` unless Contract 02 confirms a separate idea entity. | PROPOSED; OD-02 |
| I-06 | Artifact tables vs artifact reference boundary | S1 §4.8; S2 §3.5/§5; S3 §5.9; S4 §17 | WP-1-A stores typed artifact/version references only; Artifact/ArtifactVersion tables remain WP-4. Acceptance is adjusted to reference integrity, not local artifact tables. | PROPOSED; OD-05 |
| I-07 | Workflow definition: inline type/version vs WorkflowDefinition/WorkflowRun | S1 §4.7; S4 §15.5; S5 §1.1 | No `workflow_definition` table in WP-1-A. Store `workflow_definition_version_id` and `workflow_type` as references; definition ownership remains orchestration/Contract 10. | PROPOSED; OD-01/OD-06 |
| I-08 | Deletion: candidate recommendation vs exact SQL actions | S1 §6.5; S2 §3.8; S3 §7.3; S4 §20/§23 | Adopt RESTRICT/no-cascade for WP-1-A; defer archival/tombstone and retention execution. Exact SQL actions approved with physical schema. | PROPOSED; OD-07 |
| I-09 | Database engine: ADR-002 PostgreSQL vs deferred tooling vs free-first | S6 ADR-002; S2 §3.9; S9 §2/§5; S13 §10 | PostgreSQL-compatible engine required; local free PostgreSQL + open-source migration tool recommended; SQLite test adapter only. | PROPOSED; OD-08 |
| I-10 | Common record envelope includes `record_version`; S1 fields do not | S5 §1.4; S1 §4 | Add `record_version bigint` for optimistic concurrency alongside `schema_version`; they are different concepts. | PROPOSED technical default; OD-10 |
| I-11 | ContentVariant current artifact pointer vs Part 7 ownership | S1 §4.5; S2 §3.5; S3 §5.9 | Optional nullable `current_artifact_version_id` as a cross-domain reference; no FK; WP-4 owns artifact truth. If owner prefers, omit the pointer from WP-1-A. | PROPOSED; OD-04/OD-05 |
| I-12 | Relationship table is source-defined but not in S2 minimum slice | S1 §4.6; S4 §5.5; S2 §5 | Include `relationship` in WP-1-A to satisfy typed-relationship acceptance; validate polymorphic targets in the owning service. | PROPOSED; OD-10 |

---

## 5. Unresolved decision analysis

> The authoritative decision list for owner action is in `docs/workstream-review/wp1/P0_WP1_OWNER_DECISION_REGISTER.md`. The analysis below explains each decision. Recommendations are technical recommendations, not owner selections.

### D-01 — Logical naming and data-dictionary baseline (OD-01)

- **Question:** Do we freeze WP-1 on `WorkflowRun`/`workflow_run_id` and `workflow_task`, and how do we close the missing `ContentVersion`/`ContentVariant`/`WorkflowTask` entries in the canonical data dictionary?
- **Sources:** S1 §4.4/§4.5/§4.7; S2 §3.6; S3 §5.6/§5.7; S4 §5.4/§5.5/§15.5; S5 §1.1/§3.2.
- **Accepted constraints:** ADR-010 separate lifecycles; CF-02 one owner per entity; UUIDv7 identity.
- **Options:**
  - A. Adopt `workflow_run`/`workflow_task` naming and extend the data dictionary for ContentVersion/ContentVariant/WorkflowTask before freeze.
  - B. Keep S1 `workflow_id`/`WorkflowTask` naming and add a mapping note; risk two vocabularies.
  - C. Defer naming to implementation; risk schema/API divergence.
- **Recommendation:** A. It matches S4 §15.5 and S5 §1.1, avoids two names for one record, and closes the dictionary gap explicitly.
- **If unresolved:** physical schema, API envelopes and tests cannot use one stable vocabulary; WP-2 will inherit the ambiguity.

### D-02 — ContentItem editorial fields, title and origin (OD-02)

- **Question:** Which ContentItem fields are required in WP-1-A, where does `title` live, and which origin reference is canonical?
- **Sources:** S1 §4.3; S2 §3.1/§3.3; S3 §5.3; S4 §5.4.
- **Accepted constraints:** ContentItem is shared editorial identity; ContentIdea ≠ ContentItem; typed refs; no duplicate status fields.
- **Options:**
  - A. ContentItem: identity/scope/type/lifecycle/origin/current-version pointer; title lives on ContentVersion; no title projection.
  - B. Same, plus a denormalized current-title projection on ContentItem for listing.
  - C. Title on ContentItem only; weaker version semantics.
- **Recommendation:** A, with `origin_opportunity_id` nullable and `title` on ContentVersion. If query performance later requires a projection, add it as a read model, not authoritative.
- **If unresolved:** schema cannot define NULL/NOT NULL, indexing or the current-version contract; editorial history may lose title provenance.

### D-03 — ContentVersion payload, title, numbering and integrity (OD-03)

- **Question:** What is the authoritative ContentVersion schema: payload representation, title placement, version numbering and integrity hash?
- **Sources:** S1 §4.4/§6.1; S2 §3.2; S3 §5.4; S4 §5.4; S5 §1.4.
- **Accepted constraints:** immutable version identity; entity ID ≠ version ID ≠ schema version; material change creates new version.
- **Options:**
  - A. `content_version` with `version_number integer`, `title text`, `editorial_payload jsonb`, optional `content_sha256`; unique `(content_item_id, version_number)`.
  - B. Same with payload in a separate normalized child table (sections/paragraphs).
  - C. Payload stored externally and referenced by URI/hash.
- **Recommendation:** A for WP-1-A. It is immutable, compact and testable; B can come with editorial tooling; C introduces storage ownership before WP-4.
- **If unresolved:** cannot create the first immutable version, cannot enforce uniqueness, cannot bind approvals/QA to exact content.

### D-04 — ContentVariant dimensions, profile and revision model (OD-04)

- **Question:** Are format/platform/language/treatment separate typed columns or a versioned profile reference, and is there a separate variant revision identity?
- **Sources:** S1 §4.5; S2 §3.4; S3 §5.5; S4 §5.4/§16; S7 CF-01.
- **Accepted constraints:** ContentVariant is a derivative, not a second ContentItem; domain-owned lifecycle; no generic status.
- **Options:**
  - A. Typed columns `format`, `platform_target`, `language`, `treatment`, plus nullable `variant_profile_version_id`; no separate revision table in WP-1-A.
  - B. Versioned profile reference only; dimensions resolved through Contract 11 profile.
  - C. Separate `content_variant_version` table now; more complete, more scope.
- **Recommendation:** A for WP-1-A; keep profile-version reference optional; defer full profile contract to Contract 11. A variant change that alters editorial identity should create a new variant or a later version, not silently mutate history.
- **If unresolved:** uniqueness, indexing and lifecycle tests cannot be defined; variants may become duplicate content identities.

### D-05 — Artifact/ArtifactVersion physical boundary (OD-05)

- **Question:** Does WP-1-A create Artifact/ArtifactVersion tables, or only typed references owned by WP-4/Part 7?
- **Sources:** S1 §4.8/§4.9; S2 §3.5/§5; S3 §5.9; S4 §17; S9 WP-4.
- **Accepted constraints:** Artifact and Asset are distinct; artifact versions immutable; Part 7 owns artifact metadata; WP-4 owns transfer/storage.
- **Options:**
  - A. Reference-only in WP-1-A: `current_artifact_version_id` and typed refs; no artifact tables; no FK.
  - B. Minimal Artifact/ArtifactVersion metadata tables in WP-1-A, with WP-4 owning binary transfer.
  - C. Full artifact tables and transfer now; preempts WP-4.
- **Recommendation:** A. It preserves WP-4 ownership and still satisfies the reference boundary; acceptance tests validate reference shape/version and reject malformed refs. If the owner wants local FK integrity, choose B and explicitly move the minimal artifact metadata contract into WP-1.
- **If unresolved:** either cross-domain pointers have no integrity story, or WP-1 preempts WP-4 and creates a second artifact owner.

### D-06 — WorkflowTask/Job/JobAttempt physical boundary (OD-06)

- **Question:** Does WP-1-A persist a minimal Job identity, or defer Job/JobAttempt entirely to WP-2?
- **Sources:** S1 §4.7; S2 §3.6/§5; S3 §5.7/§5.8; S9 WP-2; S4 §15.6.
- **Accepted constraints:** WorkflowTask ≠ Job ≠ JobAttempt; execution semantics belong to WP-2; task may create one or more jobs.
- **Options:**
  - A. No Job table in WP-1-A; `workflow_task` and typed refs only; WP-2 adds Job/Attempt.
  - B. Minimal `job` identity table in WP-1-A, no leases/queue; P0-A vertical slice can persist a job early.
  - C. Full WP-2 now; out of scope.
- **Recommendation:** A. It follows S2 §5/§3.6 and S9 WP-1/WP-2 ordering. Choose B only if the owner changes the vertical-slice acceptance to require a persisted Job before WP-2.
- **If unresolved:** WP-1 scope expands into execution, or the P0-A slice has no durable job identity when needed.

### D-07 — Deletion, archival and FK actions (OD-07)

- **Question:** What exact FK delete/update actions and archival/tombstone behaviors apply to WP-1-A?
- **Sources:** S1 §6.5; S2 §3.8; S3 §7.3; S4 §20/§23; S7 CF-06 reference.
- **Accepted constraints:** archival/logical/physical deletion distinct; lineage/evidence preserved; local deletion ≠ external deletion; no broad cascade.
- **Options:**
  - A. `ON DELETE RESTRICT`, no cascade; no physical delete in WP-1-A; archival later.
  - B. Soft-delete/archival columns from day one; more fields and workflow.
  - C. Cascade deletes; rejected.
- **Recommendation:** A. It is the conservative CF-06-compatible default and avoids inventing retention policy. Add archival/tombstone only through the owning governance work.
- **If unresolved:** migrations may bake in destructive delete semantics that later conflict with evidence-retention requirements.

### D-08 — Database engine and migration tooling (OD-08)

- **Question:** Which PostgreSQL-compatible engine, driver/ORM and migration tool are approved for WP-1-A?
- **Sources:** S6 ADR-002; S2 §3.9; S9 §2/§5; S13 §10; S14.
- **Accepted constraints:** PostgreSQL-compatible relational store; no paid services; free-first; no dependency installation without authorization.
- **Options:** see §8.
- **Recommendation:** PostgreSQL 16 + SQLAlchemy 2 + Alembic, using a local free PostgreSQL instance/container; alternative plain SQL + psycopg if dependency minimization is required. SQLite only as a fast test adapter, not acceptance.
- **If unresolved:** physical types, migration commands and acceptance tests cannot be fixed; implementation authorization cannot be scoped.

### D-09 — Lifecycle vocabularies for WP-1 entities (OD-09)

- **Question:** Which lifecycle vocabularies and transition tables apply to Workspace, ContentItem, ContentVersion, ContentVariant, WorkflowRun and WorkflowTask?
- **Sources:** S4 §2.1/§19; S1 §4/§6.4; S2 §3.4/§3.6; S5 §2; S12 §7.
- **Accepted constraints:** separate state machines; no universal status; owning domain validates transitions.
- **Options:**
  - A. Adopt owner/domain-specific vocabularies now for WP-1-A, with a small transition table.
  - B. Define only initial state and defer transition tables to WP-2/WP-5.
  - C. Use one generic status field; rejected by ADR-010.
- **Recommendation:** A for the minimum states needed by the vertical slice; do not invent full workflow execution states. Define `lifecycle_status` values per entity and a transition guard in the repository; WP-2 owns execution transitions.
- **If unresolved:** state columns and tests are undefined; generic statuses may collapse distinct meanings.

### D-10 — Physical schema approval (OD-10)

- **Question:** Does the owner approve the proposed physical schema in §7, including types, nullability, PK/FK, unique constraints, indexes and cross-domain reference handling?
- **Sources:** S1 §6/§8; S2 §4; S3 §7.2; S5 §1.4; S12 §10.
- **Accepted constraints:** UUIDv7; workspace isolation; ownership; immutable versions; PostgreSQL-compatible.
- **Options:**
  - A. Approve §7 with the listed technical defaults and the open fields marked.
  - B. Amend specific fields/constraints before approval.
  - C. Defer physical schema; blocks implementation and migration design.
- **Recommendation:** A with explicit amendments for the fields tied to OD-02–OD-07. This is the minimum needed to write test-first schema tests.
- **If unresolved:** no migration or repository can be implemented without inventing a schema.

### D-11 — Implementation authorization (OD-11)

- **Question:** Does the owner authorize a bounded WP-1-A implementation after the contract is frozen?
- **Sources:** S8 §7; S13 §2/§13; S14; S15.
- **Accepted constraints:** implementation authorization is separate from contract freeze; exact paths, tests, evidence, owner and stop conditions required.
- **Options:** authorize WP-1-A; defer; reject.
- **Recommendation:** Defer until OD-01–OD-10 are dispositioned. Then authorize WP-1-A only.
- **If unresolved:** no code may be written under the project’s gates.

---

## 6. Proposed physical schema scope

### 6.1 Tables in the proposal

| Table | Owner | WP-1-A? | Notes |
|---|---|---|---|
| `workspace` | Shared Data Model / Workspace | Yes | Isolation root |
| `content_item` | Shared Content Graph | Yes | Editorial identity |
| `content_version` | Shared Content Graph | Yes | Immutable revision |
| `content_variant` | Shared Content Graph / Contract 11 | Yes | Format derivative |
| `workflow_run` | Orchestration / Contract 10 | Yes | Durable coordination instance |
| `workflow_task` | Orchestration / Contract 10 | Yes | Workflow-scoped logical task |
| `workflow_task_dependency` | Orchestration | Yes | Explicit task dependencies |
| `workflow_task_ref` | Orchestration | Yes | Typed input/output references |
| `relationship` | Shared Content Graph | Yes | Typed links; polymorphic validation |
| `external_reference` | Integration boundary | Conditional | Only if first slice maps legacy IDs |
| `artifact` / `artifact_version` | Part 7 / WP-4 | **No** | Reference-only in WP-1-A (OD-05) |
| `job` / `job_attempt` | WP-2 | **No** | Deferred to WP-2 unless OD-06 says otherwise |
| `content_idea`, `brand`, `actor`, `workflow_definition` | Other owners | **No** | Typed cross-domain references only |

### 6.2 PostgreSQL DDL sketch

> Proposed, not executed. `-- OPEN` marks fields/constraints tied to an owner decision. Types assume PostgreSQL-compatible storage.

```sql
CREATE TABLE workspace (
    workspace_id                       uuid PRIMARY KEY,
    name                               text NOT NULL,
    workspace_type                     text NOT NULL,
    lifecycle_status                   text NOT NULL,
    owner_actor_id                     uuid NOT NULL,          -- cross-domain actor ref; no FK until identity schema
    default_classification_policy_id   uuid NULL,
    default_retention_policy_id        uuid NULL,
    schema_version                     text NOT NULL,
    record_version                     bigint NOT NULL DEFAULT 1,
    created_at                         timestamptz NOT NULL,
    updated_at                         timestamptz NOT NULL
);

CREATE TABLE content_item (
    content_item_id                    uuid PRIMARY KEY,
    workspace_id                       uuid NOT NULL REFERENCES workspace(workspace_id) ON DELETE RESTRICT,
    brand_id                           uuid NOT NULL,          -- Contract 03 ref; no FK
    origin_opportunity_id              uuid NULL,              -- Contract 02 ref; no FK; OPEN OD-02
    content_type                       text NOT NULL,
    lifecycle_status                   text NOT NULL,
    current_content_version_id         uuid NULL,
    created_by_actor_id                uuid NOT NULL,
    schema_version                     text NOT NULL,
    record_version                     bigint NOT NULL DEFAULT 1,
    created_at                         timestamptz NOT NULL,
    updated_at                         timestamptz NOT NULL,
    UNIQUE (content_item_id, workspace_id)
);

CREATE TABLE content_version (
    content_version_id                 uuid PRIMARY KEY,
    content_item_id                    uuid NOT NULL,
    workspace_id                       uuid NOT NULL,
    version_number                     integer NOT NULL CHECK (version_number > 0),
    title                              text NULL,              -- OPEN OD-02
    editorial_payload                  jsonb NULL,             -- OPEN OD-03; portable alternative: text
    content_sha256                     char(64) NULL,          -- OPEN OD-03
    created_by_actor_id                uuid NOT NULL,
    schema_version                     text NOT NULL,
    created_at                         timestamptz NOT NULL,
    UNIQUE (content_item_id, version_number),
    UNIQUE (content_version_id, content_item_id),
    FOREIGN KEY (content_item_id, workspace_id)
        REFERENCES content_item(content_item_id, workspace_id) ON DELETE RESTRICT
);

ALTER TABLE content_item
    ADD CONSTRAINT content_item_current_version_fk
    FOREIGN KEY (current_content_version_id, content_item_id)
    REFERENCES content_version(content_version_id, content_item_id)
    DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE content_variant (
    content_variant_id                 uuid PRIMARY KEY,
    workspace_id                       uuid NOT NULL REFERENCES workspace(workspace_id) ON DELETE RESTRICT,
    content_item_id                    uuid NOT NULL,
    format                             text NOT NULL,
    platform_target                    text NULL,
    language                           text NULL,              -- OPEN OD-04
    treatment                          text NULL,              -- OPEN OD-04
    variant_profile_version_id         uuid NULL,              -- Contract 11 ref; OPEN OD-04
    lifecycle_status                   text NOT NULL,
    current_artifact_version_id        uuid NULL,              -- Part 7 ref; no FK; OPEN OD-04/OD-05
    created_by_actor_id                uuid NOT NULL,
    schema_version                     text NOT NULL,
    record_version                     bigint NOT NULL DEFAULT 1,
    created_at                         timestamptz NOT NULL,
    updated_at                         timestamptz NOT NULL,
    FOREIGN KEY (content_item_id, workspace_id)
        REFERENCES content_item(content_item_id, workspace_id) ON DELETE RESTRICT
);

CREATE TABLE workflow_run (
    workflow_run_id                    uuid PRIMARY KEY,
    workspace_id                       uuid NOT NULL REFERENCES workspace(workspace_id) ON DELETE RESTRICT,
    workflow_definition_version_id     uuid NOT NULL,          -- Contract 10 ref; no FK in WP-1-A
    workflow_type                      text NOT NULL,
    subject_entity_type                text NOT NULL,
    subject_entity_id                  uuid NOT NULL,
    lifecycle_status                   text NOT NULL,
    correlation_id                     uuid NOT NULL,
    started_at                         timestamptz NULL,
    completed_at                       timestamptz NULL,
    created_by_actor_id                uuid NOT NULL,
    schema_version                     text NOT NULL,
    record_version                     bigint NOT NULL DEFAULT 1,
    created_at                         timestamptz NOT NULL,
    updated_at                         timestamptz NOT NULL,
    UNIQUE (workflow_run_id, workspace_id)
);

CREATE TABLE workflow_task (
    workflow_task_id                   uuid PRIMARY KEY,
    workspace_id                       uuid NOT NULL,
    workflow_run_id                    uuid NOT NULL,
    task_type                          text NOT NULL,
    task_definition_version            text NOT NULL,
    subject_entity_type                text NULL,
    subject_entity_id                  uuid NULL,
    lifecycle_status                   text NOT NULL,
    created_by_actor_id                uuid NOT NULL,
    schema_version                     text NOT NULL,
    record_version                     bigint NOT NULL DEFAULT 1,
    created_at                         timestamptz NOT NULL,
    updated_at                         timestamptz NOT NULL,
    CHECK ((subject_entity_type IS NULL) = (subject_entity_id IS NULL)),
    FOREIGN KEY (workflow_run_id, workspace_id)
        REFERENCES workflow_run(workflow_run_id, workspace_id) ON DELETE RESTRICT,
    UNIQUE (workflow_task_id, workspace_id)
);

CREATE TABLE workflow_task_dependency (
    workflow_task_id                   uuid NOT NULL,
    depends_on_task_id                 uuid NOT NULL,
    workspace_id                       uuid NOT NULL,
    PRIMARY KEY (workflow_task_id, depends_on_task_id),
    CHECK (workflow_task_id <> depends_on_task_id),
    FOREIGN KEY (workflow_task_id, workspace_id)
        REFERENCES workflow_task(workflow_task_id, workspace_id) ON DELETE RESTRICT,
    FOREIGN KEY (depends_on_task_id, workspace_id)
        REFERENCES workflow_task(workflow_task_id, workspace_id) ON DELETE RESTRICT
);

CREATE TABLE workflow_task_ref (
    workflow_task_ref_id               uuid PRIMARY KEY,
    workspace_id                       uuid NOT NULL,
    workflow_task_id                   uuid NOT NULL,
    direction                          text NOT NULL CHECK (direction IN ('input', 'output')),
    entity_type                        text NOT NULL,
    entity_id                          uuid NOT NULL,
    entity_version                     text NULL,
    role                               text NULL,
    created_at                         timestamptz NOT NULL,
    FOREIGN KEY (workflow_task_id, workspace_id)
        REFERENCES workflow_task(workflow_task_id, workspace_id) ON DELETE RESTRICT
);

CREATE TABLE relationship (
    relationship_id                    uuid PRIMARY KEY,
    workspace_id                       uuid NOT NULL REFERENCES workspace(workspace_id) ON DELETE RESTRICT,
    source_entity_type                 text NOT NULL,
    source_entity_id                   uuid NOT NULL,
    relationship_type                  text NOT NULL,
    target_entity_type                 text NOT NULL,
    target_entity_id                   uuid NOT NULL,
    valid_from                         timestamptz NOT NULL,
    valid_to                           timestamptz NULL,
    created_by_actor_id                uuid NOT NULL,
    schema_version                     text NOT NULL,
    created_at                         timestamptz NOT NULL,
    CHECK (valid_to IS NULL OR valid_to > valid_from)
);

CREATE TABLE external_reference (
    external_reference_id              uuid PRIMARY KEY,
    workspace_id                       uuid NOT NULL REFERENCES workspace(workspace_id) ON DELETE RESTRICT,
    source_system                      text NOT NULL,
    external_entity_type               text NOT NULL,
    external_id                        text NOT NULL,
    target_entity_type                 text NOT NULL,
    target_entity_id                   uuid NOT NULL,
    external_uri                       text NULL,
    observed_at                        timestamptz NOT NULL,
    created_by_actor_id                uuid NOT NULL,
    schema_version                     text NOT NULL,
    created_at                         timestamptz NOT NULL,
    UNIQUE (workspace_id, source_system, external_entity_type, external_id)
);
```

### 6.3 Nullability and required-field rules

- All IDs, `workspace_id`, `schema_version`, `created_at`, `created_by_actor_id` and `lifecycle_status` are NOT NULL.
- `title`, `editorial_payload`, `content_sha256`, `language`, `treatment`, `platform_target`, `variant_profile_version_id`, `current_artifact_version_id`, `started_at`, `completed_at`, `valid_to` and `external_uri` are nullable pending owner decisions.
- `brand_id` is NOT NULL by recommendation; owner should confirm whether brandless content is permitted.
- `origin_opportunity_id` is nullable; not every ContentItem comes from an opportunity/idea.
- `current_content_version_id` is nullable only before the first version; a committed ContentItem with no version is not publishable.
- `workflow_run.subject_entity_type/id` are NOT NULL; `workflow_task.subject_entity_*` are nullable for non-subject tasks.

### 6.4 Keys, uniqueness and indexes

| Constraint / index | Purpose |
|---|---|
| PK on every UUID | Canonical identity |
| `UNIQUE (content_item_id, version_number)` | One version number per parent |
| `UNIQUE (content_version_id, content_item_id)` | Composite target for current-version FK |
| `UNIQUE (content_item_id, workspace_id)` | Composite workspace-scoped FK target |
| `UNIQUE (workflow_run_id, workspace_id)` | Composite workspace-scoped FK target |
| `UNIQUE (workflow_task_id, workspace_id)` | Composite dependency/ref FK target |
| `UNIQUE (workspace_id, source_system, external_entity_type, external_id)` | Namespaced external identity |
| `content_item(workspace_id, lifecycle_status)` | Workspace listing |
| `content_version(content_item_id)` | Version history |
| `content_variant(content_item_id)` | Variant listing |
| `workflow_run(workspace_id, lifecycle_status)` | Workflow listing |
| `workflow_task(workflow_run_id)` | Task listing |
| `workflow_task_dependency(depends_on_task_id)` | Reverse dependency lookup |
| `workflow_task_ref(workflow_task_id, direction)` | Input/output refs |
| `relationship(workspace_id, source_entity_type, source_entity_id)` | Source lookup |
| `relationship(workspace_id, target_entity_type, target_entity_id)` | Target lookup |
| FK indexes on all referencing columns | Join/delete performance |

No partitioning, partial indexes, GIN/JSONB indexes or database-specific features are proposed in WP-1-A. They may be added after measured need.

### 6.5 Ownership and workspace isolation

- `workspace` is the isolation root; every tenant table carries `workspace_id`.
- Composite FKs prevent cross-workspace parent/child links:
  - `content_version → content_item`,
  - `content_variant → content_item`,
  - `workflow_task → workflow_run`,
  - dependencies/refs → `workflow_task`.
- Cross-domain references have **no local FK**:
  - `brand_id` → Contract 03,
  - `origin_opportunity_id` → Contract 02,
  - `owner_actor_id` / `created_by_actor_id` → identity/security,
  - `variant_profile_version_id` / `workflow_definition_version_id` → Contract 10/11,
  - `current_artifact_version_id` → Part 7/WP-4.
- Cross-domain references are validated by the owning service/read model before commit; reachability does not grant authorization.
- Each table has one owner; no consumer writes another domain’s table.
- `relationship` is polymorphic: the owning service validates source/target existence, type and workspace. No generic FK can enforce every target type.

### 6.6 Deletion and immutability

| Table | Deletion / mutation rule |
|---|---|
| `workspace` | Delete restricted while any child exists; no cascade |
| `content_item` | Delete restricted while versions/variants/relationships exist; lifecycle mutation only |
| `content_version` | Append-only; no UPDATE/DELETE; correction creates a new version |
| `content_variant` | Lifecycle mutable; no physical delete when referenced; exact archival policy OD-07 |
| `workflow_run` | History preserved; delete restricted; no cascade |
| `workflow_task` | History preserved; delete restricted; dependency/ref rows restrict |
| `workflow_task_dependency` | Delete only through explicit task cleanup policy; no cascade |
| `workflow_task_ref` | Delete only through explicit task cleanup policy; no cascade |
| `relationship` | Close with `valid_to`; do not delete historical links |
| `external_reference` | Preserve mapping; no delete when target/history depends on it |
| Artifact/ArtifactVersion | Not in WP-1-A; WP-4 owns immutability |

No `ON DELETE CASCADE` or `ON UPDATE CASCADE` is proposed. `ON UPDATE RESTRICT` is implicit because IDs are immutable. Archival/tombstone columns are deferred (OD-07).

### 6.7 Transaction boundaries

1. **Content creation:** insert `content_item` (current pointer NULL) → insert first `content_version` → update `current_content_version_id`; one transaction; deferrable composite FK.
2. **Variant creation:** validate parent in same workspace → insert `content_variant`; one transaction.
3. **Workflow creation:** insert `workflow_run` → insert `workflow_task` rows → insert dependencies/refs; one transaction; cycle check inside the transaction.
4. **Relationship creation:** validate source and target in the owning service → insert `relationship`; one transaction; no cross-domain writes.
5. **External reference creation:** validate target → insert mapping; one transaction; no distributed transaction.
6. **State change:** update mutable row with `WHERE record_version = expected` → append audit/outbox record in the same transaction. WP-1 defines the boundary; WP-2 implements the durable outbox.
7. **No transaction spans** a provider/network call, file transfer or external side effect.

Isolation recommendation: `READ COMMITTED` plus unique constraints and conditional updates; use `SERIALIZABLE` only for multi-row invariants that cannot be expressed as constraints. Exact isolation level is an owner/DBA decision under OD-08/OD-10.

---

## 7. Database and migration tooling options

| Option | Components | Free-first | Pros | Cons |
|---|---|---|---|---|
| **A (recommended)** | PostgreSQL 16 + SQLAlchemy 2.x + Alembic | Yes (local Docker/Postgres, open source) | Matches ADR-002; mature migrations; typed models; strong test ecosystem | Adds dependencies; ORM can hide SQL; container/runtime setup |
| **B** | PostgreSQL + psycopg 3 + plain SQL migrations (dbmate/goose or small runner) | Yes | Explicit SQL; fewer abstractions; easy schema review | Manual ordering/rollback; less model tooling; custom runner risk |
| **C** | SQLite + SQLAlchemy/Alembic | Yes, zero service | Fast local tests; no server | SQLite differs from PostgreSQL in types, constraints, concurrency, JSONB, DDL; not acceptance-grade for ADR-002 |
| **D** | Managed PostgreSQL free tier | Conditionally | Less operations | Paid/limited tiers can create billing exposure; violates free-first unless explicitly approved |

**Recommendation:** Option A for contract fidelity and migration discipline, using a local free PostgreSQL instance. Option B if dependency minimization is required. Option C only as a fast test adapter, never the sole WP-1 acceptance database. Option D only with explicit owner cost approval.

Migration tooling must be approved under OD-08 before any dependency is added.

---

## 8. WP-1 acceptance tests and migration safety

### 8.1 Acceptance test matrix

| ID | Test | Expected |
|---|---|---|
| WP1-AT-01 | Schema contract: tables, columns, types, nullability, PK/FK/unique/indexes match the approved schema | Exact match |
| WP1-AT-02 | UUIDv7 IDs are immutable; duplicate ID insert rejected | Rejected |
| WP1-AT-03 | `UNIQUE (content_item_id, version_number)` | Duplicate version rejected |
| WP1-AT-04 | `current_content_version_id` points to a version of the same ContentItem | Cross-parent pointer rejected |
| WP1-AT-05 | Cross-workspace parent/child references | Rejected |
| WP1-AT-06 | Cross-domain reference validation (brand, actor, opportunity, artifact) | Invalid/missing refs rejected by owner service; no local FK |
| WP1-AT-07 | Relationship source/target existence, type and workspace | Valid accepted; invalid/cross-workspace rejected |
| WP1-AT-08 | External reference uniqueness within namespace | Duplicate rejected |
| WP1-AT-09 | Workflow task dependency and cycle rejection | Cycle rejected; valid graph accepted |
| WP1-AT-10 | No cascade delete; restricted parent delete | Child rows preserved; delete rejected |
| WP1-AT-11 | Optimistic concurrency on mutable rows | Stale `record_version` update conflicts |
| WP1-AT-12 | Transaction rollback on failed multi-row write | No partial canonical state |
| WP1-AT-13 | Migration from empty DB; forward recovery; repeatable test setup | Schema matches; recovery documented |
| WP1-AT-14 | Data-dictionary traceability for every table/field | Every field maps to source or owner decision |
| WP1-AT-15 | Preservation: only approved paths changed | No unrelated file changes |

These are proposed acceptance criteria, not executed tests.

### 8.2 Migration safety requirements

- Additive, versioned migrations only; no destructive DDL in WP-1-A.
- One logical change per migration; no data backfill in schema migrations.
- PostgreSQL transactional DDL where supported; advisory lock for concurrent runners.
- Test from an empty synthetic database and from the previous schema revision.
- Backup/restore rehearsal before applying to any non-synthetic database.
- Forward-recovery plan required; down migration only for local test if safe.
- Record migration ID, schema hash, command, duration, result and limitations.
- No production data, real user content, credentials or external side effects.
- No dependency installation or migration execution without implementation authorization.

---

## 9. P0 documentation gaps

1. **No frozen WP-1 detailed contract**: S8 §4.1 disposition is OPEN; S13/S14 confirm contract freeze pending.
2. **Data-dictionary gap**: `ContentVersion`, `ContentVariant` and `WorkflowTask` are not fully defined in S4; S1 uses them.
3. **Naming conflict**: `Workflow`/`workflow_id` vs `WorkflowRun`/`workflow_run_id`; `WorkflowTask` vs `Task`.
4. **Artifact boundary**: S1 includes Artifact/ArtifactVersion; S2 recommends reference-only; WP-4 owns implementation.
5. **Job boundary**: whether WP-1-A persists a minimal Job is unresolved.
6. **Deletion/retention**: exact FK actions and archival/tombstone mechanics unresolved; CF-06 exact wording is referenced but not reproduced in S7.
7. **DB/migration tooling**: unselected; S2 defers; ADR-002 requires PostgreSQL-compatible.
8. **Physical schema**: types, nullability, indexes and constraints unapproved.
9. **Implementation authorization**: explicitly NOT GRANTED (S8/S13/S14/S15).
10. **Sprint 01 work order**: no named package, path allowlist, owner/reviewer, preservation manifest or isolated-worktree authorization in the repository.

---

## 10. Readiness and status

- **CONTRACT READY: NO — NOT READY FOR FREEZE.**
- The logical model is coherent enough for owner decision review, but the 11 decisions in `docs/workstream-review/wp1/P0_WP1_OWNER_DECISION_REGISTER.md` must be dispositioned first.
- **Remaining owner decisions:** OD-01–OD-11.
- **Implementation authorization:** NOT GRANTED.
- **Recommended next action:**
  1. Owner dispositions on OD-01–OD-11.
  2. Produce WP-1 contract candidate 0.4 and a physical schema appendix incorporating the accepted dispositions.
  3. Record the accepted baseline/version and exact source references.
  4. Issue a separate bounded WP-1-A implementation authorization with paths, tests, owner and stop conditions.

No implementation, migration, test execution or database mutation was performed.

---

## 11. Source reference index

| Ref | Path / section |
|---|---|
| S1 | `content studio os file and structure/Decision based Propesed/04(WP_1 to 6)/WP1/NEXTDECODE_P0_WP1_Final_Schema_Contract_Candidate_0.3.md` §4, §6, §8, §9, §11 |
| S2 | `content studio os file and structure/Decision based Propesed/04(WP_1 to 6)/WP1/NEXTDECODE_P0_WP1_Design_Resolution_Record_0.2.md` §2–§5 |
| S3 | `content studio os file and structure/Decision based Propesed/04(WP_1 to 6)/WP1/NEXTDECODE_P0_WP1_Canonical_Domain_Persistence_Boundary_0.1.md` §5, §7, §10 |
| S4 | `content studio os file and structure/Decision based Propesed/01(Prod&Arct)/02review for 1 to 12/NEXTDECODE_Canonical_Data_Dictionary_Entity_Ownership_Registry_1.0.md` §2, §5, §15, §17, §20, §23 |
| S5 | `content studio os file and structure/NEXTDECODE_Canonical_Contracts_Pack_1.0.md` §1.1, §1.3, §1.4, §3.2–§3.5 |
| S6 | `content studio os file and structure/NEXTDECODE_Accepted_P0_Architecture_Decision_Baseline_1.0.md` ADR-001/002/004/006/010 |
| S7 | `content studio os file and structure/Decision based Propesed/02(Artfact_01 to 12)/04WPO/NEXTDECODE_Artifact_08_v1.2_Consolidated_Freeze_Candidate.md` §3 CF-01/CF-02/CF-24 |
| S8 | `content studio os file and structure/Decision based Propesed/04(WP_1 to 6)/NEXTDECODE_P0_Owner_Review_Contract_Freeze_Decision_Record_0.1.md` §4.1, §7 |
| S9 | `content studio os file and structure/Decision based Propesed/05(P0_Impementation_plan)/01/NEXTDECODE_P0_02_P0_Implementation_Master_Plan.md` §2, §4, §5 |
| S10 | `content studio os file and structure/Decision based Propesed/05(P0_Impementation_plan)/01/NEXTDECODE_P0_04_Engineering_Work_Orders_WP1_to_WP6.md` WP-1 |
| S11 | `content studio os file and structure/Decision based Propesed/05(P0_Impementation_plan)/01/NEXTDECODE_P0_05_P0_Acceptance_Evidence_and_Release_Gates.md` §2–§5 |
| S12 | `content studio os file and structure/Decision based Propesed/02(Artfact_01 to 12)/NEXTDECODE_API_Event_Contract_Standard_1.0.md` §5.1, §7.6, §10.2 |
| S13 | `content studio os file and structure/Decision based Propesed/05(P0_Impementation_plan)/NEXTDECODE_P0_Batch13_Implementation_Readiness_Controlled_Execution_Package.docx` §2, §13, §17 |
| S14 | `content studio os file and structure/Decision based Propesed/05(P0_Impementation_plan)/NEXTDECODE_P0_Batch15_Source_Reconciliation_Contract_Closure_Dossier.docx` status/authorization |
| S15 | `content studio os file and structure/NEXTDECODE_P0_Implementation_Authorization_Brief_1.0.md` §10–§12 |

---

## 12. Final status

- **CONTRACT READY: NO — NOT READY FOR FREEZE.**
- **Remaining owner decisions:** WP1-OD-01 through WP1-OD-11.
- **Implementation authorization:** NOT GRANTED.
- **Recommended next action:** Owner dispositions on the decision register, then a final WP-1 contract candidate (0.4) and physical schema appendix, then a separate bounded WP-1-A implementation authorization.
