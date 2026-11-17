/* data.js — SAMPLE DATA ONLY. Nothing here is live: no fetch, no storage, no
   backend. Values illustrate the real Shorts Studio engine vocabulary
   (states, reason codes, package fields) captured from the working tree.

   Dataset capture point (fixed so relative times stay stable):
     2026-11-13 10:30 IST
   Cross-links: projects ↔ runs ↔ reviews ↔ research ↔ studio ↔ publish ↔ ops.
*/

const IST = "+05:30";

/** Deterministic pseudo-SHA-256 (64 hex chars) for display realism only. */
function sha(seed) {
  let out = "";
  for (let i = 0; i < 8; i += 1) {
    let x = 5381 + i * 97;
    const str = `${seed}:${i}`;
    for (let j = 0; j < str.length; j += 1) {
      x = ((x * 33) ^ str.charCodeAt(j)) >>> 0;
    }
    out += x.toString(16).padStart(8, "0");
  }
  return out;
}

export const NOW_ISO = `2026-11-13T10:30:00${IST}`;
export const NOW_MS = new Date(NOW_ISO).getTime();

/* ------------------------------------------------------------------ projects */

export const projects = [
  {
    id: "p01",
    title: "AI Agent Funding Doubled 2025",
    topic: "AI Agent Funding Doubled 2025",
    pillar: "Funding Watch",
    stage: "review",
    status: "active",
    owner: "Owner (local)",
    run_id: "r03",
    review_id: "rv01",
    updated_at: `2026-11-13T09:15:00${IST}`,
    note: "Packaged for review; awaiting human decision.",
  },
  {
    id: "p02",
    title: "Libghostty 1.0 in 60 Seconds",
    topic: "libghostty 1.0 terminal library release",
    pillar: "Dev Tools",
    stage: "render",
    status: "needs_attention",
    owner: "Owner (local)",
    run_id: "r05",
    review_id: "rv02",
    updated_at: `2026-11-13T05:10:00${IST}`,
    note: "Storyboard review required (gate=require); render retrying.",
  },
  {
    id: "p03",
    title: "Crusoe Wyoming Data Center Build",
    topic: "Crusoe data center campus expansion, southeast Wyoming",
    pillar: "Infrastructure",
    stage: "publish",
    status: "blocked",
    owner: "Owner (local)",
    run_id: "r04",
    review_id: "rv06",
    updated_at: `2026-11-12T22:40:00${IST}`,
    note: "Approved, but publish is blocked: reuse rights not permitted.",
  },
  {
    id: "p04",
    title: "Does AI Accelerate AI Research?",
    topic: "AI accelerating AI research",
    pillar: "Hype Check",
    stage: "publish",
    status: "completed",
    owner: "Owner (local)",
    run_id: "r01",
    review_id: "rv03",
    updated_at: `2026-11-12T20:45:00${IST}`,
    note: "Approved and published to the private destination.",
  },
  {
    id: "p05",
    title: "LLM Judges for Identity Resolution",
    topic: "LLM-as-judge accuracy in identity resolution",
    pillar: "AI Engineering",
    stage: "script",
    status: "needs_attention",
    owner: "Owner (local)",
    run_id: "r07",
    review_id: "rv05",
    updated_at: `2026-11-13T07:05:00${IST}`,
    note: "Previous run failed (voice provider); re-run in progress.",
  },
  {
    id: "p06",
    title: "Tesla Wind-Down: Cybertruck",
    topic: "Tesla winding down Cybertruck production",
    pillar: "Automotive",
    stage: "script",
    status: "blocked",
    owner: "Owner (local)",
    run_id: "r08",
    review_id: "rv04",
    updated_at: `2026-11-11T19:05:00${IST}`,
    note: "v1 rejected; v2 script changes requested (human input pending).",
  },
];

/* ---------------------------------------------------------------------- runs */

const stage = (name, state, started, finished, extra = {}) => ({
  name, state, started_at: started, finished_at: finished, ...extra,
});

export const runs = [
  {
    id: "r01",
    project_id: "p04",
    state: "ok",
    attempts: 1,
    max_attempts: 3,
    started_at: `2026-11-12T16:02:00${IST}`,
    finished_at: `2026-11-12T18:31:00${IST}`,
    trigger: "manual: CLI",
    error_code: null,
    promotion: { status: "completed", completed_at: `2026-11-12T20:45:00${IST}` },
    stages: [
      stage("research", "ok", `2026-11-12T16:02:00${IST}`, `2026-11-12T16:21:00${IST}`),
      stage("script", "ok", `2026-11-12T16:21:00${IST}`, `2026-11-12T16:52:00${IST}`),
      stage("visuals", "ok", `2026-11-12T16:52:00${IST}`, `2026-11-12T17:30:00${IST}`),
      stage("voice", "ok", `2026-11-12T17:30:00${IST}`, `2026-11-12T17:44:00${IST}`),
      stage("render", "ok", `2026-11-12T17:44:00${IST}`, `2026-11-12T18:26:00${IST}`),
      stage("review_package", "ok", `2026-11-12T18:28:00${IST}`, `2026-11-12T18:31:00${IST}`),
    ],
  },
  {
    id: "r02",
    project_id: "p06",
    state: "ok",
    attempts: 1,
    max_attempts: 3,
    started_at: `2026-11-11T14:40:00${IST}`,
    finished_at: `2026-11-11T17:12:00${IST}`,
    trigger: "manual: CLI",
    error_code: null,
    promotion: { status: "completed", completed_at: `2026-11-11T17:20:00${IST}` },
    stages: [
      stage("research", "ok", `2026-11-11T14:40:00${IST}`, `2026-11-11T15:02:00${IST}`),
      stage("script", "ok", `2026-11-11T15:02:00${IST}`, `2026-11-11T15:35:00${IST}`),
      stage("visuals", "ok", `2026-11-11T15:35:00${IST}`, `2026-11-11T16:24:00${IST}`),
      stage("voice", "ok", `2026-11-11T16:24:00${IST}`, `2026-11-11T16:41:00${IST}`),
      stage("render", "ok", `2026-11-11T16:41:00${IST}`, `2026-11-11T17:05:00${IST}`),
      stage("review_package", "ok", `2026-11-11T17:09:00${IST}`, `2026-11-11T17:12:00${IST}`),
    ],
  },
  {
    id: "r03",
    project_id: "p01",
    state: "ok",
    attempts: 1,
    max_attempts: 3,
    started_at: `2026-11-13T03:55:00${IST}`,
    finished_at: `2026-11-13T06:42:00${IST}`,
    trigger: "scheduled",
    error_code: null,
    promotion: { status: "completed", completed_at: `2026-11-13T06:50:00${IST}` },
    stages: [
      stage("research", "ok", `2026-11-13T03:55:00${IST}`, `2026-11-13T04:14:00${IST}`),
      stage("script", "ok", `2026-11-13T04:14:00${IST}`, `2026-11-13T04:47:00${IST}`),
      stage("visuals", "ok", `2026-11-13T04:47:00${IST}`, `2026-11-13T05:38:00${IST}`),
      stage("voice", "ok", `2026-11-13T05:38:00${IST}`, `2026-11-13T05:56:00${IST}`),
      stage("render", "ok", `2026-11-13T05:56:00${IST}`, `2026-11-13T06:34:00${IST}`),
      stage("review_package", "ok", `2026-11-13T06:40:00${IST}`, `2026-11-13T06:42:00${IST}`),
    ],
  },
  {
    id: "r04",
    project_id: "p03",
    state: "ok",
    attempts: 1,
    max_attempts: 3,
    started_at: `2026-11-12T12:10:00${IST}`,
    finished_at: `2026-11-12T15:26:00${IST}`,
    trigger: "manual: CLI",
    error_code: null,
    promotion: { status: "completed", completed_at: `2026-11-12T15:40:00${IST}` },
    stages: [
      stage("research", "ok", `2026-11-12T12:10:00${IST}`, `2026-11-12T12:33:00${IST}`),
      stage("script", "ok", `2026-11-12T12:33:00${IST}`, `2026-11-12T13:05:00${IST}`),
      stage("visuals", "ok", `2026-11-12T13:05:00${IST}`, `2026-11-12T14:12:00${IST}`),
      stage("voice", "ok", `2026-11-12T14:12:00${IST}`, `2026-11-12T14:30:00${IST}`),
      stage("render", "ok", `2026-11-12T14:30:00${IST}`, `2026-11-12T15:18:00${IST}`),
      stage("review_package", "ok", `2026-11-12T15:22:00${IST}`, `2026-11-12T15:26:00${IST}`),
    ],
  },
  {
    id: "r05",
    project_id: "p02",
    state: "in_progress",
    attempts: 2,
    max_attempts: 3,
    started_at: `2026-11-13T05:10:00${IST}`,
    finished_at: null,
    trigger: "auto-retry (attempt 2/3)",
    error_code: null,
    promotion: null,
    stages: [
      stage("research", "ok", `2026-11-13T05:10:00${IST}`, `2026-11-13T05:29:00${IST}`),
      stage("script", "ok", `2026-11-13T05:29:00${IST}`, `2026-11-13T06:01:00${IST}`),
      stage("visuals", "warn", `2026-11-13T06:01:00${IST}`, `2026-11-13T06:48:00${IST}`, {
        note: "Storyboard gate=require: review_status=blocked — scene pack held for human storyboard review.",
      }),
      stage("voice", "queued", null, null),
      stage("render", "queued", null, null),
    ],
  },
  {
    id: "r06",
    project_id: "p05",
    state: "failed",
    attempts: 3,
    max_attempts: 3,
    started_at: `2026-11-12T15:40:00${IST}`,
    finished_at: `2026-11-12T18:24:00${IST}`,
    trigger: "scheduled",
    error_code: "voice_provider_unavailable",
    promotion: { status: "failed", completed_at: `2026-11-12T18:24:00${IST}` },
    stages: [
      stage("research", "ok", `2026-11-12T15:40:00${IST}`, `2026-11-12T16:02:00${IST}`),
      stage("script", "ok", `2026-11-12T16:02:00${IST}`, `2026-11-12T16:40:00${IST}`),
      stage("visuals", "ok", `2026-11-12T16:40:00${IST}`, `2026-11-12T17:21:00${IST}`),
      stage("voice", "failed", `2026-11-12T17:21:00${IST}`, `2026-11-12T18:24:00${IST}`, {
        note: "Attempt 3/3 exhausted: voice provider unavailable (error_code=voice_provider_unavailable).",
      }),
    ],
  },
  {
    id: "r07",
    project_id: "p05",
    state: "in_progress",
    attempts: 1,
    max_attempts: 3,
    started_at: `2026-11-13T07:05:00${IST}`,
    finished_at: null,
    trigger: "manual: CLI (after fix)",
    error_code: null,
    promotion: null,
    stages: [
      stage("research", "ok", `2026-11-13T07:05:00${IST}`, `2026-11-13T07:24:00${IST}`),
      stage("script", "running", `2026-11-13T07:24:00${IST}`, null),
      stage("visuals", "queued", null, null),
      stage("voice", "queued", null, null),
    ],
  },
  {
    id: "r08",
    project_id: "p06",
    state: "blocked",
    attempts: 0,
    max_attempts: 3,
    started_at: `2026-11-11T19:30:00${IST}`,
    finished_at: null,
    trigger: "queued after review rejection",
    error_code: "dependency_failed",
    promotion: null,
    stages: [
      stage("script", "blocked", `2026-11-11T19:30:00${IST}`, null, {
        note: "Waiting for requested script changes (human input). Task blocked with error_code=dependency_failed.",
      }),
    ],
  },
];

/* ------------------------------------------------------- autonomy task queue */

export const tasks = [
  {
    id: "9f1c3a2b4d5e6f70819a2b3c4d5e6f70",
    kind: "render_clip",
    state: "running",
    attempts: 2,
    max_attempts: 3,
    priority: 100,
    project_id: "p02",
    run_id: "r05",
    lease_owner: "pipeline-worker-01",
    lease_until: `2026-11-13T11:00:00${IST}`,
    not_before: null,
    error_code: null,
    created_at: `2026-11-13T05:10:00${IST}`,
  },
  {
    id: "b2d4e6f81a3c5e7f90b2d4e6f81a3c5e",
    kind: "verify_claims",
    state: "succeeded",
    attempts: 1,
    max_attempts: 3,
    priority: 100,
    project_id: "p01",
    run_id: "r03",
    lease_owner: null,
    lease_until: null,
    not_before: null,
    error_code: null,
    created_at: `2026-11-13T04:14:00${IST}`,
  },
  {
    id: "c3e5f7a92b4d6e8f01c3e5f7a92b4d6e",
    kind: "package_review",
    state: "succeeded",
    attempts: 1,
    max_attempts: 3,
    priority: 100,
    project_id: "p01",
    run_id: "r03",
    lease_owner: null,
    lease_until: null,
    not_before: null,
    error_code: null,
    created_at: `2026-11-13T06:34:00${IST}`,
  },
  {
    id: "d4f6a8b03c5e7f9a12d4f6a8b03c5e7f",
    kind: "generate_storyboard",
    state: "running",
    attempts: 1,
    max_attempts: 3,
    priority: 80,
    project_id: "p02",
    run_id: "r05",
    lease_owner: "render-worker-01",
    lease_until: `2026-11-13T08:05:00${IST}`,
    not_before: null,
    error_code: null,
    created_at: `2026-11-13T06:48:00${IST}`,
    stale_lease: true,
  },
  {
    id: "e5a7b9c14d6f8a0b23e5a7b9c14d6f8a",
    kind: "voice_render",
    state: "failed",
    attempts: 3,
    max_attempts: 3,
    priority: 100,
    project_id: "p05",
    run_id: "r06",
    lease_owner: null,
    lease_until: null,
    not_before: null,
    error_code: "voice_provider_unavailable",
    created_at: `2026-11-12T17:21:00${IST}`,
  },
  {
    id: "f6b8c9d25e7a9b1c34f6b8c9d25e7a9b",
    kind: "promote_run",
    state: "blocked",
    attempts: 0,
    max_attempts: 3,
    priority: 100,
    project_id: "p05",
    run_id: "r06",
    lease_owner: null,
    lease_until: null,
    not_before: null,
    error_code: "dependency_failed",
    created_at: `2026-11-12T17:21:00${IST}`,
    note: "Child of voice_render — blocked because the parent task failed.",
  },
  {
    id: "a7c9d0e36f8b0a2d45a7c9d0e36f8b0a",
    kind: "collect_analytics",
    state: "queued",
    attempts: 0,
    max_attempts: 3,
    priority: 40,
    project_id: null,
    run_id: null,
    lease_owner: null,
    lease_until: null,
    not_before: `2026-11-13T22:00:00${IST}`,
    error_code: null,
    created_at: `2026-11-12T20:50:00${IST}`,
  },
];

/* ------------------------------------------------------------------ research */

const sig = (t, s, sum, f, e) => ({ title_relevance: t, source_relevance: s, summary_relevance: sum, freshness: f, engagement: e });

export const research = [
  {
    id: "rp01",
    project_id: "p01",
    topic: "AI Agent Funding Doubled 2025",
    status: "verified",
    source_count: 4,
    primary_source_checked: true,
    two_sources_checked: true,
    freshness_days: 2,
    updated_at: `2026-11-13T04:14:00${IST}`,
    claims: [
      {
        id: "c01-1",
        text: "Venture funding for AI agent startups roughly doubled between 2024 and 2025.",
        status: "verified",
        evidence: [
          { source: "Hacker News", url: "example.com/funding-analysis", published: `2026-11-10`, score: 232, rank: 29.1, signals: sig(3, 3, 0, 5.9, 8.2) },
          { source: "Market brief", url: "example.com/agent-market-brief", published: `2026-11-08`, score: 180, rank: 21.4, signals: sig(3, 3, 2, 5.2, 6.8) },
        ],
      },
      {
        id: "c01-2",
        text: "Agent deployments moved from pilots into production at mid-size firms in 2025.",
        status: "supported",
        evidence: [
          { source: "Practitioner survey", url: "example.com/deploy-survey", published: `2026-11-06`, score: 141, rank: 17.9, signals: sig(2, 3, 3, 4.8, 7.1) },
        ],
      },
      {
        id: "c01-3",
        text: "Model-driven experiment shortlisting reduces wasted GPU-hours in research labs.",
        status: "verified",
        evidence: [
          { source: "Research lab blog", url: "example.com/hypothesis-generation", published: `2026-11-09`, score: 376, rank: 17.8, signals: sig(3, 3, 2, 5.9, 8.9) },
        ],
      },
    ],
  },
  {
    id: "rp02",
    project_id: "p02",
    topic: "libghostty 1.0 terminal library release",
    status: "verified",
    source_count: 3,
    primary_source_checked: true,
    two_sources_checked: true,
    freshness_days: 1,
    updated_at: `2026-11-13T05:29:00${IST}`,
    claims: [
      { id: "c02-1", text: "libghostty 1.0 was released as an embeddable terminal library.", status: "verified", evidence: [{ source: "Hacker News", url: "example.com/libghostty", published: `2026-11-12`, score: 341, rank: 17.7, signals: sig(3, 3, 0, 5.9, 8.8) }] },
      { id: "c02-2", text: "The library targets cross-platform embedding rather than end users.", status: "verified", evidence: [{ source: "Author write-up", url: "example.com/ghostty-notes", published: `2026-11-12`, score: 90, rank: 12.2, signals: sig(3, 2, 0, 5.9, 4.1) }] },
    ],
  },
  {
    id: "rp03",
    project_id: "p03",
    topic: "Crusoe data center campus expansion, southeast Wyoming",
    status: "needs_review",
    source_count: 3,
    primary_source_checked: true,
    two_sources_checked: false,
    freshness_days: 3,
    updated_at: `2026-11-12T12:33:00${IST}`,
    claims: [
      { id: "c03-1", text: "Crusoe acquired the southeast Wyoming data center site from Crusoe's partners.", status: "verified", evidence: [{ source: "Hacker News", url: "example.com/crusoe-wyoming", published: `2026-11-12`, score: 51, rank: 18.9, signals: sig(1, 3, 0, 5.9, 5.9) }] },
      { id: "c03-2", text: "The campus expansion is scheduled to complete before Q4 next year.", status: "unverified", evidence: [{ source: "Aggregator post", url: "example.com/dc-timeline", published: `2026-11-05`, score: 22, rank: 6.1, signals: sig(1, 1, 0, 5.1, 2.2) }] },
      { id: "c03-3", text: "Two competing reports describe different capacity figures for the site.", status: "conflicting", evidence: [{ source: "Report A", url: "example.com/capacity-a", published: `2026-11-04`, score: 61, rank: 9.8, signals: sig(2, 2, 1, 5.0, 3.3) }, { source: "Report B", url: "example.com/capacity-b", published: `2026-11-03`, score: 44, rank: 8.2, signals: sig(2, 2, 1, 4.9, 3.0) }] },
    ],
  },
  {
    id: "rp04",
    project_id: "p05",
    topic: "LLM-as-judge accuracy in identity resolution",
    status: "needs_review",
    source_count: 4,
    primary_source_checked: true,
    two_sources_checked: false,
    freshness_days: 1,
    updated_at: `2026-11-13T07:24:00${IST}`,
    claims: [
      { id: "c04-1", text: "An LLM-judge setup reached parity with human review at ~4x lower cost.", status: "verified", evidence: [{ source: "Hacker News", url: "example.com/llm-judges", published: `2026-11-13`, score: 376, rank: 17.8, signals: sig(3, 3, 0, 5.9, 8.9) }] },
      { id: "c04-2", text: "Judge accuracy holds when the schema constrains the output format.", status: "unverified", evidence: [{ source: "Vendor post", url: "example.com/judge-schema", published: `2026-11-11`, score: 88, rank: 10.4, signals: sig(2, 1, 0, 5.5, 4.4) }] },
    ],
  },
  {
    id: "rp05",
    project_id: "p06",
    topic: "Tesla winding down Cybertruck production",
    status: "verified",
    source_count: 3,
    primary_source_checked: true,
    two_sources_checked: true,
    freshness_days: 2,
    updated_at: `2026-11-11T15:02:00${IST}`,
    claims: [
      { id: "c05-1", text: "Tesla is winding down Cybertruck production over several years amid poor sales.", status: "verified", evidence: [{ source: "Hacker News", url: "example.com/cybertruck-wind-down", published: `2026-11-11`, score: 904, rank: 19.1, signals: sig(0, 3, 0, 5.9, 10.2) }] },
      { id: "c05-2", text: "Reported production targets for the line were cut for the next fiscal year.", status: "outdated", evidence: [{ source: "Older report", url: "example.com/older-targets", published: `2026-09-28`, score: 120, rank: 8.8, signals: sig(2, 2, 0, 3.1, 5.0) }] },
    ],
  },
];

/* -------------------------------------------------------------------- studio */

export const studio = [
  {
    project_id: "p01",
    stages: {
      script: { state: "ok", profile: "standard_35s", words: 81, word_range: [72, 92], target_seconds: 35 },
      storyboard: { gate: "require", review_status: "auto_approved" },
      visuals: { state: "ok", mode: "ai_video_scenes", asset_count: 5, quality: "review_ready" },
      voice: { state: "ok" },
      edit: { state: "ok" },
    },
    checklist: { primary_source_checked: true, two_sources_checked: true, claims_verified: true, rights_cleared: true },
    artifacts: [
      { name: "output_short.mp4", path: "outputs/output_short.mp4", sha256: sha("p01-video"), state: "ready" },
      { name: "metadata.json", path: "data/metadata.json", sha256: sha("p01-meta"), state: "ready" },
      { name: "background.mp4", path: "outputs/background.mp4", sha256: sha("p01-bg"), state: "ready" },
      { name: "storyboard.png", path: "outputs/storyboard/p01.png", sha256: sha("p01-sb"), state: "ready" },
    ],
  },
  {
    project_id: "p02",
    stages: {
      script: { state: "ok", profile: "standard_35s", words: 88, word_range: [72, 92], target_seconds: 35 },
      storyboard: { gate: "require", review_status: "blocked", note: "Human storyboard review required before render." },
      visuals: { state: "warn", mode: "ai_video_scenes", asset_count: 2, quality: "draft_only" },
      voice: { state: "queued" },
      edit: { state: "queued" },
    },
    checklist: { primary_source_checked: true, two_sources_checked: false, claims_verified: true, rights_cleared: true },
    artifacts: [
      { name: "storyboard_v2.png", path: "outputs/storyboard/p02_v2.png", sha256: sha("p02-sb"), state: "draft_only" },
      { name: "output_short.mp4", path: "outputs/output_short.mp4", sha256: null, state: "missing", note: "Render queued behind storyboard review." },
      { name: "metadata.json", path: "data/metadata.json", sha256: sha("p02-meta"), state: "draft_only" },
    ],
  },
  {
    project_id: "p03",
    stages: {
      script: { state: "ok", profile: "standard_35s", words: 84, word_range: [72, 92], target_seconds: 35 },
      storyboard: { gate: "require", review_status: "auto_approved" },
      visuals: { state: "ok", mode: "cutout", asset_count: 8, quality: "review_ready" },
      voice: { state: "ok" },
      edit: { state: "ok" },
    },
    checklist: { primary_source_checked: true, two_sources_checked: false, claims_verified: false, rights_cleared: false, note: "2 of 4 claims unresolved; cutout reuse rights restricted." },
    artifacts: [
      { name: "output_short.mp4", path: "outputs/output_short.mp4", sha256: sha("p03-video"), state: "ready" },
      { name: "metadata.json", path: "data/metadata.json", sha256: sha("p03-meta"), state: "ready" },
      { name: "cutout_pack.zip", path: "outputs/cutouts/p03.zip", sha256: sha("p03-cut"), state: "ready" },
    ],
    rights: { status: "restricted", detail: "2 cutouts lack a permitted reuse basis (reuse_rights ≠ permitted)." },
  },
  {
    project_id: "p04",
    stages: {
      script: { state: "ok", profile: "standard_35s", words: 81, word_range: [72, 92], target_seconds: 35 },
      storyboard: { gate: "require", review_status: "auto_approved" },
      visuals: { state: "ok", mode: "ai_video_scenes", asset_count: 5, quality: "review_ready" },
      voice: { state: "ok" },
      edit: { state: "ok" },
    },
    checklist: { primary_source_checked: true, two_sources_checked: true, claims_verified: true, rights_cleared: true },
    artifacts: [
      { name: "output_short.mp4", path: "outputs/output_short.mp4", sha256: sha("p04-video"), state: "ready" },
      { name: "metadata.json", path: "data/metadata.json", sha256: sha("p04-meta"), state: "ready" },
      { name: "background.mp4", path: "outputs/background.mp4", sha256: sha("p04-bg"), state: "ready" },
    ],
  },
  {
    project_id: "p05",
    stages: {
      script: { state: "in_progress", profile: "standard_35s", words: 64, word_range: [72, 92], target_seconds: 35, note: "Below word range (72–92) — script still drafting." },
      storyboard: { gate: "require", review_status: "pending" },
      visuals: { state: "queued", mode: "ai_video_scenes", asset_count: 0, quality: "draft_only" },
      voice: { state: "queued" },
      edit: { state: "queued" },
    },
    checklist: { primary_source_checked: true, two_sources_checked: false, claims_verified: false, rights_cleared: true },
    artifacts: [
      { name: "longform_script.txt", path: "data/longform_script.txt", sha256: sha("p05-ls"), state: "draft_only" },
      { name: "output_short.mp4", path: "outputs/output_short.mp4", sha256: null, state: "missing", note: "Prior run failed at voice." },
    ],
  },
  {
    project_id: "p06",
    stages: {
      script: { state: "changes_requested", profile: "standard_35s", words: 90, word_range: [72, 92], target_seconds: 35, note: "v1 script retained; v2 edits requested by reviewer." },
      storyboard: { gate: "warn", review_status: "auto_approved" },
      visuals: { state: "ok", mode: "cutout", asset_count: 6, quality: "review_ready" },
      voice: { state: "ok" },
      edit: { state: "ok" },
    },
    checklist: { primary_source_checked: true, two_sources_checked: true, claims_verified: false, rights_cleared: true, note: "1 claim outdated after new filing; awaiting refresh." },
    artifacts: [
      { name: "output_short.mp4 (v1, rejected)", path: "outputs/output_short.mp4", sha256: sha("p06-video-v1"), state: "ready" },
      { name: "metadata.json", path: "data/metadata.json", sha256: sha("p06-meta"), state: "ready" },
    ],
  },
];

/* -------------------------------------------------------------------- reviews */

/* Review packages mirror review_bundle.py fields + CF-21 decision outcomes.
   Decisions carry a locally-asserted reviewer label only (no identity store). */

export const reviews = [
  {
    id: "rv01",
    project_id: "p01",
    version: 1,
    status: "pending_human_review",
    created_at: `2026-11-13T06:42:00${IST}`,
    video_sha256: sha("p01-video"),
    metadata_sha256: sha("p01-meta"),
    package_sha256: sha("p01-package"),
    title: "AI Agent Funding Doubled 2025",
    hook: "AI labs now shortlist experiments with models before a single GPU-hour is spent.",
    script_profile: "standard_35s",
    target_duration_seconds: 35,
    word_count: 81,
    word_range: [72, 92],
    visual_quality_status: "review_ready",
    visuals: { mode: "ai_video_scenes", asset_count: 5 },
    claims_summary: { verified: 2, supported: 1, unverified: 0, conflicting: 0 },
    rights_status: "permitted",
    storyboard: { gate: "require", review_status: "auto_approved" },
    qa: { status: "pass" },
    platform_copy: {
      youtube_description: "New analysis suggests agent startup funding doubled through 2025 — and why the bottleneck is shifting to question quality.",
      instagram_caption: "Agent funding doubled in a year. The teams winning aren't guessing which experiments to run.",
      facebook_title: "AI Agent Funding Doubled 2025",
      facebook_description: "A look at what changed in 2025 — and what it means for builders.",
    },
    decision: null,
    pending_ttl_hours: 48,
    history: [
      { at: `2026-11-13T06:42:00${IST}`, event: "Packaged", detail: "review-20261113-0112-ai-agent-funding.json queued (slot promoted)." },
      { at: `2026-11-13T06:50:00${IST}`, event: "Slot promoted", detail: "Became the active pending package (single-slot queue)." },
    ],
  },
  {
    id: "rv02",
    project_id: "p02",
    version: 1,
    status: "pending_human_review",
    created_at: `2026-11-13T06:48:00${IST}`,
    video_sha256: sha("p02-video-wip"),
    metadata_sha256: sha("p02-meta"),
    package_sha256: sha("p02-package"),
    title: "Libghostty 1.0 in 60 Seconds",
    hook: "The terminal just became a library you can embed anywhere.",
    script_profile: "standard_35s",
    target_duration_seconds: 35,
    word_count: 88,
    word_range: [72, 92],
    visual_quality_status: "draft_only",
    visuals: { mode: "ai_video_scenes", asset_count: 2 },
    claims_summary: { verified: 1, supported: 0, unverified: 1, conflicting: 0 },
    rights_status: "permitted",
    storyboard: { gate: "require", review_status: "blocked" },
    qa: { status: "pass" },
    platform_copy: {
      youtube_description: "libghostty 1.0 turns the terminal into an embeddable library. What that unlocks.",
      instagram_caption: "Your terminal is now a library. Here's why that matters.",
      facebook_title: "libghostty 1.0",
      facebook_description: "The terminal as an embeddable component — a quick explainer.",
    },
    decision: null,
    pending_ttl_hours: 48,
    not_approvable: [
      "visual_quality_status=draft_only — the approval gate verifies visuals equality and would refuse this package.",
      "storyboard review_status=blocked under gate=require.",
    ],
    history: [
      { at: `2026-11-13T06:48:00${IST}`, event: "Packaged", detail: "Draft pack queued for early review; visuals still draft-only." },
    ],
  },
  {
    id: "rv03",
    project_id: "p04",
    version: 2,
    status: "approved",
    created_at: `2026-11-12T18:31:00${IST}`,
    video_sha256: sha("p04-video"),
    metadata_sha256: sha("p04-meta"),
    package_sha256: sha("p04-package"),
    title: "Does AI Accelerate AI Research?",
    hook: "Does AI really speed up AI research, or is it just faster noise?",
    script_profile: "standard_35s",
    target_duration_seconds: 35,
    word_count: 81,
    word_range: [72, 92],
    visual_quality_status: "review_ready",
    visuals: { mode: "ai_video_scenes", asset_count: 5 },
    claims_summary: { verified: 2, supported: 1, unverified: 0, conflicting: 0 },
    rights_status: "permitted",
    storyboard: { gate: "require", review_status: "auto_approved" },
    qa: { status: "pass" },
    platform_copy: {
      youtube_description: "New analysis suggests AI tools are accelerating the discovery of valuable hypotheses in machine learning research.",
      instagram_caption: "Is AI actually making AI research faster? A new look at recent data.",
      facebook_title: "Is AI Accelerating AI Research?",
      facebook_description: "New insights suggest AI is helping researchers find valuable hypotheses faster.",
    },
    decision: {
      outcome: "approved",
      decided_at: `2026-11-12T20:11:00${IST}`,
      reviewer_label: "Owner (local)",
      package_sha256: sha("p04-package"),
      note: "Evidence checks out; cleared for the private destination only.",
    },
    history: [
      { at: `2026-11-12T18:31:00${IST}`, event: "Packaged", detail: "Version 2 (v1 expired). Queued for review." },
      { at: `2026-11-12T20:11:00${IST}`, event: "Decision recorded", detail: "APPROVED via local approval CLI with reviewer label." },
    ],
  },
  {
    id: "rv04",
    project_id: "p06",
    version: 1,
    status: "rejected",
    created_at: `2026-11-11T17:12:00${IST}`,
    video_sha256: sha("p06-video-v1"),
    metadata_sha256: sha("p06-meta"),
    package_sha256: sha("p06-package"),
    title: "Tesla Wind-Down: Cybertruck",
    hook: "Tesla is quietly ending the Cybertruck experiment.",
    script_profile: "standard_35s",
    target_duration_seconds: 35,
    word_count: 90,
    word_range: [72, 92],
    visual_quality_status: "review_ready",
    visuals: { mode: "cutout", asset_count: 6 },
    claims_summary: { verified: 1, supported: 0, unverified: 0, conflicting: 0 },
    rights_status: "permitted",
    storyboard: { gate: "warn", review_status: "auto_approved" },
    qa: { status: "pass" },
    platform_copy: { youtube_description: "What the production wind-down means for the truck's future.", instagram_caption: "The Cybertruck experiment is winding down.", facebook_title: "Cybertruck wind-down", facebook_description: "Production is being scaled back over several years." },
    decision: {
      outcome: "rejected",
      decided_at: `2026-11-11T19:05:00${IST}`,
      reviewer_label: "Owner (local)",
      package_sha256: sha("p06-package"),
      note: "Hook overstates the claim; primary source is an aggregation, not the filing. Changes requested for v2.",
    },
    history: [
      { at: `2026-11-11T17:12:00${IST}`, event: "Packaged", detail: "Version 1 queued for review." },
      { at: `2026-11-11T19:05:00${IST}`, event: "Decision recorded", detail: "REJECTED — status recorded in the existing immutable decision-record format." },
    ],
  },
  {
    id: "rv05",
    project_id: "p05",
    version: 1,
    status: "expired",
    created_at: `2026-11-12T16:55:00${IST}`,
    video_sha256: sha("p05-video-exp"),
    metadata_sha256: sha("p05-meta"),
    package_sha256: sha("p05-package"),
    title: "LLM Judges for Identity Resolution",
    hook: "This review pipeline now checks itself at 4x lower cost.",
    script_profile: "standard_35s",
    target_duration_seconds: 35,
    word_count: 76,
    word_range: [72, 92],
    visual_quality_status: "review_ready",
    visuals: { mode: "ai_video_scenes", asset_count: 4 },
    claims_summary: { verified: 1, supported: 0, unverified: 1, conflicting: 0 },
    rights_status: "permitted",
    storyboard: { gate: "require", review_status: "auto_approved" },
    qa: { status: "pass" },
    platform_copy: { youtube_description: "LLM judges reached human parity for identity review at a fraction of the cost.", instagram_caption: "AI reviewing AI output — at 4x lower cost.", facebook_title: "LLM judges at work", facebook_description: "Where automated review actually holds up." },
    decision: null,
    pending_ttl_hours: 48,
    history: [
      { at: `2026-11-12T16:55:00${IST}`, event: "Packaged", detail: "Version 1 queued for review." },
      { at: `2026-11-12T18:24:00${IST}`, event: "Superseded by run failure", detail: "Run r06 failed at voice; package retained but review never decisioned." },
      { at: `2026-11-13T07:00:00${IST}`, event: "Expired", detail: "48h pending TTL reached. Expiry never implies approval — repackage required." },
    ],
  },
  {
    id: "rv06",
    project_id: "p03",
    version: 1,
    status: "approved",
    created_at: `2026-11-12T15:26:00${IST}`,
    video_sha256: sha("p03-video"),
    metadata_sha256: sha("p03-meta"),
    package_sha256: sha("p03-package"),
    title: "Crusoe Wyoming Data Center Build",
    hook: "A data center campus is rising on the Wyoming plains.",
    script_profile: "standard_35s",
    target_duration_seconds: 35,
    word_count: 84,
    word_range: [72, 92],
    visual_quality_status: "review_ready",
    visuals: { mode: "cutout", asset_count: 8 },
    claims_summary: { verified: 1, supported: 0, unverified: 1, conflicting: 1 },
    rights_status: "restricted",
    storyboard: { gate: "require", review_status: "auto_approved" },
    qa: { status: "pass" },
    platform_copy: { youtube_description: "Inside the Wyoming data center campus expansion.", instagram_caption: "The plains are getting a data center the size of a small town.", facebook_title: "Wyoming data center build", facebook_description: "What the campus expansion involves." },
    decision: {
      outcome: "approved",
      decided_at: `2026-11-12T22:40:00${IST}`,
      reviewer_label: "Owner (local)",
      package_sha256: sha("p03-package"),
      note: "Content approved on quality; distribution remains blocked on rights.",
    },
    history: [
      { at: `2026-11-12T15:26:00${IST}`, event: "Packaged", detail: "Version 1 queued for review." },
      { at: `2026-11-12T22:40:00${IST}`, event: "Decision recorded", detail: "APPROVED — approval does not confer a consumable publish authorization." },
    ],
  },
];

/* ------------------------------------------------------------------ publish */

export const publish = {
  policy: {
    public_publishing: "disabled_pending_owner_policy",
    default_destination: "private",
    autonomous_publishing: "disabled",
    upload_window: {
      mode: "opt_in",
      window: "20:00 IST",
      enforced: false,
      note: "Opt-in in the current engine (require_window=false) — not a mandatory gate.",
    },
    note: "Display-only. This screen never triggers uploads, exports or external calls.",
  },
  authorizations: [
    {
      project_id: "p04",
      destination: "private",
      state: "authorized",
      reason_code: null,
      checks: { approval: "pass", qa: "pass", rights: "pass", evidence: "pass", promotion: "pass", window: "na" },
      ledger: { entry_id: "upl_20261112_2045", recorded_at: `2026-11-12T20:45:00${IST}`, destination: "private" },
      note: "Public release intentionally not requested (policy: disabled pending owner decision).",
    },
    {
      project_id: "p01",
      destination: "—",
      state: "blocked_approval",
      reason_code: "blocked_approval",
      reason_detail: "Review rv01 is pending_human_review — approval is required before any publish authorization.",
      checks: { approval: "fail", qa: "pass", rights: "pass", evidence: "pass", promotion: "pass", window: "na" },
      ledger: null,
    },
    {
      project_id: "p02",
      destination: "—",
      state: "blocked_approval",
      reason_code: "blocked_approval",
      reason_detail: "No approvable package: visuals draft_only and storyboard blocked (gate=require).",
      checks: { approval: "fail", qa: "pass", rights: "pass", evidence: "fail", promotion: "na", window: "na" },
      ledger: null,
    },
    {
      project_id: "p03",
      destination: "—",
      state: "blocked",
      reason_code: "rights_not_permitted",
      reason_detail: "Approval rv06 exists, but 2 cutouts lack a permitted reuse basis — approval does not confer authorization.",
      checks: { approval: "pass", qa: "pass", rights: "fail", evidence: "fail", promotion: "pass", window: "na" },
      ledger: null,
    },
    {
      project_id: "p05",
      destination: "—",
      state: "not_ready",
      reason_code: "no_pending_package",
      reason_detail: "Review rv05 expired without a decision; a fresh package is required after the re-run completes.",
      checks: { approval: "fail", qa: "na", rights: "pass", evidence: "fail", promotion: "na", window: "na" },
      ledger: null,
    },
    {
      project_id: "p06",
      destination: "—",
      state: "not_ready",
      reason_code: "decision_rejected",
      reason_detail: "v1 was REJECTED (CF-21 outcome). v2 is blocked awaiting requested script changes.",
      checks: { approval: "fail", qa: "na", rights: "pass", evidence: "fail", promotion: "na", window: "na" },
      ledger: null,
    },
  ],
};

/* ----------------------------------------------------------------- analytics */

export const analytics = {
  range_days: 14,
  note: "Local-first baseline only (data/analytics_latest.json reports “local baseline available”). All figures below are illustrative sample data.",
  kpis: { views_14d: 148320, watch_hours_14d: 5210, net_subs_14d: 940, median_retention_pct: 66 },
  series: [
    { day: "2026-10-31", views: 8100, watch_hours: 280, net_subs: 38 },
    { day: "2026-11-01", views: 9400, watch_hours: 330, net_subs: 44 },
    { day: "2026-11-02", views: 8900, watch_hours: 301, net_subs: 40 },
    { day: "2026-11-03", views: 10600, watch_hours: 372, net_subs: 61 },
    { day: "2026-11-04", views: 12200, watch_hours: 438, net_subs: 72 },
    { day: "2026-11-05", views: 11700, watch_hours: 409, net_subs: 65 },
    { day: "2026-11-06", views: 9800, watch_hours: 336, net_subs: 51 },
    { day: "2026-11-07", views: 8600, watch_hours: 290, net_subs: 42 },
    { day: "2026-11-08", views: 10100, watch_hours: 352, net_subs: 55 },
    { day: "2026-11-09", views: 11400, watch_hours: 402, net_subs: 70 },
    { day: "2026-11-10", views: 12600, watch_hours: 447, net_subs: 78 },
    { day: "2026-11-11", views: 10900, watch_hours: 381, net_subs: 59 },
    { day: "2026-11-12", views: 12800, watch_hours: 458, net_subs: 82 },
    { day: "2026-11-13", views: 13210, watch_hours: 472, net_subs: 83 },
  ],
  quality: [
    { label: "Claims verified at package time", value: 92, tone: "ok", note: "Blocking statuses: unverified, outdated, conflicting, unsupported" },
    { label: "Rights cleared before publish", value: 78, tone: "warn", note: "reuse_rights must be permitted for every cutout" },
    { label: "QA pass rate (render checks)", value: 86, tone: "ok", note: "qa.status must equal pass" },
    { label: "First-pass render rate", value: 71, tone: "warn", note: "retryable failures: render, voice providers" },
  ],
  turnaround: { median_review_hours: 6.2, p90_review_hours: 19.5 },
  pillars: [
    { pillar: "Hype Check", items: 14, views: 41200, retention: 71 },
    { pillar: "Dev Tools", items: 11, views: 33800, retention: 64 },
    { pillar: "AI Engineering", items: 9, views: 27650, retention: 69 },
    { pillar: "Funding Watch", items: 8, views: 22100, retention: 58 },
    { pillar: "Infrastructure", items: 6, views: 18400, retention: 61 },
  ],
};

/* --------------------------------------------------------------- operations */

export const workers = [
  { id: "pipeline-worker-01", kind: "Pipeline runner", state: "healthy", last_heartbeat: `2026-11-13T10:24:00${IST}`, detail: "Executing render_clip (t01) for run r05." },
  { id: "autonomy-worker-01", kind: "Autonomy worker", state: "healthy", last_heartbeat: `2026-11-13T10:26:00${IST}`, detail: "Polling queued tasks; 2 claimable (not_before respected)." },
  { id: "render-worker-01", kind: "Render worker", state: "stale", last_heartbeat: `2026-11-13T07:41:00${IST}`, detail: "Lease on t04 (generate_storyboard) expired at 08:05 — recover on restart." },
  { id: "uploader-01", kind: "Upload worker", state: "paused", last_heartbeat: `2026-11-12T20:45:00${IST}`, detail: "Public publishing disabled pending owner policy; private ledger writes only." },
];

export const incidents = [
  {
    id: "INC-01",
    severity: "high",
    title: "Run r06 failed — voice provider unavailable",
    state: "recovering",
    opened_at: `2026-11-12T18:24:00${IST}`,
    detail: "3/3 attempts exhausted (voice_render, error_code=voice_provider_unavailable). Recovery: provider reconfigured; retry run r07 started 07:05.",
    run_id: "r06",
  },
  {
    id: "INC-02",
    severity: "medium",
    title: "Render worker lease expired",
    state: "open",
    opened_at: `2026-11-13T08:10:00${IST}`,
    detail: "render-worker-01 missed heartbeats; task t04 (generate_storyboard) stalled under an expired lease. Recovery requires worker restart.",
    run_id: "r05",
  },
];

export const models = [
  { provider: "omniroute", model: "groq/openai/gpt-oss-120b", chain: 1, configured: true, ok: true, latency_ms: 2488, checked_at: `2026-10-24T08:52:58${IST}` },
  { provider: "gemini", model: "gemini-3.5-flash-lite", chain: 1, configured: true, ok: true, latency_ms: 2158, checked_at: `2026-10-24T08:53:00${IST}` },
  { provider: "groq", model: "qwen/qwen3.8-27b", chain: 3, configured: true, ok: true, latency_ms: 1213, checked_at: `2026-10-24T08:53:03${IST}` },
  { provider: "ollama", model: "gemma3:4b", chain: 1, configured: false, ok: false, latency_ms: null, checked_at: `2026-10-24T08:53:04${IST}`, error: "not_configured" },
];

/* -------------------------------------------------------------------- events */

export const events = [
  { at: `2026-11-13T10:10:00${IST}`, kind: "ops", tone: "warn", title: "Incident INC-02 opened", detail: "render-worker-01 lease expired — storyboard task stalled." },
  { at: `2026-11-13T09:15:00${IST}`, kind: "review", tone: "info", title: "Review waiting on human decision", detail: "rv01 (AI Agent Funding Doubled 2025) pending_human_review for 3h 28m." },
  { at: `2026-11-13T08:05:00${IST}`, kind: "ops", tone: "warn", title: "Task lease expired", detail: "t04 generate_storyboard lease elapsed; recover on worker restart." },
  { at: `2026-11-13T07:05:00${IST}`, kind: "run", tone: "running", title: "Run r07 started", detail: "Manual re-run for p05 after voice provider fix (INC-01)." },
  { at: `2026-11-13T07:00:00${IST}`, kind: "review", tone: "warn", title: "Review rv05 expired", detail: "48h pending TTL reached — expiry never implies approval; repackage required." },
  { at: `2026-11-13T06:50:00${IST}`, kind: "review", tone: "info", title: "Review packaged", detail: "rv01 became the active pending package (slot promotion)." },
  { at: `2026-11-12T22:40:00${IST}`, kind: "review", tone: "ok", title: "Decision recorded: APPROVED", detail: "rv06 (Crusoe Wyoming) — distribution still blocked on rights." },
  { at: `2026-11-12T20:45:00${IST}`, kind: "publish", tone: "ok", title: "Private upload recorded", detail: "upl_20261112_2045 — destination: private (public release not requested)." },
  { at: `2026-11-12T20:11:00${IST}`, kind: "review", tone: "ok", title: "Decision recorded: APPROVED", detail: "rv03 (Does AI Accelerate AI Research?) via local approval CLI." },
  { at: `2026-11-12T18:24:00${IST}`, kind: "run", tone: "danger", title: "Run r06 failed", detail: "voice_provider_unavailable after 3/3 attempts — incident INC-01." },
  { at: `2026-11-11T19:05:00${IST}`, kind: "review", tone: "danger", title: "Decision recorded: REJECTED", detail: "rv04 (Cybertruck) — v2 changes requested." },
  { at: `2026-11-11T19:30:00${IST}`, kind: "run", tone: "warn", title: "Run r08 blocked", detail: "dependency_failed — waiting for requested script changes." },
];

/* ---------------------------------------------------------------- governance */

export const governance = {
  note: "Display of P0 governance state. Owner-gated: no actions available here, and none may be inferred.",
  decisions: [
    { id: "D01", topic: "WP2/WP3, architecture & security concurrence", status: "pending_owner" },
    { id: "D07", topic: "API/event envelope freeze (with API-LC-01/02/08)", status: "pending_owner" },
    { id: "D09", topic: "No approval without attributable human identity", status: "pending_owner" },
    { id: "D02–D12", topic: "P0 control decisions (remaining)", status: "pending_owner" },
  ],
  api_lc: { label: "API-LC-01..10", status: "open", detail: "Candidate dispositions framed for owners — no selection recorded (M6-F)." },
  gov09: { status: "open", detail: "Narrow conceptual separation recorded (REG-083); record relationship unresolved." },
  m6p_entries: { label: "M6-P ENTRY-01..12", status: "gate_blocked", detail: "Implementation entry gate blocked pending P0 closure." },
  autonomy_publish: { status: "gate_blocked", detail: "Autonomous public publishing disabled pending owner policy." },
};

/* ------------------------------------------------------------------ lookups */

export function projectById(id) {
  return projects.find((p) => p.id === id) || null;
}
export function runById(id) {
  return runs.find((r) => r.id === id) || null;
}
export function reviewById(id) {
  return reviews.find((r) => r.id === id) || null;
}
export function researchById(id) {
  return research.find((r) => r.id === id) || null;
}
export function studioFor(projectId) {
  return studio.find((s) => s.project_id === projectId) || null;
}
export function publishFor(projectId) {
  return publish.authorizations.find((a) => a.project_id === projectId) || null;
}
export function researchFor(projectId) {
  return research.find((r) => r.project_id === projectId) || null;
}
export function tasksForRun(runId) {
  return tasks.filter((t) => t.run_id === runId);
}
export function runForProject(projectId) {
  return runs.filter((r) => r.project_id === projectId);
}
export function reviewsForProject(projectId) {
  return reviews.filter((r) => r.project_id === projectId);
}
