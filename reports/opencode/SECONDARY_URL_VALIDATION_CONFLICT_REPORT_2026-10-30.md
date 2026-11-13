# Shorts Studio — Research Feed URL Validation: CONFLICT REPORT (No Edits Made)

**Agent:** OpenCode (secondary implementation agent)
**Date:** 2026-10-30 · **Task:** Implement scheme validation in `desk._dedupe_source_urls()`
**Action taken:** **STOPPED — no repository file was edited, created, staged, committed, or deleted. Git untouched.** This report is the only file written (docs/ only, per standing report rule).

---

## 1. Verdict

**CONFLICT DETECTED → implementation halted before editing**, per the task's own safety requirement:

> "If the required implementation overlaps with another agent's current changes, STOP and report the conflict instead of editing."

Two independent conflicts were verified:

1. **Same-file, same-region overlap with Qoder's active WIP** (Phase 10.1.1).
2. **Direct semantic conflict with a pinned contract test** in Qoder's in-flight work, which explicitly documents the decision NOT to add scheme validation here.

---

## 2. Verified facts (evidence before deciding)

### 2.1 Current implementation — `_dedupe_source_urls()`

- Location: `app/research/desk.py:663-677`.
- Current behavior (verified by reading code):
  - Accepts any list of URLs; drops empty strings and `None` (line 668-670).
  - Collapses arXiv abs/html/pdf mirrors (line 671-672) and trailing-slash / fragment variants of the same URL (line 672).
  - Does NOT validate schemes — schemeless strings like `not-a-url` are kept as-is and fail later at fetch time.
- Production caller: `desk.py:735` (`research_topic()` → `urls_to_fetch = _dedupe_source_urls(urls_to_fetch)`). Only one production caller; the other three references are tests.

### 2.2 Conflict 1 — Qoder's active unstaged diff is in the exact region

- Git status: `app/research/desk.py` = `M` (unstaged), diff = **+420/−18 across 13 hunks** (verified `git diff --stat`).
- Hunk `@@ -430,6 +677,33 @@ def _dedupe_source_urls(urls: list[str]) -> list[str]:` — Qoder's diff **inserts `merge_duplicate_claims()` immediately after `_dedupe_source_urls`** (verified hunk content from the diff). The function I would modify and the function Qoder is actively inserting are adjacent in the same hunk region.
- Editing `_dedupe_source_urls` body risks merge friction with Qoder's in-flight edit on the very next line block.

### 2.3 Conflict 2 — Qoder's WIP test pins "no scheme validation" as a deliberate contract

`tests/test_research_feeds.py:618-647` (Qoder's untracked Phase 10.1.1 test file) — `test_malformed_url_handling` states verbatim:

> "_dedupe_source_urls collapses mirrors; **it does not validate schemes.** The contract is de-duplication only: empty and None entries are dropped, a trailing slash and a fragment are treated as the same document, and arXiv abs/html/pdf mirrors collapse. **Schemeless strings are kept untouched and fail later at fetch time**, where the error is reported. **Stricter scheme validation here would be a production change; it is proposed separately rather than asserted.**"

And the test asserts (lines 639-647):
- `'not-a-url' in result` — a schemeless string must be KEPT.
- `len(result) == 4` — exact output length under the keep-everything-nonempty contract.

**Impact if I implemented the requested validation:** this pinned test would fail immediately (the schemeless entry would now be rejected → `'not-a-url' in result` fails; length changes). Repairing it would require editing Qoder's test file — an explicit "do not edit files currently being changed by Qoder" target — or would break Qoder's suite at its next run.

### 2.4 Ownership history

- My own prior audit + WIP reconciliation (`reports/unattributed/SECONDARY_WIP_RECONCILIATION_2026-10-30.md`, execution-order step 3) assigned the "optional `_dedupe_source_urls` scheme validation" item to **Qoder's Phase 10.1.1 feed workstream**.
- The Phase 10.1.1 evidence-verification report (`reports/unattributed/PHASE10_1_1_EVIDENCE_VERIFICATION_REPORT.md`, dated today) shows Qoder actively working this exact workstream.

### 2.5 Related tests status (read-only check, nothing modified)

- `tests/test_production_reliability.py:106-114` (`test_dedupe_source_urls_collapses_arxiv_mirrors`) — feeds only https URLs; would not break from scheme validation, but the file itself is in Qoder's modified set (`M`) and pinned to current behavior.
- `tests/test_research_feeds.py:243-253` (`test_duplicate_feed_entries_deduped`) — dedupe-only expectations; consistent with current behavior.

---

## 3. What the correct path forward looks like (recommendation only, no edits)

The task's goal is valid and directly matches the audit Finding F5-adjacent gap ("invalid URLs may fail later during fetching"). Two clean options for the owner/primary agent:

**Option 1 (recommended):** Qoder implements the scheme validation as part of Phase 10.1.1, updating `test_malformed_url_handling` in the same commit (single-owner atomic change: `desk.py` + the contract test it pins). Suggested minimal design for Qoder:
```python
from urllib.parse import urlparse

def _dedupe_source_urls(urls: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for url in urls:
        url = str(url or "").strip()
        if not url:
            continue
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            continue          # reject file:, javascript:, data:, and schemeless
        match = re.search(r"arxiv\.org/(?:abs|html|pdf)/([^/?#]+)", url, re.I)
        key = f"arxiv:{re.sub(r'v\d+$', '', match.group(1))}" if match else url.split("#")[0].rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(url)
    return out
```
Plus updated test expectations in `test_malformed_url_handling` (reject `not-a-url`, keep the mirror-collapse assertions) and a new focused test file covering: valid http/https accepted, duplicates consistent, `file:`/`javascript:`/`data:`/schemeless/empty/None rejected-or-dropped.

**Option 2:** If the owner decree was "I (OpenCode) must implement regardless," require: (a) revert/defer Qoder's adjacent hunk insertion, or (b) permission to edit Qoder's test file. Neither is currently authorized — so STOP stands.

---

## 4. Scope confirmations

- Files I would have needed to touch: `app/research/desk.py` (Qoder-actively-modified) + `tests/test_research_feeds.py` (Qoder-untracked WIP). Both are explicitly protected by the task's own safety rules.
- Files I did NOT touch: everything. `pipelines/short.py`, `api/main.py`, scheduler scripts, Strict Fail-Closed logic, Phase 9 audio (`app/voice/*`, `app/render/ffmpeg_tools.py`), Phase 10.1.1 evidence semantics, approval/publishing safeguards — all untouched.
- WIP preservation: verified — all staged renames, unstaged modifications, and untracked files remain exactly as they were (git status re-checked before decision; no git write operations performed).
- Tests executed: none (test execution was not required to establish the conflict; running tests was unnecessary because the decision to stop precedes implementation, and no change exists to validate).

---

## 5. Bottom line

The requested implementation **directly overlaps Qoder's Phase 10.1.1 workstream** — same file, adjacent active diff, and an explicitly pinned "no scheme validation" contract in Qoder's in-flight tests. Per the task's stop-condition, I halted before editing and am reporting the conflict for unresolved ownership.

**Recommendation:** assign this change to Qoder as Phase 10.1.1 item (Option 1) so `desk.py` + the contract test change land atomically in one owner's commit.

*No edits. No git operations. Awaiting owner decision.*
