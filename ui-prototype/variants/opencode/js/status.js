/* status.js — the single source of truth for workflow state vocabulary.
   Every screen renders states through this registry so labels, colors and
   meanings stay consistent across Overview, Workflows, Review, Publishing…

   Vocabulary mirrors the real Shorts Studio engine vocabulary where it exists:
   - run states: in_progress | promoting | ok | failed | blocked   (run_tracker.py)
   - task states: queued | running | succeeded | failed | blocked  (app/autonomy)
   - review package: pending_human_review | decided via CF-21 outcomes
     approved | rejected | changes_requested | expired | revoked | withdrawn
   - visual quality: review_ready | draft_only                     (review_bundle.py)
   - storyboard gate: off | skip | warn | require                  (storyboard.py)
   - claim statuses: verified | supported (passing);
     unverified | outdated | conflicting | unsupported (blocking)  (authorization.py)
   - rights: permitted | restricted                                (authorization.py)
   - qa: pass | fail                                               (authorization.py)
   - publish decision: authorized | blocked                        (authorization.py)
   - worker: healthy | stale | offline | paused
   - incident: open | recovering | recovered
*/

export const STAGE_ORDER = ["research", "script", "visuals", "voice", "render", "review", "publish"];

export const STATUS = {
  /* project lifecycle */
  active: { label: "Active", tone: "ok" },
  needs_attention: { label: "Needs attention", tone: "warn" },
  blocked: { label: "Blocked", tone: "danger" },
  completed: { label: "Completed", tone: "neutral" },
  draft: { label: "Draft", tone: "neutral" },
  archived: { label: "Archived", tone: "neutral" },

  /* pipeline stages */
  research: { label: "Research", tone: "neutral" },
  script: { label: "Script", tone: "neutral" },
  visuals: { label: "Visuals", tone: "neutral" },
  voice: { label: "Voice", tone: "neutral" },
  render: { label: "Render", tone: "neutral" },
  review: { label: "Review", tone: "neutral" },
  publish: { label: "Publish", tone: "neutral" },
  stage_done: { label: "Done", tone: "ok" },
  stage_pending: { label: "Pending", tone: "neutral" },

  /* runs (run_tracker.py vocabulary) */
  in_progress: { label: "In progress", tone: "running" },
  promoting: { label: "Promoting", tone: "running" },
  ok: { label: "Completed", tone: "ok" },
  failed: { label: "Failed", tone: "danger" },

  /* autonomy tasks (app/autonomy vocabulary) */
  queued: { label: "Queued", tone: "neutral" },
  running: { label: "Running", tone: "running" },
  succeeded: { label: "Succeeded", tone: "ok" },

  /* review & decision (review_bundle.py + CF-21 outcomes) */
  pending_human_review: { label: "Pending human review", tone: "pending" },
  approved: { label: "Approved", tone: "ok" },
  rejected: { label: "Rejected", tone: "danger" },
  changes_requested: { label: "Changes requested", tone: "warn" },
  expired: { label: "Expired", tone: "warn" },
  revoked: { label: "Revoked", tone: "danger" },
  withdrawn: { label: "Withdrawn", tone: "neutral" },

  /* research packages */
  needs_review: { label: "Needs review", tone: "warn" },

  /* package quality */
  review_ready: { label: "Review-ready", tone: "ok" },
  draft_only: { label: "Draft only", tone: "warn" },
  ready: { label: "Ready", tone: "ok" },
  missing: { label: "Missing", tone: "danger" },

  /* storyboard gate */
  off: { label: "Off", tone: "neutral" },
  skip: { label: "Skip", tone: "neutral" },
  warn: { label: "Warn", tone: "warn" },
  require: { label: "Require", tone: "info" },

  /* claims + evidence */
  verified: { label: "Verified", tone: "ok" },
  supported: { label: "Supported", tone: "ok" },
  unverified: { label: "Unverified", tone: "warn" },
  outdated: { label: "Outdated", tone: "warn" },
  conflicting: { label: "Conflicting", tone: "danger" },
  unsupported: { label: "Unsupported", tone: "danger" },

  /* rights + qa */
  permitted: { label: "Permitted", tone: "ok" },
  restricted: { label: "Restricted", tone: "danger" },
  pass: { label: "Pass", tone: "ok" },
  fail: { label: "Fail", tone: "danger" },

  /* publishing */
  authorized: { label: "Authorized", tone: "ok" },
  blocked_approval: { label: "Blocked (approval)", tone: "danger" },
  not_ready: { label: "Not ready", tone: "neutral" },
  recorded: { label: "Recorded", tone: "neutral" },

  /* operations */
  healthy: { label: "Healthy", tone: "ok" },
  stale: { label: "Stale", tone: "warn" },
  offline: { label: "Offline", tone: "neutral" },
  paused: { label: "Paused", tone: "info" },
  open: { label: "Open", tone: "danger" },
  recovering: { label: "Recovering", tone: "running" },
  recovered: { label: "Recovered", tone: "ok" },

  /* governance */
  pending_owner: { label: "Pending owner", tone: "warn" },
  pending_owner_decision: { label: "Pending owner decision", tone: "warn" },
  gate_blocked: { label: "Blocked", tone: "danger" },
};

/** Resolve a state key to its registry entry (with safe fallback). */
export function statusInfo(key) {
  return STATUS[key] || { label: key ? String(key).replaceAll("_", " ") : "—", tone: "neutral" };
}

export const STATUS_TONES = ["ok", "info", "warn", "danger", "running", "neutral", "pending"];
