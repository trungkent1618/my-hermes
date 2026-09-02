---
name: openrouter-free-access
description: Cost-free LLM inference via OpenRouter's free tier — :free model IDs, the openrouter/free vs openrouter/auto router aliases, the 50→1000 requests/day rate-limit mechanic, recommended free models, and how to wire it into Hermes/agents. Use whenever a user wants free/cheap model access, asks about openrouter/free, :free models, rate limits, or whether they need a gateway like OmniRoute.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
---

# OpenRouter Free Access (cost-free LLM inference)

Use this skill when a user is on a free tier, asks "how do I get free models", mentions
`openrouter/free`, `:free` model IDs, rate limits, or whether a self-hosted router
(OmniRoute, etc.) is needed to get "unlimited" free calls.

## Two router aliases (don't confuse them)

- **`openrouter/free`** — picks a random **free** ($0) model that supports the features
  your request needs (image understanding, tool calling, structured output). Cost: $0.
  Best used as a fallback/resilience alias.
- **`openrouter/auto`** — a meta-model reads your prompt and routes to the *best* model for
  the task, with a `cost_quality_tradeoff` dial (0=quality, 10=cheapest). **This can cost
  money** (though some windows are $0). NOT a "free" guarantee. Do not recommend it as the
  no-cost option.

## Rate-limit mechanic (critical to state correctly)

Free-tier requests are **rate-limited, not credit-limited**:
- Account with **< $10 credit on file**: **50 requests/day**.
- Account with **≥ $10 credit on file**: **1,000 requests/day**.

Nuance users get wrong: the "$10 credit" threshold means **$10 loaded into the account**
(a card charge/min deposit), NOT $10 spent. With only free models, those $10 are never
burned — they just sit there raising the cap. So the cheapest way to get 20x more headroom
is a one-time $10 top-up, not paying per token.

## Recommended free models (as of mid-2026 — ROTATES)

Free models churn constantly; always confirm live. Strong picks reported:
- **General/reasoning:** `tencent/hy3:free` (295B MoE, 256K ctx — strong default),
  `meta-llama/llama-4-maverick:free`, `meta-llama/llama-4-scout:free`,
  `moonshotai/kimi-vl-a3b-thinking:free`, `openrouter/optimus-alpha`, `openrouter/quasar-alpha`.
- **Coding:** `qwen3-coder:free` (1M ctx, top free coder), `deepseek/deepseek-v3-base:free`,
  `deepseek/deepseek-r1-distill-llama-70b:free`, `deepseek-v4-flash:free` (1M ctx),
  `nvidia/llama-3.1-nemotron-nano-8b-v1:free`.
- **Multimodal:** `google/gemini-2.5-pro-exp-03-25:free` (experimental, may vanish),
  `qwen/qwen2.5-vl-3b-instruct:free`.

Pitfall: many older guides claim "free DeepSeek/Gemini/Mistral" — those $0 IDs frequently
disappear. Treat any `:free` ID as ephemeral; verify before relying on it.

## Wiring into Hermes / agents

- The model field is just the OpenRouter model name. Set Hermes to `tencent/hy3:free` for the
  primary, and use `openrouter/free` as a fallback alias (if the named free model is rate-limited,
  the router rebounds to another free one).
- No extra infra needed: the OpenRouter API key (`OPENROUTER_API_KEY`) is the only secret.
  The `:free` IDs and the `openrouter/free` alias already do the "routing" — you do NOT need
  OmniRoute, a self-hosted gateway, or Dokploy to get free multi-model access.
- If exposing a self-hosted router anyway (e.g. OmniRoute) to use it as a Hermes custom
  provider, it MUST be self-hosted (not the hosted version) and locked down (auth + IP
  allowlist), because it would hold all your provider API keys.

## Why "unlimited free calls" is a myth

A free router only pools other providers' free tiers. Each still enforces its own RPM / daily
caps, so you get "free until the free tiers saturate", not infinite. Honest framing for users
chasing "unlimited": raise the OpenRouter cap with a $10 deposit, or accept intermittent
rate-limit fallbacks.

## Reference

See `references/free-models.md` for the detailed model/alias/limit table and the verification
recipe (how to confirm live `:free` IDs and current caps).
