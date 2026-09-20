import logging
import time
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select

from app.core.logging import configure_logging
from app.core.settings import get_settings
from app.db.session import SessionLocal
from app.models.tiktok_account import TikTokAccount
from app.services.tiktok.client import TikTokOAuthError
from app.services.tiktok.oauth import oauth_configured
from app.services.tiktok.tokens import (
    TikTokConfigurationError,
    TikTokIdentityError,
    refresh_account_tokens,
)

configure_logging()
logger = logging.getLogger("tiktok-token-worker")


def run_once() -> int:
    settings = get_settings()
    if not oauth_configured(settings):
        logger.info("TikTok OAuth not configured; token refresh cycle skipped")
        return 0

    now = datetime.now(UTC)
    cutoff = now + timedelta(seconds=settings.token_refresh_lead_seconds)

    refreshed = 0
    with SessionLocal() as db:
        accounts = db.scalars(
            select(TikTokAccount).where(
                TikTokAccount.status == "CONNECTED",
                TikTokAccount.access_token_expires_at <= cutoff,
            )
        ).all()

        for account in accounts:
            if account.refresh_token_expires_at <= now:
                account.status = "REAUTH_REQUIRED"
                account.updated_at = now
                db.commit()
                logger.warning("Refresh token expired for account_id=%s", account.id)
                continue

            try:
                refresh_account_tokens(db, account)
                refreshed += 1
                logger.info("Token refreshed account_id=%s", account.id)
            except (TikTokOAuthError, TikTokIdentityError) as exc:
                account.status = "REAUTH_REQUIRED"
                account.updated_at = datetime.now(UTC)
                db.commit()
                logger.warning(
                    "Token refresh requires reauth account_id=%s error=%s",
                    account.id,
                    type(exc).__name__,
                )

            except (httpx.RequestError, TikTokConfigurationError) as exc:
                account.status = "ERROR"
                account.updated_at = datetime.now(UTC)
                db.commit()
                logger.warning(
                    "Token refresh failed account_id=%s error=%s",
                    account.id,
                    type(exc).__name__,
                )
    return refreshed


def main() -> None:
    settings = get_settings()
    logger.info(
        "Token refresh worker started interval=%ss lead=%ss",
        settings.token_refresh_interval_seconds,
        settings.token_refresh_lead_seconds,
    )
    while True:
        try:
            run_once()
        except Exception:
            logger.exception("Unexpected token refresh worker error")
        time.sleep(settings.token_refresh_interval_seconds)


if __name__ == "__main__":
    main()
