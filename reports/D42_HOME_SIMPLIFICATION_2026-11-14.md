# D42 — Home Simplification

**Date:** 2026-11-14  
**Status:** IMPLEMENTED — MINIMAL STATUS-FIRST HOME  
**Scope:** Existing Home page only; no backend/API changes.

## Product intent

Home should answer immediately: what is running, what is waiting, and what needs attention. Detailed diagnostics belong in the relevant inspection pages, not on Home.

## Removed from Home

- Decorative hero slogan/artwork and explanatory copy.
- Total task count and redundant execution-state explanations.
- Queue-health breakdown bars and database/worker telemetry panel.
- Worker roster and agent-readiness caveats.
- Long global event timeline.
- Large recent-task table.
- Multi-paragraph operational boundary cards.

## Home now contains

1. Workspace runtime status and refresh action.
2. Three counts: running tasks, queued tasks, and tasks/runs needing attention.
3. **What’s happening:** active local tasks and persisted in-progress Shorts Studio production runs, with direct Inspect links.
4. **Waiting in queue:** up to five queued tasks.
5. **Needs attention:** failed/blocked tasks and failed production runs, with Inspect links.
6. One short note clarifying that task completion is not approval or publishing.

All displayed records come from existing API responses. No pipeline stages or task activity are inferred or fabricated. Production runs and autonomy tasks remain separately identifiable.

## Validation

- `npm --prefix dashboard run typecheck` — PASS.
- `npm --prefix dashboard run build` — PASS; 1745 modules transformed.
- `git diff --check` — PASS.

## Boundaries

No API, backend, database, schema, provider, approval, publishing, or governance changes. No deployment or Git operations. Existing dashboard architecture and other pages are preserved.
