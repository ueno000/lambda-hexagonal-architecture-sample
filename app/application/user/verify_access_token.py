import json
from dataclasses import dataclass
from typing import Optional

import requests
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import api_gateway

app = api_gateway.ApiGatewayResolver()
logger = Logger()
tracer = Tracer()
VERIFY_URL = "https://api.line.me/oauth2/v2.1/verify?access_token="


def verify_access_token(access_token: str) -> Optional[str]:
    """_summary_
    有効なアクセストークンか検証

    Args:
        access_token (str): _description_

    Returns:
        Optional[str]: _description_
    """
    try:
        response = requests.get(
            VERIFY_URL + access_token,
            timeout=30,
        )
        response.raise_for_status()

        if not response.ok:
            return None

        verify_response_content = response.text  # ReadAsStringAsync 相当
        data = json.loads(verify_response_content)

        verify_result = VerifyResult(
            client_id=data.get("client_id"),
            expires_in=data.get("expires_in"),
            scope=data.get("scope"),
        )

        if verify_result is None:
            return None

        return access_token

    except Exception as e:
        logger.exception(f"Failed to fetch forecast : {e}")
        return None


@dataclass
class VerifyResult:
    client_id: str | None
    expires_in: int | None
    scope: str | None
