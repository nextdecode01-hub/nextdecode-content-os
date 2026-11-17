# NEXTDECODE — Story-First Documentary Production Upgrade

**Date:** 2026-11-17  
**Status:** Incremental implementation in progress; this document distinguishes implemented code from target capabilities.  
**Repository:** `/home/demon/shorts_studio`

## Owner direction consolidated

NEXTDECODE must not behave like a template-driven AI/technology Shorts generator. It is a story-first documentary production system covering a rotating range of categories: science, world events, business/economy, history/mysteries, nature/environment, space, human stories, consumer/society, culture/entertainment, technology/AI, investigations and sports.

The core dependency is:

**Topic → editorial angle → script → beat/phase plan → visual/audio evidence plan → asset acquisition → edit decisions → render → creative QA → human approval.**

The script is the source of truth for the video. Visuals must serve the exact story beat, not be selected from a generic topic keyword and retrofitted underneath narration.

## Product principles

1. **Category diversity:** avoid consecutive videos from the same main category when a strong alternative exists. Detect semantic/story-family repetition, not only identical titles.
2. **No forced rotation:** never choose a weak topic just to satisfy category diversity.
3. **Editorial direction before narration:** define the viewer question, distinct angle, why it matters now, strongest evidence, surprising but defensible insight and final viewer payoff.
4. **Narrative is topic-specific:** mini-documentary, investigation, science explainer, history reveal, human story, business case, timeline and comparison are options—not mandatory templates.
5. **Complete production script:** every phase needs timecodes, exact narration, purpose, visual type/action, asset/source search, on-screen text, audio direction, edit direction, rights notes and fallback.
6. **Reality first when relevant:** prefer authentic event footage, original interviews/speech, natural sound, real demonstrations, original documents and archival images when they materially improve the story and can be cleared.
7. **Animation with a purpose:** use custom 2D/3D, motion graphics, generated images or existing GIFs when real footage cannot explain an invisible mechanism or when a visual needs to be created.
8. **No fabricated evidence:** never invent a screenshot, news clip, quote, demonstration or event reconstruction. Label illustrative material.
9. **Rights are separate from attribution:** credit does not itself grant permission. Each media asset needs a documented rights basis, licence/permission and attribution requirements.
10. **Human governance:** uncertain rights, weak evidence, failed quality gates and publishing actions remain blocked pending review. Public publishing stays disabled by default.

## Topic taxonomy and rotation

The initial deterministic taxonomy is implemented in `app/research/topic_diversity.py`:
- `classify_topic(title, summary)`
- `similarity(left, right)`
- `annotate_and_diversify(candidates, recent_topics, limit)`

The taxonomy currently includes 12 broad categories plus a general-curiosity fallback. It annotates candidates with `topic_category` and a similarity/category-repeat diagnostic, removes close repeats against recent titles, then prefers category breadth before filling remaining slots by rank.

Research discovery in `app/research/topics.py` has been broadened beyond AI feeds to include world, business, history, space, nature, sports, documentary and general curiosity communities, plus category-specific Google News RSS queries. Existing Hacker News, arXiv and Google Trends sources remain optional inputs.

**Known limitations to address next:**
- Current taxonomy is keyword-based; ambiguous/multi-topic stories need confidence and human-readable rationale.
- Recent history currently derives from the existing used-topic text file; category-aware history should eventually be persisted with run metadata and configurable cooldown windows.
- X/social conversation intelligence is not yet integrated as a first-class provider. It must distinguish original posts, reposts, opinion, verified claims and engagement metrics; never fabricate a viral signal.
- Discovery breadth and ranking need live measurement. Search availability is not evidence of audience demand.

## Story-first script contract

`app/script/short.py` now prompts for a topic-specific editorial decision and a production storyboard, not only a voiceover. Required direction fields:
- `content_pillar` (story format)
- `editorial_angle`
- `viewer_question`
- `viewer_payoff`
- `hook`
- `voice_text`
- `production_storyboard[]`

Each storyboard phase includes:
- phase and start/end seconds;
- narration excerpt copied from the final voiceover;
- viewer purpose;
- visual type and visible action;
- asset search or primary-source URL;
- on-screen text;
- audio direction;
- edit/transition direction;
- rights notes;
- fallback.

`app/script/production_storyboard.py` validates phase count, required fields, contiguous time coverage, supported visual types, target runtime and narration excerpt alignment. It marks rights status as review-required; it does not infer clearance from a source label.

## Visual and media system target

The existing project already has visual planning, asset resolution, asset QA, storyboard/contact-sheet review, cutouts, provenance and FFmpeg edit/timeline infrastructure. Extend those modules; do not create a parallel renderer.

Visual selection order is contextual, not absolute:
1. Real event footage or original demonstration.
2. Original interview/speech and natural sound where the human voice adds meaning.
3. Primary documents, reports, data, maps, screenshots and evidence.
4. Licensed archive or stock footage and photographs.
5. Existing licensed GIF/animation.
6. Original generated image or custom animation.
7. Original motion graphic/typography when it communicates better.

A visual director should issue shot-level instructions: what the viewer must see, action, framing, duration, source segment, transition, movement, continuity, caption/overlay and reason for selection. A 10-second narration beat may need several distinct shots.

### Media rights record (required per asset)

- provider and asset identifier;
- exact source/landing-page URL;
- creator/owner;
- licence name, version and URL;
- commercial-use and adaptation permissions;
- permission evidence or rights basis;
- attribution text and whether attribution is mandatory;
- retrieval timestamp and cached-file digest;
- review status and reviewer;
- intended use and any platform/territory/time restrictions.

Unknown or ambiguous rights must be blocked from automatic publishing. Corner credits and description credits are rendered only after the actual licence/permission basis is established. News-agency footage such as AP/Reuters should be treated as licensed footage unless a clear alternative rights basis exists. Do not assume a few seconds is automatically safe.

## Audio direction target

The final audio may combine:
- original speaker/interview audio;
- natural sound (NAT sound) from the actual scene;
- NEXTDECODE narration;
- licensed music and sound effects.

The edit director should support J-cuts, L-cuts, sound bridges, reaction cuts, ducking and clean transitions. Keep original speech where it adds authority, emotion or first-hand explanation; do not automatically cover every clip with TTS. Extract audio only from a selected, rights-cleared media segment and preserve source/timecode provenance. Avoid speech/music separation unless necessary and quality-tested.

## Shorts production contract

Target remains 45–60 seconds, vertical 9:16, natural English, cinematic/documentary pacing, hybrid real+created visuals, free-first and local-first. The final storyboard and EDL must correspond to the same approved script version. Changes to narration invalidate stale storyboard alignment and trigger regeneration/review.

Creative QA must evaluate:
- hook clarity and specificity;
- story progression and new information per beat;
- evidence alignment;
- real-vs-illustrative visual honesty;
- source and rights traceability;
- visual variety and action relevance;
- original audio quality and narration balance;
- mobile readability;
- runtime, pacing and payoff.

A successful render is not automatically a successful video. The storyboard/contact sheet and rendered video require human review before publishing.

## Long-form expansion

The repository already contains `app/script/longform.py` and `pipelines/longform.py`, with 2/4/6/8/10-minute profiles and a primary + independent secondary source requirement. Preserve this implementation and extend it as follows:

1. Commission a distinct long-form story angle; do not simply stretch a Short.
2. Build a research dossier: primary source, independent corroboration, source timeline, evidence notes, uncertainty and opposing viewpoints.
3. Write a chapter outline with a central question, chapter-level purpose, evidence and turning points.
4. Generate a complete narration script with beat IDs and chapter timecodes.
5. Build a detailed shot list for every chapter, not just one generic B-roll query per chapter.
6. Search authentic footage, interviews, demonstrations, archive, documents, maps and licensed stock; use original visuals for explanation.
7. Plan original speech, natural sound, narration, music and sound bridges.
8. Create a chapter EDL and render chapters/intermediates for recoverable editing.
9. Run long-form-specific fact, source, audio, continuity, retention and rights QA.
10. Human-review the full video and sources before any publication.

Long-form should reuse the same research, topic taxonomy, rights ledger, media adapters, Visual Director, audio plan, EDL and QA contracts as Shorts, while having its own pacing, chapter structure and runtime validation. Do not destabilize the current Shorts path to enable long-form.

## Implementation status — 2026-11-17

### Implemented in this increment
- Added deterministic 12-category taxonomy and topic similarity helper.
- Broadened topic discovery sources and category-specific discovery queries.
- Added category annotation, near-duplicate filtering and category-diverse ordering.
- Reframed Shorts script prompt from AI/technology-only to broad NEXTDECODE editorial categories.
- Required a topic-specific editorial angle, viewer question and payoff.
- Required a timed production storyboard with real footage, original speech, natural sound, documents, archive, stock, GIF, generated image and custom animation options.
- Added deterministic storyboard validation for complete time coverage, required production direction, visual type and narration excerpt integrity.
- Reframed long-form commissioning prompt for broad documentary categories and richer visual-source options.
- Added focused tests for taxonomy, similarity, storyboard timing and fail-closed validation.

### Not yet implemented / not yet verified
- X/social provider integration and conversation brief generation.
- First-class rights/permission ledger across all media types and publish-time enforcement for every provider.
- Actual search/acquisition of news archive footage and interviews, including licensing workflow.
- Original speech/NAT sound segment extraction and timeline mixing.
- GIF provider/search/rights handling.
- Visual Director routing every new storyboard visual type through actual asset providers and rendering adapters.
- Shot-level storyboard-to-EDL enforcement in the live production pipeline.
- Long-form chapter-level shot lists, mixed original speech/audio and full documentary QA.
- End-to-end live run with a category different from the previous AI/security stories.

## Next engineering sequence

1. Add focused rights policy/ledger validation and connect it to asset resolution and publishing gates.
2. Implement beat-level visual-type routing and source-specific search adapters while preserving Pixabay/Pexels/Wikimedia/Coverr/Openverse.
3. Add original speech/NAT sound clip selection, timecode provenance and FFmpeg audio timeline support.
4. Connect validated storyboard phases to shot planning and EDL; reject unfulfilled visual requirements instead of silently substituting generic motion graphics.
5. Extend the long-form chapter plan to the same beat-level production contract.
6. Run a new non-AI category production experiment, inspect the actual contact sheet and final video, then compare against the previous output.

No provider permission, paid archive licence, audience performance or production success should be claimed without evidence.
