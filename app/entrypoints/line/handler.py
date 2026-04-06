from datetime import datetime, timezone

import boto3
import json

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import api_gateway

from app.adapters import dynamodb_query_service, dynamodb_unit_of_work
from app.application.line.assign_received_message import assign_received_message
from app.domain.command_handlers import (
    create_line_message_processor_command_handler,
)
from app.domain.commands import (
    create_line_message_processor_command,
)

from app import config
from app.domain.model.line.line_messaging_webhook_event import LINEMessagingWebhookEvent
from app.entrypoints.line.signature import validate_signature

app_config = config.AppConfig(**config.config)

app = api_gateway.ApiGatewayResolver()
logger = Logger()
tracer = Tracer()

# # ========== DynamoDB クライアント初期化 ==========
# # DynamoDBクライアントを指定リージョンで作成
# dynamodb_client = boto3.resource(
#     "dynamodb",
#     region_name=config.AppConfig.get_default_region(),
#     endpoint_url="http://host.docker.internal:8000",
# )
# # Unit of Work パターン：複数の変更をトランザクションで管理
# unit_of_work = dynamodb_unit_of_work.DynamoDBUnitOfWork(
#     config.AppConfig.get_table_name_line(), dynamodb_client.meta.client
# )


@app.post("/line/receive-message")
def receive_message():
    """
    Handle LINE webhook message reception.
    Validates signature, processes the webhook event, and assigns the received message.
    """
    try:
        event = app.current_event

        headers = event.headers or {}
        body = event.body or ""

        # Validate LINE signature
        error, request_body = validate_signature(
            headers=headers,
            body=body,
            channel_secret=config.AppConfig.get_line_channel_secret(),
        )

        if error:
            logger.warning("Signature validation failed")
            return {"error": "Invalid signature"}, 400

        payload = json.loads(request_body)
        webhook_event = LINEMessagingWebhookEvent(**payload)

        # Process the message using command handler
        # processor_id = create_line_message_processor_command_handler.handle_create_line_messaging_processor_command(
        #     command=create_line_message_processor_command.CreateLINEMessagingProcessorCommand(
        #         event=webhook_event
        #     ),
        #     unit_of_work=unit_of_work,
        # )

        # Assign the received message
        assign_received_message(webhook_event)


        return {}

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {str(e)}")
        return {"error": "Invalid JSON"}, 400
    except Exception as e:
        logger.exception("Error occurred while processing LINE message")
        return {"error": "Internal server error"}, 500


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    """
    AWS Lambda handler for LINE webhook events.
    """
    return app.resolve(event, context)
