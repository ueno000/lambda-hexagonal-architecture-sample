import json
from datetime import datetime, timezone
from typing import Any, Dict

import boto3
import requests
from aws_lambda_powertools import Logger

from app import config
from app.adapters import aws_clients, dynamodb_query_service, dynamodb_unit_of_work
from app.application.ai_chat.prompt_builder import build_daily_guide_prompt
from app.domain.model.ai_chat.ai_user_profile import AIUserProfile
from app.domain.model.ai_chat.chat_session import ChatSession
from app.domain.model.line.line_message_processor import MessageStatus

logger = Logger()

dynamodb_client = aws_clients.get_dynamodb_client()

line_query_service = dynamodb_query_service.DynamoDBLINEMessageProcessorsQueryService(
    config.AppConfig.get_table_name_line(), dynamodb_client
)

ai_user_profiles_query_service = (
    dynamodb_query_service.DynamoDBAIUserProfilesQueryService(
        config.AppConfig.get_table_name_ai_user_profile(),
        dynamodb_client,
    )
)

unit_of_work = dynamodb_unit_of_work.DynamoDBUnitOfWork(
    config.AppConfig.get_table_name_line(),
    config.AppConfig.get_table_name_line_user(),
    config.AppConfig.get_table_name_ai_user_profile(),
    dynamodb_client,
)

sqs_client = boto3.client(
    "sqs",
    region_name=config.AppConfig.get_default_region(),
)


def execute(line_message_processor, ai_user_profile_id: str) -> None:
    logger.info(
        f"Starting AI chat request for processor_id: {line_message_processor.id}, user_id: {ai_user_profile_id}"
    )

    ai_user_profile = ai_user_profiles_query_service.get_ai_user_profile_by_id(
        ai_user_profile_id
    )
    if not ai_user_profile:
        logger.error(f"AI user profile not found: {ai_user_profile_id}")
        return

    prompt = init_chat_request(ai_user_profile)
    logger.info(f"Builded Prompt: {prompt}")

    # リクエスト
    chat_response_text = request_chat(prompt)

    updated_line_message_processor = response_chat(
        line_message_processor,
        chat_response_text,
    )

    logger.info(
        f"Enqueueing reply request for processor_id: {updated_line_message_processor.id}"
    )
    enqueue_reply_request(updated_line_message_processor.id)
    logger.info("AI chat request completed successfully")


def init_chat_request(ai_user_profile: Dict[str, Any]) -> str:
    return build_daily_guide_prompt(_parse_ai_user_profile(ai_user_profile))


def request_chat(prompt: str) -> str:
    gemini_api_key = config.AppConfig.get_gemini_api_key()
    if not gemini_api_key:
        logger.error("gemini_api_key is not set")
        raise RuntimeError("gemini_api_key is not set")

    payload: Dict[str, Any] = {}

    try:
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
        text = _extract_chat_text(payload)
        logger.info(f"Chat text extracted successfully: {text}")
        return text
    except Exception as e:
        logger.error(
            f"Error requesting chat from Gemini API: {type(e).__name__}: {str(e)}"
        )
        if payload:
            logger.error(f"Error payload: {_stringify_error_payload(payload)}")
        raise


def response_chat(line_message_processor, chat_response_text: str):
    ### 返信内容をLINEMessageProcessorに保存
    line_message_processor.reply_message = chat_response_text
    line_message_processor.processing_status = MessageStatus.ReplyReady
    line_message_processor.last_update_date = datetime.now(timezone.utc).isoformat()

    with unit_of_work:
        unit_of_work.line_message_processors.put(line_message_processor)
        unit_of_work.commit()
    logger.info(f"Message processor {line_message_processor.id} updated successfully")

    return line_message_processor


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


def _stringify_error_payload(payload: Dict[str, Any]) -> str:
    error = payload.get("error")
    if error is None:
        return json.dumps(payload, ensure_ascii=False)

    if isinstance(error, str):
        return error

    if isinstance(error, dict):
        return json.dumps(error, ensure_ascii=False)

    return json.dumps(error, ensure_ascii=False)


def enqueue_reply_request(line_message_processor_id: str) -> None:
    """LINEMessageProcessor の ID を reply SQS キューに送信する。

    Args:
        line_message_processor_id (str): LINEMessageProcessor の ID

    Raises:
        RuntimeError: REPLY_QUEUE_URL が未設定の場合
    """
    queue_url = config.AppConfig.get_reply_queue_url()
    if not queue_url:
        logger.error("REPLY_QUEUE_URL is not set")
        raise RuntimeError("REPLY_QUEUE_URL is not set")

    logger.info(
        f"Sending message to reply queue for processor_id: {line_message_processor_id}"
    )

    try:
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(
                {"line_message_processor_id": line_message_processor_id},
                ensure_ascii=False,
            ),
        )
        logger.info(
            f"Reply request enqueued successfully for processor_id: {line_message_processor_id}"
        )
    except Exception as e:
        logger.error(
            f"Error enqueuing reply request for processor_id: {line_message_processor_id}, error: {type(e).__name__}: {str(e)}"
        )
        raise RuntimeError(
            f"Failed to enqueue reply request for processor_id: {line_message_processor_id}"
        ) from e
