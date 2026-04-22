import json

from aws_lambda_powertools import Logger, Tracer

from app import config
from app.adapters import aws_clients, dynamodb_query_service
from app.application.ai_chat.ai_chat_request import execute

logger = Logger()
tracer = Tracer()

dynamodb_client = aws_clients.get_dynamodb_client()

line_query_service = dynamodb_query_service.DynamoDBLINEMessageProcessorsQueryService(
    config.AppConfig.get_table_name_line(), dynamodb_client
)


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    records = event.get("Records", [])

    for record in records:
        try:
            process_record(record)
        except Exception:
            logger.exception("Failed to process record, dropping message")
            # 例外を再送出しない
            continue


@tracer.capture_method
def process_record(record: dict) -> None:
    body = json.loads(record["body"])
    processor_id = body["line_message_processor_id"]
    ai_user_profile_id = body["ai_user_profile_id"]
    logger.info(
        "Processing ai-chat SQS message. processor_id=%s ai_user_profile_id=%s",
        processor_id,
        ai_user_profile_id,
    )

    line_message_processor = line_query_service.get_line_message_processor_by_id(
        processor_id
    )
    if not line_message_processor:
        logger.warning(
            "LINE message processor not found. processor_id=%s",
            processor_id,
        )
        return

    execute(line_message_processor, ai_user_profile_id)
