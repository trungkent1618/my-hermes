# R2 + Custom Domain Integration

## Status (2026-08-27)

### Buckets Created
| Bucket | Purpose | Custom Domain | Status |
|--------|---------|---------------|--------|
| `hermes-image-db` | Images | `media.wanderlee.site` | ✅ Active |
| `hermes-video-db` | Videos | `video.wanderlee.site` | ✅ Active |

### DNS Records
| Subdomain | Type | Points to | Status |
|-----------|------|-----------|--------|
| `media.wanderlee.site` | CNAME | `pub-2884c63d.r2.dev` | ✅ Created |
| `video.wanderlee.site` | CNAME | `pub-2884c63d.r2.dev` | ✅ Created |

### Account
- **Account ID:** Replace with your Cloudflare account ID
- **Region:** ENAM

## Public URL Format

```
https://media.wanderlee.site/images/<key>
https://video.wanderlee.site/videos/<key>
```

## Plugin URLs

- Image plugin returns: `https://media.wanderlee.site/images/YYYYMMDD_hash.png`
- Video plugin returns: `https://video.wanderlee.site/videos/YYYYMMDD_hash.mp4`

## Troubleshooting

### 404 on custom domain
- Check R2 dashboard → bucket → Custom Domains
- Verify CNAME record exists in DNS
- Wait for propagation (usually minutes)

### 403 Forbidden
- Public access not enabled on bucket
- CORS not configured

## Related
- `agnes-image-integration` — Image generation skill
- `agnes-video-integration` — Video generation skill
