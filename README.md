# My Hermes — Media Studio

A Hermes Agent profile specialized in AI-generated media.

## What's Included

- **Agnes AI Integration**: Image generation (agnes-image-2.1-flash) and video generation (agnes-video-2.5-flash)
- **Cloudflare R2 Storage**: Permanent public URLs with custom domains
- **Custom Plugins**: `image_gen/agnes` and `video_gen/agnes` for seamless media generation
- **Skills**: Model selection, storage management, and video animation workflows

## Quick Install

```bash
hermes profile install github.com/WanderleeDev/my-hermes --alias
```

Then fill in your `.env` (see SETUP.md).

## Requirements

- Hermes Agent >= 0.12.0
- Agnes AI API key (https://agnes-ai.com)
- Cloudflare account with R2 enabled

## Author

WanderleeDev

## License

MIT
