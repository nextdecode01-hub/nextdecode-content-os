# NEXTDECODE Plans — Implementation Reality Reconciliation

**Date:** 2026-11-15  
**Purpose:** Distinguish previously discussed plans from verified repository implementation. This is a current repository inspection, not a claim that every historical design contract has been implemented.

## Executive answer

**No: all previously discussed plans have not been executed.** The repository contains substantial implementation across Shorts Studio, local autonomy, Dashboard and production observability, but several foundational P0 contracts and end-to-end acceptance gates remain incomplete. Some older documents are planning/historical sources and explicitly say they do not authorize or prove implementation. Current code must be judged by runtime evidence, not by the existence of those documents.

## Status vocabulary

- **Implemented (code present):** implementation exists in the current worktree; runtime acceptance may still be separate.
- **Tested:** relevant tests actually ran and passed in the current environment.
- **Partial:** a local/prototype implementation exists but does not satisfy the canonical shared-system contract.
- **Documented/proposed:** architecture/specification exists, but code implementation is not evidenced.
- **Not verified:** current runtime or production behavior has not been established.
- **Not implemented:** no implementation found in inspected source scope.

## Reconciliation snapshot

| Previously discussed area | Current repository evidence | Honest status |
|---|---|---|
| Existing Shorts Studio production pipeline | Research, evidence, script, voice, visual, render, RunTracker and publishing modules exist; many current worktree modifications are uncommitted | Implemented in parts; production acceptance not achieved |
| Automated Edit Director | app/render/edit_director.py, timeline/assembly integration, tests and M1 report | Implemented in current worktree; focused 93 tests passed; real creative acceptance still not achieved |
| Visual asset intelligence | app/visuals/asset_qa.py, modified stock/visual modules, QA report and tests exist | Partial; recent contact sheets show duplicates/repeated composition and incomplete provenance on some candidates |
| Research/script evidence quality | Existing research/evidence/script modules and tests; latest D49 report records a 52-word draft rejected against 92–118 word band in one run | Implemented in parts; latest run blocker is evidenced; rewrite root cause still needs investigation |
| Render/production reliability | Stage manifests and run reports exist; recent run failed at render with generic RuntimeError / unknown in manifest | Partial; exact failure diagnostics need closure; successful full production acceptance not verified |
| Local autonomy planner and task queue | app/autonomy has planner, capability registry, task DAG, SQLite adapter, local PostgreSQL adapter, leases, retries, events and worker heartbeat | Implemented local runtime; not canonical P0 shared control plane |
| Worker identity/isolation/agent contracts | Worker identity/lifecycle, sandbox, agent contracts, assignment, isolation and runner modules exist with tests | Partial local implementation; canonical WP3 trust/enrollment/credential contracts not proven complete |
| Durable workflow / job system | Local autonomy task DAG and queue exist; canonical WP2 contracts and shared control plane remain distinct | Partial; do not equate local task queue with canonical WP2 |
| PostgreSQL system of record | Local PostgreSQL used by autonomy runtime | Partial; app/autonomy/README.md explicitly says it is not the accepted P0 cloud shared control plane |
| Canonical P0 WP1–WP6 | Accepted architecture decisions and extensive contract/workstream docs exist; multiple docs still list open field/state/event/acceptance conflicts | Documented and partially implemented; not fully closed or verified |
| Centralized governance / publishing | Existing security and publishing boundaries plus authorization tests exist; public automatic publishing disabled | Implemented safeguards in current paths; complete canonical WP5/WP6 conformance remains unverified |
| Dashboard | dashboard/, API integration and D-series reports exist; independent agent owns active Dashboard work | Separate active workstream; this pipeline pass does not claim its completion |
| Central brain | New app/brain deterministic read-only context/decision service, versioned project context and authenticated API | Foundation v0 implemented; persistence, cross-domain state and AI intelligence not implemented |
| AI agents / chatbot | Some bounded local specialists and agent runtime exist; no unified central-brain agent/chat product | Future extension; not the present milestone |
| Blender/original 3D template system | Proposed in production architecture discussions; no current verified integration evidence in this inspection | Not verified / not accepted as implemented |
| Remotion alternative | Evaluated as a candidate only | Deferred; not adopted |
| Music/SFX full production capability | Prior plans and module work exist, but no fresh end-to-end acceptance evidence in this reconciliation | Not verified as complete |

## Accepted architecture decisions versus implementation

docs/archive/legacy-source-imports/NEXTDECODE_Accepted_P0_Architecture_Decision_Baseline_1.0.md records ten owner-accepted architectural directions:

1. UUIDv7 canonical IDs.
2. PostgreSQL-compatible relational system of record.
3. Database-backed durable queue and transactional outbox/inbox initially.
4. Versioned HTTP/JSON contracts with schema validation.
5. Worker identity and capability-based authorization.
6. Artifact metadata in PostgreSQL and binary storage behind an abstraction.
7. Centralized publishing authorization; no adapter bypass; public auto-publishing disabled.
8. Explicit quality outcomes and non-bypassable hard blockers.
9. Evidence-backed, use-specific rights policy.
10. Separate lifecycle state machines.

These are accepted architectural decisions, not proof of completed implementation. The same baseline says hosting, full schemas, transitions, retry/lease semantics, worker credentials, artifact transfer, policy schemas, quality thresholds and operational targets remain open. The canonical master index also says P0-A is a narrow vertical slice and P0 implementation authorization is separate from documentation readiness.

## New central brain foundation v0

Added:
- config/brain/project_context.v1.json — versioned owner direction and production guardrails.
- app/brain/context.py — schema-validated project context loader.
- app/brain/service.py — bounded, read-only run-manifest observer and deterministic next-action recommendations.
- app/brain/api.py — /brain/context, /brain/overview, /brain/decision.
- tests/test_brain.py — six focused tests.

The endpoints inherit the existing bearer API boundary. They do not mutate runs, execute recommendations, call an LLM or persist a decision journal. Dashboard can consume these stable endpoints independently.

## Verification in this increment

- venv/bin/python -m pytest -q tests/test_brain.py tests/test_autonomy_api.py: **15 passed**.
- Full repository suite after brain implementation and API wiring: **1,237 passed, 12 skipped, 71 subtests passed in 120.11s**.
- Python compilation and scoped git diff --check passed after final API wiring.

## Immediate next engineering priorities

1. Complete brain v0 verification and expose its read-only API contract to the independent Dashboard agent.
2. Investigate the latest real pipeline failure from its exact stage evidence; the D49 script-gate failure and later render-stage failures are different runs and must not be conflated.
3. Close stage failure diagnostics so the exact bounded exception category/reason is retained without secrets or raw prompts.
4. Integrate production run state, autonomy jobs, workers and review/governance only through explicit canonical contracts; do not invent a second source of truth.
5. Complete one owner-reviewed 45–60 second end-to-end video. Technical tests alone are not creative acceptance.
6. Reconcile remaining WP1–WP6 canonical contract conflicts before claiming the central brain is the shared system of record.

## Actions not taken

No dependency installation, external provider call, service restart, production render, upload, publishing, deployment, commit, push, destructive cleanup or Dashboard source edit was performed in this increment.


## Central Brain v1 integration increment — 2026-11-15

**Implemented:** a deterministic unified read model that combines the existing run-manifest observer with a bounded observer for the local autonomy SQLite runtime.

- Added `app/brain/autonomy_observer.py`: SQLite `mode=ro` connection and `PRAGMA query_only=ON`; no database creation, schema migration, queue mutation, lease recovery or worker action.
- Added sanitized queue counts, expired lease count, recent failed task metadata and worker heartbeat freshness. Task payloads/results, hostnames, PIDs, database paths, secrets and raw errors are excluded.
- Added `GET /brain/operations` and expanded the overview/decision responses for Dashboard integration. Existing router-level API-key dependency remains the authentication boundary.
- Deterministic decision ordering now considers production-run failures first, then expired leases, stale worker heartbeats, failed local tasks and queued/running work. All outputs remain recommendation-only.
- PostgreSQL observation is explicitly fail-closed/unavailable until a non-mutating read-only adapter is qualified. The existing PostgreSQL TaskStore constructor initializes schema and is not called.
- Every local autonomy signal is labelled `non_canonical_operational_observation`. The Brain does not treat local SQLite/PostgreSQL runtime tables as the accepted P0 canonical shared control plane.
- The accepted P0 baseline and WP1–WP5 source documents were inspected. Detailed schemas/contracts remain candidate/open; Brain does not infer canonical entities or state transitions from them.

**Verification:** `py_compile` passed. Focused Brain + autonomy API suite: 21 passed. Full repository suite: 1,243 passed, 12 skipped, 71 subtests passed in 107.73s. Scoped `git diff --check` passed. No production run, provider call, deployment, upload, publishing, dependency installation, commit or push was performed.

**Remaining:** qualify a read-only PostgreSQL observer only after schema/contract closure; integrate canonical workflow/job/worker/artifact/governance entities only against their approved contracts. This increment is a local operational read model, not the P0 shared control plane.


## Provider runtime reliability increment — 2026-11-15

- Expanded health coverage from the original four providers to all ten automatic-chain adapters: OmniRoute, Gemini, Groq, Pollinations Text, NVIDIA NIM, Cloudflare Workers AI, OpenRouter, Mistral, Cerebras and Ollama.
- Added secret-free GET /providers/inventory (nextdecode.providers.inventory.v1) for Dashboard/backend consumers. It reports configuration readiness, last-known health freshness, latency, cooldown eligibility, resolved model and owner-configured routing priority. It performs no provider calls.
- Fixed is_configured() to use real provider configuration checks rather than an unconditional true result.
- Fixed Ollama health readiness to require explicit OLLAMA_BASE_URL and OLLAMA_MODEL; a default localhost URL is not proof that Ollama is installed/running.
- Provider health now defaults on for routing: only a recent failed explicit probe triggers the six-hour skip; missing/stale health is unknown and does not disable a provider.
- Provider chain order now de-duplicates entries and ignores unknown provider IDs while preserving the configured order and appending supported fallbacks.
- NVIDIA NIM now uses the already-present NVIDIA_API_KEY_2 as a secondary credential if the primary key fails; the configured model and endpoint remain unchanged.
- Health probe error persistence now stores exception class only, not raw messages that might contain request/credential details.
- Preserved AI_PROVIDER_CHAIN=nvidia,groq,openrouter,omniroute,ollama from the existing .env and all existing model settings. Gemini, Pollinations Text, Cloudflare, Mistral and Cerebras remain supported as later fallback entries when configured. OpenAI and Anthropic remain direct-only, outside the automatic free-first chain.
- No live API probes were executed. Existing health data is stale (24 Oct 2026); the new inventory correctly reports stale health as unknown until an explicit probe is run.

**Verification:** provider-focused suite: 62 passed. Full repository suite: 1,249 passed, 12 skipped, 71 subtests passed in 113.12s. No API keys were displayed, no live provider calls were made, and no model defaults, API endpoints, .env routing order or credentials were changed.


## Live model qualification — 15 Nov 2026

Owner authorized live qualification requests to configured provider APIs. Initial exact-model portfolio run completed: 10 candidates tested, 4 passed the structured JSON schema check, 6 failed. This is an initial connectivity/contract screen, not a final quality ranking.

Successful:
- Groq qwen/qwen3.8-27b — 1,531 ms
- Groq openai/gpt-oss-20b — 1,405 ms
- Groq openai/gpt-oss-120b — 2,492 ms
- Pollinations Text openai — 2,327 ms

Failed:
- Gemini gemini-3.5-flash — SDK RuntimeError, 592 ms
- Gemini gemini-flash-latest — SDK RuntimeError, 692 ms
- Gemini gemini-3.5-flash-lite — SDK RuntimeError, 694 ms
- NVIDIA google/gemma-4-31b-it — RuntimeError after 20,523 ms
- OpenRouter recursive/flint-v1.0:free — HTTP 429, 1,609 ms
- Cloudflare Llama 3.3 70B — returned JSON but failed required output schema, 7,341 ms

OpenRouter account quota endpoint succeeded and returned 54 free-model requests used against a displayed limit of 50, remaining 0. Runtime now marks that route quota-saturated and avoids additional free-model calls.

A follow-up Groq exact-model probe succeeded in 828 ms and verified raw response header capture:
- Model qwen/qwen3.8-27b
- Remaining tokens: 7,636 / 8,000
- Remaining requests: 999 / 1,000
- Actual response usage: 120 input + 188 output = 308 total tokens

Added persistent per-model usage and provider quota telemetry. Quota threshold switching is model-specific when provider headers expose the relevant remaining/limit pair. At >=90% consumption, the saturated model is skipped and the next configured model/provider is attempted. Unknown quota remains unknown; no synthetic limits are assigned.

The Dashboard read endpoint now returns the 10-candidate portfolio, use-case tags, exact model qualification results, observed per-model usage, quota counters and 90% threshold state. Dashboard source remains owned by the separate frontend workstream.

**Next qualification gates:** diagnose Gemini/NVIDIA failures, repair Cloudflare schema behavior if the returned model is otherwise useful, and test Mistral/Cerebras once usable credentials are present. Then perform repeated content-quality comparisons before owner approval of the final 10-model production roster.


**Final verification after portfolio/quota changes:** 1,252 passed, 12 skipped, 71 subtests passed in 104.19s. Provider-focused suite: 65 passed. Python compilation passed. JSON artifacts for portfolio, qualification, usage and quota are valid. Scoped provider/API diff check passed. A repository-wide diff check found an unrelated trailing blank line in another workstream's tests/test_visual_chain.py; it was left untouched to preserve parallel-agent changes.


## NVIDIA NIM requalification — 15 Nov 2026

Both configured NVIDIA API credentials independently authenticated against `GET /v1/models` (HTTP 200); the account catalog returned 83 model IDs. The previously configured `google/gemma-4-31b-it` is present in that list but timed out on both keys during chat-completion tests. The earlier suggested IDs `deepseek-ai/deepseek-v4-flash`, `nvidia/llama-3.3-nemotron-super-49b-v1.5`, `nvidia/nvidia-nemotron-nano-9b-v2`, `qwen/qwen3-next-80b-a3b-instruct`, and `openai/gpt-oss-120b` returned explicit HTTP 410 model-end-of-life responses. `nvidia/nemotron-3-super-120b-a12b` and `moonshotai/kimi-k2.6` returned 404 not found for this account.

Current live-catalog candidates tested:
- `nvidia/nemotron-3.5-bolt-e4b`: structured-output smoke test passed in 2.1s (47 words). Evidence summarization passed in 1.9s. A production-style script prompt returned 79 words without JSON mode (format invalid); with JSON mode it returned 79 words (valid JSON but under NEXTDECODE's 92–118 word target). A stricter qualification probe returned 124 words, failing the word-count gate. Treat as fast extraction / evidence classification candidate, not yet approved as script writer.
- `nvidia/nemotron-3.5-lightning-30b-a3b`: structured-output smoke response used 300 reasoning tokens and failed the requested JSON schema; a subsequent stricter NEXTDECODE script qualification returned 104 words and passed the exact schema, but took 38.5s. Treat as slow quality candidate pending repeated content scoring.
- `nvidia/nemotron-3.5-super-vl-120b-a12b` not tested yet; multimodal candidate only if image/video understanding becomes a priority.
- `deepseek-ai/deepseek-v4.1-flash`, `z-ai/glm-5.3-flash`, and `openai/gpt-oss-20b` each timed out at 30s in this round. `mistralai/mistral-large-4-1t-a52b` returned in 10.3s but spent 299 reasoning tokens and failed the short-form output schema. No production selection from these results.

The secondary NVIDIA key also completed a Nemotron Bolt chat completion (HTTP 200, 40 total tokens). Neither NVIDIA response exposed usable rate-limit headers; provider quota therefore remains unknown. We must not invent a quota/remaining-token figure. API catalog metadata exposed only model ID/owner for the tested model, not a context-window or output-limit value.

### Qualification contract correction
The earlier model qualification prompt used a 40–60 word response and accepted 20–120 words. That did not match the actual NEXTDECODE 45–60 second Shorts script contract. Updated the common qualification prompt/schema to require 92–118 words, exact hook/first-sentence match, <=60-character title, and non-empty string tags. A model can no longer pass merely by returning short valid JSON. This is a qualification-only acceptance gate; it does not change production script generation or provider priority.

The portfolio now contains 11 candidates against a target of 10 selected production models. NVIDIA has two provisional candidates: Nemotron Bolt (fast) and Nemotron Lightning (quality/slow). Neither is approved as a default production model yet. Full quality scoring and repeated trials remain necessary.


**NVIDIA follow-up verification:** both keys authenticated; secondary-key chat completion passed. Nemotron Bolt passed quick schema/evidence checks but did not consistently obey 92–118 word script length. Nemotron Lightning passed a 104-word script qualification in 38.5s. NVIDIA quota headers were absent, so capacity remains unknown. Qualification prompt/schema was corrected to the real NEXTDECODE short duration requirement. Provider-focused suite: 48 passed. Full repository suite: 1,253 passed, 12 skipped, 71 subtests passed in 96.53s. Scoped diff check and all six portfolio/telemetry JSON files passed validation.
