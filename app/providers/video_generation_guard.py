"""Fail-closed authorization for optional paid video-generation APIs.

No provider call should be made before this guard authorizes a per-run request.
Default policy is zero budget and disabled. A future owner-approved run must
set an explicit approval flag, a positive USD cap and one supported route.
This module never initiates network requests or chooses a paid provider.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

DEFAULT_POLICY_PATH = Path(__file__).resolve().parents[2] / "config" / "video_generation_policy.v1.json"
SUPPORTED_ROUTES = frozenset({"direct_provider_apis", "unified_gateway"})


class VideoGenerationNotAuthorized(PermissionError):
    """Raised when paid video generation is not explicitly authorized."""


@dataclass(frozen=True)
class VideoGenerationAuthorization:
    route: str
    budget_usd: float
    approved: bool
    policy_status: str


def load_video_generation_policy(path: str | Path | None = None) -> dict:
    policy_path = Path(path) if path else DEFAULT_POLICY_PATH
    data = json.loads(policy_path.read_text(encoding="utf-8"))
    if data.get("schema") != "nextdecode.video-generation-policy.v1":
        raise ValueError("unsupported video-generation policy schema")
    return data


def authorize_video_generation(
    *,
    route: str,
    env: Mapping[str, str] | None = None,
    policy: dict | None = None,
) -> VideoGenerationAuthorization:
    """Authorize one provider run; deny by default and require a positive cap."""
    settings = policy or load_video_generation_policy()
    values = os.environ if env is None else env
    if route not in SUPPORTED_ROUTES:
        raise VideoGenerationNotAuthorized(f"unsupported video generation route: {route}")
    route_policy = (settings.get("routes") or {}).get(route) or {}
    if not route_policy.get("supported", False):
        raise VideoGenerationNotAuthorized(f"route is not supported by policy: {route}")
    if not route_policy.get("enabled", False) or not settings.get("enabled", False):
        raise VideoGenerationNotAuthorized("video generation is disabled by the zero-budget policy")
    approval_key = (settings.get("approval_environment") or {}).get(
        "approved_flag", "NEXTDECODE_VIDEO_GENERATION_APPROVED"
    )
    budget_key = (settings.get("approval_environment") or {}).get(
        "budget_usd", "NEXTDECODE_VIDEO_GENERATION_BUDGET_USD"
    )
    route_key = (settings.get("approval_environment") or {}).get(
        "allowed_route", "NEXTDECODE_VIDEO_GENERATION_ROUTE"
    )
    if values.get(approval_key) != "1":
        raise VideoGenerationNotAuthorized("explicit owner approval flag is missing")
    try:
        budget = float(values.get(budget_key, "0"))
    except (TypeError, ValueError):
        budget = 0.0
    if budget <= 0:
        raise VideoGenerationNotAuthorized("a positive per-run USD budget is required")
    if values.get(route_key) != route:
        raise VideoGenerationNotAuthorized("requested route does not match the explicitly approved route")
    return VideoGenerationAuthorization(
        route=route,
        budget_usd=budget,
        approved=True,
        policy_status=str(settings.get("status") or "approved"),
    )
