"""Adapter that turns a planned visual scene into an editable local SVG asset.

This is deliberately isolated from protected shot-selection and FFmpeg modules.
The visual-chain owner can call render_scene_component() at the asset-resolution
boundary when a shot's visual_source is one of the supported component kinds.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from app.visuals.production_components import render_component
from app.visuals.screen_components import render_screen_component

SCREEN_KINDS = {"browser", "terminal", "code", "dashboard", "app"}
VECTOR_KINDS = {"metric_cards", "bar_chart", "flow_diagram", "icon_tile"}

def render_scene_component(scene: dict[str, Any], output_path: str | Path) -> dict[str, Any]:
    """Render a declared component scene and return a normalized asset record.

    Scene contract:
      {"visual_source":"screen_component"|"vector_component",
       "component":{...}, "scene_id":"...", "narration":"..."}
    """
    if not isinstance(scene, dict):
        raise TypeError("scene must be an object")
    source = str(scene.get("visual_source") or "").strip().lower()
    spec = scene.get("component")
    if not isinstance(spec, dict):
        raise ValueError("component spec is required")
    kind = str(spec.get("kind") or "").strip().lower()
    if source == "screen_component" and kind in SCREEN_KINDS:
        svg = render_screen_component(spec)
    elif source == "vector_component" and kind in VECTOR_KINDS:
        svg = render_component(spec)
    else:
        raise ValueError(f"unsupported scene component source/kind: {source}/{kind}")
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(svg, encoding="utf-8")
    return {
        "asset_type": "image",
        "media_type": "image/svg+xml",
        "path": str(target),
        "scene_id": str(scene.get("scene_id") or ""),
        "visual_source": source,
        "component_kind": kind,
        "editable": True,
        "generated_locally": True,
        "external_api_used": False,
    }

def render_scene_component_file(scene_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    scene = json.loads(Path(scene_path).read_text(encoding="utf-8"))
    return render_scene_component(scene, output_path)
