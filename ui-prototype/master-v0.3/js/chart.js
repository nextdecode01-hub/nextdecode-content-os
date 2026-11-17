/* chart.js — dependency-free inline SVG charts with accessible fallbacks.
   Charts carry role="img" + aria-label summaries; the underlying numbers are
   always available in adjacent tables or the sr-only summary. */

import { el, fmtDay, fmtNum } from "./dom.js";

const W = 720;
const PAD = { top: 12, right: 8, bottom: 22, left: 8 };

function svgEl(tag, attrs = {}) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined) continue;
    node.setAttribute(k, v);
  }
  return node;
}

/** Line/area chart. points: [{day, [key]}], key: field to plot. */
export function lineChart({ points, key, height = 220, color = "var(--accent)", label }) {
  const values = points.map((p) => p[key]);
  const max = Math.max(...values, 1);
  const min = 0;
  const innerW = W - PAD.left - PAD.right;
  const innerH = height - PAD.top - PAD.bottom;
  const x = (i) => PAD.left + (i / (points.length - 1)) * innerW;
  const y = (v) => PAD.top + innerH - ((v - min) / (max - min)) * innerH;

  const lineD = points.map((p, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(p[key]).toFixed(1)}`).join(" ");
  const areaD = `${lineD} L${x(points.length - 1).toFixed(1)},${(PAD.top + innerH).toFixed(1)} L${PAD.left},${(PAD.top + innerH).toFixed(1)} Z`;

  const svg = svgEl("svg", {
    viewBox: `0 0 ${W} ${height}`,
    width: "100%",
    height,
    role: "img",
    "aria-label": `${label}. Latest: ${fmtNum(points[points.length - 1][key])}. Peak: ${fmtNum(max)} over ${points.length} days.`,
  });

  const gridlines = [0.25, 0.5, 0.75].map((f) =>
    svgEl("line", {
      x1: PAD.left, x2: W - PAD.right,
      y1: PAD.top + innerH * f, y2: PAD.top + innerH * f,
      stroke: "var(--chart-grid)", "stroke-width": 1,
    }));

  const area = svgEl("path", { d: areaD, fill: color, opacity: 0.12, stroke: "none" });
  const line = svgEl("path", { d: lineD, fill: "none", stroke: color, "stroke-width": 2.2, "stroke-linejoin": "round", "stroke-linecap": "round" });
  const lastDot = svgEl("circle", { cx: x(points.length - 1), cy: y(points[points.length - 1][key]), r: 3.5, fill: color });

  const labels = [0, Math.floor(points.length / 2), points.length - 1].map((i) =>
    svgEl("text", {
      x: x(i), y: height - 6, "text-anchor": i === 0 ? "start" : i === points.length - 1 ? "end" : "middle",
      fill: "var(--text-faint)", "font-size": 10.5, "font-family": "var(--mono)",
    }, fmtDay(points[i].day)));

  svg.append(...gridlines, area, line, lastDot, ...labels);

  const wrap = el("div", { style: "min-width:0" }, svg);
  return wrap;
}

/** Tiny inline sparkline for stat cards. */
export function sparkline(values, { height = 34, width = 120, color = "var(--accent)" } = {}) {
  const max = Math.max(...values, 1);
  const step = width / Math.max(1, values.length - 1);
  const d = values.map((v, i) => `${i === 0 ? "M" : "L"}${(i * step).toFixed(1)},${(height - 2 - (v / max) * (height - 6)).toFixed(1)}`).join(" ");
  const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, width, height, "aria-hidden": "true" });
  svg.append(svgEl("path", { d, fill: "none", stroke: color, "stroke-width": 1.8, "stroke-linecap": "round", "stroke-linejoin": "round" }));
  return svg;
}
