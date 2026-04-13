import unittest
from unittest.mock import Mock, patch

import requests

from app.tests.support import install_test_stubs

install_test_stubs()

from app.application.ai_chat import ai_chat_request
from app.domain.model.line.line_message_processor import (
    LINEMessageProcessor,
    MessageStatus,
)
from app.domain.model.line.line_user import LINEUser


class AIChatRequestTests(unittest.TestCase):
    def test_init_chat_request_builds_prompt_from_validated_profile(self):
        ai_user_profile = {
            "id": "profile-1",
            "line_user_id": "line-user-1",
            "name": "Taro",
            "interest_topics": ["weather"],
            "lines": ["Yamanote"],
        }

        with patch.object(
            ai_chat_request, "build_daily_guide_prompt", return_value="prompt"
        ) as mock_build_prompt:
            actual = ai_chat_request.init_chat_request(ai_user_profile)

        self.assertEqual("prompt", actual)
        profile_arg = mock_build_prompt.call_args.args[0]
        self.assertEqual("profile-1", profile_arg.id)
        self.assertEqual("line-user-1", profile_arg.line_user_id)

    def test_request_chat_returns_first_text_part(self):
        response = Mock()
        response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "hello from gemini"}]}}]
        }

        with patch.object(
            ai_chat_request.config.AppConfig,
            "get_gemini_api_key",
            return_value="dummy-key",
        ), patch.object(
            ai_chat_request.requests, "post", return_value=response
        ) as mock_post:
            actual = ai_chat_request.request_chat("prompt")

        self.assertEqual("hello from gemini", actual)
        mock_post.assert_called_once()
        response.raise_for_status.assert_called_once_with()

    def test_request_chat_returns_error_message_when_response_is_error(self):
        response = Mock()
        response.json.return_value = {
            "error": {
                "code": 429,
                "message": "quota exceeded",
            }
        }
        response.raise_for_status.side_effect = requests.HTTPError("429 Client Error")

        with patch.object(
            ai_chat_request.config.AppConfig,
            "get_gemini_api_key",
            return_value="dummy-key",
        ), patch.object(ai_chat_request.requests, "post", return_value=response):
            actual = ai_chat_request.request_chat("prompt")

        self.assertEqual("quota exceeded", actual)

    def test_response_chat_updates_processor_and_persists(self):
        line_message_processor = LINEMessageProcessor(
            id="processor-1",
            processing_status=MessageStatus.AwaitingChatResponse.value,
            message_event={"replyToken": "reply-token"},
            line_user=LINEUser(id="user-1", line_id="line-user-1", talk_count=0),
        )

        fake_unit_of_work = Mock()
        fake_unit_of_work.__enter__ = Mock(return_value=fake_unit_of_work)
        fake_unit_of_work.__exit__ = Mock(return_value=None)

        with patch.object(ai_chat_request, "unit_of_work", fake_unit_of_work):
            actual = ai_chat_request.response_chat(
                line_message_processor,
                "profile-1",
                "generated reply",
            )

        self.assertIs(line_message_processor, actual)
        self.assertEqual("generated reply", actual.reply_message)
        self.assertEqual(MessageStatus.ReplyReady, actual.processing_status)
        fake_unit_of_work.line_message_processors.put.assert_called_once_with(actual)
        fake_unit_of_work.commit.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
