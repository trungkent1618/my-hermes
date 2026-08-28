---
name: agnes-video-integration
description: "Trigger: agnes video, video generate, agnes-video, animate image. Use Agnes AI for video generation (text-to-video or image-to-video). Local file storage only — NO R2, NO public URLs."
license: Apache-2.0
metadata:
  author: "trungkent1618"
  version: "3.0"
---

# Agnes Video Integration

## Storage policy (MANDATORY — read first)
- **NO Cloudflare R2. NO public URLs. NO boto3. NO upload scripts.**
- All generated videos are saved locally by the plugin to
  `F:\hermes_agent_data\my-hermes\videos\` (or `MY_HERMES_DATA_DIR` in `.env`)
  and returned as an **absolute local path**.
- The plugin already does this. **NEVER** write your own upload code, never call
  `boto3`, never construct an R2 URL. If a video does not render inline in chat,
  that is a Hermes display limitation — the file exists on disk; do NOT work around
  it by uploading to R2.

## Activation Contract
Load when: user requests video generation via Agnes AI, or when `video_generate` is called.

## IMPORTANT: Use Plugin / Tool Only
**CRITICAL:** Never call the Agnes API directly. Never write a standalone Python
script that imports the plugin and `print(json.dumps(result))` — that bypasses the
chat media renderer and the video will not show inline.

Preferred path (renders inline in chat):
- Call the native `video_generate` tool with the user's prompt / source image.
  Hermes routes it to the `agnes` video plugin and embeds the result.

If you must call the plugin directly (e.g. reference mode from a specific URL),
return the plugin's `success_response` dict through the normal tool flow — do NOT
`print()` it as text.

The plugin handles:
- Building the correct payload (`mode`, `size: "720P"`, `seconds`, `aspect_ratio`)
- Routing through the local proxy (`AGNES_BASE_URL`) for key rotation
- Saving the result locally and returning the absolute path

### Why use the plugin/tool?
1. Correct API schema (`mode` is required; flash only accepts `720P`).
2. Proxy key rotation is preserved (no client-side polling of apihub).
3. Local storage is handled — no R2, no secrets, no public-URL dance.

**Never** construct API requests manually. **Never** upload to R2.

ALWAYS ask for explicit approval ("visto bueno") BEFORE generating a video or
running terminal commands / writing files.

Read-only checks (listing files, checking config) are OK without approval.

## Image input for image-to-video (reference mode)
- The plugin accepts a **public Agnes CDN URL** (`https://platform-outputs.agnes-ai.space/...`)
  as `image_url` directly — no local-to-public conversion needed, no R2.
- If the user gives a local image path, resolve it via the image registry
  (`~/.hermes/image_registry.json`) to its public URL, or just re-generate the
  image and use the returned URL. Do NOT upload the image to R2 to get a URL.

## Model Selection
| When to Use | Model | Why |
|-------------|-------|-----|
| Default (free, fast) | `agnes-video-2.5-flash` | Good enough, 720P only |
| Reference / animate image | `agnes-video-2.5-flash` | Same model, `mode=reference` |

Do NOT upgrade to paid `agnes-video-2.5` or legacy `agnes-video-v2.0`.

## Constraints
- `agnes-video-2.5-flash` ONLY accepts `size: "720P"`.
- `duration` 4–12 seconds (string).
- `aspect_ratio`: 16:9 / 9:16 / 1:1 / 4:3 / 3:4.

## Execution Steps (video from image)
1. Get the source image's public URL (Agnes CDN URL from the image result, or registry).
2. Call `video_generate` (or the plugin) with `image_url=...`, `model=agnes-video-2.5-flash`,
   `duration=5`, `aspect_ratio=...`, `resolution=720P`.
3. The plugin saves locally and returns the absolute path. Present that path to the user.
   Do NOT re-upload anything.

## Pitfalls
1. **No R2. Ever.** Local storage only.
2. Video API needs a PUBLIC image URL for reference mode — use the Agnes CDN URL,
   not a local path and not an R2 URL.
3. Flash model = 720P only.
4. Let the plugin/tool handle everything; do not script it yourself.
