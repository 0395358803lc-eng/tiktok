import hashlib
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.models.media_asset import MediaAsset

ALLOWED_VIDEO_MIME = {
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "video/webm": ".webm",
}


class MediaValidationError(ValueError):
    pass


def media_root() -> Path:
    settings = get_settings()
    root = Path(__file__).resolve().parents[3]
    path = Path(settings.media_root)
    if not path.is_absolute():
        path = root / path
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


async def save_video_upload(db: Session, upload: UploadFile) -> MediaAsset:
    settings = get_settings()
    mime = (upload.content_type or "").lower()
    suffix = ALLOWED_VIDEO_MIME.get(mime)
    if suffix is None:
        raise MediaValidationError("Supported video types are MP4, MOV, and WebM")

    stored_name = f"{uuid4().hex}{suffix}"
    target = media_root() / stored_name
    digest = hashlib.sha256()
    size = 0

    try:
        with target.open("wb") as handle:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > settings.media_max_video_bytes:
                    raise MediaValidationError("Video exceeds the configured maximum size")
                digest.update(chunk)
                handle.write(chunk)
        target.chmod(0o600)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()

    if size == 0:
        target.unlink(missing_ok=True)
        raise MediaValidationError("Uploaded video is empty")

    asset = MediaAsset(
        kind="VIDEO",
        original_name=(upload.filename or "video")[:255],
        stored_name=stored_name,
        mime_type=mime,
        size_bytes=size,
        sha256=digest.hexdigest(),
        created_at=datetime.now(UTC),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def asset_path(asset: MediaAsset) -> Path:
    path = media_root() / asset.stored_name
    if not path.is_file():
        raise FileNotFoundError("Stored media file is missing")
    return path
