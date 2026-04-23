from dataclasses import dataclass
from typing import Optional

import requests
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import api_gateway

app = api_gateway.ApiGatewayResolver()
logger = Logger()
INFO_URL = "https://api.line.me/oauth2/v2.1/userinfo"


@dataclass
class InfoResult:
    sub: str
    name: str
    picture: str


def get_info(access_token: str) -> Optional[InfoResult]:
    """_summary_
    ユーザー情報を取得する
    See Also:
        https://developers.line.biz/ja/reference/line-login/#userinfo

    Args:
        access_token (str): _description_

    Returns:
        Optional[InfoResult]: _description_
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(INFO_URL, headers=headers)
    logger.info(f"status: {response.status_code}")
    logger.info(f"body: {response.text}")

    if not response.ok:
        return None

    data = response.json()

    return InfoResult(
        sub=data.get("sub"),
        name=data.get("name"),
        picture=data.get("picture"),
    )
