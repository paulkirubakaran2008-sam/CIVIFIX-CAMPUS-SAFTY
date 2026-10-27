"""Persistent image storage.

Render's filesystem is ephemeral -- anything written to backend/uploads/ is
gone the next time the service redeploys or restarts. Local disk storage is
fine for `uvicorn --reload` development, but production needs somewhere the
files actually survive.

When CLOUDINARY_CLOUD_NAME / CLOUDINARY_API_KEY / CLOUDINARY_API_SECRET are
set, uploaded images go to Cloudinary's free tier (generous free quota, no
credit card required) via a signed REST upload -- no extra SDK dependency,
just httpx (already a project dependency) plus hashlib from the standard
library. When they are unset, behaviour is unchanged from earlier phases:
images are written to the local uploads/ folder and served from /uploads/.
"""
import hashlib
import time

import httpx

from ..config import get_settings
from ..repository import upload_path


class ImageStorageError(Exception):
    pass


def _cloudinary_configured(settings) -> bool:
    return bool(settings.cloudinary_cloud_name and settings.cloudinary_api_key and settings.cloudinary_api_secret)


async def save_image(content: bytes, filename: str, content_type: str) -> str:
    """Persist an uploaded image and return the URL to store on the report."""
    settings = get_settings()
    if _cloudinary_configured(settings):
        return await _save_to_cloudinary(content, filename, settings)
    upload_path(filename).write_bytes(content)
    return f"/uploads/{filename}"


async def _save_to_cloudinary(content: bytes, filename: str, settings) -> str:
    timestamp = str(int(time.time()))
    # Cloudinary's signed-upload signature: sha1 of the sorted param string
    # plus the API secret. public_id and timestamp are the only signed
    # params we send.
    public_id = filename.rsplit(".", 1)[0]
    signature_base = f"public_id={public_id}&timestamp={timestamp}{settings.cloudinary_api_secret}"
    signature = hashlib.sha1(signature_base.encode("utf-8")).hexdigest()

    data = {
        "api_key": settings.cloudinary_api_key,
        "timestamp": timestamp,
        "public_id": public_id,
        "signature": signature,
    }
    files = {"file": (filename, content, "application/octet-stream")}
    url = f"https://api.cloudinary.com/v1_1/{settings.cloudinary_cloud_name}/image/upload"

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, data=data, files=files)
    except httpx.HTTPError as exc:
        raise ImageStorageError("Could not reach Cloudinary") from exc

    if response.status_code != 200:
        raise ImageStorageError(f"Cloudinary upload failed with status {response.status_code}")

    body = response.json()
    secure_url = body.get("secure_url")
    if not secure_url:
        raise ImageStorageError("Cloudinary response did not include secure_url")
    return secure_url
