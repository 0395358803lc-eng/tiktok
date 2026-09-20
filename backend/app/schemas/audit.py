from datetime import datetime

from pydantic import BaseModel


class AuditEventSummary(BaseModel):
    id: int
    event_type: str
    account_id: int | None
    actor: str
    status: str
    detail: str | None
    created_at: datetime
