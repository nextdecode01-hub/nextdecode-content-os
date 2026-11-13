# Shorts Studio documentation index

This directory separates operational documentation, the canonical NEXTDECODE planning mirror, historical source material, and workstream-specific records.

## Main areas

- [NEXTDECODE workspace mirror](nextdecode-workspace/00_CONTROL_AND_INDEX/00_MASTER_INDEX.md) — dated local mirror of the canonical D-drive workspace. Folders 00–08 were copied on 2026-11-05: 247 files, all SHA-256 checks matched after a refresh from the current D-drive source. The authoritative source remains `D:\\MsP\\NEXTDECODE_WORKSPACE\\`. See [mirror manifest](nextdecode-workspace/MIRROR_MANIFEST.md).
- [Reports archive](../reports/README.md) — audits, implementation reports, handovers, test designs and verification records grouped by evidenced author/agent provenance.
- [Workstream review records](workstream-review/) — local workstream-specific registers that are not yet part of the canonical D-drive workspace.
- [Legacy source snapshot](archive/legacy-source-imports/README.md) — preserved original imported documents. The old root path remains as a compatibility symlink for historical references.
- [Reference links](references/links.md) — previously collected external project and tooling references.

## Repository architecture

- [Repository structure standard](architecture/REPOSITORY_STRUCTURE_STANDARD.md) - proposed modular-monolith layout, file-placement rules and dependency direction.
- [Repository rationalization audit](architecture/REPOSITORY_RATIONALIZATION_AUDIT.md) - archive removals, dashboard constraints and next steps.

## Current operational documentation

- `AI_PROVIDER_STATUS.md` — provider availability notes.
- `CONTENT_STRATEGY.md` — channel/content strategy.
- `META_REELS_SETUP.md` — Meta account and publishing setup.
- `MONETIZATION_PLAN.md` — monetization planning.
- `MONTH_PLAN.md` — planning notes.
- `REQUIRED_SETUP.md` — local setup requirements.
- `TOOLING_STACK.md` — current tools and dependencies.
- `dependency_map.md` - current application-owned autonomy and module dependency map.
- `ROADMAP.md` — Shorts Studio roadmap.

## Owner decisions and Telegram boundary

The D-drive mirror records the following current MOB decisions. These are policy boundaries, not implementation authorization:

1. MOB-DEC-01 selected Option B: authenticated Content OS session pairing plus independent step-up verification for account recovery and high-risk decisions. Detailed factor, risk tiers and protocol remain open.
2. MOB-DEC-02 conditionally selected Option C for research/topic selection, script/editorial review and final-video review. Auto-decision requires explicit owner enablement and an exact predefined owner-approved rule. AI confidence or similarity alone can never trigger approval.
3. Critical, high-impact, uncertain, conflicting, rights-sensitive, safety-sensitive and policy-exception cases require human intervention. Timeout may escalate or notify but cannot bypass the human gate.
4. MOB-RECON-01 Path A separates a bounded automated workflow/policy disposition from human CF-21 `ApprovalDecision: APPROVED`. It cannot satisfy required human approval.
5. Publishing authorization remains separate. No Telegram bot, token, inbound transport, automated approval operation or publishing behavior is authorized by these records.

Exact timeout windows, stage eligibility, critical taxonomy, rule lifecycle, historical-decision matching, audit schema, API-LC decisions and security acceptance remain open. Do not implement these open items or infer a default from the policy principles.

## Source-of-truth and change-control rules

- The D-drive workspace is canonical; this repository copy is a dated mirror for local engineering reference.
- A newer timestamp or draft version does not outrank an accepted owner decision.
- Do not edit the mirrored canonical documents as if they were local working drafts. Reconcile changes against D-drive source first.
- Preserve P0-A as a narrow vertical slice; do not expand it into a full Control Center without separate owner authorization.
- Keep the existing Shorts Studio specialist engine; do not restart or replace its architecture.
- Reports are historical evidence unless revalidated against the exact current revision and environment.
- Human approval and central publishing authorization remain separate gates; automatic public publishing stays disabled absent separate authorization.

## WP1 local review register

`workstream-review/wp1/P0_WP1_OWNER_DECISION_REGISTER.md` is preserved as a separate local WP1 review register. It remains marked awaiting owner disposition and is not presented as an accepted or frozen canonical contract. Its related investigation report is in `../reports/unattributed/P0_WP1_CONTRACT_CLOSURE_REPORT.md`.


For file-move and cleanup evidence, see [CLEANUP_MIGRATION_MANIFEST.md](CLEANUP_MIGRATION_MANIFEST.md).


## Engineering collaboration model

The owner-approved model (2026-11-05) is collaborative, not single-writer-by-agent:

- **ChatGPT:** architecture, direct implementation, integration, debugging, test execution and technical review.
- **OpenCode:** engineering partner for independent implementation, backend/API work, alternatives, review and debugging.
- **Qoder:** additional implementation partner for focused contributions; not the sole writer.
- **Kilo:** independent read-only security acceptance after implementation/evidence completion and separate explicit authorization.
- **Copilot:** focused regression-test review.
- **Antigravity:** targeted product/UI work only.

One active writer per file at a time. Parallel work is permitted only on independent files/packages under shared versioned contracts. No commit, push, merge, deployment or public publishing without separate explicit owner authorization. No dependency installation or paid-provider activation without explicit approval.


## Report archive boundary

The reports/ archive organizes repository-generated engineering reports and agent outputs. The D-drive workspace mirror intentionally preserves its own canonical hierarchy, including P0 testing evidence, acceptance records and release documentation; those documents are not flattened or re-attributed by this cleanup.
- [Root layout audit](ROOT_LAYOUT_AUDIT.md) — explains which root-level entrypoints, runtime paths and agent configurations must remain in place.


## MOB-01 closure pack — REG-078

The local mirror now includes [REG-078 — NEXTDECODE MOB-01 Owner Decision & Contract Dependency Closure Pack](nextdecode-workspace/03_P0_GOVERNANCE_AND_DECISIONS/02_OWNER_REVIEW_AND_AUTHORIZATION/NEXTDECODE_MOB01_OWNER_DECISION_CONTRACT_DEPENDENCY_CLOSURE_PACK_0.1.md).

Its status is DOCUMENTATION-ONLY DECISION AGENDA — NOT APPROVED. It selects no new owner options, grants no contract freeze, and authorizes no implementation, tests, agent dispatch or provider activation. It consolidates unresolved MOB-DEC-03..07, GOV-09, CF-20/CF-21, API-LC-01..10, SEC-MOB-01..09 and MOB-A07 acceptance dependencies.

Existing MOB-DEC-01 Option B, conditional MOB-DEC-02 Option C and MOB-RECON-01 Path A remain as recorded. GOV-09 and MOB-DEC-03..07 remain open. Telegram remains an untrusted interaction/notification channel; it cannot create human approval or publishing authorization. Any future bot/token/transport/interactive implementation requires the separate owner, contract, security/privacy and Artifact 10 gates described in REG-078.
- [Root module dependency map](ROOT_MODULE_DEPENDENCY_MAP.md) — module/caller classification, compatibility approach and deferred refactors.
- [Operations package README](../app/operations/README.md) — module ownership, compatibility rules and authority boundaries.
- [Notifications package README](../app/notifications/README.md) — Telegram outbound-only transport, manual review reminders and compatibility boundary.
- [Providers package README](../app/providers/README.md) — shared LLM clients, health checks, fallback behavior and path compatibility.
- [Tracking package README](../app/tracking/README.md) — run identity, manifest, artifact and promotion-journal invariants.
- [Publishing package README](../app/publish/README.md) — platform adapters, shared authorization boundary and safe test rules.
- [Temporary holding manifest](../_holding/MANIFEST.md) - quarantined legacy helpers, hashes and restore instructions.
- [Maintenance utilities](../tools/maintenance/README.md) - operator-only maintenance commands and safety gates.
- [Repository structure migration plan](architecture/REPOSITORY_STRUCTURE_MIGRATION_PLAN.md) - phased, caller-aware migration from the current Shorts Studio layout to the Content OS target.
- [Root Python file audit](architecture/ROOT_PYTHON_FILE_AUDIT.md) - classifies all root Python files as canonical entrypoints, compatibility facades, hybrid adapters or migration candidates.
