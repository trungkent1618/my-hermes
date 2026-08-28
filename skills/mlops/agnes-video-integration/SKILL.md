---
name: agnes-video-integration
description: "Trigger: agnes video, video generate, agnes-video, animate image. Use Agnes AI for video generation from images with R2 storage."
license: Apache-2.0
metadata:
  author: "xam"
  version: "2.0"
---

# Agnes Video Integration

## Activation Contract

Load when: user requests video generation via Agnes AI, or when `video_generate`/`video_gen` is called.

## IMPORTANT: Use Plugin Only

**CRITICAL:** The skill must NEVER call the Agnes API directly.

All video generation must go through the plugin at `~/.hermes/plugins/video_gen/agnes/__init__.py`.

The plugin handles:
- Constructing the correct API payload (including `mode` parameter)
- Auto-detecting mode based on input (`"reference"` when images provided, `"text"` otherwise)
- Polling for completion
- Uploading to R2

### Why use the plugin?
1. The plugin knows the correct API schema (e.g., `mode` parameter is required)
2. The plugin handles errors and rate limits
3. The plugin manages R2 uploads automatically
4. The plugin resolves local paths to public URLs via registry

**Never** construct API requests manually — always call the plugin.

ALWAYS ask for explicit approval ("visto bueno") BEFORE executing any action that:
- Generates videos
- Runs terminal commands
- Writes files
- Modifies configuration

Read-only checks (listing files, checking config) are OK without approval.

## Image Registry (for video input)

Videos are generated from images. The image must have a public URL.
Check `~/.hermes/image_registry.json` for registered images:
```json
{
  "local": { ... },
  "r2": {
    "images/20260827_xxx.png": {
      "url": "https://media.wanderlee.site/images/xxx.png",
      "local_path": "/home/ubuntu/.hermes/cache/images/...",
      "prompt": "...",
      "created": "..."
    }
  }
}
```

### Using registered images in video generation:
- Pass local path as `image_url` → plugin checks registry for public URL
- If no public URL found, returns error (video API requires public URLs)
- Solution: Re-generate image with `storage="r2"` first

## Model Selection (Decision Logic for AI)

The skill decides which model to use based on prompt context. The plugin receives the model ID from the skill, not vice versa.

### Video Models
| When to Use | Model | Why |
|-------------|-------|-----|
| Legacy API, v2 reference | `agnes-video-v2.0` | Older but stable |
| Professional quality, cinematic, paid | `agnes-video-2.5` | Best quality |
| Default (free, fast) | `agnes-video-2.5-flash` | Good enough for most cases |

**Decision flow:**
1. Read user prompt
2. Check for quality keywords (cinematic, professional) → use 2.5 if available
3. Otherwise → use 2.5-flash (free default)
4. Pass chosen model to plugin via `model` parameter

### Important
- Do NOT hardcode model selection in the plugin
- The skill decides based on full context
- Plugin just executes with whatever model ID it receives

## Timeouts

| Type | Timeout | Behavior |
|------|---------|----------|
| Video | 120s | Poll every 2s, show progress every ~20s |

## Usage Examples

### Generate video from image
```
Animate image https://media.wanderlee.site/images/xxx.png for 4 seconds
# Returns video URL
```

### Generate video with specific duration
```
Generate video from https://media.wanderlee.site/images/xxx.png seconds=8
# 8 second video
```

### Generate video with specific model
```
Generate video model=agnes-video-2.5 prompt="cinematic drone shot"
# Use higher quality model
```

### Generate video from local image path
```
Generate video from /home/ubuntu/.hermes/images/photo.png
# Plugin looks up registry for public URL
# If not found, suggests uploading to R2 first
```

## Execution Steps

### Video Generation
1. Skill reads prompt and decides model (see Model Selection above)
2. Skill validates input image has public URL
3. If input is local path → check registry for public URL
4. If no public URL → error, suggest re-generating image with storage=r2
5. **Call the plugin** — do NOT construct API requests manually
6. Plugin handles: mode detection, API call, polling, R2 upload
7. Plugin returns video URL (R2 or Agnes CDN)
8. Register in `~/.hermes/image_registry.json`
9. Return video URL to user

### Pitfalls

1. **Always use the plugin** — never call the API directly
2. Video API only accepts PUBLIC URLs, not local paths or base64
3. Ensure input image has permanent URL (R2 preferred over temporary Agnes URL)
4. Video duration limited to 4-12 seconds
5. Max 5 reference images per video
6. Size must be exactly "720P" for flash models
7. **Mode parameter is required** — plugin sets it automatically:
   - `"reference"` when providing an image URL
   - `"text"` for text-only generation
8. API key must be read from config.yaml fallback if .env is missing/truncated
9. Model IDs require `-flash` suffix (e.g., `agnes-video-2.5-flash` not `agnes-video-2.5`)
10. **Rate limit: 2 video requests per minute** — plugin handles retries automatically
11. **Polling 429 is normal** — if you get 429 during polling, the task is still processing; wait and retry
12. **Config uses env vars** — `config.yaml` uses `${AGNES_API_KEY}` syntax, not hardcoded keys

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
hermes-video-db/     → video.wanderlee.site/
└── videos/
    └── YYYYMMDD_hash.mp4
```

## References

- Plugin: `~/.hermes/plugins/video_gen/agnes/__init__.py`
- Registry: `~/.hermes/image_registry.json`
- Env: `~/.hermes/.env` (AGNES_API_KEY, R2 credentials)
- `agnes-r2-storage/references/r2-custom-domain.md` — Custom domain setup
- `agnes-r2-storage/references/r2-setup.md` — Setup guide and portability info
