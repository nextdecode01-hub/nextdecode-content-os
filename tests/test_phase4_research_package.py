"""Phase 4 smoke test: research modules live in app/research/ and imports resolve."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from app.research import desk, selector, topics, trends

ROOT = Path(__file__).resolve().parents[1]

RESEARCH_MODULES = {
    "app/research/topics.py": "topics",
    "app/research/trends.py": "trends",
    "app/research/selector.py": "selector",
    "app/research/desk.py": "desk",
}

OLD_ROOT_MODULES = ("topic_research", "trend_research", "topic_selector", "research_desk")


def test_research_package_files_and_init_exist() -> None:
    assert (ROOT / "app" / "__init__.py").is_file()
    assert (ROOT / "app" / "research" / "__init__.py").is_file()
    for relative in RESEARCH_MODULES:
        assert (ROOT / relative).is_file(), f"{relative} is missing"


def test_old_root_modules_were_moved_not_copied() -> None:
    for name in OLD_ROOT_MODULES:
        assert not (ROOT / f"{name}.py").exists(), f"{name}.py still exists in the repo root"


def test_public_api_is_importable() -> None:
    assert callable(topics.discover_topics)
    assert callable(trends.fetch_all)
    assert callable(selector.select_best)
    assert callable(selector.rank_topics)
    assert callable(desk.research_topic)


def test_project_paths_still_resolve_to_repo_root_data() -> None:
    assert trends.CACHE_PATH == ROOT / "data" / "trend_cache.json"
    assert trends.HISTORY_PATH == ROOT / "data" / "trend_history.json"
    assert trends.USED_TOPICS_PATH == ROOT / "data" / "used_topics.txt"
    assert selector.ROOT == ROOT
    assert selector.USED_TOPICS_PATH == ROOT / "data" / "used_topics.txt"
    assert topics.PROJECT_ROOT == ROOT


def test_no_active_code_imports_old_research_names() -> None:
    pattern = re.compile(
        r"^\s*(?:from|import)\s+(" + "|".join(re.escape(name) for name in OLD_ROOT_MODULES) + r")\b",
        re.MULTILINE,
    )
    offenders: list[str] = []
    for path in sorted(ROOT.glob("*.py")) + sorted(ROOT.glob("app/**/*.py")):
        source = path.read_text(encoding="utf-8-sig")
        for match in pattern.finditer(source):
            offenders.append(f"{path.relative_to(ROOT)}: {match.group(0).strip()}")
    assert not offenders, "old research imports remain: " + ", ".join(offenders)


def test_imports_work_from_repo_root() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import app.research.topics, app.research.trends, app.research.desk, app.research.selector",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-800:]


def test_setup_check_reports_new_module_paths() -> None:
    source = (ROOT / "setup_check.py").read_text(encoding="utf-8")
    for module in ("app.research.trends", "app.research.desk", "app.research.selector"):
        assert f'"{module}"' in source, f"setup_check.py is not checking {module}"
