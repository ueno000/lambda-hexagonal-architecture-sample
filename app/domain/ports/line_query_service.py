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


class AIUserProfilesQueryService(ABC):
    @abstractmethod
    def get_ai_user_profile_by_line_user_id(self, line_user_id: str) -> Optional[dict]:
        ...

    @abstractmethod
    def get_ai_user_profile_by_id(self, ai_user_profile_id: str) -> Optional[dict]:
        ...
