# NEXTDECODE Content OS

**Decode what comes next.**
NEXTDECODE Content OS is a local-first, human-governed system for researching, commissioning, producing, reviewing and preparing multi-format content for the NEXTDECODE media brand.

The system is designed to support more than one channel and more than one content format. Each channel has its own editorial profile, audience promise, topic eligibility, history and feedback signals. Shared infrastructure must not cause one channel's topic history or audience signals to leak into another.

> **Release status (17 November 2026):** Active development baseline. The current main branch has a passing local Python and dashboard test baseline, but this repository is **not yet declared v1.0.0 LTS or production-release-ready**. See [release readiness](#release-readiness).

## Product principles

- **Story-first:** one researched story package is the editorial source of truth; formats are adaptations of that story, not unrelated content streams.
- **Evidence-led:** factual claims need traceable sources and claim provenance. Unsupported claims must be revised, qualified or removed.
- **Visuals serve the beat:** visual selection should support the exact narration beat, not fill time with loosely related stock footage.
- **Faceless documentary production:** no on-camera presenter is required. Use relevant footage, archive, original graphics, maps, diagrams, screen recordings and narration.
- **Local-first and free-first:** prefer local execution and free/open tools. No paid provider activation or dependency installation is implied by this repository.
- **Human-governed:** human review is required before publishing. Public publishing is a separately protected action and must not be inferred from generation or editorial approval.
- **Fail closed:** missing rights, provenance, approval, integrity or destination requirements must block the protected action rather than silently downgrade it.

## Current channel: NEXTDECODE

The active channel profile is `config/channels/nextdecode.v1.json`.

**Audience promise:** evidence-led documentaries and explainers that decode important changes in technology, business, economics and the future.

**Primary editorial lanes:**
- AI and artificial intelligence
- Technology and innovation
- Startups and entrepreneurship
- Business and economics
- Markets and industry shifts
- Future trends

Related areas are eligible only when they connect clearly to this audience promise. General-interest topics such as unrelated sports, wildlife, celebrity entertainment, true crime or geopolitics are not automatically in scope.

See [channel strategy and format contract](docs/architecture/NEXTDECODE_CHANNEL_STRATEGY_AND_FORMAT_CONTRACT_2026-11-17.md).

## Content formats and implementation status

The format registry is maintained in `app/content/formats.py`. The registry deliberately distinguishes an intended channel format from an executable producer.

| Format | Current status | Important boundary |
|---|---|---|
| YouTube Shorts | Supported producer | Vertical short-video generation; publishing remains separately authorized |
| Instagram Reels | Supported producer | Reuses the vertical short-video producer; generation support does not imply destination readiness |
| Facebook Reels | Supported producer | Reuses the vertical short-video producer; generation support does not imply destination readiness |
| YouTube long-form | Supported with constraints | Separate horizontal producer; real renders remain drafts until reviewed and authorized |
| YouTube Community posts | Not implemented | No complete post artifact, QA and approval chain |
| Instagram posts | Not implemented | No complete image-post artifact, QA and approval chain |
| Instagram carousels | Not implemented | No complete slide-pack artifact, QA and approval chain |
| Facebook posts | Not implemented | No complete post artifact, QA and approval chain |
| LinkedIn posts | Not implemented | No complete post artifact, QA and approval chain |
| X posts/threads | Not implemented | No complete post/thread artifact, QA and approval chain |

The word **supported** above refers to a generation producer, not an unconditional promise of production readiness or successful platform publishing. Format routing rejects unknown and unimplemented formats. See the [content-format routing contract](docs/architecture/NEXTDECODE_CONTENT_FORMAT_ROUTING_CONTRACT_2026-11-17.md).

## System architecture

The repository is a modular Python application with a dashboard and local production tooling. Important areas:

| Area | Responsibility |
|---|---|
| `api/` | Authenticated API and job entrypoints |
| `app/research/` | Topic discovery, channel fit, source retrieval, lineage and claim evidence |
| `app/script/` | Editorial commissioning, scripts, beat plans and production storyboards |
| `app/content/` | Content-format capability registry and routing contract |
| `app/visuals/` | Visual intent, asset discovery/resolution, storyboard and visual QA |
| `app/voice/` | Narration providers and speech preparation |
| `app/render/` | Timeline, FFmpeg assembly, captions, audio and render QA |
| `app/providers/` | Model and media-provider adapters, routing and health |
| `app/tracking/` | Run identity, manifests, artifact hashes and lifecycle records |
| `app/publish/` | Platform adapters and shared publishing authorization |
| `app/autonomy/` | Agent/task execution and policy boundaries |
| `app/brain/` | Project context, routing and autonomy observation |
| `dashboard/` | React/Vite operations dashboard |
| `config/channels/` | Channel-specific editorial and format configuration |
| `docs/` | Architecture contracts, operational guidance and source-of-truth records |
| `reports/` | Dated implementation, audit and verification evidence |
| `tests/` | Python regression and contract tests |
| `tools/` | Audits, research and production utilities |

The current production flow is conceptually:

`Channel profile → topic discovery → research and claim evidence → editorial angle → script → beat/storyboard → asset acquisition and rights review → edit/render → QA → human review → protected publishing authorization`

Not every stage or format is equally mature. The architecture and reports distinguish implemented behavior from planned capabilities; do not infer implementation from a roadmap item.

## Quick start (WSL)

The project is developed in WSL. From the repository root:

```bash
cd ~/shorts_studio
```

Use the project's Python environment. On the current machine the active environment is `venv`:

```bash
./venv/bin/python --version
./venv/bin/python setup_check.py
```

Create a private local `.env` from `.env.example` only if one does not already exist. Never overwrite an existing local credentials file:

```bash
cp .env.example .env
chmod 600 .env
```

Edit `.env` locally and supply only the providers and platform credentials you intentionally configure. **Never commit `.env`, OAuth tokens, API keys, private keys or credential exports.** The setup checker is designed to report readiness without printing credential values or publishing.

Install dependencies only in a deliberately prepared environment and according to the project's dependency policy:

```bash
./venv/bin/python -m pip install -r requirements.txt
```

For account-specific provider and platform setup, read [required setup](docs/REQUIRED_SETUP.md) and [Meta Reels setup](docs/META_REELS_SETUP.md). Provider availability, quotas and platform permissions can change; verify them before enabling a live integration.

## Run and review

- The canonical short producer is `pipelines/short.py`.
- The canonical long-form producer is `pipelines/longform.py`.
- The strong editorial pipeline is implemented under `app/research/`, `app/script/` and `app/visuals/`.
- Use the documented scripts and module entrypoints from the repository root. Do not recreate retired root-level compatibility wrappers.
- A generated video is a draft, not publishing authorization.
- Inspect the complete video, source claims, storyboard/contact sheet, visual relevance, rights and metadata before requesting human approval.
- Dry-run artifacts are mechanics checks only. They are not narration-backed editorial work and must remain marked not-for-publish.

Useful local commands:

```bash
# Safe local setup/readiness report
./venv/bin/python setup_check.py

# Full Python regression suite
PYTHONPATH=. ./venv/bin/python -m pytest -q --disable-warnings

# Dashboard tests
cd dashboard
npm test -- --run

# Dashboard type-check and production build
npm run build
```

A local dry run does not prove live provider access, production editorial quality, platform credentials or publishing readiness. Follow the specific producer contract and keep its storyboard/rights gates intact.

## Governance and publishing safety

Publishing is protected by the shared boundary in `app/publish/authorization.py` and the orchestration/adapters under `app/publish/`.

- Human review and approval are mandatory before publishing.
- Approval must bind to the exact current artifact/metadata version and integrity digests.
- Rights, source evidence, storyboard status, destination policy and upload-time artifact integrity are separate checks.
- Public publishing requires its own explicit authorization; an editorial approval is not a public-release grant.
- Do not use live platform credentials or real uploads as smoke tests.
- The autonomous task/agent system is not allowed to bypass the protected publishing boundary.
- Unknown or ambiguous rights must not be treated as permission.

See [publishing package governance](app/publish/README.md), [documentation index](docs/README.md), and the accepted project decision records in the [NEXTDECODE workspace index](docs/nextdecode-workspace/00_CONTROL_AND_INDEX/00_MASTER_INDEX.md).

## Testing and CI

The repository's GitHub Actions workflow is `.github/workflows/ci.yml`. It currently checks Python 3.14 compilation, shell syntax, dependency consistency and the Python test suite. The dashboard has its own Vitest suite and Vite production build, which should be run locally as shown above.

Latest local verification for this baseline (17 November 2026):
- Python: **1,439 passed, 12 skipped, 75 subtests passed**.
- Dashboard: **10 test files passed, 26 tests passed**.
- Dashboard production build: passed, with a bundle-size warning (main JavaScript chunk exceeds 500 kB).

These are dated local results, not a claim that GitHub Actions has passed for every commit or that a real production run has succeeded. Re-run checks after changes and inspect the Actions result for the exact pushed commit.

## Roadmap and release readiness

The strategic roadmap is staged: end-to-end reliability; research/story intelligence; visual intelligence and production quality; multi-format production; publishing governance; analytics and learning; post/carousel formats; then isolated multi-channel support.

**LTS is not yet declared.** Before tagging a production release, the owner must have evidence for:
1. A clean checkout install and recovery path.
2. Full CI on the exact release commit.
3. A real end-to-end production run, with artifacts and stage evidence.
4. Rights/provenance and storyboard gates enforced across the complete asset set.
5. Human approval, protected publishing authorization, private-destination defaults and upload integrity.
6. Dashboard functional/security acceptance and API authorization review.
7. Backup, restore, operational monitoring and rollback procedures.
8. Release notes, known limitations and an owner-approved release tag.

Until these are evidenced, treat the repository as an active development baseline—not a production LTS release.

## Documentation and change control

Start here:
- [Documentation map and source-of-truth rules](docs/README.md)
- [Content OS architecture](docs/architecture/NEXTDECODE_BRAIN_FOUNDATION.md)
- [Channel strategy](docs/architecture/NEXTDECODE_CHANNEL_STRATEGY_AND_FORMAT_CONTRACT_2026-11-17.md)
- [Format routing contract](docs/architecture/NEXTDECODE_CONTENT_FORMAT_ROUTING_CONTRACT_2026-11-17.md)
- [Story-first production upgrade](docs/production/NEXTDECODE_STORY_FIRST_DOCUMENTARY_PRODUCTION_UPGRADE_2026-11-17.md)
- [Reports and agent evidence](reports/README.md)
- [Operational roadmap](docs/ROADMAP.md)

Preserve the accepted architecture, owner decisions and P0 source-of-truth documents. Make incremental changes in place. Do not restart or redesign the project, remove historical evidence, enable paid providers, or publish publicly without the required owner authorization.

The previous Shorts & Reels operator guide is preserved at [README_SHORTS_STUDIO_LEGACY_2026-11-17.md](docs/archive/legacy-guides/README_SHORTS_STUDIO_LEGACY_2026-11-17.md). It is historical reference material and is not the current product contract.
