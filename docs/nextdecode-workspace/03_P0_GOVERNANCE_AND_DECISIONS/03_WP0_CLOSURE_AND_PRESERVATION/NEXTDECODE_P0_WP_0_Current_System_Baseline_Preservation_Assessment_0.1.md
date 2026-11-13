# NEXTDECODE — P0-WP-0
## Current System Baseline & Preservation Assessment

**Document ID:** NEXTDECODE_P0_WP_0_Current_System_Baseline_Preservation_Assessment_0.1  
**Version:** 0.1 — Preliminary remote baseline  
**Assessment mode:** Read-only  
**Repository:** `nextdecode01-hub/nextdecode-content-os`  
**Inspection date:** 1 November 2026  
**Status:** PARTIAL — remote baseline inspected; local working-tree verification and runtime test evidence outstanding

---

## 1. Executive summary

The connected private GitHub repository contains a substantial existing Shorts Studio implementation. It is not an empty shell and should not be replaced wholesale.

The remote snapshot includes research, scripting, voice, visual planning/rendering, publishing, approval, scheduling, a runner, Docker Compose configuration, documentation, and 21 test modules.

However, the remote repository does not yet demonstrate the accepted P0 durable shared workflow foundation:
- no GitHub Actions workflow directory was found;
- the repository has no dependency lockfile;
- `api/main.py` stores job records in process memory;
- a database-backed durable queue, transactional outbox/inbox, canonical UUIDv7 identity, and centralized authorization service were not verified in this inspection;
- the current remote README describes a local/n8n operating model, while the accepted long-term architecture is hybrid with a cloud control plane.

**WP-0 is not complete.** The local working tree has significant previously reported uncommitted work. It has not been inspected in this session and must not be overwritten, cleaned, reset, stashed, or assumed to match remote `main`.

## 2. Repository identity and remote baseline

| Field | Observed value |
|---|---|
| Repository | `nextdecode01-hub/nextdecode-content-os` |
| Visibility | Private |
| Default branch | `main` |
| Latest remote `main` commit | `9d38f81ba4f8022d0e820b6a5e1fe2a0fc288c8c` |
| Commit message | `before dashboad impimented` |
| Commit timestamp | 2026-10-30 21:25:35 UTC |
| Parent | `42bf6c7727d5c5cf1af696d839c40855cd4df931` |
| Tree SHA | `d4411395f09487aeee6482185a5cb68cb576e2d3` |
| Recursive tree entries | 128 |
| Tree response truncated | No |
| Branch protection | Disabled on `main` |
| GitHub Actions runs returned | 0 |
| `.github/workflows/` | Not found |
| Dependency lockfile | Not found in repository tree |
| Dependency manifest | `requirements.txt` |

Remote links:
- Repository: https://github.com/nextdecode01-hub/nextdecode-content-os
- Main branch: https://github.com/nextdecode01-hub/nextdecode-content-os/tree/main
- Latest commit: https://github.com/nextdecode01-hub/nextdecode-content-os/commit/9d38f81ba4f8022d0e820b6a5e1fe2a0fc288c8c

## 3. Existing architecture and module map

The remote tree includes these notable components:

| Area | Observed files / modules |
|---|---|
| API | `api/main.py` |
| Research | `app/research/desk.py`, `selector.py`, `topics.py`, `trends.py` |
| Script | `app/script/pipeline.py`, `short.py`, `studio.py`, `longform.py`, `voice_guide.py` |
| Voice | `app/voice/provider.py` |
| Visuals | `app/visuals/motion_director.py`, `stock_fetcher.py`, `visual_assets.py`, `visual_quality.py` |
| Pipelines | `pipelines/short.py`, `pipelines/longform.py` |
| Publishing | `publish_all.py`, `publish_social.py`, `app/publish/*` |
| Approval/review | `approval_integrity.py`, `approve_review.py`, `review_bundle.py`, `review_ledger.py` |
| Scheduling/runner | `scheduled_publish.py`, `run_scheduled_generation.sh`, `n8n_runner.py` |
| Workspace/analytics | `workspace_sync.py`, `analytics_collect.py`, `monetization_tracker.py` |
| Deployment preparation | `compose.yaml`, `Dockerfile.runner` |
| Tests | `tests/` with 21 test modules |

The README documents a strong Shorts pipeline and a separate long-form path. It also documents n8n scheduling and an approval-gated publishing flow. These are repository-documented behaviors; they have not been executed or independently runtime-verified in this assessment.

## 4. Source-level observations

### 4.1 API job state

`api/main.py` defines an in-process `jobs` dictionary protected by a thread lock. Jobs are launched using a daemon thread and a subprocess. This means the inspected API implementation does not itself provide durable shared job state across process restarts or multiple API instances.

**Architecture implication:** this API can be treated as an existing local execution interface, but it is not evidence that the accepted DB-backed workflow/job foundation already exists.

### 4.2 Runner boundary

`n8n_runner.py` exposes a restricted set of runner endpoints, checks a bearer token, serializes execution with a process lock, and invokes fixed scripts. Its current contract is a local runner bridge, not the full accepted worker registry/capability contract.

**Architecture implication:** preserve and assess it as a bounded adapter candidate. Do not silently promote it into the canonical orchestrator or worker-control plane.

### 4.3 Publishing and approval

The inspected `publish_all.py` includes:
- review-only defaults unless publishing configuration is explicitly enabled;
- checks for an approved review package;
- checks that approval is current for the IST day;
- metadata/video SHA-256 matching;
- content and visual checks;
- destination setup checks.

`approval_integrity.py` supplies file hashing and same-day approval checks.

**Architecture implication:** existing approval controls are valuable and must be preserved during assessment. They are not yet proof of the accepted centralized authorization model, immutable version-bound approval records, or complete enforcement across every publishing entry point. A full entry-point and call-graph audit remains open.

### 4.4 Dependencies and reproducibility

`requirements.txt` lists dependencies without pinned versions. The repository tree contains no lockfile. `Dockerfile.runner` installs from `requirements.txt`.

**Architecture implication:** reproducible dependency resolution remains an engineering gap to assess in the appropriate work package. No dependency installation or upgrade was performed.

### 4.5 CI and repository protection

No `.github/workflows/` directory was found, GitHub Actions returned zero workflow runs, and the `main` branch metadata reported branch protection disabled.

**Architecture implication:** there is no remote evidence of an active GitHub Actions CI gate or protected-main policy at this snapshot. This is not evidence that no local test process exists.

## 5. Preservation risks and constraints

The user previously reported a local working tree with extensive modified and untracked files, including Phase 4–11 documentation and implementation work. That earlier report is historical context and has not been refreshed in this inspection.

Therefore:
- do not run `git reset`, `git clean`, `git checkout`, `git stash`, or broad staging;
- do not overwrite files based on remote `main`;
- do not assume the local HEAD equals remote `9d38f81`;
- do not delete or archive apparently duplicate modules until call sites and tests are mapped;
- do not treat a GitHub snapshot as a complete representation of local WIP;
- do not run tests against the user's local environment from this remote-only inspection.

## 6. Evidence status

| Claim | Evidence class | Status |
|---|---|---|
| Remote repository identity and default branch | Direct GitHub metadata | VERIFIED |
| Remote `main` SHA and parent | Direct GitHub commit/branch metadata | VERIFIED |
| 128 tree entries, untruncated | Recursive Git tree response | VERIFIED |
| 21 test modules exist in remote tree | Recursive Git tree paths | VERIFIED |
| No `.github/workflows/` directory found | Remote tree and directory lookup | VERIFIED for inspected remote snapshot |
| No GitHub Actions runs returned | GitHub Actions API response | VERIFIED for returned query |
| No dependency lockfile in remote tree | Recursive tree path inspection | VERIFIED for inspected remote snapshot |
| API jobs are held in process memory | Source inspection of `api/main.py` | VERIFIED at source level |
| Runner uses fixed endpoints and bearer-token check | Source inspection of `n8n_runner.py` | VERIFIED at source level |
| Publishing has approval/hash checks | Source inspection of `publish_all.py` and `approval_integrity.py` | VERIFIED at source level |
| Local working tree is dirty and contains WIP | Earlier user-provided status, not refreshed | HISTORICAL — REVERIFY |
| Current local tests pass | No local execution performed | NOT VERIFIED |
| Remote snapshot tests pass | No test execution performed | NOT VERIFIED |
| Production publishing cannot be bypassed | Full entry-point audit not performed | NOT VERIFIED |
| Durable DB queue/outbox/inbox exists | Not verified in inspected files | NOT VERIFIED |
| Hybrid control plane is deployed | No deployment evidence inspected | NOT VERIFIED |

## 7. WP-0 closure gaps

The following evidence is still required before WP-0 can be marked complete:

1. **Local Git identity:** current local `HEAD`, branch, upstream, and remote tracking SHA.
2. **Local preservation snapshot:** current `git status --short --branch`, including untracked files, without modifying the tree.
3. **Local/remote relationship:** determine whether local `HEAD` is ahead, behind, diverged, or equal to `origin/main`; separately account for local uncommitted changes.
4. **Runtime baseline:** current test collection and test result from the user's actual project environment, if the owner authorizes that read/test-only operation.
5. **Phase 10/11 evidence:** reconcile current source and test evidence against the historical reports; do not add test counts from different runs.
6. **Publishing path map:** enumerate every direct and indirect publishing entry point and establish whether all are subject to the same owner approval, rights, and authorization gates.
7. **Persistence inventory:** map current SQLite/workspace state, run tracking, review ledgers, and any other persistence before designing migrations.
8. **Contract gap map:** map existing entities and state transitions against accepted ADR-001–ADR-010 and CF-01–CF-24.

## 8. Recommended next action

Complete the local preservation and runtime evidence capture before any implementation planning is finalized.

The safest next step is to run read-only Git inspection commands from the user's existing WSL project directory. The following commands only display repository state; they do not alter files or Git history:

```bash
cd /home/demon/shorts_studio

printf '\n=== LOCATION ===\n'
pwd

printf '\n=== LOCAL HEAD ===\n'
git rev-parse HEAD

printf '\n=== BRANCH AND UPSTREAM ===\n'
git status --short --branch
git branch -vv

printf '\n=== REMOTE MAIN ===\n'
git ls-remote origin refs/heads/main

printf '\n=== AHEAD / BEHIND (if upstream exists) ===\n'
git rev-list --left-right --count HEAD...@{upstream}

printf '\n=== TRACKED CHANGE SUMMARY ===\n'
git diff --stat

printf '\n=== STAGED CHANGE SUMMARY ===\n'
git diff --cached --stat

printf '\n=== UNTRACKED FILES ===\n'
git ls-files --others --exclude-standard
```

Do not run `git fetch` as part of this capture; `git ls-remote` reads the remote ref without updating local refs. If the upstream is not configured, the ahead/behind command may report an error; preserve that output rather than changing configuration.

A separate test run should only be performed after the owner explicitly authorizes it. No tests were run for this report.

## 9. Decision and authorization status

- Artifact 08 consolidated owner decision baseline: **APPROVED**.
- Detailed contract freeze: **PENDING**.
- P0-WP-0: **PARTIAL — remote baseline only**.
- P0 implementation authorization: **NOT GRANTED**.
- Repository writes/Git mutations: **NOT AUTHORIZED**.
- Coding-agent execution: **NOT AUTHORIZED**.
- Paid services/cloud deployment: **NOT AUTHORIZED**.

**End of preliminary P0-WP-0 assessment.**
