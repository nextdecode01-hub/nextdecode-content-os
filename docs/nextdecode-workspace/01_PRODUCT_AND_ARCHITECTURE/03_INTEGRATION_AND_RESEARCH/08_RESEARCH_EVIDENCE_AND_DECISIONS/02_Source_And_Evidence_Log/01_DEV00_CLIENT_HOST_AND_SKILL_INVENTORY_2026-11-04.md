# DEV-00 — Client, Host and Existing Skill Inventory

Document ID: ND-DEV-00-001
Version: 0.1.0
Date: 2026-11-04
Status: READ-ONLY INVENTORY — partial; not a full host security assessment
Scope: Authorized Anish WSL2/Windows development environment and currently surfaced ChatGPT integration context

## 1. Allowed and excluded actions
Allowed: read-only directory listing, reading existing skill files, and checking installed runtime versions. Excluded: installing/updating packages, creating credentials, changing MCP/client configuration, reading secret values, running tests, Git commands, modifying source files, enabling services or external side effects.

## 2. Host observations
| Item | Observation | Confidence / limitation |
|---|---|---|
| Project | `/home/demon/shorts_studio` in WSL2 Ubuntu | Path observed through connected Windows device's WSL share |
| Node.js | v24.14.1 | Read-only `node --version` command via WSL; meets current upstream filesystem MCP Node 24+ requirement |
| npm | 9.2.0 | Read-only version command |
| Docker CLI/daemon | `docker --version` returned unavailable in WSL shell | Docker-based MCP isolation cannot currently be assumed available; daemon/runtime state not established |
| Docker Compose | `docker compose version` returned unavailable | Same limitation |
| `.agents/skills` | Contains `documentation-writer` and `p0-documentation-intelligence` | Directory listing and both SKILL.md files read |
| `.vscode` | Listing showed `tasks.json`; no MCP config was visible in that directory listing | Does not establish absence of MCP config in other host/global locations |
| Secrets | `.env`, `.n8n-docker.env`, `youtube_token.json` filenames are present in project root listing | Values were not read; these paths must be excluded from agent mounts |
| ChatGPT GitHub integration | GitHub connector tools are available in current ChatGPT tool environment | Exact connected repository permissions/scopes not yet audited |
| Other local agent clients | Qoder, OpenCode, Kilo, Copilot and Antigravity are referenced in project governance | This inventory does not prove each client is currently installed, connected or configured |

## 3. Existing local skills
### `documentation-writer`
- Path: `.agents/skills/documentation-writer/SKILL.md`
- Provenance metadata: `github/awesome-copilot`, path `skills/documentation-writer`, ref `refs/heads/main`, tree SHA `016d8040a3f91c8360b1003e74fbf29f34c283f5`.
- Purpose: Diátaxis-based technical documentation across tutorial, how-to, reference and explanation types.
- Skill-specific workflow: clarify document type/audience/goal/scope, propose structure, wait for approval before writing.
- External web research is prohibited by this skill unless the user provides a link and instructs its use.
- Assessment: existing reusable skill; do not reinstall or duplicate. Its approval-before-writing rule applies when this skill is invoked for a documentation request.

### `p0-documentation-intelligence`
- Path: `.agents/skills/p0-documentation-intelligence/SKILL.md`
- Purpose: P0 source precedence, handoff, contract, gap, ownership and evidence reconciliation.
- Boundaries: documentation/governance intelligence only; does not authorize code, tests, provider configuration, deployment or publishing.
- Assessment: existing project-specific governance skill; preserve and use for P0 handoffs and reconciliation.

## 4. Immediate design implications
1. Node.js v24.14.1 is compatible with the current filesystem MCP documented runtime prerequisite; this is only a runtime prerequisite check, not a deployment approval.
2. Docker is unavailable in the inspected WSL shell. Therefore the proposed Docker read-only isolation design cannot yet be implemented or proven on this host.
3. Do not fall back to an unisolated npx filesystem server with write-capable tools. Existing local filesystem access and connected desktop tooling should be assessed for read-only boundaries first.
4. If container runtime is later considered, evaluate installation/licensing/resource overhead and Windows/WSL integration separately; do not install it as part of this inventory.
5. Exclude `.env`, `.n8n-docker.env`, `youtube_token.json`, private caches, user home paths and generated output folders from any future agent mount unless a specific task requires a narrowly scoped item.
6. Existing documentation-writer and P0 documentation intelligence skills already cover two useful capabilities. New skills should be added only for demonstrated gaps and must not duplicate these responsibilities.

## 5. Open DEV-00 items
- Verify exact ChatGPT GitHub connector repository scope and permitted operations before relying on it for a sensitive review.
- Inventory Codex, VS Code, Qoder, OpenCode, Kilo, Copilot and Antigravity versions/configuration only when an authorized read-only scope and paths are established.
- Determine whether Podman or another supported isolation runtime exists; current check did not establish it.
- Determine whether the project has global MCP configuration outside `.vscode`; no global settings were inspected.
- Check skill upstream changes only in a separate research pass; current provenance SHA is the local skill metadata, not proof it is latest upstream.

## 6. Evidence references
- Current filesystem MCP README: https://github.com/modelcontextprotocol/servers/blob/main/src/filesystem/README.md
- MCP local server security guidance: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/docs/2026-07-28/tutorials/security/local-server-security.mdx
- GitHub MCP config guidance: https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/configure-mcp-servers

No tools were installed, no settings changed, no secret values read, and no project code or tests executed.
