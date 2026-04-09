from datetime import datetime, timezone
import uuid

import boto3
import requests
from aws_lambda_powertools import Logger, Tracer

from app import config
from app.adapters import dynamodb_unit_of_work
from app.domain.model.line.line_user import LINEUser

logger = Logger()
tracer = Tracer()

dynamodb_client = boto3.resource(
    "dynamodb",
    region_name=config.AppConfig.get_default_region(),
    endpoint_url=config.AppConfig.get_dynamodb_endpoint_url(),
)

unit_of_work = dynamodb_unit_of_work.DynamoDBUnitOfWork(
    config.AppConfig.get_table_name_line(),
    config.AppConfig.get_table_name_line_user(),
    dynamodb_client.meta.client,
)


@tracer.capture_method
def create_line_user(line_id: str) -> LINEUser:
    """LINE ユーザーが存在しない場合に新規作成する。"""
    display_name = fetch_line_display_name(line_id)
    new_user = LINEUser(
        id=str(uuid.uuid4()),
        line_id=line_id,
        name=display_name,
        create_date=datetime.now(timezone.utc).isoformat(),
    )
    with unit_of_work:
        unit_of_work.line_users.add(new_user)
        unit_of_work.commit()
    logger.info("Created new LINE user with ID: %s", new_user.id)
    return new_user


def fetch_line_display_name(line_id: str) -> str | None:
    """_summary_
    LINEのプロフィールAPIを呼び出して、ユーザーの表示名を取得する。
    Args:
        line_id (str): _description_

    Returns:
        str | None: _description_
    """
    access_token = config.AppConfig.get_line_channel_access_token()
    if not access_token:
        logger.warning("LINE_CHANNEL_ACCESS_TOKEN is not set")
        return None

    response = requests.get(
        f"https://api.line.me/v2/bot/profile/{line_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )

    if response.status_code != 200:
        logger.warning(
            "Failed to fetch LINE profile. status=%s body=%s",
            response.status_code,
            response.text,
        )
        return None

    return response.json().get("displayName")
