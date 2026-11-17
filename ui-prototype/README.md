# NEXTDECODE Control Center — Visual Prototype

Status: isolated, non-production UI exploration.

## Open
Open `index.html` directly in a browser. No build step, package installation, server, API key, network request or external dependency is required.

## Scope
- Clickable navigation shell for the planned Control Center areas.
- Overview concept with illustrative pipeline, review queue and activity.
- Responsive desktop/mobile layout.
- All displayed operational values are sample data.

## Explicit non-capabilities
- Does not connect to `api/main.py` or any backend.
- Does not read or mutate project, workflow, approval, authorization or publishing state.
- Does not trigger generation, upload, export or public publishing.
- Does not implement P1 modules or override P0/P1 scope gates.

## Governance
This prototype is for visual feedback only. It is not an implementation baseline, canonical product decision, frontend architecture selection, or production-readiness evidence. Any production integration must follow the accepted P0 contracts, P1 authorization and the relevant owner decisions.
