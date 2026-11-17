# D-22 — Dashboard Increment 04

**Date:** 2026-11-13  
**Disposition:** PASS — home KPI refinement and evidence-based Content Workspace.

## Home command center

Replaced the five mixed headline metrics with exactly four operational KPIs:
1. Total tasks — all persisted local autonomy task records.
2. In progress — running tasks, with active worker count in the explanatory detail.
3. Waiting — queued tasks awaiting a worker.
4. Needs attention — failed plus blocked tasks, explicitly broken down.

Added four short definitions below the KPI row so users understand what each number means and what it does not prove. Worker availability and capability count remain in the workforce supporting panel rather than competing with the four primary numbers.

## Content Workspace

Replaced the Content Hub placeholder with a live editorial workspace:
- NEXTDECODE editorial promise and five series from `docs/CONTENT_STRATEGY.md`.
- Six pipeline stages mapped from the Shorts Studio Pipeline Contract.
- Stage maturity labels distinguish partial implementation, connected read-only review, and not-connected domains.
- Live records link to existing legacy jobs, pending review package and autonomy tasks.
- Explicitly states that these services are not joined by a canonical Content ID / Content Graph yet.
- Editorial quality principles preserve source/evidence/claim distinctions, rights checks, artifact-bound approvals and real analytics requirements.

## Verification

- `npm run build`: PASS — TypeScript and Vite production build completed (1737 modules transformed).
- No backend routes, database schema, API mutation or publishing controls were added.
- No fake content ideas, content calendar entries, research packages or analytics were created.

## Known boundaries

The Content Graph remains a target architecture rather than an implemented dashboard API. Research, content identity, calendar, asset rights and distribution analytics are not presented as live data. The Content Workspace is an evidence-based integration map and operational overview until canonical read services are authorized and implemented.
