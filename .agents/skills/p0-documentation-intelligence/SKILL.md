---
name: p0-documentation-intelligence
description: Reconcile NEXTDECODE P0 handoffs, contracts, decisions, gaps, ownership, and evidence without inventing approval or changing project scope. Use for P0 status assessments, handoffs, dependency reviews, and authorization briefs; not for implementation or general technical writing.
---

# P0 Documentation Intelligence

Produce an evidence-grounded P0 assessment or handoff that preserves the standing P0 Documentation Handoff & Dependency Protocol. This skill is for governance intelligence, not engineering execution.

## Boundaries

- Do not treat a plan, report, passing hermetic test, generated artifact, or chat summary as production verification.
- Do not invent owner approval, contract freeze, implementation completion, a resolved conflict, or live integration evidence.
- Do not silently alter a canonical decision, rename an identifier, merge status vocabularies, or promote proposed material to accepted material.
- Do not modify repository code, tests, workflows, credentials, deployments, schedules, provider configuration, or canonical P0 documents unless the user separately authorizes that exact action.
- Do not run tests, integrations, deployments, publishing, or destructive Git operations when the request is documentation-only.

## Source protocol

1. Locate the current master handoff/continuity document, accepted P0 decision baseline, canonical contracts, status-vocabulary/source-precedence record, applicable work-package document, and any owner decision or handoff update.
2. Record each source's title, version/date, stated status, scope, and whether it is accepted, proposed, historical, or merely report-backed.
3. Apply this hierarchy when sources disagree:
   1. explicit owner decision and accepted ADR/CF decision;
   2. governing canonical contract;
   3. approved work-package specification;
   4. reconciliation/addendum material;
   5. implementation handoff, test report, chat summary, or generated output.
4. Preserve the higher-authority source and describe the conflict. Do not select a winner from lower-authority material.
5. Treat a missing source, version mismatch, ambiguous ownership, contradictory status, or missing acceptance oracle as a documented gap.

## Required distinction

For every item assessed, separate these dimensions rather than collapsing them into one claim:

- **Decision authority:** accepted, proposed, deferred, or unresolved.
- **Design maturity:** documented candidate, frozen contract, or not designed.
- **Implementation:** observed code/configuration, implementation report only, or absent.
- **Verification:** current independent evidence, historical/self-reported evidence, or no evidence.
- **Operational state:** integration, staging, and live production proof are separate from implementation.

Use the project's requested status vocabulary exactly when supplied. If none is supplied, define the vocabulary before assigning statuses. `VERIFIED` requires a named scope/build/environment and retained, relevant evidence; use a narrower qualifier when only a specific property is verified (for example, transfer-hash equality).

## Assessment workflow

1. State the question, allowed actions, and excluded actions.
2. Build an evidence register with source path, version/date, authority level, and the exact claim it supports.
3. Identify accepted decisions, frozen constraints, unresolved decisions, conflicts, dependencies, ownership, and stop conditions.
4. Inspect repository evidence only to the scope authorized. Report the exact revision/worktree state and distinguish tracked baseline from uncommitted work.
5. Build a coverage matrix. At minimum include: module or decision, design evidence, implementation evidence, test/verification evidence, integration/live evidence, status, gaps/dependencies, owner, and confidence.
6. Reconcile prior claims explicitly. A prior positive report becomes historical evidence unless independently corroborated for the named revision and environment.
7. End with the strongest proven areas, weakest/blocked areas, and the smallest next evidence-gathering steps. Do not turn those recommendations into work authorization.

## Ownership and handoff boundaries

Apply the owner-approved collaboration model recorded on 2026-11-05; it supersedes the earlier single-owner assignment:

- **ChatGPT:** architecture, direct implementation, integration, debugging, test execution, and technical review.
- **OpenCode:** engineering partner for independent implementation, backend/API work, alternatives, review, and debugging.
- **Copilot:** focused regression-test review.

Use one active writer per file at a time. Parallel work is allowed only across independent files/packages with shared versioned contracts; cross-review, integration, and regression evidence are required before acceptance. ChatGPT, OpenCode, and Qoder may all contribute, but must coordinate file ownership and avoid concurrent edits to the same file.

No commit, push, merge, deployment, public publishing, or production side effect is authorized by a normal implementation task. Each requires separate explicit owner authorization. Do not install dependencies or enable paid providers without explicit approval. A stage handoff, report completion, or bounded engineering approval does not automatically authorize integration, release, or the next stage.

## Stop and escalate

Stop the assessment and request owner direction when a critical gap would require choosing between conflicting authoritative sources, changing a frozen decision, granting access, exposing credentials, or authorizing code/tests/integration/deployment/publishing. Report the exact missing decision, owner needed, affected scope, and safe alternatives.

## Completion report

Report:

- sources inspected and their authority/status;
- decisions preserved, proposals, unresolved items, and conflicts;
- evidence-backed coverage matrix and confidence;
- exact repository/worktree scope inspected, if any;
- actions explicitly not performed;
- ownership/dependency consequences;
- next evidence step and the separate authorization it would require.

## Portability

This folder is intentionally self-contained: only `SKILL.md` is required. When used outside this repository, ask for or locate the equivalent master handoff, decision baseline, contracts, source-precedence rules, and work-package materials before making NEXTDECODE-specific conclusions.
