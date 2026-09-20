import json
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.models.media_asset import MediaAsset
from app.models.tiktok_account import TikTokAccount
from app.services.media_library import asset_path
from app.services.tiktok.client import TikTokAPIError
from app.services.tiktok.crypto import decrypt_token
from app.services.tiktok.scopes import VIDEO_UPLOAD_SCOPE, normalize_scopes

VIDEO_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
PHOTO_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/content/init/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"

MIN_CHUNK = 5 * 1024 * 1024
MAX_CHUNK = 64 * 1024 * 1024
MAX_FINAL_CHUNK = 128 * 1024 * 1024


class TikTokDraftScopeError(RuntimeError):
    pass


class TikTokDraftValidationError(ValueError):
    pass


@dataclass(slots=True)
class DraftInitResult:
    publish_id: str
    upload_url: str | None = None


@dataclass(slots=True)
class DraftStatusResult:
    status: str
    fail_reason: str | None
    uploaded_bytes: int | None
    downloaded_bytes: int | None
    public_post_ids: list[str]


def require_upload_scope(account: TikTokAccount) -> None:
    if VIDEO_UPLOAD_SCOPE not in normalize_scopes(account.scopes):
        raise TikTokDraftScopeError(
            "This TikTok account has not granted the video.upload scope"
        )


def video_chunk_plan(size_bytes: int) -> tuple[int, int]:
    if size_bytes <= 0:
        raise TikTokDraftValidationError("Video file is empty")
    if size_bytes <= MAX_CHUNK:
        return size_bytes, 1
    chunk_size = MAX_CHUNK
    total_chunk_count = size_bytes // chunk_size
    if total_chunk_count < 1 or total_chunk_count > 1000:
        raise TikTokDraftValidationError("Video requires an unsupported number of chunks")
    final_size = size_bytes - (total_chunk_count - 1) * chunk_size
    if final_size > MAX_FINAL_CHUNK:
        raise TikTokDraftValidationError("Final TikTok upload chunk would be too large")
    return chunk_size, total_chunk_count


def _payload(response: httpx.Response, context: str) -> dict:
    try:
        payload = response.json()
    except ValueError as exc:
        raise TikTokAPIError(f"TikTok returned a non-JSON {context} response") from exc
    error = payload.get("error") or {}
    code = error.get("code")
    if response.is_error or code not in (None, 0, "ok"):
        raise TikTokAPIError(str(error.get("message") or f"TikTok {context} failed"))
    return payload


def init_video_draft(account: TikTokAccount, asset: MediaAsset) -> DraftInitResult:
    require_upload_scope(account)
    chunk_size, total_count = video_chunk_plan(asset.size_bytes)
    response = httpx.post(
        VIDEO_INIT_URL,
        headers={
            "Authorization": f"Bearer {decrypt_token(account.access_token_enc)}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        json={
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": asset.size_bytes,
                "chunk_size": chunk_size,
                "total_chunk_count": total_count,
            }
        },
        timeout=20,
    )
    data = (_payload(response, "video draft initialization").get("data") or {})
    publish_id = data.get("publish_id")
    upload_url = data.get("upload_url")
    if not publish_id or not upload_url:
        raise TikTokAPIError("TikTok video draft response is missing publish_id or upload_url")
    parsed = urlparse(str(upload_url))
    if parsed.scheme != "https" or not (parsed.hostname or "").endswith("tiktokapis.com"):
        raise TikTokAPIError("TikTok returned an unexpected upload URL")
    return DraftInitResult(publish_id=str(publish_id), upload_url=str(upload_url))


def upload_video_file(asset: MediaAsset, upload_url: str) -> int:
    path = asset_path(asset)
    chunk_size, total_count = video_chunk_plan(asset.size_bytes)
    uploaded = 0
    with path.open("rb") as handle, httpx.Client(timeout=120) as client:
        for index in range(total_count):
            start = index * chunk_size
            if index == total_count - 1:
                size = asset.size_bytes - start
            else:
                size = chunk_size
            data = handle.read(size)
            if len(data) != size:
                raise OSError("Stored video ended before the expected byte range")
            end = start + size - 1
            response = client.put(
                upload_url,
                headers={
                    "Content-Type": asset.mime_type,
                    "Content-Length": str(size),
                    "Content-Range": f"bytes {start}-{end}/{asset.size_bytes}",
                },
                content=data,
            )
            if response.is_error:
                raise TikTokAPIError(
                    f"TikTok media transfer failed with HTTP {response.status_code}"
                )
            uploaded += size
    return uploaded


def validate_photo_request(
    *,
    photo_urls: list[str],
    cover_index: int,
    title: str | None,
    description: str | None,
) -> None:
    if not 1 <= len(photo_urls) <= 35:
        raise TikTokDraftValidationError("Photo drafts require between 1 and 35 image URLs")
    if cover_index < 0 or cover_index >= len(photo_urls):
        raise TikTokDraftValidationError("Photo cover index is outside the image list")
    if title and len(title) > 90:
        raise TikTokDraftValidationError("Photo title exceeds 90 characters")
    if description and len(description) > 4000:
        raise TikTokDraftValidationError("Photo description exceeds 4000 characters")
    for url in photo_urls:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise TikTokDraftValidationError(
                "Photo URLs must be public HTTPS URLs from a verified domain"
            )


def init_photo_draft(
    account: TikTokAccount,
    *,
    photo_urls: list[str],
    cover_index: int,
    title: str | None,
    description: str | None,
    is_aigc: bool = False,
) -> DraftInitResult:
    require_upload_scope(account)
    validate_photo_request(
        photo_urls=photo_urls,
        cover_index=cover_index,
        title=title,
        description=description,
    )
    post_info: dict[str, str] = {}
    if title:
        post_info["title"] = title
    if description:
        post_info["description"] = description

    response = httpx.post(
        PHOTO_INIT_URL,
        headers={
            "Authorization": f"Bearer {decrypt_token(account.access_token_enc)}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        json={
            "post_info": post_info,
            "source_info": {
                "source": "PULL_FROM_URL",
                "photo_cover_index": cover_index,
                "photo_images": photo_urls,
            },
            "post_mode": "MEDIA_UPLOAD",
            "media_type": "PHOTO",
            "is_aigc": is_aigc,
        },
        timeout=20,
    )
    data = (_payload(response, "photo draft initialization").get("data") or {})
    publish_id = data.get("publish_id")
    if not publish_id:
        raise TikTokAPIError("TikTok photo draft response is missing publish_id")
    return DraftInitResult(publish_id=str(publish_id))


def fetch_draft_status(account: TikTokAccount, publish_id: str) -> DraftStatusResult:
    require_upload_scope(account)
    response = httpx.post(
        STATUS_URL,
        headers={
            "Authorization": f"Bearer {decrypt_token(account.access_token_enc)}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        json={"publish_id": publish_id},
        timeout=20,
    )
    data = (_payload(response, "draft status").get("data") or {})
    raw_ids = data.get("publicaly_available_post_id") or []
    return DraftStatusResult(
        status=str(data.get("status") or "UNKNOWN"),
        fail_reason=(str(data["fail_reason"]) if data.get("fail_reason") else None),
        uploaded_bytes=(int(data["uploaded_bytes"]) if data.get("uploaded_bytes") is not None else None),
        downloaded_bytes=(int(data["downloaded_bytes"]) if data.get("downloaded_bytes") is not None else None),
        public_post_ids=[str(value) for value in raw_ids],
    )


def encode_photo_source(photo_urls: list[str], cover_index: int, is_aigc: bool) -> str:
    return json.dumps(
        {
            "photo_urls": photo_urls,
            "cover_index": cover_index,
            "is_aigc": is_aigc,
        },
        separators=(",", ":"),
    )


def decode_photo_source(raw: str | None) -> tuple[list[str], int, bool]:
    if not raw:
        raise TikTokDraftValidationError("Photo draft source is missing")
    data = json.loads(raw)
    return (
        [str(url) for url in data.get("photo_urls") or []],
        int(data.get("cover_index", 0)),
        bool(data.get("is_aigc", False)),
    )
