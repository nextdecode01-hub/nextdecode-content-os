import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  createStudioDraft,
  createStudioVersion,
  createStudioWorkspace,
  listStudioVersions,
  loadStudioDraft,
  verifyStudioVersion,
  type StudioBeat,
} from './studioPersistence';

const databaseName = 'nextdecode-studio-workbench';
const beats: StudioBeat[] = [
  {
    id: 1,
    name: 'Atomic persistence scene',
    start: 0,
    end: 5,
    kind: 'Motion graphic',
    description: 'A deterministic persistence fixture.',
    caption: 'Version pointer and version record move together.',
  },
];

async function deleteStudioDatabase() {
  await new Promise<void>((resolve, reject) => {
    const request = indexedDB.deleteDatabase(databaseName);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
    request.onblocked = () => reject(new Error('Studio database deletion was blocked'));
  });
}

beforeEach(async () => {
  await deleteStudioDatabase();
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe('Studio immutable version persistence', () => {
  it('persists the draft pointer and immutable version together', async () => {
    const workspace = await createStudioWorkspace('Atomic test workspace');
    const draft = await createStudioDraft(workspace.workspaceId, 'Atomic test Short', beats);

    const version = await createStudioVersion(draft.title, beats, {
      draftId: draft.draftId,
      workspaceId: workspace.workspaceId,
    });

    const savedDraft = await loadStudioDraft(draft.draftId);
    const versions = await listStudioVersions(draft.draftId);

    expect(savedDraft?.currentVersionId).toBe(version.versionId);
    expect(versions).toHaveLength(1);
    expect(versions[0].versionId).toBe(version.versionId);
    expect(await verifyStudioVersion(versions[0])).toBe(true);
  });

  it('rolls back the draft pointer when the immutable version insert fails', async () => {
    const workspace = await createStudioWorkspace('Atomic rollback workspace');
    const draft = await createStudioDraft(workspace.workspaceId, 'Atomic rollback Short', beats);
    const randomUUID = vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('11111111-1111-4111-8111-111111111111');

    const firstVersion = await createStudioVersion(draft.title, beats, {
      draftId: draft.draftId,
      workspaceId: workspace.workspaceId,
    });

    await expect(
      createStudioVersion('A second version with a duplicate ID', beats, {
        draftId: draft.draftId,
        workspaceId: workspace.workspaceId,
      }),
    ).rejects.toBeTruthy();

    const savedDraft = await loadStudioDraft(draft.draftId);
    const versions = await listStudioVersions(draft.draftId);

    expect(randomUUID).toHaveBeenCalledTimes(2);
    expect(savedDraft?.currentVersionId).toBe(firstVersion.versionId);
    expect(versions).toHaveLength(1);
    expect(versions[0].versionId).toBe(firstVersion.versionId);
  });
});
