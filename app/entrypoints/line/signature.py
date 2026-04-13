import base64
import hashlib
import hmac
from aws_lambda_powertools import Logger
from typing import Tuple, Optional

logger = Logger()


def validate_signature(
    headers: dict,
    body: str,
    channel_secret: str,
) -> Tuple[Optional[dict], Optional[str]]:
    """
    LINE から送られてくる Webhook リクエストの署名検証を行う拡張メソッド
    ビジネスロジックにあたるので、Application レイヤーに配置するのがベストらしい

    Returns:
        (error_response, request_body)
    """

    logger.info("validate_signature start")
    logger.info("body type=%s", type(body))
    logger.info("body len=%s", len(body))
    logger.info("channel_secret exists=%s", bool(channel_secret))

    # ヘッダー取得
    signature = headers.get("x-line-signature") or headers.get("X-Line-Signature")
    if not signature:
        return (
            {"statusCode": 400, "body": "Signature header missing"},
            None,
        )

    # 検証
    if not verify_signature(signature, body, channel_secret):
        return (
            {"statusCode": 400, "body": "Signature verification failed"},
            None,
        )

    return None, body


def verify_signature(
    signature: str,
    body: str,
    channel_secret: str,
) -> bool:
    key_bytes = channel_secret.encode("utf-8")
    body_bytes = body.encode("utf-8")

    digest = hmac.new(
        key_bytes,
        body_bytes,
        hashlib.sha256,
    ).digest()

    hash64 = base64.b64encode(digest).decode("utf-8")

    return hmac.compare_digest(signature, hash64)
