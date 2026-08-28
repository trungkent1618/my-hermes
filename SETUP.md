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

# Cloudflare R2 credentials
# Get yours at: https://dash.cloudflare.com → R2 → Manage R2 API Tokens
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
```

### Optional: Custom Domains

If you want permanent public URLs with your own domain:

1. Create two R2 buckets: `hermes-image-db` and `hermes-video-db`
2. Connect custom domains in Cloudflare Dashboard:
   - `media.yourdomain.com` → `hermes-image-db`
   - `video.yourdomain.com` → `hermes-video-db`
3. Update the plugin URL builders if needed

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
- [Cloudflare R2 Docs](https://developers.cloudflare.com/r2)
- [Profile Distributions](https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions)
