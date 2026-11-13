# B3 R6 Integration Test Design

**Document ID:** ND-GOV-005-B3-DEEPSEEK-TEST-DESIGN-01  
**Status:** TEST DESIGN ONLY — no tests implemented, no tests executed, no acceptance claimed.  
**Scope:** Frozen R6 (`cutout_selection` renderer → pipeline → metadata persistence) and R1–R5 regression protection.  
**Mode:** read-only. No source or test files were modified in producing this design.

---

## 1. Authority, scope and reconciliation

### 1.1 Frozen contract

The design oracle is `ND_GOV_005_B3_REMEDIATION_SPEC_FINAL_2026-10-31.md`, R6:

> `"cutout_selection": render.get("evidence", {}).get("cutout_selection", {})` in the pipeline evidence block. Renderer already emits both keys (`assembly.py:104-106`); no logic change.

The owner decision behind it is `ND_GOV_004_ZERO_CUTOUT_RIGHTS_INVESTIGATION_2026-10-31.md` §6: zero-cutout content is publishable only when the selector's reason is recorded; `rights_gate.publish_ready` is never the authority.

### 1.2 Dependency reconciliation inputs

No mounted file is literally titled "Copilot dependency reconciliation report." The dependency findings used here come from the two available reconciliation artifacts:

| Input | Role in this design |
|---|---|
| `ND_GOV_005_B3_DOC_RECON_01_2026-11-02.md` | Source inventory, R6 blocked on incomplete baseline, hash-authority conflict |
| `ND_GOV_005_B3_CODEX_R6_VERIFY_03_2026-11-02.md` | Actual renderer return structure, missing `app/render/` and `app/visuals/cutouts.py` in the worktree, tests that do not invoke the pipeline, named coverage gaps |

If the owner holds a separate Copilot dependency report, its dependency table should replace §7 of this document; the test cases do not change.

### 1.3 What this design is not

- It is not a verification or acceptance result.
- It does not modify production code or tests.
- It does not re-litigate R1–R5 semantics; R1–R5 appear only as regression protection.
- It does not propose a renderer redesign; R6 is a persistence contract.

---

## 2. System under test

### 2.1 Actual renderer invocation

The production path is the compatibility shim, not a direct import of `app.render.assembly`:

```python
# app/script/pipeline.py:347-354
render = motion_render.render_video(
    shots,
    mix_source,
    output_path,
    work_dir=shots_dir,
    ass_path=ass_path,
    evidence={
        "ledger": ledger,
        "script_sha256": ledger.get("script_sha256", ""),
        "ledger_sha256": ledger.get("ledger_sha256", ""),
    },
)
```

`motion_render.py:48` re-exports `app.render.assembly.render_video`:

```python
def render_video(shots: list[dict], audio_path: Path, out_path: Path, *,
                 work_dir: Path, ass_path: Path | None = None,
                 width: int = WIDTH, height: int = HEIGHT,
                 fps: int = FPS, evidence: dict | None = None) -> dict:
```

Inputs that matter to R6:

| Input | Requirement | Why |
|---|---|---|
| `shots` | Non-empty list; `shots[-1]["end"]` present; each shot has `index`, `start`, `end`, `duration`, and narration (`claim`/`caption`/scene narration) | The renderer derives `scene_claims` from shot narration |
| `audio_path` | Existing, probe-able audio file | `render_video` raises if missing; `_probe_duration` sets duration |
| `out_path` | Writable path in a temp dir | Real render writes an MP4 |
| `work_dir` | Temp dir | Cutout cards and assets are written here |
| `ass_path` | Optional; temp path | Captions; can be omitted in a minimal renderer test |
| `evidence` | `{"ledger": <claim ledger>, ...}` | Without a ledger the cutout block is skipped and `cutout_selection` becomes `{}` |
| env | `DRY_RUN` explicitly set/cleared | Changes asset resolution and shot rendering; must not be inherited implicitly |

The returned `render` dict contains `status`, `path`, `duration`, `shots`, `width`, `height`, `assets`, `storyboard`, `motion`, `audio_boundaries`, and — critically — `evidence` (`app/render/assembly.py:330-349`).

### 2.2 Real renderer-generated `cutout_selection`

Inside `render_video`, when `evidence.get("ledger")` is truthy (`assembly.py:79-112`):

1. `scene_claims[index] = claim_ledger.claims_for_scene(ledger, narration)`.
2. `selection = cutout_module.select_cutout_scenes(ledger, scene_claims)`.
3. `evidence["cutout_selection"] = selection`.
4. `rights = cutout_module.rights_gate(list(cutout_plan.values()))`.
5. At return: `"cutout_selection": evidence.get("cutout_selection") or {}`.

`select_cutout_scenes` (`app/visuals/cutouts.py:207-259`) always returns three keys:

```json
{
  "selected": [
    {"scene_index": 0, "claim_id": "clm_example", "claim_type": "statistic",
     "status": "supported", "priority": 3}
  ],
  "budget": 1,
  "reason": "1 of 1 cutout slot(s) used"
}
```

Zero-cutout selector results still return a **non-empty dict**:

```json
{"selected": [], "budget": 1, "reason": "no claim worth a cutout"}
{"selected": [], "budget": 0, "reason": "no scenes"}
```

`{}` is produced only when the renderer never ran the cutout block (no ledger): `evidence.get("cutout_selection")` is `None`, and `or {}` yields `{}`. The real renderer therefore emits the key in every successful return; "missing key" is a stub/older-renderer case, not a real-renderer case.

The renderer also emits `evidence.cutouts` as a list of persisted card records whose `reuse_rights` is a **bare status string** (`assembly.py:342`), plus `evidence.rights_gate` with `checked`, `blocked`, `publish_ready`, `blocked_claim_ids`.

### 2.3 Pipeline consumption and persistence

The shared production pipeline evidence block is `app/script/pipeline.py:453-464`:

```python
"evidence": {
    ...
    "cutouts": render.get("evidence", {}).get("cutouts", []),
    "rights_gate": render.get("evidence", {}).get("rights_gate", {}),
},
```

Frozen R6 adds the sibling key:

```python
"cutout_selection": render.get("evidence", {}).get("cutout_selection", {}),
```

The required data flow is therefore:

```text
shots + audio + ledger
  -> motion_render.render_video(... evidence={"ledger": ...})
  -> render["evidence"]["cutout_selection"]        # nested, not top-level
  -> metadata["evidence"]["cutout_selection"]      # pipeline persistence
  -> data/metadata*.json                           # JSON write (main / caller)
```

Three wrong shapes must be treated as defects, not alternatives:

1. Reading `render["cutout_selection"]` (top-level) — the renderer nests it under `evidence`.
2. Reading `visuals["cutout_selection"]` — `visuals` is `_describe_visuals(...)`, which has no such key.
3. Falling back to `research["cutout_selection"]` — no research fallback is authorized.

### 2.4 Contract divergences and decision gates

| # | Question | Frozen position | Handoff position | Design treatment |
|---|---|---|---|---|
| D1 | Missing renderer `cutout_selection` key | Default `{}`, key present | `reports/unattributed/R6_CORRECTION_COMPLETE.md`: "missing not synthesized," key absent | Acceptance cases follow frozen `{}`; the absent-key variant is a non-acceptance characterization test |
| D2 | Pass-through source | `render["evidence"]` | Worktree reads `visuals` | Acceptance asserts `render`; a decoy test proves the source |
| D3 | `cutouts` / `rights_gate` persistence | R6 names only `cutout_selection`; the shared block already passes the other two | Worktree drops all three | Assert all three are pass-through, as R1–R5 regression protection, not as a new R6 requirement |
| D4 | Malformed renderer `evidence` (`None`, string, list) | Expression raises `AttributeError`; fail-closed | Not addressed | Characterization test only; owner decides whether to define `{}` fallback |
| D5 | `cutout_selection: null` | `.get(..., {})` returns `None` (key present) | Not addressed | Preserve `null`; downstream R5 blocks. Do not normalize |
| D6 | `budget` sign | Frozen R5: integer, no non-negative constraint | Worktree accepts negative | Regression suite preserves negative acceptance; do not "fix" in R6 |

---

## 3. Test layers

| Layer | Name | Renderer | Pipeline | JSON | Purpose |
|---|---|---|---|---|---|
| U | Unit | No | No (helper only) | Optional | Contract shape of selector and JSON equality helper |
| M | Mocked pipeline pass-through | Stubbed | Real `run()` / `main()` | Optional | Prove pipeline reads nested renderer evidence and persists it |
| R | Actual renderer integration | Real | No (direct call) | No | Prove the real renderer emits the expected `cutout_selection` |
| E | Renderer → pipeline → JSON | Real (or captured real) | Real | Real | Prove exact end-to-end persistence |
| G | R1–R5 regression | Per case | Per case | Per case | Prove R6 did not change rights outcomes |

Rules:

- M tests must never call the real renderer; R tests must never call the full pipeline; E tests call the real renderer through the real pipeline with only external boundaries doubled.
- U tests may call private helpers only if the helper is a stable, named seam. Otherwise use M.
- No test writes to the repository's live `data/` or `outputs/`; every path is a `tmp_path`.
- No test uses the network. No test relies on the current date without a frozen clock or fixture timestamp.

---

## 4. External boundaries and required test doubles

| Boundary | Real implementation | Double / control | Used by |
|---|---|---|---|
| Topic selection | `app.research.selector.select_best`, `discover_topics` | Deterministic selected topic + ranked list | M, E |
| Research | `app/research/desk.py::research_topic` | Canned research bundle with claims and sources | M, E |
| Script writing | `app/script/studio.py::write_script` | Canned script dict with every key the pipeline reads | M, E |
| Claim ledger | `app/research/claims.py::build_ledger`, `write_ledger` | Prefer real with canned research; golden ledger for R | M, R, E |
| TTS | `app/voice/provider.py::generate_voice` | Stub dict + pre-created silent audio file | M, E |
| Audio probe | `pipeline.probe_duration` / ffprobe | Stub `2.0` for M; real probe for R/E | M, R, E |
| Captions | `pipeline.build_captions`, `motion_render.make_kinetic_ass` | Stub minimal captions; no ASS file required for M | M, E |
| Shot planning | `motion_director.plan_shots`, `app/visuals/shotplan.py` | Golden shots for R; stubbed shots for M | M, R, E |
| Renderer | `motion_render.render_video` → `app/render/assembly.py` | Stub returning a controlled `render` dict for M; real for R/E | M, R, E |
| QA | `motion_render.qa_video` | Stub `{"duration": 2.0, "width": 1080, "height": 1920, "warnings": []}` | M, E |
| Cutout selector | `app/visuals/cutouts.py::select_cutout_scenes` | Real for R; may be stubbed for M only if the test is not about selection | M, R |
| Card rendering | `cutouts.build_source_card` (ffmpeg/drawtext) | Stub `{"rendered": True, "reuse_rights": {...}}` when testing gate consistency; real when testing card records | R |
| Rights gate | `cutouts.rights_gate` | Real; this is part of the renderer evidence contract | R |
| Storyboard | `app/visuals/storyboard.py::build_storyboard` | Real for R/E; stub only if the baseline is incomplete | R, E |
| Asset chain | `app/visuals/chain.py::plan_scenes`, `stock_fetcher` | No network; `DRY_RUN` or deterministic asset stubs | R, E |
| Filesystem | repo `data/`, `outputs/` | `tmp_path` for work, output, metadata | All |
| Clock | `approval_integrity.approved_today`, `upload_window_open` | Frozen/injected timestamp for authorization cases | G |
| Approval/governance | `tests/governance_fixtures.py` sandbox | Real fixture, temp root | G (boundary-level) |
| Binaries | `ffmpeg`, `ffprobe` | `shutil.which` skip for R/E; generate a synthetic audio file | R, E |
| Environment | `DRY_RUN`, `STORYBOARD_GATE`, `TTS_*`, `MUSIC_BED` | Explicitly set/clear per test; never inherit | R, E |
| Network | stock providers, LLM, TTS | No network; all external calls doubled | All |
| JSON | stdlib `json` | Real; this is the serialization under test | All |

---

## 5. Test cases

### 5.1 Unit tests (U)

#### U1 — `test_describe_visuals_has_no_cutout_selection_key`

- **Layer:** unit.
- **Purpose:** lock the fact that `visuals` cannot be the R6 source.
- **Setup:** call `pipeline._describe_visuals([], [])` and call it again with one stock asset and one shot.
- **Action:** inspect the returned dict.
- **Assertions:**
  - `"cutout_selection" not in result`.
  - Key set is exactly `{mode, asset_count, asset_path, shot_count, procedural_shot_count, providers, assets, credits}`.
- **Expected:** pass. If this fails, the decoy premise in M2 must be re-derived.
- **Dependencies:** none beyond `app.script.pipeline` import.

#### U2 — `test_select_cutout_scenes_contract_for_cutout_worthy_claim`

- **Layer:** unit.
- **Purpose:** define the real renderer's selection shape before testing persistence.
- **Setup:** ledger with one `supported` `statistic` claim; `scene_claims = {0: [claim]}`.
- **Action:** `cutouts.select_cutout_scenes(ledger, scene_claims)`.
- **Assertions:**
  - Exact keys `{"selected", "budget", "reason"}`.
  - `type(budget) is int` and not bool; `budget == 1`.
  - `selected` is a list of one dict with key order-independent equality to `{scene_index: 0, claim_id: ..., claim_type: "statistic", status: "supported", priority: 3}`.
  - `reason == "1 of 1 cutout slot(s) used"`.
- **Expected:** pass.
- **Dependencies:** `app.visuals.cutouts`, `CUTOUT_CLAIM_TYPES` constants.

#### U3 — `test_select_cutout_scenes_contract_for_zero_and_no_scene_cases`

- **Layer:** unit.
- **Purpose:** distinguish selector-empty from `{}`.
- **Setup:**
  - Case A: one `supported` `statement` claim (not cutout-worthy).
  - Case B: `scene_claims = {}`.
- **Action:** call the selector.
- **Assertions:**
  - Case A: `selected == []`; `budget == 1`; `reason == "no claim worth a cutout"`.
  - Case B: `selected == []`; `budget == 0`; `reason == "no scenes"`.
  - Both are non-empty dicts with all three keys.
- **Expected:** pass.
- **Dependencies:** `CUTOUT_CLAIM_TYPES`; claim `verification.status`.

#### U4 — `test_json_round_trip_is_lossless_for_selection_payloads`

- **Layer:** unit.
- **Purpose:** establish the exact-equality helper used by M/E.
- **Setup:** payloads:
  1. U2 non-empty selection.
  2. `{}`.
  3. U3 selector-empty.
  4. Extra nested field `{"reason": "x", "budget": 0, "selected": [], "meta": {"a": [1, 2]}}`.
  5. Unicode reason.
- **Action:** `json.loads(json.dumps(payload))`.
- **Assertions:** reloaded equals original; `type(budget)` preserved (`int` stays `int`, `bool` stays `bool`); list order preserved; no key loss.
- **Expected:** pass.
- **Dependencies:** stdlib `json` only.

#### U5 — `test_frozen_default_expression_oracle`

- **Layer:** unit (oracle characterization, not production coverage).
- **Purpose:** pin the frozen default semantics used by M5/E3.
- **Setup:** a local pure function `frozen_selection(render)` implementing exactly `render.get("evidence", {}).get("cutout_selection", {})`.
- **Action:** evaluate over:
  - `{"evidence": {"cutout_selection": S}}` → `S`.
  - `{"evidence": {}}` → `{}`.
  - `{}` → `{}`.
  - `{"evidence": {"cutout_selection": None}}` → `None`.
  - `{"evidence": None}` → `AttributeError` (characterization).
- **Assertions:** as listed.
- **Expected:** pass; the `None` and `AttributeError` rows are documented divergences D4/D5, not acceptance failures.
- **Dependencies:** none.

### 5.2 Mocked pipeline pass-through tests (M)

**Common harness:** patch every boundary in §4 except `pipeline.run`/`pipeline.main` and the `json` module. Use a temp work dir and a pre-created `voice.mp3`; do not call the real renderer. A `render_stub(selection, cutouts=None, rights_gate=None, assets=None)` factory returns a full-enough render dict.

#### M1 — `test_pipeline_persists_nested_renderer_cutout_selection`

- **Setup:** render stub returns:
  ```python
  {"status": "ok", "assets": [], "evidence": {
      "cutout_selection": S,
      "cutouts": C,
      "rights_gate": G,
  }}
  ```
  where `S` is U2's non-empty selection, `C` a permitted card list, `G` `{"checked": 1, "blocked": 0, ...}`.
- **Action:** `metadata = pipeline.run(topic="T", work_dir=tmp)`.
- **Assertions:**
  - `metadata["evidence"]["cutout_selection"] == S`.
  - `metadata["evidence"]["cutouts"] == C`.
  - `metadata["evidence"]["rights_gate"] == G`.
  - The render stub was called with `evidence["ledger"]` truthy.
- **Expected:** pass on a correct implementation; fails if the pipeline reads `visuals`, drops the key, or synthesizes.
- **Dependencies:** all M doubles.

#### M2 — `test_pipeline_uses_render_evidence_not_visuals_decoy`

- **Purpose:** source discrimination — the direct regression for the worktree bug.
- **Setup:** patch `pipeline._describe_visuals` to return a normal visuals dict plus `"cutout_selection": DECOY`; render evidence contains `S` (different reason/budget/selected).
- **Action:** `pipeline.run(...)`.
- **Assertions:**
  - `metadata["evidence"]["cutout_selection"] == S`.
  - `metadata["evidence"]["cutout_selection"] != DECOY`.
  - `DECOY["reason"]` and `S["reason"]` differ so the assertion is unambiguous.
- **Expected:** pass only if the implementation reads `render["evidence"]`.
- **Dependencies:** `_describe_visuals` patched; render stub.

#### M3 — `test_pipeline_does_not_use_research_fallback`

- **Setup:** render evidence has no `cutout_selection` key; `research["cutout_selection"] = DECOY`.
- **Action:** `pipeline.run(...)`.
- **Assertions:** persisted value is `{}` (frozen default), never `DECOY`; key present.
- **Expected:** pass.
- **Dependencies:** research stub with decoy.

#### M4 — `test_pipeline_preserves_empty_selection_dict`

- **Setup:** render evidence `{"cutout_selection": {}}`.
- **Action:** `pipeline.run(...)`.
- **Assertions:** `"cutout_selection" in metadata["evidence"]`; value `== {}`; not omitted; not replaced by a synthesized reason.
- **Expected:** pass.
- **Dependencies:** render stub.

#### M5 — `test_pipeline_defaults_missing_selection_to_empty_dict`

- **Setup:** render evidence `{"cutouts": [], "rights_gate": {}}` (no `cutout_selection` key).
- **Action:** `pipeline.run(...)`.
- **Assertions:** `metadata["evidence"]["cutout_selection"] == {}`; key present.
- **Expected:** frozen pass. The handoff's "key absent" variant is **not** asserted here; see D1/E3.
- **Dependencies:** render stub.

#### M6 — `test_pipeline_preserves_selector_shaped_empty_selection`

- **Setup:** render evidence `{"cutout_selection": {"selected": [], "budget": 0, "reason": "no scenes"}}`.
- **Action:** `pipeline.run(...)`.
- **Assertions:** exact persistence of all three keys; not collapsed to `{}`; `budget` remains `int`; `reason` remains `str`.
- **Expected:** pass. This is the real zero-cutout proof shape.
- **Dependencies:** render stub.

#### M7 — `test_pipeline_does_not_mutate_renderer_evidence`

- **Setup:** deep-copy the render evidence before the call.
- **Action:** `pipeline.run(...)`.
- **Assertions:**
  - `render["evidence"]` equals its pre-call snapshot (no added/removed/changed keys).
  - `metadata["evidence"]["cutout_selection"] == snapshot["cutout_selection"]`.
- **Expected:** pass.
- **Note:** a post-run mutation/alias check (mutating render after `run` and observing metadata) is characterization only; value equality is the acceptance assertion.
- **Dependencies:** `copy.deepcopy`.

#### M8 — `test_pipeline_does_not_synthesize_cutouts_rights_gate_or_reuse_rights`

- **Setup:** render evidence only `{"cutout_selection": S}`; no `cutouts`, no `rights_gate`.
- **Action:** `pipeline.run(...)`.
- **Assertions:**
  - No synthesized `cutouts` and no synthesized `rights_gate` (absent or exactly the empty value passed; match the shared block's `.get(..., default)` semantics).
  - No `reuse_rights` key added to any selection entry.
  - No `publish_ready` added to the selection.
- **Expected:** pass; R6 is pass-through, not synthesis.
- **Dependencies:** render stub.

#### M9 — `test_pipeline_main_writes_selection_to_json`

- **Setup:** same stubs as M1; a temp `--out` path.
- **Action:** `pipeline.main(["--topic", "T", "--work-dir", str(tmp), "--out", str(out)])`.
- **Assertions:**
  - `json.loads(out.read_text())["evidence"]["cutout_selection"] == S`.
  - The written `governance.entry == "direct"` (main's documented draft stamp).
  - No other evidence key changed relative to M1.
- **Expected:** pass.
- **Dependencies:** `main` writes JSON; no live `data/`.

### 5.3 Actual renderer integration tests (R)

**Prerequisites:** complete baseline including `app/render/`, `app/visuals/cutouts.py`, `app/visuals/storyboard.py`, `app/research/claims.py`, `motion_director.py`; `ffmpeg` and `ffprobe` on PATH; a golden `shots.json`, `ledger.json`, and a short synthetic audio file. Skip the whole group with a clear skip reason when `shutil.which("ffmpeg")` or `shutil.which("ffprobe")` is absent, or when required modules are missing. Pin the baseline hashes in the test session header.

#### R1 — `test_real_renderer_emits_cutout_selection_for_cutout_worthy_claim`

- **Setup:** shots from `golden_shots.json` (2–3 shots, `end` aligned to audio); ledger with one `supported` `statistic` claim whose narration matches shot 0; audio 2 s; `work_dir` temp; `out_path` temp; `DRY_RUN` explicitly `"0"`.
- **Action:** call `motion_render.render_video(shots, audio, out, work_dir=work, evidence={"ledger": ledger, "script_sha256": ..., "ledger_sha256": ...})`.
- **Assertions:**
  - `render["evidence"]["cutout_selection"]` is a dict with `selected`, `budget`, `reason`.
  - `budget >= 1`; `type(budget) is int`; `selected` non-empty.
  - `selected[0]["claim_id"]` equals the ledger claim id; `scene_index` is in range; types are JSON-native.
  - `reason` matches `r"\d+ of \d+ cutout slot\(s\) used"`.
  - `render["evidence"]["cutouts"]` is a list; when non-empty, each record has `reuse_rights` (string) and `rights_gate` has `checked == len(cutouts)`.
  - `render["evidence"]["cutout_selection"]` is not present at `render` top level.
- **Expected:** pass on a complete baseline with a cutout-worthy claim.
- **Dependencies:** real renderer, ffmpeg/ffprobe, golden shots/ledger/audio; card rendering may fail without fonts but selection must still be emitted.

#### R2 — `test_real_renderer_emits_empty_dict_without_ledger`

- **Setup:** same shots/audio; `evidence=None` (or `{"ledger": None}`); **do not** pass a ledger.
- **Action:** real `render_video`.
- **Assertions:** `render["evidence"]["cutout_selection"] == {}`; key present; no `selected`/`budget`/`reason` keys.
- **Expected:** pass. This is the real empty-selection case.
- **Dependencies:** real renderer; no ledger module needed.

#### R3 — `test_real_renderer_emits_selector_reason_when_no_cutout_worthy_claim`

- **Setup:** ledger with a `supported` `statement` claim (not in `CUTOUT_CLAIM_TYPES`); shots whose narration matches it.
- **Action:** real `render_video` with the ledger.
- **Assertions:** `selected == []`; `budget >= 1`; `reason == "no claim worth a cutout"`; key present.
- **Expected:** pass.
- **Dependencies:** real renderer + golden ledger variant.

#### R4 — `test_renderer_selection_and_evidence_are_json_native`

- **Setup:** R1 output.
- **Action:** `json.dumps(render["evidence"])`, then `json.loads`.
- **Assertions:** reload equals original; no `Path`, `datetime`, bytes, or custom objects; `budget` stays `int`; `selected` list order preserved.
- **Expected:** pass.
- **Dependencies:** stdlib `json`.

#### R5 — `test_renderer_rights_gate_matches_cutouts`

- **Setup:** stub `cutouts.build_source_card` to return `{"rendered": True, "reuse_rights": {"status": status}, "claim_id": ...}` for two claims (one `permitted`, one `unknown`); pass a ledger with both; call real `render_video`.
- **Action:** inspect `render["evidence"]`.
- **Assertions:** `rights_gate["checked"] == len(cutouts)`; `rights_gate["blocked"]` equals the number of non-permitted cards; `publish_ready == (blocked == 0 and bool(cutouts))`; `blocked_claim_ids` matches.
- **Expected:** pass. This is a renderer contract check, not a replacement for B3 R4.
- **Dependencies:** real renderer plus `build_source_card` stub; no font dependency.

#### R6 — `test_renderer_nests_selection_under_evidence_not_visuals`

- **Setup:** R1 output.
- **Action:** inspect locations.
- **Assertions:** `"cutout_selection" in render["evidence"]`; `"cutout_selection" not in render`; no asset dict in `render["assets"]` carries `cutout_selection`; applying `pipeline._describe_visuals(render["assets"], shots)` yields no `cutout_selection`.
- **Expected:** pass; documents the correct source path.
- **Dependencies:** R1 output; `_describe_visuals`.

### 5.4 Renderer → pipeline → JSON persistence tests (E)

These are the highest-value R6 tests. They invoke the real renderer through the real pipeline, doubling only external boundaries. They require the complete baseline, ffmpeg/ffprobe, and a 2–3 second synthetic render.

#### E1 — `test_real_renderer_through_pipeline_persists_exact_selection`

- **Setup:** patch all non-renderer stages (§4); wrap `pipeline.motion_render.render_video` with `unittest.mock.patch.object(..., wraps=...)` so the real renderer runs and its return is captured; call `pipeline.run(topic="T", work_dir=tmp)`.
- **Action:** compare captured `render["evidence"]["cutout_selection"]` to `metadata["evidence"]["cutout_selection"]`.
- **Assertions:**
  - Exact dict equality, including `selected` order, `budget` type, `reason` string.
  - `metadata["evidence"]["cutouts"] == render["evidence"]["cutouts"]`.
  - `metadata["evidence"]["rights_gate"] == render["evidence"]["rights_gate"]`.
  - The render stub (wrapped real) received `evidence["ledger"]` truthy.
- **Expected:** pass on the frozen implementation. This is the primary R6 integration assertion.
- **Dependencies:** complete baseline, ffmpeg, golden inputs, all M doubles except the renderer.

#### E2 — `test_real_renderer_pipeline_main_json_exact_equality`

- **Setup:** same as E1, but call `pipeline.main(["--topic", "T", "--work-dir", str(tmp), "--out", str(out)])`; capture the real render return with `wraps`.
- **Action:** read `out` JSON.
- **Assertions:**
  - `persisted["evidence"]["cutout_selection"] == captured["evidence"]["cutout_selection"]`.
  - `json.loads(json.dumps(captured_selection, sort_keys=True)) == json.loads(json.dumps(persisted_selection, sort_keys=True))`.
  - `persisted["governance"]["entry"] == "direct"` (main stamp); evidence unchanged.
- **Expected:** pass. This is the renderer → pipeline → JSON proof.
- **Dependencies:** E1 plus `main` write path.

#### E3 — `test_frozen_missing_selection_through_main_is_empty_dict`

- **Setup:** stub the renderer (not real) to return `{"assets": [], "evidence": {"cutouts": [], "rights_gate": {}}}`; call `pipeline.main([...])`.
- **Action:** read JSON.
- **Assertions:** `"cutout_selection" in persisted["evidence"]`; value `== {}`.
- **Expected:** frozen pass. A separate **non-acceptance characterization** may assert the handoff's absent-key behavior; do not run both as acceptance (D1).
- **Dependencies:** M harness + `main`.

#### E4 — `test_real_renderer_without_ledger_through_main_is_empty_dict`

- **Setup:** real renderer with `evidence=None` through the pipeline; pipeline must still pass a ledger in the real path, so this case requires a pipeline variant/test hook that omits the ledger. Alternatively, call the real renderer directly (R2) and separately test the pipeline default with a stub (M5).
- **Design note:** the production pipeline always passes a ledger, so a "real renderer without ledger through the pipeline" is not a reachable end-to-end state. Keep R2 for the renderer and M5/E3 for the pipeline default; do not contort the pipeline to make E4 pass.
- **Expected:** not applicable end-to-end; documented as a reachable-path limitation.
- **Dependencies:** none beyond R2/M5.

#### E5 — `test_persisted_metadata_preserves_r5_outcomes`

- **Setup:** use E1/E2 persisted metadata variants:
  1. Selector-empty proof (`{"selected": [], "budget": 0, "reason": "no scenes"}`).
  2. `{}`.
  3. Non-empty `cutouts` with `reuse_rights: "permitted"` and `rights_gate: 1/0`.
  4. Non-empty `cutouts` with `reuse_rights: "unknown"` and `rights_gate: 1/0`.
- **Action:** call `_rights_violations(metadata)` on each; optionally `authorize_publish` with a governance/approval sandbox.
- **Assertions:**
  - Case 1: no violations (R5 authorizes).
  - Case 2: zero-cutout proof finding (R3/R5 block).
  - Case 3: no violations (R1 string normalizes).
  - Case 4: card-specific `reuse_rights` finding (R1 block).
  - At boundary level, if used: codes `authorized`, `blocked_rights`, `authorized`, `blocked_rights`.
- **Expected:** pass; R6 preserves R1–R5 outcomes.
- **Dependencies:** `publish_authorization._rights_violations`; optional `governance_fixtures`.

### 5.5 R1–R5 regression protection (G)

#### G1 — `test_r1_r5_suites_unchanged`

- **Layer:** CI/meta.
- **Action:** run the existing `RightsAndEvidenceTests` and the DeepSeek R1–R5 adversarial suite against the R6 tree.
- **Assertions:** counts match the pre-R6 baseline; any known pre-existing failures are explicitly listed and not attributed to R6. Current baseline knowns: R4 cap/true-total defects and R5 non-string-reason acceptance (from the adversarial run), plus the existing R6 test failures in the incomplete worktree.
- **Expected:** no new failures caused by the R6 line.
- **Dependencies:** test environment, baseline hashes.

#### G2 — `test_r6_does_not_change_rights_outcomes`

- **Layer:** integration/regression.
- **Setup:** a matrix of persisted metadata: `{}`, selector-empty, permitted card, unknown card, gate mismatch, boolean count, negative budget.
- **Action:** `_rights_violations(metadata)`.
- **Assertions:** exact golden outcomes per input, unchanged from the R1–R5 oracle.
- **Expected:** pass.
- **Dependencies:** `publish_authorization`.

#### G3 — `test_r6_preserves_cutouts_and_rights_gate`

- **Layer:** mocked pipeline.
- **Setup:** render evidence with `cutouts` and `rights_gate`; run pipeline.
- **Assertions:** exact equality for both, in addition to `cutout_selection`.
- **Expected:** pass; guards the worktree bug that drops all three.
- **Dependencies:** M harness.

#### G4 — `test_r6_does_not_synthesize_rights_evidence`

- **Layer:** mocked pipeline.
- **Setup:** render evidence lacks `cutouts`, `rights_gate`, and `reuse_rights`.
- **Assertions:** no `reuse_rights` added; no `rights_gate` constructed; no `cutouts` inferred from assets; no `publish_ready` invented.
- **Expected:** pass.
- **Dependencies:** M harness.

#### G5 — `test_zero_cutout_artifact_remains_publishable`

- **Layer:** integration.
- **Setup:** E1/E2 metadata with selector-empty proof; a governance/approval sandbox bound to the persisted metadata and video.
- **Action:** `authorize_publish(platform="youtube", data_root=root)`.
- **Assertions:** `status == "authorized"`; destination private by default; no `blocked_rights`.
- **Expected:** pass; this is the B3 outcome R6 exists to preserve.
- **Dependencies:** `governance_fixtures`, `approval_integrity`, frozen clock.

---

## 6. Equality and assertion rules

`assert_selection_exact(original, persisted)` must enforce:

1. Both are dicts.
2. Exact key sets: no added keys, no dropped keys.
3. Exact value equality, recursively.
4. `type(persisted["budget"]) is int` and not `bool`.
5. `type(persisted["reason"]) is str` and non-empty for selector-shaped proof; `{}` has no such keys.
6. `selected` is a list; order preserved; each entry is a dict with JSON-native values.
7. `json.loads(json.dumps(original, sort_keys=True)) == json.loads(json.dumps(persisted, sort_keys=True))`.
8. No aliasing requirement: value equality is required; object identity is not. A post-run mutation/alias check is characterization only.

Special cases:

| Renderer value | Persisted expectation (frozen) |
|---|---|
| Non-empty selection `S` | `S` exactly |
| `{}` | `{}`, key present |
| Selector-empty `{"selected": [], "budget": 0, "reason": "no scenes"}` | exact dict, not `{}` |
| Missing key | `{}`, key present |
| `None` | `None` (key present), downstream R5 blocks |
| Non-dict malformed value | preserved as-is; downstream R5 blocks; do not crash-normalize in R6 |
| `render["evidence"]` missing | `{}` |
| `render["evidence"]` is `None`/string/list | characterization only; frozen expression raises; owner decision D4 |

---

## 7. Fixtures and data

| Fixture | Shape | Used by |
|---|---|---|
| `golden_shots.json` | 2–3 shots with `index`, `start`, `end`, `duration`, `claim`, `caption`, `source`, `asset_query` | R, E |
| `golden_ledger_cutout.json` | One `supported` `statistic` claim with narration matching shot 0 | R, E |
| `golden_ledger_no_cutout.json` | One `supported` `statement` claim; no cutout-worthy kinds | R3 |
| `golden_selection_nonempty.json` | U2 shape | M, E |
| `golden_selection_selector_empty.json` | `{"selected": [], "budget": 0, "reason": "no scenes"}` | M, E |
| `golden_selection_empty.json` | `{}` | M, E |
| `silent_2s.wav` | Generated by ffmpeg in a session fixture; no repo asset | R, E |
| `render_stub(selection, cutouts, rights_gate, assets)` | Full-enough render dict | M |
| `pipeline_stage_stubs()` | Context manager patching every non-renderer boundary | M, E |
| `assert_selection_exact` | Equality helper from §6 | M, E, G |
| `frozen_clock` | Injected timestamp for approval cases | G5 |

No fixture may be read from the live `data/` or `outputs/` directories; copy or synthesize into `tmp_path`.

---

## 8. Dependencies and environment

### 8.1 Required baseline

R6 is executable only on a baseline that includes the renderer and evidence layer:

- `app/render/assembly.py`, `app/render/ffmpeg_tools.py`, `app/render/shots.py`, `app/render/subtitles.py`
- `app/visuals/cutouts.py`, `app/visuals/storyboard.py`, `app/visuals/chain.py`, `app/visuals/beats.py`, `app/visuals/shotplan.py`
- `app/research/claims.py`, `app/research/atomic.py`, `app/research/lineage.py`, `app/research/desk.py`, `app/research/selector.py`
- `app/script/pipeline.py`, `app/script/studio.py`, `app/voice/provider.py`
- `motion_director.py`, `motion_render.py`, `stock_fetcher.py`, `visual_assets.py`
- `publish_authorization.py`, `approval_integrity.py`, `visual_quality.py`
- `tests/governance_fixtures.py` for the authorization cases

The `/tmp/nd_gov_005` snapshot does **not** contain `app/render/`, `app/visuals/cutouts.py`, `app/visuals/storyboard.py`, or `motion_director.py`; R6 is unexecutable there. Do not treat a run in that snapshot as R6 evidence.

### 8.2 Binaries and environment

- `ffmpeg` and `ffprobe` on PATH; skip R/E with a recorded reason when absent.
- A writable temp root; no repository writes.
- `DRY_RUN` explicitly set per test; never inherited.
- No network. Stock, LLM and TTS boundaries are doubled.
- Python 3.11+ for `zoneinfo`; pytest; `unittest.mock`.
- `fastapi` is not required for R6; it is required only if a test imports `publish_all` or the API.

### 8.3 Hash pinning

The test session must record and assert the hashes of the files under test:

- `app/render/assembly.py`
- `app/script/pipeline.py`
- `publish_authorization.py`
- `tests/governance_fixtures.py`
- the test file itself

If a hash differs from the acceptance manifest, fail fast with a clear message rather than producing ambiguous results. The current published reports disagree on `pipeline.py` and `tests/test_publish_governance.py` hashes; do not inherit those values.

---

## 9. Expected results and blockers

| Layer | Expected on complete frozen baseline | Expected on incomplete `/tmp/nd_gov_005` |
|---|---|---|
| U | All pass | U2/U3 may pass; U1 imports `pipeline` and may fail on missing `motion_director` |
| M | All pass | M1/M2/M5/M6/M9 fail because `pipeline` reads `visuals`; import may fail first |
| R | Pass with ffmpeg + golden ledger | Blocked: no `app/render/`, no `cutouts.py`, no `motion_director.py` |
| E | Pass with complete baseline | Blocked |
| G | Pass (with known pre-existing R4/R5 defects explicitly excluded) | G1/G2 may run; G5 needs governance fixtures |

These are design expectations, not verification results. A blocked layer is a dependency failure, not a B3 pass or fail.

---

## 10. Traceability

| Frozen R6 clause | Cases |
|---|---|
| `render.get("evidence", {})` | M2, R6, E1 |
| `.get("cutout_selection", {})` | M5, E3, U5 |
| Persist under `metadata["evidence"]` | M1, M9, E1, E2 |
| Renderer already emits both keys | R1, R2, R3, R6 |
| No logic change / no synthesis | M8, G4 |
| Non-empty preservation | M1, R1, E1 |
| Empty `{}` preservation | M4, R2, E3 |
| Missing → `{}` | M5, E3 |
| Exact equality | M1, M7, E1, E2, U4 |
| Zero-cutout proof remains authoritative | E5, G5 |
| R1–R5 unchanged | G1, G2, G3, G4 |

---

## 11. Non-goals

- No implementation of these tests in this document.
- No execution and no acceptance verdict.
- No change to R1–R5 semantics or the renderer.
- No new rights policy, no non-negative budget rule, no external state mapping.
- No use of the live `data/` or `outputs/` directories.
