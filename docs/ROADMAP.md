# Nextdecode Shorts & Reels Studio — Roadmap

Last reviewed: 2026-10-26

## Product goal

Build a reliable, human-reviewed system for researching, producing, publishing, and improving original Nextdecode videos. Optimize for accurate content, consistent quality, and audience learning—not upload volume, promised virality, or guaranteed revenue.

## Current baseline

- The strong Short pipeline covers topic selection, source verification, script critique, narration, multi-shot rendering, captions, audio, and media QA.
- A separate long-form pipeline supports evidence-gated scripts, chapter visuals, narration, review, and YouTube publishing.
- The application-owned task worker schedules and executes generation jobs. Publishing requires same-day owner approval tied to the exact video and metadata hashes.
- YouTube upload authorization previously succeeded. Meta credentials and a reliable Instagram media host remain account-owner setup dependencies.
- Analytics collectors and a feedback ledger exist, but automated performance collection is not part of the active schedule.
- Docker Compose migration is prepared but not active.
- Automated baseline on 2026-10-26 after cleanup: **91 passed** locally. Runner health, source relevance, topic consistency, asset matching, and procedural-visual gates are covered by tests; CI is still missing.
- Experimental and alternate implementations were archived to `/home/demon/shorts_studio_archive_pre_20261026/`; the root now holds one main Short path, one long-form path, and the approval-gated publisher.
- Licensed stock keys are still not configured, so recent runs relied on Wikimedia images and some were irrelevant or duplicated. This is the top visual-quality blocker.

## Priorities

1. **P0 — Reliability and safety:** one maintained production path, reproducible tests, and human approval that cannot be bypassed.
2. **P1 — Publishable quality:** accurate research, relevant licensed/original visuals, strong editing, and consistent review.
3. **P1 — Distribution readiness:** complete platform setup without weakening the all-destination publishing gate.
4. **P2 — Audience learning:** collect real per-platform analytics and run controlled weekly experiments.
5. **P3 — Sustainable scale:** improve cost, throughput, formats, and monetization readiness only after quality is stable.

## Phase 0 — Stabilize the production foundation

**Target:** week 1  
**Outcome:** a reproducible, tested system with one clearly defined production workflow.

- Restore the full test suite to green, starting with the runner health-check failure.
- Add CI for automated tests and basic static checks on every proposed change.
- Pin runtime dependencies and replace deprecated dependencies through tested migrations.
- Declare the strong Short pipeline, current long-form pipeline, and approval-gated publisher as the supported production paths.
- Label modular, consensus and alternate model paths as experimental; repair interface and persistence mismatches before enabling them.
- Require an explicit human checklist for every approval entry point. Remove or disable auxiliary flows that auto-approve or pre-complete review items.
- Run one Short and one long-form dress rehearsal from generation through review without publishing.

**Exit criteria**

- All automated tests pass locally and in CI.
- A fresh environment can install and run the documented workflow.
- Only one scheduled production workflow is active.
- Every publishing path rejects missing, stale, mismatched, or automatic approval.
- Both dress rehearsals produce reviewable packages without manual code edits.

## Phase 1 — Make output consistently publishable

**Target:** weeks 2–3  
**Outcome:** predictable editorial and visual quality with clear evidence for reviewers.

- Strengthen the first-second hook, pacing, shot variety, subtitle readability, loudness, and Nextdecode visual identity.
- Put source excerpts and claim-to-evidence links directly in the review package so factual checks are fast and visible.
- Review footage relevance and licensing per scene; keep procedural or unverified visuals draft-only.
- Validate long-form chapter pacing and ensure each chapter has intentional, topic-specific visuals.
- Track generation success, provider failures, latency, render duration, and review rejection reasons.
- Add safe retries for transient provider failures while preserving duplicate-upload protection.
- Monitor local archive capacity and document a tested backup and restore process.

**Exit criteria**

- Five consecutive Shorts and two long-form videos complete generation and QA without code intervention.
- Every approved package has verified claims, suitable visuals, clean audio, readable captions, and platform-specific copy.
- Review rejections and generation failures are recorded in a usable weekly report.
- No procedural-only or unverified-visual package can be approved or published.

## Phase 2 — Complete distribution and operating readiness

**Target:** weeks 2–4; account-owner work can run in parallel  
**Outcome:** reliable delivery to the intended platforms with no unapproved or partial cross-posting.

### Account-owner dependencies

- Finish Meta developer/app verification and required Facebook/Instagram permissions.
- Link the Instagram professional account to the correct Facebook Page.
- Store Page/account IDs and tokens only in the private `.env`.
- Configure a stable public HTTPS media host; use the temporary tunnel only as a documented fallback.
- Grant read-only analytics access separately when ready; upload permission does not provide analytics access.

### Engineering work

- Validate all destinations with `setup_check.py` and non-publishing preflight checks.
- Exercise credential expiry, media-host failure, duplicate-upload, and partial-failure handling in tests.
- Perform the first coordinated cross-post only after explicit owner review and approval.
- Keep the application-owned worker as the sole generation task runtime; verify its restart recovery and health before enabling any future schedule.
- Use five review-passed Shorts per week as the initial publishing target; treat extra generated drafts as backlog, not a quota.

**Exit criteria**

- YouTube, Facebook, and Instagram all pass preflight before coordinated Short publishing.
- A real owner-approved cross-post completes without duplicates or silent partial failure.
- The active scheduler survives restart and has one clearly documented operating procedure.
- Five packages per week can be reviewed without lowering the quality gate.

## Phase 3 — Build the performance learning loop

**Target:** weeks 4–8  
**Outcome:** content decisions based on comparable audience evidence rather than guesses.

- Schedule read-only analytics collection after explicit authorization; retain manual Studio/Meta snapshots as a fallback.
- Capture 24-hour and 7-day results for each published video, keeping platform metrics separate.
- Compare series, topics, hook archetypes, openings, retention, watch time, saves/shares, and follows/subscribers.
- Connect validated results to topic selection and the feedback ledger without allowing a single outlier to dominate.
- Run one controlled editorial experiment per week and record the hypothesis, change, result, and decision.
- Review the initial 20-video cohort before changing cadence, posting time, or content mix.

**Exit criteria**

- Each published video has a complete feedback record or an explicitly documented data gap.
- The 20-video cohort has a per-platform performance review.
- Weekly planning uses recorded evidence and selects only one primary experiment.
- No system claims measured demand, virality, or revenue from editorial scores alone.

## Phase 4 — Scale sustainably and prepare for monetization

**Target:** after the first 20-video review, then ongoing  
**Outcome:** growth without sacrificing originality, accuracy, safety, or reliability.

- Double down on formats with repeatable audience evidence; retire formats that consistently underperform.
- Expand long-form only when retention and production capacity support it.
- Profile model and render cost, latency, and failure rates; optimize the slowest or least reliable stages first.
- Add new providers or pipeline architectures only behind contract tests and the existing review/publishing gates.
- Update monetization eligibility snapshots weekly from official dashboards and keep platform thresholds separate.
- Check channel policy, originality, two-step verification, advanced features, and AdSense readiness where applicable.
- Revisit posting cadence and times only after sufficient audience-activity data exists.

**Exit criteria**

- Scaling decisions are supported by quality, reliability, and audience data.
- Monetization progress is reported as eligibility gaps, never as promised approval or income.
- Increased throughput does not bypass review, source verification, licensing, or duplicate protection.

## Next priority checklist (2026-10-26)

Check items off in order. `Owner` means the account owner must act; `Code` means a code/test change in this repository. An item is done only when its "Done when" condition is met.

### P0 — Before the next scheduled publish

- [ ] **Configure a licensed stock key.** Owner. Add `PEXELS_API_KEY` (existing key) or `PIXABAY_API_KEY` to `.env`, then run `./venv/bin/python setup_check.py`. Done when stock B-roll reports READY and a test generation records `multi_shot_stock` with every shot matched and unique.
- [ ] **Regenerate pending Short and long-form packages.** Code. Run the review-only pipeline again so `review_pending.json` and `longform_review_pending.json` carry fresh hashes. Done when `approval_integrity.py` accepts the new package and the old approvals are rejected.
- [ ] **Short dress rehearsal.** Code. Generate one Short through `run_scheduled_generation.sh` with `PUBLISH_MODE=review`. Done when the MP4, captions, metadata, and review package are produced with no manual edits, and the publish step refuses to run.
- [ ] **Long-form dress rehearsal.** Code. Run `run_longform_pipeline.sh` on a Wednesday/Saturday path. Done when an 8-minute cut passes audio/video QA and every chapter has a topic-matched, credited visual.
- [ ] **Confirm one scheduler only.** Owner. Verify `nextdecode-autonomy-worker.service` is the only generation task worker. Done when it survives restart and there is one documented schedule owner.
- [ ] **Remove quarantined credentials.** Owner. Check `/home/demon/.local/share/shorts_studio_private_artifacts/stray-wsl.localhost-env-20261026`, delete it, and rotate Facebook/Instagram tokens if the copy was ever exposed.

### P1 — This week: publishable quality

- [ ] **Add CI.** Code. Run pytest, `compileall`, and shell syntax checks on every proposed change. Done when a clean checkout runs 91 tests green without local state.
- [ ] **Pin and modernize dependencies.** Code. Pin `requirements.txt` and migrate deprecated `google.generativeai` to `google.genai` with tests. Done when the test warning is gone and a fresh install reproduces the run.
- [ ] **Put evidence in the review package.** Code. Include each claim, verbatim source excerpt, source URL, and licence line. Done when a reviewer can verify every number without opening the repository.
- [ ] **Normalize Short loudness.** Code. Target about −14 LUFS integrated and true peak ≤ −1 dB, verified with `ffmpeg -af ebur128`. Done when a generated Short passes the measured check.
- [ ] **Strengthen the first three seconds.** Code. Require a concrete claim plus an early visual change in the opening; keep the hook scorer in the gate. Done when five consecutive drafts pass without manual hook edits.
- [ ] **Record production telemetry.** Code. Log generation success, provider/model, latency, render duration, and review rejection reason per run. Done when a weekly summary can be produced from the logs.
- [ ] **Test archive backup and restore.** Owner + Code. Restore one archived video/metadata pair from the backup. Done when a documented restore succeeds.

### P2 — Distribution and learning (run in parallel)

- [ ] **Finish Meta setup and preflight.** Owner. Complete app verification, link Instagram to the correct Page, then run `meta_preflight.py` without publishing. Done when all three destinations pass preflight.
- [ ] **Stable Instagram media host.** Owner. Configure public HTTPS hosting and keep the tunnel only as fallback. Done when a test media URL is reachable without the tunnel.
- [ ] **Read-only analytics access.** Owner. Grant analytics scope separately and schedule daily collection. Done when 24-hour and 7-day metrics are stored per platform.
- [ ] **First coordinated cross-post.** Owner. Approve one reviewed Short and verify all destinations. Done when no duplicate upload or silent partial failure occurs.
- [ ] **Autonomous worker resilience.** Code. Verify worker restart recovery, queue persistence, lease expiry, dependency blocking and task audit history. Done when the acceptance suite passes after a worker restart.

### P3 — After the first 20-video cohort

- [ ] Review the cohort per platform before changing cadence, posting time, or content mix.
- [ ] Run one controlled editorial experiment per week and record hypothesis, change, result, and decision.
- [ ] Profile model and render cost, latency, and failure rate; optimize the slowest stage first.
- [ ] Update monetization eligibility weekly from official dashboards as gaps, never as promised income.

## Working cadence

- **Each work session:** state the current roadmap item, make a focused change, run relevant checks, and record the result and next blocker.
- **Daily during production:** review generated drafts, failures, and scheduled-run health; publishing still requires owner approval.
- **Weekly:** review five-video quality and performance, choose one experiment, update blockers, and reorder roadmap tasks only when evidence supports it.
- **Monthly:** review the content cohort, provider costs/reliability, security and backups, monetization eligibility, and the next month's priorities.

## Permanent guardrails

- Never publish without the required owner approval or weaken approval to meet a schedule.
- Never commit credentials, expose OAuth codes, or print secrets in logs.
- Do not run two schedulers against the same publishing workflow.
- Do not enable paid providers, automatic publishing, or new external permissions without explicit authorization.
- Do not present procedural placeholders as finished footage or editorial estimates as audience data.
- Do not promise views, platform approval, or revenue.
