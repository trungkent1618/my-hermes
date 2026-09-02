---
name: cloudflare-mcp
description: Diagnose/fix Cloudflare MCP in Hermes oauth 403 scope 429.
category: cloudflare
---

# Cloudflare MCP in Hermes

## When to use
- User asks "do we have Cloudflare MCP" / "q mcp cloudflare tenemos".
- A cloudflare-* MCP server is enabled but its tools never appear, or `hermes mcp test` fails.
- User expects to perform account actions (create Workers, write KV, edit DNS, manage R2) via MCP and it isn't working.
- You see OAuth errors, `insufficient_scope`, or "Connection failed" on a Cloudflare MCP server.

## DNS record management (custom domains, Dokploy, etc.)
The `cloudflare-api` server is the right tool for **creating/editing DNS records**
(a sibling record's IP is often reusable, e.g. `dokploy.wanderlee.site → A <IP>`).
Worked recipes and the Dokploy custom-domain pattern live in
`references/dns-mcp.md`. Key takeaway: add the A record with `proxied: false`
(grey cloud) so Traefik + Let's Encrypt issues the TLS cert; orange-cloud can
break MCP/WebSocket traffic. `cloudflare-docs` is READ-ONLY and cannot write DNS.

## The Cloudflare MCP servers
Hermes's catalog ships up to five `cloudflare-*` MCP servers (HTTP/StreamableHTTP transport):

- **cloudflare-api** → `https://mcp.cloudflare.com/mcp` — THE action server (Workers, KV, R2, DNS, etc.). Auth: **OAuth 2.1** (`oauth: {}` in config).
- **cloudflare-docs** → `https://docs.mcp.cloudflare.com/mcp` — READ-ONLY documentation index. No account auth needed.
- **cloudflare-bindings** → `https://bindings.mcp.cloudflare.com/mcp`
- **cloudflare-builds** → `https://builds.mcp.cloudflare.com/mcp`
- **cloudflare-observability** → `https://observability.mcp.cloudflare.com/mcp`

The last four are frequently pre-seeded in `config.yaml` like this (the trap):
```yaml
  cloudflare-bindings:
    url: https://bindings.mcp.cloudflare.com/mcp
    headers:
      Authorization: Bearer ${CLOUDFLARE_API_TOKEN}
```
Cloudflare's MCP servers expect **OAuth**, not a static bearer token — see Pitfalls.

## Diagnostic workflow
1. **Inventory:** `hermes mcp list` → Name / Transport / Tools / Status (✓ enabled).
2. **Test:** `hermes mcp test <name>` → reports Transport, Auth, ✓/✗.
   - `Auth: none` on an `oauth: {}` server ⇒ OAuth flow never completed. Fix: `hermes mcp login cloudflare-api` (interactive browser login — the user does it, agent never sees credentials).
   - `✗ Connection failed ... Server returned an error response` ⇒ need a deeper probe (step 3).
3. **Probe the MCP endpoint directly with curl** to see the REAL error (recipes in `references/diagnose.md`): decodes 403 `insufficient_scope` (missing `user:read`/`account:read`) vs 401 vs 429.
4. **Verify the token is valid** against the REST API before blaming it:
   `curl -H "Authorization: Bearer $TOKEN" https://api.cloudflare.com/client/v4/user/tokens/verify` → expect `{"success":true}`.
5. **Confirm which token is in play:** `printenv | grep -i cloudflare` and compare with the profile `.env` (`~/.hermes/profiles/<profile>/.env`). Token lengths can differ between shell env and file — you may be testing the wrong one.

## Fix paths
- **OAuth server (cloudflare-api):** complete `hermes mcp login cloudflare-api`. No static token needed; Cloudflare assigns the right scopes during login.
- **Static-token servers (bindings/builds/observability):** Cloudflare MCP rejects plain bearer tokens with 403 `insufficient_scope`. Preferred fix: convert them to OAuth (`oauth: {}` + `hermes mcp login <name>`). Alternative: mint a token with `User Details: Read` + `Account Settings: Read` scopes in dash.cloudflare.com/profile/api-tokens (the USER must do this — the agent must not handle the secret; reference `${CLOUDFLARE_API_TOKEN}` in config).

## Pitfalls
- **cloudflare-docs is READ-ONLY docs** — it cannot create workers, write KV, or touch DNS. Don't promise account actions from it.
- **A REST-valid token is NOT automatically accepted by the MCP servers.** MCP needs OAuth or the `user:read`/`account:read` scopes; a static bearer is usually rejected (403 `insufficient_scope`). This is the #1 cause of "MCP enabled but failing".
- **429 "Too many authentication failures" is a RATE-LIMIT from repeated bad-auth attempts, NOT proof the token is invalid.** Wait ~15-30s and retry; verify the token separately with the verify endpoint.
- **`hermes mcp test` showing `Auth: none`** on an oauth server means the OAuth handshake was never finished — run `hermes mcp login`.
- **Never write Cloudflare tokens into chat/config in plaintext** — reference `${CLOUDFLARE_API_TOKEN}` and let the user set it in the profile `.env`.

## Verification
After fixing: `hermes mcp test cloudflare-api` should report a successful connection, and account-action tools should appear in the agent's tool list (namespaced `mcp__cloudflare_api__*`).
