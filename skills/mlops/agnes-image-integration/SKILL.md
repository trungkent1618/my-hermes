---
name: agnes-image-integration
description: "Trigger: agnes image, image generate, agnes-image, /imagine. Use Agnes AI for image generation with model selection. Local file storage only — NO R2, NO public URLs."
license: Apache-2.0
metadata:
  author: "trungkent1618"
  version: "3.0"
---

# Agnes Image Integration

## Storage policy (MANDATORY — read first)
- **NO Cloudflare R2. NO public URLs. NO boto3. NO upload scripts.**
- All generated images are saved locally by the plugin to
  `F:\hermes_agent_data\my-hermes\images\` (or `MY_HERMES_DATA_DIR` in `.env`)
  and returned as an **absolute local path**.
- The plugin already does this. **NEVER** write your own upload code or call
  `boto3`. If an image does not render inline in chat, the file exists on disk;
  do NOT work around it by uploading to R2.

## Activation Contract
Load when: user requests image generation via Agnes AI, or when `image_generate` is called.

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
    "F:\\hermes_agent_data\\my-hermes\\images\\agnes_20260829_xxx.png": {
      "url": "https://platform-outputs...png",
      "prompt": "...",
      "created": "2026-08-29T..."
    }
  }
}
```

### Storage
- Images are saved locally to `F:\hermes_agent_data\my-hermes\images\` by the plugin.
  No R2, no cloud.

### Using registered images in video generation (reference mode)
- The video API accepts a **public Agnes CDN URL** (`https://platform-outputs.agnes-ai.space/...`)
  as `image_url` directly. Use the `url` from the image registry — do NOT re-upload to R2.
- Never upload a local image to R2 just to obtain a URL.

## Model Selection (Decision Logic for AI)
| When to Use | Model | Why |
|-------------|-------|-----|
| Quick test, draft, simple shape | `agnes-image-2.0-flash` | Faster (~5s) |
| Complex scene, detailed, cinematic | `agnes-image-2.1-flash` | Better quality |
| Default (unclear) | `agnes-image-2.1-flash` | Best quality default |

Pass the chosen model to the plugin via the `model` parameter. Do NOT hardcode in plugin.

## Timeouts
| Type | Timeout | Behavior |
|------|---------|----------|
| Image | 30s | Error + suggest retry |

## Usage Examples
### Generate image (default: saved locally)
```
/imagine a cyberpunk city
# Saved to F:\hermes_agent_data\my-hermes\images\... ; returned as absolute path
```
### Generate image with specific model
```
Generate image model=agnes-image-2.0-flash
```
### Generate image with specific ratio
```
Generate image aspect_ratio=16:9
```

## Execution Steps
1. Skill reads prompt and decides model.
2. Skill calls the `image_generate` tool (or plugin) with the model ID.
3. Plugin generates and saves locally; returns the absolute path.
4. Register in `image_registry.json` (plugin does this).
5. Return the path to the user. No uploads.

## Pitfalls
1. **No R2. Ever.** Local storage only.
2. API key is read from the profile `.env` by the plugin (proxy client key).
3. Model IDs require `-flash` suffix (`agnes-image-2.1-flash`, not `agnes-image-2.1`).
4. For video reference mode, pass the image's public Agnes CDN URL — not a local path, not an R2 URL.

## References
- Plugin: `~/.hermes/plugins/image_gen/agnes/__init__.py`
- Registry: `~/.hermes/image_registry.json`
- Local media dir: `F:\hermes_agent_data\my-hermes\` (set via `MY_HERMES_DATA_DIR` in `.env`)
