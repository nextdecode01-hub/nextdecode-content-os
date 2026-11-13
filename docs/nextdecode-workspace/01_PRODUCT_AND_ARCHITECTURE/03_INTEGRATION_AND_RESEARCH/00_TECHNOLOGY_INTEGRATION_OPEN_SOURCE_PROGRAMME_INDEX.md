# NEXTDECODE — Technology, Tools, Integrations & Open-Source Programme

Document ID: ND-INT-INDEX-001
Version: 0.1.0-draft
Date: 2026-11-04
Status: DRAFT — planning and research control; no adoption or implementation authorization
Authority: Subordinate to accepted P0 ADRs/CFs, canonical contracts and owner decisions
Scope: NEXTDECODE Content OS and its existing Shorts Studio specialist engine only

## Purpose
This programme creates one controlled, evidence-backed place to discover, evaluate, select, integrate and maintain technologies, external services, developer tools, agents, MCP tools and GitHub repositories. It extends the existing integration/research area; it does not replace the P0 or P1 architecture documents.

## Authority and non-duplication
1. Accepted P0 ADR/CF decisions and canonical contracts remain authoritative.
2. Existing Shorts Studio remains the specialist production engine; Content OS is built around it.
3. P0-A remains a narrow vertical slice, not a full Control Center.
4. P1 remains a draft subordinate to P0 until owner review.
5. A catalogue entry is not an adoption decision. A proposed integration is not an implementation instruction.
6. No code, Git, tests, dependencies, credentials, provider accounts, paid services, deployment, uploads or publishing are authorized by this programme.
7. Do not create duplicate canonical schemas or competing contracts; reference the canonical owner and contract version.

## Programme folders
| Folder | Responsibility |
|---|---|
| 01_TOOL_AND_TECHNOLOGY_CATALOGUE | Stack components, libraries, runtimes, AI providers, developer/quality tools, infrastructure |
| 02_EXTERNAL_INTEGRATION_CATALOGUE | Provider integrations, APIs, SDKs, CLI, MCP, data flows and failure semantics |
| 03_GITHUB_OPEN_SOURCE_REPOSITORY_CATALOGUE | Repository discovery, evaluation, adoption, rejected/deferred decisions and POCs |
| 04_AGENT_AND_TOOL_ASSIGNMENT | Which human/agent/service uses which tool, under what permission and task boundary |
| 05_INTEGRATION_IMPLEMENTATION_BLUEPRINTS | Versioned contracts, implementation work packages, config/secrets and acceptance tests |
| 06_EVALUATION_SECURITY_LICENSING | Technical, licence, commercial, security, privacy and maintenance evaluation |
| 07_MAINTENANCE_AND_VERSION_GOVERNANCE | Version compatibility, upgrades, deprecation, health reviews and rollback |
| 08_RESEARCH_EVIDENCE_AND_DECISIONS | Research briefs, source evidence, scorecards and owner decisions |

## Mandatory catalogue fields
Every technology/tool: ID, name, category, canonical source, official docs, version/date checked, problem solved, proposed component, user/agent, purpose, integration surface, data touched, dependencies, licence/terms, cost/free limits, security/privacy, maturity/maintenance, alternatives, decision state, owner, evidence, review date.
Every external integration: provider/API, official endpoint/docs, auth scopes, caller, purpose, request/response schema, data classification, rate limits, retries/idempotency, timeouts, webhook/events, failure/unknown-outcome handling, audit, cost, secrets location, tests, rollback, owner and approval.
Every GitHub repository: URL, owner, stars/forks only as dated context (not quality proof), latest release/commit checked, licence and exact licence file, language, dependency health, security advisories, maintainers/activity, architecture fit, code quality, integration method, fork/vendor risk, commercial constraints, PoC evidence, decision and implementation plan.

## Traceability chain
Requirement → Capability → Component → Canonical entity/contract → Tool or provider → Agent/service owner → Integration/work package → Configuration → Test case → Acceptance evidence → Owner decision → Maintenance record.
Each link must use stable IDs. Missing links are recorded as gaps, never inferred.

## Status vocabulary
DISCOVERY_BACKLOG; UNDER_RESEARCH; EVALUATED; RECOMMENDED; OWNER_APPROVED; ADOPTED; DEFERRED; REJECTED; RETIRED.
Also record evidence confidence: VERIFIED_PRIMARY_SOURCE; VERIFIED_REPOSITORY; SECONDARY_SOURCE; INFERENCE; UNKNOWN.
Never label a tool FREE without current pricing/limits evidence. Never label a repository safe/commercially usable without licence and security review.

## Initial priority order
1. Inventory current stack and live integrations from the repository and existing docs (read-only).
2. Reconcile each item with P0/P1 architecture and existing accepted decisions.
3. Build component-to-tool-to-agent responsibility map.
4. Discover candidate GitHub repositories and provider tools from official sources.
5. Evaluate licences, security, maintenance, cost and technical fit.
6. Create integration-specific contracts and implementation work packages.
7. Owner review; only then separately authorize implementation.

## Change control
Every change to a catalogue record records old/new value, evidence, impact on dependent components/contracts/work packages, compatibility, tests, decision authority and date. Superseded records remain discoverable. Do not silently overwrite decisions.

## Programme status
Initial folder structure created on 2026-11-04. On 2026-11-13, the first core-stack/future-extension fit scorecard (ND-INT-EVAL-002) and proposed parallel agent handoff pack (ND-INT-HANDOFF-001) were added under the existing research and assignment folders. These are preliminary research artifacts only. Independent agent reports, current official-source verification, catalogue population, owner decisions and implementation work packages remain pending.
