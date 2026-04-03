from typing import Optional

from app.domain.model.line.line_messaging_webhook_event import LINEMessagingWebhookEvent
from pydantic import BaseModel


class CreateLINEMessagingProcessorCommand(BaseModel):
    event: LINEMessagingWebhookEvent
