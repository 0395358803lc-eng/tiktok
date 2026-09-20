from datetime import datetime

from pydantic import BaseModel


class TikTokScopeCapability(BaseModel):
    scope: str
    label: str
    description: str
    configured: bool


class TikTokConfigStatus(BaseModel):
    configured: bool
    environment: str
    scopes: list[str]
    scope_capabilities: list[TikTokScopeCapability]
    redirect_uri: str | None


class OAuthStartRequest(BaseModel):
    scopes: list[str] | None = None


class OAuthStartResponse(BaseModel):
    authorize_url: str


class TikTokAccountSummary(BaseModel):
    id: int
    open_id: str
    union_id: str | None
    display_name: str | None
    avatar_url: str | None
    username: str | None
    bio_description: str | None
    profile_deep_link: str | None
    is_verified: bool | None
    follower_count: int | None
    following_count: int | None
    likes_count: int | None
    video_count: int | None
    scopes: list[str]
    status: str
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime
    last_token_refresh_at: datetime | None
    profile_synced_at: datetime | None


class TikTokVideoSummary(BaseModel):
    id: int
    account_id: int
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
    synced_at: datetime


class TikTokVideoSyncRequest(BaseModel):
    cursor: int | None = None
    max_count: int = 20


class TikTokVideoSyncResponse(BaseModel):
    synced_count: int
    cursor: int | None
    has_more: bool


class TikTokVideoRefreshRequest(BaseModel):
    video_ids: list[str]
