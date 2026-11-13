# NEXTDECODE — Batch 12 Source Inventory & Agent–Worker Contract Reconciliation Handoff

**Document ID:** ND-P0-B12-AGW-002  
**Version:** 0.1  
**Prepared:** 3 November 2026  
**Status:** Working handoff — source reconciliation and owner review required  
**Authority:** Existing source documents only; this handoff makes no new owner decision  
**Implementation authorization:** NOT GRANTED  
**Canonical-document update:** NOT PERFORMED

## 1. File classification

| Field | Classification |
|---|---|
| Project | NEXTDECODE Content OS |
| Lifecycle phase | P0 — Architecture, Contracts & Governance Closure |
| Phase stage | Contract reconciliation / pre-implementation preparation |
| Part | Part 5 — Agent Contracts & Orchestration (cross-part interface work) |
| Primary work package | WP-01 — Authoritative Source Inventory (Batch 12 continuation) |
| Secondary work package | WP-AGW — Agent–Worker Interface Closure |
| Batch lineage | Batch 12 source verification; Batch 17 state-machine catalogue; Batch 18 API/Event schema pack |
| Domain focus | Agent orchestration, durable execution, worker trust, artifact handoff, central governance |
| System layer | Shared contracts and integration boundaries |
| Backend / frontend | **Shared contract, backend-led.** Backend/API/orchestrator/worker interfaces are primary. Frontend work is limited to later contract-aligned consumers; UI must not define domain rules. |
| Primary consumers | Documentation agent, backend/API architect, orchestration engineer, worker-runtime engineer, independent reviewers |
| Change type | Documentation-only reconciliation proposal |
| Storage category | `P0/04-contracts-and-interfaces/agent-worker` |
| Related handoff | `NEXTDECODE_AGENT_WORKER_CONTRACT_CLOSURE_HANDOFF_ND-P0-AGW-001.md` |
| Supersedes | Nothing |

### Recommended storage taxonomy

This is a proposed filing convention, not a claim that these folders already exist.

```text
NEXTDECODE_Content_OS/
├── 00-governance-and-owner-decisions/
├── 01-product-and-scope/
├── 02-architecture-and-ADRs/
├── 03-domain-model-and-data-dictionary/
├── 04-contracts-and-interfaces/
│   ├── api-events/
│   ├── agent-worker/
│   ├── workflow-jobs/
│   ├── worker-registry/
│   ├── artifacts/
│   └── governance-approval-rights/
├── 05-backend/
├── 06-frontend/
├── 07-integration-and-adapters/
├── 08-quality-security-and-testing/
├── 09-release-and-operations/
├── 10-evidence-and-audit/
└── 99-archive-and-superseded/
```

**Filing rules**
1. File by primary responsibility, not by the team that created it.
2. Cross-cutting contracts belong in `04-contracts-and-interfaces`; implementation plans belong in backend/frontend/integration folders.
3. Owner decisions belong in `00-governance-and-owner-decisions`, with references from affected documents.
4. Test evidence belongs in `08-quality-security-and-testing` or `10-evidence-and-audit`.
5. Never overwrite an approved/reviewed version; create a new version and record what it supersedes.
6. Keep draft, proposed, accepted, implementation evidence and independent verification visibly distinct.

### Standard header for future files

```yaml
project: NEXTDECODE Content OS
document_id: ND-[PHASE]-[PART]-[TOPIC]-[SEQUENCE]
version: 0.1
status: Draft | Working | Proposed | Owner review required | Accepted | Superseded
phase: P0
phase_stage: Architecture | Contract closure | Implementation | Integration | Verification | Release
part: Part [number] — [name]
batch: Batch [number, if applicable]
work_package: WP-[number/name]
domain_owner: [canonical owning domain]
system_layer: Backend | Frontend | Shared contract | Data | Infrastructure | Governance
workstream: Backend | Frontend | Shared | Cross-functional
primary_consumers: [roles/agents]
dependencies: [document IDs and versions]
authority_basis: [accepted decision/source]
implementation_authorization: NOT GRANTED unless separately recorded
repository_authorization: NOT GRANTED unless separately recorded
external_side_effects: NOT AUTHORIZED unless separately recorded
supersedes: [document ID/version or None]
storage_category: [taxonomy path]
```

**Filename convention:** `NEXTDECODE_[PHASE]_[PART-or-WP]_[TOPIC]_[ARTIFACT-TYPE]_v[MAJOR.MINOR].ext`

Examples:
- `NEXTDECODE_P0_WP2_Durable_Job_Contract_Design_v0.2.md`
- `NEXTDECODE_P0_Part5_Agent_Task_Envelope_Spec_v0.2.md`
- `NEXTDECODE_P0_SHARED_API_Event_Contract_Review_v0.2.md`
- `NEXTDECODE_P0_WP6_Contract_Conformance_Test_Plan_v0.1.md`

## 2. Purpose

Continue Batch 12 source intake and the Agent–Worker closure handoff ND-P0-AGW-001.

The receiving agent must establish controlling source versions; reconcile four Agent–Worker interface families inside the existing Batch 18 structure; preserve domain ownership; classify source-defined vs proposed/open/conflicted details; prepare field-level schemas, traceability, tests and an owner-decision sheet; and identify implementation dependencies without beginning implementation.

**Do not create a parallel API standard.** Batch 18 remains the target specification pack. This file is a navigation and reconciliation handoff only.

## 3. Source inventory and authority assessment

The following files were located in the accessible Library. Statuses below reflect what each document says about itself; a newer timestamp alone does not prove supersession.

| Source document | Located status/version | Role | Treatment |
|---|---|---|---|
| `NEXTDECODE_Accepted_P0_Architecture_Decision_Baseline_1.0.md` | v1.0; owner decisions recorded; 31 Oct 2026 | High-level ADR-001–010 baseline | Evidence of accepted high-level decisions; verify owner-decision provenance |
| `NEXTDECODE_Architecture_Decision_Records_Pack_1.0.md` | v1.0; Draft for owner review; ADR records proposed/open | Detailed ADR records | Status conflict with accepted baseline; do not silently revoke accepted decisions |
| `NEXTDECODE_Architecture_Decision_Register_1.0.md` | v1.0; proposed register; ADR-001–015 pending, ADR-016–018 deferred | ADR tracking | Reconcile with baseline and original owner evidence |
| `NEXTDECODE_Artifact_08_P0_Detailed_Contract_Freeze_Open_Decisions_Closure_1.0.md` | v1.0; owner review required | Detailed contract freeze | Explicitly says detailed freeze and implementation authorization are not granted |
| `NEXTDECODE_Artifact_10_P0_Owner_Review_Authorization_Pack_1.0.md` | v1.0; owner review pack awaiting review | Decision/authorization register | Use to locate open decisions; do not infer approval |
| `NEXTDECODE_Canonical_Data_Dictionary_Entity_Ownership_Registry_1.0.md` | v1.0; working architecture standard, documentation only | Entity identity and ownership | Logical model, not final SQL/ORM/migration/API implementation |
| `NEXTDECODE_API_Event_Contract_Standard_1.0.md` | v1.0; architecture specification, documentation only | Controlling interface principles | Query/command/event separation, versioning, ownership and validation |
| `NEXTDECODE_Unified_Lifecycle_State_Transition_Standard_1.0.md` | v1.0; architecture specification, documentation only | State-machine principles | Preserve owner-owned state, expected-version checks, audit and unknown-outcome handling |
| `NEXTDECODE_Canonical_Contracts_Pack_1.0.md` | v1.0; proposed baseline, approval pending | Cross-contract context | Candidate only where owner freeze is absent |
| `NEXTDECODE_Artifact_08_Consolidated_Owner_Decision_Record_Contract_Freeze_Closure_1.0.md` | v1.0; located; duplicate copies also found | Owner-decision evidence | Identify authoritative copy/hash and inspect full disposition |
| `NEXTDECODE_P0_Batch12_Authoritative_Source_Verification_Contract_Reconciliation.docx` | Batch 12 | Provenance/source-intake method | Capture source identity, approval evidence, dates, hash, coverage and limitations |
| `NEXTDECODE_P0_Batch17_State_Machine_Transition_Catalogue.docx` | Batch 17; detailed candidate, owner freeze pending | Domain lifecycle transitions | Candidate detail, not proof of code behavior or frozen enums |
| `NEXTDECODE_P0_Workflow_Job_Contract_Reconciliation_0.1.md` | v0.1; design reconciliation, owner review required | WP-1/WP-2 and workflow/job cardinality | Candidate; detailed freeze and implementation authorization not granted |
| `NEXTDECODE_P0_Batch18_API_Event_Schema_Specification_Pack.docx` | Batch 18; detailed interface candidate, owner freeze pending | Primary target | Proposed changes remain in this pack; example routes/payloads are illustrative unless approved |
| `NEXTDECODE_AGENT_WORKER_CONTRACT_CLOSURE_HANDOFF_ND-P0-AGW-001.md` | v0.1 handoff; owner freeze pending | Earlier Agent–Worker handoff | Continue its scope; it is not source authority |

### Retrieval limitations
- Notion connector search did not provide usable authoritative project evidence; the connected search path reported a Business-access requirement and general page search returned unrelated results. Do not claim the Notion workspace was successfully searched.
- Library search located the files above. Complete provenance audit, hash comparison and duplicate resolution remain pending.
- The authoritative master handoff register was not confirmed in the accessible source set. Do not claim it has been updated.
- The full owner-decision trail for ADR status and rights vocabulary conflicts remains to be established.

## 4. Material conflicts — do not silently resolve

### 4.1 ADR acceptance status
The Accepted P0 Architecture Decision Baseline 1.0 says ADR-001 through ADR-010 are accepted (10/10). The ADR Records Pack and ADR Register 1.0 still label records proposed/pending and show a broader pending register.

**Required handling:** Record a source-status/provenance conflict. Locate owner decision evidence, dates and supersession relationship. Do not downgrade accepted decisions or promote pending ADRs by inference.

### 4.2 Rights-state vocabulary
- Accepted ADR baseline ADR-009: `CLEARED`, `RESTRICTED`, `PENDING_VERIFICATION`, `PROHIBITED`, `UNKNOWN`.
- Batch 17 and later CF-20 / ND-GOV-005 material: `UNKNOWN`, `PENDING_REVIEW`, `CLEARED`, `RESTRICTED`, `EXPIRED`, `REVOKED`, `DENIED`.
- ND-GOV-005 says local `reuse_rights: permitted` is not a canonical rights state and must not automatically map to `CLEARED`.

**Required handling:** Preserve both vocabularies with source attribution. Route reconciliation to Contract 07 / CF-20 owner. Do not merge, rename, translate or map values without explicit owner disposition.

### 4.3 High-level ADR acceptance is not detailed contract freeze
Artifact 08 and Batch 18 distinguish accepted high-level ADRs from detailed contract approval.

**Required handling:** ADR-001–010 acceptance does not automatically approve every field, endpoint, enum, timeout, schema or transition in Batches 12/17/18.

### 4.4 Duplicate owner-decision files
More than one Library copy of the consolidated Artifact 08 owner-decision record was found, including a duplicate-suffixed copy and a text extraction.

**Required handling:** Compare document control metadata, content, source identity and hashes. Identify one authoritative source only when evidence supports it. Do not delete or overwrite duplicates.

## 5. Ownership and backend/frontend mapping

| Area | Canonical owner/source boundary | Work package | Primary impact |
|---|---|---|---|
| Canonical Actor identity | Identity & Security | Identity dependency | Backend identity/auth context; frontend consumes identity |
| Agent definition, identity, immutable version and capabilities | Contract 10 / Part 5 | Part 5 / AGW | Backend/orchestrator; frontend may display metadata later |
| Worker identity, trust, eligibility, credentials and capability verification | WP-3 | WP-3 | Backend/worker runtime; admin UI only if separately scoped |
| Workflow, WorkflowTask, Job, JobAttempt, Lease, dispatch, retry, recovery and execution state | WP-2 | WP-2 | Backend/orchestrator/queue/worker |
| Agent task execution and outcome reporting | Agent Handler under Part 5 | Part 5 / AGW | Backend/runtime |
| Artifact identity, immutable versions, provenance, integrity and transfer | WP-4 | WP-4 | Backend/storage/adapters; frontend consumes references |
| Quality, rights, approval and protected-action authorization | Contract 07 / WP-5 | WP-5 | Backend policy enforcement; frontend cannot grant permission |
| Query/command/event envelopes and compatibility | API/Event Standard 1.0; Batch 18 candidate | Shared interface | Backend-first shared contract; frontend is typed consumer |
| Conformance, replay, stale-version, duplicate-delivery and unknown-outcome tests | WP-6 | WP-6 | Shared tests, primarily backend/API integration |

**Ownership invariant:** Consumers request changes through the owning domain's command interface. They do not write directly into another domain's canonical state. Events communicate committed facts; they are not authorization.

## 6. Four Agent–Worker interface families to reconcile in Batch 18

Do not invent final route names, event names, JSON Schema constraints or numeric policy values.

### 6.1 Assignment issuance
The orchestrator issues a bounded assignment to an eligible worker. Reconcile:
- canonical `job_id` and `attempt_id` from WP-2;
- canonical `worker_id` from WP-3;
- `agent_id` and immutable `agent_version_id` where applicable, owned by Contract 10;
- assignment identity and lease/fencing context, with ownership and field names confirmed against WP-2/WP-3;
- required capabilities/resource constraints;
- expiry/deadline and bounded task input/reference;
- WP-4 artifact/input references;
- correlation/causation and schema version;
- no implicit permission for protected external actions.

### 6.2 Assignment acknowledgement or rejection
The worker acknowledges/rejects a specific assignment after authenticating itself and validating current eligibility.
- Bind to exact assignment, job, attempt, worker and current lease/fencing generation.
- Reject expired, revoked, mismatched, stale or unauthorized assignments.
- Return structured machine-readable rejection reasons.
- Acknowledgement is not task completion.
- A stale worker must not continue after lease loss or reassignment.
- Exact enums/error codes remain open unless found in an accepted source.

### 6.3 Result submission and acceptance
The worker/Agent Handler submits a result for the exact attempt; the orchestrator validates before committing canonical state.
- Bind to job, attempt, worker, lease/fencing generation and agent/version as applicable.
- Carry structured outcome, timestamps, correlation/causation and schema version.
- Reference WP-4 artifact IDs/versions/manifests, not binary payloads in job state.
- Validate artifact ownership, provenance, integrity and transfer completion under WP-4.
- Distinguish worker-reported success from canonical accepted completion.
- Reject/quarantine stale, duplicate, mismatched or unverifiable results.
- Apply WP-2 idempotency and expected-state-version rules.

### 6.4 Failure reporting and recovery signalling
The worker reports observed failure/inability to continue; the orchestrator/WP-2 decides canonical workflow/job/attempt transitions.
- Distinguish execution failure, worker loss, lease expiry, cancellation, policy denial, artifact failure, retryable/permanent error and unknown external outcome.
- Lease expiry is not proof that the job failed.
- Keep agent outcome, job/attempt state and worker/lease state separate.
- Retry/reassignment creates a new attempt under WP-2 rules.
- Earlier-attempt results cannot overwrite a later attempt.
- Uncertain external side effects require reconciliation, not blind retry.

### 6.5 Lease renewal, expiry and fencing
Reconcile with WP-2:
- one authoritative lease owner;
- monotonic fencing/lease-generation semantics and scope;
- stale generation rejection;
- worker stops protected work after lease loss;
- renewal only while identity, assignment and lease remain valid;
- no invented heartbeat, TTL, retry or timeout values.

## 7. Proposed identity linkage — owner review required

Earlier handoff proposed `AgentIdentity.actor_ref` → canonical Actor reference.

- Actor identity remains owned by Identity & Security.
- Agent identity/definition/version remains owned by Contract 10.
- `agent_id` remains an agent-domain identifier.
- `agent_version_id` remains immutable.
- Worker identity remains distinct and is owned by WP-3.

**Status:** Proposal only. Confirm reference type, field ownership, uniqueness and lifecycle with Identity & Security and Contract 10 before freezing. Do not implement this proposed field based only on this handoff.

## 8. Required agent deliverables

1. **Source provenance matrix:** exact filename/version/status, owner/approval evidence, dates, identity/hash where available, scope, limitations and supersession.
2. **Batch 18 change proposal:** section-by-section proposed additions/revisions for the four interface families and lease/fencing.
3. **Field-level interface matrix:** each field classified `SOURCE-DEFINED`, `PROPOSED`, `OPEN`, `DEFERRED` or `CONFLICTED`, with owner and source.
4. **Ownership/traceability matrix:** map each field/behavior to WP-2, WP-3, Part 5, Contract 10, WP-4, WP-5, Data Dictionary and API/Event Standard.
5. **Owner decision sheet:** only genuine owner decisions, with options, impact and exact source conflict. Do not ask the owner to decide already-settled matters.
6. **Conformance test plan:** stale assignment, wrong worker, expired lease, stale fencing generation, duplicate acknowledgement/result, superseded-attempt result, invalid artifact reference, unauthorized protected action and unknown external outcome.
7. **Change log/document-control report:** preserve old versions; distinguish proposed from executed changes.
8. **Implementation dependency map:** backend/frontend work that becomes eligible only after owner freeze and separate implementation authorization.

## 9. Acceptance criteria

This documentation work is complete only when:
- every relied-upon source is identified by exact filename, version and stated status;
- ADR status and rights vocabulary conflicts are recorded, not silently reconciled;
- every interface field has a source/owner and status classification;
- assignment, acknowledgement/rejection, result, failure/recovery and lease/fencing are covered;
- domain ownership is preserved;
- proposed tests cover duplicate, stale, unauthorized and unknown-outcome cases;
- unresolved decisions are assigned to the correct owner;
- Batch 18 changes are proposed as a tracked revision, not represented as accepted;
- no implementation, repository, Git, provider, deployment or publishing action is claimed.

## 10. Authorization boundary

**Permitted:** Read listed documentation sources; compare versions/content; prepare source inventory; draft a proposed Batch 18 revision/change proposal; prepare schemas marked proposed/open; produce traceability, decision and test-planning documents.

**Not authorized:**
- repository inspection or modification;
- code/configuration/workflow/database changes;
- running tests, production workflows or live pipeline executions;
- assigning or launching agents/workers;
- integration, merge, commit, push or destructive Git/file operations;
- provider activation, credential/permission changes or paid services;
- deployment, production generation, external upload or public publishing;
- changing canonical owner decisions, frozen contracts or source registers;
- claiming the handoff register or canonical documents were updated without verified evidence.

Separate explicit owner authorization is required for any prohibited action.

## 11. Recommended sequence

| Step | Work item | Phase / part | Layer | Gate |
|---|---|---|---|---|
| 1 | Complete Batch 12 provenance and duplicate-source reconciliation | P0 / governance + architecture | Shared documentation | Evidence-based inventory |
| 2 | Reconcile Agent–Worker families in Batch 18 | P0 / Part 5 + WP-2/WP-3 | Shared contract, backend-led | Owner review |
| 3 | Resolve genuine ADR-status and rights-vocabulary conflicts | P0 / governance (ADR / Contract 07) | Shared governance | Explicit owner disposition |
| 4 | Freeze detailed schemas and interface decisions | P0 / API/Event + owning domains | Shared contract | Formal owner freeze |
| 5 | Produce backend implementation plan and frontend consumer map | P0 / relevant parts | Backend + frontend | Separate implementation authorization |
| 6 | Implement and verify bounded vertical slice | P0 / authorized work package | Backend-led, frontend as scoped | Approved criteria and test evidence |

Do not skip from step 2 to implementation while source conflicts or contract fields remain unresolved.

## 12. Required completion report from receiving agent

- Files inspected: exact filename, version and status.
- Files created: exact filename, version and path.
- Files modified: exact filename and sections; otherwise “none”.
- Source conflicts: evidence and proposed resolution path; no silent decisions.
- Fields/interfaces: source-defined vs proposed/open/conflicted.
- Tests: proposed only or actually run; identify environment/evidence.
- Owner decisions required: exact decision, owner and impact.
- Authorization check: confirm no prohibited action occurred.
- Next dependency: exact document/decision required before the next work package.

---

**End of handoff.** This is a working navigation and reconciliation artifact. It does not amend canonical sources, freeze detailed contracts or grant implementation authority.
