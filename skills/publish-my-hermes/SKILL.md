---
name: publish-my-hermes
description: "Trigger: /publish, publicar distribución, push my-hermes."
version: 1.0.0
author: WanderleeDev
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [publish, distribution, github, my-hermes, version]
---

# Publish My Hermes

Publish the my-hermes distribution to GitHub with automatic version bumping.

## Activation Contract

Load when: user runs `/publish`, says "publicar distribución", "push my-hermes", or wants to release a new version.

## Script

The publish script lives at `scripts/publish.sh` within this skill directory.

## Versioning

The script auto-detects the current git tag and bumps it:

| Flag | Effect | Example |
|------|--------|---------|
| `major` | v1.0.0 → v2.0.0 | Breaking changes |
| `minor` | v1.0.0 → v1.1.0 | New features |
| `patch` | v1.0.0 → v1.0.1 | Bug fixes (default) |

## Usage

```bash
# Interactive (asks for confirmation)
./scripts/publish.sh patch "Fix video plugin bug"

# Non-interactive (auto-confirm)
./scripts/publish.sh minor -y "Add cloudflare skill"

# Default: patch bump with date message
./scripts/publish.sh
```

## What It Does

1. Detects current git tag (e.g., `v1.0.0`)
2. Bumps version based on flag (major/minor/patch)
3. Shows pending changes
4. Asks confirmation (unless `-y`)
5. Updates `distribution.yaml` with new version
6. Commits all changes
7. Creates git tag (e.g., `v1.0.1`)
8. Pushes to GitHub with tags

## After Publishing

Users can update with:
```bash
hermes profile update my-hermes
```

## Important

- Always run from the profile directory
- Requires git remote configured
- Requires commit access to the repo
