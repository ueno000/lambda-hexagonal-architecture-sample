import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.tests.support import install_test_stubs

install_test_stubs()

from app.domain.command_handlers import create_line_message_processor_command_handler
from app.domain.commands.create_line_message_processor_command import (
    CreateLINEMessagingProcessorCommand,
)


class DummyUnitOfWork:
    def __init__(self):
        self.line_message_processors = SimpleNamespace(add=Mock())
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def commit(self):
        self.committed = True


class CommandHandlerTests(unittest.TestCase):
    def test_create_line_message_processor_command_stores_first_event(self):
        command = CreateLINEMessagingProcessorCommand(
            message_event=SimpleNamespace(
                events=[
                    SimpleNamespace(
                        replyToken="reply-token",
                    )
                ]
            )
        )
        unit_of_work = DummyUnitOfWork()

        processor_id = (
            create_line_message_processor_command_handler.handle_create_line_messaging_processor_command(
                command=command,
                unit_of_work=unit_of_work,
            )
        )

        self.assertTrue(processor_id)
        self.assertTrue(unit_of_work.committed)
        saved_processor = unit_of_work.line_message_processors.add.call_args.args[0]
        self.assertEqual(processor_id, saved_processor.id)
        self.assertEqual("reply-token", saved_processor.message_event.replyToken)
