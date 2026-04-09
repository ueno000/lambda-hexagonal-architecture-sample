import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

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
    def test_assign_received_message_enqueues_processor_id(self):
        webhook_event = SimpleNamespace(
            events=[
                {
                    "source": {"userId": "user-1"},
                    "replyToken": "reply-token",
                    "message": {"type": "text"},
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
            assign_received_message, "enqueue_chat_request"
        ) as mock_enqueue_chat_request:
            processor_id = assign_received_message.assign_received_message(webhook_event)

        self.assertEqual("processor-1", processor_id)
        self.assertTrue(dummy_uow.committed)
        self.assertEqual(
            MessageStatus.AwaitingChatResponse,
            line_message_processor.processing_status,
        )
        self.assertEqual("user-1", line_message_processor.line_user.line_id)
        mock_enqueue_chat_request.assert_called_once_with("processor-1")

    def test_enqueue_chat_request_sends_expected_message(self):
        with patch.object(
            assign_received_message.config.AppConfig,
            "get_chat_queue_url",
            return_value="https://example.com/chat-queue",
        ), patch.object(
            assign_received_message.sqs_client, "send_message"
        ) as mock_send_message:
            assign_received_message.enqueue_chat_request("processor-123")

        mock_send_message.assert_called_once_with(
            QueueUrl="https://example.com/chat-queue",
            MessageBody=json.dumps(
                {"line_message_processor_id": "processor-123"},
                ensure_ascii=False,
            ),
        )


if __name__ == "__main__":
    unittest.main()
