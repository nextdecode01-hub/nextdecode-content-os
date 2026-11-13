# NEXTDECODE Content OS
## Part 6 — Centralized Quality, Rights, Approval & Publishing Governance
**Version:** 1.0  
**Status:** Architecture proposal — not implementation approval  
**Date:** 31 October 2026

---

## 1. Purpose

This document defines the centralized governance layer that determines whether content and its associated assets are eligible to move through production, review, approval, and distribution.

The central principle is:

> Creation may be distributed across studios and agents. Authorization must remain centralized, deterministic, traceable, and enforceable.

The governance layer is independent of any individual studio. Shorts, long-form video, carousels, newsletters, and future formats should use the same policy concepts while applying format- and platform-specific rules.

This document is a proposed architecture baseline. It does not claim that these controls are currently implemented, and it does not authorize code changes, account changes, uploads, or publishing.

### 1.1 Goals

- Centralize quality, rights, safety, approval, and publishing eligibility.
- Prevent studios, agents, and direct adapters from bypassing required controls.
- Separate warnings, review requirements, and hard blockers.
- Bind decisions to exact content, artifact, policy, and destination versions.
- Support conditional automation only within explicitly configured policy.
- Provide a reliable emergency pause and auditable exception process.
- Make policy decisions consistent across studios and distribution channels.

### 1.2 Non-goals

- Replacing specialist quality checks inside studios.
- Treating an LLM opinion as a legal rights determination.
- Allowing a human approval to override a non-overridable hard blocker.
- Enabling automatic publishing by default.
- Selecting a legal compliance standard or platform policy interpretation without review.

---

## 2. Governance architecture

The governance layer consists of distinct services with explicit boundaries.

| Component | Responsibility |
|---|---|
| Quality evaluator | Runs deterministic and specialist quality checks |
| Rights and provenance service | Tracks asset origin, license evidence, permitted use, and restrictions |
| Safety and policy evaluator | Applies platform and workspace safety rules |
| Approval service | Records human decisions against exact versions |
| Publishing policy engine | Determines whether a destination and action are eligible |
| Publish authorization service | Issues short-lived, scoped authorization for a specific operation |
| Distribution adapter | Performs the approved platform operation |
| Audit service | Records decisions, evidence, policy versions, and outcomes |
| Emergency control | Pauses or restricts distribution independently of agents |

These services may initially be modules in one deployable application. Their logical boundaries must still be preserved.

### 2.1 Decision authority

- Agents can produce assessments and recommendations.
- Deterministic evaluators produce machine-readable check results.
- The policy engine combines authoritative check results and configured policy.
- The approval service records human decisions.
- The authorization service issues a narrowly scoped publishing authorization.
- The adapter executes only the operation covered by that authorization.

No agent, studio, or adapter may independently declare content publishable.

### 2.2 One governance path

Every external distribution operation must pass through the same authorization boundary, regardless of whether it is triggered by:
- a user action in the dashboard;
- a scheduled workflow;
- a conditional auto-publishing rule;
- an agent recommendation;
- a command-line utility;
- an API request;
- a studio-specific integration.

A direct adapter invocation without a valid authorization must fail closed.

---

## 3. Governance objects and version binding

Governance decisions must be attached to stable, versioned objects.

### 3.1 Core objects

| Object | Purpose |
|---|---|
| `content_id` | Stable identity of the content item |
| `content_version` | Version of the content's structured record |
| `artifact_id` | Identity of a script, video, image, caption, or other output |
| `artifact_version` | Immutable version of an artifact |
| `artifact_hash` | Integrity fingerprint of the exact artifact bytes |
| `asset_id` | Identity of a source or production asset |
| `rights_record_id` | Rights and provenance record for an asset |
| `policy_id` | Identity of a policy |
| `policy_version` | Exact policy version used in a decision |
| `evaluation_id` | Quality, safety, or rights evaluation |
| `approval_id` | Human approval decision |
| `destination_id` | Platform account, channel, or distribution destination |
| `authorization_id` | Scoped permission to perform a specific distribution operation |
| `distribution_attempt_id` | Identity of an attempted external operation |

### 3.2 Version-binding rule

A governance decision is valid only for the exact versions it evaluated.

At minimum, a decision should bind to:
- content ID and content version;
- relevant artifact IDs, versions, and hashes;
- asset and rights-record versions;
- policy version;
- destination and platform settings relevant to the operation.

If a material input changes, the platform must invalidate or re-evaluate the affected decisions. It must never silently reuse an approval or authorization for different content.

### 3.3 Material versus non-material changes

A policy-controlled change classification should distinguish:
- **Material:** changes to narration, factual claims, visual scenes, music, assets, captions that alter meaning, destination, privacy, or rights-relevant metadata.
- **Potentially non-material:** formatting or metadata changes explicitly permitted by a versioned policy.

The classification itself must be deterministic and auditable. If the system cannot establish that a change is non-material, it should require re-evaluation.

---

## 4. Quality governance

Quality governance determines whether an artifact meets the requirements for its next workflow stage. A quality pass is not publishing authorization.

### 4.1 Quality dimensions

A shared quality framework may include:

1. **Factual integrity** — claims are supported by evidence and uncertainty is represented.
2. **Editorial quality** — clarity, structure, originality, and coherence.
3. **Brand alignment** — voice, audience, visual identity, and positioning.
4. **Format compliance** — duration, dimensions, aspect ratio, captions, and other format rules.
5. **Technical integrity** — valid files, codecs, audio/video integrity, and render completeness.
6. **Asset integrity** — required assets exist, references resolve, and provenance is available.
7. **Accessibility** — captions, legibility, audio clarity, and other applicable checks.
8. **Platform readiness** — destination-specific metadata and content requirements.

The exact checks and thresholds should be defined by format, destination, and policy version.

### 4.2 Check outcomes

Each check should return one of the following:

| Outcome | Meaning | Workflow effect |
|---|---|---|
| `pass` | Requirement satisfied | May proceed to other checks |
| `warning` | Issue recorded but not necessarily blocking | Proceed only if policy allows |
| `needs_review` | Human judgment required | Hold for review |
| `fail` | Requirement not satisfied | Block the affected stage |
| `not_applicable` | Check does not apply | Record rationale |
| `not_evaluated` | Check was not run or evidence is unavailable | Never treat as pass |

A missing check is not a passing check.

### 4.3 Quality gate result

The quality evaluator should return:
- evaluation ID and timestamp;
- evaluator and version;
- exact input artifact references and hashes;
- policy and ruleset versions;
- check results;
- warnings and defects;
- coverage information;
- overall status;
- recommended next action.

The policy engine—not the evaluator or agent—determines whether warnings are acceptable for a specific workflow.

### 4.4 Factual claim governance

For factual content:
- claims should have stable IDs;
- material claims should link to evidence references;
- evidence should preserve source identity, retrieval time, and relevant excerpt or location;
- unsupported, disputed, or stale claims must be surfaced;
- coverage must be measured, not inferred from a general research summary;
- policy defines which claims require correction, review, or blocking.

A reviewer agent may identify possible problems, but deterministic coverage rules and configured policy decide whether a factual gate passes.

---

## 5. Rights and provenance governance

Rights governance applies to every externally used asset, including video, images, music, sound effects, fonts, templates, and third-party text where relevant.

### 5.1 Rights record

A proposed rights record contains:

| Field | Meaning |
|---|---|
| `asset_id` | Linked asset identity |
| `source_type` | Original, licensed, public-domain claim, platform library, user-supplied, or other |
| `source_reference` | Original source or provider reference |
| `creator_or_owner` | Known creator or rights holder |
| `license_name` | License or permission description |
| `license_reference` | Link or stored evidence reference |
| `permitted_uses` | Allowed usage categories |
| `territory` | Geographic limitations, if any |
| `time_limit` | Expiry or duration restriction, if any |
| `attribution_required` | Whether attribution is required |
| `modification_allowed` | Whether edits or derivatives are permitted |
| `commercial_use_allowed` | Whether commercial use is permitted |
| `evidence_status` | Verified, unverified, disputed, expired, or restricted |
| `reviewed_by` | Reviewer or verification process |
| `reviewed_at` | Review timestamp |
| `record_version` | Version of the rights record |

The schema is a proposed baseline. It is not a substitute for legal advice or the complete terms of a license.

### 5.2 Rights states

Proposed asset-level states:
- `verified` — required evidence reviewed and permitted use established for the stated scope;
- `unverified` — evidence is missing or has not been reviewed;
- `restricted` — use is permitted only under specified conditions;
- `disputed` — ownership or permission is contested or inconsistent;
- `expired` — permission or license has expired;
- `prohibited` — use is not permitted under the recorded evidence or policy.

An agent's assertion that an asset is “copyright free” is not sufficient evidence.

### 5.3 Rights gate

The rights gate must evaluate every asset actually present in the final artifact, not merely assets listed in an earlier plan.

The gate should verify:
- every used asset resolves to a registry record;
- the record covers the intended use and destination;
- required evidence is present;
- restrictions and attribution obligations are satisfied;
- licenses or permissions have not expired;
- the final artifact's asset manifest matches the evaluated manifest.

Unknown or unresolved rights must not be silently treated as permitted.

### 5.4 Changes and substitutions

If an asset is replaced, added, removed, or materially edited:
- update the asset manifest;
- bind the new version to its rights record;
- re-run affected checks;
- invalidate any approval or authorization that depended on the previous asset set.

---

## 6. Safety and policy governance

Safety and policy evaluation is separate from editorial quality.

A piece of content may be technically excellent and still be ineligible for distribution.

### 6.1 Policy layers

The policy engine should combine:
1. platform-wide safety and legal constraints applicable to the service;
2. workspace-level rules;
3. brand-specific rules;
4. format-specific rules;
5. destination-specific rules;
6. campaign or content-specific restrictions.

More restrictive applicable rules take precedence. A lower-level policy cannot weaken a higher-priority hard constraint.

### 6.2 Policy rule metadata

Each rule should define:
- stable rule ID;
- version;
- scope;
- severity;
- deterministic or human-reviewed evaluation method;
- required evidence;
- applicable formats and destinations;
- whether it is overridable;
- who may approve an exception, if exceptions are allowed;
- effective date and expiry, where relevant.

### 6.3 Untrusted content

Research sources, user-provided documents, comments, captions, and downloaded assets may contain instructions. These must be treated as data, not as authority to change system rules, reveal secrets, or invoke tools.

---

## 7. Centralized approval service

Approval is a durable, explicit decision against an exact artifact version.

### 7.1 Approval states

Proposed states:
- `not_required` — current policy does not require a human approval step;
- `pending` — approval is required and has not been granted;
- `approved` — authorized reviewer approved the specified scope;
- `rejected` — reviewer rejected the specified version;
- `expired` — approval validity period ended;
- `invalidated` — a material change or policy event invalidated approval.

Approval is distinct from a quality pass, rights pass, or publishing authorization.

### 7.2 Approval scope

Approval must specify:
- the content and artifact versions;
- exact artifact hashes where applicable;
- the intended format;
- destination or destination class;
- privacy or visibility setting, if relevant;
- policy version;
- permitted action;
- optional expiry.

Approval for one platform, format, or privacy level must not automatically authorize another.

### 7.3 Approval invalidation

Approval must be invalidated when:
- a material artifact changes;
- a relevant asset or rights record changes;
- the destination changes;
- the privacy setting changes;
- the governing policy is revised in a way that affects eligibility;
- an approval expires or is revoked;
- an integrity check detects a hash mismatch.

### 7.4 No approval by silence

A pending approval remains pending until an authorized human makes an explicit decision. Time passing, a missed notification, or the user's unavailability does not constitute approval.

---

## 8. Publishing policy engine

The publishing policy engine determines what action is permitted for a specific content item, destination, and time.

### 8.1 Three primary outcomes

<details>
</details>

| Outcome | Meaning | Action |
|---|---|---|
| `AUTO_PUBLISH_ELIGIBLE` | All hard gates pass and current policy permits automatic distribution | Authorization may be issued when execution conditions are met |
| `PENDING_APPROVAL` | Human decision or required review is outstanding | Hold; do not publish |
| `BLOCKED` | A hard requirement failed or a non-overridable restriction applies | Stop; approval cannot bypass the blocker |

A separate `NOT_ELIGIBLE` or `NOT_SCHEDULED` state may be useful for content that is valid but outside the configured publishing window or policy scope.

### 8.2 Conditions for automatic eligibility

Automatic eligibility requires all of the following:
- content is in an eligible workflow state;
- required quality gates pass;
- required factual evidence checks pass;
- rights and provenance checks pass;
- safety and destination policies pass;
- required approvals exist and remain valid, or policy explicitly says they are not required;
- artifact versions and hashes match the evaluated versions;
- destination account is authorized and healthy;
- privacy and metadata settings match the policy;
- frequency, timing, and campaign limits are satisfied;
- emergency pause is inactive;
- policy explicitly permits automatic distribution for this format and destination.

If any required condition is unknown, stale, or unevaluated, automatic eligibility must not be granted.

### 8.3 Conditional automatic publishing

The previously discussed direction was **conditional automatic publishing** as a proposed preference, not a fully finalized publishing policy.

The initial policy proposal was:
- routine, pre-approved short-form social content may become eligible for automatic publishing;
- content requiring review remains on hold;
- hard rights, safety, or validation blockers cannot be overridden by ordinary approval;
- long-form content is not initially in the automatic-publishing scope;
- platform-specific frequency limits and approval windows remain open decisions.

This document does not lock exact platform coverage, frequency caps, time windows, or eligibility thresholds.

### 8.4 Policy evaluation output

A policy decision should contain:
- decision ID;
- content and artifact version references;
- destination;
- policy version;
- each gate result and evidence reference;
- final outcome;
- reason codes;
- decision timestamp;
- next eligible action;
- expiry or re-evaluation conditions.

The system should explain the result in clear terms, such as “blocked because one used music asset has unverified rights,” rather than returning only a generic failure.

---

## 9. Publishing authorization and distribution adapters

A policy decision is not itself a credential to publish. A separate authorization service issues a scoped authorization for one operation.

### 9.1 Authorization scope

An authorization should be bound to:
- one content item;
- one exact artifact version and hash;
- one destination/account;
- one operation (for example, upload or publish);
- one privacy setting;
- one metadata package;
- one policy decision;
- a short validity period;
- an idempotency key.

The authorization should be single-use where practical. If the operation is retried, the adapter must use the same idempotency identity or query the previous operation outcome before creating another external side effect.

### 9.2 Adapter requirements

Every adapter must:
1. Require a valid authorization.
2. Validate scope and expiry.
3. Verify artifact hash and destination.
4. Enforce the authorized privacy setting.
5. Use idempotent operation handling where supported.
6. Record request and response metadata with secrets redacted.
7. Return a structured result to the orchestrator.
8. Never silently fall back to a broader permission or public visibility.
9. Refuse direct execution when authorization is absent or invalid.

Adapters are execution components, not policy engines.

### 9.3 Private-by-default configuration

Privacy defaults must be explicit and platform-specific. The system should never infer that “upload” means “public.”

A destination configuration should define:
- default visibility;
- permitted visibility values;
- whether public release requires additional approval;
- whether scheduled publication is allowed;
- how the adapter verifies the final setting.

The current Shorts YouTube uploader privacy change is a separately reported project change. This architecture document does not verify runtime behavior or authorize changes to other uploaders. Long-form uploader behavior must be assessed separately rather than assumed to match Shorts.

---

## 10. Emergency pause and policy changes

### 10.1 Emergency pause

The platform must provide an independent emergency control that can:
- stop new publishing authorizations;
- prevent queued distribution jobs from starting;
- pause scheduled releases;
- revoke unconsumed authorizations;
- allow safe in-flight operations to be inspected and handled;
- preserve workflow and audit state.

The exact handling of an already-started external upload depends on platform capabilities. The system must not claim it can reverse an operation that the external platform has already completed.

### 10.2 Pause scopes

Potential scopes:
- global distribution pause;
- one platform pause;
- one destination/account pause;
- one content item or campaign pause;
- one studio pause.

The emergency control should be available independently of the agent runtime and local rendering PC.

### 10.3 Policy versioning

- Policies are versioned and immutable once used for a decision.
- Policy updates create a new version.
- Each decision records the exact version evaluated.
- Changes to high-risk rules require explicit human authorization.
- Rollback means selecting a previous approved policy version through a controlled operation, not rewriting history.
- A policy change may trigger re-evaluation of queued or scheduled content.

Agents cannot edit or activate policies.

---

## 11. Governance state model

A simplified lifecycle is shown below. Real workflows may include parallel evaluations and format-specific branches.

```text
DRAFT
  |
  v
QUALITY_EVALUATION
  |
  +---- hard failure --------------------> BLOCKED
  |
  +---- review required -----------------> PENDING_REVIEW
  |                                           |
  |                         rejected --------+
  |                         approved
  |                            |
  v                            v
RIGHTS_AND_SAFETY_EVALUATION
  |
  +---- hard blocker --------------------> BLOCKED
  |
  +---- unresolved review ---------------> PENDING_REVIEW
  |
  v
PUBLISH_POLICY_EVALUATION
  |
  +---- auto not allowed ----------------> PENDING_APPROVAL
  |
  +---- conditional rules pass ----------> AUTO_PUBLISH_ELIGIBLE
  |
  +---- hard restriction ----------------> BLOCKED
                                             |
AUTO_PUBLISH_ELIGIBLE or APPROVED             |
  |                                          |
  v                                          |
AUTHORIZATION_ISSUED                         |
  |                                          |
  v                                          |
DISTRIBUTION_QUEUED                           |
  |                                          |
  v                                          |
DISTRIBUTION_EXECUTION                       |
  |                                          |
  +---- success --------------------------> PUBLISHED / SCHEDULED
  |
  +---- retryable failure ----------------> RETRY_PENDING
  |
  +---- terminal failure -----------------> DISTRIBUTION_FAILED
```

`PENDING_REVIEW`, `PENDING_APPROVAL`, and `BLOCKED` are different states. They must not be collapsed into one generic “needs approval” status.

---

## 12. Audit and evidence requirements

For every governance decision and distribution attempt, preserve:
- decision and evaluation IDs;
- content and artifact versions and hashes;
- asset manifest and rights-record versions;
- policy and ruleset versions;
- check outcomes and evidence references;
- approval identity, scope, and timestamp;
- authorization scope and expiry;
- destination and privacy configuration;
- adapter request/response status;
- platform operation ID where returned;
- retries, errors, and recovery actions;
- emergency pause and policy-change events.

Do not store access tokens or secret values in audit logs. Preserve enough sanitized evidence to explain what the system decided and why.

---

## 13. Security and abuse-resistance requirements

- Only the authorization service can issue publishing authorization.
- Only authorized human roles can approve content or change high-risk policies.
- Agents and studios cannot call external publishing APIs with ambient credentials.
- Every external side effect is attributable to a workflow and authorization.
- Authorization tokens are scoped, short-lived, and protected from reuse.
- The system fails closed if policy, rights, or approval services are unavailable.
- A compromised agent must not be able to publish, change policy, or expand permissions.
- Direct command-line and API paths must enforce the same controls as the dashboard.
- Emergency pause must not depend on the local worker or an LLM provider.

---

## 14. Implementation sequence

### Stage A — Central policy model
- Define gate outcomes and reason codes.
- Define version-bound evaluation records.
- Define policy storage and policy versioning.
- Define rights and asset manifest references.

### Stage B — Approval and authorization
- Implement approval records and invalidation rules.
- Implement publishing policy evaluation.
- Implement scoped, expiring authorization.
- Add audit events for each decision.

### Stage C — Adapter enforcement
- Route every distribution entry point through authorization.
- Remove or disable bypass paths.
- Enforce explicit privacy settings.
- Add idempotency and outcome reconciliation.

### Stage D — Conditional automation
- Define eligible format/destination combinations.
- Define frequency and scheduling constraints.
- Add emergency pause and revocation behavior.
- Run dry-run and failure-injection tests before enabling any real distribution.

This is a proposed sequence. It does not authorize implementation or production publishing.

---

## 15. Open decisions

The following require explicit product, operational, or legal review:

1. Exact quality checks and thresholds by format.
2. Required factual claim coverage by content category.
3. Rights verification standard and who can mark evidence verified.
4. Which policy exceptions are possible, and who may approve them.
5. Exact human approval requirements by format and destination.
6. Initial conditional auto-publishing scope and eligible platforms.
7. Publishing frequency caps, quiet hours, and scheduling rules.
8. Approval expiry and revalidation windows.
9. Emergency pause permissions and notification behavior.
10. Audit and evidence retention periods.
11. Platform-specific privacy and scheduling behavior.
12. Legal review requirements for licenses, claims, and jurisdiction-specific content.

No values should be invented to fill these gaps. They should be decided and versioned before the relevant automation is enabled.

---

## 16. Acceptance criteria

Part 6 is ready to guide implementation when:

- [ ] Quality, rights, safety, approval, policy, authorization, and adapter responsibilities are separated.
- [ ] Every decision binds to exact content and artifact versions.
- [ ] Missing or unevaluated checks cannot be treated as passing.
- [ ] Rights are evaluated against the assets actually used in the final artifact.
- [ ] Approval is explicit, scoped, version-bound, and invalidated by material changes.
- [ ] Hard blockers cannot be bypassed by ordinary approval.
- [ ] All publishing entry points require centralized authorization.
- [ ] Authorization is scoped, expiring, auditable, and idempotency-aware.
- [ ] Privacy settings are explicit and enforced by adapters.
- [ ] Conditional auto-publishing is disabled unless a specific policy enables it.
- [ ] Emergency pause works independently of agents and local workers.
- [ ] Policy changes are versioned and require appropriate human authorization.
- [ ] Direct API and command-line paths cannot bypass governance.
- [ ] Dry-run, failure-injection, and negative bypass tests are defined.
- [ ] No production publishing is inferred or authorized by this document.

---

## 17. Relationship to the other architecture parts

| Part | Relationship |
|---|---|
| Part 1 — System Architecture Master Reference | Defines the overall Content OS and governance direction |
| Part 2 — Shorts Studio Pipeline Contract | Supplies the production artifacts and pipeline stages governed here |
| Part 3 — Shared Data Model & Content Graph | Stores versioned content, assets, evidence, decisions, and relationships |
| Part 4 — Persistent Job Queue, Scheduler & Worker Architecture | Executes, pauses, retries, and recovers governance and distribution jobs |
| Part 5 — Agent Contracts & Orchestration | Defines agent recommendations and bounded tasks; agents cannot authorize publishing |
| Part 6 — Centralized Quality, Rights, Approval & Publishing Governance | Defines centralized eligibility, approval, authorization, and enforcement |

**Next architecture document:** Part 7 — Studio Integration APIs & Artifact Management.

---

**Document status:** Proposed architecture baseline. No implementation, policy activation, account change, upload, or publishing authorization is granted by this document.
