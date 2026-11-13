"""Task 1 acceptance tests for run_tracker.py (Phase 10.4 core).

All tests inject temporary directories — nothing touches real project
data/ or outputs/ paths.  Timestamps are injected for determinism.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.tracking import run_tracker as rt

NOW = datetime(2026, 10, 31, 14, 22, 33, tzinfo=timezone.utc)


# ---------------------------------------------------------------- run IDs

def test_run_id_format(tmp_path: Path) -> None:
    run_id = rt.generate_run_id("NIST AI RMF Explained: What Enterprises Need", now=NOW)
    assert run_id == "20261031-142233-nist-ai-rmf-explained-what-enterprises-n"


def test_run_id_empty_topic_falls_back_to_manual(tmp_path: Path) -> None:
    assert rt.generate_run_id("", now=NOW) == "20261031-142233-manual"


def test_run_id_naive_datetime_treated_as_utc() -> None:
    naive = datetime(2026, 10, 31, 14, 22, 33)
    assert rt.generate_run_id("x", now=naive) == "20261031-142233-x"


# ------------------------------------------------------------ collisions

def test_same_timestamp_collision_gets_numeric_suffix(tmp_path: Path) -> None:
    first = rt.start_run("dup", runs_root=tmp_path / "runs", index_path=tmp_path / "index.jsonl", now=NOW)
    second = rt.start_run("dup", runs_root=tmp_path / "runs", index_path=tmp_path / "index.jsonl", now=NOW)

    assert first.run_dir.name == "20261031-142233-dup"
    assert second.run_dir.name == "20261031-142233-dup-1"
    assert second.run_dir.name != first.run_dir.name
    assert first.run_dir.is_dir() and second.run_dir.is_dir()


def test_three_way_collision_suffixes(tmp_path: Path) -> None:
    ids = [
        rt.start_run("c", runs_root=tmp_path / "runs", index_path=tmp_path / "i.jsonl", now=NOW).run_dir.name
        for _ in range(3)
    ]
    assert ids == ["20261031-142233-c", "20261031-142233-c-1", "20261031-142233-c-2"]


# ------------------------------------------------------ manifest lifecycle

def test_initial_manifest_is_in_progress(tmp_path: Path) -> None:
    tracker = rt.start_run("topic a", runs_root=tmp_path / "runs", index_path=tmp_path / "i.jsonl", now=NOW)
    manifest = json.loads((tracker.run_dir / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "in_progress"
    assert manifest["failure"] is None
    assert manifest["finished_at"] is None
    assert manifest["artifacts"] == {}
    assert manifest["started_at"] == "2026-10-31T14:22:33+00:00"


def test_mark_ok_transitions_and_finishes(tmp_path: Path) -> None:
    end = datetime(2026, 10, 31, 14, 25, 0, tzinfo=timezone.utc)
    tracker = rt.start_run("t", runs_root=tmp_path / "runs", index_path=tmp_path / "i.jsonl", now=NOW)
    tracker.mark_ok(finished_at=end)
    manifest = json.loads((tracker.run_dir / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "ok"
    assert manifest["finished_at"] == "2026-10-31T14:25:00+00:00"
    assert manifest["failure"] is None


def test_terminal_state_is_immutable(tmp_path: Path) -> None:
    tracker = rt.start_run("t", runs_root=tmp_path / "runs", index_path=tmp_path / "i.jsonl", now=NOW)
    tracker.mark_ok()

    with pytest.raises(RuntimeError):
        tracker.mark_ok()
    with pytest.raises(RuntimeError):
        tracker.mark_failed(stage="voice")


# --------------------------------------------------------------- artifacts

def test_record_artifact_hashes_and_sizes(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    tracker = rt.start_run("t", runs_root=runs, index_path=tmp_path / "i.jsonl", now=NOW)
    artifact = tracker.run_dir / "voice.mp3"
    payload = b"\x00\x01 artificial voice bytes"
    artifact.write_bytes(payload)

    entry = tracker.record_artifact("voice", artifact, stage="voice")

    expected_hash = hashlib.sha256(payload).hexdigest()
    assert entry["sha256"] == expected_hash
    assert entry["bytes"] == len(payload)
    assert entry["stage"] == "voice"
    manifest = json.loads((tracker.run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["artifacts"]["voice"]["path"] == "voice.mp3"


def test_record_artifact_missing_file_raises(tmp_path: Path) -> None:
    tracker = rt.start_run("t", runs_root=tmp_path / "runs", index_path=tmp_path / "i.jsonl", now=NOW)
    with pytest.raises(RuntimeError, match="artifact not found"):
        tracker.record_artifact("ghost", tracker.run_dir / "missing.mp4")


def test_record_stage_appends(tmp_path: Path) -> None:
    tracker = rt.start_run("t", runs_root=tmp_path / "runs", index_path=tmp_path / "i.jsonl", now=NOW)
    tracker.record_stage("research", started_at="2026-10-31T14:22:34+00:00",
                         finished_at="2026-10-31T14:24:02+00:00")
    manifest = json.loads((tracker.run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["stages"] == [{
        "name": "research",
        "started_at": "2026-10-31T14:22:34+00:00",
        "finished_at": "2026-10-31T14:24:02+00:00",
        "status": "ok",
    }]


# ----------------------------------------------------------------- failure

def test_mark_failed_writes_sanitized_failure_json(tmp_path: Path) -> None:
    tracker = rt.start_run("t", runs_root=tmp_path / "runs", index_path=tmp_path / "i.jsonl", now=NOW)

    class Boom(RuntimeError):
        pass

    exc = Boom("secret sk_live_ABCDEF123456 leaked in message https://api.example.com?token=xyz")
    tracker.mark_failed(stage="voice", exc=exc, error_category="voice")

    failure = json.loads((tracker.run_dir / "failure.json").read_text(encoding="utf-8"))
    assert failure["error_type"] == "Boom"
    assert failure["error_category"] == "voice"
    assert failure["stage"] == "voice"
    # Sanitization: the raw message must not appear anywhere.
    blob = json.dumps(failure)
    assert "sk_live" not in blob and "token" not in blob and "api.example.com" not in blob

    manifest = json.loads((tracker.run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "failed"
    assert manifest["failure"]["error_type"] == "Boom"


def test_unknown_category_is_normalized(tmp_path: Path) -> None:
    tracker = rt.start_run("t", runs_root=tmp_path / "runs", index_path=tmp_path / "i.jsonl", now=NOW)
    tracker.mark_failed(stage="voice", error_category="???")
    manifest = json.loads((tracker.run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["failure"]["error_category"] == "unknown"


# ------------------------------------------------------------------- index

def test_index_jsonl_append_only(tmp_path: Path) -> None:
    index_path = tmp_path / "index.jsonl"
    first = rt.start_run("one", runs_root=tmp_path / "runs", index_path=index_path, now=NOW)
    first.mark_ok()
    second = rt.start_run("two", runs_root=tmp_path / "runs", index_path=index_path, now=NOW)
    second.mark_failed(stage="render")

    lines = [json.loads(line) for line in index_path.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 2
    assert lines[0]["run_id"] == first.run_id and lines[0]["status"] == "ok"
    assert lines[1]["run_id"] == second.run_id
    assert lines[1]["status"] == "failed"
    assert lines[1]["failure_stage"] == "render"
    assert lines[0]["failure_stage"] is None  # successful records carry no failure keys


def test_failed_run_does_not_modify_existing_index_lines(tmp_path: Path) -> None:
    index_path = tmp_path / "index.jsonl"
    a = rt.start_run("a", runs_root=tmp_path / "runs", index_path=index_path, now=NOW)
    a.mark_ok()
    before = index_path.read_text(encoding="utf-8")
    b = rt.start_run("b", runs_root=tmp_path / "runs", index_path=index_path, now=NOW)
    b.mark_failed(stage="script")

    assert index_path.read_text(encoding="utf-8").startswith(before)


# ----------------------------------------------------- malformed / fs errors

def test_corrupt_manifest_loads_with_clear_error(tmp_path: Path) -> None:
    tracker = rt.start_run("t", runs_root=tmp_path / "runs", index_path=tmp_path / "i.jsonl", now=NOW)
    (tracker.run_dir / "manifest.json").write_text("{ not json !!!", encoding="utf-8")

    with pytest.raises(RuntimeError, match="corrupt manifest"):
        rt.load_manifest(tracker.run_dir)


def test_manifest_missing_run_id_is_malformed(tmp_path: Path) -> None:
    tracker = rt.start_run("t", runs_root=tmp_path / "runs", index_path=tmp_path / "i.jsonl", now=NOW)
    (tracker.run_dir / "manifest.json").write_text('{"status": "ok"}', encoding="utf-8")

    with pytest.raises(RuntimeError, match="malformed manifest"):
        rt.load_manifest(tracker.run_dir)


def test_runs_root_path_is_a_file_raises_untouched(tmp_path: Path) -> None:
    blocker = tmp_path / "not_a_dir"
    blocker.write_text("i am a file", encoding="utf-8")

    with pytest.raises(OSError):
        rt.start_run("t", runs_root=blocker, index_path=tmp_path / "i.jsonl", now=NOW)


def test_missing_manifest_raises(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="manifest not found"):
        rt.load_manifest(tmp_path / "no_such_run")


# ----------------------------------------------------------- non-integration

def test_nothing_written_outside_injected_paths(tmp_path: Path) -> None:
    """The tracker must not touch real project outputs — only injected dirs."""
    rt.start_run("t", runs_root=tmp_path / "runs", index_path=tmp_path / "i.jsonl", now=NOW)
    assert rt.DEFAULT_RUNS_ROOT == rt.ROOT / "outputs" / "runs"
    assert rt.DEFAULT_INDEX_PATH == rt.ROOT / "data" / "runs" / "index.jsonl"
    assert {p.name for p in tmp_path.iterdir()} == {"runs"}  # index only appears after a terminal lifecycle event


# --------------------------------------------------- owner-approved hardening

def test_manifest_has_schema_version(tmp_path: Path) -> None:
    tracker = rt.start_run("t", runs_root=tmp_path / "runs", index_path=tmp_path / "i.jsonl", now=NOW)
    manifest = json.loads((tracker.run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1


def test_artifact_outside_run_dir_rejected(tmp_path: Path) -> None:
    tracker = rt.start_run("t", runs_root=tmp_path / "runs", index_path=tmp_path / "i.jsonl", now=NOW)
    outside = tmp_path / "outside.mp4"
    outside.write_bytes(b"boundary")
    manifest = json.loads((tracker.run_dir / "manifest.json").read_text(encoding="utf-8"))

    with pytest.raises(RuntimeError, match="escapes the run directory"):
        tracker.record_artifact("external", outside)

    # Rejection must leave the manifest unchanged.
    after = json.loads((tracker.run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert after == manifest


def test_symlink_escape_rejected(tmp_path: Path) -> None:
    tracker = rt.start_run("t", runs_root=tmp_path / "runs", index_path=tmp_path / "i.jsonl", now=NOW)
    outside = tmp_path / "secret_asset.mp4"
    outside.write_bytes(b"outside content")
    link = tracker.run_dir / "linked.mp4"
    try:
        link.symlink_to(outside)
    except OSError:  # symlink privilege may be unavailable on some filesystems
        pytest.skip("symlinks unavailable in this environment")

    with pytest.raises(RuntimeError, match="escapes the run directory"):
        tracker.record_artifact("linked", link)


def test_symlink_resolving_inside_run_dir_allowed_and_stored_relative(tmp_path: Path) -> None:
    tracker = rt.start_run("t", runs_root=tmp_path / "runs", index_path=tmp_path / "i.jsonl", now=NOW)
    real = tracker.run_dir / "shots"
    real.mkdir()
    target = real / "shot_000.mp4"
    target.write_bytes(b"inside")
    link = tracker.run_dir / "alias.mp4"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlinks unavailable in this environment")

    entry = tracker.record_artifact("alias", link)
    assert entry["path"] == "shots/shot_000.mp4"


def test_duplicate_artifact_name_rejected(tmp_path: Path) -> None:
    tracker = rt.start_run("t", runs_root=tmp_path / "runs", index_path=tmp_path / "i.jsonl", now=NOW)
    artifact = tracker.run_dir / "voice.mp3"
    artifact.write_bytes(b"first recording")
    tracker.record_artifact("voice", artifact, stage="voice")
    second = tracker.run_dir / "voice2.mp3"
    second.write_bytes(b"second recording")

    with pytest.raises(RuntimeError, match="already recorded"):
        tracker.record_artifact("voice", second, stage="replace-attempt")

    manifest = json.loads((tracker.run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["artifacts"]["voice"]["path"] == "voice.mp3"  # original preserved


def test_interrupted_run_identification_states(tmp_path: Path) -> None:
    """Documented recovery rule (no automatic recovery): in_progress states."""
    index_path = tmp_path / "i.jsonl"
    # State A: interrupted/unknown — in_progress, no failure.json
    a = rt.start_run("interrupted", runs_root=tmp_path / "runs", index_path=index_path, now=NOW)
    a_manifest = rt.load_manifest(a.run_dir)
    assert a_manifest["status"] == "in_progress"
    assert not (a.run_dir / "failure.json").exists()

    # State B: failure recorded, manifest finalization incomplete (simulated crash
    # between failure.json write and manifest write inside mark_failed)
    b = rt.start_run("crashed_mid_failure", runs_root=tmp_path / "runs", index_path=index_path, now=NOW)
    (b.run_dir / "failure.json").write_text(json.dumps({
        "run_id": b.run_id, "stage": "voice", "error_type": "Boom", "error_category": "voice",
    }), encoding="utf-8")
    b_manifest = rt.load_manifest(b.run_dir)
    assert b_manifest["status"] == "in_progress"
    assert (b.run_dir / "failure.json").exists()

    # States C/D: terminal — failed and ok are distinct and unambiguous.
    c = rt.start_run("terminal_fail", runs_root=tmp_path / "runs", index_path=index_path, now=NOW)
    c.mark_failed(stage="render")
    d = rt.start_run("terminal_ok", runs_root=tmp_path / "runs", index_path=index_path, now=NOW)
    d.mark_ok()
    assert rt.load_manifest(c.run_dir)["status"] == "failed"
    assert (c.run_dir / "failure.json").exists()
    assert rt.load_manifest(d.run_dir)["status"] == "ok"
    assert not (d.run_dir / "failure.json").exists()


def test_sha256_consistency_file_larger_than_2mb(tmp_path: Path) -> None:
    tracker = rt.start_run("t", runs_root=tmp_path / "runs", index_path=tmp_path / "i.jsonl", now=NOW)
    payload = os.urandom(2 * 1024 * 1024 + 7)  # > 2 MB, odd tail for the chunk loop
    artifact = tracker.run_dir / "background.mp4"
    artifact.write_bytes(payload)

    entry = tracker.record_artifact("background", artifact, stage="render")

    assert entry["sha256"] == hashlib.sha256(payload).hexdigest()
    assert entry["bytes"] == len(payload)
