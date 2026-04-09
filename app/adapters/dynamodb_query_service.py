from typing import Any, List, Optional, Tuple

from boto3.dynamodb.conditions import Key
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
            ExpressionAttributeValues={":v": line_id},
            Limit=1,
        )

        items = response.get("Items", [])
        if not items:
            return None

        return line_user.LINEUser.parse_obj(items[0])


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
            Key={"id": processor_id},
        )

        return (
            line_message_processor.LINEMessageProcessor.parse_obj(
                processor_response["Item"]
            )
            if processor_response.get("Item")
            else None
        )
