import logging

from app.application.line.send_message import send_message
from app.domain.model.line.line_message_processor import MessageStatus

logger = logging.getLogger(__name__)


def reply_message(
    line_message_processor_status: MessageStatus, reply_token: str
) -> None:
    # 返信可能な状態か確認
    if line_message_processor_status != MessageStatus.AwaitingChatResponse.value:
        logger.warning(
            "Message is not ready for reply. Current status: %s",
            line_message_processor_status,
        )
        return

    logger.info("Replying message with reply_token=%s", reply_token)

    response = send_message(
        reply_token,
        "これは返信メッセージです。",
    )

    if response.status_code == 200:
        logger.info("Message replied successfully")
    else:
        logger.error(
            "Failed to reply message. Status code: %s, Response: %s",
            response.status_code,
            response.text,
        )
