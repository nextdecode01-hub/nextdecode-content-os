import pytest

from app.providers import video_generation as vg
from app.providers.video_generation_guard import VideoGenerationNotAuthorized


class Response:
    def __init__(self, body):
        self._body = body
    def raise_for_status(self):
        return None
    def json(self):
        return self._body


class Session:
    def __init__(self, post_body=None, get_body=None):
        self.post_body = post_body or {}
        self.get_body = get_body or {}
        self.posts = []
        self.gets = []
    def post(self, url, **kwargs):
        self.posts.append((url, kwargs))
        return Response(self.post_body)
    def get(self, url, **kwargs):
        self.gets.append((url, kwargs))
        return Response(self.get_body)


def test_kling_create_task_normalizes_response(monkeypatch):
    monkeypatch.setattr(vg, "authorize_video_generation", lambda **kwargs: True)
    session = Session(post_body={"data": {"id": "task-1", "status": "submitted"}})
    provider = vg.KlingVideoProvider(api_key="test-key", session=session)
    result = provider.create_text_to_video("A cinematic data center", duration=5)
    assert result["task_id"] == "task-1"
    assert session.posts[0][0].endswith("/text-to-video/kling-2.5-turbo")
    assert session.posts[0][1]["json"]["settings"]["aspect_ratio"] == "9:16"


def test_kling_status_uses_tasks_query_and_extracts_video(monkeypatch):
    session = Session(get_body={"data": [{"id": "task-1", "status": "succeeded",
        "outputs": [{"type": "video", "url": "https://cdn.example/video.mp4"}]}]})
    provider = vg.KlingVideoProvider(api_key="test-key", session=session)
    result = provider.get_task("task-1")
    assert result["status"] == "completed"
    assert result["video_url"] == "https://cdn.example/video.mp4"
    assert "task_ids=task-1" in session.gets[0][0]


def test_kling_creation_is_guarded_before_network(monkeypatch):
    def deny(**kwargs):
        raise VideoGenerationNotAuthorized("disabled")
    monkeypatch.setattr(vg, "authorize_video_generation", deny)
    session = Session()
    provider = vg.KlingVideoProvider(api_key="test-key", session=session)
    with pytest.raises(VideoGenerationNotAuthorized):
        provider.create_text_to_video("prompt")
    assert session.posts == []


def test_runway_uses_official_api_version_and_task_path(monkeypatch):
    monkeypatch.setattr(vg, "authorize_video_generation", lambda **kwargs: True)
    session = Session(post_body={"id": "uuid-1"}, get_body={"id": "uuid-1", "status": "SUCCEEDED",
        "output": ["https://cdn.example/out.mp4"]})
    provider = vg.RunwayVideoProvider(api_key="test-key", session=session)
    created = provider.create_text_to_video("A server room", duration=5)
    assert created["task_id"] == "uuid-1"
    assert session.posts[0][0].endswith("/v1/text_to_video")
    assert session.posts[0][1]["headers"]["X-Runway-Version"] == "2024-11-06"
    status = provider.get_task("uuid-1")
    assert status["video_url"] == "https://cdn.example/out.mp4"
