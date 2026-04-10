import unittest
from unittest.mock import Mock, patch

from app.tests.support import install_test_stubs

install_test_stubs()

from app.application.ai_chat import ai_chat_request
from app.domain.model.ai_chat.ai_user_profile import AIUserProfile
from app.domain.model.line.line_message_processor import LINEMessageProcessor
from app.domain.model.line.line_message_processor import MessageStatus
from app.domain.model.line.line_user import LINEUser


class DummyUnitOfWork:
    def __init__(self):
        self.line_message_processors = type(
            "LineMessageProcessorsRepo", (), {"put": Mock()}
        )()
        self.commit_count = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def commit(self):
        self.commit_count += 1


def make_processor():
    return LINEMessageProcessor(
        id="processor-1",
        processing_status=MessageStatus.AwaitingChatResponse.value,
        message_event={"message": {"text": "/本日の案内"}, "replyToken": "reply-token"},
        line_user=LINEUser(id="user-1", line_id="line-user-1", talk_count=0),
    )


class AIChatRequestTests(unittest.TestCase):
    def test_init_chat_request_builds_prompt_from_ai_user_profile(self):
        processor = make_processor()
        ai_user_profile = AIUserProfile(
            id="profile-1",
            line_user_id="user-1",
            name="太郎",
            gender="男性",
            birth_year=1990,
            interest_topics=["グルメ", "イベント"],
            residence="東京都",
            lines=["山手線", "中央線"],
        )

        prompt = ai_chat_request.init_chat_request(processor, ai_user_profile)

        self.assertIn("情報の正確性とソースの信頼性", prompt)
        self.assertIn("名前：太郎", prompt)
        self.assertIn("年齢：30代", prompt)
        self.assertIn("性別:男性", prompt)
        self.assertIn("関心トピック：グルメ、イベント", prompt)
        self.assertIn("居住/勤務地：東京都", prompt)
        self.assertIn("お気に入り路線： 山手線、中央線", prompt)
        self.assertIn("【運行情報】「山手線 運行情報」「中央線 運行情報」", prompt)
        self.assertIn(
            "【関心トピック】「グルメ 最新」「イベント 最新」",
            prompt,
        )
        self.assertIn("■ユーザー入力 /本日の案内", prompt)

    def test_execute_calls_request_and_response(self):
        processor = make_processor()
        ai_user_profile = {"id": "profile-1", "name": "太郎"}

        with patch.object(
            ai_chat_request.ai_user_profiles_query_service,
            "get_ai_user_profile_by_id",
            return_value=ai_user_profile,
        ) as mock_get_profile, patch.object(
            ai_chat_request, "init_chat_request", return_value="prompt"
        ) as mock_init, patch.object(
            ai_chat_request, "request_chat", return_value="reply"
        ) as mock_request, patch.object(
            ai_chat_request, "response_chat"
        ) as mock_response:
            ai_chat_request.execute(processor, "profile-1")

        mock_get_profile.assert_called_once_with("profile-1")
        mock_init.assert_called_once_with(processor, ai_user_profile)
        mock_request.assert_called_once_with("prompt")
        mock_response.assert_called_once_with(processor, "profile-1", "reply")

    def test_request_chat_calls_gemini_generate_content(self):
        response = type(
            "Response",
            (),
            {
                "raise_for_status": lambda self: None,
                "json": lambda self: {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "text": "generated reply",
                                    }
                                ]
                            }
                        }
                    ]
                },
            },
        )()

        with patch.object(
            ai_chat_request.config.AppConfig,
            "get_gemini_api_key",
            return_value="secret-key",
        ), patch.object(
            ai_chat_request.requests, "post", return_value=response
        ) as mock_post:
            result = ai_chat_request.request_chat("prompt text")

        self.assertEqual("generated reply", result)
        mock_post.assert_called_once_with(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent",
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": "secret-key",
            },
            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": "prompt text",
                            }
                        ]
                    }
                ]
            },
            timeout=30,
        )

    def test_response_chat_updates_processor_to_reply_ready(self):
        processor = make_processor()
        dummy_uow = DummyUnitOfWork()
        chat_session = ai_chat_request.init_chat_session("profile-1", "ai reply")

        with patch.object(ai_chat_request, "unit_of_work", dummy_uow), patch.object(
            ai_chat_request, "init_chat_session", return_value=chat_session
        ) as mock_init_chat_session:
            ai_chat_request.response_chat(processor, "profile-1", "ai reply")

        mock_init_chat_session.assert_called_once_with("profile-1", "ai reply")
        self.assertEqual("ai reply", processor.reply_message)
        self.assertEqual(MessageStatus.ReplyReady, processor.processing_status)
        self.assertEqual(1, dummy_uow.commit_count)
        self.assertEqual(1, dummy_uow.line_message_processors.put.call_count)

    def test_init_chat_session_stores_ai_response(self):
        chat_session = ai_chat_request.init_chat_session("profile-1", "ai reply")

        self.assertEqual("profile-1", chat_session.ai_user_profile_id)
        self.assertEqual("ai reply", chat_session.reply_message)


if __name__ == "__main__":
    unittest.main()
