from dataclasses import dataclass
from typing import Optional

import requests
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import api_gateway

app = api_gateway.ApiGatewayResolver()
logger = Logger()
PROFILE_URL = "https://api.line.me/v2/profile"


@dataclass
class ProfileResult:
    user_id: str
    display_name: str | None
    picture_url: str | None
    status_message: str | None


def get_profile(access_token: str) -> Optional[ProfileResult]:
    """_summary_
    ユーザープロフィールを取得する

    Args:
        access_token (str): _description_

    Returns:
        Optional[ProfileResult]: _description_
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(PROFILE_URL, headers=headers)

    if not response.ok:
        return None

    data = response.json()

    return ProfileResult(
        user_id=data.get("user_id"),
        display_name=data.get("display_name"),
        picture_url=data.get("picture_url"),
        status_message=data.get("status_message"),
    )
