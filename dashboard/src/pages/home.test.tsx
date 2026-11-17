import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { ReactNode } from 'react';
import { cleanup, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { api } from '../api';
import type { Health, ProductionRun, Task } from '../api';
import { Home } from './home';

// Home renders <Link> outside the router tree in tests; stub it with a plain anchor.
vi.mock('@tanstack/react-router', () => ({
  Link: ({ children }: { children?: ReactNode }) => <a href="#">{children}</a>,
}));

const iso = (msAgo: number) => new Date(Date.now() - msAgo).toISOString();

const healthFixture: Health = {
  database: 'ok',
  database_accessible: true,
  queue_counts: {},
  total_tasks: 3,
  expired_running_leases: 0,
  workers: [],
  active_workers: 0,
  stale_workers: 0,
  stopped_workers: 0,
};

function makeTask(partial: Pick<Task, 'task_id' | 'task_type' | 'status'> & Partial<Task>): Task {
  return {
    plan_id: null,
    priority: 1,
    attempts: 1,
    max_attempts: 3,
    created_at: iso(600000),
    updated_at: iso(30000),
    lease_owner: null,
    lease_until: null,
    error_code: null,
    payload_json: null,
    result_json: null,
    ...partial,
  };
}

const runningTask = makeTask({ task_id: 'task-running-1', task_type: 'render_short', status: 'running' });
const queuedTask = makeTask({
  task_id: 'task-queued-1',
  task_type: 'generate_script',
  status: 'queued',
  attempts: 0,
  updated_at: iso(90000),
});
const blockedTask = makeTask({
  task_id: 'task-blocked-1',
  task_type: 'publish_video',
  status: 'blocked',
  error_code: 'capability_unavailable',
  updated_at: iso(60000),
});

const tasksResponse = { tasks: [runningTask, queuedTask, blockedTask], limit: 200 };

function makeRun(partial: Pick<ProductionRun, 'run_id' | 'topic' | 'status'> & Partial<ProductionRun>): ProductionRun {
  return {
    quality: 'hd',
    started_at: iso(120000),
    finished_at: null,
    stage_count: 5,
    active_stage: null,
    artifact_count: 3,
    failure_stage: null,
    error_type: null,
    error_category: null,
    ...partial,
  };
}

const liveRun = makeRun({
  run_id: 'run-live-1',
  topic: 'Morning tea short',
  status: 'in_progress',
  active_stage: 'render',
});
const completedRun = makeRun({
  run_id: 'run-done-1',
  topic: 'Evening gym short',
  status: 'ok',
  started_at: iso(7200000),
  finished_at: iso(3600000),
  stage_count: 6,
  artifact_count: 4,
});
const failedRun = makeRun({
  run_id: 'run-fail-1',
  topic: 'News recap short',
  status: 'failed',
  started_at: iso(5400000),
  stage_count: 4,
  artifact_count: 1,
  failure_stage: 'render',
});

const runsResponse = { runs: [liveRun, completedRun, failedRun], limit: 100, source: 'manifest' };

beforeEach(() => {
  vi.spyOn(api, 'health').mockResolvedValue(healthFixture);
  vi.spyOn(api, 'tasks').mockResolvedValue(tasksResponse);
  vi.spyOn(api, 'productionRuns').mockResolvedValue(runsResponse);
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

function renderHome() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <Home />
    </QueryClientProvider>,
  );
}

describe('Home independent query failure handling', () => {
  it('shows a local runtime-status error and keeps task and production sections visible when health fails', async () => {
    vi.spyOn(api, 'health').mockRejectedValue(new Error('health endpoint down'));

    renderHome();

    expect(await screen.findByText('Runtime status unavailable')).toBeInTheDocument();
    expect(
      await screen.findByText('Health endpoint unreachable · saved records are shown where available'),
    ).toBeInTheDocument();
    expect(await screen.findAllByText('Morning tea short')).toHaveLength(2); // work panel + production list
    expect(screen.getByText('Artifacts')).toBeInTheDocument();
    expect(screen.getByText('2 active')).toBeInTheDocument();
    expect(screen.getByText('Running tasks').nextElementSibling).toHaveTextContent('1');
    expect(screen.queryByText('Could not load live data')).not.toBeInTheDocument();
  });

  it('keeps health, production and loaded run items visible while tasks fail', async () => {
    vi.spyOn(api, 'tasks').mockRejectedValue(new Error('tasks endpoint down'));

    renderHome();

    expect((await screen.findAllByText('Could not load live data')).length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText('Production pipeline activity')).toBeInTheDocument();
    expect(screen.getByText('Artifacts')).toBeInTheDocument();
    expect(await screen.findAllByText('Morning tea short')).toHaveLength(2);
    expect(screen.getByText('Workspace operational')).toBeInTheDocument();
    expect(screen.getByText('Unavailable')).toBeInTheDocument();
    expect(screen.getAllByText('Task data unavailable').length).toBeGreaterThanOrEqual(1);
  });

  it('keeps health and task sections visible while production runs fail', async () => {
    vi.spyOn(api, 'productionRuns').mockRejectedValue(new Error('runs endpoint down'));

    renderHome();

    expect((await screen.findAllByText('Could not load live data')).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Production pipeline activity')).toBeInTheDocument();
    expect(screen.getByText('Failed-run data unavailable')).toBeInTheDocument();
    expect(screen.queryByText('Run data unavailable')).not.toBeInTheDocument();
    expect(await screen.findByText('Render Short')).toBeInTheDocument();
    expect(screen.getByText('Running tasks')).toBeInTheDocument();
    expect(screen.getByText('Workspace operational')).toBeInTheDocument();
    expect(screen.queryByText('Artifacts')).not.toBeInTheDocument();
  });

  it('keeps loaded sections visible while one query is still loading', async () => {
    vi.spyOn(api, 'productionRuns').mockReturnValue(new Promise<typeof runsResponse>(() => {}));

    renderHome();

    expect(await screen.findByText('Loading live workspace data…')).toBeInTheDocument();
    expect(await screen.findByText('Render Short')).toBeInTheDocument();
    expect(screen.getByText('Generate Script')).toBeInTheDocument();
    expect(screen.getByText('Workspace operational')).toBeInTheDocument();
    expect(screen.getByText('Running tasks').nextElementSibling).toHaveTextContent('1');
    expect(screen.getByText('Failed-run data loading…')).toBeInTheDocument();
    expect(screen.queryByText('Run data loading…')).not.toBeInTheDocument();
    expect(screen.queryByText('Runs')).not.toBeInTheDocument();
  });
});
