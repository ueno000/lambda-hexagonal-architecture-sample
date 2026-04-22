import unittest
from types import SimpleNamespace

from app.tests.support import install_test_stubs

install_test_stubs()

from app.adapters.dynamodb_query_service import (
    DynamoDBAIUserProfilesQueryService,
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
        self.assertEqual({"id": {"S": "processor-1"}}, captured["Key"])

    def test_get_line_user_by_line_id_queries_index(self):
        captured = {}

        class DummyClient:
            def query(self, **kwargs):
                captured.update(kwargs)
                return {
                    "Items": [
                        {
                            "id": f"LINEUSER#user-1",
                            "line_id": "line-user-1",
                        }
                    ]
                }

        query_service = DynamoDBLINEUsersQueryService(
            "user-table",
            DummyClient(),
        )

        user = query_service.get_line_user_by_line_id("line-user-1")

        self.assertEqual("user-table", captured["TableName"])
        self.assertEqual("line_id-index", captured["IndexName"])
        self.assertEqual(
            {":v": {"S": "line-user-1"}}, captured["ExpressionAttributeValues"]
        )
        self.assertEqual("user-1", user.id)

    def test_get_ai_user_profile_by_line_user_id_queries_index(self):
        captured = {}

        class DummyClient:
            def query(self, **kwargs):
                captured.update(kwargs)
                return {
                    "Items": [
                        {
                            "id": "profile-1",
                            "line_user_id": "user-1",
                        }
                    ]
                }

        query_service = DynamoDBAIUserProfilesQueryService(
            "ai-user-profile-table",
            DummyClient(),
        )

        profile = query_service.get_ai_user_profile_by_line_user_id("user-1")

        self.assertEqual("ai-user-profile-table", captured["TableName"])
        self.assertEqual("line_user_id-index", captured["IndexName"])
        self.assertEqual(
            {":v": {"S": "user-1"}}, captured["ExpressionAttributeValues"]
        )
        self.assertEqual("profile-1", profile["id"])

    def test_get_ai_user_profile_by_id_uses_id_key(self):
        captured = {}

        class DummyClient:
            def get_item(self, **kwargs):
                captured.update(kwargs)
                return {"Item": {"id": "profile-1", "line_user_id": "user-1"}}

        query_service = DynamoDBAIUserProfilesQueryService(
            "ai-user-profile-table",
            DummyClient(),
        )

        profile = query_service.get_ai_user_profile_by_id("profile-1")

        self.assertEqual("ai-user-profile-table", captured["TableName"])
        self.assertEqual({"id": {"S": "profile-1"}}, captured["Key"])
        self.assertEqual("profile-1", profile["id"])


if __name__ == "__main__":
    unittest.main()
