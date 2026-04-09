import unittest
from unittest.mock import Mock, patch

from app.tests.support import install_test_stubs

install_test_stubs()

from app.application.line import create_line_user


class DummyUnitOfWork:
    def __init__(self):
        self.line_users = type("LineUsersRepo", (), {"add": Mock()})()
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def commit(self):
        self.committed = True


class CreateLineUserTests(unittest.TestCase):
    def test_create_line_user_saves_display_name(self):
        dummy_uow = DummyUnitOfWork()

        with patch.object(
            create_line_user,
            "fetch_line_display_name",
            return_value="Taro",
        ), patch.object(create_line_user, "unit_of_work", dummy_uow):
            user = create_line_user.create_line_user("line-user-1")

        self.assertEqual("line-user-1", user.line_id)
        self.assertEqual("Taro", user.name)
        self.assertTrue(dummy_uow.committed)

    def test_fetch_line_display_name_calls_line_profile_api(self):
        response = type(
            "Response",
            (),
            {
                "status_code": 200,
                "text": "ok",
                "json": lambda self: {"displayName": "Hanako"},
            },
        )()

        with patch.object(
            create_line_user.config.AppConfig,
            "get_line_channel_access_token",
            return_value="access-token",
        ), patch.object(
            create_line_user.requests,
            "get",
            return_value=response,
        ) as mock_get:
            display_name = create_line_user.fetch_line_display_name("line-user-1")

        self.assertEqual("Hanako", display_name)
        mock_get.assert_called_once_with(
            "https://api.line.me/v2/bot/profile/line-user-1",
            headers={"Authorization": "Bearer access-token"},
            timeout=10,
        )


if __name__ == "__main__":
    unittest.main()
