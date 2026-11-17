# NEXTDECODE Audience Growth & Faceless Documentary Research
**Date:** 2026-11-17  
**Status:** Initial evidence-backed scan. The 100-150 channel / 1,000-video benchmark is NOT complete.

## Editorial definition
Faceless means no on-camera human presenter. It does not mean animal-only or non-human subject matter. Use narration with footage, archival material, maps, animation, diagrams, graphics and screen recordings. The editorial promise should be to explain surprising things about the world through clear, researched, visually compelling stories. Broad topics should be united by editorial quality, not forced into an AI-only identity.

## YouTube guidance
YouTube describes recommendation performance through **appeal** (viewer chooses to watch), **engagement** (viewer stays) and **satisfaction** (viewer feels the experience was worthwhile). It recommends clear title/thumbnail promises, fast hooks, accessible framing and retention analysis.  
Source: https://support.google.com/youtube/answer/16559650?hl=en

YouTube monetization policy expects original, authentic work. Generic, repetitive, mass-produced, interchangeable templates and low-value reused material can make a channel ineligible. Faceless production and AI assistance are not inherently disqualifying; the finished work must add distinct creative, educational or entertainment value.  
Source: https://support.google.com/youtube/answer/1311392?hl=en

YouTube's performance FAQ says upload frequency is not a guaranteed growth lever; a viral video may not build a durable audience if viewers do not return. Relative watch time matters more for short videos, absolute watch time more for longer videos.  
Source: https://support.google.com/youtubecreatorstudio/answer/141805?hl=en

## First-pass reference channel set
Discovery shortlist, not a ranking. A third-party survey captured a snapshot of channel sizes and recent formats in early November 2026; counts are time-bound and not independently audited.

| Territory | Channels | Format lesson |
|---|---|---|
| Investigations / world affairs | FRONTLINE PBS, DW Documentary | Evidence-led reporting, human stakes |
| History / civilizations | Fall of Civilizations, Kings and Generals, Epic History, Mark Felton Productions, Simple History, Dark Docs | Maps, chronology, archival proof, character arcs |
| Engineering / aerospace | Real Engineering, Curious Droid | Machines explained through constraints and trade-offs |
| Space / science | Astrum, NASA, LEMMiNO | Scale, visual evidence, unanswered questions |
| Geography / systems | Wendover Productions, RealLifeLore | Simple why/how question reveals a larger system |
| Business / money | MagnatesMedia | Rise/fall arcs, incentives, conflict |
| Prototypes / transport | Found And Explained, Mustard | Strange inventions and visual specificity |
| Mystery / research | LEMMiNO, Dark Skies | Evidence ladder, competing explanations, uncertainty |

Survey: https://framitor.site/blog/best-documentary-youtube-channels  
Discovery directory: https://facelesslist.com/categories/history/

Direct channel-page snapshot during this scan: Found And Explained showed 690K subscribers / 279 videos. Its popular list included a TR3B spy-plane video (7.3M views), the Kharkovchanka Antarctic machine (6.2M), and the Breitspurbahn railway concept (5.9M). These counts can change.  
Channel: https://www.youtube.com/@FoundAndExplained

## Story patterns worth testing
1. Forgotten invention: what was built, why it seemed brilliant, why it disappeared.
2. Everyday mystery: a familiar object, price or route explained by a hidden system.
3. Engineering trade-off: one design choice solved a constraint but created another.
4. Rise / collapse / comeback: company, technology, city or institution.
5. Evidence-led mystery: claim, supporting evidence, contradiction, responsible conclusion.
6. Scale reveal: visual comparison makes an abstract fact instantly understandable.
7. Human-stakes explainer: one person or community makes a large system relatable.
These are test hypotheses, not guaranteed viral formulas.

## Repository implications
The repo already has broad topic discovery and a 12-category taxonomy. The legacy selector still describes channel fit in AI/technology-first terms and uses AI-era editorial pillars. If broad discovery feeds this selector unchanged, non-tech candidates may be under-scored. Fix this before treating diversification as complete.

Recommended selection dimensions:
- Audience-promise fit (not narrow AI fit)
- Demand evidence, trend velocity and evergreen potential; unknown stays unknown
- Packaging strength: clear, accurate curiosity question
- Story strength: stakes, conflict, surprise, cause/effect, reveal, payoff
- Visual proof feasibility: can the claims be shown specifically?
- Source quality, corroboration and claim confidence
- Differentiation vs each channel/topic's own baseline
- Production effort, rights, asset availability and cost
- Monetization / advertiser suitability (do not invent RPM)
- Audience continuity: likely next video for the same viewer

Use topic-dependent format routing. Do not force every story into one sequence or visual style.

## Shorts packaging / retention experiments
Generate three materially different hook/title concepts per candidate. Score clarity, honest curiosity, broad relevance, immediate visual proof, payoff and claim accuracy. Test multiple structures: cold open -> question -> proof -> twist -> payoff; claim -> context -> contradiction -> resolution; object -> origin -> constraint -> consequence; mystery -> evidence -> best-supported answer -> uncertainty.

Measure in own YouTube Studio: viewed-vs-swiped-away, average view duration, average percentage viewed, retention curve, shares, comments, likes, subscribers gained, returning viewers and traffic sources. Competitor public pages cannot reveal private retention, swipe-away, CTR or subscriber conversion.

## Benchmark dataset plan (not yet completed)
- Pilot: 20-30 channels across at least 8 territories; then expand to 100-150.
- Capture 8-12 recent uploads per channel plus selected outliers; separate Shorts and long-form.
- Fields: channel/video URL, category, format, title, duration, publish date, public views/likes/comments if available, capture date, hook/story pattern, visual type and source confidence.
- Compare each video's views with that channel's own recent median and age-matched peers, not raw views alone.
- Flag on-camera channels, broadcaster/licensed libraries and compilations separately.
- Missing metrics are null, never zero. Do not infer CTR, retention, swipe-away or subscriber conversion from public data.

## Initial publishing experiment
Provisional allocation only (not a proven optimum): 50% discovery-led Shorts, 30% narrative Shorts, 20% longer-form experiments. Evaluate subscriber gain and returning viewers, not only views, before reallocating.

## Guardrails
Human approval before publishing; no automatic public uploads. Verify rights per asset. No fake engagement, misleading packaging or unsupported claims. Avoid near-identical AI scripts/templates. Do not confuse faceless with wildlife-only.

## Sources
- https://support.google.com/youtube/answer/16559650?hl=en
- https://support.google.com/youtube/answer/1311392?hl=en
- https://support.google.com/youtubecreatorstudio/answer/141805?hl=en
- https://framitor.site/blog/best-documentary-youtube-channels
- https://facelesslist.com/categories/history/
- https://www.youtube.com/@FoundAndExplained

**Status:** Initial scan complete; comprehensive benchmark and selector scoring changes remain pending. No code changed in this research increment.


## Engine integration — benchmark is now read by the topic selector

The selector now imports `app.research.benchmark.load_benchmark_context()` and
loads the benchmark once (cached) for its scoring context. The channel-fit
dimension includes a `benchmark_reference` record in its breakdown with source
availability, observation count, channel count, recurring title patterns and
explicit `score_adjustment: 0.0`.

This is intentionally advisory-only. The benchmark currently has a small,
uneven public sample and mostly lifetime view counts. It must not directly
inflate or suppress topic scores, replace live demand/evidence checks, or
override editorial judgement. If the file is absent or unreadable, the selector
continues without benchmark context.

Focused regression group after integration:
`PYTHONPATH=. pytest -q tests/test_research_benchmark_context.py
tests/test_selector_growth_breadth.py tests/test_selector_judgement_mapping.py
tests/test_research_quality.py tests/test_pipeline_topic_discovery.py`
— **44 passed**.
