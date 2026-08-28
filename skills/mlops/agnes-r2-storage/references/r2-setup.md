# R2 Setup Guide

## Buckets
- `hermes-image-db` → media.wanderlee.site
- `hermes-video-db` → video.wanderlee.site

## Credentials (in ~/.hermes/.env)
```
R2_ACCOUNT_ID=your_account_id_here
R2_ACCESS_KEY_ID=your_access_key_here
R2_SECRET_ACCESS_KEY=your_secret_key_here
```

## Public URL Format
```
https://media.wanderlee.site/images/<key>
https://video.wanderlee.site/videos/<key>
```

## Free Tier
- 10 GB storage/month (per account, not per bucket)
- 1M writes/month
- 10M reads/month
- Unlimited egress (FREE)

## Plugin Behavior
- Image plugin: uses Agnes CDN URL directly (~1h TTL)
- Image plugin + `storage="r2"`: downloads + uploads to R2 for permanent URL
- Video plugin: uploads to R2 on completion

## Troubleshooting
- 401: Check token scope ("Object Read & Write")
- 404: Enable public access in R2 dashboard
- 403: Check CORS or bucket permissions

## Profile Portability

### Export/Import Profile
```bash
# Create export
hermes profile export default -o agnes-setup.tar.gz

# Share and import elsewhere
scp agnes-setup.tar.gz user@remote:~/
hermes profile import ~/agnes-setup.tar.gz
```

### What's Included
- `config.yaml` with `${AGNES_API_KEY}` placeholder
- `plugins/` directory with image and video code
- `skills/mlops/` with setup documentation

### What's NOT Included
- `~/.hermes/.env` (your secrets)
- `auth.json` (OAuth tokens)
- `state.db` (conversation history)

### Post-Import Setup
1. Create `~/.hermes/.env` with your credentials
2. Copy from `.env.example` template
3. Configure R2 buckets in Cloudflare dashboard
