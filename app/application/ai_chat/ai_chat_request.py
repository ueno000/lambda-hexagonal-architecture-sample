from datetime import datetime, timezone
import json
from typing import Any, Dict

import boto3
import requests

from app import config
from app.adapters import dynamodb_query_service, dynamodb_unit_of_work
from app.application.ai_chat.prompt_builder import build_daily_guide_prompt
from app.domain.model.ai_chat.chat_session import ChatSession
from app.domain.model.line.line_message_processor import MessageStatus
from app.domain.model.ai_chat.ai_user_profile import AIUserProfile


dynamodb_client = boto3.resource(
    "dynamodb",
    region_name=config.AppConfig.get_default_region(),
    endpoint_url=config.AppConfig.get_dynamodb_endpoint_url(),
)

line_query_service = dynamodb_query_service.DynamoDBLINEMessageProcessorsQueryService(
    config.AppConfig.get_table_name_line(), dynamodb_client.meta.client
)

ai_user_profiles_query_service = (
    dynamodb_query_service.DynamoDBAIUserProfilesQueryService(
        config.AppConfig.get_table_name_ai_user_profile(),
        dynamodb_client.meta.client,
    )
)

unit_of_work = dynamodb_unit_of_work.DynamoDBUnitOfWork(
    config.AppConfig.get_table_name_line(),
    config.AppConfig.get_table_name_line_user(),
    dynamodb_client.meta.client,
)

sqs_client = boto3.client(
    "sqs",
    region_name=config.AppConfig.get_default_region(),
)


def execute(line_message_processor, ai_user_profile_id: str) -> None:
    ai_user_profile = ai_user_profiles_query_service.get_ai_user_profile_by_id(
        ai_user_profile_id
    )
    if not ai_user_profile:
        raise ValueError(f"AI user profile not found: {ai_user_profile_id}")

    prompt = init_chat_request(ai_user_profile)
    chat_response = request_chat(prompt)
    updated_line_message_processor = response_chat(
        line_message_processor,
        ai_user_profile_id,
        chat_response,
    )
    enqueue_reply_request(updated_line_message_processor.id)


def init_chat_request(ai_user_profile: Dict[str, Any]) -> str:
    return build_daily_guide_prompt(_parse_ai_user_profile(ai_user_profile))


def request_chat(prompt: str) -> str:
    gemini_api_key = config.AppConfig.get_gemini_api_key()
    if not gemini_api_key:
        raise RuntimeError("gemini_api_key is not set")

    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent",
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": gemini_api_key,
        },
        json={
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt,
                        }
                    ]
                }
            ]
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return _extract_chat_text(payload)


def response_chat(line_message_processor, ai_user_profile_id: str, chat_response: str):
    chat_session = init_chat_session(ai_user_profile_id, chat_response)
    line_message_processor.reply_message = chat_session.reply_message
    line_message_processor.processing_status = MessageStatus.ReplyReady
    line_message_processor.last_update_date = datetime.now(timezone.utc).isoformat()

    with unit_of_work:
        unit_of_work.line_message_processors.put(line_message_processor)
        unit_of_work.commit()

    return line_message_processor


def init_chat_session(ai_user_profile_id: str, chat_response: str):
    return ChatSession(
        id=f"chat-session-{ai_user_profile_id}",
        ai_user_profile_id=ai_user_profile_id,
        reply_message=chat_response,
    )


def _parse_ai_user_profile(ai_user_profile: Dict[str, Any]) -> AIUserProfile:
    model_validate = getattr(AIUserProfile, "model_validate", None)
    if callable(model_validate):
        return model_validate(ai_user_profile)

    return AIUserProfile(**ai_user_profile)


def _extract_chat_text(payload: Dict[str, Any]) -> str:
    candidates = payload.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini response does not contain candidates")

    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise RuntimeError("Gemini response does not contain text")

    text = parts[0].get("text")
    if not text:
        raise RuntimeError("Gemini response does not contain text")

    return text


def enqueue_reply_request(line_message_processor_id: str) -> None:
    """LINEMessageProcessor の ID を reply SQS キューに送信する。

    Args:
        line_message_processor_id (str): LINEMessageProcessor の ID

    Raises:
        RuntimeError: REPLY_QUEUE_URL が未設定の場合
    """
    queue_url = config.AppConfig.get_reply_queue_url()
    if not queue_url:
        raise RuntimeError("REPLY_QUEUE_URL is not set")

    sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(
            {"line_message_processor_id": line_message_processor_id},
            ensure_ascii=False,
        ),
    )
