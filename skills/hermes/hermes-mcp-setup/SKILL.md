---
name: hermes-mcp-setup
description: Configure/repair Hermes MCP servers and OAuth auth.
---

# Hermes MCP Server Setup & Auth

Class-level skill for managing MCP servers in Hermes Agent. Covers the reliable
non-interactive config path (which the interactive CLI often breaks) and the
Cloudflare OAuth auth model (a common gotcha).

## When to use
- Adding or editing an `mcp_servers` entry in `~/.hermes/profiles/<profile>/config.yaml`.
- A server reports `Auth: none`, `Connection failed`, or `403 insufficient_scope`.
- `hermes mcp add` / `hermes mcp login` fails with "non-interactive environment".
- You need to switch a server from static-token auth to OAuth (or vice versa).

## Reliable non-interactive config (PREFERRED)
The `patch` tool and direct file writes to Hermes config files are BLOCKED by a
security guard ("Refusing to write to Hermes config file ... use 'hermes config'").
Use the `hermes config` CLI instead — it works non-interactively:

```
hermes config set mcp_servers.<name>.url "https://host/mcp"
hermes config set mcp_servers.<name>.oauth "{}"      # empty map = OAuth enabled
hermes config set mcp_servers.<name>.timeout 180
hermes config set mcp_servers.<name>.connect_timeout 60
# to remove a bad static-token header:
hermes config unset mcp_servers.<name>.headers
```

Nested keys use dot notation and ARE saved even if the running version doesn't
recognize them. To switch a server from static Bearer token to OAuth, run
`hermes config unset mcp_servers.<name>.headers` then
`hermes config set mcp_servers.<name>.oauth "{}"`.

## Local command-based MCP servers (stdio)
Some MCP servers are local CLIs, not HTTP endpoints. For these, use `command` and `args` instead of `url`:

``` 
hermes config set mcp_servers.<name>.type "local"
hermes config set mcp_servers.<name>.command "<binary>"
hermes config set mcp_servers.<name>.args '["subcommand", "--flag"]'
```

Example for Engram, already installed system-wide:
``` 
hermes config set mcp_servers.engram.type "local"
hermes config set mcp_servers.engram.command "engram"
hermes config set mcp_servers.engram.args '["mcp"]'
```

Verify with `hermes mcp list` after reload. No OAuth, no token, no browser is involved for local stdio servers.

See `references/engram-mcp-local.md` for installed Engram version, Cloud setup, sync commands, and the verified `telegram-bot` profile replication steps.

## PITFALL: `hermes mcp add` is interactive and destructive
- `hermes mcp add <name> --url ... --auth oauth` prompts and, in a headless/non-TTY
  environment, errors with "non-interactive environment and no cached tokens found"
  and does NOT save the config.
- Worse, if you do `hermes mcp remove <name>` then `hermes mcp add <name>` and the
  add fails interactively, the server is GONE from config.yaml (the remove succeeded,
  the add did not). Always re-add via `hermes config set` afterward if this happens.
- `hermes mcp login <name>` ALSO requires a real browser plus TTY — it cannot complete
  in a headless agent environment. The user must run it on their own machine.

## Verify
```
hermes mcp list                                  # shows Status: enabled
hermes mcp test <name>                           # tests connection (needs working auth)
```
`hermes mcp test` on an OAuth server before login reports `Auth: none` and fails —
expected until the user completes `hermes mcp login <name>` in a browser.
`hermes mcp test` on a local stdio server validates startup only; it does not imply network auth.

## Cloudflare MCP auth model (common case)
See `references/cloudflare-mcp-auth.md` for the full breakdown. TL;DR:
- All `*.mcp.cloudflare.com` servers (bindings, builds, observability, docs) have
  built-in Cloudflare OAuth. They REJECT static `Authorization: Bearer` tokens
  with `403 insufficient_scope`. Configure them with `oauth: {}` and complete
  `hermes mcp login <name>` in a browser.
- `mcp.cloudflare.com` (Code Mode server) accepts BOTH OAuth (recommended) AND a
  static API token (for CI; account tokens need `Account Resources: Read`; no IP filtering).

## Cross-profile note
MCP config lives per-profile under `~/.hermes/profiles/<profile>/config.yaml`.
Writing to ANOTHER profile's config is blocked by the cross-profile guard — only
edit the active/current profile unless the user explicitly directs otherwise.
