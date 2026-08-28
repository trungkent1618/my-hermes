import os, sys, json
from pathlib import Path

# Load profile .env into environment (so the plugin finds AGNES_API_KEY and R2 creds)
profile_dir = Path(__file__).resolve().parent
env_path = profile_dir / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

# Import the plugin module directly from its file path
plugin_file = profile_dir / "plugins" / "video_gen" / "agnes" / "__init__.py"
import importlib.util
spec = importlib.util.spec_from_file_location("agnes_video_plugin", str(plugin_file))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

provider = mod.AgnesVideoGenProvider()
prompt = "Ancient East Asian young woman named Guangmu, peaches and cream complexion, long black hair in loose bun, wearing simple pale blue crossed-collar ancient robe, jade bracelet, gentle expression, subtle cinematic motion, soft natural light, slow graceful movement, 9:16 portrait composition"
result = provider.generate(
    prompt=prompt,
    model="agnes-video-2.5-flash",
    aspect_ratio="9:16",
    duration=5,
    resolution="720P",
)
print(json.dumps(result, ensure_ascii=False, indent=2))
