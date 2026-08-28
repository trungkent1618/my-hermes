---
name: my-hermes-video-health-check
description: "Trigger: my-hermes video health, video rotate test, proxy video check. Loop-test Agnes video generation through the local proxy to confirm the proxy key rotation works and the pipeline is healthy."
license: MIT
metadata:
  author: "trungkent1618"
  version: "1.0"
---

# my-hermes Video Health Check

## What it does
Runs a loop of Agnes video generations through the local proxy (`AGNES_BASE_URL`)
to verify the full pipeline is healthy:
- Plugin routes through the proxy (reads `AGNES_BASE_URL` + `AGNES_API_KEY` from
  the profile `.env`, NOT from the environment).
- Proxy key rotation works (each job picks a different upstream Agnes key).
- `agnes-video-2.5-flash` (free, 720P) actually produces a video.

## When to use
- After editing the video plugin or `.env`.
- When video seems to fail — to tell "proxy key pool exhausted" from "real bug".
- Periodic smoke test of the my-hermes video pipeline.

## How to run
From the profile directory, with the Hermes venv python:

```bat
C:\Users\Admin\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe skills\my-hermes-video-health-check\health_check.py --count 5
```

Or via bash:
```bash
PY="C:/Users/Admin/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe"
PROFILE="C:/Users/Admin/AppData/Local/hermes/profiles/my-hermes"
"$PY" "$PROFILE/skills/my-hermes-video-health-check/health_check.py" --count 5
```

## Reading the result
- `N/M succeeded` — if >0, the pipeline works; failures are proxy-rotation hitting
  an expired/revoked Agnes video key (expected transient behavior, NOT a my-hermes bug).
- If 0/M and image via the same proxy still works: the Agnes **video** keys inside
  the proxy pool are all expired/revoked. Fix in the proxy config (outside this
  profile — do NOT edit proxy source): renew Agnes video keys in
  `E:\hermes_agent\tools\CLIProxyAPI\.agnes-package\config.yaml` or the
  EasyCLIProxyAPI-Custom GUI.
- If every attempt returns `401 无效的令牌` immediately (0.2s): this is the expired-key
  case above, OR (legacy) the plugin was sending to apihub with the proxy key. The
  current plugin reads `AGNES_BASE_URL` from `.env` so it always hits the proxy; if
  you still see that, confirm the patched build (grep `_profile_env` in the plugin).

## Notes
- Video model is forced to `agnes-video-2.5-flash` (free, 720P only).
- The proxy randomizes the upstream region (global/china) — the client does not care.
- Each attempt waits a few seconds between calls to avoid hammering the proxy.
