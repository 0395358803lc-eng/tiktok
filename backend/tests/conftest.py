import pytest
from sqlalchemy import delete, func, select

from app.db.session import SessionLocal
from app.models.admin_session import AdminSession
from app.models.audit_event import AuditEvent


@pytest.fixture(autouse=True)
def cleanup_test_side_effects():
    with SessionLocal() as db:
        audit_floor = db.scalar(select(func.coalesce(func.max(AuditEvent.id), 0))) or 0
        session_floor = db.scalar(select(func.coalesce(func.max(AdminSession.id), 0))) or 0

    yield

    with SessionLocal() as db:
        db.execute(delete(AuditEvent).where(AuditEvent.id > audit_floor))
        db.execute(delete(AdminSession).where(AdminSession.id > session_floor))
        db.commit()
