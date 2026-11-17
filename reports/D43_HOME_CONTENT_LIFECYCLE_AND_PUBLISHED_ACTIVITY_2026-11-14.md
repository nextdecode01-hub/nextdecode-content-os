# D43 — Home Content Lifecycle & Published Activity

**Date:** 2026-11-14  
**Status:** IMPLEMENTED — READ-ONLY HOME INTEGRATION  
**Scope:** Existing dashboard Home and styling only.

## Product change

Home now gives a more complete lifecycle snapshot while retaining the compact command-center layout:

1. Runtime status and running / queued / attention counts.
2. Active task and production-run activity.
3. **Production pipeline activity:** saved production-run count, completed run count, recorded stage count, recorded artifact count, and a short recent-run list.
4. **Published content activity:** an explicit platform-analytics unavailable state with a route to Analytics.
5. Queue and operator attention lists remain available below.

## Evidence and data boundaries

- Production activity is sourced from the existing authenticated `GET /production-runs` API and its persisted run-manifest summaries.
- Stage and artifact totals are sums of recorded manifest fields only. They are not estimates of pipeline progress.
- Repository inspection found no connected YouTube / Instagram audience-analytics API or publication-performance read model for Home.
- The published-content panel therefore clearly says analytics are not connected and identifies the metrics that will appear when an authorized source exists.
- No views, likes, comments, shares, subscribers, retention or watch-time values are fabricated.
- A completed production run is not represented as a published upload.

## Files changed

- `dashboard/src/pages/home.tsx`
- `dashboard/src/styles.css`
- `reports/D43_HOME_CONTENT_LIFECYCLE_AND_PUBLISHED_ACTIVITY_2026-11-14.md`

## Validation

- `npm --prefix dashboard run typecheck` — PASS.
- `npm --prefix dashboard run build` — PASS; Vite transformed 1745 modules.
- `git diff --check` — PASS.
- Python API tests were attempted but could not be collected in the system Python because `fastapi` is not installed there; the expected `.venv/bin/pytest` executable was also absent. No backend code changed, so frontend typecheck/build remain the relevant validation for this UI-only increment.

## Boundaries preserved

No API/backend, database, schema, provider connection, analytics ingestion, approval, publishing, workflow, worker, artifact-registry or canonical Studio adapter changes. No production jobs, uploads, deployment, commit or push.
