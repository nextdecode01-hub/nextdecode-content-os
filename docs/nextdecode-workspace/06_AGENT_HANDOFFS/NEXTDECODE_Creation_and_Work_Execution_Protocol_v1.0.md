# NEXTDECODE --- Creation & Work Execution Protocol

**Document ID:** ND-GOV-CREATION-001\
**Version:** 1.0\
**Status:** Standing working protocol\
**Applies to:** All human and AI agents contributing to NEXTDECODE,
including Qoder, OpenCode, Kilo, Codex, and future agents\
**Authority:** Operates alongside the existing P0 Documentation Handoff
& Dependency Protocol. It does not replace, override, or create a
competing master plan.

------------------------------------------------------------------------

## 1. Purpose

Ensure that NEXTDECODE work is created once, correctly, safely, and with
traceable evidence. Prevent duplicate documents, repeated discovery,
unnecessary redesign, scope drift, and premature claims of completion.

**Core rule: No work without a clear reason to exist.**

Agents must prefer reusing or extending valid existing work over
creating a duplicate.

## 2. Mandatory workflow

Every work package, document, component, or subsystem must follow this
sequence:

1.  **DISCOVER** --- Inspect relevant existing files, documents,
    decisions, code, tests, and recorded progress before proposing or
    creating anything.
2.  **RECONCILE** --- Identify authoritative versions, accepted
    decisions, ownership, dependencies, completed work, gaps, unresolved
    decisions, and conflicts.
3.  **DEFINE** --- State the purpose, scope, inputs, outputs, owner,
    dependencies, exclusions, and measurable acceptance criteria.
4.  **CREATE** --- Create or modify only what is necessary and
    authorized. Prefer extending the authoritative existing artifact.
5.  **VERIFY** --- Check the result against the acceptance criteria and
    preserve evidence. Do not claim verification based only on intention
    or inspection of a plan.
6.  **RECORD & ADVANCE** --- Record what changed, what was verified,
    what remains blocked, and the next dependency. Continue from the
    actual stopping point; do not restart completed work.

Do not skip a stage. If a stage cannot be completed, record the blocker
and stop only the affected work.

## 3. Pre-work requirements

Before starting, the responsible agent must establish:

-   **Existing work:** Which relevant files, documents, code, tests, and
    decisions already exist?
-   **Authority:** Which document/version or decision is authoritative?
    Is it approved, proposed, frozen, or only a candidate?
-   **Progress:** What is already complete, in progress, verified, or
    blocked?
-   **Purpose:** What specific problem does this work solve?
-   **Scope and exclusions:** What is included, and what must remain
    untouched?
-   **Ownership:** Who owns the work and who may review it? Respect
    existing role assignments.
-   **Dependencies:** What must exist first, and what interfaces will
    this work affect?
-   **Contracts:** What inputs, outputs, states, permissions, and
    failure behavior must be preserved?
-   **Acceptance:** What observable evidence will prove the work is
    complete?
-   **Authorization:** Is this design, implementation, verification, or
    production activity explicitly authorized?

If the necessary source document or decision is missing, name the exact
missing document/section and explain whether safe work can proceed.
Never invent an owner decision or silently fill a contractual gap.

## 4. Reuse and anti-duplication rules

Agents MUST:

-   Search before creating a new file, plan, specification, test,
    component, service, or workflow.
-   Reuse accepted decisions and completed work; do not reopen them
    without new evidence or an explicit request.
-   Extend the existing authoritative artifact when that is clearer and
    safer than creating another.
-   Create a new artifact only when there is a distinct, documented
    purpose and no suitable existing home.
-   Check filenames, document IDs, versions, repository paths, and
    overlapping scope before creation.
-   Record why a new artifact is necessary and link it to the related
    existing artifacts.
-   Avoid repeating discovery, audits, tests, or explanations when valid
    evidence already exists. Repeat them only when the source changed,
    evidence is stale/insufficient, acceptance requires a fresh run, or
    the user explicitly requests it.
-   Never create a second master plan or competing source of truth.

If a requested task is already complete, report the existing result and
its evidence instead of recreating it.

## 5. Architecture, decisions, and ownership

-   Preserve accepted architecture, interfaces, contracts, naming,
    ownership, and documented boundaries.
-   Do not silently change a frozen or accepted decision.
-   Do not convert a proposal, recommendation, or candidate into an
    accepted decision without the required owner approval.
-   Do not merge responsibilities that existing architecture assigns to
    separate components.
-   Keep development tracks, runtime components, agents, workers, and
    governance authorities conceptually distinct.
-   Raise conflicts explicitly with the exact sources and sections
    involved; do not resolve them by guessing.
-   Respect one-writer-per-file/worktree and the project's assigned
    agent roles. Independent reviewers remain read-only unless
    explicitly reassigned.
-   Report any newly discovered documentation dependency or contract
    gap.

## 6. Minimal and purposeful creation

Create the smallest complete change that satisfies the stated
requirement and preserves the architecture.

Before adding a file, service, abstraction, dashboard, automation,
dependency, or workflow, explain why existing capabilities cannot
satisfy the need. Avoid speculative infrastructure, duplicate
abstractions, unnecessary formatting churn, and unrelated refactoring.

A deliverable should have one clear owner, one authoritative location, a
defined interface, and explicit acceptance criteria.

## 7. Status vocabulary

Use these statuses consistently; do not substitute vague labels such as
"done" or "almost ready."

  ------------------------------------------------------------------------------------
  Status                                           Meaning
  ------------------------------------------------ -----------------------------------
  `READY`                                          Scope, required decisions,
                                                   dependencies, and acceptance
                                                   criteria are clear; work may
                                                   proceed within its authorization.

  `BLOCKED_ON_DOCUMENTATION`                       A required document, section,
                                                   contract, or evidence is missing or
                                                   unresolved.

  `BLOCKED_ON_OWNER_DECISION`                      A decision reserved for an
                                                   authorized owner has not been made.

  `BLOCKED_ON_DEPENDENCY`                          A required upstream task,
                                                   interface, or artifact is not
                                                   ready.

  `IMPLEMENTATION_COMPLETE_PENDING_VERIFICATION`   Changes are implemented, but
                                                   required acceptance checks have not
                                                   yet passed.

  `VERIFIED`                                       Defined acceptance criteria passed
                                                   and supporting evidence is
                                                   recorded.

  `APPROVED`                                       The authorized owner explicitly
                                                   approved the relevant scope or
                                                   action.
  ------------------------------------------------------------------------------------

**These states are not interchangeable:**

-   Created does not mean implemented.
-   Implemented does not mean verified.
-   Verified does not mean approved.
-   Design approval does not authorize implementation.
-   Implementation approval does not authorize production activity or
    public publishing.

## 8. Verification and evidence

-   Verify against the acceptance criteria defined before creation.
-   Run only relevant checks; reuse existing valid evidence where
    appropriate.
-   Record exact commands/checks, results, test counts, failures, and
    limitations when applicable.
-   Distinguish mocked/hermetic checks from live integration or
    production evidence.
-   Do not claim a test passed unless it was actually run and its result
    observed.
-   Do not claim a feature is production-ready based solely on unit
    tests or a design review.
-   If verification is incomplete, use
    `IMPLEMENTATION_COMPLETE_PENDING_VERIFICATION` or the applicable
    blocked status.

## 9. Safety and authorization boundaries

Unless separately and explicitly authorized, agents MUST NOT:

-   Perform destructive changes, delete or overwrite user work, or
    discard uncommitted changes.
-   Commit, push, merge, rebase, release, deploy, or publish.
-   Trigger production side effects, external customer actions, or paid
    infrastructure usage.
-   Expose, copy into reports, or transmit secrets, credentials, tokens,
    or private user data.
-   Bypass permissions, rights checks, quality gates, human approval, or
    centralized authorization.
-   Enable automatic public publishing or treat silence as consent.
-   Expand their own permissions, tool access, or assigned ownership.

Use least privilege, scoped access, and read-only review where required.
If authorization is ambiguous, stop the protected action and ask the
appropriate owner.

## 10. Questions and escalation

Ask the user or owner only when a genuinely critical decision is missing
and cannot be resolved from authoritative documentation.

Before asking: 1. Search the existing record for the answer. 2. State
the exact decision needed. 3. Explain why it blocks progress and what
depends on it. 4. Present a recommendation only if useful, clearly
labeled as a recommendation---not an accepted decision.

Do not ask the user to repeat information already available. Do not turn
routine implementation choices into unnecessary approval loops when the
documented delegation permits the agent to decide.

## 11. Required completion report

At the end of each work package, provide a concise report:

``` text
Work package:
Status:
Purpose / outcome:
Existing artifacts reused:
Files created or modified:
Authoritative documents and versions checked:
Accepted decisions preserved:
Implementation or design changes:
Verification performed:
Evidence and results:
Unresolved gaps / blockers:
Authorization boundaries respected:
Next dependency / recommended next action:
```

If no files were changed, say so. If a task was already complete,
identify the existing artifact and evidence; do not manufacture a new
deliverable.

## 12. Relationship to the P0 Documentation Handoff & Dependency Protocol

This protocol supplements the existing P0 Documentation Handoff &
Dependency Protocol. For every P0 work package, agents must additionally
identify:

-   Relevant P0 documents and versions.
-   Accepted decisions and owner approvals.
-   Documentation gaps and unresolved decisions.
-   Conflicts or dependencies across work packages.
-   Exact acceptance criteria and authorization status.

The P0 protocol remains authoritative for P0-specific handoffs,
dependency management, ownership boundaries, and authorization. If this
protocol appears to conflict with an authoritative P0 decision or
owner-approved instruction, do not silently choose one: flag the
conflict and follow the established escalation path.

------------------------------------------------------------------------

## Standing instruction

**Discover before creating. Reconcile before changing. Define before
building. Verify before claiming completion. Record before moving on.**

Do not make the project repeat work it has already completed.
