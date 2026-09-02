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


## Agnes2API-Nexus gateway
- Active gateway: `http://127.0.0.1:8080/v1`.
- `AGNES_API_KEY` is the Nexus client key; the real Agnes keys stay inside Nexus.
- Nexus currently accepts `POST /v1/images/generations` and `POST /v1/videos`.
- Video caveat: the current Nexus build may return a queued task from POST and
  `501 nexus_not_implemented` for `GET /v1/videos/:id`; video completion polling
  must be implemented in Nexus before image-to-video can complete through this
  gateway. Do not bypass Nexus or upload to R2 as a workaround.


```bash
# In .env
AGNES_API_KEY=<nexus-client-key>
AGNES_BASE_URL=http://127.0.0.1:8080/v1 # Agnes2API-Nexus endpoint
AGNES_VIDEO_POLL=auto                    # gateway polls video to completion
```

With `AGNES_BASE_URL` set, image and video requests go through Agnes2API-Nexus.
Image generation is verified working. Video creation currently returns a queued task;
completion requires Nexus to implement `GET /v1/videos/:id`. The profile must not
bypass the gateway or upload to R2.

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
