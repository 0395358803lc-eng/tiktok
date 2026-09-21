import json
from dataclasses import asdict, dataclass
from urllib.parse import urlparse

import httpx

from app.models.media_asset import MediaAsset
from app.models.tiktok_account import TikTokAccount
from app.services.tiktok.client import TikTokAPIError
from app.services.tiktok.crypto import decrypt_token
from app.services.tiktok.drafts import (
    DraftInitResult,
    DraftStatusResult,
    upload_video_file,
    validate_photo_request,
    video_chunk_plan,
)
from app.services.tiktok.scopes import VIDEO_PUBLISH_SCOPE, normalize_scopes

CREATOR_INFO_URL = "https://open.tiktokapis.com/v2/post/publish/creator_info/query/"
VIDEO_PUBLISH_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
PHOTO_PUBLISH_URL = "https://open.tiktokapis.com/v2/post/publish/content/init/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"


class TikTokPublishScopeError(RuntimeError):
    pass


class TikTokPublishValidationError(ValueError):
    pass


@dataclass(slots=True)
class CreatorInfo:
    creator_avatar_url: str | None
    creator_username: str | None
    creator_nickname: str | None
    privacy_level_options: list[str]
    comment_disabled: bool
    duet_disabled: bool
    stitch_disabled: bool
    max_video_post_duration_sec: int | None


@dataclass(slots=True)
class DirectPostOptions:
    privacy_level: str
    allow_comment: bool
    allow_duet: bool
    allow_stitch: bool
    brand_content_toggle: bool
    brand_organic_toggle: bool
    is_aigc: bool
    consent_music_usage: bool
    consent_branded_policy: bool
    title: str | None = None
    description: str | None = None
    auto_add_music: bool = False
    video_cover_timestamp_ms: int | None = None


def require_publish_scope(account: TikTokAccount) -> None:
    if VIDEO_PUBLISH_SCOPE not in normalize_scopes(account.scopes):
        raise TikTokPublishScopeError(
            "This TikTok account has not granted the video.publish scope"
        )


def _payload(response: httpx.Response, context: str) -> dict:
    try:
        payload = response.json()
    except ValueError as exc:
        raise TikTokAPIError(f"TikTok returned a non-JSON {context} response") from exc
    error = payload.get("error") or {}
    code = error.get("code")
    if response.is_error or code not in (None, 0, "ok"):
        message = error.get("message") or f"TikTok {context} failed"
        log_id = error.get("log_id")
        if code == "unaudited_client_can_only_post_to_private_accounts":
            message = (
                "TikTok chặn Direct Post: ứng dụng chưa audit chỉ được đăng ở chế độ "
                "SELF_ONLY vào tài khoản TikTok đang đặt là Riêng tư (Private). "
                "Hãy chuyển tài khoản đích sang Private rồi thử lại."
            )
        details = [str(message)]
        if code not in (None, 0, "ok"):
            details.append(f"code={code}")
        if log_id:
            details.append(f"log_id={log_id}")
        raise TikTokAPIError(" | ".join(details))
    return payload


def _utf16_units(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


def query_creator_info(account: TikTokAccount) -> CreatorInfo:
    require_publish_scope(account)
    response = httpx.post(
        CREATOR_INFO_URL,
        headers={
            "Authorization": f"Bearer {decrypt_token(account.access_token_enc)}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        timeout=20,
    )
    data = (_payload(response, "creator-info query").get("data") or {})
    options = [str(value) for value in (data.get("privacy_level_options") or [])]
    if not options:
        raise TikTokAPIError("TikTok creator-info response has no privacy options")
    max_duration = data.get("max_video_post_duration_sec")
    return CreatorInfo(
        creator_avatar_url=(
            str(data["creator_avatar_url"]) if data.get("creator_avatar_url") else None
        ),
        creator_username=(
            str(data["creator_username"]) if data.get("creator_username") else None
        ),
        creator_nickname=(
            str(data["creator_nickname"]) if data.get("creator_nickname") else None
        ),
        privacy_level_options=options,
        comment_disabled=bool(data.get("comment_disabled", False)),
        duet_disabled=bool(data.get("duet_disabled", False)),
        stitch_disabled=bool(data.get("stitch_disabled", False)),
        max_video_post_duration_sec=(
            int(max_duration) if max_duration is not None else None
        ),
    )


def creator_info_json(info: CreatorInfo) -> str:
    return json.dumps(asdict(info), separators=(",", ":"))


def validate_direct_post(
    *,
    info: CreatorInfo,
    media_type: str,
    options: DirectPostOptions,
    asset: MediaAsset | None = None,
    photo_urls: list[str] | None = None,
    cover_index: int = 0,
) -> None:
    if options.privacy_level not in info.privacy_level_options:
        raise TikTokPublishValidationError(
            "Selected privacy level is not currently available for this creator"
        )

    if not options.consent_music_usage:
        raise TikTokPublishValidationError(
            "Music Usage Confirmation consent is required before Direct Post"
        )

    if options.brand_content_toggle and not options.consent_branded_policy:
        raise TikTokPublishValidationError(
            "Branded Content Policy consent is required for branded content"
        )

    if options.brand_content_toggle and options.privacy_level == "SELF_ONLY":
        raise TikTokPublishValidationError(
            "Branded content cannot use SELF_ONLY visibility"
        )

    if info.comment_disabled and options.allow_comment:
        raise TikTokPublishValidationError(
            "Comments are disabled by the creator's current TikTok settings"
        )

    if media_type == "VIDEO":
        if info.duet_disabled and options.allow_duet:
            raise TikTokPublishValidationError(
                "Duet is disabled by the creator's current TikTok settings"
            )
        if info.stitch_disabled and options.allow_stitch:
            raise TikTokPublishValidationError(
                "Stitch is disabled by the creator's current TikTok settings"
            )
        if options.title and _utf16_units(options.title) > 2200:
            raise TikTokPublishValidationError(
                "Video caption exceeds TikTok's 2200 UTF-16-unit limit"
            )
        if asset is None:
            raise TikTokPublishValidationError("Direct video post media asset is missing")
        if asset.duration_seconds is None:
            raise TikTokPublishValidationError(
                "Video duration metadata is required before Direct Post"
            )
        if (
            info.max_video_post_duration_sec is not None
            and asset.duration_seconds > info.max_video_post_duration_sec
        ):
            raise TikTokPublishValidationError(
                "Video duration exceeds this creator's current TikTok limit"
            )
        if options.video_cover_timestamp_ms is not None:
            if options.video_cover_timestamp_ms < 0:
                raise TikTokPublishValidationError("Video cover timestamp cannot be negative")
            if options.video_cover_timestamp_ms > int(asset.duration_seconds * 1000):
                raise TikTokPublishValidationError(
                    "Video cover timestamp exceeds the video duration"
                )
    elif media_type == "PHOTO":
        validate_photo_request(
            photo_urls=photo_urls or [],
            cover_index=cover_index,
            title=options.title,
            description=options.description,
        )
    else:
        raise TikTokPublishValidationError("Unsupported Direct Post media type")


def init_video_direct_post(
    account: TikTokAccount,
    asset: MediaAsset,
    *,
    info: CreatorInfo,
    options: DirectPostOptions,
) -> DraftInitResult:
    require_publish_scope(account)
    validate_direct_post(
        info=info,
        media_type="VIDEO",
        options=options,
        asset=asset,
    )
    chunk_size, total_count = video_chunk_plan(asset.size_bytes)
    post_info = {
        "privacy_level": options.privacy_level,
        "disable_comment": not options.allow_comment,
        "disable_duet": not options.allow_duet,
        "disable_stitch": not options.allow_stitch,
        "brand_content_toggle": options.brand_content_toggle,
        "brand_organic_toggle": options.brand_organic_toggle,
        "is_aigc": options.is_aigc,
    }
    if options.title:
        post_info["title"] = options.title
    if options.video_cover_timestamp_ms is not None:
        post_info["video_cover_timestamp_ms"] = options.video_cover_timestamp_ms

    response = httpx.post(
        VIDEO_PUBLISH_URL,
        headers={
            "Authorization": f"Bearer {decrypt_token(account.access_token_enc)}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        json={
            "post_info": post_info,
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": asset.size_bytes,
                "chunk_size": chunk_size,
                "total_chunk_count": total_count,
            },
        },
        timeout=20,
    )
    data = (_payload(response, "Direct Post video initialization").get("data") or {})
    publish_id = data.get("publish_id")
    upload_url = data.get("upload_url")
    if not publish_id or not upload_url:
        raise TikTokAPIError(
            "TikTok Direct Post video response is missing publish_id or upload_url"
        )
    parsed = urlparse(str(upload_url))
    if parsed.scheme != "https" or not (parsed.hostname or "").endswith("tiktokapis.com"):
        raise TikTokAPIError("TikTok returned an unexpected upload URL")
    return DraftInitResult(publish_id=str(publish_id), upload_url=str(upload_url))


def init_photo_direct_post(
    account: TikTokAccount,
    *,
    info: CreatorInfo,
    options: DirectPostOptions,
    photo_urls: list[str],
    cover_index: int,
) -> DraftInitResult:
    require_publish_scope(account)
    validate_direct_post(
        info=info,
        media_type="PHOTO",
        options=options,
        photo_urls=photo_urls,
        cover_index=cover_index,
    )
    post_info = {
        "privacy_level": options.privacy_level,
        "disable_comment": not options.allow_comment,
        "auto_add_music": options.auto_add_music,
        "brand_content_toggle": options.brand_content_toggle,
        "brand_organic_toggle": options.brand_organic_toggle,
    }
    if options.title:
        post_info["title"] = options.title
    if options.description:
        post_info["description"] = options.description

    response = httpx.post(
        PHOTO_PUBLISH_URL,
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
            "post_mode": "DIRECT_POST",
            "media_type": "PHOTO",
            "is_aigc": options.is_aigc,
        },
        timeout=20,
    )
    data = (_payload(response, "Direct Post photo initialization").get("data") or {})
    publish_id = data.get("publish_id")
    if not publish_id:
        raise TikTokAPIError("TikTok Direct Post photo response is missing publish_id")
    return DraftInitResult(publish_id=str(publish_id))


def fetch_publish_status(
    account: TikTokAccount,
    publish_id: str,
) -> DraftStatusResult:
    require_publish_scope(account)
    response = httpx.post(
        STATUS_URL,
        headers={
            "Authorization": f"Bearer {decrypt_token(account.access_token_enc)}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        json={"publish_id": publish_id},
        timeout=20,
    )
    data = (_payload(response, "Direct Post status").get("data") or {})
    raw_ids = data.get("publicaly_available_post_id") or []
    return DraftStatusResult(
        status=str(data.get("status") or "UNKNOWN"),
        fail_reason=(str(data["fail_reason"]) if data.get("fail_reason") else None),
        uploaded_bytes=(
            int(data["uploaded_bytes"]) if data.get("uploaded_bytes") is not None else None
        ),
        downloaded_bytes=(
            int(data["downloaded_bytes"]) if data.get("downloaded_bytes") is not None else None
        ),
        public_post_ids=[str(value) for value in raw_ids],
    )


__all__ = [
    "CreatorInfo",
    "DirectPostOptions",
    "TikTokPublishScopeError",
    "TikTokPublishValidationError",
    "creator_info_json",
    "fetch_publish_status",
    "init_photo_direct_post",
    "init_video_direct_post",
    "query_creator_info",
    "require_publish_scope",
    "upload_video_file",
    "validate_direct_post",
]
