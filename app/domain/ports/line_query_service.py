from abc import ABC, abstractmethod
from typing import Optional

from app.domain.model.line import line_user, line_message_processor


class LINEUsersQueryService(ABC):
    @abstractmethod
    def get_line_user_by_line_id(self, line_id: str) -> Optional[line_user.LINEUser]:
        ...


class LINEMessageProcessorsQueryService(ABC):
    @abstractmethod
    def get_line_message_processor_by_id(
        self, processor_id: str
    ) -> Optional[line_message_processor.LINEMessageProcessor]:
        ...
