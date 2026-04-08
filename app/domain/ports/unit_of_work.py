import typing
from abc import ABC, abstractmethod

from app.domain.model.line import line_user, line_message_processor


class LINEUsersRepository(ABC):
    @abstractmethod
    def add(self, line_user: line_user.LINEUser) -> None: ...

    @abstractmethod
    def put(self, line_user: line_user.LINEUser) -> None: ...

    @abstractmethod
    def update(self, line_user: line_user.LINEUser) -> None: ...

    @abstractmethod
    def get(self, user_id: str) -> typing.Optional[line_user.LINEUser]: ...


class LINEMessageProcessorsRepository(ABC):
    @abstractmethod
    def add(
        self, line_message_processor: line_message_processor.LINEMessageProcessor
    ) -> None: ...

    @abstractmethod
    def put(
        self, line_message_processor: line_message_processor.LINEMessageProcessor
    ) -> None: ...

    @abstractmethod
    def update(
        self, line_message_processor: line_message_processor.LINEMessageProcessor
    ) -> None: ...

    @abstractmethod
    def get(
        self, processor_id: str
    ) -> typing.Optional[line_message_processor.LINEMessageProcessor]: ...


class UnitOfWork(ABC):
    line_users: LINEUsersRepository
    line_message_processors: LINEMessageProcessorsRepository

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def __enter__(self) -> typing.Any: ...

    @abstractmethod
    def __exit__(self, *args) -> None: ...
