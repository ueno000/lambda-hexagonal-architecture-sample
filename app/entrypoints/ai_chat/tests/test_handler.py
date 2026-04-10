import json
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

from app.tests.support import install_test_stubs

install_test_stubs()

from app.domain.model.line.line_message_processor import LINEMessageProcessor
from app.domain.model.line.line_message_processor import MessageStatus
from app.domain.model.line.line_user import LINEUser

handler_path = (
    Path(__file__).resolve().parents[1] / "handler.py"
)
spec = importlib.util.spec_from_file_location("ai_chat_handler", handler_path)
handler = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(handler)


class AIChatHandlerTests(unittest.TestCase):
    def test_process_record_queries_line_message_processor_and_calls_execute(self):
        record = {
            "body": json.dumps(
                {
                    "line_message_processor_id": "processor-1",
                    "ai_user_profile_id": "profile-1",
                }
            )
        }
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
        ) as mock_get_processor, patch.object(
            handler, "execute"
        ) as mock_execute:
            handler.process_record(record)

        mock_get_processor.assert_called_once_with("processor-1")
        mock_execute.assert_called_once_with(message_processor, "profile-1")

    def test_process_record_returns_when_processor_not_found(self):
        record = {
            "body": json.dumps(
                {
                    "line_message_processor_id": "missing",
                    "ai_user_profile_id": "profile-1",
                }
            )
        }

        with patch.object(
            handler.line_query_service,
            "get_line_message_processor_by_id",
            return_value=None,
        ) as mock_get_processor, patch.object(
            handler, "execute"
        ) as mock_execute:
            handler.process_record(record)

        mock_get_processor.assert_called_once_with("missing")
        mock_execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
