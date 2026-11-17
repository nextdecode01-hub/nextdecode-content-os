# NEXTDECODE Control Center — ChatGPT Variant

**Status:** Updated dark-first sample dashboard prototype  
**Variant:** chatgpt  
**Entry point:** `index.html`

## Preview

Open `index.html` directly in a modern browser. It is dependency-free and requires no build step or package installation.

## Visual direction

- Dark by default, matching the supplied ChatGPT Appearance reference.
- Background: `#110A16`; surface: `#17111E`; foreground: `#92A2B9`; accent: `#7A3535`.
- Deep plum/charcoal surfaces, muted blue-grey text, restrained burgundy accent and subtle borders.
- Low visual noise, compact operational cards and readable tables.
- Global appearance selector in the top bar: Dark / Light / System.
- Theme applies across the dashboard pages and is retained in local browser storage where available.

## Included surfaces

Overview, Projects, Workflows, Research, Studio, Review & Approvals, Publishing, Analytics, Operations and Settings.

Navigation and table filtering are interactive. Publishing is display-only. Theme mode is global and remains available while navigating pages.

## Safety and scope

- All data is illustrative; no real project or account data is loaded.
- No backend, API, database, provider or analytics connection.
- No generation, approval, export, upload or publishing action is implemented.
- No credentials, package dependencies or external network resources are used.
- This prototype does not implement P1 production functionality or alter P0/P1 decisions.

## Known limitations

- This is a visual/interaction prototype, not a production frontend architecture.
- Table filters operate only on rows already rendered in the page.
- Sample performance bars and KPI values are illustrative.
- Authentication, authorization, audit trails, server state, persistence and workflow transitions are intentionally absent.
- Accessibility has been considered in semantic navigation, focus visibility and reduced-motion handling, but a full keyboard/screen-reader audit has not yet been performed.
