# NEXTDECODE — P0 Governance & Authorization Contract Reconciliation

**Document ID:** `NEXTDECODE_P0_Governance_Authorization_Contract_Reconciliation_0.1`  
**Version:** 0.1  
**Date:** 1 November 2026  
**Status:** DESIGN RECONCILIATION — OWNER REVIEW REQUIRED  
**Scope:** WP-5; cross-document findings X-04 and X-05  
**Detailed contract freeze:** NOT GRANTED  
**Implementation authorization:** NOT GRANTED

---

## 1. Purpose and disposition

This document reconciles the governance terminology and central authorization boundary across WP-5, WP-6 and the Consolidated Contract Appendix.

It addresses two findings:

- **X-04:** WP-5 wording grouped review and QA, while the appendix correctly represented them as separate concepts.
- **X-05:** Central authorization is accepted, but the policy request/decision contract, protected-action catalogue, emergency-pause authority and in-flight action behavior remain incomplete.

**Disposition:** X-04 is resolved at the conceptual boundary in this candidate by consistently separating five governance concepts. X-05 is clarified at the logical-contract level, but owner-reserved emergency-pause authority and in-flight external action policy remain open.

This document does not change accepted ADR-007 / CF-22 centralized authorization, accepted QA/rights/approval vocabularies, or the rule that automatic public publishing remains disabled.

## 2. Authority and decision labels

Source precedence:

1. Accepted owner decision record and ADR-001–ADR-010 / CF-01–CF-24.
2. Governing canonical data dictionary, API/Event Contract Standard and Unified Lifecycle/State Transition Standard.
3. WP-1 through WP-6 package specifications.
4. Consolidated Contract Appendix as a derivative consolidation aid.
5. This reconciliation as a candidate clarification.

Labels:
- **ACCEPTED BASELINE:** already accepted by the owner.
- **SOURCE-DEFINED:** required by authoritative project sources.
- **RECONCILED:** wording or boundary clarified without changing accepted policy.
- **PROPOSED:** candidate detail for owner review.
- **OPEN / OWNER-RESERVED:** needs additional specification or explicit owner decision.
- **DEFERRED:** intentionally postponed where a safe abstract boundary exists.

No proposal below becomes accepted merely by appearing in this document.

## 3. Five distinct governance concepts — X-04

The model must consistently represent these five concepts as distinct records/decisions. Execution and external distribution outcome remain separate operational facts.

| Concept | Question answered | What it must not be confused with |
|---|---|---|
| **QA result** | Does this exact version meet defined quality requirements? | Human review or approval |
| **Rights assessment** | Is this material permitted for this intended use, territory, platform, duration and context? | Technical accessibility or general ownership |
| **Review snapshot** | What exact material/evidence did a reviewer inspect and record? | QA result or approval decision |
| **Approval decision** | Did an authorized human approve this exact version and scope? | Authorization to execute an action |
| **Authorization decision** | May this actor perform this exact action on this exact resource now? | Approval, worker capability or successful execution |

### 3.1 QA result — ACCEPTED BASELINE

Accepted outcomes:
- `PASS`
- `PASS_WITH_WARNINGS`
- `NEEDS_REVIEW`
- `BLOCKED`

A hard blocker cannot be bypassed by ordinary approval, retry or adapter behavior. QA is bound to the exact version and applicable QA policy/check set.

### 3.2 Rights assessment — ACCEPTED BASELINE

Accepted rights states:
- `UNKNOWN`
- `PENDING_REVIEW`
- `CLEARED`
- `RESTRICTED`
- `EXPIRED`
- `REVOKED`
- `DENIED`

Rights are use-specific. A rights assessment must be evaluated against the requested use and relevant scope; a generic `CLEARED` label must not be treated as universal permission. Unknown, pending, restricted, expired, revoked or denied rights do not grant protected use.

### 3.3 Review snapshot — RECONCILED / PROPOSED

A ReviewSnapshot should identify what the reviewer actually inspected:
- exact ContentItem/ContentVariant version where relevant;
- exact ArtifactVersion and ArtifactManifest versions;
- attached QA and rights evidence references;
- intended use and scope;
- reviewer identity and timestamp;
- comments/findings and requested changes;
- snapshot schema/version.

The snapshot is evidence of inspection, not the approval itself. If the inspected material changes, a prior review snapshot must not silently describe the new version.

### 3.4 Approval decision — ACCEPTED BASELINE

Accepted approval decisions:
- `APPROVED`
- `REJECTED`
- `CHANGES_REQUESTED`
- `EXPIRED`
- `REVOKED`

Approval must be attributable and bound to the exact reviewed version and scope. A changed artifact, manifest, material rights scope or destination may require new review/approval under the applicable policy.

Approval is not execution authorization.

### 3.5 Authorization decision — ACCEPTED BASELINE

Centralized authorization is the sole authority for protected actions. Default-deny/fail-closed behavior applies. Authorization is exact-action, exact-resource and scope-aware.

An authorization decision is not a perpetual grant, not transferable to a different artifact/hash/destination, and not proof that the action was executed successfully.

### 3.6 Execution and distribution outcome — RECONCILED

Execution is a separate operational fact:
- an action was attempted;
- the execution system recorded its outcome;
- any ambiguous external result was reconciled.

A successful authorization does not mean the action happened. An attempted upload does not prove the platform accepted it. A platform acceptance response does not automatically establish public visibility or final distribution success.

## 4. Canonical governance relationships

The following relationships are proposed as the minimum interoperable model:

1. QA result targets an exact content/artifact/manifest version and a versioned QA policy.
2. Rights assessment targets identified source/material and an explicit intended-use scope.
3. ReviewSnapshot references exact versions and the evidence shown to the reviewer.
4. ApprovalDecision references the ReviewSnapshot and exact approved scope/version.
5. AuthorizationDecision references actor, action, resource, scope, policy version and required QA/rights/approval evidence.
6. ExecutionRecord references the authorization decision used at action time and records the actual attempt/outcome.
7. DistributionRecord, where applicable, records destination and external outcome separately from authorization and approval.

Typed references do not grant ownership, access, approval or authorization.

## 5. Central policy evaluation contract — X-05

### 5.1 Authority — ACCEPTED BASELINE

ADR-007 / CF-22 establishes centralized authorization. All APIs, workers, studios, pipelines and distribution adapters must enforce the same authority. No adapter may create a competing authorization decision or self-authorize.

### 5.2 Proposed policy evaluation request

A policy request should carry, at minimum:

| Field | Meaning |
|---|---|
| `request_id` | Canonical request/correlation identity |
| `actor_type`, `actor_id` | User, service, worker or other authenticated actor |
| `workspace_id` | Explicit workspace boundary |
| `action` | Exact protected action being requested |
| `resource_type`, `resource_id` | Exact target resource |
| `resource_version_id` | Exact version where applicable |
| `content_hash` | Exact byte/content identity where relevant |
| `destination_type`, `destination_id` | Exact platform/account/location where relevant |
| `approval_decision_id` | Required approval evidence, if applicable |
| `qa_evidence_refs` | Relevant QA results |
| `rights_evidence_refs` | Relevant rights assessments |
| `policy_context` | Relevant non-secret context and requested scope |
| `requested_at` | Evaluation time |
| `correlation_id`, `causation_id` | Traceability references |

This is a logical candidate only. Exact envelope field names, required/optional rules and schema compatibility must conform to the governing API/Event Contract Standard.

### 5.3 Proposed policy decision

A decision should preserve:
- canonical `authorization_decision_id`;
- request identity;
- decision outcome (`ALLOW` or `DENY` as proposed labels; exact enum reconciliation required);
- actor, action, resource, version/hash and destination binding;
- policy identifier and immutable policy version;
- reason code and structured evidence references;
- issued-at and expiry timestamps;
- revocation status/reference where applicable;
- decision authority identity;
- correlation/audit references.

A denial should be explainable to an authorized operator without leaking secrets or unnecessary sensitive information.

### 5.4 Decision enforcement

- Missing, malformed, ambiguous or expired authorization denies the protected action.
- A decision for one action cannot authorize another action.
- A decision for one artifact/version/hash cannot authorize another.
- A decision for one destination/account cannot authorize another.
- A changed resource, hash, destination or required evidence triggers re-evaluation.
- Revocation is enforced at the protected-action boundary.
- Retry does not convert a denial into permission.
- Workers and agents cannot mint, widen or transfer authorization.
- A policy `ALLOW` does not override hard QA, rights, safety or integrity blockers.

**OPEN:** exact request/response schema, reason codes, decision caching, policy rollout/version compatibility, revocation propagation targets, and maximum decision lifetime.

## 6. Protected-action catalogue — PROPOSED

The catalogue must be explicit and centrally governed. Candidate action families:

| Family | Candidate protected actions |
|---|---|
| Artifact access | `ARTIFACT_READ`, `ARTIFACT_WRITE`, `ARTIFACT_TRANSFER`, `ARTIFACT_EXPORT`, `ARTIFACT_SHARE`, `ARTIFACT_DELETE` |
| Governance | `REVIEW_SUBMIT`, `APPROVAL_RECORD`, `APPROVAL_REVOKE` |
| Production | `PRODUCTION_START`, `PRODUCTION_CANCEL`, `PRODUCTION_PROMOTE` |
| Distribution | `DISTRIBUTION_PREPARE`, `DISTRIBUTION_UPLOAD`, `DISTRIBUTION_PUBLISH`, `DISTRIBUTION_DELETE_OR_RETRACT` |
| Administration | `WORKER_ENROLL`, `WORKER_SUSPEND`, `WORKER_REVOKE`, `POLICY_CHANGE`, `EMERGENCY_PAUSE_ACTIVATE`, `EMERGENCY_PAUSE_RELEASE` |

These are candidate names, not frozen enums. The final catalogue must:
- define each action's exact resource and scope;
- distinguish reversible from irreversible/consequential actions;
- identify required QA, rights, review, approval and authorization evidence;
- specify whether human confirmation is mandatory;
- identify the owning authority and audit requirements;
- default-deny unknown action names.

No action family grants public publishing permission. Automatic public publishing remains disabled pending separate policy and authorization.

## 7. Emergency pause contract — owner-reserved portion of X-05

### 7.1 Accepted/source-defined principle

An emergency pause blocks new consequential protected actions. The central authorization boundary must be consulted at execution time.

### 7.2 Proposed minimum semantics

While pause is active:
1. New protected actions in the pause scope are denied.
2. Every adapter, worker, API and direct pipeline path observes the same authoritative pause state.
3. Existing `ALLOW` decisions do not bypass an active pause if the action has not yet crossed its authorized execution point.
4. Pause activation is attributable, time-stamped and audited.
5. Deactivation does not automatically replay denied actions.
6. Any resumed action is re-evaluated under current policy and evidence.
7. Pause cannot be bypassed by retry, alternate adapter, agent delegation or a stale cached decision.

### 7.3 Scope dimensions — PROPOSED

A pause may need to be scoped by:
- entire workspace/brand;
- action family;
- destination/platform/account;
- worker or adapter;
- policy/security incident.

The system must make the active scope explicit. A narrower pause must not be interpreted as a broader pause, or vice versa.

### 7.4 Owner-reserved decisions — NOT RESOLVED

Explicit owner decision required for:
- who may activate an emergency pause;
- whether any role may activate globally or only within a delegated scope;
- who may release/deactivate it;
- whether two-person confirmation is required for release;
- incident evidence and notification requirements;
- treatment of actions already in flight;
- whether a break-glass exception exists at all.

**Safe default pending owner decision:** no break-glass bypass; missing/ambiguous pause authority fails closed. Do not invent an override role.

## 8. In-flight external actions and ambiguous outcomes

This is a critical boundary: an external upload/publish request may have reached a platform even if NEXTDECODE loses the response.

### 8.1 Required distinctions

- **Not started:** action has not crossed the external execution boundary.
- **In flight:** request may be processing; outcome not yet known.
- **Confirmed success:** authoritative external response/evidence confirms the action.
- **Confirmed failure:** authoritative evidence confirms rejection/failure.
- **Unknown outcome:** external side effect may have happened, but available evidence is insufficient.
- **Reconciled:** follow-up evidence establishes the actual external state.

### 8.2 Proposed handling

1. Pause blocks new protected actions within scope.
2. Do not claim that an already transmitted external request was cancelled unless the provider confirms cancellation.
3. Preserve the original request, authorization decision, destination, idempotency key and attempt evidence.
4. Mark ambiguous actions `UNKNOWN_OUTCOME` (subject to governing lifecycle vocabulary) rather than falsely recording failure or success.
5. Query/reconcile the external destination only through an authorized mechanism.
6. Do not blindly retry an ambiguous non-idempotent action.
7. If the provider supports idempotency, reuse the same provider idempotency key only under the provider's documented contract.
8. Record reconciliation evidence and the final confirmed outcome.
9. Any subsequent action requires fresh authorization under current pause/policy state.

**OWNER-RESERVED:** whether any in-flight action may be allowed to complete, actively cancelled, or left for reconciliation under each protected-action family. No universal cancellation behavior is assumed.

## 9. Adapter, pipeline and worker enforcement

Every protected action must pass through the central authorization boundary at the point of action.

Required rules:
- Distribution adapters cannot self-authorize.
- Direct platform adapters cannot bypass the parent publisher governance gate.
- Direct pipeline calls cannot bypass governed orchestration and required policy checks.
- Worker capability is not permission.
- Agent delegation cannot expand authority.
- Missing authorization denies.
- Expired/revoked authorization denies.
- Resource/version/hash/destination mismatch denies.
- Hard rights, QA, safety and integrity blockers remain enforced.
- Policy denials cannot be bypassed through retries.
- Dry-run cannot silently become live execution.
- Automatic public publishing remains disabled.
- Human approval before critical publishing actions remains required.

Inherited Phase 11 findings remain verification targets, not proof of current behavior:
- G1 storyboard approval gate reportedly defaults to `warn`.
- G2 rights evidence reportedly not enforced end-to-end by publishing.
- G3 unsupported factual claims reportedly warning-only.
- U1 direct platform adapters reportedly bypass parent publisher gate.
- D1 direct pipeline reportedly bypasses governed orchestration/run identity/quality gates.
- T1 shot/beat/render traceability reportedly incomplete.
- R1 Run Tracker runtime/recovery evidence reportedly missing.

These historical reports have not been freshly retested in this reconciliation.

## 10. Audit and explainability

At minimum, preserve attributable records for:
- policy evaluation request and decision;
- policy version and reason code;
- QA run and checks;
- rights assessment and evidence changes;
- ReviewSnapshot creation;
- approval, rejection, change request, expiry and revocation;
- authorization issuance, denial, expiry and revocation;
- emergency pause activation and release;
- protected-action execution request and outcome;
- adapter denial or bypass attempt;
- ambiguous external outcome and reconciliation.

Audit evidence must bind to exact entity/version/hash/destination scope where applicable. Secrets and unnecessary sensitive data must not be logged.

## 11. WP-6 acceptance matrix — proposed oracles

These are design targets, not executed tests. Use isolated synthetic fixtures and non-production destinations only.

| Test ID | Scenario | Expected oracle |
|---|---|---|
| GOV-01 | QA returns `BLOCKED`; ordinary approval attempted | Protected action remains denied |
| GOV-02 | Rights state is `UNKNOWN` or `PENDING_REVIEW` for a protected use | Denied for that use |
| GOV-03 | Rights assessment is cleared for a different use/scope | Scope mismatch denied |
| GOV-04 | Approval references ArtifactVersion A; request targets B | Denied or new review/approval required |
| GOV-05 | Authorization is missing | Denied |
| GOV-06 | Authorization is expired or revoked | Denied |
| GOV-07 | Authorization hash differs from target bytes | Denied |
| GOV-08 | Authorization destination differs from requested destination | Denied |
| GOV-09 | Authorization is for a different action | Denied |
| GOV-10 | Emergency pause active before protected action | Denied across all adapter paths |
| GOV-11 | Pause activated after external request sent | State remains in-flight/unknown until evidence; no false cancellation claim |
| GOV-12 | Pause released | No automatic replay; fresh policy evaluation required |
| GOV-13 | Direct adapter attempts to bypass central gate | Denied and audited |
| GOV-14 | Direct pipeline attempts to bypass governed checks | Denied and audited |
| GOV-15 | Agent attempts to expand delegator authority | Denied |
| GOV-16 | Policy denial followed by retry | Still denied absent changed, valid policy/evidence |
| GOV-17 | Dry-run path attempts live side effect | Blocked |
| GOV-18 | External response lost after request transmission | `UNKNOWN_OUTCOME`; reconcile before unsafe retry |
| GOV-19 | Policy decision inspected by authorized operator | Explainable from policy version and evidence without secret exposure |
| GOV-20 | Public publishing path invoked during P0 test | No live publishing; test environment guard blocks it |

WP-6's detailed acceptance plan remains authoritative for the complete scenario and failure matrix. This table is an additional traceability candidate, not permission to run tests.

## 12. Open-decision register

| ID | Open item | Status / required before |
|---|---|---|
| G-01 | Exact policy request/response schema | OPEN — contract freeze |
| G-02 | Protected-action catalogue and exact scope | OPEN — governance implementation |
| G-03 | Reason-code/severity catalogue | OPEN — policy implementation |
| G-04 | QA check catalogue and studio mapping | OPEN — studio enforcement |
| G-05 | Rights evidence schema and detailed use matrix | OPEN — rights implementation |
| G-06 | ReviewSnapshot schema and snapshot strategy | OPEN — approval implementation |
| G-07 | Approval expiry/revocation/re-review rules | OPEN — approval implementation |
| G-08 | Authorization grant schema and revocation propagation | OPEN — authorization integration |
| G-09 | Emergency pause scope and activation authority | OWNER-RESERVED — freeze |
| G-10 | In-flight external action reconciliation policy | OWNER-RESERVED — distribution integration |
| G-11 | Policy version rollout/compatibility strategy | OPEN — policy deployment |
| G-12 | Legal escalation/high-risk rights review | OPEN — rights operations |
| G-13 | Audit retention/access policy | OPEN — operational governance |
| G-14 | Complete adapter/pipeline bypass inventory | Requires separately authorized verification |
| GOV-15 | Break-glass exception existence and authority | OWNER-RESERVED — do not assume one |
| GOV-16 | Emergency pause release authority and safeguards | OWNER-RESERVED — freeze |
| GOV-17 | Decision caching and execution-time recheck rules | OPEN — contract freeze |
| GOV-18 | External provider idempotency/reconciliation matrix | OPEN — distribution integration |

No new rights, approval or QA vocabulary is introduced. No break-glass role, exception or publishing permission is granted by this document.

## 13. Traceability and remaining gaps

- **X-04:** concept count/terminology normalized to five separate governance concepts in Section 3.
- **X-05:** central authorization request/decision, action catalogue, emergency pause and in-flight handling clarified as logical candidates in Sections 5–8. Owner-reserved authority remains open.
- **X-06:** worker trust, credential and active-job revocation semantics remain a separate reconciliation.
- **X-08:** command/event envelope compatibility remains a separate conformance task.
- **X-10:** WP-6 test oracle, evidence and environment controls still require a complete acceptance traceability matrix.
- **X-09:** artifact lifecycle/legal hold/purge remains partially open under the separate artifact reconciliation.

## 14. Safety and authorization boundary

This document does not authorize:
- repository/code changes or tests;
- agent execution;
- policy deployment or production configuration changes;
- credential issuance, revocation or secret changes;
- provider activation or paid services;
- live publishing or platform uploads;
- emergency pause activation/deactivation in a real environment;
- destructive deletion or purge.

Any such action requires separate appropriate authorization.

## 15. Plain-language explanation

NEXTDECODE needs five different answers before a consequential action can happen:

1. Is the output technically good enough?
2. Are we allowed to use the material for this purpose?
3. What exactly did the reviewer inspect?
4. Did an authorized human approve that exact version?
5. Is this actor allowed to perform this exact action right now?

Even after all five are satisfied, the system must separately record whether the action actually happened. If an emergency pause is activated after an upload request has already left the system, we cannot pretend the upload was cancelled. We must find out what happened before retrying.

**Reconciliation outcome:** X-04 has a consistent conceptual model. X-05 has a clearer logical contract candidate, but emergency-pause authority and in-flight action policy remain owner-reserved. P0 remains **NOT READY FOR DETAILED CONTRACT FREEZE**.

**Detailed contract freeze:** NOT GRANTED.  
**Implementation authorization:** NOT GRANTED.
