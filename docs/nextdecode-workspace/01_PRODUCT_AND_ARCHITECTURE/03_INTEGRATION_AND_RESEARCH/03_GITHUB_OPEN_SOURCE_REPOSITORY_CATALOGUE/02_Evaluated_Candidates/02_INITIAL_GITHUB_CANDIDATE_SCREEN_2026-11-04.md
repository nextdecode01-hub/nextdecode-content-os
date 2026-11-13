# NEXTDECODE — Initial GitHub Candidate Screen

Document ID: ND-OSS-SCREEN-001
Version: 0.1.0-draft
Research date: 2026-11-04
Status: FIRST-PASS SCREEN — not a security audit, licence opinion, adoption decision or implementation authorization
Scope: NEXTDECODE Content OS / shorts_studio only

## 1. Evaluation rules
- Prefer official upstream repositories and documentation.
- Separate developer productivity tools from runtime product dependencies.
- Preserve the accepted P0 architecture: PostgreSQL-compatible authoritative shared state, DB-backed queue/outbox/inbox initially, centralized authorization and bounded workers/agents.
- Do not introduce a second orchestrator, state store, identity system or governance authority without a documented gap and owner decision.
- Treat README claims as leads; verify exact release, licence file, dependency advisories, deployment burden and current compatibility before adoption.

## 2. Candidate screen
| ID | Candidate | Potential NEXTDECODE purpose | Evidence found | Initial disposition |
|---|---|---|---|---|
| OSS-C01 | github/github-mcp-server | Read-only remote repository/PR/commit/security evidence for engineering review agents | Official GitHub repo describes MIT licence and explicit --read-only mode; toolsets can be allow-listed. | HIGH-PRIORITY EVALUATION. Configure only repo/read/PR-read/code-security-read tools; enforce --read-only and repository-limited token. |
| OSS-C02 | modelcontextprotocol/servers — filesystem | Scoped local access to source/docs/evidence for audit and engineering agents | Official filesystem README supports allowed-directory scoping and Docker read-only bind mounts; MIT licence. | HIGH-PRIORITY EVALUATION. Prefer read-only Docker mount and exactly /home/demon/shorts_studio; never expose whole home or unrelated directories. |
| OSS-C03 | modelcontextprotocol/servers — git | Read-only status/diff/history support for review agents | Official Git server docs say it can read and manipulate repositories, is early development, and without --repository any reachable repo can be targeted. MIT licence. | CONDITIONAL / DEFERRED. Do not enable until write-capable tools are technically unavailable or OS-level read-only isolation is proven; pin --repository to the exact repo. |
| OSS-C04 | github/awesome-copilot | Reusable agent skills, documentation and codebase-onboarding workflows | Official skills catalogue includes documentation-writer, acquire-codebase-knowledge, ai-team-orchestration and other task-specific skills. Existing documentation-writer was previously installed project-scope. | KEEP / AUDIT EXISTING. Avoid duplicate installs; evaluate each skill independently for scope, quality and maintenance. |
| OSS-C05 | pydantic/pydantic-ai | Typed Python agent/tool layer, structured outputs, MCP toolsets and provider abstraction | Official README describes typed agent loop and MCP/toolsets; package metadata states MIT; Python 3.11+ install docs. | EVALUATE AS A THIN AGENT-LAYER CANDIDATE. Must not replace WP2 durable workflow/job execution or central policy. |
| OSS-C06 | langchain-ai/langgraph | Stateful graph orchestration for complex multi-step agent reasoning | Official repo describes low-level stateful agent framework; Python package metadata states MIT and versioned checkpoint packages. | COMPARE AGAINST PydanticAI; do not adopt both by default. Potential overlap with WP2; restrict evaluation to agent subgraphs/checkpoint need, not platform workflow authority. |
| OSS-C07 | langfuse/langfuse | LLM traces, prompt/version observability, evaluations and datasets | Official repo describes agent evals/observability; core repo is MIT except ee folders; self-hosting docs describe Docker Compose for local/test and infrastructure responsibility for production. | EVALUATE LATER WITH BATCH 21. Cost is not only licence: hosting, ClickHouse/DB, backup, retention and operational burden must be included. |

## 3. Important security and architecture findings
### GitHub MCP
The official server has an explicit read-only mode that disables write tools even if they are otherwise selected. It also supports toolset and individual-tool allow-lists. Recommended evaluation configuration: repository-only token, minimum read scopes, read-only mode, and only repositories/PR/commit/security read surfaces required for the assigned agent. Lockdown mode is a best-effort prompt-injection filter, not an authorization boundary.

### Filesystem MCP
Allowed-directory scoping is supported. The safest candidate setup for review is a read-only Docker bind mount of only /home/demon/shorts_studio. A local npx process with write-capable filesystem tools is not equivalent to a read-only boundary. The upstream release history records security fixes for path/symlink handling; pin and review the exact package version and advisories before any installation.

### Git MCP
The server can expose mutating Git operations. The official README says the server is early development and warns that without --repository it can access any reachable repository through tool-supplied repo_path. A repository argument constrains the target but does not itself make the server read-only. Therefore defer unless write tools are removed or an independently verified read-only filesystem boundary is used.

### Agent frameworks
PydanticAI and LangGraph are alternatives to compare, not automatic additions. Both can support agent workflows, but the Content OS already has an accepted durable execution architecture. Neither may become the source of truth for workflow/job state, worker trust, approval or authorization.

### Observability
Langfuse could help trace LLM/model/tool calls and evaluate quality, but the project must first define event/audit boundaries, data redaction, retention and operating cost. It must not become the canonical approval/audit ledger.

## 4. Implementation ownership proposal (not an assignment)
| Candidate | Intended user | Purpose | Boundary |
|---|---|---|---|
| GitHub MCP | Engineering coordinator, architecture reviewer, QA reviewer | Read repo files, PRs, commits and security evidence | Read-only; repo-limited token; no issue/PR writes |
| Filesystem MCP | Documentation intelligence, architecture review, QA | Inspect source, docs, tests, manifests and evidence | Read-only mount; one repo path; no home-directory access |
| Git MCP | Reviewer only if safe mode is proven | Diff/status/history | Deferred until mutation is technically prevented |
| Awesome Copilot skills | Documentation and codebase-intelligence agents | Reusable workflow instructions | Audit existing skills first; skill instructions do not grant tool permissions |
| PydanticAI | Future bounded research/fact-check/strategy agent runtime | Typed Python agent execution and MCP tool integration | No durable job queue, policy or authorization ownership |
| LangGraph | Alternative for complex stateful agent subgraphs | Graph branching, checkpointed agent reasoning | No competing platform orchestrator; compare with PydanticAI |
| Langfuse | AI quality/observability operator | LLM trace/evaluation visibility | Telemetry only; never canonical governance or approval state |

## 5. Exact next evaluation work packages
- OSS-EVAL-01: inspect current installed .agents/skills; inventory skill names, provenance and duplicates; read-only only.
- OSS-EVAL-02: GitHub MCP configuration design; prove read-only mode, token scope, tool allow-list and target repository confinement without creating a token.
- OSS-EVAL-03: Filesystem MCP isolation design; verify Docker read-only bind mount, path scope, symlink/path traversal behavior and no unrelated directory exposure.
- OSS-EVAL-04: Git MCP threat review; establish whether all mutating tools can be disabled; if not, reject for routine review use.
- OSS-EVAL-05: PydanticAI vs LangGraph comparative prototype design; no installation or code changes until authorized.
- OSS-EVAL-06: Langfuse data-flow, privacy, self-hosting and operating-cost review; no provider deployment.

## 6. Sources
- GitHub MCP official repository: https://github.com/github/github-mcp-server
- GitHub MCP configuration guide: https://github.com/github/github-mcp-server/blob/main/docs/server-configuration.md
- MCP filesystem server README: https://github.com/modelcontextprotocol/servers/blob/main/src/filesystem/README.md
- MCP Git server README: https://github.com/modelcontextprotocol/servers/blob/main/src/git/README.md
- MCP server release/security notes: https://github.com/modelcontextprotocol/servers/releases
- Awesome Copilot skills catalogue: https://github.com/github/awesome-copilot/blob/main/docs/README.skills.md
- GitHub skills installation documentation: https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills
- PydanticAI repository: https://github.com/pydantic/pydantic-ai
- PydanticAI installation: https://github.com/pydantic/pydantic-ai/blob/main/docs/install.md
- LangGraph repository: https://github.com/langchain-ai/langgraph
- LangGraph package metadata: https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/pyproject.toml
- Langfuse repository: https://github.com/langfuse/langfuse
- Langfuse self-hosting: https://langfuse.com/docs/deployment/self-host

## 7. Open questions / decision gates
- Which coding/review agents will consume each MCP server, and in which host (ChatGPT, Codex, Qoder, OpenCode, Kilo, Copilot or another client)? This must be mapped to actual tool support, not assumed.
- Does the project need a separate agent runtime library at all, or can existing orchestration and direct provider SDKs meet requirements with less complexity?
- What trace data may be retained, where, for how long, and with what redaction?
- Which repository skills already exist in .agents/skills and are actively used?
- Which candidates are truly free for the intended use, including API quotas, infrastructure and support costs?

No candidate is marked ADOPTED by this screen.
