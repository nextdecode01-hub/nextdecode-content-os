from app.visuals.screen_components import render_screen_component
from app.providers import media_sources, zai


def test_screen_component_generates_editable_svg_and_escapes_text(tmp_path):
    target = tmp_path / "browser.svg"
    svg = render_screen_component({"kind":"browser","title":"AI & systems",
        "url":"https://example.test","lines":["Research <verified>"]}, target)
    assert target.read_text(encoding="utf-8") == svg
    assert "AI &amp; systems" in svg
    assert "Research &lt;verified&gt;" in svg
    assert 'width="900" height="1500"' in svg


def test_screen_component_supports_terminal_code_dashboard():
    for kind in ("terminal","code","dashboard","app"):
        assert "<svg" in render_screen_component({"kind":kind,"title":"Demo","lines":["one","two"]})


def test_screen_component_rejects_unknown_kind():
    try:
        render_screen_component({"kind":"video"})
    except ValueError as exc:
        assert "unsupported" in str(exc)
    else:
        raise AssertionError("unsupported kind should fail closed")


def test_coverr_missing_key_returns_empty(monkeypatch):
    monkeypatch.delenv("COVERR_API_KEY", raising=False)
    assert media_sources.search_coverr_videos("AI data center") == []


def test_openverse_preserves_license_and_attribution(monkeypatch):
    class Response:
        def raise_for_status(self): pass
        def json(self):
            return {"results":[{"id":"abc","title":"Server room","creator":"A",
                "url":"https://cdn.test/a.jpg","foreign_landing_url":"https://site.test/a",
                "license":"by-sa","license_version":"4.0","license_url":"https://creativecommons.org/licenses/by-sa/4.0/",
                "attribution":"A, CC BY-SA","width":1200,"height":800,"mature":False}]}
    monkeypatch.setattr(media_sources.requests,"get",lambda *a,**k:Response())
    item=media_sources.search_openverse_images("server room")[0]
    assert item["license"] == "by-sa"
    assert item["requires_attribution"] is True
    assert item["commercial_use"] is True
    assert item["attribution"] == "A, CC BY-SA"


def test_zai_missing_key_fails_closed(monkeypatch):
    monkeypatch.delenv("Z_API_KEY", raising=False)
    try:
        zai.chat([{"role":"user","content":"hello"}])
    except RuntimeError as exc:
        assert "Z_API_KEY" in str(exc)
    else:
        raise AssertionError("missing Z_API_KEY should fail closed")


def test_production_vector_components_are_valid_editable_svg():
    from app.visuals.production_components import render_component
    cases = [
        {"kind":"metric_cards","title":"Model metrics","cards":[{"label":"Latency","value":"120 ms"}]},
        {"kind":"bar_chart","title":"Benchmark","data":[{"label":"Model A","value":8},{"label":"Model B","value":4}]},
        {"kind":"flow_diagram","title":"Pipeline","nodes":[{"title":"Research","detail":"Collect evidence"},{"title":"Render","detail":"Build video"}]},
        {"kind":"icon_tile","title":"Security","symbol":"shield","caption":"Verify every claim"},
    ]
    for spec in cases:
        svg = render_component(spec)
        assert svg.startswith("<svg")
        assert 'width="1080"' in svg
        assert "</svg>" in svg


def test_production_vector_components_escape_untrusted_text():
    from app.visuals.production_components import render_component
    svg = render_component({"kind":"metric_cards","title":"R&D <live>","cards":[{"label":"A & B","value":"<script>"}]})
    assert "R&amp;D &lt;live&gt;" in svg
    assert "&lt;script&gt;" in svg


def test_production_vector_components_reject_unknown_kind():
    from app.visuals.production_components import render_component
    try:
        render_component({"kind":"webpage"})
    except ValueError:
        pass
    else:
        raise AssertionError("unknown component must fail closed")


def test_scene_component_adapter_renders_editable_local_asset(tmp_path):
    from app.visuals.scene_component_adapter import render_scene_component
    output = tmp_path / "scene.svg"
    record = render_scene_component({
        "scene_id": "beat-02",
        "visual_source": "vector_component",
        "component": {"kind": "flow_diagram", "title": "How it works",
                      "nodes": [{"title": "Input", "detail": "User request"},
                                {"title": "Output", "detail": "Useful result"}]},
    }, output)
    assert output.exists()
    assert record["asset_type"] == "image"
    assert record["editable"] is True
    assert record["external_api_used"] is False
    assert record["scene_id"] == "beat-02"


def test_scene_component_adapter_supports_screen_windows(tmp_path):
    from app.visuals.scene_component_adapter import render_scene_component
    output = tmp_path / "terminal.svg"
    record = render_scene_component({
        "visual_source": "screen_component",
        "component": {"kind": "terminal", "title": "Terminal",
                      "lines": ["python train.py", "training complete"]},
    }, output)
    assert output.exists()
    assert "training complete" in output.read_text()
    assert record["component_kind"] == "terminal"


def test_scene_component_adapter_fails_closed_on_unknown_source(tmp_path):
    from app.visuals.scene_component_adapter import render_scene_component
    try:
        render_scene_component({"visual_source": "remote_browser", "component": {"kind": "browser"}}, tmp_path / "x.svg")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown visual source must fail closed")
