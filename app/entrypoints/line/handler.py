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


def _is_base64_encoded(event) -> bool:
    if getattr(event, "is_base64_encoded", False):
        return True
    if getattr(event, "isBase64Encoded", False):
        return True

    raw_event = getattr(event, "raw_event", None)
    if isinstance(raw_event, dict):
        return bool(raw_event.get("isBase64Encoded"))

    return False


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

    raise parse_errors[-1]


@app.post("/line/receive-message")
def receive_message():
    """
    LINE Webhookメッセージ受信処理
    """
    try:
        event = app.current_event

        headers = event.headers or {}
        body = event.body or ""

        logger.info(
            "===========Received LINE webhook event. headers=%s body=%s", headers, body
        )

        # Validate LINE signature
        error, request_body = validate_signature(
            headers=headers,
            body=body,
            channel_secret=config.AppConfig.get_line_channel_secret(),
        )

        logger.info("===========request_body=%s", request_body)

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
        logger.error(f"Invalid JSON payload: {str(e)}")
        return {"error": "Invalid JSON"}, 400
    except Exception as e:
        logger.exception("Error occurred while processing LINE message")
        return {"error": "Internal server error"}, 500


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    return app.resolve(event, context)
