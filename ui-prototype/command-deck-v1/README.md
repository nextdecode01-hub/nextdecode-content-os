# NEXTDECODE Command Deck v1

Independent prototype, separate from `master-v0.3` and all earlier variants.

## Run

From WSL:
```bash
cd /home/demon/shorts_studio/ui-prototype/command-deck-v1
python3 -m http.server 9020 --bind 0.0.0.0
```
Open `http://127.0.0.1:9020/#/overview`.

## Experience
- Situation room: executive signal, operational confidence, KPIs, critical path, production topology, work ownership, decisions, incidents, agent operations, event stream and trust posture.
- Portfolio map, work & ownership, agent operations, workflow observability, incident command, decision register, evidence & provenance, production floor, release control, intelligence, and policy & boundaries.
- Interactive record detail drawer, work queue filters, route navigation, responsive mobile sidebar, keyboard shortcuts and toast feedback.

## Governance
- All metrics and records are illustrative demo data, not production telemetry.
- No backend, database, API, live connectors, real agent dispatch, or production mutation is connected.
- No upload, scheduling, approval mutation or publishing action is implemented.
- `external_actions_allowed=false`; public publishing remains disabled.
- Local runtime IDs, local events and review states do not replace canonical WP2/WP3/WP4/WP5 contracts.
- Human review approval and protected publishing authorization remain separate.

## Verification
- Windows HTTP retrieval on port 9020 returned HTTP 200 (55,706 bytes at the last check).
- Windows Chrome headless DOM inspection returned the rendered overview page content.
- Visual appearance in the user's interactive Chrome session still needs their confirmation.
- No commit or push was performed.
