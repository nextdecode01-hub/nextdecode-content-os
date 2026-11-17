# OpenCode — Engineering-Grade NEXTDECODE Dashboard Prototype Challenge

You are being evaluated on your ability to produce a high-quality, maintainable, technically credible dashboard prototype that respects the existing NEXTDECODE architecture and governance. Do not turn this into a production integration task.

## Your assignment

Create a separate independent prototype under:

`ui-prototype/variants/opencode/`

Build a polished Control Center experience with a clear modular structure. Compete on interaction quality, engineering discipline, accessibility and extensibility — not on the number of files or abstractions.

## Required screens and workflows

- Overview: cross-project operational summary, work needing attention, recent events and pipeline health.
- Projects: project portfolio, status, owner, stage and filters.
- Workflows: execution runs, run details, queue state, retries, failures and blocked states.
- Research: research packages, source count, claim verification and evidence review.
- Studio: content items, script/visual/voice/edit stages and artifact readiness.
- Review & Approvals: exact version under review, evidence/rights/quality state, pending decision and history. All actions are mock-only.
- Publishing: destination/readiness visibility, clearly disabled protected actions, no external publishing.
- Analytics: sample trend and useful content-quality/performance signals.
- Operations: workers, heartbeat, queue depth, incidents and recovery states.
- Settings: display preferences and workspace configuration placeholders.

Use realistic sample data and consistent state definitions across screens. Make navigation and page-level interactions genuinely work.

## Visual requirements

- Dark-first interface inspired by ChatGPT's current dark UI: charcoal surfaces, readable muted text, subtle borders, restrained green/teal accent.
- Do not use a white dashboard as the default.
- Provide a global Dark / Light / System appearance mode selector. Dark is default and applies to every feature/page, not just the Overview.
- Persistent sidebar or responsive equivalent, clear page context, sample-data indicator, global search/filter affordance where appropriate.
- Desktop, tablet and mobile support.
- Thoughtful hierarchy and density: operationally useful, not a collection of oversized cards.

## Technical approach

- Prefer React + TypeScript + Vite only if the current environment already supports it without installing dependencies or modifying root manifests.
- Otherwise build a dependency-free HTML/CSS/JS prototype, or source-only React files with clear prerequisites.
- Organize code by reusable layout, navigation, page modules, components, sample data and theme tokens where appropriate.
- Avoid premature abstractions and do not add a state-management framework for a static prototype.
- Ensure theme preference applies globally and is retained locally if implemented.
- Use semantic HTML, accessible labels, keyboard navigation, visible focus, reduced-motion support and responsive table handling.

## Existing architecture and safety constraints

- NEXTDECODE is local-first, free-first, human-governed.
- Existing Shorts Studio remains the specialist production engine.
- P0 canonical contracts and architecture are the source of truth.
- Broad P1 Control Center implementation is gated by P0 closure/readiness and formal owner authorization.
- This is prototype-only authorization.

Strict boundaries:
- All created/modified files must remain inside `ui-prototype/variants/opencode/`.
- Do not edit root project files, production code, API, database, schema, migrations, canonical docs or any other variant.
- No dependencies, installs, live API/backend/database/provider calls, secrets, deployment, uploads or publishing.
- Use sample data only.
- No actual content generation, approval, export or distribution action.
- Do not perform git reset/stash/clean/delete/commit/push.
- Preserve all existing work.

## Required deliverables

1. Complete isolated prototype source.
2. README with exact preview steps and technical prerequisites.
3. Component/page structure and brief architecture rationale.
4. State model for workflow statuses and review gates.
5. Accessibility and responsive checklist.
6. Known limitations and checks actually executed.
7. Self-evaluation using the weighted rubric below.

## Evaluation rubric

| Criterion | Weight |
|---|---:|
| Visual quality | 25% |
| Workflow usability | 25% |
| Responsive behavior | 15% |
| Accessibility | 15% |
| Component quality | 10% |
| Performance | 10% |

Score each 1–5 with concrete evidence. Do not present self-scores as independent benchmarks. State confidence and list any trade-offs.

## Final response

Report exact files, preview instructions, implemented interactions, technical structure, checks run, limitations, weighted score and confidence. Explicitly state that this prototype does not authorize P1 implementation or production integration.
