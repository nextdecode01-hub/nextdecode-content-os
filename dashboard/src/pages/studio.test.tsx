import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { api } from '../api';
import * as studioPersistence from '../studioPersistence';
import { createStudioDraft, createStudioWorkspace, listStudioDrafts, listStudioTaskLinks, listStudioVersions, LEGACY_WORKSPACE_ID, type StudioBeat } from '../studioPersistence';
import { StudioWorkbench, StudioWorkspaceNavigator } from './studio';

const beats: StudioBeat[] = [
  {
    id: 1,
    name: 'Existing workspace scene',
    start: 0,
    end: 5,
    kind: 'Motion graphic',
    description: 'This scene must disappear when the empty workspace is selected.',
    caption: 'Old workspace content.',
  },
];

async function clearStudioDatabase() {
  await new Promise<void>((resolve, reject) => {
    const request = indexedDB.deleteDatabase('nextdecode-studio-workbench');
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
    request.onblocked = () => reject(new Error('Studio database deletion was blocked'));
  });
}

beforeEach(async () => {
  await clearStudioDatabase();
  vi.spyOn(api, 'jobs').mockResolvedValue({});
  vi.spyOn(api, 'pendingReview').mockResolvedValue(null);
  vi.spyOn(api, 'caps').mockResolvedValue({ capabilities: [] });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe('Studio workspace selection', () => {
  it('ignores a slower workspace response after the user has selected a newer workspace', async () => {
    const first = await createStudioWorkspace('A - First workspace');
    const firstDraft = await createStudioDraft(first.workspaceId, 'First workspace Short', beats);
    const slow = await createStudioWorkspace('B - Slow workspace');
    const slowDraft = await createStudioDraft(slow.workspaceId, 'Slow workspace Short', beats);

    const originalListStudioDrafts = studioPersistence.listStudioDrafts;
    let releaseSlow!: (drafts: typeof firstDraft[]) => void;
    const slowResult = new Promise<typeof firstDraft[]>(resolve => { releaseSlow = resolve; });
    const listSpy = vi.spyOn(studioPersistence, 'listStudioDrafts').mockImplementation(async workspaceId => {
      if (workspaceId === slow.workspaceId) return slowResult;
      return originalListStudioDrafts(workspaceId);
    });

    render(<StudioWorkspaceNavigator />);
    const workspaceSelect = await screen.findByLabelText('Selected workspace');
    await screen.findByRole('option', { name: 'A - First workspace' });

    fireEvent.change(workspaceSelect, { target: { value: slow.workspaceId } });
    fireEvent.change(workspaceSelect, { target: { value: first.workspaceId } });

    await waitFor(() => {
      expect((workspaceSelect as HTMLSelectElement).value).toBe(first.workspaceId);
      expect((screen.getByLabelText('Selected Short') as HTMLSelectElement).value).toBe(firstDraft.draftId);
    });

    releaseSlow([slowDraft]);
    await waitFor(() => expect((workspaceSelect as HTMLSelectElement).value).toBe(first.workspaceId));
    expect((screen.getByLabelText('Selected Short') as HTMLSelectElement).value).toBe(firstDraft.draftId);
    expect(listSpy).toHaveBeenCalledWith(slow.workspaceId);
  });

  it('persists an immutable version, submits it to the task API, and renders the worker result', async () => {
    const draft = await createStudioDraft(LEGACY_WORKSPACE_ID, 'Worker-connected Short', beats);
    const taskId = 'studio-ui-validation-task';
    vi.spyOn(api, 'createTask').mockResolvedValue({
      task_id: taskId,
      status: 'queued',
      task_type: 'studio.storyboard.validate',
    });
    vi.spyOn(api, 'task').mockResolvedValue({
      task: {
        task_id: taskId,
        task_type: 'studio.storyboard.validate',
        status: 'succeeded',
        priority: 100,
        attempts: 1,
        max_attempts: 3,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        result_json: JSON.stringify({
          output: {
            scene_count: 1,
            actual_duration_seconds: 5,
            timeline_contiguous: true,
            human_review_required: true,
            external_actions_allowed: false,
          },
        }),
      },
      events: [],
    });

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={queryClient}>
        <StudioWorkbench />
      </QueryClientProvider>,
    );

    const submitButton = await screen.findByRole('button', { name: 'Submit storyboard for validation' });
    await waitFor(() => expect(submitButton).toBeEnabled());
    fireEvent.click(submitButton);

    await waitFor(() => expect(api.createTask).toHaveBeenCalledTimes(1));
    expect(api.createTask).toHaveBeenCalledWith(
      'studio.storyboard.validate',
      expect.objectContaining({
        title: 'Worker-connected Short',
        studio_version_id: expect.stringMatching(/^[a-f0-9-]{36}$/),
        studio_content_sha256: expect.stringMatching(/^[a-f0-9]{64}$/),
        scenes: [expect.objectContaining({ id: 1, name: 'Existing workspace scene' })],
      }),
      expect.stringMatching(/^studio-storyboard-/),
    );
    await screen.findByText(/Saved immutable version/);
    await screen.findByText('succeeded');
    await screen.findByText('Continuous');
    expect(await listStudioVersions(draft.draftId)).toHaveLength(1);
    const versions = await listStudioVersions(draft.draftId);
    expect(await listStudioTaskLinks(versions[0].versionId)).toEqual([
      expect.objectContaining({ taskId, draftId: draft.draftId, versionId: versions[0].versionId }),
    ]);
  });

  it('clears the previous Short when the workbench receives an empty workspace selection', async () => {
    const populated = await createStudioWorkspace('A - Populated workspace');
    const draft = await createStudioDraft(populated.workspaceId, 'Existing Short', beats);
    expect(await listStudioDrafts(populated.workspaceId)).toHaveLength(1);
    const empty = await createStudioWorkspace('B - Empty workspace');

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={queryClient}>
        <StudioWorkbench />
      </QueryClientProvider>,
    );

    window.dispatchEvent(new CustomEvent('studio-draft-selected', {
      detail: { workspaceId: populated.workspaceId, draftId: draft.draftId },
    }));
    await screen.findAllByText(/Existing workspace scene/);

    window.dispatchEvent(new CustomEvent('studio-draft-selected', {
      detail: { workspaceId: empty.workspaceId, draftId: null },
    }));

    await waitFor(() => {
      expect(screen.getByText('No Short selected')).toBeInTheDocument();
    });
    expect(screen.queryByText(/Existing workspace scene/)).not.toBeInTheDocument();
    expect(screen.getByText(/This workspace is empty/)).toBeInTheDocument();
  });

});
