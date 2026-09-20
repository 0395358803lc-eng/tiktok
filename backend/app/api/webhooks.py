from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select

from app.api.auth import DbSession, require_admin
from app.core.settings import get_settings
from app.models.admin_session import AdminSession
from app.models.tiktok_webhook_event import TikTokWebhookEvent
from app.schemas.webhooks import WebhookAck, WebhookEventSummary
from app.services.tiktok.webhooks import (
    TikTokWebhookPayloadError,
    TikTokWebhookVerificationError,
    ingest_webhook_event,
    parse_webhook_payload,
    validate_webhook_client,
    verify_webhook_signature,
)

router = APIRouter(prefix="/tiktok", tags=["webhooks"])
Admin = Annotated[AdminSession, Depends(require_admin)]


@router.post("/webhooks", response_model=WebhookAck)
async def receive_tiktok_webhook(request: Request, db: DbSession):
    settings = get_settings()
    secret = settings.active_tiktok_client_secret
    if secret is None:
        raise HTTPException(status_code=503, detail="TikTok webhook secret is not configured")

    raw_body = await request.body()
    try:
        signature_timestamp = verify_webhook_signature(
            raw_body=raw_body,
            signature_header=request.headers.get("TikTok-Signature"),
            client_secret=secret.get_secret_value(),
            tolerance_seconds=settings.webhook_signature_tolerance_seconds,
        )
        envelope = parse_webhook_payload(raw_body)
        validate_webhook_client(envelope, settings)
    except TikTokWebhookVerificationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except TikTokWebhookPayloadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _, duplicate = ingest_webhook_event(
        db,
        raw_body=raw_body,
        envelope=envelope,
        signature_timestamp=signature_timestamp,
    )
    return WebhookAck(ok=True, duplicate=duplicate)


@router.get("/webhook-events", response_model=list[WebhookEventSummary])
def list_webhook_events(
    _: Admin,
    db: DbSession,
    limit: int = Query(default=100, ge=1, le=500),
):
    rows = db.scalars(
        select(TikTokWebhookEvent)
        .order_by(TikTokWebhookEvent.id.desc())
        .limit(limit)
    ).all()
    return [
        WebhookEventSummary(
            id=row.id,
            event_type=row.event_type,
            user_open_id=row.user_open_id,
            event_created_at=row.event_created_at,
            status=row.status,
            attempts=row.attempts,
            error_detail=row.error_detail,
            received_at=row.received_at,
            processed_at=row.processed_at,
        )
        for row in rows
    ]
