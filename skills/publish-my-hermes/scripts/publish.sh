#!/bin/bash
# publish.sh — Publica la distribución de my-hermes con auto-versionado
# Uso: ./scripts/publish.sh [major|minor|patch] [-y] [mensaje]
# Ejemplo: ./scripts/publish.sh patch -y "Fix en plugin de video"

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
PROFILE_DIR=""

# Search for the my-hermes repo (directory containing distribution.yaml and .git)
# First try: skill is inside a profile's skills directory
CANDIDATE="$(dirname "$(dirname "$SKILL_DIR")")"
if [ -f "$CANDIDATE/distribution.yaml" ] && [ -d "$CANDIDATE/.git" ]; then
    PROFILE_DIR="$CANDIDATE"
fi

# Second try: search upward from the skill for distribution.yaml
if [ -z "$PROFILE_DIR" ]; then
    SEARCH="$SKILL_DIR"
    while [ "$SEARCH" != "/" ]; do
        if [ -f "$SEARCH/distribution.yaml" ] && [ -d "$SEARCH/.git" ]; then
            PROFILE_DIR="$SEARCH"
            break
        fi
        SEARCH="$(dirname "$SEARCH")"
    done
fi

# Third try: common locations
if [ -z "$PROFILE_DIR" ]; then
    for PATH_CANDIDATE in "$HOME/my-hermes" "$HOME/.hermes/profiles/my-hermes" "$HOME/.hermes/my-hermes"; do
        if [ -f "$PATH_CANDIDATE/distribution.yaml" ] && [ -d "$PATH_CANDIDATE/.git" ]; then
            PROFILE_DIR="$PATH_CANDIDATE"
            break
        fi
    done
fi

if [ -z "$PROFILE_DIR" ]; then
    echo "ERROR: Could not find my-hermes repo (with distribution.yaml and .git)"
    exit 1
fi

cd "$PROFILE_DIR"

# Verificar que es un repo git
if [ ! -d .git ]; then
    echo "ERROR: No es un repo git."
    exit 1
fi

# Detectar remote y branch
REMOTE=$(git remote get-url origin 2>/dev/null || echo "sin-remote")
BRANCH=$(git branch --show-current 2>/dev/null || echo "main")

# Determinar bump type
BUMP="patch"
MSG=""
SKIP_CONFIRM=false

for arg in "$@"; do
    case "$arg" in
        major|minor|patch) BUMP="$arg" ;;
        -y|--yes) SKIP_CONFIRM=true ;;
        *) MSG="$arg" ;;
    esac
done

# Obtener versión actual
CURRENT_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
CURRENT_VERSION="${CURRENT_TAG#v}"
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

# Hacer bump
case "$BUMP" in
    major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
    minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
    patch) PATCH=$((PATCH + 1)) ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
NEW_TAG="v$NEW_VERSION"

echo "=== Publish My Hermes ==="
echo "Remote: $REMOTE"
echo "Branch: $BRANCH"
echo "Bump:   $BUMP ($CURRENT_TAG → $NEW_TAG)"
echo ""

# Verificar cambios
if git diff --quiet && git diff --staged --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
    echo "No hay cambios para publicar."
    exit 0
fi

# Mostrar cambios
echo "Cambios a publicar:"
git status --short
echo ""

# Pedir confirmación
if [ "$SKIP_CONFIRM" = false ]; then
    read -p "¿Publicar $NEW_TAG? (s/n): " CONFIRM
    if [ "$CONFIRM" != "s" ] && [ "$CONFIRM" != "S" ]; then
        echo "Cancelado."
        exit 0
    fi
fi

# Actualizar versión en distribution.yaml
sed -i "s/^version:.*/version: $NEW_VERSION/" distribution.yaml

# Commit
COMMIT_MSG="${MSG:-v$NEW_VERSION}"
git add -A
git commit -m "$COMMIT_MSG"

# Tag
git tag "$NEW_TAG"

# Push
git push origin "$BRANCH" --tags

echo ""
echo "=== Publicado $NEW_TAG ==="
echo ""
echo "Para que otros reciban los cambios:"
echo "  hermes profile update my-hermes"
