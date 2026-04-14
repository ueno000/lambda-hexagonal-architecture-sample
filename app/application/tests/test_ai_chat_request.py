import unittest
from unittest.mock import Mock, patch

from app.tests.support import install_test_stubs

install_test_stubs()

from app.application.ai_chat import ai_chat_request
from app.domain.model.line.line_message_processor import (
    LINEMessageProcessor,
    MessageStatus,
)
from app.domain.model.line.line_user import LINEUser


# テスト用カスタム例外
class HTTPError(Exception):
    pass


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

    # def test_request_chat_returns_error_message_when_response_is_error(self):
    #     error_payload = {
    #         "code": 429,
    #         "message": "quota exceeded",
    #     }
    #     response = Mock()
    #     response.json.return_value = {"error": error_payload}
    #     response.raise_for_status.side_effect = HTTPError("429 Client Error")

    #     with patch.object(
    #         ai_chat_request.config.AppConfig,
    #         "get_gemini_api_key",
    #         return_value="dummy-key",
    #     ), patch.object(ai_chat_request.requests, "post", return_value=response):
    #         actual = ai_chat_request.request_chat("prompt")

    #     self.assertEqual('{"code": 429, "message": "quota exceeded"}', actual)

    # def test_execute_persists_error_message_when_request_chat_raises(self):
    #     line_message_processor = LINEMessageProcessor(
    #         id="processor-1",
    #         processing_status=MessageStatus.AwaitingChatResponse.value,
    #         message_event={"replyToken": "reply-token"},
    #         line_user=LINEUser(id="user-1", line_id="line-user-1", talk_count=0),
    #     )

    #     with patch.object(
    #         ai_chat_request.ai_user_profiles_query_service,
    #         "get_ai_user_profile_by_id",
    #         return_value={
    #             "id": "profile-1",
    #             "line_user_id": "line-user-1",
    #             "interest_topics": [],
    #             "lines": [],
    #         },
    #     ), patch.object(
    #         ai_chat_request, "init_chat_request", return_value="prompt"
    #     ), patch.object(
    #         ai_chat_request,
    #         "request_chat",
    #         side_effect=HTTPError("429 Client Error"),
    #     ), patch.object(
    #         ai_chat_request, "response_chat", return_value=line_message_processor
    #     ) as mock_response_chat, patch.object(
    #         ai_chat_request, "enqueue_reply_request"
    #     ) as mock_enqueue_reply_request:
    #         ai_chat_request.execute(line_message_processor, "profile-1")

    #     mock_response_chat.assert_called_once_with(
    #         line_message_processor,
    #         "profile-1",
    #         "HTTPError: 429 Client Error",
    #     )
    #     mock_enqueue_reply_request.assert_called_once_with("processor-1")


if __name__ == "__main__":
    unittest.main()
