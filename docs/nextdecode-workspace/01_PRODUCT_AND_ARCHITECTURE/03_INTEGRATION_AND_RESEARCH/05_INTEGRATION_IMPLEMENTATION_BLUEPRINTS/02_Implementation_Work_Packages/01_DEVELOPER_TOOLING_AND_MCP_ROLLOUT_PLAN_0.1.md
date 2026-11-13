# NEXTDECODE — Developer Tooling and MCP Rollout Plan

Document ID: ND-INT-PLAN-001
Version: 0.1.0-draft
Date: 2026-11-04
Status: PROPOSED PLAN — no installation or configuration authorization

## 1. Goal
Introduce developer/reviewer tool integrations only where they materially improve safe work on NEXTDECODE. Start with read-only visibility and evidence quality. Write-capable integrations remain separate and require scoped authorization.

## 2. Work package sequence
| WP | Name | Objective | Inputs/dependencies | Deliverables | Acceptance evidence | State |
|---|---|---|---|---|---|---|
| DEV-00 | Client and host inventory | Identify actual client hosts, versions, native GitHub/filesystem capabilities and supported MCP transports | Owner-approved read-only inspection scope | Client capability matrix; host runtime matrix | Each client has verified version, supported transport, auth and permission controls | READY FOR READ-ONLY DISCOVERY |
| DEV-01 | GitHub read-only access design | Define native connector vs official GitHub MCP usage for ChatGPT and local agents | DEV-00; GitHub repo scope; credential owner | Exact tool allowlist, token-scope matrix, secret handling, revocation plan | Prove only required repository/PR/commit/security reads are available; all writes absent | BLOCKED ON DEV-00 |
| DEV-02 | Filesystem read-only sandbox design | Design isolated filesystem MCP or safer equivalent | DEV-00; target repository path; Docker/OS capabilities | Container config, mount map, package pin, network restrictions, threat model | Disposable fixture proves no writes, no path escape, no symlink escape, no unrelated path visibility | BLOCKED ON DEV-00 |
| DEV-03 | Existing skills inventory | Avoid duplicate skill installs and identify reusable task instructions | Explicit read-only local inspection | Skill inventory with provenance, version, scope, active/inactive and duplicates | Every existing skill path inspected; no files modified | READY FOR READ-ONLY DISCOVERY |
| DEV-04 | Agent framework decision | Decide whether PydanticAI, LangGraph or neither is required | P0 WP2/WP3 boundaries; capability gap from current code; DEV-00 | Comparison and ADR proposal, not adoption | Demonstrate concrete requirement, no overlap with durable workflow/job authority, operational/cost/licence comparison | BLOCKED ON ARCHITECTURE GAP EVIDENCE |
| DEV-05 | Observability decision | Define whether LLM tracing/evaluation needs Langfuse or a simpler local solution | Batch 21; privacy/data retention; current telemetry baseline | Data-flow design, redaction policy, cost/hosting comparison | No sensitive prompts/secrets retained; retention/backup/restore and access controls specified | BLOCKED ON GOVERNANCE |
| DEV-06 | Security and owner review | Approve or reject each candidate independently | DEV-01..05 evidence | Decision records and exact allowed configuration | Owner/security approval names exact versions, scope, host, identity and review date | PENDING |
| DEV-07 | Implementation package | Translate only approved decisions into isolated implementation tasks | DEV-06 approval; approved contracts | Exact config/installation steps, rollback, test cases, acceptance criteria | Reproducible, scoped and reversible implementation evidence | NOT AUTHORIZED |

## 3. Recommended sequencing
- Start DEV-00 and DEV-03 as read-only inventory tasks.
- In parallel, prepare design-only drafts for DEV-01 and DEV-02. Do not install packages or create credentials.
- Defer agent framework selection until a real capability gap is shown. The accepted P0 execution architecture is not up for replacement by a library preference.
- Defer Langfuse until telemetry, privacy and retention requirements are explicit.
- Require owner/security approval before any configuration or credential action.

## 4. Candidate architecture direction
### GitHub access
Use the existing ChatGPT GitHub connector for ChatGPT work if its connected repository scope and read-only capabilities are sufficient. For local IDE/agent clients, evaluate the official GitHub MCP read-only endpoint with repository-limited credentials and a narrow read-tool allowlist. Avoid duplicate access paths.

### Local filesystem access
Prefer existing desktop/IDE project access when it can enforce read-only scope. If MCP is needed, run a pinned server inside a container that exposes only the Shorts Studio repository via a read-only mount. The server allowlist is an additional guardrail, not the enforcement boundary.

### Git inspection
Prefer GitHub remote read APIs or a read-only copy of the repository. Do not expose a Git MCP server with mutating operations to reviewer agents. A repository selector is not a substitute for read-only enforcement.

### Agent runtime
Keep current provider SDKs and the P0 durable workflow system unless a concrete requirement proves they are insufficient. PydanticAI and LangGraph are alternative libraries for bounded agent reasoning, not platform workflow engines or authorization systems.

### LLM observability
Start with a privacy-aware, local structured trace design if possible. Adopt a hosted/self-hosted tracing platform only after data retention, redaction, storage and operational costs are approved.

## 5. Non-goals
- Replacing Shorts Studio.
- Replacing n8n or the P0 durable workflow/job architecture without a separate architecture decision.
- Installing all candidate MCP servers.
- Granting general write access to agents.
- Enabling automatic public publishing.
- Adding paid services or using paid API quotas.
- Running production tests, live provider probes or external side effects.

## 6. Rollback requirements
Every approved installation/configuration must specify: prior config backup; exact package/image version; removal steps; credential revocation; cache/state cleanup; host restart impact; verification that previous tool state is restored; and a record of any data left behind. Rollback must not delete user project data or credentials without explicit instruction.

## 7. Exit criteria for this plan
- Client/host matrix verified.
- Tool permission matrix reviewed by owner/security.
- DEV-01/02 security tests passed in disposable environment.
- Duplicate skills and integration paths resolved.
- Each candidate has a documented owner decision: adopt, defer or reject.
- Any adopted tool has a version-pinned implementation package and reversible change plan.
