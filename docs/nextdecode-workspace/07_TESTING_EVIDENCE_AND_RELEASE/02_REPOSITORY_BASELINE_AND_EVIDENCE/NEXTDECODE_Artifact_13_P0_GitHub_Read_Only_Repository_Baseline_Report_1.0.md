# NEXTDECODE Content OS
## Artifact 13 — GitHub Read-Only Repository Baseline Report 1.0

**Inspection mode:** Read-only GitHub connector inspection  
**Report status:** Partial baseline completed; local working-tree state not available  
**Version:** 1.0  
**Inspection date:** 2026-10-31  
**Repository:** `nextdecode01-hub/nextdecode-content-os`  
**Branch inspected:** `main`  
**Inspected revision:** `9d38f81ba4f8022d0e820b6a5e1fe2a0fc288c8c`

---

## 1. Executive summary

The connected GitHub account exposes one relevant repository: `nextdecode01-hub/nextdecode-content-os`. Its README identifies it as **Nextdecode Shorts & Reels Studio (WSL)**. The inspected repository therefore appears to be the GitHub-hosted Shorts Studio codebase, despite the repository name emphasizing Content OS.

The remote `main` branch contains substantial existing production functionality:
- topic discovery, research, and evidence extraction;
- short- and long-form script generation;
- voice generation;
- visual asset sourcing, shot planning, and video rendering;
- quality checks and review packaging;
- human approval tied to video and metadata hashes;
- YouTube, Facebook, and Instagram publishing adapters;
- scheduled generation/publishing orchestration and an n8n runner;
- local SQLite-backed workspace synchronization.

**The existing engine should be preserved and integrated incrementally. A wholesale rewrite is not justified by this inspection.**

However, the latest GitHub snapshot exposes a significant apparent file-move/integration inconsistency: publishing modules and visual-quality code now live under package directories, while several callers and tests still refer to their former root-level locations. This is a high-priority source-level finding that needs local confirmation and a controlled repair plan. Tests were not run under the read-only authorization.

The repository does **not** currently demonstrate the accepted P0 cloud control-plane architecture: PostgreSQL authority, UUIDv7 entity identity, durable transactional queue/outbox/inbox, worker registration and capabilities, centralized authorization contracts, or object-storage artifact abstraction. Those remain future foundation work, not reasons to replace the Shorts Studio production engine.

## 2. Inspection scope and limitations

### 2.1 What was inspected

Read-only GitHub access was used to inspect:
- repository metadata and default branch;
- `main` branch head and latest commit metadata;
- recursive Git tree;
- README and roadmap;
- dependency manifest and Docker/Compose configuration;
- API, generation, review, approval, publishing, and runner source;
- representative tests and dependency-map documentation;
- `.gitignore`, `.dockerignore`, and `.env.example` variable names only.

No secret values were read. `.env`, token files, private credentials, production media, local databases, and customer/personal data were not fetched.

### 2.2 What was not inspected or verified

- Local WSL working-tree status, untracked files, local branches, remotes, and local-only commits.
- Installed Python environment or local dependency versions.
- Runtime behavior or application startup.
- Test execution, lint, build, or type-check results.
- Live n8n instance state or actual active schedules.
- Production credentials, account permissions, publishing readiness, or actual platform uploads.
- Current state of historical blockers G1, G2, G3, U1, D1, Traceability v2, and run-tracker runtime integration unless represented in the inspected repository documentation.

The remote GitHub snapshot may differ from the local WSL directory. This report does not claim the two are byte-for-byte identical.

## 3. Repository identity and remote baseline

| Field | Observed value |
|---|---|
| Repository | `nextdecode01-hub/nextdecode-content-os` |
| Visibility | Private |
| Default branch | `main` |
| Remote repository size | 427 KB (GitHub metadata) |
| Latest inspected commit | `9d38f81ba4f8022d0e820b6a5e1fe2a0fc288c8c` |
| Commit message | `before dashboad impimented` |
| Commit timestamp | 2026-10-30 21:25:35 UTC |
| Parent commit | `42bf6c7727d5c5cf1af696d839c40855cd4df931` |
| Branch protection | Disabled on `main` |
| Recursive tree entries | 128 |
| Test modules | 21 |
| GitHub Actions workflow files | 0 found in inspected tree |
| Dependency lockfiles | None found |
| Requirements manifest | `requirements.txt` |

The latest commit reports changes to files under `app/publish/` and `app/visuals/`, including publisher and visual-quality modules. The current dependency map documentation is dated 2026-10-26 and describes an earlier repository layout; it must be reconciled with the newer 2026-10-30 tree.

**Remote baseline only:** GitHub's branch view does not expose whether the user's local WSL working tree has uncommitted or untracked changes.

Repository: https://github.com/nextdecode01-hub/nextdecode-content-os  
Inspected commit: https://github.com/nextdecode01-hub/nextdecode-content-os/commit/9d38f81ba4f8022d0e820b6a5e1fe2a0fc288c8c

## 4. Project structure observed

| Area | Observed paths | Responsibility |
|---|---|---|
| API wrapper | `api/main.py` | FastAPI job-start/status wrapper |
| Research | `app/research/` | Topic discovery, source retrieval, evidence extraction, ranking |
| Script generation | `app/script/`, `pipelines/` | Short and long-form scripts and editorial pipeline |
| Voice | `app/voice/` | Pluggable narration provider |
| Visual planning/assets | `app/visuals/`, `motion_director.py`, `motion_render.py` | Shot plans, asset sourcing, motion and rendering |
| Short generation | `pipelines/short.py` | Short-form generation entry point |
| Long-form generation | `pipelines/longform.py` | Long-form generation entry point |
| Publishing | `app/publish/` | YouTube, Facebook, Instagram, and YouTube long-form adapters |
| Review/approval | `review_bundle.py`, `review_ledger.py`, `approve_review.py`, `approve_longform.py`, `approval_integrity.py` | Review packages, approvals, integrity checks |
| Scheduling/runner | `n8n_runner.py`, `scheduled_publish.py`, shell scripts, workflow JSON | Scheduled generation and gated publishing |
| Workspace data | `workspace_sync.py` | SQLite-backed content records and synchronization |
| Tests | `tests/` | 21 test modules covering pipeline, research, approval, storage, and reliability |
| Documentation | `README.md`, `ROADMAP.md`, `docs/` | Product, setup, roadmap, provider, and dependency documentation |
| Container | `Dockerfile.runner`, `compose.yaml` | Prepared runner and n8n Compose deployment |

The repository tree contains 128 entries. The structure is a compact Python application with root-level entry points and domain packages, not a separated cloud control-plane service architecture.

## 5. Existing capabilities worth preserving

### 5.1 Research and editorial chain

The strong Short pipeline is described and wired as:

`topic_selector → research_desk → script_studio → voice_provider → motion_director → motion_render → QA`

The research desk fetches and reads sources, extracts claims, and flags unsupported numbers/contradictions. The script studio generates and critiques hooks and scripts. This is a valuable existing production capability to retain behind future Content OS interfaces.

### 5.2 Visual production

The repository contains:
- multi-shot planning with safe zones, cut lengths, motion, and SFX decisions;
- visual asset sourcing and provider fallbacks;
- FFmpeg-based rendering;
- subtitle and audio processing;
- visual-quality classification.

The visual-quality module defines publishable modes and requires asset metadata and licensing fields for stock assets. This is a useful starting point, but it is not yet equivalent to a complete rights-evidence and use-specific rights policy service.

### 5.3 Human review and approval integrity

The current design includes:
- review packages with video and metadata SHA-256 hashes;
- a checklist for human review;
- approval freshness checks using Asia/Kolkata time;
- rejection when the rendered video or metadata no longer matches the approved hashes;
- a visual-quality gate that blocks procedural/unverified visuals from publishing.

This is strong existing safety logic worth preserving. It is currently implemented as local file-based workflow logic rather than the centralized authorization and immutable approval contracts envisioned by the accepted P0 architecture.

### 5.4 Publishing and orchestration

`n8n_runner.py` exposes fixed generation and publishing operations, requires bearer authentication, rejects request bodies, uses a single-execution lock, and forces generation into review mode. The scheduled publishing script checks the 20:00 IST window and delegates to the publisher.

`publish_all.py` contains preflight checks and an all-destination setup gate intended to avoid partial cross-posting.

These are existing operational capabilities, but the live n8n instance and current production schedule were not inspected.

## 6. High-priority findings

### Finding RB-13-01 — Publisher and visual-quality path mismatch

<badge>High priority</badge>

Observed facts:
- The recursive tree contains publisher files under `app/publish/`:
  - `app/publish/youtube_upload.py`
  - `app/publish/youtube_longform_upload.py`
  - `app/publish/facebook_reels_upload.py`
  - `app/publish/instagram_reels_upload.py`
- The tree does not contain root-level `youtube_upload.py`, `youtube_longform_upload.py`, `facebook_reels_upload.py`, or `instagram_reels_upload.py`.
- The tree contains `app/visuals/visual_quality.py`, but no root-level `visual_quality.py`.
- Root-level `publish_all.py` imports `from visual_quality import has_publishable_visuals` and maps platform publishers to root-level script filenames.
- `tests/test_visual_quality.py` imports `from visual_quality import has_publishable_visuals`.
- `tests/test_phase2_storage_layout.py` reads `ROOT / "youtube_upload.py"`.
- The moved publisher files set their path root using `Path(__file__).resolve().parent`, which now resolves to `app/publish/`; their visible source uses that directory for `.env`, `data/`, `outputs/`, or `youtube_token.json` paths, whereas project documentation describes those as root-level project resources.

Assessment:
This appears to be an incomplete package relocation or a set of stale references. It is likely to break imports, publisher discovery, token/config lookup, and storage paths in a clean checkout. This is a source-level finding, not a runtime-confirmed failure, because tests and application code were not executed.

Required follow-up:
1. Confirm the local WSL tree matches this remote commit.
2. Identify the intended canonical module paths and project root semantics.
3. Update imports, publisher discovery, and resource paths consistently.
4. Add regression tests for imports and path resolution.
5. Run the full authorized test suite before accepting the repair.

Do not patch this during the read-only baseline.

### Finding RB-13-02 — Test suite and CI are not currently demonstrated as healthy

<badge>High priority</badge>

Observed facts:
- 21 test modules exist.
- No `.github/workflows/` files were present in the inspected tree.
- No `pytest.ini`, `pyproject.toml`, or dependency lockfile was found.
- `requirements.txt` lists dependencies without pinned versions.
- The test suite was not run.

The roadmap's 91-passed result is dated 2026-10-26 and is historical. It predates the inspected 2026-10-30 commit and cannot be used as evidence that the current `main` branch passes.

Required follow-up:
- reconcile the publisher/path issue first;
- define reproducible runtime and dependency versions;
- add CI only under a separate implementation authorization;
- capture current test results against an exact commit.

### Finding RB-13-03 — API wrapper has a separate security and durability boundary

Observed facts in `api/main.py`:
- job state is held in a process-local Python dictionary;
- job IDs use a shortened UUID string;
- `/start`, `/jobs`, and `/status/{job_id}` are defined without visible authentication dependencies;
- `/start` can start a pipeline subprocess;
- the log directory is created at module import time.

Assessment:
This wrapper is not equivalent to the accepted P0 control plane. If exposed beyond a trusted local boundary, the unauthenticated job-start/status routes would require protection. In-memory job state is not durable across process restarts. Import-time directory creation is a side effect that should be considered when the module is imported by tests or tools.

This does not establish that the API is publicly exposed. Deployment/network exposure was not inspected.

### Finding RB-13-04 — Existing state is local-file/SQLite oriented

Observed facts:
- `workspace_sync.py` imports `sqlite3` and creates `data/workspace.db`.
- Review, approval, metadata, and generated artifacts use local JSON/files under `data/` and `outputs/`.
- The repository has no visible PostgreSQL migration framework or transactional outbox/inbox implementation in the inspected tree.

Assessment:
This is suitable evidence of the existing studio's local operating model, but it does not satisfy ADR-002/ADR-003's accepted authoritative shared database and durable queue direction.

Required follow-up:
Keep the local studio state model behind a future adapter boundary. Do not abruptly replace it or assume its SQLite workspace database is the future shared control-plane database.

### Finding RB-13-05 — Repository guardrails need strengthening

Observed facts:
- `main` is not protected according to GitHub branch metadata.
- No CI workflow files were found.
- No pinned dependency lockfile was found.
- `.gitignore` and `.dockerignore` do contain explicit exclusions for environment files, tokens, credentials, local databases, and generated media.
- `.env.example` contains variable names and placeholders; no secret values were read.

Assessment:
Secret and generated-file ignore rules are a useful baseline. Branch protection, automated checks, and dependency reproducibility are not established by the inspected repository configuration.

## 7. ADR-001–ADR-010 implementation mapping

These statuses describe the current repository's visible evidence, not owner acceptance of new contracts.

| ADR | Evidence in current repository | Baseline status |
|---|---|---|
| ADR-001 — UUIDv7 canonical IDs | Local workspace record IDs and short API job IDs are visible; no UUIDv7 canonical domain-ID contract found | NOT FOUND for accepted canonical identity contract |
| ADR-002 — PostgreSQL-compatible authoritative DB | `workspace_sync.py` uses SQLite; JSON/files are used for review and pipeline state | NOT FOUND |
| ADR-003 — Durable queue + transactional outbox/inbox | n8n runner and local scheduled scripts exist; no transactional outbox/inbox implementation found | NOT FOUND |
| ADR-004 — Versioned HTTP/JSON + schema validation | FastAPI wrapper and fixed runner endpoints exist; no shared versioned contract/schema layer identified | PARTIALLY IMPLEMENTED |
| ADR-005 — Unique worker identity and scoped credentials/capabilities | Runner uses a shared bearer key; no worker registration/capability model identified | NOT FOUND |
| ADR-006 — Relational artifact metadata + object storage abstraction | Local metadata JSON and local media/archive paths exist; no object-storage abstraction identified | NOT FOUND |
| ADR-007 — Centralized authorization; adapters cannot bypass | Local review approval and publisher checks exist; separate adapters and API wrapper exist; centralized authorization boundary not established | PARTIALLY IMPLEMENTED |
| ADR-008 — Four QA outcomes and hard blockers | Visual checks and review-ready/draft-only statuses exist; accepted four-outcome contract not identified | PARTIALLY IMPLEMENTED |
| ADR-009 — Evidence-backed, use-specific rights | Stock asset title/license metadata and visual publishability checks exist; full use-specific rights evidence/state model not identified | PARTIALLY IMPLEMENTED |
| ADR-010 — Separate lifecycle state machines | Separate review/publish scripts and statuses exist; formal per-entity lifecycle contracts not identified | PARTIALLY IMPLEMENTED |

No ADR is marked `IMPLEMENTED — VERIFIED`, because no tests or runtime checks were executed during this inspection.

## 8. Historical blocker reconciliation

| Item | Current result |
|---|---|
| G1 | NOT RECONCILED — original acceptance criterion not located in inspected files |
| G2 | NOT RECONCILED — original acceptance criterion not located in inspected files |
| G3 | NOT RECONCILED — original acceptance criterion not located in inspected files |
| U1 | NOT RECONCILED — original acceptance criterion not located in inspected files |
| D1 | NOT RECONCILED — original acceptance criterion not located in inspected files |
| Traceability v2 | NOT RECONCILED — original acceptance criterion not located in inspected files |
| Run-tracker runtime integration | NOT RECONCILED — original acceptance criterion not located in inspected files |

The repository has `review_bundle.py`, `review_ledger.py`, and phase tests, but their existence alone does not prove closure of the historical identifiers. Original engineering reports or acceptance criteria are needed to reconcile them accurately.

## 9. Reuse and gap recommendation for NEXTDECODE Content OS

### 9.1 Preserve and integrate

Recommended to preserve:
- `app/research/` research and source-evidence pipeline;
- `app/script/` short/long-form editorial engines;
- `app/voice/` narration provider abstraction;
- `app/visuals/`, `motion_director.py`, and `motion_render.py`;
- `pipelines/short.py` and `pipelines/longform.py` as specialized production entry points;
- review-package and hash-bound approval logic;
- publisher adapters, after the path/layout inconsistency is reconciled;
- `n8n_runner.py` as an existing integration adapter, not as the authoritative P0 orchestrator.

### 9.2 Build as a separate P0 foundation

Still needed for the accepted Content OS architecture:
- canonical UUIDv7 entity identity and explicit domain contracts;
- authoritative PostgreSQL-compatible shared persistence;
- durable job model and transactional outbox/inbox;
- versioned API contracts and schema validation;
- worker registration, identity, scoped credentials, capabilities, and revocation;
- centralized authorization decisions;
- artifact metadata/versioning and object-storage transfer abstraction;
- formal QA outcome and rights-evidence contracts;
- audit/correlation and lifecycle transition enforcement.

### 9.3 Integration principle

Do not rewrite the existing Shorts Studio engine to fit the new control plane. Wrap its production capabilities behind a bounded worker/adapter contract. The cloud control plane should own shared workflow state, identity, policy, and approvals; the existing studio should remain a specialized execution engine.

## 10. Proposed work allocation (not authorized)

| Work package | Proposed focus | Suggested owner from existing role plan | Notes |
|---|---|---|---|
| WP-0 | Confirm local/remote parity and capture exact baseline | OpenCode, if separately assigned | First resolve whether WSL matches GitHub `main` |
| WP-1 | Reconcile current publisher/visual-quality path inconsistency | Qoder or OpenCode, owner to decide | Keep narrow; tests required |
| WP-2 | Freeze P0 contracts and schema | Qoder, if separately assigned | Only after Artifact 08 owner approval |
| WP-3 | Identity, authorization, job/lease/queue foundation | Qoder, if separately assigned | New control-plane foundation |
| WP-4 | Worker adapter around Shorts Studio | Qoder, if separately assigned | Avoid invasive engine changes |
| WP-5 | Artifact metadata/transfer abstraction | To be assigned | Preserve local execution option |
| WP-6 | Independent QA and evidence review | Kilo, read-only | Exact revision and test evidence required |

This table is a proposal only. No agent task has been issued. Qoder, OpenCode, and Kilo roles are unchanged.

## 11. Recommended next sequence

1. Confirm that the local WSL repository is intended to match GitHub `main` at `9d38f81`.
2. Obtain a local read-only status/branch/commit snapshot, because GitHub cannot reveal local uncommitted or untracked work.
3. Reconcile the package move for publishers and visual-quality modules before using the current remote tree as an implementation baseline.
4. Run the test suite only after separate test-execution authorization; capture exact commands and results.
5. Locate original G1/G2/G3/U1/D1, Traceability v2, and run-tracker acceptance reports.
6. Review and freeze Artifact 08 contracts.
7. Approve a single bounded implementation package and issue a separate authorization.

## 12. Read-only confirmation

- GitHub repository metadata, tree, and file contents were read.
- No GitHub write operation was called.
- No files, branches, commits, pull requests, issues, settings, or workflows were changed.
- No local WSL files were accessed.
- No tests or application code were executed.
- No secrets or private credential values were read.
- No deployment, upload, or publishing action was performed.

**Baseline conclusion:** `BASELINE PARTIAL — OWNER DECISIONS AND LOCAL PARITY CHECK REQUIRED`

**Implementation authorization:** NOT ISSUED  
**Agent task assignment:** NONE  
**Deployment/production/publishing authorization:** NOT ISSUED

**End of Artifact 13 — P0 GitHub Read-Only Repository Baseline Report 1.0**
