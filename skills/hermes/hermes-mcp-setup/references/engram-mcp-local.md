# Engram MCP local + Engram Cloud

## Instalado y configurado
- Binario: `engram` v1.20.0
- MCP config en Hermes: `command: engram`, `args: ["mcp"]`, `type: local`
- Estado: habilitado en `coder` y `telegram-bot`
- No requiere OAuth ni browser; solo stdio local

## Comandos útiles
- `engram whoami` / `wrangler whoami`: verifica sesión/token activo
- `engram mcp --tools=agent|admin|all`: perfiles de herramientas MCP
- `engram cloud status|enroll|config|serve`: cloud replication
- `engram sync --cloud --project <name>`: sincronizar proyecto explícito
- `engram doctor`: diagnóstico local

## Cloud
- Opt-in, local-first; SQLite local sigue siendo la fuente de verdad
- Imagen oficial: `ghcr.io/gentleman-programming/engram`
- Docker Compose ejemplo: `docs/engram-cloud/docker-compose.cloud.yml`
- Sync siempre requiere `--project` explícito

## Perfil telegram-bot
- Skills de Cloudflare sincronizadas desde `coder`
- MCPs replicados: cloudflare-* + engram
