# Cloudflare DNS via the `cloudflare-api` MCP server

The action server for DNS (and most account mutations) is **`cloudflare-api`** →
`https://mcp.cloudflare.com/mcp`. It exposes a single code-execution tool:
`mcp__cloudflare_api__execute`, which runs an async arrow function with
`cloudflare.request({ method, path, query?, body?, contentType?, rawBody? })`.

> `cloudflare-docs` is READ-ONLY — it cannot create or edit DNS records. Use
> `cloudflare-api` for any write.

## Context pre-set in the sandbox
- `accountId` is already in scope (e.g. the Maxdeploys@gmail.com account). You
  can use it directly in API paths like `/accounts/${accountId}/...`.
- Zone-scoped DNS endpoints use the **zone_id**, not the account. Look it up once.

## Recipes

### Resolve the zone_id for a domain
```js
async () => {
  const z = await cloudflare.request({ method: 'GET', path: '/zones', query: { name: 'wanderlee.site' } });
  return z.result[0].id; // e.g. f88881245f2d58f22d52de8598ca180a
};
```

### List existing DNS records (inspect before adding)
```js
async () => {
  const zid = '<zone_id>';
  const r = await cloudflare.request({ method: 'GET', path: `/zones/${zid}/dns_records`, query: { per_page: 100 } });
  return r.result.map(x => ({ name: x.name, type: x.type, content: x.content, proxied: x.proxied }));
};
```

### Create an A record (custom domain for a self-hosted service)
```js
async () => {
  const zid = '<zone_id>';
  const r = await cloudflare.request({
    method: 'POST',
    path: `/zones/${zid}/dns_records`,
    body: { type: 'A', name: 'engram.wanderlee.site', content: '161.153.193.243', ttl: 1, proxied: false }
  });
  return { success: r.success, errors: r.errors,
           record: r.result && { id: r.result.id, name: r.result.name, type: r.result.type, content: r.result.content, proxied: r.result.proxied } };
};
```
`ttl: 1` = "Automatic" in the dashboard. `proxied: false` = grey-cloud (DNS only).

## Pattern: custom domain for a service deployed on Dokploy
1. Find the Dokploy server's public IP. Often a sibling record already exists,
   e.g. `dokploy.wanderlee.site → A <IP>` — reuse that same IP for the new
   subdomain so it lands on the same Traefik ingress.
2. Create the A record with **`proxied: false`** (grey cloud).
   - Traefik + Let's Encrypt issues the TLS cert at the server (ACME HTTP-01).
   - Orange-cloud (proxied: true) terminates TLS at Cloudflare and can break
     long-lived / non-HTTP traffic such as MCP streams or WebSockets.
3. In the Dokploy UI, open the service → **Domains** → add `sub.domain.tld`.
   Traefik provisions the Let's Encrypt cert automatically.
4. Verify propagation: `dig +short sub.domain.tld` (or just curl the host once
   Dokploy shows it healthy).

## Notes / pitfalls
- DNS writes need `#dns_records:edit` on the token — the OAuth `cloudflare-api`
  login grants this by default.
- Don't bake the IP into a skill permanently; read the zone first (records change).
- `cloudflare-api` must be authorized via OAuth (`hermes mcp login cloudflare-api`).
  Static bearer tokens are rejected (403 insufficient_scope). See this skill's
  main SKILL.md for the auth diagnostic.
