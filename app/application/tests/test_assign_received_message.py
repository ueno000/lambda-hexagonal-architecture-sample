import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from app.tests.support import install_test_stubs

install_test_stubs()

from app.application.line import assign_received_message
from app.domain.model.line.line_message_processor import MessageStatus
from app.domain.model.line.line_user import LINEUser


class DummyUnitOfWork:
    def __init__(self):
        self.line_message_processors = SimpleNamespace(put=Mock())
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def commit(self):
        self.committed = True


class AssignReceivedMessageTests(unittest.TestCase):
    def test_assign_received_message_sends_greeting_for_new_user(self):
        webhook_event = SimpleNamespace(
            events=[
                {
                    "source": {"userId": "new-user"},
                    "replyToken": "reply-token",
                    "message": {"type": "text", "text": "hello"},
                }
            ]
        )
        created_user = LINEUser(id="line-user-id", line_id="new-user")

        with patch.object(
            assign_received_message.line_users_query_service,
            "get_line_user_by_line_id",
            return_value=None,
        ), patch.object(
            assign_received_message,
            "create_line_user",
            return_value=created_user,
        ) as mock_create_line_user, patch.object(
            assign_received_message,
            "send_message",
        ) as mock_send_message, patch.object(
            assign_received_message,
            "insert_line_message_processor",
        ) as mock_insert_line_message_processor, patch.object(
            assign_received_message,
            "enqueue_ai_chat_request",
        ) as mock_enqueue_ai_chat_request, patch.object(
            assign_received_message,
            "enqueue_reply_request",
        ) as mock_enqueue_reply_request, patch.object(
            assign_received_message.ai_user_profiles_query_service,
            "get_ai_user_profile_by_line_user_id",
        ) as mock_get_ai_user_profile:
            processor_id = assign_received_message.assign_received_message(
                webhook_event
            )

        self.assertIsNone(processor_id)
        mock_create_line_user.assert_called_once_with("new-user")
        mock_send_message.assert_called_once_with(
            reply_token="reply-token",
            message="はじめまして。メッセージありがとうございます。",
        )
        mock_insert_line_message_processor.assert_not_called()
        mock_enqueue_ai_chat_request.assert_not_called()
        mock_enqueue_reply_request.assert_not_called()
        mock_get_ai_user_profile.assert_not_called()

    def test_assign_received_message_enqueues_reply_queue_for_normal_message(self):
        webhook_event = SimpleNamespace(
            events=[
                {
                    "source": {"userId": "user-1"},
                    "replyToken": "reply-token",
                    "message": {"type": "text", "text": "hello"},
                }
            ]
        )
        line_user = LINEUser(id="line-user-id", line_id="user-1")
        line_message_processor = SimpleNamespace(
            id="processor-1",
            processing_status=MessageStatus.Initial,
            line_user=None,
            last_update_date=None,
        )
        dummy_uow = DummyUnitOfWork()

        with patch.object(
            assign_received_message.line_users_query_service,
            "get_line_user_by_line_id",
            return_value=line_user,
        ), patch.object(
            assign_received_message,
            "insert_line_message_processor",
            return_value=line_message_processor,
        ), patch.object(
            assign_received_message, "unit_of_work", dummy_uow
        ), patch.object(
            assign_received_message, "enqueue_ai_chat_request"
        ) as mock_enqueue_ai_chat_request, patch.object(
            assign_received_message, "enqueue_reply_request"
        ) as mock_enqueue_reply_request, patch.object(
            assign_received_message.ai_user_profiles_query_service,
            "get_ai_user_profile_by_line_user_id",
        ) as mock_get_ai_user_profile, patch.object(
            assign_received_message, "send_message"
        ) as mock_send_message:
            processor_id = assign_received_message.assign_received_message(
                webhook_event
            )

        self.assertEqual("processor-1", processor_id)
        self.assertTrue(dummy_uow.committed)
        self.assertEqual(
            MessageStatus.ReplyReady,
            line_message_processor.processing_status,
        )
        self.assertEqual("user-1", line_message_processor.line_user.line_id)
        mock_enqueue_ai_chat_request.assert_not_called()
        mock_enqueue_reply_request.assert_called_once_with("processor-1")
        mock_send_message.assert_not_called()
        mock_get_ai_user_profile.assert_not_called()

    def test_assign_received_message_enqueues_ai_chat_queue_for_todays_guide_command(
        self,
    ):
        webhook_event = SimpleNamespace(
            events=[
                {
                    "source": {"userId": "user-1"},
                    "replyToken": "reply-token",
                    "message": {"type": "text", "text": "/本日の案内"},
                }
            ]
        )
        line_user = LINEUser(id="line-user-id", line_id="user-1")
        line_message_processor = SimpleNamespace(
            id="processor-1",
            processing_status=MessageStatus.Initial,
            line_user=None,
            last_update_date=None,
        )
        dummy_uow = DummyUnitOfWork()
        ai_user_profile = {"id": "profile-1", "line_user_id": "line-user-id"}

        with patch.object(
            assign_received_message.line_users_query_service,
            "get_line_user_by_line_id",
            return_value=line_user,
        ), patch.object(
            assign_received_message,
            "insert_line_message_processor",
            return_value=line_message_processor,
        ), patch.object(
            assign_received_message, "unit_of_work", dummy_uow
        ), patch.object(
            assign_received_message.ai_user_profiles_query_service,
            "get_ai_user_profile_by_line_user_id",
            return_value=ai_user_profile,
        ) as mock_get_ai_user_profile, patch.object(
            assign_received_message, "enqueue_ai_chat_request"
        ) as mock_enqueue_ai_chat_request, patch.object(
            assign_received_message, "enqueue_reply_request"
        ) as mock_enqueue_reply_request:
            processor_id = assign_received_message.assign_received_message(
                webhook_event
            )

        self.assertEqual("processor-1", processor_id)
        mock_get_ai_user_profile.assert_called_once_with("line-user-id")
        mock_enqueue_ai_chat_request.assert_called_once_with("processor-1", "profile-1")
        mock_enqueue_reply_request.assert_not_called()

    def test_assign_received_message_replies_when_ai_user_profile_is_missing(self):
        webhook_event = SimpleNamespace(
            events=[
                {
                    "source": {"userId": "user-1"},
                    "replyToken": "reply-token",
                    "message": {"type": "text", "text": "/本日の案内"},
                }
            ]
        )
        line_user = LINEUser(id="line-user-id", line_id="user-1")
        line_message_processor = SimpleNamespace(
            id="processor-1",
            processing_status=MessageStatus.Initial,
            line_user=None,
            last_update_date=None,
        )
        dummy_uow = DummyUnitOfWork()

        with patch.object(
            assign_received_message.line_users_query_service,
            "get_line_user_by_line_id",
            return_value=line_user,
        ), patch.object(
            assign_received_message,
            "insert_line_message_processor",
            return_value=line_message_processor,
        ), patch.object(
            assign_received_message, "unit_of_work", dummy_uow
        ), patch.object(
            assign_received_message.ai_user_profiles_query_service,
            "get_ai_user_profile_by_line_user_id",
            return_value=None,
        ), patch.object(
            assign_received_message, "enqueue_ai_chat_request"
        ) as mock_enqueue_ai_chat_request, patch.object(
            assign_received_message, "enqueue_reply_request"
        ) as mock_enqueue_reply_request, patch.object(
            assign_received_message, "send_message"
        ) as mock_send_message:
            processor_id = assign_received_message.assign_received_message(
                webhook_event
            )

        self.assertEqual("processor-1", processor_id)
        mock_send_message.assert_called_once_with(
            reply_token="reply-token",
            message="設定からプロフィール設定をしてください",
        )
        mock_enqueue_ai_chat_request.assert_not_called()
        mock_enqueue_reply_request.assert_not_called()

    def test_enqueue_ai_chat_request_sends_expected_message(self):
        with patch.object(
            assign_received_message.config.AppConfig,
            "get_ai_chat_queue_url",
            return_value="https://example.com/ai-chat-queue",
        ), patch.object(
            assign_received_message.sqs_client, "send_message"
        ) as mock_send_message:
            assign_received_message.enqueue_ai_chat_request(
                "processor-123", "profile-1"
            )

        mock_send_message.assert_called_once_with(
            QueueUrl="https://example.com/ai-chat-queue",
            MessageBody=json.dumps(
                {
                    "line_message_processor_id": "processor-123",
                    "ai_user_profile_id": "profile-1",
                },
                ensure_ascii=False,
            ),
        )

    def test_enqueue_reply_request_sends_expected_message(self):
        with patch.object(
            assign_received_message.config.AppConfig,
            "get_reply_queue_url",
            return_value="https://example.com/reply-queue",
        ), patch.object(
            assign_received_message.sqs_client, "send_message"
        ) as mock_send_message:
            assign_received_message.enqueue_reply_request("processor-456")

        mock_send_message.assert_called_once_with(
            QueueUrl="https://example.com/reply-queue",
            MessageBody=json.dumps(
                {"line_message_processor_id": "processor-456"},
                ensure_ascii=False,
            ),
        )


if __name__ == "__main__":
    unittest.main()
