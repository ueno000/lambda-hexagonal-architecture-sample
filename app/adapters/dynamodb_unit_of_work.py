import enum
import typing

from mypy_boto3_dynamodb import client

from app.adapters.internal import dynamodb_base
from app.domain.model.ai_chat import ai_user_profile
from app.domain.model.line import line_message_processor, line_user
from app.domain.ports import unit_of_work


class DBPrefix(enum.Enum):
    LINE_USER = "LINEUSER"
    LINE_MESSAGE_PROCESSOR = "LINEMESSAGEPROCESSOR"
    AI_USER_PROFILE = "AIUSERPROFILE"


class DynamoDBLINEUsersRepository(dynamodb_base.DynamoDBRepository):
    """LINE Users DynamoDB repository."""

    def __init__(self, table_name, context: dynamodb_base.DynamoDBContext):
        super().__init__(table_name, context)

    def add(self, line_user: line_user.LINEUser) -> None:
        """Adds a LINE user to the DynamoDB table."""
        self.add_generic_item(
            item=line_user.dict(), key=self.generate_line_user_key(line_user.id)
        )

    def put(self, line_user: line_user.LINEUser) -> None:
        """Puts a LINE user into the DynamoDB table (upsert)."""
        self.put_generic_item(
            item=line_user.dict(), key=self.generate_line_user_key(line_user.id)
        )

    def update(self, line_user: line_user.LINEUser) -> None:
        """Updates an existing LINE user in the DynamoDB table."""
        update_fields = {k: v for k, v in line_user.dict().items() if k not in {"id"}}
        update_expression_setters = [f"{key}=:{key}" for key in update_fields.keys()]
        update_values = {f":{key}": value for key, value in update_fields.items()}

        self.update_generic_item(
            expression={
                "UpdateExpression": f"set {', '.join(update_expression_setters)}",
                "ExpressionAttributeValues": update_values,
                "ConditionExpression": "attribute_exists(PK)",
            },
            key=self.generate_line_user_key(line_user.id),
        )

    def get(self, user_id: str) -> typing.Optional[line_user.LINEUser]:
        """Gets a LINE user from the DynamoDB table."""
        key = self.generate_line_user_key(user_id)
        request = self._create_get_request(key)
        user_dict = self._context.get_generic_item(request)
        return (
            line_user.LINEUser.parse_obj(user_dict) if user_dict is not None else None
        )

    @staticmethod
    def generate_line_user_key(id: str) -> dict:
        """Generates primary key for LINE user entity."""
        return {
            "id": id,
        }


class DynamoDBLINEMessageProcessorsRepository(dynamodb_base.DynamoDBRepository):
    """LINE Message Processors DynamoDB repository."""

    def __init__(self, table_name, context: dynamodb_base.DynamoDBContext):
        super().__init__(table_name, context)

    def add(
        self, line_message_processor: line_message_processor.LINEMessageProcessor
    ) -> None:
        """Adds a LINE message processor to the DynamoDB table."""
        self.add_generic_item(
            item=line_message_processor.dict(),
            key=self.generate_line_message_processor_key(line_message_processor.id),
        )

    def put(
        self, line_message_processor: line_message_processor.LINEMessageProcessor
    ) -> None:
        """Puts a LINE message processor into the DynamoDB table (upsert)."""
        self.put_generic_item(
            item=line_message_processor.dict(),
            key=self.generate_line_message_processor_key(line_message_processor.id),
        )

    def update(
        self, line_message_processor: line_message_processor.LINEMessageProcessor
    ) -> None:
        """Updates an existing LINE message processor in the DynamoDB table."""
        update_fields = {
            k: v for k, v in line_message_processor.dict().items() if k != "id"
        }
        update_expression_setters = [f"{key}=:{key}" for key in update_fields.keys()]
        update_values = {f":{key}": value for key, value in update_fields.items()}

        self.update_generic_item(
            expression={
                "UpdateExpression": f"set {', '.join(update_expression_setters)}",
                "ExpressionAttributeValues": update_values,
                "ConditionExpression": "attribute_exists(PK)",
            },
            key=self.generate_line_message_processor_key(line_message_processor.id),
        )

    def get(
        self, processor_id: str
    ) -> typing.Optional[line_message_processor.LINEMessageProcessor]:
        """Gets a LINE message processor from the DynamoDB table."""
        key = self.generate_line_message_processor_key(processor_id)
        request = self._create_get_request(key)
        processor_dict = self._context.get_generic_item(request)
        return (
            line_message_processor.LINEMessageProcessor.parse_obj(processor_dict)
            if processor_dict is not None
            else None
        )

    @staticmethod
    def generate_line_message_processor_key(processor_id: str) -> dict:
        """Generates primary key for LINE message processor entity."""
        return {
            "PK": f"{DBPrefix.LINE_MESSAGE_PROCESSOR.value}#{processor_id}",
        }


class DynamoDBAIUserProfileRepository(dynamodb_base.DynamoDBRepository):
    """AI User Profile DynamoDB repository."""

    def __init__(self, table_name, context: dynamodb_base.DynamoDBContext):
        super().__init__(table_name, context)

    def add(self, ai_user_profile: ai_user_profile.AIUserProfile) -> None:
        """Adds a AI User Profile to the DynamoDB table."""
        self.add_generic_item(
            item=_dump_model(ai_user_profile),
            key=self.generate_ai_user_profile_key(ai_user_profile.id),
        )

    def put(self, ai_user_profile: ai_user_profile.AIUserProfile) -> None:
        """Puts a AI User Profile into the DynamoDB table (upsert)."""
        self.put_generic_item(
            item=_dump_model(ai_user_profile),
            key=self.generate_ai_user_profile_key(ai_user_profile.id),
        )

    def update(self, ai_user_profile: ai_user_profile.AIUserProfile) -> None:
        """Updates an existing AI User Profile in the DynamoDB table."""
        update_fields = {
            k: v
            for k, v in ai_user_profile.model_dump(exclude_unset=True).items()
            if k not in {"id"}
        }

        update_expression_setters = [f"#{k}=:{k}" for k in update_fields.keys()]
        expression_attribute_names = {f"#{k}": k for k in update_fields.keys()}
        update_values = {f":{k}": v for k, v in update_fields.items()}

        self.update_generic_item(
            expression={
                "UpdateExpression": f"set {', '.join(update_expression_setters)}",
                "ExpressionAttributeValues": update_values,
                "ExpressionAttributeNames": expression_attribute_names,
                "ConditionExpression": "attribute_exists(id)",
            },
            key=self.generate_ai_user_profile_key(ai_user_profile.id),
        )

    def get(self, profile_id: str) -> typing.Optional[ai_user_profile.AIUserProfile]:
        """Gets a AI User Profile from the DynamoDB table."""
        key = self.generate_ai_user_profile_key(profile_id)
        request = self._create_get_request(key)
        user_dict = self._context.get_generic_item(request)
        return (
            ai_user_profile.AIUserProfile.parse_obj(user_dict)
            if user_dict is not None
            else None
        )

    @staticmethod
    def generate_ai_user_profile_key(id: str) -> dict:
        """Generates primary key for AI User Profile entity."""
        return {
            "id": id,
        }


def _dump_model(model: typing.Any) -> dict:
    model_dump = getattr(model, "model_dump", None)
    if callable(model_dump):
        return model_dump()

    dict_method = getattr(model, "dict", None)
    if callable(dict_method):
        return dict_method()

    if isinstance(model, dict):
        return model

    raise TypeError(f"Unsupported model type: {type(model)!r}")


class DynamoDBUnitOfWork(unit_of_work.UnitOfWork):
    """Repository provider and unit of work for DynamoDB."""

    line_users: DynamoDBLINEUsersRepository
    line_message_processors: DynamoDBLINEMessageProcessorsRepository
    ai_user_profile: DynamoDBAIUserProfileRepository

    def __init__(
        self,
        line_table_name: str,
        line_user_table_name: str,
        ai_user_profile_table_name: str,
        dynamodb_client: client.DynamoDBClient,
    ):
        self._dynamo_db_client = dynamodb_client
        self._line_table_name = line_table_name
        self._line_user_table_name = line_user_table_name
        self._ai_user_profile_table_name = ai_user_profile_table_name
        self._context: typing.Optional[dynamodb_base.DynamoDBContext] = None

    def commit(self) -> None:
        """Commits up to 25 changes to the DynamoDB table in a single transaction."""
        if self._context:
            self._context.commit()

    def __enter__(self) -> typing.Any:
        self._context = dynamodb_base.DynamoDBContext(
            dynamodb_client=self._dynamo_db_client
        )
        self.line_users = DynamoDBLINEUsersRepository(
            table_name=self._line_user_table_name, context=self._context
        )
        self.line_message_processors = DynamoDBLINEMessageProcessorsRepository(
            table_name=self._line_table_name, context=self._context
        )
        self.ai_user_profile = DynamoDBAIUserProfileRepository(
            table_name=self._ai_user_profile_table_name, context=self._context
        )
        return self

    def __exit__(self, *args) -> None:
        self._context = None
        self.line_users = None  # type: ignore
        self.line_message_processors = None  # type: ignore
        self.ai_user_profile = None  # type: ignore
