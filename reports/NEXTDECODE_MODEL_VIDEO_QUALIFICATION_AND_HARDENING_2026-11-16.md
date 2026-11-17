# NEXTDECODE Model, Provider and Production Hardening
Date: 2026-11-16

## Owner decision
The owner approved the ten-model candidate roster for continued qualification. This approval does not certify every candidate as production-qualified and does not authorize paid API calls or video generation. The two existing reserve candidates remain reserves. Automatic role promotion remains disabled.

## Current routing disposition
The active task router is deliberately constrained to four repeatedly tested models:
- Groq openai/gpt-oss-120b: script drafting, script review, visual planning, general fallback, secondary research synthesis.
- Groq qwen/qwen3.8-27b: research synthesis, drafting fallback, review fallback, visual planning fallback, metadata fallback.
- Groq openai/gpt-oss-20b: fast classification, metadata transformation, secondary evidence extraction.
- NVIDIA nvidia/nemotron-3.5-bolt-e4b: evidence extraction only, using exact-model repeated evidence benchmark qualification.

Nemotron Super VL visual_qa routing is disabled until actual NEXTDECODE contact sheets and sampled video frames pass qualification. Gemini, Cloudflare and OpenRouter are not active automatic routes while their saved provider checks show runtime errors, schema mismatch or exhausted free-model quota. Pollinations remains a candidate but lacks repeatable production-task qualification. Nemotron Lightning remains a reserve because of high latency and failed visual-plan structure trials.

## Candidate portfolio
The owner-approved candidate pool remains ten routed candidates from the portfolio plus two reserve candidates. Candidate approval and production qualification are separate statuses. No candidate is automatically promoted.

The ten candidates are:
1. Groq Qwen 3.8 27B
2. Groq GPT-OSS 20B
3. Groq GPT-OSS 120B
4. Gemini 3.5 Flash
5. Gemini Flash Latest
6. Gemini 3.5 Flash Lite
7. NVIDIA Nemotron Bolt E4B
8. OpenRouter Recursive Flint Free
9. Cloudflare Llama 3.3 70B
10. Pollinations Text OpenAI

Reserves:
- NVIDIA Nemotron Lightning 30B A3B
- NVIDIA Nemotron Super VL 120B A12B is a visual-QA specialist candidate, not yet qualified for automated production use.

## Existing benchmark evidence
The saved repeated benchmark has 45 calls: five exact models, three task types and three repetitions. API usage attribution in that benchmark is unknown, so no repeat API benchmark was initiated in this pass.

| Exact model | Script | Evidence | Visual plan | Decision |
|---|---:|---:|---:|---|
| Groq GPT-OSS 120B | 3/3 | 3/3 | 3/3 | Preferred tested general production model |
| Groq Qwen 3.8 27B | 2/3 | 3/3 | 3/3 | Qualified fallback; script word-count reliability needs work |
| Groq GPT-OSS 20B | 1/3 | 3/3 | 3/3 | Extraction/classification only; script route excluded |
| NVIDIA Nemotron Bolt E4B | 0/3 | 3/3 | 0/3 | Evidence extraction only |
| NVIDIA Nemotron Lightning 30B A3B | 3/3 | 3/3 | 0/3 | Reserve; slow and not visual-plan qualified |

The structured checks do not establish factual accuracy or editorial quality. Offline review of saved samples found GPT-OSS 120B strongest overall, but it still adds broad claims not present in the narrow evidence prompt. Qwen's sample says ?significantly reduce? compute relative to dense models, which overstates the supplied evidence. Lightning's sample adds auxiliary losses and token dropping, which were not in the supplied evidence. Existing evidence and script gates must continue to reject unsupported expansions.

Saved exact-model qualification records (2026-11-15) show:
- Groq Qwen, GPT-OSS 20B and GPT-OSS 120B: technical schema checks passed.
- NVIDIA Bolt and Lightning: technical schema checks passed.
- Gemini Flash, Gemini Flash Latest and Flash Lite: runtime errors.
- OpenRouter Recursive Flint Free: HTTP 429.
- Cloudflare Llama 3.3: schema mismatch.
- Pollinations Text: one technical schema pass, no repeated editorial qualification.
- Super VL: one basic image-understanding test passed; non-streaming image test exhausted output budget; no project contact-sheet qualification.

## Provider and budget status
No new model API requests, provider authentication requests or video-generation requests were made during this pass. Existing API usage and quota snapshots are historical and are not treated as current quota proof. Current local quota inspection returns unknown for GPT-OSS 120B, GPT-OSS 20B and Nemotron Bolt, and low for Qwen. The router therefore blocks automatic model calls until a fresh provider-reported quota snapshot exists. Unknown quota is not represented as available quota.

Video generation remains disabled by the zero-budget policy. Kling has a configured credential but no live generation was attempted. Runway and Google Veo remain unconfigured/unverified. The workflow now calls the authorization guard before provider construction and records the approval route and budget metadata in the generated-asset sidecar.

## Production failure root cause and correction
The three latest production runs failed before script drafting with:
No supported research claims are available for script writing.

The research-to-script bundle applied a Mixtral/Mistral/Hugging Face/arXiv publisher allowlist to every topic, including unrelated AI-research topics. This caused valid claims from other fetched publishers to be discarded. The allowlist is now topic-specific. For non-MoE topics, supported claims can be used from fetched sources; single-source claims are admitted only as explicitly qualified claims when the verbatim quote is located in the fetched source. Unverified, unfetched and non-verbatim claims remain excluded. Failure diagnostics now report safe source/claim counts and verification-status counts.

## Renderer integration
The existing generated-asset path is preserved:
source shot -> motion director -> shot annotation -> provenance-validating visual resolver -> EDL -> FFmpeg assembly -> delivery QA.
A synthetic local fixture proved an 8-shot, 10-second 360x640/30fps H.264 + AAC output with EDL delivery QA passing. This is integration proof only, not a production Short or live provider generation.

## Reliability safeguards added
- Provider-wide health failures can be overridden only by a recent exact-model benchmark for the same task type, with at least three trials, at least 80% pass rate and mean score at least 80.
- Quota checks remain absolute and cannot be overridden by model qualification.
- Provider quota is usable only when provider-reported counters are fresh (two-hour window); stale, missing or malformed quota is unknown and blocks automatic model calls.
- Visual QA task routing is explicitly disabled until project-frame qualification exists.
- Video generation is denied before provider construction unless the selected route is explicitly authorized.
- Invalid generated clips continue through the normal visual fallback path.
- Non-MoE research claims are no longer filtered by the MoE-only publisher allowlist.

## Verification
- Focused model/router/provider/research regression after final quota and routing changes: 117 passed.
- Final full repository suite after all hardening changes: 1,300 passed, 12 skipped, 71 subtests passed in 171.46 seconds, exit code 0.
- Earlier focused renderer/provider regression: 193 passed, 1 skipped, 11 subtests passed.
- Earlier full repository baseline before this hardening pass: 1,289 passed, 12 skipped, 71 subtests passed.
- git diff --check: passed.
- Python compilation of modified modules: passed.
- No commit, push, deployment, upload or publication.

## Remaining production acceptance blockers
1. Current provider quota/authentication is not freshly verified; no new provider requests were sent because usage cost/allowance could not be proven.
2. Nemotron Super VL has not been evaluated on project contact sheets and sampled production frames; automated visual QA remains disabled.
3. The approved candidate roster is not equivalent to ten fully quality-qualified production models.
4. No new 45?60 second production Short was rendered and accepted in this pass. The latest recorded production attempts stopped at the research evidence gate; this gate has now been corrected and covered by tests, but a new live research/model run is still required.
5. Human storyboard, final audiovisual review and publishing approval remain mandatory.

The system is safer and the known repeatable routing/evidence defects are corrected, but production readiness must not be declared until the remaining acceptance blockers are closed.

