# D38 — Dashboard/backend integration batch 1
Date: 2026-11-14
Status: IMPLEMENTED LOCALLY · FRONTEND BUILD VERIFIED · LIVE API SMOKE TEST NOT RUN

## Scope
Improve the existing NEXTDECODE Content OS dashboard's API boundary and task inspection without changing backend routes, persistence schema, canonical WP contracts, provider activation, publishing, deployment or ECC.

## Changes
- Reworked `dashboard/src/api.ts` into a shared request boundary.
  - Handles network failures with an actionable local-runtime message.
  - Parses JSON responses consistently and reports empty/invalid JSON separately.
  - Uses structured `ApiError` with HTTP status, endpoint and optional request ID.
  - Safely extracts bounded JSON error details; does not echo arbitrary HTML/raw server bodies.
  - Preserves review endpoint's existing 404-as-no-pending-review behavior.
  - Keeps auth responsibility at the existing Vite proxy; no browser credential handling added.
- Improved `dashboard/src/components.tsx` error display with HTTP/endpoint/request-ID context when available, without exposing credentials.
- Improved `dashboard/src/pages/task.tsx`.
  - Uses abort-signal-aware React Query task fetch.
  - Presents task result through the existing sanitized event-detail renderer rather than rendering raw result JSON.
  - Keeps event history read-only and preserves approval/publishing boundary messaging.

## Validation
- `npm run typecheck`: PASS.
- `npm run build`: PASS; Vite transformed 1,745 modules and produced production assets.
- `git diff --check`: PASS.
- Live API/auth smoke test: NOT RUN. A local API endpoint probe command was rejected by the remote shell command guard before execution; no live API behavior is claimed as verified.
- No backend/Python tests were run in this batch.

## Explicitly unchanged
- No backend route, schema, DDL, ORM or migration changes.
- No canonical WP2–WP6 bridge implementation.
- No agent dispatch or provider calls.
- No external generation, upload, approval mutation, publishing or deployment.
- No Git commit, push, reset, clean, stash or destructive operation.
- Existing dirty and untracked user work was preserved.

## Remaining verification
1. Verify authenticated endpoint responses against a running local API and the configured Vite proxy.
2. Browser-level dashboard walkthrough for health/task/error/loading states.
3. Continue next bounded integration increment only after inspecting the live endpoint behavior and current owner/contract gates.
