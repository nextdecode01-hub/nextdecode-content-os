# NEXTDECODE Sample Dashboard — Parallel Agent Assignments

**Date:** 2026-11-13  
**Status:** Ready for manual dispatch by the owner  
**Purpose:** Create competing sample Control Center prototypes and independently evaluate them.

## Shared brief

Build an isolated sample dashboard for NEXTDECODE Content OS. The goal is to compare product thinking and interaction quality, not to start the production P1 dashboard.

Product context:
- Brand: NEXTDECODE — “Decode what comes next.”
- Product: content operations workspace for research, scripts, production, quality, human review, distribution and analytics.
- Existing Shorts Studio remains the specialist production engine.
- P0 canonical contracts and existing architecture remain authoritative.
- P1 broad Control Center implementation remains gated by P0 closure/readiness and formal owner authorization.
- Local-first, free-first, target spend ₹0.
- Human approval before protected actions; public publishing disabled by default.

Required areas:
1. Overview
2. Projects
3. Workflows
4. Research
5. Studio
6. Review & Approvals
7. Publishing (display-only)
8. Analytics
9. Operations
10. Settings

Every prototype must use illustrative data only. Show useful empty/loading/error/blocked states, responsive behavior, realistic dense tables and clear workflow states. No backend/API/database/provider connection. No credentials, external calls, generation, approvals, export, upload, publishing or production state mutation.

## Assignment 1 — Antigravity: independent product/UI prototype

**Priority:** Lead visual and interaction design  
**Output directory:** `ui-prototype/variants/antigravity/`

Create a distinct, polished dashboard concept. Do not copy the ChatGPT variant or overwrite the original `ui-prototype/index.html`.

Explore a coherent design system, navigation hierarchy, page layouts, review workflow, dense operational tables, responsive behavior, and meaningful states. Include the 10 required areas. Keep publishing display-only and make human review/approval boundaries visually unambiguous.

Preferred candidate for comparison: React + TypeScript + Vite with a modular SPA structure. However, do not install dependencies or modify project-root manifests. If the dependencies are not already available, produce source-only React files or a dependency-free HTML/CSS/JS prototype and explain preview requirements.

Deliver:
- all source under the specified output directory;
- README with exact preview instructions and limitations;
- route/page inventory and component inventory;
- design rationale and known accessibility gaps;
- no production integration.

## Assignment 2 — Qoder: independent implementation-oriented prototype

**Priority:** Component quality and practical implementation  
**Output directory:** `ui-prototype/variants/qoder/`

Build a separate sample dashboard variant, not a copy of Antigravity's work. Focus on modular component structure, predictable state, clean responsive layouts, accessible interactions and implementation feasibility.

Required areas and safety constraints are identical to the shared brief. Keep all files inside the Qoder variant directory. Do not install packages, modify production files, change project-root manifests, or connect APIs.

Deliver:
- isolated source and README;
- component/route structure;
- sample data model;
- basic interaction notes;
- accessibility and responsive checklist;
- preview/build prerequisites.

## Assignment 3 — Copilot: independent QA and accessibility review

**Mode:** Read-only review; do not edit prototype files.

Review:
- `ui-prototype/index.html` (original);
- `ui-prototype/variants/chatgpt/`;
- `ui-prototype/variants/antigravity/` when available;
- `ui-prototype/variants/qoder/` when available.

Check navigation, keyboard operation, focus visibility, semantic structure, responsive breakpoints, text contrast, table overflow, empty/loading/error/blocked states, misleading actions, browser console errors and maintainability.

Deliver a prioritized defect list with exact file/line references, severity, reproduction steps, expected behavior and recommended fix. Distinguish verified defects from manual-review recommendations. Do not change files.

## Assignment 4 — DeepSeek: independent product and UX challenge

**Mode:** Read-only critique; do not edit prototype files.

Challenge the concepts against actual NEXTDECODE workflows. Check:
- whether the Overview answers “what needs attention now?”;
- whether research → brief → script → production → quality/rights → human review → authorization → distribution is understandable;
- whether the dashboard overemphasizes vanity metrics;
- whether blocked, pending, failed and unknown states are distinct;
- whether review is version-specific and human-controlled;
- whether Publishing could be mistaken for a live publishing control;
- whether navigation can grow without becoming a crowded admin template;
- whether each screen earns its place in the product.

Deliver a concise UX critique, missing workflow states, unnecessary features, information architecture recommendations and a scored comparison. No edits.

## Global rules

- Preserve all existing files and dirty repository state.
- Do not edit `ui-prototype/index.html` or the ChatGPT variant.
- Do not touch production source, API, schema, migrations, canonical P0/P1 documents or configuration.
- No dependency installation, paid service, live provider probe, deployment, upload or publishing.
- No commit, push, reset, stash, clean or deletion.
- Do not use Kilo.
- Keep all new prototype files in the assigned directory.
- Cite exact files and line numbers in reviews.
- State which checks were actually run; never claim browser testing or accessibility certification without evidence.

## Shared evaluation scorecard

| Criterion | Weight | What to assess |
|---|---:|---|
| Visual quality | 25% | Visual hierarchy, coherence, brand fit, craft and information density |
| Workflow usability | 25% | Navigation, task clarity, review flow, status comprehension and next actions |
| Responsive behavior | 15% | Desktop/tablet/mobile layout and usable overflow behavior |
| Accessibility | 15% | Semantic HTML, keyboard access, focus, contrast, labels and reduced motion |
| Component quality | 10% | Reuse, consistency, maintainability and state organization |
| Performance | 10% | Lightweight rendering, dependencies, asset weight and responsiveness |

Score 1–5 per criterion and calculate the weighted score. Scores are reviewer judgments, not benchmark measurements. Add confidence and evidence for each score.

## Final comparison report

After all variants are ready, produce:
1. Side-by-side score table.
2. Best elements worth combining.
3. Critical usability/accessibility defects.
4. Recommended visual direction.
5. Recommended component and route architecture.
6. Remaining gaps before a production implementation could even be considered.
7. Explicit statement that prototype selection does not authorize P1 implementation.

Do not select a winner solely by visual appeal. Workflow usability, accessibility and governance clarity are equally important.


## Assignment 5 — Hermes: product architecture translated into UX

**Prompt file:** `ui-prototype/variants/hermes/TASK_PROMPT.md`  
**Output directory:** `ui-prototype/variants/hermes/`

Build an independent dark-first sample dashboard from the actual NEXTDECODE product and governance context. Test the ability to translate the domain/workflow model into usable information architecture, state visibility and human-review surfaces. Do not copy other variants. Keep all work isolated. Deliver source, README, navigation map, component inventory, limitations and evidence-based self-score.

## Assignment 6 — OpenCode: engineering-grade prototype

**Prompt file:** `ui-prototype/variants/opencode/TASK_PROMPT.md`  
**Output directory:** `ui-prototype/variants/opencode/`

Build an independent dark-first dashboard prototype with strong modular structure, coherent workflow states, accessible interactions and a global Dark / Light / System selector. Prefer existing React/TypeScript/Vite capability only if available without installs or root manifest changes; otherwise deliver a dependency-free prototype. No backend, API, production changes or governance bypass.

Both variants are evaluated using the same scorecard as Antigravity and Qoder. Hermes and OpenCode must work independently and must not edit each other's files.
