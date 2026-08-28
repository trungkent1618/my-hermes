import os
from pathlib import Path
import boto3
from botocore.config import Config

profile_dir = Path("C:/Users/Admin/AppData/Local/hermes/profiles/my-hermes")
env_path = profile_dir / ".env"
for line in env_path.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip())

account_id = os.environ["R2_ACCOUNT_ID"]
access_key = os.environ["R2_ACCESS_KEY_ID"]
secret_key = os.environ["R2_SECRET_ACCESS_KEY"]
bucket = os.environ.get("R2_VIDEO_BUCKET", "hermes-video-db")
domain = os.environ.get("R2_VIDEO_DOMAIN", "video.yourdomain.com")

video_path = Path("F:/hermes_agent_data/my-hermes/videos/agnes_20260829_020000_25398492.mp4")
key = "videos/20260829_020000_cat_butterfly.mp4"

s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name="auto",
    config=Config(signature_version="s3v4"),
)
s3.put_object(Bucket=bucket, Key=key, Body=video_path.read_bytes(), ContentType="video/mp4")
url = f"https://{domain}/{key}"
print(url)
