from __future__ import annotations
import pytest
from fastapi import HTTPException
from api import main as api_main

def test_task_api_enqueues_only_registered_capabilities(tmp_path, monkeypatch):
    monkeypatch.setenv(api_main.API_KEY_ENV, "test-api-key")
    monkeypatch.setenv("NEXTDECODE_TASK_DB", str(tmp_path / "tasks.sqlite3"))
    result = api_main.enqueue_task({
        "task_type": "content.short.generate",
        "payload": {"topic": "Autonomous systems", "dry_run": True},
        "idempotency_key": "api-test-1",
    })
    assert result["status"] == "queued"
    rows = api_main.list_autonomous_tasks()
    assert len(rows["tasks"]) == 1
    detail = api_main.get_autonomous_task(result["task_id"])
    assert detail["task"]["task_type"] == "content.short.generate"
    assert detail["events"][0]["event"] == "queued"

def test_task_api_rejects_arbitrary_commands(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXTDECODE_TASK_DB", str(tmp_path / "tasks.sqlite3"))
    with pytest.raises(HTTPException) as caught:
        api_main.enqueue_task({"task_type": "shell.exec", "payload": {"command": "rm -rf /"}})
    assert caught.value.status_code == 400

def test_task_api_rejects_unknown_fields():
    with pytest.raises(HTTPException) as caught:
        api_main.enqueue_task({"task_type": "content.short.generate", "command": "echo"})
    assert caught.value.status_code == 400


def test_plan_api_creates_safe_short_plan(tmp_path, monkeypatch):
    monkeypatch.setenv(api_main.API_KEY_ENV, "test-api-key")
    monkeypatch.setenv("NEXTDECODE_TASK_DB", str(tmp_path / "plans.sqlite3"))
    result = api_main.create_autonomous_plan({"goal": "Create a YouTube Short about agentic AI"})
    assert result["plan"]["human_approval_required"] is True
    assert result["plan"]["external_actions_allowed"] is False
    assert api_main.get_autonomous_plan(result["plan_id"])["status"] == "queued"


def test_plan_api_refuses_publication_and_unknown_fields():
    with pytest.raises(HTTPException) as caught:
        api_main.create_autonomous_plan({"goal": "Publish this video publicly"})
    assert caught.value.status_code == 422
    with pytest.raises(HTTPException) as caught:
        api_main.create_autonomous_plan({"goal": "Create a short", "shell": "echo unsafe"})
    assert caught.value.status_code == 400

from fastapi.testclient import TestClient

def test_authenticated_http_plan_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setenv(api_main.API_KEY_ENV, "test-http-key")
    monkeypatch.setenv("NEXTDECODE_TASK_DB", str(tmp_path / "http.sqlite3"))
    client = TestClient(api_main.app)
    denied = client.post("/plans", json={"goal": "Create a Short about AI"})
    assert denied.status_code == 401
    headers = {"Authorization": "Bearer test-http-key"}
    created = client.post("/plans", headers=headers,
                          json={"goal": "Create a YouTube Short about AI agents",
                                "idempotency_key": "http-plan-1"})
    assert created.status_code == 202
    plan_id = created.json()["plan_id"]
    fetched = client.get(f"/plans/{plan_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "queued"
    tasks = fetched.json()["tasks"]
    research = next(task for task in tasks if task["task_type"] == "research.topic.collect")
    draft = next(task for task in tasks if task["task_type"] == "content.short.script.draft")
    assert research["task_id"] in draft["depends_on"]
    catalog = client.get("/tool-catalog?capability=browser-automation", headers=headers)
    assert catalog.status_code == 200
    assert catalog.json()["candidates"][0]["id"] == "playwright"


def test_start_endpoint_rejects_unauthenticated_requests(monkeypatch):
    monkeypatch.setenv(api_main.API_KEY_ENV, "test-start-key")
    response = TestClient(api_main.app).post("/start", json={"topic": "test"})
    assert response.status_code == 401


def test_authenticated_autonomy_health_and_dead_letters(monkeypatch):
    monkeypatch.setenv(api_main.API_KEY_ENV, "test-health-key")

    class FakeStore:
        def health(self):
            return {"database": "postgresql", "database_accessible": True, "active_workers": 1}

        def dead_letters(self, limit):
            return [{"task_id": "failed-task", "status": "failed"}]

    monkeypatch.setattr(api_main, "_task_store", lambda: FakeStore())
    client = TestClient(api_main.app)
    headers = {"Authorization": "Bearer test-health-key"}
    assert client.get("/autonomy/health").status_code == 401
    health = client.get("/autonomy/health", headers=headers)
    assert health.status_code == 200
    assert health.json()["database"] == "postgresql"
    dead = client.get("/autonomy/dead-letters?limit=5", headers=headers)
    assert dead.status_code == 200
    assert dead.json()["dead_letters"][0]["task_id"] == "failed-task"



def test_csv_specialist_is_available_through_authenticated_task_api(tmp_path, monkeypatch):
    monkeypatch.setenv(api_main.API_KEY_ENV, "test-csv-api-key")
    monkeypatch.setenv("NEXTDECODE_TASK_DB", str(tmp_path / "csv.sqlite3"))
    result = api_main.enqueue_task({
        "task_type": "data.csv.profile",
        "payload": {"csv_text": "views,likes\n10,2\n20,4\n"},
    })
    assert result["status"] == "queued"
    assert result["task_type"] == "data.csv.profile"
    with pytest.raises(HTTPException) as caught:
        api_main.enqueue_task({
            "task_type": "data.csv.profile",
            "payload": {"csv_text": "value,value\n1,2\n"},
        })
    assert caught.value.status_code == 400
