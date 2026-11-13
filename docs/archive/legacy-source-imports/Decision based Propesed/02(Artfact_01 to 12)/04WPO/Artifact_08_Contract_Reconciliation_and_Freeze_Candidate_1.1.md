# NEXTDECODE Content OS

# Artifact 08 --- Contract Reconciliation & Freeze Candidate 1.1

**Version:** 1.1\
**Date:** 1 November 2026\
**Status:** Reconciliation candidate --- owner confirmation required for
final consolidated freeze\
**Authority:** Product Owner\
**Supersedes:** Nothing. This document supplements Artifact 08 v1.0 and
its decision records.

## 1. Purpose

This document reconciles the already-reviewed owner decisions CF-01
through CF-24 with the detailed P0 contract proposal and records the
remaining closure gates.

It does not reopen accepted owner decisions, silently change them, or
grant implementation permission.

### Current disposition

  -----------------------------------------------------------------------
  Area                                Status
  ----------------------------------- -----------------------------------
  ADR-001--ADR-010                    OWNER-ACCEPTED

  CF-01--CF-24                        OWNER REVIEW COMPLETED; decisions
                                      recorded

  Detailed contract proposals         EXIST; reconciliation required

  Contract freeze                     PENDING consolidated owner
                                      confirmation

  Implementation authorization        NOT GRANTED

  Repository/Git/code/test actions    NOT AUTHORIZED

  Paid services / cloud provider /    NOT AUTHORIZED / DEFERRED
  deployment                          

  Production generation / upload /    NOT AUTHORIZED
  publishing                          
  -----------------------------------------------------------------------

## 2. Source documents reconciled

This candidate was prepared against the existing Library records:

1.  `NEXTDECODE_Artifact_08_P0_Detailed_Contract_Freeze_Open_Decisions_Closure_1.0.md`
2.  `NEXTDECODE_Artifact_08_Consolidated_Owner_Decision_Record_Contract_Freeze_Closure_1.0.md`
3.  `NEXTDECODE_Artifact_08_Implementation_Reference_Accepted_Contract_Decisions_1.0.md`
4.  `NEXTDECODE_P0_Detailed_Contract_Freeze_Pack_1.0.md`

The existing v1.0 documents are preserved. This v1.1 file is a
reconciliation layer, not a replacement.

## 3. Owner decisions --- do not reopen

### 3.1 High-level architecture

ADR-001 through ADR-010 remain accepted:

-   UUIDv7 canonical IDs, opaque and immutable.
-   PostgreSQL-compatible relational database as authoritative
    shared-state store.
-   DB-backed durable queue with transactional outbox/inbox initially.
-   Versioned HTTP/JSON contracts with schema validation.
-   Unique worker identity, scoped short-lived credentials and
    capability authorization.
-   Relational artifact metadata with binary storage behind an
    abstraction.
-   Centralized authorization; publishing adapters cannot bypass it.
-   QA outcomes: `PASS`, `PASS_WITH_WARNINGS`, `NEEDS_REVIEW`,
    `BLOCKED`; ordinary approval cannot bypass hard blockers.
-   Evidence-backed, use-specific rights.
-   Separate lifecycle state machines for content, workflow, execution,
    review, approval, authorization and distribution.

### 3.2 Detailed owner decision status

-   CF-01--CF-15: explicitly accepted by owner.
-   CF-16--CF-21: accepted under standing delegation.
-   CF-22: explicit owner choice, Option A --- centralized
    authorization.
-   CF-23: accepted under standing delegation.
-   CF-24: explicit no-paid-services constraint; operational/provider
    selections deferred.

The complete accepted decision summaries remain in the existing
Implementation Reference. This candidate does not paraphrase them into
new decisions.

## 4. Reconciliation findings

### RCN-01 --- Canonical content identity

**Existing decision:** CF-01 establishes `ContentItem` as the shared
editorial identity and `ContentVariant` as a
format/platform/language/treatment derivative.

**Required reconciliation:** All data dictionaries, entity tables, API
payloads, foreign keys and studio adapters must use this distinction
consistently.

**Disposition:** ACCEPTED DECISION --- carry forward. Do not reopen
without a superseding owner decision.

### RCN-02 --- Entity identity versus version identity

**Existing decision:** Canonical entity IDs are immutable; version
identity is distinct.

**Required detailed contract:** - `entity_id` identifies the enduring
logical entity. - `version_id` or an explicitly defined immutable
version number identifies a specific revision. - A mutable status is
never encoded into an ID. - Review, approval, QA, authorization and
distribution refer to exact version references. - A correction or
regenerated output creates a new version/artifact; it does not overwrite
history.

**Disposition:** ACCEPTED DIRECTION; exact version representation and
schema remain a detailed-specification item.

### RCN-03 --- Rights-state vocabulary conflict

**Conflict found:** The accepted CF-20 implementation reference defines:
`UNKNOWN`, `PENDING_REVIEW`, `CLEARED`, `RESTRICTED`, `EXPIRED`,
`REVOKED`, `DENIED`.

The earlier detailed contract pack uses a different candidate
vocabulary: `CLEARED`, `RESTRICTED`, `PENDING_VERIFICATION`,
`PROHIBITED`, `UNKNOWN`.

**Reconciliation rule:** The accepted CF-20 vocabulary is authoritative.
The older detailed-pack vocabulary must be aligned before freeze.

Proposed semantic mapping for documentation compatibility only: -
`PENDING_VERIFICATION` → `PENDING_REVIEW` - `PROHIBITED` → `DENIED`

Do not run a data migration or assume perfect semantic equivalence
without a separately approved migration plan. `EXPIRED` and `REVOKED`
must remain distinguishable from `DENIED`.

**Disposition:** DOCUMENTATION CONFLICT --- resolution specified by
accepted CF-20; update detailed schema before freeze.

### RCN-04 --- Approval-decision vocabulary conflict

**Conflict found:** Accepted CF-21 defines: `APPROVED`, `REJECTED`,
`CHANGES_REQUESTED`, `EXPIRED`, `REVOKED`.

The older detailed contract request example includes only `APPROVED` and
`REJECTED`.

**Reconciliation rule:** The full CF-21 decision vocabulary is
authoritative. The request/response schema must support the full
lifecycle, while preserving the distinction between a new decision
command and the resulting approval record.

**Mandatory binding:** - immutable review package; - exact
content/artifact/manifest version and checksum references; -
attributable actor and timestamp; - decision and reason; - policy
version/scope where applicable.

A new artifact/content version does not inherit approval automatically.
Revocation and expiry must be auditable.

**Disposition:** DOCUMENTATION GAP --- resolve by aligning detailed
approval schema to accepted CF-21.

### RCN-05 --- Authorization is separate from approval

**Accepted decision:** CF-22 Option A --- one central authorization
authority.

**Required reconciliation:** - Authorization is default-deny and
fail-closed. - It is bound to exact action, resource, version,
destination/account, policy version and time window. - Approval may be a
prerequisite but is not authorization. - Workers, APIs, studios and
distribution adapters must enforce the central decision. - Expiry and
revocation are enforced at execution time. - Agent delegation cannot
expand authority. - A direct adapter cannot bypass the central decision.

**Disposition:** OWNER-ACCEPTED; detailed contract must be checked
against every protected action boundary.

### RCN-06 --- QA outcomes and hard blockers

The accepted QA outcomes remain: `PASS`, `PASS_WITH_WARNINGS`,
`NEEDS_REVIEW`, `BLOCKED`.

Each result must be immutable and bound to exact target versions and
policy version. Checks must be evidence-backed. Scores are
supplementary. `BLOCKED` cannot be converted to a pass by ordinary
approval.

**Disposition:** OWNER-ACCEPTED; detailed check catalogue and thresholds
remain open/deferred.

### RCN-07 --- Job, attempt, lease and retry

Accepted directions: - Workflow, task, job, attempt and worker execution
are distinct identities. - Delivery is at-least-once; exactly-once
execution is not assumed. - Job attempts have durable history. - Leases
have owner, expiry and heartbeat semantics. - Stale workers cannot
overwrite newer attempts. - Idempotency keys prevent duplicate logical
side effects. - Transactional outbox/inbox supports durable event
dispatch and consumer deduplication. - Event delivery does not prove
business completion.

Still deferred: - lease duration and heartbeat interval; - retry count,
backoff, jitter and dead-letter thresholds; - idempotency retention; -
outbox/inbox retention and replay/purge rules; - ordering guarantees
beyond scoped ordering.

**Disposition:** ACCEPTED DIRECTION; numeric operational values remain
DEFERRED and must not be guessed.

### RCN-08 --- Worker trust and capability boundaries

Accepted directions: - Worker identity is independent of
hostname/machine name. - Registration and trust have explicit
lifecycles. - Declared, verified, available and authorized capabilities
are distinct. - Credentials are unique, scoped, short-lived and
revocable. - Capability declarations are not permissions. - Local and
remote workers share governance. - Jobs execute within bounded isolation
and scoped filesystem/network/credential/artifact access. - Admin,
production, QA and publishing permissions remain separated.

Still open: - final capability catalogue; - credential issuer/protocol
and secret-storage mechanism; - numeric resource limits and concurrency
quotas.

The capability catalogue should be aligned with real studio adapter
boundaries only during a separately authorized read-only system
inspection. This document does not authorize that inspection.

### RCN-09 --- Artifact and manifest

Accepted directions: - Asset and Artifact are distinct. - Artifact
identity and versions are immutable. - Relational metadata is
authoritative; binary storage is abstracted. - Checksums and structural
validation are recorded. - Transfer is scoped, attributable and
verifiable. - Manifests refer to exact immutable component versions. -
Review, approval and distribution bind to exact manifest/artifact
versions. - Quarantine blocks normal downstream use. - Repairs create
new versions. - Technical validation does not establish factual
accuracy, rights or approval.

Still deferred: - storage provider and transfer protocol; - exact
retention durations; - legal-hold implementation; - backup/replication
and encryption provider settings.

### RCN-10 --- Error, recovery and audit

Accepted directions: - Shared structured error taxonomy. - Severity and
retryability are independent. - Retryability is explicit and
operation-specific. - Failure and attempt history is durable. -
Ambiguous external actions require reconciliation. - Recovery has a
defined domain owner. - Policy/authorization denial cannot be bypassed
through retry. - Diagnostics are access-controlled. - Correlation and
causation context is retained.

Detailed schemas, audit-event catalogue, retention durations and
operational monitoring thresholds must be completed in the relevant
contracts. Provider choices remain deferred.

### RCN-11 --- Operational constraints

CF-24 remains binding: - local-first and free-first; - no paid
subscriptions, usage-based spending, paid
APIs/models/storage/databases/automation or charge-generating
infrastructure without separate explicit owner approval; - no automatic
upgrades or silently billable free trials; - no provider selection,
cloud deployment or production infrastructure implied by hybrid
architecture.

**Disposition:** ACCEPTED CONSTRAINT; provider and operational
selections DEFERRED.

## 5. Contract-freeze closure checklist

The following checklist distinguishes completed owner decisions from
remaining documentation work.

  -----------------------------------------------------------------------
  ID                      Freeze requirement      Status
  ----------------------- ----------------------- -----------------------
  FZ-01                   ADR-001--ADR-010        COMPLETE
                          recorded as accepted    

  FZ-02                   CF-01--CF-24 owner      COMPLETE
                          review and decisions    
                          recorded                

  FZ-03                   `ContentItem` /         DECIDED; propagate
                          `ContentVariant`        consistently
                          canonical distinction   
                          reconciled              

  FZ-04                   Entity ownership and    NEEDS DOCUMENT
                          typed relationships     RECONCILIATION
                          consistent across 12    
                          contracts               

  FZ-05                   Required/optional       NEEDS DETAILED SCHEMA
                          fields, nullability and REVIEW
                          validation rules        
                          complete                

  FZ-06                   Entity versioning and   NEEDS DETAILED SCHEMA
                          exact-version           REVIEW
                          references complete     

  FZ-07                   Full state-transition   NEEDS CLOSURE
                          tables and              
                          terminal/reopen rules   
                          complete                

  FZ-08                   Job, attempt, lease,    DIRECTION ACCEPTED;
                          retry and idempotency   PARAMETERS DEFERRED
                          semantics complete      

  FZ-09                   Event envelope,         NEEDS DETAILED SCHEMA
                          outbox/inbox,           REVIEW
                          deduplication and       
                          recovery complete       

  FZ-10                   Worker identity,        DIRECTION ACCEPTED;
                          registration, trust and CATALOGUE/PROTOCOL OPEN
                          capability contracts    
                          complete                

  FZ-11                   Artifact, manifest,     NEEDS DETAILED SCHEMA
                          transfer and integrity  REVIEW
                          contracts complete      

  FZ-12                   Rights vocabulary       DOCUMENTATION CONFLICT
                          aligned to CF-20        IDENTIFIED

  FZ-13                   Approval vocabulary     DOCUMENTATION GAP
                          aligned to CF-21        IDENTIFIED

  FZ-14                   Central authorization   OWNER DECISION
                          consistently            ACCEPTED;
                          represented in every    SCHEMA/BOUNDARIES NEED
                          contract                RECONCILIATION

  FZ-15                   QA outcomes and         OWNER-ACCEPTED; CHECK
                          hard-blocker rules      CATALOGUE OPEN
                          consistent              

  FZ-16                   Error taxonomy, audit   NEEDS DETAILED SCHEMA
                          and recovery contracts  REVIEW
                          complete                

  FZ-17                   Deferred operational    COMPLETE AS A
                          values explicitly       CONSTRAINT
                          marked and not guessed  

  FZ-18                   Cross-document          IN PROGRESS
                          contradiction register  
                          resolved                

  FZ-19                   Final consolidated      PENDING
                          version and             
                          checksum/reference      
                          prepared                

  FZ-20                   Owner confirms          PENDING
                          consolidated detailed   
                          contract freeze         

  FZ-21                   Separate implementation NOT GRANTED; separate
                          authorization           gate
  -----------------------------------------------------------------------

## 6. Explicitly deferred --- not blockers to documenting the architecture

These values must not be invented merely to make the document appear
complete:

-   Cloud provider, account, region and deployment topology.
-   Production database host/provider and sizing.
-   Queue provider beyond initial DB-backed direction.
-   Object-storage vendor, region, replication and encryption settings.
-   Token issuer, exact token format and production credential
    configuration.
-   Lease duration, heartbeat cadence, retry counts, backoff and jitter.
-   Resource quotas, concurrency limits, scheduling weights and
    fairness.
-   Retention durations and legal-hold implementation.
-   Monitoring, tracing, logging and alerting provider.
-   Backup schedule, RPO, RTO and restore-test cadence.
-   Production workload placement and capacity.
-   Budget and spending authority.

A deferred choice must remain explicitly deferred. A recommendation is
not owner approval.

## 7. Required next work --- design/documentation only

The next work sequence is:

1.  Reconcile the 12 domain contracts against CF-01--CF-24 without
    reopening accepted decisions.
2.  Normalize entity schemas, required fields, nullability, identity and
    version references.
3.  Complete lifecycle transition tables, including cancellation,
    expiry, revocation, terminal and reopen behavior.
4.  Complete job/attempt/lease/retry/idempotency and outbox/inbox
    contract schemas.
5.  Complete worker registration, trust, capability and isolation
    contract schemas.
6.  Complete artifact/manifest/transfer/validation contracts.
7.  Align rights and approval vocabularies to accepted CF-20 and CF-21.
8.  Verify every protected action references the centralized
    authorization authority.
9.  Complete error, audit, correlation and recovery contracts.
10. Publish a consolidated freeze candidate with unresolved items
    clearly marked.
11. Obtain explicit owner confirmation of the detailed contract freeze.

No repository inspection, code change, Git operation, test execution,
dependency installation, environment/credential change, agent execution,
deployment, paid-service activation, production generation, upload or
publishing is authorized by this document.

## 8. Implementation gate remains separate

Even after detailed contract freeze approval: - implementation requires
separate explicit owner authorization; - authorization must specify
scope, repository, permitted files/actions, tests, Git permissions and
stop conditions; - no paid services or cloud deployment without separate
explicit approval; - no production publishing without separate explicit
approval.

## 9. Final status

**ARTIFACT 08 RECONCILIATION CANDIDATE 1.1 PREPARED.**

-   Accepted owner decisions preserved.
-   No prior decision reopened.
-   Rights and approval vocabulary conflicts identified for correction
    in detailed specifications.
-   Deferred operational values retained as deferred.
-   Formal detailed contract freeze remains pending owner confirmation.
-   Implementation authorization remains NOT GRANTED.

------------------------------------------------------------------------

**End of Artifact 08 --- Contract Reconciliation & Freeze Candidate
1.1**
