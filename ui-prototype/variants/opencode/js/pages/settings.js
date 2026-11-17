/* settings.js — display preferences and workspace configuration placeholders.
   Only display preferences are persisted (localStorage): theme + density.
   Governance items are display-only with no actions. */

import { el } from "../dom.js";
import { governance } from "../data.js";
import { loadPrefs, savePrefs, clearPrefs } from "../store.js";
import { themeRadiogroup, setTheme, getTheme } from "../theme.js";
import {
  pageHead, panel, banner, kv, dataTable, badge,
} from "../components.js";
import { toast } from "../toasts.js";

export default {
  id: "settings",
  title: "Settings",
  render(main) {
    const prefs = loadPrefs();

    const densityGroup = el("div", { class: "seg", role: "radiogroup", "aria-label": "Table density" });
    ["comfortable", "compact"].forEach((val) => {
      const b = el("button", {
        type: "button", class: "seg__opt", role: "radio",
        "aria-checked": String((prefs.density || "comfortable") === val),
        tabindex: (prefs.density || "comfortable") === val ? "0" : "-1",
        on: {
          click: () => {
            prefs.density = val;
            savePrefs(prefs);
            document.documentElement.dataset.density = val;
            densityGroup.querySelectorAll(".seg__opt").forEach((x, i) => {
              x.setAttribute("aria-checked", String(i === (val === "compact" ? 1 : 0)));
              x.tabIndex = i === (val === "compact" ? 1 : 0) ? "0" : "-1";
            });
            toast(`Density set to ${val} (saved locally).`);
          },
        },
      }, val === "comfortable" ? "Comfortable" : "Compact");
      densityGroup.append(b);
    });
    if (prefs.density) document.documentElement.dataset.density = prefs.density;

    const themeGroup = themeRadiogroup({ label: "Appearance" });

    const appearancePanel = panel({
      title: "Appearance",
      body: el("div", { class: "stack" },
        el("div", { class: "stack", style: "gap:6px" },
          el("span", { class: "field__label" }, "Theme — applies to every page"),
          themeGroup,
          el("span", { class: "text-faint", style: "font-size:var(--fs-xs)" },
            `Current: ${getTheme()}. “System” follows your operating system preference live. Saved in localStorage (nd-cc-theme).`)),
        el("div", { class: "stack", style: "gap:6px" },
          el("span", { class: "field__label" }, "Table density"),
          densityGroup,
          el("span", { class: "text-faint", style: "font-size:var(--fs-xs)" },
            "Compact tightens table rows and card padding across all screens. Saved in localStorage (nd-cc-prefs)."))),
    });

    const storagePanel = panel({
      title: "Local data & preferences", meta: "local-first — nothing leaves this machine",
      body: el("div", {},
        kv([
          { k: "Theme storage", v: "localStorage key nd-cc-theme", mono: false },
          { k: "Preferences storage", v: "localStorage key nd-cc-prefs (density)", mono: false },
          { k: "Sample data", v: "in-memory JS module (js/data.js) — no storage, no fetch" },
          { k: "Credentials", v: "none stored — the prototype has no secrets by design" },
        ]),
        el("div", { style: "margin-top:12px" },
          el("button", {
            class: "btn", type: "button",
            on: {
              click: () => {
                clearPrefs();
                setTheme("dark");
                document.documentElement.dataset.density = "comfortable";
                toast("Local preferences cleared. Theme reset to Dark.");
              },
            },
          }, "Reset local preferences"))),
    });

    const configPanel = panel({
      title: "Workspace configuration (placeholders)", meta: "display-only sample values",
      body: el("div", {},
        kv([
          { k: "STORYBOARD_GATE", v: "require (default; off | skip | warn | require; unknown values fail closed)" },
          { k: "Upload window", v: "20:00 IST — opt-in (require_window=false); not a mandatory gate" },
          { k: "API base URL", v: "not configured in this prototype (no backend calls exist)" },
          { k: "Review approval path", v: "local approval CLI only — HTTP decision endpoints are out of scope" },
          { k: "Destination default", v: "private; public release disabled pending owner policy" },
        ])),
    });

    const governancePanel = panel({
      title: "P0 governance gates", meta: "owner-gated — display only",
      body: el("div", {},
        dataTable({
          caption: "P0 governance gates (sample display)",
          columns: [
            { key: "gate", label: "Gate" },
            { key: "status", label: "Status", render: (r) => badge(r.status) },
            { key: "detail", label: "Detail" },
          ],
          rows: [
            ...governance.decisions.map((d) => ({ gate: `Decision ${d.id}`, status: d.status, detail: d.topic })),
            { gate: governance.api_lc.label, status: governance.api_lc.status, detail: governance.api_lc.detail },
            { gate: "GOV-09", status: governance.gov09.status, detail: governance.gov09.detail },
            { gate: governance.m6p_entries.label, status: governance.m6p_entries.status, detail: governance.m6p_entries.detail },
            { gate: "Autonomous publishing", status: governance.autonomy_publish.status, detail: governance.autonomy_publish.detail },
          ],
          stack: true,
          emptyMessage: "No gates.",
        }),
        el("p", { class: "text-faint", style: "font-size:var(--fs-xs); margin-top:10px" }, governance.note)),
    });

    main.append(
      pageHead({
        title: "Settings",
        sub: "Display preferences and workspace configuration placeholders. Only appearance and density are persisted; everything else is shown read-only.",
      }),
      banner({
        tone: "info", glyph: "info",
        title: "What Settings can change in this prototype",
        body: "Theme and density only. Workspace configuration and governance gates are read-only placeholders — no owner decision can be made or inferred here.",
      }),
      el("div", { class: "grid grid--2", style: "margin-top: var(--sp-5)" },
        appearancePanel,
        storagePanel,
        configPanel,
        governancePanel,
      ),
    );
  },
};
