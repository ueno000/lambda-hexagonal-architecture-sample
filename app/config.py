import os
import typing

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    cors_config: dict = Field(..., title="CORS configuration")

    @staticmethod
    def get_api_base_path() -> str:
        return f'/{os.environ.get("API_BASE_PATH")}'

    @staticmethod
    def get_default_region() -> typing.Optional[str]:
        return os.environ.get("AWS_DEFAULT_REGION")

    @staticmethod
    def get_table_name_line() -> str:
        return os.environ.get("TABLE_NAME_LINE", "")

    @staticmethod
    def get_line_channel_secret() -> str:
        return os.environ.get("LINE_CHANNEL_SECRET", "")

    @staticmethod
    def get_dynamodb_endpoint_url() -> typing.Optional[str]:
        # ローカル DynamoDB のエンドポイントを返す。None なら本番の DynamoDB に接続される。
        return os.environ.get("DYNAMODB_ENDPOINT_URL")



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
