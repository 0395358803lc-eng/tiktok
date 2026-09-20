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
