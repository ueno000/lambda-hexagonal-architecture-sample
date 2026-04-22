from aws_lambda_powertools import Logger

from app import config
from app.adapters import aws_clients, dynamodb_unit_of_work
from app.application.line.send_message import send_message
from app.domain.model.line.line_message_processor import (
    LINEMessageProcessor,
    MessageStatus,
)

logger = Logger()

REPLY_TEXT = "これは返信メッセージです。"

dynamodb_client = aws_clients.get_dynamodb_client()

unit_of_work = dynamodb_unit_of_work.DynamoDBUnitOfWork(
    config.AppConfig.get_table_name_line(),
    config.AppConfig.get_table_name_line_user(),
    dynamodb_client,
)


def reply_message(line_message_processor: LINEMessageProcessor) -> None:
    # 返信可能な状態か確認
    if line_message_processor.processing_status != MessageStatus.ReplyReady.value:
        logger.warning(
            "Message is not ready for reply. Current status: %s",
            line_message_processor.processing_status,
        )
        return

    reply_token = get_reply_token(line_message_processor)
    logger.info("Replying message with reply_token=%s", reply_token)

    reply_message_text = REPLY_TEXT
    if line_message_processor.reply_message is not None:
        reply_message_text = "【本日の案内】\r\n" + line_message_processor.reply_message

    response = send_message(reply_token, reply_message_text)

    if response.status_code == 200:
        update_reply_result(line_message_processor, reply_message_text)
        logger.info("Message replied successfully")
    else:
        logger.error(
            "Failed to reply message. Status code: %s, Response: %s",
            response.status_code,
            response.text,
        )


def update_reply_result(
    line_message_processor: LINEMessageProcessor, reply_text: str
) -> None:
    """_summary_
    LINEUserの状態とLINEMessageProcessorの返信内容を更新する。

        Args:
            line_message_processor (LINEMessageProcessor): _description_
            reply_text (str): _description_
    """
    line_user = line_message_processor.line_user
    if not line_user:
        logger.warning(
            "LINE user is not attached to processor. processor_id=%s",
            line_message_processor.id,
        )
        return
    # LINEユーザーのtalk_countをインクリメント
    line_user.talk_count = (line_user.talk_count or 0) + 1

    # DynamoDBに更新を保存
    with unit_of_work:
        unit_of_work.line_users.put(line_user)
        unit_of_work.commit()

    # LINEMessageProcessorの返信内容と状態を更新
    line_message_processor.reply_message = reply_text
    line_message_processor.line_user = line_user
    line_message_processor.processing_status = MessageStatus.Completed

    # DynamoDBに更新を保存
    with unit_of_work:
        unit_of_work.line_message_processors.put(line_message_processor)
        unit_of_work.commit()


def get_reply_token(line_message_processor: LINEMessageProcessor) -> str:
    message_event = line_message_processor.message_event
    if isinstance(message_event, dict):
        return message_event["replyToken"]
    return message_event.replyToken
