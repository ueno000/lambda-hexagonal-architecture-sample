import logging

from app.application.line.send_message import send_message
from app.domain.model.line.line_message_processor import (
    LINEMessageProcessor,
    MessageStatus,

)

logger = logging.getLogger(__name__)


def reply_message(line_message_processor_status:MessageStatus, reply_token:str) -> None:

    if line_message_processor_status != 1:
        logger.warning(
            "Message is not ready for reply. Current status: %s",
            line_message_processor_status,
        )
        return

    logger.info("Replying message with reply_token=%s", reply_token)

    response = send_message(
        reply_token,
        "answer from lambda",
    )

    if response.status_code == 200:
        logger.info("Message replied successfully")
    else:
        logger.error(
            "Failed to reply message. Status code: %s, Response: %s",
            response.status_code,
            response.text,
        )
