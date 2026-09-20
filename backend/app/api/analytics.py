from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.auth import DbSession, require_admin
from app.models.admin_session import AdminSession
from app.models.tiktok_account import TikTokAccount
from app.schemas.analytics import TikTokAnalyticsReport
from app.services.analytics import build_analytics_report

router = APIRouter(prefix="/tiktok", tags=["analytics"])
Admin = Annotated[AdminSession, Depends(require_admin)]


@router.get(
    "/accounts/{account_id}/analytics",
    response_model=TikTokAnalyticsReport,
)
def account_analytics(
    account_id: int,
    _: Admin,
    db: DbSession,
    days: int = Query(default=30),
):
    if days not in {7, 30, 90}:
        raise HTTPException(
            status_code=400,
            detail="Analytics range must be 7, 30, or 90 days",
        )

    account = db.get(TikTokAccount, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="TikTok account not found")

    return TikTokAnalyticsReport(
        **build_analytics_report(db, account_id=account_id, days=days)
    )
