import base64
import json
from dataclasses import asdict
from typing import Optional

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import api_gateway

from app import config
from app.adapters import aws_clients
from app.adapters.dynamodb_query_service import DynamoDBAIUserProfilesQueryService
from app.application.user.exist_line_user_usecase import ExistLineUserUseCase
from app.domain.model.user.exist_user_result import ExistUserResult

app = api_gateway.ApiGatewayResolver()
logger = Logger()
tracer = Tracer()


def exist_line_user(req_body: str) -> Optional[ExistUserResult]:
    dynamodb_client = aws_clients.get_dynamodb_client()
    ai_user_profiles_query_service = DynamoDBAIUserProfilesQueryService(
        config.AppConfig.get_table_name_ai_user_profile(),
        dynamodb_client,
    )

    usecase = ExistLineUserUseCase(ai_user_profiles_query_service)
    return usecase.execute(req_body)


@app.post("/user/exist-line-user")
def exist_user():
    """
    受信したアクセストークンから、LINEUserに同一ユーザーのLINEUserIdがあるか検証する
    """
    try:
        event = app.current_event

        body = _normalize_request_body(event)

        result = exist_line_user(body)

        if result is None:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Internal server error"}),
            }

        return {"statusCode": 200, "body": json.dumps(asdict(result))}

    except Exception as e:
        logger.exception(e, "Error occurred while processing Exist LINE User")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
        }


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
