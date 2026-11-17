/* toasts.js — transient notices via a polite live region.
   Used to make "mock-only" boundaries explicit: actions never change state. */

import { el } from "./dom.js";

let region = null;

function ensureRegion() {
  if (!region || !region.isConnected) {
    region = el("div", { class: "toasts", role: "status", "aria-live": "polite" });
    document.body.append(region);
  }
  return region;
}

export function toast(message, ms = 4200) {
  const host = ensureRegion();
  const node = el("div", { class: "toast" }, message);
  host.append(node);
  setTimeout(() => node.remove(), ms);
}
