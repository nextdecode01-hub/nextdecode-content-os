# NEXTDECODE --- P0 WP-0 Preservation & Contract-Gap Register

**Version:** 1.0 \| **Date:** 1 November 2026\
**Repository:** `/home/demon/shorts_studio`\
**Mode:** Read-only assessment based on the user-provided local
snapshot, prior remote-source inspection and historical handovers.

## 1. Status and recommendation

**WP-0 recommended disposition: CONDITIONALLY COMPLETE as a baseline and
preservation assessment only.** Runtime verification, fresh test
execution, independent QA and production-readiness verification remain
unverified or incomplete.

WP-0 does not authorize implementation, cleanup, Git operations, tests,
deployment or production publishing.

## 2. Preservation snapshot

Latest user-provided snapshot: - Branch `main`, reported tracking
`origin/main`. - Remote `main` SHA:
`9d38f81ba4f8022d0e820b6a5e1fe2a0fc288c8c`. - 23 tracked files
modified. - 56 untracked paths reported (paths, not a verified count of
individual files). - No staged changes reported. - `git diff --stat`
output was blank in the supplied capture; this is an output-capture
limitation, not proof that there are no modifications.

**Preservation rules** 1. Preserve all 23 modified tracked files and all
56 reported untracked paths. 2. Do not delete, reset, revert, stash,
overwrite, rename or clean up local work without explicit authorization.
3. Do not broadly stage, commit, push or alter branches/remotes without
explicit authorization. 4. Preserve root-level and `app/publish/`
uploader paths until call-site ownership is reconciled. 5. Preserve
tests, fixtures, docs, generated evidence and legacy-looking files. 6.
Never weaken assertions to make tests pass. 7. Historical reports are
evidence of past runs, not fresh verification.

Known untracked WIP includes `app/render/`, research claim/lineage
modules, script evidence, visual beats/shotplan/storyboard/chain
modules, voice text preparation, `run_tracker.py`, numerous QA tests,
Phase 10/11 reports, fixtures and audit scripts. This is not a complete
path-by-path inventory.

## 3. Existing work to preserve and reuse

  -----------------------------------------------------------------------
  Area                    Existing work           Reuse boundary
  ----------------------- ----------------------- -----------------------
  Research                Research desk/selector, Evolve through
                          atomic research,        contracts/adapters
                          claims, lineage         

  Script/evidence         Script pipeline/studio  Preserve current
                          and evidence support    pipeline behavior

  Visual planning         Beats, shot plan,       Retain specialist
                          storyboard, visual      visual components
                          chain, cutouts, vision  
                          review                  

  Rendering               Assembly, FFmpeg tools, Keep Shorts Studio as
                          shots, subtitles, audio specialist engine
                          diagnostics             

  Run tracking            `run_tracker.py`,       Reuse as local
                          manifests, promotion    provenance foundation;
                          journal                 runtime verification
                                                  needed

  Review                  Review bundle, approval Transitional evidence,
                          integrity, CSV ledger   not canonical event
                                                  history

  Storage                 SQLite                  Migration/adaptor
                          `content_records`,      starting point, not
                          archive, JSON metadata  authoritative workflow
                                                  store

  Runner                  Authenticated           Preserve route contract
                          fixed-command n8n       while designing worker
                          runner                  abstraction

  Publishing              Parent publisher and    Do not assume all paths
                          platform adapters       enforce central
                                                  authorization
  -----------------------------------------------------------------------

## 4. Remote baseline findings

From prior read-only inspection of the remote snapshot, not a fresh
local inspection: - `api/main.py` uses process-local in-memory jobs; it
is not durable shared state. - `n8n_runner.py` is a restricted
authenticated local command runner, not a worker registry or lease-based
dispatcher. - n8n calls `/run/generate` and `/run/publish` on the
runner, not FastAPI `/start`. - Inspected `compose.yaml` contained n8n
and runner, but no PostgreSQL-backed shared workflow store or durable
queue. - `workspace_sync.py` uses SQLite `content_records` and external
mirrors; this is not the canonical workflow/task model. -
`review_ledger.py` is a CSV feedback ledger; `review_bundle.py` is a
review package, not immutable approval-event history. - Direct platform
adapters could be invoked separately from `publish_all.py`. - Inspected
YouTube upload paths explicitly set public privacy. - Analytics are
local JSON and not proven linked to immutable canonical content
versions. - Remote dependency map was a 26 October snapshot and may be
stale.

## 5. Contract-gap register

  ------------------------------------------------------------------------------
  Foundation              Gap against accepted           Priority
                          architecture                   
  ----------------------- ------------------------------ -----------------------
  Canonical identity      UUIDv7 immutable IDs and       Critical
                          explicit versions across       
                          entities                       

  Domain model            Canonical content, variant,    Critical
                          workflow, task, execution,     
                          artifact and governance        
                          relationships                  

  Persistence             Authoritative shared-state     Critical
                          persistence                    

  Execution               Durable queue, outbox/inbox,   Critical
                          idempotency and recovery       

  Workers                 Registration, trust, leases,   High
                          capability authorization and   
                          isolation                      

  Artifacts               Immutable registry, integrity, High
                          versioning and controlled      
                          transfer                       

  Governance              Central authorization enforced Critical
                          across all paths               

  Rights                  Use-specific evidence and      Critical
                          fail-closed enforcement        

  Quality                 Hard enforcement for           Critical
                          unsupported claims and policy  
                          blockers                       

  Approval                Attributable approval bound to Critical
                          exact versions                 

  Audit                   Canonical tamper-evident event High
                          history                        

  Analytics               Link metrics to canonical      Medium
                          content/version/distribution   

  Hybrid                  Cloud control plane/local      High
                          worker contracts, recovery and 
                          security                       
  ------------------------------------------------------------------------------

## 6. Inherited blocker register

These findings are from prior Phase 10/11 reports and inspections; they
have not been freshly retested here.

  -----------------------------------------------------------------------
  ID                      Finding                 Required outcome
  ----------------------- ----------------------- -----------------------
  G1                      Storyboard gate default Explicit approval
                          reported as `warn`      required for protected
                                                  rendering

  G2                      Rights not enforced     Rights checked
                          end-to-end at           centrally for intended
                          publishing              use; fail closed

  G3                      Unsupported claims      Unsupported material
                          warning-only            claims block
                                                  publication readiness

  U1                      Direct adapters could   Central authorization
                          bypass parent publisher at every adapter
                                                  boundary

  D1                      Direct pipeline could   One governed execution
                          bypass governed         path; bounded test
                          orchestration           modes

  T1                      Shot/beat/render        Stable namespaced IDs,
                          traceability incomplete versioned plans and
                                                  render manifests

  R1                      Run Tracker             Independent runtime,
                          runtime/recovery        crash and recovery
                          evidence missing        verification
  -----------------------------------------------------------------------

Other reported concerns: editorial critic variability; shell failure
propagation; incomplete plan-hash/approval linkage; incomplete
coverage/query-switch reporting; no approved non-public upload
destination or safe upload dry-run; independent Kilo QA
pending/unavailable.

## 7. Phase 10/11 evidence status

**Phase 10 --- OpenCode owner** - Historical final handover reported 535
passing tests and focused checks. - Run Tracker, promotion journal and
review provenance integration were reported. - Remaining limitations
included no verified live production run, no runtime storm/recovery
proof, post-promotion edge cases and pending independent Kilo QA.

**Phase 11 --- Qoder owner** - Historical handovers reported ShotPlan
traceability implementation and focused tests. - G1 remained a critical
blocker. - Other reported gaps: rights/claims enforcement, direct
publisher/pipeline bypasses, incomplete traceability and no approved
non-public destination. - Stage A/B was design proposal awaiting
approval before Stage C, not implementation authorization.

**Kilo** is the independent read-only QA owner; independent acceptance
evidence was not available in the supplied status. All historical test
counts are not fresh test results.

## 8. WP-0 closure boundary

WP-0 has enough evidence to record the remote baseline, user-supplied
local snapshot, preservation boundaries, Phase 10/11 ownership/status,
contract gaps and blockers.

It does not establish current local runtime behavior, fresh test
results, independent QA acceptance, formal contract freeze, production
readiness or permission to modify the repository.

Do not repeat Git inventory solely to reconfirm the supplied snapshot.

## 9. Next step

Proceed to **Artifact 08 --- Detailed Contract Freeze** as
design/documentation only: 1. Consolidate accepted decisions into one
authoritative reference. 2. Complete canonical entities and
relationships. 3. Define state machines and API/event contracts. 4.
Define worker identity, trust, leases and capabilities. 5. Define
artifact registration, integrity, versioning and transfer. 6. Define
centralized authorization, QA, rights, approval and publishing
enforcement. 7. Define idempotency, retries, recovery and audit. 8.
Define acceptance criteria for WP-1 through WP-6.

WP-1 implementation remains unauthorized pending formal owner approval
and separate explicit implementation authorization.
