import type { ReactNode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { Distribution } from './distribution';

vi.mock('@tanstack/react-router', () => ({
  Link: ({ children }: { children?: ReactNode }) => <a href="#">{children}</a>,
}));

beforeEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

afterEach(() => {
  cleanup();
});

describe('Distribution publish control', () => {
  it('offers real manual and scheduled modes and prepares a copyable command', async () => {
    const exec = vi.fn(() => true);
    Object.defineProperty(document, 'execCommand', { value: exec, configurable: true });

    render(<Distribution />);

    const manual = screen.getByRole('radio', { name: /manual/i });
    const scheduled = screen.getByRole('radio', { name: /automatic/i });

    // Scheduled is the safe default and shows the 20:00 IST command.
    expect(scheduled).toHaveAttribute('aria-checked', 'true');
    expect(manual).toHaveAttribute('aria-checked', 'false');
    expect(screen.getByText(/orchestration --scheduled-approved/)).toBeInTheDocument();

    // Switching mode is genuinely wired and rewrites the prepared command.
    fireEvent.click(manual);
    expect(manual).toHaveAttribute('aria-checked', 'true');
    expect(scheduled).toHaveAttribute('aria-checked', 'false');
    expect(screen.getByText(/PUBLISH_MODE=publish AUTO_PUBLISH_APPROVED=true/)).toBeInTheDocument();

    // Copy button is real: it invokes the clipboard path and confirms it.
    fireEvent.click(screen.getByRole('button', { name: /copy command/i }));
    expect(exec).toHaveBeenCalled();
    expect(await screen.findByText('Copied')).toBeInTheDocument();
  });

  it('never exposes an upload/execute control in the browser', () => {
    render(<Distribution />);
    // The only actions are the mode switch, copy and script download.
    for (const button of screen.getAllByRole('button')) {
      expect(button.textContent).not.toMatch(/^(upload|publish now|execute|run now)/i);
    }
    // Blocked gates are stated honestly.
    expect(screen.getByText('Publishing is locked by failing gates')).toBeInTheDocument();
  });
});
