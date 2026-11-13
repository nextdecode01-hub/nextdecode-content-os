"""Current dependency map documents the application-owned autonomous runtime."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def test_map_documents_autonomous_runtime_contracts():
 text=(ROOT/"docs"/"dependency_map.md").read_text(encoding="utf-8")
 for required in ("app.autonomy.store","app.autonomy.worker","app.autonomy.registry","idempotency","lease","SQLite","review-only"):
  assert required.lower() in text.lower()
def test_autonomy_core_files_exist():
 for name in ("models.py","store.py","registry.py","worker.py","tasks.py","cli.py"):
  assert (ROOT/"app"/"autonomy"/name).is_file()
