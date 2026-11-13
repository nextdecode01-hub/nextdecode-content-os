"""Regression coverage for the API's fail-closed bearer authentication."""

import pytest
from fastapi import HTTPException

from api import main as api_main


def test_api_refuses_requests_when_server_key_is_not_configured(monkeypatch):
    monkeypatch.delenv(api_main.API_KEY_ENV, raising=False)

    with pytest.raises(HTTPException) as caught:
        api_main.require_api_key("Bearer any-value")

    assert caught.value.status_code == 503
    assert caught.value.detail == "api_key_not_configured"


@pytest.mark.parametrize(
    "authorization",
    [
        None,
        "",
        "Basic configured-key",
        "Bearer",
        "Bearer ",
        "Bearer wrong-key",
    ],
)
def test_api_rejects_missing_malformed_or_incorrect_bearer_credentials(
    monkeypatch, authorization
):
    monkeypatch.setenv(api_main.API_KEY_ENV, "configured-key")

    with pytest.raises(HTTPException) as caught:
        api_main.require_api_key(authorization)

    assert caught.value.status_code == 401
    assert caught.value.detail == "unauthorized"


def test_api_accepts_case_insensitive_bearer_scheme_and_matching_key(monkeypatch):
    monkeypatch.setenv(api_main.API_KEY_ENV, "configured-key")

    assert api_main.require_api_key("bEaReR configured-key") is None


def test_all_state_and_generation_routes_use_api_key_dependency():
    protected_paths = {"/jobs", "/start", "/status/{job_id}", "/capabilities", "/tasks", "/tasks/{task_id}", "/plans", "/plans/{plan_id}", "/tool-catalog"}
    routes = {
        route.path: route
        for route in api_main.app.routes
        if hasattr(route, "dependant")
    }

    assert protected_paths <= routes.keys()
    for path in protected_paths:
        dependencies = routes[path].dependant.dependencies
        assert any(
            dependency.call is api_main.require_api_key
            for dependency in dependencies
        ), f"{path} is missing API-key authentication"


def test_health_route_remains_a_minimal_public_liveness_probe():
    health_route = next(
        route
        for route in api_main.app.routes
        if getattr(route, "path", None) == "/health"
    )

    assert not any(
        dependency.call is api_main.require_api_key
        for dependency in health_route.dependant.dependencies
    )
