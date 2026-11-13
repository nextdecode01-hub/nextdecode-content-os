# NEXTDECODE Content OS — P1 Functional Requirements

**Document ID:** ND-P1-REQ-001 | **Version:** 0.1.0-draft | **Date:** 2026-11-04  
**Status:** DRAFT — requirements require P1 scope approval and P0 contract traceability.

## 1. Requirement status

- **Accepted:** Explicitly selected planning requirement or inherited accepted P0 invariant.
- **Recommended:** Assistant-proposed requirement/default, not owner-approved.
- **Open:** Scope/measure/contract requires decision.
- **Blocked:** Implementation depends on P0 freeze or authorization.

## 2. Research and evidence

| ID | Requirement | Status | Acceptance evidence |
|---|---|---|---|
| RES-001 | Support hybrid topic discovery: creator-supplied topics and system-discovered recommendations | Accepted planning direction | Both paths create traceable topic/idea records |
| RES-002 | Select research depth dynamically among Standard, Advanced and Frontier | Accepted planning direction | Research run records selected depth and rationale |
| RES-003 | Provide manual depth override | Accepted planning direction | Explicit override is retained in run metadata |
| RES-004 | Escalate research when evidence gaps, contradictions, uncertainty or risk justify it | Accepted planning direction | Escalation reason and resulting work are auditable |
| EVD-001 | Map material claims to supporting/contradicting evidence | Recommended | Claim-evidence links are queryable and versioned |
| EVD-002 | Distinguish facts, interpretations, hypotheses and forecasts | Recommended | Output schema exposes claim class and uncertainty |
| EVD-003 | Evaluate source authority, relevance, freshness, independence, directness and consistency | Recommended | Evaluation report includes dimension-level findings |
| EVD-004 | Track claim lineage into briefs, scripts and final artifacts | Recommended | Sample artifact traces back to source and evidence versions |
| EVD-005 | Avoid counting syndicated copies of one source as independent corroboration | Recommended | Duplicate/source-family test passes |

## 3. Product formats and creation

| ID | Requirement | Status | Acceptance evidence |
|---|---|---|---|
| CRT-001 | Plan content for Shorts, Long-form, Social, X, Blog, Newsletter and Podcast | Accepted planning scope | Each supported format has a distinct item/workflow contract |
| CRT-002 | Preserve specialized studio boundaries | Accepted P0 invariant | Cross-studio contract tests pass |
| CRT-003 | Integrate existing Shorts Studio rather than replace it | Accepted P0 invariant | Existing engine remains separately callable through adapter |
| CRT-004 | Bind each production run to exact inputs and output artifact versions | Recommended | Manifest resolves immutable input/output references |
| CRT-005 | Support export-oriented delivery | Accepted planning direction | Export bundle is generated with manifest and checksums |
| CRT-006 | Do not enable live publishing through P1 planning | Accepted boundary | No publishing side effect in P1 acceptance environment |

## 4. Quality, rights and review

| ID | Requirement | Status | Acceptance evidence |
|---|---|---|---|
| QLT-001 | Evaluate content quality using explicit outcomes and evidence | Accepted P0 direction | P0 quality result vocabulary used |
| QLT-002 | Preserve hard blockers that ordinary approval cannot override | Accepted P0 invariant | Negative bypass test |
| RGT-001 | Enforce use-specific rights with evidence | Accepted P0 invariant | Rights state and usage scope checked |
| RGT-002 | Unknown/pending/restricted/expired/revoked/denied rights cannot be treated as cleared | Accepted P0 contract direction | Rights negative tests per protected use |
| APR-001 | Bind human approval to exact content/artifact versions | Accepted P0 direction | Changed hash invalidates prior approval as specified by canonical contract |
| APR-002 | Keep approval separate from authorization and external execution | Accepted P0 invariant | Authorization required at protected boundary |

## 5. Learning and feedback

| ID | Requirement | Status | Acceptance evidence |
|---|---|---|---|
| LRN-001 | Collect creator feedback as the highest-priority learning input | Accepted planning direction | Feedback source priority is recorded |
| LRN-002 | Collect audience comments and performance signals as secondary evidence | Accepted planning direction | Signals retain origin and confidence |
| LRN-003 | Separate Research Feedback, Content Feedback and Market Feedback | Accepted planning direction | Classification is explicit and testable |
| LRN-004 | Generate evidence-backed improvement proposals | Accepted planning direction | Proposal has problem, evidence, impact, risk and affected workflow |
| LRN-005 | Stage changes before production activation | Accepted planning direction | Staging result required |
| LRN-006 | Require separate creator authorization for production activation | Accepted planning direction | Stage approval cannot activate production |
| LRN-007 | Keep proposals versioned, reversible and auditable | Accepted planning direction | Rollback restores prior approved configuration |
| LRN-008 | Evaluate candidate/current versions on equivalent tests and data | Recommended | Evaluation report demonstrates comparable conditions |

## 6. Policy and notification governance

| ID | Requirement | Status | Acceptance evidence |
|---|---|---|---|
| POL-001 | Use central policy authority with module-scoped policies inside protected limits | Accepted planning direction | Precedence tests |
| POL-002 | Use hybrid policy enforcement with approved module snapshots | Accepted planning direction | Valid snapshot enforcement test |
| POL-003 | Require fresh central authorization for high-risk operations | Accepted planning direction | Outage negative test |
| POL-004 | Use risk-based snapshot expiry; revocation overrides expiry | Accepted planning direction | Expired/revoked snapshot test |
| POL-005 | Restrict only operations dependent on expired snapshots when continuity can be proven | Accepted planning direction | Independent safe operation continues; dependent operation blocked |
| NOT-001 | Adapt routine digest timing only within creator-approved boundaries | Accepted planning direction | Boundary enforcement test |
| NOT-002 | Keep critical alerts immediate | Accepted planning direction | Critical delivery test under quiet hours |
| NOT-003 | Group/deduplicate notifications without deleting source events | Accepted planning direction | Event ledger remains complete |
| NOT-004 | Reconsider rejected recommendations only with materially new evidence | Accepted planning direction | No duplicate prompt without evidence change |
| NOT-005 | Evaluate cadence using replay, simulation and comparative metrics | Accepted planning direction | Leakage-aware report |
| NOT-006 | Use controlled progressive activation for notification policy changes | Accepted planning direction | Staged rollout state transitions |
| REC-001 | Detect repeated incident patterns and adjust restrictions/monitoring | Recommended | Recurrence scenario test after policy approval |

## 7. Agent orchestration and reliability

| ID | Requirement | Status | Acceptance evidence |
|---|---|---|---|
| AGT-001 | Agents operate under task-scoped contracts and capabilities | Accepted P0 direction | Unauthorized tool/action denied |
| AGT-002 | Child agents cannot exceed parent authority | Recommended | Delegation boundary test |
| AGT-003 | Persist workflow/task state and verified checkpoints | Recommended, P0 dependency | Restart/recovery test |
| AGT-004 | Retry is bounded and error-classified | Accepted P0 direction | Retry exhaustion and dead-letter tests |
| AGT-005 | Reconcile uncertain external side effects before retry | Accepted P0 direction | Simulated timeout prevents duplicate action |
| AGT-006 | Failed/blocked stages cannot produce success-grade artifacts | Recommended | Failure propagation test |
| AGT-007 | Cancellation and recovery preserve valid prior artifacts and audit lineage | Recommended | Interrupted workflow test |

## 8. Cross-cutting requirements

| ID | Requirement | Status | Acceptance evidence |
|---|---|---|---|
| AUD-001 | Keep audit records distinct from operational logs/metrics/traces | Recommended | Audit persists beyond telemetry retention |
| PRV-001 | Maintain provenance from sources/claims to output artifacts | Recommended | End-to-end lineage query |
| OBS-001 | Expose health, queue, workflow, provider and quality operational indicators | Recommended | Health/reporting checks |
| RES-001A | Isolate module failure from independent modules | Recommended | Failure-domain integration test |
| SEC-001 | Revoke identity and capability grants independently | Accepted P0 security direction | Revocation test |
| SEC-002 | Never expose secrets in ordinary logs/prompts/artifacts | Accepted P0 security direction | Secret scanning and redaction tests |
| DAT-001 | Use versioned contracts and validated boundaries | Accepted P0 direction | Schema compatibility tests |
| DAT-002 | Do not create competing sources of truth | Accepted P0 direction | Data ownership/consistency tests |

## 9. P0/P1 boundary requirements

| ID | Requirement | Status |
|---|---|---|
| BND-001 | P0-A remains a narrow vertical slice, not full Control Center/dashboard | Accepted scope constraint |
| BND-002 | Frontend work during P0 is limited to contract-aligned necessary surfaces and integration scaffolding | Accepted scope constraint |
| BND-003 | Broad Control Center expansion is deferred unless separately authorized | Accepted scope constraint |
| BND-004 | P1 implementation begins only after P0 closure/readiness and formal P1 authorization | Blocked prerequisite |
| BND-005 | No public publishing, paid infrastructure or deployment without separate explicit authorization | Accepted P0 invariant |

## 10. Requirement governance

Each requirement must link to:
- source decision/document;
- contract ID/version;
- owning module;
- dependencies;
- risk class;
- positive and negative acceptance tests;
- status and owner;
- evidence artifact.

Requirements that conflict with accepted P0 decisions must be blocked and submitted for reconciliation, not silently rewritten.

