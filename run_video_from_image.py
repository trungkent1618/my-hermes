import os, sys, json
from pathlib import Path

profile_dir = Path(__file__).resolve().parent
env_path = profile_dir / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

plugin_file = profile_dir / "plugins" / "video_gen" / "agnes" / "__init__.py"
import importlib.util
spec = importlib.util.spec_from_file_location("agnes_video_plugin", str(plugin_file))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

provider = mod.AgnesVideoGenProvider()

# Public URL from image_registry.json for the cat image
image_url = "https://platform-outputs.agnes-ai.space/images/t2i/task_DxPNNKLGNqSUL2kkaxBPSJmFbvDkVbXt/output_6295c524b8ba414db07f1602ac4d4d2d.png"

prompt = ("A playful ginger tabby kitten pouncing on lush green grass, slowly reaching one paw up toward a delicate white and yellow butterfly fluttering just above, the butterfly gently flaps its wings and drifts, a soft breeze sways the grass, warm golden hour sunlight, subtle realistic lifelike motion, cinematic 16:9")

result = provider.generate(
    prompt=prompt,
    model="agnes-video-2.5-flash",
    image_url=image_url,
    aspect_ratio="16:9",
    duration=5,
    resolution="720P",
)
print(json.dumps(result, ensure_ascii=False, indent=2))
