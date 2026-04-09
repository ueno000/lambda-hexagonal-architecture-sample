from app.domain.model.line.line_messaging_webhook_event import LINEMessageEvent
from app.domain.model.line.line_user import LINEUser
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Any, Optional
from enum import Enum


class MessageStatus(Enum):
    Initial = 0
    AwaitingChatResponse = 1
    ReplyReady = 2
    Completed = 3
    Failed = 4


class LINEMessageProcessor(BaseModel):
    id: str = Field(..., title="Id")
    processing_status: MessageStatus = Field(
        default=MessageStatus.Initial, title="ProcessingStatus"
    )
    message_event: LINEMessageEvent = Field(..., title="MessageEvent")
    line_user: Optional[LINEUser] = None
    reply_message: Optional[str] = None
    create_date: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        title="CreateDate",
    )
    last_update_date: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        title="LastUpdateDate",
    )

    class Config:
        use_enum_values = True

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        processing_status = data.get("processing_status")
        if isinstance(processing_status, Enum):
            data["processing_status"] = processing_status.value
        return data
