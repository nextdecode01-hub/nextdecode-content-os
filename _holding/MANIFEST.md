# Quarantine manifest

**Created:** 2026-11-05
**Scope:** reversible quarantine only; no source deletion.

| Original path | Holding path | SHA-256 | Disposition |
|---|---|---|---|
| archive/legacy-oauth/get_code.py | _holding/legacy-oauth/get_code.py | 6bbf7a1a3c2eebe61155fa96cda2f53826e9439fe1b99d6a1ffd8f66ab1d698c | QUARANTINED; dormant legacy OAuth helper; security review and modern re-auth replacement required |
| archive/legacy-oauth/manual_auth.py | _holding/legacy-oauth/manual_auth.py | 44c1292e18739627acb204c5c1b9c2fcb8cbbfbe451e3f9598b28a44366303ca | QUARANTINED; dormant legacy OAuth helper; security review and modern re-auth replacement required |

## Evidence and restore

- Repository-wide text search found no runtime imports or command invocations; references were tests and documentation only.
- manual_auth.py uses the legacy localhost:5678 callback. get_code.py exchanges a supplied code and writes the local YouTube token file.
- Neither helper is a verified replacement for the current token refresh/authentication path. Do not execute either routinely.
- Restore by moving a file to its original archive/legacy-oauth/ path and updating tests/docs in the same change.
- SHA-256 values were captured before the move. File contents were not modified.
