from datetime import UTC, datetime, timedelta

from sqlalchemy import delete

from app.core.settings import get_settings
from app.db.session import SessionLocal
from app.main import app
from app.models.analytics import AccountStatSnapshot
from app.models.audit_event import AuditEvent
from app.models.tiktok_account import TikTokAccount
from app.models.tiktok_draft_job import TikTokDraftJob
from app.models.tiktok_publish_job import TikTokPublishJob
from app.models.tiktok_video import TikTokVideo
from app.services.review_package import build_review_package
from app.services.tiktok.crypto import encrypt_token


def _account(db, open_id: str, scopes: str) -> TikTokAccount:
    now = datetime.now(UTC)
    account = TikTokAccount(
        open_id=open_id,
        scopes=scopes,
        access_token_enc=encrypt_token("review-access"),
        refresh_token_enc=encrypt_token("review-refresh"),
        access_token_expires_at=now + timedelta(hours=2),
        refresh_token_expires_at=now + timedelta(days=30),
        status="CONNECTED",
        created_at=now,
        updated_at=now,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def test_review_package_maps_all_personal_scopes_to_real_routes():
    with SessionLocal() as db:
        report = build_review_package(db, get_settings(), app)

    scopes = {item["scope"] for item in report["scope_matrix"]}
    assert scopes == {
        "user.info.basic",
        "user.info.profile",
        "user.info.stats",
        "video.list",
        "video.upload",
        "video.publish",
    }
    assert all(item["code_implemented"] for item in report["scope_matrix"])
    assert len(report["demo_video_plan"]) == 5
    assert report["website_url"].startswith("https://")
    assert report["terms_url"].endswith("/terms")
    assert report["privacy_url"].endswith("/privacy")


def test_review_package_tracks_public_brand_and_portal_name_separately():
    with SessionLocal() as db:
        report = build_review_package(db, get_settings(), app)

    app_name = next(item for item in report["checks"] if item["key"] == "app_name")
    portal_name = next(item for item in report["checks"] if item["key"] == "portal_app_name")
    public_use = next(item for item in report["checks"] if item["key"] == "public_use_case")
    demo_video = next(item for item in report["checks"] if item["key"] == "demo_video")
    assert app_name["status"] == "PASS"
    assert portal_name["status"] == "MANUAL"
    assert public_use["status"] == "MANUAL"
    assert demo_video["status"] == "FAIL"
    assert report["status"] == "NOT_READY_FOR_REVIEW"


def test_all_scope_live_evidence_can_pass_with_matching_configuration():
    open_id = "review-all-scopes-open-id"
    all_scopes = (
        "user.info.basic,user.info.profile,user.info.stats,"
        "video.list,video.upload,video.publish"
    )
    settings = get_settings().model_copy(update={"tiktok_scopes": all_scopes})
    now = datetime.now(UTC)

    with SessionLocal() as db:
        db.execute(delete(TikTokAccount).where(TikTokAccount.open_id == open_id))
        db.commit()
        account = _account(db, open_id, all_scopes)
        account.profile_synced_at = now
        account.display_name = "Review User"
        account.avatar_url = "https://example.test/avatar.jpg"
        account.username = "review_user"
        account.profile_deep_link = "https://www.tiktok.com/@review_user"
        account.is_verified = False

        db.add_all(
            [
                AccountStatSnapshot(
                    account_id=account.id,
                    captured_at=now - timedelta(minutes=10),
                    follower_count=1,
                    following_count=1,
                    likes_count=0,
                    video_count=1,
                ),
                AccountStatSnapshot(
                    account_id=account.id,
                    captured_at=now,
                    follower_count=2,
                    following_count=1,
                    likes_count=1,
                    video_count=1,
                ),
            ]
        )
        db.add(
            TikTokVideo(
                account_id=account.id,
                video_id="review-video-id",
                synced_at=now,
            )
        )
        db.add(
            AuditEvent(
                event_type="VIDEOS_SYNCED",
                account_id=account.id,
                actor="test",
                status="SUCCESS",
                created_at=now,
            )
        )
        db.add(
            TikTokDraftJob(
                account_id=account.id,
                media_type="VIDEO",
                source_type="FILE_UPLOAD",
                publish_id="review-draft-publish-id",
                status="SEND_TO_USER_INBOX",
                created_at=now,
                updated_at=now,
            )
        )
        db.add(
            TikTokPublishJob(
                account_id=account.id,
                media_type="VIDEO",
                source_type="FILE_UPLOAD",
                privacy_level="SELF_ONLY",
                disable_comment=True,
                disable_duet=True,
                disable_stitch=True,
                auto_add_music=False,
                brand_content_toggle=False,
                brand_organic_toggle=False,
                is_aigc=False,
                consent_music_usage=True,
                consent_branded_policy=True,
                creator_info_json="{}",
                publish_id="review-direct-publish-id",
                status="PUBLISH_COMPLETE",
                schedule_status="COMPLETED",
                retry_count=0,
                max_retries=2,
                created_at=now,
                updated_at=now,
            )
        )
        db.commit()

        report = build_review_package(db, settings, app)
        assert all(item["status"] == "PASS" for item in report["scope_matrix"])
        assert all(item["live_evidence"] for item in report["scope_matrix"])

        db.execute(delete(AuditEvent).where(AuditEvent.account_id == account.id))
        db.execute(delete(TikTokDraftJob).where(TikTokDraftJob.account_id == account.id))
        db.execute(delete(TikTokPublishJob).where(TikTokPublishJob.account_id == account.id))
        db.execute(delete(TikTokVideo).where(TikTokVideo.account_id == account.id))
        db.execute(delete(AccountStatSnapshot).where(AccountStatSnapshot.account_id == account.id))
        db.delete(account)
        db.commit()


def test_submitted_jobs_and_single_stats_snapshot_do_not_count_as_live_pass():
    open_id = "review-incomplete-evidence-open-id"
    all_scopes = (
        "user.info.basic,user.info.profile,user.info.stats,"
        "video.list,video.upload,video.publish"
    )
    settings = get_settings().model_copy(update={"tiktok_scopes": all_scopes})
    now = datetime.now(UTC)

    with SessionLocal() as db:
        db.execute(delete(TikTokAccount).where(TikTokAccount.open_id == open_id))
        db.commit()
        account = _account(db, open_id, all_scopes)
        account.profile_synced_at = now
        account.display_name = "Incomplete Review User"
        account.username = "incomplete_review"
        db.add(
            AccountStatSnapshot(
                account_id=account.id,
                captured_at=now,
                follower_count=1,
                following_count=1,
                likes_count=0,
                video_count=0,
            )
        )
        db.add(
            TikTokDraftJob(
                account_id=account.id,
                media_type="VIDEO",
                source_type="FILE_UPLOAD",
                publish_id="incomplete-draft-publish-id",
                status="SUBMITTED",
                created_at=now,
                updated_at=now,
            )
        )
        db.add(
            TikTokPublishJob(
                account_id=account.id,
                media_type="VIDEO",
                source_type="FILE_UPLOAD",
                privacy_level="SELF_ONLY",
                disable_comment=True,
                disable_duet=True,
                disable_stitch=True,
                auto_add_music=False,
                brand_content_toggle=False,
                brand_organic_toggle=False,
                is_aigc=False,
                consent_music_usage=True,
                consent_branded_policy=True,
                creator_info_json="{}",
                publish_id="incomplete-direct-publish-id",
                status="SUBMITTED",
                schedule_status="RUNNING",
                retry_count=0,
                max_retries=2,
                created_at=now,
                updated_at=now,
            )
        )
        db.commit()

        report = build_review_package(db, settings, app)
        by_scope = {item["scope"]: item for item in report["scope_matrix"]}
        assert by_scope["user.info.stats"]["live_evidence"] is False
        assert by_scope["video.upload"]["live_evidence"] is False
        assert by_scope["video.publish"]["live_evidence"] is False

        db.execute(delete(TikTokDraftJob).where(TikTokDraftJob.account_id == account.id))
        db.execute(delete(TikTokPublishJob).where(TikTokPublishJob.account_id == account.id))
        db.execute(delete(AccountStatSnapshot).where(AccountStatSnapshot.account_id == account.id))
        db.delete(account)
        db.commit()
