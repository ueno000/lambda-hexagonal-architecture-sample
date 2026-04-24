import sys
import types


def install_test_stubs() -> None:
    _install_pydantic_stub()
    _install_boto3_stub()
    _install_powertools_stub()
    _install_requests_stub()
    _install_mypy_boto3_dynamodb_stub()


def _install_pydantic_stub() -> None:
    if "pydantic" in sys.modules:
        return

    module = types.ModuleType("pydantic")

    class BaseModel:
        def __init__(self, **kwargs):
            annotations = getattr(self.__class__, "__annotations__", {})
            for name in annotations:
                if name in kwargs:
                    value = kwargs[name]
                elif hasattr(self.__class__, name):
                    default = getattr(self.__class__, name)
                    value = default() if callable(default) else default
                else:
                    value = None
                setattr(self, name, value)

        @classmethod
        def parse_obj(cls, obj):
            if isinstance(obj, cls):
                return obj
            return cls(**obj)

        def dict(self, *args, **kwargs):
            return dict(self.__dict__)

    def Field(default=None, default_factory=None, **kwargs):
        if default_factory is not None:
            return default_factory
        return default

    def field_validator(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    module.BaseModel = BaseModel
    module.Field = Field
    module.field_validator = field_validator
    sys.modules["pydantic"] = module


def _install_boto3_stub() -> None:
    if "boto3" in sys.modules:
        return

    module = types.ModuleType("boto3")

    class DummyClient:
        def __init__(self):
            self.meta = types.SimpleNamespace(client=self)

        def get_secret_value(self, **kwargs):
            return {"SecretString": "{}"}

        def send_message(self, **kwargs):
            return {"MessageId": "dummy"}

        def get_item(self, **kwargs):
            return {}

        def query(self, **kwargs):
            return {"Items": []}

        def transact_write_items(self, **kwargs):
            return {}

    def client(*args, **kwargs):
        return DummyClient()

    def resource(*args, **kwargs):
        return types.SimpleNamespace(meta=types.SimpleNamespace(client=DummyClient()))

    module.client = client
    module.resource = resource
    sys.modules["boto3"] = module

    dynamodb_module = types.ModuleType("boto3.dynamodb")
    conditions_module = types.ModuleType("boto3.dynamodb.conditions")
    types_module = types.ModuleType("boto3.dynamodb.types")
    conditions_module.Key = lambda value: value

    class TypeDeserializer:
        def deserialize(self, value):
            return value

    types_module.TypeDeserializer = TypeDeserializer
    sys.modules["boto3.dynamodb"] = dynamodb_module
    sys.modules["boto3.dynamodb.conditions"] = conditions_module
    sys.modules["boto3.dynamodb.types"] = types_module


def _install_powertools_stub() -> None:
    if "aws_lambda_powertools" in sys.modules:
        return

    module = types.ModuleType("aws_lambda_powertools")

    class Logger:
        def info(self, *args, **kwargs):
            return None

        def warning(self, *args, **kwargs):
            return None

        def error(self, *args, **kwargs):
            return None

        def exception(self, *args, **kwargs):
            return None

        def inject_lambda_context(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

    class Tracer:
        def capture_method(self, func):
            return func

        def capture_lambda_handler(self, func):
            return func

    module.Logger = Logger
    module.Tracer = Tracer
    sys.modules["aws_lambda_powertools"] = module

    event_handler_module = types.ModuleType("aws_lambda_powertools.event_handler")
    api_gateway_module = types.ModuleType(
        "aws_lambda_powertools.event_handler.api_gateway"
    )

    class ApiGatewayResolver:
        def __init__(self):
            self.current_event = None

        def post(self, _path):
            def decorator(func):
                return func

            return decorator

        def resolve(self, event, context):
            return {"event": event, "context": context}

    api_gateway_module.ApiGatewayResolver = ApiGatewayResolver
    event_handler_module.api_gateway = api_gateway_module
    sys.modules["aws_lambda_powertools.event_handler"] = event_handler_module
    sys.modules[
        "aws_lambda_powertools.event_handler.api_gateway"
    ] = api_gateway_module


def _install_requests_stub() -> None:
    if "requests" in sys.modules:
        return

    module = types.ModuleType("requests")
    module.post = lambda *args, **kwargs: types.SimpleNamespace(
        status_code=200, text="ok"
    )
    module.get = lambda *args, **kwargs: types.SimpleNamespace(
        status_code=200, text="ok", json=lambda: {"displayName": "Stub User"}
    )
    sys.modules["requests"] = module


def _install_mypy_boto3_dynamodb_stub() -> None:
    if "mypy_boto3_dynamodb" in sys.modules:
        return

    module = types.ModuleType("mypy_boto3_dynamodb")
    module.client = types.SimpleNamespace(DynamoDBClient=object)
    module.type_defs = types.SimpleNamespace(TransactWriteItemTypeDef=dict)
    sys.modules["mypy_boto3_dynamodb"] = module
