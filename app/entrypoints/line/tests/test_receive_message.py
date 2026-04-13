import base64
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.tests.support import install_test_stubs

install_test_stubs()

from app.entrypoints.line import handler


class ReceiveMessageTests(unittest.TestCase):
    def test_normalize_request_body_decodes_base64_encoded_body(self):
        payload = {"destination": "dest", "events": []}
        event = SimpleNamespace(
            body=base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8"),
            raw_event={"isBase64Encoded": True},
        )

        actual = handler._normalize_request_body(event)

        self.assertEqual(json.dumps(payload), actual)

    def test_receive_message_processes_base64_encoded_body(self):
        payload = {
            "destination": "dest",
            "events": [
                {
                    "type": "message",
                    "message": {"type": "sticker", "id": "1"},
                    "replyToken": "reply-token",
                    "mode": "active",
                    "timestamp": 1,
                    "webhookEventId": "event-id",
                    "deliveryContext": {"isRedelivery": False},
                    "source": {"type": "user", "userId": "user-1"},
                }
            ],
        }
        encoded_body = base64.b64encode(json.dumps(payload).encode("utf-8")).decode(
            "utf-8"
        )
        handler.app.current_event = SimpleNamespace(
            headers={"x-line-signature": "signature"},
            body=encoded_body,
            raw_event={"isBase64Encoded": True},
        )

        with patch.object(
            handler.config.AppConfig,
            "get_line_channel_secret",
            return_value="secret",
        ), patch.object(
            handler, "validate_signature", return_value=(None, json.dumps(payload))
        ), patch.object(
            handler, "event_type_switcher"
        ) as mock_event_type_switcher:
            response = handler.receive_message()

        self.assertEqual({}, response)
        webhook_event = mock_event_type_switcher.call_args.args[0]
        self.assertEqual("dest", webhook_event.destination)
        self.assertEqual("sticker", webhook_event.events[0]["message"]["type"])


if __name__ == "__main__":
    unittest.main()
