import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.tests.support import install_test_stubs

install_test_stubs()

from app.entrypoints.line import handler


class LineHandlerTests(unittest.TestCase):
    def test_receive_message_returns_400_when_signature_is_invalid(self):
        handler.app.current_event = SimpleNamespace(headers={}, body="{}")

        with patch.object(
            handler,
            "validate_signature",
            return_value=(True, "{}"),
        ):
            response = handler.receive_message()

        self.assertEqual(({"error": "Invalid signature"}, 400), response)

    def test_receive_message_calls_event_type_switcher_for_valid_payload(self):
        payload = {
            "destination": "destination",
            "events": [
                {
                    "type": "message",
                    "replyToken": "reply-token",
                    "message": {"type": "text"},
                    "source": {"userId": "user-1"},
                }
            ],
        }
        handler.app.current_event = SimpleNamespace(headers={}, body=json.dumps(payload))

        with patch.object(
            handler,
            "validate_signature",
            return_value=(False, json.dumps(payload)),
        ), patch.object(handler, "event_type_switcher") as mock_event_type_switcher:
            response = handler.receive_message()

        self.assertEqual({}, response)
        mock_event_type_switcher.assert_called_once()
        webhook_event = mock_event_type_switcher.call_args.args[0]
        self.assertEqual("destination", webhook_event.destination)
        self.assertEqual("message", webhook_event.events[0]["type"])

    def test_receive_message_returns_400_for_invalid_json(self):
        handler.app.current_event = SimpleNamespace(headers={}, body="not-used")

        with patch.object(
            handler,
            "validate_signature",
            return_value=(False, "{invalid-json"),
        ):
            response = handler.receive_message()

        self.assertEqual(({"error": "Invalid JSON"}, 400), response)


if __name__ == "__main__":
    unittest.main()
