# Provider Inventory API Contract — 15 November 2026

**Owner:** Provider runtime / backend  
**Consumer:** Dashboard settings (independent frontend workstream)  
**Status:** Implemented, read-only

## Endpoint

`GET /providers/inventory`

Authentication: existing `Authorization: Bearer <SHORTS_STUDIO_API_KEY>` dependency, attached at router registration.

This endpoint is a configuration/last-known-health read. It makes **no external provider requests**, writes no files, and never returns API keys or secret values.

## Response

```json
{
  "schema": "nextdecode.providers.inventory.v1",
  "default_provider": "auto",
  "provider_order": ["nvidia", "groq", "gemini"],
  "health_gate_enabled": true,
  "providers": [
    {
      "id": "groq",
      "model": "configured model name",
      "configured": true,
      "configuration_status": "configured",
      "health": "unknown",
      "last_checked_at": null,
      "latency_ms": null,
      "last_error": null,
      "eligible_for_routing": true
    }
  ],
  "live_probe_performed": false
}
```

`providers` includes every active automatic-chain adapter: `gemini`, `groq`, `pollinations_text`, `nvidia`, `cloudflare`, `openrouter`, `mistral`, `cerebras`. OmniRoute is retired because its gateway is offline; Ollama was removed by the owner. Neither appears in active routing or health inventory.

## Status semantics

- `configured`: credentials/settings exist; not proof of network health.
- `health=healthy`: explicit JSON workload probe passed within 24 hours.
- `health=unhealthy`: explicit probe failed within 24 hours.
- `health=unknown`: never probed or last probe is stale.
- `eligible_for_routing`: configured and not currently suppressed by a recent failed-probe cooldown.
- `live_probe_performed=false`: this endpoint never runs probes.

Dashboard must not label configured as connected/healthy. It should show unknown as “Not checked” or “Unknown”, not as failed. No provider settings mutation, key editing, model changes or probe trigger is exposed by this endpoint.

## Probe execution

`app.providers.model_health.probe_all()` explicitly contacts configured providers and persists the outcome in `data/model_health.json`. This is a potentially billable/external operation and must not be triggered by page refresh, polling, API startup or dashboard query. A separate owner-approved operator action can be designed later.

## Model preservation

The API reports the model values resolved by the existing provider-specific environment/default configuration. It does not change models, credentials, endpoints, or the existing owner-configured chain priority.


## Model portfolio Dashboard integration — 15 Nov 2026

The provider page should consume:

- `GET /providers/inventory` — provider configuration, status and routing order.
- `GET /providers/portfolio` — ten candidate models, use cases, exact-model qualification result, observed per-model token usage and provider quota snapshot.

Suggested Dashboard columns:
- Model + provider
- Qualification: passed / failed / not tested
- Use case / role
- Latency (ms)
- Estimated output words/s (label as estimate; do not call it tokens/s)
- Actual input/output/total tokens from usage metadata, when exposed
- Remaining requests/tokens/credits, only when returned by provider
- Quota state: normal / >=90% used / unknown
- Last checked timestamp

The portfolio is not yet the production allowlist. The current first pass has four successful candidates and six failures; owner approval is required before promoting any model to a production role. A single successful test is not a robust quality score. Repeated same-prompt and task-specific evaluation should follow.

### Automatic 90% failover

The runtime skips a model/provider when an authoritative provider counter proves at least 90% consumption:
- Groq: model-specific token/request rate-limit headers.
- OpenRouter: account free-model daily request counter / available credit fields.
- Other providers: only if their API response supplies a comparable remaining + limit pair.

For Gemini and providers that do not expose remaining quota to the API key, show quota as unknown and continue to rely on actual rate-limit errors and health-based fallback. Do not infer quota from local token usage as if it were the provider's remaining allowance.

The provider chain continues to respect the owner's priority. A quota-saturated model is skipped; the next model/provider is attempted. `AI_HEALTH_GATE=false` disables both health/quota skipping; `AI_IGNORE_HEALTH=1` is the explicit emergency override.


## Owner correction and 16 Nov 2026 active-provider update

- OmniRoute is offline and removed from active routing.
- Ollama was already removed by the owner and is removed from active routing.
- Active inventory now exposes eight hosted adapters: Gemini, Groq, Pollinations Text, NVIDIA, Cloudflare, OpenRouter, Mistral and Cerebras.
- Cerebras and Mistral are currently not configured; they remain optional adapters.
- The current portfolio target is 10 production models, with 12 provisional candidates (Nemotron Super VL was added as a visual-QA candidate). No automatic promotion.
- Gemini/Groq free quotas are owner-confirmed as quickly exhausted; quota must be represented from authoritative counters where available, otherwise unknown.
- Cloudflare requires both `CF_ACCOUNT_ID` and `CF_API_TOKEN`; both are configured. Its image generation endpoint passed a live test. Current text model returned JSON but failed the required 92–118-word script length.
- NVIDIA Nemotron Super VL passed a live text test and a streamed image-understanding test; it is a provisional visual-QA candidate, not a video generator.
