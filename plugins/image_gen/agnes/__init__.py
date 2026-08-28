from typing import Any, Dict, List, Optional
import base64
import json
import os
import time
from pathlib import Path

import httpx
import yaml

from agent.image_gen_provider import (
    ImageGenProvider,
    error_response,
    normalize_reference_images,
    save_b64_image,
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
    # __file__: <profile>/plugins/image_gen/agnes/__init__.py
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


def _save_image_local(b64_data: str, prefix: str = "image") -> str:
    """Decode base64 and write under the local data dir; return absolute path."""
    raw = base64.b64decode(b64_data)
    ts = time.strftime("%Y%m%d_%H%M%S")
    short = __import__("uuid").uuid4().hex[:8]
    path = _local_data_dir() / "images" / f"{prefix}_{ts}_{short}.png"
    path.write_bytes(raw)
    return str(path)


def _load_registry() -> dict:
    if REGISTRY_PATH.exists():
        try:
            return json.loads(REGISTRY_PATH.read_text())
        except Exception:
            pass
    return {"local": {}, "imgbb": {}, "r2": {}}


def _save_registry(reg: dict) -> None:
    REGISTRY_PATH.write_text(json.dumps(reg, indent=2))


def _upload_to_imgbb(image_data: bytes) -> Optional[str]:
    """Upload image to imgbb and return URL."""
    try:
        b64 = base64.b64encode(image_data).decode()
        resp = httpx.post(
            "https://api.imgbb.com/1/upload",
            data={"key": "", "image": b64},
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                return data["data"]["url"]
        return None
    except Exception:
        return None


def _upload_to_r2(image_data: bytes, key: str) -> Optional[str]:
    """Upload image to R2 and return public URL."""
    try:
        import boto3
        from botocore.config import Config

        account_id = os.environ.get("R2_ACCOUNT_ID")
        access_key = os.environ.get("R2_ACCESS_KEY_ID")
        secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")
        bucket = os.environ.get("R2_IMAGE_BUCKET", "hermes-image-db")
        domain = os.environ.get("R2_IMAGE_DOMAIN", "media.wanderlee.site")

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
            Body=image_data,
            ContentType='image/png'
        )

        # Use custom domain for public URL
        return f"https://{domain}/{key}"

    except Exception as e:
        print(f"[R2] Upload error: {e}")
        return None


def _get_imgbb_url(local_path: str) -> Optional[str]:
    """Get imgbb URL for a local path from registry."""
    reg = _load_registry()
    return reg.get("imgbb", {}).get(local_path)


def _get_r2_url(local_path: str) -> Optional[str]:
    """Get R2 URL for a local path from registry."""
    reg = _load_registry()
    for r2_key, entry in reg.get("r2", {}).items():
        if entry.get("local_path") == local_path:
            return entry.get("url")
    return None


def _get_local_path(imgbb_url: str) -> Optional[str]:
    """Get local path for an imgbb URL from registry."""
    reg = _load_registry()
    for local_path, entry in reg.get("imgbb", {}).items():
        if entry.get("url") == imgbb_url:
            return local_path
    return None


class AgnesImageGenProvider(ImageGenProvider):
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

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "agnes-image-2.1-flash",
                "display": "Agnes Image 2.1 Flash",
                "speed": "~10s",
                "strengths": "High quality, complex scenes",
                "price": "Free",
            },
            {
                "id": "agnes-image-2.0-flash",
                "display": "Agnes Image 2.0 Flash",
                "speed": "~5s",
                "strengths": "Fast iteration",
                "price": "Free",
            },
        ]

    def default_model(self) -> Optional[str]:
        return "agnes-image-2.1-flash"

    def _select_model(self, prompt: str, requested_model: Optional[str]) -> str:
        """Return requested model or default. Model selection should be done by skill layer."""
        if requested_model:
            return requested_model
        # Let skill decide model based on context - plugin uses default
        return self.default_model()

    def capabilities(self) -> Dict[str, Any]:
        return {"modalities": ["text", "image"], "max_reference_images": 4}

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Agnes AI",
            "badge": "free",
            "tag": "Agnes AI image generation",
            "env_vars": [
                {
                    "key": "AGNES_API_KEY",
                    "prompt": "Agnes AI API key",
                    "url": "https://apihub.agnes-ai.com",
                },
            ],
        }

    def _aspect_ratio_to_ratio(self, aspect_ratio: str) -> str:
        mapping = {
            "landscape": "16:9",
            "portrait": "9:16",
            "square": "1:1",
            "16:9": "16:9",
            "9:16": "9:16",
            "1:1": "1:1",
            "4:3": "4:3",
            "3:4": "3:4",
        }
        return mapping.get(aspect_ratio, "1:1")

    def _save_and_register(
        self, b64_data: str, prompt: str, storage: str = "local"
    ) -> Optional[str]:
        """Save image and register in registry. Returns the URL/path."""
        try:
            path = save_b64_image(b64_data, prefix=self.name, extension="png")
            local_path = str(path)
            
            reg = _load_registry()
            now = time.strftime("%Y-%m-%dT%H:%M:%S")
            
            if storage == "imgbb":
                img_data = base64.b64decode(b64_data)
                imgbb_url = _upload_to_imgbb(img_data)
                if imgbb_url:
                    reg.setdefault("imgbb", {})[local_path] = {
                        "url": imgbb_url,
                        "prompt": prompt[:100],
                        "created": now,
                    }
                    _save_registry(reg)
                    return imgbb_url
            elif storage == "r2":
                img_data = base64.b64decode(b64_data)
                r2_key = f"images/{time.strftime('%Y%m%d_%H%M%S')}_{os.path.basename(local_path)}.png"
                r2_url = _upload_to_r2(img_data, r2_key)
                if r2_url:
                    reg.setdefault("r2", {})[r2_key] = {
                        "url": r2_url,
                        "prompt": prompt[:100],
                        "created": now,
                    }
                    _save_registry(reg)
                    return r2_url
            
            reg.setdefault("local", {})[local_path] = {
                "url": local_path,
                "prompt": prompt[:100],
                "created": now,
            }
            _save_registry(reg)
            return local_path
            
        except Exception as e:
            print(f"[ImageGen] Save/register error: {e}")
            return None

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        *,
        image_url: Optional[str] = None,
        reference_image_urls: Optional[List[str]] = None,
        storage: Optional[str] = None,  # "local" or "imgbb"
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

        sources = []
        if image_url:
            sources.append(image_url)
        sources.extend(normalize_reference_images(reference_image_urls) or [])
        modality = "image" if sources else "text"

        model_id = self._select_model(prompt, kwargs.get("model"))
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
        ratio = self._aspect_ratio_to_ratio(aspect_ratio)

        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": model_id,
                "prompt": prompt,
                "size": "1K",
                "ratio": ratio,
                "extra_body": {"response_format": "url"},
            }

            if modality == "image" and sources:
                payload["extra_body"]["image"] = sources

            with httpx.Client(timeout=30) as client:
                response = client.post(
                    f"{base_url}/images/generations",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            if "data" in data and len(data["data"]) > 0:
                item = data["data"][0]
                if item.get("b64_json"):
                    # Local storage only (R2 removed per user request)
                    image = _save_image_local(item["b64_json"], self.name)
                    reg = _load_registry()
                    now = time.strftime("%Y-%m-%dT%H:%M:%S")
                    reg.setdefault("local", {})[image] = {
                        "url": image,
                        "prompt": prompt[:100],
                        "created": now,
                    }
                    _save_registry(reg)
                    if not image:
                        return error_response(
                            error="Failed to save image",
                            error_type="provider_error",
                            provider=self.name,
                            model=model_id,
                            prompt=prompt,
                            aspect_ratio=aspect_ratio,
                        )
                elif item.get("url"):
                    # Agnes CDN URL (~1h valid). Download to local data dir so the
                    # file persists and renders in chat.
                    try:
                        with httpx.Client(timeout=30) as client:
                            img_resp = client.get(item["url"])
                            img_resp.raise_for_status()
                        local_path = _save_image_local(
                            base64.b64encode(img_resp.content).decode(), self.name
                        )
                        reg = _load_registry()
                        now = time.strftime("%Y-%m-%dT%H:%M:%S")
                        reg.setdefault("local", {})[local_path] = {
                            "url": item["url"],
                            "prompt": prompt[:100],
                            "created": now,
                        }
                        _save_registry(reg)
                        image = local_path
                        print(f"[ImageGen] Saved locally: {local_path}")
                    except Exception as e:
                        print(f"[ImageGen] Download failed: {e}, using URL directly")
                        image = item["url"]
                else:
                    return error_response(
                        error="No image URL in response",
                        error_type="provider_error",
                        provider=self.name,
                        model=model_id,
                        prompt=prompt,
                        aspect_ratio=aspect_ratio,
                    )
            else:
                return error_response(
                    error=f"Unexpected response format: {data}",
                    error_type="provider_error",
                    provider=self.name,
                    model=model_id,
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                )

            return success_response(
                image=image,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                provider=self.name,
                modality=modality,
            )

        except httpx.TimeoutException:
            return error_response(
                error="Image generation timed out (30s limit). Please try again.",
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
    ctx.register_image_gen_provider(AgnesImageGenProvider())
