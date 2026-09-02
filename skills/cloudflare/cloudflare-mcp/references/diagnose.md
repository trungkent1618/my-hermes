# Cloudflare MCP — diagnostic recipes

Reusable probes. Never print the token value; read it into a shell var.

## 1. Verify a token is valid against the REST API
```bash
TOK=$(grep '^CLOUDFLARE_API_TOKEN=' ~/.hermes/profiles/<profile>/.env | cut -d= -f2-)
curl -s -o /tmp/cf_verify.json -w "HTTP %{http_code}\n" \
  -H "Authorization: Bearer $TOK" \
  https://api.cloudflare.com/client/v4/user/tokens/verify
python3 -c "import json;d=json.load(open('/tmp/cf_verify.json'));print('success:',d.get('success'));[print('err',e.get('code'),e.get('message')) for e in d.get('errors',[])]"
```
Expect `HTTP 200`, `success: True`. A valid REST token does NOT guarantee MCP acceptance.

## 2. Probe the MCP endpoint directly to see the REAL error
`hermes mcp test` hides the cause behind "Server returned an error response". Hit the endpoint with an `initialize` JSON-RPC call:
```bash
curl -s -o /tmp/mcp_resp.json -w "HTTP %{http_code}\n" -X POST "https://bindings.mcp.cloudflare.com/mcp" \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
head -c 800 /tmp/mcp_resp.json
```
Observed real errors:
- `403 {"error":"insufficient_scope","error_description":"Token lacks required user:read or account:read scope"}` → static bearer rejected; needs OAuth or those scopes.
- `429 "Too many authentication failures"` → rate-limit from repeated bad auth; wait 15-30s, then retry. NOT proof the token is invalid.
- `401` → bad/expired token.

## 3. Which token is actually in play
```bash
printenv | grep -i cloudflare          # token in current shell
grep '^CLOUDFLARE_API_TOKEN=' ~/.hermes/profiles/<profile>/.env | cut -d= -f2- | wc -c   # token in file
```
Token lengths can differ between shell env and the profile `.env` — you may be testing the wrong one. Use the file's token for the probes above (that's what the MCP server config expands).

## 4. Hermes CLI commands
- `hermes mcp list` — inventory + enabled status.
- `hermes mcp test <name>` — connection test (reports Transport / Auth / ✓✗).
- `hermes mcp login <name>` — complete OAuth for an `oauth: {}` server (interactive browser flow; user authenticates).
- `hermes mcp reauth --all` — re-authenticate all OAuth servers.
