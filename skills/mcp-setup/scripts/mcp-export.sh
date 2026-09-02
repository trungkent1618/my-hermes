#!/bin/bash
# mcp-export.sh — Exporta MCPs configurados a JSON (sin secrets)
# Uso: ./scripts/mcp-export.sh [filter]
# Ejemplo: ./scripts/mcp-export.sh cloudflare

set -e

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT="$SKILL_DIR/references/mcp-inventory.json"
FILTER="${1:-}"

echo "=== Exportar MCPs ==="
[ -n "$FILTER" ] && echo "Filtro: $FILTER"
echo ""

if ! command -v hermes &>/dev/null; then
    echo "ERROR: hermes CLI no encontrado"
    exit 1
fi

# URLs conocidas de Cloudflare MCP
declare -A KNOWN_URLS=(
    [cloudflare-api]="https://mcp.cloudflare.com/mcp"
    [cloudflare-bindings]="https://bindings.mcp.cloudflare.com/mcp"
    [cloudflare-builds]="https://builds.mcp.cloudflare.com/mcp"
    [cloudflare-observability]="https://observability.mcp.cloudflare.com/mcp"
    [cloudflare-docs]="https://docs.mcp.cloudflare.com/mcp"
)

MCP_LIST=$(hermes mcp list 2>/dev/null | tail -n +3 | grep -v "^$" | grep "^  [a-zA-Z]" | grep -v "^  Name ")

if [ -z "$MCP_LIST" ]; then
    echo "No se encontraron MCPs configurados."
    exit 0
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Construir JSON con python
FILTER="$FILTER" TIMESTAMP="$TIMESTAMP" OUTPUT="$OUTPUT" MCP_LIST="$MCP_LIST" python3 << 'EOF'
import json, os

filter_str = os.environ.get("FILTER", "")
timestamp = os.environ["TIMESTAMP"]
output = os.environ["OUTPUT"]

# URLs conocidas
known_urls = {
    "cloudflare-api": "https://mcp.cloudflare.com/mcp",
    "cloudflare-bindings": "https://bindings.mcp.cloudflare.com/mcp",
    "cloudflare-builds": "https://builds.mcp.cloudflare.com/mcp",
    "cloudflare-observability": "https://observability.mcp.cloudflare.com/mcp",
    "cloudflare-docs": "https://docs.mcp.cloudflare.com/mcp",
}

mcp_list = os.environ["MCP_LIST"]
entries = []

for line in mcp_list.strip().split("\n"):
    parts = line.split()
    if len(parts) < 2:
        continue
    
    name = parts[0]
    
    # Filtrar
    if filter_str and filter_str.lower() not in name.lower():
        continue
    
    # Buscar URL conocida
    url = known_urls.get(name, "")
    
    # Detectar auth
    if url and "cloudflare" in url:
        auth = "oauth"
    elif url:
        auth = "unknown"
    else:
        auth = "none"
    
    entries.append({
        "name": name,
        "url": url,
        "auth": auth,
        "status": "enabled"
    })

data = {"exported_at": timestamp, "mcp": entries}

with open(output, "w") as f:
    json.dump(data, f, indent=2)

print(f"Exportados {len(entries)} MCPs")
for e in entries:
    url_display = e["url"][:50] + "..." if len(e["url"]) > 50 else e["url"]
    print(f"  - {e['name']} ({e['auth']}) {url_display}")
EOF

echo "Exportado a: $OUTPUT"
