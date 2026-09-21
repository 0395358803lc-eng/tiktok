from pathlib import Path

from fastapi import FastAPI
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.settings import ROOT_DIR, Settings
from app.models.tiktok_account import TikTokAccount
from app.models.tiktok_webhook_event import TikTokWebhookEvent
from app.services.tiktok.scopes import configured_personal_scopes, normalize_scopes

SCOPE_MATRIX = (
    {
        "scope": "user.info.basic",
        "product": "Login Kit / User Info",
        "feature": "OAuth connection and basic profile identity",
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
        "feature": "Extended profile information",
        "routes": ["/api/tiktok/accounts/{account_id}/sync-profile"],
    },
    {
        "scope": "user.info.stats",
        "product": "User Info",
        "feature": "Follower/following/likes/video statistics and historical analytics",
        "routes": [
            "/api/tiktok/accounts/{account_id}/sync-profile",
            "/api/tiktok/accounts/{account_id}/analytics",
        ],
    },
    {
        "scope": "video.list",
        "product": "Display API",
        "feature": "Authorized account public video library and metrics",
        "routes": [
            "/api/tiktok/accounts/{account_id}/videos",
            "/api/tiktok/accounts/{account_id}/videos/sync",
            "/api/tiktok/accounts/{account_id}/videos/refresh",
        ],
    },
    {
        "scope": "video.upload",
        "product": "Content Posting API",
        "feature": "Upload video/photo content to TikTok Inbox as a draft",
        "routes": [
            "/api/tiktok/accounts/{account_id}/drafts/video",
            "/api/tiktok/accounts/{account_id}/drafts/photo",
            "/api/tiktok/drafts/{job_id}/refresh",
        ],
    },
    {
        "scope": "video.publish",
        "product": "Content Posting API",
        "feature": "Direct Post with creator-info validation, scheduling and status tracking",
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
        if code_implemented and is_configured and granted_count > 0:
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
        select(func.count()).select_from(TikTokWebhookEvent)
    ) or 0

    demo_files: list[Path] = []
    for root in (ROOT_DIR / "docs", ROOT_DIR / "runtime"):
        if root.exists():
            demo_files.extend(root.rglob("*.mp4"))
            demo_files.extend(root.rglob("*.mov"))

    checks: list[dict[str, str]] = []

    def add(key: str, label: str, status: str, detail: str) -> None:
        checks.append({"key": key, "label": label, "status": status, "detail": detail})

    add(
        "website",
        "Externally facing HTTPS website",
        "PASS" if website_is_https and public_text else "FAIL",
        origin or "No frontend origin configured",
    )
    add(
        "legal",
        "Terms and Privacy visible in website source",
        "PASS" if terms_exists and privacy_exists else "FAIL",
        f"terms={terms_exists}, privacy={privacy_exists}",
    )
    add(
        "app_name",
        "Review-safe public app name",
        "FAIL" if brand_contains_tiktok else "PASS",
        (
            "Current public brand includes 'TikTok'; TikTok App Review Guidelines say "
            "the app name should not reference social media companies."
            if brand_contains_tiktok
            else "Public app name does not contain the TikTok brand reference."
        ),
    )
    add(
        "public_use_case",
        "Non-private product use case",
        "MANUAL",
        (
            "Confirm the review description presents a genuine user-facing service. "
            "TikTok states apps for private or personal use are not approved."
        ),
    )
    add(
        "url_verification_file",
        "URL verification artifact",
        "PASS" if verification_files else "FAIL",
        (
            verification_files[0].name
            if verification_files
            else "No TikTok URL-verification file found in frontend/public"
        ),
    )
    add(
        "portal_url_verification",
        "Developer Portal URL-property verification",
        "MANUAL",
        "Confirm Website, Terms, Privacy, and Content Posting URL properties are verified in the portal.",
    )
    add(
        "sandbox_demo",
        "First-review Sandbox environment",
        "PASS" if settings.tiktok_environment.lower() == "sandbox" else "WARN",
        f"TIKTOK_ENVIRONMENT={settings.tiktok_environment}",
    )
    add(
        "scope_demo_coverage",
        "Every requested scope has live Sandbox evidence",
        "PASS" if all(item["status"] == "PASS" for item in scope_items) else "FAIL",
        (
            "All six personal scopes have a connected account with live evidence."
            if all(item["status"] == "PASS" for item in scope_items)
            else "Do not request scopes that cannot yet be demonstrated end-to-end."
        ),
    )
    add(
        "webhook_test",
        "TikTok Developer Portal webhook Test URL evidence",
        "PASS" if webhook_events > 0 else "FAIL",
        f"{webhook_events} persisted webhook event(s)",
    )
    add(
        "demo_video",
        "App Review demo video evidence",
        "PASS" if demo_files else "FAIL",
        (
            f"{len(demo_files)} local demo video file(s) found"
            if demo_files
            else "No MP4/MOV review demo evidence is stored locally"
        ),
    )
    add(
        "direct_post_audit",
        "Direct Post unaudited-client restriction acknowledged",
        "MANUAL",
        (
            "Until Content Posting audit approval, Direct Post must be demonstrated under "
            "TikTok's unaudited-client restrictions, including SELF_ONLY visibility."
        ),
    )

    fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    return {
        "status": "READY_FOR_REVIEW" if fail_count == 0 else "NOT_READY_FOR_REVIEW",
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
            "Video 1 — Public website → Admin → Login Kit OAuth → basic/extended profile → stats.",
            "Video 2 — Video Library → video.list sync → stored video metrics → Analytics.",
            "Video 3 — Draft Upload Studio → video.upload → SEND_TO_USER_INBOX → webhook evidence.",
            "Video 4 — Direct Post Studio → Creator Info → SELF_ONLY post → status/webhook completion.",
            "Video 5 — Operations Control Center → disconnect/revoke → production/readiness evidence.",
        ],
        "website_url": origin + "/" if origin else "",
        "terms_url": origin + "/terms" if origin else "",
        "privacy_url": origin + "/privacy" if origin else "",
        "oauth_redirect_url": redirect,
        "webhook_url": origin + "/api/tiktok/webhooks" if origin else "",
    }
