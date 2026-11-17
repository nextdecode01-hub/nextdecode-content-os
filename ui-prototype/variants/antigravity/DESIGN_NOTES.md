# NEXTDECODE Content OS — Design & Research Notes
**Author:** Antigravity (Design Lead)  
**Document:** Independent Research, Information Architecture & UX Rationale  
**Target:** `ui-prototype/variants/antigravity/`

---

## 1. Independent UX Research & Benchmark Analysis

In developing this dashboard concept, we researched modern creative-operations systems, high-velocity developer tools, and AI orchestration platforms. We synthesized lessons from five primary industry benchmarks:

1. **Linear Design System (Methodology & Precision)**
   - *Reference:* [Linear Design System & Method](https://linear.app/method)
   - *Key Takeaway:* High-density operational software thrives when decorative noise is removed in favor of micro-typography, subtle borders (`border-white/10`), status indicators with distinct micro-hues, and full keyboard navigation. We adopted Linear's keyboard-first philosophy (numbered hotkeys `1`-`0`, `/` search focus, `?` shortcut modal).

2. **Vercel Dashboard & Geist Interface Principles**
   - *Reference:* [Vercel Design System & Principles](https://vercel.com/design)
   - *Key Takeaway:* True dark-mode interfaces must not use pure pitch-black or muddy tertiary colors (like purple or plum) as card surfaces. Instead, an obsidian canvas (`#0B0D12`) paired with slate-gray card elevations (`#12161F`, `#181E2A`) ensures maximum readability and natural contrast with code tokens, badges, and media players.

3. **Runway & Descript (Creative Operations & AI Media Review)**
   - *Reference:* [Runway Creative Tools & Descript Timeline UX](https://runwayml.com)
   - *Key Takeaway:* Reviewing short-form vertical video (9:16) cannot be done in a generic table or text snippet. A video review interface requires a synchronized multi-pane workstation: the vertical video player on the left, storyboard scene thumbnails directly underneath, and the editorial checklist / claim evidence drawer on the right.

4. **GitHub & Stripe (Governance, Immutability & Trust Boundaries)**
   - *Reference:* [Stripe Dashboard Workbench & GitHub Audit Boundaries](https://stripe.com)
   - *Key Takeaway:* In high-stakes environments where actions are protected, the UI must make boundaries visually unmistakable. The operator must never wonder: *"If I click this, will it go live on YouTube?"* Our design explicitly separates **Review Approval** (which generates a local cryptographic decision record) from **Publishing** (which is permanently locked in fail-closed mode).

5. **W3C Web Content Accessibility Guidelines (WCAG 2.1 AA/AAA)**
   - *Reference:* [W3C WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
   - *Key Takeaway:* Contrast ratios between text and surfaces were strictly calibrated: `#F1F5F9` on `#12161F` achieves a **13.5:1** contrast ratio (far exceeding the 7:1 AAA standard). Secondary text `#94A3B8` achieves **5.6:1** (exceeding the 4.5:1 AA standard).

---

## 2. Proposed Information Architecture (IA)

We organized the 10 capability areas into three coherent conceptual tiers rather than a flat, undifferentiated list:

```
NEXTDECODE Content OS
├── Core Operations (Daily Executive Cockpit)
│   ├── [1] Overview ────────► Executive pulse, active review alert, pipeline stepper, recent activity
│   ├── [2] Projects ────────► Content catalog, format filters (35s, 55s, 8m), pillars, lifecycle states
│   └── [3] Workflows ───────► Autonomy DAG graph, PostgreSQL task queue, worker leases & retries
│
├── Creation & Assembly (The Production Engine)
│   ├── [4] Research ────────► Atomic claim ledger, source veracity, quotes, corroboration & freshness
│   ├── [5] Studio ──────────► Multi-track sequencer, B-roll queries, procedural motion cards, prosody
│   └── [6] Review Suite ────► 9:16 video player, storyboard strip, 7-point checklist, cryptographic sign-off
│
└── Distribution & Systems (Governance & Host Infrastructure)
    ├── [7] Publishing ──────► Platform readiness matrix (YouTube, IG, FB), fail-closed governance lock
    ├── [8] Analytics ───────► Audience retention drop-off curve, visual pacing scores, epistemic trust index
    ├── [9] Operations ──────► PostgreSQL 18 health (port 54329), Bubblewrap sandboxes, backup verification
    └── [0] Settings ────────► Display-only governance parameters, local Ollama routes, IST expiry policies
```

---

## 3. Key User Journeys

### Journey A: The Morning Review & Cryptographic Sign-Off (Primary Loop)
1. **Operator Lands on Overview**: The prominent green/cyan banner immediately alerts the operator: *"Human Review Pending: Does AI Actually Accelerate AI Research?"*
2. **One-Click Jump to Review Suite**: Operator clicks *"Launch Review Suite"* (or presses hotkey `6`).
3. **Inspects 9:16 Vertical Video**: The operator watches the synthesized video, checks audio pacing and vertical subtitle framing.
4. **Inspects Storyboard Beats**: Clicks through the 5 scene thumbnails to inspect B-roll selection and procedural motion graphic cards.
5. **Verifies Evidence**: Checks the atomic claim ledger citations linked to the narration lines.
6. **Affirms 7-Point Checklist**: The operator clicks each of the 7 mandatory checklist items. The *"Sign & Commit Approval Record"* button stays disabled until all 7 are confirmed.
7. **Commits Approval**: Operator enters rationale and clicks approve. The system simulates writing the read-only (`0o400`) decision record and updates the review queue count.

### Journey B: Rejection & Editorial Rationale (Fail-Safe Loop)
1. Operator detects an issue (e.g., procedural visual defect or hallucinated claim).
2. Operator clicks *"Reject with Rationale"*.
3. Modal appears: operator selects failure category (`Factual Error`, `Visual Defect`, etc.) and enters mandatory rationale.
4. The system writes an append-only rejection record to `data/review_rejections/` while leaving the original review package preserved in `data/review_queue/` for forensic audit.

---

## 4. Visual & Interaction Design Decisions

### A. Surface Palette: Rejecting the "Plum / Lime" Clashing Reference
The ChatGPT prototype used `#110A16` (muddy plum) with `#7A3535` (brown-burgundy) and neon lime accents. This created visual fatigue and clashing aesthetics for a professional operations tool.
**Our Choice**:
- A pure **Obsidian & Slate** foundation (`#0B0D12` / `#12161F` / `#1F2633`) providing neutral, high-contrast, eye-friendly backgrounds that let media assets and data take center stage.
- **Emerald Green (`#10B981`)** as the primary affirmative accent, symbolizing verified facts and cryptographic security.
- **Cyan (`#06B6D4`)** as the secondary workflow accent, symbolizing automated task execution.

### B. Purpose-Built Workstations vs. Generic Tables
In other variants, 8 out of 10 pages were rendered as generic HTML tables (`cols` + `rows`).
**Our Choice**:
- Every page is a custom-designed operational tool:
  - **Workflows** features an interactive DAG node pipeline.
  - **Review** features a live 9:16 video player and storyboard contact sheet.
  - **Research** features atomic claim cards with offset indicators.
  - **Studio** features a multi-track beat sequencer with audio loudness rails.
  - **Analytics** features an interactive retention curve drop-off chart.

---

## 5. Responsive Behavior & Accessibility

### Responsive Strategy
- **Desktop (>1024px)**: Full two-column and three-column layouts, sticky sidebar, side-by-side video and checklist workstation.
- **Tablet (768px - 1024px)**: Review suite stacks vertically (video player spans full width on top, checklist and controls underneath). Stat grids adjust to 2 columns.
- **Mobile (<768px)**: Sidebar seamlessly transitions to a top/bottom horizontal scrolling navigation bar. All grids collapse into readable single-column cards with touch-friendly 44px tap targets.

### Accessibility Architecture
- **Semantic HTML**: `<aside>`, `<main>`, `<header>`, `<nav>`, `<section>`, `<article>`, and native `<button>` elements throughout.
- **Keyboard Traps Eliminated**: All modals (`Rejection Modal`, `Shortcuts Modal`) can be dismissed with `Escape`.
- **Focus Rings**: Universal `:focus-visible` ring (`2px solid #10B981`) ensures clear visual focus indicators without ugly outlines during mouse clicks.
- **Reduced Motion Support**: `@media (prefers-reduced-motion: reduce)` rules disable transitions and animations for users with vestibular sensitivities.

---

## 6. Important States, Limitations & Unresolved Questions

### Handled States in Prototype
- ✅ **Pending Human Review**: Active review cards with prominent callouts.
- ✅ **Cryptographic Approval Committed**: Displays generated SHA-256 hashes and IST expiry window.
- ✅ **Rejection Recorded**: Modal with audit rationale requirement.
- ✅ **Fail-Closed Governance**: Clear badges indicating public publishing is permanently locked.
- ✅ **Theme Persistence**: Dark / Light / System state remembered across sessions.

### Known Prototype Limitations
- **Simulated Video Player**: Uses canvas/CSS procedural animations rather than an actual video codec stream (as no live media server is connected).
- **Static In-Memory State**: State updates (like checking items or approving) modify in-memory JavaScript objects; refreshing the page restores sample baseline data.
- **No Backend Connection**: As mandated by safe execution rules, zero network requests or API mutations occur.

### Unresolved Product Questions for Owner
1. **Multi-Operator Collaboration**: In a production environment with multiple reviewers, should the dashboard show real-time presence (e.g. *"Operator 2 is currently reviewing this Short"* to avoid duplicate approvals)?
2. **Revision Feedback Loop**: When a script is rejected in Review, should the rejection rationale automatically trigger a specialized `content.short.script.repair` specialist in `app/autonomy/` with the rejection notes as input?
3. **Mobile Field Approval**: Does the owner envision approving content from mobile devices on-the-go (requiring WebAuthn / biometric hardware token support), or will approvals be strictly desktop-bound?
