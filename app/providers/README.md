# Providers package

This package owns the shared LLM provider client, model-health probing and the OmniRoute gateway adapter.

## Modules

- `multi_model_ai.py` — provider configuration, generation, JSON output and fallback routing.
- `model_health.py` — provider probes, health persistence and unhealthy-provider filtering.
- `omniroute_client.py` — OpenAI-compatible local OmniRoute client.

## Compatibility and paths

The root-level modules remain import aliases and CLI entrypoints. New code should import from `app.providers`.

The package resolves `PROJECT_ROOT`/health paths back to the repository root so `.env`, `data/token_usage.json` and `data/model_health.json` retain their existing locations. Provider order, model defaults, health schema and fallback semantics are unchanged by the package move.

## Safety boundaries

- This move does not install or enable providers.
- Existing paid-provider and free-provider policy remains unchanged.
- No provider probe or live API request is run by package import or CLI `--help`.
- Credentials remain in the root `.env` and are not copied into this package.
