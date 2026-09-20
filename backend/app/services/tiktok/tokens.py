from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.models.tiktok_account import TikTokAccount
from app.services.audit import record_audit
from app.services.tiktok.client import TokenResponse, refresh_access_token
from app.services.tiktok.crypto import decrypt_token, encrypt_token
from app.services.tiktok.oauth import oauth_configured


class TikTokConfigurationError(RuntimeError):
    pass


class TikTokIdentityError(RuntimeError):
    pass


def refresh_account_tokens(db: Session, account: TikTokAccount) -> TokenResponse:
    settings = get_settings()
    if (
        not oauth_configured(settings)
        or settings.active_tiktok_client_key is None
        or settings.active_tiktok_client_secret is None
    ):
        raise TikTokConfigurationError("TikTok OAuth is not configured")

    token = refresh_access_token(
        client_key=settings.active_tiktok_client_key,
        client_secret=settings.active_tiktok_client_secret.get_secret_value(),
        refresh_token=decrypt_token(account.refresh_token_enc),
    )
    if token.open_id != account.open_id:
        raise TikTokIdentityError("TikTok account identity mismatch")

    now = datetime.now(UTC)
    account.scopes = token.scope
    account.access_token_enc = encrypt_token(token.access_token)
    account.refresh_token_enc = encrypt_token(token.refresh_token)
    account.access_token_expires_at = now + timedelta(seconds=token.expires_in)
    account.refresh_token_expires_at = now + timedelta(seconds=token.refresh_expires_in)
    account.status = "CONNECTED"
    account.last_token_refresh_at = now
    account.updated_at = now
    db.commit()
    db.refresh(account)
    record_audit(
        db,
        event_type="TOKEN_REFRESHED",
        account_id=account.id,
        detail="TikTok access token refreshed",
    )
    return token
