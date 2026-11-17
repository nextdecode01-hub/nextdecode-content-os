import json
import pytest

from app.providers.video_generation_guard import (
    VideoGenerationNotAuthorized,
    authorize_video_generation,
    load_video_generation_policy,
)


def test_default_policy_is_zero_budget_and_both_routes_disabled():
    policy = load_video_generation_policy()
    assert policy["enabled"] is False
    assert policy["default_budget_usd"] == 0
    assert policy["routes"]["direct_provider_apis"]["supported"] is True
    assert policy["routes"]["unified_gateway"]["supported"] is True
    assert policy["routes"]["direct_provider_apis"]["enabled"] is False
    assert policy["routes"]["unified_gateway"]["enabled"] is False


@pytest.mark.parametrize("route", ["direct_provider_apis", "unified_gateway"])
def test_paid_generation_is_denied_under_current_zero_budget_policy(route):
    with pytest.raises(VideoGenerationNotAuthorized, match="disabled"):
        authorize_video_generation(route=route, env={})


def test_invalid_route_fails_closed():
    with pytest.raises(VideoGenerationNotAuthorized, match="unsupported"):
        authorize_video_generation(route="random_gateway", env={})


def test_even_future_enabled_policy_requires_explicit_approval_and_budget():
    policy = load_video_generation_policy()
    policy["enabled"] = True
    policy["routes"]["direct_provider_apis"]["enabled"] = True
    with pytest.raises(VideoGenerationNotAuthorized, match="approval"):
        authorize_video_generation(route="direct_provider_apis", env={}, policy=policy)


def test_future_approved_route_requires_positive_budget_and_route_match():
    policy = load_video_generation_policy()
    policy["enabled"] = True
    policy["routes"]["direct_provider_apis"]["enabled"] = True
    approval_env = {
        "NEXTDECODE_VIDEO_GENERATION_APPROVED": "1",
        "NEXTDECODE_VIDEO_GENERATION_BUDGET_USD": "2.50",
        "NEXTDECODE_VIDEO_GENERATION_ROUTE": "direct_provider_apis",
    }
    approved = authorize_video_generation(route="direct_provider_apis", env=approval_env, policy=policy)
    assert approved.approved is True
    assert approved.budget_usd == 2.5
    with pytest.raises(VideoGenerationNotAuthorized, match="route"):
        authorize_video_generation(
            route="unified_gateway",
            env={**approval_env, "NEXTDECODE_VIDEO_GENERATION_ROUTE": "direct_provider_apis"},
            policy={**policy, "routes": {
                **policy["routes"],
                "unified_gateway": {"supported": True, "enabled": True},
            }},
        )
