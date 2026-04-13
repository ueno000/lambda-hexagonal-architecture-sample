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

        body = _normalize_request_body(event)

        try:
            channel_secret = app_config.get_line_channel_secret()
        except Exception:
            logger.exception("get_line_channel_secret failed")
            raise

        # Validate LINE signature
        error, request_body = validate_signature(
            headers=headers,
            body=body,
            channel_secret=channel_secret,
        )

        if error:
            logger.warning("Signature validation failed")
            return {"error": "Invalid signature"}, 400

        payload = json.loads(request_body)
        logger.info("json.loads success")

        webhook_event = LINEMessagingWebhookEvent(**payload)
        logger.info("pydantic success")

        # Assign the received message
        event_type_switcher(webhook_event)

        return {}

    except json.JSONDecodeError as e:
        failed_body = locals().get("request_body", "")
        logger.error("request_body repr=%r", failed_body)

        return {"error": "Invalid JSON"}, 400

    except Exception as e:
        logger.exception("Error occurred while processing LINE message")
        return {"error": "Internal server error"}, 500


def _normalize_request_body(event) -> str:
    """API Gateway からのリクエストボディを正規化する"""
    body = event.body or ""

    if isinstance(body, bytes):
        body = body.decode("utf-8")
    elif not isinstance(body, str):
        body = json.dumps(body, ensure_ascii=False)

    raw_event = getattr(event, "raw_event", {}) or {}
    is_base64_encoded = getattr(event, "is_base64_encoded", None)
    if is_base64_encoded is None:
        is_base64_encoded = raw_event.get("isBase64Encoded", False)

    if is_base64_encoded:
        body = base64.b64decode(body).decode("utf-8")

    return body


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    return app.resolve(event, context)
