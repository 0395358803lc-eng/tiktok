from datetime import datetime

from pydantic import BaseModel


class TikTokConfigStatus(BaseModel):
    configured: bool
    environment: str
    scopes: list[str]
    redirect_uri: str | None


class OAuthStartResponse(BaseModel):
    authorize_url: str


class TikTokAccountSummary(BaseModel):
    id: int
    open_id: str
    union_id: str | None
    display_name: str | None
    avatar_url: str | None
    scopes: list[str]
    status: str
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime
    last_token_refresh_at: datetime | None
    profile_synced_at: datetime | None
