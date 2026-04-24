import unittest
from types import SimpleNamespace

from app.tests.support import install_test_stubs

install_test_stubs()

from app.application.user.update_ai_profile_usecase import UpdateAIProfileUseCase


class DummyUnitOfWork:
    def __init__(self):
        self.ai_user_profile = SimpleNamespace(update=self._update)
        self.updated_profile = None
        self.committed = False

    def _update(self, profile):
        self.updated_profile = profile

    def commit(self):
        self.committed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class UpdateAIProfileUseCaseTests(unittest.TestCase):
    def test_execute_updates_profile_with_existing_line_user_id(self):
        unit_of_work = DummyUnitOfWork()
        query_service = SimpleNamespace(
            get_ai_user_profile_by_id=lambda _id: {
                "id": "profile-1",
                "line_user_id": "line-user-1",
            }
        )
        req = SimpleNamespace(
            id="profile-1",
            model_dump=lambda **_kwargs: {
                "name": "Hanako",
                "region": "Tokyo",
            },
        )

        result = UpdateAIProfileUseCase(unit_of_work, query_service).execute(req)

        self.assertEqual("profile-1", result.id)
        self.assertEqual("line-user-1", result.line_user_id)
        self.assertEqual("Hanako", result.name)
        self.assertEqual("Tokyo", result.region)
        self.assertIs(unit_of_work.updated_profile, result)
        self.assertTrue(unit_of_work.committed)


if __name__ == "__main__":
    unittest.main()
