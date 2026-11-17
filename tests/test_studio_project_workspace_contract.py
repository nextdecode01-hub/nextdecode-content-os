from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PERSISTENCE = ROOT / "dashboard" / "src" / "studioPersistence.ts"
STUDIO_PAGE = ROOT / "dashboard" / "src" / "pages" / "studio.tsx"


def test_persistence_exposes_project_scoped_workspace_and_storyboard_operations():
    source = PERSISTENCE.read_text(encoding="utf-8")
    for symbol in (
        "StudioWorkspace",
        "listStudioWorkspaces",
        "createStudioWorkspace",
        "listStudioDrafts",
        "createStudioDraft",
        "workspaceId",
        "byWorkspace",
        "migrateLegacyStudioData",
    ):
        assert symbol in source


def test_persistence_keeps_legacy_draft_and_versions_readable():
    source = PERSISTENCE.read_text(encoding="utf-8")
    assert "STUDIO_DRAFT_ID = 'nextdecode-shorts-studio-main'" in source
    assert "LEGACY_WORKSPACE_ID" in source
    assert "LEGACY_SHORT_TITLE" in source
    assert "nextdecode-studio-workspace-main" in source
    assert "parentVersionId" in source
    assert "restoreOfVersionId" in source


def test_studio_ui_has_workspace_and_short_selection_without_server_integration():
    source = STUDIO_PAGE.read_text(encoding="utf-8")
    for text in (
        "listStudioWorkspaces",
        "listStudioDrafts",
        "createStudioWorkspace",
        "createStudioDraft",
        "Selected workspace",
        "Selected Short",
    ):
        assert text in source
    assert "fetch('/api" not in source
