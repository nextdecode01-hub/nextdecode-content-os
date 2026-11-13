# NEXTDECODE — MCP and Developer Tool Permission Architecture

Document ID: ND-SEC-TOOL-001
Version: 0.1.0-draft
Date: 2026-11-04
Status: PROPOSED SECURITY DESIGN — owner review required; no configuration change authorized
Authority: Subordinate to accepted ADR-005, ADR-007, canonical contracts and security owner decisions

## 1. Objective
Provide agents with the minimum tools needed for their assigned work while preventing tool capability from becoming implicit permission. The design separates: (a) identity and authorization, (b) client-visible tool selection, (c) server-side permission, and (d) operating-system/container isolation.

## 2. Core security rules
1. A tool's advertised readOnlyHint is metadata, not a security boundary.
2. An MCP server's path allowlist is a cooperative application-level guardrail. Enforce filesystem scope using OS/container isolation and read-only mounts where appropriate.
3. Pin server package/container versions and inspect provenance before execution; local MCP servers are ordinary processes with the host process's filesystem, environment and network access unless isolated.
4. Prefer official provider-hosted remote MCP for remote SaaS access when available, rather than installing a third-party proxy with broad credentials.
5. Use the smallest tool allowlist. Do not expose unused write, delete, publish, billing, user-admin or credential-management tools.
6. Secrets are injected by the host's secret mechanism; never write tokens into config files, repository documents, prompts or logs.
7. A read-only agent role is enforced by both tool surface and credential scope. Prompt instructions alone do not make a tool read-only.
8. Tool approval and product authorization are separate. A tool call cannot grant publishing authorization, approve content, or bypass a domain gate.
9. All remote side effects require centralized authorization at the adapter boundary, exact action/resource/version/destination binding, idempotency and outcome reconciliation.
10. Untrusted repository files, webpages, issues, prompts and tool outputs must never be interpreted as policy or instructions that override system/owner rules.

## 3. Permission tiers
| Tier | Name | Allowed capability | Default users | Explicitly excluded |
|---|---|---|---|---|
| T0 | Public research | Public web/docs/repository metadata; no private workspace access | Research agents | Private files, credentials, write actions |
| T1 | Workspace read-only | Read/list/search within one approved project mount | Documentation, architecture, QA reviewers | Write, delete, shell, home directory, unrelated repos |
| T2 | Repository read-only | Read private repo files, PRs, commits, checks and security evidence | Engineering/QA reviewers | Push, merge, issue/PR mutation, settings, secrets write |
| T3 | Scoped engineering write | Edit only assigned files/branch through approved workflow | Named implementation agent for a specific work package | Default branch writes, secrets, publishing, unrelated modules |
| T4 | Protected external action | Exact owner-authorized export/publish/provider operation | Protected adapter/service under central authorization | General-purpose agent direct action or broad token |

No user, agent or service inherits a higher tier by virtue of having access to a client or MCP server. Tier T3/T4 require separate work-package or policy authorization.

## 4. MCP/developer integration matrix
| Tool | Proposed tier | Required controls | Decision |
|---|---|---|---|
| GitHub connector in ChatGPT | T2 where repository access is read-only | Verify connected repo scope and available actions; do not assume all operations are read-only | Prefer existing connector for ChatGPT tasks; avoid duplicate server if it meets need |
| GitHub official MCP server | T2 | Use official read-only endpoint/mode; repo-limited credential; allow only read tools/toolsets; verify host supports the required transport | Evaluate for local IDE/agent clients that lack equivalent native integration |
| Filesystem MCP | T1 | Container/OS sandbox with only the target repository mounted read-only; command-line allowlist; pin package/image; no broad environment secrets; network egress restricted where practical | High-priority candidate, but only after host isolation and client compatibility test |
| Git MCP | T1/T2 | Exact repository target; remove mutating tools at server/client boundary; read-only filesystem backing or equivalent OS enforcement | Defer until technically inert; `--repository` alone is not read-only |
| GitHub CLI | T2 for inspection; T3 only if separately authorized | Dedicated least-privilege auth context; read-only commands for reviewers; avoid inherited broad personal token | Existing local availability and scopes must be inventoried before use |
| Agent skills/instruction packs | No permission tier by themselves | Review provenance, content, version and allowed tool calls; skills never grant credentials or authorization | Audit existing `.agents/skills` before adding new skills |
| PydanticAI / LangGraph | Runtime library, not permission tier | Agent toolsets must be allow-listed; tool calls use service identity and policy gateway; durable workflow/job state stays with P0 control plane | Compare only if a concrete agent-runtime gap is demonstrated |

## 5. Filesystem MCP reference configuration principles
The upstream filesystem server supports command-line allowed directories and marks its write-capable tools separately. Its documentation also supports a Docker read-only bind mount. For NEXTDECODE review use:
- Mount only `/home/demon/shorts_studio` to a fixed in-container path, e.g. `/workspace/shorts_studio`.
- Use a read-only bind mount (`ro`) and a non-root container user.
- Start the server with only `/workspace/shorts_studio` as its allowed root.
- Do not mount `/home/demon`, the Docker socket, SSH directories, `.env` secrets or unrelated workspaces.
- Disable write tools in the client tool allowlist as defense in depth; the read-only mount is the enforcing layer.
- Pin the package/container by immutable version or digest and maintain an update/review record.
- Validate path traversal, symlink escape, absolute path, `..`, and attempted write behavior in a disposable test fixture before any real project connection.
- Node.js 24+ is listed by current upstream documentation for npx/source execution; verify the target host version before considering deployment.

A client-side allowlist or MCP tool annotation alone is not sufficient. If the host cannot provide a genuine read-only filesystem boundary, do not connect the production repository.

## 6. GitHub MCP reference configuration principles
- Prefer the official GitHub read-only endpoint/mode when using the official hosted service.
- Use a fine-grained, repository-specific credential with minimum contents/metadata/PR read permissions required for the task.
- Allow only required read toolsets, such as repository contents, pull request read, commit read and code-security read where actually needed.
- Exclude issue/PR writes, comments, merge, branch creation, Actions dispatch, repository settings, secrets, administration and workflow mutation.
- Never put a PAT in a checked-in config. Use host-managed secret storage and expiration/rotation.
- Verify the client is connected to the intended repository before each work package; do not rely on a model instruction to limit repository scope.
- Use the existing ChatGPT GitHub connector for ChatGPT-side work if its connected scope and read/write actions meet the task; do not add redundant infrastructure without a client gap.

## 7. Git MCP deferral rationale
The upstream Git MCP server exposes repository operations that can mutate state. Passing an exact `--repository` restricts the target but does not disable writes. Therefore, it is not approved for routine architecture/QA review until one of the following is demonstrated:
- the server build/tool surface contains only non-mutating operations; or
- the server process sees a read-only repository/filesystem and cannot reach a writable copy; and
- the host does not provide a shell or alternate write path that bypasses the MCP restriction.

If these conditions cannot be proven, use GitHub's read-only remote interface or direct read-only file/diff evidence instead.

## 8. Agent permission profiles (proposed)
| Profile | Tools exposed | Data scope | Approval requirement |
|---|---|---|---|
| Research Analyst | Public search/browser, approved source connectors | Public sources and explicitly provided research material | No private workspace or external side effects |
| Documentation Reader | Filesystem read/list/search | One approved docs/repo mount | No write access |
| Architecture Reviewer | Filesystem read-only + GitHub read-only | Assigned repo and canonical architecture docs | No code/document edits |
| QA/Security Reviewer | Filesystem read-only + GitHub read-only + test evidence reader | Assigned branch/commit and evidence package | No fixes during independent acceptance |
| Implementation Agent | Approved editor/filesystem write for exact worktree + test runner only | Work-package file allowlist and assigned branch | Explicit task-specific authorization; review before merge |
| Production Worker | Narrow service APIs and scoped artifact storage | Assigned job/artifact versions only | Central policy checks; no self-approval |
| Publishing Adapter | Provider-specific protected API | Exact authorized content/version/destination | Central authorization, human approval and outcome reconciliation |

## 9. Security validation checklist before connection
- [ ] Client and MCP server versions pinned and provenance checked.
- [ ] Server process runs with least OS identity and minimal environment.
- [ ] Filesystem sandbox exposes only the intended repository and is read-only for review.
- [ ] No `.env`, SSH key, cloud credential, Docker socket or unrelated home path is mounted.
- [ ] Network egress is restricted to required provider domains where feasible.
- [ ] Tool allowlist contains only necessary operations; destructive tools absent.
- [ ] Credentials are least-privilege, short-lived where possible, scoped and revocable.
- [ ] Tool output and untrusted content are treated as data, not instructions.
- [ ] Logs redact tokens, prompts containing sensitive data and private content not needed for audit.
- [ ] A disposable test proves read-only behavior, path confinement and denial on attempted escape/write.
- [ ] Owner/security review records the exact configuration, version, scope and expiry/review date.

## 10. Implementation order (proposal only)
1. Inventory actual client hosts and available native integrations (ChatGPT, Codex, VS Code, Qoder, OpenCode, Kilo, Copilot). Do not assume one config works everywhere.
2. Confirm current Node/Docker availability on the target host without changing it.
3. Decide whether native GitHub connector already covers ChatGPT workflows.
4. Design GitHub MCP read-only config for local agent clients, without creating credentials.
5. Design filesystem MCP isolated read-only container and disposable security test.
6. Evaluate Git MCP only after a write-inert configuration is technically demonstrated.
7. Owner approves or rejects each integration separately.
8. Only after approval create a dedicated implementation work package; no install/config change is authorized by this document.

## 11. Evidence and references
- MCP local server security guidance (2026-07-28): https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/docs/2026-07-28/tutorials/security/local-server-security.mdx
- Official MCP filesystem server README: https://github.com/modelcontextprotocol/servers/blob/main/src/filesystem/README.md
- GitHub MCP configuration guidance: https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/configure-mcp-servers
- GitHub MCP concepts and configuration: https://docs.github.com/en/copilot/concepts/customizations/mcp
- VS Code MCP configuration and sandboxing: https://code.visualstudio.com/docs/agents/reference/mcp-configuration
- PydanticAI MCP client: https://pydantic.dev/docs/ai/mcp/client/

## 12. Open owner decisions
- Which client hosts need local MCP access versus existing native connectors?
- Is the filesystem review server worth the Node/Docker dependency, or do existing desktop tools provide safer read-only access?
- Who owns credential creation, rotation and revocation for any remote MCP connection?
- What exact repo paths may each agent inspect, and are `.env`/generated media directories excluded?
- Is any agent runtime framework necessary beyond existing Python/provider SDKs and P0 workflow execution?
