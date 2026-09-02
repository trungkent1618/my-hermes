#!/usr/bin/env python3
"""my-hermes video health check — loop-test Agnes video via the local proxy.

Verifies the proxy key rotation + video pipeline are healthy. Reads
AGNES_API_KEY / AGNES_BASE_URL from the profile .env (same as the plugin),
so it works without Hermes injecting env vars.

Usage:
    python health_check.py [--count N] [--prompt "..."] [--no-r2]
"""
import argparse
import os
import sys
import time
from pathlib import Path

# Profile dir = <profile>/skills/my-hermes-video-health-check/health_check.py
# parents: [0]=skill dir, [1]=skills, [2]=profile
PROFILE_DIR = Path(__file__).resolve().parents[2]


def _profile_env() -> dict:
    env: dict = {}
    env_path = PROFILE_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def main() -> int:
    ap = argparse.ArgumentParser(description="my-hermes video health check")
    ap.add_argument("--count", type=int, default=5, help="number of video attempts")
    ap.add_argument("--prompt", default="health-check clip: waves rolling onto a quiet beach at dusk",
                    help="prompt to generate")
    ap.add_argument("--no-r2", action="store_true", help="use storage=local (default already local)")
    args = ap.parse_args()

    # Make the plugin importable and load it the same way the app does.
    plugin_dir = PROFILE_DIR / "plugins" / "video_gen" / "agnes"
    if not (plugin_dir / "__init__.py").exists():
        print(f"[FAIL] video plugin not found at {plugin_dir}")
        return 2
    sys.path.insert(0, str(plugin_dir))

    # Surface the profile .env so the plugin's _profile_env() picks up proxy creds.
    penv = _profile_env()
    for k in ("AGNES_API_KEY", "AGNES_BASE_URL", "AGNES_VIDEO_POLL"):
        if penv.get(k):
            os.environ.setdefault(k, penv[k])

    import importlib.util
    spec = importlib.util.spec_from_file_location("avg_health", plugin_dir / "__init__.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    prov = mod.AgnesVideoGenProvider()

    print(f"[info] api_key = {prov.api_key[:4]}*** (proxy client key)")
    print(f"[info] base_url from .env = {penv.get('AGNES_BASE_URL', '(unset)')}")
    print(f"[info] model = agnes-video-2.5-flash (free, 720P)")
    print(f"[info] attempts = {args.count}\n")

    ok = 0
    failures = {}
    for i in range(args.count):
        t0 = time.time()
        try:
            res = prov.generate(args.prompt, duration=5, aspect_ratio="16:9", storage="local")
        except Exception as e:  # noqa: BLE001 - report anything unexpected
            res = {"success": False, "error": f"exception: {e}"}
        succ = bool(res.get("success"))
        err = str(res.get("error") or "")[:60]
        dt = time.time() - t0
        if succ:
            ok += 1
            vid = (res.get("video") or "")[:80]
            print(f"  #{i + 1} SUCCESS ({dt:.1f}s) {vid}")
        else:
            key = err.split(":", 1)[0] if err else "unknown"
            failures[key] = failures.get(key, 0) + 1
            print(f"  #{i + 1} FAIL ({dt:.1f}s) {err}")
        if i < args.count - 1:
            time.sleep(3)

    print(f"\n=== {ok}/{args.count} succeeded ===")
    if failures:
        print("[failures by type]")
        for k, v in sorted(failures.items(), key=lambda x: -x[1]):
            print(f"  {v}x  {k}")

    if ok == 0:
        base_url = penv.get("AGNES_BASE_URL", "")
        if ":8080" in base_url:
            print("\n[DIAGNOSIS] Agnes2API-Nexus created tasks but video polling is not")
            print("implemented in the current gateway build (501 nexus_not_implemented).")
            print("Do not rotate keys or upload to R2; Nexus must implement GET /v1/videos/:id.")
        else:
            print("\n[DIAGNOSIS] 0 succeeded. If image via the same gateway works, the Agnes")
            print("VIDEO credentials inside the gateway pool may be expired/revoked.")
            print("This is NOT a my-hermes bug; inspect the active gateway configuration.")
        return 1
    print("\n[OK] Pipeline healthy — gateway produced video and local save succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
