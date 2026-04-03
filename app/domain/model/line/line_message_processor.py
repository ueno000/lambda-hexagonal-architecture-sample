from app.domain.model.line.line_messaging_webhook_event import LINEMessageEvent
from pydantic import BaseModel, Field


class LINEMessageProcessor(BaseModel):
    id: str = Field(..., title="Id")
    messageEvents: LINEMessageEvent = Field(..., title="MessageEvents")
    createDate: str = Field(..., title="CreateDate")
    lastUpdateDate: str = Field(..., title="LastUpdateDate")
