# NEXTDECODE Creative Operations — Command Deck v2

Independent redesign in a new directory. `command-deck-v1` and `master-v0.3` are untouched.

## Run
From WSL:
```bash
cd /home/demon/shorts_studio/ui-prototype/command-deck-v2
python3 -m http.server 9020 --bind 0.0.0.0
```
Open: http://127.0.0.1:9020/#/home

If port 9020 is already serving v1, stop only that known prototype server or use another port, e.g. 9021.

## Navigation / naming
- Command: Command Center, Portfolio & Projects, Execution Queue
- Create: Creator Workspace, Production Studio, Content & Asset Library, Research Desk
- Orchestrate: Agent Command, Workflow Canvas, Run Observatory, Schedules & Triggers
- Govern & Release: Review & Decisions, Incidents & Recovery, Evidence & Lineage, Release Guard, Governance & Access
- Learn: Insights & Analytics, Workspace Settings

## Prototype boundaries
- All records, statuses and metrics are illustrative demo content, not live telemetry.
- No backend, database, API, connectors, real agent dispatch, scheduling, production mutation or upload is connected.
- `external_actions_allowed=false`; public publishing remains disabled.
- Local demo agent labels are not canonical WP3 worker registrations.
- Local workflow diagrams and sample runs do not replace canonical WP2/WP4 records.
- Human review approval is separate from protected-action authorization.
- No commits, pushes or production changes were made.
