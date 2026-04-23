class DataSaveException(Exception):
    """DynamoDB や外部ストレージへの保存に失敗したときの例外"""

    def __init__(self, message: str, inner_exception: Exception | None = None):
        super().__init__(message)
        self.inner_exception = inner_exception
