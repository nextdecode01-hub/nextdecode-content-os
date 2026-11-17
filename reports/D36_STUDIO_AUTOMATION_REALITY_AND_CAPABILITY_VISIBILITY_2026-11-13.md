# D36 — Studio Workbench Increment 03: Automation Reality & Capability Visibility
Date: 2026-11-13

## Owner concern
The owner asked whether AI and automation will operate automatically once the Studio UI is complete. The answer is no: the current Studio is a local UI prototype, and a completed interface does not create an orchestrated production workflow.

## Repository evidence reviewed

### Architecture
- Part 7 — Studio Integration APIs & Artifact Management 1.0 is explicitly marked Architecture proposal — not implementation approval.
- It defines Content OS ownership of shared identity, workflow coordination, governance, artifact registration and distribution; Shorts Studio remains the specialized production engine.
- Proposed adapter responsibilities include validated job envelopes, exact input refs, progress/outcomes, artifact registration, events, cancellation/recovery and no direct publishing.
- Part 2 Shorts Studio Pipeline Contract labels stages partially implemented and calls out incomplete research package versioning, claim enforcement, storyboard gate/traceability, rights enforcement, render identity, review lifecycle, approval and publishing.
- These documents are target architecture and report-backed maps, not proof of an implemented end-to-end Studio adapter.

### Current local autonomy registry
- research.topic.collect: enabled and planner-allowed.
- content.short.script.draft: enabled and planner-allowed.
- content.short.generate: enabled but planner-disallowed; handler explicitly enforces dry_run=True and verifies dry_run=True.
- content.longform.generate: disabled.
- publishing.check: planner-disallowed and blocked-only; it does not upload or post.
- Local autonomy task artifacts are human-review pending and external_actions_allowed=false; these are not canonical WP4 artifact records or WP5 ApprovalRequest/ApprovalDecision records.

### Existing Shorts production engine
- app/script/pipeline.py wires topic selection, research desk, claim ledger, script studio, voice provider, motion director, shot planner, render assembly and QA helpers.
- app/render/assembly.py contains full multi-shot assembly logic.
- pipelines/short.py has an explicit procedural dry-run path that skips LLM, research, stock, archive and upload calls. It creates a procedural background and silent voice track and labels the result not_for_publish.
- Presence of these modules does not prove the whole production chain is invoked by the Studio UI, persisted as a durable job, or safe for unattended execution.

### API boundary
- Current API exposes authenticated local autonomy /tasks, /plans, /autonomy/health, /autonomy/dead-letters, plus legacy /start, /status/{job_id}, /jobs and /review/pending.
- /jobs is an in-memory legacy registry. /review/pending is read-only from this dashboard.
- The existing local autonomy runtime is explicitly distinct from canonical WP2/WP3/WP4/WP5.

## UI change
Added an AI & Automation Readiness panel to /studio, driven by the live /capabilities API:
- Displays actual registered capability metadata for research, short script draft, short generation and publishing check.
- Labels enabled/planner-allowed vs enabled/direct-task-only vs disabled.
- States explicitly that planner availability is not proof of a complete Studio workflow; generation is procedural dry-run; publishing check is readiness-only.
- No new generation, workflow, approval or publishing endpoint/action was added.

## Verification
- dashboard npm run build — PASS; TypeScript + Vite, 1742 modules.
- dashboard npm run typecheck — PASS.
- git diff --check — PASS.
- /studio — HTTP 200.
- /api/capabilities — HTTP 200.

## Accurate answer to automation question
- Research and script-draft specialists are available in the local autonomy runtime, but not yet connected as a full Studio-owned production flow.
- Full rendering components exist in the Shorts engine, but the autonomous generation capability intentionally only accepts a procedural dry-run.
- Persistent canonical Studio job, canonical artifact registration, unified QA/rights gates, review/approval lifecycle and adapter integration are not established by the inspected evidence.
- Therefore AI will not automatically carry a topic all the way to a final publish-ready video merely because the Studio UI is complete.

## Next engineering sequence (evidence-led)
1. Define and verify the minimal Shorts Studio adapter boundary using accepted/authorized WP2–WP6 contracts; do not treat Part 7 proposal as approved schema.
2. Reconcile current local autonomy task IDs/artifacts with canonical workflow/job/worker/artifact/approval identities; no ID substitution.
3. Build a review-only orchestration path for topic -> research artifact -> script artifact, using existing specialists and preserving exact hashes/provenance.
4. Add storyboard/shot-plan and rights/evidence gates to a production-safe run identity; ensure direct-entry paths cannot bypass them.
5. Connect rendering only after approved run envelope, input versions, resource policy, retry/cancel behavior, and output manifest are verified.
6. Register immutable output artifacts and QA evidence; approval remains a separate human action bound to exact artifact hashes.
7. Only after explicit owner authorization, consider external distribution; no auto-publication by default.

## Non-actions
- No production run, external network generation, upload, publishing or provider spend initiated.
- No database/schema migration, API endpoint or canonical contract implemented.
- No commit, push or deployment.
