export type TaskEventView = { title: string; details: Array<[string, string]> };

const EVENT_LABELS: Record<string, string> = {
  queued: 'Task queued',
  claimed: 'Worker claimed task',
  started: 'Execution started',
  running: 'Execution running',
  heartbeat: 'Worker heartbeat',
  execution_heartbeat: 'Execution heartbeat',
  succeeded: 'Task completed',
  completed: 'Task completed',
  failed: 'Execution failed',
  blocked: 'Execution blocked',
  retry_scheduled: 'Retry scheduled',
  requeued: 'Task returned to queue',
  lease_expired: 'Worker lease expired',
  lease_recovered: 'Task recovered after lease expiry',
  cancelled: 'Execution cancelled',
  dependency_wait: 'Waiting for dependencies',
  dependency_ready: 'Dependencies completed',
};

const PRIVATE_KEY = /(?:secret|password|passwd|token|credential|api[_-]?key|authorization|cookie|session[_-]?key|private[_-]?key)/i;

function sanitizeValue(value: unknown, depth = 0): unknown {
  if (value === null || value === undefined || typeof value === 'number' || typeof value === 'boolean') return value;
  if (typeof value === 'string') return value.length > 300 ? value.slice(0, 297) + '…' : value;
  if (Array.isArray(value)) return value.slice(0, 8).map(item => sanitizeValue(item, depth + 1));
  if (typeof value === 'object') {
    if (depth >= 3) return '[nested object omitted]';
    return Object.fromEntries(Object.entries(value as Record<string, unknown>).slice(0, 12).map(([key, item]) => [
      key, PRIVATE_KEY.test(key) ? '[redacted]' : sanitizeValue(item, depth + 1),
    ]));
  }
  return '[unavailable]';
}

function displayValue(value: unknown): string {
  const safe = sanitizeValue(value);
  if (typeof safe === 'string') return safe;
  try {
    const text = JSON.stringify(safe);
    return text.length > 300 ? text.slice(0, 297) + '…' : text;
  } catch {
    return '[unavailable]';
  }
}

export function presentTaskEvent(event: string, detailJson?: string): TaskEventView {
  const normalized = (event || 'unknown').trim().toLowerCase();
  const title = EVENT_LABELS[normalized] ?? normalized.replace(/[._-]+/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  if (!detailJson) return { title, details: [] };
  try {
    const parsed: unknown = JSON.parse(detailJson);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      return { title, details: [['Detail', displayValue(parsed)]] };
    }
    const details = Object.entries(parsed as Record<string, unknown>)
      .filter(([key]) => !PRIVATE_KEY.test(key))
      .slice(0, 8)
      .map(([key, value]) => [
        key.replace(/[._-]+/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
        displayValue(value),
      ] as [string, string]);
    return { title, details };
  } catch {
    return { title, details: [['Detail', 'Unstructured event detail omitted']] };
  }
}
