# Agnes AI Integration Notes
## Session-specific details from integration work

### R2 Storage Configuration

#### Buckets
- `hermes-image-db` → Images (media.wanderlee.site)
- `hermes-video-db` → Videos (video.wanderlee.site)

#### Custom Domains
- `media.wanderlee.site` → CNAME to `pub-2884c63d.r2.dev`
- `video.wanderlee.site` → CNAME to `pub-2884c63d.r2.dev`

#### DNS Setup
CNAME records created via Cloudflare dashboard:
```
media.wanderlee.site  →  pub-2884c63d.r2.dev
video.wanderlee.site  →  pub-2884c63d.r2.dev
```

#### S3 Endpoint
```
https://{account_id}.r2.cloudflarestorage.com
```

#### Credentials Location
Stored in `~/.hermes/.env`:
```
R2_ACCOUNT_ID=***
R2_ACCESS_KEY_ID=***
R2_SECRET_ACCESS_KEY=***
```

### Plugin Architecture

#### Image Plugin
- Path: `~/.hermes/plugins/image_gen/agnes/__init__.py`
- Default model: `agnes-image-2.1-flash`
- Timeout: 30s
- Storage: R2 (uploads when `storage="r2"` explicitly requested)
- Env vars read: `R2_IMAGE_BUCKET`, `R2_IMAGE_DOMAIN`, `R2_ACCOUNT_ID`, etc.

#### Video Plugin
- Path: `~/.hermes/plugins/video_gen/agnes/__init__.py`
- Default model: `agnes-video-2.5-flash`
- Timeout: 120s
- Polling: GET `/agnesapi?video_id=X&model_name=agnes-video-2.5-flash`
- Env vars read: `R2_VIDEO_BUCKET`, `R2_VIDEO_DOMAIN`, etc.

### Bug Fixes Applied

1. **Video URL extraction**: API returns `data["url"]` not `data["metadata"]["url"]`
2. **Closed client bug**: Separate httpx.Client needed for polling (original client closes after POST)
3. **Mode parameter**: Video API requires `mode` param (`"reference"` or `"text"`)
4. **API key truncation**: Original key was truncated in .env; full 51-char key required

### Model Selection Logic

Models are selected by the SKILL layer, not hardcoded in plugins:

| When to Use | Image Model | Video Model |
|-------------|-------------|-------------|
| Quick test | agnes-image-2.0-flash | agnes-video-2.5-flash |
| High quality | agnes-image-2.1-flash | agnes-video-2.5 |
| Default | agnes-image-2.1-flash | agnes-video-2.5-flash |

### Generated Content Registry

Images tracked in `~/.hermes/image_registry.json`:
```json
{
  "local": { ... },
  "r2": {
    "images/YYYYMMDD_xxx.png": {
      "url": "https://media.wanderlee.site/images/...",
      "prompt": "...",
      "created": "..."
    }
  }
}
```

### API Endpoints

- Base URL: `https://apihub.agnes-ai.com/v1`
- Image: `POST /v1/images/generations`
- Video: `POST /v1/videos` (async)
- Video poll: `GET /agnesapi?video_id=X&model_name=...`

### Rate Limits
- 2 video requests per minute (Agnes AI)

### Portability Pattern

The integration follows the portable config pattern:
1. Secrets in `~/.hermes/.env`
2. Config in `~/.hermes/config.yaml` with `${VAR}` syntax
3. Templates in `~/.hermes/.env.example`
4. Plugin code reads from env vars with defaults
