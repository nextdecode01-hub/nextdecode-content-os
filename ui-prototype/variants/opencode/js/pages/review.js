/* review.js — Review & Approvals.
   Shows the exact version under review (video/metadata SHA-256 bindings),
   evidence / rights / quality state, pending decisions and decision history.

   GOVERNANCE BOUNDARY (mock-only):
   - Decisions can NEVER be recorded from this prototype. The dialog exists to
     demonstrate the required fields (attributable reviewer label per D-09,
     outcome, note) and always ends with "no decision was recorded".
   - Real approvals happen through the local approval CLI against the immutable
     decision-record format. */

import { el } from "../dom.js";
import { statusInfo } from "../status.js";
import {
  reviews, projects, NOW_MS,
} from "../data.js";
import { store } from "../store.js";
import {
  pageHead, badge, banner, drawer, kv, hashChip, relTime, mockDialog,
  emptyState, chipGroup, dataTable,
} from "../components.js";
import { toast } from "../toasts.js";

function packageHeadMeta(r) {
  const p = projects.find((x) => x.id === r.project_id);
  return `${p.title} · v${r.version} · packaged ${relTime(r.created_at)}`;
}

function claimsMeter(r) {
  const c = r.claims_summary;
  const total = c.verified + c.supported + c.unverified + c.conflicting;
  const blocking = c.unverified + c.conflicting;
  return el("div", { class: "stack", style: "gap:6px" },
    el("div", { style: "display:flex; justify-content:space-between; font-size:var(--fs-sm)" },
      el("span", {}, `${c.verified + c.supported}/${total} claims verified/supported`),
      blocking ? el("span", { class: "text-danger" }, `${blocking} blocking`) : el("span", { class: "text-ok" }, "0 blocking")),
    el("div", { class: "meter__track", role: "img", "aria-label": `${c.verified + c.supported} of ${total} claims verified or supported` },
      el("div", { class: "meter__fill meter--ok", style: `width:${total ? Math.round(((c.verified + c.supported) / total) * 100) : 0}%` })));
}

function decisionRecordCard(decision) {
  return el("div", { class: "stack", style: "gap:8px" },
    el("div", { class: "stack", style: "flex-direction:row; gap:8px; align-items:center; flex-wrap:wrap" },
      badge(decision.outcome),
      el("span", { class: "text-faint", style: "font-size:var(--fs-xs)" }, `recorded ${relTime(decision.decided_at)}`)),
    kv([
      { k: "Reviewer label", v: `${decision.reviewer_label} (locally-asserted label — no identity store)` },
      { k: "Package sha256", v: hashChip(decision.package_sha256) },
      { k: "Note", v: decision.note },
    ]));
}

function reviewDrawer(r) {
  const p = projects.find((x) => x.id === r.project_id);

  const mockActions = r.status === "pending_human_review"
    ? el("div", { class: "drawer__section" },
        el("h3", {}, "Decision (mock)"),
        banner({
          tone: "danger", glyph: "lock", title: "Mock-only",
          body: "Approvals are recorded via the local approval CLI against the immutable decision record. No decision made here changes any state.",
        }),
        el("div", { style: "display:flex; gap:8px; flex-wrap:wrap" },
          el("button", {
            class: "btn btn--primary", type: "button",
            on: { click: () => openMockDecision(r) },
          }, "Record decision (mock)…"),
          r.not_approvable ? el("button", {
            class: "btn", type: "button", disabled: true, "aria-disabled": "true",
            title: "Package is draft-only — the approval gate would refuse it.",
          }, "Approve — unavailable") : null))
    : null;

  const qualityChecks = el("div", { class: "checklist" },
    [
      { label: `Visual quality: ${statusInfo(r.visual_quality_status).label}`, ok: r.visual_quality_status === "review_ready" },
      { label: `Storyboard (${r.storyboard.gate}): ${statusInfo(r.storyboard.review_status).label}`, ok: ["auto_approved", "human_approved"].includes(r.storyboard.review_status) },
      { label: `QA: ${statusInfo(r.qa.status).label}`, ok: r.qa.status === "pass" },
      { label: `Reuse rights: ${statusInfo(r.rights_status).label}`, ok: r.rights_status === "permitted" },
      { label: `Claims: ${r.claims_summary.unverified + r.claims_summary.conflicting} blocking`, ok: (r.claims_summary.unverified + r.claims_summary.conflicting) === 0 },
      { label: `Word count ${r.word_count} within ${r.word_range[0]}–${r.word_range[1]}`, ok: r.word_count >= r.word_range[0] && r.word_count <= r.word_range[1] },
    ].map((row) => el("div", { class: `checklist__item checklist__item--${row.ok ? "ok" : "fail"}` },
      el("span", { class: "checklist__glyph", "aria-hidden": "true" }, row.ok ? "✓" : "✗"),
      el("span", {}, row.label))));

  return el("div", { class: "stack" },
    el("div", { class: "drawer__section" },
      el("h3", {}, "Version under review"),
      kv([
        { k: "Project", v: p.title },
        { k: "Version", v: `v${r.version} · packaged ${relTime(r.created_at)}` },
        { k: "Video sha256", v: hashChip(r.video_sha256) },
        { k: "Metadata sha256", v: hashChip(r.metadata_sha256) },
        { k: "Package sha256", v: hashChip(r.package_sha256) },
        { k: "Format", v: `${r.script_profile} · ${r.target_duration_seconds}s · ${r.word_count} words (range ${r.word_range[0]}–${r.word_range[1]})` },
        { k: "Hook", v: r.hook },
      ])),
    r.not_approvable ? banner({
      tone: "warn", glyph: "alert", title: "Not approvable in this state",
      body: r.not_approvable.join(" "),
    }) : null,
    r.status === "expired" ? banner({
      tone: "warn", glyph: "clock", title: "Expired — expiry never implies approval",
      body: `The 48h pending TTL passed without a decision. A fresh package must be created for the current version; no publish authorization can be derived from this record.`,
    }) : null,
    el("div", { class: "drawer__section" },
      el("h3", {}, "Evidence / rights / quality"),
      qualityChecks,
      claimsMeter(r)),
    el("div", { class: "drawer__section" },
      el("h3", {}, "Platform copy (as packaged)"),
      kv(Object.entries(r.platform_copy).map(([k, v]) => ({ k: k.replaceAll("_", " "), v })))),
    r.decision ? el("div", { class: "drawer__section" },
      el("h3", {}, "Decision record"),
      decisionRecordCard(r.decision)) : null,
    mockActions,
    el("div", { class: "drawer__section" },
      el("h3", {}, "History"),
      el("div", { class: "timeline" },
        r.history.map((h) => el("div", { class: "timeline__item" },
          el("span", { class: "timeline__dot timeline__dot--neutral", "aria-hidden": "true" }, "·"),
          el("div", { class: "stack", style: "gap:1px" },
            el("span", { class: "timeline__time" }, relTime(h.at)),
            el("span", { class: "timeline__title" }, h.event),
            el("span", { class: "timeline__detail" }, h.detail)))))),
  );
}

function openMockDecision(r) {
  const dlg = mockDialog({
    title: `Record decision — ${r.id} (mock)`,
    body: buildMockForm(r),
    onClose: () => {},
  });

  function buildMockForm(r) {
    const outcomes = [
      { value: "approved", label: "Approve", hint: "Records APPROVED in the decision record (mock only)." },
      { value: "changes_requested", label: "Request changes", hint: "Records CHANGES_REQUESTED with the note (mock only)." },
      { value: "rejected", label: "Reject", hint: "Records REJECTED in the existing immutable record format (mock only)." },
    ];
    let outcome = "approved";

    const radios = el("div", { class: "radio-row", role: "radiogroup", "aria-label": "Decision outcome" },
      outcomes.map((o, i) => el("label", { class: "radio-opt" },
        el("input", { type: "radio", name: "mock-outcome", value: o.value, checked: i === 0 ? true : null, on: { change: (e) => { outcome = o.value; sync(); } } }),
        el("span", {}, el("span", { class: "radio-opt__label" }, o.label), el("span", { class: "radio-opt__hint" }, ` ${o.hint}`)))));

    const idLabel = `rev-label-${Math.random().toString(36).slice(2, 7)}`;
    const reviewer = el("input", { class: "input", id: idLabel, type: "text", placeholder: "e.g. Owner (local)", autocomplete: "off", on: { input: sync } });
    const idNote = el("input", { class: "input", type: "text", placeholder: "Why this decision (recorded verbatim)", autocomplete: "off", style: "margin-top:8px" });

    const hint = el("p", { class: "text-faint", style: "font-size:var(--fs-xs); margin-top:10px" },
      "The approval gate requires an attributable human identity (D-09). Submitting here performs no write — the prototype has no backend.");

    const submit = el("button", { class: "btn btn--primary", type: "button", "aria-disabled": "true", on: { click: submitMock } }, "Submit (mock)");
    const cancel = el("button", { class: "btn", type: "button", on: { click: () => dlg.close() } }, "Cancel");

    function sync() {
      const ready = reviewer.value.trim().length > 0;
      submit.setAttribute("aria-disabled", String(!ready));
    }

    function submitMock() {
      if (submit.getAttribute("aria-disabled") === "true") return;
      dlg.close();
      toast("Mock only — no decision was recorded. Real approvals go through the local approval CLI with an attributable reviewer identity.");
    }

    const actions = el("div", { class: "dialog__actions" }, cancel, submit);
    return el("div", { class: "stack" },
      el("p", { style: "margin-bottom:10px" }, `Package ${r.id} · ${projects.find((x) => x.id === r.project_id).title} · v${r.version}`),
      radios,
      el("div", { style: "margin-top:12px" },
        el("label", { class: "field__label", for: idLabel }, "Reviewer label (required)"),
        reviewer,
        el("label", { class: "field__label", for: `${idLabel}-n`, style: "margin-top:8px" }, "Decision note"),
        idNote),
      hint, actions);
  }
}

export default {
  id: "review",
  title: "Review & Approvals",
  render(main, param) {
    let queueRegion = null;
    let historyRegion = null;

    function pendingCard(r) {
      const p = projects.find((x) => x.id === r.project_id);
      const waitH = Math.round((NOW_MS - new Date(r.created_at).getTime()) / 3600_000 * 10) / 10;
      return el("div", { class: "pubcard" },
        el("div", { class: "pubcard__head" },
          el("div", { class: "stack", style: "gap:2px; min-width:0" },
            el("strong", {}, r.title),
            el("span", { class: "text-faint", style: "font-size:var(--fs-xs)" }, `${r.id} · v${r.version} · waiting ${waitH}h · ${packageHeadMeta(r)}`)),
          el("span", { style: "margin-left:auto" }, badge(r.status))),
        el("div", { class: "pubcard__checks" },
          el("span", { class: `pubcheck ${r.visual_quality_status === "review_ready" ? "pubcheck--pass" : "pubcheck--fail"}` }, el("span", { class: "pubcheck__glyph", "aria-hidden": "true" }, r.visual_quality_status === "review_ready" ? "✓" : "✗"), el("span", {}, `visuals: ${r.visual_quality_status}`)),
          el("span", { class: `pubcheck ${r.rights_status === "permitted" ? "pubcheck--pass" : "pubcheck--fail"}` }, el("span", { class: "pubcheck__glyph", "aria-hidden": "true" }, r.rights_status === "permitted" ? "✓" : "✗"), el("span", {}, `rights: ${r.rights_status}`)),
          el("span", { class: `pubcheck ${r.qa.status === "pass" ? "pubcheck--pass" : "pubcheck--fail"}` }, el("span", { class: "pubcheck__glyph", "aria-hidden": "true" }, r.qa.status === "pass" ? "✓" : "✗"), el("span", {}, `qa: ${r.qa.status}`)),
          el("span", { class: `pubcheck ${(r.claims_summary.unverified + r.claims_summary.conflicting) === 0 ? "pubcheck--pass" : "pubcheck--fail"}` }, el("span", { class: "pubcheck__glyph", "aria-hidden": "true" }, (r.claims_summary.unverified + r.claims_summary.conflicting) === 0 ? "✓" : "✗"), el("span", {}, `claims: ${r.claims_summary.verified + r.claims_summary.supported} verified/supported`))),
        r.not_approvable ? el("span", { class: "reason-code" }, "not_approvable: draft_only visuals + blocked storyboard") : null,
        el("div", { style: "display:flex; gap:8px; flex-wrap:wrap" },
          el("button", { class: "btn btn--sm btn--primary", type: "button", on: { click: () => navigateTo(r.id) } }, "Open package"),
          el("button", {
            class: "btn btn--sm", type: "button",
            disabled: Boolean(r.not_approvable),
            "aria-disabled": r.not_approvable ? "true" : null,
            title: r.not_approvable ? "Package is draft-only — the approval gate would refuse it." : "Opens the mock decision dialog.",
            on: { click: () => (r.not_approvable ? toast("This package is draft-only — the approval gate would refuse approval.") : openMockDecision(r)) },
          }, "Record decision (mock)…")));
    }

    function historyTable() {
      const decided = reviews.filter((r) => r.decision || r.status === "expired");
      const rows = decided.map((r) => ({
        r,
        outcome: r.decision?.outcome || r.status,
        reviewer: r.decision?.reviewer_label || "—",
      }));
      return dataTable({
        caption: "Decision history — immutable decision-record entries (sample)",
        columns: [
          { key: "id", label: "Review", render: (row) => el("button", { class: "btn btn--sm", type: "button", on: { click: () => navigateTo(row.r.id) } }, `${row.r.id} · v${row.r.version}`) },
          { key: "title", label: "Package", render: (row) => row.r.title },
          { key: "outcome", label: "Outcome (CF-21)", render: (row) => badge(row.outcome) },
          { key: "reviewer", label: "Reviewer label", render: (row) => row.reviewer === "—" ? el("span", { class: "text-faint" }, "— (expired)") : row.reviewer },
          { key: "at", label: "Recorded", render: (row) => row.r.decision ? relTime(row.r.decision.decided_at) : relTime(row.r.history[row.r.history.length - 1]?.at) },
          { key: "sha", label: "Package sha256", render: (row) => hashChip(row.r.package_sha256) },
        ],
        rows,
        stack: true,
        emptyMessage: "No decisions recorded yet.",
      });
    }

    function navigateTo(id) {
      window.location.hash = `#/review/${id}`;
    }

    function renderQueue() {
      const pending = reviews.filter((r) => r.status === "pending_human_review");
      queueRegion.replaceChildren(
        pending.length
          ? el("div", { class: "grid grid--2" }, pending.map(pendingCard))
          : emptyState({ glyph: "review", title: "Queue clear", body: "No packages are waiting for a human decision." }));
    }

    queueRegion = el("div", {});
    renderQueue();

    main.append(
      pageHead({
        title: "Review & Approvals",
        sub: "Human-controlled decision surface. Each package binds the exact version (video + metadata SHA-256) — decisions are version-specific and immutable once recorded.",
      }),
      banner({
        tone: "danger", glyph: "lock",
        title: "Mock-only — this screen cannot approve anything",
        body: "Real approvals are recorded via the local approval CLI with an attributable reviewer identity, then consumed by publish authorization. Rejections reuse the existing immutable decision-record format (status: rejected).",
      }),
      el("div", { class: "filterbar", style: "margin-top: var(--sp-5)" },
        chipGroup({
          label: "Queue view", name: "view", value: "pending",
          options: [
            { value: "pending", label: "Pending", count: reviews.filter((r) => r.status === "pending_human_review").length },
            { value: "history", label: "History", count: reviews.filter((r) => r.decision || r.status === "expired").length },
          ],
          onChange: (v) => {
            historyRegion.style.display = v === "history" ? "" : "none";
            queueRegion.style.display = v === "pending" ? "" : "none";
          },
        }),
      ),
      queueRegion,
      el("div", { class: "page__section" },
        el("h2", { class: "sr-only" }, "Decision history"),
        historyRegion = historyTable()),
      banner({
        tone: "info", glyph: "clock", title: "Pending TTL: 48h (sample)",
        body: "Expired packages (rv05) never imply approval — a fresh package must be created for the current version.",
      }),
    );

    if (param) {
      const r = reviews.find((x) => x.id === param);
      if (r) {
        drawer({
          title: r.title,
          meta: packageHeadMeta(r),
          content: reviewDrawer(r),
          onClose: () => history.replaceState(null, "", "#/review"),
        });
      }
    }
  },
};
