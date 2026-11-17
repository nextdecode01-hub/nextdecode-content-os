import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from api import main as api_main


class FakeStore:
    def __init__(self):
        self.event_calls = []
        self.recent_calls = []
        self.stuck_calls = []
        self.list_calls = []

    def event_feed(self, after_event_id=0, limit=100):
        self.event_calls.append((after_event_id, limit))
        rows = [{"event_id": i, "task_id": f"task-{i}", "at": "2026-11-14T10:00:00+00:00",
                 "event": "queued", "detail_json": "{}"} for i in range(1, 81)]
        return [row for row in rows if row["event_id"] > after_event_id][:limit]

    def recent_event_feed(self, limit=100):
        self.recent_calls.append(limit)
        return [{"event_id": i, "task_id": f"task-{i}", "at": "2026-11-14T10:00:00+00:00",
                 "event": "queued", "detail_json": "{}"} for i in range(81-limit, 81)]

    def stuck_tasks(self, stale_after_seconds=120, limit=100):
        self.stuck_calls.append((stale_after_seconds, limit))
        return [{"task_id": "task-stuck", "task_type": "research.topic.collect",
                 "lease_owner": "worker-a", "lease_until": None, "attempts": 1,
                 "updated_at": "2026-11-14T10:00:00+00:00",
                 "last_execution_heartbeat": None}][:limit]

    def list(self, limit=100):
        self.list_calls.append(limit)
        return [{"task_id": "task-a"}]


@pytest.fixture
def fake_store(monkeypatch):
    store = FakeStore()
    monkeypatch.setattr(api_main, "_task_store", lambda: store)
    return store


def test_event_feed_zero_cursor_returns_recent_window(fake_store):
    result = api_main.autonomy_event_feed(after_event_id=0, limit=12)
    assert len(result["events"]) == 12
    assert result["events"][0]["event_id"] == 69
    assert result["events"][-1]["event_id"] == 80
    assert result["next_after_event_id"] == 80
    assert fake_store.recent_calls == [12]


def test_event_feed_nonzero_cursor_is_forward_only(fake_store):
    result = api_main.autonomy_event_feed(after_event_id=75, limit=3)
    assert [event["event_id"] for event in result["events"]] == [76, 77, 78]
    assert result["next_after_event_id"] == 78
    assert fake_store.event_calls == [(75, 3)]


def test_event_feed_rejects_negative_cursor():
    with pytest.raises(HTTPException) as caught:
        api_main.autonomy_event_feed(after_event_id=-1, limit=10)
    assert caught.value.status_code == 400


def test_stuck_tasks_is_bounded_and_read_only(fake_store):
    result = api_main.autonomy_stuck_tasks(stale_after_seconds=99999, limit=999)
    assert result["stale_after_seconds"] == 3600
    assert fake_store.stuck_calls == [(3600, 500)]
    assert result["stuck_tasks"][0]["task_id"] == "task-stuck"


@pytest.mark.parametrize("value", [0, -1])
def test_stuck_tasks_rejects_nonpositive_staleness(value):
    with pytest.raises(HTTPException) as caught:
        api_main.autonomy_stuck_tasks(stale_after_seconds=value, limit=10)
    assert caught.value.status_code == 400


def test_task_list_uses_bounded_store_limit(fake_store):
    result = api_main.list_autonomous_tasks(limit=999)
    assert result["limit"] == 500
    assert fake_store.list_calls == [500]


def test_new_observability_routes_require_bearer_authentication():
    protected = {"/autonomy/events", "/autonomy/stuck-tasks"}
    routes = {route.path: route for route in api_main.app.routes if hasattr(route, "dependant")}
    assert protected <= routes.keys()
    for path in protected:
        assert any(dep.call is api_main.require_api_key for dep in routes[path].dependant.dependencies)


def test_observability_http_routes_enforce_auth_and_return_bounded_data(monkeypatch, fake_store):
    monkeypatch.setenv(api_main.API_KEY_ENV, "test-dashboard-key")
    client = TestClient(api_main.app)

    denied = client.get("/autonomy/events")
    assert denied.status_code == 401

    headers = {"Authorization": "Bearer test-dashboard-key"}
    events = client.get("/autonomy/events?limit=5", headers=headers)
    assert events.status_code == 200
    assert len(events.json()["events"]) == 5
    assert events.json()["next_after_event_id"] == 80

    stuck = client.get("/autonomy/stuck-tasks?stale_after_seconds=120&limit=10", headers=headers)
    assert stuck.status_code == 200
    assert stuck.json()["stuck_tasks"][0]["task_id"] == "task-stuck"

    tasks = client.get("/tasks?limit=999", headers=headers)
    assert tasks.status_code == 200
    assert tasks.json()["limit"] == 500
