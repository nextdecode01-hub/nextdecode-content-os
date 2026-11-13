# Integration Evaluation and Implementation Work Packages

**Document ID:** INT-WP-001 | **Version:** 0.1 draft | **Date:** 2026-11-04  
**Status:** Proposed sequencing; no implementation authorization  
**Authority:** P0 accepted ADRs/CFs and canonical contracts prevail. P0-A scope remains narrow.

## 1. Work package overview

| WP ID | Name | Priority | Output | Dependency | Gate |
|---|---|---|---|---|---|
| INT-WP-00 | Source and adapter inventory closure | P0 planning | Complete source-to-provider map | Existing baseline | Read-only |
| INT-WP-01 | Canonical contract mapping | P0 planning | Port-to-contract crosswalk | WP1–WP6 reconciliation | Owner review |
| INT-WP-02 | Provider terms, privacy and licence review | P0 planning | Provider legal/data register | Provider shortlist | Owner/security review |
| INT-WP-03 | Capability and cost benchmark design | P1 planning | Reproducible benchmark specification | INT-WP-01/02 | Owner approval before live calls |
| INT-WP-04 | Offline adapter contract harness design | P1 planning | Fixture matrix and test cases | INT-WP-01 | Implementation separately authorized |
| INT-WP-05 | Secrets and execution boundary design | P0/P1 cross-cutting | Credential/permission architecture | WP3 and host inventory | Security approval |
| INT-WP-06 | Storage provider selection | WP4-dependent | Object storage decision record | ArtifactVersion/retention/restore | Owner approval |
| INT-WP-07 | Internal orchestration boundary | WP2-dependent | n8n ↔ Content OS responsibility map | Workflow/job/attempt semantics | Owner approval |
| INT-WP-08 | Read-only GitHub MCP evaluation | DEV-01 | Threat model and permission proof | Isolation/credential design | Explicit authorization |
| INT-WP-09 | Controlled provider pilot design | Later | Provider-specific pilot plan | All applicable gates | Separate explicit approval |
| INT-WP-10 | Maintenance and deprecation governance | P1 | Version and incident register | INT-WP-00..09 | Architecture/security review |

## 2. Detailed work packages

### INT-WP-00 — Close source inventory
**Goal:** establish what is implemented, called, configured by name, documented historically, or actually live.

Tasks:
1. Enumerate provider adapters, SDKs, HTTP clients and every caller.
2. Trace environment variable names to code reads without opening secret values.
3. Record provider/model defaults, timeout, retry, cooldown, response validation and fallback behavior.
4. Identify asynchronous operations, external IDs and idempotency/unknown-outcome handling.
5. Reconcile SRC-INT-001..006; retain conflicts where source evidence is insufficient.

Acceptance:
- Every provider row has source file, symbol/caller, date inspected and evidence status.
- No credential values copied or printed.
- Every undocumented external side effect is flagged.
- No source/config/runtime mutation.

### INT-WP-01 — Map adapters to canonical contracts
**Goal:** ensure external integrations do not introduce parallel lifecycle, identity, approval or persistence models.

Tasks:
1. Map each port family to canonical entity, contract owner, API/event schema and lifecycle.
2. Map generated/retrieved media to Asset/Artifact/ArtifactVersion and immutable manifest references.
3. Map rights, approval, quality and authorization to WP5-owned semantics.
4. Map provider jobs to external operation references; canonical workflow/job/attempt remains WP2-owned.
5. Map distribution actions to Contract 12 and centralized authorization.
6. Record exact clause-level gaps and owner decisions.

Acceptance:
- No provider adapter is a system of record.
- No new canonical state vocabulary introduced without owner decision.
- Missing/ambiguous rights or authorization remains fail-closed.
- No expansion of P0-A beyond its narrow vertical slice.

### INT-WP-02 — Terms, privacy and licence review
**Goal:** prevent a nominally free tool from creating privacy, IP, commercial-use or data-retention risk.

For each provider:
- Terms, DPA, privacy, data retention, training use and region.
- Commercial-use permission and generated-output/voice rights.
- Stock media licence and attribution requirements.
- API usage limits, account eligibility and prohibited use.
- Subprocessor/security information and incident notification.
- Exit/export/deletion procedure.

Acceptance:
- Each use case has an explicit permitted data class and purpose.
- Each asset source has a licence evidence record.
- Free-tier restrictions and commercial eligibility are recorded separately.
- Unknown legal/rights questions are escalated, not guessed.

### INT-WP-03 — Benchmark specification
**Goal:** compare quality, cost and reliability on the same task distribution.

Tasks:
1. Define fixed test set and versioned prompt/template.
2. Define scoring rubric for factual grounding, schema validity, editorial quality and safety.
3. Define latency, retry, 429, cost and output-variance metrics.
4. Define human review and adjudication.
5. Specify account/plan/model identifiers without exposing secrets.

Acceptance:
- Provider comparison is reproducible and normalized.
- No provider wins solely by latency or free-tier status.
- Budget ceiling and stop conditions are explicit.
- Live test execution requires separate approval.

### INT-WP-04 — Offline contract harness
**Goal:** prove adapter behavior without provider credentials or network calls.

Test cases:
- valid success response;
- malformed or schema-incompatible response;
- 400 invalid request;
- 401/403 authentication/permission failure;
- 429 with and without Retry-After;
- 5xx transient failure;
- connection timeout before request acceptance;
- timeout after possible remote side effect;
- async accepted response followed by succeeded/failed/canceled;
- duplicate callback/replayed webhook;
- missing rights metadata or unsupported asset licence;
- provider/model fallback with provenance preserved.

Acceptance:
- Deterministic fixtures and assertions.
- No network calls and no secrets.
- Unknown side-effect outcomes are not retried blindly.
- Provider-specific differences remain explicit rather than normalized away.

### INT-WP-05 — Secret and execution boundary
**Goal:** keep credentials and external side effects outside agent control.

Tasks:
- Define secret manager/runtime environment and credential owner.
- Define service identity, capability scopes, token TTL, rotation/revocation and audit.
- Define network egress allowlist and payload redaction.
- Separate read-only, generation, storage-write and distribution permissions.
- Ensure agent tools cannot directly read secret files or invoke unapproved external writes.

Acceptance:
- No credential values in prompts, logs, files, agent context or artifacts.
- Each operation uses the minimum scope.
- Publishing authorization is rechecked at the side-effect boundary.
- OS/container controls enforce isolation; tool annotations alone are insufficient.

### INT-WP-06 — Storage provider selection
**Goal:** choose object storage only after canonical artifact and retention semantics are clear.

Compare:
- Cloudflare R2;
- local filesystem for development/test only;
- other S3-compatible providers only if a demonstrated requirement exists.

Acceptance:
- ArtifactVersion identity/checksum and relational metadata are authoritative.
- Storage key is opaque and non-authoritative.
- Backup, restore, encryption, access control, retention, legal hold and purge semantics defined.
- Cost model includes storage, operations, retrieval and account/subscription requirements.
- No selection overrides ADR-002 or WP4.

### INT-WP-07 — Orchestration boundary
**Goal:** use n8n as a trigger/orchestration surface without duplicating Content OS durable state.

Acceptance:
- n8n does not own canonical job/attempt state.
- Workflow triggers are idempotent or safely deduplicated.
- Retries and callbacks reconcile with canonical job state.
- Workflow exports, credentials and license posture are documented.
- Customer-facing workflow-builder use is separately reviewed under n8n license terms.

### INT-WP-08 — GitHub MCP read-only evaluation
**Goal:** enable useful repository intelligence without allowing accidental mutation.

Acceptance:
- Exact repository allowlist and least-privilege read-only token.
- Only read/list/search/get operations exposed.
- Write, issue mutation, PR mutation, merge, branch and release actions technically unavailable.
- Credential never exposed to model context.
- Audit trail and revocation procedure.
- If technical read-only enforcement cannot be demonstrated, do not enable.

### INT-WP-09 — Controlled provider pilot
**Goal:** only after all preceding relevant gates close, run one bounded provider operation.

Required owner authorization must name:
- provider and account;
- exact operation and data class;
- environment and target resource;
- maximum calls/usage/spend;
- whether data may be retained;
- start/end window;
- rollback/disable action;
- responsible operator and evidence destination.

No authorization is implied by this work package.

## 3. Dependency sequence

1. INT-WP-00 source inventory closure.
2. INT-WP-01 canonical contract mapping.
3. INT-WP-02 terms/privacy/licence review in parallel with contract mapping.
4. INT-WP-05 secret/execution boundary design.
5. INT-WP-03 benchmark design and INT-WP-04 offline harness design.
6. INT-WP-06 storage decision only after WP4 semantics.
7. INT-WP-07 orchestration decision only after WP2 semantics.
8. INT-WP-08 GitHub MCP only after read-only permission proof.
9. INT-WP-09 any live pilot only with separate explicit authorization.
10. INT-WP-10 ongoing maintenance/version governance.

## 4. No-go conditions

Stop the work package if:
- the canonical contract or owner is unknown;
- the provider terms or data use are unacceptable/unclear;
- credentials would be exposed to an agent or untrusted process;
- cost/quota cannot be bounded;
- the operation is non-idempotent and unknown outcomes cannot be reconciled;
- rights evidence is absent or ambiguous;
- the design duplicates canonical state;
- implementation would expand P0-A or contradict accepted P0 decisions.

## 5. Change log

- 0.1 — Initial work package breakdown and acceptance gates. Planning only; no installation, configuration, code change, test execution or provider activation.
