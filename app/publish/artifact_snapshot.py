#!/usr/bin/env python3
"""ND-M3-F1 — digest-bound upload snapshot pinned to an open file descriptor.

Authorization supplies the expected SHA-256. This module copies and hashes the
source, verifies the persisted bytes, then opens the verified inode read-only
and unlinks its staging name. Transfers use the process-local descriptor path
(/proc/self/fd/N or /dev/fd/N), never a replaceable staging pathname.

The descriptor stays open for the entire transfer. Closing the snapshot releases
it. This prevents a later unlink/recreate of the former staging pathname from
redirecting a transfer to different bytes. It is an inode-pinning control, not
a defense against a fully compromised process running as the same OS identity.
"""
from __future__ import annotations

import hashlib
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_DIR_NAME = ".upload_snapshots"
_HEX = frozenset("0123456789abcdef")


class ArtifactIntegrityError(RuntimeError):
    """Raised when the local artifact does not match its authorized digest."""


@dataclass
class UploadSnapshot:
    """A verified artifact exposed through a pinned, open read-only descriptor."""

    path: Path
    sha256: str
    size: int
    fd: int
    staging_path: Path

    def close(self) -> None:
        """Release the pinned descriptor. Safe to call more than once."""
        if self.fd < 0:
            return
        descriptor, self.fd = self.fd, -1
        try:
            os.close(descriptor)
        except OSError:
            pass


def digest_file(path: Path) -> str:
    """SHA-256 of a file's bytes on disk."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _digest_descriptor(descriptor: int) -> str:
    """Hash the inode referenced by an already-open descriptor."""
    digest = hashlib.sha256()
    with os.fdopen(os.dup(descriptor), "rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _descriptor_path(descriptor: int) -> Path:
    """Return a same-process path that reopens this exact descriptor."""
    for root in (Path("/proc/self/fd"), Path("/dev/fd")):
        if root.is_dir():
            candidate = root / str(descriptor)
            if candidate.exists():
                return candidate
    raise ArtifactIntegrityError(
        "This platform has no process-local descriptor filesystem; "
        "refusing a pathname-based upload that cannot pin the verified inode")


def _staging_dir(root: Path) -> Path:
    staging = Path(root) / "outputs" / SNAPSHOT_DIR_NAME
    staging.mkdir(parents=True, exist_ok=True)
    os.chmod(staging, 0o700)
    return staging


def _validated_digest(expected: str) -> str:
    digest = str(expected or "").strip().lower()
    if len(digest) != 64 or not set(digest) <= _HEX:
        raise ArtifactIntegrityError(
            "An authorized video digest is required; refusing to snapshot an unbound artifact")
    return digest


def build_upload_snapshot(source: Path, expected_sha256: str, *,
                          root: Path | None = None) -> UploadSnapshot:
    """Copy, verify, and pin the exact authorized bytes for a transfer.

    The copy is hashed inline, flushed and fsynced, then independently hashed
    through a newly opened read-only descriptor. Device/inode identity is
    compared before the staging pathname is unlinked. The returned path
    refers to the open descriptor, not to a mutable directory entry.
    """
    expected = _validated_digest(expected_sha256)
    source = Path(source)
    if not source.is_file():
        raise ArtifactIntegrityError(f"Authorized video file is missing: {source}")

    staging = _staging_dir(Path(root) if root is not None else ROOT)
    descriptor, temp_name = tempfile.mkstemp(
        prefix="upload_snapshot_", suffix=".mp4", dir=str(staging))
    temp_path = Path(temp_name)
    read_descriptor = -1
    created_identity: tuple[int, int] | None = None
    try:
        inline = hashlib.sha256()
        with os.fdopen(descriptor, "wb", closefd=False) as out, source.open("rb") as src:
            for chunk in iter(lambda: src.read(1024 * 1024), b""):
                out.write(chunk)
                inline.update(chunk)
            out.flush()
            os.fsync(descriptor)

        if inline.hexdigest() != expected:
            raise ArtifactIntegrityError(
                "The video file changed after authorization (mutated between authorize and "
                "snapshot); refusing to upload: expected "
                f"sha256={expected}, got sha256={inline.hexdigest()}")

        os.fchmod(descriptor, 0o400)
        created = os.fstat(descriptor)
        created_identity = (created.st_dev, created.st_ino)

        # Open the same inode read-only; O_NOFOLLOW and the identity comparison
        # reject a staging-name swap that occurs before this open.
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        read_descriptor = os.open(temp_path, flags)
        opened = os.fstat(read_descriptor)
        if (opened.st_dev, opened.st_ino) != created_identity:
            raise ArtifactIntegrityError(
                "The upload snapshot pathname changed during descriptor pinning; refusing transfer")

        persisted = _digest_descriptor(read_descriptor)
        if persisted != expected:
            raise ArtifactIntegrityError(
                "The snapshot bytes do not match the authorized digest "
                f"(expected {expected}, persisted {persisted})")

        # Remove the mutable name while keeping the verified inode alive.
        # Any later recreation of this name cannot change the descriptor target.
        temp_path.unlink()
        os.close(descriptor)
        descriptor = -1
        transfer_path = _descriptor_path(read_descriptor)
        return UploadSnapshot(
            path=transfer_path,
            sha256=persisted,
            size=opened.st_size,
            fd=read_descriptor,
            staging_path=temp_path,
        )
    except BaseException:
        if read_descriptor >= 0:
            try:
                os.close(read_descriptor)
            except OSError:
                pass
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                pass
        # Only remove the staging name if it still identifies our own inode.
        try:
            current = temp_path.stat()
            if created_identity is None or (current.st_dev, current.st_ino) == created_identity:
                temp_path.unlink()
        except OSError:
            pass
        raise


@contextmanager
def upload_snapshot(source: Path, expected_sha256: str, *,
                    root: Path | None = None) -> Iterator[UploadSnapshot]:
    """Yield a descriptor-pinned snapshot and always release its descriptor."""
    snapshot = build_upload_snapshot(source, expected_sha256, root=root)
    try:
        yield snapshot
    finally:
        snapshot.close()


def staging_is_empty(root: Path | None = None) -> bool:
    staging = _staging_dir(Path(root) if root is not None else ROOT)
    return not any(staging.iterdir())
