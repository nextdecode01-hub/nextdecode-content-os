# ND-QA-002B-R3 — Final Independent Verification

## Verdict: REVISE

### Concrete B1 defect

A blocked-only scheduler run exits with code `2`, but its top-level JSON reports `"status": "completed"`. In `scheduled_publish.py`, that status is computed from `failed or ambiguous` and omits the `blocked` flag. The blocked-child test checks the child outcome label and aggregate exit code, but does not assert the top-level status.

### Contract and precedence

Source inspection confirms the scheduler return precedence:

1. Any blocked result → `2`
2. Otherwise any ambiguous result → `3`
3. Otherwise ordinary failure → `1`
4. Otherwise success → `0`

The regression tests cover all-success, ordinary failure, blocked, ambiguous, and the requested mixed outcomes. They assert the aggregate codes and per-child labels.

`publish_all.py` and `n8n_runner.py` use compatible mappings: `0` completed, `2` blocked, `3` ambiguous, and other nonzero codes ordinary failure.

### Evidence and repository state

The R3 evidence file exists at `/tmp/ND-ENG-002B-R3-EVIDENCE.md`. Its recorded focused diffs match the scheduler and scheduler-test changes inspected. Both the R3 worktree and shared repository are at `9d38f81ba4f8022d0e820b6a5e1fe2a0fc288c8c`.

The current shared worktree shows no changes to `scheduled_publish.py` or the R3 test file; the R3 test file is absent from the shared checkout. The evidence manifest's historical shared-tree snapshot cannot be independently confirmed from current state.

### Verification limits

No tests were run and no files were modified.
