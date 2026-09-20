from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent


def record_audit(
    db: Session,
    *,
    event_type: str,
    account_id: int | None = None,
    actor: str = "system",
    status: str = "SUCCESS",
    detail: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        event_type=event_type,
        account_id=account_id,
        actor=actor[:120],
        status=status[:32],
        detail=detail[:500] if detail else None,
        created_at=datetime.now(UTC),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
