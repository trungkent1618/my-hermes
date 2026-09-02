# my-hermes Profile — Update Procedure

Profile: `my-hermes` (fork source: `github.com/trungkent1618/my-hermes`)
Installed at: `C:\Users\Admin\AppData\Local\hermes\profiles\my-hermes`

## Why a custom procedure?
`hermes profile update my-hermes` clones the fork fresh and then deletes the
old profile dir. On Windows it can hit a `PermissionError` deleting a stale
`.git/objects/pack/*.idx` left from a previous clone (file lock). When that
happens the update aborts and the live plugins are NOT updated.

## Safe update steps (when fork has new commits)
1. Make sure Hermes desktop is closed (releases file locks).
2. Remove the stale `.git` tangle dregs if present (NOT a real repo — safe):
   ```
   rm -rf "C:/Users/Admin/AppData/Local/hermes/profiles/my-hermes/.git"
   ```
3. Run the update:
   ```
   hermes profile update my-hermes -y
   ```
   If it still errors on `.git`, repeat step 2 and retry.
   Alternative that also works (overwrites distribution files, keeps `.env`):
   ```
   hermes profile install github.com/trungkent1618/my-hermes --alias --force -y
   ```

## Verify after update
- Image plugin routes via proxy: grep for `AGNES_BASE_URL` in
  `plugins/image_gen/agnes/__init__.py`
- Video plugin: no paid-model auto-upgrade — `_select_model` should return
  `self.default_model()` (agnes-video-2.5-flash); no `agnes-video-2.5"` upgrade.
- `.env` preserved: `AGNES_API_KEY=<nexus-client-key>`, `AGNES_BASE_URL=http://127.0.0.1:8080/v1`.

## Local fork workflow (authoritative copy)
- Fork repo: `C:\Users\Admin\my-hermes-fork` (origin = trungkent1618/my-hermes,
  upstream = WanderleeDev/my-hermes).
- To change plugins: edit in the fork, `git commit` + `git push origin main`,
  then run the update steps above. NEVER hand-edit live plugins and rely on
  `profile update` to keep them — live edits are overwritten on update.

## What is patched vs upstream (WanderleeDev/my-hermes)
1. Image + video plugins read `AGNES_BASE_URL` (default apihub) instead of
   hardcoding apihub — requests now route through Agnes2API-Nexus
   (`http://127.0.0.1:8080/v1`) for gateway-managed key rotation.
2. Video plugin `AGNES_VIDEO_POLL=auto`: when the gateway returns a completed
   video URL, the plugin uses it without client-side polling. Agnes2API-Nexus
   currently returns a queued task and its poll route is not implemented yet
   (`501 nexus_not_implemented`), so Nexus video completion remains blocked until
   that gateway route is implemented. No R2 fallback is allowed.
3. Video `_select_model` no longer auto-upgrades to paid `agnes-video-2.5` or to
   `agnes-video-v2.0` (different request schema, not enabled on proxy). Always
   defaults to free `agnes-video-2.5-flash` unless a model is explicitly given.

## Model constraints (IMPORTANT)
- `agnes-video-2.5-flash` ONLY accepts `size: "720P"`. The video plugin hardcodes
  `"size": "720P"` in the request payload (line ~315), so this is always sent —
  do NOT change it to other resolutions (e.g. 1080P/480P); Agnes will reject with
  a `400 size must be 720P` error. `aspect_ratio` may be 16:9 / 9:16 / 1:1 / 4:3 / 3:4.
- `duration` is sent as a string `"4"`–`"12"` seconds (default `"5"`).

## Storage: local files (R2 removed)
- Media is saved locally, NOT to Cloudflare R2 (user found R2 unnecessary).
- Root dir: `MY_HERMES_DATA_DIR` env in the profile `.env` (default
  `F:\hermes_agent_data\my-hermes`). Subdirs `images/` and `videos/` are created
  automatically. Override by setting `MY_HERMES_DATA_DIR` in `.env`.
- Image plugin: writes PNG to `<root>/images/` and returns the absolute path.
- Video plugin: downloads the Agnes CDN URL to `<root>/videos/` and returns the
  absolute path. (Agnes CDN URLs are ephemeral, so we materialise the bytes.)
- Hermes renders absolute local filesystem paths in the chat session (both image
  and video `success_response` accept a local path), so generated media shows up
  inline. If a path ever fails to render, it is a Hermes display quirk, not a
  plugin bug — the file exists on disk.

- Agnes has two real endpoints: `https://apihub.agnes-ai.com/v1` (global) and
  `https://api.agnes-ai.cn/v1` (china). The local proxy **randomizes the upstream
  region per request**, so the client must NOT hardcode a region.
- The plugin only distinguishes "via proxy" vs "direct to Agnes":
  - If `AGNES_BASE_URL` points at the local proxy (anything other than the two
    real Agnes endpoints), video runs in **proxy mode** (uses the final URL the
    proxy returns; no client-side polling — preserves proxy key rotation).
  - If `AGNES_BASE_URL` is one of the two real Agnes endpoints (direct use, no
    proxy), video falls back to **direct self-poll** mode.
- Never hardcode a region in the plugin; let the proxy decide.

## Troubleshooting video 401 `无效的令牌` (invalid token)
- Symptom: every video request via proxy returns `HTTP 401 ... 无效的令牌`
  (Chinese "invalid token") from upstream Agnes, while **image** via the same
  proxy still works.
- Cause: the **Agnes VIDEO API keys inside the proxy pool are expired/revoked**
  (not a my-hermes bug). The plugin correctly sends the proxy client key
  `123456`; the proxy accepts it but then forwards with an invalid Agnes video
  credential.
- Fix (outside this profile — do NOT edit proxy source per user rule):
  rotate/renew the Agnes video keys in the proxy config, e.g.
  `E:\hermes_agent\tools\CLIProxyAPI\.agnes-package\config.yaml` or the
  EasyCLIProxyAPI-Custom GUI. After renewing, video works again (pipeline is
  verified correct — it succeeded earlier when a valid key was rotated in).

## Gotcha: video 401 in manual Python tests (NOT a real bug)
- If you test the plugin directly with `python` (not via the Hermes app), and
  you do NOT export `AGNES_BASE_URL`/`AGNES_API_KEY` into the environment, an
  OLD plugin build sent the request to `https://apihub.agnes-ai.com/v1` with the
  proxy client key `123456` -> Agnes rejects with `401 无效的令牌`.
- Current plugin build reads BOTH `AGNES_API_KEY` and `AGNES_BASE_URL` from the
  profile `.env` file directly (via `_profile_env()`), so it routes through the
  proxy even in a bare `python` invocation. The Hermes app always worked because
  it injects the profile `.env` into the environment. If you ever see that 401 in
  a manual test, confirm the plugin is the patched build (grep `_profile_env`).
