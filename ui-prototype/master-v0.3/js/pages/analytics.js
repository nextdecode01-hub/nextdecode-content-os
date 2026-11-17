/* analytics.js — sample trend + content-quality signals.
   Honest framing: the engine currently reports a local-only baseline
   (data/analytics_latest.json), so everything here is illustrative and
   labeled as such. Charts are inline SVG with text alternatives. */

import { el, fmtNum } from "../dom.js";
import { analytics } from "../data.js";
import { store } from "../store.js";
import {
  pageHead, panel, statCard, banner, dataTable, chipGroup, meterRow, kv,
} from "../components.js";
import { lineChart } from "../chart.js";

const SERIES = [
  { key: "views", label: "Views" },
  { key: "watch_hours", label: "Watch hours" },
  { key: "net_subs", label: "Net subscribers" },
];

export default {
  id: "analytics",
  title: "Analytics",
  render(main) {
    if (!store.filters.analytics) store.filters.analytics = { series: "views" };
    const f = store.filters.analytics;

    let chartRegion = el("div", {});

    function renderChart() {
      chartRegion.replaceChildren(lineChart({
        points: analytics.series,
        key: f.series,
        label: `Daily ${SERIES.find((s) => s.key === f.series).label.toLowerCase()} over the last 14 days (sample data)`,
      }));
    }
    renderChart();

    const qualityMeters = el("div", { class: "stack" },
      analytics.quality.map((q) => el("div", { class: "stack", style: "gap:4px" },
        meterRow({ label: q.label, value: q.value, unit: "%", tone: q.tone }),
        el("span", { class: "text-faint", style: "font-size:var(--fs-xs)" }, q.note))));

    const seriesTable = dataTable({
      caption: "Daily series underlying the chart (sample data)",
      columns: [
        { key: "day", label: "Day" },
        { key: "views", label: "Views", align: "right", render: (r) => fmtNum(r.views) },
        { key: "watch_hours", label: "Watch hours", align: "right", render: (r) => fmtNum(r.watch_hours) },
        { key: "net_subs", label: "Net subs", align: "right", render: (r) => fmtNum(r.net_subs) },
      ],
      rows: [...analytics.series].reverse(),
      stack: true,
      emptyMessage: "No series data.",
    });

    main.append(
      pageHead({
        title: "Analytics",
        sub: "Trend and quality signals. Operational quality metrics (claims, rights, QA, first-pass render) are the product's core signals — vanity metrics are deliberately secondary.",
      }),
      banner({
        tone: "info", glyph: "info",
        title: "Sample data — local-first baseline only",
        body: "The current engine collects a local baseline (data/analytics_latest.json: “local baseline available”). No platform APIs are connected, so all figures below are illustrative.",
      }),

      el("div", { class: "grid grid--kpi", style: "margin-top: var(--sp-5)" },
        statCard({ label: "Views (14d)", value: fmtNum(analytics.kpis.views_14d), glyph: "analytics" }),
        statCard({ label: "Watch hours (14d)", value: fmtNum(analytics.kpis.watch_hours_14d), glyph: "video" }),
        statCard({ label: "Net subs (14d)", value: fmtNum(analytics.kpis.net_subs_14d), glyph: "checkCircle" }),
        statCard({ label: "Median retention", value: `${analytics.kpis.median_retention_pct}%`, hint: "all published items (sample)", glyph: "clock" }),
      ),

      el("div", { class: "grid grid--main", style: "margin-top: var(--sp-4)" },
        el("div", { class: "stack" },
          panel({
            title: "14-day trend", meta: "sample data",
            actions: chipGroup({
              label: "Chart series", name: "series", value: f.series,
              options: SERIES.map((s) => ({ value: s.key, label: s.label, count: null })),
              showCounts: false,
              onChange: (v) => { f.series = v; renderChart(); },
            }),
            body: chartRegion,
          }),
          panel({ title: "Content-quality signals", meta: "what gates actually check", body: qualityMeters }),
        ),
        el("div", { class: "stack" },
          panel({
            title: "Review turnaround", meta: "human decision latency (sample)",
            body: kv([
              { k: "Median", v: `${analytics.turnaround.median_review_hours}h` },
              { k: "p90", v: `${analytics.turnaround.p90_review_hours}h` },
              { k: "Note", v: "Review latency is an operational governance signal, not a marketing metric." },
            ]),
          }),
          panel({
            title: "By content pillar", meta: "14d (sample)",
            body: dataTable({
              caption: "Views and retention per pillar (sample)",
              columns: [
                { key: "pillar", label: "Pillar" },
                { key: "items", label: "Items", align: "right" },
                { key: "views", label: "Views", align: "right", render: (r) => fmtNum(r.views) },
                { key: "retention", label: "Retention", align: "right", render: (r) => `${r.retention}%` },
              ],
              rows: analytics.pillars,
              stack: true,
              emptyMessage: "No pillar data.",
            }),
          }),
          seriesTablePanel(),
        ),
      ),
    );

    function seriesTablePanel() {
      return panel({
        title: "Daily series", meta: "table fallback for the chart",
        body: seriesTable,
      });
    }
  },
};
