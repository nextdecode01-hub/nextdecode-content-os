# NEXTDECODE Hybrid Control Center

**Status:** Isolated sample prototype  
**Entry point:** `index.html`

## Preview
Open `index.html` directly in a modern browser. No build step or dependencies are required.

## Product direction
A single connected Content OS concept combining:
- Control Center: operational overview, priorities, review queue and system pulse.
- Creator Workspace: idea-first entry point and quick-start creative actions.
- Workflow Studio: interactive idea-to-review pipeline with stage explanations.
- Insights Console: illustrative performance metrics and learning opportunities.

## Included areas
Overview, Projects, Workflows, Research, Studio, Review & Approvals, Publishing, Analytics, Operations and Settings.

## Interactions
- Sidebar navigation across dashboard sections.
- Idea prompt and quick-start chips with sample-only confirmation.
- Selectable workflow stages with contextual explanations.
- New-project entry point with a sample-only modal.
- Table views with text and status filtering.
- Global search for dashboard sections.
- Notification feedback.
- Global Dark / Light / System appearance selector. Dark is default; preference is stored locally where available.

## Visual reference
The dark-first palette references the owner's supplied ChatGPT appearance preference:
- Background: `#110A16`
- Surface: `#17111E`
- Foreground: `#92A2B9`
- Accent: `#7A3535`

The design combines plum/charcoal surfaces and restrained burgundy accents with a more prominent creator entry point and workflow visualization.

## Safety and governance
- All records and metrics are illustrative sample data.
- No API, backend, database, provider, analytics or account connection.
- No real project creation, content generation, approval, export, upload or publishing.
- Publishing is display-only; external actions are unavailable.
- Existing P0 architecture, contracts and P1 authorization boundaries are unchanged.
- Prototype selection does not authorize production dashboard implementation.

## Limitations and validation
- This is a dependency-free visual/interaction prototype, not production frontend architecture.
- Data is static; filters operate only on rows rendered in the browser.
- The creator prompt only displays a demo confirmation; it does not invoke an AI model.
- Project/run/evidence details are summary-level, not fully implemented drill-downs.
- Authentication, permissions, audit persistence, live telemetry, server state and real workflow transitions are absent.
- Semantic navigation, labelled controls, visible focus and reduced-motion styling are included. Full screen-reader/accessibility testing has not been performed.
- File writes were confirmed. Browser rendering and cross-browser tests have not yet been performed.

## Evaluation
Shared rubric: visual quality 25%, workflow usability 25%, responsive behavior 15%, accessibility 15%, component quality 10%, performance 10%.
