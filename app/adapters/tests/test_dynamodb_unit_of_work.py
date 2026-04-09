import unittest

from app.tests.support import install_test_stubs

install_test_stubs()

from app.adapters.dynamodb_unit_of_work import (
    DBPrefix,
    DynamoDBLINEMessageProcessorsRepository,
    DynamoDBLINEUsersRepository,
)


class DynamoDBUnitOfWorkTests(unittest.TestCase):
    def test_generate_line_user_key_uses_id_prefix(self):
        key = DynamoDBLINEUsersRepository.generate_line_user_key("user-1")

        self.assertEqual({"id": "user-1"}, key)

    def test_generate_line_message_processor_key_uses_pk_prefix(self):
        key = DynamoDBLINEMessageProcessorsRepository.generate_line_message_processor_key(
            "processor-1"
        )

        self.assertEqual(
            {"PK": f"{DBPrefix.LINE_MESSAGE_PROCESSOR.value}#processor-1"},
            key,
        )


if __name__ == "__main__":
    unittest.main()
