import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.tests.support import install_test_stubs

install_test_stubs()

from app.application.user.exist_line_user_usecase import ExistLineUserUseCase


class ExistLineUserUseCaseTests(unittest.TestCase):
    def setUp(self):
        self.line_user_query_service = SimpleNamespace(
            get_line_user_by_line_id=lambda _user_id: None
        )
        self.ai_user_query_service = SimpleNamespace(
            get_ai_user_profile_by_line_user_id=lambda _user_id: None
        )
        self.usecase = ExistLineUserUseCase(
            self.line_user_query_service, self.ai_user_query_service
        )

    def test_extract_access_token_returns_token(self):
        body = json.dumps({"accessToken": "token-123"})

        result = self.usecase.extract_access_token(body)

        self.assertEqual("token-123", result)

    def test_execute_returns_none_when_user_id_cannot_be_extracted(self):
        with patch.object(self.usecase, "extract_user_id", return_value=None):
            result = self.usecase.execute(json.dumps({"accessToken": "invalid"}))

        self.assertIsNone(result)

    def test_execute_returns_not_exist_result_when_profile_is_missing(self):
        self.line_user_query_service.get_line_user_by_line_id = (
            lambda _user_id: SimpleNamespace(id="line-user-record-1")
        )

        with patch.object(self.usecase, "extract_user_id", return_value="line-user-1"):
            result = self.usecase.execute(json.dumps({"accessToken": "token-123"}))

        self.assertFalse(result.is_exist)
        self.assertIsNone(result.user_profile_id)
        self.assertIsNone(result.name)

    def test_execute_returns_existing_profile_result(self):
        self.line_user_query_service.get_line_user_by_line_id = (
            lambda _user_id: SimpleNamespace(id="line-user-record-1")
        )
        self.ai_user_query_service.get_ai_user_profile_by_line_user_id = (
            lambda _user_id: {
            "id": "profile-1",
            "name": "Taro",
            "gender": "male",
            "age": "30",
            "region": "Tokyo",
            "region_cd": "13",
            "lines": ["1", "2"],
            "interest_topics": ["10", "20"],
        }
        )

        with patch.object(self.usecase, "extract_user_id", return_value="line-user-1"):
            result = self.usecase.execute(json.dumps({"accessToken": "token-123"}))

        self.assertTrue(result.is_exist)
        self.assertEqual("profile-1", result.user_profile_id)
        self.assertEqual("Taro", result.name)
        self.assertEqual(["1", "2"], result.lines)
        self.assertEqual(["10", "20"], result.interest_topics)

    def test_execute_returns_none_when_query_service_raises(self):
        def raise_error(_user_id):
            raise RuntimeError("dynamodb failed")

        self.line_user_query_service.get_line_user_by_line_id = (
            lambda _user_id: SimpleNamespace(id="line-user-record-1")
        )
        self.ai_user_query_service.get_ai_user_profile_by_line_user_id = raise_error

        with patch.object(self.usecase, "extract_user_id", return_value="line-user-1"):
            result = self.usecase.execute(json.dumps({"accessToken": "token-123"}))

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
