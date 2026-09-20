from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tiktok_account import TikTokAccount
from app.models.tiktok_video import TikTokVideo
from app.services.analytics import capture_video_snapshots
from app.services.audit import record_audit
from app.services.tiktok.client import TikTokAPIError
from app.services.tiktok.crypto import decrypt_token
from app.services.tiktok.scopes import VIDEO_LIST_SCOPE, normalize_scopes

VIDEO_LIST_URL = "https://open.tiktokapis.com/v2/video/list/"
VIDEO_QUERY_URL = "https://open.tiktokapis.com/v2/video/query/"
VIDEO_FIELDS = (
    "id",
    "create_time",
    "cover_image_url",
    "share_url",
    "video_description",
    "duration",
    "height",
    "width",
    "title",
    "embed_link",
    "like_count",
    "comment_count",
    "share_count",
    "view_count",
    "is_aigc",
)


class TikTokVideoScopeError(RuntimeError):
    pass


@dataclass(slots=True)
class VideoItem:
    video_id: str
    create_time: datetime | None
    cover_image_url: str | None
    share_url: str | None
    video_description: str | None
    duration: int | None
    height: int | None
    width: int | None
    title: str | None
    embed_link: str | None
    like_count: int | None
    comment_count: int | None
    share_count: int | None
    view_count: int | None
    is_aigc: bool | None


@dataclass(slots=True)
class VideoPage:
    videos: list[VideoItem]
    cursor: int | None
    has_more: bool


def _require_video_scope(account: TikTokAccount) -> None:
    if VIDEO_LIST_SCOPE not in normalize_scopes(account.scopes):
        raise TikTokVideoScopeError(
            "This TikTok account has not granted the video.list scope"
        )


def _parse_error(response: httpx.Response, payload: dict) -> None:
    error = payload.get("error") or {}
    code = error.get("code")
    if response.is_error or code not in (None, 0, "ok"):
        message = error.get("message") or "TikTok video API request failed"
        raise TikTokAPIError(str(message))


def _optional_string(data: dict, name: str) -> str | None:
    value = data.get(name)
    return str(value) if value not in (None, "") else None


def _optional_int(data: dict, name: str) -> int | None:
    value = data.get(name)
    return int(value) if value is not None else None


def _video_item(data: dict) -> VideoItem:
    video_id = data.get("id")
    if not video_id:
        raise TikTokAPIError("TikTok video response is missing id")

    epoch = data.get("create_time")
    create_time = (
        datetime.fromtimestamp(int(epoch), tz=UTC)
        if epoch is not None
        else None
    )
    return VideoItem(
        video_id=str(video_id),
        create_time=create_time,
        cover_image_url=_optional_string(data, "cover_image_url"),
        share_url=_optional_string(data, "share_url"),
        video_description=_optional_string(data, "video_description"),
        duration=_optional_int(data, "duration"),
        height=_optional_int(data, "height"),
        width=_optional_int(data, "width"),
        title=_optional_string(data, "title"),
        embed_link=_optional_string(data, "embed_link"),
        like_count=_optional_int(data, "like_count"),
        comment_count=_optional_int(data, "comment_count"),
        share_count=_optional_int(data, "share_count"),
        view_count=_optional_int(data, "view_count"),
        is_aigc=(bool(data["is_aigc"]) if "is_aigc" in data else None),
    )


def fetch_video_page(
    *,
    access_token: str,
    cursor: int | None = None,
    max_count: int = 20,
) -> VideoPage:
    body: dict[str, int] = {"max_count": max(1, min(max_count, 20))}
    if cursor is not None:
        body["cursor"] = cursor

    response = httpx.post(
        VIDEO_LIST_URL,
        params={"fields": ",".join(VIDEO_FIELDS)},
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=20,
    )
    try:
        payload = response.json()
    except ValueError as exc:
        raise TikTokAPIError("TikTok returned a non-JSON video-list response") from exc

    _parse_error(response, payload)
    data = payload.get("data") or {}
    return VideoPage(
        videos=[_video_item(item) for item in (data.get("videos") or [])],
        cursor=int(data["cursor"]) if data.get("cursor") is not None else None,
        has_more=bool(data.get("has_more")),
    )


def query_video_items(*, access_token: str, video_ids: list[str]) -> list[VideoItem]:
    if not video_ids:
        return []
    if len(video_ids) > 20:
        raise ValueError("TikTok video query supports at most 20 video IDs per request")

    response = httpx.post(
        VIDEO_QUERY_URL,
        params={"fields": ",".join(VIDEO_FIELDS)},
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={"filters": {"video_ids": video_ids}},
        timeout=20,
    )
    try:
        payload = response.json()
    except ValueError as exc:
        raise TikTokAPIError("TikTok returned a non-JSON video-query response") from exc

    _parse_error(response, payload)
    data = payload.get("data") or {}
    return [_video_item(item) for item in (data.get("videos") or [])]


def _upsert_video(
    db: Session,
    *,
    account: TikTokAccount,
    item: VideoItem,
    now: datetime,
) -> TikTokVideo:
    video = db.scalar(
        select(TikTokVideo).where(
            TikTokVideo.account_id == account.id,
            TikTokVideo.video_id == item.video_id,
        )
    )
    if video is None:
        video = TikTokVideo(
            account_id=account.id,
            video_id=item.video_id,
            synced_at=now,
        )
        db.add(video)

    video.create_time = item.create_time
    video.cover_image_url = item.cover_image_url
    video.share_url = item.share_url
    video.video_description = item.video_description
    video.duration = item.duration
    video.height = item.height
    video.width = item.width
    video.title = item.title
    video.embed_link = item.embed_link
    video.like_count = item.like_count
    video.comment_count = item.comment_count
    video.share_count = item.share_count
    video.view_count = item.view_count
    video.is_aigc = item.is_aigc
    video.synced_at = now
    return video


def sync_video_page(
    db: Session,
    account: TikTokAccount,
    *,
    cursor: int | None = None,
    max_count: int = 20,
) -> VideoPage:
    _require_video_scope(account)
    page = fetch_video_page(
        access_token=decrypt_token(account.access_token_enc),
        cursor=cursor,
        max_count=max_count,
    )
    now = datetime.now(UTC)
    for item in page.videos:
        _upsert_video(db, account=account, item=item, now=now)
    db.commit()
    capture_video_snapshots(
        db,
        account_id=account.id,
        video_ids=[item.video_id for item in page.videos],
        captured_at=now,
    )
    record_audit(
        db,
        event_type="VIDEOS_SYNCED",
        account_id=account.id,
        detail=f"Synchronized {len(page.videos)} TikTok videos",
    )
    return page


def refresh_video_metadata(
    db: Session,
    account: TikTokAccount,
    *,
    video_ids: list[str],
) -> list[VideoItem]:
    _require_video_scope(account)
    items = query_video_items(
        access_token=decrypt_token(account.access_token_enc),
        video_ids=video_ids,
    )
    now = datetime.now(UTC)
    for item in items:
        _upsert_video(db, account=account, item=item, now=now)
    db.commit()
    capture_video_snapshots(
        db,
        account_id=account.id,
        video_ids=[item.video_id for item in items],
        captured_at=now,
    )
    record_audit(
        db,
        event_type="VIDEOS_REFRESHED",
        account_id=account.id,
        detail=f"Refreshed {len(items)} TikTok video records",
    )
    return items
