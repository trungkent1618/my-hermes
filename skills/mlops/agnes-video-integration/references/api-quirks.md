# Agnes API Quirks & Rate Limits

## Rate Limits

### Video Generation
- **2 requests per minute** for video creation
- **Polling endpoint** (`/agnesapi`) has separate limits
- If you get 429 on polling, wait and retry — the task may still be processing

### Image Generation
- No strict rate limit observed during testing
- 30s timeout is standard

## API Payload Requirements

### Video Endpoint (`POST /v1/videos`)
Required fields:
- `model` — must have `-flash` suffix (e.g., `agnes-video-2.5-flash`)
- `prompt` — text description
- `seconds` — string, "4" to "12"
- `size` — must be exactly `"720P"` for flash models
- `mode` — **REQUIRED**: `"reference"` for image input, `"text"` for text-only

Optional:
- `images` — array of public URLs (max 5)
- `aspect_ratio` — default 16:9

### Image Endpoint (`POST /v1/images/generations`)
Required fields:
- `model` — must have `-flash` suffix
- `prompt` — text description
- `size` — "1K" for standard
- `ratio` — "1:1", "16:9", etc.
- `extra_body.response_format` — `"url"` or `"b64_json"`

## Known Issues

### Bug: Closed HTTP Client
**Symptom:** `Client error 'Cannot send a request, as the client has been closed'`
**Cause:** Using same httpx.Client for POST and polling
**Fix:** Create separate client for polling (done in plugin v2.0+)

### Polling Timeout
The `_poll_video` method now uses a separate client to avoid this issue.

## Workarounds

If rate limited on video:
1. Wait 60 seconds for the window to reset
2. Retry the generation
3. The video task was created successfully — just need to poll again

### Rate Limit Behavior (2026-08-27)
- Video creation endpoint: 2 requests per minute
- Polling endpoint (`/agnesapi`): Also rate limited independently
- When polling returns 429, the task is still processing — don't cancel
- Wait and retry polling; the task will complete eventually

### Successful Pattern
The plugin handles this correctly by:
1. Creating the task (may get 429, but task is queued)
2. Polling with separate client (handles 429 gracefully)
3. Uploading to R2 when complete

## Testing Notes

- Custom domains (`media.wanderlee.site`, `video.wanderlee.site`) work for public access
- R2 upload is automatic when credentials are present
- Registry tracks both local paths and R2 URLs
