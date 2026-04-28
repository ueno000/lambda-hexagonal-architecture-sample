import importlib.util
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.tests.support import install_test_stubs

install_test_stubs()

handler_path = Path(__file__).resolve().parents[1] / "handler.py"
spec = importlib.util.spec_from_file_location("user_handler", handler_path)
handler = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(handler)


class UserHandlerTests(unittest.TestCase):
    def test_exist_user_returns_character_type_in_response(self):
        handler.app.current_event = SimpleNamespace(
            body='{"accessToken":"token-123"}',
            is_base64_encoded=False,
            raw_event={},
        )
        exist_result = SimpleNamespace(
            model_dump=lambda: {
                "is_exist": True,
                "line_user_id": "line-user-1",
                "user_profile_id": "profile-1",
                "character_type": 2,
                "name": "Taro",
            }
        )

        with patch.object(handler, "exist_line_user", return_value=exist_result):
            response = handler.exist_user()

        self.assertEqual(200, response["statusCode"])
        self.assertEqual(2, json.loads(response["body"])["character_type"])

    def test_update_ai_profile_character_type_returns_200(self):
        handler.app.current_event = SimpleNamespace(
            body='{"id":"profile-1","character_type":2}',
            is_base64_encoded=False,
            raw_event={},
        )
        valid_result = SimpleNamespace(
            is_valid=True,
            value=SimpleNamespace(id="profile-1", character_type=2),
        )

        with patch.object(
            handler,
            "get_body",
            return_value=valid_result,
        ), patch.object(
            handler,
            "update_ai_user_profile_character_type",
            return_value=SimpleNamespace(id="profile-1"),
        ) as mock_update:
            response = handler.update_ai_profile_character_type()

        self.assertEqual(200, response["statusCode"])
        self.assertEqual("profile-1", json.loads(response["body"])["id"])
        mock_update.assert_called_once()

    def test_update_ai_profile_character_type_returns_400_for_invalid_request(self):
        handler.app.current_event = SimpleNamespace(
            body='{"id":"profile-1","character_type":"invalid"}',
            is_base64_encoded=False,
            raw_event={},
        )
        invalid_result = SimpleNamespace(is_valid=False, value=None)

        with patch.object(
            handler, "get_body", return_value=invalid_result
        ), patch.object(
            handler, "update_ai_user_profile_character_type"
        ) as mock_update:
            response = handler.update_ai_profile_character_type()

        self.assertEqual(400, response["statusCode"])
        self.assertEqual(
            "Request validation error.", json.loads(response["body"])["error"]
        )
        mock_update.assert_not_called()


if __name__ == "__main__":
    unittest.main()
