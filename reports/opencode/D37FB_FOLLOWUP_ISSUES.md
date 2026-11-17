# D37-FB Follow-Up Issue List

**Date:** 2026-11-13
**Source:** D37-FB runtime acceptance (`reports/opencode/D37FB_STUDIO_WORKSPACE_RUNTIME_ACCEPTANCE_2026-11-13.md`) and its operational closure.
**Status:** OPEN — documented only; intentionally **not implemented** in this task.

---

## F-1. Atomic `createStudioVersion` persistence

- **File:** `dashboard/src/studioPersistence.ts` (`createStudioVersion`)
- **Issue:** the draft row (with `currentVersionId` → the new version) and the version row are written in **two separate IndexedDB transactions**. A crash between the two commits leaves `currentVersionId` pointing at a version that was never stored — an orphaned current-version reference.
- **Risk:** low (local single-user IndexedDB, tiny window), but it is the only non-atomic write in the persistence layer.
- **Suggested fix (when authorized):** fold both puts into one `transaction([DRAFTS, VERSIONS], 'readwrite')` and commit atomically via `transactionDone`.

## F-2. Empty-workspace workbench clearing

- **File:** `dashboard/src/pages/studio.tsx` (`StudioWorkspaceNavigator.selectWorkspace` / `StudioWorkbench`)
- **Issue:** switching to a workspace that has **no** Shorts does not dispatch any event to the workbench, so the workbench keeps displaying the previously selected Short while the navigator shows an empty Short selector. Observed in S11 (`extraFinding`): 5 beats and the prior inspector state remained visible.
- **Risk:** cosmetic/UX ambiguity today (no cross-draft write observed — the workbench remains consistent with what it displays), but a user could edit while the navigator visually indicates an empty workspace.
- **Suggested fix (when authorized):** have the navigator also dispatch a workspace-selection event (including the empty case) and have the workbench clear/reset to a defined empty state instead of holding the stale Short.

## F-3. Missing favicon

- **File:** `dashboard/index.html` (or `dashboard/public/`)
- **Issue:** every page load emits a benign `favicon.ico` HTTP 404 (9 occurrences across the acceptance run's reloads). No functional impact; it is the only console/network entry in an otherwise clean sweep.
- **Suggested fix (when authorized):** ship a favicon (`public/favicon.ico` + `<link rel="icon">`) or add a Vite middleware/`public/` fallback to silence the 404.

---

*Reminder: these items require owner authorization before implementation; none blocks the accepted D37-FA/D37-FB state.*
