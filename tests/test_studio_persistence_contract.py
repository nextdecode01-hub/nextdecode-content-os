from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PERSISTENCE = ROOT / "dashboard" / "src" / "studioPersistence.ts"
STUDIO_PAGE = ROOT / "dashboard" / "src" / "pages" / "studio.tsx"


def test_studio_versions_are_append_only_and_digest_backed():
    source = PERSISTENCE.read_text(encoding="utf-8")
    assert "crypto.subtle.digest('SHA-256'" in source
    assert "objectStore(VERSIONS).add(version)" in source
    assert "objectStore(VERSIONS).put(" not in source
    assert "verifyStudioVersion" in source


def test_studio_validation_task_link_is_separate_and_version_scoped():
    source = PERSISTENCE.read_text(encoding="utf-8")
    assert "TASK_LINKS = 'taskLinks'" in source
    assert "store.createIndex('byVersion','versionId'" in source
    assert "store.createIndex('byTask','taskId',{unique:true})" in source
    assert "version.draftId!==draftId" in source
    assert "versionId,taskId,linkedAt" in source


def test_studio_ui_persists_drafts_and_restores_as_new_versions():
    source = STUDIO_PAGE.read_text(encoding="utf-8")
    assert "saveStudioDraft('AI Accelerates Research?',beats)" in source
    assert "linkStudioValidationTask(version.versionId,result.task_id)" in source
    assert "verifyStudioVersion(version)" in source
    assert "restoreOfVersionId:version.versionId" in source
    assert "Restore as new version" in source


def test_studio_scope_does_not_add_server_routes_or_canonical_integrations():
    source = STUDIO_PAGE.read_text(encoding="utf-8")
    assert "studio.storyboard.validate" in source
    assert "WP2/WP5" in source
    assert "fetch('/api" not in source
