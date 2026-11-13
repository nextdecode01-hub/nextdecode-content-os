# NEXTDECODE --- P0 Decision Resolution Register

**Document ID:** `NEXTDECODE_P0_Decision_Resolution_Register_0.1`\
**Version:** 0.1\
**Date:** 1 November 2026\
**Status:** WORKING DECISION REGISTER --- OWNER REVIEW REQUIRED\
**Scope:** P0 contract-freeze decision resolution across WP-1 to WP-6\
**Detailed contract freeze:** NOT GRANTED\
**Implementation authorization:** NOT GRANTED

------------------------------------------------------------------------

## 1. Purpose

This register consolidates the open decision groups identified in the P0
Consolidation & Readiness Review and the P0 Owner Review & Contract
Freeze Decision Record.

It distinguishes:

-   Routine design recommendations that may be prepared under the
    owner's standing delegation.
-   Contract semantics that must be explicit before detailed contract
    freeze.
-   Material owner-reserved decisions that must not be silently
    resolved.
-   Provider and operational choices that can safely be deferred.

This register does not replace WP-1 through WP-6, the accepted Artifact
08 decision records, or the canonical data dictionary. It does not
authorize implementation or operational activity.

## 2. Decision status vocabulary

  -----------------------------------------------------------------------
  Status                              Meaning
  ----------------------------------- -----------------------------------
  OWNER-ACCEPTED                      Explicitly accepted by the owner or
                                      under the standing delegation rule,
                                      with supporting record

  CARRIED FORWARD                     Previously accepted decision
                                      retained without reopening

  PROPOSED                            Conservative recommendation; not
                                      yet formally accepted

  OPEN --- OWNER DECISION             Requires an explicit owner decision

  DEFERRED                            Intentionally postponed until a
                                      stated condition is met

  FROZEN                              Included in a formally approved
                                      detailed contract baseline

  VERIFIED                            Supported by current implementation
                                      or independent evidence
  -----------------------------------------------------------------------

A recommendation, document, previous "next", or silence does not itself
constitute owner acceptance.

## 3. Accepted baseline --- carry forward without reopening

### Architecture decisions

-   ADR-001: UUIDv7 canonical IDs.
-   ADR-002: PostgreSQL-compatible relational database as authoritative
    shared-state store.
-   ADR-003: Database-backed durable queue with transactional
    outbox/inbox initially.
-   ADR-004: Versioned HTTP/JSON contracts with schema validation.
-   ADR-005: Unique worker identity, scoped short-lived credentials and
    capability authorization.
-   ADR-006: Relational artifact metadata; binaries behind an
    object-storage abstraction.
-   ADR-007: Centralized authorization; publishing adapters cannot
    bypass it; automatic publishing disabled pending separate policy.
-   ADR-008: QA outcomes `PASS`, `PASS_WITH_WARNINGS`, `NEEDS_REVIEW`,
    `BLOCKED`; hard blockers cannot be bypassed by ordinary approval.
-   ADR-009: Evidence-backed rights states and use-specific enforcement.
-   ADR-010: Separate lifecycle state machines for content, workflow,
    execution, review, approval, authorization and distribution.

### Contract decisions

-   CF-01--CF-15: explicitly accepted by the owner.
-   CF-16--CF-21: accepted under standing delegation.
-   CF-22: explicitly accepted --- centralized authorization, Option A.
-   CF-23: accepted under standing delegation.
-   CF-24: no-paid-services constraint explicitly accepted;
    operational/provider choices remain deferred.

### Project constraints

-   Single-owner Creator Mode at initial scope.
-   Existing Shorts Studio remains a specialised Python/FFmpeg engine
    behind a bounded adapter; no wholesale replacement.
-   Long-term hybrid direction: cloud control plane for authoritative
    shared workflow state, local worker for local-only/heavy rendering
    when available.
-   Local-first/free-first development; no paid services or silent
    billing exposure.
-   Human approval remains required for critical actions; automatic
    public publishing remains disabled.
-   Approval, authorization, execution and confirmed external outcome
    remain distinct.
-   Unknown, missing or ambiguous rights, approval or authorization fail
    closed for protected actions.
-   Existing ownership remains unchanged: Qoder --- Phase 11
    engineering; OpenCode --- Phase 10 engineering/closure; Kilo ---
    independent read-only QA.
-   No implementation, agent execution, repository changes, tests,
    dependency/environment changes, provider activation, deployment,
    production generation, upload or publishing without the relevant
    separate explicit authorization.

## 4. Proposed routine resolutions

These are conservative proposals prepared under the standing-delegation
approach. They are not represented as formally owner-approved or frozen.

  ---------------------------------------------------------------------------------------------------------
  Master ID   Area                Proposed resolution Status           Rationale / impact Source
  ----------- ------------------- ------------------- ---------------- ------------------ -----------------
  ODR-01      Entity schema       Keep the canonical  PROPOSED         Prevents competing WP-1 v0.3;
                                  data dictionary                      definitions; exact Canonical Data
                                  authoritative;                       physical schema    Dictionary
                                  specify fields,                      still needs        
                                  nullability,                         completion         
                                  constraints,                                            
                                  references and                                          
                                  transitions in a                                        
                                  canonical schema                                        
                                  appendix                                                

  ODR-02      Content versioning  Keep entity         PROPOSED         Prevents edits or  WP-1 v0.3; CF-01
                                  identity, content                    derivatives from   
                                  version and variant                  overwriting        
                                  identity distinct;                   identity/history   
                                  content versions                                        
                                  are immutable                                           

  ODR-03      Workflow model      Separate workflow   PROPOSED         Makes execution    WP-2 v0.1;
                                  definition,                          reproducible and   ADR-010
                                  workflow run, task                   dependencies       
                                  and dependency; pin                  explicit           
                                  each run to a                                           
                                  definition version                                      

  ODR-04      Job lifecycle       Separate logical    PROPOSED         Supports traceable WP-2 v0.1
                                  job from attempts;                   retries and clear  
                                  specify terminal                     completion         
                                  outcomes,                            semantics          
                                  cancellation and                                        
                                  remediation                                             
                                  explicitly                                              

  ODR-05      Lease/fencing       Permit one          PROPOSED         Protects shared    WP-2 v0.1;
                                  authoritative                        state from delayed ADR-003
                                  active lease per                     or disconnected    
                                  job; use fencing so                  workers            
                                  stale workers                                           
                                  cannot commit after                                     
                                  takeover                                                

  ODR-06      Retry/idempotency   Same key plus same  PROPOSED         Prevents duplicate WP-2 v0.1
                                  canonical payload                    logical effects    
                                  returns the                          and key misuse     
                                  original logical                                        
                                  result; same key                                        
                                  plus different                                          
                                  payload is a                                            
                                  conflict                                                

  ODR-07      Outbox/inbox        Commit domain-state PROPOSED         Supports restart   WP-2 v0.1;
                                  changes and outbox                   recovery and       ADR-003
                                  records atomically;                  at-least-once      
                                  deduplicate                          delivery           
                                  repeated delivery                                       
                                  through inbox                                           
                                  receipts                                                

  ODR-08      Worker identity     Keep worker         PROPOSED         Prevents machine   WP-3 v0.1; CF-13
                                  identity                             naming from        
                                  independent of                       becoming identity  
                                  hostname; define                     or trust           
                                  explicit enrollment                                     
                                  and trust lifecycle                                     

  ODR-09      Worker capability   Keep declared,      PROPOSED         Capability claims  WP-3 v0.1; CF-13
                                  verified, available                  must not grant     
                                  and authorized                       permission         
                                  capabilities                                            
                                  distinct                                                

  ODR-10      Worker isolation    Require least       PROPOSED ---     Prevents unbounded WP-3 v0.1; CF-14
                                  privilege and       minimum          execution and      
                                  bounded filesystem, guarantees       lateral access     
                                  network,            require                             
                                  credential,         owner/security                      
                                  artifact and        review                              
                                  resource access                                         

  ODR-11      Artifact model      Keep Asset,         PROPOSED         Protects           WP-4 v0.1;
                                  Artifact and                         provenance and     ADR-006
                                  ArtifactVersion                      version integrity  
                                  distinct; preserve                                      
                                  immutable artifact                                      
                                  versions and                                            
                                  lineage                                                 

  ODR-12      Artifact transfer   Require scoped,     PROPOSED ---     Prevents           WP-4 v0.1
                                  attributable,       security details locator-only       
                                  time-limited        remain open      access and         
                                  transfer and                         undetected         
                                  integrity                            corruption         
                                  verification                                            

  ODR-13      Artifact lifecycle  Define lifecycle    PROPOSED /       Avoids premature   WP-4 v0.1
                                  ownership and       PARTIALLY        vendor choices     
                                  enforcement hooks   DEFERRED         without leaving    
                                  now; defer                           lifecycle          
                                  provider-specific                    undefined          
                                  retention and                                           
                                  backup values                                           

  ODR-14      Governance schema   Separate QA         PROPOSED         Avoids conflating  WP-5 v0.1;
                                  results, rights                      quality, rights,   ADR-008/009/010
                                  evidence,                            approval and       
                                  review/approval                      permission         
                                  snapshots and                                           
                                  policy decisions                                        

  ODR-15      Authorization       Bind protected      PROPOSED ---     Prevents approval  WP-5 v0.1;
              binding             authorization to    exact policy     or stale           ADR-007
                                  exact action,       semantics        permission from    
                                  resource,           require owner    authorizing a      
                                  version/hash,       review           different action   
                                  destination and                                         
                                  policy context                                          

  ODR-16      Emergency pause     Require a central   OPEN --- OWNER   Authority, scope,  WP-5 v0.1
                                  pause authority and DECISION         override and       
                                  fail-closed                          recovery are       
                                  behavior for                         material           
                                  protected actions                    governance         
                                  while paused                         decisions          

  ODR-17      Error and recovery  Separate error      PROPOSED         Prevents blind     WP-2 v0.1; WP-6
                                  severity from                        retries and loss   v0.1
                                  retryability;                        of operational     
                                  preserve attempt                     evidence           
                                  history; reconcile                                      
                                  ambiguous external                                      
                                  effects before                                          
                                  retry                                                   

  ODR-18      Shorts Studio       Retain Shorts       PROPOSED         Preserves existing WP-5 v0.1; WP-6
              integration         Studio as a bounded                  work while         v0.1; inherited
                                  specialist engine;                   enforcing common   D1/U1
                                  governed                             workflow controls  
                                  orchestration must                                      
                                  prevent direct                                          
                                  bypass                                                  

  ODR-19      Vertical-slice      Use a synthetic,    PROPOSED         Tests the          WP-6 v0.1
              evidence            deterministic,                       integrated         
                                  non-production test                  contracts without  
                                  path with failure                    external side      
                                  injection                            effects            

  ODR-20      Acceptance evidence Tie evidence to     PROPOSED         Makes acceptance   WP-6 v0.1
                                  requirement,                         attributable and   
                                  source/build                         reproducible       
                                  identity,                                               
                                  environment,                                            
                                  inputs, outputs and                                     
                                  reviewer                                                

  ODR-21      Provider and        Keep interfaces     DEFERRED         These choices are  ADR-002/006;
              operations          provider-neutral;                    not required to    CF-24
                                  defer vendor,                        settle core        
                                  region, sizing and                   contract semantics 
                                  production                                              
                                  operations                                              

  ODR-22      Scope and ownership Carry forward       CARRIED FORWARD  Preserves accepted Accepted owner
                                  single-owner        --- verify       project            decision record;
                                  Creator Mode and    detailed row     boundaries;        project
                                  existing            wording at final original full      constraints
                                  engineering/QA      reconciliation   register wording   
                                  responsibilities;                    should be          
                                  no scope expansion                   reconciled before  
                                                                       final freeze       
  ---------------------------------------------------------------------------------------------------------

## 5. Genuine contract-freeze blockers

The following must be resolved in the detailed contracts before freeze.
They are not safe to leave as implementation-time guesses.

1.  Exact entity fields, nullability, keys, constraints, foreign-key
    behavior, indexes and lifecycle transitions.
2.  ContentVersion schema and its relationship to ContentItem and
    ContentVariant.
3.  Workflow definition/run/task schemas, version pinning and dependency
    rules.
4.  Job and attempt states, terminal outcomes, cancellation and
    remediation.
5.  Lease ownership, fencing, expiry recovery and stale-worker commit
    rejection.
6.  Idempotency scope, conflict semantics, retry classification and
    outbox/inbox recovery.
7.  Worker enrollment, trust transitions, identity proof, capability
    verification and revocation.
8.  Minimum worker isolation and active-job revocation behavior.
9.  Artifact, version, manifest, transfer, validation, quarantine and
    provenance contracts.
10. QA, rights, approval and policy-decision schemas.
11. Exact authorization request/decision binding, expiry and revocation
    semantics.
12. Emergency pause authority, scope, override and recovery.
13. Shared error taxonomy, audit/correlation requirements and interface
    compatibility rules.
14. Shorts Studio adapter contract and mandatory bypass-prevention
    points.
15. WP-6 acceptance evidence schema and the criteria for independent QA
    and owner acceptance.

## 6. Safe deferrals

These may remain deferred only if the provider-neutral contract and
required enforcement hooks are explicit.

  -----------------------------------------------------------------------
  Area                                Deferral
  ----------------------------------- -----------------------------------
  Cloud provider, account, region and Defer
  deployment topology                 

  Hosted database provider and        Defer
  production sizing                   

  Object-storage provider, region and Defer
  replication                         

  Credential issuer and               Defer after security protocol is
  provider-specific token format      defined

  Numerical lease/heartbeat/retry     Defer after semantics, safe bounds
  values                              and configuration ownership are
                                      defined

  Artifact retention, backup and      Defer after lifecycle ownership and
  legal-hold durations                enforcement hooks are defined

  Monitoring vendor and production    Defer
  alert thresholds                    

  Production RPO/RTO and restore      Defer; production readiness cannot
  cadence                             be claimed

  Budget and paid-service activation  Defer; no spending authorized

  Advanced broker, multi-user/team,   Outside P0 scope
  SaaS, billing, multi-brand and      
  broad cloud rendering               
  -----------------------------------------------------------------------

## 7. Owner-reserved decisions

Do not close these under routine delegation:

-   **Security:** minimum isolation guarantees, trust/revocation
    behavior and emergency override authority.
-   **Rights:** evidence requirements and use-specific enforcement where
    they materially affect permitted use.
-   **Authorization:** protected-action scope and any override/exception
    authority.
-   **Data lifecycle:** deletion, legal hold, backup and recovery
    obligations where irreversible or legally material.
-   **External effects:** any permission to upload, publish or perform
    other real-world actions.
-   **Commercial operations:** any paid provider, subscription, usage
    charge, billing exposure or deployment.

Recommendations may be prepared for these areas, but owner authority
remains required.

## 8. Cross-package acceptance invariants

1.  One canonical owner per entity.
2.  Canonical identity is immutable; versions are explicit.
3.  Unknown, missing or ambiguous rights, approval or authorization
    never grant permission.
4.  Approval, authorization, execution and confirmed external outcome
    remain distinct.
5.  Hard QA, rights and policy blockers cannot be bypassed by ordinary
    approval or retry.
6.  Workers execute bounded assignments.
7.  Queue delivery may repeat; idempotency and durable attempts protect
    logical effects.
8.  Artifact versions are immutable and integrity checked; repair
    creates a new version.
9.  Review and approval are attributable and bound to exact versions.
10. Automatic public publishing remains disabled.
11. Shorts Studio remains a bounded specialist engine.
12. Local-only work waits safely when the local worker is unavailable.
13. Hybrid control-plane direction remains architectural only; no
    provider/deployment is selected.
14. Development remains local-first/free-first.
15. No paid services without explicit approval.

## 9. Next decision and freeze sequence

Recommended sequence:

1.  Reconcile the full ODR-01--ODR-22 wording against the source
    register and package-local O/J/W/A/G/F decisions.
2.  Complete the canonical schema appendix and lifecycle transition
    tables.
3.  Complete job, lease, retry, idempotency and outbox/inbox semantics.
4.  Complete worker trust, capability and minimum isolation contracts.
5.  Complete artifact registration/transfer and governance/authorization
    interface schemas.
6.  Resolve owner-reserved decisions in one consolidated review where
    practical.
7.  Update WP-1 through WP-6 and produce one versioned consolidated
    contract baseline.
8.  Request explicit owner approval for detailed contract freeze.
9.  Treat implementation authorization as a separate subsequent
    decision.

## 10. Current disposition

  -----------------------------------------------------------------------
  Area                                Current status
  ----------------------------------- -----------------------------------
  ADR-001--ADR-010                    Accepted

  CF-01--CF-24                        Carried forward as recorded

  WP-1--WP-6                          Design candidates; owner review
                                      required

  Routine resolutions in this         Proposed, not silently accepted
  register                            

  Owner-reserved decisions            Open

  Provider/operational choices        Deferred where safe

  Detailed contract freeze            NOT FROZEN

  Implementation authorization        NOT GRANTED

  Repository changes, tests, Git      Not authorized by this register
  operations or agent execution       

  Paid services, deployment,          Not authorized
  production generation, upload or    
  publishing                          
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## Plain-language explanation

This register is the bridge between the architecture we already agreed
on and a precise implementation contract. It closes routine design
ambiguity where a conservative recommendation is appropriate, while
keeping security, rights, authorization, irreversible data decisions,
external actions and spending under your authority.

A proposed resolution is not the same as an accepted decision. A frozen
contract is not the same as implemented or production-ready software.

**NEXTDECODE principle:** clear contracts first, explicit authority
second, controlled implementation later.
