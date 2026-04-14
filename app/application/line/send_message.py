import json
import logging

import requests
from dataclasses import asdict

from app import config
from app.domain.model.line.line_request_message import (
    RequestReplyMessage,
    TextMessage,
)

logger = logging.getLogger(__name__)


def send_message(reply_token: str, message: str):
    access_token = config.AppConfig.get_line_channel_access_token()
    if not access_token:
        raise RuntimeError("LINE_CHANNEL_ACCESS_TOKEN is not set")

    messages = [TextMessage(type="text", text=message)]

    request_reply_message = RequestReplyMessage(
        replyToken=reply_token,
        messages=[asdict(m) for m in messages],
    )

    json_data = json.dumps(asdict(request_reply_message), ensure_ascii=False)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    try:
        response = requests.post(
            "https://api.line.me/v2/bot/message/reply",
            headers=headers,
            data=json_data,
            timeout=10,
        )
    except Exception as e:
        logger.error(f"Error sending message to LINE API: {type(e).__name__}: {str(e)}")

    logger.info("LINE response status=%s body=%s", response.status_code, response.text)
    return response
