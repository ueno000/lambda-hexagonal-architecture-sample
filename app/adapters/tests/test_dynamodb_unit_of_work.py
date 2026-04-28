import unittest
from unittest.mock import Mock

from app.tests.support import install_test_stubs

install_test_stubs()

from app.adapters.dynamodb_unit_of_work import (
    DBPrefix,
    DynamoDBAIUserProfileRepository,
    DynamoDBLINEMessageProcessorsRepository,
    DynamoDBLINEUsersRepository,
)
from app.domain.model.ai_chat.ai_user_profile import AIUserProfile


class DynamoDBUnitOfWorkTests(unittest.TestCase):
    def test_generate_line_user_key_uses_id_prefix(self):
        key = DynamoDBLINEUsersRepository.generate_line_user_key("user-1")

        self.assertEqual({"id": "user-1"}, key)

    def test_generate_line_message_processor_key_uses_pk_prefix(self):
        key = (
            DynamoDBLINEMessageProcessorsRepository.generate_line_message_processor_key(
                "processor-1"
            )
        )

        self.assertEqual(
            {"PK": f"{DBPrefix.LINE_MESSAGE_PROCESSOR.value}#processor-1"},
            key,
        )

    def test_ai_user_profile_repository_add_serializes_model_before_enqueue(self):
        context = Mock()
        repository = DynamoDBAIUserProfileRepository("ai-user-profile-table", context)
        profile = AIUserProfile(
            id="profile-1",
            line_user_id="line-user-1",
            name="Taro",
            gender="male",
            age="30",
            region="Tokyo",
            region_cd="13",
            lines=["Yamanote"],
            interest_topics=["weather"],
            character_type=0,
        )

        repository.add(profile)

        enqueued_item = context.add_generic_item.call_args.kwargs["item"]
        self.assertEqual("ai-user-profile-table", enqueued_item["Put"]["TableName"])
        self.assertEqual({"S": "profile-1"}, enqueued_item["Put"]["Item"]["id"])
        self.assertEqual(
            {"S": "line-user-1"}, enqueued_item["Put"]["Item"]["line_user_id"]
        )


if __name__ == "__main__":
    unittest.main()
