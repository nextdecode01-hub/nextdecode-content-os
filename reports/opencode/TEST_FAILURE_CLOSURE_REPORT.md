# OPENCODE — TEST FAILURE CLOSURE REPORT (NEXTDECODE Content OS)

Status: **COMPLETE — ACCEPTED BY OWNER AS MILESTONE (2026-11-13)** — full suite green on three consecutive complete runs.
Baseline HEAD `419801d` is unchanged; **no commit was created** (owner authorization not given).

## 1. Starting commit and environment

| Item | Value |
|---|---|
| Branch | `main` |
| HEAD at start and at completion | `419801d1638c8e678e1a41ec201693fcdf2a95bb` — "feat: consolidate content OS runtime and governance baseline" (== the baseline stated in the order) |
| Environment | WSL2 Ubuntu · Python 3.14.4 (`venv/bin/python`) · pytest 9.1.1 · pluggy 1.7.0 · anyio 4.15.1 · ffmpeg 8.0.1 |
| Test interpreter | `venv/` matches CI's Python 3.14 (`.venv/` is an empty stub) |
| Repo tree notes | 5 modified docs files present at mission start were reverted and new untracked `reports/D21–D23_DASHBOARD_INCREMENT_*.md` files appeared **by parallel dashboard work** during the mission (verified HEAD never moved). This mission touched none of `dashboard/`, `ui-prototype/`, or the docs. |

## 2. Initial test baseline

### Attempt 0 — `venv/bin/python -m pytest -q` (repo root, no args)

**Interrupted: 74 errors during collection (1.13s).** Every real `tests/test_*.py`
failed with pytest "import file mismatch": the module was first imported from

```
outputs/autonomy/agent-workspaces/02b5cc2ea70e41c691adc68981958b96/workspace/tests/test_*.py
```

### Root cause (attempt 0)

- No `pytest.ini`/`pyproject.toml` existed and CI ran `python -m pytest -q` from repo root, so pytest scanned the **entire tree** with no `testpaths`.
- `outputs/autonomy/agent-workspaces/<hash>/workspace/` contains a **full snapshot of the repo including a copy of `tests/`** (runtime autonomy-worker data; verified gitignored at `.gitignore:56`, so CI never sees it).
- Test modules are collected rootless (by basename). The snapshot copy under `outputs/…` is reached first (alphabetically before `tests/`), gets imported and cached in `sys.modules`; collecting the real `tests/test_api_auth.py` then hits the basename collision → "import file mismatch".
- Verified the workspace is not referenced by any test (`grep -rn agent-workspaces tests/` → no hits).
- Single-file collection of the same test (`pytest --collect-only tests/test_api_auth.py`) succeeded → tests themselves import cleanly; this is collection-scope pollution, not a product defect.

### Fix 1 (P0-A): `pytest.ini` (new file, repo root)

```ini
[pytest]
testpaths = tests
```

Smallest correct fix: scopes collection to the real suite, keeps CI semantics
identical, does not weaken any test, and makes local runs deterministic
against future agent-workspace snapshots. (Alternative rejected: adding
`tests/__init__.py` would change rootless import semantics and likely break
`import governance_fixtures` style helpers.)

**Evidence:** after fix — `pytest --collect-only -q` → **921 tests collected, 0 errors**.

## 3. Run 1 — first full green-collection suite (post Fix 1)

Command: `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -q`
Saved output: `/tmp/nd_pytest_run1.txt` (WSL)

```
22 failed, 888 passed, 11 skipped, 71 subtests passed in 84.70s
```

## 4. Failure inventory (Run 1, exact IDs)

| # | Cluster | Failing tests |
|---|---|---|
| 1 | `tests/test_autonomy_core.py` (5) | `test_worker_claim_execute_and_persist_evidence`, `test_retryable_failure_requeues_until_attempt_limit`, `test_stale_worker_cannot_finish_claimed_task`, `test_recursive_dependency_failure_blocks_all_descendants`, `test_worker_passes_successful_dependency_outputs_as_transient_context` |
| 2 | `tests/test_autonomy_planner.py` (3) | `test_plan_dependencies_are_respected_and_plan_completes`, `test_failed_dependency_blocks_descendant`, `test_failed_branch_does_not_mark_plan_terminal_while_independent_work_is_queued` |
| 3 | `tests/test_social_orchestrator_integrity.py` (4) | `test_concurrent_posts_are_serialized_and_only_one_adapter_runs`, `test_corrupt_ledger_blocks_before_adapter`, `test_file_adapter_receives_pinned_snapshot_and_ledger_prevents_duplicate`, `test_provider_success_with_ledger_failure_is_reported_ambiguous` |
| 4 | `tests/test_upload_artifact_integrity.py` (10) | FB: `test_positive_unchanged_artifact_transfers_bound_bytes`, `test_negative_mutation_after_authorization_never_reaches_the_network` · IG: `test_positive_meta_model_serves_snapshot_bytes_over_http`, `test_negative_mutation_after_authorization_prevents_the_tunnel`, `test_ledger_write_failure_returns_ambiguous_after_remote_publish`, `test_snapshot_and_tunnel_cleanup_when_meta_transfer_raises` · YT-short: `test_positive_unchanged_artifact_uploads_the_snapshot`, `test_negative_replacement_between_authorizations_blocks_the_upload` · YT-longform: `test_positive_unchanged_longform_artifact_uploads_the_snapshot`, `test_negative_longform_replacement_blocks_the_upload` |

## 5. Root causes and fixes

### Clusters 1–2 — autonomy core + planner (8 failures)

**Root cause A — implementation self-inconsistency (fixed in implementation).**
`Capability` (app/autonomy/registry.py) declared the default
`sandbox_profile: str = "project-readonly"`, but the package's own fail-closed
policy `LocalWorkerPolicy` (app/autonomy/execution_policy.py) allowlists only
`{bwrap-project-ro-network, in-process-bounded, bwrap-project-ro-output-rw,
in-process-readonly}`. Every capability constructed the plain documented way —
which is exactly how all TaskWorker-driven tests build test capabilities — was
therefore permanently rejected with
`PolicyDecision(False, "sandbox_profile_not_allowlisted")`, and
`TaskWorker.run_once` (worker.py:117–122) marked the task `blocked` **before
the handler ever ran**. `"project-readonly"` existed nowhere else in the
codebase: it is a stale default left behind when the profile allowlist was
introduced. This is an implementation defect (the dataclass default violated
its own package policy), not a test defect.

**Fix A:** default changed to `sandbox_profile: str = "in-process-bounded"`
(allowlisted; the honest default since handlers execute in-process and the
default scopes are `workspace:read`+`artifact:write`). **The policy allowlist
itself was not touched** — networked/bwrap profiles must still be declared
explicitly, and all ten default-registry capabilities keep their explicit
profiles. No capability gained authority.

**Root cause B — contract drift on `TaskStore.finish` (fixed in tests).**
`finish(task_id, worker_id, result, attempt)` (store.py:326–336) requires the
fenced `attempt` and raises `RuntimeError("task lease lost or fenced; …")` on
owner/attempt mismatch — the stale-worker fence. Tests still called the old
3-argument form:

- `tests/test_autonomy_core.py` — 2 direct calls
- `tests/test_autonomy_planner.py` — 4 direct calls across the 3 failing tests
- `tests/test_autonomy_postgres.py` — 4 direct calls (skipped locally because
  `NEXTDECODE_TEST_POSTGRES_DSN` is unset, but latently broken; fixed for
  Postgres parity rather than leaving known-broken skipped tests)

**Fix B:** each call now passes the attempt taken from the claim row
(`attempt=claimed["attempts"]`). In
`test_stale_worker_cannot_finish_claimed_task` the non-owner worker presents
the *current* attempt number, so the owner-mismatch branch of the fence is the
branch under test.

### Cluster 3 — social orchestrator (4 failures)

**Root cause — contract drift on the protected-action receipt (fixed in test
fixture).** `social.publish()` verifies the WP5 receipt before any adapter,
ledger read, or concurrency logic runs
(social_orchestrator.py:574 → authorization.verify_protected_action_decision:596–629).
A receipt must carry `status="authorized"`, the scope keys
`action_type="publish" / platform / purpose / destination="private"`, the nine
binding fields and a matching `authorization_id` (SHA-256 over the canonical
binding). The test mocked `authorize_publish` with
`{"video_sha256": …}` only → `PublishNotAuthorized` fired before the behavior
under test. Not an implementation defect: the stricter receipt verification is
intentional fail-closed governance.

**Fix:** new helper `_authorized_receipt(platform, video_sha256, purpose)`
mirrors the real contract (imports `POLICY_VERSION`, computes the canonical
`authorization_id`), and the `authorize_publish` mock builds a per-platform
receipt via `side_effect`. The tests' actual subjects — ledger duplicate
prevention, flock serialization, ambiguous-failure reporting, corrupt-ledger
fail-closed — are unchanged and now execute.

### Cluster 4 — upload artifact integrity (10 failures)

**Root cause — same receipt contract, stale `_decision()` fixture.** The
upload modules verify the receipt immediately after authorization
(facebook_reels_upload.py:104 `platform="facebook"`,
instagram_reels_upload.py:260 `platform="instagram"`,
youtube_upload.py:77 `platform="youtube", purpose="short"` via
`upload_video` defaults, youtube_longform_upload.py:55
`platform="youtube_longform", purpose="longform"`); the fake
`_decision()` carried only 4 keys → `PublishNotAuthorized` replaced the
flow under test.

**Fix:** `_decision(video_bytes, *, platform, purpose="short")` now emits the
full receipt shape with the per-platform scope and a correct
`authorization_id`; all six call sites updated. The negative tests keep their
intent unchanged: post-authorization mutation is still detected by the
digest-pinned snapshot stage and still fails closed with
`ArtifactIntegrityError` before any network/tunnel activity — only now the
rejection happens at the correct stage, as the tests were written to prove.

## 6. Full-suite results after each meaningful batch

| Run | Command | Result | Notes |
|---|---|---|---|
| 0 | `venv/bin/python -m pytest -q` | 74 collection errors | pre-`pytest.ini` |
| 1 | same | **22 failed / 888 passed / 11 skipped** (84.70s) | post Fix 1; `/tmp/nd_pytest_run1.txt` |
| focused | pytest on the 5 affected test files | **71 passed / 11 skipped / 0 failed** (0.94s) | after batch-1 fixes |
| 2 | full suite | **910 passed / 11 skipped / 0 failed** (79.04s) | post batch 1; `/tmp/nd_pytest_run2.txt` |
| 3 | full suite | **910 passed / 11 skipped / 0 failed** (117.16s) | consecutive run 1/2; `/tmp/nd_pytest_run3.txt` |
| 4 | full suite | **910 passed / 11 skipped / 0 failed** (116.95s) | consecutive run 2/2; `/tmp/nd_pytest_run4.txt` |
| 5 (PG) | full suite **with** `NEXTDECODE_TEST_POSTGRES_DSN` against an isolated disposable PostgreSQL 17.4 cluster | **921 passed / 0 skipped / 0 failed** (89.72s) | every test executed, zero skips; `/tmp/nd_pytest_run5_postgres.txt` |

Totals reconcile: 921 collected in every run (910+11); all 22 Run-1 failures
resolved with zero regressions and zero test-count change.

Reproduce:

```bash
cd /home/demon/shorts_studio
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -q
```

## 7. CI verification and remaining risks

### CI parity evidence (every ci.yml step replicated locally in WSL, Python 3.14.4)

| CI step | Local result |
|---|---|
| `pip install -r requirements.txt` on Python 3.14 | **fresh venv install OK** (`/tmp/nd_ci_parity_venv`) |
| `python -m pip check` | "No broken requirements found" (both venvs) |
| `python -m compileall -q app api pipelines tools tests` | OK |
| `python -m py_compile setup_check.py` | OK |
| `bash -n` on every tracked `*.sh` | OK |
| `ffmpeg` (CI apt-installs) | 8.0.1 present |
| `python -m pytest -q` | green ×3 (runs 2–4) |
| Postgres-dependent tests | CI has no Postgres service → `NEXTDECODE_TEST_POSTGRES_DSN` unset → 11 skipped, **identical skip set locally** |
| Collection scope | `git ls-files` shows **no tracked test file outside `tests/`** → `testpaths = tests` cannot change CI collection; the `outputs/` pollution that broke local collection is gitignored and absent from a fresh checkout |

**Not executed:** the GitHub Actions job itself (push or `workflow_dispatch`
requires owner authorization). All of CI's steps were instead executed locally
with a matching interpreter — that is the evidence base; no unverified parity
claim is made beyond it.

### Security / governance acceptance (verified, not weakened)

- `verify_protected_action_decision` and every receipt scope/binding check: **untouched** — fixtures were upgraded to satisfy the real contract.
- Upload snapshot integrity: negative mutation tests still fail closed with `ArtifactIntegrityError` before any network/tunnel action.
- Destination gate (`destination="private"`, public publishing disabled), approval-integrity, evidence, rights and storyboard gates: untouched and passing.
- Registry policy allowlist `ALLOWED_SCOPES` / `ALLOWED_PROFILES`: **unchanged**; the only implementation change aligns a stale dataclass default with the existing allowlist — no capability gained authority.
- Stale-worker attempt fence: preserved and now additionally covered by the corrected tests.

### Working-tree reconciliation and post-acceptance checks (owner P0/P1 follow-ups)

- **Exact diff (P0):** 6 tracked files changed, +94/−23; full file-level patch preserved at `/tmp/nd_mission_diff.patch` (282 lines). Untracked additions owned by this mission: `pytest.ini` and this report — nothing else.
- **Parallel-work ownership (P0):** `dashboard/`, `reports/D21–D23_DASHBOARD_INCREMENT_*.md`, `ui-prototype/` and the `*:Zone.Identifier` files are pre-existing/parallel work — untouched by this mission. The 5 docs files that were modified at mission start now match HEAD byte-for-byte (`git diff -- docs/` is empty); they were reverted by the parallel work, never committed, never touched here. HEAD never moved (`419801d`).
- **PostgreSQL integration (P0): CLOSED with execution evidence.** No Postgres service existed in the environment, so an isolated disposable PostgreSQL 17.4 cluster was created from portable binaries under `/tmp` (zero system footprint): `initdb -U postgres -A trust` → isolated per-test schemas (the fixture creates and drops `autonomy_test_<hash>` schemas) → run → `pg_ctl stop` → cluster deleted. First the 11 previously-skipped tests alone: **11 passed (1.03s)**; then the complete suite with the same DSN: **921 passed / 0 skipped / 0 failed (89.72s)**. Server log preserved at `/tmp/nd_pgtest_pg17_server.log`.
- **Caller compatibility (P1): CLOSED.** `git grep` across `app/ api/ pipelines/ tools/` finds exactly one production caller of `TaskStore.finish` — `app/autonomy/worker.py:171`, already passing `attempt=attempt` — and both store implementations (`store.py:326`, `postgres_store.py:438`) share the identical fenced signature. No integration update is required.
- **Hosted CI (P0): still pending** owner authorization to push or trigger `workflow_dispatch`. All CI steps remain replicated locally (table above).
- **Dependency reproducibility (P1): open by owner decision** — locking/constraining `requirements.txt` is a repo change requiring owner approval before it is made.

### Remaining risks

1. `pytest.ini` and this report are untracked; if the owner commits them, CI gains the same deterministic local collection scope (harmless — CI's fresh checkout collects `tests/` either way).
2. `requirements.txt` uses loose pins; CI resolves wheels at run time. Fresh-install parity was verified today (Python 3.14.4) but is not frozen.
3. ~~`test_autonomy_postgres.py` fixes are DSN-gated and could not be executed locally~~ — **CLOSED post-report:** all 11 Postgres tests passed against the isolated cluster, and the full suite with the same DSN was 921/0/0 (see §7).
4. ~~`TaskStore.finish` now requires `attempt` everywhere~~ — **CLOSED post-report:** single production caller, already compliant (see §7).
5. Full-suite wall time varies (79s vs 117s) across identical runs; identical pass/skip sets each time (no order-dependent failures observed).

## 8. Final acceptance verdict

**PASS.**

- Full collection: 921 tests, 0 errors.
- Failures resolved: 22 → 0 (8 autonomy, 4 social orchestrator, 10 upload integrity; plus 4 latent postgres-test breakages fixed preventively).
- Final state: **910 passed / 11 skipped / 0 failed** on three consecutive complete runs (runs 2, 3, 4); with an isolated PostgreSQL 17.4 cluster the complete suite ran **921 passed / 0 skipped / 0 failed** (run 5).
- No skip/xfail/quarantine was added; no assertion loosened; no security or governance control weakened.
- CI steps verified locally with a matching interpreter; the only unverifiable step is triggering the hosted job itself (needs owner authorization to push).
- Exact final commit: **none** — no commit was created; working tree carries the changes on top of HEAD `419801d`.

### Files changed by this mission

| File | Change |
|---|---|
| `pytest.ini` *(new)* | collection scope fix (`testpaths = tests`) with root-cause comment |
| `app/autonomy/registry.py` | stale default `sandbox_profile` → allowlisted `in-process-bounded` (+ comment) |
| `tests/test_autonomy_core.py` | 2 `finish()` calls carry the fenced `attempt` |
| `tests/test_autonomy_planner.py` | 4 `finish()` calls carry the fenced `attempt` |
| `tests/test_autonomy_postgres.py` | 4 `finish()` calls carry the fenced `attempt` |
| `tests/test_social_orchestrator_integrity.py` | `_authorized_receipt()` helper; mock emits the real receipt contract |
| `tests/test_upload_artifact_integrity.py` | `_decision()` emits the full receipt with per-platform scope; 6 call sites updated |
| `reports/opencode/TEST_FAILURE_CLOSURE_REPORT.md` *(new)* | this report |
