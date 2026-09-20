import logging
import time

import httpx
from sqlalchemy import select

from app.core.logging import configure_logging
from app.core.settings import get_settings
from app.db.session import SessionLocal
from app.models.tiktok_account import TikTokAccount
from app.models.tiktok_video import TikTokVideo
from app.services.tiktok.client import TikTokAPIError, TikTokOAuthError
from app.services.tiktok.profile import sync_account_profile
from app.services.tiktok.scopes import STATS_SCOPE, VIDEO_LIST_SCOPE, normalize_scopes
from app.services.tiktok.videos import refresh_video_metadata, sync_video_page

configure_logging()
logger = logging.getLogger("tiktok-analytics-worker")


def _chunks(values: list[str], size: int):
    for index in range(0, len(values), size):
        yield values[index : index + size]


def run_once() -> int:
    settings = get_settings()
    processed = 0

    with SessionLocal() as db:
        accounts = db.scalars(
            select(TikTokAccount).where(TikTokAccount.status == "CONNECTED")
        ).all()

        for account in accounts:
            granted = set(normalize_scopes(account.scopes))
            did_work = False

            try:
                if STATS_SCOPE in granted:
                    sync_account_profile(db, account)
                    did_work = True

                if VIDEO_LIST_SCOPE in granted:
                    stored_ids = db.scalars(
                        select(TikTokVideo.video_id)
                        .where(TikTokVideo.account_id == account.id)
                        .order_by(TikTokVideo.create_time.desc().nullslast())
                        .limit(settings.analytics_max_videos_per_cycle)
                    ).all()

                    if not stored_ids:
                        sync_video_page(db, account, max_count=20)
                    else:
                        for batch in _chunks(list(stored_ids), 20):
                            refresh_video_metadata(db, account, video_ids=batch)
                    did_work = True

                if did_work:
                    processed += 1
            except (TikTokOAuthError, TikTokAPIError, httpx.RequestError) as exc:
                logger.warning(
                    "Analytics sync failed account_id=%s error=%s",
                    account.id,
                    type(exc).__name__,
                )
            except Exception:
                logger.exception(
                    "Unexpected analytics sync failure account_id=%s",
                    account.id,
                )

    return processed


def main() -> None:
    settings = get_settings()
    interval = max(settings.analytics_interval_seconds, 300)
    logger.info(
        "TikTok analytics worker started interval=%ss max_videos=%s",
        interval,
        settings.analytics_max_videos_per_cycle,
    )

    while True:
        started = time.monotonic()
        processed = run_once()
        logger.info("Analytics cycle complete processed_accounts=%s", processed)
        elapsed = time.monotonic() - started
        time.sleep(max(interval - elapsed, 1))


if __name__ == "__main__":
    main()
