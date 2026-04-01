from typing import Any, List

from mypy_boto3_dynamodb import client, type_defs

from app.domain.exceptions import repository_exception


class DynamoDBContext:
    """DynamoDB のトランザクションを扱うコンテキストマネージャ。"""

    def __init__(self, dynamodb_client: client.DynamoDBClient):
        self._db_items: List[type_defs.TransactWriteItemTypeDef] = []
        self._dynamo_db_client = dynamodb_client

    def commit(self) -> None:
        """保留中の変更（最大25件）を1つのトランザクションとして DynamoDB にコミットする。"""
        try:
            self._dynamo_db_client.transact_write_items(TransactItems=self._db_items)
            self._db_items = []
        except Exception as e:
            raise repository_exception.RepositoryException(
                "Failed to commit a transaction to DynamoDB."
            ) from e

    def add_generic_item(self, item: dict) -> None:
        """DynamoDB の更新系操作（Put / Update / Delete）を保留リストに追加する。"""
        dynamodb_item = type_defs.TransactWriteItemTypeDef(**item)
        self._db_items.append(dynamodb_item)

    def get_generic_item(self, request: dict) -> Any:
        """
        プライマリキーを使って DynamoDB からアイテムを取得する。
        プライマリキーにはパーティションキーとソートキーの両方が必要。
        """
        item = self._dynamo_db_client.get_item(**request)

        return item["Item"] if "Item" in item else None


class DynamoDBRepository:
    """汎用的な DynamoDB リポジトリ。"""

    def __init__(self, table_name: str, context: DynamoDBContext):
        self._table_name = table_name
        self._context = context

    def add_generic_item(self, item: dict, key: dict) -> None:
        """
        指定されたデータを DynamoDB の Put 操作形式に変換し、
        トランザクション用の保留リストに追加する。
        """
        self._context.add_generic_item(
            item=self._create_put_modifier(obj=item, key=key)
        )

    def update_generic_item(self, expression: dict, key: dict) -> None:
        """
        指定された更新内容を DynamoDB の Update 操作形式に変換し、
        トランザクション用の保留リストに追加する。
        """
        self._context.add_generic_item(
            item=self._create_update_modifier(expression=expression, key=key)
        )

    def delete_generic_item(self, key: dict) -> None:
        """
        指定されたキーをもとに DynamoDB の Delete 操作形式に変換し、
        トランザクション用の保留リストに追加する。
        """
        self._context.add_generic_item(item=self._create_delete_modifier(key=key))

    def _create_put_modifier(self, obj: dict, key: dict) -> dict:
        """
        Put 操作用のリクエストを生成する。
        同一の PK / SK が既に存在する場合は失敗する（重複防止）。
        """
        return {
            "Put": {
                "TableName": self._table_name,
                "Item": {**obj, **key},
                "ConditionExpression": "(attribute_not_exists(PK) AND attribute_not_exists(SK))",
            }
        }

    def _create_update_modifier(self, expression: dict, key: dict) -> dict:
        """
        Update 操作用のリクエストを生成する。
        """
        return {"Update": {"TableName": self._table_name, "Key": key, **expression}}

    def _create_get_request(self, key: dict) -> dict:
        """
        GetItem 用のリクエストを生成する。
        """
        return {"TableName": self._table_name, "Key": {**key}}

    def _create_delete_modifier(self, key: dict) -> dict:
        """
        Delete 操作用のリクエストを生成する。
        """
        return {"Delete": {"TableName": self._table_name, "Key": key}}
