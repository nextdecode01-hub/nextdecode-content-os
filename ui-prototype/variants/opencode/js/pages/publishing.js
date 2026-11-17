/* publishing.js — DISPLAY-ONLY distribution readiness.
   Shows authorization state per project (approval → QA → rights → evidence →
   manifest promotion → optional upload window). No publish/upload/export
   control exists on this screen, and public publishing is shown as disabled
   pending owner policy. */

import { el, fmtRel } from "../dom.js";
import { statusInfo } from "../status.js";
import { publish, projects, reviews, NOW_MS } from "../data.js";
import { store } from "../store.js";
import {
  pageHead, panel, badge, banner, kv, dataTable, emptyState, chipGroup,
} from "../components.js";
import { toast } from "../toasts.js";

function rel(iso) {
  return fmtRel(iso, NOW_MS);
}

function checkGlyph(state) {
  if (state === "pass") return { glyph: "✓", cls: "pubcheck--pass" };
  if (state === "fail") return { glyph: "✗", cls: "pubcheck--fail" };
  return { glyph: "—", cls: "pubcheck--na" };
}

const CHECK_LABELS = {
  approval: "Approval",
  qa: "QA pass",
  rights: "Rights permitted",
  evidence: "Evidence supported",
  promotion: "Manifest promotion",
  window: "Upload window",
};

function authCard(auth) {
  const p = projects.find((x) => x.id === auth.project_id);
  const review = reviews.find((r) => r.project_id === auth.project_id);

  const checks = el("div", { class: "pubcard__checks" },
    Object.entries(auth.checks).map(([key, state]) => {
      const g = checkGlyph(state);
      return el("span", { class: `pubcheck ${g.cls}` },
        el("span", { class: "pubcheck__glyph", "aria-hidden": "true" }, g.glyph),
        el("span", {}, `${CHECK_LABELS[key]}: ${state}`));
    }));

  const stateInfo = statusInfo(auth.state);

  return el("div", { class: "pubcard" },
    el("div", { class: "pubcard__head" },
      el("div", { class: "stack", style: "gap:2px; min-width:0" },
        el("strong", {}, p.title),
        el("span", { class: "text-faint", style: "font-size:var(--fs-xs)" },
          `${p.id} · ${review ? `review ${review.id} (${statusInfo(review.status).label})` : "no package"}`)),
      el("span", { style: "margin-left:auto; display:flex; gap:8px; align-items:center; flex-wrap:wrap" },
        auth.reason_code ? el("span", { class: "reason-code" }, auth.reason_code) : null,
        badge(auth.state))),
    checks,
    auth.reason_detail ? el("p", { class: "text-muted", style: "font-size:var(--fs-sm); margin:0" }, auth.reason_detail) : null,
    auth.note ? el("p", { class: "text-faint", style: "font-size:var(--fs-xs); margin:0" }, auth.note) : null,
    auth.ledger
      ? el("p", { class: "text-faint mono", style: "font-size:var(--fs-xs); margin:0" },
          `ledger ${auth.ledger.entry_id} · ${auth.ledger.destination} · recorded ${rel(auth.ledger.recorded_at)}`)
      : null,
    el("div", { style: "display:flex; gap:8px; align-items:center" },
      el("button", {
        class: "btn btn--sm", type: "button", disabled: true, "aria-disabled": "true",
        title: "Display-only prototype — publishing actions are not available.",
        on: { click: () => toast("Display-only: this prototype never triggers uploads or exports.") },
      }, auth.state === "authorized" ? "Publish action (display-only)" : "Publish — unavailable"),
      el("span", { class: "text-faint", style: "font-size:var(--fs-xs)" }, "Destination: " + (auth.destination || "—"))));
}

export default {
  id: "publishing",
  title: "Publishing",
  render(main) {
    if (!store.filters.publishing) store.filters.publishing = { view: "all" };
    const f = store.filters.publishing;

    const ledgerRows = publish.authorizations.filter((a) => a.ledger).map((a) => ({
      entry: a.ledger.entry_id,
      project: projects.find((p) => p.id === a.project_id)?.title,
      destination: a.ledger.destination,
      recorded_at: a.ledger.recorded_at,
      public_release: "not requested",
    }));

    let cardsRegion = el("div", {});

    function renderCards() {
      const rows = publish.authorizations.filter((a) => f.view === "all" || (f.view === "blocked" ? a.state !== "authorized" : a.state === "authorized"));
      cardsRegion.replaceChildren(
        rows.length
          ? el("div", { class: "grid grid--2" }, rows.map(authCard))
          : emptyState({ glyph: "publishing", title: "Nothing in this view", body: "No authorizations match the current filter." }));
    }
    renderCards();

    main.append(
      pageHead({
        title: "Publishing",
        sub: "Destination readiness visibility only. Authorization derives from the decision record and publish checks — approval alone never confers a publish grant.",
      }),
      banner({
        tone: "danger", glyph: "lock",
        title: "Display-only — protected actions are disabled by design",
        body: "This screen performs no uploads, exports or external calls. Public publishing is disabled pending an owner policy decision; the default destination is private.",
      }),
      el("div", { class: "filterbar", style: "margin-top: var(--sp-5)" },
        chipGroup({
          label: "Authorization view", name: "view", value: f.view,
          options: [
            { value: "all", label: "All", count: publish.authorizations.length },
            { value: "blocked", label: "Blocked", count: publish.authorizations.filter((a) => a.state !== "authorized").length },
            { value: "authorized", label: "Authorized", count: publish.authorizations.filter((a) => a.state === "authorized").length },
          ],
          onChange: (v) => { f.view = v; renderCards(); },
        })),
      cardsRegion,
      el("div", { class: "page__section" },
        panel({
          title: "Workspace policy", meta: "displayed from sample config",
          body: el("div", {},
            kv([
              { k: "Public publishing", v: "disabled_pending_owner_policy" },
              { k: "Autonomous publishing", v: "disabled" },
              { k: "Default destination", v: publish.policy.default_destination },
              { k: "Upload window", v: `${publish.policy.upload_window.window} — opt-in (require_window=false), not a mandatory gate` },
              { k: "Ledger", v: "social_upload_ledger.json — private entries only" },
            ])),
        })),
      el("div", { class: "page__section" },
        panel({
          title: "Upload ledger", meta: "display-only",
          body: dataTable({
            caption: "Recorded uploads (sample)",
            columns: [
              { key: "entry", label: "Entry", render: (r) => el("span", { class: "mono" }, r.entry) },
              { key: "project", label: "Project" },
              { key: "destination", label: "Destination", render: (r) => badge(r.destination === "private" ? "ok" : "neutral") },
              { key: "recorded_at", label: "Recorded", render: (r) => rel(r.recorded_at) },
              { key: "public_release", label: "Public release" },
            ],
            rows: ledgerRows,
            stack: true,
            emptyMessage: "No uploads recorded.",
          }),
        })),
      banner({
        tone: "info", glyph: "info", title: "Why p03 is blocked even though its review was approved",
        body: "Approval (rv06) is a human decision about content. Authorization additionally requires rights, evidence and promotion checks — approval recorded ≠ consumable grant.",
      }),
    );
  },
};
