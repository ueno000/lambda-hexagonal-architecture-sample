import unittest

from app.tests.support import install_test_stubs

install_test_stubs()

from app.domain.model.user.ai_profile_request import (
    AIUserProfileCharacterTypeUpdateRequest,
)


class AIUserProfileCharacterTypeUpdateRequestTests(unittest.TestCase):
    def test_validate_character_type_is_int_accepts_integer(self):
        value = AIUserProfileCharacterTypeUpdateRequest.validate_character_type_is_int(
            AIUserProfileCharacterTypeUpdateRequest, 2
        )

        self.assertEqual(2, value)

    def test_validate_character_type_is_int_rejects_string(self):
        with self.assertRaises(ValueError):
            AIUserProfileCharacterTypeUpdateRequest.validate_character_type_is_int(
                AIUserProfileCharacterTypeUpdateRequest, "2"
            )

    def test_validate_character_type_range_rejects_out_of_range_value(self):
        with self.assertRaises(ValueError):
            AIUserProfileCharacterTypeUpdateRequest.validate_character_type_range(
                AIUserProfileCharacterTypeUpdateRequest, 99
            )


if __name__ == "__main__":
    unittest.main()
