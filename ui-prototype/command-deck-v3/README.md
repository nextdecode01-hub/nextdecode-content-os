# NEXTDECODE OS — Final Product Prototype

This is the expanded final prototype built in the existing command-deck-v3 directory. The original V3 state is preserved as index.pre-final.html.

## Run
From WSL:
```bash
cd /home/demon/shorts_studio/ui-prototype/command-deck-v3
python3 -m http.server 9022 --bind 0.0.0.0
```
Open: http://127.0.0.1:9022/#/home

## Product identity
- NEXTDECODE OS — the unified content operating system.
- Engineering Command Center — the engineering control-plane workspace.
- Shorts Studio — the existing specialist short-form production engine; integrated, not replaced.
- Creator Workspace — the entry point to the multi-format creation network.

## Navigation
- Home: Home, Portfolio.
- Create: Creator Workspace, Content Graph, Content Planner, Research Desk, Brand & Knowledge, Content Library, Shorts Studio, Long-form Studio, Social & Carousel, X & Threads, Blog Studio, Newsletter Studio, Podcast & Audio, Campaign Packages.
- Orchestrate: Agent Command, Workflow Canvas, Execution Monitor, Schedules & Triggers, Integrations & Providers.
- Govern: Review & Decisions, Quality & Rights, Evidence & Lineage, Incidents & Recovery, Distribution & Release, Governance & Access.
- Engineering: Engineering Command Center, Execution Queue, WP1–WP6 Workstreams, Database & Migrations, Testing & Acceptance, Technical Operations.
- Intelligence: Analytics & Performance, Audience Insights, Feedback & Learning, Improvement Proposals.
- System: Notifications, Workspace Settings.

39 navigation routes; 40 page sections including the preserved legacy Studio surface.

## Product source alignment
- NEXTDECODE_Master_Blueprint_2.0.md
- System Architecture Pipeline Parts 1–8
- Shared Intelligence Contracts 01–12
- P1 Product Expansion planning package
- docs/CONTENT_STRATEGY.md

Seven major formats are surfaced as distinct studios: short video, long video, social/carousel, X/thread, blog/article, newsletter and podcast/audio. Campaign packages coordinate multiple outputs; they are not an eighth media format. Distribution destinations include YouTube, Instagram, Facebook, X, LinkedIn, website, newsletter and podcast feeds.

Editorial series: AI You Can Use, Hype Check, What Changed, How It Works, Startup Breakdown.

## Interaction
- 39 navigation routes with active state and URL hash routing.
- Creator Workspace format cards navigate to specialist studio routes.
- Content Graph nodes navigate to connected workspaces.
- Search button and Ctrl/Cmd+K open local prototype navigation search.
- Home creative brief accepts demo input and opens Research Desk.
- Record drawers, queue filters, notifications and protected-action notices are demo interactions.
- Desktop sidebar keeps labels beside icons; mobile sidebar collapses behind a menu.
- Scrollbars are visually hidden while native scrolling remains enabled.
- Dimensional CSS brand emblem respects reduced-motion preferences.

## Maturity and authority
The UI distinguishes existing specialist modules, partial capabilities, planned P1 work and design-only concepts. P1 documentation is planning material, not implementation authorization.
- Existing Shorts Studio and research/evidence modules are represented as existing foundations.
- Long-form is marked partial.
- Unified multiformat studios, content graph experience, staged learning and other P1 capabilities are marked planned/design.
- Local demo agent identities are not canonical WP3 worker registrations.
- Local workflows and sample runs do not replace canonical WP2/WP4 records.
- Engineering Command Center displays WP1–WP6 as canonical workstreams.
- Human review approval remains separate from protected-action authorization.
- external_actions_allowed=false; public publishing is disabled.
- No database, API, provider, live analytics, agent dispatch, schedule, upload, approval mutation or publishing action is connected.
- No commits, pushes, deployments or production changes were made.

## Files
- index.html — current final prototype.
- index.pre-final.html — preserved pre-final V3.
- build_final.py and patch_*.py — build/patch scripts.
- verify_final.py — structural verification helper.