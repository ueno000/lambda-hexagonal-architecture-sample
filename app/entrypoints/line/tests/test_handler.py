import json
import base64
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

    def test_receive_message_accepts_double_encoded_json_payload(self):
        payload = {
            "destination": "destination",
            "events": [
                {
                    "type": "message",
                    "replyToken": "reply-token",
                    "message": {"type": "sticker"},
                    "source": {"userId": "user-1"},
                }
            ],
        }
        handler.app.current_event = SimpleNamespace(headers={}, body="not-used")

        with patch.object(
            handler,
            "validate_signature",
            return_value=(False, json.dumps(json.dumps(payload))),
        ), patch.object(handler, "event_type_switcher") as mock_event_type_switcher:
            response = handler.receive_message()

        self.assertEqual({}, response)
        mock_event_type_switcher.assert_called_once()
        webhook_event = mock_event_type_switcher.call_args.args[0]
        self.assertEqual("sticker", webhook_event.events[0]["message"]["type"])

    def test_receive_message_accepts_base64_encoded_payload(self):
        payload = {
            "destination": "destination",
            "events": [
                {
                    "type": "message",
                    "replyToken": "reply-token",
                    "message": {"type": "sticker"},
                    "source": {"userId": "user-1"},
                }
            ],
        }
        encoded_body = base64.b64encode(json.dumps(payload).encode("utf-8")).decode(
            "utf-8"
        )
        handler.app.current_event = SimpleNamespace(
            headers={}, body=encoded_body, is_base64_encoded=True
        )

        with patch.object(
            handler,
            "validate_signature",
            return_value=(False, encoded_body),
        ), patch.object(handler, "event_type_switcher") as mock_event_type_switcher:
            response = handler.receive_message()

        self.assertEqual({}, response)
        mock_event_type_switcher.assert_called_once()
        webhook_event = mock_event_type_switcher.call_args.args[0]
        self.assertEqual("sticker", webhook_event.events[0]["message"]["type"])

    def test_receive_message_prefers_raw_event_body(self):
        payload = {
            "destination": "destination",
            "events": [
                {
                    "type": "message",
                    "replyToken": "reply-token",
                    "message": {"type": "text", "text": "hello"},
                    "source": {"userId": "user-1"},
                }
            ],
        }
        handler.app.current_event = SimpleNamespace(
            headers={},
            body="{broken",
            raw_event={"body": json.dumps(payload), "isBase64Encoded": False},
        )

        with patch.object(
            handler,
            "validate_signature",
            return_value=(False, json.dumps(payload)),
        ), patch.object(handler, "event_type_switcher") as mock_event_type_switcher:
            response = handler.receive_message()

        self.assertEqual({}, response)
        mock_event_type_switcher.assert_called_once()

    def test_receive_message_sanitizes_control_characters_before_json_parse(self):
        corrupted_payload = (
            '{"destination":"destination","events":[{"type":"message","replyToken":"reply-token",'
            '"message":{"type":"sticker","markAsReadToken":"abc\x0bdef"},"source":{"userId":"user-1"}}]}'
        )
        handler.app.current_event = SimpleNamespace(headers={}, body=corrupted_payload)

        with patch.object(
            handler,
            "validate_signature",
            return_value=(False, corrupted_payload),
        ), patch.object(handler, "event_type_switcher") as mock_event_type_switcher:
            response = handler.receive_message()

        self.assertEqual({}, response)
        mock_event_type_switcher.assert_called_once()


if __name__ == "__main__":
    unittest.main()
