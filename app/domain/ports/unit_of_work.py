import typing
from abc import ABC, abstractmethod

from app.domain.model import product, product_version
from app.domain.model.line import line_user, line_message_processor


class ProductsRepository(ABC):
    @abstractmethod
    def add(self, product: product.Product) -> None:
        ...

    @abstractmethod
    def update_attributes(self, product_id: str, **kwargs) -> None:
        ...

    @abstractmethod
    def get(self, product_id: str) -> typing.Optional[product.Product]:
        ...

    @abstractmethod
    def delete(self, product_id: str) -> None:
        ...


class ProductVersionsRepository(ABC):
    @abstractmethod
    def add(
        self, product_id: str, product_version: product_version.ProductVersion
    ) -> None:
        ...

    @abstractmethod
    def get(
        self, product_id: str, product_version_id: str
    ) -> typing.Optional[product_version.ProductVersion]:
        ...


class LINEUsersRepository(ABC):
    @abstractmethod
    def add(self, line_user: line_user.LINEUser) -> None:
        ...

    @abstractmethod
    def put(self, line_user: line_user.LINEUser) -> None:
        ...

    @abstractmethod
    def update(self, line_user: line_user.LINEUser) -> None:
        ...

    @abstractmethod
    def get(self, user_id: str) -> typing.Optional[line_user.LINEUser]:
        ...


class LINEMessageProcessorsRepository(ABC):
    @abstractmethod
    def add(
        self, line_message_processor: line_message_processor.LINEMessageProcessor
    ) -> None:
        ...

    @abstractmethod
    def put(
        self, line_message_processor: line_message_processor.LINEMessageProcessor
    ) -> None:
        ...

    @abstractmethod
    def update(
        self, line_message_processor: line_message_processor.LINEMessageProcessor
    ) -> None:
        ...

    @abstractmethod
    def get(
        self, processor_id: str
    ) -> typing.Optional[line_message_processor.LINEMessageProcessor]:
        ...


class UnitOfWork(ABC):
    products: ProductsRepository
    product_versions: ProductVersionsRepository
    line_users: LINEUsersRepository
    line_message_processors: LINEMessageProcessorsRepository

    @abstractmethod
    def commit(self) -> None:
        ...

    @abstractmethod
    def __enter__(self) -> typing.Any:
        ...

    @abstractmethod
    def __exit__(self, *args) -> None:
        ...
