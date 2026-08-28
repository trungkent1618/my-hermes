# Setup Guide

## Installation

```bash
# Install from GitHub
hermes profile install github.com/WanderleeDev/my-hermes --alias

# Or install locally during development
hermes profile install ~/.hermes/profiles/my-hermes --alias
```

## Configuration

After installation, fill in your environment variables:

```bash
# Copy the example file
cp ~/.hermes/profiles/my-hermes/.env.EXAMPLE ~/.hermes/profiles/my-hermes/.env

# Edit with your credentials
nano ~/.hermes/profiles/my-hermes/.env
```

### Required Variables

```bash
# Agnes AI API key
# Get yours at: https://agnes-ai.com
AGNES_API_KEY=your_key_here

# Local media storage root (images/videos saved here instead of R2)
MY_HERMES_DATA_DIR=F:\hermes_agent_data\my-hermes
```

## Local storage (no R2)

This profile stores all generated media as local files — no Cloudflare R2, no
public URLs. Set `MY_HERMES_DATA_DIR` in `.env` to the root folder; the plugins
create `images/` and `videos/` subdirs and return absolute paths.


## Using an Agnes Proxy (key rotation)

Instead of putting a real Agnes API key in `.env`, you can point the plugins at a
local Agnes proxy (e.g. EasyCLIProxyAPI). The proxy holds the real keys and rotates
them; this profile only authenticates to the proxy with its client key.

```bash
# In .env
AGNES_API_KEY=<proxy-client-key>        # e.g. 123456 — NOT a real Agnes key
AGNES_BASE_URL=http://127.0.0.1:8317/v1 # your proxy's /v1 endpoint
AGNES_VIDEO_POLL=auto                    # proxy already polls video to completion
```

With `AGNES_BASE_URL` set, image and video requests go through the proxy. For video,
the proxy returns the final asset URL (no client-side polling of `apihub.agnes-ai.com`),
so the proxy's key rotation is always honored. Leave `AGNES_BASE_URL` empty to call
Agnes directly (requires a real `AGNES_API_KEY`).

## Usage

```bash
# Start the agent
my-hermes chat

# Generate an image
> /imagine a cyberpunk city at sunset

# Generate a video from an image
> Animate this image for 5 seconds: https://media.yourdomain.com/images/xxx.png
```

## Updating

```bash
hermes profile update my-hermes
```

## File Structure

```
my-hermes/
├── distribution.yaml      # Profile manifest
├── .gitignore            # Excludes secrets & user data
├── SOUL.md               # Agent personality
├── config.yaml           # Hermes configuration
├── plugins/
│   ├── image_gen/agnes/   # Image generation plugin
│   └── video_gen/agnes/   # Video generation plugin
├── skills/
│   ├── mlops/agnes-image-integration/
│   ├── mlops/agnes-video-integration/
│   └── mlops/agnes-r2-storage/
├── README.md
└── SETUP.md              # This file
```

## Resources

- [Agnes AI Docs](https://wiki.agnes-ai.com)
- [Hermes Agent Docs](https://hermes-agent.nousresearch.com)
- [Profile Distributions](https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions)
