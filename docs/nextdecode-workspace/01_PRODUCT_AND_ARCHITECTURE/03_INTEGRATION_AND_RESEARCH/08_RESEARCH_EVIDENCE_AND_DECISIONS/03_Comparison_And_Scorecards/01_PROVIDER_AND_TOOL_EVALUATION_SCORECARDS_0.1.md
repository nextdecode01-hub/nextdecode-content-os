# Provider and Tool Evaluation Scorecards — Initial Decision Screen

**Document ID:** INT-EVAL-001 | **Version:** 0.1 draft | **Date:** 2026-11-04  
**Status:** Preliminary desk evaluation; not procurement, adoption or activation approval  
**Scope:** NEXTDECODE Content OS and its bounded integration with existing Shorts Studio  
**Budget principle:** Free-first, local-first, target spend ₹0 unless separately approved.

## 1. How to read this scorecard

This is a decision screen, not a benchmark. Scores are qualitative and based on source code inspected, project documentation and official public documentation reviewed on 2026-11-04. No live provider tests, account entitlement checks, load tests or commercial/legal review were performed.

**Rating scale:** 1 = poor fit; 2 = weak; 3 = conditional/neutral; 4 = strong; 5 = very strong.  
**Confidence:** H = direct source/API evidence; M = official public docs but no account/runtime verification; L = project documentation or incomplete evidence.

### Weighted criteria

| Criterion | Weight | What earns a high score |
|---|---:|---|
| Free-first / cost controllability | 15% | Useful no-cost path, predictable metering, hard budget controls |
| Local-first / operational independence | 10% | Can run locally or be replaced without vendor lock-in |
| Integration fit / developer ergonomics | 15% | Stable documented API, SDK, mature integration path |
| Reliability / recoverability | 15% | Clear limits, retry semantics, async status, idempotency or reconciliation |
| Security / privacy / data controls | 15% | Clear data handling, scoped auth, retention controls, low sensitive-data exposure |
| Licensing / commercial suitability | 10% | Clear terms for intended use and outputs |
| Maintainability / portability | 10% | Versioned API, ecosystem health, standards, exit path |
| Content quality / capability | 10% | Meets editorial and production quality needs |
| **Total** | **100%** | |

**Hard gates override scores:** unresolved rights, unacceptable data terms, no credential boundary, no budget cap, unsafe retry/unknown-outcome behavior or conflict with P0 authority = do not adopt, regardless of numerical score.

## 2. Initial provider/tool scorecards

| Candidate | Cost | Local | Fit | Reliability | Security | License | Maintain | Quality | Weighted indicative score | Confidence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Gemini Developer API | 4 | 1 | 4 | 3 | 2 | 3 | 4 | 4 | 3.20/5 | M |
| Groq API | 4 | 1 | 4 | 3 | 3 | 3 | 4 | 4 | 3.30/5 | M |
| OpenAI API | 2 | 1 | 5 | 4 | 4 | 4 | 5 | 5 | 3.75/5 | M |
| OmniRoute | 3 | 1 | 3 | 2 | 2 | 2 | 2 | 3 | 2.30/5 | L |
| Ollama (local) | 5 | 5 | 3 | 2 | 4 | 3 | 3 | 2–4 | 3.50/5 | L |
| Edge TTS | 5 | 2 | 4 | 3 | 2 | 2 | 3 | 4 | 3.20/5 | M |
| Cartesia | 3 | 1 | 4 | 4 | 3 | 2 | 4 | 4 | 3.20/5 | M |
| ElevenLabs | 2 | 1 | 4 | 4 | 3 | 3 | 4 | 5 | 3.25/5 | M |
| Wikimedia Commons | 5 | 1 | 4 | 3 | 4 | 2–5 per asset | 4 | 3 | 3.55/5* | H |
| Pexels API | 5 | 1 | 4 | 3 | 3 | 2–3 | 4 | 3.40/5 | M |
| Cloudflare R2 | 4 | 1 | 4 | 4 | 4 | 4 | 4 | 4 | 3.70/5 | H |
| n8n Community | 4 | 3 | 4 | 3 | 3 | 2–4 by use case | 4 | 4 | 3.50/5 | M |
| GitHub MCP read-only | 4 | 1 | 4 | 3 | 4 if scoped | 4 | 4 | 4 | 3.55/5 | M |
| Filesystem MCP isolated | 5 | 5 | 4 | 3 | 4 if OS-isolated | 4 | 4 | 4 | 4.10/5 | M |

*Wikimedia Commons has no single blanket licence score: the licence must be evaluated per file. The wide range is intentional and a hard gate applies to each asset.

These scores are directional. Averages must not be interpreted as evidence that two providers are interchangeable. Quality, privacy and rights vary by model, plan, account, asset and use case.

## 3. Evidence notes and decision implications

### 3.1 LLM providers

**Gemini Developer API — conditional, not default for sensitive project data.**
- Official pricing documentation distinguishes Free and Paid tiers; its current page says Free-tier content may be used to improve Google products, while Paid-tier content is not.
- Free access and quotas are model-specific and can change. Do not send internal P0 docs, private project source, credentials or proprietary drafts through a free-tier endpoint without an approved data policy.
- Recommendation: retain as a low-cost experimentation candidate for non-sensitive, low-risk content only after payload classification; do not make it the universal Content OS model.

**Groq — promising inference candidate, account-specific limits required.**
- Official rate-limit documentation exposes RPM, RPD, TPM, TPD and audio-specific limits; actual limits vary by organization and model.
- Recommendation: benchmark latency, structured-output validity, context window and cost against a fixed task set. Treat 429/Retry-After and organization-level quotas as first-class controls.

**OpenAI API — capability candidate, not zero-cost default.**
- Official pricing is usage-based and model/tool dependent. Data controls must be reviewed for the exact API/service and account configuration.
- Recommendation: use only for tasks where measured quality advantage justifies cost; set explicit per-run and monthly budget caps before any use.

**OmniRoute — do not approve as a critical dependency yet.**
- Current project docs reference it, but source/runtime, provider terms, routing transparency, account ownership and exact model mapping were not independently verified in this pass.
- Recommendation: retain as an existing-project investigation item; require route-level provider attribution, privacy review, failure semantics and exit plan before it becomes a Content OS dependency.

**Ollama — useful local/private fallback candidate, not automatically a quality-equivalent fallback.**
- Local execution improves control over data egress but introduces hardware, model licensing, performance and maintenance trade-offs.
- Recommendation: benchmark a small set of tasks locally; only use for explicitly approved task classes where quality is sufficient. Never silently replace a cloud model with a lower-quality local model.

### 3.2 Speech providers

**Edge TTS — useful free-first path with a policy caveat.**
- The existing source includes an Edge TTS adapter. The service is not equivalent to a locally hosted offline model; service availability, terms and voice rights need review.
- Recommendation: keep as a development/non-sensitive candidate until terms and commercial use are confirmed; maintain a separately approved production voice path.

**Cartesia — promising quality candidate, but free tier is not a commercial-use assumption.**
- Its public pricing page lists a free plan and identifies commercial-use licensing under Pro.
- Recommendation: do not use free-tier generated voice in monetized NEXTDECODE publishing unless provider terms explicitly permit the intended use.

**ElevenLabs — quality candidate with spend and voice-rights gates.**
- Recommendation: evaluate quality against the approved NEXTDECODE voice benchmark; verify plan, commercial rights, voice cloning consent and data retention before selection.

### 3.3 Media and storage

**Wikimedia Commons — retain as a source adapter, never as blanket rights clearance.**
- Code already captures licence/author/page metadata. Each file needs an asset-level licence decision and attribution record.
- Recommendation: fail closed when licence evidence is missing, ambiguous or incompatible with the intended edit/use.

**Pexels — useful curated stock candidate with restrictions.**
- Recommendation: keep as an optional stock provider after reviewing API terms, attribution requirements, restrictions on redistribution and AI dataset/model use. Do not treat a downloadable file as unrestricted stock.

**Cloudflare R2 — strong object-storage candidate, but defer final selection until WP4.**
- Official pricing currently includes 10 GB-month Standard storage, 1M Class A operations and 10M Class B operations per month; egress is free. An R2 subscription/account is still required and overages are billable.
- R2 offers an S3-compatible API, but compatibility is not 100%; verify the specific API operations needed.
- Recommendation: shortlist for a binary-storage adapter only after ArtifactVersion, retention, access control, encryption, backup/restore and cost controls close under WP4.

### 3.4 Orchestration and developer tooling

**n8n Community — useful internal orchestration, not the canonical workflow database.**
- Its Sustainable Use License allows internal workflow creation/editing by the organization, but a product that lets outside customers create/configure automations or a hosted automation service can require a commercial license.
- Recommendation: keep n8n as an optional internal orchestration layer; Content OS remains authoritative for workflow/job/attempt state. Re-check license before any customer-facing automation builder or managed service.

**GitHub MCP — high-priority read-only evaluation.**
- Recommendation: read-only repository-scoped access, least-privilege token, narrow toolset; no issue/PR/write/merge actions in the initial evaluation.

**Filesystem MCP — defer until isolation exists.**
- Current inspected WSL host did not have Docker CLI/Compose. Do not run filesystem MCP with broad unisolated host access as a workaround.
- Recommendation: evaluate only after OS/container sandbox, read-only mount, path allowlist and audit logging are technically enforced.

## 4. Recommended shortlist (not adoption)

| Rank | Candidate | Proposed next action | Why |
|---:|---|---|---|
| 1 | Cloudflare R2 | WP4 architecture fit and cost/restore review | Low-cost object-storage option with S3 compatibility and no egress fees |
| 2 | GitHub MCP read-only | DEV-01 threat model and permission proof | High leverage for repo intelligence; manageable if read-only and scoped |
| 3 | Groq | Fixed benchmark against current Shorts Studio task set | Low-cost inference option; rate limits need account-level capture |
| 4 | Local Ollama | Hardware-aware quality/performance benchmark | Local data control and reduced external dependency |
| 5 | Wikimedia Commons | Rights-evidence and asset-provenance acceptance tests | Already present in source and supports per-asset metadata |
| 6 | Pexels | Terms and asset-quality review | Potential complementary stock-video source |
| 7 | Cartesia / ElevenLabs | Controlled voice quality and commercial-rights comparison | Compare actual voice output and plan eligibility, not marketing claims |
| 8 | n8n | Internal-only license and workflow-boundary review | Useful orchestration, but not canonical state authority |

## 5. Rejected/deferred for now

- **OmniRoute as a mandatory Content OS dependency:** defer until routing transparency, terms, privacy and failure behavior are evidenced.
- **Multiple orchestration frameworks at once:** do not adopt LangGraph, PydanticAI and other agent runtimes without a demonstrated capability gap.
- **Public publishing automation:** prohibited without separate explicit authorization and all P0 governance gates.
- **Customer-facing n8n workflow builder:** licensing implications require review before product design or implementation.
- **Unisolated filesystem MCP:** reject on current host posture.
- **Provider free-tier claims as production SLAs:** reject; limits and terms are mutable and account-specific.

## 6. Benchmark design before choosing model/voice provider

Use one versioned, representative dataset and identical prompts/settings:
- 20 short-form research synthesis tasks with source-grounded factual claims;
- 20 script generation tasks with fixed duration, brand voice and evidence constraints;
- 20 structured JSON extraction tasks with schema validation;
- 10 refusal/safety/rights-boundary cases;
- 10 long-context tasks.

Measure:
- schema pass rate, factual support/unsupported claim rate, human editorial preference;
- p50/p95 latency, retry rate, timeout and 429 rate;
- input/output token or character usage and estimated INR cost;
- output variance across repeat runs;
- data class permitted and provider terms;
- fallback equivalence and actual provider/model lineage.

No benchmark has been run. Test set creation and execution require separate authorization if they touch live providers or consume paid quotas. Offline mock/fixture tests may be prepared as documentation first.

## 7. Owner decisions required

- EVAL-OD-01: Which data classes may leave the local environment for free-tier model APIs?
- EVAL-OD-02: Is Edge TTS allowed for monetized/commercial NEXTDECODE content after terms review?
- EVAL-OD-03: Is Cartesia Pro or another paid TTS ever acceptable, and what spend ceiling?
- EVAL-OD-04: Confirm R2 as preferred WP4 candidate only after storage/restore design.
- EVAL-OD-05: Confirm GitHub MCP read-only evaluation scope and repository boundary.
- EVAL-OD-06: Define whether n8n remains strictly internal or is ever exposed to customers.
- EVAL-OD-07: Approve offline benchmark dataset design and later live benchmark scope.

## 8. Official evidence references

- Groq [rate limits](https://console.groq.com/docs/rate-limits): account/org and model-specific limits; 429 handling.
- Gemini [pricing and data use](https://ai.google.dev/gemini-api/docs/pricing): Free/Paid tier data-use difference and model-specific availability.
- Gemini [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits): usage tiers, RPM/TPM and spend-based limits.
- OpenAI [API pricing](https://developers.openai.com/api/docs/pricing): usage-based model/tool pricing; recheck current model and feature.
- YouTube [Data API overview](https://developers.google.com/youtube/data/getting-started) and [videos.insert](https://developers.google.com/youtube/v3/docs/videos/insert): default quota allocation, upload endpoint and OAuth scope; quota bucket details may change.
- Cloudflare [R2 pricing](https://developers.cloudflare.com/r2/pricing/), [getting started](https://developers.cloudflare.com/r2/get-started/) and [S3 compatibility](https://developers.cloudflare.com/r2/api/s3/api/).
- n8n [Sustainable Use License FAQ](https://support.n8n.io/article/can-i-use-your-license-for-my-use-case): internal use vs customer-facing workflow-building/service restrictions.
- Cartesia [pricing](https://www.cartesia.ai/pricing): free vs commercial-use plan distinctions.
- Pexels [API documentation](https://www.pexels.com/api/documentation/) and [terms help](https://help.pexels.com/hc/en-us/articles/900005880463-What-are-the-Terms-and-Conditions).
- Wikimedia [reuse guidance](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia): rights must be checked for each file.

## 9. Change log

- 0.1 — First-pass qualitative scorecards and shortlist. Scores are desk estimates with explicit confidence; no provider adoption or live benchmark.
