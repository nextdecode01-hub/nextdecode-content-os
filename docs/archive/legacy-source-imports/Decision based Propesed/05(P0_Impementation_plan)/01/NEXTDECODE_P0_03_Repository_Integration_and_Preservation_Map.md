# NEXTDECODE P0 — Repository Integration & Preservation Map

**Version:** 0.1  
**Status:** Planning map; paths are logical targets, not verified current files  
**Project:** `/home/demon/shorts_studio`

## 1. Purpose

Provide a safe conceptual map for integrating the Content OS foundation with the existing Shorts Studio without assuming that proposed directories already exist or that current files are safe to overwrite.

## 2. Existing system to preserve

The existing project contains a Python/FFmpeg Shorts production pipeline and related modules, including historically referenced areas:
- `api/main.py`
- `app/research/`
- `app/script/`
- `app/visuals/`
- `app/render/`
- `app/publish/`
- `pipelines/short.py`
- `publish_all.py`
- `publish_social.py`
- tests under `tests/`

These are historical references from prior user-provided project context. Their current contents and exact status have not been freshly inspected in this planning step.

## 3. Logical target boundaries

The following is a proposed logical layout, not an instruction to create all directories immediately:

```text
shorts_studio/
  api/                         # Existing API; integrate through versioned contracts
  app/
    research/                  # Existing specialist research capabilities
    script/                    # Existing script generation
    visuals/                   # Existing visual planning/assets
    render/                    # Existing FFmpeg/rendering engine
    publish/                   # Existing adapters; central gates must be enforced
    content_os/
      domain/                  # Canonical entities and domain rules
      application/             # Use cases and orchestration interfaces
      contracts/               # Versioned request/event schemas
      persistence/             # Repositories and transaction boundaries
      workflow/                # Workflow/task coordination
      execution/               # Jobs, attempts, leases, dispatch
      workers/                 # Registration, identity, capabilities
      artifacts/               # Artifact metadata, manifests, transfer
      governance/              # Rights, QA, review, approval, authorization
      adapters/
        shorts_studio/         # Bounded integration to existing pipeline
  migrations/                  # Versioned additive database migrations
  tests/
    content_os/
      unit/
      integration/
      recovery/
      security/
      contract/
  docs/
    content_os/                # Approved contract and implementation docs
```

## 4. Ownership boundaries

| Logical area | Owns | Must not own |
|---|---|---|
| Domain | Canonical identity, entity rules, invariants | Database vendor details, UI |
| Persistence | DB schema, transactions, repositories | Product policy decisions |
| Workflow | Workflow and task state/dependencies | Worker process internals |
| Execution | Job, attempt, lease, retry and dispatch | Editorial approval |
| Worker registry | Worker identity, trust and capability facts | Global authorization policy |
| Artifact service | Artifact/version/manifest/transfer records | Editorial content identity |
| Governance | QA, rights, review, approval and authorization decisions | Media rendering |
| Shorts adapter | Translate bounded jobs to existing pipeline | Bypass central authorization |
| Distribution adapter | Execute specifically authorized destination action | Self-authorize publication |

## 5. Integration pattern

1. Content OS creates a canonical content item and variant.
2. Workflow service creates a task and requests a durable job.
3. Execution service dispatches a bounded job to an authorized worker.
4. Shorts Studio adapter invokes the existing pipeline for the approved task type.
5. Worker returns structured result and output references.
6. Artifact service registers immutable artifact/version and integrity metadata.
7. Governance services evaluate applicable QA, rights, review and authorization gates.
8. Distribution adapter remains disabled for automatic public publishing unless a separate policy and authorization explicitly permit it.

## 6. Preservation rules

Latest historical snapshot: 23 tracked modified files and 56 untracked paths, no staged changes. Do not assume the snapshot is still current; do not request a broad inventory again without a concrete reason.

Prohibited without separate explicit approval:
- `git reset`, `git checkout`/restore of user work, `git clean`, stash, destructive rebase.
- Deleting, renaming or overwriting existing files.
- Broad `git add`, commit, push, branch or remote changes.
- Destructive database migrations or data deletion.
- Provider activation, spending, deployment or public publishing.

Implementation should prefer additive modules and narrowly scoped migrations. If a target path collides with existing work, stop and report the exact conflict rather than replacing it.

## 7. Proposed integration acceptance checks

- Existing Shorts pipeline can still be invoked through its current supported path.
- New adapter does not import internal pipeline details unnecessarily.
- Adapter input is schema-validated and bounded.
- Worker authorization is checked before execution.
- Job/attempt identifiers and correlation IDs are preserved.
- Output is registered as an immutable artifact version.
- Retries do not duplicate logical work or unprotected external side effects.
- Publishing adapters cannot bypass centralized authorization.
- Existing tests remain intact; new tests are isolated and deterministic.
- No unrelated files are modified.

## 8. Open design choices

- Exact module/package naming and import boundaries.
- Whether to place the new package under `app/content_os/` or a separate top-level package.
- Migration framework and database connection strategy.
- Test fixture and local development database approach.
- Exact adapter invocation contract and process isolation.
- Whether a separate worktree is appropriate for implementation.

These require repository-specific inspection and owner-approved implementation planning. This map does not establish that any proposed path exists.
