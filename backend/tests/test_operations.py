from datetime import UTC, datetime, timedelta

from sqlalchemy import delete

from app.api.operations import _run_account_action
from app.core.settings import get_settings
from app.db.session import SessionLocal
from app.models.tiktok_account import TikTokAccount
from app.services.operations import build_operations_summary, build_production_readiness
from app.services.tiktok.crypto import encrypt_token


def _account(db, open_id: str, scopes: str = "user.info.basic") -> TikTokAccount:
    now = datetime.now(UTC)
    account = TikTokAccount(
        open_id=open_id,
        scopes=scopes,
        access_token_enc=encrypt_token("ops-access"),
        refresh_token_enc=encrypt_token("ops-refresh"),
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


def test_operations_summary_reports_missing_scopes():
    open_id = "ops-summary-open-id"
    with SessionLocal() as db:
        db.execute(delete(TikTokAccount).where(TikTokAccount.open_id == open_id))
        db.commit()
        account = _account(db, open_id)

        summary = build_operations_summary(db, get_settings())
        row = next(item for item in summary["accounts"] if item["account_id"] == account.id)

        assert row["status"] == "CONNECTED"
        assert row["health"] in {"WARNING", "ERROR"}
        assert "user.info.basic" in row["scopes"]
        assert row["access_token_minutes_left"] > 0
        assert isinstance(row["issues"], list)

        db.delete(account)
        db.commit()


def test_production_readiness_returns_detailed_checks():
    with SessionLocal() as db:
        report = build_production_readiness(db, get_settings())
        keys = {item["key"] for item in report["checks"]}
        assert {
            "app_env",
            "tiktok_env",
            "oauth",
            "redirect_https",
            "frontend_https",
            "all_personal_scopes",
            "workers",
            "backup",
            "migration",
            "webhooks",
            "publish_queue",
            "legal_pages",
        }.issubset(keys)
        assert report["status"] in {"READY", "NOT_READY"}
        assert report["fail_count"] + report["warn_count"] + report["pass_count"] == len(
            report["checks"]
        )


def test_bulk_action_dispatch_can_be_mocked(monkeypatch):
    open_id = "ops-bulk-open-id"
    with SessionLocal() as db:
        db.execute(delete(TikTokAccount).where(TikTokAccount.open_id == open_id))
        db.commit()
        account = _account(db, open_id)

        called = {"profile": 0}

        def fake_sync(_db, target):
            assert target.id == account.id
            called["profile"] += 1

        monkeypatch.setattr("app.api.operations.sync_account_profile", fake_sync)
        detail = _run_account_action(db, account, "SYNC_PROFILE")
        assert detail == "Profile synchronization completed"
        assert called["profile"] == 1

        db.delete(account)
        db.commit()
