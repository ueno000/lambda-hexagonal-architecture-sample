import json
from dataclasses import dataclass
import unittest
from unittest.mock import patch

from app.tests.support import install_test_stubs

install_test_stubs()

from app.domain.model.line.line_message_processor import MessageStatus
from app.entrypoints.reply import handler


@dataclass
class DummyMessageEvent:
    replyToken: str


@dataclass
class DummyMessageProcessor:
    processing_status: int
    message_event: DummyMessageEvent


class ReplyHandlerTests(unittest.TestCase):
    def test_process_record_calls_reply_message(self):
        record = {"body": json.dumps({"line_message_processor_id": "processor-1"})}
        message_processor = DummyMessageProcessor(
            processing_status=MessageStatus.AwaitingChatResponse.value,
            message_event=DummyMessageEvent(replyToken="reply-token"),
        )

        with patch.object(
            handler.line_query_service,
            "get_line_message_processor_by_id",
            return_value=message_processor,
        ), patch.object(handler, "reply_message") as mock_reply_message:
            handler.process_record(record)

        mock_reply_message.assert_called_once_with(message_processor)

    def test_process_record_returns_when_processor_not_found(self):
        record = {"body": json.dumps({"line_message_processor_id": "missing"})}

        with patch.object(
            handler.line_query_service,
            "get_line_message_processor_by_id",
            return_value=None,
        ), patch.object(handler, "reply_message") as mock_reply_message:
            handler.process_record(record)

        mock_reply_message.assert_not_called()


if __name__ == "__main__":
    unittest.main()
