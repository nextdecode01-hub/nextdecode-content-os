# NEXTDECODE --- P0 Cross-Document Consistency & Gap Review

**Document ID:**
`NEXTDECODE_P0_Cross_Document_Consistency_Gap_Review_0.1`\
**Version:** 0.1\
**Date:** 1 November 2026\
**Status:** REVIEW FINDINGS --- OWNER REVIEW REQUIRED\
**Scope:** WP-1 through WP-6, Decision Resolution Register v0.1,
Consolidated Contract Appendix v0.1, and P0 Consolidation & Readiness
Review v0.1\
**Detailed contract freeze:** NOT GRANTED\
**Implementation authorization:** NOT GRANTED

------------------------------------------------------------------------

## 1. Executive finding

The P0 package set is broadly aligned on its main architecture:
canonical identity and ownership, durable at-least-once execution,
bounded workers, immutable artifacts, centralized governance and a
non-production vertical-slice acceptance path.

However, the documents are **not yet a single internally complete
contract baseline**. This review identifies: - a small number of wording
inconsistencies and omissions between package documents and the
consolidated appendix; - several areas where the appendix compresses a
source contract enough to lose required detail; - unresolved ownership
and state-machine boundaries; - open decisions that remain correctly
open and must not be converted into implementation assumptions.

No source code, repository state, tests or runtime behavior were
inspected or changed for this review. Findings are based on the named
design documents, not fresh implementation verification.

## 2. Documents reviewed

1.  `NEXTDECODE_P0_WP1_Final_Schema_Contract_Candidate_0.3.md`
2.  `NEXTDECODE_P0_WP2_Durable_Job_Workflow_Execution_0.1.md`
3.  `NEXTDECODE_P0_WP3_Worker_Registry_Contract_Boundary_0.1.md`
4.  `NEXTDECODE_P0_WP4_Artifact_Registration_Storage_Transfer_0.1.md`
5.  `NEXTDECODE_P0_WP5_Governance_Quality_Rights_Authorization_0.1.md`
6.  `NEXTDECODE_P0_WP6_Vertical_Slice_Integration_Recovery_Validation_0.1.md`
7.  `NEXTDECODE_P0_Decision_Resolution_Register_0.1.md`
8.  `NEXTDECODE_P0_Consolidated_Contract_Appendix_0.1.md`
9.  `NEXTDECODE_P0_Consolidation_Readiness_Review_0.1.md`

The accepted Artifact 08 decisions and governing canonical data
dictionary/API-event/lifecycle standards remain higher-authority sources
where the P0 drafts are subordinate to them.

## 3. Findings summary

  --------------------------------------------------------------------------------
  ID                Severity          Finding                    Disposition
  ----------------- ----------------- -------------------------- -----------------
  X-01              HIGH              Workflow state ownership   Resolve before
                                      and lifecycle/execution    freeze
                                      state wording remains      
                                      ambiguous                  

  X-02              HIGH              WP-4 ArtifactVersion and   Restore
                                      manifest contract detail   source-defined
                                      is lost in appendix        fields and
                                      consolidation              manifest
                                                                 semantics

  X-03              HIGH              Transfer, validation and   Complete before
                                      quarantine records are     freeze
                                      named but not              
                                      contractually defined      

  X-04              HIGH              Governance concept         Normalize
                                      count/labels differ        terminology
                                      between WP-5 and appendix  

  X-05              HIGH              Authorization and          Owner-reserved;
                                      emergency-pause contract   resolve before
                                      remains incomplete across  freeze
                                      WP-5, WP-6 and appendix    

  X-06              HIGH              Worker trust, credential   Resolve before
                                      and revocation semantics   freeze;
                                      remain insufficiently      owner/security
                                      specified                  review

  X-07              MEDIUM            Job/task/workflow mapping  Define canonical
                                      and state-machine          mapping
                                      boundaries are not fully   
                                      reconciled                 

  X-08              MEDIUM            Event, command and         Add compatibility
                                      interface envelope         and validation
                                      requirements are           rules
                                      incomplete versus          
                                      governing standard         

  X-09              MEDIUM            Artifact                   Owner-reserved
                                      lifecycle/deletion/legal   data-lifecycle
                                      hold and access action     resolution
                                      semantics are incomplete   

  X-10              MEDIUM            WP-6 acceptance evidence   Complete
                                      does not yet define all    acceptance matrix
                                      test oracle and            
                                      environment controls       

  X-11              MEDIUM            ODR-22 in the Decision     Reconcile; do not
                                      Resolution Register is not treat as accepted
                                      a faithful transcription   wording
                                      of a confirmed source row  

  X-12              LOW               Status labels and document Normalize
                                      authority language vary    glossary and
                                      across the set             document
                                                                 precedence
  --------------------------------------------------------------------------------

No finding below authorizes implementation. "Resolve before freeze"
means specify and approve the contract, not start coding.

## 4. Detailed findings

### X-01 --- Workflow lifecycle and execution state ownership

**Severity:** HIGH\
**Sources:** WP-1 §4.7; WP-2 workflow/job/task boundaries; Consolidated
Contract Appendix §3.2 and §4.

WP-1 describes Workflow with `lifecycle/execution state` as separately
named domain-owned concepts. This phrase is directionally correct but
leaves unclear: - whether Workflow has a business lifecycle separate
from run execution; - whether the `Workflow` record is a definition, a
run, or both; - which entity owns task state and how it relates to job
state; - whether workflow cancellation and workflow-run cancellation are
distinct.

The appendix uses `Workflow definition`, `Workflow run` and
`Workflow task` in its conceptual list, but the WP-1 candidate's minimum
model still presents `workflow_id`, `workflow_type` and
`workflow_definition_version` together without a clearly separate run
identity.

**Required resolution:** 1. Explicitly separate `WorkflowDefinition`
(versioned reusable definition) from `WorkflowRun` (one execution
instance). 2. Define whether `WorkflowTask` is a run-scoped task
instance or a reusable task definition; avoid using one record for both.
3. Map `WorkflowTask` to `Job` explicitly. A task may create one or more
jobs only if the contract defines cardinality and ownership; do not
assume one-to-one. 4. Keep workflow lifecycle, run execution, task
execution and job/attempt state distinct. 5. Specify which owner commits
each transition and what events are emitted.

**Freeze effect:** Blocker. Without this, WP-1 and WP-2 can produce
incompatible schemas and status transitions.

### X-02 --- ArtifactVersion and manifest details are compressed or omitted

**Severity:** HIGH\
**Sources:** WP-1 §4.8; WP-4 §§5, 12; Consolidated Contract Appendix
§§6.1--6.3 and 8.5.

WP-4's ArtifactVersion model includes `checksum_algorithm`,
`validation_status`, `provenance_refs` and `rights_refs`, in addition to
hash, media type, size and storage reference. The appendix's candidate
ArtifactVersion field list is explicitly carried from WP-1 and does not
reproduce all of these WP-4 fields.

WP-4 also requires manifests to have canonical identity and immutable
versions, exact component artifact-version references,
composition/dependency information, integrity and production provenance.
The appendix introduces `ArtifactManifest` but its envelope omits a
manifest version identity, component roles/order, explicit dependencies
and schema version.

**Required resolution:** 1. Reconcile the ArtifactVersion field set with
WP-4; do not silently drop checksum algorithm, validation evidence,
provenance or rights references. 2. Decide which fields are
authoritative on ArtifactVersion versus separate
ValidationRecord/RightsAssessment records. Prefer typed references to
duplicating authoritative state. 3. Define `ArtifactManifest` and
`ArtifactManifestVersion` (or an explicitly equivalent immutable version
model). 4. Define component role, ordering, dependency, exact
ArtifactVersion references, provenance and integrity semantics. 5.
Define the relation between Artifact, ArtifactVersion, Asset, Manifest
and StudioProduction.

**Freeze effect:** Blocker. Manifest and exact artifact version binding
are core to reproducibility, review and approval.

### X-03 --- Transfer, validation and quarantine records are only named

**Severity:** HIGH\
**Sources:** WP-4 §§7--11, 15--16; Consolidated Contract Appendix §§6
and 8.5.

WP-4 describes a logical storage operation set and a proposed transfer
lifecycle:
`REQUESTED → AUTHORIZED → TRANSFERRING → VERIFIED → REGISTERED`, with
failure/interruption states such as `EXPIRED`, `FAILED`, `CANCELLED` and
`RECONCILIATION_REQUIRED`.

The appendix lists TransferRecord, ValidationRecord and QuarantineRecord
as logical concepts but does not define their minimum fields, owning
authority, lifecycle transitions or relationships. It mentions
interrupted-transfer recovery and quarantine behavior in prose, but this
is not enough to make the interface implementable.

**Required resolution:** 1. Define TransferRecord identity, actor,
action, exact artifact/session scope, workspace/job scope, authorization
reference, expiry, attempt/progress evidence and final outcome. 2.
Define the temporary transfer/session identity and when bytes become a
registered durable ArtifactVersion. 3. Define ValidationRecord identity,
target exact version/hash, validator/capability, validation
profile/schema version, outcome, evidence and timestamp. 4. Define
QuarantineRecord identity, exact target version, trigger/reason,
authority, state, evidence, release/revalidation decision and audit
references. 5. Preserve the WP-4 distinction between validation,
availability, quarantine, rights, QA, approval and authorization. 6.
Specify retry/resume behavior without treating partial bytes as a
complete artifact.

**Freeze effect:** Blocker for artifact transfer and safe downstream
use. Provider-specific transfer technology may remain deferred.

### X-04 --- Governance concepts are labelled inconsistently

**Severity:** HIGH\
**Sources:** WP-5 §4; WP-5 QA/rights/approval sections; Consolidated
Contract Appendix §7.1.

WP-5 describes "four separate governance concepts" and its table groups
"Review / QA" together, then rights, approval and authorization. The
appendix presents five separate concepts: QA, rights, review, approval
and authorization.

This is not necessarily a policy disagreement, but it is a terminology
and data-model ambiguity: QA assessment is not identical to a human
review record. A QA result may trigger review, while a reviewer may
inspect materials and record a decision separately.

**Required resolution:** 1. Standardize the model on five distinct
records/concepts: QA result, rights assessment, review snapshot, human
approval decision and authorization decision. 2. Keep execution outcome
separate as a sixth operational fact. 3. Define the relationship between
a review snapshot and the QA evidence it contains; inclusion must not
merge ownership or state. 4. Update WP-5 §4 wording and all appendix
references consistently.

**Freeze effect:** Blocker for governance schema consistency. Accepted
QA, rights and approval vocabularies remain unchanged.

### X-05 --- Central authorization and emergency pause remain incomplete

**Severity:** HIGH\
**Sources:** WP-5 §§5--13, 17; WP-6 F-11--F-18; Consolidated Contract
Appendix §§7.4--7.5, 11 and 12.

The central authorization decision is accepted (CF-22 / ADR-007).
However, the exact policy request/decision schema, protected-action
catalogue, reason codes, revocation propagation, emergency-pause
authority and in-flight action behavior remain open.

WP-6 includes a test where emergency pause is activated before a
protected action, but does not by itself define the pause authority,
scope, deactivation controls or handling of already in-flight external
actions.

**Required resolution:** 1. Define the canonical protected-action
catalogue and action/resource/version/hash/destination binding. 2.
Define policy decision identity, policy version, reason code, evidence
references, expiry and revocation behavior. 3. Define emergency pause
activation authority, scope, audit, deactivation/recovery authority and
in-flight action reconciliation. 4. Require all direct adapters,
pipelines, APIs and workers to consult the same central authorization
boundary at the point of action. 5. Ensure an `ALLOW` decision is not
treated as perpetual or transferable authorization.

**Owner authority required:** Yes, for emergency override authority and
any exception to fail-closed rules.

**Freeze effect:** Blocker.

### X-06 --- Worker trust and credential contracts need a minimum interoperable specification

**Severity:** HIGH\
**Sources:** WP-3 §§5--13; WP-2 assignment/lease contract; Consolidated
Contract Appendix §5.

The documents agree on unique worker identity, scoped short-lived
credentials, capability separation and local/remote parity. But WP-3
leaves enrollment protocol, machine identity proof, credential
issuer/format/rotation, revocation propagation, local secret storage,
isolation technology and active-job revocation open.

Some provider-specific choices can be deferred. The minimum trust
protocol and behavior cannot be deferred if workers are expected to
claim jobs safely.

**Required resolution:** 1. Specify enrollment states and transitions,
including pending verification, trusted, suspended and revoked semantics
(final enum names to be reconciled with the governing lifecycle
standard). 2. Define machine identity proof requirements without
selecting a vendor. 3. Define credential scope, audience/subject
binding, expiry, renewal, rotation and revocation semantics independent
of token vendor. 4. Define what happens to an active lease/job when
trust or credentials are revoked. 5. Define minimum isolation guarantees
even if the isolation technology is deferred. 6. Keep declared,
verified, available and authorized capability facts separate.

**Owner/security review required:** Minimum isolation, identity proof
and revocation behavior.

**Freeze effect:** Blocker.

### X-07 --- WorkflowTask, Job and JobAttempt cardinality and state mapping

**Severity:** MEDIUM\
**Sources:** WP-1 §4.7; WP-2 §§4--10; WP-6 scenario; Consolidated
Contract Appendix §4.

WP-1 explicitly defers whether a physical Job/JobAttempt record is
required in the WP-1 vertical-slice schema to WP-2. WP-2 introduces Job
and JobAttempt as durable execution records. The appendix lists all
concepts but does not specify cardinality, mapping or the point where a
task is considered complete.

**Required resolution:** - Define whether one task may create multiple
jobs, and whether a job may serve more than one task (recommended
default: one job belongs to one task execution context; any fan-out is
represented explicitly). - Define whether task completion requires all
linked jobs to reach accepted outcomes. - Define cancellation
propagation and partial/fan-out failure handling. - Define whether a
retry is a new JobAttempt only (recommended) or a new Job, and preserve
the accepted logical-job identity. - Define the source of truth for each
status.

**Freeze effect:** Blocker if left ambiguous; routine cardinality
defaults may be proposed but require explicit contract text.

### X-08 --- Command/event envelope and compatibility rules are not complete

**Severity:** MEDIUM\
**Sources:** WP-1 §7; WP-2 §§10--11; Consolidated Contract Appendix
§§8--9; API/Event Contract Standard.

The appendix includes useful command and event envelope fields, but does
not fully reconcile them to the governing API/Event Contract Standard.
Missing or insufficiently specified areas include: - canonical envelope
required/optional field rules; - event ordering and aggregate-version
semantics; - schema compatibility and consumer behavior for unknown
fields/versions; - command validation and rejection envelope; - event
replay and retention; - correlation/causation constraints; - sensitive
payload minimization and reference-versus-inline payload rules.

**Required resolution:** Treat the governing API/Event Contract Standard
as authoritative, produce a field-by-field conformance matrix, and make
the appendix illustrative only until that reconciliation is complete.

**Freeze effect:** Blocker for cross-domain API/event contracts.

### X-09 --- Artifact deletion and lifecycle policy is only partially reconciled

**Severity:** MEDIUM\
**Sources:** WP-1 §6.5; WP-4 §§13, 16; Decision Resolution Register
ODR-13; Consolidated Contract Appendix §§6 and 11.

WP-1 recommends restrictive references/no cascade and warns against
deleting history as a side effect. WP-4 separately requires
dependency-aware deletion, controlled recovery and distinct `DELETE`
permission. The appendix mentions retention, deletion, legal hold,
backup and restore as open but does not define a lifecycle contract.

**Required resolution:** 1. Define logical retirement versus deletion
request versus physical purge. 2. Define dependency discovery and impact
assessment. 3. Define legal hold and preservation behavior. 4. Define
approval/authorization for irreversible purge. 5. Define how artifact
bytes and relational metadata remain consistent during
deletion/recovery. 6. Define audit/evidence retention independently from
ordinary content retention.

**Owner authority required:** Yes, for irreversible deletion, legal hold
and material retention obligations.

**Freeze effect:** The lifecycle interface and safeguards block freeze;
exact durations/provider backup settings may be deferred if safely
abstracted.

### X-10 --- WP-6 test scenarios need explicit oracles and environment controls

**Severity:** MEDIUM\
**Sources:** WP-6 §§4--9 and 15--18; Consolidated Contract Appendix §10.

WP-6 provides a clear 18-step scenario and 18 failure-injection cases.
The appendix carries the scenario and categories but does not fully
define: - test environment isolation and explicit non-production
guarantees; - expected result/oracle for every scenario; - test fixture
identity and deterministic output specification; - evidence completeness
and retention; - cleanup/teardown rules that do not delete user data; -
how each result maps to `PASS`, `PASS_WITH_WARNINGS`, `NEEDS_REVIEW` or
`BLOCKED`; - independent QA exit criteria and owner acceptance record.

**Required resolution:** Maintain WP-6's detailed scenario and failure
table as the authoritative acceptance plan; add a traceability matrix
from each acceptance requirement to test ID, expected outcome, evidence
and reviewer.

**Freeze effect:** Acceptance contract blocker. No tests are authorized
by this review.

### X-11 --- ODR-22 wording is a provisional grouping, not a verified source decision

**Severity:** MEDIUM\
**Sources:** Decision Resolution Register v0.1 ODR-22; Consolidation
Readiness Review ODR register; accepted owner decision record.

The Decision Resolution Register explicitly says ODR-22's detailed
source wording must be reconciled. Its current description groups
single-owner Creator Mode and existing engineering/QA responsibilities.
These are project constraints, but the exact original ODR-22
decision-area wording is not established by the reviewed excerpts.

**Required resolution:** Preserve the row as
`PROVISIONAL GROUPING — SOURCE RECONCILIATION REQUIRED`. Do not cite
ODR-22 as an owner-approved decision or treat the wording as
authoritative until matched to the complete original register.

**Freeze effect:** Reconciliation required for register integrity; not
necessarily a technical blocker by itself.

### X-12 --- Status vocabulary and source precedence need one glossary

**Severity:** LOW\
**Sources:** All reviewed design candidates and consolidated documents.

Documents use overlapping labels such as `ACCEPTED`, `OWNER-ACCEPTED`,
`SOURCE-DEFINED`, `RECOMMENDED`, `PROPOSED`, `OPEN`, `DEFERRED`,
`FROZEN`, `VERIFIED` and `NOT VERIFIED`. These are broadly
understandable but are not yet a single controlled status taxonomy.

**Required resolution:** - Publish one glossary distinguishing decision
authority, design maturity, implementation state and evidence state. -
Define document precedence: accepted ADR/CF owner record and governing
standards first; WP package contracts next; consolidation appendix as a
derivative index, not an override. - Mark every field/state/envelope as
accepted, source-defined, proposed or open. - Ensure no "verified" label
is used without current evidence and scope.

**Freeze effect:** Quality/traceability improvement; resolve before
final consolidated publication.

## 5. Confirmed alignments --- no change required

The following are consistent across the reviewed set and should be
preserved:

1.  UUIDv7 immutable canonical identity; entity/version/schema version
    are distinct.
2.  One authoritative owner per canonical entity; typed references do
    not grant permission.
3.  ContentItem is the editorial identity; ContentVariant is a
    derivative; ContentVersion is immutable.
4.  Workflow orchestration does not own ContentItem, Artifact, QA,
    rights, approval or publication lifecycle.
5.  PostgreSQL-compatible relational authority and DB-backed durable
    queue/outbox/inbox remain accepted directions; no provider is
    selected.
6.  At-least-once delivery is accepted; exactly-once execution is not
    claimed.
7.  Retry creates a new attempt while preserving logical job identity.
8.  Fencing prevents stale attempts from committing after takeover.
9.  Worker identity is independent of hostname;
    declared/verified/available/authorized capabilities remain separate.
10. Local and remote workers share the same trust boundary.
11. Asset, Artifact and ArtifactVersion are distinct; artifact versions
    are immutable.
12. Storage locator alone is not authorization; integrity and scoped
    transfer are required.
13. QA, rights, approval and authorization are separate; hard blockers
    fail closed.
14. Centralized authorization is accepted; publishing adapters cannot
    bypass it.
15. Automatic public publishing remains disabled; human approval remains
    required for critical publishing actions.
16. P0 acceptance is synthetic, deterministic and non-production;
    protected distribution requests are denied.
17. Shorts Studio remains a bounded specialist engine; no wholesale
    replacement.
18. No paid services, provider activation, deployment, implementation or
    external side effects are authorized by these design documents.

## 6. Recommended reconciliation actions

Apply in this order:

### R-01 --- Normalize domain and workflow model

-   Define WorkflowDefinition, WorkflowRun, WorkflowTask, Job and
    JobAttempt boundaries.
-   Define cardinality and status ownership.
-   Update WP-1 and WP-2 together.

### R-02 --- Restore artifact contract completeness

-   Reconcile ArtifactVersion fields with WP-4.
-   Define ManifestVersion, TransferRecord, ValidationRecord and
    QuarantineRecord.
-   Define registration/transfer/availability transitions.
-   Update WP-1, WP-4 and appendix together.

### R-03 --- Normalize governance terminology and interfaces

-   Separate QA result from review snapshot.
-   Define policy request/decision schemas and protected-action
    catalogue.
-   Resolve emergency pause authority and in-flight behavior with owner.
-   Update WP-5 and appendix.

### R-04 --- Complete worker trust minimum

-   Specify vendor-neutral enrollment and credential semantics.
-   Specify active-job revocation and minimum isolation guarantees.
-   Keep technology/provider choices deferred where safe.
-   Update WP-3 and appendix.

### R-05 --- Complete event and error conformance

-   Reconcile command/event envelopes to the governing API/Event
    Contract Standard.
-   Define schema compatibility, replay, ordering, redaction and error
    mapping.
-   Update WP-1, WP-2 and appendix.

### R-06 --- Complete data lifecycle boundary

-   Define logical retirement, deletion request, legal hold, recovery
    and purge authority.
-   Keep exact durations/provider settings deferred only if enforcement
    hooks are explicit.
-   Update WP-1, WP-4 and WP-5.

### R-07 --- Make WP-6 acceptance executable as a specification

-   Map each requirement to test ID, preconditions, steps, expected
    outcome and retained evidence.
-   Define test-environment isolation and non-production guardrails.
-   Preserve the no-side-effect boundary.
-   Do not run tests without separate authorization.

### R-08 --- Reconcile master decision register

-   Validate ODR-01--ODR-22 against the original source register and
    package-local IDs.
-   Correct ODR-22 wording or mark it provisional.
-   Preserve source identifiers; do not renumber package-local
    O/J/W/A/G/F records.

## 7. Freeze-readiness assessment

  -----------------------------------------------------------------------
  Area                                Assessment
  ----------------------------------- -----------------------------------
  High-level architecture alignment   COHERENT

  Canonical identity and ownership    MOSTLY ALIGNED; exact schemas open

  Workflow/job/task contract          NOT READY --- X-01, X-07

  Worker trust and isolation          NOT READY --- X-06

  Artifact and transfer contract      NOT READY --- X-02, X-03

  Governance and authorization        NOT READY --- X-04, X-05

  API/event compatibility             NOT READY --- X-08

  Data lifecycle                      NOT READY --- X-09

  Acceptance evidence contract        NOT READY --- X-10

  Decision register traceability      PARTIAL --- X-11, X-12
  -----------------------------------------------------------------------

**Overall disposition: NOT READY FOR DETAILED CONTRACT FREEZE.**

The design is sufficiently coherent to continue controlled specification
reconciliation. It is not sufficiently precise to claim a frozen,
implementation-ready contract baseline.

## 8. Authority and safety status

This review: - does not change accepted ADR-001--ADR-010 or
CF-01--CF-24; - does not grant acceptance to proposed resolutions; -
does not close owner-reserved security, rights, authorization or
data-lifecycle decisions; - does not authorize repository
inspection/modification, tests, Git operations or agent execution; -
does not select providers or permit paid services; - does not authorize
deployment, production generation, upload or publishing; - does not
claim any inherited Phase 10/11 blocker is fixed; - does not establish
independent Kilo QA acceptance.

**Detailed contract freeze:** NOT GRANTED.\
**Implementation authorization:** NOT GRANTED.

------------------------------------------------------------------------

## Plain-language explanation

The architecture documents agree on the big picture, but a few important
pieces are still described at different levels of detail. The biggest
gaps are how workflows map to jobs, exactly what an artifact manifest
and transfer record contain, how worker trust is revoked, and how
central authorization and emergency pause behave.

The appendix is a useful map, but it shortened some details that WP-4
and WP-5 had already specified. We should restore those details rather
than let the shorter summary become the accidental source of truth.

**NEXTDECODE principle:** reconcile the source contracts first, preserve
every accepted decision, and freeze only when the interfaces are precise
enough that implementation requires no guessing.
