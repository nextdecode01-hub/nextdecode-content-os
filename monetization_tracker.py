#!/usr/bin/env python3
"""Track YouTube monetization progress without storing credentials."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "data" / "monetization_progress.json"

DEFAULT = {
    "checked_at": None,
    "source": "YouTube Studio > Earn",
    "subscribers": 0,
    "valid_public_uploads_90d": 0,
    "qualified_shorts_views_90d": 0,
    "qualified_longform_watch_hours_365d": 0,
    "two_step_verification": False,
    "advanced_features": False,
    "adsense_ready": False,
    "policy_notes": "",
}

def load() -> dict:
    if not STATE.exists():
        return dict(DEFAULT)
    value = json.loads(STATE.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit("monetization_progress.json must contain an object")
    result = dict(DEFAULT)
    result.update(value)
    return result

def pct(value: float, target: float) -> int:
    return min(100, round((value / target) * 100)) if target else 0

def report(value: dict) -> dict:
    subscribers = max(0, int(value.get("subscribers", 0)))
    shorts = max(0, int(value.get("qualified_shorts_views_90d", 0)))
    hours = max(0.0, float(value.get("qualified_longform_watch_hours_365d", 0)))
    uploads = max(0, int(value.get("valid_public_uploads_90d", 0)))
    expanded = {
        "subscribers": {"current": subscribers, "target": 500, "percent": pct(subscribers, 500), "gap": max(0, 500 - subscribers)},
        "shorts_views": {"current": shorts, "target": 3_000_000, "percent": pct(shorts, 3_000_000), "gap": max(0, 3_000_000 - shorts)},
        "longform_watch_hours": {"current": hours, "target": 3_000, "percent": pct(hours, 3_000), "gap": max(0, 3_000 - hours)},
        "valid_public_uploads": {"current": uploads, "target": 3, "percent": pct(uploads, 3), "gap": max(0, 3 - uploads)},
    }
    ads = {
        "subscribers": {"current": subscribers, "target": 1_000, "percent": pct(subscribers, 1_000), "gap": max(0, 1_000 - subscribers)},
        "shorts_views": {"current": shorts, "target": 10_000_000, "percent": pct(shorts, 10_000_000), "gap": max(0, 10_000_000 - shorts)},
        "longform_watch_hours": {"current": hours, "target": 4_000, "percent": pct(hours, 4_000), "gap": max(0, 4_000 - hours)},
    }
    expanded_ready = subscribers >= 500 and uploads >= 3 and (shorts >= 3_000_000 or hours >= 3_000)
    ads_ready = subscribers >= 1_000 and (shorts >= 10_000_000 or hours >= 4_000)
    return {"expanded_ypp": {"ready_by_metrics": expanded_ready, "metrics": expanded}, "ads_revenue": {"ready_by_metrics": ads_ready, "metrics": ads}, "account_readiness": {k: bool(value.get(k)) for k in ("two_step_verification", "advanced_features", "adsense_ready")}}

def main() -> int:
    parser = argparse.ArgumentParser(description="Update or report monetization progress")
    parser.add_argument("command", choices=("show", "update"))
    parser.add_argument("--subscribers", type=int)
    parser.add_argument("--uploads-90d", type=int)
    parser.add_argument("--shorts-views-90d", type=int)
    parser.add_argument("--watch-hours-365d", type=float)
    parser.add_argument("--two-step", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--advanced-features", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--adsense-ready", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--policy-notes", default=None)
    args = parser.parse_args()
    value = load()
    if args.command == "update":
        for attr, key in (("subscribers", "subscribers"), ("uploads_90d", "valid_public_uploads_90d"), ("shorts_views_90d", "qualified_shorts_views_90d"), ("watch_hours_365d", "qualified_longform_watch_hours_365d"), ("two_step", "two_step_verification"), ("advanced_features", "advanced_features"), ("adsense_ready", "adsense_ready"), ("policy_notes", "policy_notes")):
            current = getattr(args, attr)
            if current is not None:
                value[key] = current
        value["checked_at"] = datetime.now(timezone.utc).isoformat()
        STATE.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    output = {"snapshot": value, "progress": report(value)}
    print(json.dumps(output, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

