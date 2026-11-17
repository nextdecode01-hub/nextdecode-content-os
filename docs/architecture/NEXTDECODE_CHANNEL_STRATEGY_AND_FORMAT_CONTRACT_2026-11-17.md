# NEXTDECODE Channel Strategy & Format Contract

**Status:** Active channel profile v1  
**Channel:** NEXTDECODE  
**Tagline:** Decode what comes next.

## 1. Audience promise

Evidence-led documentaries and explainers that decode important changes in technology, business, economics and the future. The channel is not a general-interest documentary channel and is not restricted to AI news.

## 2. Editorial niche

### Primary lanes
- AI & Artificial Intelligence
- Technology & Innovation
- Startups & Entrepreneurship
- Business & Economics
- Markets & Industry Shifts
- Future Trends

### Related lanes (must connect to the audience promise)
- Semiconductors, computing and advanced hardware
- Robotics, automation and industrial technology
- Cybersecurity, digital privacy and trust
- Internet platforms, digital economy and creator economy
- Venture capital, startup funding and corporate strategy
- Global trade, technology supply chains and industry competition
- Energy transition, batteries and electric mobility
- Cloud, data centres and digital infrastructure
- Biotechnology and science-to-market innovation
- Work, productivity and the future of jobs
- Technology policy, regulation and industry geopolitics
- Consumer technology and the economics of products

A related lane is not an unrestricted invitation to cover the entire parent category. For example, general geopolitics is out of scope; chip export controls or technology supply-chain policy can be in scope.

### Out of scope unless directly connected
General history, wildlife/nature, general sports, celebrity entertainment, unrelated true crime, unrelated geopolitics and generic lifestyle. Unclear cases remain available for manual editorial review rather than being silently treated as a fit.

## 3. Editorial quality rules
- Every factual claim needs evidence and source provenance.
- Explain why the development matters and who/what it affects.
- Prefer specific companies, products, technologies, decisions, mechanisms and measurable consequences over generic trend summaries.
- Avoid generic trend-chasing and unrelated viral topics.
- Faceless visual storytelling; no human-on-camera presenter requirement.

## 4. Multi-format content system

The editorial story is the source package; formats are platform-native adaptations, not separate unrelated topic streams.

| Format | Strategic role | Typical treatment |
|---|---|---|
| YouTube long-form | Flagship depth, authority and watch time | 6, 8, 10, 12 or 15-minute profiles; evidence, context, mechanism, consequences |
| YouTube Shorts | Discovery and one strong idea | 30, 45, 60 or 90-second single-idea story |
| Instagram Reels | Discovery and shareable explanation | Adapted vertical cut, native opening/caption |
| Facebook Reels | Additional discovery/distribution | Platform-specific packaging |
| YouTube Community posts | Audience conversation and follow-up | Polls, questions, updates, evidence-led context |
| Instagram posts/carousels | Saveable explainers | Charts, timelines, comparisons, key takeaways |
| Facebook posts | Discussion and distribution | Context-setting copy and visual summaries |
| LinkedIn posts | Professional/business audience distribution | Industry, company, technology and economic implications |
| X posts | Timely discussion and concise insight | Evidence-linked threads or concise observations |

Repurpose from an approved research/story package. Preserve claims and source provenance, but adapt hook, structure, caption and creative to each platform. Do not publish identical copy everywhere.

**Capability boundary:** This profile declares the channel's intended formats. It does not claim that every listed platform's post/carousel publishing adapter is implemented or connected. Existing YouTube long-form and short/reel publishing paths must continue to respect their own protected authorization and human-approval requirements. New post/carousel adapters require separate qualification and approval before they can publish.

## 5. Channel isolation for future expansion

Every future channel must have its own profile, niche allowlist, audience promise, topic history, category rotation, feedback signals, editorial voice and format strategy. Shared research/render infrastructure is acceptable; topic eligibility and audience feedback must not bleed between channels.

## 6. Engine integration in this increment

- `config/channels/nextdecode.v1.json` is the active machine-readable channel profile.
- `app/research/channel_profile.py` loads the profile and evaluates channel relevance using explicit editorial signals.
- `app/research/selector.py::niche_relevance` now uses the active NEXTDECODE channel gate. Unrelated broad categories are not automatically eligible.
- `app/script/short.py` and `app/script/longform.py` now use the focused NEXTDECODE positioning in their editorial prompts.
- `config/brain/project_context.v1.json` has been aligned with the multi-format positioning.

This is a first profile-and-eligibility increment, not a claim that every format already has a complete production and publishing pipeline. The next engineering step is to make the selected format an explicit first-class job input and route it to the correct script, visual, render, QA, metadata and publishing contract.

## 7. Governance

Human approval remains mandatory before publishing. Automatic public publishing remains disabled. Local-first/free-first and evidence/rights provenance requirements remain in force.
