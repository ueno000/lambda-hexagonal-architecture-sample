import unittest
from types import SimpleNamespace

from app.tests.support import install_test_stubs

install_test_stubs()

from app.adapters.dynamodb_query_service import (
    DynamoDBLINEMessageProcessorsQueryService,
    DynamoDBLINEUsersQueryService,
)


class DynamoDBQueryServiceTests(unittest.TestCase):
    def test_get_line_message_processor_by_id_uses_id_key(self):
        captured = {}

        class DummyClient:
            def get_item(self, **kwargs):
                captured.update(kwargs)
                return {"Item": {"id": "processor-1", "message_event": {"replyToken": "r"}}}

        query_service = DynamoDBLINEMessageProcessorsQueryService(
            "line-table",
            DummyClient(),
        )

        query_service.get_line_message_processor_by_id("processor-1")

        self.assertEqual("line-table", captured["TableName"])
        self.assertEqual({"id": "processor-1"}, captured["Key"])

    def test_get_line_user_by_line_id_queries_index(self):
        captured = {}

        class DummyClient:
            def query(self, **kwargs):
                captured.update(kwargs)
                return {"Items": [{"id": "user-1", "line_id": "line-user-1"}]}

        query_service = DynamoDBLINEUsersQueryService(
            "user-table",
            DummyClient(),
        )

        query_service.get_line_user_by_line_id("line-user-1")

        self.assertEqual("user-table", captured["TableName"])
        self.assertEqual("line_id-index", captured["IndexName"])
        self.assertEqual({":v": "line-user-1"}, captured["ExpressionAttributeValues"])


if __name__ == "__main__":
    unittest.main()
