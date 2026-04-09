import json
import os
import typing
from functools import lru_cache

import boto3
from pydantic import BaseModel, Field


@lru_cache(maxsize=1)
def load_line_secrets() -> dict:
    secret_id = os.environ.get("LINE_SECRET_ARN", "")
    if not secret_id:
        return {}

    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_id)
    secret_string = response.get("SecretString", "{}")
    return json.loads(secret_string)


class AppConfig(BaseModel):
    cors_config: dict = Field(..., title="CORS configuration")

    @staticmethod
    def get_default_region() -> typing.Optional[str]:
        return os.environ.get("AWS_REGION", "ap-northeast-1")

    @staticmethod
    def get_table_name_line() -> str:
        return os.environ.get("TABLE_NAME_LINE", "")

    @staticmethod
    def get_table_name_line_user() -> str:
        return os.environ.get("TABLE_NAME_LINE_USER", "")

    @staticmethod
    def get_chat_queue_url() -> str:
        return os.environ.get("CHAT_QUEUE_URL", "")

    @staticmethod
    def get_line_channel_secret() -> str:
        return load_line_secrets().get("LINE_CHANNEL_SECRET", "")

    @staticmethod
    def get_line_channel_access_token() -> str:
        return load_line_secrets().get("LINE_CHANNEL_ACCESS_TOKEN", "")

    @staticmethod
    def get_dynamodb_endpoint_url() -> typing.Optional[str]:
        value = os.environ.get("DYNAMODB_ENDPOINT_URL")
        return value or None


config = {
    "cors_config": {
        "allow_origin": "*",
        "expose_headers": [],
        "allow_headers": [
            "Content-Type,X-Amz-Date,Authorization,X-Api-Key,x-amz-security-token"
        ],
        "max_age": 100,
        "allow_credentials": True,
    },
}
