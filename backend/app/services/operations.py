import os
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.settings import ROOT_DIR, Settings
from app.models.tiktok_account import TikTokAccount
from app.models.tiktok_draft_job import TikTokDraftJob
from app.models.tiktok_publish_job import TikTokPublishJob
from app.models.tiktok_video import TikTokVideo
from app.models.tiktok_webhook_event import TikTokWebhookEvent
from app.services.tiktok.oauth import oauth_configured
from app.services.tiktok.scopes import PERSONAL_SCOPES, configured_personal_scopes, normalize_scopes

EXPECTED_MIGRATION = "0011_publish_scheduler"
WORKER_PIDS = {
    "token_worker": "token-worker.pid",
    "scheduler_worker": "scheduler-worker.pid",
    "webhook_worker": "webhook-worker.pid",
    "publish_worker": "publish-worker.pid",
    "draft_worker": "draft-worker.pid",
    "analytics_worker": "analytics-worker.pid",
    "watchdog": "watchdog.pid",
}


def _minutes_left(value: datetime, now: datetime) -> int:
    return int((value - now).total_seconds() // 60)


def _days_left(value: datetime, now: datetime) -> int:
    return int((value - now).total_seconds() // 86400)


def _worker_alive(name: str) -> bool:
    pid_path = ROOT_DIR / "runtime" / name
    try:
        pid = int(pid_path.read_text().strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def _latest_backup() -> tuple[Path | None, float | None]:
    root = ROOT_DIR / "runtime" / "backups"
    files = list(root.glob("th_tiktok_*.dump")) if root.exists() else []
    if not files:
        return None, None
    latest = max(files, key=lambda path: path.stat().st_mtime)
    age_hours = (datetime.now(UTC).timestamp() - latest.stat().st_mtime) / 3600
    return latest, age_hours


def build_operations_summary(db: Session, settings: Settings) -> dict:
    now = datetime.now(UTC)
    configured_scopes = set(configured_personal_scopes(settings))
    accounts = db.scalars(select(TikTokAccount).order_by(TikTokAccount.id.desc())).all()

    rows = []
    total_scheduled = 0
    total_running = 0
    total_failed = 0

    for account in accounts:
        granted = set(normalize_scopes(account.scopes))
        missing = sorted(configured_scopes - granted)
        access_minutes = _minutes_left(account.access_token_expires_at, now)
        refresh_days = _days_left(account.refresh_token_expires_at, now)
        profile_age = (
            (now - account.profile_synced_at).total_seconds() / 3600
            if account.profile_synced_at is not None
            else None
        )

        stored_videos = db.scalar(
            select(func.count()).select_from(TikTokVideo).where(
                TikTokVideo.account_id == account.id
            )
        ) or 0
        scheduled = db.scalar(
            select(func.count()).select_from(TikTokPublishJob).where(
                TikTokPublishJob.account_id == account.id,
                TikTokPublishJob.schedule_status.in_(["SCHEDULED", "READY"]),
            )
        ) or 0
        running = db.scalar(
            select(func.count()).select_from(TikTokPublishJob).where(
                TikTokPublishJob.account_id == account.id,
                TikTokPublishJob.schedule_status == "RUNNING",
            )
        ) or 0
        failed_posts = db.scalar(
            select(func.count()).select_from(TikTokPublishJob).where(
                TikTokPublishJob.account_id == account.id,
                TikTokPublishJob.schedule_status == "FAILED",
            )
        ) or 0
        failed_drafts = db.scalar(
            select(func.count()).select_from(TikTokDraftJob).where(
                TikTokDraftJob.account_id == account.id,
                TikTokDraftJob.status == "FAILED",
            )
        ) or 0
        webhook_errors = db.scalar(
            select(func.count()).select_from(TikTokWebhookEvent).where(
                TikTokWebhookEvent.user_open_id == account.open_id,
                TikTokWebhookEvent.status == "ERROR",
            )
        ) or 0

        issues: list[str] = []
        if account.status != "CONNECTED":
            issues.append(f"Trạng thái tài khoản: {account.status}")
        if missing:
            issues.append("Thiếu scope đã cấu hình: " + ", ".join(missing))
        if access_minutes <= 30:
            issues.append("Access token sẽ hết hạn trong vòng 30 phút")
        if refresh_days <= 7:
            issues.append("Refresh token sẽ hết hạn trong vòng 7 ngày")
        if account.profile_synced_at is None:
            issues.append("Hồ sơ chưa từng được đồng bộ")
        elif profile_age is not None and profile_age > 24:
            issues.append("Dữ liệu hồ sơ đã cũ hơn 24 giờ")
        if failed_posts:
            issues.append(f"{failed_posts} tác vụ đăng bài thất bại")
        if failed_drafts:
            issues.append(f"{failed_drafts} tác vụ bản nháp thất bại")
        if webhook_errors:
            issues.append(f"{webhook_errors} lỗi Webhook")

        severe = (
            account.status in {"ERROR", "REVOKED", "REAUTH_REQUIRED"}
            or refresh_days <= 0
            or webhook_errors > 0
        )
        health = "ERROR" if severe else ("WARNING" if issues else "OK")

        total_scheduled += scheduled
        total_running += running
        total_failed += failed_posts

        rows.append(
            {
                "account_id": account.id,
                "display_name": account.display_name,
                "username": account.username,
                "status": account.status,
                "scopes": sorted(granted),
                "missing_configured_scopes": missing,
                "access_token_expires_at": account.access_token_expires_at,
                "refresh_token_expires_at": account.refresh_token_expires_at,
                "access_token_minutes_left": access_minutes,
                "refresh_token_days_left": refresh_days,
                "profile_synced_at": account.profile_synced_at,
                "profile_age_hours": round(profile_age, 1) if profile_age is not None else None,
                "stored_videos": stored_videos,
                "scheduled_posts": scheduled,
                "running_posts": running,
                "failed_posts": failed_posts,
                "failed_drafts": failed_drafts,
                "webhook_errors": webhook_errors,
                "health": health,
                "issues": issues,
            }
        )

    pending_webhooks = db.scalar(
        select(func.count()).select_from(TikTokWebhookEvent).where(
            TikTokWebhookEvent.status == "PENDING"
        )
    ) or 0
    error_webhooks = db.scalar(
        select(func.count()).select_from(TikTokWebhookEvent).where(
            TikTokWebhookEvent.status == "ERROR"
        )
    ) or 0

    return {
        "generated_at": now,
        "accounts_total": len(accounts),
        "connected_accounts": sum(1 for row in accounts if row.status == "CONNECTED"),
        "reauth_accounts": sum(1 for row in accounts if row.status == "REAUTH_REQUIRED"),
        "issue_accounts": sum(1 for row in rows if row["health"] != "OK"),
        "scheduled_posts": total_scheduled,
        "running_posts": total_running,
        "failed_posts": total_failed,
        "pending_webhooks": pending_webhooks,
        "error_webhooks": error_webhooks,
        "accounts": rows,
    }


def build_production_readiness(db: Session, settings: Settings) -> dict:
    now = datetime.now(UTC)
    checks: list[dict[str, str]] = []

    def add(key: str, label: str, status: str, detail: str) -> None:
        checks.append({"key": key, "label": label, "status": status, "detail": detail})

    add(
        "app_env",
        "Môi trường ứng dụng",
        "PASS" if settings.app_env.lower() == "production" else "FAIL",
        f"APP_ENV={settings.app_env}",
    )
    add(
        "tiktok_env",
        "Môi trường TikTok",
        "PASS" if settings.tiktok_environment.lower() == "production" else "FAIL",
        f"TIKTOK_ENVIRONMENT={settings.tiktok_environment}",
    )
    add(
        "oauth",
        "Cấu hình OAuth TikTok",
        "PASS" if oauth_configured(settings) else "FAIL",
        "OAuth client, secret và redirect URI đã được cấu hình"
        if oauth_configured(settings)
        else "Cấu hình OAuth chưa đầy đủ",
    )

    redirect = settings.tiktok_redirect_uri or ""
    add(
        "redirect_https",
        "HTTPS OAuth redirect",
        "PASS" if redirect.startswith("https://") else "FAIL",
        redirect or "Chưa cấu hình redirect URI",
    )
    origin = settings.frontend_origin or ""
    add(
        "frontend_https",
        "HTTPS frontend origin",
        "PASS" if origin.startswith("https://") else "FAIL",
        origin or "Chưa cấu hình frontend origin",
    )

    configured = set(configured_personal_scopes(settings))
    missing_scopes = [scope for scope in PERSONAL_SCOPES if scope not in configured]
    add(
        "all_personal_scopes",
        "Scope API tài khoản cá nhân",
        "PASS" if not missing_scopes else "FAIL",
        "Đã cấu hình đầy đủ các scope tài khoản cá nhân được hỗ trợ"
        if not missing_scopes
        else "Thiếu: " + ", ".join(missing_scopes),
    )

    account_count = db.scalar(
        select(func.count()).select_from(TikTokAccount).where(
            TikTokAccount.status == "CONNECTED"
        )
    ) or 0
    add(
        "connected_account",
        "Tài khoản TikTok đã kết nối",
        "PASS" if account_count > 0 else "FAIL",
        f"{account_count} tài khoản đã kết nối",
    )

    account_issues = 0
    for account in db.scalars(select(TikTokAccount)).all():
        granted = set(normalize_scopes(account.scopes))
        if account.status != "CONNECTED" or configured - granted:
            account_issues += 1
    add(
        "account_scope_health",
        "Tình trạng scope của tài khoản đã kết nối",
        "PASS" if account_issues == 0 and account_count > 0 else "WARN",
        f"{account_issues} tài khoản cần chú ý",
    )

    dead_workers = [
        key for key, filename in WORKER_PIDS.items() if not _worker_alive(filename)
    ]
    add(
        "workers",
        "Worker nền",
        "PASS" if not dead_workers else "FAIL",
        "Tất cả worker cần thiết đang chạy"
        if not dead_workers
        else "Đang dừng: " + ", ".join(dead_workers),
    )

    backup, backup_age = _latest_backup()
    add(
        "backup",
        "Backup PostgreSQL gần nhất",
        "PASS" if backup is not None and backup_age is not None and backup_age <= 24 else "FAIL",
        (
            f"{backup.name}, cách đây {backup_age:.1f} giờ"
            if backup is not None and backup_age is not None
            else "Chưa tìm thấy backup"
        ),
    )

    migration = db.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
    add(
        "migration",
        "Migration cơ sở dữ liệu",
        "PASS" if migration == EXPECTED_MIGRATION else "FAIL",
        f"Hiện tại={migration or 'không rõ'}, yêu cầu={EXPECTED_MIGRATION}",
    )

    error_webhooks = db.scalar(
        select(func.count()).select_from(TikTokWebhookEvent).where(
            TikTokWebhookEvent.status == "ERROR"
        )
    ) or 0
    pending_webhooks = db.scalar(
        select(func.count()).select_from(TikTokWebhookEvent).where(
            TikTokWebhookEvent.status == "PENDING",
            TikTokWebhookEvent.received_at < now.replace(microsecond=0),
        )
    ) or 0
    add(
        "webhooks",
        "Hàng đợi xử lý Webhook",
        "PASS" if error_webhooks == 0 else "FAIL",
        f"lỗi={error_webhooks}, đang chờ={pending_webhooks}",
    )

    stuck_cutoff = now.timestamp() - 3600
    stuck_running = 0
    for job in db.scalars(
        select(TikTokPublishJob).where(TikTokPublishJob.schedule_status == "RUNNING")
    ).all():
        if job.updated_at.timestamp() < stuck_cutoff:
            stuck_running += 1
    add(
        "publish_queue",
        "Hàng đợi đăng bài",
        "PASS" if stuck_running == 0 else "FAIL",
        f"{stuck_running} tác vụ chạy quá 1 giờ",
    )

    public_site = ROOT_DIR / "frontend" / "src" / "PublicSite.tsx"
    legal_text = public_site.read_text(errors="ignore") if public_site.exists() else ""
    terms_exists = "export function TermsPage" in legal_text
    privacy_exists = "export function PrivacyPage" in legal_text
    add(
        "legal_pages",
        "Trang Điều khoản và Quyền riêng tư",
        "PASS" if terms_exists and privacy_exists else "FAIL",
        f"điều khoản={terms_exists}, quyền riêng tư={privacy_exists}",
    )

    fail_count = sum(1 for item in checks if item["status"] == "FAIL")
    warn_count = sum(1 for item in checks if item["status"] == "WARN")
    pass_count = sum(1 for item in checks if item["status"] == "PASS")
    return {
        "generated_at": now,
        "status": "READY" if fail_count == 0 else "NOT_READY",
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "checks": checks,
    }
