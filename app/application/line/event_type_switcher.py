from aws_lambda_powertools import Logger, Tracer
from app.application.line.assign_received_message import assign_received_message
from app.domain.model.line.line_messaging_webhook_event import (
    LINEMessagingWebhookEvent,
)

logger = Logger()
tracer = Tracer()

SUPPORTED_MESSAGE_TYPES = {"text", "sticker"}
MESSAGE_EVENT_TYPE = "message"


def _process_message_event(webhook_event: LINEMessagingWebhookEvent) -> None:
    try:
        assign_received_message(webhook_event)
    except Exception:
        logger.exception(
            "Failed to process LINE message event, but returning webhook response"
        )


@tracer.capture_method
def event_type_switcher(webhook_event: LINEMessagingWebhookEvent):
    """
    受信したLINEのWebhookイベントのタイプを判別し、適切な処理を呼び出す。

    Args:
        webhook_event (LINEMessagingWebhookEvent): _description_
    """
    try:
        event = webhook_event.events[0]
        event_type = event.get("type")
        message_type = event.get("message", {}).get("type")

        if event_type == MESSAGE_EVENT_TYPE and message_type in SUPPORTED_MESSAGE_TYPES:
            logger.info("Processing LINEMessageEvent")
            _process_message_event(webhook_event)
            return

        if event_type == MESSAGE_EVENT_TYPE:
            logger.warning("Message type '%s' is not handled", message_type)
            return

        logger.info("Unsupported event type: %s", event_type)
    except Exception:
        logger.exception(
            "Unexpected error in event_type_switcher, but returning webhook response"
        )
