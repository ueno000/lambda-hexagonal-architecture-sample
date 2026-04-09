import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.tests.support import install_test_stubs

install_test_stubs()

from app.application.line import send_message


class SendMessageTests(unittest.TestCase):
    def test_send_message_raises_when_access_token_is_missing(self):
        with patch.object(
            send_message.config.AppConfig,
            "get_line_channel_access_token",
            return_value="",
        ):
            with self.assertRaises(RuntimeError):
                send_message.send_message("reply-token", "hello")

    def test_send_message_posts_expected_payload(self):
        response = SimpleNamespace(status_code=200, text="ok")

        with patch.object(
            send_message.config.AppConfig,
            "get_line_channel_access_token",
            return_value="access-token",
        ), patch.object(
            send_message.requests, "post", return_value=response
        ) as mock_post:
            result = send_message.send_message("reply-token", "hello")

        self.assertIs(result, response)
        mock_post.assert_called_once_with(
            "https://api.line.me/v2/bot/message/reply",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer access-token",
            },
            data=json.dumps(
                {
                    "replyToken": "reply-token",
                    "messages": [{"type": "text", "text": "hello"}],
                },
                ensure_ascii=False,
            ),
            timeout=10,
        )


if __name__ == "__main__":
    unittest.main()
