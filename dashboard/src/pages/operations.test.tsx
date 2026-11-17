import type { ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { api, type Health, type Task, type Worker } from '../api';
import { Operations } from './operations';

vi.mock('@tanstack/react-router', () => ({
  Link: ({ children }: { children?: ReactNode }) => <a>{children}</a>,
}));

const now = new Date().toISOString();
const worker: Worker = {
  worker_id: 'worker-local-01',
  hostname: 'wsl-host',
  pid: 4312,
  state: 'running',
  started_at: now,
  heartbeat_at: now,
  alive: true,
  stale: false,
};
const task = (overrides: Partial<Task> = {}): Task => ({
  task_id: 'task-123456789012345',
  task_type: 'studio.render_short',
  status: 'failed',
  priority: 50,
  attempts: 2,
  max_attempts: 3,
  created_at: now,
  updated_at: now,
  ...overrides,
});
const health: Health = {
  database: 'sqlite',
  database_accessible: true,
  queue_counts: { queued: 1, running: 1, succeeded: 4, failed: 1, blocked: 1 },
  total_tasks: 8,
  expired_running_leases: 1,
  workers: [worker, { ...worker, worker_id: 'worker-stale', state: 'stale', stale: true, alive: false }],
  active_workers: 1,
  stale_workers: 1,
  stopped_workers: 0,
};

function renderOperations() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}><Operations /></QueryClientProvider>);
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('Operations read-only observability', () => {
  it('renders database, worker, lease, queue and exception evidence from the APIs', async () => {
    vi.spyOn(api, 'health').mockResolvedValue(health);
    vi.spyOn(api, 'tasks').mockResolvedValue({ tasks: [task(), task({ task_id: 'task-blocked-123456', status: 'blocked' }), task({ task_id: 'task-running-123456', status: 'running' }), task({ task_id: 'task-queued-123456', status: 'queued' })], limit: 200 });
    vi.spyOn(api, 'deadLetters').mockResolvedValue({ dead_letters: [task({ task_id: 'dead-letter-123456', status: 'failed' })] });
    vi.spyOn(api, 'stuckTasks').mockResolvedValue({ stuck_tasks: [{ task_id: 'stuck-task-123456', task_type: 'studio.render_short', lease_owner: 'worker-stale', attempts: 2, updated_at: now, last_execution_heartbeat: now }], stale_after_seconds: 120 });
    vi.spyOn(api, 'eventFeed').mockResolvedValue({ events: [{ event_id: 7, task_id: 'task-123456789012345', event: 'task.failed', at: now, detail_json: null }], next_after_event_id: 7 });

    renderOperations();

    expect(await screen.findByText('Operations & system health')).toBeInTheDocument();
    expect(await screen.findByText('worker-local-01')).toBeInTheDocument();
    expect(screen.getAllByText('Online').length).toBeGreaterThan(0);
    expect(screen.getAllByText('worker-stale').length).toBeGreaterThan(0);
    expect(screen.getByText('Stuck-task candidates')).toBeInTheDocument();
    expect(screen.getByText('stuck-task-12…')).toBeInTheDocument();
    expect(screen.getByText('Failed and blocked tasks')).toBeInTheDocument();
    expect(screen.getByText('Local task event stream')).toBeInTheDocument();
    expect(await screen.findByText('Task Failed')).toBeInTheDocument();
    expect(screen.getByText('No retry, requeue, pause or worker restart controls.')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /retry|restart|requeue|recover/i })).not.toBeInTheDocument();
  });

  it('keeps independent telemetry visible when the health endpoint fails', async () => {
    vi.spyOn(api, 'health').mockRejectedValue(new Error('health endpoint unavailable'));
    vi.spyOn(api, 'tasks').mockResolvedValue({ tasks: [], limit: 200 });
    vi.spyOn(api, 'deadLetters').mockResolvedValue({ dead_letters: [] });
    vi.spyOn(api, 'stuckTasks').mockResolvedValue({ stuck_tasks: [], stale_after_seconds: 120 });
    vi.spyOn(api, 'eventFeed').mockResolvedValue({ events: [], next_after_event_id: 0 });

    renderOperations();

    expect((await screen.findAllByText('Could not load live data')).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/health endpoint unavailable/i).length).toBeGreaterThan(0);
    expect(screen.getByText('Stuck-task candidates')).toBeInTheDocument();
    expect(screen.getByText('Failed and blocked tasks')).toBeInTheDocument();
    expect(screen.getByText('No stale execution heartbeats detected')).toBeInTheDocument();
    expect(screen.queryByText('Database reachable')).not.toBeInTheDocument();
  });
});
