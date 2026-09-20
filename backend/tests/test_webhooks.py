import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import delete

from app.core.settings import get_settings
from app.db.session import SessionLocal
from app.main import app
from app.models.tiktok_account import TikTokAccount
from app.models.tiktok_draft_job import TikTokDraftJob
from app.models.tiktok_webhook_event import TikTokWebhookEvent
from app.services.tiktok.crypto import encrypt_token
from app.services.tiktok.webhooks import (
    TikTokWebhookVerificationError,
    verify_webhook_signature,
)
from app.workers.tiktok_webhooks import run_once

client = TestClient(app)


def _signature(secret: str, timestamp: int, body: bytes) -> str:
    digest = hmac.new(
        secret.encode(),
        str(timestamp).encode() + b"." + body,
        hashlib.sha256,
    ).hexdigest()
    return f"t={timestamp},s={digest}"


def _account(db, open_id: str) -> TikTokAccount:
    now = datetime.now(UTC)
    account = TikTokAccount(
        open_id=open_id,
        scopes="user.info.basic",
        access_token_enc=encrypt_token("webhook-access"),
        refresh_token_enc=encrypt_token("webhook-refresh"),
        access_token_expires_at=now + timedelta(days=1),
        refresh_token_expires_at=now + timedelta(days=30),
        status="CONNECTED",
        created_at=now,
        updated_at=now,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def _event(
    db,
    *,
    dedup_hash: str,
    event_type: str,
    user_open_id: str | None,
    content: dict,
) -> TikTokWebhookEvent:
    now = datetime.now(UTC)
    event = TikTokWebhookEvent(
        dedup_hash=dedup_hash,
        client_key="webhook-test-client",
        event_type=event_type,
        user_open_id=user_open_id,
        event_created_at=now,
        content_json=json.dumps(content, separators=(",", ":")),
        signature_timestamp=int(now.timestamp()),
        status="PENDING",
        attempts=0,
        received_at=now,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def test_webhook_signature_verification():
    body = b'{"event":"authorization.removed"}'
    timestamp = 1_700_000_000
    secret = "webhook-secret"
    header = _signature(secret, timestamp, body)
    now = datetime.fromtimestamp(timestamp, tz=UTC)

    assert (
        verify_webhook_signature(
            raw_body=body,
            signature_header=header,
            client_secret=secret,
            tolerance_seconds=300,
            now=now,
        )
        == timestamp
    )

    try:
        verify_webhook_signature(
            raw_body=body,
            signature_header="t=1700000000,s=" + ("0" * 64),
            client_secret=secret,
            tolerance_seconds=300,
            now=now,
        )
    except TikTokWebhookVerificationError as exc:
        assert "invalid" in str(exc)
    else:
        raise AssertionError("Expected invalid signature to be rejected")


def test_webhook_endpoint_is_signed_and_idempotent(monkeypatch):
    secret = "webhook-endpoint-secret"
    key = "webhook-endpoint-client"
    settings = get_settings().model_copy(
        update={
            "tiktok_environment": "sandbox",
            "tiktok_sandbox_client_key": key,
            "tiktok_sandbox_client_secret": SecretStr(secret),
            "webhook_signature_tolerance_seconds": 300,
        }
    )
    monkeypatch.setattr("app.api.webhooks.get_settings", lambda: settings)

    timestamp = int(datetime.now(UTC).timestamp())
    payload = {
        "client_key": key,
        "event": "unknown.test.event",
        "create_time": timestamp,
        "user_openid": "webhook-endpoint-open-id",
        "content": "{}",
    }
    body = json.dumps(payload, separators=(",", ":")).encode()
    signature = _signature(secret, timestamp, body)
    dedup_hash = hashlib.sha256(body).hexdigest()

    first = client.post(
        "/api/tiktok/webhooks",
        content=body,
        headers={
            "Content-Type": "application/json",
            "TikTok-Signature": signature,
        },
    )
    second = client.post(
        "/api/tiktok/webhooks",
        content=body,
        headers={
            "Content-Type": "application/json",
            "TikTok-Signature": signature,
        },
    )
    invalid = client.post(
        "/api/tiktok/webhooks",
        content=body,
        headers={
            "Content-Type": "application/json",
            "TikTok-Signature": "t=" + str(timestamp) + ",s=" + ("0" * 64),
        },
    )

    assert first.status_code == 200
    assert first.json()["duplicate"] is False
    assert second.status_code == 200
    assert second.json()["duplicate"] is True
    assert invalid.status_code == 401

    with SessionLocal() as db:
        rows = db.query(TikTokWebhookEvent).filter(
            TikTokWebhookEvent.dedup_hash == dedup_hash
        ).all()
        assert len(rows) == 1
        db.execute(
            delete(TikTokWebhookEvent).where(
                TikTokWebhookEvent.dedup_hash == dedup_hash
            )
        )
        db.commit()


def test_authorization_removed_webhook_revokes_account():
    open_id = "webhook-auth-removed-open-id"
    dedup = "a" * 64
    with SessionLocal() as db:
        db.execute(delete(TikTokWebhookEvent).where(TikTokWebhookEvent.dedup_hash == dedup))
        db.execute(delete(TikTokAccount).where(TikTokAccount.open_id == open_id))
        db.commit()
        account = _account(db, open_id)
        account_id = account.id
        event = _event(
            db,
            dedup_hash=dedup,
            event_type="authorization.removed",
            user_open_id=open_id,
            content={"reason": 1},
        )
        event_id = event.id

    processed, failed = run_once()
    assert processed >= 1
    assert failed == 0

    with SessionLocal() as db:
        account = db.get(TikTokAccount, account_id)
        event = db.get(TikTokWebhookEvent, event_id)
        assert account is not None
        assert event is not None
        assert account.status == "REVOKED"
        assert event.status == "PROCESSED"
        db.delete(event)
        db.delete(account)
        db.commit()


def test_content_posting_webhooks_update_draft_job():
    open_id = "webhook-publish-open-id"
    inbox_hash = "b" * 64
    complete_hash = "c" * 64
    publish_id = "webhook-publish-id"

    with SessionLocal() as db:
        db.execute(
            delete(TikTokWebhookEvent).where(
                TikTokWebhookEvent.dedup_hash.in_([inbox_hash, complete_hash])
            )
        )
        db.execute(delete(TikTokAccount).where(TikTokAccount.open_id == open_id))
        db.commit()
        account = _account(db, open_id)
        job = TikTokDraftJob(
            account_id=account.id,
            media_type="VIDEO",
            source_type="FILE_UPLOAD",
            publish_id=publish_id,
            status="SUBMITTED",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = job.id

        _event(
            db,
            dedup_hash=inbox_hash,
            event_type="post.publish.inbox_delivered",
            user_open_id=open_id,
            content={"publish_id": publish_id, "publish_type": "INBOX_SHARE"},
        )

    processed, failed = run_once()
    assert processed >= 1
    assert failed == 0

    with SessionLocal() as db:
        job = db.get(TikTokDraftJob, job_id)
        assert job is not None
        assert job.status == "SEND_TO_USER_INBOX"
        _event(
            db,
            dedup_hash=complete_hash,
            event_type="post.publish.complete",
            user_open_id=open_id,
            content={"publish_id": publish_id, "publish_type": "INBOX_SHARE"},
        )

    processed, failed = run_once()
    assert processed >= 1
    assert failed == 0

    with SessionLocal() as db:
        job = db.get(TikTokDraftJob, job_id)
        assert job is not None
        assert job.status == "PUBLISH_COMPLETE"
        db.execute(
            delete(TikTokWebhookEvent).where(
                TikTokWebhookEvent.dedup_hash.in_([inbox_hash, complete_hash])
            )
        )
        account_id = job.account_id
        db.execute(delete(TikTokDraftJob).where(TikTokDraftJob.id == job_id))
        db.execute(delete(TikTokAccount).where(TikTokAccount.id == account_id))
        db.commit()
