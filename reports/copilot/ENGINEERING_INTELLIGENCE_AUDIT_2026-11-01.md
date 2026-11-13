# NEXTDECODE Engineering Intelligence Audit

**Date:** 2026-11-01  
**Scope:** Focused, read-only review of backend/API, persistence, approval and publishing, research-source policy, and tests.  
**Validation:** No tests run; no files modified during the audit itself. The report was added afterward at the user's request.

## Five most important findings

| Rank / risk | Evidence and impact | Recommended action | Safe to delegate? |
|---|---|---|---|
| **1 — High: publishing approval can be bypassed.** `publish_social.py` invokes its CLI with `require_approval=False`; standalone publisher CLIs in `app/publish/youtube_upload.py`, `app/publish/facebook_reels_upload.py`, and `app/publish/instagram_reels_upload.py` can publish directly. The guarded `publish_all.py` is therefore not the sole authorization boundary, contrary to accepted ADR-007. | Put authorization at a shared boundary every publishing route must use; test that direct entrypoints reject missing or stale approvals. | **Yes, narrowly**, with owner review of the policy boundary. |
| **2 — High if network-reachable: API routes have no authentication.** `api/main.py` exposes `/start`, `/jobs`, and `/status/{job_id}` without an auth dependency. `/start` can launch a long-running job; request fields are loosely typed/coerced. | Confirm intended network exposure; require authenticated, validated requests and test unauthorized access, malformed inputs, and status access. | **Partly.** Tests and schema validation are bounded; auth contract needs an owner decision. |
| **3 — High: accepted shared-state architecture is not implemented.** API job state is a process-local dictionary (`api/main.py`); `workspace_sync.py` uses local SQLite. The accepted baseline calls for PostgreSQL as the shared system of record and a durable database-backed queue. Restarts lose API job state; multiple processes do not share its concurrency guard. | Design and implement durable job/state storage and leases before treating this as a multi-worker service. | **No, not as a standalone patch.** Delegate the cross-system design/implementation to Qoder or OpenCode. |
| **4 — Medium: cross-posting can partially succeed.** `publish_all.py` uploads sequentially; a later platform failure leaves earlier uploads published. `publish_social.py` also enables partial execution in its CLI. | Track per-platform publication state, make retries idempotent, and clearly report partial outcomes; do not promise atomicity across external platforms. | **Yes for tests and retry-state handling**; broader workflow semantics belong with Qoder/OpenCode. |
| **5 — Medium: the “no Wikipedia” source rule is not enforced.** `app/research/trends.py` registers and fetches Wikipedia trend candidates. Separately, feed helpers in `app/research/desk.py` are stubs returning empty lists. Final fact research does search and fetch sources, so this does **not** prove Wikipedia is used as claim evidence; it can still seed topic discovery, and there is no exclusion regression test. | Exclude Wikipedia from discovery and final source URLs, then test both; retain multi-source research and claim-ledger checks. | **Yes**, as a focused source-policy change with regression tests. |

## Implementation status

- **Implemented:** Strong pipeline fails closed; run manifests record artifact hashes and promotion state; claim ledger captures evidence; approval binds the current video and metadata hashes and checks approval freshness.
- **Partial:** Guarded publish preflight, local run tracking, and SQLite persistence exist, but authorization is bypassable, cross-posts are sequential, and API jobs are in-memory.
- **Missing against accepted decisions:** Centralized non-bypassable publishing authorization, authenticated/schema-validated API routes, PostgreSQL-backed shared state/queue, and an enforced Wikipedia exclusion.

## Existing tests and important gaps

Existing focused tests cover approval hashes/freshness, mocked upload safety, claim lineage, run tracking, storage layout, and Bearer auth on the separate n8n runner.

Important gaps: FastAPI route auth/input/concurrency; direct-publisher approval bypass; partial cross-post retry behavior; Wikipedia exclusion.

Relevant suites: `tests/test_approval_integrity.py`, `tests/test_upload_safety.py`, `tests/test_n8n_runner.py`, `tests/test_run_tracker.py`, and `tests/test_claim_ledger.py`.

## Top five engineering risks

1. Publishing outside the centralized approval boundary.
2. Unauthenticated API access if the service is network-reachable.
3. Lost or inconsistent job state across restarts/processes.
4. Partial cross-posts and unsafe retries after a platform failure.
5. Research topic/source selection violating the no-Wikipedia requirement.

## Focused tasks and ownership

**Copilot can contribute most:**
1. Add tests and close direct publishing approval bypasses.
2. Add API request validation and tests for the agreed authentication contract.
3. Enforce the no-Wikipedia policy with source-selection and source-URL tests.

**Qoder/OpenCode:** own the PostgreSQL-backed queue/system-of-record and worker identity/capability model, plus cross-platform distribution-state design.

## Audit record

- **Files inspected:** `api/main.py`, `publish_all.py`, `publish_social.py`, the three publisher modules, `pipelines/short.py`, `run_tracker.py`, `workspace_sync.py`, `app/research/desk.py`, `app/research/trends.py`, selected tests, README, accepted baseline, and prior audit handovers.
- **Commands executed:** read-only `git status`, `git log`, targeted `git diff`, and focused `rg` searches.
- **Tests executed:** None, per audit constraints.
- **Files modified during the audit:** **NO.** This report was created afterward at the user's request. The pre-existing worktree changes were left untouched.
- **Confidence:** High for code-path findings; medium for operational API exposure and actual use of Wikipedia-derived topics.
