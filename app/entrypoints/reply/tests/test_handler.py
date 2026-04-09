import json
import unittest
from unittest.mock import patch

from app.tests.support import install_test_stubs

install_test_stubs()

from app.domain.model.line.line_message_processor import LINEMessageProcessor
from app.domain.model.line.line_message_processor import MessageStatus
from app.domain.model.line.line_user import LINEUser
from app.entrypoints.reply import handler


class ReplyHandlerTests(unittest.TestCase):
    def test_process_record_calls_reply_message(self):
        record = {"body": json.dumps({"line_message_processor_id": "processor-1"})}
        message_processor = LINEMessageProcessor(
            id="processor-1",
            processing_status=MessageStatus.AwaitingChatResponse.value,
            message_event={"replyToken": "reply-token"},
            line_user=LINEUser(id="user-1", line_id="line-user-1", talk_count=0),
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
