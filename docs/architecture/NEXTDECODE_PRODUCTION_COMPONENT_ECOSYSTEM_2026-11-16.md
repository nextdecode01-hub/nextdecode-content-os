# NEXTDECODE Production Component & Provider Expansion — 2026-11-16

## Owner decision
Approved additions are free-first and provisional. No paid generation is enabled. Keep human approval before publishing. Provider adapters are isolated from Parallel-owned visual-selection modules; selection-chain wiring must be completed by that owner against the contracts below.

## Implemented in this increment
- `app/providers/media_sources.py`: Coverr video search and Openverse image search adapters. They normalize source metadata and preserve attribution/license fields.
- `app/providers/zai.py`: direct Z.AI chat and image-inspection adapters.
- `app/providers/multi_model_ai.py`: Z.AI GLM-4.5-Flash added to the shared hosted text provider chain (only attempted when `Z_API_KEY` exists).
- `app/providers/model_health.py`: Z.AI included in configuration and structured-output health probes.
- `app/visuals/screen_components.py`: JSON-spec-driven editable SVG windows for browser, terminal, code editor, dashboard and app screens. Text is escaped; output is a normal SVG source file suitable for the current FFmpeg still-image path.
- `tests/test_production_components.py`: offline tests for SVG generation, escaping, provider missing-key behavior and license metadata.

## Provider facts / gates
| Provider | Purpose | Free access / constraints | Integration rule |
|---|---|---|---|
| Coverr | Stock video and music | API demo: 50 requests/hour; API usage requires attribution/logo per API docs; verify item license and commercial terms | Candidate source only; keep provenance and add Coverr attribution overlay/credits before publish |
| Openverse | Openly licensed photos and audio | Anonymous API access; rate limits apply; each result has its own license | Never infer rights from search engine; persist license, version, creator, landing URL and attribution; reject unclear/dead/mature assets |
| Z.AI GLM-4.5-Flash | Text/chat | Existing key authenticated in a prior probe; observed 429 overload on GLM-4.7-Flash, so avoid treating all GLM models as healthy | GLM-4.5-Flash is available as a fallback, not a default priority; schema/quality health gate remains authoritative |
| Z.AI GLM-4.6V-Flash | Vision QA | Existing key passed image understanding probe | Separate vision QA path; never conflate with text generation or image/video generation |
| NVIDIA Nemotron Super VL | Contact-sheet/frame QA | Existing key passed text + streamed image-understanding probe | Provisional visual-QA candidate; sampled frames/contact sheets only |
| Cloudflare Flux | Generated stills | Existing account ID + API token; free daily Neurons are shared across Workers AI | Keep current provider; do not assume unlimited free usage |
| Kling | Text/image-to-video | Existing credential, but generation spends credits | Not activated; owner approval and per-shot credit budget required |

## New screen/window component contract
The screen component renderer accepts a JSON object such as:

```json
{
  "kind": "browser",
  "title": "Inside an AI research workflow",
  "subtitle": "A visual walkthrough",
  "url": "https://example.test/research",
  "lines": ["Collect sources", "Compare model outputs", "Verify claims"]
}
```

Supported `kind`: `browser`, `terminal`, `code`, `dashboard`, `app`.

Call `render_screen_component(spec, output_path)` to create editable SVG. Change the JSON fields to edit visible content; no screenshot regeneration or external UI service is required. Current implementation is a static screen visual. Cursor movement, typing, scrolling, window resizing, transitions and live browser capture are future animation/interaction capabilities and should be implemented as timeline keyframes rather than hard-coded one-off effects.

## Recommended component ecosystem (research-backed)
1. **Structured screen/UI scenes (implement now):** local SVG/HTML templates driven by scene JSON. This is deterministic, editable, offline, and avoids API spend. Build reusable browser, terminal, code editor, dashboard, mobile device, map, chart and notification components.
2. **Playwright + Remotion (evaluate next):** Playwright can capture real browser/app workflows; Remotion composes React components into motion video. Use only when genuine UI interaction matters; it adds browser/runtime dependencies and must be separately qualified. The current SVG templates are the zero-dependency baseline.
3. **Openverse:** photo/audio search with per-item rights metadata. Strong candidate for stills and sound, subject to rights checks.
4. **Coverr:** extra stock video and music catalogue; keep within 50 calls/hour and cache results.
5. **Lucide / Tabler icons and self-authored SVG:** use local vector icons for concepts, labels and diagrams; verify each library's license and pin versions before bundling.
6. **Wikimedia Commons:** preserve current source for diagrams, historic imagery and technical illustrations; attribution and file-page metadata remain mandatory.
7. **YouTube Audio Library / Openverse audio:** source music and SFX with explicit rights/attribution metadata. Never treat generic “royalty-free” wording as a license record.

## Required integration contract for visual-selection owner
- Add Coverr as an additional stock-video candidate source after existing Pixabay/Pexels behavior; don't reorder existing providers without evidence.
- Add Openverse as still-image discovery alongside Wikimedia. Persist license code/version/URL, creator, attribution, source landing page, dimensions and download URL in asset metadata.
- Apply relevance scoring to title, description, tags, aspect ratio and usable duration; don't accept provider rank as relevance.
- Cache query responses and downloaded assets; obey provider quotas.
- Never download or publish assets whose rights fields are absent/ambiguous. For Coverr API results, preserve required provider attribution. For Openverse, use per-item license terms.
- Add a source-level provenance record and attribution output in the final run manifest.
- For generated UI scenes, use structured JSON specs and the SVG renderer; scene plan should declare screen type, content, visual state, animation actions and duration.

## Not enabled / deferred
- No paid Kling generation, fal/Replicate/Stability generation or external subscription.
- No automatic public publishing.
- No new package install.
- No Playwright/Remotion dependency added in this increment.
- No edits to `app/visuals/chain.py`, `stock_fetcher.py`, `app/render/assembly.py` or dashboard. Parallel-agent changes in those areas are preserved.
- Coverr/Openverse discovery adapters are implemented but still require owner-coordinated selection-chain wiring and a full end-to-end render before production qualification.

## Research references
- Coverr API overview and attribution: https://coverr.co/api/docs/
- Coverr demo quota: https://coverr.co/api/docs/start
- Coverr API product page: https://coverr.co/developers/
- Openverse API: https://api.openverse.org/v1/
- Openverse search algorithm: https://docs.openverse.org/api/reference/search_algorithm.html
- Openverse scope: https://openverse.org/about
- Playwright/Remotion example architecture: https://github.com/mauriciobc/videodoc

External service terms and quotas can change; re-check them before production use.


## Tooling expansion — second increment

### Added local vector production components
- `app/visuals/production_components.py`
- Components: `metric_cards`, `bar_chart`, `flow_diagram`, `icon_tile`.
- 1080×1920 editable SVG, escaped text, no external assets or new Python dependencies.
- These should be used for metrics, model comparisons, architecture flows, security concepts and simple visual metaphors.

### Playwright browser capture utility
- `tools/production/capture_browser_scene.mjs`
- Optional screenshot capture of authorized public/demo browser pages at 1080×1920.
- Playwright is not installed automatically. Script fails with clear setup instructions when unavailable.
- Privacy gate: never capture private account data, credentials, payment pages or personal data. Use sanitized staging/demo pages and preserve capture provenance.

### Remotion animated-scene starter
- `tools/production/remotion/package.json`
- `tools/production/remotion/src/index.jsx`
- `tools/production/remotion/src/scenes/NextDecodeDemo.jsx`
- A minimal 5-second 1080×1920 composition demonstrates title and staged step reveals.
- Dependencies are declared but not installed. This is intentionally a separate scene renderer, not a replacement for FFmpeg. Once approved/installed, export individual scene clips and feed them into the existing edit decision list.

### Why these tools fill gaps
| Gap | New tool | Role |
|---|---|---|
| Fake or generic software footage | Playwright | Capture genuine authorized product/browser UI |
| Static scenes lack movement | Remotion | Compose timed motion, transitions and text reveals |
| Repeated generic stock b-roll | Local vector components | Produce topic-specific charts, flow diagrams, metric cards and icon metaphors |
| Screen content hard to revise | Existing JSON-driven SVG screen components | Edit scene copy/layout without re-capturing |
| Stock/image coverage gaps | Coverr + Openverse adapters | Expand candidate discovery with rights provenance |

### Installation and integration gates
No new npm packages, browser binaries or Python packages were installed. Node.js is present (v24.14.1), npm is present (9.2.0). Playwright and Remotion require an approved dependency installation and runtime qualification before production use. The current FFmpeg renderer remains the final assembly authority.

The visual-selection integration boundary remains unchanged: the Parallel owner must wire Coverr/Openverse and component selection into the live shot chain. This increment supplies tested isolated components and a documented contract; it does not modify the protected visual chain, stock fetcher, assembly or dashboard.


## Scene component adapter — integration boundary

`app/visuals/scene_component_adapter.py` now exposes a single renderer entry point:
`render_scene_component(scene, output_path)`.

Accepted scene contract:
- `visual_source=screen_component` with kinds `browser|terminal|code|dashboard|app`
- `visual_source=vector_component` with kinds `metric_cards|bar_chart|flow_diagram|icon_tile`
- Output is a local SVG asset with a normalized asset record: type, media type, path, scene ID, component kind, editability, local-generation flag and external-API flag.
- Unknown sources/kinds fail closed.

This provides a concrete adapter contract for the visual-selection/asset-resolution owner without editing their protected modules. The remaining connection is to call this adapter from the live asset-resolution stage and ensure the existing renderer rasterizes SVG reliably before clip assembly. This live-chain wiring has not yet been completed.

## Model portfolio decision — 2026-11-16

**Status remains `qualification_in_progress`; no final production model roster has been approved.** The current portfolio contains 12 candidates against a target of 10. The measured benchmark covers 45 requests and validates schema/contract reliability, not editorial quality:
- Groq GPT-OSS 120B: script 3/3, evidence 3/3, visual plan 3/3 — strongest tested all-round candidate.
- Groq Qwen 3.8 27B: script 2/3, evidence 3/3, visual plan 3/3 — balanced candidate.
- Groq GPT-OSS 20B: script 1/3, evidence 3/3, visual plan 3/3 — fast extraction/classification candidate, not preferred script writer.
- NVIDIA Nemotron Bolt E4B: script 0/3, evidence 3/3, visual plan 0/3 — extraction/evidence classification only.
- NVIDIA Nemotron Lightning 30B A3B: script 3/3, evidence 3/3, visual plan 0/1; one script call took about 29.4 seconds — quality candidate, not yet reliable for visual planning.
- NVIDIA Nemotron Super VL 120B: image understanding works in streamed mode; candidate for contact-sheet/visual QA, not video generation.
- Cloudflare Llama 3.3 70B: tested response was too short for the required Shorts script word-count gate.
- Z.AI GLM-4.5-Flash: API text call verified; GLM-4.6V-Flash image call verified. Not yet included in the 45-request comparative benchmark.

The final roster needs editorial scoring on the same scripts, repeatability, output length, evidence faithfulness, latency, quota and fallback drills. The portfolio's owner-approval policy remains in force.

## Video-generation tools and API decision

No video-generation API has been selected as the always-on production provider. The default pipeline remains free-first and uses stock footage, local screen/vector components, generated stills where already available, and FFmpeg composition. Video-generation APIs are optional paid shot sources, not the main renderer.

Qualified candidates to evaluate in a separately approved paid pilot:
1. **Kling 4.0 / 4.0 Flash** — direct Kling API credentials are present in the local environment from the prior credential-presence audit, but no production client or live generation test has been qualified. Kling's current API docs describe native generation up to 30 seconds, text/image/video references and keyframe control. Resource packages are purchased; treat as paid. Official docs: https://kling.ai/document-api/guides/capability-map/video and https://kling.ai/document-api/quickStart/userManual
2. **Google Veo 3.1 / Veo 3.1 Fast** — official Gemini API supports text/image-to-video and Veo-specific extension/frame controls. Current published pricing lists Veo 3.1 with audio at $0.40/sec (720p/1080p), Veo 3.1 Fast with audio at $0.10/sec (720p) and $0.12/sec (1080p); no free tier is listed for video generation. Check the current price and account access before any call. Official docs: https://ai.google.dev/gemini-api/docs/video and https://ai.google.dev/gemini-api/docs/pricing
3. **Runway API** — a unified API surface with models from Kling, Google Veo, ByteDance Seedance, MiniMax/Hailuo, WAN and Runway. Useful if we want one API integration and provider routing. Billing is credit-based and paid; official model catalog and pricing: https://docs.dev.runwayml.com/guides/models/ and https://docs.dev.runwayml.com/guides/pricing/

Recommendation: keep video generation disabled by default. If the owner approves a small paid pilot, compare Kling 4.0 Flash (direct existing credential) against Veo 3.1 Fast and one Runway-routed alternative using the same 5-second and 8-second prompts, reference images, 9:16 framing, motion consistency, artifact rate and actual delivered cost. Select one primary and one fallback only after blind review of the rendered clips. Do not call any paid generation endpoint before approval.

The current API integration state is: Kling key presence previously confirmed, but no direct Kling client; Google Gemini credentials are present for existing model calls, but video endpoint entitlement is not verified; no Runway credential was confirmed. Credential presence does not mean account quota, billing or model access is active.


## Owner-approved video-generation policy — zero budget / dual route support

Owner decision (2026-11-16):
- Default video-generation spend: **₹0 / US$0**.
- Both direct provider APIs and the Runway unified gateway may be supported architecturally.
- Both routes remain **disabled** in normal operation.
- No automatic paid generation and no automatic fallback to a paid provider.
- Explicit owner approval and a positive per-run budget are mandatory before any paid provider call.
- Human approval before publishing remains mandatory.

Implementation:
- Policy file: `config/video_generation_policy.v1.json`
- Fail-closed guard: `app/providers/video_generation_guard.py`
- Tests: `tests/test_video_generation_guard.py`

The guard requires all of the following after a future policy change:
1. Policy-level `enabled=true`.
2. Selected route-level `enabled=true`.
3. `NEXTDECODE_VIDEO_GENERATION_APPROVED=1`.
4. A positive `NEXTDECODE_VIDEO_GENERATION_BUDGET_USD`.
5. `NEXTDECODE_VIDEO_GENERATION_ROUTE` exactly matches the selected route.

The present policy has `enabled=false`, both route flags false, and zero default budget. Therefore, the guard denies both routes. This is an authorization boundary, not a provider client. No paid API client is invoked by this module.

Supported routes:
- `direct_provider_apis`: Kling and Google Veo can be qualified independently.
- `unified_gateway`: Runway can be qualified as a single integration route for its supported model catalog.

Neither route is currently selected as primary or fallback. The free-first production stack remains stock footage, local screen/vector scenes and FFmpeg.


## SVG-to-FFmpeg compatibility smoke test — 2026-11-16

- Generated a representative `flow_diagram` scene through `render_scene_component()`.
- Ran the installed FFmpeg against the generated SVG and rasterized one frame to PNG.
- Result: FFmpeg exit code `0`; PNG output existed; no stderr.
- The smoke test used a temporary fixture under `/tmp`; no production render or dependency installation was performed.

### Integration status

The adapter and rasterization path are validated in isolation, but live scene selection is not yet connected. The remaining required change belongs at the visual-selection/asset-resolution boundary: the selection owner must emit an explicit `visual_source` plus a validated `component` specification for chosen narration beats, then pass the rendered local SVG through the existing asset path. Do not infer or auto-convert arbitrary stock shots into components. Preserve stock selection, asset rights/provenance, shot timing, and FFmpeg assembly behavior.
