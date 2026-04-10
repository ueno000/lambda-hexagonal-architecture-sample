import base64
import json
import re

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
CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _is_base64_encoded(event) -> bool:
    if getattr(event, "is_base64_encoded", False):
        return True
    if getattr(event, "isBase64Encoded", False):
        return True

    raw_event = getattr(event, "raw_event", None)
    if isinstance(raw_event, dict):
        return bool(raw_event.get("isBase64Encoded"))

    return False


def _get_request_body(event) -> str | bytes:
    raw_event = getattr(event, "raw_event", None)
    if isinstance(raw_event, dict) and raw_event.get("body") is not None:
        return raw_event["body"]

    return event.body or ""


def _parse_request_payload(request_body: str, is_base64_encoded: bool = False) -> dict:
    normalized_body = request_body.decode("utf-8") if isinstance(request_body, bytes) else request_body
    parse_errors = []

    bodies_to_try = [normalized_body]
    if is_base64_encoded:
        bodies_to_try.insert(
            0,
            base64.b64decode(normalized_body).decode("utf-8"),
        )

    for body in bodies_to_try:
        try:
            payload = json.loads(body)
            if isinstance(payload, str):
                payload = json.loads(payload)
            return payload
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            parse_errors.append(exc)

        sanitized_body = CONTROL_CHAR_PATTERN.sub("", body)
        if sanitized_body == body:
            continue

        try:
            payload = json.loads(sanitized_body)
            if isinstance(payload, str):
                payload = json.loads(payload)
            logger.warning("LINE webhook body contained raw control characters and was sanitized before parsing")
            return payload
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            parse_errors.append(exc)

    raise parse_errors[-1]


def _excerpt_around_error(value: str | bytes | None, position: int, radius: int = 80) -> str:
    if value is None:
        return ""

    text = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)
    start = max(position - radius, 0)
    end = min(position + radius, len(text))
    return repr(text[start:end])


@app.post("/line/receive-message")
def receive_message():
    """
    LINE Webhookメッセージ受信処理
    """
    request_body = None
    body = ""

    try:
        event = app.current_event

        headers = event.headers or {}
        body = _get_request_body(event)

        logger.info(
            "===========Received LINE webhook event. headers=%s body=%s", headers, body
        )

        # Validate LINE signature
        error, request_body = validate_signature(
            headers=headers,
            body=body,
            channel_secret=config.AppConfig.get_line_channel_secret(),
        )

        logger.info(
            "===========request_body metadata type=%s is_base64_encoded=%s length=%s",
            type(request_body).__name__,
            _is_base64_encoded(event),
            len(request_body) if request_body is not None else 0,
        )

        if error:
            logger.warning("Signature validation failed")
            return {"error": "Invalid signature"}, 400

        payload = _parse_request_payload(
            request_body,
            is_base64_encoded=_is_base64_encoded(event),
        )
        webhook_event = LINEMessagingWebhookEvent(**payload)

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
        preview_source = request_body if request_body is not None else body
        logger.error(
            "Failed to parse LINE webhook JSON. error_pos=%s body_preview=%s",
            e.pos,
            (
                preview_source[:400]
                if isinstance(preview_source, str)
                else str(preview_source)[:400]
            ),
        )
        logger.error(
            "Failed to parse LINE webhook JSON near error. excerpt=%s",
            _excerpt_around_error(preview_source, e.pos),
        )
        logger.error(f"Invalid JSON payload: {str(e)}")
        return {"error": "Invalid JSON"}, 400
    except Exception as e:
        logger.exception("Error occurred while processing LINE message")
        return {"error": "Internal server error"}, 500


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    return app.resolve(event, context)
