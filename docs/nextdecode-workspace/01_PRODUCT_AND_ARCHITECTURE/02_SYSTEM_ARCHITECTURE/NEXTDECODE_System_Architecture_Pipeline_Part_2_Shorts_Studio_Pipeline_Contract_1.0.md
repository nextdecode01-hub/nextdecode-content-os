# NEXTDECODE System Architecture & Pipeline
## Part 2 — Shorts Studio Pipeline Contract 1.0

**Status:** Architecture draft  
**Purpose:** Reusable technical reference for future coding agents.  
**Relationship:** `NEXTDECODE_Master_Blueprint_2.0` defines the product vision and scope (WHAT/WHY). This document maps the Shorts Studio pipeline and its proposed technical boundaries (HOW).

---

## 1. Scope, evidence labels and agent instructions

This document is based on the Phase 10 and Phase 11 reconciliation reports and the pipeline mapping completed in the architecture discussion. It is a report-based map, not a fresh repository inspection.

Use these labels:
- **Implemented (report-backed):** Reported as implemented.
- **Partially Implemented:** Some functionality exists, but enforcement, integration or runtime behavior is incomplete.
- **Proposed:** Target design; not an existing implementation.
- **Not Verified:** Available evidence does not prove end-to-end behavior.

**Instructions for future coding agents**
1. Read this document with `NEXTDECODE_Master_Blueprint_2.0`.
2. Verify the current authorized repository state before implementation; report discrepancies.
3. Do not treat this document as authorization to edit code, tests, config, docs, dependencies, Git state or deployments.
4. Do not perform Git/GitHub operations without explicit owner authorization.
5. Preserve existing WIP. Never reset, revert, overwrite or clean up unrelated changes.
6. Do not install dependencies or run production uploads/publishing without explicit approval.
7. If repository evidence differs, report it; do not silently force code to match this document.

## 2. End-to-end Shorts Studio pipeline

Logical stage sequence:

```text
Topic / Brief
  -> Research and Evidence
  -> Claim Ledger
  -> Script
  -> Storyboard and Shot Planning
  -> Visual Assets
  -> Rendering
  -> QA
  -> Review Package
  -> Approval
  -> Publishing
  -> Analytics and Learning
```

This is a logical map. It does not prove that every stage is controlled by one orchestrator or that every direct entry point follows the complete chain.

## 3. Stage-by-stage pipeline contract

### 3.1 Research
**Reported components:** `app/research/topics.py`, `app/research/desk.py`, `app/research/claims.py`, `app/research/lineage.py`  
**Status:** Partially Implemented.

**Purpose:** Topic discovery/processing, research gathering, evidence preparation and source lineage.

**Known gaps:** Trend radar, competitor intelligence and systematic content-gap analysis are not established as implemented. A stable, versioned research-package contract is not fully verified.

**Proposed output:** Stable research-package ID; topic/brief references; source records and retrieval metadata; evidence excerpts/summaries; timestamp and provenance; uncertainty and missing-evidence markers.

**Proposed failure behavior:** Preserve partial research and diagnostics; clearly mark incomplete work; allow safe retries without corrupting existing records.

### 3.2 Claim Ledger
**Reported components:** `app/research/claims.py`, `app/research/lineage.py`, `app/script/evidence.py`  
**Status:** Partially Implemented.

**Purpose:** Track factual claims, supporting evidence and source relationships.

**Known gaps:** Unsupported claims are not consistently enforced as publish blockers. One Phase 11 trace run reported 4 of 9 beats linked to claims and 3 beats marked `evidence_missing`. Complete claim-to-rendered-shot traceability is not established.

**Proposed output:** Claim ID/text; supporting source IDs; evidence and review status; downstream script-section, beat and shot references.

**Proposed failure behavior:** Missing evidence remains visible. Unsupported claims cannot silently become verified. Central policy determines publish eligibility.

### 3.3 Script
**Reported components:** `app/script/pipeline.py`, `app/script/studio.py`, `app/script/evidence.py`  
**Status:** Partially Implemented.

**Purpose:** Generate/refine scripts, review quality and associate factual statements with evidence.

**Known gaps:** Exact schemas, quality thresholds and all runtime contracts are not fully verified.

**Proposed output:** Stable script ID/version; format and target-duration metadata; structured sections/beats; claim references; generation provenance and review status.

**Proposed failure behavior:** Preserve the last valid version. A failed rewrite must not overwrite an accepted script. Record validation failures.

### 3.4 Storyboard and Shot Planning
**Reported components:** `app/visuals/beats.py`, `app/visuals/shotplan.py`, `app/visuals/storyboard.py`, `app/visuals/chain.py`  
**Status:** Partially Implemented.

**Purpose:** Convert script structure into beats, shots, timing and scene organization.

**Known gaps:** G1 storyboard gate defaults to `warn`; `needs_review` can proceed to rendering. Stable traceability across beats, shots and rendered outputs is incomplete. A frozen plan hash is not established.

**Proposed output:** Versioned storyboard and shot plan; stable beat/shot IDs; timing and visual intent; relevant claim references; validation result; gate status; immutable plan hash/version.

**Proposed failure behavior:** Hard-fail validation stops dependent rendering. `needs_review` routes to review, not ordinary pass. Exceptions must be explicit and recorded.

### 3.5 Visual Assets
**Reported components:** `app/visuals/chain.py`, `app/visuals/cutouts.py`, `app/visuals/vision_review.py`  
**Status:** Partially Implemented.

**Purpose:** Find, prepare, select and review visual assets while carrying metadata and rights information.

**Known gaps:** G2 rights gate is calculated but not reliably consumed by publishing. Unknown rights are not reliably blocking. A centralized rights registry is not established.

**Proposed output:** Asset ID/source/provider; asset reference; intended shot/beat; rights/license evidence; attribution requirements; review status; provenance.

**Proposed failure behavior:** Unknown rights are not cleared rights. Rights failures block distribution until resolved. Substitutions preserve provenance and trigger revalidation where required.

### 3.6 Rendering
**Reported components:** `app/render/assembly.py`, `app/render/ffmpeg_tools.py`, `app/render/shots.py`, `app/render/subtitles.py`, `motion_render.py`  
**Status:** Partially Implemented; traceability incomplete.

**Report-backed evidence:** Phase 11 describes two strong-pipeline E2E runs producing 1080x1920 H.264/AAC MP4s with QA `pass`. One trace run reported 14 shots and 9 beats.

**Known gaps:** Stable shot-to-render identity is incomplete; complete per-shot render manifest and plan hash are not established. Direct `app.script.pipeline` entry was reported to bypass controls present in the higher-level path.

**Proposed output:** Video artifact; render metadata/properties; per-shot render manifest; source plan/storyboard version and hash; asset/audio/subtitle references; logs and diagnostics; QA handoff status.

**Proposed failure behavior:** Preserve last known-good output. Failed renders must not replace accepted artifacts. Record failure stage and diagnostics. Retries must be safe.

### 3.7 Quality Assurance (QA)
**Status:** Partially Implemented.

A technical QA `pass` does not by itself prove factual support, cleared asset rights, completed storyboard review, human approval or publishing authorization.

**Known gaps:** Unsupported claims are warnings rather than consistent publish blockers; `needs_review` storyboard can proceed under `warn`; rights are not reliably enforced at publishing; one central fail-closed policy decision is not established.

**Proposed gate categories:** Technical validity; factual evidence; storyboard/shot-plan validation; asset rights/attribution; brand/format compliance; review/approval eligibility.

**Proposed failure behavior:** Hard blockers stop progression. Warnings remain distinct from blockers. Gate results record policy version, checks and reasons. Downstream components cannot reinterpret blocked as approved.

### 3.8 Review Package
**Reported component:** `review_bundle.py`  
**Status:** Partially Implemented.

**Purpose:** Package artifacts, provenance, hashes and review information.

**Known gaps:** Review provenance and artifact hashes are reported, but direct pipeline paths do not consistently receive run tracking and the complete review lifecycle.

**Proposed output:** Review package ID; content/run ID; artifact references and hashes; script/storyboard/shot-plan/render versions; QA and rights results; warnings/blockers; approval request metadata.

**Proposed failure behavior:** Review packages are immutable snapshots or explicitly versioned. Material artifact changes reopen/invalidate approval.

### 3.9 Approval
**Reported component:** `approve_review.py`  
**Status:** Partially Implemented.

**Known gaps:** File-based and partial approval; one global approval slot reported; roles/signatures not established; some direct publishing paths bypass intended parent-level controls.

**Proposed target:** Per-content-item approval; states such as pending, approved, rejected, changes requested, expired and revoked; reviewer/timestamp where supported; approval bound to exact artifact hashes and policy version.

**Proposed failure behavior:** Pending means hold. Rejection/changes requested means do not publish. Approval of one artifact version cannot authorize another. Ordinary approval cannot override hard rights/safety/validation blockers.

### 3.10 Publishing
**Reported components:** `app/publish/`, `publish_all.py`, `publish_social.py` and platform adapters  
**Status:** Partially Implemented; production publishing not verified.

**Known gaps:** Direct adapters can publish publicly without expected approval. `publish_social.py --execute` was reported to skip approval. Direct `app.script.pipeline` entry can bypass QA, run identity, approval and sanitized failure handling. No real production publishing was verified.

**Proposed target:** Central distribution authorization before every external action; platform-specific policy; idempotency/duplicate protection; persistent publishing ledger; clear dry-run/private-test/scheduled/public modes; human approval or conditional auto-publishing only under an explicitly owner-approved policy.

**Proposed failure behavior:** Fail closed if approval, rights, identity or required QA evidence is missing. Retry safely. Record outcomes without exposing secrets. Never treat pending/failed as success.

## 4. Cross-cutting findings

| Area | Report-based finding | Status |
|---|---|---|
| Pipeline entry points | Direct script pipeline can bypass controls in higher-level path | Risk |
| Run identity | Tracker wired in `pipelines/short.py`; runtime integration unverified | Not Verified end-to-end |
| Persistent jobs | API jobs are in memory | Gap |
| API security | API reported unauthenticated | Gap |
| Approval | Single global slot; no roles/signatures | Gap |
| Asset rights | No centralized rights registry | Gap |
| Metadata | Metadata schema unversioned; artifact versions differ | Gap |
| Traceability | ID namespaces collide; no complete per-shot manifest/plan hash | Gap |
| Analytics | Feedback/analytics not reliably linked to runs | Gap |
| Production publishing | No real production publishing verified | Not Verified |

These are Phase 10/11 report findings, not a fresh code audit.

## 5. Common failure, retry and recovery contract — proposed

1. Persist successful stage outputs and metadata.
2. Preserve last known-good artifacts; failed retries must not destroy them.
3. Use stable, non-colliding IDs for runs, content, research, claims, beats, shots, assets, reviews, approvals and publications.
4. Version scripts, storyboards, shot plans, brand configuration, policies and renders.
5. Fail closed at critical gates: unknown rights, missing required approval and hard validation failures stop distribution.
6. Make retries safe and prevent duplicate external publication.
7. Preserve sanitized diagnostics: stage, reason, IDs and timestamps.
8. Keep warnings distinct from blockers.
9. Resume from the last valid persisted state after interruption.
10. Invalidate stale approvals after material artifact changes.

## 6. Shorts Studio ↔ Content OS integration boundary — proposed

**Shorts Studio remains the specialized production engine:**
- Executes Shorts-specific production.
- Produces the video and production artifacts.
- Returns manifests, diagnostics and stage outcomes.

**NEXTDECODE Content OS owns the shared operating layer:**
- Cross-format content lifecycle and Content Graph.
- Shared knowledge, brand and strategy context.
- Research/studio orchestration.
- Central QA, rights, policy and approval.
- Persistent scheduling/orchestration and distribution authorization.
- Cross-format analytics.

This is target architecture, not proof these Content OS services exist today.

### Proposed integration flow

```text
Content OS creates content item/request
  -> Shorts Studio adapter validates/maps inputs
  -> Shorts Studio pipeline executes
  -> Adapter returns artifacts, manifest, diagnostics, status
  -> Content OS registers artifacts and lineage
  -> Central QA / rights / policy gates
  -> Review and approval
  -> Distribution authorization
  -> Publishing adapter + ledger
  -> Analytics and learning
```

### Conceptual payload (draft only; not an existing API)

```json
{
  "contract_version": "1.0",
  "content_item_id": "stable-content-id",
  "production_run_id": "stable-run-id",
  "studio": "short_video",
  "format": "shorts",
  "input_refs": {
    "brief_id": "brief-id",
    "research_package_id": "research-id",
    "brand_profile_id": "brand-id"
  },
  "requested_outputs": [
    "video",
    "script",
    "storyboard",
    "shot_plan",
    "asset_manifest",
    "render_manifest"
  ],
  "execution": {
    "mode": "dry_run",
    "requested_by": "content_os"
  },
  "result": {
    "status": "pending",
    "artifact_refs": [],
    "diagnostic_refs": []
  }
}
```

Before implementation, define exact schemas, required/optional fields, ID rules, artifact storage/reference format, status/error enums, timeout/retry/cancellation semantics, version compatibility, authentication/authorization, dry-run behavior and bypass prevention.

## 7. Decisions and non-decisions

**Established direction**
- Shorts Studio remains a specialized engine inside Content OS.
- Content OS provides shared intelligence and cross-format orchestration.
- Critical rights and publishing controls should be centrally enforced.
- Human control and explicit authorization remain important.
- Integrate/improve existing capabilities rather than replacing Shorts Studio wholesale.

**Proposed, not locked**
- Integration API/schema.
- Content Graph schema and database.
- Persistent queue/worker implementation.
- Central policy engine.
- Approval states and role model.
- Retry/backoff/idempotency details.
- Local, hybrid or cloud execution topology.
- Conditional auto-publishing rules and numeric frequency limits.

**Not authorized by this document:** code/test/config/doc changes, dependency installation, Git/GitHub operations, agent ownership changes, deployment, real uploads or public publishing.

## 8. Production blockers to carry forward

- **G1 — Storyboard gate:** Default `warn` allows `needs_review` to render.
- **G2 — Rights gate:** Calculated but not reliably consumed by publishing; unknown rights not reliably blocked.
- **G3 — Factual claims:** Unsupported claims are warnings rather than consistent publish blockers.
- **U1 — Direct publishing bypass:** Adapters can publish publicly without expected approval; `publish_social.py --execute` skips approval.
- **D1 — Direct pipeline bypass:** `app.script.pipeline` can bypass QA, run identity, approval and sanitized failure handling.
- **Traceability:** ID namespaces collide; no complete per-shot render manifest/plan hash; evidence/coverage checks incomplete.
- **Run tracking:** Core tracker tests exist, but runtime integration in `short.py` is unverified.
- **API:** Unauthenticated API and in-memory jobs reported.
- **Approval:** Single global slot; no roles/signatures.
- **Rights:** No centralized rights registry.
- **Schema/versioning:** Metadata unversioned; related artifact versions inconsistent.
- **Analytics:** Analytics/feedback not reliably linked to runs.
- **Publishing:** No live production publishing verified.

Revalidate these against the authorized current repository state before implementation planning.

## 9. Evidence and limitations

Source reports:
- `PHASE11_FINAL_REPORT_2026-10-31.md`
- `PHASE11_FINAL_RECONCILIATION.md`
- `PHASE10_FINAL_RECONCILIATION.md`

Reported evidence:
- Phase 11: 29 focused tests passed (10 traceability, 13 shot-plan, 6 query-dedup); a reported full suite of 503 passed excluding the strict file; strict fail-closed suite 20/20.
- Phase 11: two strong-pipeline E2E runs produced 1080x1920 H.264/AAC MP4s with QA `pass`.
- One trace run: 14 shots, 9 beats; 4/9 beats linked to claims and 3 marked `evidence_missing`.
- Phase 10: full suite reported 535 passed, 1 warning.
- Run tracker integration tested hermetically; runtime integration in `short.py` remained unverified.
- No production deployment, scheduler execution, real provider upload or real publishing verified.

Test counts come from different report scopes/times and must not be merged into one universal result. Kilo's independent QA report was unavailable during reconciliation; independent QA evidence remains unavailable.

## 10. Instructions for coding agents receiving this document

1. Read this document with `NEXTDECODE_Master_Blueprint_2.0`.
2. Perform only an explicitly authorized read-only verification first.
3. Produce a discrepancy report: confirmed behavior, differences, unverified paths, missing contracts, risks and blockers.
4. Do not implement proposed contracts solely because they appear here.
5. Obtain explicit owner approval before code, tests, config, dependencies, Git, deployment or publishing changes.
6. Work in small isolated scopes with explicit file ownership and test evidence.
7. Preserve unrelated WIP; report unexpected changes before proceeding.
8. For publishing work, prove every entry point is subject to the same central authorization and fail-closed policy.
9. Report commands, environment, exact test results and what was not tested.

## 11. Next document — Part 3

**NEXTDECODE System Architecture & Pipeline — Part 3: Technical Architecture Design**

Planned topics:
1. Shared data model and Content Graph entities.
2. Persistent job queue and worker architecture.
3. Agent contracts and orchestration boundaries.
4. Centralized QA, rights and approval policy.
5. Shorts Studio integration API and artifact manifest.
6. Local-first now, hybrid/cloud-ready later.

Design the data model independently first, then compare it with the existing `workspace_sync.py` SQLite prototype. Do not let the prototype dictate the target architecture merely because it exists.

---

**End of Part 2 — Shorts Studio Pipeline Contract 1.0**
