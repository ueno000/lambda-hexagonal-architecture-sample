from typing import Optional

from app.domain.model.line.line_messaging_webhook_event import LINEMessagingWebhookEvent
from app.domain.model.line.line_user import LINEUser
from pydantic import BaseModel


class UpdateLINEMessagingProcessorCommand(BaseModel):
    id: str
    message_event: LINEMessagingWebhookEvent
    line_user: LINEUser
    last_update_date: str
