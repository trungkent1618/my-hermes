from typing import Any, Dict, List, Optional

import os
import time
import json
import base64
import uuid
from pathlib import Path

import httpx
import yaml

from agent.video_gen_provider import (
    VideoGenProvider,
    error_response,
    success_response,
)

REGISTRY_PATH = Path.home() / ".hermes" / "image_registry.json"


def _profile_env() -> dict:
    """Load the profile-local .env file directly.

    Precedence for Agnes credentials: profile .env > os.environ > config.yaml.
    Reading the profile .env ourselves guarantees we always use the proxy
    client key (AGNES_API_KEY in this file), never a real Agnes key that may
    happen to live in the global environment.
    """
    env: dict = {}
    # __file__: <profile>/plugins/video_gen/agnes/__init__.py
    profile_dir = Path(__file__).resolve().parents[3]
    env_path = profile_dir / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def _local_data_dir() -> Path:
    """Local media storage root (absolute). Defaults to F:\\hermes_agent_data\\my-hermes.

    Override with MY_HERMES_DATA_DIR in the profile .env. Subdirs images/ and
    videos/ are created on demand. Hermes renders absolute local paths in chat.
    """
    penv = _profile_env()
    raw = penv.get("MY_HERMES_DATA_DIR") or os.environ.get("MY_HERMES_DATA_DIR") or r"F:\hermes_agent_data\my-hermes"
    root = Path(raw)
    (root / "images").mkdir(parents=True, exist_ok=True)
    (root / "videos").mkdir(parents=True, exist_ok=True)
    return root


def _save_video_local(video_url: str, prefix: str = "video") -> str:
    """Download a video URL and write under the local data dir; return absolute path.

    Agnes CDN URLs are ephemeral, so we materialise the bytes locally.
    """
    with httpx.Client(timeout=120) as client:
        resp = client.get(video_url, follow_redirects=True)
        resp.raise_for_status()
        data = resp.content
    ts = time.strftime("%Y%m%d_%H%M%S")
    short = uuid.uuid4().hex[:8]
    path = _local_data_dir() / "videos" / f"{prefix}_{ts}_{short}.mp4"
    path.write_bytes(data)
    return str(path)


def _load_registry() -> dict:
    if REGISTRY_PATH.exists():
        try:
            return json.loads(REGISTRY_PATH.read_text())
        except Exception:
            pass
    return {"local": {}, "imgbb": {}, "r2": {}}


def _upload_video_to_r2(video_data: bytes, key: str) -> Optional[str]:
    """Upload video to R2 and return public URL."""
    try:
        import boto3
        from botocore.config import Config
        import hashlib

        account_id = os.environ.get("R2_ACCOUNT_ID")
        access_key = os.environ.get("R2_ACCESS_KEY_ID")
        secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")
        bucket = os.environ.get("R2_VIDEO_BUCKET", "hermes-video-db")
        domain = os.environ.get("R2_VIDEO_DOMAIN", "video.wanderlee.site")

        if not all([account_id, access_key, secret_key]):
            return None

        s3 = boto3.client(
            's3',
            endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name='auto',
            config=Config(signature_version='s3v4')
        )

        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=video_data,
            ContentType='video/mp4'
        )

        # Use custom domain for public URL
        return f"https://{domain}/{key}"

    except Exception as e:
        print(f"[R2] Video upload error: {e}")
        return None


class AgnesVideoGenProvider(VideoGenProvider):
    @property
    def name(self) -> str:
        return "agnes"

    @property
    def display_name(self) -> str:
        return "Agnes AI"

    @property
    def api_key(self) -> Optional[str]:
        """Get API key from profile .env first, then env, then config.yaml.

        Reading the profile .env directly guarantees we use the proxy client key,
        never a real Agnes key that may be set in the global environment.
        """
        penv = _profile_env()
        key = penv.get("AGNES_API_KEY")
        if key:
            return key

        key = os.environ.get("AGNES_API_KEY")
        if key:
            return key

        # Fallback: read from config.yaml
        config_path = Path.home() / ".hermes" / "config.yaml"
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
            for prov in config.get("custom_providers", []):
                if prov.get("name") == "agnes":
                    return prov.get("api_key")
        return None

    def is_available(self) -> bool:
        return bool(self.api_key)

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "agnes-video-2.5-flash",
                "display": "Agnes Video 2.5 Flash",
                "speed": "~30s",
                "strengths": "Fast, free tier",
                "price": "Free",
                "modalities": ["text", "image"],
            },
            {
                "id": "agnes-video-2.5",
                "display": "Agnes Video 2.5",
                "speed": "~60s",
                "strengths": "Higher quality",
                "price": "$0.025/s",
                "modalities": ["text", "image"],
            },
            {
                "id": "agnes-video-v2.0",
                "display": "Agnes Video V2.0",
                "speed": "~60s",
                "strengths": "Legacy, free",
                "price": "Free",
                "modalities": ["text", "image"],
            },
        ]

    def default_model(self) -> Optional[str]:
        return "agnes-video-2.5-flash"

    def _select_model(self, prompt: str, requested_model: Optional[str]) -> str:
        """Return the requested model, else the safe default (free flash model).

        We deliberately do NOT auto-upgrade to paid models (agnes-video-2.5) or to
        agnes-video-v2.0 based on prompt keywords: v2.0 uses a different request
        schema (num_frames/frame_rate/width/height) and the local proxy is not
        configured for it, so an upgrade would fail. Always default to flash.
        """
        if requested_model:
            return requested_model
        return self.default_model()  # "agnes-video-2.5-flash"

    def capabilities(self) -> Dict[str, Any]:
        return {
            "modalities": ["text", "image"],
            "aspect_ratios": ["16:9", "9:16", "1:1", "4:3", "3:4"],
            "resolutions": ["720P"],
            "min_duration": 4,
            "max_duration": 12,
            "supports_audio": False,
            "supports_negative_prompt": False,
            "max_reference_images": 5,
        }

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Agnes AI",
            "badge": "free",
            "tag": "Agnes AI video generation",
            "env_vars": [
                {
                    "key": "AGNES_API_KEY",
                    "prompt": "Agnes AI API key",
                    "url": "https://apihub.agnes-ai.com",
                },
            ],
        }

    def _poll_video(self, client: httpx.Client, headers: dict, video_id: str, 
                    model: str, timeout: int = 120) -> Optional[str]:
        """Poll until video is ready or timeout (2 minutes max)."""
        start = time.time()
        poll_count = 0
        
        while time.time() - start < timeout:
            poll_count += 1
            try:
                # Derive poll host from AGNES_BASE_URL (strip /v1, add /agnesapi),
                # matching the proxy's own AgnesVideoPollBaseURL logic.
                poll_base = os.environ.get("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1").rstrip("/")
                if poll_base.endswith("/v1"):
                    poll_base = poll_base[:-3]
                r = client.get(
                    f"{poll_base}/agnesapi",
                    headers=headers,
                    params={"video_id": video_id, "model_name": model},
                    timeout=10,
                )
                r.raise_for_status()
                data = r.json()
                
                status = data.get("status", "unknown")
                
                if status == "completed":
                    return data.get("url") or data.get("metadata", {}).get("url")
                elif status == "failed":
                    error_msg = data.get("error", {}).get("message", "Unknown error")
                    return f"FAILED:{error_msg}"
                elif status in ("queued", "in_progress", "processing"):
                    # Progress update every 10 polls (~20s)
                    if poll_count % 10 == 0:
                        progress = data.get("progress", 0)
                        elapsed = int(time.time() - start)
                        print(f"  [Video] Progress: {progress}% ({elapsed}s elapsed)")
                    time.sleep(2)
                    continue
                else:
                    return None
            except httpx.TimeoutException:
                print(f"  [Video] Poll timeout (attempt {poll_count})")
                time.sleep(2)
                continue
            except Exception as e:
                print(f"  [Video] Poll error: {e}")
                time.sleep(2)
        
        return "TIMEOUT"

    def generate(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        image_url: Optional[str] = None,
        reference_image_urls: Optional[List[str]] = None,
        duration: Optional[int] = None,
        aspect_ratio: str = "16:9",
        resolution: str = "720P",
        negative_prompt: Optional[str] = None,
        audio: Optional[bool] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        prompt = (prompt or "").strip()

        if not prompt:
            return error_response(
                error="Prompt is required",
                error_type="invalid_input",
                provider=self.name,
                prompt="",
                aspect_ratio=aspect_ratio,
            )

        # Determine mode and endpoints
        if image_url or reference_image_urls:
            mode = "reference"
            modality = "image"
        else:
            mode = "text"
            modality = "text"

        model_id = self._select_model(prompt, model)
        api_key = self.api_key or ""
        # Route through AGNES_BASE_URL (proxy, e.g. http://127.0.0.1:8317/v1) so the
        # proxy handles key rotation/region. Read from profile .env first (so it
        # works without relying on Hermes injecting the var into the environment),
        # then os.environ, then fall back to apihub.
        penv = _profile_env()
        base_url = (
            penv.get("AGNES_BASE_URL")
            or os.environ.get("AGNES_BASE_URL")
            or "https://apihub.agnes-ai.com/v1"
        ).rstrip("/")
        duration_str = str(duration or 5)

        # Check if image_url is a local path and convert to imgbb/R2 URL if needed
        resolved_image_url = image_url
        if image_url and image_url.startswith("/"):
            reg = _load_registry()
            # Check imgbb first
            imgbb_entry = reg.get("imgbb", {}).get(image_url)
            if imgbb_entry and imgbb_entry.get("url"):
                resolved_image_url = imgbb_entry["url"]
            else:
                # Check R2
                for r2_key, entry in reg.get("r2", {}).items():
                    if entry.get("local_path") == image_url:
                        resolved_image_url = entry.get("url")
                        break

        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": model_id,
                "prompt": prompt,
                "seconds": duration_str,
                "mode": mode,
                "size": "720P",
                "aspect_ratio": aspect_ratio,
            }

            if mode == "reference":
                sources = []
                if resolved_image_url or image_url:
                    actual_url = resolved_image_url or image_url
                    sources.append(actual_url)
                if reference_image_urls:
                    for ref_url in reference_image_urls:
                        if ref_url.startswith("/"):
                            reg = _load_registry()
                            # Check imgbb first
                            imgbb_entry = reg.get("imgbb", {}).get(ref_url)
                            if imgbb_entry and imgbb_entry.get("url"):
                                ref_url = imgbb_entry["url"]
                            else:
                                # Check R2
                                for r2_key, entry in reg.get("r2", {}).items():
                                    if entry.get("local_path") == ref_url:
                                        ref_url = entry.get("url")
                                        break
                        sources.append(ref_url)
                payload["images"] = sources[:5]  # Max 5 for Flash

            print(f"  [Video] Creating task with model={model_id}...")

            with httpx.Client(timeout=60) as client:
                response = client.post(
                    f"{base_url}/videos",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            video_id = data.get("video_id")
            # Proxy mode: the upstream proxy already polls the async task to
            # completion and returns the final asset URL in THIS response, so we
            # must NOT self-poll (self-polling would hit apihub.agnes-ai.com
            # directly, bypassing the proxy's key rotation). Direct mode (base_url
            # is apihub) keeps the original self-poll behavior.
            poll_mode = os.environ.get("AGNES_VIDEO_POLL", "auto").lower()
            if poll_mode == "auto":
                # Proxy randomizes the upstream region (global apihub.agnes-ai.com
                # vs china api.agnes-ai.cn), so the client must NOT hardcode a
                # region. "auto" = proxy mode whenever AGNES_BASE_URL points at the
                # local proxy (anything other than the two real Agnes endpoints);
                # direct self-poll only when hitting Agnes directly.
                _real_endpoints = ("apihub.agnes-ai.com", "api.agnes-ai.cn")
                poll_mode = "proxy" if not any(e in base_url for e in _real_endpoints) else "direct"

            if poll_mode == "proxy" or not video_id:
                # Use the URL the proxy already resolved.
                data_list = data.get("data") or [{}]
                first = data_list[0] if data_list else {}
                video_url = (
                    data.get("video_url")
                    or data.get("url")
                    or first.get("url")
                    or first.get("video_url")
                )
                if not video_url:
                    return error_response(
                        error=f"No video URL in proxy response: {data}",
                        error_type="provider_error",
                        provider=self.name,
                        model=model_id,
                        prompt=prompt,
                        aspect_ratio=aspect_ratio,
                    )
                # Default: save locally so the file persists and renders in chat.
                # (R2 removed per user request — local storage only.)
                try:
                    result = _save_video_local(video_url, self.name)
                    print(f"  [Video] Saved locally: {result}")
                except Exception as e:
                    print(f"  [Video] Local save failed ({e}); returning CDN URL")
                    result = video_url
                print(f"  [Video] Proxy returned final URL")
            else:
                if not video_id:
                    return error_response(
                        error=f"No video_id in response: {data}",
                        error_type="provider_error",
                        provider=self.name,
                        model=model_id,
                        prompt=prompt,
                        aspect_ratio=aspect_ratio,
                    )
                print(f"  [Video] Task created: {video_id}")

                # Poll for completion (2 minute timeout) - create new client for polling
                with httpx.Client(timeout=60) as poll_client:
                    result = self._poll_video(poll_client, headers, video_id, model_id, timeout=120)

            if result is None:
                return error_response(
                    error="Video generation failed or timed out (2min limit). Please try again.",
                    error_type="timeout",
                    provider=self.name,
                    model=model_id,
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                )
            elif result.startswith("FAILED:"):
                error_msg = result[7:]  # Remove "FAILED:" prefix
                return error_response(
                    error=f"Video generation failed: {error_msg}",
                    error_type="provider_error",
                    provider=self.name,
                    model=model_id,
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                )
            elif result == "TIMEOUT":
                return error_response(
                    error="Video generation timed out after 2 minutes. Please try again.",
                    error_type="timeout",
                    provider=self.name,
                    model=model_id,
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                )

            # Local storage only (R2 removed per user request). `result` already
            # holds the absolute local path from the proxy/save step above.
            return success_response(
                video=result,
                model=model_id,
                prompt=prompt,
                modality=modality,
                aspect_ratio=aspect_ratio,
                duration=duration or 5,
                provider=self.name,
            )

        except httpx.TimeoutException:
            return error_response(
                error="Video task creation timed out. Please try again.",
                error_type="timeout",
                provider=self.name,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )
        except httpx.HTTPStatusError as exc:
            return error_response(
                error=f"HTTP {exc.response.status_code}: {exc.response.text}",
                error_type="provider_error",
                provider=self.name,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )
        except Exception as exc:
            return error_response(
                error=str(exc),
                error_type=type(exc).__name__,
                provider=self.name,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )


def register(ctx) -> None:
    ctx.register_video_gen_provider(AgnesVideoGenProvider())
