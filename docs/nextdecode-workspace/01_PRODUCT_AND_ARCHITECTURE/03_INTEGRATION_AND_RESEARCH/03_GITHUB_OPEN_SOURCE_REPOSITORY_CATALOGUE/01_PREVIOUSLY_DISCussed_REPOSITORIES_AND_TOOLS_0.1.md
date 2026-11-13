# Previously Discussed Repositories and Developer Integrations

Document ID: ND-OSS-BASE-001
Version: 0.1.0-draft
Date: 2026-11-04
Status: Historical discussion recovery — candidates only; verify current upstream state before use

## 1. Purpose and limits
This record recovers specific repositories/tools previously discussed for NEXTDECODE. It is not a fresh upstream audit, adoption approval, licence clearance or implementation authorization. URLs and historical intent are retained; current branch, release, licence, vulnerabilities and maintenance status must be checked directly.

## 2. Recovered candidates
| ID | Repository / tool | Upstream | Previously discussed purpose | Proposed NEXTDECODE user | Status |
|---|---|---|---|---|---|
| OSS-H01 | Awesome Copilot | https://github.com/github/awesome-copilot | Source for reusable agent skills; documentation-writer was previously installed project-scope under .agents/skills. | Documentation workflow / engineering agents | Existing project-scope skill reference; inspect before duplicating |
| OSS-H02 | MCP Filesystem Server | https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem | Scoped filesystem access for inspecting project source, tests, manifests and evidence. | Read-only audit/research agents; narrowly scoped engineering agents if later authorized | Candidate integration; command previously discussed: npx -y @modelcontextprotocol/server-filesystem /home/demon/shorts_studio |
| OSS-H03 | MCP Git Server | https://github.com/modelcontextprotocol/servers/tree/main/src/git | Read-only repository history, diffs, branches and change inspection. | Architecture/review/QA agents | Read-only intent; no write scope |
| OSS-H04 | GitHub MCP Server | https://github.com/github/github-mcp-server | Remote repository, commits, pull requests and review evidence. | Engineering coordinator and read-only review agents | Optional; repository-limited read-only access preferred |
| OSS-H05 | Genfeed.ai | https://github.com/ | Architectural reference discussed for memory/context, approval-first workflows and execution visibility. | Product/architecture research only | Not a clone/adoption recommendation; prior discussion flagged AGPL-3.0-or-later, so direct code reuse requires legal/licence review |

## 3. Recovered constraints and decisions
- NEXTDECODE GitHub repository: nextdecode01-hub/nextdecode-content-os; remote previously recorded as git@github.com:nextdecode01-hub/nextdecode-content-os.git.
- Git MCP access intent was read-only. Any token should be repository-limited and read-only; no credential is stored in this document.
- Filesystem access must be scoped to /home/demon/shorts_studio, not the whole home directory or unrelated projects.
- GitHub/Filesystem/Git tools are developer/agent infrastructure, not end-user Content OS runtime features.
- The documentation-writer skill was previously installed project-scope from github/awesome-copilot; audit existing .agents/skills before adding anything to avoid duplicates.
- Previously suggested custom skills: P0 Documentation Intelligence, Multi-Agent Task Orchestrator, Architecture & Contract Reviewer, Engineering QA & Security. These are proposals, not confirmed installed skills.
- Do not expand agent permissions because a tool supports write operations. Tool capability and granted authority are separate.

## 4. Required verification before any adoption
For each candidate, record: current upstream URL and maintainer; exact licence file and obligations; latest release/commit checked with date; supported OS/runtime; package provenance; open security advisories; dependency health; permission model; data sent/stored; network exposure; secrets handling; install/update path; reproducible test; rollback/uninstall; owner and review interval.

## 5. Next evaluation order
1. Verify already-installed documentation-writer skill and inventory .agents/skills without modifying it.
2. Evaluate filesystem MCP and Git MCP as least-privilege local development interfaces.
3. Evaluate GitHub MCP with repository-only, read-only scopes and no write tools.
4. Decide whether custom NEXTDECODE skills add unique value or duplicate existing capabilities.
5. Keep Genfeed as a product/architecture reference unless a separate licence review explicitly approves code reuse.

## 6. Evidence status
The repository names and earlier intentions are recovered from prior project discussions. No upstream repository was fetched or inspected as part of this record. All current licence/security/maintenance assertions remain unverified except the historical AGPL warning noted above.
