# n8n Workflow Template — Aligned to Shorts Studio

## Goal
Create an n8n workflow JSON that aligns with the existing Shorts Studio project and can be imported into the local n8n instance to handle YouTube + Facebook + Instagram publishing.

## Existing Project Context

### Current n8n workflow (`workflow_n8n_approved_schedule.json`, id `aibl9NX61mKH9z5m`)
A 4-node flow that calls a private `studio-runner` service:
1. `scheduleTrigger` (12:00 IST) → `httpRequest` POST `http://studio-runner:8080/run/generate` (review-only generation)
2. `scheduleTrigger` (20:00 IST) → `httpRequest` POST `http://studio-runner:8080/run/publish` (approval-gated publishing)

The runner holds all credentials. n8n never sees platform tokens. This is the credential boundary that must be preserved.

### What's already built locally
- `publish_all.py` — preflight + publish to YouTube, Facebook, Instagram
- `approve_review.py` — human review gate
- `strong_pipeline.py` — topic → research → script → voice → motion render
- `review_package.json` — approved, all checklist items true
- `.env` — YouTube OAuth present, Meta credentials empty, Gemini/Groq/OmniRoute set

### `restore_n8n_workflow.sh` (186 lines)
Idempotent restore script. Backs up DB, reads workflow from `WORKFLOW_FILE` env (default `workflow_n8n_approved_schedule.json`), queries live n8n by name, activates or creates. Safe to run repeatedly.

## Design Decisions

**Decision 1 — Keep the runner boundary.** Option A (add direct Meta Graph API + YouTube nodes inside n8n) would move credentials out of the runner and into n8n, breaking the existing security model. Option B (add a schedule trigger that calls the runner's publish endpoint) preserves the boundary and reuses `publish_all.py`, which is already tested. **Chosen: Option B.**

**Decision 2 — Separate publish trigger at 20:30 IST.** The existing 20:00 IST trigger handles approval-gated publishing for long-form content. The new trigger runs 30 minutes later for Shorts, giving the approval gate time to complete and isolating publish failures from approval failures. This matches the two-trigger pattern already in use (12:00 generate, 20:00 publish).

**Decision 3 — Restore script supports a second workflow.** The script already accepts `WORKFLOW_FILE` as an env override. The new workflow will be added as a second invocation in the script, so both workflows survive DB wipes.

## Plan

### Step 1 — Create `workflow_n8n_publish.json`
Copy `workflow_n8n_approved_schedule.json` and add:
1. A new `scheduleTrigger` node at 20:30 IST named "Publish Approved Short (20:30 IST)"
2. A new `httpRequest` node POST `http://studio-runner:8080/run/publish_shorts` that runs `publish_all.py` after the approval gate
3. A sticky note documenting the new flow
4. Keep the existing 12:00 IST generate and 20:00 IST publish triggers unchanged

### Step 2 — Update `restore_n8n_workflow.sh`
Add a second workflow restore invocation using `WORKFLOW_FILE=workflow_n8n_publish.json`. The script already supports this via env override — just add the second call after the first completes.

### Step 3 — Validate
Run `setup_check.py` to confirm all required items are READY before activating the new workflow.

## Out of Scope
- Adding direct platform API nodes inside n8n (would break credential boundary)
- Changing the runner service or its endpoints
- Modifying the existing 12:00/20:00 IST workflow

## Validation
- `bash restore_n8n_workflow.sh` — both workflows present and active
- `setup_check.py` — all required items READY
- Check n8n workflow list shows both workflows with expected node counts