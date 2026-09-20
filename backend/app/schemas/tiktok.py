from datetime import datetime

from pydantic import BaseModel


class TikTokConfigStatus(BaseModel):
    configured: bool
    scopes: list[str]
    redirect_uri: str | None


class OAuthStartResponse(BaseModel):
    authorize_url: str


class TikTokAccountSummary(BaseModel):
    id: int
    open_id: str
    scopes: list[str]
    status: str
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime
    last_token_refresh_at: datetime | None
