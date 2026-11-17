# Providers package

This package owns the shared hosted LLM provider client, model-health probing and exact-model qualification. OmniRoute and Ollama are retired from active routing.

## Modules

- `multi_model_ai.py` — hosted-provider configuration, generation, JSON output and fallback routing.
- `model_health.py` — supported-provider probes, health persistence and unhealthy-provider filtering.
- `omniroute_client.py` — retained legacy module for compatibility only; it is not imported by the active router or health inventory.

## Active automatic provider inventory

The active chain supports:
- Gemini
- Groq
- Pollinations Text
- NVIDIA NIM
- Cloudflare Workers AI
- OpenRouter
- Mistral
- Cerebras

The owner-configured `AI_PROVIDER_CHAIN` controls priority; unknown, duplicate and retired names are ignored. `AI_GENERATION_PROVIDER` may be `auto` or one of the active provider IDs.

**Retired:** OmniRoute (gateway currently offline) and Ollama (owner removed it). Old environment entries are ignored; secret values were not deleted. `NEXTDECODE_AUTONOMY_MODE` is local-only and now fails closed because the old Ollama runtime is retired. It does not silently route autonomous tasks to hosted models.

OpenAI and Anthropic remain direct-call integrations, not automatic free-first chain members. Their presence in a manual/direct path does not silently make them eligible for automatic spend.

## Compatibility and paths

The root-level modules remain import aliases and CLI entrypoints. New code should import from `app.providers`.

The package resolves `PROJECT_ROOT`/health paths back to the repository root so `.env`, `data/token_usage.json` and `data/model_health.json` retain their existing locations.

## Safety boundaries

- This package does not install or enable providers.
- Paid-provider use requires explicit configuration and owner policy.
- No provider probe or live API request runs on package import or CLI `--help`.
- Credentials remain in the root `.env` and are never copied into this package.
- Inventory reads are secret-free and do not make network calls.

## Status semantics

- **Configured:** sufficient non-secret configuration exists to attempt a provider.
- **Health:** last explicit structured-output workload probe passed/failed. Missing or older-than-24-hour probe is `unknown`, not healthy.
- **Routing eligibility:** configured and not within the six-hour cooldown after a recent failed probe.
- Quota state remains unknown unless an authoritative provider response exposes comparable remaining and limit values.

The health gate defaults on. `AI_HEALTH_GATE=false` bypasses health/quota skipping; `AI_IGNORE_HEALTH=1` remains the emergency override.

## Health and inventory operations

- `provider_inventory()` and `GET /providers/inventory` return secret-free configuration and last-known health. They do **not** make network requests.
- `probe_all()` covers every active automatic-chain adapter and validates the same JSON output contract. It performs real provider API calls and writes `data/model_health.json`; invoke it deliberately, not from startup or Dashboard polling.
- Probe exception details are reduced to exception class names so request URLs, headers or credential-bearing error messages are not persisted.
- NVIDIA NIM supports `NVIDIA_API_KEY` and `NVIDIA_API_KEY_2` as sequential credential fallback.

## Model portfolio and qualification

- `config/brain/model_portfolio.v1.json` is a 12-candidate evaluation pool for a final target of 10. It is not an approved production allowlist.
- Automatic selection is disabled; owner approval is required.
- `qualify_portfolio()` sends a bounded structured-output request per candidate and writes `data/model_qualification.json`. It calls the exact named model, not a fallback model chain.
- Repeated same-task benchmark outputs are stored under `data/model_benchmark_v1/`; raw responses are retained for human editorial review.
- Model usage metadata is accumulated per provider/model when returned by the API. Missing token usage remains unknown.
- OpenAI-compatible response rate-limit headers are stored in `data/provider_quota.v1.json`; OpenRouter account quota is queried only during explicit qualification.
- Automatic routing skips a model at 90% consumption only when provider-published remaining and limit values are both available.
- Dashboard portfolio reads do not make external calls.

## NVIDIA findings — 16 Nov 2026

- Both NVIDIA API keys authenticated to the catalog. Earlier Nemotron Bolt and Lightning probes passed some tasks but showed distinct role fit.
- Nemotron Bolt E4B: 3/3 evidence classification, 0/3 production script and 0/3 visual-plan contract in repeated benchmark. Keep as extraction-only provisional candidate.
- Nemotron Lightning 30B A3B: 3/3 script and 3/3 evidence; 0/3 visual-plan contract. Mean script latency ~29.4s. Keep as quality-candidate, not default.
- Nemotron 3.5 Super VL 120B A12B: added as provisional `visual_qa` candidate. Text request and image understanding succeeded through NVIDIA NIM. Needs tests on our own rendered frames/contact sheets; it is not a video generator.
- NVIDIA quota remains unknown where no authoritative rate-limit headers/account counter is exposed.

## Cloudflare findings — 16 Nov 2026

- Both `CF_ACCOUNT_ID` and `CF_API_TOKEN` are required and present.
- `@cf/black-forest-labs/flux-1-schnell` image generation passed a real API test (~4.1s, ~641 KB image).
- `@cf/meta/llama-3.3-70b-instruct-fp8-fast` returned valid JSON but only 46 words against the 92–118-word Shorts requirement. API works; current model is not qualified as the production script writer.
- Free Workers AI allocation is measured in Neurons/day, not request count; see the current official pricing page.
