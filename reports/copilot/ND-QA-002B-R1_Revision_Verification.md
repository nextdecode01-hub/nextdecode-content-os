# ND-QA-002B-R1 — Revision Verification

## REVISE

The requested behavior is implemented in the inspected code, but verification is incomplete: malformed/empty stdout is not directly covered by tests, and `/tmp/nd002b` has no `.git` metadata, so the complete revision scope cannot be confirmed.

1. **Child exit 2 -> blocked / aggregate 2: verified.** `publish_all.py:241-258` maps child return code 2 to per-platform `status="blocked"` and records exit code 2. At `:284-285`, any blocked result returns aggregate 2. `n8n_runner.py:32-45` independently labels exit 2 `blocked_policy` with HTTP 200.

2. **Child stdout parsing: implementation handles malformed/empty output safely; test coverage missing.** `publish_all.py:247-255` tries stdout lines from last to first, catches JSON `ValueError`, accepts only dictionaries with a truthy reason, and falls back to a generic policy reason when no usable JSON line exists. It does not evaluate output. `tests/test_nd_eng_002b.py:128-151` tests valid JSON reason/code only; no malformed or empty stdout regression test was found.

3. **Aggregation sequences: verified for asserted outcomes.** `tests/test_nd_eng_002b.py:107-116` feeds `[0,2,0]` and checks YouTube completed, Facebook blocked (exit 2), Instagram completed, and aggregate 2. `:118-127` feeds `[2,3]`, checks YouTube blocked, Facebook ambiguous (exit 3), and aggregate 2, verifying blocked precedence over ambiguity. The third destination in `[2,3]` defaults to success but is not asserted.

4. **`requests.head` stub: verified.** The integration test at `tests/test_nd_eng_002b.py:261-332` stubs `requests.post` and `requests.get` and patches `requests.head` to raise an assertion if reached. This prevents accidental HEAD egress during the test.

5. **Unrelated changes: not fully verifiable.** `/tmp/nd002b` is not a Git worktree (`.git` absent; `git status` fails). Comparison against the shared checkout found focused deltas in `publish_all.py`, `n8n_runner.py`, the new `tests/test_nd_eng_002b.py`, and two expected exit-code assertion updates in `tests/test_publish_governance.py`. This is not a complete changed-file inventory. No tests were run: the integration test setup removes/recreates `data`, `outputs`, and `research` under its test root, which would violate the read-only request.

**Conclusion:** Revise by adding malformed/empty stdout tests and provide a Git-backed revision or diff manifest so unrelated changes can be ruled out. No files in `/tmp/nd002b` were modified.
