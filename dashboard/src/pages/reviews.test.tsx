import type { ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { api, ApiError } from '../api';
import { Reviews } from './reviews';

vi.mock('@tanstack/react-router', () => ({
  Link: ({ children }: { children?: ReactNode }) => <a href="#">{children}</a>,
}));

function renderReviews() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}><Reviews /></QueryClientProvider>);
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('Review desk owner gate', () => {
  it('keeps approval and publishing disabled while required gates fail', async () => {
    vi.spyOn(api, 'pendingReview').mockRejectedValue(new ApiError(409, '/review/pending', 'review_artifact_hash_mismatch'));

    renderReviews();

    expect(await screen.findByText('Review package failed integrity verification')).toBeInTheDocument();
    // The blocked package stays visible with every failure reason
    expect(screen.getByText('2026-11-07 package — stale, mismatched, unreviewed')).toBeInTheDocument();
    expect(screen.getByText(/0 of 7 items marked true/)).toBeInTheDocument();
    expect(screen.getByText('Visual status: draft_only')).toBeInTheDocument();
    expect(screen.getByText(/Single source/)).toBeInTheDocument();
    expect(screen.getByText('Approval & publish: disabled')).toBeInTheDocument();
    // No control anywhere can approve or publish
    expect(screen.queryByRole('button', { name: /approve|publish|upload|post/i })).not.toBeInTheDocument();
    expect(screen.queryByText('All gates pass')).not.toBeInTheDocument();
    // The local repair path is shown with real commands
    expect(screen.getByText(/sha256sum outputs\/output_short\.mp4/)).toBeInTheDocument();
    expect(screen.getByText(/approve_review --interactive/)).toBeInTheDocument();
    expect(screen.getByText(/publish\.orchestration --scheduled-approved/)).toBeInTheDocument();
  });

  it('shows gates for a fresh valid package without claiming approval', async () => {
    const now = new Date().toISOString();
    vi.spyOn(api, 'pendingReview').mockResolvedValue({
      status: 'pending_human_review',
      review_package_sha256: 'abc123def45678901234567890123456789012345678901234567890123456',
      package: {
        title: 'CI test package',
        content_pillar: 'AI You Can Use',
        created_at: now,
        hook: 'Hook line',
        video_sha256: 'def789',
        metadata_sha256: 'meta456',
        target_duration_seconds: 35,
        word_count: 81,
        word_range: [72, 92],
        script_profile: 'standard_35s',
        visual_quality_status: 'pass_with_warnings',
        visuals: { mode: 'licensed', asset_count: 5 },
        source_urls: ['https://example.test/source-a', 'https://example.test/source-b'],
        checklist: { a: true, b: true },
        platform_copy: { youtube_description: 'desc' },
        status: 'pending_human_review',
      },
    } as any);

    renderReviews();

    expect(await screen.findByText('CI test package')).toBeInTheDocument();
    expect(screen.getByText('PUBLISH GATES')).toBeInTheDocument();
    expect(screen.getByText('2/2 complete')).toBeInTheDocument();
    expect(screen.queryByText('Approval recorded')).not.toBeInTheDocument();
    expect(screen.getByText(/Not recorded — local command only/)).toBeInTheDocument();
    // Still no approve/publish button — the CLI is the only approval path
    expect(screen.queryByRole('button', { name: /approve|publish|upload|post/i })).not.toBeInTheDocument();
  });
});
