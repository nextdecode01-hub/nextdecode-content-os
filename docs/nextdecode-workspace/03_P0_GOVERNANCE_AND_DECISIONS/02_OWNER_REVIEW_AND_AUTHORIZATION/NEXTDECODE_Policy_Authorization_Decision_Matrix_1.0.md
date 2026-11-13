# NEXTDECODE — Policy & Authorization Decision Matrix
**Version:** 1.0  
**Status:** Architecture specification — documentation only  
**Scope:** Workspace, Shared Intelligence Core, studios, agents, workers, governance, integrations, distribution and commercial operations  
**Companions:** Canonical Data Dictionary & Entity Ownership Registry 1.0; Unified Lifecycle & State Transition Standard 1.0; API & Event Contract Standard 1.0; Shared Intelligence Core Contracts 01–12; Architecture Parts 1–8

---

## 1. Purpose

This document defines the central authorization model for NEXTDECODE: who or what may perform an action, on which resource, within what scope, under which policy, and with what approval or evidence.

It makes authority explicit across every studio and integration. A capability available to an agent is not automatically permission to use it for every task. A workflow being ready is not authorization. Human approval is not a substitute for policy evaluation. Owner silence is never consent.

This matrix covers:
- humans, owner and delegated roles;
- agents, services and workers;
- read, research, creation, quality and operational actions;
- publishing, financial and commercial actions;
- security, privacy, policy and architecture changes;
- emergency controls, exceptions, audit and revocation.

**Documentation-only boundary:** This standard does not authorize implementation, repository access, code changes, provider connections, infrastructure provisioning, spending, uploads or publishing.

## 2. Normative language

- **MUST / MUST NOT:** mandatory.
- **SHOULD / SHOULD NOT:** expected default; deviations require documented rationale.
- **MAY:** optional.
- **Owner approval:** an explicit decision by the authorized owner through an authenticated, auditable mechanism. Silence, inactivity, missed notifications and expired requests do not qualify.

---

## 3. Authorization model

### 3.1 Authorization decision tuple

Every protected action MUST be evaluated against a complete decision tuple:

| Dimension | Question |
|---|---|
| Subject | Who/what is requesting the action? |
| Identity assurance | Is the identity authenticated, current and not revoked? |
| Capability | What operation is requested? |
| Resource | Which entity, artifact, account, integration or system is affected? |
| Scope | Which workspace, brand, studio, channel or environment? |
| Context | Why, when, from which workflow/task and under what conditions? |
| Policy | Which policy version applies? |
| Evidence | What facts, approvals, rights and validations support the request? |
| Limits | Are quotas, budgets, rate limits and risk boundaries satisfied? |
| Decision | Is the action allowed, conditionally allowed, pending or denied? |
| Obligations | What restrictions, logging, expiry or follow-up apply? |

A decision MUST be specific enough to prevent a permission granted for one action/resource/version from being reused for another.

### 3.2 Decision outcomes

| Decision | Meaning |
|---|---|
| `ALLOW` | All required conditions are satisfied for the specified action and scope |
| `ALLOW_WITH_CONDITIONS` | Action may proceed only while explicit obligations remain satisfied |
| `PENDING_APPROVAL` | A required human/owner decision is outstanding |
| `DENY` | The action is not permitted under current policy |
| `BLOCKED` | A hard guard, missing prerequisite or safety restriction prevents the action |
| `INDETERMINATE` | Identity, evidence, policy or state cannot reliably be established; protected actions fail closed |

`ALLOW` is not a permanent role permission. It is a scoped decision for a defined action and context.

### 3.3 Fail-closed rule

If identity, scope, policy version, rights status, required evidence or authorization cannot be verified, protected actions MUST fail closed. Safe, non-mutating diagnostics MAY continue if they do not expose restricted data or cause external effects.

### 3.4 Policy precedence

When multiple policies apply, the most restrictive applicable rule wins, subject to this authority hierarchy:

1. Applicable law, legal hold and mandatory platform/security constraints.
2. Owner-approved global security, privacy and governance policies.
3. Workspace-level policy.
4. Brand-level policy.
5. Studio-level policy.
6. Task/workflow-specific delegated constraints.
7. Agent/worker capability configuration.

Lower-level policy MUST NOT weaken a higher-level restriction. A task or agent cannot override a workspace or owner policy.

### 3.5 Permission is not ownership

Access to an artifact, source, customer record or intelligence record does not confer IP ownership, redistribution rights, commercial rights or permission to share it outside its authorized purpose.

---

## 4. Principals and authority classes

### 4.1 Principal types

| Principal | Identity purpose | Default authority |
|---|---|---|
| Owner | Ultimate platform/workspace authority | Owner-controlled decisions within legal and platform constraints |
| Human delegate | Assigned human responsibility | Explicitly delegated scope and duration |
| Human reviewer | Quality/editorial review | Review and approve only assigned review scope |
| Agent | Autonomous or assisted reasoning/execution | Task-scoped capabilities only |
| Service | Domain/API operation | Service-specific capabilities |
| Worker | Executes durable jobs | Job-scoped execution capabilities |
| External integration | Provider/platform identity | Narrow adapter operations and scopes |

These are identity categories, not a complete role catalogue. A person may hold multiple explicit roles, but each action is evaluated against the relevant role and scope.

### 4.2 Owner authority

The owner retains authority over:
- mission, positioning and strategic priorities;
- policy and governance changes;
- security and privacy policy;
- permission grants and delegation boundaries;
- publishing automation policy;
- financial limits and commercial commitments;
- external provider approval and data-processing boundaries;
- fundamental architecture and contract changes;
- production release and deployment authorization;
- customer onboarding, billing and SaaS launch;
- emergency-control release where owner authority is required.

Owner authority MUST be authenticated, scoped and audited. It does not override law, platform constraints or mandatory safety/security controls.

### 4.3 Agent authority

Agents:
- receive explicit task-scoped permissions;
- may use only registered capabilities assigned to the task;
- cannot grant, widen or self-renew permissions;
- cannot impersonate the owner;
- cannot change the policy governing their current task;
- cannot convert a recommendation into a financial, publishing or legal commitment;
- must stop or escalate when a required permission or protection is absent.

### 4.4 Worker and service authority

Workers and services receive only the technical permissions required for their operation. A worker lease, job assignment or API credential is not proof of business authorization. Before protected side effects, the domain service MUST re-check the relevant governance decision and current policy.

---

## 5. Scope hierarchy and isolation

Authorization scope can include platform, workspace, brand, studio, content item or artifact, channel/account, workflow/job/task, integration/provider, environment (development, staging, production), and financial/resource account.

A narrower scope MUST NOT silently expand to a broader one.

Examples:
- Access to NEXTDECODE Shorts artifacts does not imply access to a future separate brand.
- A research task's source access does not authorize publishing the research.
- A worker assigned to one job cannot inspect unrelated workspace jobs.
- A channel-specific approval does not authorize another destination.
- Development access does not authorize production deployment.

Cross-workspace federation or sharing requires explicit policy and authorization. No cross-platform audience identity matching is permitted without an explicitly authorized, privacy-compliant basis.

---

## 6. Master action decision matrix

The following matrix defines the default authority boundary. Domain policies may be stricter, but MUST NOT be less restrictive without an explicit owner-approved policy change.

| Action class | Agent/AI | Service/worker | Human delegate/reviewer | Owner approval required? |
|---|---|---|---|---|
| Read public/internal data within assigned scope | Allow if scoped | Allow if scoped | Allow if scoped | No, unless policy requires |
| Read confidential/restricted data | Explicit task grant and purpose only | Explicit service/job grant only | Role and purpose grant | For new access class or exceptional scope |
| Discover opportunities and monitor approved sources | Allow within approved sources/budgets | Execute assigned jobs | Configure within delegated scope | For new provider, data category or spend |
| Score and assess opportunities | Recommend/prepare | Compute assigned assessment | Review within assigned role | Strategic policy changes require owner |
| Conduct approved research | Allow within source, data and resource limits | Execute scoped research jobs | Request/review | Restricted data, new provider or added spend |
| Create drafts, scripts, storyboards and variants | Allow within approved brand/editorial constraints | Execute production tasks | Review/edit | Owner for mission/positioning/policy change |
| Render and process approved assets | Assigned tools/resources only | Execute within quota | Request/review | Budget/service expansion |
| Run quality checks | Assess and report findings | Execute deterministic checks | Review findings | No, unless changing quality policy |
| Change quality thresholds or bypass checks | Recommend only | Deny | No authority unless explicitly delegated | Yes |
| Register rights evidence and flag uncertainty | Prepare/classify with provenance | Store/process records | Review/verify within role | New rights policy or exception requires owner |
| Declare rights cleared | Only when evidence and policy permit; no self-certification | No independent clearance | Authorized rights reviewer | Owner for exceptional policy override |
| Prepare approval package | Allow | Execute | Review package | No |
| Approve assigned editorial review | No, unless explicitly designated automated check; never owner approval | No | Assigned review scope only | Owner if policy requires |
| Grant governance authorization for public action | No | No | Only a specifically delegated role if policy permits | Owner policy required; public auto-publishing currently disabled |
| Prepare distribution packages/schedule proposals | Allow within scope | Execute | Review | No |
| Publish publicly | Deny under current baseline | Deny absent valid authorization | Execute only with valid authorization and platform permission | Separate explicit owner publishing policy required |
| Delete/overwrite governed records | Recommend/request only | Approved retention workflow only | Role-limited | Owner for exceptional or broad deletion |
| Spend money, purchase services or incur commitments | Deny | Deny | Deny unless separately delegated | Explicit owner authorization |
| Research sponsorships and prepare proposals | Allow | Execute research | Review | No |
| Negotiate binding terms, accept sponsorship, sign agreements | Deny | Deny | Deny absent explicit legal/commercial delegation | Explicit owner authorization |
| Change budget, financial limits or subscriptions | Recommend only | Deny | No by default | Yes |
| Reallocate within approved resource envelope | Recommend; execute only if bounded policy delegates | Execute within approved limits | Within delegated limits | Significant/strategic change requires owner |
| Scale approved infrastructure within pre-authorized envelope | Request/recommend | Execute only within approved policy and budget | Review/monitor | No new spend; owner for expansion |
| Create new provider account or subscription | Deny | Deny | Deny | Yes |
| Connect external account/provider | Request/recommend | No self-authorization | May assist setup | Explicit owner authorization |
| Transfer data to external AI provider | Approved provider/data class and task scope only | Enforce transfer policy | Review exceptions | New provider/data category requires owner |
| Change agent permissions or registry trust | Deny | Deny | No by default | Yes |
| Change security/privacy/governance policy | Recommend only | Deny | No | Yes |
| Change fundamental architecture/contracts | Propose ADR only | Implement after approved scope | Review | Yes |
| Modify code in an authorized scope | Explicit repository/task grant, isolated branch/workspace | Tool execution under that grant | Review | Fresh explicit repository scope authorization |
| Merge code | Only if separately delegated low-risk policy allows and checks pass | Approved merge workflow | Review | Sensitive/foundational/security changes require owner |
| Deploy/release to production | Prepare/recommend | Execute only under release authorization | Approve if delegated | Separate production release authorization |
| Pause an unsafe operation | Within assigned emergency capability | Within assigned capability | Within assigned scope | No |
| Release global/security emergency pause | Deny | Deny | Deny by default | Owner or explicitly designated security authority |
| View audit logs | Scoped and minimized | Service-specific | Role-scoped | Restricted audit access requires owner policy |

**Current baseline interpretation:** A row marked “owner approval required” defines an authority boundary, not an action already approved. Public publishing, spending, external account connection and production release remain separately gated.

---

## 7. Explicit action rules by domain

### 7.1 Research and opportunity intelligence

Agents MAY discover and monitor approved public sources, prepare opportunity candidates, assess relevance/confidence/evidence quality, propose research plans, conduct approved research within source/privacy/provider/resource constraints, and report contradictions or missing evidence.

Agents MUST NOT:
- bypass source restrictions or paywalls;
- collect restricted personal data without an approved lawful basis;
- infer cross-platform identity without authorization;
- treat an opportunity score as a production or publishing command;
- increase research spend or provider quota;
- present model inference as verified fact.

### 7.2 Creation and studio operations

Agents MAY prepare and execute approved briefs, scripts, storyboards, voice/visual/edit plans, format adaptations, rendering and asset processing, metadata and packaging proposals.

They MUST use the correct immutable brand/studio identity version, preserve provenance, enforce rights and quality gates, and register artifacts with version and lineage.

They MUST NOT change brand mission/editorial policy, fabricate rights clearance, suppress material quality failures, or publish because rendering succeeded.

### 7.3 Quality, rights and approval

Quality assessment, rights verification, human review and governance authorization are distinct decisions.

- A quality `PASS` is not rights clearance.
- Rights `CLEARED` is not editorial approval.
- Editorial approval is not publishing authorization.
- Approval for one artifact version is not approval for a changed version.
- Hard blockers cannot be bypassed by ordinary approval.
- Unknown rights status remains unresolved; it is not implicitly cleared.

### 7.4 Distribution and publishing

The system MAY prepare channel-specific adaptations, metadata and thumbnails, schedule proposals, and internal staging records where explicitly permitted.

The system MUST NOT publicly publish under the current baseline without a separate explicit owner-approved policy and a valid action-specific authorization.

Any future publishing authorization must bind to exact content/artifact version, distribution package version, destination account/channel, operation type, policy version, validity window, required rights/quality/review conditions and emergency pause status.

A provider timeout after submission creates an unknown outcome requiring reconciliation, not a blind retry.

### 7.5 Business and monetization

AI MAY research revenue models and market opportunities, prepare sponsorship prospect lists from approved sources, draft proposals and rate-card options, analyze scoped performance/revenue data, and forecast scenarios.

AI MUST NOT accept or reject binding sponsorship offers, negotiate or accept binding terms, sign agreements, make financial representations, spend money, purchase services, launch unapproved commercial campaigns, or change budgets/financial limits/payment instructions.

These actions require explicit owner authorization and any separately required legal/financial review.

### 7.6 Engineering and infrastructure

AI MAY propose architecture changes and, after explicit task authorization, modify code within the approved repository scope, isolated workspace/branch and defined acceptance criteria.

AI MUST NOT infer repository access from prior work, access GitHub or a local repository without fresh explicit authorization, modify files outside approved scope, change secrets/permissions/security controls/production settings without authorization, autonomously merge sensitive foundational/security changes, or deploy production without separate release authorization.

Autonomous scaling is limited to already approved services and budgets. No new subscription, contract, spending or budget increase is permitted without owner approval.

---

## 8. Human approval and owner approval matrix

### 8.1 Approval classes

| Approval class | Purpose | Default approver |
|---|---|---|
| Editorial review | Editorial suitability and brand alignment | Assigned human reviewer; owner where policy requires |
| Quality exception | Review warning or permitted exception | Designated quality/governance authority |
| Rights exception | Resolve an explicitly exception-eligible rights issue | Authorized rights owner/reviewer; owner for policy exception |
| Public publishing policy | Define whether and how automated public publishing may operate | Owner |
| Specific protected action | Authorize exact action/resource/target/version | Owner or expressly delegated authority under approved policy |
| Financial/commercial | Spend, accept commitments, change limits | Owner |
| Security/privacy | Change security, privacy or provider data-processing policy | Owner |
| Architecture | Change foundational architecture or contracts | Owner |
| Production release | Release to production environment | Explicit release authority; owner where required |

### 8.2 Approval record requirements

Every approval record MUST include:
- approval ID;
- approver identity and role;
- exact action;
- exact resource and immutable version;
- target/destination, if applicable;
- decision and reason;
- evidence/review package reference;
- policy version;
- request, decision and expiry times;
- conditions and limitations;
- revocation/supersession reference where relevant.

### 8.3 Approval validity

Approval is valid only while all bound conditions remain true. It becomes invalid or requires re-evaluation when the artifact/package version, target, action or applicable policy changes; rights/evidence status changes; approval expires or is revoked; or a relevant emergency pause/security incident intervenes.

Expiry, silence, missed notification or owner unavailability MUST NOT be interpreted as approval.

---

## 9. Publishing authorization policy boundary

<badge color="warning">Disabled pending explicit owner policy</badge>

Autonomous public publishing is not enabled by this document or previous architecture planning.

Until a separate owner-approved publishing policy exists:
- automation may prepare and validate content;
- automation may create internal handoff/staging records where allowed;
- automation may prepare schedule proposals;
- public publishing remains denied unless explicit valid authorization is separately provided under an approved policy.

A future proposal must define eligible platforms/formats, eligibility and hard-blocker rules, quality and rights requirements, human review, action-specific authorization, destination allowlists, frequency/volume limits, time windows, retry/reconciliation, emergency pause, incident response, audit/reporting, revocation and policy version. None of these defaults are pre-approved.

---

## 10. Resource, quota and financial authority

### 10.1 Separate resource concepts

| Concept | Examples | Authority |
|---|---|---|
| Technical resource quota | CPU, memory, concurrency, storage | Bounded by approved configuration |
| Provider quota | API calls, rate limits, model tokens | Respect provider/account limits |
| Financial budget | Monthly spend, project budget | Owner-controlled |
| Actual expense | Invoice, subscription charge, usage bill | Record and reconcile; cannot be created by inference |
| Strategic allocation | Distribution of approved capacity/budget | Only within explicit delegation |

### 10.2 Autonomous resource operation

The platform MAY queue work when capacity is unavailable, defer low-priority work, use already approved alternate workers/providers where policy permits, scale within a pre-approved technical and financial envelope, and stop work before exceeding a limit.

It MUST NOT create a paid account, enable unapproved paid usage, increase a budget/cap, accept a new contract, incur a new subscription/commitment, or silently route restricted data to a new provider.

When capacity cannot be obtained within the approved envelope, defer, degrade gracefully or request owner action.

---

## 11. External AI provider and data-processing authorization

Before data is sent to an external AI provider, the platform MUST verify:
1. Provider is on the approved provider registry.
2. Provider is approved for the data classification and use case.
3. Data-protection terms are verified.
4. Training use is prohibited unless explicitly authorized.
5. Retention and deletion terms are acceptable.
6. Processing location/residency requirements are met.
7. Required security controls are verified.
8. Payload is minimized and redacted.
9. Task has a valid purpose and scope.
10. Transfer is logged with provider/model and policy references.

If any required protection is unknown or unverifiable, transfer MUST be blocked. A model being technically available does not make its provider approved.

---

## 12. Security, privacy and data governance

### 12.1 Security controls

- Strong human authentication, MFA/passkeys where supported.
- Separate human, owner, agent, service and worker identities.
- Short-lived, scoped, revocable credentials.
- Least-privilege access.
- No self-granted permissions.
- Audit privileged actions.
- Revoke credentials promptly after compromise or role change.
- Security isolation takes precedence over workflow completion.

### 12.2 Privacy controls

- Purpose limitation and data minimization.
- Explicit consent/legal basis where required.
- Workspace/brand isolation.
- Public/Internal/Confidential/Restricted classification.
- Retention, deletion and legal-hold workflows.
- No unauthorized personal-data profiling.
- No cross-platform identity matching without an explicitly authorized basis.
- No sale/licensing/monetization of customer-contributed data or intelligence.

### 12.3 Customer data boundary

If NEXTDECODE later serves customers:
- customer data remains isolated by customer/workspace;
- shared learning requires explicit authorization and appropriate aggregation/anonymization;
- confidential content and identifiable audience data must not be exposed across customers;
- customer-contributed data/intelligence must not be sold, licensed or placed in a marketplace;
- access does not confer ownership.

---

## 13. Emergency controls and exception handling

### 13.1 Emergency control levels

Controls may apply at global platform, workspace, brand, studio, agent, worker, integration/provider, publishing-only, financial operations or security-isolation level.

### 13.2 Activation and release

A designated agent, worker or service MAY activate a narrow emergency pause when it detects a defined safety/security condition and has the explicit capability. Humans with assigned operational roles MAY pause within their scope.

Global/security pause release remains owner-controlled or assigned to an explicitly designated security authority under an approved policy.

### 13.3 Exception rules

Exceptions MUST be explicitly permitted by governing policy, name the exact rule/resource, identify the authorized approver, include reason/evidence, have limited scope/expiry, be auditable, and trigger downstream re-evaluation.

No exception may bypass mandatory law, platform restrictions, security isolation or a non-overridable hard blocker.

### 13.4 Owner unavailability

When the owner is unavailable:
- routine, pre-authorized, reversible work may continue;
- work outside the approved authority envelope must pause or remain pending;
- silence is never approval;
- expired approval requests remain expired;
- the system preserves a durable recovery/decision queue;
- on return, the owner receives a prioritized briefing of pending decisions, incidents and completed work.

---

## 14. Authorization decision procedure

Every protected action SHOULD follow this deterministic procedure:

1. **Identify:** authenticate subject and identity assurance.
2. **Scope:** resolve workspace, brand, studio, resource and environment.
3. **Classify:** identify action risk and data classification.
4. **Capability:** verify the subject has the required capability.
5. **Policy:** load applicable policy hierarchy and version.
6. **State:** verify current domain state and expected state version.
7. **Evidence:** verify required quality, rights, provenance and approval evidence.
8. **Limits:** verify quota, rate and approved budget constraints.
9. **Emergency:** check pause, revocation and incident controls.
10. **Decide:** ALLOW, ALLOW_WITH_CONDITIONS, PENDING_APPROVAL, DENY, BLOCKED or INDETERMINATE.
11. **Enforce:** execute only the authorized operation and obligations.
12. **Audit:** persist decision, reason, policy version, actor and result.
13. **Reconcile:** verify external side effects and resolve unknown outcomes.

The enforcement point MUST be close to the resource/action owner. A UI-only check is insufficient.

---

## 15. Decision record and audit schema

A policy decision record SHOULD include:

| Field | Description |
|---|---|
| `decision_id` | UUIDv7 |
| `subject_ref` / `subject_type` | Actor identity |
| `action` | Stable action identifier |
| `resource_ref` / `resource_type` | Target resource |
| `resource_version` | Immutable version where applicable |
| `scope` | Workspace/brand/studio/channel/environment |
| `decision` | Common decision outcome |
| `reason_codes` | Machine-readable reasons |
| `policy_refs` | Policy IDs and versions evaluated |
| `evidence_refs` | Rights, quality, approval and other evidence |
| `conditions` | Obligations attached to conditional allow |
| `valid_from` / `valid_until` | Decision validity |
| `correlation_id` | End-to-end workflow |
| `evaluated_at` | UTC timestamp |
| `enforcement_point` | Service/adapter that enforced decision |
| `result_ref` | Operation/result reference |
| `revocation_ref` | Revocation or supersession, if any |

Decision records MUST be immutable. A changed decision creates a new record linked to the prior one.

---

## 16. Policy lifecycle and change control

### 16.1 Policy states

Recommended lifecycle:

`DRAFT → IN_REVIEW → APPROVED → ACTIVE → SUPERSEDED`

Additional states may include `REJECTED`, `EXPIRED` and `REVOKED`.

Only an authorized owner or designated policy authority may activate a policy that changes protected authority.

### 16.2 Policy changes

Every policy change MUST identify owner/scope and rationale, assess affected APIs/events/agents/workers/adapters, include relevant security/privacy/rights/financial review, define effective time, preserve prior versions, include migration and rollback/revocation plans, be tested before activation, and be audited.

Agents MAY draft policy proposals and impact analyses. They MUST NOT approve or activate policies that expand their authority.

### 16.3 Emergency policy changes

Emergency containment MAY temporarily restrict authority to prevent harm. It MUST NOT be used by an agent or worker to expand permissions or weaken safeguards.

Emergency changes require an audit record, scope, reason, expiry/review time and authorized release process.

---

## 17. Risk tiers and autonomy boundaries

Risk tiers determine required controls; they do not grant permissions.

| Tier | Typical action | Default autonomy |
|---|---|---|
| R0 — Read-only | Read authorized public/internal data | Autonomous within scope |
| R1 — Reversible preparation | Draft, summarize, classify, prepare a brief | Autonomous within scope |
| R2 — Bounded internal execution | Approved research, rendering, internal processing | Autonomous with task/resource limits |
| R3 — Consequential internal change | Modify governed records, change workflow configuration, delete/archive | Explicit policy and scoped authorization |
| R4 — External/public or financial action | Publish, send externally, spend, accept commercial terms | Explicit owner-approved policy and action-specific authorization |
| R5 — Foundational/security authority | Change security, privacy, permissions, governance, architecture or production controls | Owner-controlled; no autonomous expansion |

A risk tier may be raised by data sensitivity, irreversibility, scale, external visibility, legal exposure or uncertainty. When classification is uncertain, use the stricter tier.

---

## 18. Acceptance criteria

### Identity and scope
- [ ] Human, agent, service and worker identities are distinct.
- [ ] Every protected action is authenticated and scoped.
- [ ] Cross-workspace access is denied unless explicitly federated.
- [ ] Delegation cannot exceed the delegator's authority.
- [ ] Expired/revoked credentials are rejected.

### Policy decisions
- [ ] Decision tuple is complete for protected actions.
- [ ] Policy precedence is deterministic.
- [ ] Unknown identity/evidence/policy fails closed.
- [ ] Decisions are versioned, scoped and auditable.
- [ ] Lower-level policies cannot weaken higher-level controls.

### Agents and automation
- [ ] Agents cannot grant or expand permissions.
- [ ] Task assignment is not authorization for unrelated actions.
- [ ] Autonomous work stays within approved source, provider and resource limits.
- [ ] Owner absence does not expand authority.
- [ ] Silence and expiry never count as approval.

### Quality, rights and publishing
- [ ] Quality, rights, human approval and governance authorization are separate.
- [ ] Hard blockers cannot be bypassed by ordinary approval.
- [ ] Approval binds to exact version/action/target.
- [ ] Public publishing remains disabled until separate owner policy approval.
- [ ] External unknown outcomes are reconciled before unsafe retry.

### Financial and commercial
- [ ] No autonomous spending, new subscription or budget increase.
- [ ] No AI acceptance/signature of binding commercial terms.
- [ ] Resource scaling is restricted to approved envelope.
- [ ] Financial records distinguish forecast, approved budget and actual expense.

### Security and privacy
- [ ] Provider data transfer requires verified protection.
- [ ] Data classification and minimization are enforced.
- [ ] Customer data is not sold/licensed/monetized.
- [ ] Emergency pause and credential revocation are effective.
- [ ] Privileged actions are audited.

---

## 19. Required test scenarios

1. Agent attempts to grant itself a new capability — denied.
2. Worker attempts access to a different workspace — denied.
3. Human delegate acts outside delegated scope — denied.
4. Expired credential attempts protected action — denied.
5. Unknown policy version — fail closed.
6. Conflicting policies — most restrictive applicable rule enforced.
7. Task assignment is used to request an unrelated action — denied.
8. Agent attempts to change mission or editorial policy — proposal only.
9. Agent attempts to change quality threshold — denied pending owner approval.
10. Quality pass with unresolved rights — protected action blocked.
11. Human approval for an old artifact version — invalid for new version.
12. Approval expires while owner is unavailable — remains expired.
13. Missed notification — no implicit approval.
14. `APPROVED_FOR_HANDOFF` used as publish authorization — denied.
15. Publishing request without separate active policy — denied.
16. Publishing request during emergency pause — denied.
17. Provider timeout after possible publish — unknown outcome and reconciliation.
18. Agent attempts to spend or create subscription — denied.
19. Resource scaling exceeds approved budget envelope — denied/deferred.
20. External AI provider has unverifiable retention/training terms — transfer blocked.
21. Agent attempts to accept sponsorship terms — denied.
22. Agent attempts production deployment without release authorization — denied.
23. Emergency pause activation is audited.
24. Unauthorized actor attempts global pause release — denied.
25. Cross-customer data query — denied.
26. Policy update by unauthorized service — denied.
27. Revoked permission is rejected on retry.
28. Audit decision cannot be silently edited or deleted.

---

## 20. Open implementation decisions

These remain open:
- exact role and capability catalogue;
- policy engine and policy-as-code format;
- policy storage, signing and distribution;
- authentication provider and credential protocol;
- delegation and approval UX;
- exact risk scoring and tier escalation rules;
- detailed action identifiers and resource mappings;
- approval expiry durations by action type;
- emergency-control roles and escalation contacts;
- audit retention and legal-hold implementation;
- provider registry and verification workflow;
- enforcement integration points and failure behavior;
- policy simulation, test and staged rollout tooling;
- customer-facing authorization model for future SaaS.

Any choice that expands owner, agent, worker or external authority requires explicit approval. Non-critical implementation choices may be selected later within this boundary.

---

## 21. Explicit non-goals and authority boundaries

This document does not approve implementation readiness, authorize repository/GitHub/code access, authorize API or policy-engine implementation, connect external accounts/providers, select cloud/identity/policy vendors, provision infrastructure or incur expenditure, approve autonomous public publishing, authorize uploads/distribution/public release, authorize spending/subscriptions/binding commercial commitments, grant new permissions, or change mission, policy or architecture.

Each such action requires its own applicable authorization.

## 22. Architecture decision summary

| Decision | Standard |
|---|---|
| Authorization basis | Subject + action + resource + scope + context + policy + evidence + limits |
| Decision outcomes | ALLOW, ALLOW_WITH_CONDITIONS, PENDING_APPROVAL, DENY, BLOCKED, INDETERMINATE |
| Unknown authorization | Fail closed for protected actions |
| Policy precedence | Higher-level restrictions cannot be weakened by lower-level policy |
| Agent permissions | Task-scoped, least privilege, no self-grant |
| Human approval | Exact action/resource/version/target and policy scope |
| Owner silence | Never approval |
| Hard blockers | Not bypassable by ordinary approval |
| Public publishing | Disabled pending separate explicit owner policy |
| Financial authority | AI recommendation/preparation only |
| Infrastructure scaling | Only within approved services and budget envelope |
| Provider data processing | Verified protections required; otherwise block |
| Customer data | No sale, licensing or monetization |
| Emergency controls | Layered, audited, scoped and revocable |
| Foundational/security policy | Owner-controlled |

---

**End of Artifact 04 — Policy & Authorization Decision Matrix 1.0**

**Next recommended artifact:** Artifact 05 — Module-to-Contract Traceability Matrix 1.0.
