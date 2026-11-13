# AI Provider Test Report
**Date:** 2026-10-22  
**Test Type:** JSON Generation (real workload: short-form script generation)

## Results Summary

| Provider | Primary Model | Status | Latency | Issue |
|----------|---------------|--------|---------|-------|
| **Groq** | qwen/qwen3.8-27b | ✅ WORKING | 1.8s | None |
| **OmniRoute** | groq/openai/gpt-oss-120b | ✅ WORKING | 4.2s | None |
| **Ollama** | gemma3:4b | ✅ WORKING | 51.6s | Not in .env (slow) |
| **Gemini (primary)** | gemini-3.5-flash | ❌ BROKEN | — | Quota exceeded (429) |
| **Gemini (fallback 1)** | gemini-flash-latest | ❌ BROKEN | — | Quota exceeded (429) |
| **Gemini (fallback 2)** | gemini-3.5-flash-lite | ✅ WORKING | 10.8s | Works, but slow |

## Detailed Findings

### ✅ WORKING PROVIDERS

**Groq Chain**
- `groq/qwen/qwen3.8-27b` → OK (1.8s) ✅
- `groq/openai/gpt-oss-20b` → OK (1.8s) ✅
- `groq/openai/gpt-oss-120b` → OK (2.5s) ✅

**OmniRoute Gateway**
- `groq/openai/gpt-oss-120b` → OK (4.2s) ✅
- Gateway has 1835+ available models (auto routing, multi-provider)

**Ollama Local**
- `gemma3:4b` → OK (51.6s) ⚠️ SLOW
- Running on localhost:11434
- **Not configured in .env** (health check marked as "not_configured")

### ❌ BROKEN PROVIDERS

**Gemini Free Tier (Primary & Fallback 1)**
- `gemini-3.5-flash` → QUOTA EXCEEDED (429)
- `gemini-flash-latest` → QUOTA EXCEEDED (429)
- Root cause: Free tier rate limits exhausted
- Error: "You exceeded your current quota, please check your plan and billing details"

**Gemini Lite (Fallback 2)**
- `gemini-3.5-flash-lite` → OK (10.8s) ✅
- Only working Gemini model but slower than Groq/OmniRoute

## Recommendations

### 1. **Fix Gemini Chain** (IMMEDIATE)
**Current:**
```
GEMINI_MODEL=gemini-3.5-flash
GEMINI_FALLBACK_MODELS=gemini-flash-latest,gemini-3.5-flash-lite
```

**Should be:**
```
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_FALLBACK_MODELS=  # (empty, only lite model works)
```

### 2. **Add Ollama to .env** (OPTIONAL)
Ollama server is running but not in configuration. It's slow (51.6s) so don't prioritize, but document it:
```
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=gemma3:4b
```

### 3. **Update Provider Chain** (RECOMMENDED)
**Current:**
```
AI_PROVIDER_CHAIN=groq,omniroute,gemini,ollama
```

**Should be:**
```
AI_PROVIDER_CHAIN=groq,omniroute,gemini
```
(Ollama is 10-60x slower; use only if primary chain fails)

### 4. **Keep Health Gate Enabled** (ALREADY SET)
```
AI_HEALTH_GATE=true  # ✅ Already enabled
```
This will skip unhealthy providers automatically.

## Performance Ranking

| Rank | Provider | Model | Speed | Reliability |
|------|----------|-------|-------|-------------|
| 1 | Groq | qwen/qwen3.8-27b | 1.8s | Excellent |
| 2 | OmniRoute | groq/openai/gpt-oss-120b | 4.2s | Excellent |
| 3 | Gemini | gemini-3.5-flash-lite | 10.8s | Good |
| 4 | Ollama | gemma3:4b | 51.6s | Good (if local) |

## Action Items

- [x] Test all providers
- [x] Identify broken models (Gemini primary tier)
- [ ] **Update `.env` GEMINI_MODEL to gemini-3.5-flash-lite**
- [ ] **Prune GEMINI_FALLBACK_MODELS (keep only lite)**
- [ ] Optionally add Ollama to .env (not urgent)
- [ ] Run health probe after changes: `python3 model_health.py --probe --prune`
