# NEXTDECODE Shorts Studio — Production Architecture & Agent Execution Charter

**Status:** Working target architecture and execution reference  
**Scope:** Existing Shorts Studio pipeline; upgrade in place  
**Owner:** Product owner  
**Orchestration:** ChatGPT / implementation orchestrator  
**Last consolidated:** 2026-11-15

> This document consolidates the production decisions and plans agreed in recent conversations. It is an execution reference, not evidence that every proposed capability is already implemented.

## 1. Product objective

Build NEXTDECODE Shorts Studio into a reliable, local-first, free-first, quality-focused automated video production system. It must behave like an intelligent editor rather than a media downloader followed by a file concatenator.

Initial target: 45–60 second vertical shorts, natural English narration, cinematic and fast editing, hybrid visuals, and human approval before publishing. Longer-form production can follow later.

Creative references supplied by the owner establish these goals:
- Cinematic, subject-specific visuals and polished presentation.
- Story-led progression, with each shot serving a clear narrative or explanatory purpose.
- Intentional editing: selected clip segments, pacing, framing, movement, transitions, sound design and continuity.
- A complete story and satisfying ending, not unrelated assets joined together.

Current benchmark topic: Mixtral / Mixture-of-Experts explainer. Reference videos are quality references, not templates to copy shot-for-shot.

## 2. Non-negotiable constraints

1. Preserve the existing repository architecture and decisions. Upgrade the current pipeline; do not replace or redesign it.
2. Preserve all uncommitted changes. Never reset, clean, stash, overwrite or broadly reformat shared work without explicit coordination.
3. Local-first and free-first. Initial recurring operating budget target is ₹0/month.
4. Hardware includes Intel integrated graphics and no dedicated GPU. Avoid GPU-heavy local generative video workflows.
5. Prefer deterministic, reproducible processing and reusable templates.
6. Human approval is mandatory before publishing. Public publishing stays disabled unless the owner explicitly changes that policy.
7. Research claims remain evidence-grounded. Rights, source attribution and provenance must be recorded for media assets.
8. A technically successful render is not automatically a successful video.
9. Do not add providers or dependencies without demonstrating measurable quality or reliability benefit.
10. Do not build a custom foundation model, codec, general-purpose video editor or duplicate dashboard.

## 3. Current baseline — reported observations to re-verify

These findings came from recent production runs and reviews. Re-verify against the latest run before changing code:
- One reviewed render planned 14 shots and rendered all 14 through the same motion-graphics provider.
- Zero stock video clips were used in that render.
- Similar MoE/router diagrams and generic gradient/text cards repeated across scenes.
- Some scenes were marked `no_action`, weakening narrative progression.
- Storyboard auto-approval occurred despite weak visual quality.
- Music and sound effects were missing in the reviewed output.
- Vision review encountered HTTP 429 rate limiting.
- Kokoro voice generation became stuck, with a run remaining in an in-progress state.
- A later execution reported stock video downloads/conversion and mixed visual sources; completion and review were still pending at the time of that report.
- Recent code work has included MoE visual-query classification changes, action-beat recognition, storyboard/run observability endpoints and dashboard scene-review UI. Verify current repository state before assuming exact implementation status.

These observations describe distinct runs. Always identify the run ID; do not combine them into a false claim about one run.

## 4. Target production architecture

Target a closed-loop workflow:

1. Research & Evidence
2. Editorial Script Director
3. Visual Director / Storyboard
4. Asset Intelligence
5. Automated Edit Director
6. Timeline Execution / Render
7. Technical QA + Creative QA
8. Targeted scene repair and re-render
9. Human approval
10. Publishing only through the existing protected approval boundary

### 4.1 Research & Evidence

Discover sources and build claim/evidence records; track provenance and confidence; distinguish supported, partially supported and unsupported claims; block or qualify claims that do not meet evidence requirements. Extend existing modules and provider adapters; do not duplicate the evidence system.

### 4.2 Editorial Script Director

Create a compelling hook, clear narrative progression, concrete explanation and satisfying payoff. Ensure every spoken beat has a communicative purpose, duration fits the target runtime, and narration avoids generic filler, repeated claims and unsupported certainty. Produce sentence/beat IDs for downstream visual planning. Preserve evidence constraints and source attribution. LLMs may assist drafting and critique, but deterministic validation and evidence gates remain authoritative.

### 4.3 Visual Director

For every beat, define:
- Beat and narration reference.
- What the audience must understand or feel.
- Visual subject and action.
- Visual family/type (real footage, still, original 2D/3D graphic, diagram, AI-generated insert, typography, etc.).
- Shot size, framing and composition.
- Camera/object movement.
- Environment, lighting and continuity notes.
- Desired duration and transition intent.
- Asset requirements and acceptable alternatives.
- Prohibited/repetitive visual patterns where relevant.

A topic-level query must not force every scene into the same diagram. A scene-type label is not enough; the renderer needs actionable visual instructions.

### 4.4 Asset Intelligence

Build and own the decision logic around external media:
- Generate multiple concrete search concepts per beat based on visual action and subject, not topic keywords alone.
- Search existing providers in batches and respect limits and terms.
- Cache search results and downloaded assets appropriately.
- Inspect duration, dimensions, FPS, codec, orientation, integrity and resolution.
- Generate representative frames/contact sheets for visual inspection.
- Score semantic relevance, visible action, composition, image quality, motion, usable duration, vertical-crop suitability and continuity.
- Deduplicate assets and near-duplicate compositions across a video.
- Record provider/source URL, creator, licence/usage terms, attribution requirements and retrieval timestamp.
- Reject unsuitable or unreviewed assets explicitly. Do not silently treat fallback cards as equivalent to footage.
- Keep a reason for each selection/rejection.

Provider strategy:
- **Pixabay:** primary free stock image/video candidate source. Respect API limits, caching rules and download restrictions.
- **Pexels:** use existing working API access if present. New key issuance may be restricted; verify account access rather than assuming.
- **Wikimedia Commons:** useful for historical/scientific/educational media; verify each file's licence, creator and attribution.
- Do not add more providers until current integrations and candidate ranking are measured and proven insufficient.

An API result is not automatically approved. Rights and creative relevance are separate gates.

### 4.5 Automated Edit Director — core capability to build

This is the central differentiator to build inside the existing system. It makes editing decisions before rendering:
- Select the best temporal segment from a source clip.
- Decide source in/out points and timeline duration.
- Align visible action with the corresponding narration beat.
- Choose crop, vertical reframing and subject placement.
- Apply controlled pan/zoom/tracking or other movement when appropriate.
- Choose cut, match cut, dissolve, wipe or another transition based on editorial intent.
- Control pacing and shot-length variation.
- Avoid repeating assets, compositions or motion patterns without narrative reason.
- Coordinate overlays, labels and captions.
- Place music and sound effects against narration and scene events.
- Preserve continuity across scenes.
- Emit an explicit edit plan and record important decisions.

The editor must not assume every source clip should be used in full or every scene needs a transition effect. Intentional hard cuts are often correct.

### 4.6 Edit Decision List (EDL) / timeline contract

Introduce or extend a structured, versioned edit-plan representation. Illustrative fields (not a claim about the current schema):
- scene_id / beat_id
- source_asset_id and provenance reference
- source_in / source_out
- timeline_start / duration
- playback_speed (when justified)
- aspect ratio / crop / focal position
- motion treatment
- transition_in / transition_out
- narration segment reference and sync markers
- overlay/caption references
- music/SFX cues and gain/ducking intent
- continuity group / adjacent scene references
- QA status and rationale

The EDL must be deterministic and inspectable. Rendering the same approved EDL and same source assets should be reproducible within render-stack limits. Validate schema, paths, durations, overlaps and media availability before rendering.

### 4.7 Timeline execution and rendering

- Retain **FFmpeg** as the primary media-processing and final rendering/compositing engine.
- FFmpeg executes timeline decisions; it is not the creative decision-maker.
- Use it for trimming, scaling/cropping, compositing, overlays, transitions, audio mixing, encoding and final assembly.
- Extend existing render/assembly modules rather than creating a parallel renderer.
- Preserve vertical 1080×1920 and established frame-rate/output contracts unless the owner approves a change.
- Add render manifests and per-scene diagnostics for targeted re-rendering.

### 4.8 Blender — original 3D visual engine

Use Blender for reusable original 3D scenes that stock media cannot explain well:
- AI token routing and expert activation.
- Network/data flow and system architecture.
- Processor/chip and hardware visualizations.
- Scientific/molecular structures.
- Cinematic openers, transitions and explanatory scenes.

Preferred integration:
1. Install/use stable Blender desktop on Windows for scene development and visual inspection.
2. Build deterministic templates using Blender Python (`bpy`).
3. Run Blender in background/headless mode for automated renders.
4. Feed rendered clips into the existing timeline/FFmpeg pipeline.
5. Keep templates parameter-driven (objects, labels, colours, camera, duration, animation state), reusable and versioned.

Hardware strategy:
- Benchmark simple low-poly/procedural scenes first on the Intel machine.
- Prefer lightweight scenes, restrained lighting, short shots and sensible render settings.
- Do not assume GPU rendering is supported or faster. Verify devices and benchmark CPU/Eevee options on the actual machine.
- Avoid heavy local AI video-generation models.

Blender MCP:
- Optional agent interface for scene exploration, prototyping or interactive debugging.
- Not a mandatory production dependency.
- Prefer controlled `bpy` scripts and headless Blender for reproducible production.
- Security-review any community MCP server; do not expose arbitrary Python execution to untrusted callers.

### 4.9 Remotion evaluation

Remotion may be evaluated for React-driven animated compositions, typography and timeline sequences. It is not automatically selected.

Before adoption:
- Verify current licensing for the exact company/team/use case.
- Build one representative scene and compare quality, render time, maintainability and integration cost against FFmpeg + existing motion graphics.
- Check whether it duplicates current capabilities.
- Adopt only if it provides measurable advantage and acceptable licensing.
- Do not make it a blocker for the first benchmark.

### 4.10 Voice, captions and audio

- **Kokoro:** retain as local-first voice candidate, but fix process lifecycle, timeouts, locking/contention, stuck-job detection and recovery.
- **faster-whisper:** retain for local transcription/caption support; validate alignment against narration.
- **Music/SFX:** establish a curated, rights-cleared local library with source/licence metadata.
- **Audio Director:** implement voice-first mixing, music ducking, controlled SFX placement, fades, loudness/peak checks and silence detection.
- Paid TTS (e.g. ElevenLabs) remains an optional quality fallback, not a mandatory dependency. Check current pricing/licensing before paid use.
- Music and SFX must not obscure narration. Avoid decorative effects that do not reinforce the scene.

### 4.11 Vision and creative QA

Vision review is a helper, not the only quality gate:
- Respect RPM/TPM limits with bounded concurrency, exponential backoff and jitter.
- Distinguish approved, rejected, pending, failed and unreviewed states.
- HTTP 429 or review failure must never silently become approval.
- Cache review results by asset/version where safe.
- Use deterministic checks for dimensions, black/frozen frames, audio peaks/silence, subtitle presence, timing and file integrity.
- Use vision review for relevance, composition, repetition and visual defects when available.
- Use contact sheets and full-video review for benchmark acceptance.
- Weak scenes should produce targeted repair instructions and be re-rendered; avoid unnecessary full regeneration.

## 5. External services and cost policy

### 5.1 Default operating mode

Target ₹0/month recurring spend:
- Existing free stock APIs and free media sources.
- Existing free-tier LLM/vision capacity where available.
- Local Kokoro and faster-whisper.
- FFmpeg and Blender.
- Own Python orchestration, scoring, EDL and QA logic.

This assumes free-tier availability; it is not unlimited capacity. Hardware, electricity, internet and storage are excluded.

### 5.2 Optional paid services

Paid TTS, premium LLM/vision or AI-video generation may be considered only when a measurable quality/reliability gap exists, value is explained, current official pricing/licence is checked, per-run usage/cost is recorded, and the owner approves spend.

AI video generation is selective, not default. Never make production dependent on a paid AI video API without explicit owner approval.

### 5.3 Cost ledger

Record per run:
- Research/search requests and tokens.
- Script/critique model and token usage.
- Vision requests, model and retries.
- TTS characters/minutes and provider.
- Image/video generation seconds and credits.
- Asset downloads and storage.
- Render duration and resource use.
- Total estimated and actual paid cost, currency and pricing snapshot date.

Do not report fixed monthly cost without usage assumptions and current price evidence.

## 6. Agent roles and coordination

### Product owner
Defines creative direction, constraints and final acceptance; approves paid services and any publishing-policy change; reviews complete candidate videos.

### Orchestrator (ChatGPT / assigned lead)
Owns integrated roadmap, work allocation, dependencies and acceptance. Maintains one view of defects, owners and evidence. Reconciles agent changes and protects shared work. Does not claim completion without artifacts, tests and run evidence.

### Parallel agent
Independently audits and remediates existing visual pipeline defects: asset search/selection, scene diversity, action classification, fallback correctness, vision rate limiting, Kokoro reliability, music/SFX path and storyboard quality gates.
Must report exact files, root causes, tests, run ID, rendered video/contact sheet, provider mix and remaining risks.
Must coordinate before editing EDL/Automated Edit Director/timeline-contract modules owned by the orchestrator.
Must not alter publishing governance or dashboard ownership.

### OpenCode
Owns independent Dashboard work. Does not own video creative/editing architecture. Avoid shared-file collisions; dashboard work proceeds independently.

### Specialist reviewers
Use existing assigned engineering, regression, security and product-review roles. Reviews include evidence and exact scope; avoid duplicate implementation.

### Shared-work rules
- Inspect `git status` and relevant diffs before editing.
- Treat existing uncommitted changes as owned until ownership is confirmed.
- Never overwrite another agent's changes.
- Coordinate shared modules and establish clear file/feature boundaries.
- Integrate coherent batches with focused then broader regression tests.
- No commits/pushes unless explicitly requested.

## 7. Implementation roadmap and acceptance gates

### M0 — Baseline and environment
Identify latest run and inspect manifest, storyboard, assets, render logs, contact sheet and full video. Record provider/visual-type distribution and failure states. Inspect installed Blender, FFmpeg, Python and dependencies before installing. Record current code ownership and uncommitted changes.

**Accept when:** baseline is tied to a specific run ID and actual visual evidence.

### M1 — Stabilize existing pipeline (Parallel-led)
Fix asset relevance/diversity and silent fallback; fix `no_action` classification where narration justifies; make vision review rate-limit-aware and fail closed; fix Kokoro contention/timeouts/recovery; restore reliable music/SFX; strengthen storyboard approval.

**Accept when:** tests pass and a completed benchmark demonstrates relevant varied visuals, reviewed scenes and working audio.

### M2 — Editing contract and Edit Director (Orchestrator-led)
Audit existing timeline/assembly first. Define/extend versioned EDL. Implement clip in/out selection, duration, crop, motion, transition, narration sync and audio cues. Validate plans before render. Preserve compatibility with existing artifacts where practical.

**Accept when:** inspectable EDL is generated and executed; rendered output visibly reflects its decisions.

### M3 — Blender prototype and reusable scene engine
Verify environment and install stable Blender only if absent. Create one short parameter-driven 3D scene using `bpy`. Benchmark on actual hardware. Integrate into existing render path. Add templates only after prototype review.

**Accept when:** vertical scene renders reliably, integrates into final video and can be regenerated from parameters.

### M4 — Audio and full production integration
Implement/verify voice, music, SFX, ducking, fades, caption timing and loudness checks. Combine footage, original graphics and optional generated inserts through EDL.

**Accept when:** complete short has intentional sound design and coherent scene timing.

### M5 — Closed-loop Creative QA
Inspect full render and contact sheet. Identify defects by scene/timecode. Generate targeted repairs and re-render affected scenes. Re-run technical and creative QA.

**Accept when:** weak scenes are not silently accepted and final candidate passes human review.

### M6 — Repeatability and cost control
Produce at least three independently reviewed topics. Compare quality, failure rate, production time and per-video cost. Tune caching, concurrency, retry budgets and render settings.

**Accept when:** quality and cost are repeatable across topics, not merely one successful demo.

## 8. Creative and technical acceptance criteria

Review:
- Hook strength and story progression.
- Factual accuracy and evidence quality.
- Scene relevance to exact narration.
- Diversity of visual subjects and compositions.
- Appropriate mix of real footage, original graphics and diagrams.
- Clip segment quality and visible action.
- Vertical framing and subject visibility.
- Pacing and shot-duration variation.
- Camera/object movement where appropriate.
- Transitions that support rather than distract.
- Voice clarity and narration synchronization.
- Music/SFX balance and intentional placement.
- Caption accuracy, timing and readability.
- Continuity and satisfying ending.
- Rights, provenance and attribution.
- Technical integrity: resolution, frame rate, sync, corruption, unintended black/frozen frames.

A proposed creative target of 85/100 may be used only after the rubric is defined and calibrated. It is not a verified current score or substitute for owner approval.

## 9. Immediate execution checklist

1. Confirm latest Parallel run is complete; do not start competing renders.
2. Obtain Parallel's final defect/fix report and exact files changed.
3. Inspect latest actual video, contact sheet, storyboard and EDL/timeline implementation.
4. Map existing timeline capabilities before implementing duplicates.
5. Establish file ownership for EDL/Automated Edit Director modules.
6. Prototype one EDL-driven scene end-to-end.
7. Verify Blender installation and benchmark one simple `bpy` scene.
8. Integrate only proven components into the existing pipeline.
9. Produce a complete Mixtral benchmark render.
10. Review, repair, re-render and obtain owner approval.

## 10. Explicit non-goals

- Replacing the existing Shorts Studio architecture.
- Building a new editor application.
- Replacing FFmpeg.
- Adding many stock providers without evidence.
- Generating every shot with AI video.
- Installing heavy local generative-video models on Intel hardware.
- Making Blender MCP mandatory.
- Adopting Remotion without licensing and benchmark evaluation.
- Auto-approving unreviewed/weak scenes.
- Enabling automatic public publishing.
- Treating tests, provider counts or successful rendering as proof of creative quality.

## 11. Agent handoff template

Every implementation agent reports:
1. Assignment and scope.
2. Baseline observed (run IDs, files, logs, visual evidence).
3. Root cause.
4. Files changed.
5. Implementation details.
6. Tests and exact results.
7. Production run ID and artifact paths.
8. Before/after evidence.
9. Provider mix and review status.
10. Cost/usage, if applicable.
11. Remaining risks and blocked items.
12. Shared-file conflicts or follow-up ownership.

Do not claim completion if the production artifact is missing, unreviewed or materially below acceptance criteria.

---

**Operating principle:** NEXTDECODE owns creative intelligence and editing decisions. External services provide media or specialist capabilities; Blender creates original 3D scenes; FFmpeg executes the approved timeline; Creative QA closes the loop; the owner retains final publishing approval.
