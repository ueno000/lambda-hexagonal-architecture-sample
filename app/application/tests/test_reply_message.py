from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.tests.support import install_test_stubs

install_test_stubs()

from app.application.line import reply_message
from app.domain.model.line.line_message_processor import MessageStatus


class ReplyMessageTests(unittest.TestCase):
    def test_reply_message_skips_when_status_is_not_awaiting_chat_response(self):
        with patch.object(reply_message, "send_message") as mock_send_message:
            reply_message.reply_message(MessageStatus.Initial.value, "reply-token")

        mock_send_message.assert_not_called()

    def test_reply_message_calls_send_message_when_status_is_awaiting_chat_response(
        self,
    ):
        response = SimpleNamespace(status_code=200, text="ok")

        with patch.object(
            reply_message, "send_message", return_value=response
        ) as mock_send_message:
            reply_message.reply_message(
                MessageStatus.AwaitingChatResponse.value,
                "reply-token",
            )

        mock_send_message.assert_called_once_with(
            "reply-token",
            "これは返信メッセージです。",
        )


if __name__ == "__main__":
    unittest.main()
