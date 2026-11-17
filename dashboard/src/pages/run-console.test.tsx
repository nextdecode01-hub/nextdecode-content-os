import type { ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { api, type ProductionRun, type ProductionRunAssets, type ProductionRunDetail, type ProductionStoryboard, type ToolCandidate } from '../api';
import { RunConsole, buildRunReport } from './run-console';

vi.mock('@tanstack/react-router', () => ({
  Link: ({ children }: { children?: ReactNode }) => <a>{children}</a>,
  useParams: () => ({ runId: 'run-console-001' }),
}));

const started = new Date(Date.now() - 6 * 60_000).toISOString();
const finished = new Date(Date.now() - 4 * 60_000).toISOString();

const run: ProductionRun = {
  run_id: 'run-console-001',
  topic: 'Mixture-of-experts routing',
  status: 'ok',
  stage_count: 3,
  artifact_count: 3,
  started_at: started,
  finished_at: finished,
};

const detail: ProductionRunDetail = {
  run,
  schema_version: 2,
  stages: [
    { name: 'research', status: 'ok', started_at: started, finished_at: started },
    { name: 'script', status: 'ok', started_at: started, finished_at: started },
    { name: 'render', status: 'ok', started_at: started, finished_at: finished },
  ],
  artifacts: [
    { name: 'video', path: 'output_short.mp4', sha256: 'a'.repeat(64), computed_sha256: 'a'.repeat(64), bytes: 2_000_000, actual_bytes: 2_000_000, stage: 'render', exists: true, integrity_status: 'verified' },
    { name: 'captions', path: 'captions.ass', sha256: 'b'.repeat(64), computed_sha256: 'b'.repeat(64), bytes: 4_000, actual_bytes: 4_000, stage: 'render', exists: true, integrity_status: 'verified' },
    { name: 'storyboard', path: 'storyboard.json', sha256: 'c'.repeat(64), computed_sha256: 'd'.repeat(64), bytes: 9_000, actual_bytes: 9_000, stage: 'render', exists: true, integrity_status: 'digest_mismatch' },
  ],
  evidence_source: 'RunTracker manifest',
  trace_completeness: 'complete',
  canonical_workflow_linked: false,
};

const assets: ProductionRunAssets = {
  script: {
    title: 'How MoE routes tokens',
    hook: 'Only a few experts fire for every token.',
    voice_text: 'Sparse routing sends each token to a small set of experts, which is why the compute stays flat as the model grows.',
    word_count: 312,
    duration_seconds: 52,
    source_urls: ['https://arxiv.org/abs/2401.00001', 'https://example.org/moe-explainer'],
    tags: ['mixture-of-experts', 'routing'],
  },
  assets: [
    { id: 'claim-ledger', path: 'claim_ledger.json', media_type: 'application/json', available: true, bytes: 2_000, url: '/api/production-runs/run-console-001/assets/claim-ledger' },
    { id: 'voice-mp3', path: 'voice.mp3', media_type: 'audio/mpeg', available: true, bytes: 900_000, url: '/api/production-runs/run-console-001/assets/voice-mp3' },
  ],
  evidence_source: 'run assets directory',
};

const storyboard: ProductionStoryboard = {
  run_id: 'run-console-001',
  title: 'How MoE routes tokens',
  scene_count: 2,
  review_status: 'review_required',
  approved: false,
  review_required: true,
  review_reasons: ['one scene uses a fallback provider'],
  summary: {},
  scenes: [
    { index: 0, start: 0, end: 4, narration: 'Only a few experts fire.', scene_type: 'hook', visual_type: 'footage', provider: 'wikimedia', asset_id: 'asset-1', relevance: 'high', relevance_confidence: 'confirmed', review_reason: '', fallback_reason: '', relevance_reason: '', image_url: null },
    { index: 1, start: 4, end: 11, narration: 'Routing sends each token to a small set of experts.', scene_type: 'evidence', visual_type: 'generated', provider: 'pil-composite', asset_id: 'asset-2', relevance: 'medium', relevance_confidence: 'inferred', review_reason: '', fallback_reason: 'no licensed footage matched', relevance_reason: '', image_url: null },
  ],
};

function candidate(capability: string, id: string, status: string): ToolCandidate {
  return { id, capability, role: 'renderer', rank: 1, deployment: 'local', license: 'project', cost_model: 'zero', status, strengths: [], limitations: [], requires_approval: false };
}

function renderConsole() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}><RunConsole /></QueryClientProvider>);
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('Run console: one persisted run, end to end', () => {
  it('shows the journey, the written script, the sources, the visual providers and the approval path', async () => {
    vi.spyOn(api, 'productionRun').mockResolvedValue(detail);
    vi.spyOn(api, 'productionRunAssets').mockResolvedValue(assets);
    vi.spyOn(api, 'productionStoryboard').mockResolvedValue(storyboard);
    vi.spyOn(api, 'pendingReview').mockResolvedValue(null);
    vi.spyOn(api, 'health').mockResolvedValue({ database: 'sqlite', database_accessible: true, queue_counts: {}, total_tasks: 0, expired_running_leases: 0, workers: [], active_workers: 1, stale_workers: 0, stopped_workers: 0 });
    vi.spyOn(api, 'toolCatalog').mockImplementation(async (capability?: string) => ({
      capability: capability ?? '',
      candidates: capability === 'research' ? [candidate('research', 'existing-research-desk', 'active')] : [],
    }));

    renderConsole();

    expect(await screen.findByRole('heading', { name: 'Mixture-of-experts routing' })).toBeInTheDocument();

    // Journey covers the whole pipeline, including stages this manifest did not record.
    expect(screen.getByText('Evidence gate')).toBeInTheDocument();
    expect(screen.getByText('Shot planning')).toBeInTheDocument();

    // Script as written by the engine.
    expect(screen.getByText('How MoE routes tokens')).toBeInTheDocument();
    expect(screen.getByText('Only a few experts fire for every token.')).toBeInTheDocument();
    expect(screen.getByText(/Sparse routing sends each token/)).toBeInTheDocument();

    // Research sources come from the run-local script record.
    expect(screen.getAllByText(/arxiv\.org/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/example\.org/).length).toBeGreaterThan(0);

    // Visual plan names the provider per scene and flags the fallback.
    expect(screen.getByText('wikimedia')).toBeInTheDocument();
    expect(screen.getByText('pil-composite')).toBeInTheDocument();
    expect(screen.getByText('no licensed footage matched')).toBeInTheDocument();

    // Output + approvals.
    expect(screen.getByText('SHA-256 verified')).toBeInTheDocument();
    expect(screen.getByText(/approve_review --interactive/)).toBeInTheDocument();
    expect(screen.getByText('No pending package')).toBeInTheDocument();

    // Integrity panel counts the real mismatch.
    expect(screen.getAllByText('1 mismatch').length).toBeGreaterThan(0);

    // System map joins what the run persisted with what the catalog declares.
    expect(screen.getByText('Which engine does which job')).toBeInTheDocument();
    expect(screen.getByText('existing-research-desk')).toBeInTheDocument();
    expect(screen.getByText(/does not invent one/)).toBeInTheDocument();
  });

  it('never invents a script, source or storyboard when the run has no assets', async () => {
    vi.spyOn(api, 'productionRun').mockResolvedValue({
      ...detail,
      run: { ...run, status: 'failed', failure_stage: 'render', error_type: 'RuntimeError', error_category: 'unknown' },
      artifacts: [],
      failure: { stage: 'render', error_type: 'RuntimeError', error_category: 'unknown' },
    });
    vi.spyOn(api, 'productionRunAssets').mockRejectedValue(new Error('no run directory'));
    vi.spyOn(api, 'productionStoryboard').mockRejectedValue(new Error('no storyboard'));
    vi.spyOn(api, 'pendingReview').mockResolvedValue(null);
    vi.spyOn(api, 'health').mockResolvedValue({ database: 'sqlite', database_accessible: true, queue_counts: {}, total_tasks: 0, expired_running_leases: 0, workers: [], active_workers: 0, stale_workers: 0, stopped_workers: 0 });
    vi.spyOn(api, 'toolCatalog').mockResolvedValue({ capability: 'research', candidates: [] });

    renderConsole();

    expect(await screen.findByText('Stopped at Render')).toBeInTheDocument();
    expect(screen.getByText(/RuntimeError · unknown/)).toBeInTheDocument();
    expect(screen.getByText('Run-local script unavailable')).toBeInTheDocument();
    expect(screen.getByText('No sources recorded')).toBeInTheDocument();
    expect(screen.getByText('No persisted storyboard')).toBeInTheDocument();
    expect(screen.getByText('No video recorded')).toBeInTheDocument();
    expect(screen.queryByText(/arxiv\.org/)).not.toBeInTheDocument();
  });
});

describe('Run evidence report', () => {
  it('records missing fields as "not recorded" instead of guessing', () => {
    const report = buildRunReport(detail, undefined, undefined, null);

    expect(report).toContain('# Nextdecode — run console evidence');
    expect(report).toContain('- Run: run-console-001');
    expect(report).toContain('Run-local script record unavailable.');
    expect(report).toContain('No storyboard was persisted for this run.');
    expect(report).toContain('- The dashboard does not run, edit, approve or publish anything.');
  });
});
