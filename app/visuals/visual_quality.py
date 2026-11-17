from __future__ import annotations

from pathlib import Path


PUBLISHABLE_VISUAL_MODES = frozenset(
    {
        "owner_recorded",
        "original_footage",
        "licensed_stock",
        "coverr_stock",
        "pixabay_stock",
        "multi_shot_stock",
    }
)

REQUIRED_STOCK_FIELDS = ("title", "license")


def _assets_are_publishable(visuals: dict) -> bool:
    """A multi-shot video is publishable when every real asset carries a licence."""
    assets = visuals.get("assets")
    if not isinstance(assets, list) or not assets:
        return False
    seen_wikimedia_titles = set()
    for asset in assets:
        if not isinstance(asset, dict):
            return False
        if not all(str(asset.get(field, "")).strip() for field in REQUIRED_STOCK_FIELDS):
            return False
        if asset.get("provider") == "wikimedia":
            if asset.get("query_matched") is not True:
                return False
            title = str(asset.get("title", ""))
            if title in seen_wikimedia_titles:
                return False
            seen_wikimedia_titles.add(title)
        path = str(asset.get("path", "")).strip()
        if path and not Path(path).is_file():
            return False
    return True


def has_publishable_visuals(visuals: object) -> bool:
    if not isinstance(visuals, dict):
        return False
    try:
        asset_count = int(visuals.get("asset_count", 0))
    except (TypeError, ValueError):
        return False
    mode = visuals.get("mode")
    if mode not in PUBLISHABLE_VISUAL_MODES or asset_count <= 0:
        return False
    if mode == "multi_shot_stock":
        if int(visuals.get("procedural_shot_count", 0)) != 0:
            return False
        if int(visuals.get("shot_count", asset_count)) != asset_count:
            return False
        return _assets_are_publishable(visuals)
    asset_path = visuals.get("asset_path")
    return isinstance(asset_path, str) and Path(asset_path).is_file()
