import uuid
from datetime import datetime, timezone

from app.domain.commands import create_line_message_processor_command
from app.domain.model.line.line_message_processor import LINEMessageProcessor
from app.domain.ports import unit_of_work


def handle_create_line_messaging_processor_command(
    command: create_line_message_processor_command.CreateLINEMessagingProcessorCommand,
    unit_of_work: unit_of_work.UnitOfWork,
) -> str:
    """_summary_

    Args:
        command (create_line_message_processor_command.CreateLINEMessagingProcessorCommand): _description_
        unit_of_work (unit_of_work.UnitOfWork): _description_

    Returns:
        str: _description_
    """
    current_time = datetime.now(timezone.utc).isoformat()
    id = str(uuid.uuid4())

    first_event = command.event.events[0]

    line_messaging_processor_obj = LINEMessageProcessor(
        id=id,
        message_event=first_event,
        create_date=current_time,
        last_update_date=current_time,
    )

    with unit_of_work:
        unit_of_work.line_message_processors.add(line_messaging_processor_obj)
        unit_of_work.commit()

    return id
