import json
import uuid
from datetime import datetime, timezone

import boto3

from aws_lambda_powertools import Logger, Tracer

from app import config
from app.domain.model.line.line_messaging_webhook_event import LINEMessagingWebhookEvent
from app.domain.model.line.line_user import LINEUser
from app.domain.model.line.line_message_processor import (
    LINEMessageProcessor,
    MessageStatus,
)
from app.adapters import dynamodb_unit_of_work, dynamodb_query_service
from app.application.line.create_line_user import create_line_user
from app.application.line.send_message import send_message

app_config = config.AppConfig(**config.config)
logger = Logger()
tracer = Tracer()

# ========== DynamoDB クライアント初期化 ==========
# DynamoDBクライアントを指定リージョンで作成
endpoint = config.AppConfig.get_dynamodb_endpoint_url()

dynamodb_client = boto3.resource(
    "dynamodb",
    region_name=config.AppConfig.get_default_region(),
    endpoint_url=endpoint,
)

# Unit of Work パターン：複数の変更をトランザクションで管理
unit_of_work = dynamodb_unit_of_work.DynamoDBUnitOfWork(
    config.AppConfig.get_table_name_line(),
    config.AppConfig.get_table_name_line_user(),
    dynamodb_client.meta.client,
)
# CQRS パターン：読み取り専用のクエリサービス
line_query_service = dynamodb_query_service.DynamoDBLINEMessageProcessorsQueryService(
    config.AppConfig.get_table_name_line(), dynamodb_client.meta.client
)

line_users_query_service = dynamodb_query_service.DynamoDBLINEUsersQueryService(
    config.AppConfig.get_table_name_line_user(), dynamodb_client.meta.client
)
ai_user_profiles_query_service = (
    dynamodb_query_service.DynamoDBAIUserProfilesQueryService(
        config.AppConfig.get_table_name_ai_user_profile(),
        dynamodb_client.meta.client,
    )
)

sqs_client = boto3.client(
    "sqs",
    region_name=config.AppConfig.get_default_region(),
)


@tracer.capture_method
def assign_received_message(
    messaging_webhook_event: LINEMessagingWebhookEvent,
) -> str | None:
    """
    LINE の Webhook イベントから受信メッセージを割り当てる。
    受信したメッセージを処理し、ユーザーを取得または作成し、メッセージを保存する。

    Args:
        messaging_webhook_event: LINE のメッセージング Webhook イベント

    Returns:
        作成されたメッセージプロセッサの ID（イベントがない場合は None）
    """
    try:
        logger.info("Processing LINE messaging webhook event")

        if not messaging_webhook_event.events:
            logger.warning("No events in webhook")
            return None

        first_event = messaging_webhook_event.events[0]
        user_id = first_event["source"]["userId"]
        logger.info(f"Processing message for user: {user_id}")

        # Find or create LINE user
        line_user = line_users_query_service.get_line_user_by_line_id(user_id)
        if not line_user:
            logger.info(f"User {user_id} not found, creating new user")
            line_user = create_line_user(user_id)
            send_message(
                reply_token=first_event["replyToken"],
                message="はじめまして。メッセージありがとうございます。",
            )
            logger.info("Sent first message greeting to user: %s", user_id)
            return None

        # Save the LINE message processor
        line_message_processor = insert_line_message_processor(messaging_webhook_event)
        logger.info("Message processed successfully")

        # ここで、update_line_message_processorをする。lineuserを付与する
        line_message_processor.processing_status = MessageStatus.AwaitingChatResponse
        line_message_processor.line_user = LINEUser.parse_obj(line_user.dict())
        line_message_processor.last_update_date = datetime.now(timezone.utc).isoformat()

        with unit_of_work:
            unit_of_work.line_message_processors.put(line_message_processor)
            unit_of_work.commit()

        # LINEMessageProcessorのIdをSQSキューに送信
        if is_today_guide_command(messaging_webhook_event):
            ai_user_profile = (
                ai_user_profiles_query_service.get_ai_user_profile_by_line_user_id(
                    line_user.id
                )
            )
            if not ai_user_profile:
                send_message(
                    reply_token=first_event["replyToken"],
                    message="設定からプロフィール設定をしてください",
                )
                logger.info(
                    "AI user profile not found. Sent profile setup guidance. line_user_id=%s",
                    line_user.id,
                )
                return line_message_processor.id

            enqueue_ai_chat_request(
                line_message_processor.id,
                ai_user_profile["id"],
            )
            logger.info(
                "Enqueued ai-chat request for LINE message processor ID: %s",
                line_message_processor.id,
            )
        else:
            # リプライする前にLINEMessageProcessorの状態をReplyReadyに更新しておく
            line_message_processor.processing_status = MessageStatus.ReplyReady
            with unit_of_work:
                unit_of_work.line_message_processors.put(line_message_processor)
                unit_of_work.commit()
            enqueue_reply_request(line_message_processor.id)

            logger.info(
                "Enqueued reply request for LINE message processor ID: %s",
                line_message_processor.id,
            )

        return line_message_processor.id

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise


def is_today_guide_command(
    messaging_webhook_event: LINEMessagingWebhookEvent,
) -> bool:
    first_event = messaging_webhook_event.events[0]
    message = first_event.get("message", {})
    return message.get("type") == "text" and message.get("text") == "/本日の案内"


@tracer.capture_method
def insert_line_message_processor(
    messaging_webhook_event: LINEMessagingWebhookEvent,
) -> str:
    """
    LINEMessageProcessor のインスタンスを作成して登録する。

    Args:
        messaging_webhook_event: LINE のメッセージング Webhook イベント
        line_user: 対応する LINE ユーザー

    Returns:
        作成されたメッセージプロセッサの ID

    Raises:
        Exception: 登録に失敗した場合
    """
    try:
        processor_id = str(uuid.uuid4())
        line_message_processor = LINEMessageProcessor(
            id=processor_id, message_event=messaging_webhook_event.events[0]
        )

        # Insert using unit of work
        with unit_of_work:
            unit_of_work.line_message_processors.add(line_message_processor)
            unit_of_work.commit()

        logger.info(f"Inserted LINE message processor with ID: {processor_id}")
        return line_message_processor

    except Exception as e:
        logger.error(f"Error inserting LINE message processor: {str(e)}")
        unit_of_work.rollback()
        raise


def enqueue_ai_chat_request(
    line_message_processor_id: str, ai_user_profile_id: str
) -> None:
    """LINEMessageProcessor の ID を ai-chat SQS キューに送信する。

    Args:
        line_message_processor_id (str): LINEMessageProcessor の ID
        ai_user_profile_id (str): AIUserProfile の ID

    Raises:
        RuntimeError: AI_CHAT_QUEUE_URL が未設定の場合
    """

    queue_url = config.AppConfig.get_ai_chat_queue_url()
    if not queue_url:
        raise RuntimeError("AI_CHAT_QUEUE_URL is not set")

    try:
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(
                {
                    "line_message_processor_id": line_message_processor_id,
                    "ai_user_profile_id": ai_user_profile_id,
                },
                ensure_ascii=False,
            ),
        )
        logger.info(
            f"Reply request enqueued successfully for processor_id: {line_message_processor_id}"
        )
    except Exception as e:
        logger.error(
            f"Error enqueuing reply request for processor_id: {line_message_processor_id}, error: {type(e).__name__}: {str(e)}"
        )
        raise RuntimeError(
            f"Failed to enqueue reply request for processor_id: {line_message_processor_id}"
        ) from e


def enqueue_reply_request(line_message_processor_id: str) -> None:
    """LINEMessageProcessor の ID を reply SQS キューに送信する。

    Args:
        line_message_processor_id (str): LINEMessageProcessor の ID

    Raises:
        RuntimeError: REPLY_QUEUE_URL が未設定の場合
    """
    queue_url = config.AppConfig.get_reply_queue_url()
    if not queue_url:
        raise RuntimeError("REPLY_QUEUE_URL is not set")

    try:
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(
                {"line_message_processor_id": line_message_processor_id},
                ensure_ascii=False,
            ),
        )
        logger.info(
            f"Reply request enqueued successfully for processor_id: {line_message_processor_id}"
        )
    except Exception as e:
        logger.error(
            f"Error enqueuing reply request for processor_id: {line_message_processor_id}, error: {type(e).__name__}: {str(e)}"
        )
        raise RuntimeError(
            f"Failed to enqueue reply request for processor_id: {line_message_processor_id}"
        ) from e
