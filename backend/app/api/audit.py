from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.api.auth import DbSession, require_admin
from app.models.admin_session import AdminSession
from app.models.audit_event import AuditEvent
from app.schemas.audit import AuditEventSummary

router = APIRouter(prefix="/audit", tags=["audit"])
Admin = Annotated[AdminSession, Depends(require_admin)]


@router.get("/events", response_model=list[AuditEventSummary])
def list_audit_events(
    _: Admin,
    db: DbSession,
    limit: int = Query(default=100, ge=1, le=500),
):
    rows = db.scalars(
        select(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit)
    ).all()
    return [
        AuditEventSummary(
            id=row.id,
            event_type=row.event_type,
            account_id=row.account_id,
            actor=row.actor,
            status=row.status,
            detail=row.detail,
            created_at=row.created_at,
        )
        for row in rows
    ]
