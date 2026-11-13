# External Technology Handbook — Volume 01
## Integration Foundations, APIs, MCP, GitHub and Filesystem

Version: 0.1.0-draft | Date: 2026-11-04
Status: Learning/design guide; no setup is authorized.

## 1. How external tools connect to NEXTDECODE

NEXTDECODE has internal business rules. External tools provide specialist capabilities: a model generates text, a TTS provider creates narration, a storage service stores media or a platform API distributes content.

Safe flow:
1. Workflow identifies a required capability.
2. Domain component validates request and authorization.
3. Provider-neutral adapter translates the internal request to provider format.
4. Provider performs the operation.
5. Adapter normalizes response, errors, IDs, usage and timestamps.
6. System records evidence and state using canonical contracts.
7. Reconciliation handles timeouts and ambiguous outcomes.

A provider supplies a capability; it does not own NEXTDECODE identity, workflow, rights, approval or authorization.

## 2. Integration vocabulary

### API
An Application Programming Interface is a defined way for one system to request data/actions from another. Its contract specifies operations, input/output, authentication, errors and limits.

### SDK
A Software Development Kit is a language-specific library wrapping an API. It simplifies calls but does not remove authentication, error, rate-limit or data-handling responsibilities.

### CLI
A Command-Line Interface is a terminal-controlled program. It is useful for automation but may read/write files, use credentials or execute commands. Permissions matter.

### HTTP request/response
A client sends a method, URL, headers, authentication and optional body. The server returns a status, headers and body.
- GET commonly retrieves information.
- POST commonly submits or creates an operation.
- PUT/PATCH commonly replaces or modifies.
- DELETE commonly removes.
Never assume an operation is safe to retry without checking its contract.

### Webhook
A service sends an HTTP request to your application when an event occurs, such as a completed video render. Verify signatures, timestamps, replay protection, idempotency, payload schema and retry behavior.

### OAuth
A delegated authorization protocol used when an application accesses a user's platform account. Scopes limit permission. Tokens are credentials and must be protected like passwords.

### Rate limits and quotas
Providers may limit requests/minute (RPM), tokens/minute (TPM), requests/day (RPD) or operation-specific usage. Handle 429 responses, retry-after instructions, backoff, budgets and usage tracking.

### Idempotency
An operation is idempotent when repeating the same request does not create unintended duplicate effects. If a provider times out after accepting a request, do not blindly retry. Use idempotency keys, provider IDs or reconciliation.

## 3. MCP — Model Context Protocol

MCP is a protocol allowing an AI application to connect to external tools, resources and prompts through a standardized interface. It is not an AI model, agent framework, authorization policy or security sandbox.

Main parts:
- Host: AI application managing user experience and trust boundary.
- Client: component inside host connecting to a server.
- Server: process/service exposing tools, resources and prompts.
- Tools: callable operations, e.g. reading a file or listing issues.
- Resources: data exposed for reading.
- Prompts: reusable prompt templates.
- Transport: local stdio or remote network transport.

Local stdio starts a process on the same machine. That process inherits the OS identity and accessible resources of its environment. Remote transport introduces network authentication, TLS, endpoint trust and data-egress considerations.

MCP does not guarantee:
- A server is trustworthy.
- OS-level filesystem isolation.
- Tool annotations are enforced.
- Untrusted repository instructions are safe.
- A business action is authorized.
- A described read-only tool is actually read-only.

NEXTDECODE rule: MCP is a tool-access layer below project authorization and governance. Side effects still require canonical authorization.

## 4. GitHub MCP Server

Repository: https://github.com/github/github-mcp-server

Purpose: expose selected GitHub capabilities to compatible AI clients.

Possible use:
- Read approved repository metadata, issues and pull requests.
- Retrieve source files for a named work package.
- Gather review context without manual tool switching.

Risks:
- Connected identity may expose private repository data.
- Write-capable tools can create or modify resources.
- Tool descriptions do not replace GitHub permissions.

Controls:
- Least-privilege identity and narrow repository selection.
- Explicit read-only toolset/mode for initial evaluation.
- No organization-wide access without demonstrated need.
- No tokens in prompts or logs.
- Test that write operations are unavailable or denied.

Acceptance test: a test identity can read only the selected repository and cannot create issues, push commits or modify files/settings.

Status: high-priority evaluation candidate; no configuration/token creation authorized.

## 5. Filesystem MCP Server

Repository: https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem

Purpose: provide filesystem read/list/search/metadata and write/move/create operations through MCP.

Value: a documentation reviewer could inspect a narrow set of project files.

Risk: full toolset contains destructive writes. An allowed-directory list is a useful guardrail, not a complete OS security boundary. The official README specifies Node.js 24+ and MIT licence; the wider official MCP reference-server collection warns that its servers are examples, not production-ready products. Release history includes security fixes/advisories.

Safer design:
- Dedicated low-privilege process identity.
- Only a narrow workspace subdirectory mounted.
- Read-only mount for reviewers.
- No home folder, credentials, browser data, .env, tokens or unrelated repositories.
- Network egress disabled unless justified.
- Separate isolated staging area for future authorized writes.
- Pin versions and review advisories.

Host constraint: inspected WSL had Node v24.14.1, but Docker CLI/Compose were unavailable. The proposed isolated deployment is blocked on that host. Do not run broad unisolated filesystem MCP as a shortcut.

Acceptance test: isolated process reads synthetic fixture only; traversal, symlink escape, write, move and delete fail; no secret file is reachable.

Status: design evaluation only; deployment deferred.

## 6. MCP Git Server

Repository: https://github.com/modelcontextprotocol/servers/tree/main/src/git

Purpose: expose Git repository operations to an MCP client.

Potential value: inspect status, history and diffs.

Risk: Git operations may mutate index, working tree, branches or commits. It must not bypass work orders, branch protections, review or authorization.

Acceptance test: only approved read operations exposed; commit, checkout, reset, add, apply and push unavailable; sandbox working tree unchanged.

Status: deferred.

## 7. GitHub Awesome Copilot

Repository: https://github.com/github/awesome-copilot

Purpose: community catalogue of instructions, agents, skills and configurations.

Potential value: discover reusable documentation, testing, code review and architecture workflows.

Existing overlap: workspace already has documentation-writer with Awesome Copilot provenance and project-specific p0-documentation-intelligence. Avoid duplicates.

Review every skill's source commit, instructions, allowed tools, licence, linked assets and behavior before adoption. Community contribution does not equal security approval.

Acceptance test: compare local skills against selected candidates and import only a proven capability gap.

Status: provenance already present; selective audit only.

## 8. Agent frameworks do not own business workflow

PydanticAI and LangGraph may implement bounded agent behavior. They must not replace canonical Content OS entities, PostgreSQL persistence direction, workflow/job contracts, centralized authorization, approval state or the Shorts Studio specialist engine.

## 9. Security checklist

Before connecting any tool, ask:
- Which OS identity does it run as?
- Which files, repositories and APIs can it access?
- Which operations mutate data?
- Which credentials are available?
- What data leaves the machine?
- What telemetry is collected?
- Can untrusted content manipulate its behavior?
- Can it access unrelated network services?
- Are logs redacted?
- Can it be disabled and rolled back?

Evaluate with synthetic data, read-only access first, exact tool inventory, denied-operation tests and recorded version/licence/configuration.

## 10. Glossary

| Term | Meaning |
|---|---|
| Least privilege | Only the access required for a task |
| Sandbox | Technically isolated execution environment |
| Read-only mount | Filesystem mount the process cannot modify |
| Tool annotation | Behavior hint, not enforcement |
| Prompt injection | Untrusted content attempting to manipulate model instructions |
| Egress | Data leaving the environment over a network |
| Secret | API key, OAuth token or password |
| Audit log | Record of who/what acted and when |
| Rollback | Return to a known-good version/configuration |
| SBOM | Software Bill of Materials listing components |
| Pinning | Selecting an exact dependency version |
| Supply-chain risk | Risk introduced by dependencies, build or distribution systems |

## Sources
- https://modelcontextprotocol.io/
- https://github.com/modelcontextprotocol/servers
- https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem
- https://github.com/modelcontextprotocol/servers/releases
- https://github.com/github/github-mcp-server
- https://github.com/github/awesome-copilot
- https://github.com/pydantic/pydantic-ai
- https://github.com/langchain-ai/langgraph

Verify exact releases, security advisories and licence files again before setup.
