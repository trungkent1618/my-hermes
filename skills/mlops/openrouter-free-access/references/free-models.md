# OpenRouter Free Tier — Model / Alias / Limit Reference

State captured: mid-2026. Free models rotate; re-verify before relying on any `:free` ID.

## Aliases

| Alias | Behavior | Cost | Use as |
|-------|----------|------|--------|
| `openrouter/free` | Random $0 model that satisfies request features (vision, tools, structured output) | $0 | Primary or fallback for free access |
| `openrouter/auto` | Meta-model routes to best model for task via `cost_quality_tradeoff` (0=quality,10=cheap) | Can charge (some $0 windows) | Quality, NOT a free guarantee |

## Rate-limit mechanic

- < $10 credit on file => 50 requests/day
- >= $10 credit on file => 1,000 requests/day
- "Credit on file" = $10 loaded/deposited (card), NOT $10 spent. Free models never burn it.
- Cheapest 20x headroom = one-time $10 deposit; per-token cost stays $0 for `:free` IDs.

## Free model picks (ephemeral — verify live)

General / reasoning:
- `tencent/hy3:free` — 295B MoE, 21B active, 192 experts top-8, 256K ctx, 4 providers. Strong default.
- `meta-llama/llama-4-maverick:free`, `meta-llama/llama-4-scout:free`
- `moonshotai/kimi-vl-a3b-thinking:free`
- `openrouter/optimus-alpha`, `openrouter/quasar-alpha` (rotating OpenRouter-curated)

Coding:
- `qwen3-coder:free` — 1M ctx, top free coder
- `deepseek/deepseek-v3-base:free`
- `deepseek/deepseek-r1-distill-llama-70b:free`
- `deepseek-v4-flash:free` — 1M ctx, native reasoning
- `nvidia/llama-3.1-nemotron-nano-8b-v1:free`

Multimodal:
- `google/gemini-2.5-pro-exp-03-25:free` (experimental, may vanish)
- `qwen/qwen2.5-vl-3b-instruct:free`

## Verification recipe (run before trusting an ID)

1. `web_search` "openrouter free models list <month year>" — cross-check current IDs.
2. OpenRouter model page pattern: `https://openrouter.ai/<model-id>` — shows $0 pricing + context.
3. For the live free collection: `https://openrouter.ai/collections/free-models`.
4. To confirm your account's actual cap: check OpenRouter dashboard / account credits, not just docs.

## Wiring into Hermes

- Primary model: `tencent/hy3:free`. Fallback alias: `openrouter/free` (rebounds when hy3 saturates).
- Only secret needed: `OPENROUTER_API_KEY` in `~/.hermes/.env`.
- No OmniRoute / Dokploy / self-hosted gateway required for free multi-model access — the `:free`
  IDs + `openrouter/free` alias already do the routing.
- If self-hosting a router (OmniRoute) to use as a Hermes custom provider, self-host it and lock
  it down (auth + IP allowlist) because it holds all provider keys.
