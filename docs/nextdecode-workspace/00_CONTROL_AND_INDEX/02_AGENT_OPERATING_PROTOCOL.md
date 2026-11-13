# NEXTDECODE — AGENT OPERATING PROTOCOL

Version: 0.1.0-draft
Applies to: Every human and AI agent working on NEXTDECODE documentation or engineering.

## 1. Mandatory start sequence
1. Read 00_CONTROL_AND_INDEX/00_MASTER_INDEX.md.
2. Read 01_DOCUMENT_REGISTER.md and the latest change log.
3. Read the relevant accepted P0 decisions and governing contracts.
4. Read only the workstream documents assigned to your task.
5. Check the open-decision and dependency register before proposing a design or edit.
6. Confirm your task's explicit authorization boundary. If authorization is absent, remain read-only.

## 2. Authority rules
- Owner-approved decisions outrank agent recommendations.
- Accepted P0 ADR/CF decisions outrank working blueprints and P1 drafts.
- Canonical data ownership and API/Event standards outrank local module convenience.
- Reconciliation documents are proposals unless explicitly owner-ratified.
- Do not promote CANDIDATE or DRAFT to ACCEPTED/FROZEN.
- If two authoritative sources appear to conflict, stop the affected design and record exact source, section, impact and decision needed.

## 3. Agent work boundaries
| Role | Allowed responsibility | Not allowed by default |
|---|---|---|
| Architecture coordinator | Cross-document traceability, dependency and conflict register | Changing owner decisions |
| Domain/workstream agent | Work only within assigned WP/domain and approved contract | Editing another domain's canonical schema |
| Backend agent | Implement approved API, persistence and workflow contracts after authorization | Creating competing canonical entities or auth rules |
| Frontend agent | Implement approved contract-aligned UI and integration scaffolding | Owning business rules, bypassing central authorization |
| QA/security reviewer | Independent read-only verification and evidence report | Modifying implementation under review |
| Product/UI reviewer | Targeted UX/product review | Expanding scope without owner approval |
| Integration coordinator | Compatibility, integration and release evidence | Declaring acceptance without evidence |

## 4. Known project ownership continuity
- Qoder: Phase 11 engineering owner / sole writer for the current governance-closure milestone, as previously established.
- OpenCode: Phase 10 engineering/closure owner; read-only API/backend architecture review where assigned.
- Kilo: independent read-only QA/security acceptance after implementation is complete.
- Copilot: focused regression-test review suggestion only.
- Antigravity: targeted product/UI review suggestion only.
These notes preserve prior ownership context; they do not assign new tasks or authorize agent execution.

## 5. Parallel development protocol
Parallel backend/frontend work is permitted only after a shared versioned contract is identified and approved, one canonical owner is named, request/response/event schemas and error semantics are defined, compatibility tests are specified, UI cannot bypass central authorization, and integration/rollback responsibilities are explicit.
P0-A scope remains a narrow vertical slice, not a full Control Center.

## 6. Required agent deliverable
Every agent handoff must specify task ID, objective, named owner and reviewer, exact input documents with versions and paths, accepted decisions and constraints, in-scope files/modules and out-of-scope areas, read/write permissions and permitted commands, dependencies and unresolved decisions, required tests/evidence and acceptance criteria, output format/report path, completion status, deviations, risks and follow-up decisions.

## 7. Safety / preservation rules
No delete, reset, revert, stash, overwrite, broad staging, commit, push, branch/remote changes, credentials changes, paid service, deployment, external upload or public publishing without explicit authorization. Preserve all pre-existing modified and untracked repository files. Documentation organization does not authorize repository operations.

## 8. Status reporting
Use only: NOT_STARTED, IN_PROGRESS, BLOCKED, READY_FOR_REVIEW, ACCEPTED, REJECTED, SUPERSEDED. Include dated evidence. A test claim must name exact command, environment, commit and output; never infer from historical reports.