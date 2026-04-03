import uuid
from datetime import datetime, timezone

from app.domain.commands import create_line_message_processor_command
from app.domain.model.line.line_message_processor import LINEMessageProcessor
from app.domain.ports import unit_of_work


def handle_create_line_messaging_processor_command(
    command: create_line_message_processor_command.CreateLINEMessagingProcessorCommand,
    unit_of_work: unit_of_work.UnitOfWork,
) -> str:
    current_time = datetime.now(timezone.utc).isoformat()
    id = str(uuid.uuid4())

    first_event = command.event.events[0]

    line_messaging_processor_obj = LINEMessageProcessor(
        id=id,
        messageEvents=first_event,
        createDate=current_time,
        lastUpdateDate=current_time,
    )

    with unit_of_work:
        unit_of_work.products.add(line_messaging_processor_obj)
        unit_of_work.commit()

    return id
