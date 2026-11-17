export type TaskStateGroup = 'pending' | 'running' | 'completed' | 'failed' | 'blocked' | 'unknown';

const STATE_ALIASES: Record<string, TaskStateGroup> = {
  queued: 'pending',
  pending: 'pending',
  scheduled: 'pending',
  running: 'running',
  started: 'running',
  succeeded: 'completed',
  completed: 'completed',
  done: 'completed',
  success: 'completed',
  failed: 'failed',
  error: 'failed',
  blocked: 'blocked',
  rejected: 'blocked',
};

export function taskStateGroup(status: string): TaskStateGroup {
  return STATE_ALIASES[status.trim().toLowerCase()] ?? 'unknown';
}

export function taskStateLabel(status: string): string {
  const group = taskStateGroup(status);
  if (group === 'unknown') return status ? status.replace(/[_-]/g, ' ') : 'Unknown';
  return ({ pending: 'Pending', running: 'Running', completed: 'Completed',
    failed: 'Failed', blocked: 'Blocked' } as const)[group];
}

export function taskStateTone(status: string): 'good' | 'bad' | 'info' | 'warn' | 'neutral' {
  const group = taskStateGroup(status);
  if (group === 'completed') return 'good';
  if (group === 'failed') return 'bad';
  if (group === 'running') return 'info';
  if (group === 'blocked') return 'warn';
  return 'neutral';
}

export function taskStateIsActive(status: string): boolean {
  const group = taskStateGroup(status);
  return group === 'pending' || group === 'running';
}
