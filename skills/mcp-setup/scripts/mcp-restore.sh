#!/bin/bash
# mcp-restore.sh — Restaura MCPs desde el inventario JSON
# Uso: ./scripts/mcp-restore.sh

set -e

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INPUT="$SKILL_DIR/references/mcp-inventory.json"

echo "=== Restaurar MCPs ==="
echo ""

if ! command -v hermes &>/dev/null; then
    echo "ERROR: hermes CLI no encontrado"
    exit 1
fi

if [ ! -f "$INPUT" ]; then
    echo "ERROR: No se encontró $INPUT"
    echo "Ejecutá primero: ./scripts/mcp-export.sh"
    exit 1
fi

MCP_COUNT=$(python3 -c "import json; data=json.load(open('$INPUT')); print(len(data['mcp']))")

echo "MCPs a restaurar: $MCP_COUNT"
echo ""

# Restaurar cada MCP
INPUT="$INPUT" python3 << 'EOF'
import json, subprocess, sys, os

input_path = os.environ["INPUT"]

with open(input_path) as f:
    data = json.load(f)

for mcp in data["mcp"]:
    name = mcp["name"]
    url = mcp.get("url", "")
    auth = mcp.get("auth", "unknown")
    
    print(f"Restaurando {name}...")
    
    if url:
        cmd = ["hermes", "mcp", "add", name, "--url", url, "--auth", auth]
        print(f"  Ejecutando: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  ✓ {name} agregado")
            if auth == "oauth":
                print(f"  → Ejecutá: hermes mcp login {name}")
        else:
            print(f"  ✗ Error: {result.stderr}")
    else:
        print(f"  → {name} requiere configuración manual (sin URL pública)")
    
    print()

print("=== Restauración completada ===")
print()
print("Para verificar:")
print("  hermes mcp list")
print("  hermes mcp test <nombre>")
EOF
