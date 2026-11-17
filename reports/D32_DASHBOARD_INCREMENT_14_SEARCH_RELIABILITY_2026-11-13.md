# D32 — Dashboard Increment 14: Search Reliability
Date: 2026-11-13

## Finding
The global workspace search combined task and capability queries. If either API request failed, the UI could fall through to the generic "No matching records" empty state, which incorrectly presented a service failure as a valid zero-result search.

## Change
Updated dashboard/src/shell.tsx:
- Added a dedicated error branch after the loading state and before the no-results branch.
- Search API failures now display "Search service unavailable", the returned error message, and a local API troubleshooting hint.
- The error uses role="alert" so assistive technology is notified.
- Existing empty state remains reserved for successful queries with zero matching records.
- No backend behavior or search permissions changed.

## Verification
- dashboard npm run build — PASS; TypeScript compile + Vite build, 1741 modules.
- dashboard npm run typecheck — PASS.
- git diff --check — PASS (completed in the same successful command chain).
- Existing search behavior remains read-only.

## Not verified
- No browser-driven API failure simulation or route smoke test completed in this increment.
- No screen-reader or visual browser QA.
- No commit, push, or deployment.
