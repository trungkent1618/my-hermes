#!/bin/bash
# publish.sh — Publica la distribución a GitHub
# Uso: ./scripts/publish.sh [mensaje-del-commit]
# Ejemplo: ./scripts/publish.sh "Agrego skill de cloudflare"

set -e

# Detectar directorio del perfil
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

# Verificar que es un repo git
if [ ! -d .git ]; then
    echo "ERROR: No es un repo git. Ejecutá 'git init' primero."
    exit 1
fi

# Detectar remote
REMOTE=$(git remote get-url origin 2>/dev/null || echo "sin-remote")
BRANCH=$(git branch --show-current 2>/dev/null || echo "main")

echo "=== Publish My Hermmes ==="
echo "Remote: $REMOTE"
echo "Branch: $BRANCH"
echo ""

# Verificar cambios (incluyendo archivos nuevos)
if git diff --quiet && git diff --staged --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
    echo "No hay cambios para publicar."
    exit 0
fi

# Mostrar cambios
echo "Cambios a publicar:"
git status --short
echo ""

# Pedir confirmación (saltar con -y)
if [ "$1" = "-y" ] || [ "$1" = "--yes" ]; then
    echo "Confirmación automática (-y)"
else
    read -p "¿Publicar? (s/n): " CONFIRM
    if [ "$CONFIRM" != "s" ] && [ "$CONFIRM" != "S" ]; then
        echo "Cancelado."
        exit 0
    fi
fi

# Commit (tomar mensaje del arg, o usar fecha)
if [ "$1" = "-y" ] || [ "$1" = "--yes" ]; then
    COMMIT_MSG="${2:-$(date +%Y-%m-%d) update}"
else
    COMMIT_MSG="${1:-$(date +%Y-%m-%d) update}"
fi
git add -A
git commit -m "$COMMIT_MSG"

# Push
git push origin "$BRANCH"

echo ""
echo "=== Publicado: $COMMIT_MSG ==="
echo ""
echo "Para que otros reciban los cambios:"
echo "  hermes profile update my-hermes"
