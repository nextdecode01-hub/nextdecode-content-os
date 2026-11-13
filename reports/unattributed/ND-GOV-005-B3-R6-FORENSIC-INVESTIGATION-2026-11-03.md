# ND-GOV-005 — Independent R6 Forensic Investigation

**Document ID:** `ND-GOV-005-B3-R6-FORENSIC-INVESTIGATION-2026-11-03`  
**Mode:** READ-ONLY forensic review of `/tmp/nd_gov_005`  
**Date:** 2026-11-03  
**Status:** R6 IS NOT ACCEPTED — the current implementation does not satisfy the frozen contract

> No production edits, test edits, fixture/mock edits, commits, pushes, merges, deployments, publishing or uploads were performed. The shared checkout was not inspected or changed. Findings are based on the snapshot named below plus two read-only import probes.

---

## 1. Snapshot identity and limitations

| Item | Value at review time |
|---|---|
| Snapshot | `/tmp/nd_gov_005` |
| HEAD (from snapshot metadata) | `9d38f81ba4f8022d0e820b6a5e1fe2a0fc288c8c` |
| `app/script/pipeline.py` | 388 lines, `2120ef6d584189d82bb2d947ff623351756b3206881810814e4a40b3535f4a13`, mtime 2026-11-02T00:20:37 |
| `motion_render.py` | 644 lines, `aa76e900d3ef9dfc4424972ec36518b11fec1632fa3573d27bd3f6e24ac018f7`, mtime 2026-11-01T19:40:31 |
| `publish_authorization.py` | 643 lines, `3fa4157b629bcfe34dfa38b6fdefb60a10835b060dff9b7b92b0cd0267e0c6cd` |
| `tests/test_publish_governance.py` | 781 lines, `84716460c926b2ccdb31f454c97c7b4f5ba81f624872ba0de0e32cf72b1c65e2`, mtime 2026-11-02T00:43:50 |
| `tests/governance_fixtures.py` | `6ce23498d8bb844c41de833b7d7845c2447ec3268b8f6d1355ffc548aab8cfc3` |
| `app/render/assembly.py` | `79f0bc20f27ae88d1e7e9c2efad5b90b7743851779cce931003fb74b86cacc7b`, transferred 2026-11-02T02:59:02 |
| `B3_DEPENDENCY_RECONCILIATION_MANIFEST.md` | 182 lines, mtime 2026-11-02T03:05:27 |
| `motion_director.py` | 6-line shim, `0fc6fe188191b9418c7a6be1edbb0fcbdd78ccdf8de459ea7c59c8c35b157bc8`, mtime 2026-11-03T02:23 |

Limitations:

- The snapshot was still changing near review time (`motion_director.py` is newer than the pipeline/tests). Findings are tied to the hashes above.
- No Git history was read; the `.git` file points outside the snapshot. Historical provenance below comes from in-snapshot timestamps, helper scripts and the dependency manifest.
- No pytest suite was executed. The two import probes used `python -B` with `PYTHONDONTWRITEBYTECODE=1` and made no writes.
- No original B3 or R6 source copy exists in the snapshot (`glob **/*pipeline*.py` finds only the current pipeline and test files; `archive/` has no pipeline copy). Claims about the pre-R6 assignment are therefore labelled INFERRED where they cannot be proven from the snapshot.

---

## 2. Executive finding

R6 fails for **independent, compounding reasons**, not one test bug:

1. The short pipeline cannot be imported at all: the preserved `motion_render.py` imports root modules that do not exist in the snapshot.
2. Even if imported, `run()` raises `NameError: claim_count` while building `metadata["evidence"]`.
3. The preserved renderer has no `evidence` parameter and returns no nested `evidence.cutout_selection`.
4. The pipeline never passes the claim ledger to the renderer.
5. The pipeline reads top-level `render["cutout_selection"]` and then `visuals["cutout_selection"]`, not the frozen nested expression, and omits the key instead of persisting `{}` on missing.
6. The three R6 tests do not execute the short pipeline; they call the long-form uploader, whose `main()` never calls the renderer, then assert against the fixture's pre-written metadata.
7. The tests mock a top-level `cutout_selection`, which is not the frozen shape.

The transferred `app/render/assembly.py` contains the correct nested contract, but it is not on the execution path.

---

## 3. Confirmed defects

### F-01 — Pipeline import blocker: preserved renderer imports missing root modules

**Classification: VERIFIED**

Evidence:

- `app/script/pipeline.py:22-23`:

```python
import motion_director
import motion_render
```

- `motion_render.py:26-27`:

```python
import visual_assets
import stock_fetcher
```

- Root files `visual_assets.py` and `stock_fetcher.py` do not exist (`ls` reports “No such file or directory”); the only copies are under `app/visuals/`.
- `app/render/assembly.py:30-32` correctly imports `from app.visuals import chain`, `motion_director`, `stock_fetcher`, but `motion_render.py` was preserved as the old 644-line monolith and does not re-export `app.render.assembly`.

Reproduction (read-only import probe):

```text
$ cd /tmp/nd_gov_005
$ PYTHONDONTWRITEBYTECODE=1 python -B -c 'import app.script.pipeline'
...
File "/tmp/nd_gov_005/app/script/pipeline.py", line 23, in <module>
    import motion_render
File "/tmp/nd_gov_005/motion_render.py", line 26, in <module>
    import visual_assets
ModuleNotFoundError: No module named 'visual_assets'
```

Provenance: `B3_DEPENDENCY_RECONCILIATION_MANIFEST.md:66` records `motion_render.py` as “PRESERVED (not overwritten)” with a hash different from the source. The manifest nevertheless claims the renderer path is satisfied at lines 157-166.

Impact: `app.script.pipeline` cannot load; the R6 path is dead before `run()`.

---

### F-02 — Undefined `claim_count` in evidence assembly

**Classification: VERIFIED (static name resolution)**

Evidence: `app/script/pipeline.py:343-349`:

```python
metadata["evidence"] = {
    "flags": [],
    "summary": {"claims": claim_count, "by_status": {"supported": claim_count}},
    "ledger_path": "research/claim_ledger.json",
    "ledger_sha256": "",
    "unmapped_factual": [],
}
```

`claim_count` is referenced twice and assigned nowhere in the module. `grep -n claim_count` returns only line 345. There is no global import or parameter named `claim_count`; the `run()` local scope has no such name. When line 345 executes, Python raises `NameError: name 'claim_count' is not defined` and no metadata is returned.

Provenance: no assignment exists in the snapshot. The R6 comment block at lines 334-337 replaced an earlier evidence block; whether the original B3 assigned `claim_count = len(research.get("claims") or [])` cannot be verified from the snapshot. That origin is **INFERRED**, but the undefined name in the current file is **VERIFIED**.

Impact: even after F-01 is repaired, `run()` cannot produce metadata, so R6 persistence cannot occur.

---

### F-03 — Renderer has no `evidence` contract and emits no `cutout_selection`

**Classification: VERIFIED**

Evidence: `motion_render.py:492-494`:

```python
def render_video(shots: list[dict], audio_path: Path, out_path: Path, *, work_dir: Path,
                 ass_path: Path | None = None, width: int = WIDTH, height: int = HEIGHT,
                 fps: int = FPS) -> dict:
```

There is no `evidence` parameter. The return at `motion_render.py:558-569` contains:

```python
return {
    "status": status,
    "path": str(out_path),
    ...
    "assets": assets,
    "credits": stock_fetcher.credit_lines(assets),
}
```

There is no `evidence` key and no `cutout_selection` key anywhere in the file (`grep` for `cutout|evidence` returns only these unrelated matches). The renderer therefore cannot satisfy the frozen R6 source contract.

By contrast, the transferred `app/render/assembly.py` has the required shape:

- Signature includes `evidence: dict | None = None` (`app/render/assembly.py:41-43`).
- When `evidence["ledger"]` exists, it computes `select_cutout_scenes` and stores `evidence["cutout_selection"] = selection` (`:79-108`).
- It returns `"cutout_selection": evidence.get("cutout_selection") or {}` nested under `"evidence"` (`:330-349`).

The correct implementation exists but is not used by the pipeline.

---

### F-04 — Pipeline reads the wrong source locations and keeps a prohibited `visuals` fallback

**Classification: VERIFIED**

Evidence: `app/script/pipeline.py:334-342`:

```python
# B3 R6: Pipeline persistence is a pass-through of renderer-emitted cutout_selection only.
...
# Trace renderer -> pipeline: check renderer result, then visuals (from assets).
cutout_selection = None
if isinstance(render, dict):
    cutout_selection = render.get("cutout_selection")
if cutout_selection is None:
    cutout_selection = visuals.get("cutout_selection")
```

Required frozen expression:

```python
cutout_selection = render.get("evidence", {}).get("cutout_selection", {})
```

The implementation reads:

1. top-level `render["cutout_selection"]`, which the renderer does not emit; then
2. `visuals["cutout_selection"]`, where `visuals` is `_describe_visuals(render.get("assets") or [], shots)` (`:289`), and `_describe_visuals` (`:177-210`) returns no `cutout_selection` key.

Both paths are always `None` for the real renderer. The `visuals` fallback also violates the “pass-through-only” and “no visuals source” contract: it could persist a non-renderer value if one ever appeared in the visuals dict.

---

### F-05 — Pipeline never passes the claim ledger to the renderer

**Classification: VERIFIED**

Evidence: `app/script/pipeline.py:270-273` and `:280-282`:

```python
render = motion_render.render_video(
    shots, audio_path, output_path, work_dir=shots_dir, ass_path=ass_path
)
```

No `evidence={"ledger": ...}` argument is passed. Even if `motion_render` were the correct shim to `app/render/assembly.py`, `assembly.render_video` would see `evidence.get("ledger")` as false and return `cutout_selection: {}` (`assembly.py:79-81`, `:347`).

The pipeline also does not import or build a claim ledger (`grep` for `claims_ledger|build_ledger|write_ledger` in `pipeline.py` returns nothing).

Impact: the renderer has no ledger from which to select cutouts; the real R6 selection can never be produced on this path.

---

### F-06 — Missing-key behavior omits the key instead of persisting `{}`

**Classification: VERIFIED (contract mismatch)**

Evidence: `app/script/pipeline.py:350-351`:

```python
if cutout_selection is not None:
    metadata["evidence"]["cutout_selection"] = cutout_selection
```

Frozen R6 requires `.get("cutout_selection", {})`, i.e. a missing key becomes `{}` and the persisted key is present. The current conditional omits the key when the value is `None`. That is the handoff’s “missing not synthesized” variant, not the frozen default.

Impact: even a repaired renderer/source path would produce the wrong serialization for missing selection.

---

### F-07 — Duplicate renderer and QA calls

**Classification: VERIFIED**

Evidence: `app/script/pipeline.py:270-286` contains the same block twice:

```python
render = motion_render.render_video(...)
qa = motion_render.qa_video(...)
step("render", {...})
_log(...)

source_urls = script.get("source_urls") or []
render = motion_render.render_video(...)   # second call
qa = motion_render.qa_video(...)           # second call
step("render", {...})                      # duplicate step
_log(...)
source_urls = script.get("source_urls") or []  # duplicate assignment
```

The first render result is discarded. This doubles render cost/latency and makes the evidence source ambiguous if the two calls differ.

---

### F-08 — No claim ledger is built or written; `ledger_sha256` is empty

**Classification: VERIFIED**

Evidence: `app/script/pipeline.py:346-347` writes:

```python
"ledger_path": "research/claim_ledger.json",
"ledger_sha256": "",
```

No `claim_ledger.json` exists anywhere in the snapshot (`glob **/claim_ledger.json` returns none). `publish_authorization._check_ledger_binding` (`publish_authorization.py:383-396`) raises `blocked_evidence` when the digest or path is empty, and would also block when the file is missing or digest-mismatched.

Impact: even if R6 persisted `cutout_selection`, the resulting metadata would fail evidence binding at authorization. This is a nearby production defect, not an R6-only test issue.

---

### F-09 — Evidence summary is synthesized as “all supported”

**Classification: VERIFIED (code); impact INFERRED**

Evidence: `app/script/pipeline.py:345`:

```python
"summary": {"claims": claim_count, "by_status": {"supported": claim_count}},
```

This asserts every claim is `supported` without consulting the ledger or claim verification statuses. It is the same synthetic pattern that B3 was meant to remove from rights evidence, but applied to claim status. It can cause `_evidence_violations` to pass when the actual research contains unsupported, outdated or conflicting claims.

The correct source is `ledger["summary"]` from `app.research.claims.summarize()` (`app/research/claims.py:435-469`), where `by_status` is counted from actual verification statuses. The pipeline currently does not build that ledger at all.

---

### F-10 — The three R6 tests do not test the short pipeline

**Classification: VERIFIED**

Evidence: `tests/test_publish_governance.py:253-337`:

- Each test patches `motion_render.render_video` with a return dict.
- Each test calls `code = longform.main([])`.
- Each test then reads `box.paths["metadata"]`.

`longform.main` (`app/publish/youtube_longform_upload.py:19-45`) does not call `motion_render.render_video`; it authorizes, reads metadata, and uploads. The `render_video` patch is dead code. The test never imports `app.script.pipeline`, never calls `pipeline.run`, and never exercises `_describe_visuals`, the evidence block, or `pipeline.main`.

Impact: the tests cannot detect F-01–F-09. They test the long-form uploader’s authorization path, not R6 persistence.

Historical provenance: the tests file mtime is 2026-11-02T00:43:50. `update_tests.py:10-44` contains the earlier metadata round-trip tests (`test_cutout_selection_serialization_*`) and `update_tests.py:49-133` replaces them with the long-form tests. `final_fix.py` and `remove_metadata_patches.py` document repeated removal of `patch.object(longform, "metadata_file", ...)`; `longform.py:25` defines `metadata_file` as a local variable, not a module attribute, so that patch was never valid. The dependency manifest is later (03:05) but does not correct the test target.

---

### F-11 — The tests mock the wrong `cutout_selection` shape

**Classification: VERIFIED**

Evidence: the mocked renderer returns top-level `cutout_selection` at `tests/test_publish_governance.py:273`, `:305`, `:332`:

```python
"<render dict>": {
    ...
    "cutout_selection": {"reason": "Renderer emitted", "budget": 42, ...},
}
```

The frozen contract is `render["evidence"]["cutout_selection"]`. The mock never nests it under `evidence`. This encodes the same top-level mistake as F-04; even if the test called the pipeline, it would validate the wrong source and could mask the defect.

---

### F-12 — The tests assert against fixture metadata, not pipeline output

**Classification: VERIFIED**

Evidence: `tests/test_publish_governance.py:278`, `:309`, `:336` read `box.paths["metadata"]`. The fixture writes that file before the test (`tests/governance_fixtures.py:168-177`) and gives every zero-cutout payload a default `cutout_selection`:

```python
cutout_selection = {
    "reason": "No visual cutouts requiring rights clearance; all content is original or procedural.",
    "budget": 0,
}
```

`longform.main` never rewrites this file. Therefore:

- Test 1 expects `{"reason":"Renderer emitted","budget":42,...}`; the file contains the fixture default → assertion mismatch.
- Test 2 expects `{}`; the file contains the fixture default → assertion mismatch.
- Test 3 expects the key absent; the file contains the fixture default → assertion mismatch.

The tests are not observing renderer output at all. Their pass/fail is a comparison of the test’s expectation against a fixture authored independently of the renderer.

Test 3 also contradicts the frozen missing-key default: frozen R6 says missing → `{}` key present, not key absent. This is a contract mismatch even if the test were moved to the pipeline.

---

### F-13 — Dependency manifest claim is contradicted by source

**Classification: REPORTED (manifest) / VERIFIED (contradiction)**

Evidence: `B3_DEPENDENCY_RECONCILIATION_MANIFEST.md:77` claims:

> “motion_render.py - Entry point `render_video()`, returns `cutout_selection` ✅ PRE-EXISTING”

Source verification: `motion_render.py:492-569` has no `cutout_selection`, no `evidence` parameter and no `evidence` return key. The manifest also claims at lines 157-166 that the “minimum renderer dependency closure” is satisfied, while the read-only import probe fails at `motion_render.py:26`.

The manifest correctly records that `motion_render.py` was preserved with a different hash from the source (`:66`, `:121`), but then treats that preserved file as R6-capable. It is not.

---

### F-14 — The transferred renderer assembly is correct but unwired

**Classification: VERIFIED**

Evidence: `app/render/assembly.py` has the required `evidence` parameter (`:41-43`), computes `cutout_selection` (`:79-108`), and returns it nested (`:330-349`). Its hash matches the dependency manifest (`79f0bc…`).

However, `app/script/pipeline.py` imports root `motion_render`, not `app.render.assembly`; the root `motion_render` is the old monolith. The dependency transfer reached the filesystem but not the execution path.

---

### F-15 — Partial dependency repair: `motion_director` is shimmed, `motion_render` is not

**Classification: VERIFIED**

Evidence: `motion_director.py:1-6` is a compatibility shim:

```python
"""Backward-compatible shim: real module lives in app/visuals/motion_director.py."""
import sys
from app.visuals import motion_director as _module
sys.modules[__name__] = _module
```

No equivalent shim exists for `motion_render`; it remains the 644-line monolith that imports missing root `visual_assets` and `stock_fetcher`. The repair is incomplete.

---

## 4. Potential defects

| ID | Finding | Classification | Why it matters |
|---|---|---|---|
| P-01 | `pipeline.main()` writes metadata without a `governance` stamp | INFERRED | If used as a publishable entry, `authorize_publish` blocks `blocked_governance`; may be intentional draft-only, but the R6 path does not state it |
| P-02 | `claim_count` semantics unresolved: research claims vs ledger summary | INFERRED | `research["claims"]` is deduplicated/capped at 14 (`app/research/desk.py:707-731,831`); `ledger.summary["claims"]` can be smaller after `bind_script` (`app/research/claims.py:395-398,435-469`). A local `claim_count` may not match either |
| P-03 | Non-empty `cutout_selection` with zero rendered cards | INFERRED | `assembly.select_cutout_scenes` can select scenes while `build_source_card` fails to render; `cutouts` stays empty but `cutout_selection` has `selected`. The pipeline persists selection without cutouts; downstream R4/R5 interpretation is ambiguous |
| P-04 | `render_video` duplicate call can produce different assets/selection | INFERRED | Two renders with the same inputs may still differ in asset resolution; the second result wins, but the first is billed in time |
| P-05 | Global `sys.modules["motion_render"]` mock contaminates the test session | VERIFIED (test hygiene) | `tests/test_publish_governance.py:31-35` replaces the module before other tests import it; a real pipeline import would receive the mock, not the renderer |
| P-06 | `test_pipeline.py` and `test_r1_r6.py` are print-only, not assertion tests | VERIFIED | They can execute code but cannot fail the suite; `test_r1_r6.py` does not rebind approval hashes and would be masked by governance/approval |

---

## 5. Contract mismatches

| ID | Frozen R6 contract | Current implementation |
|---|---|---|
| C-01 | `render.get("evidence", {}).get("cutout_selection", {})` | top-level `render.get("cutout_selection")`, then `visuals.get(...)` (`pipeline.py:338-342`) |
| C-02 | Missing key → `{}`, key present | conditional omission (`pipeline.py:350-351`) |
| C-03 | Renderer accepts `evidence` and returns nested `evidence.cutout_selection` | root `motion_render.render_video` has no `evidence` parameter and no nested return (`motion_render.py:492-569`) |
| C-04 | Pipeline passes the claim ledger to the renderer | no `evidence` argument (`pipeline.py:271-273`, `:280-282`) |
| C-05 | Tests exercise the short pipeline | tests call `longform.main` (`tests:253-337`) |
| C-06 | Test mock uses nested `render["evidence"]["cutout_selection"]` | mock uses top-level `cutout_selection` (`tests:273,305,332`) |
| C-07 | Missing-key test expects `{}` | test 3 expects key absent (`tests:337`) |
| C-08 | Evidence summary reflects ledger statuses | hardcoded all-supported (`pipeline.py:345`) |
| C-09 | Claim ledger bound by path/digest | `ledger_sha256: ""`, no ledger file (`pipeline.py:346-347`) |

---

## 6. Test coverage gaps

1. **No import/smoke test** for `app.script.pipeline`; F-01 would be caught immediately.
2. **No short-pipeline execution test**; the three R6 tests call the long-form uploader.
3. **No assertion that `motion_render.render_video` was called**, no call-argument assertion for `evidence`, and no assertion that the ledger was passed.
4. **No nested-shape test**: no mock or fixture sets `render["evidence"]["cutout_selection"]`.
5. **No missing-key default test** for `{}`; the existing test asserts the opposite.
6. **No ledger test**: no `claim_ledger.json` is written, and no test checks `ledger_sha256`.
7. **No real renderer integration test**; no test invokes `app.render.assembly.render_video` or the compatible shim.
8. **No claim-count/summary test**; `claim_count` is undefined and the summary is synthetic.
9. **No end-to-end JSON rewrite test**; tests read the fixture’s pre-written metadata.
10. **Stale/manual artifacts**: `test_r1_r6.py` prints PASS/FAIL without assertions; `new_tests.py` is a fragment; `test_pipeline.py` only prints. None gates R6.

---

## 7. Minimal proposed corrections

These are proposed corrections for a separately authorized implementation; no code was changed.

1. **Restore the renderer entrypoint contract**: replace root `motion_render.py` with the compatibility shim to `app.render.assembly.render_video` (as in the production `motion_render.py` shim), or update the monolith to accept `evidence` and return the nested `evidence` block. The former is smaller and matches the transferred assembly.
2. **Pass the ledger**: in `app/script/pipeline.py`, build/write the claim ledger from `research` and the script, then call `render_video(..., evidence={"ledger": ledger, "script_sha256": ..., "ledger_sha256": ...})`.
3. **Fix `claim_count`**: define it from the ledger summary (`ledger["summary"]["claims"]`) or, if the summary remains research-based, from `len(research.get("claims") or [])`; do not leave an undefined name. Prefer ledger-derived `by_status` over the hardcoded all-supported map.
4. **Remove the duplicate render/QA block**: one `render_video` call, one `qa_video`, one `step("render")`.
5. **Use the exact frozen expression**: `cutout_selection = render.get("evidence", {}).get("cutout_selection", {})`; delete the top-level and `visuals` fallbacks; always persist the key so missing becomes `{}`.
6. **Bind the ledger**: write `research/claim_ledger.json`, set `ledger_path` to the real path and `ledger_sha256` to its digest; otherwise `authorize_publish` blocks.
7. **Rewrite the R6 tests**: target `app.script.pipeline.run` or `pipelines.short.run_strong_pipeline`; mock `motion_render.render_video` with a nested `{"evidence": {"cutout_selection": ...}}`; assert the renderer was called with a ledger; assert the persisted metadata/JSON; include non-empty, `{}`, missing→`{}` and nested-shape cases.
8. **Remove the global `sys.modules["motion_render"]` mock**; patch the pipeline’s renderer symbol with `unittest.mock.patch.object`.
9. **Retire the long-form R6 tests** or relabel them as long-form authorization tests; they cannot cover short-pipeline persistence.

---

## 8. Remaining questions requiring owner decisions

| ID | Question | Why it cannot be inferred |
|---|---|---|
| Q-01 | Is the authoritative R6 baseline the snapshot’s 388-line pipeline or the production 540-line pipeline with ledger integration? | The snapshot pipeline has no ledger build/evidence block; the frozen spec cites `pipeline.py:453-464`, not `:343-351` |
| Q-02 | Is claim-ledger construction part of R6 scope, or a prerequisite owned by another change? | Without a ledger the renderer cannot emit a real selection |
| Q-03 | Should missing renderer selection persist `{}` or omit the key? | Frozen says `{}`; the R6 handoff says absent; snapshot omits |
| Q-04 | Should `claim_count` count research claims or ledger claims after `bind_script`? | The two counts differ; no accepted definition in the snapshot |
| Q-05 | Is `app/render/assembly.py` the intended renderer, and may root `motion_render.py` be replaced by its shim? | Dependency transfer added the former but preserved the latter |
| Q-06 | Should the three R6 tests be rewritten or retired? | Test edits require explicit authorization; current tests are misleading green/red signals |
| Q-07 | Should `pipeline.main()` stamp governance, or is it intentionally draft-only? | It affects whether pipeline output can be authorized at all |
| Q-08 | Should `app.render.assembly` card-render failure be treated as zero cutouts or as an evidence failure? | Affects R4/R5 interaction when selection is non-empty but `cutouts` is empty |

---

## 9. Status

**R6 IS NOT ACCEPTED.**

The current implementation does not satisfy the frozen R6 contract. The short pipeline cannot import, `claim_count` is undefined, the preserved renderer has no `evidence`/`cutout_selection` contract, the pipeline reads the wrong keys and never passes the ledger, the missing-key default is wrong, and the three R6 tests do not execute the short pipeline or use the nested shape. The transferred `app/render/assembly.py` contains the correct nested contract but is not wired into the execution path.

No production, test, fixture, repository or shared-checkout changes were made.
