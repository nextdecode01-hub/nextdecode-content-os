"""Regression test for descriptor-pinned upload snapshots (ND-M3-F1)."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from app.publish.artifact_snapshot import build_upload_snapshot


class DescriptorPinnedSnapshotTests(unittest.TestCase):
    def test_recreated_staging_name_cannot_redirect_transfer_bytes(self):
        original = b"authorized video bytes" * 8192
        replacement = b"unapproved replacement bytes" * 8192

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "outputs" / "output_short.mp4"
            source.parent.mkdir(parents=True)
            source.write_bytes(original)

            snapshot = build_upload_snapshot(
                source, hashlib.sha256(original).hexdigest(), root=root
            )
            former_name = snapshot.staging_path
            try:
                self.assertFalse(former_name.exists())
                # Simulate a same-user process recreating the former pathname.
                former_name.write_bytes(replacement)

                transferred = snapshot.path.read_bytes()
                self.assertEqual(transferred, original)
                self.assertEqual(
                    hashlib.sha256(transferred).hexdigest(),
                    snapshot.sha256,
                )
            finally:
                snapshot.close()
                former_name.unlink(missing_ok=True)

            self.assertFalse(snapshot.path.exists())


if __name__ == "__main__":
    unittest.main()
