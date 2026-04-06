from typing import Any, List, Optional, Tuple

from boto3.dynamodb.conditions import Key
from boto3.dynamodb.types import TypeDeserializer
from mypy_boto3_dynamodb import client

from app.adapters.dynamodb_unit_of_work import (
    DBPrefix,
    DynamoDBProductsRepository,
    DynamoDBLINEUsersRepository,
    DynamoDBLINEMessageProcessorsRepository,
)
from app.domain.model import product
from app.domain.model.line import line_message_processor, line_user
from app.domain.ports import products_query_service, line_query_service


class DynamoDBProductsQueryService(products_query_service.ProductsQueryService):
    """Products DynamoDB query service."""

    def __init__(self, table_name: str, dynamodb_client: client.DynamoDBClient):
        self._table_name = table_name
        self._dynamodb_client = dynamodb_client

    def list_products(
        self, page_size: int, next_token: Any
    ) -> Tuple[List[product.Product], Any]:
        """Returns a list of all products in repository with paging after 1 MB."""

        if next_token:
            result = self._dynamodb_client.scan(
                TableName=self._table_name,
                Limit=page_size,
                FilterExpression=Key("PK").begins_with(f"{DBPrefix.PRODUCT.value}#"),
                ExclusiveStartKey=next_token,
            )
        else:
            result = self._dynamodb_client.scan(
                TableName=self._table_name,
                Limit=page_size,
                FilterExpression=Key("PK").begins_with(f"{DBPrefix.PRODUCT.value}#"),
            )

        products = [product.Product.parse_obj(item) for item in result["Items"]]

        if "LastEvaluatedKey" in result:
            return products, result["LastEvaluatedKey"]
        else:
            return products, None

    def get_product_by_id(self, product_id: str) -> Optional[product.Product]:
        """Returns a single product by ID."""

        product_response = self._dynamodb_client.get_item(
            TableName=self._table_name,
            Key=DynamoDBProductsRepository.generate_product_key(product_id),
        )

        return (
            product.Product.parse_obj(product_response["Item"])
            if product_response["Item"]
            else None
        )


class DynamoDBLINEUsersQueryService(line_query_service.LINEUsersQueryService):
    def __init__(self, table_name: str, dynamodb_client: client.DynamoDBClient):
        self._table_name = table_name
        self._dynamodb_client = dynamodb_client

    def get_line_user_by_line_id(self, line_id: str) -> Optional[line_user.LINEUser]:
        response = self._dynamodb_client.query(
            TableName=self._table_name,
            IndexName="line_id-index",
            KeyConditionExpression="line_id = :v",
            ExpressionAttributeValues={
                ":v": line_id
            },
            Limit=1,
        )

        items = response.get("Items", [])
        if not items:
            return None

        return line_user.LINEUser.parse_obj(items[0])

class DynamoDBLINEMessageProcessorsQueryService(line_query_service.LINEMessageProcessorsQueryService):
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
            Key=DynamoDBLINEMessageProcessorsRepository.generate_line_message_processor_key(
                processor_id
            ),
        )

        return (
            line_message_processor.LINEMessageProcessor.parse_obj(processor_response["Item"])
            if processor_response.get("Item")
            else None
        )
