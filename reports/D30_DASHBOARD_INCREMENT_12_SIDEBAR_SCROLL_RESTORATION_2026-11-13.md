# D30 — Dashboard Increment 12: Sidebar Scroll Restoration
Date: 2026-11-13

## User-reported issue
The sidebar scrollbar was visually hidden, but sidebar navigation could not be scrolled on desktop.

## Diagnosis
The base desktop .sidebar is fixed to the viewport and uses a flex-column layout, but it did not have overflow-y:auto. The previous scrollbar-hiding rules only suppressed scrollbar chrome; they did not enable scrolling. The explicit overflow-y:auto had only been applied inside the mobile media query, so desktop did not receive a scroll container.

## Change
Updated dashboard/src/styles.css:
- Enabled overflow-y:auto on the sidebar at all viewport widths.
- Added overscroll-behavior:contain to keep sidebar scroll chaining contained.
- Set the sidebar navigation to lex:0 0 auto so its full content contributes to the sidebar's scrollable height.
- Gave the spacer a small minimum height so the bottom controls remain separated when the sidebar is full.
- Preserved the existing hidden-scrollbar rules. Scrollbar chrome remains invisible; scrolling is intended to work via wheel, trackpad, touch, and keyboard focus.

## Verification
- dashboard: npm run build — PASS (TypeScript compile + Vite build; 1741 modules).
- dashboard: npm run typecheck — PASS.
- git diff --check — PASS (no output; command completed successfully).
- No backend, database, workflow, review, approval, or publishing behavior changed.

## Limitations
- The desktop scroll interaction and visual appearance were not manually browser-tested in this increment. Please verify the sidebar with the mouse wheel/trackpad in the open dashboard; if the issue persists, capture the viewport and we can inspect the exact rendered layout.
- No commit, push, or deployment performed.
