import base64
import json

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import api_gateway

from app.application.line.event_type_switcher import event_type_switcher

from app import config
from app.domain.model.line.line_messaging_webhook_event import LINEMessagingWebhookEvent
from app.entrypoints.line.signature import validate_signature

app_config = config.AppConfig(**config.config)

app = api_gateway.ApiGatewayResolver()
logger = Logger()
tracer = Tracer()


@app.post("/line/receive-message")
def receive_message():
    """
    LINE Webhookメッセージ受信処理
    """
    try:
        event = app.current_event

        headers = event.headers or {}

        logger.info("before _normalize_request_body")

        body = _normalize_request_body(event)

        logger.info("after _normalize_request_body")

        channel_secret = app_config.get_line_channel_secret()

        if not channel_secret:
            logger.error("LINE channel secret is not configured")
            return {"error": "Server configuration error"}, 500

        logger.info("before validate_signature")

        # Validate LINE signature
        error, request_body = validate_signature(
            headers=headers,
            body=body,
            channel_secret=channel_secret,
        )

        logger.info("after validate_signature")
        logger.info("===========request_body=%s", request_body)

        if error:
            logger.warning("Signature validation failed")
            return {"error": "Invalid signature"}, 400

        payload = json.loads(request_body)
        logger.info("json.loads success")

        webhook_event = LINEMessagingWebhookEvent(**payload)
        logger.info("pydantic success")

        # Process the message using command handler
        # processor_id = create_line_message_processor_command_handler.handle_create_line_messaging_processor_command(
        #     command=create_line_message_processor_command.CreateLINEMessagingProcessorCommand(
        #         event=webhook_event
        #     ),
        #     unit_of_work=unit_of_work,
        # )

        # Assign the received message
        event_type_switcher(webhook_event)

        return {}

    except json.JSONDecodeError as e:
        failed_body = locals().get("request_body", "")

        logger.error("JSON decode failed at pos=%s", e.pos)
        logger.error("request_body repr=%r", failed_body)
        logger.error("around error=%r", failed_body[max(e.pos - 40, 0) : e.pos + 40])

        return {"error": "Invalid JSON"}, 400

    except Exception as e:
        logger.exception("Error occurred while processing LINE message")
        return {"error": "Internal server error"}, 500


def _normalize_request_body(event) -> str:
    body = event.body or ""

    if isinstance(body, bytes):
        body = body.decode("utf-8")
    elif not isinstance(body, str):
        body = json.dumps(body, ensure_ascii=False)

    logger.info("=========Normalized request body: %s", body)

    raw_event = getattr(event, "raw_event", {}) or {}
    is_base64_encoded = getattr(event, "is_base64_encoded", None)
    if is_base64_encoded is None:
        is_base64_encoded = raw_event.get("isBase64Encoded", False)

    if is_base64_encoded:
        body = base64.b64decode(body).decode("utf-8")

    logger.info("===========Decoded request body: %s", body)

    return body


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    return app.resolve(event, context)
