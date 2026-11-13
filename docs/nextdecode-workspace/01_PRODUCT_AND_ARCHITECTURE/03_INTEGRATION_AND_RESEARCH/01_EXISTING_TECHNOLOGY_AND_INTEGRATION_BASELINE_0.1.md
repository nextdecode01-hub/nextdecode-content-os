# NEXTDECODE — Existing Technology and Integration Baseline (Read-Only Inventory)

Document ID: ND-INT-BASE-001
Version: 0.1.0-draft
Date: 2026-11-04
Status: INITIAL INVENTORY — source reconciliation required; not a verified live-system state
Scope: Existing NEXTDECODE Content OS / shorts_studio materials only

## 1. Evidence boundary
This inventory is derived from the currently available README, tooling/provider notes, dependency map, P1 draft architecture and a read-only directory listing. These sources have different dates and may describe different runtime snapshots. No environment variables or secret values were read. No Git command, code change, test, service call or provider probe was performed.

## 2. Existing specialist-engine capabilities visible in README
| Capability | Existing project evidence | Content OS relationship |
|---|---|---|
| Topic discovery and trend selection | app/research/topics.py, trends.py, selector.py | Research capability; adapter boundary to be designed |
| Source reading and evidence extraction | app/research/desk.py, lineage.py, claims.py, atomic.py | Evidence/claim provenance; reconcile to canonical P0/P1 contracts |
| Script and editorial generation | app/script/short.py, studio.py, pipeline.py, evidence.py | Specialist creation engine |
| Voice/TTS | app/voice/provider.py, text_prep.py | Pluggable voice capability |
| Visual planning and assets | app/visuals/motion_director.py, chain.py, storyboard.py, cutouts.py, vision_review.py | Specialist visual-production capability |
| Rendering and media QA | app/render/assembly.py, subtitles.py, audio_diagnostics.py, ffmpeg_tools.py | Local production capability |
| Review and approval | review_bundle.py, approve_review.py, approval_integrity.py, review_ledger.py | Must align with central P0 governance and exact-version approval |
| Publishing adapters | app/publish/ plus root compatibility scripts | Protected side-effect boundary; no bypass of central authorization |
| Scheduling/orchestration | n8n workflow, run scripts, n8n_runner.py | Existing orchestration to reconcile with P0 WP2/WP3 |
| Notifications | notify_review.py, notify_status.py | Private notifications; scope and data minimization to verify |
| Analytics | analytics_collect.py and related modules | Analytics/learning capability; read-only access and consent/scope to verify |

## 3. Existing technology and provider references
| Area | Source-stated technologies | Initial classification |
|---|---|---|
| Application language | Python | Existing implementation fact from repository layout/docs |
| Media processing | FFmpeg, ffprobe | Existing specialist-engine dependency |
| Voice | Edge TTS; ElevenLabs; Cartesia; OpenAI fallback references | Provider chain is source/version-sensitive; verify current implementation/config |
| AI/LLM | Groq, OmniRoute, Gemini, Ollama references | Provider chain and model IDs conflict across dated documents; do not freeze |
| Visual generation | Gemini, fal, Replicate, OpenAI, local FFmpeg references | Existing code/config references; per-provider current status unverified |
| Research/discovery | YouTube Data API, Trends API, Reddit, X references | API availability, terms, quotas and enabled state require separate verification |
| Asset sourcing | Wikimedia Commons; Pexels/Pixabay references | Rights/terms and current API availability must be checked per asset/use |
| Orchestration | n8n | Existing workflow references differ by workflow ID and deployment mode |
| Local data | SQLite references and data/workspace.db | Local state evidence; not a replacement for accepted PostgreSQL-compatible shared-state authority |
| Workspace/storage integrations | Airtable, Notion, Supabase, Cloudinary, R2 references | Candidate/optional integration references; not evidence of active or approved adoption |
| Social platforms | YouTube, Facebook, Instagram; other adapters listed in tooling note | Separate export/publishing capabilities; all external side effects remain gated |
| Notifications | Telegram | Private notification integration reference; current credential/config not checked |
| Tunnel/hosting | cloudflared references | Temporary media-access helper; production architecture decision remains open |

## 4. Source conflicts requiring reconciliation
| Conflict ID | Sources | Conflict | Required action |
|---|---|---|---|
| SRC-INT-001 | README.md vs docs/AI_PROVIDER_STATUS.md | README identifies a different Gemini model/provider state from the 2026-10-22 provider report. | Inspect current provider implementation and non-secret config names; run a separately authorized health verification only if requested. |
| SRC-INT-002 | README.md vs docs/TOOLING_STACK.md | TTS, visual provider order, trend module naming and n8n workflow IDs differ. | Reconcile code entry points, workflow export/live state evidence and document dates. |
| SRC-INT-003 | docs/dependency_map.md vs current repository listing | Dependency map identifies snapshot main @ 6ec4ccf (2026-10-26); it is not a current architecture proof. | Regenerate only under explicit read-only analysis scope; do not run Git commands now. |
| SRC-INT-004 | P0 accepted ADR-002 vs local SQLite references | P0 accepts PostgreSQL-compatible authoritative shared-state store; SQLite appears in local specialist tooling. | Define SQLite only as bounded local cache/legacy/local-worker state if compatible; no competing shared source of truth. |
| SRC-INT-005 | P0/P1 export boundary vs platform publisher modules | Existing publisher scripts exist, but P1 planning does not authorize automatic public publishing. | Keep publisher capability isolated behind central authorization; do not infer permission from code presence. |
| SRC-INT-006 | n8n workflow documentation | README and dependency map refer to different workflow IDs/deployment arrangements and activation states. | Treat live n8n state as UNKNOWN until separately inspected with read-only evidence. |

## 5. Initial agent/component responsibility map (provisional)
| User/agent/service | Potential use | Boundary |
|---|---|---|
| Creator / owner | Review research, scripts, storyboards, quality reports, approvals and export packages | Human decisions remain required for protected actions |
| Research agent | Topic discovery, source triage, claim extraction and evidence synthesis | Cannot certify rights, approve content or publish |
| Fact-check agent | Verify claim/evidence links, contradictions and unsupported statements | Produces findings; governance authority remains central |
| Strategy agent | Use brand, audience and performance evidence to propose priorities | Recommendations only; no silent policy changes |
| Script/editorial agent | Draft/revise content against evidence and brand rules | Must cite input versions and preserve creator override |
| Visual director/production agent | Create shot plans and execute bounded studio tasks | Uses approved assets/rights state; cannot bypass storyboard/quality gates |
| Analytics agent | Collect permitted metrics and produce cohort insights | Read-only scopes; cannot claim causation from correlation |
| Engineering agents | Implement only assigned work packages after authorization | Least privilege, scoped changes, tests and handoff evidence |
| Shorts Studio engine | Execute existing research-to-media production functions | Remains specialist engine; Content OS integrates via explicit adapter contract |
| n8n | Trigger approved/scheduled workflows | Scheduler is not policy authority and cannot authorize publishing |

## 6. Verification gaps
- Current provider health and exact model IDs are not freshly verified.
- Current n8n active workflow ID, timezone and runner target are not freshly verified.
- API scopes, quotas, terms, pricing and licence status are not freshly verified.
- No tool is marked OWNER_APPROVED or ADOPTED by this inventory alone.
- The repository listing is not a complete dependency/SBOM or security audit.
- Current P0 contract freeze and implementation authorization remain governed by the existing P0 records.

## 7. Next work
1. Build source-of-truth register for each tool/provider/module.
2. Map each integration to canonical P0/P1 contract, owner and consuming component.
3. Reconcile the six source conflicts above.
4. Research external candidate repositories and tools using official documentation, repository files, licence and security advisories.
5. Produce candidate scorecards and exact implementation work packages only after architecture fit is demonstrated.
