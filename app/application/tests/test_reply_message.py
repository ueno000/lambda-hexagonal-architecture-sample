import unittest
from unittest.mock import Mock, patch

from app.tests.support import install_test_stubs

install_test_stubs()

from app.application.line import reply_message
from app.domain.model.line.line_message_processor import LINEMessageProcessor
from app.domain.model.line.line_message_processor import MessageStatus
from app.domain.model.line.line_user import LINEUser


class DummyUnitOfWork:
    def __init__(self):
        self.line_users = type("LineUsersRepo", (), {"put": Mock()})()
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


def make_processor(status: int = MessageStatus.AwaitingChatResponse.value):
    return LINEMessageProcessor(
        id="processor-1",
        processing_status=status,
        message_event={"replyToken": "reply-token"},
        line_user=LINEUser(id="user-1", line_id="line-user-1", talk_count=0),
    )


class ReplyMessageTests(unittest.TestCase):
    def test_reply_message_skips_when_status_is_not_awaiting_chat_response(self):
        with patch.object(reply_message, "send_message") as mock_send_message:
            reply_message.reply_message(make_processor(MessageStatus.Initial.value))

        mock_send_message.assert_not_called()

    def test_reply_message_calls_send_message_when_status_is_awaiting_chat_response(
        self,
    ):
        response = type("Response", (), {"status_code": 200, "text": "ok"})()
        processor = make_processor()
        dummy_uow = DummyUnitOfWork()

        with patch.object(
            reply_message, "send_message", return_value=response
        ) as mock_send_message, patch.object(
            reply_message, "unit_of_work", dummy_uow
        ):
            reply_message.reply_message(processor)

        mock_send_message.assert_called_once_with(
            "reply-token",
            reply_message.REPLY_TEXT,
        )
        self.assertEqual(1, processor.line_user.talk_count)
        self.assertEqual(reply_message.REPLY_TEXT, processor.reply_message)
        self.assertEqual(MessageStatus.Completed, processor.processing_status)
        self.assertEqual(2, dummy_uow.commit_count)
        self.assertEqual(1, dummy_uow.line_users.put.call_count)
        self.assertEqual(1, dummy_uow.line_message_processors.put.call_count)


if __name__ == "__main__":
    unittest.main()
