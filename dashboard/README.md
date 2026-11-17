# NEXTDECODE Dashboard — local connected vertical slice

React + TypeScript + Vite, TanStack Router/Query, Tailwind CSS v4 and Lucide. Connected read-only to the existing local FastAPI autonomy API.

Run: `npm install && npm run dev` then open http://127.0.0.1:5173.

The Vite dev server binds to loopback only. Its server-side proxy reads SHORTS_STUDIO_API_KEY from ~/.config/nextdecode/api.env and injects the bearer header when proxying to 127.0.0.1:8765. The key is not included in browser code. Never expose this development server to a LAN/public network. This is not production authentication; WP3-B production session/auth/CSRF and authorization-aware read services remain open.

Live read endpoints: /autonomy/health, /tasks, /tasks/{id}, /capabilities. No task mutations, dispatch, approval, upload or publishing controls are present.

The connected database is the local autonomy runtime only: task_plans, tasks, task_dependencies, task_events, plan_idempotency, worker_heartbeats. It is not the canonical P0 shared control plane. Local task IDs are not canonical WP2 IDs; worker heartbeats are not canonical WP3 registrations. Projects, content, research, reviews, governance and analytics remain intentionally unconnected rather than populated with fake data.

## Additional live read surfaces
- `GET /autonomy/dead-letters?limit=100` — terminal failures, read-only; no retry/requeue action.
- `GET /plans/{plan_id}` — stored local autonomy plan document and its task/dependency records.

The Plan Topology screen derives its plan list from plan-linked tasks and renders the persisted plan JSON, step IDs, dependency references, execution status and task detail links. It does not create or mutate plans. Global search (`Ctrl+K` / `Cmd+K`) searches the current task and capability read models in the browser and navigates to the selected read-only record. Search is not a global full-text index and does not search payload/result bodies.

## Connected product surfaces added (read-only)
- /jobs — existing in-memory legacy /jobs registry. These job records are distinct from durable autonomy tasks and canonical WP2 jobs; no start/cancel actions are exposed.
- /reviews — active /review/pending package, exact package/video/metadata SHA-256 values, source URLs, visual metadata, platform copy and checklist. This is an inspection surface only; it cannot approve/reject/extend or publish. A 404 from the review service is presented as an empty queue.
- Navigation labels expose the production job monitor and review desk. All API calls remain behind the loopback-only Vite server proxy; API keys stay server-side.

The review page displays package hashes returned by the service but does not claim to hash or visually inspect the underlying media bytes. Review completion and protected publishing authorization remain distinct.
