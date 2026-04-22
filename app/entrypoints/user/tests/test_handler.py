import base64
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.tests.support import install_test_stubs

install_test_stubs()

from app.domain.model.user.exist_user_result import ExistUserResult
from app.entrypoints.user import handler


class UserHandlerTests(unittest.TestCase):
    def test_normalize_request_body_decodes_base64_body(self):
        event = SimpleNamespace(
            body=base64.b64encode(b'{"accessToken":"token-123"}').decode("utf-8"),
            is_base64_encoded=True,
            raw_event={},
        )

        body = handler._normalize_request_body(event)

        self.assertEqual('{"accessToken":"token-123"}', body)

    def test_normalize_request_body_serializes_non_string_body(self):
        event = SimpleNamespace(
            body={"accessToken": "token-123"},
            is_base64_encoded=False,
            raw_event={},
        )

        body = handler._normalize_request_body(event)

        self.assertEqual(
            json.dumps({"accessToken": "token-123"}, ensure_ascii=False), body
        )

    def test_exist_user_returns_200_when_usecase_succeeds(self):
        handler.app.current_event = SimpleNamespace(
            body='{"accessToken":"token-123"}',
            is_base64_encoded=False,
            raw_event={},
        )
        result = ExistUserResult(
            is_exist=True,
            user_profile_id="profile-1",
            name="Taro",
            gender="male",
            age="30",
            region="Tokyo",
            region_cd="13",
            lines=["1", "2"],
            interest_topics=["1", "2"],
        )

        with patch.object(handler, "exist_line_user", return_value=result):
            response = handler.exist_user()

        self.assertEqual(200, response["statusCode"])
        self.assertEqual("profile-1", json.loads(response["body"])["user_profile_id"])

    def test_exist_user_returns_500_when_usecase_returns_none(self):
        handler.app.current_event = SimpleNamespace(
            body='{"accessToken":"token-123"}',
            is_base64_encoded=False,
            raw_event={},
        )

        with patch.object(handler, "exist_line_user", return_value=None):
            response = handler.exist_user()

        self.assertEqual(500, response["statusCode"])
        self.assertEqual("Internal server error", json.loads(response["body"])["error"])


if __name__ == "__main__":
    unittest.main()
