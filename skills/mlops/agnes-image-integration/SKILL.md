---
name: agnes-image-integration
description: "Trigger: agnes image, image generate, agnes-image, /imagine. Use Agnes AI for image generation with model selection and R2 storage."
license: Apache-2.0
metadata:
  author: "xam"
  version: "2.0"
---

# Agnes Image Integration

## Activation Contract

Load when: user requests image generation via Agnes AI, or when `image_generate`/`image_gen` is called.

## IMPORTANT: Get Approval First

ALWAYS ask for explicit approval ("visto bueno") BEFORE executing any action that:
- Generates images
- Runs terminal commands
- Writes files
- Modifies configuration

Read-only checks (listing files, checking config) are OK without approval.

## Image Registry

Generated images are tracked in `~/.hermes/image_registry.json`:
```json
{
  "local": {
    "/home/ubuntu/.hermes/cache/images/agnes_20260827_xxx.png": {
      "url": "https://platform-outputs...png",
      "prompt": "...",
      "created": "2026-08-27T..."
    }
  },
  "r2": {}
}
```

### Storage options for new images:
- `storage="local"`: Download from URL and save to `~/.hermes/cache/images/`
- `storage="r2"`: Upload to Cloudflare R2 and save permanent public URL

### Key implementation detail:
When image API returns a URL (not base64), plugin uses it directly by default.
Only downloads and uploads to R2 if `storage="r2"` is explicitly requested.
This avoids unnecessary bandwidth and storage usage.

### Using registered images in video generation:
- Pass local path as `image_url` → video plugin checks registry for public URL
- If no public URL found, returns error (video API requires public URLs)
- Solution: Re-generate image with `storage="r2"` or upload manually

## Model Selection (Decision Logic for AI)

The skill decides which model to use based on prompt context. The plugin receives the model ID from the skill, not vice versa.

### Image Models
| When to Use | Model | Why |
|-------------|-------|-----|
| Quick test, draft, simple shape, placeholder | `agnes-image-2.0-flash` | Faster (~5s), same quality for simple prompts |
| Complex scene, detailed description, high quality, cinematic | `agnes-image-2.1-flash` | Better quality for complex scenes |
| Default (unclear) | `agnes-image-2.1-flash` | Best quality default |

**Decision flow:**
1. Read user prompt
2. Check if they mention speed/test → use 2.0-flash
3. Otherwise → use 2.1-flash (safer default)
4. Pass chosen model to plugin via `model` parameter

### Important
- Do NOT hardcode model selection in the plugin
- The skill decides based on full context
- Plugin just executes with whatever model ID it receives

## Storage Options

### Local
Images saved to `~/.hermes/cache/images/`

### R2 (Cloudflare)
For permanent public URLs with free tier:
1. Bucket: `hermes-image-db`
2. Custom domain: `media.wanderlee.site`
3. Public URL format: `https://media.wanderlee.site/images/YYYYMMDD_hash.png`

### ImgBB (deprecated)
No longer works without API key. Use R2 instead.

## Timeouts

| Type | Timeout | Behavior |
|------|---------|----------|
| Image | 30s | Error + suggest retry |

## Usage Examples

### Generate image (default: uses Agnes URL directly)
```
/imagine a cyberpunk city
# Returns https://platform-outputs.agnes-ai.space/images/...
# URL is public for ~1 hour
```

### Generate image (upload to R2 for permanent storage)
```
Generate image storage=r2
# Downloads from Agnes, uploads to R2
# Returns https://media.wanderlee.site/images/xxx.png
```

### Generate image with specific model
```
Generate image model=agnes-image-2.0-flash
# Use faster model for quick tests
```

### Generate image with specific ratio
```
Generate image aspect_ratio=16:9
# Landscape orientation
```

## Execution Steps

### Image Generation
1. Skill reads prompt and decides model (see Model Selection above)
2. Skill calls plugin with chosen model ID
3. Plugin generates image via API
4. If API returns base64 → upload to R2 and return R2 URL
5. If API returns URL → use directly (or upload to R2 if storage=r2)
6. Register in `image_registry.json`
7. Return URL to user

### Pitfalls

1. By default, image API returns a temporary URL (~1 hour). Use `storage="r2"` for permanent storage
2. For video generation from image, ensure image has permanent URL (R2 or uploaded)
3. API key must be read from config.yaml fallback if .env is missing/truncated
4. Model IDs require `-flash` suffix (e.g., `agnes-image-2.1-flash` not `agnes-image-2.1`)
5. R2 requires CORS configuration for browser access
6. **Config uses env vars** — `config.yaml` uses `${AGNES_API_KEY}` syntax, not hardcoded keys
7. **Portable setup** — `.env.example` template exists for sharing without exposing secrets

## Global Configuration

### API Credentials
Stored in `~/.hermes/.env`:
```
AGNES_API_KEY=***
```

### R2 Credentials
Stored in `~/.hermes/.env`:
```
R2_ACCOUNT_ID=2884c63d70470fc763e5bc49f7259994
R2_ACCESS_KEY_ID=***
R2_SECRET_ACCESS_KEY=***
```

### Bucket Structure
```
hermes-image-db/     → media.wanderlee.site/
├── images/
│   └── YYYYMMDD_hash.png
```

## References

- Plugin: `~/.hermes/plugins/image_gen/agnes/__init__.py`
- Registry: `~/.hermes/image_registry.json`
- Env: `~/.hermes/.env` (AGNES_API_KEY, R2 credentials)
- `agnes-r2-storage/references/r2-custom-domain.md` — Custom domain setup
- `agnes-r2-storage/references/r2-setup.md` — Setup guide and portability info
