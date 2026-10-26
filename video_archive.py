from __future__ import annotations

import os
import re
import shutil
from datetime import datetime
from pathlib import Path


def _archive_root(project_root: Path) -> Path:
    configured = os.getenv("VIDEO_ARCHIVE_DIR", "").strip()
    if configured:
        archive_root = Path(configured).expanduser()
        return archive_root if archive_root.is_absolute() else project_root / archive_root

    drive_root = Path("D:/") if os.name == "nt" else Path("/mnt/d")
    if drive_root.is_dir():
        return drive_root / "ShortsStudioVideos"
    return project_root / "videos"


def archive_video(
    video_path: Path,
    metadata_path: Path,
    project_root: Path,
    media_type: str,
    title: str,
) -> Path:
    if media_type not in {"shorts", "longform"}:
        raise ValueError("media_type must be 'shorts' or 'longform'.")
    if not video_path.is_file():
        raise FileNotFoundError(f"Video to archive does not exist: {video_path}")
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Video metadata to archive does not exist: {metadata_path}")

    now = datetime.now().astimezone()
    archive_dir = _archive_root(project_root) / media_type / now.strftime("%Y") / now.strftime("%m")
    archive_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60].strip("-") or media_type
    filename = f"{now.strftime('%Y%m%d-%H%M%S-%f')}-{slug}"
    archived_video = archive_dir / f"{filename}{video_path.suffix.lower()}"

    shutil.copy2(video_path, archived_video)
    shutil.copy2(metadata_path, archived_video.with_suffix(".json"))
    return archived_video
