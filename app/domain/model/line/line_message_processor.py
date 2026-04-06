from app.domain.model.line.line_messaging_webhook_event import LINEMessageEvent
from app.domain.model.line.line_user import LINEUser
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional

class LINEMessageProcessor(BaseModel):
    id: str = Field(..., title="Id")
    message_event: LINEMessageEvent = Field(..., title="MessageEvent")
    line_user: Optional[LINEUser] = None
    create_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), title="CreateDate")
    last_update_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), title="LastUpdateDate")
