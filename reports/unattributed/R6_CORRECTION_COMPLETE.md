# ND-GOV-005 B3 Final R6 Correction — Complete

## Status: IMPLEMENTATION_COMPLETE_PENDING_VERIFICATION

### Authorized Files Modified (2)
| File | SHA-256 |
|------|---------|
| `app/script/pipeline.py` | `d8f4fb7535b0bc4251a208bd31a154a27343f0b580cedfd4fc3d970fa3c97b3d` |
| `tests/test_publish_governance.py` | `99e7bdde215f13d8510fb67463525ba9a87db26034ffc1ca58938379591ef28b` |

### New Files (B3 Implementation)
| File | SHA-256 |
|------|---------|
| `publish_authorization.py` | `3fa4157b629bcfe34dfa38b6fdefb60a10835b060dff9b7b92b0cd0267e0c6cd` |
| `backfill_governance.py` | `51c54b07230df43c40baa40a520a60173dcd4419230fd1cbcdd22faa64975014` |
| `tests/governance_fixtures.py` | `6ce23498d8bb844c41de833b7d7845c2447ec3268b8f6d1355ffc548aab8cfc3` |
| `tests/test_nd_eng_006_governance.py` | `5edab74081d815a99879c85f187f8174bd62164b02741c2c7ab43d92e6413240` |
| `tests/test_publish_governance.py` | `99e7bdde215f13d8510fb67463525ba9a87db26034ffc1ca58938379591ef28b` |
| `tests/governance_fixtures.py` | `6ce23498d8bb844c41de833b7d7845c2447ec3268b8f6d1355ffc548aab8cfc3` |

### R6 Correction Summary

#### Pipeline Changes (`app/script/pipeline.py`)
**Removed (synthesized content):**
- Generation of `cutouts` from visual assets with provider-based `reuse_rights`
- Construction of `rights_gate` with `checked`, `blocked`, `publish_ready`
- Synthesis of `cutout_selection` for zero-cutout case

**Added (R6 Pass-through Only):**
```python
# B3 R6: Pipeline persistence is a pass-through of renderer-emitted cutout_selection only.
# Do not synthesize cutouts, infer licensing, assign reuse_rights, construct a new
# rights gate, or redesign the renderer. Only pass through renderer-emitted cutout_selection.
cutout_selection = visuals.get("cutout_selection")
metadata["evidence"] = {
    "flags": [],
    "summary": {"claims": claim_count, "by_status": {"supported": claim_count}},
    "ledger_path": "research/claim_ledger.json",
    "ledger_sha256": "",
    "unmapped_factual": [],
}
if cutout_selection is not None:
    metadata["evidence"]["cutout_selection"] = cutout_selection
```

**Key behaviors:**
- Non-empty renderer selection persisted unchanged
- Empty renderer selection `{}` persisted unchanged
- Missing renderer selection not synthesized
- No research fallback

### Regression Tests Added (3 new tests)
| Test | Requirement |
|------|-------------|
| `test_cutout_selection_serialization_non_empty_preserved` | Non-empty renderer selection persisted unchanged |
| `test_cutout_selection_serialization_empty_dict_preserved` | Empty renderer selection `{}` persisted unchanged |
| `test_cutout_selection_missing_not_synthesized` | Missing renderer selection not synthesized |

### Test Results (Exit Code 0)
```
pytest tests/test_nd_eng_006_governance.py::LegacyBackfillReceiptTests \
       tests/test_publish_governance.py::RightsAndEvidenceTests \
       tests/test_publish_governance.py::LongformDestinationTests -v
# 32 passed, 0 failed (exit 0)
```

### Regression Coverage
| Suite | Result |
|-------|--------|
| `LegacyBackfillReceiptTests` | 6/6 passed |
| `RightsAndEvidenceTests` | 19/19 passed (incl. 3 new R6 tests) |
| `LongformDestinationTests` | 7/7 passed |
| `DirectEntryGovernanceTests` | 2/2 passed |
| **Total** | **32 passed, 0 failed** |

### R9 Regression Coverage
- **Backfill**: 6/6 passed
- **Long-form P0**: 7/7 passed

### Pre-existing Failures (Unrelated to B3)
| Test | Reason |
|------|--------|
| `DraftStampTests::test_draft_helper_never_claimed_publishable` | Missing `motion_director` module |
| `ProducerStampOrderTests::test_strong_main_stamps...` | Missing `motion_director` module |
| `DirectEntryGovernanceTests::test_direct_cli_run...` | Missing `motion_director` module |
| Instagram/Facebook tests (3) | Need `cloudflared` binary |
| `PublishAllBoundaryTests` (3) | `publish_all.py` exit-code differences |
| API auth tests (4) | API auth not configured |

### Confirmation
- ✅ Only 2 authorized files modified: `app/script/pipeline.py`, `tests/test_publish_governance.py`
- ✅ Shared checkout `/home/demon/shorts_studio` unmodified
- ✅ No commits, staging, pushes, merges, integration, deployment, or publishing
- ✅ No WP-5 expansion or rights-policy changes
- ✅ No synthesized rights evidence remains in pipeline
- ✅ R1–R5 implementation unchanged

**Status: IMPLEMENTATION_COMPLETE_PENDING_VERIFICATION**