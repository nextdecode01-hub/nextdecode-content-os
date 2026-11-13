# Live Provider Availability and Upstream Repository Re-evaluation
**Document ID:** NDX-INT-RESEARCH-2026-11-04-02  
**Version:** 0.1  
**Research date:** 2026-11-04  
**Status:** Evidence-backed desk research; account dashboard checks pending  
**Scope:** NEXTDECODE Content OS and existing Shorts Studio  
**Authority:** Research only. No adoption, installation, account changes or code changes authorized.

## 1. Why this update exists

A provider being documented as free or available does not mean a new account can obtain an API key, the user's account is entitled to a model, quota increases are open, or a dashboard shows usable credits. Provider availability changes faster than static handbooks.

The programme therefore adopts a **live provider verification gate**. Before any integration is recommended for use, distinguish:
- public documentation and published default limits;
- current key issuance / waitlist / approval status;
- the user's actual account entitlement and billing state;
- dashboard quota, remaining credits, spend cap and reset window;
- response-header/runtime limit telemetry;
- endpoint/model availability and deprecation status;
- commercial-use, attribution, retention and content-use terms.

This report corrects stale assumptions and screens current repositories for reusable engineering ideas. It does not modify Shorts Studio.

## 2. Pexels — confirmed issuance pause

**Finding:** Pexels' official API-key help article was updated 2026-11-03 and states that new API-key issuance is currently paused. Its API landing page also states that new keys cannot currently be requested. The separate unlimited-request approval process was reported paused in an article updated 2026-11-02.

**Important distinction:** This is a new-key issuance and rate-limit-increase pause. It is not evidence that all previously issued keys have been disabled. Existing credentials must be checked separately.

Published default API limits remain documented as 200 requests/hour and 20,000/month. Successful API responses expose X-Ratelimit-Limit, X-Ratelimit-Remaining and X-Ratelimit-Reset. These headers are returned for successful 2xx responses, not for 429 responses. The API docs also specify attribution guidance and a newer video endpoint path under /v1/videos/.

**NEXTDECODE disposition:** Do not depend on Pexels for any new deployment or new environment until key issuance resumes or an existing authorized key is confirmed. Existing project references must be classified as code references, configured credentials, working access or verified runtime use — never conflate them.

**Correction required:** Previous handbook statements suggesting a new user can request a Pexels key immediately are stale and must be superseded.

Official sources:
- https://help.pexels.com/hc/en-us/articles/900004904026-How-do-I-get-an-API-key
- https://help.pexels.com/hc/en-us/articles/900005852323-How-do-I-get-unlimited-requests
- https://www.pexels.com/api/
- https://www.pexels.com/api/documentation/

## 3. Alternative media-source position

### Pixabay
Official API docs currently publish a default limit of 100 requests per 60 seconds, response headers for remaining/reset quota, a 24-hour cache requirement and a prohibition on systematic mass downloads. Search result URLs are temporary for some renditions; permanent hotlinking is not allowed, and intended assets should be downloaded to the user's own storage under the applicable licence.

**Disposition:** keep as a candidate, not an automatic Pexels replacement. Verify account key availability, approval level for full-resolution assets, response headers, current terms and intended use. https://pixabay.com/api/docs/

### Wikimedia Commons
Keep as a useful source for archival and public-domain/CC media, but file-level licence, creator, attribution and non-copyright rights remain mandatory. Do not treat Commons as a single blanket licence.

### Additional principle
No single stock source should be a critical dependency. The pipeline should support provider-neutral asset discovery, manual import with provenance, and generated/local assets. If no authorized source is available, the pipeline must return an explicit shortage/blocked state rather than silently substituting a questionable source.

## 4. Repository research — current shortlist

The following repositories were inspected through their current public GitHub repository metadata and README/docs. Popularity is a discovery signal, not proof of quality or suitability. The candidate selection is based on useful engineering patterns, license, fit with the existing Python/FFmpeg pipeline, operational cost and migration risk.

| Repository | Observed facts | Useful pattern for NEXTDECODE | Risks / disposition |
|---|---|---|---|
| calesthio/OpenMontage | Public repo; 75.9k stars and 10k forks observed on GitHub page; 501 commits; AGPL-3.0; 12 pipelines and 100+ tools claimed by project | Pipeline manifests, typed tool registry, skills as operational playbooks, checkpoint/reviewer protocol, reference-video analysis, provider-specific adapters, resumable async jobs, explicit cost unknowns | **HIGH-PRIORITY READ-ONLY STUDY.** Do not copy code or adopt whole system. AGPL-3.0 obligations need legal review before reuse/distribution. Project claims require independent benchmark. |
| heygen-com/hyperframes | Apache-2.0; Node 22+; HTML/CSS/seekable animation rendered through headless Chrome + FFmpeg; deterministic frame rendering; CLI, catalog and agent skills | High-quality kinetic typography, charts, transitions, overlays and reproducible motion graphics; agent-friendly skill contract; deterministic frame-level regression | **EVALUATE AS A TARGETED RENDERER OPTION.** Keep current FFmpeg pipeline; benchmark one motion-graphic scene only. No wholesale migration. |
| harry0703/MoneyPrinterTurbo | All-in-one short-video generator: topic to script, footage matching, subtitles, music and HD render; Python 3.11+ stated in README | Compare end-to-end orchestration, footage matching and subtitle UX; mine test scenarios and edge cases | **REFERENCE ONLY.** Its all-in-one defaults and provider assumptions do not match NEXTDECODE's evidence, approval and rights gates. Inspect licence/dependencies before any code reuse. |
| Comfy-Org/ComfyUI | Node-graph image/video/audio/3D generation engine; local, API and cloud modes; repository LICENSE is GPL-3.0 | Reusable visual-generation workflows, local model experiments and API-based generation stage | **EVALUATE ONLY IF GPU/HARDWARE FITS.** GPL-3.0 and separate model/custom-node licences require review. Not a replacement for deterministic editor/render pipeline. |
| remotion-dev/remotion | React/TypeScript programmatic video; source-available Remotion licence; individual and companies up to 3 employees can use free licence, larger for-profit entities require company licence per current licence text | Compare programmatic compositions, animated data and caption systems | **REFERENCE / ALTERNATIVE.** Check licence eligibility before commercial adoption. HyperFrames currently offers a more permissive Apache-2.0 code licence. |
| langchain-ai/deepagents | MIT; long-horizon agent harness built on LangGraph, with subagents, filesystem backends, context management, human-in-loop, skills and MCP tools | Agent harness patterns, tool scoping, context management, human checkpoints | **SELECTIVE DESIGN REFERENCE.** Avoid adding a second orchestration runtime until a measured gap exists; existing P0 contracts and bounded agents remain authoritative. |
| langchain-ai/open_deep_research | GitHub repository currently marked archived; README documents multi-provider research agent and citation-oriented research workflow | Research planning, search/reader/evidence/report evaluation ideas | **DO NOT ADOPT AS A DEPENDENCY.** Archived status makes it unsuitable as a live base. Use as historical design reference only. |
| microsoft/markitdown | MIT; converts PDF, Office, HTML, image/audio metadata and other files to Markdown; warns that conversion runs with caller's OS privileges | Controlled ingestion of source documents into research workflow | **LOW-COST EVALUATION CANDIDATE.** Use narrow conversion entry points and isolate untrusted files; not a general source crawler. |

## 5. High-value patterns to bring into the existing architecture

### From OpenMontage — adapt concepts, not its codebase
1. Capability registry: every tool/provider declares capability, input/output schema, auth requirement, cost mode, availability and required review.
2. Pipeline manifests: define stage order, dependencies, required artifacts and quality gates declaratively; map to the existing Shorts Studio pipeline rather than replace it.
3. Strict provider selection: explicit provider/model/host constraints must not silently fall back to a different provider.
4. Resumable async jobs: on polling timeout, resume the same job ID; do not submit a second paid generation request.
5. Unknown cost is not zero: report unknown/unpriced usage explicitly, not as a free call.
6. Reference-video analysis: separate reference-video analysis from generic web research; analyze transcript, scene boundaries, pacing, shot types and visual grammar, then create a differentiated concept.
7. Reviewer checkpoints: preserve human review at story, storyboard, asset-rights, final quality and publish approval stages.
8. Tool/skill separation: executable capability, operational instruction and deep technical reference are separate layers.
9. Provider contract refresh: track provider model IDs, host, schema and capability changes; do not assume an API key proves account entitlement.

These patterns align with NEXTDECODE's existing human approval, provider-neutral adapter and fail-closed principles. Any mapping must still be reconciled against P0 contracts.

### From HyperFrames — targeted motion-graphics benchmark
Use it to test one 45–60 second short containing animated opening title, section transitions, kinetic captions, animated charts/timelines/maps and reusable brand overlays.

Benchmark the exact same scene against current app/render and app/visuals output for visual quality, render time, determinism, output size, font handling and maintenance burden. Keep FFmpeg as final media assembly unless evidence supports a different boundary.

### From ComfyUI — local generation experiments
Consider only as an optional local generation service behind an adapter. Benchmark one image/video use case on actual hardware. Record VRAM/RAM, generation latency, model licence, node dependencies, reproducibility and quality. Open weights do not automatically mean unrestricted commercial rights.

### From DeepAgents — bounded agent design
Borrow context offloading, scoped filesystem tools, explicit human approval and subagent isolation as design patterns. Do not introduce the runtime into P0 until an accepted use case demonstrates a measurable gap that existing orchestration cannot safely cover.

## 6. Provider dashboard and entitlement verification standard

Public docs are insufficient to mark a provider READY. For each provider and account, verify the following in its authenticated dashboard or via an authorized account-level API:

| Check | Required evidence |
|---|---|
| Key issuance | New key request available, paused, waitlisted or approval-only |
| Existing key | Key exists, last used, status and environment ownership; never expose key value |
| Account tier | Free/trial/paid/enterprise and applicable region |
| Credits/billing | Remaining credits, expiry, auto-recharge and payment status |
| Usage limits | Requests/minute, requests/day/month, tokens/minute/day, concurrent jobs |
| Spend guardrails | Project/org hard cap, soft alert and per-run budget |
| Model access | Exact model IDs/endpoints entitled for this account |
| Quota reset | Reset timestamp/time zone and response headers |
| Operational status | Incidents, degraded regions, model retirement/deprecation |
| Terms | Commercial-use scope, retention, training/data use, attribution and output rights |

For APIs, capture response headers and error codes in non-secret telemetry. Treat 401/403 as auth/entitlement issues, 429 as throttling, 5xx as provider/service failure, and insufficient-quota/billing errors as spend or credit blockers. Do not retry blindly; use bounded backoff and idempotency for paid asynchronous jobs.

### Dashboard access limitation for this run

The connected browser did not expose the user's authenticated browser session, so I could not inspect Pexels, Pixabay or other provider account dashboards. This report therefore confirms public provider policy only. It does **not** claim to know the user's Pexels key status, remaining quota, account approval, Pixabay key, or billing state. To complete account-level verification, the provider dashboard pages or screenshots must be made available in the connected browser session or shared for review. Never send API secrets in chat.

### Current account-level status

| Provider | Public availability | User dashboard/account status |
|---|---|---|
| Pexels | New key issuance paused; limit increase paused | NOT VERIFIED |
| Pixabay | Public API docs; default 100 requests/60 sec; key required; cache 24h; no mass download | NOT VERIFIED |
| Exa | Public pricing/docs available | NOT VERIFIED |
| OpenAI API | Dashboard usage/spend limits documented | NOT VERIFIED |
| Gemini/Groq/Anthropic | Account/model quotas depend on tier/project | NOT VERIFIED |
| Replicate | Public rate limits and credit-sensitive throttling documented | NOT VERIFIED |

## 7. Recommendation and staged evaluation order

1. **Immediate: correct Pexels assumptions.** Mark new-key issuance and quota increase as paused. Do not create a dependency on a new Pexels key.
2. **Immediate: preserve Pixabay as conditional alternative.** Verify a real account key and full-access entitlement; enforce cache and rate-limit rules; download selected assets to controlled storage and preserve provenance.
3. **High priority: study OpenMontage architecture read-only.** Extract capability-registry, pipeline-manifest, checkpoint, resumable-job, cost-unknown and reference-video analysis patterns. Do not copy its code or replace Shorts Studio.
4. **High priority: benchmark HyperFrames.** One isolated branded motion-graphics scene against current render path; compare quality and deterministic output before any adoption proposal.
5. **Medium priority: evaluate MarkItDown.** Synthetic document-ingestion test, narrow converter entry points and untrusted-file isolation.
6. **Conditional: ComfyUI.** Only if actual GPU/hardware and model licensing make local generation viable.
7. **Do not adopt Open Deep Research as a dependency.** Repository is archived; use only for historical study.
8. **Do not replace P0 orchestration with DeepAgents.** Evaluate design patterns, not another runtime by default.
9. **Do not adopt MoneyPrinterTurbo wholesale.** Use it as a workflow comparison reference; its end-to-end defaults are not evidence/rights/approval equivalent.

### Proposed benchmark acceptance
- Same script, same visual brief, same source media and same output format for the baseline and candidate.
- Human blind review for visual quality, pacing, readability, brand consistency and editability.
- Deterministic render comparison and frame-level regression.
- Record wall-clock time, CPU/GPU/RAM/VRAM, storage, failure/retry behavior and per-output cost.
- Rights/provenance completeness must not regress.
- Human approval and private-by-default publishing controls must remain intact.
- No adoption based on GitHub stars alone.

## 8. Research and account verification cadence

- Before every first use of a provider: check official docs, dashboard entitlement, terms, limits and model availability.
- Before a production release: re-check all providers in the release manifest and run a low-cost health/quota probe only with approval.
- Monthly: review price/limit/model changes, deprecations, incidents, SDK versions and repo maintenance.
- Quarterly: rescore repository candidates, licences, dependency risk, security advisories and community adoption.
- Event-driven: recheck immediately after 401/403/429/402, provider policy notice, model retirement, key issuance change or billing alert.
- Every evidence record must have checked_at date, source URL, evidence class (official docs/dashboard/runtime/repo), confidence and next review date.

## 9. Official and repository source register

- Pexels API key issuance: https://help.pexels.com/hc/en-us/articles/900004904026-How-do-I-get-an-API-key
- Pexels rate increase: https://help.pexels.com/hc/en-us/articles/900005852323-How-do-I-get-unlimited-requests
- Pexels API docs and headers: https://www.pexels.com/api/documentation/
- Pixabay API limits/cache: https://pixabay.com/api/docs/
- OpenMontage: https://github.com/calesthio/OpenMontage
- OpenMontage provider guide: https://github.com/calesthio/OpenMontage/blob/main/docs/PROVIDERS.md
- HyperFrames: https://github.com/heygen-com/hyperframes
- MoneyPrinterTurbo: https://github.com/harry0703/MoneyPrinterTurbo
- ComfyUI: https://github.com/Comfy-Org/ComfyUI
- Remotion: https://github.com/remotion-dev/remotion
- Remotion licence: https://github.com/remotion-dev/remotion/blob/main/LICENSE.md
- DeepAgents: https://github.com/langchain-ai/deepagents
- Archived Open Deep Research: https://github.com/langchain-ai/open_deep_research
- MarkItDown: https://github.com/microsoft/markitdown
- OpenAI usage/spend limits: https://help.openai.com/en/articles/6614457-troubleshooting-api-usage-and-spend-limits
- Replicate rate limits: https://replicate.com/docs/topics/predictions/rate-limits

## 10. Scope and completion status

| Work area | Status |
|---|---|
| Pexels public key issuance / limit status | VERIFIED from official current help pages |
| Pexels account dashboard / existing key | NOT VERIFIED — browser session unavailable |
| Pixabay public API limits and cache rule | VERIFIED from official docs |
| Pixabay user account status | NOT VERIFIED |
| Repository shortlist and README inspection | COMPLETED — first pass |
| Repository code/security/dependency audit | NOT STARTED |
| License review | PARTIAL — HyperFrames Apache-2.0, OpenMontage AGPL-3.0, ComfyUI GPL-3.0, DeepAgents MIT, Remotion source-available terms checked; remaining candidate licensing needs review |
| Existing Shorts Studio code comparison | NOT RE-INSPECTED in this run; uses prior read-only baseline |
| Benchmark execution | NOT STARTED |
| Installation/adoption | NOT AUTHORIZED |
| Tests | NOT RUN |
| Production verification | NOT PERFORMED |

**Final status:** Current provider-policy correction and repository shortlist documented. Account dashboard checks, detailed code audit and benchmarks remain open. No project code, credentials, dependencies, provider settings, Git state, publishing or deployment were changed.
