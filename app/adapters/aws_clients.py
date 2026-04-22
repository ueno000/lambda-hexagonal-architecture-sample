from functools import lru_cache

import boto3
from mypy_boto3_dynamodb import client as dynamodb_client_types

from app import config


@lru_cache(maxsize=1)
def get_dynamodb_client() -> dynamodb_client_types.DynamoDBClient:
    return boto3.client(
        "dynamodb",
        region_name=config.AppConfig.get_default_region(),
        endpoint_url=config.AppConfig.get_dynamodb_endpoint_url(),
    )
