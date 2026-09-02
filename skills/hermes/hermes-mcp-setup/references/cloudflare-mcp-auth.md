# Cloudflare MCP Auth Model

Source: official repo `github.com/cloudflare/mcp-server-cloudflare` and
`github.com/cloudflare/mcp`, README verified Aug 2026.

## Two server families

1. **Domain-specific servers** (`*.mcp.cloudflare.com`)
   - `bindings.mcp.cloudflare.com/mcp` (Workers Bindings: KV, R2, D1, Hyperdrive)
   - `builds.mcp.cloudflare.com/mcp` (Workers Builds)
   - `observability.mcp.cloudflare.com/mcp` (logs/analytics)
   - `docs.mcp.cloudflare.com/mcp` (documentation search — public, no auth)
   - Others: containers, browser, logpush, ai-gateway, autorag, auditlogs,
     dns-analytics, radar, blog, etc.
   - All have **built-in Cloudflare OAuth**. The per-server README says:
     "Connect your MCP client directly to the URL. If prompted, complete the
     Cloudflare OAuth flow in your browser."
   - They **REJECT** static `Authorization: Bearer <token>` headers. Observed
     error: `HTTP 403 {"error":"insufficient_scope","error_description":
     "Token lacks required user:read or account:read scope"}`.
   - Config form: `oauth: {}` (no headers). Auth completed via
     `hermes mcp login <name>` in an interactive browser session.

2. **Code Mode server** (`mcp.cloudflare.com/mcp`)
   - Token-efficient: 3 tools (`docs`, `search`, `execute`) that run JS against
     the Cloudflare OpenAPI spec + your account. Covers 2500+ endpoints.
   - Accepts **BOTH** auth methods:
     - **OAuth (recommended)**: connect to the URL, redirect to Cloudflare to
       authorize + select permissions. Config: `oauth: {}`.
     - **API Token** (CI/automation): Bearer token works. Both user and account
       tokens supported. For account tokens, include **Account Resources: Read**
       so the server auto-detects account_id. NOTE: tokens with **Client IP
       Address Filtering** enabled are NOT supported.
   - Disable code mode with `?codemode=false` to get one tool per endpoint
     (~244k tokens vs ~1k — only when composing with another code-mode system).

## What the agent can do once authenticated (Code Mode `execute`)
- Deploy Workers: `PUT /accounts/{account_id}/workers/scripts/{name}` with code.
- Create resources: KV namespaces, R2 buckets, D1 DBs, Hyperdrive (also via
  `bindings` server's typed tools: `kv_namespace_create`, `r2_bucket_create`,
  `d1_database_create`, etc.).
- Custom domain on a Worker: `POST /accounts/{account_id}/workers/domains`
  (requires the zone already in Cloudflare).
- New zone: `POST /zones` + `POST /zones/{zone_id}/dns_records` create it; the
  final step (changing nameservers at the registrar — GoDaddy, Namecheap, etc.)
  is MANUAL and cannot be done via MCP.

## Auth troubleshooting
- `hermes mcp test` shows `Auth: none` and fails → OAuth never completed.
- `403 insufficient_scope` on a `*.mcp.cloudflare.com` server → you passed a
  static Bearer token; switch to `oauth: {}` + browser login.
- OAuth login must be run by the USER on a machine with a browser + TTY.
  The headless agent cannot complete it.
