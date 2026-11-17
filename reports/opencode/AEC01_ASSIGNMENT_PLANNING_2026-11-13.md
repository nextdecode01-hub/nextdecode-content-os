# AEC-01 — Readiness-Aware Agent Assignment Planning (Report)

**Date:** 2026-11-13
**Status:** COMPLETE — plan-only assignment flow implemented, integrated and green.
**Milestone:** AEC-01 (follows accepted AR-01 agent readiness inventory + D37-FB runtime closure).

---

## 0. Disclosure: overwrite and recovery of parallel work

While starting this milestone I wrote a first draft of `app/autonomy/agent_assignment.py` at 12:32:52 and **overwrote an untracked implementation that a parallel agent had already created there** (`AgentAssignmentPlanner`, `AssignmentRequest`, `QualificationRecord` + its test contract). Recovery sequence:

1. The original compiled bytecode survived at `app/autonomy/__pycache__/agent_assignment.cpython-314.pyc` (12:28, 11,758 B). I disassembled it (`/tmp/aec01_dis.txt`, 1,284 lines) and reconstructed the source semantics from the disassembly plus the test contract.
2. Before my reconstruction landed, the **parallel agent restored their own v2 module** (current file, 9,576 B). I verified their restored module against their full test contract (`tests/test_agent_assignment.py`, 13 cases) and their CLI integration: **all green**.
3. I therefore did **not** modify `app/autonomy/agent_assignment.py` after their restore; my integration reuses their planner without duplication. All my work went through the `AgentExecutionAdapter` boundary and the test layer.

No further source was lost. The temporary recovery scripts and the disassembly dump were deleted after use.

---

## 1. Working readiness-aware plan-only assignment flow

**Architecture (no duplicate implementations):**

- `app/autonomy/agent_assignment.py` (parallel agent's restored v2 — unmodified by me): fail-closed `AgentAssignmentPlanner.plan()` consuming AR-01 readiness evidence; digest-verifiable `QualificationRecord`; structured `nextdecode.agent-assignment-decision.v1` decision with `process_started=false` on every path.
- `app/autonomy/agent_workspace.py` (my changes): `AgentExecutionAdapter` is the planning boundary and now also:
  - `plan_assignment(request, *, readiness_evidence, qualification, planning_authorized, now)` — delegates to the shared planner and adds the mission-required structured fields at the boundary: `required_missing_evidence` (machine-readable resolution requirement for every denial code) and idempotent **duplicate-assignment detection** (bounded ledger of 4,096 accepted assignment IDs; a repeated accepted ID is denied with `duplicate_assignment`; denied requests do not reserve an ID).
  - `execute(plan)` — an explicit, always-refusing execution boundary (see finding 1).
- `app/autonomy/cli.py` (parallel agent's work): `agent-assignment-plan` subcommand handled **before** any task-store initialization; returns 0 (planned) / 2 (denied or invalid input), JSON in/out.

**Request fields supported:** assignment ID, task reference (`task_id`), agent ID, capability, objective, input references, acceptance criteria, permission scope, correlation ID (+ bounded `timeout_seconds`).

**Readiness checks enforced before any plan is accepted (fail-closed on unknown/missing/stale/conflicting):** agent identity registered; local installation evidence; configuration evidence; qualification (AR-01 state **and** an independent digest-verifiable `QualificationRecord`); fresh availability within the clock-skew bound; not suspended, not revoked; capability declared in the agent's role inventory and matched by qualification; explicit `planning_authorized`. Invocation authorization is never granted — `invocation_authorized` is `false` in every decision's `policy_evaluation`, even when readiness evidence claims otherwise.

## 2. Review findings — all three incorporated with regression tests

| # | Finding | Resolution | Regression tests |
|---|---|---|---|
| 1 | `AgentExecutionAdapter.plan()` rejected the default `invocation_enabled=False` policy before generating a plan | Plan generation no longer requires the invocation switch: the default safe policy produces a full plan that **records the gate explicitly** (`invocation_authorized: false`, `invocation_gate: {invocation_enabled: false, reason: invocation_disabled_by_policy}`). Process execution is separated into a new `execute()` method that refuses **unconditionally** (fail-closed), after validating the plan shape. Unsafe policies (network/credentials/repo-write enabled) still refuse plan generation with `PermissionError`. | `test_invocation_plan_generates_under_the_default_safe_policy`, `test_unsafe_execution_policy_still_refuses_plan_generation`, `test_execute_always_refuses_regardless_of_policy`, `test_execute_rejects_a_non_adapter_plan`, `test_assignment_planning_works_with_invocation_disabled` |
| 2 | `_fresh_observation()` accepted future-dated timestamps as fresh | Bounded clock-skew is enforced: observations up to **+60 s** in the future stay fresh; anything further (e.g. +5 min, +1 h) is not fresh (`availability_evidence_stale`). | `test_future_availability_observation_is_not_fresh` (pre-existing), plus new `test_small_future_clock_skew_stays_fresh_within_bound`, `test_minutes_ahead_observation_is_outside_the_skew_bound` |
| 3 | Qualification relied on `bool(qualification_reference)` — an arbitrary non-empty string qualified | Verifiable qualification evidence is now defined: a qualification reference **plus** `qualification_passed` **plus** a new `qualification_evidence_sha256` field matching `^[a-f0-9]{64}$`. Partial or unverifiable evidence yields the distinct reason `qualification_evidence_not_verifiable`; complete absence keeps `qualification_evidence_missing`. The assignment planner independently enforces the same digest rule via `QualificationRecord.evidence_sha256`. | `test_qualification_reference_alone_does_not_prove_qualification` (pre-existing), plus new `test_passed_flag_with_arbitrary_reference_is_not_verifiable`, `test_malformed_qualification_digest_is_not_verifiable`, `test_digest_verified_qualification_establishes_qualified_state` |

Fail-closed execution is preserved throughout: no process launch, no network access, no credential forwarding, no repository writes were enabled anywhere.

## 3. Test suite and actual results

New isolated suite: **`tests/test_agent_assignment_planning.py` (27 tests)**, with explicitly synthetic test-only fixtures (a `fixture-agent` registry entry, fixture digests, fixture availability timestamps — no real qualified agent is manufactured). Mission scenario coverage:

| Mission scenario | Test(s) |
|---|---|
| 1 unknown agent | `test_unknown_agent_is_denied` |
| 2 unknown capability | `test_unknown_capability_is_denied` |
| 3 missing installation | `test_missing_installation_evidence_is_denied` |
| 4 missing qualification | `test_missing_qualification_is_denied` |
| 5 stale availability | `test_stale_availability_is_denied` |
| 6 suspended agent | `test_suspended_agent_is_denied` |
| 7 revoked agent | `test_revoked_agent_is_denied` |
| 8 invocation unauthorized | `test_invocation_is_never_authorized_by_the_planning_boundary` |
| 9 qualified + available + authorized | `test_qualified_available_authorized_agent_produces_plan_only_decision` |
| 10 structured denial reasons | `test_denial_decision_is_structured_and_machine_readable` |
| 11 duplicate assignment | `test_duplicate_assignment_request_is_denied`, `test_denied_assignment_does_not_reserve_the_assignment_id`, `test_a_fresh_adapter_has_no_assignment_ledger_state` |
| 12 no process invocation | `test_assignment_modules_contain_no_execution_or_network_machinery` (×3 modules), `test_planning_starts_no_process` |
| 13 no network access | `test_assignment_modules_contain_no_execution_or_network_machinery`, `test_planning_uses_no_network` |
| 14 no repository writes | `test_planning_writes_nothing_to_the_repository` |
| 15 every plan `process_started=false` | `test_every_decision_reports_process_started_false` (9 decision variants) |

Plus finding-1 regression tests and `test_assignment_planning_module_matches_the_planner_contract` (adapter boundary delegates to the shared planner without duplication).

**Actual results (final run):**

```
tests/test_agent_readiness.py + tests/test_agent_assignment.py +
tests/test_agent_assignment_planning.py + tests/test_agent_contracts.py +
tests/test_autonomy_core.py + tests/test_autonomy_planner.py +
tests/test_social_orchestrator_integrity.py + tests/test_upload_artifact_integrity.py
→ 134 passed, 7 subtests passed in 2.47 s
(py_compile of all four touched/related modules: OK; git diff --check: clean)
```

The full `tests/` directory was not used as the gate: it contains long-running live-service tests and exceeded a 15-minute budget with no failures reported from the autonomy subset above (noted in blockers).

## 4. Exact changed-file inventory

**Changed by me:**

| Path | Change |
|---|---|
| `app/autonomy/agent_workspace.py` | **+114 / −3 (entire diff is mine; file was unmodified before)** — plan/execute separation (`execute()` added, `plan()` no longer raises on the default policy, `invocation_gate` recorded), `plan_assignment()` with duplicate-assignment ledger and `required_missing_evidence` mapping, `MAX_ASSIGNMENT_LEDGER`, imports |
| `app/autonomy/agent_runtime.py` | (file was already modified by parallel AR-01 work) **my additions:** `import re`; `_QUALIFICATION_DIGEST_RE`; new `AgentReadinessEvidence.qualification_evidence_sha256` field; digest-verifying `qualified` rule with `qualification_evidence_not_verifiable` reason; `transition_requirements["qualified"]` wording |
| `tests/test_agent_readiness.py` | 2 fixture updates (digest added to stale/future tests) + 5 new finding-2/3 regression tests |
| `tests/test_agent_assignment.py` | 1-line fixture update (digest added to `_setup` evidence so the tightened AR-01 rule still admits the synthetic qualified fixture) |
| `tests/test_agent_assignment_planning.py` | **new** — 27 tests (mission scenarios + finding-1 regressions + security boundary) |

**Not mine (parallel agent's work, verified green and preserved):** `app/autonomy/agent_assignment.py` (restored v2), `app/autonomy/cli.py` (`agent-assignment-plan` subcommand), `tests/test_agent_assignment.py` test contract, `app/autonomy/agent_contracts.py` / `tests/test_agent_contracts.py`.

No database migrations, no API changes, no worker-runtime changes, no new dependencies, no n8n/paid providers, no commits or pushes; all other uncommitted/untracked work preserved (`git status` count unchanged apart from my files; `git diff --check` clean).

## 5. CLI usage and example structured output

**Assignment planning (store-free; 0 planned / 2 denied / 2 invalid):**

```
venv/bin/python -m app.autonomy.cli agent-assignment-plan \
  --request '{"assignment_id":"cli-a1","task_id":"task-a1","agent_id":"opencode",
             "capability":"code_review","objective":"Review a bounded change",
             "input_references":[],"acceptance_criteria":["No critical findings"],
             "permission_scope":["read_only"],"correlation_id":"cli-c1"}' \
  [--readiness-evidence '{"opencode": {...}}'] [--qualification '{...}']
```

Example (default invocation — denied, machine-readable, exit 2):

```json
{
  "schema_version": "nextdecode.agent-assignment-decision.v1",
  "plan_id": "e921df5333004b738245a4e8bbee19b1",
  "assignment_id": "cli-a1", "task_id": "task-a1", "agent_id": "opencode",
  "capability": "code_review", "correlation_id": "cli-c1",
  "payload_fingerprint": "81e91fa6…",
  "status": "denied", "accepted": false,
  "denial_reason_codes": ["assignment_planning_not_authorized", "agent_configuration_unverified",
    "readiness_not_available", "readiness_qualification_not_verified_for_capability",
    "readiness_qualification_reference_missing", "availability_not_confirmed",
    "availability_evidence_stale_or_future", "qualification_record_missing"],
  "required_missing_evidence": [{"code": "…", "requirement": "…"}],
  "policy_evaluation": {"planning_authorized": false, "invocation_authorized": false,
    "network_access": false, "credential_forwarding": false,
    "direct_repository_write": false, "protected_actions_permitted": false},
  "process_started": false, "network_access": false, "credential_forwarding": false,
  "direct_repository_write": false, "human_approval_required": true, "observed_at": "…"
}
```

**Invocation plan through the separated boundary (finding 1, exit 0, nothing executed):**

```
venv/bin/python -m app.autonomy.cli agent-workspace prepare
venv/bin/python -m app.autonomy.cli agent-workspace plan <workspace_id> \
  --agent opencode --task "Review the bounded change" --timeout-seconds 300
```
```json
{ "schema_version": "nextdecode.agent-invocation-plan.v1", "plan_id": "…",
  "agent_id": "opencode", "workspace_id": "…", "timeout_seconds": 300,
  "network_access": false, "credential_forwarding": false, "direct_repository_write": false,
  "invocation_authorized": false,
  "invocation_gate": {"invocation_enabled": false, "reason": "invocation_disabled_by_policy"},
  "human_approval_required": true, "process_started": false, "status": "plan_only" }
```
(Demo used a discovery-only stub on PATH; `shutil.which` never executes the candidate.)

## 6. Security boundary verification

- **Source scans:** `subprocess`, `os.system`, `socket`, `urllib`, `Popen`, `http.client` appear in none of `agent_assignment.py`, `agent_workspace.py`, `agent_runtime.py` (parametrized test asserts this permanently; the AR-01 "no subprocess in source" check still passes).
- **Runtime traps:** `subprocess.Popen/run`, `os.system`, `socket.socket/create_connection`, `builtins.open`, `Path.write_text/write_bytes/mkdir` are monkeypatched to hard-fail while planning runs — planning succeeds with all traps armed, proving no process, network or filesystem access in the assignment path.
- **Structural guarantees:** every decision (accepted and all denial variants) reports `process_started=false`, `invocation_authorized=false`, `network_access=false`, `credential_forwarding=false`, `direct_repository_write=false`, `human_approval_required=true`; `execute()` refuses unconditionally; the CLI's assignment command never initializes the task store (test monkeypatches `cli._store` to fail).
- No real agent was manufactured or launched; all fixtures are synthetic and marked test-only.

## 7. Remaining blockers

1. **Stale worker process** (carried over from D37-FB closure): `nextdecode-autonomy-worker.service` (MainPID 813) still runs pre-registry-edit code and blocks tasks with `capability_unavailable`. Requires the owner-authorized `systemctl --user restart nextdecode-autonomy-worker.service` (out of scope here).
2. **CLI planning authorization:** `agent-assignment-plan` currently always plans with `planning_authorized=false` (conservative; accepted decisions therefore require the library/adapter path or an owner-approved CLI flag). Flagged for owner decision — not changed unilaterally since it borders an authorization boundary.
3. **Full-suite runtime:** the complete `tests/` tree exceeds a 15-minute budget (live-service tests); the verification gate above used the complete autonomy/agent subset (134 passed). A CI-mode full run is recommended as follow-up.
4. Acceptance of this report closes AEC-01; owner sign-off pending as usual.

## 8. Next milestone proposal — isolated execution adapter (AEC-02)

Once AEC-01 is accepted:

1. **Isolated execution adapter** (`AgentIsolationExecutor` or an `execute_isolated()` phase behind the existing adapter): runs an *approved* invocation plan only inside the already-prepared sanitized workspace, with:
   - hard prerequisites re-checked at launch time: plan freshness (bounded TTL), workspace manifest still denying network/credentials, `staged-approved` changes only, fresh readiness record still passing every AEC-01 gate;
   - process containment: bounded timeout, bounded output capture, no environment inheritance beyond an explicit allow-list, no credential forwarding, working directory = isolated workspace, repository root never in scope;
   - two-key authorization: explicit owner approval artifact + `planning_authorized` evidence, both recorded in the decision evidence;
   - every run produces the same structured evidence schema (`process_started` becomes truthful only here) and feeds `collect_workspace_changes` → `review_workspace_changes` → `approve_added_file`/`prepare_approved_staging` for the return path.
2. Requires owner approval before implementation because it is the first milestone permitted to start a process (still never on the main repository, never with network, never with credentials).
