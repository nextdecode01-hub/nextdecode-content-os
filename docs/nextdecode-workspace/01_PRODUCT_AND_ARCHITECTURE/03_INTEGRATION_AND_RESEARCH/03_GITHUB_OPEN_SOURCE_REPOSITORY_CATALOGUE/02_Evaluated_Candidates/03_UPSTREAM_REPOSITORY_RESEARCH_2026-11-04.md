# Upstream Repository Research — 2026-11-04

Version: 0.1.0-draft
Status: Evidence-backed first-pass screen; not a security audit or adoption approval.

## Executive decisions

| Candidate | Disposition | Reason / next gate |
|---|---|---|
| GitHub MCP Server (official) | ADOPT FOR EVALUATION | Useful repository context; verify read-only toolset, scopes, repository allowlist and auditability |
| MCP Filesystem Server (official reference) | DEFER deployment | Full toolset includes destructive writes; require OS/container isolation and read-only mount |
| MCP Git Server (official reference) | DEFER | Mutation risks overlap controlled engineering workflow; prove read-only subset first |
| GitHub Awesome Copilot | ALREADY PRESENT AS PROVENANCE; audit selectively | Existing documentation-writer skill has Awesome Copilot provenance; avoid duplicate installs |
| PydanticAI | ADOPT FOR EVALUATION | Python-native typed agent framework and MCP client; test one bounded use case |
| LangGraph | ADOPT FOR EVALUATION as alternative | Stateful graph orchestration, persistence and human checkpoints; compare, do not add both by default |
| Langfuse | DEFER | Useful LLM traces/evaluation; privacy, hosting and licence scope need review |
| Arize Phoenix | DEFER; comparison candidate | OpenTelemetry/OpenInference observability; ELv2 licence requires use-case review |

No repository is approved for installation, vendoring, dependency addition or production use.

## Evidence limits and evaluation standard

This is a first-pass desk review of official repositories and documentation. It is not a complete code audit, dependency audit, vulnerability scan, maintainer verification, legal opinion, runtime test or performance benchmark.

Before adoption, capture: canonical URL; owner; release/tag and commit SHA; SPDX licence and exceptions; release cadence; maintainer concentration; issue/PR aging; security policy/advisories; dependency and SBOM posture; runtime requirements; network/telemetry behavior; credentials and data access; tool permissions; rollback/exit path; measured benefit in a NEXTDECODE use case.

## Candidate details

### 1. GitHub MCP Server
Official repository: https://github.com/github/github-mcp-server

What it is: an MCP server exposing selected GitHub capabilities to compatible AI clients.

NEXTDECODE use: read approved repository metadata, issues, PRs and source files for an engineering work package.

Risks: a GitHub identity can expose private repository data; write-capable tools can create or modify resources. Tool descriptions are not authorization. Use a least-privilege identity, narrow repository access and an explicitly read-only toolset for evaluation. Keep tokens out of prompts, files and logs.

Acceptance test: a test identity can read only the selected repository; create/update/push operations are unavailable or denied; logs contain no token values.

Disposition: ADOPT FOR EVALUATION, not installation approval.

### 2. MCP Filesystem Server
Official repository: https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem

What it is: a Node.js MCP server exposing filesystem read, list, search, metadata and write/move/create operations.

NEXTDECODE use: allow a documentation reviewer to inspect a narrowly scoped workspace without repeatedly attaching files.

Risks: its full toolset includes destructive writes. Allowed-directory settings are useful guardrails, not an OS security boundary. The official README states Node.js 24+ and MIT licensing. The official MCP reference-server collection warns that its servers are educational examples, not production-ready solutions. Recent release notes include filesystem security fixes/advisories, so versions must be pinned and reviewed.

Host constraint: inspected WSL had Node v24.14.1, but Docker CLI/Compose were unavailable. The proposed isolated read-only deployment is therefore blocked on that host. Do not use unisolated filesystem MCP as a workaround.

Acceptance test: isolated process sees only a synthetic read-only fixture; traversal, symlink escape, write, move and delete attempts fail; no secrets are mounted; network egress is disabled unless justified.

Disposition: DEFER deployment until isolation exists.

### 3. MCP Git Server
Official repository: https://github.com/modelcontextprotocol/servers/tree/main/src/git

What it is: a reference MCP server for Git repository operations.

NEXTDECODE use: potentially inspect status, history and diffs.

Risks: Git operations may mutate the index, working tree, branches or commits. It must not become an alternate path around work orders, branch protections, review or authorization.

Acceptance test: only approved read operations are exposed; commit, checkout, reset, add, apply and push are unavailable; sandbox repository remains unchanged.

Disposition: DEFER.

### 4. GitHub Awesome Copilot
Official repository: https://github.com/github/awesome-copilot

What it is: a community catalogue of instructions, agents, skills and configurations.

NEXTDECODE use: discover missing documentation, testing, code review or architecture workflows.

Existing overlap: local documentation-writer skill has Awesome Copilot provenance; p0-documentation-intelligence is project-specific. Audit before adding anything.

Risks: instructions influence agent behavior and may request tools or actions. Community contribution is not security approval. Review each skill's exact licence and linked assets.

Acceptance test: compare existing skills with selected upstream candidates; adopt only a capability gap supported by evaluation.

Disposition: ALREADY PRESENT AS PROVENANCE; selective audit only.

### 5. PydanticAI
Official repository: https://github.com/pydantic/pydantic-ai

What it is: a Python agent framework emphasizing typed inputs/outputs, validation and model/tool integration. Its documentation describes MCP client support and multiple durable-execution integrations.

NEXTDECODE use: bounded specialist tasks such as evidence extraction or structured research classification.

Risks: adds another framework and maintenance surface. It must not redefine canonical entities, workflow/job state, persistence, authorization or publishing policy.

Acceptance test: implement one isolated typed task using deterministic fixtures; compare schema validity, failure behavior, testability and complexity against existing code.

Disposition: ADOPT FOR EVALUATION, conditional.

### 6. LangGraph
Official repository: https://github.com/langchain-ai/langgraph

What it is: a low-level framework for stateful agent workflows, with durable execution, persistence/checkpointing and human-in-the-loop capabilities.

NEXTDECODE use: complex multi-step research/review workflows needing pause/resume, branching and human checkpoints.

Risks: may overlap the Content OS workflow/job state machine, durable queue and n8n. It must not create a second source of truth. Business state remains in the accepted Content OS data model.

Acceptance test: prototype one non-production workflow with pause/resume, human review, retry and crash recovery; prove business state remains consistent and no publishing side effect occurs.

Disposition: ADOPT FOR EVALUATION as an alternative to PydanticAI, not both by default.

### 7. Langfuse
Official repository: https://github.com/langfuse/langfuse

What it is: an LLM engineering platform for traces, debugging, prompt management and evaluation; supports cloud and self-hosting.

NEXTDECODE use: observe model calls, latency, token/cost usage and failures across research/script/visual generation.

Risks: traces may contain prompts, source text, scripts or secrets unless redacted. Self-hosting adds operations; cloud adds data residency/vendor terms. Repository states MIT except for its ee folders; inspect exact paths and licence obligations.

Acceptance test: synthetic trace test verifies redaction, access control, retention/deletion, export and no sensitive payload leakage. Compare with minimal OpenTelemetry-only instrumentation.

Disposition: DEFER pending observability and privacy requirements.

### 8. Arize Phoenix
Official repository: https://github.com/Arize-ai/phoenix

What it is: AI observability and evaluation built around OpenTelemetry/OpenInference; supports tracing, datasets, experiments and evaluation.

NEXTDECODE use: alternative to Langfuse for trace inspection and evaluation.

Risks: repository uses Elastic License 2.0 (ELv2), not a permissive MIT/Apache licence. Review legal fit. Self-hosting still requires storage, access control and upgrades. Verify telemetry configuration and trace-data handling.

Acceptance test: local synthetic-only evaluation verifies data flow, telemetry, retention, licence fit and resource footprint.

Disposition: DEFER; comparison candidate only.

## Cross-candidate rules

- Do not deploy Filesystem MCP until an isolation boundary exists.
- Do not deploy Git MCP while mutation can be reached.
- Prefer one agent framework only if a measured workflow gap exists.
- Start with minimal OpenTelemetry requirements before selecting a full observability platform.
- Do not add Langfuse and Phoenix by default.
- Existing skills must be audited before importing community skills.
- No tool may bypass canonical contracts, centralized authorization, human approval or publishing safety gates.

## Open owner decisions

| ID | Question | Required review |
|---|---|---|
| OSS-01 | Which GitHub identity, repositories and read-only toolset are acceptable? | Owner/security |
| OSS-02 | Which isolation runtime will be supported on WSL? | Owner/engineering/security |
| OSS-03 | Is an agent framework needed beyond existing code and tools? | Architecture/owner |
| OSS-04 | Which telemetry is necessary and what must be redacted? | Owner/security/operations |
| OSS-05 | What licence policy applies to dependencies, skills and hosted services? | Owner/legal |
| OSS-06 | Who owns upstream monitoring and upgrade approval? | Operations/owner |

## Sources
- https://github.com/modelcontextprotocol/servers
- https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem
- https://github.com/modelcontextprotocol/servers/releases
- https://github.com/github/awesome-copilot
- https://github.com/pydantic/pydantic-ai
- https://github.com/langchain-ai/langgraph
- https://github.com/langfuse/langfuse
- https://github.com/Arize-ai/phoenix

Recheck exact releases, security advisories, licence files and dependency manifests immediately before adoption.
