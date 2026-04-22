import json

from aws_lambda_powertools import Logger, Tracer

from app import config
from app.adapters import aws_clients, dynamodb_query_service
from app.application.line.reply_message import reply_message

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
    if not records:
        logger.warning("No SQS records found")
        return

    for record in records:
        process_record(record)


@tracer.capture_method
def process_record(record: dict) -> None:
    body = json.loads(record["body"])
    processor_id = body["line_message_processor_id"]

    line_message_processor = line_query_service.get_line_message_processor_by_id(
        processor_id
    )
    if not line_message_processor:
        logger.warning(
            "LINE message processor not found. processor_id=%s",
            processor_id,
        )
        return

    reply_message(line_message_processor)
