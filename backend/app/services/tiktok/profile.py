from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.tiktok_account import TikTokAccount
from app.services.tiktok.client import UserInfoResponse, get_user_info
from app.services.tiktok.crypto import decrypt_token


class TikTokProfileIdentityError(RuntimeError):
    pass


def sync_account_profile(db: Session, account: TikTokAccount) -> UserInfoResponse:
    profile = get_user_info(access_token=decrypt_token(account.access_token_enc))
    if profile.open_id != account.open_id:
        raise TikTokProfileIdentityError("TikTok profile identity mismatch")

    now = datetime.now(UTC)
    account.union_id = profile.union_id
    account.display_name = profile.display_name
    account.avatar_url = profile.avatar_url
    account.profile_synced_at = now
    account.updated_at = now
    db.commit()
    db.refresh(account)
    return profile
