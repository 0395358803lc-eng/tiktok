from datetime import UTC, datetime
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import DbSession, require_admin
from app.core.settings import get_settings
from app.models.admin_session import AdminSession
from app.models.tiktok_account import TikTokAccount
from app.schemas.operations import (
    BulkOperationRequest,
    BulkOperationResponse,
    BulkOperationResult,
    OperationsSummary,
    ProductionReadinessReport,
)
from app.services.audit import record_audit
from app.services.operations import build_operations_summary, build_production_readiness
from app.services.tiktok.client import TikTokAPIError, TikTokOAuthError
from app.services.tiktok.profile import TikTokProfileIdentityError, sync_account_profile
from app.services.tiktok.tokens import (
    TikTokConfigurationError,
    TikTokIdentityError,
    refresh_account_tokens,
)
from app.services.tiktok.videos import TikTokVideoScopeError, sync_video_page

router = APIRouter(prefix="/operations", tags=["operations"])
Admin = Annotated[AdminSession, Depends(require_admin)]


@router.get("/summary", response_model=OperationsSummary)
def operations_summary(_: Admin, db: DbSession):
    return OperationsSummary(
        **build_operations_summary(db, get_settings())
    )


@router.get("/production-readiness", response_model=ProductionReadinessReport)
def production_readiness(_: Admin, db: DbSession):
    return ProductionReadinessReport(
        **build_production_readiness(db, get_settings())
    )


def _run_account_action(
    db: Session,
    account: TikTokAccount,
    action: str,
) -> str:
    if action == "REFRESH_TOKENS":
        refresh_account_tokens(db, account)
        return "Token refresh completed"

    if action == "SYNC_PROFILE":
        sync_account_profile(db, account)
        return "Profile synchronization completed"

    if action == "SYNC_VIDEOS":
        page = sync_video_page(db, account, max_count=20)
        return f"Video synchronization completed: {len(page.videos)} item(s)"

    raise ValueError("Unsupported bulk action")


@router.post("/bulk", response_model=BulkOperationResponse)
def bulk_operation(
    payload: BulkOperationRequest,
    _: Admin,
    db: DbSession,
):
    results: list[BulkOperationResult] = []

    for account_id in list(dict.fromkeys(payload.account_ids)):
        account = db.get(TikTokAccount, account_id)
        if account is None:
            results.append(
                BulkOperationResult(
                    account_id=account_id,
                    ok=False,
                    detail="TikTok account not found",
                )
            )
            continue

        if account.status == "REVOKED":
            results.append(
                BulkOperationResult(
                    account_id=account_id,
                    ok=False,
                    detail="TikTok account is revoked",
                )
            )
            continue

        try:
            detail = _run_account_action(db, account, payload.action)
            results.append(
                BulkOperationResult(
                    account_id=account_id,
                    ok=True,
                    detail=detail,
                )
            )
            record_audit(
                db,
                event_type="BULK_OPERATION_SUCCESS",
                account_id=account_id,
                actor="admin",
                detail=f"{payload.action}: {detail}",
            )
        except TikTokOAuthError:
            account.status = "REAUTH_REQUIRED"
            account.updated_at = datetime.now(UTC)
            db.commit()
            detail = "TikTok reauthorization is required"
            results.append(
                BulkOperationResult(
                    account_id=account_id,
                    ok=False,
                    detail=detail,
                )
            )
            record_audit(
                db,
                event_type="BULK_OPERATION_FAILED",
                account_id=account_id,
                actor="admin",
                status="WARNING",
                detail=f"{payload.action}: {detail}",
            )
        except (
            TikTokConfigurationError,
            TikTokIdentityError,
            TikTokProfileIdentityError,
            TikTokAPIError,
            TikTokVideoScopeError,
            httpx.RequestError,
            ValueError,
        ) as exc:
            db.rollback()
            detail = f"{type(exc).__name__}: {str(exc)[:240]}"
            results.append(
                BulkOperationResult(
                    account_id=account_id,
                    ok=False,
                    detail=detail,
                )
            )
            record_audit(
                db,
                event_type="BULK_OPERATION_FAILED",
                account_id=account_id,
                actor="admin",
                status="ERROR",
                detail=f"{payload.action}: {detail}",
            )

    succeeded = sum(1 for result in results if result.ok)
    return BulkOperationResponse(
        action=payload.action,
        requested=len(results),
        succeeded=succeeded,
        failed=len(results) - succeeded,
        results=results,
    )
