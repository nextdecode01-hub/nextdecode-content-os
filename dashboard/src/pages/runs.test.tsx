import type { ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { api, type ProductionRun, type ProductionRunDetail, type Task } from '../api';
import { Runs, STALE_RUN_MINUTES, runTriageReport, summarizeRuns } from './runs';

vi.mock('@tanstack/react-router', () => ({
  Link: ({ children }: { children?: ReactNode }) => <a>{children}</a>,
}));

const now = new Date().toISOString();
const task: Task = {
  task_id: 'task-run-list-123456',
  task_type: 'studio.render_short',
  status: 'running',
  priority: 50,
  attempts: 1,
  max_attempts: 3,
  created_at: now,
  updated_at: now,
};
const run: ProductionRun = {
  run_id: 'run-manifest-001',
  topic: 'AI source verification',
  status: 'failed',
  stage_count: 2,
  artifact_count: 2,
  failure_stage: 'qa',
  error_type: 'RuntimeError',
  error_category: 'quality_gate',
};
const detail: ProductionRunDetail = {
  run,
  schema_version: 1,
  stages: [
    { name: 'research', status: 'ok', started_at: now, finished_at: now },
    { name: 'qa', status: 'failed', started_at: now, finished_at: now },
  ],
  artifacts: [
    { name: 'research.json', path: 'research.json', sha256: 'a'.repeat(64), computed_sha256: 'a'.repeat(64), bytes: 100, actual_bytes: 100, stage: 'research', exists: true, integrity_status: 'verified' },
    { name: 'output_short.mp4', path: 'output_short.mp4', sha256: 'b'.repeat(64), computed_sha256: 'c'.repeat(64), bytes: 200, actual_bytes: 200, stage: 'qa', exists: true, integrity_status: 'digest_mismatch' },
  ],
  failure: { stage: 'qa', error_type: 'RuntimeError', error_category: 'quality_gate' },
  evidence_source: 'RunTracker manifest',
  trace_completeness: 'partial',
  canonical_workflow_linked: false,
};

function renderRuns() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}><Runs /></QueryClientProvider>);
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('Production run manifest observability', () => {
  it('loads a persisted run and exposes stage failure plus artifact digest mismatch', async () => {
    vi.spyOn(api, 'tasks').mockResolvedValue({ tasks: [task], limit: 200 });
    vi.spyOn(api, 'productionRuns').mockResolvedValue({ runs: [run], limit: 100, source: 'RunTracker' });
    const detailSpy = vi.spyOn(api, 'productionRun').mockResolvedValue(detail);

    renderRuns();

    expect(await screen.findByText('AI source verification')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /inspect/i }));

    expect(await screen.findByText(/Trace completeness: partial/)).toBeInTheDocument();
    expect((await screen.findAllByText('SHA-256 verified')).length).toBeGreaterThan(0);
    expect(screen.getByText('SHA-256 mismatch')).toBeInTheDocument();
    expect(screen.getByText(/Failure recorded here: RuntimeError · quality_gate/)).toBeInTheDocument();
    expect(screen.getByText(/canonical workflow linkage is not present/)).toBeInTheDocument();
    expect(detailSpy).toHaveBeenCalledWith('run-manifest-001');
    expect(screen.getByText('Failure pattern across persisted runs')).toBeInTheDocument();
  });

  it('does not invent manifest detail when the production run endpoint is unavailable', async () => {
    vi.spyOn(api, 'tasks').mockResolvedValue({ tasks: [], limit: 200 });
    vi.spyOn(api, 'productionRuns').mockRejectedValue(new Error('manifest index unavailable'));

    renderRuns();

    expect(await screen.findByText('manifest index unavailable')).toBeInTheDocument();
    expect(screen.queryByText('SHA-256 verified')).not.toBeInTheDocument();
  });
});

describe('Run index is fully browsable', () => {
  it('filters every persisted run instead of a fixed first window', async () => {
    const failed = { ...run, run_id: 'run-fail-0001', topic: 'Failed topic' };
    const ok = { ...run, run_id: 'run-ok-0002', topic: 'Succeeded topic', status: 'ok', failure_stage: null, error_type: null, error_category: null };
    vi.spyOn(api, 'tasks').mockResolvedValue({ tasks: [], limit: 200 });
    vi.spyOn(api, 'productionRuns').mockResolvedValue({ runs: [failed, ok], limit: 100, source: 'RunTracker' });

    renderRuns();

    expect(await screen.findByText('Failed topic')).toBeInTheDocument();
    expect(screen.getByText('Succeeded topic')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Filter runs by status'), { target: { value: 'failed' } });

    expect(screen.getByText('Failed topic')).toBeInTheDocument();
    expect(screen.queryByText('Succeeded topic')).not.toBeInTheDocument();
    expect(screen.getByText(/Showing 1 of 1 matching runs/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Filter runs by status'), { target: { value: 'ok' } });

    expect(await screen.findByText('Succeeded topic')).toBeInTheDocument();
    expect(screen.queryByText('Failed topic')).not.toBeInTheDocument();
  });
});

describe('Run triage from manifest fields only', () => {
  const hoursAgo = (hours: number) => new Date(Date.now() - hours * 3600_000).toISOString();
  const base: ProductionRun = {
    run_id: 'run-base',
    topic: 'topic',
    status: 'failed',
    stage_count: 1,
    artifact_count: 0,
    failure_stage: 'render',
    error_type: 'RuntimeError',
    error_category: 'unknown',
    started_at: hoursAgo(2),
  };
  const runs: ProductionRun[] = [
    base,
    { ...base, run_id: 'run-second', artifact_count: 1, started_at: hoursAgo(5) },
    { ...base, run_id: 'run-qa', failure_stage: 'qa', error_type: 'ValueError', error_category: 'quality_gate' },
    { ...base, run_id: 'run-stale', status: 'in_progress', failure_stage: null, error_type: null, error_category: null, started_at: hoursAgo(9) },
    { ...base, run_id: 'run-ok', status: 'ok', failure_stage: null, error_type: null, error_category: null, artifact_count: 7 },
  ];

  it('clusters failures by stage, error type and category without diagnosing a cause', () => {
    const triage = summarizeRuns(runs, Date.now());

    expect(triage.total).toBe(5);
    expect(triage.failed).toBe(3);
    expect(triage.ok).toBe(1);
    expect(triage.inProgress).toBe(1);
    expect(triage.stale).toBe(1);
    expect(triage.artifacts).toBe(8);
    expect(triage.clusters).toHaveLength(2);
    expect(triage.clusters[0]).toMatchObject({ stage: 'render', errorType: 'RuntimeError', category: 'unknown', count: 2, artifacts: 1 });
    expect(triage.oldestStale?.run_id).toBe('run-stale');
    expect(triage.oldestStale?.minutes).toBeGreaterThanOrEqual(STALE_RUN_MINUTES * 8);
  });

  it('writes an evidence report that states the limits instead of inferring a root cause', () => {
    const triage = summarizeRuns(runs, Date.now());
    const report = runTriageReport(triage, runs, new Date('2026-01-01T00:00:00.000Z'));

    expect(report).toContain('# Nextdecode — run triage evidence');
    expect(report).toContain('- Failed: 3 · Succeeded: 1');
    expect(report).toContain('2× · stage render · RuntimeError · unknown');
    expect(report).toContain('"unknown" / "unrecorded" means the manifest did not persist a category; it is not a diagnosis.');
    expect(report).toContain('| run-stale | in_progress |');
  });
});
