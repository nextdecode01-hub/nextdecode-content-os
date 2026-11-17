# Hermes — Independent NEXTDECODE Dashboard Prototype Challenge

You are being evaluated on whether you can translate the existing NEXTDECODE Content OS architecture and product constraints into a coherent, usable dashboard prototype — not merely produce a pretty mockup.

## Your assignment

Create an independent sample Control Center dashboard prototype under:

`ui-prototype/variants/hermes/`

You own the product reasoning and information architecture for this variant. Do not copy the ChatGPT, Antigravity, Qoder or OpenCode variants. Make your own design decisions and explain them.

## Required product surfaces

Build a coherent connected experience for:
1. Overview — priorities, risks, work requiring attention, operational health.
2. Projects — portfolio and project-level status.
3. Workflows — run state, queues, retries, blocked/failed states.
4. Research — source/evidence quality, claims and research packages.
5. Studio — Shorts editorial and production stages.
6. Review & Approvals — version-specific human review and decision history.
7. Publishing — readiness and destination status only; no live publishing controls.
8. Analytics — useful learning signals, not vanity metrics alone.
9. Operations — worker health, incidents, events and recovery visibility.
10. Settings — workspace preferences and safe configuration surfaces.

## Visual direction

- Dark UI by default, inspired by ChatGPT's current dark interface: deep neutral charcoal, clear text contrast, restrained accent color, calm surfaces and low visual noise.
- Avoid a white dashboard or bright white cards.
- Include a persistent global appearance selector: Dark / Light / System. Dark must be the default. The selector must apply consistently across every page/surface.
- The user should be able to see the current workspace, active section, sample-data warning and notifications.
- Design for desktop first, but fully usable on tablet and mobile.
- Avoid overdecorated gradients, oversized cards, excessive badges and generic admin-template styling.

## Architecture and governance context

- NEXTDECODE is a content operations system for AI, technology, startups and future-focused content.
- Existing Shorts Studio remains the specialist production engine.
- P0 canonical contracts, architecture and governance remain authoritative.
- Broad P1 dashboard implementation is still gated by P0 closure/readiness and formal owner authorization.
- This task authorizes only an isolated sample prototype.
- Human approval remains mandatory for protected actions. Public publishing is disabled by default.

## Technical boundaries

- Keep every created/modified file inside `ui-prototype/variants/hermes/`.
- Do not modify the existing prototype, another agent's variant, project-root files, API, production code, canonical documentation, schemas, migrations or configuration.
- No dependency installation, package manager changes, external API calls, provider keys, backend/database integration, deployment, uploads or publishing.
- Prefer React + TypeScript + Vite only if all required dependencies/tooling are already present and can be used without modifying root manifests. Otherwise deliver dependency-free HTML/CSS/JS or source-only React with exact preview prerequisites.
- Use sample data only.
- Make navigation and safe local interactions work. Do not implement real generation, approval, export, upload or publish actions.
- Include empty, loading, error, blocked and permission-limited states where they add meaning.
- Make keyboard focus visible and controls labelled.

## Required deliverables

1. Working isolated prototype source.
2. README with exact preview instructions.
3. Short product rationale and navigation map.
4. Component/page inventory and sample data assumptions.
5. Accessibility and responsive checklist.
6. Known gaps and exact checks actually executed.
7. Self-score using the rubric below, with evidence and confidence.

## Evaluation rubric

| Criterion | Weight |
|---|---:|
| Visual quality | 25% |
| Workflow usability | 25% |
| Responsive behavior | 15% |
| Accessibility | 15% |
| Component quality | 10% |
| Performance | 10% |

Score 1–5 per criterion. Scores are reasoned assessments, not benchmarks. Explain trade-offs and provide evidence. Do not claim browser testing or accessibility certification unless actually performed.

## Final response format

- Files created
- Preview instructions
- Key design decisions
- Best workflow decisions and why
- Limitations
- Tests/checks actually run
- Weighted score and confidence
- Any unresolved questions

Do not change canonical project decisions. Prototype completion does not authorize P1 implementation.
