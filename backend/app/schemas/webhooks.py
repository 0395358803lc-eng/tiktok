from datetime import datetime

from pydantic import BaseModel


class WebhookAck(BaseModel):
    ok: bool = True
    duplicate: bool = False


class WebhookEventSummary(BaseModel):
    id: int
    event_type: str
    user_open_id: str | None
    event_created_at: datetime | None
    status: str
    attempts: int
    error_detail: str | None
    received_at: datetime
    processed_at: datetime | None
