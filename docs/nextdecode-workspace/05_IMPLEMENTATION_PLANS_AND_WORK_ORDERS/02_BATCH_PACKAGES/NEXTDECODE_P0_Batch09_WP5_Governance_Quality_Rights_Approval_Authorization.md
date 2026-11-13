NEXTDECODE CONTENT OS

# P0 Batch 09
WP-5 Governance, Quality, Rights, Approval & Authorization

Design working pack • 01 November 2026

Purpose: define a reviewable candidate governance contract for quality outcomes, claims and evidence, rights, human review/approval, centralized authorization and protected actions. This document is a design candidate, not a frozen policy or authorization to execute production work, upload, distribute or publish.

## 1. Status and source discipline

| Label | Meaning |
| --- | --- |
| ACCEPTED DIRECTION | Recorded owner-accepted decision or invariant; preserve it. |
| DESIGN CANDIDATE | Proposed contract detail requiring authoritative source reconciliation. |
| SOURCE REQUIRED | Exact rule, enum, evidence threshold or transition is not verified in the current source set. |
| OWNER DECISION | A genuinely owner-reserved choice; no inferred approval. |
| NOT AUTHORIZED | No implementation, production generation, external action, upload or publishing is authorized. |

Batch 04 records incomplete exact source wording for CF-03–CF-12, CF-15–CF-19 and CF-23, and a partial authoritative artifact inventory. Therefore, this pack distinguishes accepted governance principles from candidate operational detail. Do not infer missing source wording or silently replace source-defined policy with generic best practice.

## 2. WP-5 mission and responsibility boundary

| WP-5 owns | WP-5 does not own |
| --- | --- |
| Quality outcome vocabulary and hard-blocker semantics | Canonical persistence foundation (WP-1) |
| Claim/evidence and rights-governance policy contract | Durable job orchestration and retry mechanics (WP-2) |
| Review and exact-version human approval contract | Worker registration/trust/credential lifecycle (WP-3) |
| Central authorization decision boundary and policy integration | Artifact binary storage and transfer implementation (WP-4) |
| Protected-action policy and governance audit requirements | Integrated P0 vertical-slice proof and recovery sign-off (WP-6) |
| Fail-closed governance rules across production and distribution | Unapproved automatic public publishing |

WP-5 is the governance authority boundary. Other packages may request decisions and enforce responses, but must not create bypasses or competing policy authorities.

## 3. Accepted governance invariants

- Centralized authorization is the authoritative decision point (CF-22, Option A).

- Approval, authorization, execution and confirmed external outcome are separate facts.

- Hard QA, rights and policy blockers cannot be bypassed by ordinary approval.

- Unknown, missing or ambiguous rights, approval or authorization never grant permission for protected actions.

- Rights are evidence-backed and use-specific; a generic 'rights cleared' label is insufficient unless supported by the governing contract.

- Review and approval bind to an exact content/artifact version and defined purpose.

- Automatic public publishing remains disabled pending separate policy approval.

- Publishing adapters cannot bypass centralized authorization.

- Workers and agents cannot self-approve, self-authorize or self-expand scope.

- Every review, approval, denial, authorization decision, override attempt and protected action is attributable and auditable.

## 4. Governance decision model

| Decision concept | Meaning | Must not be confused with |
| --- | --- | --- |
| Policy | Versioned rule set defining required checks and permitted actions | A single approval record |
| Quality assessment | Structured evaluation of content/output against quality criteria | Rights clearance or authorization |
| Review | Human or automated examination with findings and evidence | Approval |
| Approval | Human acceptance of an exact version for a defined purpose | Permission to execute an external action |
| Authorization | Central policy decision granting/denying a scoped action to a principal | Worker capability or queue access |
| Execution | A bounded worker attempts the authorized action | Successful external outcome |
| Confirmed outcome | Evidence establishes what actually happened externally | API request accepted or local process completed |
| Exception/override | A narrowly governed disposition where policy permits it | A general bypass of hard blockers |

## 5. Quality outcome contract

The recorded quality outcomes are PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW and BLOCKED. These are quality dispositions, not workflow, execution or authorization states.

| Outcome | Candidate interpretation | Protected-action implication |
| --- | --- | --- |
| PASS | All required quality checks pass for the exact version and scope | May satisfy the quality gate; other rights, approval and authorization gates still apply. |
| PASS_WITH_WARNINGS | Required checks pass but non-blocking warnings remain | Proceed only where policy explicitly permits; warnings remain visible and attributable. |
| NEEDS_REVIEW | Human or specialist judgment is required before disposition | Do not treat as cleared for protected action. |
| BLOCKED | A hard blocker or failed mandatory requirement exists | Protected action denied; ordinary approval cannot bypass. |

Exact mapping of individual checks to these outcomes, severity levels and warning thresholds remains SOURCE REQUIRED.

| Quality dimension | Candidate evidence | Critical distinction |
| --- | --- | --- |
| Factual accuracy | Claim-to-source support, dates, quotations and uncertainty | Unsupported claims must not become acceptable merely because style scores are high. |
| Source quality | Source identity, authority, recency, provenance and corroboration | A URL alone is not evidence that a claim is supported. |
| Brand consistency | Approved voice, terminology, visual and editorial constraints | Brand preference cannot override legal/rights/safety blockers. |
| Format/platform compliance | Duration, dimensions, captions, metadata and platform requirements | Technical compliance is separate from permission to publish. |
| Production integrity | Render completion, media validation, audio/video integrity and artifact hashes | A successful render does not establish content quality or rights. |
| Safety/policy | Applicable prohibited or restricted content checks | Hard blockers remain blocking. |
| Accessibility | Captions, legibility, contrast and other required checks | Required checks and thresholds must be sourced. |

## 6. Hard blockers and non-bypass rules

| Blocker class | Examples (illustrative) | Required behavior |
| --- | --- | --- |
| Rights blocker | Unknown/missing/ambiguous license, ownership, consent or use-specific permission | Deny protected use until evidence is resolved. |
| Authorization blocker | No valid central allow decision, wrong scope, expired/revoked grant | Do not dispatch or execute protected action. |
| Approval blocker | Missing, stale, wrong-version or wrong-purpose approval | Require valid approval bound to exact version/purpose. |
| Quality blocker | Mandatory factual, safety, technical or policy check fails | Set BLOCKED; ordinary approval cannot clear. |
| Artifact integrity blocker | Hash mismatch, unsafe/quarantined or incomplete artifact | Do not consume, export or distribute as valid. |
| Identity/trust blocker | Untrusted/revoked worker or invalid credential | Do not assign or continue protected operation. |
| External outcome uncertainty | Timeout after side-effect request; result unknown | Reconcile; do not blindly replay non-idempotent action. |

An override mechanism, if any, must be explicitly defined in governing policy, limited to permitted warning classes, role-scoped, reasoned, time-bounded where appropriate and fully audited. It must never silently bypass a hard blocker.

## 7. Claim and evidence governance

| Concept | Candidate contract | Questions to verify from source |
| --- | --- | --- |
| Claim | Atomic factual assertion used in content | What is the canonical claim identity and version model? |
| Evidence item | A source, document, dataset, recording or observation supporting/refuting a claim | What evidence types and provenance fields are mandatory? |
| Claim-evidence link | Explicit relation with support/refute/context role | Can one claim have conflicting evidence and how is it represented? |
| Source snapshot | Captured source identity/content or relevant excerpt at research time | What capture and retention rules apply? |
| Verification record | Reviewer, method, timestamp, result and scope | Which verification methods are accepted? |
| Confidence/uncertainty | Explicit qualification of strength and limitations | Are numerical confidence scores permitted or discouraged? |
| Unsupported claim | Claim without adequate evidence for intended use | Which quality outcome and remediation are required? |
| Stale evidence | Evidence no longer sufficiently current for the claim | What recency rules apply by claim type? |

- Preserve source provenance and the exact claim wording/version reviewed.

- Distinguish source existence from source support: a source may exist but not support the claim.

- Record contradictory evidence rather than selecting only convenient support.

- Do not convert model confidence or generated citations into verified evidence without an accepted verification process.

- Unsupported claims should be removed, qualified, or escalated according to the governing policy; exact remediation rules are SOURCE REQUIRED.

## 8. Rights and permitted-use model

The accepted direction requires evidence-backed rights and use-specific enforcement. The following is a candidate structure, not a legal determination or final rights taxonomy.

| Rights dimension | Candidate questions | Enforcement implication |
| --- | --- | --- |
| Ownership / control | Who created or controls the source asset/content? | Ownership claim requires provenance/evidence. |
| License / permission | What permission or license applies, and from whom? | Permission must cover the intended action and use. |
| Use purpose | Editorial, commentary, education, promotion, commercial, advertising or other purpose? | Permission may differ by purpose. |
| Territory / audience | Where and to whom may it be distributed? | Restrict or deny outside granted scope. |
| Term / expiry | Is permission time-limited or revocable? | Recheck before use/distribution where required. |
| Modification / derivative | Are edits, adaptations, crops, voiceover or derivative works permitted? | Do not assume derivative permission. |
| Attribution | Is credit required and what form is required? | Required attribution must be preserved in output/metadata. |
| Person / likeness / voice | Are releases/consents required for identifiable people or voices? | Missing or ambiguous consent fails closed where required. |
| Music / stock / third-party assets | What exact license and platform/monetization restrictions apply? | Asset-level evidence and restrictions must flow to final content. |
| Evidence quality | Is the rights evidence authentic, current and attributable? | Unknown/missing/ambiguous evidence cannot grant permission. |

A rights decision must be bound to the asset/content version, intended use, destination and relevant time/territory constraints. A single broad status must not erase these dimensions.

## 9. Review and approval lifecycle

| Candidate state | Meaning | Guard |
| --- | --- | --- |
| NOT_SUBMITTED | No review request exists | No approval implied. |
| SUBMITTED | Exact version and review purpose submitted | Version and evidence references fixed. |
| IN_REVIEW | Review actively underway | Reviewer identity and scope recorded. |
| NEEDS_CHANGES | Findings require correction | Changes create a new version or revision; prior review remains historical. |
| REVIEW_COMPLETE | Required review findings recorded | Does not automatically mean approved. |
| APPROVED | Authorized human approved exact version for defined purpose | Approval scope, actor, timestamp and version must match. |
| REJECTED | Approval refused | Reason and findings retained. |
| WITHDRAWN / EXPIRED | Approval no longer valid for use | Fresh approval required where policy says so. |

These are illustrative state labels. The governing source may define different names and transitions. A material content or artifact change must invalidate or supersede any approval that is version-bound to the prior version.

## 10. Central authorization decision contract

| Input dimension | Candidate requirement | Fail-closed behavior |
| --- | --- | --- |
| Principal | Authenticated user, service or worker identity | Unknown or untrusted principal denied. |
| Action | Specific action such as read, generate, export, upload, publish or delete | Unrecognized action denied. |
| Resource | Exact content/artifact/version/workspace and relevant object | Missing or ambiguous resource scope denied. |
| Purpose | Declared business/editorial purpose | Missing or disallowed purpose denied. |
| Context | Destination, platform, territory, time, environment and other policy context | Missing mandatory context denied. |
| Evidence | Rights, review, approval, QA and trust references required by policy | Missing, stale or mismatched evidence denied. |
| Policy version | Exact policy/rule-set version used for decision | Decision must be reproducible and auditable. |
| Decision | ALLOW or DENY plus reason/obligations as defined by source | Only explicit valid ALLOW permits protected action. |

The central authorization interface is authoritative (CF-22, Option A). Policy decision records should include correlation ID, principal, action, resource/version, context, policy version, result, reason, obligations and timestamp as required by the governing contract.

| Decision property | Rule |
| --- | --- |
| Default | DENY for protected actions unless a valid explicit allow is returned. |
| Scope | Narrowest resource/action/purpose scope necessary. |
| Expiry | Time-bounded or re-evaluated when relevant context changes. |
| Revocation | A prior allow does not guarantee future permission if policy/evidence is revoked or changed. |
| Audit | Every decision is attributable and queryable. |
| Consistency | Adapters and workers call the central authority; no local bypass. |
| Separation | Approval records and authorization decisions remain distinct. |

## 11. Protected action gate matrix

| Action | Quality | Rights | Human approval | Central authorization | Default |
| --- | --- | --- | --- | --- | --- |
| Internal draft generation | Applicable checks; unresolved issues visible | Check source asset use constraints | Not necessarily required unless policy says | Required for protected resources/actions | Allow only within authorized internal scope |
| Production render | Required checks for inputs and output | All incorporated assets cleared for intended production use | Exact-version approval if required by policy | Explicit allow for render scope | Block on unresolved hard blockers |
| External export/share | Required checks and artifact integrity | Destination/purpose-specific rights | Required where policy requires | Explicit allow for destination and version | Deny by default |
| Platform upload | Required QA and platform compliance | Platform, territory, monetization and asset permissions | Human approval required | Explicit allow for platform/action/version | Deny without all gates |
| Public publishing | Required QA; no hard blockers | Rights cleared for public use and destination | Human approval required | Explicit central allow | Automatic public publishing disabled |
| Deletion/retention action | Audit/retention checks | Rights/privacy/hold implications assessed | Authorized disposition where required | Explicit allow | Deny if held or uncertain |
| Credential/worker admin | Not a content QA action | Not applicable unless assets involved | Separate admin approval policy | Privileged central authorization | Deny by default |

This matrix is a candidate interpretation of accepted invariants, not a replacement for the original action policy or platform-specific rules.

## 12. Exception and override governance

| Question | Candidate control | Status |
| --- | --- | --- |
| Can a hard blocker be overridden by ordinary approval? | No; accepted invariant prohibits ordinary approval bypass. | ACCEPTED DIRECTION |
| Can warnings be accepted? | Only where the governing policy explicitly permits; record exact warning and rationale. | SOURCE REQUIRED |
| Who may grant an exception? | Only a specifically authorized role/principal under a defined policy. | SOURCE REQUIRED |
| What must an exception contain? | Exact resource/version, action, purpose, reason, evidence, actor, scope and expiry/review point. | DESIGN CANDIDATE |
| Can an exception authorize a different version? | No; it must bind to exact version and defined scope. | DESIGN CANDIDATE |
| Can an exception bypass rights law or external platform rules? | No; no internal override can create rights that do not exist. | GOVERNING LEGAL/POLICY CONSTRAINT |
| Can agents approve their own work? | No; separation of duties and human approval apply. | ACCEPTED DIRECTION |

## 13. Audit, traceability and evidence retention

- Record reviewer, approver and authorizer as distinct actor roles where applicable.

- Bind every review and approval to exact content/artifact version, purpose and relevant evidence.

- Record policy version, authorization input scope, allow/deny result and reason.

- Retain quality findings, hard-blocker classification, remediation and subsequent reassessment.

- Record rights evidence source, scope, validity/expiry and use-specific determination.

- Record attempted bypasses, denied actions, exception requests and approved exceptions.

- Correlate governance events with workflow, job, attempt, worker, artifact and distribution records.

- Apply authoritative retention, privacy and legal-hold rules; exact periods remain SOURCE REQUIRED.

## 14. Acceptance test catalogue

| Test ID | Scenario | Expected result | Status |
| --- | --- | --- | --- |
| WP5-QA-01 | All mandatory checks pass | PASS recorded for exact version; other gates still evaluated | NOT RUN |
| WP5-QA-02 | Only non-blocking warning remains | PASS_WITH_WARNINGS only if policy permits; warning retained | NOT RUN |
| WP5-QA-03 | Mandatory human judgment missing | NEEDS_REVIEW; protected action blocked | NOT RUN |
| WP5-QA-04 | Hard blocker exists and ordinary approver clicks approve | BLOCKED remains; approval cannot bypass | NOT RUN |
| WP5-CLM-01 | Claim has no supporting evidence | Unsupported claim flagged; protected publication blocked per policy | NOT RUN |
| WP5-CLM-02 | Source exists but does not support claim | Claim remains unsupported; source existence not treated as support | NOT RUN |
| WP5-RGT-01 | Rights are unknown, missing or ambiguous | Protected use denied | NOT RUN |
| WP5-RGT-02 | License permits one purpose but not intended destination/use | Use denied for out-of-scope purpose | NOT RUN |
| WP5-RGT-03 | Approval/rights evidence refers to old artifact version | Current version remains uncleared | NOT RUN |
| WP5-APR-01 | Approval refers to exact version and purpose | Approval valid only within matching scope | NOT RUN |
| WP5-APR-02 | Content changes after approval | Old approval cannot authorize changed version | NOT RUN |
| WP5-AUTH-01 | No central authorization decision exists | Protected action denied | NOT RUN |
| WP5-AUTH-02 | Local publisher adapter attempts direct bypass | Adapter call blocked; denial audited | NOT RUN |
| WP5-AUTH-03 | Authorization revoked before execution | Protected action stopped or safely reconciled | NOT RUN |
| WP5-PUB-01 | Public publish requested without human approval | No public action; automatic publishing remains disabled | NOT RUN |
| WP5-AUD-01 | Review/approval/authorization event occurs | Actor, exact version, scope, policy and correlation are auditable | NOT RUN |
| WP5-EXC-01 | Agent attempts self-approval or self-authorize | Denied and audited | NOT RUN |

## 15. Integration contract with WP-1 to WP-4 and WP-6

| Package | WP-5 dependency / contract | Required integration proof |
| --- | --- | --- |
| WP-1 Domain & persistence | Persist review, approval, policy decision, rights/evidence and audit references without collapsing state machines | Schema supports exact-version binding, provenance and audit. |
| WP-2 Workflow/jobs | Expose governance checks at dispatch and protected stage boundaries | Denied action never dispatched; uncertain outcome reconciled. |
| WP-3 Worker trust | Consume worker identity/trust and scoped credentials; worker capability is not permission | Untrusted/revoked worker denied; no self-expansion. |
| WP-4 Artifacts | Consume exact artifact version, integrity and quarantine status; govern access/export/deletion | Invalid/quarantined artifact cannot pass policy gate. |
| WP-6 Integration | Verify full vertical slice, failure recovery and no-bypass paths | End-to-end tests demonstrate every gate and external outcome boundary. |

## 16. Open and deferred decisions

| Item | Disposition | Closure trigger |
| --- | --- | --- |
| Exact quality severity/check-to-outcome mapping | SOURCE REQUIRED | Import governing QA policy and original CF wording. |
| Exact claim/evidence schema and verification method | SOURCE REQUIRED | Import data dictionary and research/claim contracts. |
| Rights taxonomy and evidence sufficiency rules | SOURCE REQUIRED | Import authoritative rights policy and source CF rows. |
| Role/permission matrix and exception authority | SOURCE REQUIRED / OWNER-RESERVED where applicable | Inspect approved authorization policy; ask owner only for truly reserved choices. |
| Approval expiry/revocation rules | SOURCE REQUIRED | Import lifecycle and approval contract. |
| Platform-specific upload/publish conditions | SOURCE REQUIRED | Approved platform policy and distribution adapter contracts. |
| Retention periods and audit data retention | SOURCE REQUIRED | Authoritative retention/privacy/legal policy. |
| Exact policy evaluation API schema | SOURCE REQUIRED | Import API/event contract and WP-5 spec. |
| Automatic publishing policy | DISABLED pending separate policy approval | Separate explicit owner policy decision; not approved here. |

## 17. Draft WP-5 work order — not active

| Field | Draft definition |
| --- | --- |
| Objective | Implement centralized governance for quality outcomes, claims/evidence, rights, exact-version review/approval and protected-action authorization. |
| Preconditions | Authoritative CF/QA/rights/approval/API sources verified; contract freeze approved; WP-1 through WP-4 interfaces reconciled; separate implementation authorization issued. |
| Allowed after authorization | Implement policy decision interface, evidence/rights checks, QA outcome enforcement, review/approval records, audit and negative integration tests within file allowlist. |
| Forbidden without separate approval | Automatic public publishing, policy bypass, self-approval, paid/provider activation, deployment, destructive migration, broad Git operations or agent self-expansion. |
| Required outputs | Versioned policy contract, central authorization integration, governance persistence, test evidence, audit traces and traceability matrix. |
| Exit criteria | All mandatory hard-blocker, rights, exact-version, authorization and no-bypass tests pass; independent read-only QA disposition recorded. |
| Rollback boundary | Policy changes must be versioned and reversible without silently granting permissions; emergency deny remains available under approved procedure. |

## 18. Readiness decision

| Question | Current answer |
| --- | --- |
| Is centralized authorization accepted? | Yes — CF-22, Option A. |
| Are hard blockers and fail-closed rights/authorization accepted? | Yes — core invariants are recorded as accepted. |
| Is this the final governance policy? | No — candidate only; exact source wording and detailed policy remain to be reconciled. |
| Is automatic public publishing enabled? | No — disabled pending separate policy approval. |
| Is implementation or publishing authorized? | No. |
| Can this be used for design review? | Yes — reconcile exact rules and schemas against authoritative sources before freeze. |

Recommended next step: reconcile WP-5 against the original CF source pack, QA/rights/approval policy, API/event contract and retention rules. Then prepare WP-6 vertical-slice integration, recovery and acceptance evidence design.

END OF BATCH 09


## Source document metadata (preserved from DOCX)

- **Footer:** NEXTDECODE • P0 design candidate • Not frozen • Not implementation authorization

