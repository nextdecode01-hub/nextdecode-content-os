import type { ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { api, type Task } from '../api';
import { Task as TaskPage } from './task';

vi.mock('@tanstack/react-router', () => ({
  Link: ({ children }: { children?: ReactNode }) => <a>{children}</a>,
  useParams: () => ({ taskId: 'task-inspector-001' }),
}));

const now = new Date().toISOString();
const task: Task = {
  task_id: 'task-inspector-001',
  task_type: 'studio.storyboard.validate',
  status: 'failed',
  priority: 80,
  attempts: 2,
  max_attempts: 3,
  created_at: now,
  updated_at: now,
  error_code: 'QUALITY_GATE_FAILED',
  payload_json: JSON.stringify({ topic: 'AI safety', api_key: 'must-not-render', scene_count: 3 }),
  result_json: JSON.stringify({ status: 'failed', reason: 'duration out of range', access_token: 'must-not-render' }),
};
const events = [
  { event_id: 1, task_id: task.task_id, event: 'queued', at: now, detail_json: JSON.stringify({ queue: 'default' }) },
  { event_id: 2, task_id: task.task_id, event: 'claimed', at: now, detail_json: JSON.stringify({ worker_id: 'worker-1' }) },
  { event_id: 3, task_id: task.task_id, event: 'failed', at: now, detail_json: JSON.stringify({ reason: 'quality gate', api_key: 'must-not-render' }) },
];

function renderTask() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}><TaskPage /></QueryClientProvider>);
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('Task inspector lifecycle evidence', () => {
  it('renders chronological events and redacts sensitive input/output and event fields', async () => {
    vi.spyOn(api, 'task').mockResolvedValue({ task, events: [...events].reverse() });

    renderTask();

    expect(await screen.findByText('Task inspection')).toBeInTheDocument();
    expect((await screen.findAllByText('Execution failed')).length).toBeGreaterThan(0);
    expect(screen.getByText('Task queued')).toBeInTheDocument();
    expect(screen.getByText('Worker claimed task')).toBeInTheDocument();
    expect(screen.queryByText('must-not-render')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /inspect task input/i }));
    expect(screen.queryByText('must-not-render')).not.toBeInTheDocument();
    expect(screen.getByText(/Topic:/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /inspect task output/i }));
    expect(screen.getByText(/duration out of range/)).toBeInTheDocument();
    expect(screen.queryByText('must-not-render')).not.toBeInTheDocument();
  });

  it('filters persisted event history by failures and worker activity', async () => {
    vi.spyOn(api, 'task').mockResolvedValue({ task, events });

    renderTask();

    expect(await screen.findByText('Task queued')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Show'), { target: { value: 'errors' } });
    expect(screen.getAllByText('Execution failed').length).toBeGreaterThan(0);
    expect(screen.queryByText('Task queued')).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Show'), { target: { value: 'worker' } });
    expect(screen.getByText('Worker claimed task')).toBeInTheDocument();
    expect(screen.queryByText('Task queued')).not.toBeInTheDocument();
  });
});
