import json
from typing import Generic, List, Optional, Type, TypeVar

from aws_lambda_powertools import Logger
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

logger = Logger()


class HttpResponseBody(Generic[T]):
    def __init__(self):
        self.value: Optional[T] = None
        self.is_valid: bool = False
        self.validation_errors: Optional[List[dict]] = None


def get_body(request_body: str, model: Type[T]) -> HttpResponseBody[T]:
    """_summary_
    POST / PUT リクエストのボディを取得し、バリデーション結果を返す(JSONのみ)
    Args:
        request_body (str): _description_
        model (Type[T]): _description_

    Returns:
        HttpResponseBody[T]: _description_
    """

    body = HttpResponseBody[T]()
    logger.info(f"request_utils request_body:{request_body}")

    try:
        data = json.loads(request_body)

        body.value = model(**data)
        body.is_valid = True
        body.validation_errors = None

    except ValidationError as e:
        body.is_valid = False
        body.validation_errors = e.errors()
        logger.error(
            e,
            f"request_utils ValidationError request_body:{body} e.errors():{e.errors()}",
        )

    except Exception as e:
        body.is_valid = False
        body.validation_errors = [{"error": str(e)}]
        logger.exception(
            e,
            f"request_utils Exception request_body:{body}e.errors():{e.errors()}",
        )

    return body
