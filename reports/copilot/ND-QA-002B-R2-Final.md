# ND-QA-002B-R2-FINAL

## Verdict: REVISE

### Evidence manifest and six-file scope

No evidence manifest was found in `/tmp/nd002b_r2` or the shared `copilot report` folder. The worktree is based at `9d38f81ba4f8022d0e820b6a5e1fe2a0fc288c8c`.

The six apparent task files are `publish_all.py`, `n8n_runner.py`, `scheduled_publish.py`, `tests/test_n8n_runner.py`, `tests/test_publish_governance.py`, and `tests/test_nd_eng_002b.py`. Git reports four tracked modifications and two untracked tests, but the worktree also contains many other modified and untracked files. Without the referenced manifest or a clean attributable baseline, unrelated changes cannot be ruled out.

### `publish_all.py` and stdout tests

The child-result handling maps exit 2 to per-platform `status="blocked"` and `exit_code=2`; aggregate precedence returns 2 for blocked results, then 3 for ambiguous results, then 1 for ordinary failure. Success returns 0.

The four new stdout tests cover empty stdout, malformed JSON, valid JSON without a reason (including non-object JSON), and mixed malformed/progress lines with a valid reason. The generic-case helper asserts aggregate 2, per-platform blocked status, exit code 2, the expected generic reason, and empty code. The mixed-line test asserts aggregate 2 and the extracted blocked code/reason. No tests were run.

### B1 concrete defect: scheduler exit code violates the contract

In `scheduled_publish.py`, child code 2 is labeled `blocked_policy`, but it is excluded from `failed`; when all children are successful or blocked, `main()` returns 0. Thus a blocked run is reported as success instead of exit 2.

Child code 3 is labeled ambiguous, but sets `failed=True`, and `main()` returns 1. `tests/test_nd_eng_002b.py::ScheduledPublishOutcomeTests.test_ambiguous_child_is_labelled_distinctly` explicitly expects 1, contrary to the agreed exit-code contract.

Required behavior is 0 = success, 1 = ordinary failure, 2 = policy blocked, 3 = ambiguous. The scheduler currently collapses both 2 and 3 at its process boundary.

### B2

The inspected integration test stubs the `requests.head` call to raise if reached; no additional concrete B2 defect was identified in the requested scope. The four stdout cases were reviewed by source only.

### Final

Revise the scheduler aggregate return-code behavior and provide the evidence manifest/clean six-file attribution before acceptance. No files outside this report were modified; no tests or fixture-mutating commands were run.
