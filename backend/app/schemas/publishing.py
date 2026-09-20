from datetime import datetime

from pydantic import BaseModel, Field


class MediaAssetSummary(BaseModel):
    id: int
    kind: str
    original_name: str
    mime_type: str
    size_bytes: int
    sha256: str
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
