from datetime import datetime, timezone
import uuid

import boto3

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import api_gateway

from app import config
from app.domain.model.line.line_messaging_webhook_event import LINEMessagingWebhookEvent
from app.domain.model.line.line_user import LINEUser
from app.domain.model.line.line_message_processor import (
    LINEMessageProcessor,
    MessageStatus,
)
from app.entrypoints.line.signature import validate_signature
from app.adapters import dynamodb_unit_of_work, dynamodb_query_service
from app.application.line.send_message import send_message

app_config = config.AppConfig(**config.config)

app = api_gateway.ApiGatewayResolver()
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
        print("DEBUG line_user =", line_user)
        if not line_user:
            logger.info(f"User {user_id} not found, creating new user")
            line_user = create_line_user(user_id)

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

        send_message(
            reply_token=first_event["replyToken"],
            message="メッセージを受け取りました！返信をお待ちください。",
        )

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise


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


def create_line_user(line_id: str) -> LINEUser:
    """
    LINE ユーザーが存在しない場合に新規作成する。

    Args:
        line_id: LINE のユーザー ID

    Returns:
        作成された LINE ユーザー
    """
    new_user = LINEUser(
        id=str(uuid.uuid4()),
        line_id=line_id,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    with unit_of_work:
        unit_of_work.line_users.add(new_user)
        unit_of_work.commit()
    logger.info(f"Created new LINE user with ID: {new_user.id}")
    return new_user
