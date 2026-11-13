ND-ENG-006-R9: Cross-Platform Backfill Digest Correction
=========================================================

## Root Cause (Confirmed)
**File**: `backfill_governance.py:178` (R8)
```python
metadata_file.write_text(stamped_text, encoding="utf-8")  # Windows translates \n → \r\n
```
- Writer: `write_text()` → CRLF on Windows, LF on Linux
- Digest: `hashlib.sha256(stamped_text.encode("utf-8"))` → always LF
- Validator: hashes actual file bytes → CRLF on Windows, LF on Linux
- **Result**: Valid backfill rejected on Windows with `Legacy-backfill receipt does not match the stamped metadata bytes`

## Byte-Level Evidence
| Stage | Linux (LF) | Windows (CRLF before fix) |
|-------|------------|---------------------------|
| Written bytes | `...\n}\n` | `...\r\n}\r\n` |
| File digest | `edfcd440...` | `2677da95...` |
| Journal digest | `edfcd440...` | `0f4cb907...` |
| Match | ✅ | ❌ |

## Fix (1 line, `backfill_governance.py:178`)
```python
# Before:
metadata_file.write_text(stamped_text, encoding="utf-8")
# After:
metadata_file.write_bytes(stamped_text.encode("utf-8"))
```
- Writes exact bytes that were hashed (LF only)
- No platform-dependent newline translation
- Deterministic cross-platform

## Verification
| Environment | Valid Backfill + Reapproval | All Tamper/Invalid Cases Blocked |
|-------------|----------------------------|----------------------------------|
| Linux (LF) | ✅ | ✅ |
| Windows (simulated CRLF) | ✅ | ✅ |

**Cross-platform test matrix**: 8/8 pass
- Valid LF ✅ | Valid CRLF simulation ✅ | Tampered metadata ✅ | Tampered journal ✅ | Foreign ref ✅ | Spliced ✅ | Missing journal ✅ | Deterministic LF ✅

## Governance Suite Results
- `LegacyBackfillReceiptTests`: 6/6 pass
- `LongformDestinationTests`: 7/7 pass (includes 3 new P0 tests)
- `DirectPublisherApprovalTests` (YouTube): pass

## Acceptance Bundle
- **Location**: `C:\Users\yadav\Downloads\ND-ENG-006_R9_acceptance.tar.gz`
- **SHA-256**: `0021a07b3298e1a857b53d9ab98da55482069231ed2b95a8d789b3b3a389c53a`
- **Files**: 25 manifest entries (26 on disk including SHA256SUMS)
- **Replay**: `sha256sum -c SHA256SUMS` → `REPLAY_OK`
- **Contents**: R9 fixed files, R4 baseline excerpt, R6 diffs, evidence manifest, README
- **Secrets**: Clean — no `.env`, credentials, venvs, runtime data

## Changed Files (Minimal)
1. `backfill_governance.py` — line 178: `write_text` → `write_bytes` (1 line)

## Test Commands
```bash
# Cross-platform regression
python3 cross_platform_test.py
# Governance suite
PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest \
  tests/test_nd_eng_006_governance.py::LegacyBackfillReceiptTests \
  tests/test_publish_governance.py::LongformDestinationTests -v
```

## Recommendation
**Ready for integration**. Single-line fix eliminates Windows CRLF/LF digest mismatch while preserving all tamper detection. No behavior changes on Linux; Windows now works correctly.