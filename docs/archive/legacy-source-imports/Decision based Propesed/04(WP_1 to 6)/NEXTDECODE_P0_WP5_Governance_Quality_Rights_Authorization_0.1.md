# NEXTDECODE — P0 WP-5
## Governance, Quality, Rights & Authorization Foundation

**Version:** 0.1  
**Status:** DESIGN CANDIDATE — OWNER REVIEW REQUIRED  
**Scope:** P0 foundation  
**Implementation status:** Not authorized

---

## 1. Purpose

Establish the governance boundary that prevents unsafe, unreviewed, unapproved or unauthorized consequential actions across NEXTDECODE.

WP-5 connects quality assessment, rights assessment, human review and approval, centralized authorization, policy enforcement, emergency pause and auditability.

The objective is not to build every future policy catalogue in P0. It is to establish enforceable interfaces and a central decision boundary so that studios, workers, APIs and distribution adapters cannot independently bypass governance.

## 2. Decision labels

- **ACCEPTED:** Established by accepted ADR/CF decisions.
- **SOURCE-DEFINED:** Required by the P0 specification or contract sources.
- **RECOMMENDED:** Proposed design detail for owner review.
- **OPEN:** Requires further decision or evidence.
- **DEFERRED:** Intentionally postponed.

This document is a design candidate. It does not freeze every policy schema or authorize implementation.

## 3. Accepted governance baseline

The following directions are already accepted:

### Quality — CF-19 / ADR-008

- One shared QA result contract across studios.
- QA runs are immutable and bound to exact target versions.
- Canonical outcomes: `PASS`, `PASS_WITH_WARNINGS`, `NEEDS_REVIEW`, `BLOCKED`.
- Individual checks are evidence-backed.
- Hard blockers are centrally enforced and cannot be bypassed by ordinary approval.
- Studio-specific checks map to the shared contract.
- Scores are supplementary and cannot override blockers.
- QA remains separate from rights, approval and authorization.

### Rights — CF-20 / ADR-009

- Contract 07 owns the canonical rights assessment framework.
- Rights decisions are evidence-backed and use-specific.
- Accepted rights states:
  - `UNKNOWN`
  - `PENDING_REVIEW`
  - `CLEARED`
  - `RESTRICTED`
  - `EXPIRED`
  - `REVOKED`
  - `DENIED`
- Permission is evaluated against asset, intended use, platform, geography, time, commercial context and modification/attribution conditions.
- Unknown rights fail closed for protected uses.
- Rights restrictions propagate through artifact lineage.
- Studios and distribution adapters cannot override restrictions.
- Ambiguous/high-risk cases may require human legal review.
- This framework is not blanket rights clearance or legal advice.

### Approval — CF-21

- Central Governance / Contract 07 owns the approval framework.
- Review packages are immutable snapshots.
- Human decisions are attributable and bound to exact versions and scope.
- Accepted decisions:
  - `APPROVED`
  - `REJECTED`
  - `CHANGES_REQUESTED`
  - `EXPIRED`
  - `REVOKED`
- QA blockers cannot be bypassed by ordinary approval.
- Changed content, rights or destination may require re-review.
- Approval is distinct from authorization and execution.
- Human approval before publishing remains required.
- Automatic publishing remains disabled.

### Authorization — CF-22 / ADR-007

**Explicit owner decision: Option A — Centralized authorization.**

- One central governance authority makes authorization decisions.
- APIs, studios, workers and distribution adapters enforce those decisions.
- Default-deny and fail-closed behavior apply.
- Least privilege is required.
- Authorization binds to exact action, resource, version and destination.
- Expiry and revocation are enforced.
- Approval and authorization remain separate.
- Agent delegation cannot expand authority.
- No domain-local competing authorization authority.

## 4. Four separate governance concepts

These concepts must never be collapsed into one status or one button.

| Concept | Question answered | Result |
|---|---|---|
| Review / QA | Does this exact version meet required checks? | Evidence-backed QA result |
| Rights assessment | Is this intended use permitted by the available rights evidence? | Use-specific rights decision |
| Approval | Has the accountable human accepted this exact version and scope? | Attributable human decision |
| Authorization | Is this actor allowed to perform this exact action on this exact resource, version and destination now? | Central policy decision |

Execution is a fifth, separate step: an authorized adapter or worker performs the action and records the outcome.

**Critical invariant:** Approval is not authorization. Authorization is not execution. An execution request is not proof of successful completion.

## 5. Shared policy evaluation interface

**RECOMMENDED logical interface — exact API schema remains open.**

A policy evaluation request should identify:

- Request and correlation identity.
- Actor identity and actor type (human, worker, service or agent).
- Requested action.
- Target resource type and canonical ID.
- Exact content/artifact/version references where relevant.
- Intended destination and account/platform context where relevant.
- Intended use and commercial context where relevant.
- Relevant rights, QA, review and approval evidence references.
- Policy version or policy-selection context.
- Requested execution time or validity context.

A policy evaluation result should include:

- Decision: `ALLOW` or `DENY` (candidate interface vocabulary).
- Stable reason code.
- Applicable policy/version reference.
- Evaluated actor/action/resource/version/destination scope.
- Evidence references used.
- Evaluation timestamp.
- Expiry or validity boundary where applicable.
- Correlation and audit references.
- Safe remediation guidance where appropriate.

`ALLOW` is not a perpetual permission. It is bound to the evaluated scope and validity conditions.

**OPEN:** Exact request/response schema, reason-code catalogue, policy version selection and evaluation API protocol.

## 6. Central protected-action authorization

Every protected action must pass through the central authorization authority.

### Protected action examples

- Accessing restricted artifacts.
- Exporting or sharing content.
- Sending content to an external service.
- Creating or updating a platform upload.
- Publishing or scheduling publication.
- Deleting or irreversibly retiring governed records.
- Delegating consequential actions to agents or workers.

The exact protected-action catalogue is **OPEN** and must be aligned with the canonical contracts.

### Required checks

Before allowing a protected action, evaluate:

1. Actor identity and trust.
2. Actor's explicitly granted authority.
3. Requested action.
4. Exact resource and immutable version.
5. Destination, account and platform where applicable.
6. Current rights state and intended-use scope.
7. Current QA outcome and hard blockers.
8. Human approval and exact approval scope, when required.
9. Expiry, revocation and policy version.
10. Emergency pause state.
11. Any additional applicable safety or operational policy.

If a required fact is missing, ambiguous, expired or unverifiable, deny or hold the protected action according to the applicable policy. Never silently infer permission.

## 7. QA result contract

### Accepted outcomes

| Outcome | Meaning |
|---|---|
| `PASS` | Required checks passed |
| `PASS_WITH_WARNINGS` | Checks passed with visible warnings |
| `NEEDS_REVIEW` | Human or specialist review is required |
| `BLOCKED` | One or more hard blockers prevent progression |

### QA run requirements

- Immutable run identity.
- Exact target entity and version references.
- QA contract/schema version.
- Policy version.
- Individual check identifiers and outcomes.
- Evidence references.
- Severity and blocker classification.
- Findings and remediation guidance.
- Evaluator identity and timestamp.
- Correlation/run context.

### Enforcement

- A `BLOCKED` result prevents protected downstream action.
- Hard blockers cannot be bypassed by ordinary human approval.
- Numeric quality scores cannot override explicit blockers.
- Studio-specific checks map to the shared QA contract.
- QA results do not grant rights, approval or authorization.
- A new target version requires QA evidence bound to that version.

**OPEN:** Full check catalogue, severity taxonomy, warning policy and studio-specific mapping. P0 requires the shared interface and enforcement behavior, not every future check.

## 8. Rights assessment and use-specific permission

Rights are not a generic property that can be reduced to “file allowed”.

### Accepted rights states

`UNKNOWN`, `PENDING_REVIEW`, `CLEARED`, `RESTRICTED`, `EXPIRED`, `REVOKED`, `DENIED`.

### Assessment dimensions

The decision must consider, where applicable:

- Asset or source material.
- Intended use.
- Platform and destination.
- Geography.
- Time/validity period.
- Commercial or monetization context.
- Modification/adaptation conditions.
- Attribution requirements.
- Evidence and applicable restrictions.
- Relevant artifact lineage.

### Enforcement rules

- `UNKNOWN` and `PENDING_REVIEW` do not grant protected-use permission.
- `RESTRICTED` permits only the uses explicitly supported by its restrictions.
- `EXPIRED`, `REVOKED` and `DENIED` cannot be treated as `CLEARED`.
- Rights restrictions propagate through derived artifacts and manifests.
- A studio or distribution adapter cannot override rights restrictions.
- Changed intended use, destination or relevant rights evidence may require reassessment.
- Ambiguous/high-risk cases are escalated for appropriate human/legal review.

The older vocabulary `PENDING_VERIFICATION` and `PROHIBITED` is not substituted into the accepted vocabulary without an approved migration plan.

## 9. Review package and human approval

### Review package

**ACCEPTED:** Review packages are immutable snapshots.

**RECOMMENDED contents:**

- Review package identity and version.
- Content item and variant references.
- Exact script, visual, audio, render and manifest artifact versions.
- QA run and findings.
- Rights assessment and evidence references.
- Intended destination and scope.
- Warnings and unresolved questions.
- Policy versions.
- Package creation time and producer identity.

The package should be reproducible as the exact material the reviewer saw.

### Human decision record

A decision should record:

- Decision ID.
- Reviewer identity and authority context.
- Exact review package/version.
- Exact content/artifact versions and intended scope.
- Decision value.
- Reason/comments or required changes.
- Timestamp.
- Expiry or revocation context where applicable.
- Correlation and audit references.

### Accepted decision vocabulary

`APPROVED`, `REJECTED`, `CHANGES_REQUESTED`, `EXPIRED`, `REVOKED`.

Approval is not transferable to a materially changed version, changed rights scope or changed destination unless policy explicitly permits that exact scope.

Ordinary approval cannot override hard QA, rights, safety or integrity blockers.

## 10. Authorization record and exact binding

**RECOMMENDED logical authorization record — exact schema remains open.**

An authorization grant should bind to:

- Canonical authorization ID.
- Actor identity and actor type.
- Exact action.
- Exact resource identity.
- Exact content/artifact/version or hash where applicable.
- Exact destination/platform/account where applicable.
- Relevant approval reference, if required.
- QA and rights evidence references.
- Policy version and decision evidence.
- Issued-at and expiry timestamps.
- Revocation status and reason.
- Issuing governance authority.
- Correlation/audit references.

A grant for one artifact hash cannot authorize a different hash. A grant for one destination cannot authorize another. A grant for one action cannot imply a different action.

Authorization must be re-evaluated when required scope or evidence changes.

## 11. Distribution and adapter enforcement

Every distribution route must enforce the same centralized authorization boundary.

### Required rules

- Distribution adapters cannot self-authorize.
- Direct platform adapters cannot bypass the parent publisher governance gate.
- Direct pipeline calls cannot bypass governed orchestration and required policy checks.
- Missing authorization denies the protected action.
- Expired or revoked authorization denies the protected action.
- Mismatched artifact/version/hash denies the protected action.
- Mismatched destination/account/platform denies the protected action.
- Hard rights, QA, safety and integrity blockers remain enforced.
- Automatic public publishing remains disabled.
- Human approval before publishing remains required.
- No live publishing is performed during WP-5 tests.

A successful authorization decision still does not prove that an external platform action succeeded. The execution result must be separately recorded and reconciled.

## 12. Emergency pause

**SOURCE-DEFINED:** An emergency pause blocks new consequential protected actions.

**RECOMMENDED behavior:**

- Central pause state is authoritative.
- Protected-action checks consult pause state at execution time.
- New protected actions are denied while pause is active.
- Pause activation/deactivation is attributable and audited.
- Deactivation does not automatically replay previously denied actions.
- In-flight external actions are reconciled; do not assume they were cancelled.
- Pause must not be bypassable by direct adapters, workers or agents.

**OPEN:** Exact pause scope, authorized activators, recovery/deactivation authority, behavior for in-flight actions and operator notification.

## 13. Agent delegation and authority boundaries

- Agent delegation cannot expand the delegator's authority.
- Agent instructions cannot override central policy.
- An agent cannot approve its own consequential action.
- An agent cannot convert a review recommendation into authorization.
- Worker capability does not imply human, administrative or publishing authority.
- Administrative, production, QA and publishing permissions remain separated.
- Missing or ambiguous authority fails closed.

## 14. Audit and explainability

Record attributable evidence for:

- Policy evaluation requests and decisions.
- QA runs and individual checks.
- Rights assessments and evidence changes.
- Review package creation.
- Human approvals, rejections and change requests.
- Authorization issuance, denial, expiry and revocation.
- Emergency pause activation and release.
- Protected-action execution requests and outcomes.
- Adapter denials and bypass-attempt detections.
- Reconciliation of ambiguous external actions.

Audit records should preserve exact entity/version/destination scope and policy version. Secrets and unnecessary sensitive data must not be logged.

An authorized owner should be able to determine why an action was allowed or denied without exposing credentials or unrestricted diagnostic data.

## 15. Inherited Phase 11 risks to retain as explicit verification targets

These findings come from historical reports and have **not** been freshly retested in this design step:

- **G1:** Storyboard approval gate reportedly defaults to `warn`, not enforced by default.
- **G2:** Rights evidence reportedly not enforced end-to-end by publishing.
- **G3:** Unsupported factual claims reportedly warning-only.
- **U1:** Direct platform adapters reportedly bypass parent publisher gate.
- **D1:** Direct pipeline reportedly bypasses governed orchestration/run identity/quality gates.
- **T1:** Shot/beat/render traceability reportedly incomplete.
- **R1:** Run Tracker runtime/recovery evidence reportedly missing.

WP-5 must not be declared implemented or accepted merely because these risks are documented. They require authorized engineering and independent evidence.

## 16. Proposed acceptance criteria

These are design targets, not executed tests.

1. Missing authorization denies every protected action.
2. Expired authorization is denied.
3. Revoked authorization is denied.
4. Authorization for a different artifact version/hash is denied.
5. Authorization for a different destination is denied.
6. A `BLOCKED` QA result cannot pass through ordinary approval.
7. Hard rights restrictions cannot be overridden by studio or distribution adapters.
8. Unknown or pending rights block the affected protected use.
9. Rights scope mismatch denies the requested use.
10. Approval is attributable and bound to the exact reviewed version and scope.
11. Changed content or destination triggers the applicable re-review/re-authorization policy.
12. Emergency pause blocks new protected actions across all adapters.
13. Direct platform adapters cannot bypass the central gate.
14. Direct pipeline execution cannot bypass required governance checks.
15. Policy denials cannot be bypassed through retries.
16. Every policy decision is auditable with policy version and evidence references.
17. No live publishing occurs during WP-5 tests.
18. Dry-run cannot silently become live execution.
19. Agent delegation cannot expand authority.
20. QA, rights, approval, authorization and execution remain distinct records/states.

## 17. Open decisions

| ID | Open item | Required before |
|---|---|---|
| G-01 | Exact policy evaluation request/response schema | Contract freeze |
| G-02 | Protected-action catalogue | Governance implementation |
| G-03 | Policy reason-code and severity catalogue | Policy implementation |
| G-04 | QA check catalogue and studio mapping | Studio enforcement |
| G-05 | Rights evidence schema and detailed use matrix | Rights implementation |
| G-06 | Review package exact schema and snapshot strategy | Approval implementation |
| G-07 | Approval expiry/revocation and re-review rules | Approval implementation |
| G-08 | Authorization grant schema and revocation propagation | Authorization implementation |
| G-09 | Emergency pause scope and operator authority | Operational readiness |
| G-10 | In-flight external action reconciliation | Distribution integration |
| G-11 | Policy version rollout/compatibility strategy | Policy deployment |
| G-12 | Legal escalation and high-risk rights review procedure | Rights operations |
| G-13 | Audit retention and access policy | Operational governance |
| G-14 | Complete adapter/pipeline bypass inventory | Authorized Phase 11 verification |

No new rights vocabulary, approval vocabulary or competing authorization authority is introduced here.

## 18. Dependencies and handoffs

- **WP-1:** Canonical identity, versioning, ownership and relationships.
- **WP-2:** Durable jobs, attempts, event history and recovery.
- **WP-3:** Worker identity, trust, capabilities and scoped credentials.
- **WP-4:** Immutable artifacts, manifests, integrity and transfer.
- **WP-6:** End-to-end negative tests, emergency pause tests, audit reconstruction and independent QA.

Contract 07 remains the canonical governance/rights/approval ownership boundary. Studios and adapters consume the shared interfaces; they do not create competing governance authorities.

## 19. Implementation safety boundary

This document does not authorize:

- Repository inspection or changes.
- Agent execution or assignment.
- Policy activation against production traffic.
- Credential or permission changes.
- Cloud/provider activation or paid services.
- Live production rendering, external upload or publishing.
- Enabling automatic public publishing.
- Changing existing Phase 10/11 ownership.
- Claiming inherited blockers are fixed without fresh evidence.

Any such action requires separate appropriate owner authorization.

## 20. Plain-language explanation

Think of governance as the security checkpoint before NEXTDECODE performs an important action.

First, QA checks whether the exact version is good enough. Rights checks whether the material can be used for the intended purpose. A human reviewer makes the editorial decision. Then the central authorization authority decides whether this particular actor may perform this particular action on this particular version and destination right now.

Only after those separate checks can an execution adapter act. If something is missing, expired, revoked, mismatched or blocked, the safe result is to stop and explain why.

For NEXTDECODE, this prevents a good-looking video from being published when its footage rights are unclear, its QA has a hard blocker, the wrong version was approved, or a direct uploader tries to bypass the normal workflow.

---

**WP-5 outcome:** The central governance boundary and the separation of QA, rights, human approval, authorization and execution are defined. Detailed policy catalogues and operational parameters remain open for owner review. No implementation or live publishing is authorized.
