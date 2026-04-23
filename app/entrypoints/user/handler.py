import base64
import json
from typing import Optional

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import api_gateway
from aws_lambda_powertools.event_handler.api_gateway import Response

from app import config
from app.adapters import aws_clients, dynamodb_query_service, dynamodb_unit_of_work
from app.adapters.dynamodb_query_service import DynamoDBAIUserProfilesQueryService
from app.application.user.creat_ai_profile_usecase import CreateAIProfileUseCase
from app.application.user.exist_line_user_usecase import ExistLineUserUseCase
from app.domain.model.ai_chat.ai_user_profile import AIUserProfile
from app.domain.model.user.ai_profile_request import (
    AIUserProfileRequestCreate,
)
from app.domain.model.user.exist_user_result import ExistUserResult
from app.entrypoints.shared.request_utils import get_body

app = api_gateway.ApiGatewayResolver()
logger = Logger()
tracer = Tracer()

dynamodb_client = aws_clients.get_dynamodb_client()

unit_of_work = dynamodb_unit_of_work.DynamoDBUnitOfWork(
    config.AppConfig.get_table_name_line(),
    config.AppConfig.get_table_name_line_user(),
    config.AppConfig.get_table_name_ai_user_profile(),
    dynamodb_client,
)


def exist_line_user(req_body: str) -> Optional[ExistUserResult]:
    dynamodb_client = aws_clients.get_dynamodb_client()
    line_users_query_service = dynamodb_query_service.DynamoDBLINEUsersQueryService(
        config.AppConfig.get_table_name_line_user(), dynamodb_client
    )
    ai_user_profiles_query_service = DynamoDBAIUserProfilesQueryService(
        config.AppConfig.get_table_name_ai_user_profile(),
        dynamodb_client,
    )

    usecase = ExistLineUserUseCase(
        line_users_query_service, ai_user_profiles_query_service
    )
    return usecase.execute(req_body)


def create_ai_user_profile(req: AIUserProfileRequestCreate) -> AIUserProfile:
    dynamodb_client = aws_clients.get_dynamodb_client()
    ai_user_profiles_query_service = DynamoDBAIUserProfilesQueryService(
        config.AppConfig.get_table_name_ai_user_profile(),
        dynamodb_client,
    )

    usecase = CreateAIProfileUseCase(
        ai_user_profiles_query_service,
        unit_of_work,
    )
    return usecase.execute(req)


@app.post("/user/exist-line-user")
def exist_user():
    """
    受信したアクセストークンから、LINEUserに同一ユーザーのLINEUserIdがあるか検証する
    """
    try:
        event = app.current_event

        body = _normalize_request_body(event)

        result = exist_line_user(body)
        logger.info(f"result:{result}")

        if result is None:
            return Response(
                status_code=500,
                content_type="application/json",
                body=json.dumps({"error": "Internal server error"}),
            )

        return Response(
            status_code=200,
            content_type="application/json",
            body=json.dumps(result.model_dump(), ensure_ascii=False),
        )

    except Exception as e:
        logger.exception(e, "Error occurred while processing Exist LINE User")

        return Response(
            status_code=500,
            content_type="application/json",
            body=json.dumps({"error": "Internal server error"}),
        )


@app.post("/user/create-ai-profile")
def create_ai_profile():
    """
    新規AIProfileを登録する
    """
    try:
        event = app.current_event

        req_body = _normalize_request_body(event)

        result = get_body(req_body, AIUserProfileRequestCreate)

        if result.is_valid:
            created = create_ai_user_profile(result.value)

            return Response(
                status_code=201,
                content_type="application/json",
                body=json.dumps({"id": created.id}, ensure_ascii=False),
            )

        else:
            logger.error("Request validation error.")
            return Response(
                status_code=400,
                content_type="application/json",
                body=json.dumps({"error": "Internal server error"}),
            )

    except Exception as e:
        logger.exception(e, "Error occurred while processing Create AI User Profile")

        return Response(
            status_code=500,
            content_type="application/json",
            body=json.dumps({"error": "Internal server error"}),
        )


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
