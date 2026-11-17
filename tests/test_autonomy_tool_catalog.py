from app.autonomy.tool_catalog import list_capabilities, rank_candidates

def test_tool_catalog_returns_ranked_replaceable_candidates():
    candidates = rank_candidates("browser-automation")
    assert [candidate["id"] for candidate in candidates] == ["playwright", "selenium"]
    assert candidates[1]["replacement_for"] == "playwright"
    assert candidates[0]["status"] == "candidate"

def test_tool_catalog_does_not_mark_external_research_as_default():
    candidates = rank_candidates("research")
    assert candidates[0]["status"] == "active"
    assert candidates[1]["status"] == "approval-required"
    assert candidates[1]["requires_approval"] is True

def test_tool_catalog_exposes_no_implicit_install_or_execution():
    assert "task-storage" in list_capabilities()
    assert "workflow-engine" in list_capabilities()
    assert "document-extraction" in list_capabilities()
    assert "data-analysis" in list_capabilities()
    all_candidates = [
        candidate for cap in list_capabilities() for candidate in rank_candidates(cap)
    ]
    assert len({candidate["id"] for candidate in all_candidates}) == len(all_candidates)
    assert all(candidate["status"] != "installed" for candidate in all_candidates)


def test_postgresql_is_primary_and_managed_alternatives_require_approval():
    candidates = rank_candidates("task-storage")
    assert candidates[0]["id"] == "nextdecode-postgresql-autonomy"
    assert candidates[0]["status"] == "active-local-runtime"
    assert candidates[1]["id"] == "nextdecode-sqlite-worker"
    assert candidates[1]["status"] == "fallback-candidate"
    assert candidates[2]["requires_approval"] is True
    assert candidates[3]["requires_approval"] is True
    workflow = rank_candidates("workflow-engine")
    assert workflow[0]["id"] == "nextdecode-autonomy-core"
    assert workflow[0]["status"] == "active-local-runtime"
    assert [candidate["id"] for candidate in workflow[1:]] == [
        "temporal-self-hosted", "celery", "dramatiq"
    ]
    assert rank_candidates("scheduling")[0]["id"] == "apscheduler"


def test_api_catalog_endpoint_returns_ranked_candidates():
    from api.main import get_tool_catalog
    result = get_tool_catalog("browser-automation")
    assert result["candidates"][0]["id"] == "playwright"
    assert result["candidates"][1]["replacement_for"] == "playwright"


def test_editorial_alternatives_are_candidates_not_implicitly_active():
    renderers = rank_candidates("editorial-rendering")
    assert [item["id"] for item in renderers] == ["ffmpeg", "gstreamer", "moviepy"]
    assert renderers[0]["status"] == "active"
    assert all(item["status"] == "candidate" for item in renderers[1:])
    assert renderers[1]["replacement_for"] == "ffmpeg"
    assert renderers[2]["replacement_for"] == "ffmpeg"

    visual = rank_candidates("editorial-visual-analysis")
    assert visual[0]["id"] == "opencv"
    assert visual[0]["status"] == "candidate"

    speech = rank_candidates("speech-synthesis")
    assert speech[0]["id"] == "piper-tts"
    assert speech[0]["status"] == "approval-required"
    assert speech[0]["requires_approval"] is True
