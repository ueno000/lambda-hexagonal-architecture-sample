from decimal import Decimal
from typing import Any, Optional

from boto3.dynamodb.types import TypeDeserializer
from mypy_boto3_dynamodb import client

from app.adapters.dynamodb_unit_of_work import (
    DBPrefix,
    DynamoDBLINEUsersRepository,
    DynamoDBLINEMessageProcessorsRepository,
)

from app.domain.model.line import line_message_processor, line_user
from app.domain.ports import line_query_service


class DynamoDBLINEUsersQueryService(line_query_service.LINEUsersQueryService):
    def __init__(self, table_name: str, dynamodb_client: client.DynamoDBClient):
        self._table_name = table_name
        self._dynamodb_client = dynamodb_client

    def get_line_user_by_line_id(self, line_id: str) -> Optional[line_user.LINEUser]:
        response = self._dynamodb_client.query(
            TableName=self._table_name,
            IndexName="line_id-index",
            KeyConditionExpression="line_id = :v",
            ExpressionAttributeValues={":v": _serialize_attribute_value(line_id)},
            Limit=1,
        )

        items = [_deserialize_dynamodb_item(item) for item in response.get("Items", [])]
        if not items:
            return None

        return line_user.LINEUser.parse_obj(_normalize_line_user_item(items[0]))


class DynamoDBLINEMessageProcessorsQueryService(
    line_query_service.LINEMessageProcessorsQueryService
):
    """LINE Message Processors DynamoDB query service."""

    def __init__(self, table_name: str, dynamodb_client: client.DynamoDBClient):
        self._table_name = table_name
        self._dynamodb_client = dynamodb_client

    def get_line_message_processor_by_id(
        self, processor_id: str
    ) -> Optional[line_message_processor.LINEMessageProcessor]:
        """Returns a single LINE message processor by ID."""

        processor_response = self._dynamodb_client.get_item(
            TableName=self._table_name,
            Key={"id": _serialize_attribute_value(processor_id)},
        )

        return (
            line_message_processor.LINEMessageProcessor.parse_obj(
                _deserialize_dynamodb_item(processor_response["Item"])
            )
            if processor_response.get("Item")
            else None
        )


class DynamoDBAIUserProfilesQueryService(line_query_service.AIUserProfilesQueryService):
    def __init__(self, table_name: str, dynamodb_client: client.DynamoDBClient):
        self._table_name = table_name
        self._dynamodb_client = dynamodb_client

    def get_ai_user_profile_by_line_user_id(self, line_user_id: str) -> Optional[dict]:
        response = self._dynamodb_client.query(
            TableName=self._table_name,
            IndexName="line_user_id-index",
            KeyConditionExpression="line_user_id = :v",
            ExpressionAttributeValues={":v": _serialize_attribute_value(line_user_id)},
            Limit=1,
        )

        items = [_deserialize_dynamodb_item(item) for item in response.get("Items", [])]
        return items[0] if items else None

    def get_ai_user_profile_by_id(self, ai_user_profile_id: str) -> Optional[dict]:
        response = self._dynamodb_client.get_item(
            TableName=self._table_name,
            Key={"id": _serialize_attribute_value(ai_user_profile_id)},
        )
        item = response.get("Item")
        return _deserialize_dynamodb_item(item) if item else None


def _normalize_line_user_item(item: dict) -> dict:
    normalized_item = dict(item)
    user_id = normalized_item.get("id")
    prefix = f"{DBPrefix.LINE_USER.value}#"
    if isinstance(user_id, str) and user_id.startswith(prefix):
        normalized_item["id"] = user_id[len(prefix) :]
    return normalized_item


def _deserialize_dynamodb_item(item: dict) -> dict:
    if not item:
        return item

    deserializer = TypeDeserializer()
    normalized = {}
    for key, value in item.items():
        if _is_attribute_value(value):
            normalized[key] = deserializer.deserialize(value)
        else:
            normalized[key] = value
    return normalized


def _is_attribute_value(value: Any) -> bool:
    if not isinstance(value, dict) or len(value) != 1:
        return False

    attribute_type = next(iter(value))
    return attribute_type in {"S", "N", "BOOL", "NULL", "M", "L", "SS", "NS", "BS", "B"}


def _serialize_attribute_value(value: Any) -> dict:
    if value is None:
        return {"NULL": True}
    if isinstance(value, bool):
        return {"BOOL": value}
    if isinstance(value, str):
        return {"S": value}
    if isinstance(value, (int, float, Decimal)):
        return {"N": str(value)}
    if isinstance(value, list):
        return {"L": [_serialize_attribute_value(item) for item in value]}
    if isinstance(value, dict):
        return {"M": {key: _serialize_attribute_value(item) for key, item in value.items()}}

    raise TypeError(f"Unsupported DynamoDB attribute value type: {type(value)!r}")
