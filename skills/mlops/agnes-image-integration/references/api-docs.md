# Agnes AI Image Generation API

## Endpoints

### Generate Image
```
POST https://apihub.agnes-ai.com/v1/images/generations
```

### Authentication
```
Authorization: Bearer {AGNES_API_KEY}
Content-Type: application/json
```

## Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | Yes | Model ID (must have `-flash` suffix) |
| `prompt` | string | Yes | Text description |
| `size` | string | Yes | Image size: `"1K"` (standard) |
| `ratio` | string | Yes | Aspect ratio: `"1:1"`, `"16:9"`, `"9:16"`, etc. |
| `extra_body` | object | Yes | Contains `response_format` |
| `extra_body.response_format` | string | Yes | `"url"` or `"b64_json"` |
| `extra_body.image` | array | Optional | For image-to-image: array of public URLs |

## Response

```json
{
  "data": [
    {
      "url": "https://platform-outputs.agnes-ai.space/images/...",
      "b64_json": "",
      "revised_prompt": ""
    }
  ],
  "created": 1787869562,
  "task_id": "task_xxx"
}
```

## Model IDs

### Image Models
| ID | Speed | Use Case |
|----|-------|----------|
| `agnes-image-2.0-flash` | ~5s | Fast tests, simple prompts |
| `agnes-image-2.1-flash` | ~10-20s | Complex scenes, high quality |

## Timeouts
- Standard timeout: 30 seconds
- If response takes longer, expect timeout error

## Storage Options
- **URL only**: Use Agnes CDN URL directly (expires ~1 hour)
- **R2 upload**: Download and upload to Cloudflare R2 for permanent storage

## Examples

### Basic image generation
```python
payload = {
    "model": "agnes-image-2.1-flash",
    "prompt": "A cyberpunk city at night",
    "size": "1K",
    "ratio": "16:9",
    "extra_body": {"response_format": "url"}
}
```

### Image-to-image (using reference)
```python
payload = {
    "model": "agnes-image-2.1-flash",
    "prompt": "Convert to watercolor style",
    "size": "1K",
    "ratio": "1:1",
    "extra_body": {
        "response_format": "url",
        "image": ["https://example.com/reference.png"]
    }
}
```

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `model_not_found` | Wrong model ID | Use `-flash` suffix |
| `invalid_request` | Missing required field | Check payload structure |
| `timeout` | Generation took >30s | Increase timeout or simplify prompt |
