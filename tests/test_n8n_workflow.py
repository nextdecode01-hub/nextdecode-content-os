import json
from pathlib import Path


def test_compose_workflow_keeps_schedules_and_routes_to_runner():
    workflow_path = Path(__file__).resolve().parents[1] / "workflow_n8n_approved_schedule.json"
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    nodes = {node["name"]: node for node in workflow["nodes"]}

    assert workflow["settings"]["timezone"] == "Asia/Kolkata"
    assert "Generate and Queue Daily Content (12:00 IST)" in nodes
    assert "Check Owner-Approved Uploads (20:00 IST)" in nodes
    assert not any(node["type"] == "n8n-nodes-base.executeCommand" for node in nodes.values())

    request_nodes = {
        node["name"]: node
        for node in nodes.values()
        if node["type"] == "n8n-nodes-base.httpRequest"
    }
    assert set(request_nodes) == {
        "Run Secure Generation Pipeline (Review Only)",
        "Run Approval-Gated Publisher",
    }
    assert {
        node["parameters"]["url"] for node in request_nodes.values()
    } == {
        "http://studio-runner:8080/run/generate",
        "http://studio-runner:8080/run/publish",
    }
    for node in request_nodes.values():
        headers = node["parameters"]["headerParameters"]["parameters"]
        assert any(
            header["name"] == "Authorization"
            and "$env.N8N_RUNNER_API_KEY" in header["value"]
            for header in headers
        )
        assert node["parameters"]["options"]["timeout"] == 14_400_000

    valid_names = set(nodes)
    for source, connections in workflow["connections"].items():
        assert source in valid_names
        for output in connections["main"]:
            assert all(connection["node"] in valid_names for connection in output)
