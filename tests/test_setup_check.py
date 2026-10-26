import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class SetupCheckTests(unittest.TestCase):
    def test_missing_optional_integrations_do_not_look_like_blockers(self):
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            script = Path(temp_dir) / "setup_check.py"
            shutil.copyfile(project_root / "setup_check.py", script)
            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=temp_dir,
                env={"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"},
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("[OPTIONAL] Voice: ELEVENLABS_API_KEY", result.stdout)
        self.assertIn("[OPTIONAL] Storage: CLOUDINARY (all 3)", result.stdout)
        self.assertNotIn("[NEEDS SETUP] Voice: ELEVENLABS_API_KEY", result.stdout)
        self.assertIn("required setup item(s) remain", result.stdout)

    def test_optional_missing_items_do_not_set_failure_exit_code(self):
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            script = Path(temp_dir) / "setup_check.py"
            shutil.copyfile(project_root / "setup_check.py", script)
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import json, setup_check; "
                    "print(json.dumps(setup_check.format_report(["
                    "('core', True, '', False), "
                    "('analytics', False, 'Optional', True)])))",
                ],
                cwd=temp_dir,
                env={"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"},
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

        self.assertEqual(result.returncode, 0)
        report, exit_code = json.loads(result.stdout)
        self.assertEqual(exit_code, 0)
        self.assertIn("1 optional integration(s) are not configured", report[-1])


if __name__ == "__main__":
    unittest.main()
