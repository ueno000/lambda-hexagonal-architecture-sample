from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.application.line import event_type_switcher


class EventTypeSwitcherTests(unittest.TestCase):
    def test_calls_assign_received_message_for_supported_message(self):
        webhook_event = SimpleNamespace(
            events=[
                {
                    "type": "message",
                    "message": {"type": "text"},
                }
            ]
        )

        with patch.object(
            event_type_switcher, "assign_received_message"
        ) as mock_assign_received_message:
            event_type_switcher.event_type_switcher(webhook_event)

        mock_assign_received_message.assert_called_once_with(webhook_event)

    def test_does_not_raise_when_downstream_fails(self):
        webhook_event = SimpleNamespace(
            events=[
                {
                    "type": "message",
                    "message": {"type": "text"},
                }
            ]
        )

        with patch.object(
            event_type_switcher,
            "assign_received_message",
            side_effect=RuntimeError("boom"),
        ):
            event_type_switcher.event_type_switcher(webhook_event)

    def test_skips_unsupported_message_type(self):
        webhook_event = SimpleNamespace(
            events=[
                {
                    "type": "message",
                    "message": {"type": "image"},
                }
            ]
        )

        with patch.object(
            event_type_switcher, "assign_received_message"
        ) as mock_assign_received_message:
            event_type_switcher.event_type_switcher(webhook_event)

        mock_assign_received_message.assert_not_called()


if __name__ == "__main__":
    unittest.main()
