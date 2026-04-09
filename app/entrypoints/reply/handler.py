import json

import boto3
from aws_lambda_powertools import Logger, Tracer

from app import config
from app.adapters import dynamodb_query_service
from app.application.line.reply_message import reply_message

logger = Logger()
tracer = Tracer()

dynamodb_client = boto3.resource(
    "dynamodb",
    region_name=config.AppConfig.get_default_region(),
    endpoint_url=config.AppConfig.get_dynamodb_endpoint_url(),
)

line_query_service = dynamodb_query_service.DynamoDBLINEMessageProcessorsQueryService(
    config.AppConfig.get_table_name_line(), dynamodb_client.meta.client
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

    reply_token = line_message_processor.message_event["replyToken"]
    reply_message(line_message_processor.processing_status, reply_token)
