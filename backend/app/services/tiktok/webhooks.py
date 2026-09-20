import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.models.tiktok_account import TikTokAccount
from app.models.tiktok_draft_job import TikTokDraftJob
from app.models.tiktok_publish_job import TikTokPublishJob
from app.models.tiktok_webhook_event import TikTokWebhookEvent
from app.services.audit import record_audit


class TikTokWebhookVerificationError(ValueError):
    pass


class TikTokWebhookPayloadError(ValueError):
    pass


@dataclass(slots=True)
class WebhookEnvelope:
    client_key: str
    event_type: str
    user_open_id: str | None
    event_created_at: datetime | None
    content: dict[str, Any]


def _signature_parts(header: str) -> tuple[int, str]:
    parts: dict[str, str] = {}
    for item in header.split(","):
        key, sep, value = item.strip().partition("=")
        if sep and key:
            parts[key] = value
    if "t" not in parts or "s" not in parts:
        raise TikTokWebhookVerificationError("TikTok-Signature is missing t or s")
    try:
        timestamp = int(parts["t"])
    except ValueError as exc:
        raise TikTokWebhookVerificationError("TikTok-Signature timestamp is invalid") from exc
    signature = parts["s"].strip().lower()
    if len(signature) != 64:
        raise TikTokWebhookVerificationError("TikTok-Signature digest is invalid")
    return timestamp, signature


def verify_webhook_signature(
    *,
    raw_body: bytes,
    signature_header: str | None,
    client_secret: str,
    tolerance_seconds: int,
    now: datetime | None = None,
) -> int:
    if not signature_header:
        raise TikTokWebhookVerificationError("TikTok-Signature header is required")
    timestamp, signature = _signature_parts(signature_header)
    current = now or datetime.now(UTC)
    age = abs(int(current.timestamp()) - timestamp)
    if age > tolerance_seconds:
        raise TikTokWebhookVerificationError("TikTok webhook signature timestamp is stale")

    signed_payload = str(timestamp).encode() + b"." + raw_body
    expected = hmac.new(
        client_secret.encode(),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise TikTokWebhookVerificationError("TikTok webhook signature is invalid")
    return timestamp


def parse_webhook_payload(raw_body: bytes) -> WebhookEnvelope:
    try:
        payload = json.loads(raw_body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TikTokWebhookPayloadError("Webhook body must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise TikTokWebhookPayloadError("Webhook body must be a JSON object")

    client_key = str(payload.get("client_key") or "").strip()
    event_type = str(payload.get("event") or "").strip()
    if not client_key or not event_type:
        raise TikTokWebhookPayloadError("Webhook client_key and event are required")

    raw_content = payload.get("content", "{}")
    if isinstance(raw_content, str):
        try:
            content = json.loads(raw_content or "{}")
        except json.JSONDecodeError as exc:
            raise TikTokWebhookPayloadError("Webhook content is not valid JSON") from exc
    elif isinstance(raw_content, dict):
        content = raw_content
    else:
        raise TikTokWebhookPayloadError("Webhook content must be JSON text or object")
    if not isinstance(content, dict):
        raise TikTokWebhookPayloadError("Webhook content must decode to an object")

    created = payload.get("create_time")
    event_created_at = None
    if created is not None:
        try:
            event_created_at = datetime.fromtimestamp(int(created), tz=UTC)
        except (TypeError, ValueError, OSError) as exc:
            raise TikTokWebhookPayloadError("Webhook create_time is invalid") from exc

    user_open_id = payload.get("user_openid")
    return WebhookEnvelope(
        client_key=client_key,
        event_type=event_type,
        user_open_id=str(user_open_id) if user_open_id else None,
        event_created_at=event_created_at,
        content=content,
    )


def validate_webhook_client(envelope: WebhookEnvelope, settings: Settings) -> None:
    active_key = settings.active_tiktok_client_key
    if not active_key:
        raise TikTokWebhookVerificationError("TikTok client key is not configured")
    if not hmac.compare_digest(envelope.client_key, active_key):
        raise TikTokWebhookVerificationError("Webhook client_key does not match this app")


def ingest_webhook_event(
    db: Session,
    *,
    raw_body: bytes,
    envelope: WebhookEnvelope,
    signature_timestamp: int,
) -> tuple[TikTokWebhookEvent, bool]:
    dedup_hash = hashlib.sha256(raw_body).hexdigest()
    existing = db.scalar(
        select(TikTokWebhookEvent).where(
            TikTokWebhookEvent.dedup_hash == dedup_hash
        )
    )
    if existing is not None:
        return existing, True

    event = TikTokWebhookEvent(
        dedup_hash=dedup_hash,
        client_key=envelope.client_key,
        event_type=envelope.event_type,
        user_open_id=envelope.user_open_id,
        event_created_at=envelope.event_created_at,
        content_json=json.dumps(
            envelope.content,
            sort_keys=True,
            separators=(",", ":"),
        ),
        signature_timestamp=signature_timestamp,
        status="PENDING",
        attempts=0,
        received_at=datetime.now(UTC),
    )
    db.add(event)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(TikTokWebhookEvent).where(
                TikTokWebhookEvent.dedup_hash == dedup_hash
            )
        )
        if existing is None:
            raise
        return existing, True
    db.refresh(event)
    return event, False


def _json_ids(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        values = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(values, list):
        return []
    return [str(value) for value in values]


def _save_ids(job: TikTokDraftJob | TikTokPublishJob, values: list[str]) -> None:
    job.public_post_ids = json.dumps(
        list(dict.fromkeys(values)),
        separators=(",", ":"),
    )


def _matching_jobs(
    db: Session,
    publish_id: str,
) -> tuple[TikTokDraftJob | None, TikTokPublishJob | None]:
    draft = db.scalar(
        select(TikTokDraftJob).where(TikTokDraftJob.publish_id == publish_id)
    )
    direct = db.scalar(
        select(TikTokPublishJob).where(TikTokPublishJob.publish_id == publish_id)
    )
    return draft, direct


def _handle_authorization_removed(
    db: Session,
    event: TikTokWebhookEvent,
    content: dict[str, Any],
) -> bool:
    if not event.user_open_id:
        return False
    account = db.scalar(
        select(TikTokAccount).where(TikTokAccount.open_id == event.user_open_id)
    )
    if account is None:
        return False

    now = datetime.now(UTC)
    account.status = "REVOKED"
    account.updated_at = now

    active_drafts = db.scalars(
        select(TikTokDraftJob).where(
            TikTokDraftJob.account_id == account.id,
            TikTokDraftJob.status.not_in(["FAILED", "PUBLISH_COMPLETE"]),
        )
    ).all()
    for job in active_drafts:
        job.status = "FAILED"
        job.fail_reason = "authorization.removed"
        job.updated_at = now

    active_posts = db.scalars(
        select(TikTokPublishJob).where(
            TikTokPublishJob.account_id == account.id,
            TikTokPublishJob.status.not_in(["FAILED", "PUBLISH_COMPLETE"]),
        )
    ).all()
    for job in active_posts:
        job.status = "FAILED"
        job.fail_reason = "authorization.removed"
        job.updated_at = now

    db.commit()
    reason = content.get("reason")
    record_audit(
        db,
        event_type="WEBHOOK_AUTHORIZATION_REMOVED",
        account_id=account.id,
        status="WARNING",
        detail=f"TikTok authorization removed reason={reason}",
    )
    return True


def _handle_publish_event(
    db: Session,
    event_type: str,
    content: dict[str, Any],
) -> bool:
    publish_id = str(content.get("publish_id") or "").strip()
    if not publish_id:
        return False

    draft, direct = _matching_jobs(db, publish_id)
    jobs = [job for job in (draft, direct) if job is not None]
    if not jobs:
        return False

    now = datetime.now(UTC)
    post_id = content.get("post_id")
    reason = content.get("reason")

    for job in jobs:
        if event_type == "post.publish.failed":
            job.status = "FAILED"
            job.fail_reason = str(reason or "TikTok publishing failed")
        elif event_type == "post.publish.inbox_delivered":
            if isinstance(job, TikTokDraftJob):
                job.status = "SEND_TO_USER_INBOX"
        elif event_type == "post.publish.complete":
            job.status = "PUBLISH_COMPLETE"
        elif event_type == "post.publish.publicly_available":
            ids = _json_ids(job.public_post_ids)
            if post_id is not None:
                ids.append(str(post_id))
            _save_ids(job, ids)
        elif event_type == "post.publish.no_longer_publicaly_available":
            ids = _json_ids(job.public_post_ids)
            if post_id is not None:
                ids = [value for value in ids if value != str(post_id)]
            _save_ids(job, ids)
        else:
            return False
        job.updated_at = now

    db.commit()
    account_id = jobs[0].account_id
    record_audit(
        db,
        event_type="WEBHOOK_POST_EVENT",
        account_id=account_id,
        status=("ERROR" if event_type == "post.publish.failed" else "SUCCESS"),
        detail=f"{event_type} publish_id={publish_id}",
    )
    return True


def process_webhook_event(db: Session, event: TikTokWebhookEvent) -> str:
    try:
        content = json.loads(event.content_json)
    except json.JSONDecodeError as exc:
        raise TikTokWebhookPayloadError("Stored webhook content is invalid") from exc
    if not isinstance(content, dict):
        raise TikTokWebhookPayloadError("Stored webhook content is not an object")

    if event.event_type == "authorization.removed":
        handled = _handle_authorization_removed(db, event, content)
    elif event.event_type in {
        "post.publish.failed",
        "post.publish.complete",
        "post.publish.inbox_delivered",
        "post.publish.publicly_available",
        "post.publish.no_longer_publicaly_available",
    }:
        handled = _handle_publish_event(db, event.event_type, content)
    else:
        return "IGNORED"

    return "PROCESSED" if handled else "IGNORED"
