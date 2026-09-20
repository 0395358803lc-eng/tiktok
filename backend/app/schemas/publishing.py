from datetime import datetime

from pydantic import BaseModel, Field


class MediaAssetSummary(BaseModel):
    id: int
    kind: str
    original_name: str
    mime_type: str
    size_bytes: int
    sha256: str
    duration_seconds: float | None
    created_at: datetime


class VideoDraftCreateRequest(BaseModel):
    media_asset_id: int


class PhotoDraftCreateRequest(BaseModel):
    photo_urls: list[str] = Field(min_length=1, max_length=35)
    cover_index: int = 0
    title: str | None = None
    description: str | None = None
    is_aigc: bool = False


class DraftJobSummary(BaseModel):
    id: int
    account_id: int
    media_asset_id: int | None
    media_type: str
    source_type: str
    title: str | None
    description: str | None
    publish_id: str | None
    status: str
    fail_reason: str | None
    uploaded_bytes: int | None
    downloaded_bytes: int | None
    public_post_ids: list[str]
    created_at: datetime
    updated_at: datetime


class CreatorInfoSummary(BaseModel):
    creator_avatar_url: str | None
    creator_username: str | None
    creator_nickname: str | None
    privacy_level_options: list[str]
    comment_disabled: bool
    duet_disabled: bool
    stitch_disabled: bool
    max_video_post_duration_sec: int | None


class DirectVideoPostRequest(BaseModel):
    media_asset_id: int
    privacy_level: str
    title: str | None = None
    allow_comment: bool = False
    allow_duet: bool = False
    allow_stitch: bool = False
    brand_content_toggle: bool = False
    brand_organic_toggle: bool = False
    is_aigc: bool = False
    video_cover_timestamp_ms: int | None = None
    consent_music_usage: bool = False
    consent_branded_policy: bool = False


class DirectPhotoPostRequest(BaseModel):
    photo_urls: list[str] = Field(min_length=1, max_length=35)
    cover_index: int = 0
    title: str | None = None
    description: str | None = None
    privacy_level: str
    allow_comment: bool = False
    auto_add_music: bool = False
    brand_content_toggle: bool = False
    brand_organic_toggle: bool = False
    is_aigc: bool = False
    consent_music_usage: bool = False
    consent_branded_policy: bool = False


class PublishJobSummary(BaseModel):
    id: int
    account_id: int
    media_asset_id: int | None
    media_type: str
    source_type: str
    title: str | None
    description: str | None
    privacy_level: str
    disable_comment: bool
    disable_duet: bool
    disable_stitch: bool
    auto_add_music: bool
    brand_content_toggle: bool
    brand_organic_toggle: bool
    is_aigc: bool
    video_cover_timestamp_ms: int | None
    publish_id: str | None
    status: str
    fail_reason: str | None
    uploaded_bytes: int | None
    downloaded_bytes: int | None
    public_post_ids: list[str]
    created_at: datetime
    updated_at: datetime
