from pathlib import Path

from fastapi import FastAPI
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.settings import ROOT_DIR, Settings
from app.models.analytics import AccountStatSnapshot
from app.models.audit_event import AuditEvent
from app.models.tiktok_account import TikTokAccount
from app.models.tiktok_draft_job import TikTokDraftJob
from app.models.tiktok_publish_job import TikTokPublishJob
from app.models.tiktok_video import TikTokVideo
from app.models.tiktok_webhook_event import TikTokWebhookEvent
from app.services.tiktok.scopes import configured_personal_scopes, normalize_scopes

SCOPE_MATRIX = (
    {
        "scope": "user.info.basic",
        "product": "Login Kit / User Info",
        "feature": "Kết nối OAuth và nhận dạng hồ sơ cơ bản",
        "routes": [
            "/api/tiktok/oauth/start",
            "/api/tiktok/oauth/callback",
            "/api/tiktok/accounts",
            "/api/tiktok/accounts/{account_id}/sync-profile",
        ],
    },
    {
        "scope": "user.info.profile",
        "product": "User Info",
        "feature": "Thông tin hồ sơ mở rộng",
        "routes": ["/api/tiktok/accounts/{account_id}/sync-profile"],
    },
    {
        "scope": "user.info.stats",
        "product": "User Info",
        "feature": "Thống kê follower/following/likes/video và phân tích lịch sử",
        "routes": [
            "/api/tiktok/accounts/{account_id}/sync-profile",
            "/api/tiktok/accounts/{account_id}/analytics",
        ],
    },
    {
        "scope": "video.list",
        "product": "Display API",
        "feature": "Thư viện video công khai và chỉ số của tài khoản được cấp quyền",
        "routes": [
            "/api/tiktok/accounts/{account_id}/videos",
            "/api/tiktok/accounts/{account_id}/videos/sync",
            "/api/tiktok/accounts/{account_id}/videos/refresh",
        ],
    },
    {
        "scope": "video.upload",
        "product": "Content Posting API",
        "feature": "Tải video/ảnh vào Hộp thư TikTok dưới dạng bản nháp",
        "routes": [
            "/api/tiktok/accounts/{account_id}/drafts/video",
            "/api/tiktok/accounts/{account_id}/drafts/photo",
            "/api/tiktok/drafts/{job_id}/refresh",
        ],
    },
    {
        "scope": "video.publish",
        "product": "Content Posting API",
        "feature": "Đăng trực tiếp với kiểm tra Creator Info, lên lịch và theo dõi trạng thái",
        "routes": [
            "/api/tiktok/accounts/{account_id}/creator-info",
            "/api/tiktok/accounts/{account_id}/publish/video",
            "/api/tiktok/accounts/{account_id}/publish/photo",
            "/api/tiktok/publish-jobs/{job_id}/refresh",
        ],
    },
)


def _route_exists(app: FastAPI, path: str) -> bool:
    return path in app.openapi().get("paths", {})


def _public_site_text() -> str:
    path = ROOT_DIR / "frontend" / "src" / "PublicSite.tsx"
    return path.read_text(errors="ignore") if path.exists() else ""


def _live_scope_evidence(
    db: Session,
    scope: str,
    accounts: list[TikTokAccount],
) -> tuple[bool, str]:
    granted = [
        account
        for account in accounts
        if account.status == "CONNECTED" and scope in normalize_scopes(account.scopes)
    ]
    if not granted:
        return False, "Chưa có tài khoản kết nối cấp quyền này."

    account_ids = [account.id for account in granted]

    if scope == "user.info.basic":
        count = sum(
            account.profile_synced_at is not None
            and bool(account.display_name or account.avatar_url)
            for account in granted
        )
        return (
            count > 0,
            f"{count} tài khoản có hồ sơ cơ bản thật đã đồng bộ từ TikTok.",
        )

    if scope == "user.info.profile":
        count = sum(
            account.profile_synced_at is not None
            and (
                account.username is not None
                or account.bio_description is not None
                or account.profile_deep_link is not None
                or account.is_verified is not None
            )
            for account in granted
        )
        return (
            count > 0,
            f"{count} tài khoản có ít nhất một trường hồ sơ mở rộng thật đã lưu.",
        )

    if scope == "user.info.stats":
        rows = db.execute(
            select(
                AccountStatSnapshot.account_id,
                func.count(AccountStatSnapshot.id),
            )
            .where(
                AccountStatSnapshot.account_id.in_(account_ids),
                or_(
                    AccountStatSnapshot.follower_count.is_not(None),
                    AccountStatSnapshot.following_count.is_not(None),
                    AccountStatSnapshot.likes_count.is_not(None),
                    AccountStatSnapshot.video_count.is_not(None),
                ),
            )
            .group_by(AccountStatSnapshot.account_id)
        ).all()
        best_count = max((int(row[1]) for row in rows), default=0)
        return (
            best_count >= 2,
            (
                f"Tài khoản tốt nhất có {best_count} snapshot thống kê thật; "
                "cần ít nhất 2 snapshot để chứng minh dữ liệu lịch sử/delta."
            ),
        )

    if scope == "video.list":
        video_count = db.scalar(
            select(func.count())
            .select_from(TikTokVideo)
            .where(TikTokVideo.account_id.in_(account_ids))
        ) or 0
        audit_count = db.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(
                AuditEvent.account_id.in_(account_ids),
                AuditEvent.event_type.in_(("VIDEOS_SYNCED", "VIDEOS_REFRESHED")),
                AuditEvent.status != "ERROR",
            )
        ) or 0
        return (
            video_count > 0 and audit_count > 0,
            f"{video_count} video thật đã lưu; {audit_count} sự kiện đồng bộ/refresh thành công.",
        )

    if scope == "video.upload":
        completed = db.scalar(
            select(func.count())
            .select_from(TikTokDraftJob)
            .where(
                TikTokDraftJob.account_id.in_(account_ids),
                TikTokDraftJob.publish_id.is_not(None),
                TikTokDraftJob.status.in_(("SEND_TO_USER_INBOX", "PUBLISH_COMPLETE")),
            )
        ) or 0
        return (
            completed > 0,
            (
                f"{completed} draft có publish_id và đã tới TikTok Inbox/hoàn tất; "
                "trạng thái SUBMITTED đơn thuần không được tính PASS."
            ),
        )

    if scope == "video.publish":
        completed = db.scalar(
            select(func.count())
            .select_from(TikTokPublishJob)
            .where(
                TikTokPublishJob.account_id.in_(account_ids),
                TikTokPublishJob.publish_id.is_not(None),
                TikTokPublishJob.status == "PUBLISH_COMPLETE",
                TikTokPublishJob.schedule_status == "COMPLETED",
            )
        ) or 0
        return (
            completed > 0,
            (
                f"{completed} Direct Post có publish_id và PUBLISH_COMPLETE; "
                "trạng thái SUBMITTED đơn thuần không được tính PASS."
            ),
        )

    return False, "Chưa định nghĩa bằng chứng live cho scope này."


def build_review_package(
    db: Session,
    settings: Settings,
    app: FastAPI,
) -> dict:
    origin = (settings.frontend_origin or "").rstrip("/")
    configured = set(configured_personal_scopes(settings))
    accounts = db.scalars(select(TikTokAccount)).all()

    scope_items = []
    for spec in SCOPE_MATRIX:
        scope = spec["scope"]
        granted_count = sum(
            1
            for account in accounts
            if account.status == "CONNECTED"
            and scope in normalize_scopes(account.scopes)
        )
        routes = list(spec["routes"])
        code_implemented = all(_route_exists(app, route) for route in routes)
        is_configured = scope in configured
        live_evidence, evidence_detail = _live_scope_evidence(db, scope, accounts)
        if (
            code_implemented
            and is_configured
            and granted_count > 0
            and live_evidence
        ):
            item_status = "PASS"
        elif not is_configured:
            item_status = "NOT_CONFIGURED"
        else:
            item_status = "BLOCKED"
        scope_items.append(
            {
                "scope": scope,
                "product": spec["product"],
                "feature": spec["feature"],
                "configured": is_configured,
                "connected_accounts_with_scope": granted_count,
                "code_implemented": code_implemented,
                "live_evidence": live_evidence,
                "evidence_detail": evidence_detail,
                "evidence_routes": routes,
                "status": item_status,
            }
        )

    public_text = _public_site_text()
    brand_contains_tiktok = "TH TikTok Manager" in public_text
    terms_exists = "export function TermsPage" in public_text
    privacy_exists = "export function PrivacyPage" in public_text
    website_is_https = origin.startswith("https://")
    redirect = settings.tiktok_redirect_uri or ""
    verification_files = list((ROOT_DIR / "frontend" / "public").glob("tiktok*.txt"))
    webhook_events = db.scalar(
        select(func.count())
        .select_from(TikTokWebhookEvent)
        .where(
            TikTokWebhookEvent.status == "PROCESSED",
            TikTokWebhookEvent.event_type.in_(
                (
                    "authorization.removed",
                    "post.publish.failed",
                    "post.publish.complete",
                    "post.publish.inbox_delivered",
                    "post.publish.publicly_available",
                    "post.publish.no_longer_publicaly_available",
                )
            ),
        )
    ) or 0

    demo_files: list[Path] = []
    for root in (
        ROOT_DIR / "docs" / "review-evidence",
        ROOT_DIR / "runtime" / "review-evidence",
    ):
        if root.exists():
            demo_files.extend(root.rglob("*.mp4"))
            demo_files.extend(root.rglob("*.mov"))

    checks: list[dict[str, str]] = []

    def add(key: str, label: str, status: str, detail: str) -> None:
        checks.append({"key": key, "label": label, "status": status, "detail": detail})

    add(
        "website",
        "Website HTTPS công khai",
        "PASS" if website_is_https and public_text else "FAIL",
        origin or "Chưa cấu hình frontend origin",
    )
    add(
        "legal",
        "Điều khoản và Quyền riêng tư hiển thị trên website",
        "PASS" if terms_exists and privacy_exists else "FAIL",
        f"điều khoản={terms_exists}, quyền riêng tư={privacy_exists}",
    )
    add(
        "app_name",
        "Tên hiển thị website phù hợp để review",
        "FAIL" if brand_contains_tiktok else "PASS",
        (
            "Tên public hiện chứa từ 'TikTok'; hướng dẫn App Review nêu rằng tên ứng dụng không nên tham chiếu tên công ty mạng xã hội."
            if brand_contains_tiktok
            else "Tên hiển thị website hiện là TH Creator Manager và không dùng TikTok trong tên thương hiệu."
        ),
    )
    add(
        "portal_app_name",
        "Tên ứng dụng trong TikTok Developer Portal",
        "MANUAL",
        "Đổi App name trong Developer Portal thành cùng tên public TH Creator Manager trước khi nộp review.",
    )
    add(
        "public_use_case",
        "Use case không phải công cụ riêng tư/cá nhân",
        "MANUAL",
        (
            "Xác nhận mô tả review thể hiện đây là dịch vụ thực sự dành cho người dùng. TikTok nêu rằng ứng dụng chỉ dùng riêng tư/cá nhân không được duyệt."
        ),
    )
    add(
        "url_verification_file",
        "File xác minh URL",
        "PASS" if verification_files else "FAIL",
        (
            verification_files[0].name
            if verification_files
            else "Không tìm thấy file xác minh URL TikTok trong frontend/public"
        ),
    )
    add(
        "portal_url_verification",
        "Xác minh URL/property trong Developer Portal",
        "MANUAL",
        "Xác nhận Website, Terms, Privacy và URL/property của Content Posting đã được xác minh trong Developer Portal.",
    )
    add(
        "sandbox_demo",
        "Môi trường Sandbox cho lần review đầu",
        "PASS" if settings.tiktok_environment.lower() == "sandbox" else "WARN",
        f"TIKTOK_ENVIRONMENT={settings.tiktok_environment}",
    )
    add(
        "scope_demo_coverage",
        "Mọi scope xin duyệt đều có bằng chứng Sandbox thật",
        "PASS" if all(item["status"] == "PASS" for item in scope_items) else "FAIL",
        (
            "Cả 6 scope tài khoản cá nhân đều có tài khoản đã kết nối và bằng chứng thật."
            if all(item["status"] == "PASS" for item in scope_items)
            else "Không xin scope chưa thể demo end-to-end."
        ),
    )
    add(
        "webhook_endpoint_security",
        "Webhook endpoint HTTPS và xác minh chữ ký",
        (
            "PASS"
            if website_is_https and settings.active_tiktok_client_secret is not None
            else "FAIL"
        ),
        (
            "Endpoint /api/tiktok/webhooks dùng HTTPS, kiểm tra TikTok-Signature và có chống trùng lặp."
            if website_is_https and settings.active_tiktok_client_secret is not None
            else "Webhook HTTPS hoặc client secret chưa sẵn sàng."
        ),
    )
    add(
        "webhook_test",
        "Bằng chứng Webhook Test URL từ TikTok Developer Portal",
        "MANUAL",
        (
            f"{webhook_events} sự kiện TikTok đã xử lý có kiểu hợp lệ trong DB. "
            "Vẫn phải xác nhận thủ công Test URL/ảnh hoặc video trong Developer Portal "
            "vì DB không thể chứng minh nguồn gửi là giao diện TikTok Portal."
        ),
    )
    add(
        "demo_video",
        "Bằng chứng video demo App Review",
        "PASS" if demo_files else "FAIL",
        (
            f"Tìm thấy {len(demo_files)} file video demo cục bộ"
            if demo_files
            else "Chưa lưu bằng chứng video review MP4/MOV cục bộ"
        ),
    )
    add(
        "direct_post_audit",
        "Xác nhận giới hạn Direct Post của client chưa audit",
        "MANUAL",
        (
            "Trước khi được duyệt audit Content Posting, Direct Post phải được demo theo giới hạn client chưa audit của TikTok, bao gồm quyền xem SELF_ONLY."
        ),
    )

    fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    manual_count = sum(1 for check in checks if check["status"] == "MANUAL")
    if fail_count > 0:
        review_status = "NOT_READY_FOR_REVIEW"
    elif manual_count > 0:
        review_status = "READY_FOR_MANUAL_VERIFICATION"
    else:
        review_status = "READY_FOR_REVIEW"

    return {
        "status": review_status,
        "products": [
            "Login Kit",
            "User Info",
            "Display API",
            "Content Posting API",
            "Webhooks",
        ],
        "scope_matrix": scope_items,
        "checks": checks,
        "demo_video_plan": [
            "Video 1 — Website công khai → Quản trị → Login Kit OAuth → hồ sơ cơ bản/mở rộng → thống kê.",
            "Video 2 — Thư viện video → đồng bộ video.list → chỉ số video đã lưu → Phân tích.",
            "Video 3 — Tải bản nháp → video.upload → SEND_TO_USER_INBOX → bằng chứng Webhook.",
            "Video 4 — Đăng trực tiếp → Creator Info → bài SELF_ONLY → trạng thái/Webhook hoàn tất.",
            "Video 5 — Trung tâm điều hành → ngắt kết nối/thu hồi → bằng chứng production/readiness.",
        ],
        "website_url": origin + "/" if origin else "",
        "terms_url": origin + "/terms" if origin else "",
        "privacy_url": origin + "/privacy" if origin else "",
        "oauth_redirect_url": redirect,
        "webhook_url": origin + "/api/tiktok/webhooks" if origin else "",
    }
