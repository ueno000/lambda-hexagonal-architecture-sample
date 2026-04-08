from aws_lambda_powertools import Logger, Tracer
from app.application.line.assign_received_message import assign_received_message
from app.domain.model.line.line_messaging_webhook_event import (
    LINEMessagingWebhookEvent,
    LINEMessageEvent,
)

logger = Logger()
tracer = Tracer()

SUPPORTED_MESSAGE_TYPES = {"text", "sticker"}


@tracer.capture_method
def event_type_switcher(webhook_event: LINEMessagingWebhookEvent):
    """_summary_

    受信したLINEのWebhookイベントのタイプを判別し、対応する処理を呼び出す

    Args:
        webhook_event (LINEMessagingWebhookEvent): _description_
    """

    event = webhook_event.events[0]
    event_type = event.get("type")

    if event_type == "message":
        message_type = event.get("message", {}).get("type")

        if message_type in SUPPORTED_MESSAGE_TYPES:
            logger.info("Processing LINEMessageEvent")
            # 受信したメッセージを処理するための関数を呼び出す
            assign_received_message(webhook_event)

        else:
            logger.warning("Message type '%s' is not handled", message_type)
            print(f"DEBUG Unsupported message type: {message_type}")

    elif event_type == "follow":
        logger.info("Unsupported event type: %s", event_type)

    elif event_type == "unfollow":
        logger.info("Unsupported event type: %s", event_type)

    else:
        logger.info("Unsupported event type: %s", event_type)
