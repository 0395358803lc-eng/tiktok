from datetime import UTC, datetime, timedelta

from sqlalchemy import delete

from app.core.settings import get_settings
from app.db.session import SessionLocal
from app.main import app
from app.models.analytics import AccountStatSnapshot
from app.models.audit_event import AuditEvent
from app.models.tiktok_account import TikTokAccount
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
        db.add(
            AccountStatSnapshot(
                account_id=account.id,
                captured_at=now,
                follower_count=1,
                following_count=1,
                likes_count=0,
                video_count=1,
            )
        )
        for event_type in (
            "VIDEOS_SYNCED",
            "DRAFT_SUBMITTED",
            "DIRECT_POST_SUBMITTED",
        ):
            db.add(
                AuditEvent(
                    event_type=event_type,
                    account_id=account.id,
                    actor="test",
                    status="SUCCESS",
                    created_at=now,
                )
            )
        db.commit()

        report = build_review_package(db, settings, app)
        assert all(item["status"] == "PASS" for item in report["scope_matrix"])
        assert all(item["live_evidence"] for item in report["scope_matrix"])

        db.execute(delete(AuditEvent).where(AuditEvent.account_id == account.id))
        db.delete(account)
        db.commit()
