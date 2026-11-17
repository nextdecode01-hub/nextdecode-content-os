/* overview.js — cross-project operational summary: what needs attention now,
   pipeline health, review queue preview and the recent event feed. */

import { el } from "../dom.js";
import { STAGE_ORDER, statusInfo } from "../status.js";
import {
  projects, runs, reviews, events, incidents, publish, studio, NOW_MS,
} from "../data.js";
import {
  pageHead, panel, statCard, attend, meterRow, timeline, banner,
} from "../components.js";
import { navigate } from "../router.js";

function attentionItems() {
  const items = [];

  const blockedPublish = publish.authorizations.filter((a) => a.state === "blocked" || a.state === "blocked_approval");
  blockedPublish.forEach((a) => {
    const project = projects.find((p) => p.id === a.project_id);
    items.push({
      tone: "danger",
      glyph: "lock",
      title: `Publish blocked — ${a.reason_code}`,
      meta: `${project.title} · ${a.reason_detail}`,
      link: "Check publishing", go: () => navigate("publishing"),
    });
  });

  const pending = reviews.filter((r) => r.status === "pending_human_review");
  pending.forEach((r) => {
    const project = projects.find((p) => p.id === r.project_id);
    const waitH = Math.round((NOW_MS - new Date(r.created_at).getTime()) / 3600_000 * 10) / 10;
    items.push({
      tone: r.not_approvable ? "warn" : "info",
      glyph: r.not_approvable ? "alert" : "review",
      title: r.not_approvable
        ? `Review ${r.id} not approvable yet (draft-only visuals)`
        : `Review ${r.id} awaiting human decision`,
      meta: `${project.title} · waiting ${waitH}h · version ${r.version} · ${r.visual_quality_status}`,
      link: "Open review", go: () => navigate("review", r.id),
    });
  });

  const expired = reviews.filter((r) => r.status === "expired");
  expired.forEach((r) => {
    const project = projects.find((p) => p.id === r.project_id);
    items.push({
      tone: "warn", glyph: "clock",
      title: `Review ${r.id} expired without a decision`,
      meta: `${project.title} · expiry never implies approval — repackage required`,
      link: "Open review", go: () => navigate("review", r.id),
    });
  });

  runs.filter((r) => r.state === "failed").forEach((r) => {
    const project = projects.find((p) => p.id === r.project_id);
    items.push({
      tone: "danger", glyph: "alert",
      title: `Run ${r.id} failed (${r.error_code})`,
      meta: `${project.title} · attempts ${r.attempts}/${r.max_attempts} · retry run in progress`,
      link: "Open run", go: () => navigate("workflows", r.id),
    });
  });

  const storyboardGate = studio.filter((s) => s.stages.storyboard.review_status === "blocked");
  storyboardGate.forEach((s) => {
    const p = projects.find((x) => x.id === s.project_id);
    items.push({
      tone: "warn", glyph: "studio",
      title: "Storyboard review required (gate=require)",
      meta: `${p.title} · scene pack held; render queued behind it`,
      link: "Open studio", go: () => navigate("studio"),
    });
  });

  incidents.filter((i) => i.state === "open").forEach((i) => {
    items.push({
      tone: "warn", glyph: "operations",
      title: `${i.id}: ${i.title}`,
      meta: i.detail,
      link: "Operations", go: () => navigate("operations"),
    });
  });

  return items;
}

function commandBrief({ attention, runsInFlight, pendingReviews, publishBlocked, openIncidents }) {
  const critical = attention.filter((item) => item.tone === "danger").length;
  const watch = attention.filter((item) => item.tone === "warn").length;
  return el("section", { class: "command-hero", "aria-label": "Command brief" },
    el("div", { class: "command-hero__main" },
      el("div", { class: "command-hero__eyebrow" }, el("span", { class: "command-hero__pulse" }), " OPERATING PICTURE · SAMPLE ENVIRONMENT"),
      el("h2", {}, "Your operation, at a glance."),
      el("p", {}, "Coordinate work across research, production, review and distribution. Start with the signals that need a decision, then drill into the underlying records."),
      el("div", { class: "command-hero__links" },
        el("span", { class: "command-hero__link" }, "10 connected work areas"),
        el("span", { class: "command-hero__link" }, "Human-governed workflow"),
        el("span", { class: "command-hero__link" }, "Local prototype · illustrative data"))),
    el("div", { class: "command-hero__pulse-card" },
      el("div", { class: "command-hero__pulse-head" }, el("span", {}, "ATTENTION INDEX"), badgeForBrief(critical, watch)),
      el("div", { class: "command-hero__number" }, String(attention.length).padStart(2, "0")),
      el("div", { class: "command-hero__caption" }, "items requiring visibility"),
      el("div", { class: "command-hero__breakdown" },
        el("span", {}, el("i", { class: "command-dot command-dot--critical" }), `${critical} critical`),
        el("span", {}, el("i", { class: "command-dot command-dot--watch" }), `${watch} watch`)),
      el("div", { class: "command-hero__foot" },
        el("span", {}, `${runsInFlight.length} active runs`),
        el("span", {}, `${pendingReviews.length} reviews waiting`),
        el("span", {}, `${publishBlocked.length} publish gates blocked`),
        el("span", {}, `${openIncidents} open incidents`))));
}

function badgeForBrief(critical, watch) {
  const label = critical ? "Action needed" : watch ? "Monitor" : "Stable";
  const tone = critical ? "danger" : watch ? "warn" : "ok";
  return el("span", { class: `badge badge--${tone}` }, el("span", { class: "badge__dot" }), label);
}

function pipelineHealth() {
  const distribution = STAGE_ORDER.map((st) => ({
    stage: st,
    count: projects.filter((p) => p.stage === st).length,
  }));
  return el("div", { class: "stack" },
    distribution.map(({ stage, count }) => meterRow({
      label: statusInfo(stage).label,
      value: count, total: projects.length, unit: "pct_of",
      tone: count === 0 ? "" : stage === "review" ? "info" : stage === "publish" ? "ok" : "",
    })));
}

function runHealth() {
  const counts = {};
  runs.forEach((r) => { counts[r.state] = (counts[r.state] || 0) + 1; });
  const tones = { ok: "ok", in_progress: "running", failed: "danger", blocked: "danger", promoting: "running" };
  return el("div", { class: "stack" },
    ["ok", "in_progress", "failed", "blocked"].filter((k) => counts[k]).map((k) => meterRow({
      label: statusInfo(k).label, value: counts[k], total: runs.length, unit: "pct_of", tone: tones[k],
    })));
}

export default {
  id: "overview",
  title: "Overview",
  render(main) {
    const pendingReviews = reviews.filter((r) => r.status === "pending_human_review");
    const runsInFlight = runs.filter((r) => r.state === "in_progress" || r.state === "promoting");
    const publishBlocked = publish.authorizations.filter((a) => a.state !== "authorized" && a.state !== "not_ready");

    const attention = attentionItems();

    main.append(
      pageHead({
        title: "Overview",
        sub: "Management command center · sample data captured 13 Nov, 10:30 IST — no live connection.",
      }),
      commandBrief({
        attention,
        runsInFlight,
        pendingReviews,
        publishBlocked,
        openIncidents: incidents.filter((i) => i.state === "open").length,
      }),

      el("div", { class: "grid grid--kpi" },
        statCard({ label: "Awaiting human review", value: String(pendingReviews.filter((r) => !r.not_approvable).length), hint: `${pendingReviews.filter((r) => r.not_approvable).length} not yet approvable`, tone: "info", glyph: "review" }),
        statCard({ label: "Runs in flight", value: String(runsInFlight.length), hint: "of 8 runs (14d window)", glyph: "workflows" }),
        statCard({ label: "Publish blocked", value: String(publishBlocked.length), hint: "approval / rights gates", tone: "danger", glyph: "lock" }),
        statCard({ label: "Open incidents", value: String(incidents.length), hint: "1 recovering · 1 open", tone: "warn", glyph: "operations" }),
      ),

      el("div", { class: "grid grid--main", style: "margin-top: var(--sp-4)" },

        el("div", { class: "stack" },
          panel({
            title: "Needs attention", meta: `${attention.length} items`,
            body: el("div", {}, attention.map((it) => attend({
              tone: it.tone, glyph: it.glyph, title: it.title, meta: it.meta, linkLabel: it.link, onLink: it.go,
            }))),
            flush: true,
          }),

          el("div", { class: "grid grid--2" },
            panel({ title: "Pipeline health", meta: "projects by stage", body: pipelineHealth() }),
            panel({ title: "Run health", meta: `${runs.length} runs (14d)`, body: runHealth() }),
          ),

          panel({
            title: "Review queue preview",
            actions: el("button", { class: "btn btn--sm", type: "button", on: { click: () => navigate("review") } }, "Open Review & Approvals"),
            body: pendingReviews.length
              ? el("div", {},
                  pendingReviews.map((r) => attend({
                    tone: r.not_approvable ? "warn" : "info",
                    glyph: r.not_approvable ? "alert" : "review",
                    title: `${r.id} — ${r.title}`,
                    meta: `v${r.version} · ${r.visual_quality_status.replaceAll("_", " ")} · claims ${r.claims_summary.verified + r.claims_summary.supported}/${r.claims_summary.verified + r.claims_summary.supported + r.claims_summary.unverified + r.claims_summary.conflicting} verified/supported · rights ${r.rights_status}`,
                    linkLabel: "Open", go: () => navigate("review", r.id),
                  })))
              : null,
            flush: true,
          }),
        ),

        el("div", { class: "stack" },
          panel({ title: "Recent events", meta: "last 48h", flush: true, body: timeline(events.slice(0, 9)) }),
          banner({
            tone: "info", glyph: "info", title: "Sample data",
            body: "Every value on this screen is illustrative. No live runs, queues or analytics are connected.",
          }),
        ),
      ),
    );
  },
};
