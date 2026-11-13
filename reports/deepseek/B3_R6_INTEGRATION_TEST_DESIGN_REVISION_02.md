# B3 R6 Integration Test Design — Revision 02

**Document ID:** ND-GOV-005-B3-DEEPSEEK-TEST-DESIGN-REVISION-02  
**Supersedes:** `reports/deepseek/B3_R6_INTEGRATION_TEST_DESIGN.md` (Revision 01)  
**Status:** TEST DESIGN ONLY — no tests implemented, no tests executed, no publishing, no integration, no acceptance claimed.  
**Scope:** Mandatory R6 acceptance for the frozen nested renderer expression, plus an explicitly optional R1–R5 regression matrix.  
**Mode:** read-only. No source or test files were modified in producing this design.

---

## 0. Revision 02 corrections

| # | Required correction | Where applied |
|---|---|---|
| 1 | Separate mandatory R6 acceptance from optional R1–R5 regression | §4 (mandatory) and §5 (optional) are separate matrices; no R1–R5 case is mandatory |
| 2 | Frozen nested renderer expression is the only R6 source contract | §2; MP-02 is the source-discrimination test; no `visuals` or research fallback in mandatory cases |
| 3 | Preserve missing-key default `{}` | MP-04; §9 |
| 4 | Preserve null and malformed-value behavior; do not silently normalize | MP-05 and MP-06; §2.3 and §9 |
| 5 | Do not impose a non-negative budget constraint | MP-10; explicit prohibition in §2.3; no `budget >= 0` assertion anywhere |
| 6 | Full publishing authorization is not a mandatory R6 acceptance requirement | Not present in §4; only optional REG-04/REG-10 in §5, owner authorization required |
| 7 | Distinguish renderer generation, mocked pipeline pass-through and real end-to-end persistence | §3 layer definitions; RG, MP and E2E rows in §4 |
| 8 | Identify the minimum dependency closure for E1/E2 | §7 |
| 9 | Distinguish existing known defects from new R6 regressions | §6 |
| 10 | Identify tests requiring additional owner authorization | §8, with per-row markers in §4 and §5 |

---

## 1. Authority and scope

### 1.1 Frozen oracle

The only R6 source contract is the frozen expression:

```python
"cutout_selection": render.get("evidence", {}).get("cutout_selection", {})
```

from `ND_GOV_005_B3_REMEDIATION_SPEC_FINAL_2026-10-31.md`, R6. The renderer already emits the nested key (`app/render/assembly.py:104-106`, `:330-349`); R6 is persistence only.

The owner decision behind the zero-cutout proof is `ND_GOV_004_ZERO_CUTOUT_RIGHTS_INVESTIGATION_2026-10-31.md` §6, but R6 acceptance is limited to persistence of the renderer's value. Whether the persisted value authorizes publication is an R1–R5/authorization question and is optional regression coverage here.

### 1.2 Dependency reconciliation

No mounted file is literally titled “Copilot dependency reconciliation report.” The dependency findings used here come from:

- `ND_GOV_005_B3_DOC_RECON_01_2026-11-02.md` — source inventory, hash-authority conflict, R6 blocked on an incomplete baseline.
- `ND_GOV_005_B3_CODEX_R6_VERIFY_03_2026-11-02.md` — actual renderer return structure, missing modules in `/tmp/nd_gov_005`, tests that do not invoke the pipeline, named coverage gaps.

If the owner holds a separate Copilot dependency report, its dependency table replaces §7; the mandatory cases do not change.

### 1.3 What this revision does not do

- It does not implement tests.
- It does not execute tests.
- It does not authorize publishing, integration, commits or merges.
- It does not change R1–R5 semantics, the renderer, or the frozen expression.
- It does not turn optional regression or full authorization into acceptance gates.

---

## 2. The only R6 source contract

### 2.1 Contract table

For every row, the persisted location is `metadata["evidence"]["cutout_selection"]` (JSON: `evidence.cutout_selection`). The expression is evaluated against the renderer's return value `render`.

| Renderer state | Frozen expression result | Persisted value | Normalization permitted? |
|---|---|---|---|
| `render = {"evidence": {"cutout_selection": S}}`, `S` non-empty dict | `S` | `S` exactly | No |
| `render = {"evidence": {"cutout_selection": {}}}` | `{}` | `{}`, key present | No |
| `render = {"evidence": {}}` | `{}` | `{}`, key present | No |
| `render = {}` | `{}` | `{}`, key present | No |
| `render = {"assets": [...]}` (no `evidence`) | `{}` | `{}`, key present | No |
| `render = {"evidence": {"cutout_selection": None}}` | `None` | `null`, key present | No — must not become `{}` |
| `render = {"evidence": {"cutout_selection": []}}` | `[]` | `[]` | No — must not become `{}` or a dict |
| `render = {"evidence": {"cutout_selection": "x"}}` | `"x"` | `"x"` | No |
| `render = {"evidence": {"cutout_selection": 5}}` | `5` | `5` | No |
| `render = {"evidence": {"cutout_selection": true}}` | `true` | `true` | No |
| `render = {"evidence": {"cutout_selection": S}}`, `S["budget"] = -1` | `S` | `S` with `-1` | No — no non-negative constraint |
| `render = {"evidence": {"cutout_selection": S}}`, `S` has extra/unicode keys | `S` | `S` exactly | No |

### 2.2 What is not a source

The following are **not** R6 sources and must not appear in mandatory acceptance:

- `render["cutout_selection"]` at top level.
- `visuals["cutout_selection"]` from `_describe_visuals(...)`.
- `research["cutout_selection"]`.
- A pipeline-constructed selection, reason, budget, or `publish_ready`.
- Any value synthesized from `render["assets"]`, provider names, or licensing guesses.

MP-02 is the mandatory source-discrimination test: a decoy in `visuals` must lose to the nested renderer value.

### 2.3 Normalization prohibitions

Mandatory R6 acceptance must not silently:

- replace missing/`None` with a synthesized reason or budget;
- turn `None`, a list, a string, a number or a boolean into `{}`;
- turn `{}` into a selector-shaped dict;
- add keys (`selected`, `budget`, `reason`, `publish_ready`) to a malformed or empty value;
- coerce `budget` to an integer or enforce `budget >= 0`;
- reorder `selected`, deduplicate, or filter entries;
- drop extra/unknown keys;
- coerce `reuse_rights`, `status`, or any nested renderer value.

The pipeline may only persist the value returned by the frozen expression. If the owner wants a stricter failure mode for malformed values, that is a separate decision (§8, O-01).

### 2.4 Malformed `render["evidence"]` container

If `render["evidence"]` is `None`, a string, or a list, the frozen expression raises (`AttributeError`) rather than returning `{}`. The frozen specification does not define a substitute behavior. This is **not** a mandatory acceptance case; it is owner decision O-01. The design forbids silently normalizing it to `{}` without that decision.

---

## 3. Layers

| Layer | Definition | Renderer | Pipeline | JSON | Mandatory? |
|---|---|---|---|---|---|
| RG | Renderer generation: call the real `motion_render.render_video` directly; no pipeline | Real | No | No | Precondition, not standalone acceptance |
| MP | Mocked pipeline pass-through: real `pipeline.run`/`main`, stubbed renderer and boundary calls | Stubbed | Real | Optional (`main`) | Yes |
| E2E | Real end-to-end persistence: real renderer through real pipeline to metadata/JSON | Real | Real | Real | Yes, conditional on §7 |
| REG | Optional R1–R5 regression | Per case | Per case | Per case | **No** |

Supporting unit checks (selector shape, JSON round-trip) are preconditions, not an acceptance layer; they may be implemented as ordinary unit tests but they do not gate R6 acceptance on their own.

Rules:

- RG must not call the pipeline.
- MP must not call the real renderer.
- E2E must call the real renderer through the real pipeline; only external boundaries are doubled.
- REG is optional and must never be reported as mandatory R6 acceptance.

---

## 4. Mandatory R6 acceptance matrix

The acceptance matrix contains only MP (mocked pipeline pass-through) and E2E (real end-to-end persistence) rows. `authorize_publish`, `_rights_violations`, `cutouts`, `rights_gate`, and all R1–R5 cases are excluded. Renderer-generation checks are preconditions in §4.1, not standalone acceptance claims: the renderer emitting the nested key is existing behavior, while R6 is the persistence change.

| ID | Layer | Frozen clause | Scenario | Assertion | Expected | Key dependencies | Owner auth |
|---|---|---|---|---|---|---|---|
| MP-01 | MP | Persist nested value | Stub renderer returns nested non-empty `S`; call `pipeline.run` | `metadata["evidence"]["cutout_selection"] == S` exactly | Pass | Pipeline + stubs | No |
| MP-02 | MP | Only nested expression | Stub renderer returns `S`; `_describe_visuals` returns a decoy `D` | Persisted value is `S`; `D` never appears | Pass | Pipeline, patched `_describe_visuals` | No |
| MP-03 | MP | Preserve `{}` | Stub renderer returns `{"evidence": {"cutout_selection": {}}}` | Key present; value `{}`; no synthesized keys | Pass | Pipeline + stub | No |
| MP-04 | MP | Missing-key default `{}` | Four states: `{"evidence": {}}`, `{}`, `{"assets": []}`, `{"evidence": {"cutouts": []}}` | Each persists `{}` and the key is present | Pass | Pipeline + stub | No |
| MP-05 | MP | Preserve null | Stub returns `{"evidence": {"cutout_selection": None}}` | Persisted value is `None`; key present; not `{}` | Pass | Pipeline + stub | No |
| MP-06 | MP | Preserve malformed value | Stub returns `[]`, `"x"`, `5`, `true` in turn | Persisted value is identical to the stub value; no wrapping, no `{}` substitution | Pass | Pipeline + stub | No |
| MP-07 | MP | No research fallback | Renderer has no selection key; `research["cutout_selection"] = D` | Persisted value is `{}`, never `D` | Pass | Pipeline, research stub | No |
| MP-08 | MP | No mutation | Deep-copy renderer evidence before `run` | Renderer evidence unchanged; persisted value equals the snapshot | Pass | Pipeline + stub, `deepcopy` | No |
| MP-09 | MP | No synthesis when silent | Renderer has no selection key; no cutouts/rights gate | No synthesized selection, reason, budget or `publish_ready` is added | Pass | Pipeline + stub | No |
| MP-10 | MP | No non-negative budget constraint | Stub selection `{"selected": [], "budget": -1, "reason": "x"}` | Persisted `budget == -1`; no test asserts `budget >= 0` | Pass | Pipeline + stub | No |
| MP-11 | MP | Exact equality | Stub selection with extra keys, unicode reason, nested list | Persisted value equals the stub exactly; key order is not asserted, key set is | Pass | Pipeline + stub | No |
| MP-12 | MP | JSON persistence | Stub as MP-01; call `pipeline.main(["--out", path])` | JSON `evidence.cutout_selection == S` exactly after parse | Pass | Pipeline `main`, temp path | No |
| E2E-01 | E2E | Nested → metadata | Real renderer through real `pipeline.run` with §7 closure | `metadata["evidence"]["cutout_selection"] == render["evidence"]["cutout_selection"]` exactly | Pass, conditional on §7 | Real renderer + pipeline + closure | O-04, O-07 |
| E2E-02 | E2E | Nested → JSON | Real renderer through real `pipeline.main --out` | Persisted JSON selection equals the captured renderer selection; canonical JSON equality | Pass, conditional on §7 | Real renderer + pipeline + closure | O-04, O-07 |

### 4.1 Renderer-generation preconditions (not standalone acceptance)

These checks establish that the real renderer emits the nested value that E2E-01/E2E-02 consume. They are preconditions, not R6 acceptance claims in their own right.

| ID | Layer | Scenario | Assertion | Expected | Key dependencies | Owner auth |
|---|---|---|---|---|---|---|
| RG-01 | RG | Real renderer with a ledger containing a cutout-worthy `supported` claim | `render["evidence"]["cutout_selection"]` is a non-empty dict with `selected`, `budget`, `reason`; `budget` is int; `selected` entries are JSON-native | Holds | Real renderer, ledger, shots, audio, ffmpeg | O-07 |
| RG-02 | RG | Real renderer with no ledger | `render["evidence"]["cutout_selection"] == {}`; key present | Holds | Real renderer, shots, audio, ffmpeg | O-07 |
| RG-03 | RG | Real renderer with a one-scene ledger containing no cutout-worthy claim | Selector-shaped empty dict: `selected == []`, `budget == 1`, `reason == "no claim worth a cutout"` | Holds | Real renderer, ledger variant | O-07 |
| RG-04 | RG | Nested, not top-level/visuals | Key is in `render["evidence"]`; absent at `render` top level; absent from `_describe_visuals(render["assets"], shots)` | Holds | RG-01 output, `_describe_visuals` | O-07 |

### 4.2 Critical mandatory cases — detail

#### MP-02 — source discrimination

- Patch `pipeline._describe_visuals` to return a valid visuals dict plus `"cutout_selection": DECOY`.
- Stub `motion_render.render_video` to return `{"assets": [], "evidence": {"cutout_selection": S}}`, where `S` and `DECOY` differ in `reason`, `budget` and `selected`.
- Call `pipeline.run(...)`.
- Assert `metadata["evidence"]["cutout_selection"] == S` and `!= DECOY`.
- This is the only mandatory test that proves the frozen source; without it, a `visuals`-based implementation could pass the other MP cases.

#### MP-04 — missing-key default `{}`

- Four independent subtests, each a fresh sandbox:
  1. `render = {"evidence": {}}`.
  2. `render = {}`.
  3. `render = {"assets": []}`.
  4. `render = {"evidence": {"cutouts": [], "rights_gate": {}}}`.
- Assert for each: `"cutout_selection" in metadata["evidence"]` and value `== {}`.
- Do not assert key absence; that is the handoff variant, owner decision O-02.

#### MP-05 — null preservation

- `render = {"evidence": {"cutout_selection": None}}`.
- Assert key present and value `is None`; assert `metadata["evidence"]["cutout_selection"] is not {}` and is not replaced by a selector-shaped dict.
- Downstream rights behavior is optional REG-02, not R6 acceptance.

#### MP-06 — malformed value preservation

- Loop `[]`, `"x"`, `5`, `True`.
- Assert persisted value equals the input exactly (type and value); key present.
- Do not assert `{}` substitution, dict wrapping, or a synthesized reason.

#### MP-10 — negative integer budget

- `render = {"evidence": {"cutout_selection": {"selected": [], "budget": -1, "reason": "negative"}}}`.
- Assert persisted value equals the input, including `budget == -1`.
- No mandatory test may assert `budget >= 0`, `budget > 0`, or a non-negative constraint. Negative budget acceptance at the authorization layer is optional REG-05.

#### E2E-01 / E2E-02 — real end-to-end persistence

- Use the §7 minimum closure; the real renderer is invoked with a ledger; the pipeline is real; only external boundaries are doubled.
- Capture the real renderer return with `unittest.mock.patch.object(..., wraps=...)`.
- E2E-01 asserts exact metadata equality; E2E-02 asserts exact JSON equality after `main --out`.
- These are mandatory only when the §7 closure is ratified; a missing module or binary blocks acceptance and must not be reported as a pass.

---

## 5. Optional R1–R5 regression matrix

These cases are **not** R6 acceptance. They exist to detect a new R6-caused change in R1–R5 behavior. They may be run selectively and must be reported separately.

| ID | Area | Scenario | Assertion | Expected | Owner auth |
|---|---|---|---|---|---|
| REG-01 | R1–R5 suite | Existing `RightsAndEvidenceTests` and the adversarial R1–R5 suite | Result counts match the pre-R6 baseline; known defects remain known | Informational | No |
| REG-02 | R1–R5 rules | `_rights_violations` on persisted metadata: `{}`, selector-empty, permitted card, unknown card, bool count, negative budget | Outcomes match the frozen R1–R5 oracle | Informational | No |
| REG-03 | Pass-through | `cutouts` and `rights_gate` from renderer | Persisted values equal renderer values; no synthesis | Informational | No |
| REG-04 | Authorization | Zero-cutout persisted artifact with selector proof; full `authorize_publish` | Authorized; missing proof blocked | Optional | O-03 |
| REG-05 | R5 budget | Negative integer budget at the rights layer | Accepted under frozen R5 (no non-negative constraint) | Optional | O-06 |
| REG-06 | Known defect R4 | 21/25 violations | Current cap behavior remains (21 entries; 25 total lost) | Expected failure; not R6 | No |
| REG-07 | Known defect R5 | Non-string `reason` | Current acceptance remains | Expected failure; not R6 | O-06 |
| REG-08 | Known test defect | Existing R6 longform tests | `FileNotFoundError` remains; not R6 | Informational | No |
| REG-09 | Handoff variant | Missing key with key absent | Characterization only; conflicts with frozen `{}` | Not acceptance | O-02 |
| REG-10 | Full E2E authorization | Real persisted artifact through governance/approval/window | Codes match policy | Optional | O-03 |

### 5.1 Optional regression rules

- Do not include these cases in the mandatory acceptance matrix or in the R6 pass/fail verdict.
- Do not relabel a known defect as an R6 regression without showing it is absent from the pre-R6 baseline.
- REG-04 and REG-10 require owner authorization because they assert publishing authorization, which is outside mandatory R6 acceptance.
- REG-05 and REG-07 require the owner’s R5 `(str)`/budget-intent decision (O-06) before being used as pass/fail.

---

## 6. Existing known defects versus new R6 regressions

### 6.1 Known defects (not introduced by R6)

| ID | Known defect | Status / source | R6 regression? |
|---|---|---|---|
| KD-01 | The incomplete `/tmp/nd_gov_005` pipeline reads `visuals.get("cutout_selection")` and never persists the renderer value | Documented in `ND_GOV_005_B3_CODEX_R6_VERIFY_03`; baseline implementation defect | No — it is the pre-R6 baseline defect R6 is meant to correct |
| KD-02 | R4 violation list is 21 entries after the 20-cap; a 25-violation case reports 21 | Prior adversarial QA; existing R4 defect | No |
| KD-03 | R5 accepts non-string `reason` values (`1`, `true`, list, dict) | Prior adversarial QA under the frozen `(str)` reading; owner interpretation pending | No |
| KD-04 | Existing R6 longform tests fail with `FileNotFoundError` on `data/longform_metadata.json` | Existing test/snapshot defect | No |
| KD-05 | The worktree lacks `app/render/`, `app/visuals/cutouts.py`, `app/visuals/storyboard.py`, `motion_director.py` | Dependency gap documented in DOC-RECON-01 | No — blocked environment, not a code regression |

### 6.2 New R6 regression definition

A **new R6 regression** is any of the following, relative to the pre-R6 baseline:

1. The persisted value differs from `render.get("evidence", {}).get("cutout_selection", {})`.
2. A missing key no longer yields `{}`.
3. `None` or a malformed selection value is normalized.
4. `budget` is coerced or constrained to non-negative.
5. The pipeline reads `visuals`, research, or a top-level key instead of the nested expression.
6. The pipeline mutates the renderer's evidence.
7. `cutouts`/`rights_gate` pass-through changes (optional REG-03).
8. R1–R5 outcomes change (optional REG-02/REG-04).

Comparison method: run the optional REG matrix against the pre-R6 parent (frozen expression reverted) and the R6 tree; any difference attributable to the R6 line is a new regression. Known defects in KD-01–KD-05 are excluded from that comparison by name.

---

## 7. E1/E2 minimum dependency closure

E1/E2 (E2E-01/E2E-02) must execute the real renderer and the real pipeline. The minimum closure below is the smallest set that can do so; everything else is doubled.

### 7.1 Modules that must execute for real

| Module | Role | Why it cannot be stubbed for E1/E2 |
|---|---|---|
| `app/script/pipeline.py` | Pipeline under test | Contains the persistence block |
| `motion_render.py` | Compatibility shim | Production renderer entrypoint |
| `app/render/assembly.py` | Renderer | Emits nested `evidence.cutout_selection` |
| `app/render/ffmpeg_tools.py` | FFmpeg/ffprobe helpers | Real render and duration probe |
| `app/render/shots.py` | Shot renderer | Real render path |
| `app/visuals/chain.py` | Scene/asset plan | Renderer calls `plan_scenes` |
| `app/visuals/motion_director.py` | Motion planning | Imported and used by the renderer |
| `app/visuals/stock_fetcher.py` | Asset metadata | Imported by renderer; network calls must be doubled |
| `app/visuals/cutouts.py` | Cutout selector and cards | Produces the real `cutout_selection` |
| `app/research/claims.py` | Claim ledger | `claims_for_scene` drives selection |
| `app/research/lineage.py` | Claim lineage | Imported by `claims.py` |

### 7.2 Modules that need only be importable (calls doubled)

| Module | Why import-only |
|---|---|
| `app/visuals/shotplan.py`, `app/visuals/beats.py` | Pipeline imports them; `plan_shot_plan`/`annotate_shots`/`write_shot_plan` are stubbed with golden shots |
| `app/script/studio.py` | `write_script` is stubbed |
| `app/voice/provider.py` | `generate_voice` is stubbed; audio is a fixture |
| `app/research/desk.py`, `app/research/selector.py`, `app/research/topics.py` | Research/topic selection are stubbed |

### 7.3 Optional modules

| Module | Condition |
|---|---|
| `app/visuals/storyboard.py` | Only if `STORYBOARD_GATE` is not `off`/`skip`. For the minimum closure set `STORYBOARD_GATE=off`; if the test must exercise the default gate, add this module and an approved storyboard fixture |
| `app/render/audio_diagnostics.py` | Optional; the renderer's import is guarded and its failure is tolerated |

### 7.4 Not needed for E1/E2

`publish_authorization.py`, `approval_integrity.py`, `visual_quality.py`, `tests/governance_fixtures.py`, `fastapi`, `publish_all.py`, API routes, and all publisher adapters. These belong to optional REG-04/REG-10, not mandatory R6 persistence.

### 7.5 Non-module closure

- `ffmpeg` and `ffprobe` on PATH.
- A 2–3 s synthetic audio file.
- Golden `shots.json` and `ledger.json` with one cutout-worthy claim (and one non-cutout variant).
- `STORYBOARD_GATE=off`, `DRY_RUN=0`; no network.
- Writable `tmp_path` for work dir, output, and `--out`.

**Minimum closure statement:** E1/E2 require the 11 real modules in §7.1, importability of the five modules in §7.2, ffmpeg/ffprobe, and the golden shots/ledger/audio fixtures. No other production module is on the mandatory path.

---

## 8. Tests requiring additional owner authorization

| ID | Test / issue | Why owner authorization is required |
|---|---|---|
| O-01 | Asserting a defined behavior for malformed `render["evidence"]` (`None`/string/list) | The frozen expression raises; the spec does not define a substitute. Any `{}` fallback or fail-closed assertion is a new contract |
| O-02 | Accepting the handoff’s absent-key variant as an oracle | Conflicts with frozen missing-key default `{}`; only the owner can choose |
| O-03 | Full `authorize_publish` E2E (REG-04/REG-10) | Publishing authorization is outside mandatory R6 acceptance; owner authorization required to run it as a gate |
| O-04 | Ratifying the baseline and hash authority for E2E | DOC-RECON-01 records conflicting hashes and an incomplete worktree; the owner must choose the authoritative snapshot |
| O-05 | Any test that requires a production seam, helper extraction, or test-only source change | Test design assumes no source changes; a seam is an implementation decision |
| O-06 | R5 `reason` `(str)` and budget-intent interpretation | Frozen text says `(str)` and “integer”; whether non-string blocks and whether negative budget is acceptable at the rights layer is an owner decision (R6 itself imposes no non-negative constraint) |
| O-07 | Making real renderer/ffmpeg execution a mandatory acceptance requirement | The test environment must be authorized to run a real FFmpeg render and to treat a missing binary as blocked, not passed |
| O-08 | Assembling a baseline from untracked modules | The worktree lacks `app/render/`, `app/visuals/cutouts.py`, `motion_director.py`; using the shared/complete baseline must be owner-ratified |

Mandatory matrix rows marked O-04/O-07 are conditional on those decisions; they are not silently assumed.

---

## 9. Equality and assertion rules

`assert_selection_exact(original, persisted)`:

1. Both are present at `metadata["evidence"]["cutout_selection"]`.
2. Exact key sets; no added or dropped keys.
3. Exact recursive value equality.
4. `None` remains `None`; `False` remains `False`; `0` remains `0`.
5. Lists preserve order; no deduplication.
6. Types are preserved: `int` stays `int`, `bool` stays `bool`, `str` stays `str`.
7. Canonical JSON equality: `json.loads(json.dumps(original, sort_keys=True)) == json.loads(json.dumps(persisted, sort_keys=True))`.
8. No non-negative budget assertion is permitted anywhere.
9. No full authorization assertion is permitted in the mandatory matrix.

Special cases:

| Value | Expected persisted |
|---|---|
| Non-empty `S` | `S` exactly |
| `{}` | `{}` |
| Missing key | `{}` |
| `None` | `null` |
| `[]` / `"x"` / `5` / `true` | identical value |
| `budget: -1` | `-1` |
| Extra/unicode keys | preserved |
| `render["evidence"]` is `None`/string/list | not mandatory; O-01 |

---

## 10. Fixtures

| Fixture | Shape | Used by |
|---|---|---|
| `golden_shots.json` | 2–3 shots with index/start/end/duration/narration | RG, E2E |
| `golden_ledger_cutout.json` | One `supported` `statistic` claim matching shot narration | RG-01, E2E |
| `golden_ledger_no_cutout.json` | One `supported` non-cutout claim | RG-03 |
| `silent_2s.wav` | Synthetic audio generated in a session fixture | RG, E2E |
| `render_stub(selection)` | Controlled render dict | MP |
| `pipeline_stubs()` | Patches for §7.2 boundaries | MP, E2E |
| `assert_selection_exact` | §9 helper | MP, E2E |
| `capture_real_render()` | `patch.object(..., wraps=...)` | E2E |

All paths are `tmp_path`; no live `data/` or `outputs/`.

---

## 11. Expected results and blockers

| Layer | Expected on ratified complete baseline | Expected on incomplete `/tmp/nd_gov_005` |
|---|---|---|
| RG | Pass with ffmpeg + golden ledger | Blocked (missing `app/render/`, `cutouts.py`, `motion_director.py`) |
| MP | Pass on the R6 implementation | Fails on KD-01 (`visuals` source); import may fail first |
| E2E | Pass with §7 closure | Blocked |
| REG | Informational; known defects remain KD-02/KD-03/KD-04 | Informational |

A blocked layer is a dependency failure, not a pass. Known defects KD-01–KD-05 must not be counted as new R6 regressions.

---

## 12. Traceability

| Frozen R6 element | Mandatory cases |
|---|---|
| `render.get("evidence", {})` | MP-02, RG-04, E2E-01 |
| `.get("cutout_selection", {})` | MP-04, MP-05, MP-06 |
| Persist under `metadata["evidence"]` | MP-01, MP-12, E2E-01, E2E-02 |
| Renderer emits nested key | RG-01, RG-02, RG-03 |
| No logic change | MP-09 |
| Non-empty preservation | MP-01, RG-01, E2E-01 |
| Empty `{}` | MP-03 |
| Missing → `{}` | MP-04 |
| Null | MP-05 |
| Malformed value | MP-06 |
| No non-negative budget | MP-10 |
| Exact equality | MP-01, MP-08, MP-11, E2E-01, E2E-02 |

---

## 13. Non-goals

- No test implementation, execution, publishing, or integration.
- No source or test modification.
- No full publishing authorization in mandatory acceptance.
- No R1–R5 regression in mandatory acceptance.
- No new rights policy, budget sign rule, or normalization rule.
- No renderer redesign.
- No use of the live `data/` or `outputs/` directories.
