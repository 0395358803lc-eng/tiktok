from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.tiktok_account import TikTokAccount
from app.services.analytics import capture_account_snapshot
from app.services.audit import record_audit
from app.services.tiktok.client import UserInfoResponse, get_user_info
from app.services.tiktok.crypto import decrypt_token


class TikTokProfileIdentityError(RuntimeError):
    pass


def sync_account_profile(db: Session, account: TikTokAccount) -> UserInfoResponse:
    profile = get_user_info(
        access_token=decrypt_token(account.access_token_enc),
        scopes=account.scopes,
    )
    if profile.open_id != account.open_id:
        raise TikTokProfileIdentityError("TikTok profile identity mismatch")

    now = datetime.now(UTC)
    account.union_id = profile.union_id
    account.display_name = profile.display_name
    account.avatar_url = profile.avatar_url
    account.username = profile.username
    account.bio_description = profile.bio_description
    account.profile_deep_link = profile.profile_deep_link
    account.is_verified = profile.is_verified
    account.follower_count = profile.follower_count
    account.following_count = profile.following_count
    account.likes_count = profile.likes_count
    account.video_count = profile.video_count
    account.profile_synced_at = now
    account.updated_at = now
    db.commit()
    db.refresh(account)
    capture_account_snapshot(db, account, captured_at=now)
    record_audit(
        db,
        event_type="PROFILE_SYNCED",
        account_id=account.id,
        detail="TikTok profile metadata synchronized",
    )
    return profile
